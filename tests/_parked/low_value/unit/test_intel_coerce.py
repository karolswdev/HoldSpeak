# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_intel_coerce.py to restore.

# ruff: noqa


# --- TestCoerceStrListValidInput::test_single_element_list: P5: one more literal through the same coerce branch; test_mixed_types_coerced_and_filtered and the pass-through test cover it
# (was a method of class TestCoerceStrListValidInput)
def test_single_element_list(self):
    """Single element list works correctly."""
    value = ["only one"]
    result = _coerce_str_list(value)
    assert result == ["only one"]


# --- TestCoerceStrListValidInput::test_empty_list: P5: one more literal through the same coerce branch; test_mixed_types_coerced_and_filtered and the pass-through test cover it
# (was a method of class TestCoerceStrListValidInput)
def test_empty_list(self):
    """Empty list returns empty list."""
    result = _coerce_str_list([])
    assert result == []


# --- TestCoerceStrListValidInput::test_unicode_strings: P5: one more literal through the same coerce branch; test_mixed_types_coerced_and_filtered and the pass-through test cover it
# (was a method of class TestCoerceStrListValidInput)
def test_unicode_strings(self):
    """Unicode strings are handled."""
    value = ["\u65e5\u672c\u8a9e", "\u4e2d\u6587", "English"]
    result = _coerce_str_list(value)
    assert result == ["\u65e5\u672c\u8a9e", "\u4e2d\u6587", "English"]


# --- TestCoerceStrListFiltersNonStrings::test_converts_integers_to_strings: P5: one more literal through the same coerce branch; test_mixed_types_coerced_and_filtered and the pass-through test cover it
# (was a method of class TestCoerceStrListFiltersNonStrings)
def test_converts_integers_to_strings(self):
    """Integer values are converted to strings."""
    value = ["topic1", 42, "topic2"]
    result = _coerce_str_list(value)
    assert result == ["topic1", "42", "topic2"]


# --- TestCoerceStrListFiltersNonStrings::test_converts_floats_to_strings: P5: one more literal through the same coerce branch; test_mixed_types_coerced_and_filtered and the pass-through test cover it
# (was a method of class TestCoerceStrListFiltersNonStrings)
def test_converts_floats_to_strings(self):
    """Float values are converted to strings."""
    value = ["topic1", 3.14, "topic2"]
    result = _coerce_str_list(value)
    assert result == ["topic1", "3.14", "topic2"]


# --- TestCoerceStrListFiltersNonStrings::test_converts_booleans_to_strings: P5: one more literal through the same coerce branch; test_mixed_types_coerced_and_filtered and the pass-through test cover it
# (was a method of class TestCoerceStrListFiltersNonStrings)
def test_converts_booleans_to_strings(self):
    """Boolean values are converted to strings."""
    value = ["topic1", True, False, "topic2"]
    result = _coerce_str_list(value)
    assert result == ["topic1", "True", "False", "topic2"]


# --- TestCoerceStrListNonListInput::test_single_integer_returns_list_with_string: P5: one more literal through the same coerce branch; test_mixed_types_coerced_and_filtered and the pass-through test cover it
# (was a method of class TestCoerceStrListNonListInput)
def test_single_integer_returns_list_with_string(self):
    """Single integer becomes list with string representation."""
    result = _coerce_str_list(42)
    assert result == ["42"]


# --- TestCoerceStrListNonListInput::test_boolean_true_returns_list: P5: one more literal through the same coerce branch; test_mixed_types_coerced_and_filtered and the pass-through test cover it
# (was a method of class TestCoerceStrListNonListInput)
def test_boolean_true_returns_list(self):
    """Boolean True becomes list with 'True' string."""
    result = _coerce_str_list(True)
    assert result == ["True"]


# --- TestCoerceStrListNonListInput::test_boolean_false_returns_list: P5: one more literal through the same coerce branch; test_mixed_types_coerced_and_filtered and the pass-through test cover it
# (was a method of class TestCoerceStrListNonListInput)
def test_boolean_false_returns_list(self):
    """Boolean False becomes list with 'False' string."""
    result = _coerce_str_list(False)
    assert result == ["False"]


