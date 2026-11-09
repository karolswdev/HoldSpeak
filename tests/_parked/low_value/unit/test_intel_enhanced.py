# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_intel_enhanced.py to restore.

# ruff: noqa


# --- TestActionItemStatus: P1/P3: sets a dataclass field (status, task text, unicode, long text) and reads the same literal back
class TestActionItemStatus:
    """Tests for ActionItem status field."""

    def test_default_status_is_pending(self):
        """Default status should be 'pending'."""
        item = ActionItem(task="New task")
        assert item.status == "pending"

    def test_can_initialize_with_status(self):
        """ActionItem can be initialized with a specific status."""
        item = ActionItem(task="Completed task", status="done")
        assert item.status == "done"

    def test_status_can_be_set_directly(self):
        """Status can be modified directly."""
        item = ActionItem(task="Task")
        item.status = "done"
        assert item.status == "done"
        item.status = "dismissed"
        assert item.status == "dismissed"
        item.status = "pending"
        assert item.status == "pending"


# --- TestActionItemEdgeCases: P1/P3: sets a dataclass field (status, task text, unicode, long text) and reads the same literal back
class TestActionItemEdgeCases:
    """Edge cases and boundary conditions for ActionItem."""

    def test_empty_task_string(self):
        """ActionItem can have empty task (though typically filtered)."""
        item = ActionItem(task="")
        assert item.task == ""
        assert len(item.id) == 12

    def test_very_long_task(self):
        """ActionItem handles very long task text."""
        long_task = "A" * 10000
        item = ActionItem(task=long_task)
        assert item.task == long_task
        assert len(item.id) == 12

    def test_unicode_task(self):
        """ActionItem handles Unicode task text."""
        item = ActionItem(task="\u30ec\u30d3\u30e5\u30fc\u3092\u5b8c\u4e86\u3059\u308b", owner="\u7530\u4e2d\u592a\u90ce")
        assert item.task == "\u30ec\u30d3\u30e5\u30fc\u3092\u5b8c\u4e86\u3059\u308b"
        assert item.owner == "\u7530\u4e2d\u592a\u90ce"
        assert len(item.id) == 12

    def test_special_characters_in_task(self):
        """ActionItem handles special characters in task."""
        item = ActionItem(task='Review "the proposal" & submit <ASAP>')
        assert 'Review "the proposal"' in item.task

    def test_multiple_status_transitions(self):
        """ActionItem can transition through multiple statuses."""
        item = ActionItem(task="Task")
        assert item.status == "pending"
        assert item.completed_at is None

        item.mark_done()
        assert item.status == "done"
        assert item.completed_at is not None

        item.status = "pending"
        item.completed_at = None
        assert item.status == "pending"
        assert item.completed_at is None

        item.dismiss()
        assert item.status == "dismissed"
        assert item.completed_at is not None

    def test_whitespace_in_task_preserved(self):
        """Whitespace in task is preserved (stripping happens at coercion)."""
        item = ActionItem(task="  Task with spaces  ")
        assert item.task == "  Task with spaces  "

    def test_equality_by_id(self):
        """Two ActionItems with same task/owner should have same ID."""
        item1 = ActionItem(task="Same task", owner="Same owner")
        item2 = ActionItem(task="Same task", owner="Same owner")

        assert item1.id == item2.id
        # But they are different objects
        assert item1 is not item2

    def test_all_fields_together(self):
        """Test ActionItem with all fields populated."""
        item = ActionItem(
            task="Complete the report",
            owner="Alice",
            due="Next Monday",
            id="custom-id",
            status="done",
            source_timestamp=45.67,
            created_at="2024-01-10T09:00:00",
            completed_at="2024-01-12T17:30:00",
        )

        assert item.task == "Complete the report"
        assert item.owner == "Alice"
        assert item.due == "Next Monday"
        assert item.id == "custom-id"
        assert item.status == "done"
        assert item.source_timestamp == 45.67
        assert item.created_at == "2024-01-10T09:00:00"
        assert item.completed_at == "2024-01-12T17:30:00"

        result = item.to_dict()
        assert result["task"] == "Complete the report"
        assert result["owner"] == "Alice"
        assert result["due"] == "Next Monday"
        assert result["id"] == "custom-id"
        assert result["status"] == "done"
        assert result["source_timestamp"] == 45.67
        assert result["created_at"] == "2024-01-10T09:00:00"
        assert result["completed_at"] == "2024-01-12T17:30:00"


