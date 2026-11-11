"""The phone channel's web verbs on the one declared contract (2026-11-08).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``meeting_operations.py`` is. Each row states one
``PhoneService`` verb once: its call, its HTTP method and path, and (where an
owner or agent may call it) its MCP tool schema. ``web/routes/phone.py``
produces the owner routes with ``operation_router``; the routes a paired phone
calls with its device token stay hand-written there (the producer cannot
authenticate a device) and call ``OperationRegistry.invoke`` with the
authenticated device as a HELD input.

No tool, and why:

- ``phone.redeem``: only the phone app redeems a pairing token; the answer is
  its device credential. The transport holds the address the redeem reached.
- ``phone.pair``: the transport holds the address the owner pressed Pair on;
  the answer is a pairing credential.
- ``phone.save_push_key``: the Apple push key is a credential; it never goes
  through a model's context.
- ``phone.mark_read``, ``phone.decide``, ``phone.accept``, ``phone.decline``,
  ``phone.end``: the transport holds the paired device (a tool call cannot).

``PhoneService.needs_you_items`` is not a verb here: no phone route reads it;
the desk's Needs you read (``GET /api/desk/needs-you``) gathers it.
Imported only through ``holdspeak.operations`` (it imports this module).
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor, OperationOwnerRequired
from holdspeak.principals import PrincipalKind

Call = Callable[[Any, Any, dict[str, Any]], Any]

_OWNER = "the owner only: the hub token (HTTP edge right OWNER; MCP auth resolver), passed to the service unchanged"
_OWNER_OR_AGENT = ("the owner or an agent (hub or agent token), or the paired phone: its device token "
                   "(Authorization: Bearer <device JWT>), authenticated by the route on every request")
_OWNER_OR_DEVICE = ("the owner (hub token) or the paired phone: its device token, authenticated by the "
                    "route on every request and HELD as ``device`` (None for the owner)")
_REFUSALS = _CONTRACT_REFUSALS + ("owner_required", "PhoneRefused: a named code with its HTTP status", "phone_off")
_ID = {"type": "string", "minLength": 1}


def _op(name: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str, *,
        principal: str = _OWNER, owner_only: bool = True, write: bool = False, tool: bool = True,
        held: tuple[str, ...] = (), authority: str = "work", status: int = 200,
        properties: Optional[Mapping[str, Any]] = None) -> OperationDescriptor:
    """One verb; its tool (when it has one) requires the path's ids."""
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    schema = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
              "required": ids, "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=principal,
        effect="write" if write else "read", result="the PhoneService answer", refusals=_REFUSALS,
        completion="synchronous; a write is one phone_changed frame and one desk_changed frame on the hub bus",
        exposure=(f"http:{http[0]} {http[1]}",) + ((f"mcp:{name}",) if tool else ()),
        service="phone_service", method=method, held=held, owner_only=owner_only, owner_press=owner_only and write,
        call=_device_call(name, call) if "device" in held or name == "phone.redeem" else call, http=http,
        http_status=status, handler=handler, tool_schema=schema if tool else None,
        authority="authority" if owner_only and write and authority == "work" else authority,
        # phone.* is an MCP and REST family (thread_modes._thread_side): no palette grows.
        thread=("effect_proposal" if write else "evidence_read") if tool else None,
    )


def _device_call(name: str, call: Call) -> Call:
    """The paired phone or owner acts; an agent cannot impersonate either."""
    def invoke(service: Any, principal: Any, args: dict[str, Any]) -> Any:
        if getattr(principal, "kind", None) is PrincipalKind.AGENT:
            raise OperationOwnerRequired(name)
        if name != "phone.redeem" and getattr(principal, "kind", None) is not PrincipalKind.OWNER and not args.get("device"):
            raise OperationOwnerRequired(name)
        return call(service, principal, args)
    return invoke


def _by(args: dict[str, Any]) -> Optional[Mapping[str, Any]]:
    return args.get("device")


