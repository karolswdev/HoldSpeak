"""Coder family — MCP tools for the CoderService surface."""
from __future__ import annotations

from typing import Any

from holdspeak.db import get_database
from holdspeak.db.core import get_observer
from holdspeak.principals import Principal
from holdspeak.services.coder_service import CoderService

TOOLS: list[dict[str, Any]] = [
    {
        "name": "coder.list",
        "description": "List coder sessions. Steering verbs are out-of-scope for the MCP sidecar.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "description": "Filter by agent name."},
                "include_ended": {"type": "boolean", "description": "Include ended sessions (default true)."},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "coder.get",
        "description": "Get one coder session by agent:session_id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session id in agent:session_id format."},
            },
            "required": ["session_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "coder.audit",
        "description": "Read the bounded steering audit trail for coder sessions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_key": {"type": "string", "description": "Filter by session key."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500, "description": "Maximum entries (default 50)."},
            },
            "additionalProperties": False,
        },
    },
]


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call.  Raises LookupError for unowned names."""
    if name not in ("coder.list", "coder.get", "coder.audit"):
        raise LookupError(name)

    svc = CoderService(db=get_database(), reply_sender=None, observer=get_observer())

    if name == "coder.list":
        kwargs: dict[str, Any] = {}
        if "agent" in arguments:
            kwargs["agent"] = arguments["agent"]
        if "include_ended" in arguments:
            kwargs["include_ended"] = arguments["include_ended"]
        return svc.list_sessions(principal, **kwargs)

    if name == "coder.get":
        return svc.get_session(principal, str(arguments.get("session_id") or ""))

    # coder.audit
    session_key = arguments.get("session_key")
    limit = arguments.get("limit", 50)
    return svc.list_steering_audit(principal, session_key, limit)
