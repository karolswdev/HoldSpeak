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

#: Tool name -> operation name: the operation's own name, or its ``mcp:``
#: exposure (``desk_window.list`` is ``windows.list``). ``scripts/operation_parity.py`` reads this.
TOOL_OPERATIONS: dict[str, str] = {op.tool_name: op.name for op in operations.DESCRIPTORS if op.tool_schema is not None}


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call to its operation. Raises LookupError for unowned names."""
    if name not in NAMES:
        raise LookupError(name)
    from holdspeak.mcp.tools import runtime_registry  # tools.py imports this family

    try:
        return runtime_registry().invoke(principal, TOOL_OPERATIONS[name], dict(arguments or {}))
    except operations.OperationRefused as exc:
        from holdspeak.services.errors import ServiceError

        # HTTP has ContractRefusal; MCP preserves the same named contract error
        # and its admission receipt, rather than dropping the code as ValueError.
        raise ServiceError(exc.code, exc.detail, context=dict(getattr(exc, "kernel", None) or {})) from exc


__all__ = ["NAMES", "TOOLS", "TOOL_OPERATIONS", "dispatch"]
