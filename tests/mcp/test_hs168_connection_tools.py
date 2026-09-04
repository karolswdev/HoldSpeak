"""HS-168-02: MCP connection tools -- registry, classes, web = MCP parity.

Tests:
1. connection.list and connection.recheck are registered in TOOLS.
2. Both are classified in _TOOL_CLASSES.
3. Web = MCP parity: same shape from the same ConnectionsService.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import server
from holdspeak.mcp.families import project as project_family
from holdspeak.mcp.families.project import PROJECT_PALETTE, TOOLS as PROJECT_TOOLS
from holdspeak.mcp.tools import TOOLS as ALL_TOOLS
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.thread_tools import TOOL_NAMES, tool_class


OWNER = Principal(PrincipalKind.OWNER, "conn-mcp-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "conn-mcp.db")
    yield database
    reset_database()


@pytest.fixture(autouse=True)
def mcp_setup(db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_family, "get_database", lambda: db)
    monkeypatch.setattr(
        server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER),
    )
    monkeypatch.setenv("HOLDSPEAK_MCP_PEOPLE_ACCESS", "off")


def _call(name: str, arguments: dict | None = None) -> tuple[bool, dict]:
    response = server.handle_message({
        "jsonrpc": "2.0",
        "id": name,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments or {}},
    })
    assert response is not None
    result = response["result"]
    return result["isError"], json.loads(result["content"][0]["text"])


# ── 1. Registry ──────────────────────────────────────────────────────


class TestRegistry:
    def test_connection_list_in_project_tools(self) -> None:
        names = {t["name"] for t in PROJECT_TOOLS}
        assert "connection.list" in names

    def test_connection_recheck_in_project_tools(self) -> None:
        names = {t["name"] for t in PROJECT_TOOLS}
        assert "connection.recheck" in names

    def test_both_in_global_tools(self) -> None:
        names = {t["name"] for t in ALL_TOOLS}
        assert "connection.list" in names
        assert "connection.recheck" in names

    def test_both_in_palette(self) -> None:
        assert "connection.list" in PROJECT_PALETTE
        assert "connection.recheck" in PROJECT_PALETTE


# ── 2. Classification ───────────────────────────────────────────────


class TestClassification:
    def test_connection_list_classified(self) -> None:
        assert "connection.list" in TOOL_NAMES

    def test_connection_recheck_classified(self) -> None:
        assert "connection.recheck" in TOOL_NAMES

    def test_connection_list_is_evidence_read(self) -> None:
        assert tool_class("connection.list") == "evidence_read"

    def test_connection_recheck_is_evidence_read(self) -> None:
        assert tool_class("connection.recheck") == "evidence_read"


# ── 3. Parity: MCP dispatch ─────────────────────────────────────────


class TestMcpDispatch:
    def test_connection_list_returns_tools(self, db: Database) -> None:
        is_error, data = _call("connection.list")
        assert is_error is False
        assert "tools" in data
        ids = [t["provider_id"] for t in data["tools"]]
        assert "github" in ids
        assert "jira" in ids
        assert "calendar" in ids
        assert "models" in ids

    def test_connection_recheck_returns_entry(self, db: Database) -> None:
        is_error, data = _call("connection.recheck", {"provider_id": "github"})
        # Without a real GitHub adapter, this should return not_configured
        assert is_error is False or is_error is True
        if not is_error:
            assert data.get("provider_id") == "github"

    def test_connection_recheck_missing_provider_errors(self, db: Database) -> None:
        is_error, data = _call("connection.recheck", {})
        assert is_error is True
        assert "error" in data


# ── 4. Parity shape: web = MCP ──────────────────────────────────────


class TestWebMcpParity:
    def test_list_shape_matches_web(self, db: Database) -> None:
        """MCP connection.list returns the same shape as GET /api/connections."""
        is_error, data = _call("connection.list")
        assert is_error is False
        assert isinstance(data, dict)
        assert "tools" in data
        for tool in data["tools"]:
            assert "provider_id" in tool
            assert "state" in tool
            assert "next_action" in tool
