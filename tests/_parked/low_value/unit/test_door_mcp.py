# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_door_mcp.py to restore.

# ruff: noqa


# --- test_door_get_is_discoverable_with_a_closed_versioned_schema: P6: pins the exact JSON schema dict of two tools; the dispatch test below proves the tool works
def test_door_get_is_discoverable_with_a_closed_versioned_schema() -> None:
    response = server.handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert response is not None
    door_tools = [
        tool for tool in response["result"]["tools"] if tool["name"].startswith("door.")
    ]

    assert [tool["name"] for tool in door_tools] == ["door.get", "door.add_item"]
    assert door_tools[0]["inputSchema"] == {
        "$id": "holdspeak://mcp/door.get@1",
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }
    assert door_tools[1]["inputSchema"]["$id"] == "holdspeak://mcp/door.add_item@1"
    assert door_tools[1]["inputSchema"]["required"] == ["task"]
    assert door_tools[1]["inputSchema"]["additionalProperties"] is False
    resources = server.handle_message({"jsonrpc": "2.0", "id": 2, "method": "resources/list"})
    assert resources is not None
    assert all(
        "door" not in (resource.get("uri") or resource.get("uriTemplate") or "")
        for resource in [
            *resources["result"].get("resources", []),
            *resources["result"].get("resourceTemplates", []),
        ]
    )
    assert _call("door.get", {"unrecognized": True})[0] is True
