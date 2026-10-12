"""Phase 133 dispatch tests for the coder and memory tool families."""
from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.mcp import server
from holdspeak.mcp.families import coder as coder_family
from holdspeak.mcp.families import memory as memory_family
from holdspeak.mcp.server import handle_message
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import NotFound, ValidationError

OWNER = Principal(PrincipalKind.OWNER, "phase133-coder-memory-test")


def _call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Send a tools/call request through handle_message and return the result."""
    response = handle_message({
        "jsonrpc": "2.0",
        "id": name,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    assert response is not None
    return response["result"]


@pytest.fixture(autouse=True)
def _patch_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))


# ---------------------------------------------------------------------------
# coder.list
# ---------------------------------------------------------------------------

class _StubCoderService:
    """Minimal CoderService stand-in capturing call arguments."""

    def __init__(self, **_kw: Any) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []

    def list_sessions(self, principal: Any, **kwargs: Any) -> list[dict]:
        self.calls.append(("list_sessions", (principal,), kwargs))
        return [{"session": "s1"}]

    def get_session(self, principal: Any, session_id: str) -> dict:
        self.calls.append(("get_session", (principal, session_id), {}))
        if session_id == "agent:unknown":
            raise NotFound("coder session", session_id)
        return {"session_id": session_id}

    def list_steering_audit(self, principal: Any, session_key: str | None, limit: int) -> list[dict]:
        self.calls.append(("list_steering_audit", (principal, session_key, limit), {}))
        return [{"entry": "e1"}]


@pytest.fixture()
def _patch_coder(monkeypatch: pytest.MonkeyPatch) -> _StubCoderService:
    stub = _StubCoderService()
    monkeypatch.setattr(coder_family, "CoderService", lambda **_kw: stub)
    monkeypatch.setattr(coder_family, "get_database", lambda: object())
    monkeypatch.setattr(coder_family, "get_observer", lambda: None)
    return stub


def test_coder_list_dispatches(_patch_coder: _StubCoderService) -> None:
    result = _call("coder.list", {})
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload == [{"session": "s1"}]
    assert _patch_coder.calls[0][0] == "list_sessions"


def test_coder_list_passes_filters(_patch_coder: _StubCoderService) -> None:
    result = _call("coder.list", {"agent": "claude", "include_ended": False})
    assert result["isError"] is False
    call = _patch_coder.calls[0]
    assert call[2] == {"agent": "claude", "include_ended": False}


def test_coder_get_dispatches(_patch_coder: _StubCoderService) -> None:
    result = _call("coder.get", {"session_id": "agent:sess1"})
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload["session_id"] == "agent:sess1"


def test_coder_get_unknown_session_returns_is_error(_patch_coder: _StubCoderService) -> None:
    result = _call("coder.get", {"session_id": "agent:unknown"})
    assert result["isError"] is True
    payload = json.loads(result["content"][0]["text"])
    assert "error" in payload


def test_coder_audit_dispatches(_patch_coder: _StubCoderService) -> None:
    result = _call("coder.audit", {"session_key": "sk1", "limit": 10})
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload == [{"entry": "e1"}]
    call = _patch_coder.calls[0]
    assert call[1] == (OWNER, "sk1", 10)


def test_coder_audit_default_limit(_patch_coder: _StubCoderService) -> None:
    result = _call("coder.audit", {})
    assert result["isError"] is False
    call = _patch_coder.calls[0]
    # Default limit should be 50, session_key None
    assert call[1] == (OWNER, None, 50)


# ---------------------------------------------------------------------------
# memory.search
# ---------------------------------------------------------------------------

class _StubMemoryService:
    """Minimal MemoryService stand-in capturing call arguments."""

    def __init__(self, **_kw: Any) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []

    def search(self, principal: Any, query: str, **kwargs: Any) -> dict:
        self.calls.append(("search", (principal, query), kwargs))
        if not query:
            raise ValidationError("query is required")
        return {"results": [{"id": "m1"}], "total": 1}


@pytest.fixture()
def _patch_memory(monkeypatch: pytest.MonkeyPatch) -> _StubMemoryService:
    stub = _StubMemoryService()
    monkeypatch.setattr(memory_family, "MemoryService", lambda **_kw: stub)
    monkeypatch.setattr(memory_family, "get_database", lambda: object())
    monkeypatch.setattr(memory_family, "get_observer", lambda: None)
    return stub


def test_memory_search_dispatches(_patch_memory: _StubMemoryService) -> None:
    result = _call("memory.search", {"query": "meeting notes"})
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload["total"] == 1
    assert _patch_memory.calls[0][1] == (OWNER, "meeting notes")


def test_memory_search_passes_filters(_patch_memory: _StubMemoryService) -> None:
    result = _call("memory.search", {
        "query": "q",
        "kind": "note",
        "project_id": "proj1",
        "time_from": "2026-01-01",
        "time_to": "2026-12-31",
        "limit": 10,
        "offset": 5,
    })
    assert result["isError"] is False
    kwargs = _patch_memory.calls[0][2]
    assert kwargs == {
        "kind": "note",
        "project_id": "proj1",
        "time_from": "2026-01-01",
        "time_to": "2026-12-31",
        "limit": 10,
        "offset": 5,
    }


def test_memory_search_missing_query_returns_is_error(_patch_memory: _StubMemoryService) -> None:
    result = _call("memory.search", {})
    assert result["isError"] is True
    payload = json.loads(result["content"][0]["text"])
    assert "error" in payload


# ---------------------------------------------------------------------------
# Catalogue presence
# ---------------------------------------------------------------------------

def test_coder_tools_in_catalogue() -> None:
    """All three coder tools appear in tools/list with closed schemas."""
    response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert response is not None
    tools = response["result"]["tools"]
    names = {t["name"] for t in tools}
    expected = {"coder.list", "coder.get", "coder.audit"}
    assert expected <= names

    for tool in tools:
        if tool["name"] in expected:
            assert tool["inputSchema"]["type"] == "object"
            assert tool["inputSchema"]["additionalProperties"] is False


def test_memory_search_in_catalogue() -> None:
    """memory.search appears in tools/list with a closed schema."""
    response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert response is not None
    tools = response["result"]["tools"]
    names = {t["name"] for t in tools}
    assert "memory.search" in names

    tool = next(t for t in tools if t["name"] == "memory.search")
    assert tool["inputSchema"]["type"] == "object"
    assert tool["inputSchema"]["additionalProperties"] is False
    assert "query" in tool["inputSchema"].get("required", [])
