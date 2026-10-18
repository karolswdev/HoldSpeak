"""In flight: which desk item an agent works on, and how far it is.

docs/internal/CONDUCTOR.md, step 5 (lane F2, the ratified boards K4a, K4b,
K4c, K5a and K6). One read join over three records that exist:

- the launch ledger (``factory_launch.LaunchLedger``): each Hand to agent
  launch carries ``origin_ref`` (the item), its agent profile, its Work
  attempt and, after the Heartbeat followed it (K4), ``follow_through``
  with the selected PR and the close;
- the Work attempt (``db.work_attempts``): the rider binds the agent's
  session key (``<agent>:<session_id>``) to it;
- the live agent sessions (``CoderService.list_sessions``): the session's
  state and its question.

A flight is one launch, newest per item. Its ``state``:

- ``merged`` / ``pr_open``: once a PR exists the PR is the fact (K4's
  selected PR), whatever the session does;
- ``waiting``: the bound session waits on the owner, or its turn ended with
  no completed work (``turn_end`` says ``asks`` or ``idle``);
- ``done``: the bound session's last turn completed (a Stop after a prompt,
  Betterment AG0) and asks nothing; ``new`` until the owner opened it (the
  launch's ``seen_wait_id`` is that turn's id);
- ``working``: the bound session runs a turn;
- ``stopped_by_restart``: the launch's tmux session was gone at a check on
  hub start or a heartbeat (``launch_lane.record_restart_stops``);
- ``starting``: no session is bound yet (the agent has not registered);
- ``ended``: the bound session ended (SessionEnd, sticky);
- ``expired``: the bound session is past the dead window or gone from the
  registry.

Lifecycle and freshness are resolved against the WHOLE registry, before
any presentation filter (``include_ended``). A session is never matched by
name: only the attempt's binding names it. The faces draw ``working``,
``waiting``, ``pr_open`` and ``merged`` (``starting`` as STARTING) and
nothing for ``ended`` / ``expired``. Nothing here writes.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("agent_flights")

#: The launch state of an agent whose tmux session a restart took (AG0).
STOPPED_BY_RESTART = "stopped_by_restart"

#: Launch states that never ran an agent (``follow_through.UNLAUNCHED_STATES``).
_UNLAUNCHED = frozenset({"failed", "admitted", "approved", "rejected", "starting"})


def _agent_of(record: Mapping[str, Any]) -> str:
    from ..delivery.factory_launch import agent_of_profile

    return agent_of_profile(record.get("profile_id"))


def _session_index(sessions: Iterable[Any]) -> dict[str, Any]:
    """``<agent>:<session_id> -> session`` over the whole registry."""
    by_key: dict[str, Any] = {}
    for raw in sessions:
        session = raw.get("session", raw) if isinstance(raw, Mapping) else raw
        agent = str(_field(session, "agent") or "")
        sid = str(_field(session, "session_id") or "")
        if agent and sid:
            by_key[f"{agent}:{sid}"] = session
    return by_key


def _field(session: Any, name: str) -> Any:
    if isinstance(session, Mapping):
        return session.get(name)
    return getattr(session, name, None)


def _session_state(session: Any, now: datetime) -> str:
    """The bound session's state, from its raw lifecycle and its age."""
    from ..agent_context.models import (
        DEFAULT_LIFECYCLE_DEAD_SECONDS,
        LIFECYCLE_ENDED,
        LIFECYCLE_WAITING,
        TURN_ASKS,
        completed_turn,
        is_blocked,
        turn_end,
    )

    if session is None:
        return "expired"   # bound, but gone from the registry
    if str(_field(session, "lifecycle") or "") == LIFECYCLE_ENDED:
        return "ended"
    try:
        updated = datetime.fromisoformat(str(_field(session, "updated_at") or "").replace("Z", "+00:00"))
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
    except ValueError:
        updated = None
    if updated is not None and (now - updated).total_seconds() > DEFAULT_LIFECYCLE_DEAD_SECONDS:
        return "expired"
    if is_blocked(session) and turn_end(session) == TURN_ASKS:
        return "waiting"
    # Betterment AG0: a turn that ended after a prompt is done, with or
    # without a PR (was: "working" until a PR opened, and forever after).
    if completed_turn(session):
        return "done"
    if is_blocked(session) or str(_field(session, "lifecycle") or "") == LIFECYCLE_WAITING:
        return "waiting"   # a turn end with no work behind it: idle
    return "working"


