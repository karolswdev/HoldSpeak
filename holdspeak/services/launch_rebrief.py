"""Re-brief a launched agent (PHILO-15 B46).

The owner's Re-brief is typed into the launch's own pane at once when the
agent is idle or asks (its turn ended). Mid-turn it is QUEUED on the launch
record (``queued_rebrief``) and typed at the next turn end: the hub's coder
watcher calls :func:`flush_queued` with the waits that began, before the
responder sees them, so a queued Re-brief is the answer to that turn end.

The text goes through the launch's own channel (the brief's): arm the
launch's pane, then one ``process.input`` through the steering path, which
checks the pane identity again and writes its receipt. A permission prompt
on the pane (a TO APPROVE wait) is not typed over: the Re-brief waits for
the next turn end.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("services.launch_rebrief")

#: A hook event after which the agent is still in its turn.
MID_TURN_EVENTS = frozenset({"UserPromptSubmit", "PreToolUse", "PostToolUse", "SubagentStop"})
#: Launch states whose pane may still take text.
LIVE_STATES = frozenset({"launched", "registered"})

QUEUED = "queued"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _field(session: Any, name: str) -> Any:
    if isinstance(session, Mapping):
        return session.get(name)
    return getattr(session, name, None)


def mid_turn(session: Any) -> bool:
    """The agent is in its turn: its last hook event is a turn event, or it
    waits on a permission prompt in its pane (typing there would answer it)."""
    from ..agent_context.models import LIFECYCLE_ENDED, is_blocked, wait_kind

    if session is None or str(_field(session, "lifecycle") or "") == LIFECYCLE_ENDED:
        return False
    if is_blocked(session):
        return wait_kind(session) == "approve"
    return str(_field(session, "hook_event_name") or "") in MID_TURN_EVENTS


def _session_key(record: Mapping[str, Any], db: Any) -> str:
    key = str(record.get("session_key") or "")
    if key:
        return key
    attempt_id = str(record.get("attempt_id") or "")
    if not attempt_id or db is None:
        return ""
    try:
        attempt = db.work_attempts.get(attempt_id)
    except Exception:
        return ""
    return str(getattr(attempt, "session_id", "") or "")


def _find_session(sessions: Iterable[Any], key: str) -> Any:
    for session in sessions:
        if f"{_field(session, 'agent')}:{_field(session, 'session_id')}" == key:
            return session
    return None


def _registry_sessions() -> list[Any]:
    from ..agent_context import list_agent_sessions

    return list(list_agent_sessions())


def deliver(service: Any, record: Mapping[str, Any], key: str, text: str, principal: Any) -> dict[str, Any]:
    """Type ``text`` into the launch's own pane (``process.input``)."""
    from .. import coder_steering

    launch_id = str(record.get("launch_id") or "")
    fresh = service.first_message.retarget(launch_id)
    if fresh is None:
        return {"status": "target_gone"}
    target = fresh.get("target") or {}
    armed = coder_steering.arm(key, str(target.get("pane_id") or ""), runner=service._runner)
    if armed.get("status") != "armed":
        return {"status": str(armed.get("status") or "arm_refused"), "detail": armed.get("detail")}
    agent = key.split(":", 1)[0] or "agent"
    try:
        sent = service._commands.submit_process_input(
            {
                "node_id": service._local_node_id,
                "target_id": target.get("target_id"),
                "target_generation": target.get("target_generation"),
                "operation": {"family": "coder_steering", "verb": "terminal.text"},
                "payload": {"text": text, "submit": True, "session_key": key, "agent": agent},
            },
            principal,
        )
    except Exception as exc:
        return {"status": str(getattr(exc, "reason", "") or type(exc).__name__)}
    outcome = str((sent.get("receipt") or {}).get("outcome") or "")
    return {"status": "delivered" if outcome == "delivered" else (outcome or "not_delivered"),
            "command_id": sent.get("command_id")}


def rebrief(
    launch_id: str, text: str, principal: Any, *,
    service: Any, db: Any = None, sessions: Optional[Callable[[], list[Any]]] = None,
) -> dict[str, Any]:
    """The owner's Re-brief: ``delivered`` now (idle or asking), ``queued``
    mid-turn, or a named refusal (``launch_unknown``, ``no_session``,
    ``launch_ended``, a steering refusal)."""
    clean = str(text or "").strip()
    if not clean:
        return {"status": "text_required"}
    ledger = service._ledger
    record = ledger.get(launch_id)
    if not record:
        return {"status": "launch_unknown"}
    if record.get("stopped") or str(record.get("state") or "") not in LIVE_STATES:
        return {"status": "launch_ended"}
    key = _session_key(record, db)
    if not key:
        return {"status": "no_session"}
    session = _find_session((sessions or _registry_sessions)(), key)
    if mid_turn(session):
        ledger.update(launch_id, queued_rebrief={"text": clean, "at": _now(), "key": key})
        return {"status": QUEUED, "at": _now()}
    result = deliver(service, record, key, clean, principal)
    if result["status"] == "delivered":
        ledger.update(launch_id, queued_rebrief=None, last_rebrief={"at": _now(), "how": "now"})
    return result


def flush_queued(
    keys: Iterable[str], *, service: Any, principal: Any = None,
) -> list[str]:
    """Type each queued Re-brief whose session's turn just ended. Returns the
    session keys whose turn end the Re-brief answered (the responder and
    Needs you leave them alone)."""
    from ..principals import Principal, PrincipalKind

    wanted = {str(k) for k in keys}
    if not wanted:
        return []
    who = principal or Principal(PrincipalKind.OWNER, "owner-session")
    consumed: list[str] = []
    try:
        records = list(service._ledger.list())
    except Exception as exc:
        log.warning(f"re-brief flush: launches unread: {exc}")
        return []
    for record in reversed(records):
        queued = record.get("queued_rebrief")
        if not isinstance(queued, Mapping) or not queued.get("text"):
            continue
        key = str(queued.get("key") or record.get("session_key") or "")
        if key not in wanted or key in consumed:
            continue
        result = deliver(service, record, key, str(queued["text"]), who)
        launch_id = str(record.get("launch_id") or "")
        if result["status"] == "delivered":
            service._ledger.update(
                launch_id, queued_rebrief=None, last_rebrief={"at": _now(), "how": "after_turn"},
            )
            consumed.append(key)
        else:
            log.warning(f"re-brief flush: {launch_id} not delivered: {result['status']}")
    return consumed


__all__ = ["MID_TURN_EVENTS", "QUEUED", "deliver", "flush_queued", "mid_turn", "rebrief"]
