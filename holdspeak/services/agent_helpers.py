"""Betterment AG11: agents that work together (agents/DESIGN.md, "Agents
that work together"; herdr's agent contract).

A launched agent (its launch credential) may start ONE helper in its own
worktree (a branch from its own), then prompt, wait for, read and answer
it, under these rules, copied from herdr:

- ``agent.prompt`` refuses a helper that is blocked (``agent_blocked``): a
  real answer goes through ``agent.answer``; with ``wait`` it also waits, in
  one request; if nothing moves in 5 s it says ``agent_prompt_stalled``.
- ``agent.wait`` is pinned to the helper's session: a new agent in the
  same pane never satisfies it (``agent_replaced``).
- ``agent.answer`` answers only its own helper, and never an approval
  prompt (Allow stays with the owner or the gate).
- ``agent.start_helper`` is work under Normal and YOLO, and asks the owner
  under Secure (decision 22): the owner action is one use; one helper per
  launch; it counts in "working at once".

Ownership is the launch rules' own (``conductor_launch``): the helper's
``launch:<id>`` is recorded as the caller's when it is made, and every
other tool here names it (``launch_id``), so a launch reaches only its own.
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Optional

from .errors import ServiceError

#: herdr: a prompt that moves nothing in this long says so.
STALL_SECONDS = 5.0
#: The longest one request waits (an MCP call must answer).
MAX_WAIT_SECONDS = 600.0
#: What a wait ends on: the helper finished, needs an answer, or is quiet.
SETTLED = frozenset({"done", "asks", "approve", "idle", "no_signal", "stopped"})


class HelperRefused(ServiceError):
    def __init__(self, code: str, detail: str, status: int = 409) -> None:
        super().__init__(code, detail, context={"status": status})


def _helper_send(
    caller: str,
    launch_id: str,
    record: Mapping[str, Any],
    text: str,
    *,
    session_key: str,
    expected_wait_id: str = "",
    send: Optional[Callable[..., Any]] = None,
) -> dict[str, Any]:
    """Send through the registered steering authority for this helper.

    The helper is an agent operation, so it uses the same pane identity check
    and ``coder_steering`` policy as every other terminal send.  ``send`` is
    the transport seam used by the focused tests; production leaves it unset
    and reaches the normal tmux transport only through that chokepoint.
    """
    from ..delivery.commands import deliver_agent_text
    from ..operation_policy import describe_operation, resolve_policy

    if not session_key:
        raise HelperRefused("agent_not_ready", "the helper has not registered its session")
    pane = _pane(record)
    mode = str(record.get("control_mode") or "").strip().lower()
    if not mode:
        from .agent_hand_service import _config_control_mode

        mode = _config_control_mode()
    operation = describe_operation(
        operation_id=f"agent-helper:{caller}:{launch_id}",
        family="coder_steering",
        effect_class="terminal/type_text_and_keys",
        actor=f"agent:launch:{caller}",
        destination=pane,
        data_classes=("typed_text",),
        resource_scope=f"launch:{launch_id}",
        fixed_destination=True,
    )
    policy = resolve_policy(operation, mode=mode, source="config")
    if policy.outcome != "allowed":
        raise HelperRefused("helper_send_refused", policy.reason_code)

    # A supplied transport is the unit-test seam.  It still passes the same
    # pane identity proof, without starting tmux in a focused service test.
    runner = None
    audit = None
    if send is not None:
        class _PaneResolution:
            def __init__(self, pane_id: str) -> None:
                self.returncode = 0
                self.stdout = pane_id
                self.stderr = ""

        runner = lambda _argv: _PaneResolution(pane)
        audit = lambda **_kwargs: 0
    result = deliver_agent_text(
        session_key,
        str(text).strip(),
        current_target=pane,
        agent=f"launch:{caller}",
        expected_pane_id=pane,
        expected_wait_id=expected_wait_id,
        operation=operation.to_dict(),
        policy_snapshot=policy.to_dict(),
        runner=runner,
        transport=send,
        audit=audit,
    )
    if str(result.get("status") or "") != "delivered":
        raise HelperRefused("helper_send_refused", str(result.get("status") or "send refused"))
    return result


def _ledger() -> Any:
    from ..delivery.factory_launch import LaunchLedger

    return LaunchLedger()


def _helper_record(caller: str, launch_id: str, ledger: Any = None) -> Mapping[str, Any]:
    record = (ledger or _ledger()).get(str(launch_id or "")) or {}
    if not record or str(record.get("helper_of") or "") != caller:
        raise HelperRefused("not_your_helper", "an agent reaches only the helper it started", 403)
    return record


def helper_state(db: Any, launch_id: str, ledger: Any = None) -> dict[str, Any]:
    """The helper's state in the desk's words: ``working``, ``asks``,
    ``approve``, ``done``, ``idle``, ``no_signal``, ``starting``, ``stopped``;
    with its session key, its done turn and its last words."""
    from .agent_flights import flight_of_launch

    flight = flight_of_launch(db, launch_id, ledger=ledger) or {}
    state = str(flight.get("state") or "starting")
    screen = flight.get("screen") or {}
    if state == "waiting":
        if flight.get("turn_end") == "idle":
            word = "idle"
        elif screen.get("wait") == "approve" or _permission(db, flight):
            word = "approve"
        else:
            word = "asks"
    elif state in ("done", "working", "starting", "no_signal", "resuming"):
        word = "working" if state == "resuming" else state
    else:
        word = "stopped"
    return {"launch_id": launch_id, "state": word, "session_key": flight.get("session_key"),
            "turn_id": flight.get("turn_id")}


def _permission(db: Any, flight: Mapping[str, Any]) -> bool:
    key = str(flight.get("session_key") or "")
    if not key:
        return False
    from ..agent_context import list_agent_sessions

    agent, _, sid = key.partition(":")
    session = next((s for s in list_agent_sessions(agent=agent) if s.session_id == sid), None)
    return bool(session and session.notification_type == "permission_prompt")


def _pane(record: Mapping[str, Any]) -> str:
    from ..agent_context.screen_watch import first_pane

    pane = first_pane(str(record.get("session") or ""))
    if not pane:
        raise HelperRefused("pane_gone", "the helper's terminal is gone")
    return pane


def last_words(db: Any, launch_id: str, ledger: Any = None) -> Optional[str]:
    """The helper's last words: its newest Stop (the event log), else what its
    screen showed above its prompt."""
    from ..agent_context.screen_watch import STORE
    from .launch_lane import _last_words, _session_key

    record = (ledger or _ledger()).get(launch_id) or {}
    key = _session_key(db, record) if record else ""
    words = _last_words(db, key) if key else None
    if words:
        return words
    row = STORE.get(f"launch:{launch_id}")
    return (row.said or None) if row is not None else None


# ── the tools ─────────────────────────────────────────────────────────


def start_helper(
    caller: str, *, instruction: str, profile: Optional[str], hand_service: Any,
    control_mode: Callable[[], str], ledger: Any = None,
) -> dict[str, Any]:
    from ..principals import Principal, PrincipalKind

    if not str(instruction or "").strip():
        raise HelperRefused("instruction_required", "say what the helper should do", 400)
    ledger = ledger or _ledger()
    parent = ledger.get(caller) or {}
    if not parent:
        raise HelperRefused("launch_unknown", "the calling launch is not in the ledger", 404)
    if any(str(r.get("helper_of") or "") == caller for r in ledger.list()):
        raise HelperRefused("helper_exists", "this agent already has its one helper")
    if str(control_mode() or "").strip().lower() in ("safe", "secure"):
        # Decision 22 is an owner question, not a permanent refusal.  Keep the
        # request on the parent launch so the owner's one press can continue
        # through AgentHandService and its normal process.spawn admission.
        pending = parent.get("helper_request")
        if isinstance(pending, Mapping) and pending.get("status") == "awaiting_owner":
            return {
                "status": "awaiting_owner",
                "helper_of": caller,
                "owner_action": {
                    "kind": "start_helper",
                    "launch_id": caller,
                    "request_id": str(pending.get("request_id") or ""),
                },
            }
        request_id = "helper_" + uuid.uuid4().hex
        request = {
            "request_id": request_id,
            "status": "awaiting_owner",
            "instruction": str(instruction).strip(),
            "profile": profile,
            "requested_at": datetime.now(timezone.utc).isoformat(),
        }
        updater = getattr(ledger, "update", None)
        if not callable(updater):
            raise HelperRefused("helper_needs_owner", "Secure: the owner must allow this helper")
        updater(caller, helper_request=request)
        return {
            "status": "awaiting_owner",
            "helper_of": caller,
            "owner_action": {"kind": "start_helper", "launch_id": caller, "request_id": request_id},
        }
    origin = parent.get("origin_ref") or {}
    answer = hand_service.hand(
        Principal(PrincipalKind.AGENT, f"agent:launch:{caller}"),
        str(origin.get("kind") or ""), str(origin.get("id") or ""),
        instruction=str(instruction).strip(), profile=profile, helper_of=caller,
    )
    return {"launch_id": answer.get("launch_id"), "status": answer.get("status"),
            "helper_of": caller, "worktree": answer.get("worktree")}


def allow_helper(
    caller: str,
    *,
    request_id: str,
    principal: Any,
    hand_service: Any,
    ledger: Any = None,
) -> dict[str, Any]:
    """Consume one Secure helper request with the owner's press.

    The request is only a durable continuation handle.  The actual helper
    still goes through ``AgentHandService.hand`` and its process.spawn kernel
    admission, so allowing it cannot bypass launch, worktree or authority
    checks.
    """
    from ..principals import PrincipalKind

    if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
        raise HelperRefused("owner_required", "Only the owner can allow a helper", 403)
    ledger = ledger or _ledger()
    parent = ledger.get(caller) or {}
    if not parent:
        raise HelperRefused("launch_unknown", "the calling launch is not in the ledger", 404)
    pending = parent.get("helper_request")
    if not isinstance(pending, Mapping) or str(pending.get("request_id") or "") != str(request_id or ""):
        raise HelperRefused("helper_request_unknown", "that helper request is no longer available", 404)
    if pending.get("status") == "approved" and pending.get("launch_id"):
        existing = ledger.get(str(pending["launch_id"])) or {}
        return {
            "status": "launched" if existing.get("state") in ("launched", "registered") else "failed",
            "launch_id": pending["launch_id"], "helper_of": caller,
            "worktree": existing.get("worktree"), "owner_action": {"status": "consumed", "request_id": request_id},
        }
    if pending.get("status") != "awaiting_owner":
        raise HelperRefused("helper_request_settled", "that helper request is already settled")
    origin = parent.get("origin_ref") or {}
    answer = hand_service.hand(
        principal,
        str(origin.get("kind") or ""), str(origin.get("id") or ""),
        instruction=str(pending.get("instruction") or "").strip(),
        profile=pending.get("profile"), helper_of=caller,
    )
    helper_id = str(answer.get("launch_id") or "")
    settled = dict(pending)
    settled.update({"status": "approved", "launch_id": helper_id,
                    "approved_at": datetime.now(timezone.utc).isoformat()})
    ledger.update(caller, helper_request=settled)
    return {
        **answer,
        "helper_of": caller,
        "owner_action": {"status": "consumed", "request_id": request_id},
    }


def prompt(
    db: Any, caller: str, launch_id: str, text: str, *, wait: bool = False, timeout_s: float = 300.0,
    send: Optional[Callable[..., Any]] = None, clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep, ledger: Any = None,
) -> dict[str, Any]:
    record = _helper_record(caller, launch_id, ledger)
    if not str(text or "").strip():
        raise HelperRefused("empty_prompt", "say something", 400)
    started = clock()
    before = helper_state(db, launch_id, ledger)
    # A fresh launch can return before its hook registration. Wait within
    # the same five-second bound; never type into an unidentified session.
    while not before.get("session_key") and before["state"] not in ("asks", "approve", "stopped"):
        if clock() - started >= STALL_SECONDS:
            return {"launch_id": launch_id, "status": "agent_prompt_stalled", "state": before["state"]}
        sleep(0.25)
        before = helper_state(db, launch_id, ledger)
    if before["state"] in ("asks", "approve"):
        raise HelperRefused("agent_blocked", "the helper waits for an answer; use agent.answer")
    if before["state"] == "stopped":
        raise HelperRefused("agent_stopped", "the helper is not running")
    _helper_send(caller, launch_id, record, str(text).strip(),
                 session_key=str(before.get("session_key") or ""), expected_wait_id="", send=send)
    # herdr: within 5 s the helper works (or asks); else it is stalled.
    moved = None
    while clock() - started < STALL_SECONDS:
        now = helper_state(db, launch_id, ledger)
        if now["state"] in ("working", "asks", "approve") or now.get("turn_id") not in (None, before.get("turn_id")):
            moved = now
            break
        sleep(0.25)
    if moved is None:
        return {"launch_id": launch_id, "status": "agent_prompt_stalled", "state": helper_state(db, launch_id, ledger)["state"]}
    if not wait:
        return {"launch_id": launch_id, "status": "sent", "state": moved["state"]}
    return {"launch_id": launch_id, "status": "sent", **wait_for(db, caller, launch_id, timeout_s=timeout_s,
                                                                 clock=clock, sleep=sleep, ledger=ledger, record=record)}


def wait_for(
    db: Any, caller: str, launch_id: str, *, timeout_s: float = 300.0,
    clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep,
    ledger: Any = None, record: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    _helper_record(caller, launch_id, ledger) if record is None else record
    timeout = max(1.0, min(float(timeout_s or 300.0), MAX_WAIT_SECONDS))
    pinned = helper_state(db, launch_id, ledger).get("session_key")
    started = clock()
    while True:
        now = helper_state(db, launch_id, ledger)
        if pinned and now.get("session_key") and now["session_key"] != pinned:
            raise HelperRefused("agent_replaced", "another agent took the helper's pane")
        pinned = pinned or now.get("session_key")
        if now["state"] in SETTLED and now["state"] != "working":
            return {"state": now["state"], "said": last_words(db, launch_id, ledger) if now["state"] in ("done", "asks", "idle") else None}
        if clock() - started >= timeout:
            return {"state": now["state"], "timed_out": True}
        sleep(1.0)


def read(db: Any, caller: str, launch_id: str, *, lines: int = 40, ledger: Any = None) -> dict[str, Any]:
    from ..agent_context.screen_watch import capture

    record = _helper_record(caller, launch_id, ledger)
    state = helper_state(db, launch_id, ledger)
    screen: list[str] = []
    try:
        seen = capture(_pane(record))
        if seen is not None:
            screen = seen[0].rstrip().split("\n")[-max(1, min(int(lines or 40), 200)):]
    except HelperRefused:
        screen = []
    return {"launch_id": launch_id, "state": state["state"], "said": last_words(db, launch_id, ledger),
            "screen": screen, "at": datetime.now(timezone.utc).isoformat()}


def answer(
    db: Any, caller: str, launch_id: str, text: str, *, send: Optional[Callable[..., Any]] = None,
    ledger: Any = None,
) -> dict[str, Any]:
    record = _helper_record(caller, launch_id, ledger)
    state = helper_state(db, launch_id, ledger)
    if state["state"] == "approve":
        raise HelperRefused("approval_is_owners", "an approval prompt is the owner's or the gate's")
    if state["state"] != "asks":
        raise HelperRefused("not_asking", "the helper asks nothing now")
    if not str(text or "").strip():
        raise HelperRefused("empty_answer", "say the answer", 400)
    from ..coder_steering import current_wait_episode

    key = str(state.get("session_key") or "")
    episode = current_wait_episode(key) if key else ""
    if episode.endswith("|approve"):
        raise HelperRefused("approval_is_owners", "an approval prompt is the owner's or the gate's")
    if not episode.endswith("|answer"):
        raise HelperRefused("not_asking", "the helper has no current question")
    _helper_send(caller, launch_id, record, str(text).strip(),
                 session_key=key, expected_wait_id=episode, send=send)
    return {"launch_id": launch_id, "status": "sent"}


__all__ = ["HelperRefused", "answer", "helper_state", "last_words", "prompt", "read", "start_helper", "wait_for"]
