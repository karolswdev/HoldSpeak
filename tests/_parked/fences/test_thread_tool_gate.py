# PARKED 2026-11-09 (fences diet, pipe/fences-diet): "no phantom classification" fails when a tool is parked and its row stays; a stale row harms nothing.
# Replaced by: every dispatched tool has a row (test_thread_tool_gate.py, subset form).
"""Parked from tests/unit/test_thread_tool_gate.py (TestClassificationCensus)."""
from holdspeak.services.thread_tools import TOOL_NAMES


class TestClassificationCensus:
    def test_no_phantom_classifications(self) -> None:
        """No classifications for tools that do not exist in the MCP catalogue."""
        from holdspeak.mcp.tools import TOOLS as MCP_TOOLS

        mcp_names = {t["name"] for t in MCP_TOOLS}
        phantom = TOOL_NAMES - mcp_names
        assert phantom == set(), (
            f"Phantom tool classifications (remove from thread_tools._TOOL_CLASSES): "
            f"{sorted(phantom)}"
        )

