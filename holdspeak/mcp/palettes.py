"""HS-174: Named palette constants for remote credential scoping.

Palette names are the CycleGadget options in the credential issue well.
Per D4 H7: never remove a palette name; only add tools.
"""
from __future__ import annotations

from typing import Any


def _lazy_project_palette() -> frozenset[str]:
    """PROJECT palette -- every tool in the project family."""
    from holdspeak.mcp.families.project import PROJECT_PALETTE
    return PROJECT_PALETTE


def _lazy_heartbeat_names() -> frozenset[str]:
    """Heartbeat family tool names."""
    from holdspeak.mcp.families.heartbeat import TOOLS as HB_TOOLS
    return frozenset(t["name"] for t in HB_TOOLS)


def _lazy_all_tools() -> frozenset[str]:
    """Every registered MCP tool name."""
    from holdspeak.mcp.tools import TOOLS as ALL_TOOLS
    return frozenset(t["name"] for t in ALL_TOOLS)


def _lazy_desk_tools() -> frozenset[str]:
    """Desk-level tools (the top-level desk/workbench/meeting family)."""
    from holdspeak.mcp.tools import TOOLS as TOP_TOOLS
    return frozenset(t["name"] for t in TOP_TOOLS)


# ── Public API ──────────────────────────────────────────────────────────

PALETTE_NAMES: tuple[str, ...] = ("PROJECT", "SWEEP", "DESK", "ALL")


def resolve_palette(name: str) -> frozenset[str]:
    """Resolve a palette name to the set of allowed tool names.

    Raises ``ValueError`` for unknown palette names.
    """
    upper = str(name or "").strip().upper()
    if upper == "PROJECT":
        return _lazy_project_palette()
    if upper == "SWEEP":
        return _lazy_project_palette() | _lazy_heartbeat_names()
    if upper == "DESK":
        return _lazy_desk_tools()
    if upper == "ALL":
        return _lazy_all_tools()
    raise ValueError(f"Unknown palette: {name!r}")
