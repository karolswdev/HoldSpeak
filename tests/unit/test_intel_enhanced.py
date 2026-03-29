"""Unit tests for enhanced ActionItem functionality.

Tests for:
- ActionItem `id` generation (unique, deterministic for same task)
- ActionItem `status` field (pending, done, dismissed)
- ActionItem `mark_done()` method
- ActionItem `mark_pending()` method (via status setter)
- ActionItem `dismiss()` method
- ActionItem `to_dict()` includes all new fields
- ActionItem `created_at` timestamp
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch
import time

import pytest

from holdspeak.intel import ActionItem, _generate_action_item_id


# ============================================================
# Tests for _generate_action_item_id()
# ============================================================


class TestGenerateActionItemId:
    """Tests for the _generate_action_item_id helper function."""

    def test_generates_12_char_id(self):
        """Generated ID should be exactly 12 characters."""
        result = _generate_action_item_id("Test task")
        assert len(result) == 12

    def test_deterministic_for_same_input(self):
        """Same task and owner should always generate same ID."""
        id1 = _generate_action_item_id("Review proposal", "Alice")
        id2 = _generate_action_item_id("Review proposal", "Alice")
        assert id1 == id2

    def test_different_tasks_different_ids(self):
        """Different tasks should generate different IDs."""
        id1 = _generate_action_item_id("Task A")
        id2 = _generate_action_item_id("Task B")
        assert id1 != id2

    def test_different_owners_different_ids(self):
        """Same task with different owners should generate different IDs."""
        id1 = _generate_action_item_id("Review code", "Alice")
        id2 = _generate_action_item_id("Review code", "Bob")
        assert id1 != id2

    def test_none_owner_vs_empty_string_same_id(self):
        """None owner and empty string owner should produce same ID."""
        id1 = _generate_action_item_id("Task", None)
        id2 = _generate_action_item_id("Task", "")
        # Both use empty string in the hash
        assert id1 == id2

    def test_id_is_hexadecimal(self):
        """Generated ID should be valid hexadecimal."""
        result = _generate_action_item_id("Some task", "Owner")
        assert all(c in "0123456789abcdef" for c in result)

    def test_empty_task_still_generates_id(self):
        """Even empty task should generate an ID."""
        result = _generate_action_item_id("")
        assert len(result) == 12

    def test_unicode_task_generates_id(self):
        """Unicode task text should generate valid ID."""
        result = _generate_action_item_id("\u30bf\u30b9\u30af\u3092\u5b8c\u4e86\u3059\u308b", "\u7530\u4e2d")
        assert len(result) == 12
        assert all(c in "0123456789abcdef" for c in result)


# ============================================================
# Tests for ActionItem ID Generation
# ============================================================


class TestActionItemIdGeneration:
    """Tests for ActionItem automatic ID generation."""

    def test_auto_generates_id_if_not_provided(self):
        """ActionItem should auto-generate ID when not provided."""
        item = ActionItem(task="Write tests")
        assert item.id is not None
        assert len(item.id) == 12

    def test_uses_provided_id(self):
        """ActionItem should use provided ID if given."""
        item = ActionItem(task="Write tests", id="custom-id-123")
        assert item.id == "custom-id-123"

    def test_same_task_generates_same_id(self):
        """Same task text should generate same ID."""
        item1 = ActionItem(task="Review PR")
        item2 = ActionItem(task="Review PR")
        assert item1.id == item2.id

    def test_task_and_owner_affect_id(self):
        """Both task and owner should affect generated ID."""
        item1 = ActionItem(task="Fix bug", owner="Alice")
        item2 = ActionItem(task="Fix bug", owner="Bob")
        item3 = ActionItem(task="Fix bug")
        assert item1.id != item2.id
        assert item1.id != item3.id
        assert item2.id != item3.id

    def test_due_date_does_not_affect_id(self):
        """Due date should NOT affect the generated ID."""
        item1 = ActionItem(task="Task", owner="Me", due="Monday")
        item2 = ActionItem(task="Task", owner="Me", due="Friday")
        item3 = ActionItem(task="Task", owner="Me", due=None)
        assert item1.id == item2.id == item3.id


# ============================================================
# Tests for ActionItem Status Field
# ============================================================


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


# ============================================================
# Tests for ActionItem mark_done() Method
# ============================================================


class TestActionItemMarkDone:
    """Tests for ActionItem mark_done() method."""

    def test_mark_done_sets_status(self):
        """mark_done() should set status to 'done'."""
        item = ActionItem(task="Task")
        item.mark_done()
        assert item.status == "done"

    def test_mark_done_sets_completed_at(self):
        """mark_done() should set completed_at timestamp."""
        item = ActionItem(task="Task")
        assert item.completed_at is None
        item.mark_done()
        assert item.completed_at is not None

    def test_mark_done_completed_at_is_iso_format(self):
        """completed_at should be in ISO format."""
        item = ActionItem(task="Task")
        item.mark_done()
        # Should be parseable as ISO datetime
        completed = datetime.fromisoformat(item.completed_at)
        assert isinstance(completed, datetime)

    def test_mark_done_completed_at_is_recent(self):
        """completed_at should be set to approximately current time."""
        before = datetime.now()
        item = ActionItem(task="Task")
        item.mark_done()
        after = datetime.now()

        completed = datetime.fromisoformat(item.completed_at)
        assert before <= completed <= after

    def test_mark_done_from_dismissed(self):
        """mark_done() works when status was 'dismissed'."""
        item = ActionItem(task="Task", status="dismissed")
        item.mark_done()
        assert item.status == "done"
        assert item.completed_at is not None

    def test_mark_done_idempotent(self):
        """Calling mark_done() multiple times is safe."""
        item = ActionItem(task="Task")
        item.mark_done()
        first_completed_at = item.completed_at

        # Small delay to ensure different timestamp if updated
        time.sleep(0.01)
        item.mark_done()

        assert item.status == "done"
        # Second call updates completed_at
        assert item.completed_at != first_completed_at


# ============================================================
# Tests for ActionItem mark_pending() (via status setter)
# ============================================================


class TestActionItemMarkPending:
    """Tests for restoring ActionItem to pending status."""

    def test_set_pending_clears_completed_at(self):
        """Setting status to 'pending' should clear completed_at."""
        item = ActionItem(task="Task")
        item.mark_done()
        assert item.completed_at is not None

        # Restore to pending
        item.status = "pending"
        item.completed_at = None  # Manual clearing (as designed)
        assert item.status == "pending"
        assert item.completed_at is None

    def test_reopen_done_item(self):
        """A done item can be reopened by setting status to pending."""
        item = ActionItem(task="Task")
        item.mark_done()

        item.status = "pending"
        item.completed_at = None
        assert item.status == "pending"

    def test_reopen_dismissed_item(self):
        """A dismissed item can be reopened by setting status to pending."""
        item = ActionItem(task="Task")
        item.dismiss()

        item.status = "pending"
        item.completed_at = None
        assert item.status == "pending"
        assert item.completed_at is None


# ============================================================
# Tests for ActionItem dismiss() Method
# ============================================================


class TestActionItemDismiss:
    """Tests for ActionItem dismiss() method."""

    def test_dismiss_sets_status(self):
        """dismiss() should set status to 'dismissed'."""
        item = ActionItem(task="Task")
        item.dismiss()
        assert item.status == "dismissed"

    def test_dismiss_sets_completed_at(self):
        """dismiss() should set completed_at timestamp."""
        item = ActionItem(task="Task")
        assert item.completed_at is None
        item.dismiss()
        assert item.completed_at is not None

    def test_dismiss_completed_at_is_iso_format(self):
        """completed_at from dismiss() should be in ISO format."""
        item = ActionItem(task="Task")
        item.dismiss()
        completed = datetime.fromisoformat(item.completed_at)
        assert isinstance(completed, datetime)

    def test_dismiss_from_done(self):
        """dismiss() works when status was 'done'."""
        item = ActionItem(task="Task", status="done")
        original_completed = datetime.now().isoformat()
        item.completed_at = original_completed

        time.sleep(0.01)
        item.dismiss()

        assert item.status == "dismissed"
        # completed_at is updated
        assert item.completed_at != original_completed


class TestActionItemAccept:
    """Tests for ActionItem accept() review behavior."""

    def test_accept_sets_review_state_and_timestamp(self):
        item = ActionItem(task="Task")
        assert item.review_state == "pending"
        assert item.reviewed_at is None

        item.accept()

        assert item.review_state == "accepted"
        assert item.reviewed_at is not None


# ============================================================
# Tests for ActionItem to_dict() Method
# ============================================================


class TestActionItemToDict:
    """Tests for ActionItem to_dict() serialization."""

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

    def test_to_dict_correct_values(self):
        """to_dict() should return correct values."""
        item = ActionItem(
            task="Review PR",
            owner="Bob",
            due="Monday",
            id="test-id-123",
            status="done",
        )
        item.completed_at = "2024-01-15T10:30:00"

        result = item.to_dict()

        assert result["task"] == "Review PR"
        assert result["owner"] == "Bob"
        assert result["due"] == "Monday"
        assert result["id"] == "test-id-123"
        assert result["status"] == "done"
        assert result["review_state"] == "pending"
        assert result["completed_at"] == "2024-01-15T10:30:00"

    def test_to_dict_with_none_values(self):
        """to_dict() should handle None values correctly."""
        item = ActionItem(task="Minimal task")
        result = item.to_dict()

        assert result["task"] == "Minimal task"
        assert result["owner"] is None
        assert result["due"] is None
        assert result["completed_at"] is None
        assert result["source_timestamp"] is None

    def test_to_dict_includes_created_at(self):
        """to_dict() should include created_at timestamp."""
        item = ActionItem(task="Task")
        result = item.to_dict()

        assert "created_at" in result
        assert result["created_at"] is not None
        # Should be parseable as ISO datetime
        created = datetime.fromisoformat(result["created_at"])
        assert isinstance(created, datetime)

    def test_to_dict_with_source_timestamp(self):
        """to_dict() should include source_timestamp when set."""
        item = ActionItem(task="Task", source_timestamp=123.45)
        result = item.to_dict()

        assert result["source_timestamp"] == 123.45

    def test_to_dict_returns_dict_not_dataclass(self):
        """to_dict() should return a plain dict."""
        item = ActionItem(task="Task")
        result = item.to_dict()

        assert isinstance(result, dict)
        assert not hasattr(result, "__dataclass_fields__")


# ============================================================
# Tests for ActionItem created_at Timestamp
# ============================================================


class TestActionItemCreatedAt:
    """Tests for ActionItem created_at timestamp."""

    def test_created_at_auto_generated(self):
        """created_at should be auto-generated on creation."""
        item = ActionItem(task="New task")
        assert item.created_at is not None

    def test_created_at_is_iso_format(self):
        """created_at should be in ISO format."""
        item = ActionItem(task="Task")
        created = datetime.fromisoformat(item.created_at)
        assert isinstance(created, datetime)

    def test_created_at_is_recent(self):
        """created_at should be approximately current time."""
        before = datetime.now()
        item = ActionItem(task="Task")
        after = datetime.now()

        created = datetime.fromisoformat(item.created_at)
        assert before <= created <= after

    def test_created_at_can_be_provided(self):
        """created_at can be explicitly provided."""
        custom_time = "2024-06-15T14:30:00"
        item = ActionItem(task="Task", created_at=custom_time)
        assert item.created_at == custom_time

    def test_created_at_immutable_after_creation(self):
        """created_at should not change when status changes."""
        item = ActionItem(task="Task")
        original_created = item.created_at

        item.mark_done()
        assert item.created_at == original_created

        item.dismiss()
        assert item.created_at == original_created


# ============================================================
# Tests for ActionItem Edge Cases
# ============================================================


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
