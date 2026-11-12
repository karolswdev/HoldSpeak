"""The Calls window's verbs on the one declared contract (2026-11-08).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``phone_operations.py`` is. Each row states one
``CallsService`` verb once: its call, its HTTP method and path, and (where an
owner or agent may call it) its MCP tool schema. ``web/routes/calls.py``
produces the routes with ``operation_router``; ``mcp/families/declared.py``
produces the tools. The hand-written ``calls.*`` family is parked
(``mcp/families/_parked/calls_handwritten_20261108.py``).

The Line's routes share one LineService port (CallsService.line). Its wire
is HTTP-only and carries the edge's node credential as a held input. Enrolment
is HTTP-only: the one-time owner-minted code is its credential; an authenticated
agent is refused. Codes never pass through a model. Other Line rows are owner
only. Every Telnyx row can reach his account: egress, his press, off the loop.

The async verbs (place, hang up, test call) run on the hub's loop from the
worker the producer calls in (``CallsService._on_loop``); the route envelope
binds the loop first, as the hand-written route did by awaiting on it.

Place and the test call are egress and his press (``owner_press``: a steward
child is refused); decide is his word on the line. Place, hang up and the test
call wait on the line (``blocking_io``: beside the MCP queue, never holding it).
Each write is announced once by the registry (``desk_changed`` kind ``call``).

Imported only through ``holdspeak.operations`` (it imports this module).
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor
from holdspeak.services.errors import NotFound
from holdspeak.services.room_binding import BINDING_SCHEMA

Call = Callable[[Any, Any, dict[str, Any]], Any]

_OWNER = "the owner only: the hub token (HTTP edge right OWNER; MCP auth resolver), passed to the service unchanged"
_ANY = "derived by the transport (HTTP edge right OWNER; MCP auth resolver) and passed to the service unchanged"
_REFUSALS = _CONTRACT_REFUSALS + ("owner_required", "NotFound: unknown call",
                                  "ServiceError: a named reason with its HTTP status (no_number, busy, not_found, "
                                  "no_line, nothing_held, ...)", "ValidationError", "answer_stale", "held_call_forbidden")
_ID = {"type": "string", "minLength": 1}
_TO = {"to": {"type": "string", "description": "A +E.164 number or a sip: address. Empty: the owner's own number."}}


def _op(name: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str, *,
        principal: str = _ANY, owner_only: bool = False, write: bool = False, tool: bool = True,
        authority: str = "work", status: int = 200, owner_press: bool = False, blocking_io: bool = False,
        properties: Optional[Mapping[str, Any]] = None, required: tuple[str, ...] = ()) -> OperationDescriptor:
    """One verb; its tool (when it has one) requires the path's ids."""
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    schema = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
              "required": ids + list(required), "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=principal,
        effect="write" if write else "read", result="the CallsService answer", refusals=_REFUSALS,
        # The service sends its call_state frame; the registry adds the one desk_changed frame (kind call).
        completion="synchronous; a change to a call is one call_state and one desk_changed frame on the hub bus",
        exposure=(f"http:{http[0]} {http[1]}",) + ((f"mcp:{name}",) if tool else ()),
        service="calls_service", method=method, owner_only=owner_only, call=call, http=http,
        http_status=status, handler=handler, tool_schema=schema if tool else None, authority=authority,
        owner_press=owner_press, blocking_io=blocking_io,
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
    return service.status(principal)


_C = "/api/calls"
_CALL_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("calls.status", "status", ("GET", _C + "/status"), "api_calls_status", _status,
        "Read the phone line: whether the phone (the Line or ai-phone) runs, its lines, the engine a call runs on, "
        "whether a passphrase is set, whether the hub waits for calls, the active call, and the setup steps."),
    _op("calls.list", "list", ("GET", _C), "api_calls_list",
        lambda s, p, a: {"calls": s.list(p)},
        "List the last 20 phone calls, newest first: direction, state, first words, what each call did, its note."),
    _op("calls.get", "get", ("GET", _C + "/{call_id}"), "api_call_get",
        lambda s, p, a: _found(s.get(str(a.get("call_id") or ""), p), a.get("call_id")),
        "Read one phone call with its transcript and what it did."),
    _op("calls.place", "place", ("POST", _C + "/place"), "api_call_place",
        lambda s, p, a: _on_loop(s, s.place(str(a.get("to") or ""))),
        "Place a phone call. With no number, HoldSpeak calls the owner's own number (the first allowed number in "
        "Settings > Calls). A real call can cost money.", principal=_OWNER, owner_only=True, write=True,
        authority="egress", status=201, properties=_TO, owner_press=True, blocking_io=True),
    _op("calls.hangup", "hangup", ("POST", _C + "/{call_id}/hangup"), "api_call_hangup",
        lambda s, p, a: _found(_on_loop(s, s.hangup(str(a.get("call_id") or ""))), a.get("call_id")),
        "End a phone call: HoldSpeak says goodbye and hangs up.", write=True, blocking_io=True),
    _op("calls.decide", "decide", ("POST", _C + "/{call_id}/decide"), "api_call_decide",
        lambda s, p, a: _found(s.decide(str(a.get("call_id") or ""), str(a.get("decision") or ""), binding=a.get("binding")),
                               a.get("call_id")),
        "Answer what a call holds for the owner: approve or deny with the binding of the details read or spoken. "
        "A missing or stale binding is answer_stale; nothing is approved.",
        principal=_OWNER, owner_only=True, write=True, authority="authority", owner_press=True,
        properties={"decision": {"type": "string", "enum": ["approve", "deny"]}, "binding": BINDING_SCHEMA},
        required=("decision", "binding")),
    _op("calls.test_line", "test_line", ("POST", _C + "/line/test"), "api_line_test",
        lambda s, p, a: _on_loop(s, s.test_line(str(a.get("to") or ""))),
        "Test call: the Line calls the owner, says one line and hangs up. No turn runs.",
        principal=_OWNER, owner_only=True, write=True, authority="egress", properties=_TO, owner_press=True,
        blocking_io=True),
)


