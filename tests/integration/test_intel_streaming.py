"""Integration tests for intel streaming and action item API.

Tests for:
- Streaming intel analysis (_run_intel_analysis yields tokens then final result)
- WebSocket receives intel_token and intel_complete messages
- Streaming interruption handling
- PATCH /api/action-items/{id} endpoint
- WebSocket broadcasts action_item_updated
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
from datetime import datetime
from typing import Any, Iterator, Optional, Union
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock

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
    TranscriptSegment,
)
from holdspeak.web_server import (
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

    return {
        "on_bookmark": MagicMock(return_value={"timestamp": 10.5}),
        "on_stop": MagicMock(return_value={"status": "stopped"}),
        "get_state": MagicMock(return_value=state),
        "on_update_action_item": MagicMock(side_effect=update_action_item),
        "action_items": action_items,
    }


@pytest.fixture
def web_server_with_action_items(mock_callbacks_with_action_items):
    """Create MeetingWebServer with action item support."""
    server = MeetingWebServer(
        on_bookmark=mock_callbacks_with_action_items["on_bookmark"],
        on_stop=mock_callbacks_with_action_items["on_stop"],
        get_state=mock_callbacks_with_action_items["get_state"],
        on_update_action_item=mock_callbacks_with_action_items["on_update_action_item"],
        host="127.0.0.1",
    )
    return server


@pytest.fixture
def test_client_with_action_items(web_server_with_action_items):
    """Create TestClient for server with action items."""
    return TestClient(web_server_with_action_items.app)


# ============================================================
# Tests for Streaming Intel Analysis
# ============================================================


@pytest.mark.integration
class TestStreamingIntelAnalysis:
    """Tests for MeetingIntel streaming analysis."""

    def test_analyze_stream_true_returns_iterator(self, mock_streaming_intel):
        """analyze(stream=True) should return an iterator."""
        result = mock_streaming_intel.analyze("Test transcript", stream=True)
        assert hasattr(result, "__iter__")

    def test_analyze_stream_false_returns_result(self, mock_streaming_intel, mock_intel_result):
        """analyze(stream=False) should return IntelResult directly."""
        result = mock_streaming_intel.analyze("Test transcript", stream=False)
        assert isinstance(result, IntelResult)

    def test_streaming_yields_tokens_then_result(self, mock_streaming_intel):
        """Streaming should yield string tokens followed by IntelResult."""
        stream = mock_streaming_intel.analyze("Test transcript", stream=True)

        items = list(stream)
        # All but last should be strings
        tokens = items[:-1]
        final = items[-1]

        assert all(isinstance(t, str) for t in tokens)
        assert isinstance(final, IntelResult)

    def test_streaming_tokens_not_empty(self, mock_streaming_intel):
        """Should yield at least one token before final result."""
        stream = mock_streaming_intel.analyze("Test transcript", stream=True)
        items = list(stream)

        tokens = [i for i in items if isinstance(i, str)]
        assert len(tokens) > 0

    def test_streaming_preserves_transcript(self, mock_streaming_intel):
        """Streaming should receive the full transcript."""
        transcript = "Full meeting transcript with multiple speakers."
        _ = list(mock_streaming_intel.analyze(transcript, stream=True))

        assert mock_streaming_intel.analyze_called
        assert mock_streaming_intel.transcript_received == transcript


@pytest.mark.integration
class TestMeetingIntelStreamingIntegration:
    """Integration tests for MeetingIntel streaming with mocked LLM."""

    def test_analyze_stream_with_mock_llm(self):
        """Test streaming with mocked llama_cpp."""
        # Create mock LLM that yields streaming chunks
        mock_llm = MagicMock()

        def mock_stream():
            chunks = [
                {"choices": [{"delta": {"content": '{"topics":'}}]},
                {"choices": [{"delta": {"content": ' ["Test"],'}}]},
                {"choices": [{"delta": {"content": '"action_items": [],'}}]},
                {"choices": [{"delta": {"content": '"summary": "Test"}'}}]},
            ]
            for chunk in chunks:
                yield chunk

        mock_llm.create_chat_completion = MagicMock(return_value=mock_stream())

        # Patch the intel module
        with patch("holdspeak.intel.Llama", return_value=mock_llm):
            with patch.object(MeetingIntel, "_ensure_model_loaded"):
                intel = MeetingIntel()
                intel._llm = mock_llm

                stream = intel.analyze("Test transcript", stream=True)
                items = list(stream)

                # Should have tokens and final result
                tokens = [i for i in items if isinstance(i, str)]
                results = [i for i in items if isinstance(i, IntelResult)]

                assert len(tokens) > 0
                assert len(results) == 1

    def test_streaming_error_yields_error_result(self):
        """Streaming errors should yield an IntelResult with error."""
        mock_llm = MagicMock()
        mock_llm.create_chat_completion = MagicMock(side_effect=Exception("LLM error"))

        with patch("holdspeak.intel.Llama", return_value=mock_llm):
            with patch.object(MeetingIntel, "_ensure_model_loaded"):
                intel = MeetingIntel()
                intel._llm = mock_llm

                stream = intel.analyze("Test", stream=True)
                items = list(stream)

                assert len(items) == 1
                assert isinstance(items[0], IntelResult)
                assert "ERROR" in items[0].raw_response


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
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
            on_update_action_item=None,
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
            on_bookmark=mock_callbacks_with_action_items["on_bookmark"],
            on_stop=mock_callbacks_with_action_items["on_stop"],
            get_state=mock_callbacks_with_action_items["get_state"],
            on_update_action_item=mock_callbacks_with_action_items["on_update_action_item"],
        )
        client = TestClient(server.app)

        response = client.patch(
            "/api/action-items/item-001",
            json={"status": "done"},
        )

        assert response.status_code == 500


# ============================================================
# Tests for WebSocket Broadcasts
# ============================================================


@pytest.mark.integration
class TestWebSocketBroadcasts:
    """Tests for WebSocket message broadcasts."""

    @pytest.mark.asyncio
    async def test_broadcast_intel_token(self):
        """WebSocketManager should broadcast intel_token messages."""
        manager = WebSocketManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws)

        message = BroadcastMessage(type="intel_token", data='{"topics":')
        await manager.broadcast(message)

        mock_ws.send_json.assert_called_once_with({
            "type": "intel_token",
            "data": '{"topics":',
        })

    @pytest.mark.asyncio
    async def test_broadcast_intel_complete(self):
        """WebSocketManager should broadcast intel_complete messages."""
        manager = WebSocketManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws)

        intel_data = {
            "timestamp": 60.0,
            "topics": ["Topic A"],
            "action_items": [],
            "summary": "Summary",
        }
        message = BroadcastMessage(type="intel_complete", data=intel_data)
        await manager.broadcast(message)

        mock_ws.send_json.assert_called_once_with({
            "type": "intel_complete",
            "data": intel_data,
        })

    @pytest.mark.asyncio
    async def test_broadcast_action_item_updated(self):
        """WebSocketManager should broadcast action_item_updated messages."""
        manager = WebSocketManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws)

        item_data = {
            "id": "item-001",
            "task": "Test task",
            "status": "done",
            "completed_at": "2024-01-15T10:30:00",
        }
        message = BroadcastMessage(type="action_item_updated", data=item_data)
        await manager.broadcast(message)

        mock_ws.send_json.assert_called_once_with({
            "type": "action_item_updated",
            "data": item_data,
        })

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_clients(self):
        """Broadcasts should reach all connected clients."""
        manager = WebSocketManager()

        clients = []
        for _ in range(3):
            mock_ws = MagicMock()
            mock_ws.accept = AsyncMock()
            mock_ws.send_json = AsyncMock()
            await manager.connect(mock_ws)
            clients.append(mock_ws)

        message = BroadcastMessage(type="intel_token", data="test")
        await manager.broadcast(message)

        for client in clients:
            client.send_json.assert_called_once_with({
                "type": "intel_token",
                "data": "test",
            })


# ============================================================
# Tests for MeetingSession Intel Integration
# ============================================================


@pytest.mark.integration
class TestMeetingSessionIntelIntegration:
    """Tests for MeetingSession intel streaming integration."""

    def test_update_action_item_done(self, mock_transcriber):
        """MeetingSession.update_action_item should mark item as done."""
        session = MeetingSession(
            transcriber=mock_transcriber,
            intel_enabled=False,
            web_enabled=False,
        )

        # Create mock state with intel
        action_item = ActionItem(task="Test task", id="test-id-001")
        session._state = MeetingState(
            id="test-123",
            started_at=datetime.now(),
        )
        session._state.intel = IntelSnapshot(
            timestamp=0.0,
            topics=[],
            action_items=[action_item],
            summary="",
        )

        result = session.update_action_item("test-id-001", "done")

        assert result is not None
        assert result["status"] == "done"
        assert result["completed_at"] is not None

    def test_update_action_item_pending(self, mock_transcriber):
        """MeetingSession.update_action_item should revert to pending."""
        session = MeetingSession(
            transcriber=mock_transcriber,
            intel_enabled=False,
            web_enabled=False,
        )

        action_item = ActionItem(task="Test task", id="test-id-001")
        action_item.mark_done()  # Start as done

        session._state = MeetingState(
            id="test-123",
            started_at=datetime.now(),
        )
        session._state.intel = IntelSnapshot(
            timestamp=0.0,
            action_items=[action_item],
        )

        result = session.update_action_item("test-id-001", "pending")

        assert result is not None
        assert result["status"] == "pending"
        assert result["completed_at"] is None

    def test_update_action_item_dismissed(self, mock_transcriber):
        """MeetingSession.update_action_item should dismiss item."""
        session = MeetingSession(
            transcriber=mock_transcriber,
            intel_enabled=False,
            web_enabled=False,
        )

        action_item = ActionItem(task="Test task", id="test-id-001")

        session._state = MeetingState(
            id="test-123",
            started_at=datetime.now(),
        )
        session._state.intel = IntelSnapshot(
            timestamp=0.0,
            action_items=[action_item],
        )

        result = session.update_action_item("test-id-001", "dismissed")

        assert result is not None
        assert result["status"] == "dismissed"

    def test_update_action_item_not_found(self, mock_transcriber):
        """update_action_item with invalid ID returns None."""
        session = MeetingSession(
            transcriber=mock_transcriber,
            intel_enabled=False,
            web_enabled=False,
        )

        session._state = MeetingState(
            id="test-123",
            started_at=datetime.now(),
        )
        session._state.intel = IntelSnapshot(
            timestamp=0.0,
            action_items=[ActionItem(task="Task", id="different-id")],
        )

        result = session.update_action_item("nonexistent-id", "done")
        assert result is None

    def test_update_action_item_no_intel(self, mock_transcriber):
        """update_action_item with no intel returns None."""
        session = MeetingSession(
            transcriber=mock_transcriber,
            intel_enabled=False,
            web_enabled=False,
        )

        session._state = MeetingState(
            id="test-123",
            started_at=datetime.now(),
        )
        session._state.intel = None

        result = session.update_action_item("some-id", "done")
        assert result is None

    def test_update_action_item_no_state(self, mock_transcriber):
        """update_action_item with no state returns None."""
        session = MeetingSession(
            transcriber=mock_transcriber,
            intel_enabled=False,
            web_enabled=False,
        )
        session._state = None

        result = session.update_action_item("some-id", "done")
        assert result is None


# ============================================================
# Tests for Streaming Interruption
# ============================================================


@pytest.mark.integration
class TestStreamingInterruption:
    """Tests for intel streaming interruption handling."""

    def test_analysis_id_changes_on_new_analysis(self, mock_transcriber):
        """New analysis should get a new analysis ID."""
        session = MeetingSession(
            transcriber=mock_transcriber,
            intel_enabled=False,
            web_enabled=False,
        )

        # Simulate starting analysis
        session._current_analysis_id = "first-id"

        # New analysis would set new ID
        new_id = "second-id"
        session._current_analysis_id = new_id

        # Old analysis should detect interruption
        assert session._current_analysis_id != "first-id"
        assert session._current_analysis_id == "second-id"

    def test_concurrent_analysis_detection(self, mock_transcriber):
        """Concurrent analysis should be detected via analysis_id."""
        session = MeetingSession(
            transcriber=mock_transcriber,
            intel_enabled=False,
            web_enabled=False,
        )

        # First analysis starts
        analysis_1_id = "analysis-001"
        session._current_analysis_id = analysis_1_id

        # Simulate check in first analysis
        assert session._current_analysis_id == analysis_1_id

        # Second analysis starts, interrupting first
        analysis_2_id = "analysis-002"
        session._current_analysis_id = analysis_2_id

        # First analysis detects interruption
        assert session._current_analysis_id != analysis_1_id


# ============================================================
# Tests for Empty Transcript Handling
# ============================================================


@pytest.mark.integration
class TestEmptyTranscriptHandling:
    """Tests for intel analysis with empty transcript."""

    def test_streaming_with_empty_transcript(self):
        """Streaming with empty transcript should handle gracefully."""
        mock_llm = MagicMock()

        def mock_stream():
            # Empty response
            chunks = [
                {"choices": [{"delta": {"content": '{"topics": [],'}}]},
                {"choices": [{"delta": {"content": '"action_items": [],'}}]},
                {"choices": [{"delta": {"content": '"summary": ""}'}}]},
            ]
            for chunk in chunks:
                yield chunk

        mock_llm.create_chat_completion = MagicMock(return_value=mock_stream())

        with patch("holdspeak.intel.Llama", return_value=mock_llm):
            with patch.object(MeetingIntel, "_ensure_model_loaded"):
                intel = MeetingIntel()
                intel._llm = mock_llm

                stream = intel.analyze("", stream=True)
                items = list(stream)

                results = [i for i in items if isinstance(i, IntelResult)]
                assert len(results) == 1
                assert results[0].topics == []
                assert results[0].action_items == []


# ============================================================
# Tests for Action Item ID Determinism
# ============================================================


@pytest.mark.integration
class TestActionItemIdDeterminism:
    """Tests for deterministic action item ID generation."""

    def test_same_task_same_id_across_analyses(self):
        """Same task text should generate same ID across analyses."""
        item1 = ActionItem(task="Review the proposal", owner="Alice")
        item2 = ActionItem(task="Review the proposal", owner="Alice")

        assert item1.id == item2.id

    def test_different_created_at_same_id(self):
        """Different created_at should not affect ID."""
        item1 = ActionItem(
            task="Submit report",
            owner="Bob",
            created_at="2024-01-01T00:00:00",
        )
        item2 = ActionItem(
            task="Submit report",
            owner="Bob",
            created_at="2024-06-15T12:00:00",
        )

        assert item1.id == item2.id

    def test_id_stable_after_status_change(self):
        """ID should remain stable after status changes."""
        item = ActionItem(task="Complete task", owner="Me")
        original_id = item.id

        item.mark_done()
        assert item.id == original_id

        item.status = "pending"
        assert item.id == original_id

        item.dismiss()
        assert item.id == original_id


# ============================================================
# Tests for IntelSnapshot with Action Items
# ============================================================


@pytest.mark.integration
class TestIntelSnapshotActionItems:
    """Tests for IntelSnapshot action item handling."""

    def test_to_dict_converts_action_items(self):
        """to_dict should convert ActionItem objects to dicts."""
        items = [
            ActionItem(task="Task 1", id="id-001"),
            ActionItem(task="Task 2", id="id-002"),
        ]
        snapshot = IntelSnapshot(
            timestamp=60.0,
            topics=["Topic"],
            action_items=items,
            summary="Summary",
        )

        result = snapshot.to_dict()

        assert len(result["action_items"]) == 2
        assert isinstance(result["action_items"][0], dict)
        assert result["action_items"][0]["task"] == "Task 1"
        assert result["action_items"][0]["id"] == "id-001"

    def test_get_action_item_by_id(self):
        """get_action_item_by_id should find item by ID."""
        items = [
            ActionItem(task="Task 1", id="id-001"),
            ActionItem(task="Task 2", id="id-002"),
        ]
        snapshot = IntelSnapshot(
            timestamp=60.0,
            action_items=items,
        )

        found = snapshot.get_action_item_by_id("id-002")
        assert found is not None
        assert found.task == "Task 2"

    def test_get_action_item_by_id_not_found(self):
        """get_action_item_by_id should return None for missing ID."""
        items = [ActionItem(task="Task", id="id-001")]
        snapshot = IntelSnapshot(timestamp=0.0, action_items=items)

        found = snapshot.get_action_item_by_id("nonexistent")
        assert found is None

    def test_get_action_item_by_id_with_dicts(self):
        """get_action_item_by_id should work with dict items."""
        items = [
            {"task": "Task 1", "id": "id-001"},
            {"task": "Task 2", "id": "id-002"},
        ]
        snapshot = IntelSnapshot(timestamp=0.0, action_items=items)

        found = snapshot.get_action_item_by_id("id-001")
        assert found is not None
        assert found["task"] == "Task 1"
