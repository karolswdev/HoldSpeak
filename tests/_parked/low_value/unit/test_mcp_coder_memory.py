# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_mcp_coder_memory.py to restore.

# ruff: noqa


# --- test_coder_list_dispatches: P2: the stub returns a literal and the test reads that literal back through dispatch
def test_coder_list_dispatches(_patch_coder: _StubCoderService) -> None:
    result = _call("coder.list", {})
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload == [{"session": "s1"}]
    assert _patch_coder.calls[0][0] == "list_sessions"


# --- test_coder_get_dispatches: P2: the stub returns a literal and the test reads that literal back through dispatch
def test_coder_get_dispatches(_patch_coder: _StubCoderService) -> None:
    result = _call("coder.get", {"session_id": "agent:sess1"})
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload["session_id"] == "agent:sess1"


# --- test_coder_tools_in_catalogue: P6: asserts tool names and closed-schema flags in the catalogue; the dispatch tests call the same tools
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


# --- test_memory_search_in_catalogue: P6: asserts tool names and closed-schema flags in the catalogue; the dispatch tests call the same tools
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