_D, _M, _C = "/api/phone/devices", "/api/phone/messages", "/api/phone/calls"
PHONE_OPERATIONS: tuple[OperationDescriptor, ...] = (
    # The owner's routes (the edge right is OWNER): produced.
    _op("phone.devices", "devices", ("GET", _D), "api_phone_devices",
        lambda s, p, a: s.devices(p), "List the owner's paired phones."),
    _op("phone.revoke", "revoke", ("DELETE", _D + "/{device_id}"), "api_phone_device_revoke",
        lambda s, p, a: s.revoke(p, a.get("device_id")),
        "Revoke a paired phone: its token stops at once and its socket closes.", write=True, authority="authority"),
    _op("phone.let_wait", "let_wait", ("POST", _M + "/{message_id}/wait"), "api_phone_message_wait",
        lambda s, p, a: s.let_wait(p, a.get("message_id")),
        "Let a phone ask wait: it leaves Needs you; the thread keeps it.", write=True),
    _op("phone.calls", "calls", ("GET", _C), "api_phone_calls",
        lambda s, p, a: s.calls(), "List the calls to the owner's phone."),
    _op("phone.ring", "ring_held", ("POST", _C + "/{call_id}/ring"), "api_phone_call_ring",
        lambda s, p, a: s.ring_held(p, a.get("call_id")), "Let a held call ring now (Call now).", write=True,
        authority="egress"),
    _op("phone.again", "call_again", ("POST", _C + "/{call_id}/again"), "api_phone_call_again",
        lambda s, p, a: s.call_again(p, a.get("call_id")), "Call again about a missed call (Call again).",
        write=True, authority="egress"),
    _op("phone.push_key", "push_key", ("GET", "/api/phone/push"), "api_phone_push",
        lambda s, p, a: s.push_key(p), "Say which parts of the Apple push key are saved (never the key)."),
    _op("phone.save_push_key", "save_push_key", ("PUT", "/api/phone/push"), "api_phone_push_save",
        lambda s, p, a: s.save_push_key(p, a),
        "Save parts of the Apple push key (p8, key_id, team_id, bundle_id, host) in the key store.",
        write=True, tool=False, authority="config"),
    _op("phone.test_push", "test_push", ("POST", "/api/phone/push/test"), "api_phone_push_test",
        lambda s, p, a: s.test_push(p), "Send one silent push to the newest paired phone; return Apple's answer.",
        write=True, authority="egress"),
    # The pairing redeem: no principal; the one-time pairing token in the body is the credential. The
    # route holds the hub address the redeem reached (``origin``); it must be the one Pair was pressed on.
    _op("phone.redeem", "redeem", ("POST", _D), "api_phone_devices_pair",
        lambda s, p, a: s.redeem({k: v for k, v in a.items() if k != "origin"}, origin=a["origin"]),
        "Redeem a pairing token (the phone app): the device token.", write=True, tool=False, owner_only=False,
        held=("origin",), authority="authority", status=201,
        principal="none: the one-time pairing token in the body is the credential (the edge lets the route through)"),
    # Hand-written routes (web/routes/phone.py) that invoke these rows.
    _op("phone.pair", "pair_token", ("POST", "/api/phone/pair"), "api_phone_pair",
        lambda s, p, a: s.pair_token(p, hub_urls=a["hub_urls"]),
        "Make a 10-minute pairing token and its QR.", write=True, tool=False, held=("hub_urls",),
        authority="authority", status=201),
    _op("phone.messages", "messages", ("GET", _M), "api_phone_messages",
        lambda s, p, a: s.messages(after_seq=int(a.get("after_seq") or 0)),
        "List the phone messages after after_seq, each with the verbs of the item it asks about.",
        principal=_OWNER_OR_AGENT, owner_only=False,
        properties={"after_seq": {"type": "integer", "minimum": 0}}),
    _op("phone.mark_read", "mark_read", ("POST", _M + "/{message_id}/read"), "api_phone_message_read",
        lambda s, p, a: s.mark_read(a.get("message_id"), by="phone" if _by(a) else "desk"),
        "Mark a phone message read.", principal=_OWNER_OR_DEVICE, owner_only=False, write=True, tool=False,
        held=("device",)),
    _op("phone.decide", "decide", ("POST", _M + "/{message_id}/decide"), "api_phone_message_decide",
        lambda s, p, a: s.decide(a.get("message_id"), a.get("choice"), device=_by(a), expected_commit_binding=a.get("expected_commit_binding")),
        "Press a message's verb: the item's own verb as the owner's press.",
        principal="the owner (hub token) or the paired phone (device token, HELD as ``device``); never an agent",
        owner_only=False, write=True, tool=False, held=("device",), authority="authority"),
    _op("phone.get_call", "get_call", ("GET", _C + "/{call_id}"), "api_phone_call_get",
        lambda s, p, a: s.get_call(a.get("call_id")), "Read one call with its transcript.",
        principal=_OWNER_OR_AGENT, owner_only=False),
    *(_op(f"phone.{verb}", verb, ("POST", f"{_C}/{{call_id}}/{verb}"), f"api_phone_call_{verb}",
          lambda s, p, a, verb=verb: getattr(s, verb)(a.get("call_id"), device=_by(a)),
          f"{verb.capitalize()} a call.", principal=_OWNER_OR_DEVICE, owner_only=False, write=True,
          tool=False, held=("device",), authority="authority")
      for verb in ("accept", "decline", "end")),
)

