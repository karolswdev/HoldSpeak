"""The launch lane: everything the Conductor lane face shows of one launched
agent (PHILO-14 C0, backend only).

One read join, nothing written. Its parts and where each comes from:

- ``launch``: the launch ledger (``factory_launch.LaunchLedger``) and the
  launch's worktree path from the Delivery registry (``~`` for the home
  folder, as the launch sheet shows paths).
- ``follow_through``: the ledger's ``follow_through`` (the Heartbeat writes
  the PR with its ``ci`` rollup and ``checks``, the close, the cleanup).
- ``wait``: the bound session (``agent_sessions.json``) when it is blocked,
  with HoldSpeak's drafted answer (``agent_responder.AnswerStore``).
- ``events``: the session's event log (``agent_context.event_log``), paged.
- ``gated``: the gate proposals of the session, oldest first.
- ``answers``: the steering audit rows of the session key and of the
  launch's tmux session (the brief is typed under the tmux name).
- ``attempt_events``: the Work attempt's state changes.
- ``commits`` / ``files`` / ``worktree``: :func:`worktree_facts`, read in the
  worktree on request, cached for :data:`FACTS_TTL_SECONDS`.
- ``usage``: ``session_usage`` (filled only for a repository the gate holds).

A part that cannot be read says so (``{"not_read": "<reason>"}`` or
``None``); it never fails the whole lane.
"""
from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("services.launch_lane")

#: Worktree facts are cached this long per launch (read on request, no timer).
FACTS_TTL_SECONDS = 5.0
#: Each git read gives up after this long.
GIT_TIMEOUT_SECONDS = 5.0
#: Commits kept in one read.
MAX_COMMITS = 200
#: Changed files kept in one read.
MAX_FILES = 500
#: The base branches tried, in order, after ``origin/HEAD``.
BASE_CANDIDATES = ("origin/main", "origin/master", "main", "master")

Runner = Callable[[list[str]], "subprocess.CompletedProcess[str]"]

_facts_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_facts_lock = threading.Lock()


def _default_runner(argv: list[str]) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(argv, capture_output=True, text=True, timeout=GIT_TIMEOUT_SECONDS)


def _git(run: Runner, path: str, *args: str) -> "subprocess.CompletedProcess[str]":
    return run(["git", "-C", path, *args])