def _turn_end(session: Any, pr_state: str) -> str:
    from ..agent_context.models import turn_end

    return turn_end(session, work_done=pr_state == "open")


def _title_of(db: Any, ref: str) -> str:
    from ..grounding import hydrate_refs_detailed

    try:
        hydrated = hydrate_refs_detailed(db, [], [], "summary", [ref])
    except Exception:
        return ""
    return str(hydrated.blocks[0].title or "") if hydrated.blocks else ""


def _project_of(db: Any, kind: str, item_id: str) -> tuple[str, str]:
    from .agent_brief import project_for_item

    try:
        project_id = project_for_item(db, kind, item_id) or ""
        project = db.projects.get_project(project_id) if project_id else None
    except Exception:
        return "", ""
    return project_id, (str(project.name) if project is not None else "")


def _stamp(value: Any) -> Optional[datetime]:
    try:
        moment = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=timezone.utc)


def _ended_at(record: Mapping[str, Any], state: str, session: Any, close: Any) -> Optional[str]:
    """When the launch ended (PHILO-14 C4), or ``None`` while it is in flight:
    the merge (``merged_at``) once its close is not awaiting the owner, the
    owner's stop, else the bound session's last hook report (its SessionEnd,
    or the last word before it went quiet)."""
    stopped = record.get("stopped") or {}
    if isinstance(stopped, Mapping) and stopped.get("at"):
        return str(stopped["at"])
    if state == "merged":
        if close == "awaiting_confirm":
            return None
        evidence = (record.get("follow_through") or {}).get("evidence") or {}
        return str(evidence.get("merged_at") or "") or None
    if state in ("ended", "expired"):
        stamp = _field(session, "updated_at") if session is not None else None
        return str(stamp or record.get("launched_at") or "") or None
    return None


def _flight(db: Any, record: Mapping[str, Any], by_key: Mapping[str, Any], clock: datetime) -> dict[str, Any]:
    origin = record.get("origin_ref") or {}
    kind, item_id = str(origin.get("kind") or ""), str(origin.get("id") or "")
    ref = f"{kind}:{item_id}"
    session_key = ""
    attempt_id = str(record.get("attempt_id") or "")
    if attempt_id:
        try:
            attempt = db.work_attempts.get(attempt_id)
        except Exception:
            attempt = None
        session_key = str(getattr(attempt, "session_id", "") or "")
    follow = record.get("follow_through") or {}
    pr = follow.get("pr") or None
    pr_state = str((pr or {}).get("state") or "")
    session = by_key.get(session_key) if session_key else None
    if pr and pr_state == "merged":
        state = "merged"
    elif pr and pr_state == "open":
        state = "pr_open"
    elif str(record.get("state") or "") == STOPPED_BY_RESTART:
        state = STOPPED_BY_RESTART
    elif not session_key:
        state = "starting"
    else:
        state = _session_state(session, clock)
    responder_turn = _responder_turn(session_key, session) if state in ("waiting", "pr_open") else None
    if state == "waiting" and responder_turn == "done":
        state = "done"   # the responder read the turn end as a completion report
    turn_id = _turn_id(session) if state == "done" else None
    project_id, project_name = _project_of(db, kind, item_id)
    evidence = follow.get("evidence") or {}
    return {
        "origin_ref": ref,
        "kind": kind,
        "id": item_id,
        "title": _title_of(db, ref),
        "project_id": project_id,
        "project_name": project_name,
        "agent": _agent_of(record),
        "state": state,
        # PHILO-15 B48: how a waiting agent's turn ended (``asks`` /
        # ``idle`` / ``done``); IDLE is a lamp, never a Needs you row.
        # PHILO-15 B48 (lane 14) and 15: the responder's record of the
        # current wait (done / idle: not the owner's) first, else the turn
        # end the session's last words read as.
        "turn_end": "done" if state == "done" else (
            responder_turn
            or (_turn_end(session, pr_state) if state == "waiting" else None)
        ) if state in ("waiting", "pr_open") else None,
        # Betterment AG0: the done turn's id, and whether the owner has not
        # opened the agent since (``POST /api/agent/launches/{id}/seen``).
        "turn_id": turn_id,
        "new": bool(turn_id) and turn_id != str(record.get("seen_wait_id") or ""),
        "session_key": session_key or None,
        "pr": {
            "number": pr.get("number"),
            "url": pr.get("url"),
            "state": pr_state,
            # PHILO-15 B50: the PR's own title (the drawer's PR object).
            "title": pr.get("title") or None,
        } if pr else None,
        "close": follow.get("close"),
        # K4's cleanup of the agent's session (killed, session_gone,
        # no_session): the evidence that it left; absent while the close
        # waits for confirmation (Secure) or cleanup is outstanding.
        "session_cleanup": (follow.get("cleanup") or {}).get("session"),
        "merged_at": evidence.get("merged_at") or None,
        "launch_id": record.get("launch_id"),
        # PHILO-14 C4: the launch's clocks (the Conductor's stale window).
        "launched_at": record.get("launched_at") or None,
        "ended_at": _ended_at(record, state, session, follow.get("close")),
    }


