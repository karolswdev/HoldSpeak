"""Re-brief a launched agent (PHILO-15 B46; Astra r1 and r2 on #996).

Each owner Send press is one approval (Article XI.4): its principal, time
and press id. Presses wait in a small FIFO on the launch record
(``queued_rebriefs``, at most :data:`MAX_QUEUED`; a press past it
supersedes the oldest). When the agent is idle or asks, the OLDEST press is
typed now; mid-turn, the hub's coder watcher (:func:`flush_queued`) types it
at the next genuine turn end, before the responder sees that wait.

The text goes through the launch's own channel: arm the launch's pane, then
one ``process.input`` whose command id is derived from the press (so its
receipt names the press), bound to the wait episode read just before
(``expected_wait_id``): a permission prompt that begins before the
keystroke refuses it (``wait_not_current``) and the press stays queued.

Every press ends in one receipt on the launch (``rebriefs``): SENT, or
SUPERSEDED, or EXPIRED · AGENT NEVER RETURNED after
:data:`QUEUE_EXPIRY_SECONDS`.
"""
from __future__ import annotations

import threading
import uuid
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


def _principal_record(principal: Any) -> dict[str, str]:
    kind = getattr(principal, "kind", None)
    return {
        "kind": str(getattr(kind, "value", kind) or "owner"),
        "identity": str(getattr(principal, "identity", "") or "owner-session"),
    }


def _principal_from(stored: Mapping[str, Any]) -> Any:
    from ..principals import Principal, PrincipalKind

    try:
        kind = PrincipalKind(str(stored.get("kind") or "owner"))
    except ValueError:
        kind = PrincipalKind.OWNER
    return Principal(kind, str(stored.get("identity") or "owner-session"))


def new_command_id() -> str:
    """The id of one owner Send press (its approval)."""
    return str(uuid.uuid4())