def _base_ref(run: Runner, path: str) -> Optional[str]:
    head = _git(run, path, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    candidates = ([head.stdout.strip()] if head.returncode == 0 and head.stdout.strip() else []) + list(
        BASE_CANDIDATES
    )
    for ref in candidates:
        if _git(run, path, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode == 0:
            return ref
    return None


def _read_facts(path: str, run: Runner) -> dict[str, Any]:
    if not path:
        return {"not_read": "the launch has no worktree"}
    target = Path(path)
    if not target.is_dir():
        return {"not_read": "the worktree is gone"}
    try:
        resolved = str(target.resolve())
    except OSError as exc:
        return {"not_read": f"the worktree path does not resolve: {exc.strerror or exc}"}
    # Never read outside the launch's worktree: git walks up to a parent
    # repository when the folder is not a worktree itself.
    top = _git(run, resolved, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return {"not_read": "the worktree is not a git worktree"}
    try:
        same = Path(top.stdout.strip()).resolve() == Path(resolved)
    except OSError:
        same = False
    if not same:
        return {"not_read": "the worktree folder is not the top of a git worktree"}
    base = _base_ref(run, resolved)
    if base is None:
        return {"not_read": "no base branch (origin/HEAD, main or master) in the worktree"}
    head = _git(run, resolved, "rev-parse", "--abbrev-ref", "HEAD")
    log_out = _git(
        run, resolved, "log", f"--max-count={MAX_COMMITS}", "--format=%h%x09%at%x09%s", f"{base}..HEAD",
    )
    if log_out.returncode != 0:
        return {"not_read": f"git log failed: {(log_out.stderr or '').strip()[:200]}"}
    commits = []
    for line in (log_out.stdout or "").splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            try:
                at = int(parts[1])
            except ValueError:
                at = None
            commits.append({"sha": parts[0], "at": at, "subject": parts[2]})
    diff = _git(run, resolved, "diff", "--name-status", f"{base}...HEAD")
    if diff.returncode != 0:
        return {"not_read": f"git diff failed: {(diff.stderr or '').strip()[:200]}"}
    files = []
    for line in (diff.stdout or "").splitlines()[:MAX_FILES]:
        parts = line.split("\t")
        if len(parts) >= 2:
            files.append({"status": parts[0], "path": parts[-1], **({"from": parts[1]} if len(parts) == 3 else {})})
    status = _git(run, resolved, "status", "--porcelain")
    uncommitted: Any
    if status.returncode != 0:
        uncommitted = {"not_read": "git status failed"}
    else:
        staged = modified = untracked = 0
        for line in (status.stdout or "").splitlines():
            if line.startswith("??"):
                untracked += 1
                continue
            if line[:1].strip():
                staged += 1
            if line[1:2].strip():
                modified += 1
        uncommitted = {"staged": staged, "modified": modified, "untracked": untracked}
    return {
        "base": base,
        "branch": head.stdout.strip() if head.returncode == 0 else None,
        "commits": commits,
        "files": files,
        "uncommitted": uncommitted,
    }


def worktree_facts(
    launch_id: str, path: str, *, runner: Optional[Runner] = None,
    clock: Callable[[], float] = time.monotonic, ttl: float = FACTS_TTL_SECONDS,
) -> dict[str, Any]:
    """Commits on the branch (``git log <base>..HEAD``), the files they change
    (``git diff --name-status <base>...HEAD``) and the uncommitted counts
    (``git status --porcelain``), read in the launch's worktree only.

    Cached per launch for ``ttl`` seconds; read on request, never on a timer.
    A failure is ``{"not_read": "<reason>"}``."""
    now = clock()
    key = f"{launch_id}\0{path}"
    with _facts_lock:
        hit = _facts_cache.get(key)
        if hit is not None and now - hit[0] < ttl:
            return dict(hit[1])
    try:
        facts = _read_facts(path, runner or _default_runner)
    except (OSError, subprocess.TimeoutExpired) as exc:
        facts = {"not_read": f"git did not answer: {type(exc).__name__}"}
    facts["read_at"] = time.time()
    with _facts_lock:
        _facts_cache[key] = (now, facts)
        for stale in [k for k, (at, _) in _facts_cache.items() if now - at >= ttl * 4]:
            _facts_cache.pop(stale, None)
    return dict(facts)


def clear_facts_cache() -> None:
    with _facts_lock:
        _facts_cache.clear()


# ── the lane ─────────────────────────────────────────────────────────


def _worktree_path(reads: Any, record: Mapping[str, Any]) -> str:
    try:
        source = reads.registry().get(str(record.get("source_id") or ""))
    except Exception:
        return ""
    if source is None:
        return ""
    worktree = next(
        (wt for wt in getattr(source, "worktrees", []) if wt.worktree_id == record.get("worktree_id")), None
    )
    return str(getattr(worktree, "path", "") or "")


def _home_as_tilde(path: str) -> Optional[str]:
    if not path:
        return None
    for home in dict.fromkeys((str(Path.home()), str(Path.home().resolve()))):
        if path == home or path.startswith(home + "/"):
            return "~" + path[len(home):]
    return path


def _session_key(db: Any, record: Mapping[str, Any]) -> str:
    attempt_id = str(record.get("attempt_id") or "")
    if not attempt_id:
        return ""
    try:
        attempt = db.work_attempts.get(attempt_id)
    except Exception:
        return ""
    return str(getattr(attempt, "session_id", "") or "")


def _find_session(sessions: Any, key: str) -> Optional[dict[str, Any]]:
    for raw in sessions:
        session = raw.to_dict() if hasattr(raw, "to_dict") else dict(raw or {})
        if f"{session.get('agent')}:{session.get('session_id')}" == key:
            return session
    return None


def _wait(session: Optional[Mapping[str, Any]], answers: Any) -> Optional[dict[str, Any]]:
    from ..agent_context.models import is_blocked, wait_kind
    from .agent_responder import annotate_sessions
    from .needs_you_membership import TO_ANSWER, TO_APPROVE

    if session is None or not is_blocked(session):
        return None
    annotated = annotate_sessions([session], store=answers)[0]
    answer = annotated.get("answer") if isinstance(annotated.get("answer"), dict) else {}
    approve = wait_kind(session) == "approve"
    draft = None
    if answer.get("state") in ("escalated", "drafted") and (answer.get("draft") or answer.get("reason")):
        draft = {
            "verdict": str(answer.get("verdict") or ""),
            "reason": str(answer.get("reason") or ""),
            "text": str(answer.get("draft") or ""),
        }
    return {
        "question": session.get("question"),
        "kind": TO_APPROVE if approve else TO_ANSWER,
        "wait_kind": "approve" if approve else "answer",
        "started": session.get("wait_started_at") or session.get("updated_at"),
        "wait_id": session.get("wait_id"),
        "answer_state": answer.get("state"),
        "draft": draft,
    }


def _session_view(session: Optional[Mapping[str, Any]]) -> Optional[dict[str, Any]]:
    if session is None:
        return None
    from ..agent_context import AgentSession, effective_state

    try:
        state = effective_state(AgentSession.from_mapping(dict(session)))
    except Exception:
        state = session.get("lifecycle")
    return {
        "state": state,
        "lifecycle": session.get("lifecycle"),
        "updated_at": session.get("updated_at"),
        "created_at": session.get("created_at"),
        "event_count": session.get("event_count"),
        "model": session.get("model"),
        "last_tool_name": session.get("last_tool_name"),
    }


def _part(name: str, read: Callable[[], Any], fallback: Any) -> Any:
    try:
        return read()
    except Exception as exc:
        log.warning(f"launch lane: {name} unread: {exc}")
        return fallback


def launch_lane(
    launch_id: str,
    *,
    db: Any,
    reads: Any = None,
    sessions: Any = None,
    answers: Any = None,
    after: int = 0,
    limit: int = 200,
    runner: Optional[Runner] = None,
) -> Optional[dict[str, Any]]:
    """One launch's lane, or ``None`` for an unknown launch."""
    from ..agent_context import event_log

    if reads is None:
        from .agent_hand_preview import LaunchReads

        reads = LaunchReads()
    record = reads.launcher()._ledger.get(launch_id)
    if not record:
        return None
    if sessions is None:
        from ..agent_context import list_agent_sessions

        sessions = _part("sessions", list_agent_sessions, [])
    path = _worktree_path(reads, record)
    key = _session_key(db, record)
    session = _find_session(sessions, key) if key else None
    follow = dict(record.get("follow_through") or {})
    pr = follow.get("pr") or None
    origin = record.get("origin_ref") or None
    profile = str(record.get("profile_id") or "")
    limit = max(1, min(int(limit), 1000))

    def events() -> list[dict[str, Any]]:
        with db._connection() as conn:
            return event_log.list_events(conn, key, after=after, limit=limit)

    def gated() -> list[dict[str, Any]]:
        return [
            {
                "id": p.id, "tool": p.tool, "args_head": p.args_head, "state": p.state,
                "created_at": p.created_at, "decided_by": p.decided_by, "decided_at": p.decided_at,
                "reason": p.reason, "policy": dict(p.policy_snapshot),
            }
            for p in db.gate.proposals_for_session(key)
        ]

    def answers_typed() -> list[dict[str, Any]]:
        rows: dict[int, Any] = {}
        for k in dict.fromkeys(k for k in (key, str(record.get("session") or "")) if k):
            for entry in db.steering.list(session_key=k, limit=500):
                rows[entry.id] = entry
        return [
            {
                "id": e.id, "ts": e.ts, "session_key": e.session_key, "outcome": e.outcome,
                "text_head": e.text_head, "submit": e.submit, "detail": e.detail,
            }
            for _, e in sorted(rows.items())
        ]

    event_rows = _part("events", events, []) if key else []
    return {
        "launch": {
            "launch_id": record.get("launch_id"),
            "state": record.get("state"),
            "agent": "codex" if profile.lower().startswith("codex") else "claude",
            "profile_id": profile or None,
            "origin_ref": origin,
            "story_ref": record.get("story_ref"),
            "branch": record.get("branch") or None,
            "worktree_path": _home_as_tilde(path),
            "launched_at": record.get("launched_at"),
            "control_mode": record.get("control_mode"),
            "gate": record.get("gate"),
            "instruction_state": record.get("instruction_state"),
            "brief_text": record.get("brief_text"),
            "failure": record.get("failure"),
            "session_key": key or None,
            "tmux_session": record.get("session"),
            "attempt_id": record.get("attempt_id"),
        },
        "session": _session_view(session),
        "follow_through": {
            "pr": {
                "number": pr.get("number"), "url": pr.get("url"), "state": pr.get("state"),
                "review_decision": pr.get("review_decision"), "ci": pr.get("ci"),
                "checks": list(pr.get("checks") or []),
            } if isinstance(pr, Mapping) else None,
            "pr_state": follow.get("pr_state"),
            "merged": (follow.get("evidence") or {}) or None,
            "close": follow.get("close"),
            "cleanup": follow.get("cleanup"),
            "done": bool(follow.get("done")),
        },
        "wait": _part("wait", lambda: _wait(session, answers), None),
        "events": event_rows,
        "events_next_after": event_rows[-1]["id"] if len(event_rows) == limit else None,
        "gated": _part("gated", gated, []) if key else [],
        "answers": _part("answers", answers_typed, []),
        "attempt_events": _part(
            "attempt events", lambda: db.work_attempts.events(str(record.get("attempt_id"))), []
        ) if record.get("attempt_id") else [],
        "worktree": worktree_facts(launch_id, path, runner=runner),
        "usage": _part("usage", lambda: db.gate.usage_for(key), None) if key else None,
    }


__all__ = ["FACTS_TTL_SECONDS", "clear_facts_cache", "launch_lane", "worktree_facts"]
