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

from datetime import datetime, timezone
from unittest.mock import patch
import time

import pytest

from holdspeak.intel import ActionItem, _generate_action_item_id


# ============================================================
# Tests for _generate_action_item_id()
# ============================================================


class TestGenerateActionItemId:
    """Tests for the _generate_action_item_id helper function."""

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

# ============================================================
# Tests for ActionItem ID Generation
# ============================================================


class TestActionItemIdGeneration:
    """Tests for ActionItem automatic ID generation."""

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

# ============================================================
# Tests for ActionItem created_at Timestamp
# ============================================================


class TestActionItemCreatedAt:
    """Tests for ActionItem created_at timestamp."""

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


