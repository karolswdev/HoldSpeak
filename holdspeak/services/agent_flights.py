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

A flight is one launch, newest per item. Its ``state`` is one of
``working``, ``waiting``, ``pr_open``, ``merged`` or ``ended``: once a PR
exists the PR is the fact, else the session is. The faces draw the first
four (``ended`` draws nothing). Nothing here writes.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("agent_flights")

#: Launch states that never ran an agent (``follow_through.UNLAUNCHED_STATES``).
_UNLAUNCHED = frozenset({"failed", "admitted", "approved", "rejected", "starting"})


def _agent_of(record: Mapping[str, Any]) -> str:
    profile = str(record.get("profile_id") or "").lower()
    return "codex" if profile.startswith("codex") else "claude"


def _session_index(sessions: Iterable[Mapping[str, Any]]) -> tuple[dict[str, dict], dict[str, str]]:
    """``key -> session payload`` and ``tmux session name -> key``."""
    by_key: dict[str, dict] = {}
    by_tmux: dict[str, str] = {}
    for row in sessions:
        session = dict((row or {}).get("session") or row or {})
        agent, sid = str(session.get("agent") or ""), str(session.get("session_id") or "")
        if not agent or not sid:
            continue
        key = f"{agent}:{sid}"
        by_key[key] = session
        tmux = str(session.get("tmux_session") or "")
        if tmux:
            by_tmux.setdefault(tmux, key)
    return by_key, by_tmux


def _session_state(session: Optional[Mapping[str, Any]]) -> str:
    from ..agent_context.models import is_blocked

    if session is None:
        return "working"
    if str(session.get("state") or session.get("lifecycle") or "") == "ended":
        return "ended"
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
    sessions: Iterable[Mapping[str, Any]],
    *,
    ledger: Any = None,
) -> list[dict[str, Any]]:
    """One flight per item an agent was handed, newest launch per item."""
    if ledger is None:
        from ..delivery.factory_launch import LaunchLedger

        ledger = LaunchLedger()
    by_key, by_tmux = _session_index(sessions)
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
        if not session_key:
            session_key = by_tmux.get(str(record.get("session") or ""), "")
        follow = record.get("follow_through") or {}
        pr = follow.get("pr") or None
        pr_state = str((pr or {}).get("state") or "")
        if pr and pr_state == "merged":
            state = "merged"
        elif pr and pr_state == "open":
            state = "pr_open"
        else:
            state = _session_state(by_key.get(session_key)) if session_key else "working"
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
            "merged_at": evidence.get("merged_at") or None,
            "launch_id": record.get("launch_id"),
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
