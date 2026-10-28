"""Calls family (2026-10-28): the hub's phone calls, through the one service
(``holdspeak.calls.service``) the REST routes use.

``calls.status`` and ``calls.list`` read; ``calls.hangup`` ends a call;
``calls.place`` places a real call (EGRESS, ``mcp/tool_authority.py``): only
the owner's principal may call it; an agent's call is refused.
"""
from __future__ import annotations

from typing import Any

from holdspeak.principals import Principal

_NO_ARGS = {"type": "object", "properties": {}, "additionalProperties": False}

TOOLS: list[dict[str, Any]] = [
    {
        "name": "calls.status",
        "description": "Read the phone line: whether ai-phone is found and running, its lines, the engine a call runs on, whether a passphrase is set, whether the hub waits for calls, the active call, and the setup steps.",
        "inputSchema": _NO_ARGS,
    },
    {
        "name": "calls.list",
        "description": "List the last 20 phone calls, newest first: direction, state, first words, what each call did, and its note.",
        "inputSchema": _NO_ARGS,
    },
    {
        "name": "calls.place",
        "description": "Place a phone call through ai-phone (relay mode). With no number, HoldSpeak calls the owner's own number (the first allowed number in Settings > Calls). A real call can cost money.",
        "inputSchema": {
            "type": "object",
            "properties": {"to": {"type": "string", "description": "A +E.164 number or a sip: address. Empty: the owner's own number."}},
            "additionalProperties": False,
        },
    },
    {
        "name": "calls.hangup",
        "description": "End a phone call: HoldSpeak says goodbye and hangs up.",
        "inputSchema": {
            "type": "object",
            "properties": {"call_id": {"type": "string", "description": "The call id: calls[].id from calls.list."}},
            "required": ["call_id"],
            "additionalProperties": False,
        },
    },
]


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call. Raises LookupError for unowned names."""
    from holdspeak.calls.service import CALLS
    from holdspeak.services.errors import NotFound

    if name == "calls.status":
        return CALLS.status()
    if name == "calls.list":
        return {"calls": CALLS.list()}
    if name == "calls.place":
        from holdspeak.principals import PrincipalKind
        from holdspeak.services.errors import ServiceError

        if principal.kind != PrincipalKind.OWNER:
            # A real call is egress: the owner's press, never an agent's.
            raise ServiceError("owner_principal_required", "Only the owner places a call.",
                               context={"status": 403})
        return CALLS._on_loop(CALLS.place(str(arguments.get("to") or "")))
    if name == "calls.hangup":
        call_id = str(arguments.get("call_id") or "")
        found = CALLS._on_loop(CALLS.hangup(call_id))
        if found is None:
            raise NotFound("call", call_id)
        return found
    raise LookupError(name)