def _turn_id(session: Any) -> Optional[str]:
    """The id of a done turn: the completed turn's, else the wait's (a
    completion report the responder read on a wait)."""
    from ..agent_context.models import completed_turn

    if session is None:
        return None
    return completed_turn(session) or (str(_field(session, "wait_id") or "") or None)


def _responder_turn(session_key: str, session: Any) -> Optional[str]:
    """``done`` / ``idle`` when the responder recorded the session's CURRENT
    wait as a turn end that is not the owner's; else ``None``."""
    from .agent_responder import TURN_STATES, AnswerStore

    if not session_key or session is None:
        return None
    try:
        entry = AnswerStore().wait(session_key)
    except Exception:
        return None
    if not entry or entry.get("wait_id") != _field(session, "wait_id"):
        return None
    state = str(entry.get("state") or "")
    return state if state in TURN_STATES else None


def _registry(db: Any, sessions: Optional[Iterable[Any]], ledger: Any, now: Optional[datetime]):
    if ledger is None:
        from ..delivery.factory_launch import LaunchLedger

        ledger = LaunchLedger()
    if sessions is None:
        from ..agent_context import list_agent_sessions

        sessions = list_agent_sessions()
    return ledger, _session_index(sessions), now or datetime.now(timezone.utc)


def _launched(record: Mapping[str, Any]) -> bool:
    origin = record.get("origin_ref") or {}
    return bool(origin.get("kind") and origin.get("id")) and str(record.get("state") or "") not in _UNLAUNCHED


def agent_flights(
    db: Any,
    sessions: Optional[Iterable[Any]] = None,
    *,
    ledger: Any = None,
    now: Optional[datetime] = None,
) -> list[dict[str, Any]]:
    """One flight per item an agent was handed, newest launch per item.

    ``sessions`` is the WHOLE agent registry (``AgentSession`` objects or
    their mappings); ``None`` reads it (``agent_context.list_agent_sessions``)."""
    ledger, by_key, clock = _registry(db, sessions, ledger, now)
    newest: dict[str, Mapping[str, Any]] = {}
    for record in ledger.list():
        if not _launched(record):
            continue
        origin = record.get("origin_ref") or {}
        newest[f"{origin.get('kind')}:{origin.get('id')}"] = record   # the ledger is oldest first
    return [_flight(db, record, by_key, clock) for record in newest.values()]


#: The states whose agent still holds the item (the faces' ``isInFlight``).
_IN_FLIGHT = frozenset({"starting", "working", "waiting", "done", "pr_open"})

#: An ended launch stays in the Conductor's history this long.
HISTORY_WINDOW = timedelta(hours=24)