# --- TestGenerateActionItemId::test_generates_12_char_id: P6: asserts a key is present, an id is 12 hex chars or a timestamp parses, not a value the face shows
# (was a method of class TestGenerateActionItemId)
def test_generates_12_char_id(self):
    """Generated ID should be exactly 12 characters."""
    result = _generate_action_item_id("Test task")
    assert len(result) == 12


# --- TestGenerateActionItemId::test_id_is_hexadecimal: P6: asserts a key is present, an id is 12 hex chars or a timestamp parses, not a value the face shows
# (was a method of class TestGenerateActionItemId)
def test_id_is_hexadecimal(self):
    """Generated ID should be valid hexadecimal."""
    result = _generate_action_item_id("Some task", "Owner")
    assert all(c in "0123456789abcdef" for c in result)


# --- TestGenerateActionItemId::test_empty_task_still_generates_id: P6: asserts a key is present, an id is 12 hex chars or a timestamp parses, not a value the face shows
# (was a method of class TestGenerateActionItemId)
def test_empty_task_still_generates_id(self):
    """Even empty task should generate an ID."""
    result = _generate_action_item_id("")
    assert len(result) == 12


# --- TestGenerateActionItemId::test_unicode_task_generates_id: P6: asserts a key is present, an id is 12 hex chars or a timestamp parses, not a value the face shows
# (was a method of class TestGenerateActionItemId)
def test_unicode_task_generates_id(self):
    """Unicode task text should generate valid ID."""
    result = _generate_action_item_id("\u30bf\u30b9\u30af\u3092\u5b8c\u4e86\u3059\u308b", "\u7530\u4e2d")
    assert len(result) == 12
    assert all(c in "0123456789abcdef" for c in result)


# --- TestActionItemIdGeneration::test_auto_generates_id_if_not_provided: P6: asserts a key is present, an id is 12 hex chars or a timestamp parses, not a value the face shows
# (was a method of class TestActionItemIdGeneration)
def test_auto_generates_id_if_not_provided(self):
    """ActionItem should auto-generate ID when not provided."""
    item = ActionItem(task="Write tests")
    assert item.id is not None
    assert len(item.id) == 12


# --- TestActionItemMarkDone::test_mark_done_completed_at_is_iso_format: P6: asserts a key is present, an id is 12 hex chars or a timestamp parses, not a value the face shows
# (was a method of class TestActionItemMarkDone)
def test_mark_done_completed_at_is_iso_format(self):
    """completed_at should be in ISO format."""
    item = ActionItem(task="Task")
    item.mark_done()
    # Should be parseable as ISO datetime
    completed = datetime.fromisoformat(item.completed_at)
    assert isinstance(completed, datetime)


# --- TestActionItemMarkDone::test_mark_done_completed_at_is_recent: P6: asserts a key is present, an id is 12 hex chars or a timestamp parses, not a value the face shows
# (was a method of class TestActionItemMarkDone)
def test_mark_done_completed_at_is_recent(self):
    """completed_at should be set to approximately current time."""
    before = datetime.now(timezone.utc)
    item = ActionItem(task="Task")
    item.mark_done()
    after = datetime.now(timezone.utc)

    completed = datetime.fromisoformat(item.completed_at)
    assert before <= completed <= after


# --- TestActionItemDismiss::test_dismiss_completed_at_is_iso_format: P6: asserts a key is present, an id is 12 hex chars or a timestamp parses, not a value the face shows
# (was a method of class TestActionItemDismiss)
def test_dismiss_completed_at_is_iso_format(self):
    """completed_at from dismiss() should be in ISO format."""
    item = ActionItem(task="Task")
    item.dismiss()
    completed = datetime.fromisoformat(item.completed_at)
    assert isinstance(completed, datetime)


# --- TestActionItemToDict::test_to_dict_includes_all_fields: P6: asserts a key is present, an id is 12 hex chars or a timestamp parses, not a value the face shows
# (was a method of class TestActionItemToDict)
def test_to_dict_includes_all_fields(self):
    """to_dict() should include all ActionItem fields."""
    item = ActionItem(
        task="Write documentation",
        owner="Alice",
        due="Friday",
    )
    result = item.to_dict()

    assert "task" in result
    assert "owner" in result
    assert "due" in result
    assert "id" in result
    assert "status" in result
    assert "review_state" in result
    assert "reviewed_at" in result
    assert "source_timestamp" in result
    assert "created_at" in result
    assert "completed_at" in result


