"""Follow through: the Heartbeat follows an agent launch's PR to its merge.

docs/internal/CONDUCTOR.md, step 6 (lane K4). On each Heartbeat sweep:

1. **PR refresh.** Every Delivery Source with a launch whose follow-through
   is not resolved (whatever its session does: an agent that exits before
   the merge is still followed) gets one batched ``gh pr list``
   (``PrReceiptsService.refresh``). A
   missing or unauthenticated ``gh`` is a named state on the sweep receipt
   (``gh_missing``, ``gh_unauthenticated``), never a silent skip.
2. **Close the origin on merge.** The launch's PR is selected by identity
   (``_select_pr``): the source's GitHub repository as base and head (never
   a fork), the launch's branch, and a merge after the launch. Its number
   and URL are kept on the launch; several candidates are ``pr_ambiguous``
   and nothing is closed. A selected PR closed without a merge ends the
   follow-through. When it is ``merged``, it closes the item the launch
   came from (``origin_ref``):

   - ``action``: ``FollowThroughService.complete(..., "done")`` with the
     evidence ``{pr_url, merged_sha, merged_at, attempt_id, launch_id}`` in
     the ``commitment.completed`` receipt facts;
   - ``decision_record``: ``DecisionRecordService.link_work(record, "pr",
     url)``; ``decision``: the same, on the decision's record (minted from
     the meeting decision when it has none yet);
   - other kinds have no close; the launch records ``not_closable``.

   Control mode: Secure (``safe``) does not close. It puts one Door item
   ``Merged: confirm close: ...`` (the smallest Needs you mechanism: an
   action item with no owner reads UNASSIGNED in Needs you). When the owner
   marks that item done, the next sweep closes the origin with the same
   evidence; dismissed, the origin stays open (``close_declined``), whatever
   the mode is later. Normal and YOLO close at once.
3. **Clean up** after the merge and the close: the agent's tmux session is
   ended (``coder_factory.kill``, audited), the worktree is removed only if
   the launch created it (else ``worktree_kept_not_ours``) and it is clean
   and merged (``execute_worktree_remove``, refusals by name), its live Work
   attempts abandon (``mark_worktree_removed``, also when the worktree is
   already gone, before the launch reads as done), and the
   launch's own armed gate path is released under the gate file lock.

Idempotent across sweeps and restarts: the state lives on the durable launch
record (``follow_through``), the close is a replay when repeated, and a
module lock keeps two sweeps from acting at once.
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("delivery.follow_through")

#: Launch states that never ran an agent: nothing to follow.
UNLAUNCHED_STATES = frozenset({"failed", "admitted", "approved", "rejected", "starting"})
#: Origin kinds with a close (Conductor K4).
CLOSABLE_KINDS = frozenset({"action", "decision", "decision_record"})
#: Close states after which cleanup may run.
CLOSE_RESOLVED = frozenset(
    {"closed", "linked", "already_closed", "origin_dismissed", "origin_missing",
     "not_closable", "no_origin", "close_declined"}
)
#: Cleanup outcomes that end the attempt (anything else is retried).
_SESSION_FINAL = frozenset({"killed", "session_gone", "no_session"})
_WORKTREE_FINAL = frozenset(
    {"worktree_removed", "worktree_absent", "worktree_dirty", "worktree_unmerged",
     "out_of_root", "bad_name", "no_worktree", "worktree_kept_not_ours"}
)
#: Worktree outcomes after which the launch's live Work attempts abandon.
_WORKTREE_GONE = frozenset({"worktree_removed", "worktree_absent"})
SECURE_MODE = "safe"
#: Conductor K5, the wall-clock budget of one launch: a running agent with no
#: hook activity for this long, or running this long in all, raises one Door
#: item (Needs you). Nothing is stopped.
QUIET_LIMIT_SECONDS = 2 * 3600
TOTAL_LIMIT_SECONDS = 8 * 3600
_LIVE_STATES = frozenset({"launched", "registered"})

_SWEEP_LOCK = threading.Lock()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(text: Any) -> Optional[datetime]:
    try:
        stamp = datetime.fromisoformat(str(text or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)


def _config_control_mode() -> str:
    from ..services.agent_hand_service import _config_control_mode as read

    return read()


class FollowThroughObserver:
    """One sweep's follow-through over the launch ledger. Every collaborator
    is injectable; production builds them in :func:`default_follow_through`."""

    def __init__(
        self,
        db: Any,
        *,
        ledger: Any,
        registry: Any,
        receipts: Any,
        attempts: Any,
        control_mode: Callable[[], str] = _config_control_mode,
        tmux_runner: Any = None,
        git_runner: Any = None,
        gate_path: Optional[Path] = None,
        audit: Optional[Callable[..., int]] = None,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        self._db = db
        self._ledger = ledger
        self._registry = registry
        self._receipts = receipts
        self._attempts = attempts
        self._control_mode = control_mode
        self._tmux = tmux_runner
        self._git = git_runner
        self._gate_path = gate_path
        self._audit = audit
        self._clock = clock

    # ── the sweep ────────────────────────────────────────────────────

    def sweep(self, principal: Any) -> dict[str, Any]:
        """Refresh, close, clean up. Returns the bounded sweep sub-receipt."""
        with _SWEEP_LOCK:
            return self._sweep(principal)

    def _sweep(self, principal: Any) -> dict[str, Any]:
        launches = [r for r in self._ledger.list() if self._followed(r)]
        if launches and callable(getattr(self._registry, "reload", None)):
            # A launch registers its new worktree through its own registry
            # instance; read the file again so attribution can see it.
            self._registry.reload()
        receipt: dict[str, Any] = {
            "kind": "follow_through",
            "launches": len(launches),
            "sources": [],
            "closed": [],
            "confirm": [],
            "cleaned": [],
        }
        if not launches:
            return receipt
        try:
            receipt["budget"] = self._budgets(principal, launches)
        except Exception as exc:  # the budget never stops the follow-through
            log.error("launch budget check failed: %s", exc)
            receipt["budget"] = [{"error": str(exc)}]
        rows_by_source: dict[str, list[dict[str, Any]]] = {}
        for source_id in sorted({str(r.get("source_id") or "") for r in launches}):
            view = self._receipts.refresh(source_id)
            entry = next(
                (s for s in view.get("sources", []) if s.get("source_id") == source_id),
                None,
            )
            if entry is None:
                receipt["sources"].append({"source_id": source_id, "gh_state": "source_unknown"})
                continue
            receipt["sources"].append({
                "source_id": source_id,
                "gh_state": str(entry.get("gh_state") or "gh_failed"),
                "detail": str(entry.get("detail") or ""),
            })
            rows_by_source[source_id] = list(entry.get("prs") or [])
        mode = str(self._control_mode() or "yolo").lower()
        for launch in launches:
            try:
                self._follow(principal, launch, rows_by_source, mode, receipt)
            except Exception as exc:  # one launch never stops the others
                log.error("follow-through for %s failed: %s", launch.get("launch_id"), exc)
                receipt.setdefault("errors", []).append(str(launch.get("launch_id") or ""))
        return receipt

    @staticmethod
    def _followed(record: Mapping[str, Any]) -> bool:
        """Every launch that ran an agent, until its follow-through is
        resolved (``done``). The session's state does not end it: an agent
        that exits before the merge still has a PR to follow."""
        if str(record.get("state") or "") in UNLAUNCHED_STATES:
            return False
        if not record.get("attempt_id") or not record.get("worktree_id") or not record.get("source_id"):
            return False
        return not (record.get("follow_through") or {}).get("done")

    # ── the wall-clock budget (Conductor K5) ─────────────────────────

    def _budgets(self, principal: Any, launches: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Each running launch past its budget raises ONE Door item per
        limit: ``quiet`` (no hook activity for :data:`QUIET_LIMIT_SECONDS`)
        and ``total`` (running for :data:`TOTAL_LIMIT_SECONDS`). The agent is
        never stopped."""
        now = self._clock()
        activity = self._hook_activity()
        raised: list[dict[str, Any]] = []
        for launch in launches:
            if str(launch.get("state") or "") not in _LIVE_STATES:
                continue
            started = _parse(launch.get("launched_at"))
            if started is None or not self._session_alive(str(launch.get("session") or "")):
                continue
            last = max(
                [stamp for stamp in (started, activity.get(str(launch.get("session_key") or ""))) if stamp],
            )
            over = []
            if (now - started).total_seconds() >= TOTAL_LIMIT_SECONDS:
                over.append("total")
            if (now - last).total_seconds() >= QUIET_LIMIT_SECONDS:
                over.append("quiet")
            for kind in over:
                if self._budget_raised(launch, kind):
                    continue
                self._raise_budget(principal, launch, kind)
                raised.append({"launch_id": launch.get("launch_id"), "limit": kind})
        return raised

    @staticmethod
    def _hook_activity() -> dict[str, datetime]:
        """Session key -> the time of its last hook event (the registry)."""
        from .. import agent_context

        path = agent_context.AGENT_CONTEXT_FILE
        if not path.exists():
            return {}
        out: dict[str, datetime] = {}
        for session in agent_context.list_agent_sessions(state_path=path):
            stamp = _parse(getattr(session, "updated_at", None))
            if stamp is not None:
                out[f"{session.agent}:{session.session_id}"] = stamp
        return out

    def _session_alive(self, session: str) -> bool:
        from .. import coder_steering

        if not session:
            return False
        run = self._tmux or coder_steering._default_runner
        try:
            return run(["tmux", "has-session", "-t", session]).returncode == 0
        except Exception:
            return False

    def _budget_raised(self, launch: Mapping[str, Any], kind: str) -> bool:
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM action_items WHERE source_ref = ? LIMIT 1",
                (f"agent_budget:{launch['launch_id']}:{kind}",),
            ).fetchone()
        return row is not None

    def _raise_budget(self, principal: Any, launch: Mapping[str, Any], kind: str) -> None:
        from ..services.door_service import DoorService
        from ..services.follow_through_service import FollowThroughService

        origin = launch.get("origin_ref") or {}
        title = self._origin_title(str(origin.get("kind") or ""), str(origin.get("id") or "")) or str(
            (launch.get("story_ref") or {}).get("story_id") or launch.get("launch_id")
        )
        hours = (QUIET_LIMIT_SECONDS if kind == "quiet" else TOTAL_LIMIT_SECONDS) // 3600
        task = (
            f"Agent has no activity for {hours} h: {title}" if kind == "quiet"
            else f"Agent runs for more than {hours} h: {title}"
        )
        door = DoorService(FollowThroughService(self._db), None, None, None, db=self._db)  # type: ignore[arg-type]
        door.add_item(
            principal, task, source_type="agent_launch",
            source_ref=f"agent_budget:{launch['launch_id']}:{kind}",
        )

    # ── one launch ───────────────────────────────────────────────────

    def _follow(
        self, principal: Any, launch: dict[str, Any],
        rows_by_source: Mapping[str, list[dict[str, Any]]], mode: str,
        receipt: dict[str, Any],
    ) -> None:
        launch_id = str(launch["launch_id"])
        state = dict(launch.get("follow_through") or {})
        row, pr_state = self._select_pr(launch, state, rows_by_source.get(str(launch.get("source_id")), []))
        before = dict(state)
        state["pr_state"] = pr_state
        if row is not None:
            state["pr"] = {
                "url": row.get("url"), "number": row.get("number"),
                "state": row.get("state"), "review_decision": row.get("review_decision"),
            }
        if pr_state == "pr_closed_unmerged":
            # The PR was closed without a merge: nothing closes, nothing is
            # removed, and the launch is no longer followed.
            state["done"] = True
        if state != before:
            self._save(launch_id, state)
        if row is None or row.get("state") != "merged":
            return
        evidence = {
            "pr_url": str(row.get("url") or ""),
            "merged_sha": str(row.get("merged_sha") or row.get("head_sha") or ""),
            "merged_at": str(row.get("merged_at") or ""),
            "attempt_id": str(launch.get("attempt_id") or ""),
            "launch_id": launch_id,
        }
        if state.get("close") not in CLOSE_RESOLVED:
            close = self._close_or_confirm(principal, launch, state, evidence, mode)
            if close != state.get("close"):
                state["close"] = close
                state["evidence"] = evidence
                self._save(launch_id, state)
            if close in ("closed", "linked"):
                receipt["closed"].append({"launch_id": launch_id, "close": close})
            elif close == "awaiting_confirm":
                receipt["confirm"].append({"launch_id": launch_id})
        if state.get("close") not in CLOSE_RESOLVED:
            return
        cleanup = self._cleanup(launch, state.get("cleanup") or {}, str(row.get("head_sha") or ""))
        state["cleanup"] = cleanup
        state["done"] = (
            cleanup.get("session") in _SESSION_FINAL
            and cleanup.get("worktree") in _WORKTREE_FINAL
            and (cleanup.get("worktree") not in _WORKTREE_GONE or cleanup.get("attempts") == "reconciled")
        )
        self._save(launch_id, state)
        receipt["cleaned"].append({"launch_id": launch_id, **cleanup})

    def _select_pr(
        self, launch: Mapping[str, Any], state: Mapping[str, Any], rows: list[dict[str, Any]],
    ) -> tuple[Optional[dict[str, Any]], str]:
        """The launch's own PR and a named state.

        Once a PR is selected, its identity (number and URL) is kept on the
        launch and only that PR is read again. To be selected, a PR must
        have: the source's GitHub repository as its base repository, the
        same repository as its head (never a fork), the launch's branch as
        its head branch, and, when merged, a merge after the launch. A
        closed (unmerged) PR is never selected. One candidate is selected;
        several are ``pr_ambiguous`` and none is acted on."""
        kept = state.get("pr") or {}
        if kept.get("number") and kept.get("url"):
            row = next(
                (r for r in rows if r.get("number") == kept["number"] and r.get("url") == kept["url"]),
                None,
            )
            if row is None:
                return None, "pr_not_listed"
            if row.get("state") == "closed":
                return row, "pr_closed_unmerged"
            return row, "pr_" + str(row.get("state") or "open")
        repo = self._source_repo(str(launch.get("source_id") or ""))
        if not repo:
            return None, "repository_unknown"
        branch = self._launch_branch(launch)
        if not branch:
            return None, "branch_unknown"
        launched = _parse(launch.get("launched_at"))
        candidates = []
        for row in rows:
            if str(row.get("repo") or "").lower() != repo:
                continue
            if row.get("cross_repository") or str(row.get("head_repo") or repo).lower() != repo:
                continue
            if str(row.get("head_ref") or "") != branch or row.get("state") == "closed":
                continue
            if row.get("state") == "merged":
                merged = _parse(row.get("merged_at"))
                if merged is None or launched is None or merged <= launched:
                    continue
            candidates.append(row)
        if not candidates:
            return None, "no_pr"
        if len(candidates) > 1:
            return None, "pr_ambiguous"
        row = candidates[0]
        return row, "pr_" + str(row.get("state") or "open")

    def _source_repo(self, source_id: str) -> str:
        """``owner/name`` of the source's GitHub origin, lower case; "" when
        the clone has no GitHub origin."""
        from .registry import normalize_git_url
        from urllib.parse import urlsplit

        source = self._registry.get(source_id)
        if source is None or not source.primary_path:
            return ""
        run = self._git or _git_runner
        try:
            proc = run(["git", "-C", str(source.primary_path), "config", "--get", "remote.origin.url"])
        except Exception:
            return ""
        if proc.returncode != 0:
            return ""
        url = urlsplit(normalize_git_url(str(proc.stdout or "").strip()))
        parts = url.path.strip("/").split("/")
        if (url.hostname or "") != "github.com" or len(parts) != 2:
            return ""
        return "/".join(parts).lower()

    def _launch_branch(self, launch: Mapping[str, Any]) -> str:
        source = self._registry.get(str(launch.get("source_id") or ""))
        if source is None:
            return ""
        worktree = next(
            (wt for wt in source.worktrees if wt.worktree_id == launch.get("worktree_id")), None
        )
        return str(getattr(worktree, "branch", "") or "") if worktree is not None else ""

    def _save(self, launch_id: str, state: dict[str, Any]) -> None:
        self._ledger.update(launch_id, follow_through=dict(state))

    # ── the close ────────────────────────────────────────────────────

    def _close_or_confirm(
        self, principal: Any, launch: Mapping[str, Any], state: dict[str, Any],
        evidence: dict[str, str], mode: str,
    ) -> str:
        origin = launch.get("origin_ref") or {}
        kind, item_id = str(origin.get("kind") or ""), str(origin.get("id") or "")
        if not kind or not item_id:
            return "no_origin"
        if kind not in CLOSABLE_KINDS:
            return "not_closable"
        # Once the owner was asked, his answer decides, whatever the mode is
        # now: a dismissal is final for this launch.
        asked = self._confirm_status(launch)
        if asked is None and mode == SECURE_MODE:
            self._ask(principal, launch, state, kind, item_id)
            return "awaiting_confirm"
        if asked == "pending":
            return "awaiting_confirm"
        if asked == "dismissed":
            return "close_declined"
        # Confirmed, or Normal/YOLO with no question asked: close.
        return self._close(principal, kind, item_id, evidence)

    def _close(self, principal: Any, kind: str, item_id: str, evidence: dict[str, str]) -> str:
        if kind == "action":
            from ..services.follow_through_service import FollowThroughService

            try:
                result = FollowThroughService(self._db).complete(
                    principal, item_id, "done", {"evidence": evidence}
                )
            except ValueError as exc:
                text = str(exc)
                if text.startswith("commitment_closed"):
                    return "origin_dismissed"
                if "not found" in text.lower():
                    return "origin_missing"
                raise
            return "already_closed" if result.get("replayed") else "closed"
        from ..services.decision_record_service import DecisionRecordService
        from ..services.errors import NotFound

        records = DecisionRecordService(self._db)
        try:
            if kind == "decision_record":
                record_id = item_id
            else:
                found = records.records_for_source(principal, "meeting", item_id)
                record_id = found[0]["id"] if found else records.create_from_meeting(principal, item_id)["id"]
            records.link_work(principal, record_id, "pr", evidence["pr_url"])
        except (KeyError, NotFound):
            return "origin_missing"
        return "linked"

    def _confirm_status(self, launch: Mapping[str, Any]) -> Optional[str]:
        """The Secure question of this launch: None (never asked), or
        ``pending`` | ``done`` | ``dismissed``. Found by its source ref."""
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT status FROM action_items WHERE source_ref = ? ORDER BY created_at LIMIT 1",
                (f"agent_launch:{launch['launch_id']}",),
            ).fetchone()
        if row is None:
            return None
        status = str(row["status"] or "").lower()
        return status if status in ("done", "dismissed") else "pending"

    def _ask(
        self, principal: Any, launch: Mapping[str, Any], state: Mapping[str, Any],
        kind: str, item_id: str,
    ) -> None:
        """Secure: one Door item asks the owner to confirm the close."""
        from ..services.door_service import DoorService
        from ..services.follow_through_service import FollowThroughService

        title = self._origin_title(kind, item_id) or f"{kind}:{item_id}"
        number = ((state.get("pr") or {}).get("number")) or ""
        task = f"Merged: confirm close: {title}" + (f" (PR #{number})" if number else "")
        door = DoorService(FollowThroughService(self._db), None, None, None, db=self._db)  # type: ignore[arg-type]
        door.add_item(
            principal, task, source_type="agent_launch",
            source_ref=f"agent_launch:{launch['launch_id']}",
        )

    def _origin_title(self, kind: str, item_id: str) -> str:
        queries = {
            "action": "SELECT task FROM action_items WHERE id = ?",
            "decision": "SELECT text FROM decisions WHERE id = ?",
            "decision_record": "SELECT decision_text FROM decision_records WHERE id = ?",
        }
        try:
            with self._db._connection() as conn:
                row = conn.execute(queries[kind], (item_id,)).fetchone()
        except Exception:
            return ""
        return " ".join(str(row[0] or "").split())[:200] if row else ""

    # ── cleanup ──────────────────────────────────────────────────────

    def _cleanup(self, launch: Mapping[str, Any], done: Mapping[str, Any], merged_head: str) -> dict[str, Any]:
        result = dict(done)
        if result.get("session") not in _SESSION_FINAL:
            result["session"] = self._end_session(launch)
        path = self._worktree_path(launch)
        if result.get("worktree") not in _WORKTREE_FINAL:
            if self._owns_worktree(launch):
                result["worktree"] = self._remove_worktree(launch, path, merged_head)
            else:
                # A worktree the launch did not create is the owner's: kept.
                result["worktree"] = "worktree_kept_not_ours"
        if result["worktree"] in _WORKTREE_GONE and result.get("attempts") != "reconciled":
            # Idempotent, and before the launch can read as done: a sweep
            # that stopped after the removal reconciles here on the next one.
            self._attempts.mark_worktree_removed(str(launch.get("worktree_id") or ""))
            result["attempts"] = "reconciled"
        if result.get("session") in _SESSION_FINAL and result.get("gate") not in ("released", "not_armed"):
            # No agent runs there any more: the launch's own hold goes.
            result["gate"] = self._release_gate(path, str(launch.get("session") or ""))
        return result

    @staticmethod
    def _owns_worktree(launch: Mapping[str, Any]) -> bool:
        """The launch created its worktree: its worktree.create command ran
        and the launch did not fail at that stage."""
        created = (launch.get("commands") or {}).get("worktree_create")
        failed_stage = (launch.get("failure") or {}).get("stage")
        return bool(created) and failed_stage != "worktree_create"

    def _end_session(self, launch: Mapping[str, Any]) -> str:
        from .. import coder_factory, coder_steering

        session = str(launch.get("session") or "")
        pane = str((launch.get("target") or {}).get("pane_id") or "")
        if not session or not pane:
            return "no_session"
        armed = coder_steering.arm(session, pane, runner=self._tmux)
        if armed.get("status") == "pane_gone":
            return "session_gone"
        if armed.get("status") != "armed":
            return str(armed.get("status") or "error")
        kwargs: dict[str, Any] = {"runner": self._tmux}
        if self._audit is not None:
            kwargs["audit"] = self._audit
        killed = coder_factory.kill(
            session, current_target=pane, scope="session", agent="factory", **kwargs
        )
        status = str(killed.get("status") or "error")
        return "session_gone" if status == "pane_gone" else status

    def _worktree_path(self, launch: Mapping[str, Any]) -> Optional[Path]:
        source = self._registry.get(str(launch.get("source_id") or ""))
        if source is None:
            return None
        worktree = next(
            (wt for wt in source.worktrees if wt.worktree_id == launch.get("worktree_id")), None
        )
        if worktree is None:
            return None
        return Path(worktree.path).expanduser().resolve()

    def _remove_worktree(self, launch: Mapping[str, Any], path: Optional[Path], merged_head: str) -> str:
        from .factory_launch import execute_worktree_remove

        source = self._registry.get(str(launch.get("source_id") or ""))
        if path is None or source is None or not source.primary_path:
            return "no_worktree"
        if path == Path(source.primary_path).expanduser().resolve():
            # The source's own checkout is never removed.
            return "out_of_root"
        kwargs: dict[str, Any] = {}
        if self._git is not None:
            kwargs["runner"] = self._git
        if self._audit is not None:
            kwargs["audit"] = self._audit
        result = execute_worktree_remove(
            {
                "name": path.name,
                "repo_path": str(source.primary_path),
                "path": str(path),
                "merged_head": merged_head,
            },
            **kwargs,
        )
        return str(result.get("status") or "error")

    def _release_gate(self, path: Optional[Path], session: str) -> str:
        from .. import coder_gate

        if path is None:
            return "not_armed"
        key = str(path)

        def release(config: Any) -> bool:
            if key not in config.armed_paths:
                return False
            config.armed_paths = [p for p in config.armed_paths if p != key]
            config.repos.pop(key, None)
            return True

        released = coder_gate.update_gate_config(release, self._gate_path)
        if not released:
            return "not_armed"
        try:
            self._db.steering.record(
                session_key=f"factory:gate:{path.name}", agent="factory", pane_id=None,
                text=f"gate {path.name}", grounding=[], submit=False,
                outcome="gate_released", detail="the PR merged; the agent session ended",
            )
        except Exception as exc:  # the audit row never blocks the release
            log.warning("gate release audit not written (%s)", exc)
        return "released"


def _git_runner(argv: list[str]) -> Any:
    """The launch engine's own git read (one ledgered subprocess site)."""
    from .factory_launch import _default_git_runner

    return _default_git_runner(argv)


def default_follow_through(db: Any) -> FollowThroughObserver:
    """The production observer: the launch ledger, the registry, the shared
    PR receipts cache and the Work attempts of this hub."""
    from . import DeliveryRegistry
    from .attempts import WorkAttemptService, resolver_from_registry
    from .factory_launch import LaunchLedger
    from .pr_receipts import default_pr_receipts

    receipts = default_pr_receipts()
    registry = receipts._registry if hasattr(receipts, "_registry") else DeliveryRegistry()
    return FollowThroughObserver(
        db,
        ledger=LaunchLedger(),
        registry=registry,
        receipts=receipts,
        attempts=WorkAttemptService(db.work_attempts, resolver=resolver_from_registry(registry)),
    )


__all__ = [
    "CLOSABLE_KINDS",
    "UNLAUNCHED_STATES",
    "FollowThroughObserver",
    "default_follow_through",
]
