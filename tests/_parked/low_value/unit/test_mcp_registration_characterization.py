# Parked 2026-11-09 (tests/low-value-read): P8: pins which MCP family modules exist and that each exports TOOLS/dispatch (an HS-157 registration snapshot); a missing tool fails the MCP tests that call it
# Kept, not run; move back to tests/unit/test_mcp_registration_characterization.py to restore.
"""HS-157-04 — MCP family registration characterization.

Pin the registration truth that the Project Room graduation (P6) builds on:
the family module list, the Watch/Reaction tool names and schemas, and the
absence of a ``project.*`` family.  Written so that adding an unrelated new
family does NOT break these tests.
"""
from __future__ import annotations

import pytest

from holdspeak.mcp.families import FAMILIES


# ---------------------------------------------------------------------------
# (a) Family module list — Project-relevant facts only
# ---------------------------------------------------------------------------

class TestFamilyModuleList:
    """Pin the Project-relevant facts about the family list."""

    @staticmethod
    def _family_names() -> set[str]:
        return {f.__name__.rsplit(".", 1)[-1] for f in FAMILIES}

    def test_reactions_family_is_parked(self):
        """The reactions family (Watch/Reaction tools) is parked since the
        watch fold (2026-11-08): an Automation's event start is a watch."""
        assert "reactions" not in self._family_names()

    def test_project_family_registered(self):
        """The ``project`` family exists as of HS-165 (this test began
        life asserting its ABSENCE — the starting fact P6 built on)."""
        assert "project" in self._family_names()
        mod = __import__("holdspeak.mcp.families.project", fromlist=["TOOLS"])
        assert isinstance(mod.TOOLS, list) and mod.TOOLS

    def test_every_family_exports_tools_and_dispatch(self):
        """Each registered family module exports TOOLS (list) and dispatch."""
        for family in FAMILIES:
            assert hasattr(family, "TOOLS"), f"{family.__name__} missing TOOLS"
            assert isinstance(family.TOOLS, list), f"{family.__name__}.TOOLS is not a list"
            assert callable(getattr(family, "dispatch", None)), (
                f"{family.__name__} missing callable dispatch"
            )


# ---------------------------------------------------------------------------
# (b) Watch/Reaction tool names and representative schema
# ---------------------------------------------------------------------------

