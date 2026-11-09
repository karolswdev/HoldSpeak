# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_intel_honest_dispatch.py to restore.

# ruff: noqa


# --- TestIntelSchemaConstant: P1: asserts the keys and flags of a schema constant defined in the product, read back
class TestIntelSchemaConstant:
    """The ONE schema constant is well-formed and carries the named-owner shape."""

    def test_schema_has_required_top_level_keys(self) -> None:
        assert set(INTEL_SCHEMA) == {"topics", "action_items", "decisions", "summary"}

    def test_action_items_carry_named_owner_shape(self) -> None:
        item = INTEL_SCHEMA["action_items"][0]
        assert "task" in item
        assert "owner" in item
        assert "due" in item
        # The owner placeholder carries the named-owner shape (counsel M4).
        assert "name" in item["owner"].lower() or "person" in item["owner"].lower()

    def test_json_schema_matches_constant(self) -> None:
        props = INTEL_JSON_SCHEMA["properties"]
        assert set(props) == {"topics", "action_items", "decisions", "summary"}
        item_props = props["action_items"]["items"]["properties"]
        assert set(item_props) == {"task", "owner", "due"}
        # owner is string|null (the named-owner shape).
        assert item_props["owner"]["type"] == ["string", "null"]

    def test_response_format_is_well_formed(self) -> None:
        fmt = intel_response_format()
        assert fmt["type"] == "json_schema"
        assert fmt["json_schema"]["name"] == "meeting_intel"
        assert fmt["json_schema"]["strict"] is True
        assert fmt["json_schema"]["schema"] is INTEL_JSON_SCHEMA
