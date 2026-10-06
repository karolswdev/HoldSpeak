"""Agent family: Hand to agent over MCP (docs/internal/CONDUCTOR.md, step 2).

``agent.hand`` is the declared operation of the same name
(``holdspeak/agent_operations.py``), an egress row in the authority census
(``mcp/tool_authority.py``): it starts a coding agent that runs on a cloud
model and sends it a brief built from the owner's desk. A thread never
offers it; the owner's own MCP client calls it as a press.
"""
from __future__ import annotations

from typing import Any

from holdspeak.principals import Principal


def _tool() -> dict[str, Any]:
    """``agent.hand`` IS its declared operation: one schema, one set of words."""
    import copy

    from holdspeak.agent_operations import AGENT_HAND as descriptor

    schema = copy.deepcopy(dict(descriptor.args_schema))
    schema["$id"] = f"holdspeak://mcp/agent.hand@{descriptor.version}"
    return {"name": "agent.hand", "description": descriptor.description, "inputSchema": schema}


TOOLS: list[dict[str, Any]] = [_tool()]


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    if name != "agent.hand":
        raise LookupError(name)
    from holdspeak import operations
    from holdspeak.db import get_database
    from holdspeak.runtime.composition import db_or, service as runtime_service
    from holdspeak.services.agent_hand_service import default_agent_hand_service

    ops = operations.for_runtime(
        agent_hand_service=lambda: runtime_service(
            "agent_hand_service", lambda: default_agent_hand_service(db_or(get_database))
        ),
    )
    return ops.invoke(principal, "agent.hand", dict(arguments or {}))


__all__ = ["TOOLS", "dispatch"]
