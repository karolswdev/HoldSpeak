"""Coder family — the MCP tools for a coder session that no route twins.

``coder.get`` reads one session. ``coder.explain`` is declared. The other coder tools (``coder.list``, ``coder.audit``, the board and
steering verbs) are produced from ``holdspeak/coder_operations.py``
(``mcp/families/declared.py``)."""
from __future__ import annotations

from holdspeak.runtime.composition import db_or, observer_or, service as runtime_service

from typing import Any

from holdspeak.db import get_database
from holdspeak.db.core import get_observer
from holdspeak.principals import Principal
from holdspeak.services.coder_service import CoderService

TOOLS: list[dict[str, Any]] = [
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

]


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call.  Raises LookupError for unowned names."""
    if name != "coder.get":
        raise LookupError(name)

    svc = CoderService(db=db_or(get_database), reply_sender=None, observer=observer_or(get_observer))

    return svc.get_session(principal, str(arguments.get("session_id") or ""))
