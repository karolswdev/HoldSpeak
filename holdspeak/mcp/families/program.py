"""Program family (2026-10-28, design §7): the Programs engine over MCP.

The tool rows are produced from the Programs operation descriptors
(``holdspeak/program_operations.py``, on the one contract in
``holdspeak/operations.py``), the rows the HTTP routes come from too; each
call goes through ``OperationRegistry.invoke``. The authority rules live in
the service, so every transport keeps them; the descriptors' module names them.
"""
from __future__ import annotations

from typing import Any

from holdspeak import operations
from holdspeak.principals import Principal

TOOLS: list[dict[str, Any]] = [op.tool() for op in operations.PROGRAM_OPERATIONS if op.tool_schema is not None]

NAMES = frozenset(tool["name"] for tool in TOOLS)


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call to its operation. Raises LookupError for unowned names."""
    if name not in NAMES:
        raise LookupError(name)
    registry = operations.for_runtime(program_service=lambda: operations.LIVE_PROGRAM_SERVICE)
    return registry.invoke(principal, name, dict(arguments or {}))


__all__ = ["NAMES", "TOOLS", "dispatch"]