def _line(name: str, method: str, verb: str, path: str, description: str, call: Call, *,
          owner: bool = True, tool: bool = True, write: bool = False, egress: bool = False,
          held: tuple[str, ...] = (), properties: Optional[Mapping[str, Any]] = None,
          principal: str = _OWNER) -> OperationDescriptor:
    ids = [part[1:-1] for part in path.split("/") if part.startswith("{")]
    props = {**{key: _ID for key in ids}, **dict(properties or {})}
    return OperationDescriptor(
        name=f"calls.line.{name}", version=1, description=description,
        args_schema={"type": "object"}, principal=principal, effect="write" if write else "read",
        result="the LineService answer; credentials only on the HTTP code exchange",
        refusals=_REFUSALS + ("off", "usage", "no_store", "code_unknown", "code_expired"),
        completion="synchronous; next waits up to 25 seconds for commands",
        exposure=(f"http:{verb} {path}",) + ((f"mcp:calls.line.{name}",) if tool else ()),
        service="calls_service", method=f"line.{method}", held=held, owner_only=owner,
        blocking_io=True, owner_press=egress or write and owner,
        call=call, http=(verb, path), handler=f"api_line_{name.replace('.', '_')}",
        tool_schema={"type": "object", "properties": props, "required": ids,
                     "additionalProperties": False} if tool else None,
        authority="egress" if egress else "authority", thread=None,
        # The registry owns the one desk_changed frame, shared with HTTP's scope.
    )


_L = "/api/calls/line"
LINE_OPERATIONS: tuple[OperationDescriptor, ...] = (
    *(_line(verb, verb, "POST", f"{_L}/{verb}", f"The Line node's {verb} wire request.",
            lambda s, p, a, verb=verb: getattr(s.line, verb)(
                p, {k: v for k, v in a.items() if k != "node_credential"}, a["node_credential"]),
            owner=False, tool=False, write=verb != "next", held=("node_credential",),
            principal="the owner or a Line node authenticated at the edge; its credential is HELD, never JSON")
      for verb in ("hello", "events", "next")),
    _line("codes", "codes", "POST", _L + "/codes", "Make a one-time code to enrol a Line node.",
          lambda s, p, a: s.line.codes(str(a.get("node") or ""), str(a.get("hub") or "").strip()),
          write=True, tool=False),
    _line("enrol", "enrol", "POST", _L + "/enrol", "Exchange an owner's one-time code for a Line credential.",
          lambda s, p, a: s.line.enrol(p, str(a.get("code") or "")), owner=False, tool=False, write=True,
          principal="the owner or no principal: an unspent owner-minted code is the credential; never an agent"),
    _line("nodes", "nodes", "GET", _L + "/nodes", "Read the enrolled Line nodes and their last hello.",
          lambda s, p, a: s.line.nodes()),
    _line("node_revoke", "revoke", "DELETE", _L + "/nodes/{node}", "Revoke a Line node's credential.",
          lambda s, p, a: s.line.revoke(str(a.get("node") or "")), write=True),
    _line("status", "status", "GET", _L + "/status", "Read the Line state, address and secret locations.",
          lambda s, p, a: s.line.status()),
    _line("telnyx.status", "telnyx_status", "GET", _L + "/telnyx/status", "Read the Telnyx setup and balance.",
          lambda s, p, a: s.line.telnyx_status(), egress=True),
    _line("telnyx.connect", "telnyx_connect", "POST", _L + "/telnyx/connect", "Connect the Line to Telnyx.",
          lambda s, p, a: s.line.telnyx_connect(), write=True, egress=True),
    _line("telnyx.numbers", "telnyx_numbers", "GET", _L + "/telnyx/numbers", "Find Telnyx numbers and prices.",
          lambda s, p, a: s.line.telnyx_numbers(str(a.get("area") or "")), egress=True,
          properties={"area": {"type": "string"}}),
    _line("telnyx.buy", "telnyx_buy", "POST", _L + "/telnyx/buy", "Buy a number at the price in its quote.",
          lambda s, p, a: s.line.telnyx_buy(p, str(a.get("phone_number") or ""), str(a.get("quote") or "")),
          write=True, egress=True, properties={"phone_number": {"type": "string"}, "quote": {"type": "string"}}),
    _line("telnyx.assign", "telnyx_assign", "POST", _L + "/telnyx/assign", "Point a Telnyx number at the Line.",
          lambda s, p, a: s.line.telnyx_assign(str(a.get("phone_number") or "")), write=True, egress=True,
          properties={"phone_number": {"type": "string"}}),
)

# Literal Line paths must precede /api/calls/{call_id}.
CALLS_OPERATIONS = LINE_OPERATIONS + _CALL_OPERATIONS


class _LiveCallsService:
    """The bound target: the process's one CallsService (``calls.service.CALLS``), read at each call."""

    def __getattr__(self, name: str) -> Any:
        from holdspeak.calls import service as calls

        return getattr(calls.CALLS, name)


LIVE_CALLS_SERVICE = _LiveCallsService()

__all__ = ["CALLS_OPERATIONS", "LINE_OPERATIONS", "LIVE_CALLS_SERVICE"]
