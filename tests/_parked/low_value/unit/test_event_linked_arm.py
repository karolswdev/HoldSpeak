# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_event_linked_arm.py to restore.

# ruff: noqa


# --- TestEventLinkedMCP::test_calendar_event_id_in_tool_schema: P6: a key is in a tool schema; the MCP arm test calls the tool with it
# (was a method of class TestEventLinkedMCP)
def test_calendar_event_id_in_tool_schema(self, db: Database, monkeypatch: Any) -> None:
    """The MCP tool schema includes calendar_event_id."""
    from holdspeak.mcp.server import handle_message
    _setup_mcp(db, monkeypatch)

    response = handle_message({
        "jsonrpc": "2.0", "id": 1, "method": "tools/list",
    })
    tools = response["result"]["tools"]
    create_tool = next(t for t in tools if t["name"] == "scheduled_recording.create")
    assert "calendar_event_id" in create_tool["inputSchema"]["properties"]
