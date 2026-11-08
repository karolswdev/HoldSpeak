"""Program family (2026-10-28, design §7): the Programs engine over MCP.

The tool rows and the dispatch are produced from the one table of Programs
operations (``services/program_operations.py``); the HTTP routes
(``web/routes/programs.py``) are produced from the same rows. Every tool
reaches the one service the routes use
(``services/program_service.default_program_service``); the authority rules
live in the service, so every transport keeps them. The table's docstring
names them.
"""
from __future__ import annotations

from typing import Any

from holdspeak.principals import Principal
from holdspeak.services import program_operations

TOOLS: list[dict[str, Any]] = [op.tool() for op in program_operations.TOOL_ROWS]

NAMES = frozenset(tool["name"] for tool in TOOLS)


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call to its row. Raises LookupError for unowned names."""
    if name not in NAMES:
        raise LookupError(name)
    return program_operations.BY_NAME[name].call(program_operations.program_service(), principal,
                                                 dict(arguments or {}))


__all__ = ["NAMES", "TOOLS", "dispatch"]
