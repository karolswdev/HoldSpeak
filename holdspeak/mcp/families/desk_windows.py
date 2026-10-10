"""Desk windows family: an agent composes the owner's desk windows (PHILO-16 16b).

COMPOSITOR.md §13 L1: the hub owns the desk's windows, every browser is one
view of them, and the Conductor's agents reach the same windows. Each tool IS
its declared operation (``holdspeak/desk_window_operations.py``, the
``windows.*`` rows), invoked through the one registry and bound to the hub's
``DeskWindowService`` (the 2026-09-23 ruling: MCP flows through services).
``desk_window.list`` reads; ``open``, ``close``, ``raise``, ``arrange`` and
``seat`` write, and each write sends ONE ``desk_changed`` frame (kind
``windows``) so every open browser follows at once.

Authority (``mcp/tool_authority.py``): every tool is ``work`` -- a window is
not egress, authority or config. A launched agent meets the ``window`` launch
rule (``services/conductor_launch.py``), and its gate holds every tool that is
not a read in Secure (``coder_gate.mcp_tool_is_read``; ``list`` is the read).
"""
from __future__ import annotations

import copy
from typing import Any

from holdspeak.principals import Principal


def _tools() -> list[dict[str, Any]]:
    """Each tool IS its declared operation: one schema, one set of words."""
    from holdspeak.desk_window_operations import DESK_WINDOW_OPERATIONS, TOOL_OPERATIONS

    by_name = {d.name: d for d in DESK_WINDOW_OPERATIONS}
    tools = []
    for tool, operation in TOOL_OPERATIONS.items():
        descriptor = by_name[operation]
        schema = copy.deepcopy(dict(descriptor.args_schema))
        schema["$id"] = f"holdspeak://mcp/{tool}@{descriptor.version}"
        tools.append({"name": tool, "description": descriptor.description, "inputSchema": schema})
    return tools


TOOLS: list[dict[str, Any]] = _tools()


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    from holdspeak.desk_window_operations import TOOL_OPERATIONS

    operation = TOOL_OPERATIONS.get(name)
    if operation is None:
        raise LookupError(name)
    from holdspeak import operations
    from holdspeak.db import get_database
    from holdspeak.runtime.composition import db_or, service as runtime_service
    from holdspeak.services.desk_window_service import DeskWindowService

    ops = operations.for_runtime(
        desk_window_service=lambda: runtime_service(
            "desk_window_service", lambda: DeskWindowService(db_or(get_database))
        ),
    )
    return ops.invoke(principal, operation, dict(arguments or {}))


__all__ = ["TOOLS", "dispatch"]
