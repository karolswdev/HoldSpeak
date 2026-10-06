"""Follow through: the Heartbeat follows an agent launch's PR to its merge.

docs/internal/CONDUCTOR.md, step 6 (lane K4). On each Heartbeat sweep:

1. **PR refresh.** Every Delivery Source with a live or recent agent launch
   gets one batched ``gh pr list`` (``PrReceiptsService.refresh``). A
   missing or unauthenticated ``gh`` is a named state on the sweep receipt
   (``gh_missing``, ``gh_unauthenticated``), never a silent skip.
2. **Close the origin on merge.** A PR with EXACT attribution (its branch or
   head SHA is the launch's worktree) that GitHub reports ``merged`` closes
   the item the launch came from (``origin_ref``):

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
   evidence; dismissed, the origin stays open. Normal and YOLO close at once.
3. **Clean up** after the merge and the close: the agent's tmux session is
   ended (``coder_factory.kill``, audited), the worktree is removed only if
   it is clean and merged (``execute_worktree_remove``, refusals by name),
   its live Work attempts abandon (``mark_worktree_removed``), and the
   launch's own armed gate path is released under the gate file lock.

Idempotent across sweeps and restarts: the state lives on the durable launch
record (``follow_through``), the close is a replay when repeated, and a
module lock keeps two sweeps from acting at once.
"""
from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("delivery.follow_through")

#: Launch states whose agent may still open or land a PR.
FOLLOWED_STATES = frozenset({"launched", "registered", "failed_to_register"})
#: How long after its launch a PR is still followed.
FOLLOW_DAYS = 30
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
     "out_of_root", "bad_name", "no_worktree"}
)
SECURE_MODE = "safe"

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

    def _followed(self, record: Mapping[str, Any]) -> bool:
        if str(record.get("state") or "") not in FOLLOWED_STATES:
            return False
        if not record.get("worktree_id") or not record.get("source_id"):
            return False
        if (record.get("follow_through") or {}).get("done"):
            return False
        launched = _parse(record.get("launched_at"))
        return launched is None or self._clock() - launched <= timedelta(days=FOLLOW_DAYS)

    # ── one launch ───────────────────────────────────────────────────

    def _follow(
        self, principal: Any, launch: dict[str, Any],
        rows_by_source: Mapping[str, list[dict[str, Any]]], mode: str,
        receipt: dict[str, Any],
    ) -> None:
        launch_id = str(launch["launch_id"])
        state = dict(launch.get("follow_through") or {})
        row = self._exact_row(launch, rows_by_source.get(str(launch.get("source_id")), []))
        if row is not None:
            pr = {
                "url": row.get("url"), "number": row.get("number"),
                "state": row.get("state"), "review_decision": row.get("review_decision"),
            }
            if state.get("pr") != pr:
                state["pr"] = pr
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
        )
        self._save(launch_id, state)
        receipt["cleaned"].append({"launch_id": launch_id, **cleanup})

    @staticmethod
    def _exact_row(launch: Mapping[str, Any], rows: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
        """The launch's PR: exact attribution to its own worktree. A merged
        row wins over an open one; then the newest number."""
        matches = [
            r for r in rows
            if r.get("attribution") == "exact"
            and str(r.get("worktree_id") or "") == str(launch.get("worktree_id") or "")
        ]
        if not matches:
            return None
        return sorted(
            matches, key=lambda r: (r.get("state") != "merged", -int(r.get("number") or 0))
        )[0]

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
        if mode == SECURE_MODE:
            confirm = self._confirm_item(principal, launch, state, kind, item_id)
            if confirm == "pending":
                return "awaiting_confirm"
            if confirm == "dismissed":
                return "close_declined"
            # done: the owner confirmed; close with the same evidence.
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

    def _confirm_item(
        self, principal: Any, launch: Mapping[str, Any], state: dict[str, Any],
        kind: str, item_id: str,
    ) -> str:
        """Secure: one Door item asks the owner. ``pending`` | ``done`` |
        ``dismissed``. Found by its source ref, so a restart adds no second."""
        source_ref = f"agent_launch:{launch['launch_id']}"
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT id, status FROM action_items WHERE source_ref = ? ORDER BY created_at LIMIT 1",
                (source_ref,),
            ).fetchone()
        if row is None:
            from ..services.door_service import DoorService
            from ..services.follow_through_service import FollowThroughService

            title = self._origin_title(kind, item_id) or f"{kind}:{item_id}"
            number = ((state.get("pr") or {}).get("number")) or ""
            task = f"Merged: confirm close: {title}" + (f" (PR #{number})" if number else "")
            door = DoorService(FollowThroughService(self._db), None, None, None, db=self._db)  # type: ignore[arg-type]
            door.add_item(principal, task, source_type="agent_launch", source_ref=source_ref)
            return "pending"
        status = str(row["status"] or "").lower()
        if status == "done":
            return "done"
        if status == "dismissed":
            return "dismissed"
        return "pending"

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
            result["worktree"] = self._remove_worktree(launch, path, merged_head)
            if result["worktree"] == "worktree_removed":
                self._attempts.mark_worktree_removed(str(launch.get("worktree_id") or ""))
        if result.get("session") in _SESSION_FINAL and result.get("gate") not in ("released", "not_armed"):
            # No agent runs there any more: the launch's own hold goes.
            result["gate"] = self._release_gate(path, str(launch.get("session") or ""))
        return result

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
    "FOLLOWED_STATES",
    "FollowThroughObserver",
    "default_follow_through",
]
