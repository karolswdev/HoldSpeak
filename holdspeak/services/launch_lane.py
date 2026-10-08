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

A part that cannot be read says so (``{"not_read": "<reason>"}``); it never
fails the whole lane, and a failed read is never served as an empty list.
Every text the lane serves is secret-redacted (``_scrub``). The events are
drained from the hook's spool before they are read (``event_log``).
"""
from __future__ import annotations

import subprocess
import threading
import time
from datetime import datetime, timezone
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


def _launch_proposals(db: Any, key: str, launch_id: str) -> list[Any]:
    """The gate proposals of one launch, oldest first: those of its
    registered session key and those of its launch-bound credential
    (``agent:launch:<launch_id>``, Conductor R3: the hook of a launched agent
    proposes under that identity, so a read by the session key alone found
    none of them, PHILO-15 15, B45)."""
    from ..coder_factory import launch_identity

    keys = [k for k in (key, launch_identity(launch_id) if launch_id else "") if k]
    found: dict[str, Any] = {}
    for k in dict.fromkeys(keys):
        for proposal in db.gate.proposals_for_session(k):
            found[proposal.id] = proposal
    return sorted(found.values(), key=lambda p: (float(p.created_at or 0), p.id))


def _find_session(sessions: Any, key: str) -> Optional[dict[str, Any]]:
    for raw in sessions:
        session = raw.to_dict() if hasattr(raw, "to_dict") else dict(raw or {})
        if f"{session.get('agent')}:{session.get('session_id')}" == key:
            return session
    return None


def _wait(
    session: Optional[Mapping[str, Any]], answers: Any, *, work_done: bool = False,
) -> Optional[dict[str, Any]]:
    """The session's current wait as the owner sees it, or ``None``.

    It honors the responder's record of the wait (``annotate_sessions``),
    as Needs you does: a wait HoldSpeak answered is not a wait (the answer
    is in ``answers``); a wait HoldSpeak is still deciding (fresh) reads
    ``DECIDING``, not TO ANSWER; a stale decision goes to the owner."""
    from ..agent_context.models import is_blocked, turn_end, wait_kind
    from .agent_responder import ANSWERED, DECIDING, TURN_STATES, annotate_sessions
    from .needs_you_membership import TO_ANSWER, TO_APPROVE

    if session is None or not is_blocked(session):
        return None
    annotated = annotate_sessions([session], store=answers)[0]
    answer = annotated.get("answer") if isinstance(annotated.get("answer"), dict) else {}
    state = answer.get("state")
    if state == ANSWERED:
        return None
    if state in TURN_STATES:
        # PHILO-15 15: the agent reported its work done (or stopped with no
        # question): the lane says DONE / IDLE with its last words; it is
        # not a wait for the owner (no Needs you row).
        return {
            "question": session.get("question"),
            "kind": str(state).upper(),
            "wait_kind": state,
            "turn_end": state,
            "started": session.get("wait_started_at") or session.get("updated_at"),
            "wait_id": session.get("wait_id"),
            "answer_state": state,
            "draft": None,
        }
    deciding = state == DECIDING and bool(answer.get("hidden"))
    if answer.get("hidden") and not deciding:
        return None
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
        "kind": DECIDING_KIND if deciding else (TO_APPROVE if approve else TO_ANSWER),
        "wait_kind": "deciding" if deciding else ("approve" if approve else "answer"),
        # PHILO-15 B48: ``asks`` only when a real question waits; a turn end
        # with no question is ``idle``, or ``done`` once the PR is open.
        "turn_end": turn_end(session, work_done=work_done),
        "started": session.get("wait_started_at") or session.get("updated_at"),
        "wait_id": session.get("wait_id"),
        "answer_state": state,
        "draft": draft,
    }


#: The kind of a wait HoldSpeak is still deciding (YOLO): not the owner's yet.
DECIDING_KIND = "DECIDING"


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


def _queued_view(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    from .launch_rebrief import _queue

    return [
        {"id": q.get("id"), "text": q.get("text"), "at": q.get("at"),
         "approved_at": (q.get("approval") or {}).get("at")}
        for q in _queue(record)
    ]


def _not_read(name: str, exc: BaseException) -> dict[str, str]:
    # The reason is redacted WHOLE before it is cut (a cut secret head would
    # pass the redactor) and before it is logged.
    from ..memory.defense import redact

    reason = redact(str(exc))
    log.warning(f"launch lane: {name} unread: {reason}")
    return {"not_read": f"{name}: {type(exc).__name__}: {reason[:200]}"}


def _part(name: str, read: Callable[[], Any]) -> Any:
    """A part of the lane, or ``{"not_read": reason}`` when its read failed
    (never an empty list in place of a failed read)."""
    try:
        return read()
    except Exception as exc:
        return _not_read(name, exc)


def _scrub(value: Any) -> Any:
    """Every text the lane serves, secret-redacted (``memory.defense``).

    Rows written before the redaction at the source, and texts no source
    redacts (commit subjects, file names, the brief, a draft), pass here."""
    from ..memory.defense import redact

    if isinstance(value, str):
        return redact(value)
    if isinstance(value, Mapping):
        return {k: _scrub(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scrub(v) for v in value]
    return value


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
    spool_dir: Optional[Path] = None,
    control: Optional[Callable[[str], Any]] = None,
) -> Optional[dict[str, Any]]:
    """One launch's lane, or ``None`` for an unknown launch.

    Each collection is a list, or ``{"not_read": reason}`` when its read
    failed. An empty list means the read worked and found nothing (or no
    session is bound to the launch yet: ``launch.session_key`` is null)."""
    from ..agent_context import event_log

    if reads is None:
        from .agent_hand_preview import LaunchReads

        reads = LaunchReads()
    record = reads.launcher()._ledger.get(launch_id)
    if not record:
        return None
    if sessions is None:
        from ..agent_context import list_agent_sessions

        sessions = _part("sessions", list_agent_sessions)
    sessions_failed = isinstance(sessions, Mapping) and "not_read" in sessions
    path = _worktree_path(reads, record)
    key = _session_key(db, record)
    session = _find_session(sessions, key) if key and not sessions_failed else None
    follow = dict(record.get("follow_through") or {})
    pr = follow.get("pr") or None
    origin = record.get("origin_ref") or None
    profile = str(record.get("profile_id") or "")
    limit = max(1, min(int(limit), 1000))

    def events() -> list[dict[str, Any]]:
        # The hook spools; the lane read drains the spool first.
        try:
            event_log.drain_spool(db._connection, spool_dir=spool_dir)
        except Exception as exc:
            log.warning(f"launch lane: spool not drained: {exc}")
        with db._connection() as conn:
            return event_log.list_events(conn, key, after=after, limit=limit)

    def gated() -> list[dict[str, Any]]:
        return [
            {
                "id": p.id, "tool": p.tool, "args_head": p.args_head, "state": p.state,
                "created_at": p.created_at, "decided_by": p.decided_by, "decided_at": p.decided_at,
                "reason": p.reason, "policy": dict(p.policy_snapshot),
                # PHILO-14 A5: the shown command, and whether it is whole;
                # PHILO-15 15: why it waits (``hold_reason``).
                **p.shown(),
                # PHILO-15 15 (B45): the Control mode did not pass it at once
                # (a call the mode passed is a run, not a hold).
                "was_held": (p.policy_snapshot or {}).get("outcome") != "allowed",
            }
            for p in _launch_proposals(db, key, str(record.get("launch_id") or launch_id))
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

    event_rows = _part("events", events) if key else []
    if sessions_failed:
        session_part: Any = sessions
        wait_part: Any = sessions
    else:
        session_part = _part("session", lambda: _session_view(session))
        work_done = isinstance(pr, Mapping) and pr.get("number") is not None
        wait_part = _part("wait", lambda: _wait(session, answers, work_done=work_done))
    lane = {
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
            # PHILO-15 B42: when the brief reached the agent (its delivery
            # receipt), not when the launch began.
            "brief_sent_at": record.get("brief_sent_at"),
            # PHILO-15 B46: Re-briefs sent mid-turn wait for turn ends (a
            # small FIFO, oldest first); every press ends in one receipt
            # (SENT / SUPERSEDED / EXPIRED) with its approval: who pressed,
            # when, and the delivery's command id (Astra r2 on #996).
            "queued_rebriefs": _queued_view(record),
            "queued_rebrief": (_queued_view(record) or [None])[0],
            "rebriefs": [dict(r) for r in (record.get("rebriefs") or []) if isinstance(r, Mapping)],
            "control_mode": record.get("control_mode"),
            "gate": record.get("gate"),
            "instruction_state": record.get("instruction_state"),
            "brief_text": record.get("brief_text"),
            "stopped": record.get("stopped") or None,
            "failure": record.get("failure"),
            "session_key": key or None,
            "tmux_session": record.get("session"),
            "attempt_id": record.get("attempt_id"),
        },
        "session": session_part,
        "follow_through": {
            "pr": {
                "number": pr.get("number"), "url": pr.get("url"), "state": pr.get("state"),
                # PHILO-15 B50: the PR's own title (the item is the lane's).
                "title": pr.get("title") or None,
                "review_decision": pr.get("review_decision"), "ci": pr.get("ci"),
                "checks": list(pr.get("checks") or []),
            } if isinstance(pr, Mapping) else None,
            "pr_state": follow.get("pr_state"),
            "merged": (follow.get("evidence") or {}) or None,
            "close": follow.get("close"),
            "cleanup": follow.get("cleanup"),
            "done": bool(follow.get("done")),
        },
        "wait": wait_part,
        "events": event_rows,
        "events_next_after": (
            event_rows[-1]["id"] if isinstance(event_rows, list) and len(event_rows) == limit else None
        ),
        # PHILO-15 15 (B45): a launch's hook authenticates with the
        # launch-bound credential, so its holds are read by the launch id
        # too, also before the session registers.
        "gated": _part("gated", gated),
        "answers": _part("answers", answers_typed),
        "attempt_events": _part(
            "attempt events", lambda: db.work_attempts.events(str(record.get("attempt_id")))
        ) if record.get("attempt_id") else [],
        "worktree": worktree_facts(launch_id, path, runner=runner),
        "usage": _part("usage", lambda: db.gate.usage_for(key)) if key else None,
    }
    if control is not None:
        # PHILO-14 C2: how the lane may act now; scrubbed with the rest.
        lane["control"] = _part("control", lambda: control(key))
    return _scrub(lane)


def _launch_for_session(ledger: Any, db: Any, key: str) -> Optional[dict[str, Any]]:
    """The newest launch bound to session ``key`` (its record names the key,
    or its Work attempt does)."""
    for record in reversed(ledger.list()):
        if str(record.get("session_key") or "") == key:
            return record
        attempt_id = str(record.get("attempt_id") or "")
        if not attempt_id:
            continue
        try:
            attempt = db.work_attempts.get(attempt_id)
        except Exception:
            attempt = None
        if str(getattr(attempt, "session_id", "") or "") == key:
            return record
    return None


def record_owner_stop(
    key: str, session: Any, *, audit_id: Any = None, scope: str = "pane",
    db: Any = None, ledger: Any = None, now: Optional[datetime] = None,
) -> Optional[str]:
    """PHILO-14 C2: the owner killed an agent's pane. Its launch says so
    (``state = stopped_by_owner``, ``stopped = {by, at, audit_id, scope}``)
    and its session ends through the hook ingest (``SessionEnd``, reason
    ``stopped_by_owner``), so no wait stays open on a dead pane.

    Returns the launch id, or ``None`` for a session no launch is bound to
    (the session still ends)."""
    from ..agent_context import ingest_agent_hook_event

    if db is None:
        from ..db import get_database

        db = get_database()
    if ledger is None:
        from ..delivery.factory_launch import LaunchLedger

        ledger = LaunchLedger()
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    record = _launch_for_session(ledger, db, key)
    if record is not None:
        ledger.update(
            str(record.get("launch_id")), state="stopped_by_owner",
            stopped={"by": "owner", "at": stamp, "audit_id": audit_id, "scope": scope},
        )
    agent, _, session_id = key.partition(":")
    if agent and session_id and not agent.startswith("pane"):
        ingest_agent_hook_event(agent=agent, payload={
            "session_id": session_id, "cwd": str(getattr(session, "cwd", "") or ""),
            "hook_event_name": "SessionEnd", "reason": "stopped_by_owner",
        })
    return str(record.get("launch_id")) if record is not None else None


__all__ = ["DECIDING_KIND", "record_owner_stop", "FACTS_TTL_SECONDS", "clear_facts_cache", "launch_lane", "worktree_facts"]
