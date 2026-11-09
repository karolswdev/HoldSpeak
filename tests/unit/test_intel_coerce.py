"""Unit tests for intel coercion functions.

Tests for:
- _coerce_str_list(): Converts various inputs to list[str]
- _coerce_action_items(): Converts various inputs to list[ActionItem]
"""

from __future__ import annotations

import pytest

from holdspeak.intel import _coerce_str_list, _coerce_action_items, ActionItem


# ============================================================
# Tests for _coerce_str_list()
# ============================================================


class TestCoerceStrListValidInput:
    """Tests for valid string list inputs."""

    def test_valid_string_list_passes_through(self):
        """Valid list of strings passes through unchanged."""
        value = ["topic1", "topic2", "topic3"]
        result = _coerce_str_list(value)
        assert result == ["topic1", "topic2", "topic3"]

    def test_list_with_whitespace_strings(self):
        """Strings are stripped of whitespace."""
        value = ["  topic1  ", "\ttopic2\n", "  topic3"]
        result = _coerce_str_list(value)
        assert result == ["topic1", "topic2", "topic3"]

class TestCoerceStrListFiltersNonStrings:
    """Tests for filtering non-string items."""

    def test_filters_none_values(self):
        """None values are filtered out."""
        value = ["topic1", None, "topic2", None]
        result = _coerce_str_list(value)
        assert result == ["topic1", "topic2"]

    def test_filters_empty_strings(self):
        """Empty strings after stripping are filtered out."""
        value = ["topic1", "", "  ", "\t", "topic2"]
        result = _coerce_str_list(value)
        assert result == ["topic1", "topic2"]

    def test_mixed_types_coerced_and_filtered(self):
        """Mixed types are coerced to strings and empty values filtered."""
        value = ["valid", None, 123, "", "  ", True, "also valid"]
        result = _coerce_str_list(value)
        assert result == ["valid", "123", "True", "also valid"]


class TestCoerceStrListNonListInput:
    """Tests for non-list input handling."""

    def test_none_returns_empty_list(self):
        """None input returns empty list."""
        result = _coerce_str_list(None)
        assert result == []

    def test_single_string_returns_list_with_one_element(self):
        """Single string becomes list with one element."""
        result = _coerce_str_list("single topic")
        assert result == ["single topic"]

    def test_empty_string_returns_empty_list(self):
        """Empty string returns empty list."""
        result = _coerce_str_list("")
        assert result == []

    def test_whitespace_string_returns_empty_list(self):
        """Whitespace-only string returns empty list."""
        result = _coerce_str_list("   ")
        assert result == []

    def test_dict_converted_to_string(self):
        """Dictionary is converted to string representation."""
        result = _coerce_str_list({"key": "value"})
        # Dictionary converts to string like "{'key': 'value'}"
        assert len(result) == 1
        assert "key" in result[0]

class TestCoerceStrListEdgeCases:
    """Edge cases for _coerce_str_list."""

    def test_nested_list_converted_to_strings(self):
        """Nested lists are converted to string representations."""
        value = ["topic1", ["nested", "list"], "topic2"]
        result = _coerce_str_list(value)
        assert len(result) == 3
        assert result[0] == "topic1"
        assert "[" in result[1]  # String representation of list
        assert result[2] == "topic2"

# ============================================================
# Tests for _coerce_action_items()
# ============================================================


class TestCoerceActionItemsValid:
    """Tests for valid action items."""

    def test_valid_action_item_with_all_fields(self):
        """Valid action item with all fields is converted."""
        value = [{"task": "Do something", "owner": "Me", "due": "Friday"}]
        result = _coerce_action_items(value)
        assert len(result) == 1
        assert isinstance(result[0], ActionItem)
        assert result[0].task == "Do something"
        assert result[0].owner == "Me"
        assert result[0].due == "Friday"

    def test_multiple_valid_action_items(self):
        """Multiple valid action items are converted."""
        value = [
            {"task": "Task 1", "owner": "Alice", "due": "Monday"},
            {"task": "Task 2", "owner": "Bob", "due": "Tuesday"},
            {"task": "Task 3", "owner": "Charlie", "due": "Wednesday"},
        ]
        result = _coerce_action_items(value)
        assert len(result) == 3
        assert result[0].task == "Task 1"
        assert result[1].task == "Task 2"
        assert result[2].task == "Task 3"

    def test_action_item_with_task_only(self):
        """Action item with only task field is valid."""
        value = [{"task": "Minimal task"}]
        result = _coerce_action_items(value)
        assert len(result) == 1
        assert result[0].task == "Minimal task"
        assert result[0].owner is None
        assert result[0].due is None


