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


def test_required_tools_still_present_in_catalogue() -> None:
    """The existing REQUIRED_TOOLS set is still fully covered by tools/list."""
    response = handle_message({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
    assert response is not None
    names = {t["name"] for t in response["result"]["tools"]}
    missing = REQUIRED_TOOLS - names
    assert not missing, f"Missing from catalogue: {missing}"
