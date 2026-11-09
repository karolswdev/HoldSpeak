"""Declared family (2026-11-08): every declared operation's MCP tool.

The tool rows are produced from every descriptor in ``operations.DESCRIPTORS``
that declares a ``tool_schema`` (the Programs verbs, the meeting archive's
verbs, ...), the rows the HTTP routes come from too; each call goes through
``OperationRegistry.invoke`` on the hub's bound contract
(``mcp.tools.runtime_registry``). No per-family MCP file is needed for a
declared operation: give its descriptor a ``tool_schema`` and the tool is here.
The authority rules live in the services, so every transport keeps them.
"""
from __future__ import annotations

from typing import Any

from holdspeak import operations
from holdspeak.principals import Principal

TOOLS: list[dict[str, Any]] = [op.tool() for op in operations.DESCRIPTORS if op.tool_schema is not None]

NAMES = frozenset(tool["name"] for tool in TOOLS)

#: Each tool is the operation of its own name (``scripts/operation_parity.py`` reads this).
TOOL_OPERATIONS: dict[str, str] = {name: name for name in NAMES}


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call to its operation. Raises LookupError for unowned names."""
    if name not in NAMES:
        raise LookupError(name)
    from holdspeak.mcp.tools import runtime_registry  # tools.py imports this family

    return runtime_registry().invoke(principal, name, dict(arguments or {}))


__all__ = ["NAMES", "TOOLS", "TOOL_OPERATIONS", "dispatch"]
