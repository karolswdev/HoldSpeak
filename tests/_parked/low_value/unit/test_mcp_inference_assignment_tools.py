# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_mcp_inference_assignment_tools.py to restore.

# ruff: noqa


# --- test_assignment_mcp_catalogue_is_closed_to_versioned_recursive_dtos: P6: asserts schema $id strings and additionalProperties flags of the catalogue
def test_assignment_mcp_catalogue_is_closed_to_versioned_recursive_dtos() -> None:
    tools = {tool["name"]: tool["inputSchema"] for tool in inference_assignments.TOOLS}
    assert set(tools) == _EXPECTED
    for name, schema in tools.items():
        assert schema["$id"] == f"holdspeak://mcp/{name}@1"
        assert schema["additionalProperties"] is False
    scope = tools["inference_assignment.set"]["properties"]["scope"]
    assert all(variant["additionalProperties"] is False for variant in scope["oneOf"])
    entry = tools["inference_assignment.set"]["properties"]["entries"]["items"]
    assert entry["additionalProperties"] is False