# --- TestCoerceStrListEdgeCases::test_list_with_all_none: P5: one more literal through the same coerce branch; test_mixed_types_coerced_and_filtered and the pass-through test cover it
# (was a method of class TestCoerceStrListEdgeCases)
def test_list_with_all_none(self):
    """List with all None values returns empty list."""
    value = [None, None, None]
    result = _coerce_str_list(value)
    assert result == []


# --- TestCoerceStrListEdgeCases::test_very_long_list: P5: one more literal through the same coerce branch; test_mixed_types_coerced_and_filtered and the pass-through test cover it
# (was a method of class TestCoerceStrListEdgeCases)
def test_very_long_list(self):
    """Very long list is handled."""
    value = [f"topic{i}" for i in range(1000)]
    result = _coerce_str_list(value)
    assert len(result) == 1000
    assert result[0] == "topic0"
    assert result[999] == "topic999"


# --- TestCoerceStrListEdgeCases::test_special_characters_preserved: P5: one more literal through the same coerce branch; test_mixed_types_coerced_and_filtered and the pass-through test cover it
# (was a method of class TestCoerceStrListEdgeCases)
def test_special_characters_preserved(self):
    """Special characters in strings are preserved."""
    value = ["topic with 'quotes'", 'topic with "double"', "topic & symbols!"]
    result = _coerce_str_list(value)
    assert result == ["topic with 'quotes'", 'topic with "double"', "topic & symbols!"]


# --- TestCoerceActionItemsMissingOptionalFields::test_missing_owner: P5: the owner twin, the task-only case or the realistic response already takes this branch
# (was a method of class TestCoerceActionItemsMissingOptionalFields)
def test_missing_owner(self):
    """Action item without owner has None owner."""
    value = [{"task": "Do this", "due": "Tomorrow"}]
    result = _coerce_action_items(value)
    assert len(result) == 1
    assert result[0].task == "Do this"
    assert result[0].owner is None
    assert result[0].due == "Tomorrow"


# --- TestCoerceActionItemsMissingOptionalFields::test_missing_due: P5: the owner twin, the task-only case or the realistic response already takes this branch
# (was a method of class TestCoerceActionItemsMissingOptionalFields)
def test_missing_due(self):
    """Action item without due has None due."""
    value = [{"task": "Do that", "owner": "Me"}]
    result = _coerce_action_items(value)
    assert len(result) == 1
    assert result[0].task == "Do that"
    assert result[0].owner == "Me"
    assert result[0].due is None


# --- TestCoerceActionItemsMissingOptionalFields::test_missing_both_optional: P5: the owner twin, the task-only case or the realistic response already takes this branch
# (was a method of class TestCoerceActionItemsMissingOptionalFields)
def test_missing_both_optional(self):
    """Action item with only task has None for optional fields."""
    value = [{"task": "Just the task"}]
    result = _coerce_action_items(value)
    assert len(result) == 1
    assert result[0].task == "Just the task"
    assert result[0].owner is None
    assert result[0].due is None


# --- TestCoerceActionItemsMissingOptionalFields::test_null_due_becomes_none: P5: the owner twin, the task-only case or the realistic response already takes this branch
# (was a method of class TestCoerceActionItemsMissingOptionalFields)
def test_null_due_becomes_none(self):
    """Due value of null becomes None."""
    value = [{"task": "Task", "owner": "Me", "due": None}]
    result = _coerce_action_items(value)
    assert result[0].due is None


# --- TestCoerceActionItemsMissingOptionalFields::test_empty_string_due_becomes_none: P5: the owner twin, the task-only case or the realistic response already takes this branch
# (was a method of class TestCoerceActionItemsMissingOptionalFields)
def test_empty_string_due_becomes_none(self):
    """Due value of empty string becomes None."""
    value = [{"task": "Task", "owner": "Me", "due": ""}]
    result = _coerce_action_items(value)
    assert result[0].due is None


