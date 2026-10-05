"""Every name in ``holdspeak/mcp/long_tools.py`` is a real MCP tool (a typo would silently queue it)."""
from __future__ import annotations

from holdspeak.mcp.long_tools import LONG_TOOLS
from holdspeak.mcp.tool_authority import TOOL_AUTHORITY


def test_every_long_tool_is_a_real_tool() -> None:
    assert set(LONG_TOOLS) - set(TOOL_AUTHORITY) == set()
    assert all(reason for reason in LONG_TOOLS.values())
