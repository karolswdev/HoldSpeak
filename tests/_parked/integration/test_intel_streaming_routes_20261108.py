"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/integration/test_intel_streaming.py``: TestActionItemPatchEndpoint. Not collected.
"""
from __future__ import annotations
"""Integration tests for intel streaming and action item API.

Tests for:
- Streaming intel analysis (_run_intel_analysis yields tokens then final result)
- WebSocket receives intel_token and intel_complete messages
- Streaming interruption handling
- PATCH /api/action-items/{id} endpoint
- WebSocket broadcasts action_item_updated
"""


from datetime import datetime
from typing import Iterator, Optional, Union
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

from holdspeak.intel import ActionItem, IntelResult, MeetingIntel
from holdspeak.meeting_session import (
    MeetingSession,
    MeetingState,
    IntelSnapshot,
)
from holdspeak.web_server import (
    WebRuntimeCallbacks,
    MeetingWebServer,
    WebSocketManager,
    BroadcastMessage,
)


# ============================================================
# Mock Fixtures
# ============================================================


@pytest.fixture
def mock_transcriber():
    """Mock transcriber for testing."""
    transcriber = MagicMock()
    transcriber.transcribe = MagicMock(return_value="Test transcript text")
    return transcriber


@pytest.fixture
def mock_intel_result():
    """Create a mock IntelResult."""
    return IntelResult(
        topics=["Project planning", "Budget review"],
        action_items=[
            ActionItem(task="Submit proposal", owner="Me", due="Friday"),
            ActionItem(task="Review budget", owner="Remote"),
        ],
        summary="Team discussed project timeline and budget.",
        raw_response='{"topics": [], "action_items": [], "summary": ""}',
    )


@pytest.fixture
def mock_streaming_intel(mock_intel_result):
    """Create a mock MeetingIntel that yields streaming tokens."""

    class MockStreamingIntel:
        def __init__(self):
            self.analyze_called = False
            self.transcript_received = None

        def analyze(
            self, transcript: str, *, stream: bool = False
        ) -> Union[IntelResult, Iterator[Union[str, IntelResult]]]:
            self.analyze_called = True
            self.transcript_received = transcript

            if not stream:
                return mock_intel_result

            # Return a generator for streaming
            return self._stream_response()

        def _stream_response(self) -> Iterator[Union[str, IntelResult]]:
            # Yield token chunks
            tokens = ['{"topics":', ' ["Project', ' planning"', "],", '"summary":', ' "Test"}']
            for token in tokens:
                yield token
            # Final result
            yield mock_intel_result

    return MockStreamingIntel()


@pytest.fixture
def mock_callbacks_with_action_items():
    """Create mock callbacks including action item updates."""
    action_items = [
        ActionItem(task="Task 1", owner="Me", id="item-001"),
        ActionItem(task="Task 2", owner="Remote", id="item-002"),
    ]
    intel = IntelSnapshot(
        timestamp=60.0,
        topics=["Topic A"],
        action_items=action_items,
        summary="Summary text",
    )
    state = {
        "id": "test-123",
        "started_at": "2024-01-15T10:30:00",
        "duration": 120,
        "intel": intel.to_dict(),
    }

    def update_action_item(item_id: str, status: str) -> Optional[dict]:
        for item in action_items:
            if item.id == item_id:
                if status == "done":
                    item.mark_done()
                elif status == "dismissed":
                    item.dismiss()
                elif status == "pending":
                    item.status = "pending"
                    item.completed_at = None
                return item.to_dict()
        return None

    def update_action_item_review(item_id: str, review_state: str) -> Optional[dict]:
        for item in action_items:
            if item.id == item_id:
                if review_state == "accepted":
                    item.accept()
                elif review_state == "pending":
                    item.review_state = "pending"
                    item.reviewed_at = None
                else:
                    return None
                return item.to_dict()
        return None

    def edit_action_item(item_id: str, task: str, owner: str | None, due: str | None) -> Optional[dict]:
        clean_task = str(task).strip()
        if not clean_task:
            return None
        for item in action_items:
            if item.id == item_id:
                item.task = clean_task
                item.owner = owner.strip() if isinstance(owner, str) and owner.strip() else None
                item.due = due.strip() if isinstance(due, str) and due.strip() else None
                item.accept()
                return item.to_dict()
        return None

    return {
        "on_bookmark": MagicMock(return_value={"timestamp": 10.5}),
        "on_stop": MagicMock(return_value={"status": "stopped"}),
        "get_state": MagicMock(return_value=state),
        "on_update_action_item": MagicMock(side_effect=update_action_item),
        "on_update_action_item_review": MagicMock(side_effect=update_action_item_review),
        "on_edit_action_item": MagicMock(side_effect=edit_action_item),
        "action_items": action_items,
    }


@pytest.fixture
def web_server_with_action_items(mock_callbacks_with_action_items):
    """Create MeetingWebServer with action item support."""
    server = MeetingWebServer(
                 WebRuntimeCallbacks(
                     on_bookmark=mock_callbacks_with_action_items["on_bookmark"],
                     on_stop=mock_callbacks_with_action_items["on_stop"],
                     get_state=mock_callbacks_with_action_items["get_state"],
                     on_update_action_item=mock_callbacks_with_action_items["on_update_action_item"],
                     on_update_action_item_review=mock_callbacks_with_action_items["on_update_action_item_review"],
                     on_edit_action_item=mock_callbacks_with_action_items["on_edit_action_item"],
                 ),
                 host="127.0.0.1",
             )
    return server


# ============================================================
# Tests for Streaming Intel Analysis
# ============================================================


# ============================================================
# Tests for Action Item API Endpoint
# ============================================================


@pytest.mark.integration
class TestActionItemPatchEndpoint:
    """Tests for PATCH /api/action-items/{id} endpoint."""

    def test_patch_action_item_done(self, test_client_with_action_items, mock_callbacks_with_action_items):
        """PATCH with status='done' should mark item as done."""
        response = test_client_with_action_items.patch(
            "/api/action-items/item-001",
            json={"status": "done"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action_item"]["status"] == "done"
        assert data["action_item"]["completed_at"] is not None

    def test_patch_action_item_pending(self, test_client_with_action_items, mock_callbacks_with_action_items):
        """PATCH with status='pending' should mark item as pending."""
        # First mark as done
        test_client_with_action_items.patch(
            "/api/action-items/item-001",
            json={"status": "done"},
        )

        # Then revert to pending
        response = test_client_with_action_items.patch(
            "/api/action-items/item-001",
            json={"status": "pending"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action_item"]["status"] == "pending"
        assert data["action_item"]["completed_at"] is None

    def test_patch_action_item_dismissed(self, test_client_with_action_items, mock_callbacks_with_action_items):
        """PATCH with status='dismissed' should dismiss item."""
        response = test_client_with_action_items.patch(
            "/api/action-items/item-002",
            json={"status": "dismissed"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action_item"]["status"] == "dismissed"
        assert data["action_item"]["completed_at"] is not None

    def test_patch_invalid_id_returns_404(self, test_client_with_action_items):
        """PATCH with invalid ID should return 404."""
        response = test_client_with_action_items.patch(
            "/api/action-items/nonexistent-id",
            json={"status": "done"},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()

    def test_patch_invalid_status_returns_400(self, test_client_with_action_items):
        """PATCH with invalid status should return 400."""
        response = test_client_with_action_items.patch(
            "/api/action-items/item-001",
            json={"status": "invalid_status"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "invalid status" in data["error"].lower()

    def test_patch_without_handler_returns_501(self):
        """PATCH without handler should return 501."""
        # Create server without action item handler
        server = MeetingWebServer(
                     WebRuntimeCallbacks(
                         on_bookmark=MagicMock(),
                         on_stop=MagicMock(),
                         get_state=MagicMock(return_value={}),
                         on_update_action_item=None,
                     )
                 )
        client = TestClient(server.app)

        response = client.patch(
            "/api/action-items/item-001",
            json={"status": "done"},
        )

        assert response.status_code == 501
        data = response.json()
        assert data["success"] is False

    def test_patch_callback_error_returns_500(self, mock_callbacks_with_action_items):
        """PATCH callback error should return 500."""
        mock_callbacks_with_action_items["on_update_action_item"].side_effect = Exception(
            "Database error"
        )

        server = MeetingWebServer(
                     WebRuntimeCallbacks(
                         on_bookmark=mock_callbacks_with_action_items["on_bookmark"],
                         on_stop=mock_callbacks_with_action_items["on_stop"],
                         get_state=mock_callbacks_with_action_items["get_state"],
                         on_update_action_item=mock_callbacks_with_action_items["on_update_action_item"],
                     )
                 )
        client = TestClient(server.app)

        response = client.patch(
            "/api/action-items/item-001",
            json={"status": "done"},
        )

        assert response.status_code == 500

    def test_patch_action_item_review_accepts(self, test_client_with_action_items):
        response = test_client_with_action_items.patch(
            "/api/action-items/item-001/review",
            json={"review_state": "accepted"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["action_item"]["review_state"] == "accepted"
        assert payload["action_item"]["reviewed_at"] is not None

    def test_patch_action_item_review_invalid_state_returns_400(self, test_client_with_action_items):
        response = test_client_with_action_items.patch(
            "/api/action-items/item-001/review",
            json={"review_state": "approved"},
        )
        assert response.status_code == 400

    def test_patch_action_item_edit_auto_accepts(self, test_client_with_action_items):
        response = test_client_with_action_items.patch(
            "/api/action-items/item-001/edit",
            json={"task": "Edited task", "owner": "", "due": "Friday"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["action_item"]["task"] == "Edited task"
        assert payload["action_item"]["owner"] is None
        assert payload["action_item"]["due"] == "Friday"
        assert payload["action_item"]["review_state"] == "accepted"

    def test_patch_action_item_edit_empty_task_returns_400(self, test_client_with_action_items):
        response = test_client_with_action_items.patch(
            "/api/action-items/item-001/edit",
            json={"task": "   "},
        )
        assert response.status_code == 400

    def test_patch_action_item_review_without_handler_returns_501(self):
        server = MeetingWebServer(
                     WebRuntimeCallbacks(
                         on_bookmark=MagicMock(),
                         on_stop=MagicMock(),
                         get_state=MagicMock(return_value={}),
                         on_update_action_item=MagicMock(return_value={}),
                         on_update_action_item_review=None,
                         on_edit_action_item=MagicMock(return_value={}),
                     )
                 )
        client = TestClient(server.app)
        response = client.patch(
            "/api/action-items/item-001/review",
            json={"review_state": "accepted"},
        )
        assert response.status_code == 501

    def test_patch_action_item_edit_without_handler_returns_501(self):
        server = MeetingWebServer(
                     WebRuntimeCallbacks(
                         on_bookmark=MagicMock(),
                         on_stop=MagicMock(),
                         get_state=MagicMock(return_value={}),
                         on_update_action_item=MagicMock(return_value={}),
                         on_update_action_item_review=MagicMock(return_value={}),
                         on_edit_action_item=None,
                     )
                 )
        client = TestClient(server.app)
        response = client.patch(
            "/api/action-items/item-001/edit",
            json={"task": "Edited task"},
        )
        assert response.status_code == 501


# ============================================================
# Tests for WebSocket Broadcasts
# ============================================================


# ============================================================
# Tests for MeetingSession Intel Integration
# ============================================================


# ============================================================
# Tests for Streaming Interruption
# ============================================================


# ============================================================
# Tests for Empty Transcript Handling
# ============================================================


# ============================================================
# Tests for Action Item ID Determinism
# ============================================================


# ============================================================
# Tests for IntelSnapshot with Action Items
# ============================================================