def attempt_command_id(press_id: str, attempt: int) -> str:
    """The ``process.input`` command id of attempt ``attempt`` to type press
    ``press_id``: derived from the press (uuid5), so every delivery receipt
    names the press that approved it. A refused attempt (``wait_not_current``)
    keeps its own receipt; the next attempt is a new command."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"holdspeak:rebrief:{press_id}#{attempt}"))


def current_wait_id(session: Any) -> str:
    """The session's current wait episode (``<wait_id>|<kind>``), ``""``
    when it waits on nothing (``coder_steering.wait_episode``)."""
    from ..coder_steering import wait_episode

    return wait_episode(session)


def deliver(
    service: Any, record: Mapping[str, Any], key: str, text: str, principal: Any,
    *, command_id: Optional[str] = None, expected_wait_id: Optional[str] = None,
) -> dict[str, Any]:
    """Type ``text`` into the launch's own pane (``process.input``).

    ``expected_wait_id`` binds the delivery to the wait episode the caller
    read (``""``: no wait). The steering chokepoint reads the session again
    just before the keystroke and refuses ``wait_not_current`` when another
    wait (a permission prompt) began in between (Astra r2 on #996)."""
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
    payload: dict[str, Any] = {"text": text, "submit": True, "session_key": key, "agent": agent}
    if expected_wait_id is not None:
        payload["expected_wait_id"] = str(expected_wait_id)
    try:
        sent = service._commands.submit_process_input(
            {
                **({"command_id": command_id} if command_id else {}),
                "node_id": service._local_node_id,
                "target_id": target.get("target_id"),
                "target_generation": target.get("target_generation"),
                "operation": {"family": "coder_steering", "verb": "terminal.text"},
                "payload": payload,
            },
            principal,
        )
    except Exception as exc:
        return {"status": str(getattr(exc, "reason", "") or type(exc).__name__)}
    receipt = sent.get("receipt") or {}
    outcome = str(receipt.get("outcome") or "")
    return {
        "status": "delivered" if outcome == "delivered" else (outcome or "not_delivered"),
        "command_id": sent.get("command_id"),
        "operation_id": sent.get("operation_id"),
        "receipt_id": receipt.get("receipt_id"),
        "executed_at": receipt.get("executed_at"),
        "detail": receipt.get("error"),
    }


# ── the queue: a small FIFO of owner presses, each with a terminal receipt ──

#: At most this many Re-briefs wait for turn ends; a press past it
#: supersedes the oldest (a SUPERSEDED receipt).
MAX_QUEUED = 3
#: A Re-brief that waited this long for a turn end expires (an EXPIRED ·
#: AGENT NEVER RETURNED receipt): the agent stopped without a turn end.
QUEUE_EXPIRY_SECONDS = 2 * 60 * 60
#: Receipts kept on a launch (newest last).
MAX_RECEIPTS = 50

SENT = "sent"
SUPERSEDED = "superseded"
EXPIRED = "expired"

_LOCK = threading.Lock()


def _queue(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    items = record.get("queued_rebriefs")
    if not isinstance(items, list):
        legacy = record.get("queued_rebrief")
        items = [legacy] if isinstance(legacy, Mapping) and legacy.get("text") else []
    out = []
    for item in items:
        if isinstance(item, Mapping) and item.get("text"):
            entry = dict(item)
            approval = dict(entry.get("approval") or {})
            entry.setdefault("id", str(approval.get("command_id") or entry.get("at") or ""))
            out.append(entry)
    return out


def _receipt(item: Mapping[str, Any], state: str, *, how: str = "", result: Optional[Mapping[str, Any]] = None,
             detail: str = "") -> dict[str, Any]:
    """The terminal receipt of one press: the press (who, when, its command
    id) and what became of it."""
    approval = dict(item.get("approval") or {})
    out = {
        "id": str(item.get("id") or approval.get("command_id") or ""),
        "state": state,
        "text_head": str(item.get("text") or "")[:120],
        "approved_by": dict(approval.get("principal") or {}),
        "approved_at": approval.get("at") or item.get("at"),
        "press_id": approval.get("command_id"),
        "command_id": None,
        "attempts": int(item.get("attempts") or 0),
        "at": _now(),
        "how": how,
        "detail": detail,
    }
    if result:
        out.update({
            "command_id": result.get("command_id"),
            "operation_id": result.get("operation_id"),
            "receipt_id": result.get("receipt_id"),
            "at": result.get("executed_at") or out["at"],
        })
    return out


def _write(service: Any, launch_id: str, queue: list[dict[str, Any]], receipts: list[dict[str, Any]]) -> None:
    record = service._ledger.get(launch_id) or {}
    kept = [r for r in (record.get("rebriefs") or []) if isinstance(r, Mapping)] + receipts
    sent = [r for r in kept if r.get("state") == SENT]
    service._ledger.update(
        launch_id,
        queued_rebriefs=queue,
        queued_rebrief=queue[0] if queue else None,  # the first, for older readers
        rebriefs=kept[-MAX_RECEIPTS:],
        **({"last_rebrief": sent[-1]} if sent else {}),
    )


def _age_seconds(stamp: Any, now: datetime) -> float:
    try:
        then = datetime.strptime(str(stamp), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return 0.0
    return (now - then).total_seconds()


def _expire(queue: list[dict[str, Any]], now: datetime) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    keep, receipts = [], []
    for item in queue:
        if _age_seconds(item.get("at"), now) >= QUEUE_EXPIRY_SECONDS:
            receipts.append(_receipt(item, EXPIRED, detail="AGENT NEVER RETURNED"))
        else:
            keep.append(item)
    return keep, receipts


def expire_queued(service: Any, *, now: Optional[datetime] = None) -> int:
    """Expire every queued Re-brief older than :data:`QUEUE_EXPIRY_SECONDS`
    (the hub's spool loop calls this). Returns how many expired."""
    when = now or datetime.now(timezone.utc)
    count = 0
    with _LOCK:
        for record in list(service._ledger.list()):
            queue = _queue(record)
            if not queue:
                continue
            keep, receipts = _expire(queue, when)
            if receipts:
                _write(service, str(record.get("launch_id")), keep, receipts)
                count += len(receipts)
    return count


def _deliver_head(
    service: Any, launch_id: str, key: str, session: Any, how: str,
) -> Optional[dict[str, Any]]:
    """Type the oldest queued Re-brief of ``launch_id``, bound to the wait
    episode ``session`` shows now. Only that press leaves the queue."""
    record = service._ledger.get(launch_id) or {}
    queue = _queue(record)
    if not queue:
        return None
    head = queue[0]
    approval = dict(head.get("approval") or {})
    attempt = int(head.get("attempts") or 0) + 1
    press_id = str(approval.get("command_id") or head.get("id") or "")
    result = deliver(
        service, record, key, str(head["text"]), _principal_from(approval.get("principal") or {}),
        command_id=attempt_command_id(press_id, attempt) if press_id else None,
        expected_wait_id=current_wait_id(session),
    )
    fresh = _queue(service._ledger.get(launch_id) or {})
    if result["status"] == "delivered":
        _write(service, launch_id, [q for q in fresh if q.get("id") != head.get("id")],
               [_receipt({**head, "attempts": attempt}, SENT, how=how, result=result)])
    else:
        _write(service, launch_id,
               [{**q, "attempts": attempt, "last_refusal": result["status"]} if q.get("id") == head.get("id") else q
                for q in fresh], [])
    return result


def rebrief(
    launch_id: str, text: str, principal: Any, *,
    service: Any, db: Any = None, sessions: Optional[Callable[[], list[Any]]] = None,
) -> dict[str, Any]:
    """The owner's Re-brief: ``delivered`` now (idle or asking), ``queued``
    mid-turn, or a named refusal (``launch_unknown``, ``no_session``,
    ``launch_ended``, ``wait_not_current``, a steering refusal).

    The press joins a small FIFO (:data:`MAX_QUEUED`); when the agent is not
    mid-turn the OLDEST press is typed now, so presses reach the agent in
    order. Every press ends in one receipt: SENT, SUPERSEDED or EXPIRED."""
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
    # The owner's Send press is the approval (Article XI.4): its principal,
    # time and command id ride with the text to the receipt that types it.
    approval = {"principal": _principal_record(principal), "at": _now(), "command_id": new_command_id()}
    item = {"id": approval["command_id"], "text": clean, "at": approval["at"], "key": key, "approval": approval}
    with _LOCK:
        queue, receipts = _expire(_queue(ledger.get(launch_id) or {}), datetime.now(timezone.utc))
        queue.append(item)
        while len(queue) > MAX_QUEUED:
            receipts.append(_receipt(queue.pop(0), SUPERSEDED, detail="A NEWER RE-BRIEF"))
        _write(service, launch_id, queue, receipts)
        if mid_turn(session):
            return {"status": QUEUED, "at": approval["at"], "command_id": approval["command_id"],
                    "position": len(queue)}
        result = _deliver_head(service, launch_id, key, session, "now") or {"status": "not_delivered"}
    remaining = _queue(ledger.get(launch_id) or {})
    if any(q.get("id") == item["id"] for q in remaining):
        # Not typed now: an older press went first, or the wait changed
        # before the keystroke (a permission prompt). This press stays in
        # the queue for the next turn end, and says so.
        return {"status": QUEUED, "at": approval["at"], "command_id": approval["command_id"],
                "position": len(remaining), "now": result.get("status")}
    return result


def flush_queued(
    keys: Iterable[str], *, service: Any, sessions: Optional[Callable[[], list[Any]]] = None,
) -> list[str]:
    """At each turn end that began (the coder watcher's keys), type the
    oldest queued Re-brief of that session. Returns the keys whose turn end
    a Re-brief answered (the responder and Needs you leave them alone).

    The session is read again first: only a genuine turn end (idle or a
    question) takes the Re-brief; a permission wait stays the owner's. The
    delivery is bound to the wait episode read here, so a permission prompt
    that begins before the keystroke refuses it (``wait_not_current``)."""
    wanted = {str(k) for k in keys}
    if not wanted:
        return []
    try:
        current = list((sessions or _registry_sessions)())
    except Exception as exc:
        log.warning(f"re-brief flush: sessions unread: {exc}")
        return []
    consumed: list[str] = []
    try:
        expire_queued(service)
        records = list(service._ledger.list())
    except Exception as exc:
        log.warning(f"re-brief flush: launches unread: {exc}")
        return []
    for record in reversed(records):
        queue = _queue(record)
        if not queue:
            continue
        key = str(queue[0].get("key") or record.get("session_key") or "")
        if key not in wanted or key in consumed:
            continue
        session = _find_session(current, key)
        if session is None or mid_turn(session):
            continue  # a permission prompt (or the turn goes on): not ours to type into
        launch_id = str(record.get("launch_id") or "")
        with _LOCK:
            result = _deliver_head(service, launch_id, key, session, "after_turn")
        if result and result["status"] == "delivered":
            consumed.append(key)
        elif result:
            log.warning(f"re-brief flush: {launch_id} not delivered: {result['status']}")
    return consumed


__all__ = [
    "EXPIRED", "MAX_QUEUED", "MID_TURN_EVENTS", "QUEUED", "QUEUE_EXPIRY_SECONDS", "SENT", "SUPERSEDED",
    "current_wait_id", "deliver", "expire_queued", "flush_queued", "mid_turn", "rebrief",
]
