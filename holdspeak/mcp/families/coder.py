"""Coder family — the MCP tools for a coder session that no route twins.

``coder.get`` (one session) and ``coder.explain`` (why an agent has its
state). The other coder tools (``coder.list``, ``coder.audit``, the board and
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
    {
        "name": "coder.explain",
        "description": "Why an agent has its state: hook or screen rule, rule id, evidence lines, age.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "launch:<id>, a launch id, or agent:session_id."},
            },
            "required": ["target"],
            "additionalProperties": False,
        },
    },
]


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call.  Raises LookupError for unowned names."""
    if name not in ("coder.get", "coder.explain"):
        raise LookupError(name)

    if name == "coder.explain":
        # Betterment AG7: the hook or the screen rule behind the state.
        from holdspeak.services.agent_flights import explain_agent

        target = str(arguments.get("target") or "")
        answer = explain_agent(db_or(get_database), target)
        if answer is None:
            from holdspeak.services.errors import NotFound

            raise NotFound("agent", target)
        return answer

    svc = CoderService(db=db_or(get_database), reply_sender=None, observer=observer_or(get_observer))

    return svc.get_session(principal, str(arguments.get("session_id") or ""))
