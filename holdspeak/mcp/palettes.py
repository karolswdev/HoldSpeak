"""HS-174: Named palette constants for remote credential scoping.

Palette names are the CycleGadget options in the credential issue well.
Per D4 H7: never remove a palette name; only add tools.
"""
from __future__ import annotations

from typing import Any


def _lazy_project_palette() -> frozenset[str]:
    """PROJECT palette -- every tool in the project family, and the receipt read.

    PHILO-9-01: ``kernel.receipt`` joins PROJECT (and so SWEEP): an agent reads
    its own operation's receipt; the kernel's read scope refuses another
    principal's (``holdspeak/kernel/broker.py``). Palettes only gain tools.
    """
    from holdspeak.mcp.families.channel import CHANNEL_TOOLS
    from holdspeak.mcp.families.project import PROJECT_PALETTE

    # PHILO-10-01: the Send's tools join PROJECT (palettes only gain tools): a
    # connected agent prepares a send and reads what was sent; its send is
    # refused owner_principal_required with a receipt by the kernel.
    return PROJECT_PALETTE | {"kernel.receipt"} | CHANNEL_TOOLS


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


# ── CONDUCTOR: what an agent HoldSpeak launched may call ────────────────
#
# Conductor K6 (owner 2026-10-06: "the agent we spin up here - do we inject him
# with our HoldSpeak MCP? We certainly should"). The palette is DERIVED from the
# one authority table (``mcp/tool_authority.py``, the owner's thread rule of
# 2026-09-29): every ``work`` tool, so a new tool classifies itself. Two cuts:
#
# * egress, authority and config tools stop for the owner's press: not offered;
# * the People family is not offered at all. Claude Code and Codex run on cloud
#   models, and People data does not reach a cloud agent (the brief cuts it too,
#   ``services/agent_brief.py``). The People resources are refused the same way.
#
# A mixed tool (``ARGUMENT_AUTHORITY``) is offered, and each call is classed on
# its arguments: a call that would schedule or delegate is refused.

CONDUCTOR = "CONDUCTOR"

#: The families a launched agent never reaches, whatever their class.
CONDUCTOR_EXCLUDED_PREFIXES: tuple[str, ...] = ("people.",)
CONDUCTOR_EXCLUDED_RESOURCE_PREFIXES: tuple[str, ...] = ("holdspeak://people/",)


def _lazy_conductor_tools() -> frozenset[str]:
    from holdspeak.mcp.tool_authority import TOOL_AUTHORITY, WORK

    return frozenset(
        name
        for name in _lazy_all_tools()
        if TOOL_AUTHORITY.get(name) == WORK
        and not name.startswith(CONDUCTOR_EXCLUDED_PREFIXES)
    )


def conductor_call_allowed(name: str, arguments: Any) -> bool:
    """One CONDUCTOR call, classed on its arguments (a mixed tool's predicate)."""
    from holdspeak.mcp.tool_authority import TOOL_AUTHORITY, WORK, call_class

    if name not in TOOL_AUTHORITY or name.startswith(CONDUCTOR_EXCLUDED_PREFIXES):
        return False
    return call_class(name, arguments if isinstance(arguments, dict) else {}) == WORK


def conductor_resource_allowed(uri: str) -> bool:
    """A CONDUCTOR resource read: never a People resource."""
    return not str(uri or "").startswith(CONDUCTOR_EXCLUDED_RESOURCE_PREFIXES)


# ── Public API ──────────────────────────────────────────────────────────

#: The names the owner may issue in the Reach credential well. CONDUCTOR is
#: not one: only a launch issues it (``coder_factory.spawn``).
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
    if upper == CONDUCTOR:
        return _lazy_conductor_tools()
    raise ValueError(f"Unknown palette: {name!r}")
