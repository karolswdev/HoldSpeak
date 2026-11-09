"""Phase 133 registry tests: family aggregation and dispatch routing."""
from __future__ import annotations

import json
from types import SimpleNamespace, ModuleType
from typing import Any

import pytest

from holdspeak.mcp import server, tools as mcp_tools
from holdspeak.mcp.server import handle_message
from holdspeak.mcp.tools import TOOLS
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "phase133-test")

# Import REQUIRED_TOOLS from the catalogue test so we stay in sync.
from tests.unit.test_mcp_tools import REQUIRED_TOOLS


def _make_synthetic_family(tool_name: str = "synth.ping") -> ModuleType:
    """Build a fake family module with one tool and a dispatch that returns it."""
    mod = ModuleType("synthetic_family")
    mod.TOOLS = [
        {
            "name": tool_name,
            "description": "Synthetic test tool.",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        }
    ]

    def _dispatch(name: str, arguments: dict[str, Any], principal: Any) -> Any:
        if name == tool_name:
            return {"pong": True, "principal": str(principal)}
        raise LookupError(name)

    mod.dispatch = _dispatch
    return mod


def test_synthetic_family_tool_appears_in_catalogue(monkeypatch: pytest.MonkeyPatch) -> None:
    """A family-registered tool appears in tools/list through handle_message."""
    synth = _make_synthetic_family("synth.ping")
    original_families = list(mcp_tools.FAMILIES)
    original_tools = list(mcp_tools.TOOLS)

    # Inject the synthetic family into the FAMILIES list and TOOLS catalogue.
    monkeypatch.setattr(mcp_tools, "FAMILIES", original_families + [synth])
    mcp_tools.TOOLS.extend(synth.TOOLS)

    try:
        response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        assert response is not None
        names = {t["name"] for t in response["result"]["tools"]}
        assert "synth.ping" in names

        # Verify closed schema.
        tool = next(t for t in response["result"]["tools"] if t["name"] == "synth.ping")
        assert tool["inputSchema"]["additionalProperties"] is False
    finally:
        mcp_tools.TOOLS[:] = original_tools


def test_synthetic_family_tool_dispatches_through_family(monkeypatch: pytest.MonkeyPatch) -> None:
    """A family-owned tool dispatches to the family callable via tools/call."""
    synth = _make_synthetic_family("synth.ping")
    original_families = list(mcp_tools.FAMILIES)

    monkeypatch.setattr(mcp_tools, "FAMILIES", original_families + [synth])
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))

    response = handle_message({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "synth.ping", "arguments": {}},
    })
    assert response is not None
    result = response["result"]
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload["pong"] is True


def test_owned_dispatch_key_error_surfaces_not_unknown_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    """A KeyError inside an owned family dispatch surfaces as the real error.

    Ownership is decided by name membership, so a LookupError subclass raised
    by the service must never read as "not mine" and fall through to the
    legacy chain's Unknown-tool error.
    """
    synth = _make_synthetic_family("synth.boom")

    def _exploding_dispatch(name: str, arguments: dict[str, Any], principal: Any) -> Any:
        if name == "synth.boom":
            raise KeyError("boom")
        raise LookupError(name)

    synth.dispatch = _exploding_dispatch
    original_families = list(mcp_tools.FAMILIES)
    monkeypatch.setattr(mcp_tools, "FAMILIES", original_families + [synth])
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))

    response = handle_message({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "synth.boom", "arguments": {}},
    })
    assert response is not None
    result = response["result"]
    assert result["isError"] is True
    message = result["content"][0]["text"]
    assert "boom" in message
    assert "Unknown tool" not in message


def test_required_tools_still_present_in_catalogue() -> None:
    """The existing REQUIRED_TOOLS set is still fully covered by tools/list."""
    response = handle_message({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
    assert response is not None
    names = {t["name"] for t in response["result"]["tools"]}
    missing = REQUIRED_TOOLS - names
    assert not missing, f"Missing from catalogue: {missing}"


def test_no_tool_name_is_in_two_families() -> None:
    """2026-11-08: the declared family makes every descriptor's tool; no hand-written tool may repeat one."""
    from collections import Counter

    from holdspeak.mcp.families import FAMILIES

    owned = [tool["name"] for family in FAMILIES for tool in family.TOOLS]
    family_names = set(owned)
    main_only = [tool["name"] for tool in TOOLS if tool["name"] not in family_names]
    repeated = [name for name, count in Counter(owned + main_only).items() if count > 1]
    assert not repeated, repeated
    assert len(TOOLS) == len({tool["name"] for tool in TOOLS})


def test_every_declared_tool_schema_is_a_declared_tool() -> None:
    from holdspeak import operations
    from holdspeak.mcp.families import declared

    with_schema = {d.tool_name for d in operations.DESCRIPTORS if d.tool_schema is not None}
    assert declared.NAMES == with_schema
    assert {"meeting.facets", "action_item.update", "program.get"} <= declared.NAMES


def test_a_declared_meeting_tool_runs_through_the_registry(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """meeting.facets and speaker.list were web-only; their descriptors make the MCP tools."""
    from holdspeak.db import Database

    db = Database(tmp_path / "declared.db")
    monkeypatch.setattr(mcp_tools, "get_database", lambda: db)
    assert mcp_tools.dispatch("meeting.facets", {}, OWNER) == db.meetings.list_facet_values()
    assert mcp_tools.dispatch("speaker.list", {}, OWNER) == {"speakers": [], "total": 0}
    assert mcp_tools.dispatch("meeting.ready_list", {}, OWNER) == {"meetings": []}
