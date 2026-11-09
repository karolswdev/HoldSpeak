# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_shelf_alignment.py to restore.

# ruff: noqa


# --- test_the_published_shelf_schema_names_the_three_states: P4: pins words in an MCP tool description
def test_the_published_shelf_schema_names_the_three_states(hub) -> None:
    _root, client = hub
    tools = client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).json()["result"]["tools"]
    shelf = next(t for t in tools if t["name"] == "monday_brief.shelf")
    state = shelf["inputSchema"]["properties"]["state"]
    for word in ("acknowledged", "deferred", "null"):
        assert word in state["description"]
    assert shelf["inputSchema"]["required"] == ["item_id", "state"]