# These are transport implementation calls, HTTP-only, never model tools.
# authenticate rechecks the saved device row on EVERY request, including sockets.
PHONE_OPERATIONS += (
    OperationDescriptor(name="phone.authenticate", version=1,
        description="Authenticate the paired device token held by the HTTP or socket transport.",
        args_schema={"type": "object", "additionalProperties": False}, principal="the device token held by the transport; never an agent",
        effect="read", result="the paired device row, or None", refusals=_REFUSALS,
        completion="synchronous", exposure=("http:device-token authentication",),
        service="phone_service", method="authenticate", held=("token",),
        call=lambda s, p, a: _authenticate(s, p, a["token"])),
    OperationDescriptor(name="phone.hub", version=1, description="Read the hub id for an authenticated phone socket hello.",
        args_schema={"type": "object", "additionalProperties": False}, principal="the owner or paired phone, held by the socket transport",
        effect="read", result="the hub id", refusals=_REFUSALS, completion="synchronous",
        exposure=("http:WEBSOCKET /api/phone/ws",), service="phone_service", method="hub", held=("device",),
        call=_device_call("phone.hub", lambda s, p, a: s.hub())),
)


def _authenticate(service: Any, principal: Any, token: str) -> Any:
    if getattr(principal, "kind", None) is PrincipalKind.AGENT:
        raise OperationOwnerRequired("phone.authenticate")
    return service.authenticate(token)


#: The rows whose routes ``operation_router`` produces (the owner's edge, or no principal).
PRODUCED: tuple[str, ...] = ("phone.devices", "phone.revoke", "phone.let_wait", "phone.calls",
                             "phone.ring", "phone.again", "phone.push_key", "phone.save_push_key", "phone.test_push")


class _LivePhoneService:
    """The bound target: the process's one PhoneService, read at each call
    (``default_phone_service``); with the phone off, a call is refused by name."""

    def __getattr__(self, name: str) -> Any:
        from holdspeak.phone import phone_on
        from holdspeak.phone import service as phone

        if not phone_on():
            raise phone.PhoneRefused("phone_off", "The phone is off on this hub.", 409)
        return getattr(phone.default_phone_service(), name)


LIVE_PHONE_SERVICE = _LivePhoneService()

__all__ = ["LIVE_PHONE_SERVICE", "PHONE_OPERATIONS", "PRODUCED"]
