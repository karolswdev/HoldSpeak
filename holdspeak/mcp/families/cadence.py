"""Cadence family — MCP tools for the CadenceService surface."""
from __future__ import annotations

from typing import Any

from holdspeak.principals import Principal

TOOLS: list[dict[str, Any]] = []


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call.  Raises LookupError for unowned names."""
    raise LookupError(name)