def launch_history(
    db: Any,
    sessions: Optional[Iterable[Any]] = None,
    *,
    ledger: Any = None,
    now: Optional[datetime] = None,
    window: timedelta = HISTORY_WINDOW,
) -> list[dict[str, Any]]:
    """PHILO-14 C4: every launch that ENDED in the last ``window``, each
    launch once (a relaunch of an item keeps the earlier launch's receipt),
    newest end first, in the flight shape with ``ended_at``. A launch still
    in flight is never here (``agent_flights`` carries it)."""
    ledger, by_key, clock = _registry(db, sessions, ledger, now)
    out: list[tuple[datetime, dict[str, Any]]] = []
    for record in ledger.list():
        if not _launched(record):
            continue
        flight = _flight(db, record, by_key, clock)
        if flight["state"] in _IN_FLIGHT or (flight["state"] == "merged" and flight["close"] == "awaiting_confirm"):
            continue
        ended = _stamp(flight.get("ended_at"))
        if ended is None or clock - ended > window:
            continue
        out.append((ended, flight))
    out.sort(key=lambda pair: pair[0], reverse=True)
    return [flight for _ended, flight in out]


def flight_of_launch(
    db: Any, launch_id: str, sessions: Optional[Iterable[Any]] = None, *, ledger: Any = None,
) -> Optional[dict[str, Any]]:
    """The flight of one launch (any state), or ``None`` for an unknown one."""
    ledger, by_key, clock = _registry(db, sessions, ledger, None)
    record = ledger.get(launch_id)
    if not record or not _launched(record):
        return None
    return _flight(db, record, by_key, clock)


#: Betterment AG5: the session states whose agent holds a "working at
#: once" slot. A done turn, an idle (quiet) one, an ended or expired session
#: and a launch stopped by a restart hold none: their process waits and
#: costs nothing.
_SLOT_STATES = frozenset({"starting", "working", "waiting"})


def _bound_session_key(db: Any, record: Mapping[str, Any]) -> str:
    attempt_id = str(record.get("attempt_id") or "")
    if not attempt_id:
        return ""
    try:
        attempt = db.work_attempts.get(attempt_id)
    except Exception:
        return ""
    return str(getattr(attempt, "session_id", "") or "")


def slot_holders(
    db: Any,
    records: Iterable[Mapping[str, Any]],
    sessions: Optional[Iterable[Any]] = None,
    *,
    now: Optional[datetime] = None,
) -> list[Mapping[str, Any]]:
    """Betterment AG5: of these running launches, the ones that hold a
    "working at once" slot: the agent starts, works, or needs the owner (it
    asks, or a call waits for him). A turn that ended done or idle is
    finished work: it never blocks a new hand. ``sessions`` is the whole
    registry (``None`` reads it)."""
    from ..agent_context.models import TURN_ASKS, turn_end

    if sessions is None:
        from ..agent_context import list_agent_sessions

        sessions = list_agent_sessions()
    by_key = _session_index(sessions)
    clock = now or datetime.now(timezone.utc)
    held: list[Mapping[str, Any]] = []
    for record in records:
        if str(record.get("state") or "") == STOPPED_BY_RESTART:
            continue
        key = _bound_session_key(db, record)
        if not key:
            held.append(record)   # starting: the agent has not registered yet
            continue
        session = by_key.get(key)
        state = _session_state(session, clock)
        if state not in _SLOT_STATES:
            continue
        if state == "waiting":
            # The responder's record of the wait first (done / idle is not
            # the owner's), else how the turn ended.
            ended = _responder_turn(key, session) or turn_end(session)
            if ended != TURN_ASKS:
                continue
        held.append(record)
    return held


def annotate_sessions(items: list[dict[str, Any]], flights: list[dict[str, Any]]) -> None:
    """Each session row that a flight names gets ``flight`` (its item)."""
    by_session = {f["session_key"]: f for f in flights if f.get("session_key")}
    for row in items:
        session = row.get("session") or {}
        key = f"{session.get('agent')}:{session.get('session_id')}"
        flight = by_session.get(key)
        if flight is not None:
            row["flight"] = flight


__all__ = ["STOPPED_BY_RESTART", "agent_flights", "annotate_sessions", "flight_of_launch", "slot_holders"]