class TestCoerceActionItemsMissingOptionalFields:
    """Tests for handling missing optional fields."""

    def test_null_owner_becomes_none(self):
        """Owner value of null becomes None."""
        value = [{"task": "Task", "owner": None, "due": "Friday"}]
        result = _coerce_action_items(value)
        assert result[0].owner is None

    def test_empty_string_owner_becomes_none(self):
        """Owner value of empty string becomes None."""
        value = [{"task": "Task", "owner": "", "due": "Friday"}]
        result = _coerce_action_items(value)
        assert result[0].owner is None

    def test_string_null_owner_becomes_none(self):
        """Owner value of 'null' string becomes None."""
        value = [{"task": "Task", "owner": "null", "due": "Friday"}]
        result = _coerce_action_items(value)
        assert result[0].owner is None

class TestCoerceActionItemsFiltersInvalid:
    """Tests for filtering invalid action items."""

    def test_filters_item_missing_task(self):
        """Action item without task is filtered out."""
        value = [{"owner": "Me", "due": "Friday"}]
        result = _coerce_action_items(value)
        assert result == []

    def test_filters_item_with_empty_task(self):
        """Action item with empty task string is filtered out."""
        value = [{"task": "", "owner": "Me"}]
        result = _coerce_action_items(value)
        assert result == []

    def test_filters_item_with_whitespace_task(self):
        """Action item with whitespace-only task is filtered out."""
        value = [{"task": "   ", "owner": "Me"}]
        result = _coerce_action_items(value)
        assert result == []

    def test_filters_none_items(self):
        """None items in list are filtered out."""
        value = [{"task": "Valid"}, None, {"task": "Also valid"}]
        result = _coerce_action_items(value)
        assert len(result) == 2
        assert result[0].task == "Valid"
        assert result[1].task == "Also valid"

    def test_filters_non_dict_items(self):
        """Non-dict items are filtered out."""
        value = [{"task": "Valid"}, "not a dict", 42, {"task": "Also valid"}]
        result = _coerce_action_items(value)
        assert len(result) == 2
        assert result[0].task == "Valid"
        assert result[1].task == "Also valid"

    def test_filters_string_items(self):
        """String items in list are filtered out."""
        value = ["task string", {"task": "Valid dict"}]
        result = _coerce_action_items(value)
        assert len(result) == 1
        assert result[0].task == "Valid dict"

    def test_mixed_valid_and_invalid(self):
        """Mix of valid and invalid items filters correctly."""
        value = [
            {"task": "Valid 1", "owner": "Me"},
            {"owner": "No task"},  # invalid - no task
            {"task": "", "owner": "Empty task"},  # invalid - empty task
            None,  # invalid - None
            {"task": "Valid 2", "due": "Tomorrow"},
            "string item",  # invalid - not dict
            {"task": "Valid 3"},
        ]
        result = _coerce_action_items(value)
        assert len(result) == 3
        assert result[0].task == "Valid 1"
        assert result[1].task == "Valid 2"
        assert result[2].task == "Valid 3"


class TestCoerceActionItemsNonListInput:
    """Tests for non-list input handling."""

    def test_none_returns_empty_list(self):
        """None input returns empty list."""
        result = _coerce_action_items(None)
        assert result == []

    def test_single_dict_returns_empty_list(self):
        """Single dict (not in list) returns empty list."""
        result = _coerce_action_items({"task": "Single task"})
        assert result == []

class TestCoerceActionItemsTypeCoercion:
    """Tests for type coercion of field values."""

    def test_task_coerced_to_string(self):
        """Task value is coerced to string."""
        value = [{"task": 123, "owner": "Me"}]
        result = _coerce_action_items(value)
        assert len(result) == 1
        assert result[0].task == "123"

    def test_whitespace_in_values_stripped(self):
        """Whitespace in values is stripped."""
        value = [{"task": "  Task  ", "owner": "  Me  ", "due": "  Friday  "}]
        result = _coerce_action_items(value)
        assert result[0].task == "Task"
        assert result[0].owner == "Me"
        assert result[0].due == "Friday"


class TestCoerceActionItemsEdgeCases:
    """Edge cases for _coerce_action_items."""

    def test_extra_fields_ignored(self):
        """Extra fields in action items are ignored."""
        value = [{"task": "Task", "owner": "Me", "due": "Friday", "priority": "high", "notes": "extra"}]
        result = _coerce_action_items(value)
        assert len(result) == 1
        assert result[0].task == "Task"
        assert result[0].owner == "Me"
        assert result[0].due == "Friday"
        # Verify no extra attributes
        assert not hasattr(result[0], "priority")

    def test_realistic_llm_response(self):
        """Realistic LLM response structure is handled."""
        value = [
            {"task": "Submit budget proposal", "owner": "Me", "due": "End of week"},
            {"task": "Schedule onboarding sessions", "owner": "Remote", "due": None},
            {"task": "Review competitor analysis", "owner": None, "due": "Next Monday"},
            {"task": "Follow up on marketing campaign", "owner": "null", "due": ""},
        ]
        result = _coerce_action_items(value)
        assert len(result) == 4
        assert result[0].owner == "Me"
        assert result[0].due == "End of week"
        assert result[1].owner == "Remote"
        assert result[1].due is None
        assert result[2].owner is None
        assert result[2].due == "Next Monday"
        assert result[3].owner is None  # "null" string -> None
        assert result[3].due is None  # "" -> None
