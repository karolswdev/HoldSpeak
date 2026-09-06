"""HS-157-04 — MCP family registration characterization.

Pin the registration truth that the Project Room graduation (P6) builds on:
the family module list, the Watch/Reaction tool names and schemas, and the
absence of a ``project.*`` family.  Written so that adding an unrelated new
family does NOT break these tests.
"""
from __future__ import annotations

import pytest

from holdspeak.mcp.families import FAMILIES
from holdspeak.mcp.families import reactions


# ---------------------------------------------------------------------------
# (a) Family module list — Project-relevant facts only
# ---------------------------------------------------------------------------

class TestFamilyModuleList:
    """Pin the Project-relevant facts about the family list."""

    @staticmethod
    def _family_names() -> set[str]:
        return {f.__name__.rsplit(".", 1)[-1] for f in FAMILIES}

    def test_reactions_family_is_registered(self):
        """The reactions family (Watch/Reaction tools) is in FAMILIES."""
        assert "reactions" in self._family_names()

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

class TestReactionsToolNames:
    """Pin the Watch/Reaction tool names from the reactions family."""

    def test_reactions_tool_names(self):
        """The reactions family registers exactly these tool names."""
        tool_names = sorted(t["name"] for t in reactions.TOOLS)
        assert tool_names == [
            "event.list",
            "reaction.create",
            "reaction.list",
            "reaction.presets",
            "reaction.process",
            "reaction.set_enabled",
            "watch.create",
            "watch.list",
            "watch.preview",
            "watch.refresh",
            "watch.set_enabled",
        ]

    def test_every_reactions_tool_has_a_valid_schema(self):
        """Every reactions tool carries name, description, and inputSchema."""
        for tool in reactions.TOOLS:
            assert "name" in tool, "tool missing name"
            assert "description" in tool, f"{tool.get('name')} missing description"
            assert "inputSchema" in tool, f"{tool['name']} missing inputSchema"
            schema = tool["inputSchema"]
            assert schema.get("type") == "object", f"{tool['name']} schema type != object"
            assert "properties" in schema, f"{tool['name']} schema missing properties"

    def test_watch_create_schema_shape(self):
        """Pin watch.create as the representative schema (the tool the
        graduation will extend with Project-scoped Watch support)."""
        watch_create = next(
            t for t in reactions.TOOLS if t["name"] == "watch.create"
        )
        schema = watch_create["inputSchema"]
        props = schema["properties"]
        assert "connector_id" in props
        assert "query_kind" in props
        assert "name" in props
        assert "query" in props
        assert props["connector_id"]["enum"] == ["gh", "github", "jira"]
        assert props["query_kind"]["enum"] == ["pull_requests", "issues"]
        assert set(schema["required"]) == {"connector_id", "query_kind"}

    def test_reactions_tools_appear_in_aggregated_catalogue(self):
        """The aggregated TOOLS list in tools.py includes reactions tools."""
        from holdspeak.mcp.tools import TOOLS as ALL_TOOLS
        all_names = {t["name"] for t in ALL_TOOLS}
        reactions_names = {t["name"] for t in reactions.TOOLS}
        assert reactions_names.issubset(all_names), (
            f"Missing from catalogue: {reactions_names - all_names}"
        )
