"""The People MCP access setting (Conductor R7, owner 2026-10-06).

Owner: "the default should be on, for HOLDSPEAK_MCP_PEOPLE_ACCESS, and I
guess there's an affordance to set it somewhere, right?"

``mcp_access`` is ``off``, ``read`` or ``write`` (default ``write``: on). The
owner's MCP clients get the mode; an agent HoldSpeak launched gets ``read``
whenever the mode is not ``off`` (agents never write People). The
``HOLDSPEAK_MCP_PEOPLE_ACCESS`` environment variable, when set, overrides the
persisted value (``holdspeak/mcp/families/people.access_source``).
"""
from __future__ import annotations

from dataclasses import dataclass

ACCESS_MODES: tuple[str, ...] = ("off", "read", "write")
DEFAULT_ACCESS = "write"


@dataclass
class PeopleConfig:
    mcp_access: str = DEFAULT_ACCESS

    def __post_init__(self) -> None:
        value = str(self.mcp_access or "").strip().lower()
        self.mcp_access = value if value in ACCESS_MODES else DEFAULT_ACCESS
