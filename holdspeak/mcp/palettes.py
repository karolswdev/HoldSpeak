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
# 2026-09-29): every ``work`` tool, so a new tool classifies itself.
#
# * egress, authority and config tools stop for the owner's press: not offered;
# * People (owner ruling 2026-10-06, "agents should totally be able to look it
#   up via mcp"): the family's READS are offered (``people.READ_TOOLS``) and the
#   People resources are readable; every People WRITE stays out. The owner's
#   ``HOLDSPEAK_MCP_PEOPLE_ACCESS=off`` takes the reads away from agents too.
#
# A mixed tool (``ARGUMENT_AUTHORITY``) is offered, and each call is classed on
# its arguments: a call that would schedule or delegate is refused.

CONDUCTOR = "CONDUCTOR"

#: The People family and resources: reads only, and none when the owner set
#: People MCP access to ``off``.
PEOPLE_PREFIX = "people."
PEOPLE_RESOURCE_PREFIX = "holdspeak://people/"


def _people_reads() -> frozenset[str]:
    from holdspeak.mcp.families import people

    try:
        mode = people.access_mode()
    except Exception:  # an unknown value is refused by the family: no reads
        return frozenset()
    return frozenset() if mode == "off" else people.READ_TOOLS


def _people_allowed(name: str) -> bool:
    """A People tool is offered only as a read, and only while access is on."""
    return not name.startswith(PEOPLE_PREFIX) or name in _people_reads()

#: The owner's Confirm: tools that confirm a decision or a proposal on his
#: behalf (mint a decision record, confirm or drop a proposal, accept a
#: review). A launched agent proposes; the owner confirms (ruling on #903).
CONDUCTOR_OWNER_CONFIRM: frozenset[str] = frozenset({
    "decision_record.create_from_desk",
    "decision_record.create_from_meeting",
    "proposal.confirm",
    "proposal.dismiss",
    "project.decide_proposal",
    "project.accept_review",
})


def _lazy_conductor_tools() -> frozenset[str]:
    from holdspeak.mcp.tool_authority import TOOL_AUTHORITY, WORK

    return frozenset(
        name
        for name in _lazy_all_tools()
        if TOOL_AUTHORITY.get(name) == WORK
        and _people_allowed(name)
        and name not in CONDUCTOR_OWNER_CONFIRM
        and name not in _not_offered()
    )


def _not_offered() -> frozenset[str]:
    """The tools the launch audit never offers (``services/conductor_launch``)."""
    from holdspeak.services.conductor_launch import NOT_OFFERED

    return NOT_OFFERED


def _decision_not_proposed(name: str, arguments: dict[str, Any]) -> bool:
    """A desk decision the agent writes is a PROPOSAL: status ``proposed``."""
    if name == "desk.verb" and arguments.get("verb_id") == "desk.create":
        inner = arguments.get("arguments")
        return _decision_not_proposed("desk.create", inner if isinstance(inner, dict) else {})
    if name != "desk.create" or arguments.get("kind") != "decisions":
        return False
    data = arguments.get("data") if isinstance(arguments.get("data"), dict) else {}
    return str(data.get("status") or "proposed").strip().lower() != "proposed"


def conductor_call_allowed(name: str, arguments: Any) -> bool:
    """One CONDUCTOR call, classed on its arguments (a mixed tool's predicate)."""
    from holdspeak.mcp.tool_authority import TOOL_AUTHORITY, WORK, call_class

    if name not in TOOL_AUTHORITY or not _people_allowed(name):
        return False
    if name in CONDUCTOR_OWNER_CONFIRM or name in _not_offered():
        return False
    args = arguments if isinstance(arguments, dict) else {}
    if _decision_not_proposed(name, args):
        return False
    return call_class(name, args) == WORK


def conductor_resource_allowed(uri: str) -> bool:
    """A CONDUCTOR resource read: People resources while People access is on."""
    return not str(uri or "").startswith(PEOPLE_RESOURCE_PREFIX) or bool(_people_reads())


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
