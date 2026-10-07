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
- ``waiting`` / ``working``: the session the Work attempt is BOUND to (the
  rider's report, the authoritative binding) is live, blocked or not;
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

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("agent_flights")

#: Launch states that never ran an agent (``follow_through.UNLAUNCHED_STATES``).
_UNLAUNCHED = frozenset({"failed", "admitted", "approved", "rejected", "starting"})


def _agent_of(record: Mapping[str, Any]) -> str:
    profile = str(record.get("profile_id") or "").lower()
    return "codex" if profile.startswith("codex") else "claude"


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
        is_blocked,
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
    return "waiting" if is_blocked(session) else "working"


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
    if ledger is None:
        from ..delivery.factory_launch import LaunchLedger

        ledger = LaunchLedger()
    if sessions is None:
        from ..agent_context import list_agent_sessions

        sessions = list_agent_sessions()
    clock = now or datetime.now(timezone.utc)
    by_key = _session_index(sessions)
    newest: dict[str, Mapping[str, Any]] = {}
    for record in ledger.list():
        origin = record.get("origin_ref") or {}
        kind, item_id = str(origin.get("kind") or ""), str(origin.get("id") or "")
        if not kind or not item_id or str(record.get("state") or "") in _UNLAUNCHED:
            continue
        newest[f"{kind}:{item_id}"] = record   # the ledger is oldest first
    flights: list[dict[str, Any]] = []
    for ref, record in newest.items():
        kind, item_id = ref.split(":", 1)
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
        if pr and pr_state == "merged":
            state = "merged"
        elif pr and pr_state == "open":
            state = "pr_open"
        elif not session_key:
            state = "starting"
        else:
            state = _session_state(by_key.get(session_key), clock)
        project_id, project_name = _project_of(db, kind, item_id)
        evidence = follow.get("evidence") or {}
        flights.append({
            "origin_ref": ref,
            "kind": kind,
            "id": item_id,
            "title": _title_of(db, ref),
            "project_id": project_id,
            "project_name": project_name,
            "agent": _agent_of(record),
            "state": state,
            "session_key": session_key or None,
            "pr": {
                "number": pr.get("number"),
                "url": pr.get("url"),
                "state": pr_state,
            } if pr else None,
            "close": follow.get("close"),
            # K4's cleanup of the agent's session (killed, session_gone,
            # no_session): the evidence that it left; absent while the close
            # waits for confirmation (Secure) or cleanup is outstanding.
            "session_cleanup": (follow.get("cleanup") or {}).get("session"),
            "merged_at": evidence.get("merged_at") or None,
            "launch_id": record.get("launch_id"),
            # PHILO-14 C4: the Conductor drawer keeps an ended launch of the
            # last 24 h as a stale object; this is its clock.
            "launched_at": record.get("launched_at") or None,
        })
    return flights


def annotate_sessions(items: list[dict[str, Any]], flights: list[dict[str, Any]]) -> None:
    """Each session row that a flight names gets ``flight`` (its item)."""
    by_session = {f["session_key"]: f for f in flights if f.get("session_key")}
    for row in items:
        session = row.get("session") or {}
        key = f"{session.get('agent')}:{session.get('session_id')}"
        flight = by_session.get(key)
        if flight is not None:
            row["flight"] = flight


__all__ = ["agent_flights", "annotate_sessions"]