# --- TestCoerceActionItemsMissingOptionalFields::test_string_null_due_becomes_none: P5: the owner twin, the task-only case or the realistic response already takes this branch
# (was a method of class TestCoerceActionItemsMissingOptionalFields)
def test_string_null_due_becomes_none(self):
    """Due value of 'null' string becomes None."""
    value = [{"task": "Task", "owner": "Me", "due": "null"}]
    result = _coerce_action_items(value)
    assert result[0].due is None


# --- TestCoerceActionItemsNonListInput::test_string_returns_empty_list: P5: the owner twin, the task-only case or the realistic response already takes this branch
# (was a method of class TestCoerceActionItemsNonListInput)
def test_string_returns_empty_list(self):
    """String input returns empty list."""
    result = _coerce_action_items("not a list")
    assert result == []


# --- TestCoerceActionItemsNonListInput::test_integer_returns_empty_list: P5: the owner twin, the task-only case or the realistic response already takes this branch
# (was a method of class TestCoerceActionItemsNonListInput)
def test_integer_returns_empty_list(self):
    """Integer input returns empty list."""
    result = _coerce_action_items(42)
    assert result == []


# --- TestCoerceActionItemsNonListInput::test_boolean_returns_empty_list: P5: the owner twin, the task-only case or the realistic response already takes this branch
# (was a method of class TestCoerceActionItemsNonListInput)
def test_boolean_returns_empty_list(self):
    """Boolean input returns empty list."""
    result = _coerce_action_items(True)
    assert result == []


# --- TestCoerceActionItemsTypeCoercion::test_owner_coerced_to_string: P5: the owner twin, the task-only case or the realistic response already takes this branch
# (was a method of class TestCoerceActionItemsTypeCoercion)
def test_owner_coerced_to_string(self):
    """Owner value is coerced to string."""
    value = [{"task": "Task", "owner": 42}]
    result = _coerce_action_items(value)
    assert result[0].owner == "42"


# --- TestCoerceActionItemsTypeCoercion::test_due_coerced_to_string: P5: the owner twin, the task-only case or the realistic response already takes this branch
# (was a method of class TestCoerceActionItemsTypeCoercion)
def test_due_coerced_to_string(self):
    """Due value is coerced to string."""
    value = [{"task": "Task", "due": 2024}]
    result = _coerce_action_items(value)
    assert result[0].due == "2024"


# --- TestCoerceActionItemsEdgeCases::test_empty_list_returns_empty_list: P5: the owner twin, the task-only case or the realistic response already takes this branch
# (was a method of class TestCoerceActionItemsEdgeCases)
def test_empty_list_returns_empty_list(self):
    """Empty list returns empty list."""
    result = _coerce_action_items([])
    assert result == []


# --- TestCoerceActionItemsEdgeCases::test_unicode_in_fields: P5: the owner twin, the task-only case or the realistic response already takes this branch
# (was a method of class TestCoerceActionItemsEdgeCases)
def test_unicode_in_fields(self):
    """Unicode characters in fields are handled."""
    value = [{"task": "\u30bf\u30b9\u30af", "owner": "\u7530\u4e2d", "due": "\u660e\u65e5"}]
    result = _coerce_action_items(value)
    assert result[0].task == "\u30bf\u30b9\u30af"
    assert result[0].owner == "\u7530\u4e2d"
    assert result[0].due == "\u660e\u65e5"


# --- TestCoerceActionItemsEdgeCases::test_very_long_task: P5: the owner twin, the task-only case or the realistic response already takes this branch
# (was a method of class TestCoerceActionItemsEdgeCases)
def test_very_long_task(self):
    """Very long task string is handled."""
    long_task = "A" * 10000
    value = [{"task": long_task}]
    result = _coerce_action_items(value)
    assert result[0].task == long_task


# --- TestCoerceActionItemsEdgeCases::test_many_action_items: P5: the owner twin, the task-only case or the realistic response already takes this branch
# (was a method of class TestCoerceActionItemsEdgeCases)
def test_many_action_items(self):
    """Many action items are handled."""
    value = [{"task": f"Task {i}", "owner": "Me"} for i in range(100)]
    result = _coerce_action_items(value)
    assert len(result) == 100
    assert result[0].task == "Task 0"
    assert result[99].task == "Task 99"
