# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_mcp_surface.py to restore.

# ruff: noqa


# --- test_retired_destination_and_profile_resources_are_absent: P8: guards that names retired in Phase 133 stay absent
def test_retired_destination_and_profile_resources_are_absent() -> None:
    catalogue = mcp_resources.list_resources(OWNER)
    resources = {row["uri"] for row in catalogue["resources"]}
    templates = {row["uriTemplate"] for row in catalogue["resourceTemplates"]}
    assert resources.isdisjoint({
        "holdspeak://desk/inference-targets", "holdspeak://destinations",
        "holdspeak://model-profiles",
    })
    assert templates.isdisjoint({
        "holdspeak://destinations/{id}", "holdspeak://model-profiles/{id}",
    })
    for uri in ("holdspeak://destinations", "holdspeak://model-profiles"):
        with pytest.raises(mcp_resources.ResourceError, match="Unknown resource"):
            mcp_resources.read_resource(uri, OWNER)


# --- test_retired_underscore_name_absent_from_catalogue: P8: guards that names retired in Phase 133 stay absent
def test_retired_underscore_name_absent_from_catalogue() -> None:
    """The old underscore-named tool must not appear in the tool catalogue."""
    names = {tool["name"] for tool in mcp_tools.TOOLS}
    assert _RETIRED_UNDERSCORE_NAME not in names, (
        "retired underscore name still present in the TOOLS catalogue"
    )
    assert "pipeline.events" in names, (
        "pipeline.events missing from the TOOLS catalogue"
    )


# --- test_desk_crud_descriptions_carry_kind_boundary_sentence: P4: pins a sentence in five tool description strings
def test_desk_crud_descriptions_carry_kind_boundary_sentence() -> None:
    """All five desk.* CRUD tool descriptions contain the kind-boundary sentence."""
    tool_map = {tool["name"]: tool for tool in mcp_tools.TOOLS}
    for tool_name, expected_substring in _EXPECTED_SENTENCES.items():
        tool = tool_map.get(tool_name)
        assert tool is not None, f"{tool_name} missing from TOOLS catalogue"
        desc = tool["description"]
        assert expected_substring in desc, (
            f"{tool_name} description does not contain the expected kind-boundary sentence.\n"
            f"  Expected substring: {expected_substring!r}\n"
            f"  Actual description: {desc!r}"
        )
