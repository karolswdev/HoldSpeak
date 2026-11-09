"""The Calls window's verbs on the one declared contract (2026-11-08).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``phone_operations.py`` is. Each row states one
``CallsService`` verb once: its call, its HTTP method and path, and (where an
owner or agent may call it) its MCP tool schema. ``web/routes/calls.py``
produces the routes with ``operation_router``; ``mcp/families/declared.py``
produces the tools. The hand-written ``calls.*`` family is parked
(``mcp/families/_parked/calls_handwritten_20261108.py``).

The edge gives every ``/api/calls/*`` route the OWNER right
(``principals.required_right``); the Line's wire and its enrolment stay
hand-written in ``web/routes/calls.py`` (a Line credential, a one-time code).

The async verbs (place, hang up, test call) run on the hub's loop from the
worker the producer calls in (``CallsService._on_loop``); the route envelope
binds the loop first, as the hand-written route did by awaiting on it.

No tool, and why:

- ``calls.decide``: the tap form of his spoken yes on a held egress tool; an
  agent never answers his hold.

Imported only through ``holdspeak.operations`` (it imports this module).
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor
from holdspeak.services.errors import NotFound

Call = Callable[[Any, Any, dict[str, Any]], Any]

_OWNER = "the owner only: the hub token (HTTP edge right OWNER; MCP auth resolver), passed to the service unchanged"
_ANY = "derived by the transport (HTTP edge right OWNER; MCP auth resolver) and passed to the service unchanged"
_REFUSALS = _CONTRACT_REFUSALS + ("owner_required", "NotFound: unknown call",
                                  "ServiceError: a named reason with its HTTP status (no_number, busy, not_found, "
                                  "no_line, nothing_held, ...)", "ValidationError")
_ID = {"type": "string", "minLength": 1}
_TO = {"to": {"type": "string", "description": "A +E.164 number or a sip: address. Empty: the owner's own number."}}


def _op(name: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str, *,
        principal: str = _ANY, owner_only: bool = False, write: bool = False, tool: bool = True,
        authority: str = "work", status: int = 200,
        properties: Optional[Mapping[str, Any]] = None) -> OperationDescriptor:
    """One verb; its tool (when it has one) requires the path's ids."""
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    schema = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
              "required": ids, "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=principal,
        effect="write" if write else "read", result="the CallsService answer", refusals=_REFUSALS,
        # The service sends its own call_state frame for each change; no desk_changed.
        completion="synchronous; a change to a call is one call_state frame on the hub bus",
        exposure=(f"http:{http[0]} {http[1]}",) + ((f"mcp:{name}",) if tool else ()),
        service="calls_service", method=method, owner_only=owner_only, call=call, http=http,
        http_status=status, handler=handler, tool_schema=schema if tool else None, authority=authority,
        announces_changes=write,
        # calls.* is an MCP and REST family (thread_modes._thread_side): no palette grows.
        thread=("effect_proposal" if write else "evidence_read") if tool else None,
    )


def _on_loop(service: Any, coroutine: Any) -> Any:
    """Run one async verb on the hub's loop; a loop that is not there closes it unstarted."""
    try:
        return service._on_loop(coroutine)
    except RuntimeError:
        coroutine.close()
        raise


def _found(answer: Optional[dict[str, Any]], call_id: Any) -> dict[str, Any]:
    if answer is None:
        raise NotFound("call", str(call_id or ""))
    return answer


def _status(service: Any, principal: Any, args: dict[str, Any]) -> dict[str, Any]:
    service.ensure_listening()  # calls on and enabled: the hub waits for a call
    return service.status()


_C = "/api/calls"
CALLS_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("calls.status", "status", ("GET", _C + "/status"), "api_calls_status", _status,
        "Read the phone line: whether the phone (the Line or ai-phone) runs, its lines, the engine a call runs on, "
        "whether a passphrase is set, whether the hub waits for calls, the active call, and the setup steps."),
    _op("calls.list", "list", ("GET", _C), "api_calls_list",
        lambda s, p, a: {"calls": s.list()},
        "List the last 20 phone calls, newest first: direction, state, first words, what each call did, its note."),
    _op("calls.get", "get", ("GET", _C + "/{call_id}"), "api_call_get",
        lambda s, p, a: _found(s.get(str(a.get("call_id") or "")), a.get("call_id")),
        "Read one phone call with its transcript and what it did."),
    _op("calls.place", "place", ("POST", _C + "/place"), "api_call_place",
        lambda s, p, a: _on_loop(s, s.place(str(a.get("to") or ""))),
        "Place a phone call. With no number, HoldSpeak calls the owner's own number (the first allowed number in "
        "Settings > Calls). A real call can cost money.", principal=_OWNER, owner_only=True, write=True,
        authority="egress", status=201, properties=_TO),
    _op("calls.hangup", "hangup", ("POST", _C + "/{call_id}/hangup"), "api_call_hangup",
        lambda s, p, a: _found(_on_loop(s, s.hangup(str(a.get("call_id") or ""))), a.get("call_id")),
        "End a phone call: HoldSpeak says goodbye and hangs up.", write=True),
    _op("calls.decide", "decide", ("POST", _C + "/{call_id}/decide"), "api_call_decide",
        lambda s, p, a: _found(s.decide(str(a.get("call_id") or ""), str(a.get("decision") or "")),
                               a.get("call_id")),
        "Answer what a call holds for the owner: approve or deny (the tap form of his spoken yes).",
        principal=_OWNER, owner_only=True, write=True, tool=False, authority="authority"),
    _op("calls.test_line", "test_line", ("POST", _C + "/line/test"), "api_line_test",
        lambda s, p, a: _on_loop(s, s.test_line(str(a.get("to") or ""))),
        "Test call: the Line calls the owner, says one line and hangs up. No turn runs.",
        principal=_OWNER, owner_only=True, write=True, authority="egress", properties=_TO),
)


class _LiveCallsService:
    """The bound target: the process's one CallsService (``calls.service.CALLS``), read at each call."""

    def __getattr__(self, name: str) -> Any:
        from holdspeak.calls import service as calls

        return getattr(calls.CALLS, name)


LIVE_CALLS_SERVICE = _LiveCallsService()

__all__ = ["CALLS_OPERATIONS", "LIVE_CALLS_SERVICE"]