# --- TestActionItemToDict::test_to_dict_includes_created_at: P6: asserts a key is present, an id is 12 hex chars or a timestamp parses, not a value the face shows
# (was a method of class TestActionItemToDict)
def test_to_dict_includes_created_at(self):
    """to_dict() should include created_at timestamp."""
    item = ActionItem(task="Task")
    result = item.to_dict()

    assert "created_at" in result
    assert result["created_at"] is not None
    # Should be parseable as ISO datetime
    created = datetime.fromisoformat(result["created_at"])
    assert isinstance(created, datetime)


# --- TestActionItemCreatedAt::test_created_at_auto_generated: P6: asserts a key is present, an id is 12 hex chars or a timestamp parses, not a value the face shows
# (was a method of class TestActionItemCreatedAt)
def test_created_at_auto_generated(self):
    """created_at should be auto-generated on creation."""
    item = ActionItem(task="New task")
    assert item.created_at is not None


# --- TestActionItemCreatedAt::test_created_at_is_iso_format: P6: asserts a key is present, an id is 12 hex chars or a timestamp parses, not a value the face shows
# (was a method of class TestActionItemCreatedAt)
def test_created_at_is_iso_format(self):
    """created_at should be in ISO format."""
    item = ActionItem(task="Task")
    created = datetime.fromisoformat(item.created_at)
    assert isinstance(created, datetime)


# --- TestActionItemCreatedAt::test_created_at_is_recent: P6: asserts a key is present, an id is 12 hex chars or a timestamp parses, not a value the face shows
# (was a method of class TestActionItemCreatedAt)
def test_created_at_is_recent(self):
    """created_at should be approximately current time."""
    before = datetime.now(timezone.utc)
    item = ActionItem(task="Task")
    after = datetime.now(timezone.utc)

    created = datetime.fromisoformat(item.created_at)
    assert before <= created <= after


# --- TestActionItemIdGeneration::test_uses_provided_id: P1/P3/P5: passes a literal to the dataclass and reads it back, or repeats the deterministic-id test
# (was a method of class TestActionItemIdGeneration)
def test_uses_provided_id(self):
    """ActionItem should use provided ID if given."""
    item = ActionItem(task="Write tests", id="custom-id-123")
    assert item.id == "custom-id-123"


# --- TestActionItemIdGeneration::test_same_task_generates_same_id: P1/P3/P5: passes a literal to the dataclass and reads it back, or repeats the deterministic-id test
# (was a method of class TestActionItemIdGeneration)
def test_same_task_generates_same_id(self):
    """Same task text should generate same ID."""
    item1 = ActionItem(task="Review PR")
    item2 = ActionItem(task="Review PR")
    assert item1.id == item2.id


# --- TestActionItemToDict::test_to_dict_with_none_values: P1/P3/P5: passes a literal to the dataclass and reads it back, or repeats the deterministic-id test
# (was a method of class TestActionItemToDict)
def test_to_dict_with_none_values(self):
    """to_dict() should handle None values correctly."""
    item = ActionItem(task="Minimal task")
    result = item.to_dict()

    assert result["task"] == "Minimal task"
    assert result["owner"] is None
    assert result["due"] is None
    assert result["completed_at"] is None
    assert result["source_timestamp"] is None


# --- TestActionItemToDict::test_to_dict_with_source_timestamp: P1/P3/P5: passes a literal to the dataclass and reads it back, or repeats the deterministic-id test
# (was a method of class TestActionItemToDict)
def test_to_dict_with_source_timestamp(self):
    """to_dict() should include source_timestamp when set."""
    item = ActionItem(task="Task", source_timestamp=123.45)
    result = item.to_dict()

    assert result["source_timestamp"] == 123.45


# --- TestActionItemToDict::test_to_dict_returns_dict_not_dataclass: P1/P3/P5: passes a literal to the dataclass and reads it back, or repeats the deterministic-id test
# (was a method of class TestActionItemToDict)
def test_to_dict_returns_dict_not_dataclass(self):
    """to_dict() should return a plain dict."""
    item = ActionItem(task="Task")
    result = item.to_dict()

    assert isinstance(result, dict)
    assert not hasattr(result, "__dataclass_fields__")


# --- TestActionItemCreatedAt::test_created_at_can_be_provided: P1/P3/P5: passes a literal to the dataclass and reads it back, or repeats the deterministic-id test
# (was a method of class TestActionItemCreatedAt)
def test_created_at_can_be_provided(self):
    """created_at can be explicitly provided."""
    custom_time = "2024-06-15T14:30:00"
    item = ActionItem(task="Task", created_at=custom_time)
    assert item.created_at == custom_time
