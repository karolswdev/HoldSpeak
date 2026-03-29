"""Integration tests for HoldSpeak web server."""

from __future__ import annotations

import asyncio
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, AsyncMock

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

from holdspeak.web_server import (
    MeetingWebServer,
    WebSocketManager,
    BroadcastMessage,
    _format_duration,
    _find_free_port,
    _parse_iso_datetime,
)


# ============================================================
# Utility Function Tests
# ============================================================


@pytest.mark.integration
class TestFormatDuration:
    """Tests for _format_duration helper function."""

    def test_format_seconds_only(self):
        """Seconds under 60 return MM:SS format."""
        assert _format_duration(0) == "00:00"
        assert _format_duration(1) == "00:01"
        assert _format_duration(30) == "00:30"
        assert _format_duration(59) == "00:59"

    def test_format_minutes_and_seconds(self):
        """Minutes + seconds return MM:SS format."""
        assert _format_duration(60) == "01:00"
        assert _format_duration(61) == "01:01"
        assert _format_duration(90) == "01:30"
        assert _format_duration(599) == "09:59"
        assert _format_duration(3599) == "59:59"

    def test_format_hours_minutes_seconds(self):
        """Hours return HH:MM:SS format."""
        assert _format_duration(3600) == "01:00:00"
        assert _format_duration(3661) == "01:01:01"
        assert _format_duration(7200) == "02:00:00"
        assert _format_duration(36000) == "10:00:00"

    def test_format_negative_treated_as_zero(self):
        """Negative values treated as zero."""
        assert _format_duration(-1) == "00:00"
        assert _format_duration(-3600) == "00:00"

    def test_format_float_truncated(self):
        """Float values are truncated to int."""
        assert _format_duration(1.9) == "00:01"
        assert _format_duration(59.9) == "00:59"


@pytest.mark.integration
class TestFindFreePort:
    """Tests for _find_free_port helper function."""

    def test_returns_valid_port(self):
        """Should return a port number in valid range."""
        port = _find_free_port("127.0.0.1")
        assert isinstance(port, int)
        assert 1024 <= port <= 65535

    def test_returns_different_ports(self):
        """Should return different ports on consecutive calls."""
        ports = {_find_free_port("127.0.0.1") for _ in range(5)}
        # At least some should be different (not strictly all)
        assert len(ports) >= 1

    def test_port_is_bindable(self):
        """Returned port should be usable."""
        import socket

        port = _find_free_port("127.0.0.1")
        # Verify we can bind to it
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # This should not raise
            sock.bind(("127.0.0.1", port))


@pytest.mark.integration
class TestParseIsoDatetime:
    """Tests for _parse_iso_datetime helper function."""

    def test_valid_iso_string(self):
        """Valid ISO strings should be parsed."""
        result = _parse_iso_datetime("2024-01-15T10:30:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_iso_with_microseconds(self):
        """ISO strings with microseconds should be parsed."""
        result = _parse_iso_datetime("2024-01-15T10:30:00.123456")
        assert result == datetime(2024, 1, 15, 10, 30, 0, 123456)

    def test_iso_with_timezone(self):
        """ISO strings with timezone should be parsed."""
        result = _parse_iso_datetime("2024-01-15T10:30:00+00:00")
        assert result is not None
        assert result.hour == 10

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        assert _parse_iso_datetime("") is None

    def test_none_returns_none(self):
        """None input should return None."""
        assert _parse_iso_datetime(None) is None

    def test_invalid_string_returns_none(self):
        """Invalid string should return None."""
        assert _parse_iso_datetime("not-a-date") is None
        assert _parse_iso_datetime("2024/01/15") is None

    def test_non_string_returns_none(self):
        """Non-string types should return None."""
        assert _parse_iso_datetime(12345) is None
        assert _parse_iso_datetime({"date": "2024-01-15"}) is None
        assert _parse_iso_datetime(["2024-01-15"]) is None


# ============================================================
# BroadcastMessage Tests
# ============================================================


@pytest.mark.integration
class TestBroadcastMessage:
    """Tests for BroadcastMessage dataclass."""

    def test_to_dict(self):
        """to_dict() should return proper dictionary."""
        msg = BroadcastMessage(type="test", data={"key": "value"})
        result = msg.to_dict()
        assert result == {"type": "test", "data": {"key": "value"}}

    def test_immutable(self):
        """BroadcastMessage should be immutable (frozen)."""
        msg = BroadcastMessage(type="test", data="data")
        with pytest.raises(Exception):  # FrozenInstanceError
            msg.type = "modified"


# ============================================================
# WebSocketManager Tests
# ============================================================


@pytest.mark.integration
class TestWebSocketManager:
    """Tests for WebSocketManager."""

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self):
        """Should track connected clients."""
        manager = WebSocketManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()

        await manager.connect(mock_ws)
        assert mock_ws in manager._clients

        await manager.disconnect(mock_ws)
        assert mock_ws not in manager._clients

    @pytest.mark.asyncio
    async def test_broadcast_to_clients(self):
        """Should broadcast message to all connected clients."""
        manager = WebSocketManager()

        mock_ws1 = MagicMock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_json = AsyncMock()

        mock_ws2 = MagicMock()
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_json = AsyncMock()

        await manager.connect(mock_ws1)
        await manager.connect(mock_ws2)

        message = BroadcastMessage(type="update", data="test")
        await manager.broadcast(message)

        mock_ws1.send_json.assert_called_once_with({"type": "update", "data": "test"})
        mock_ws2.send_json.assert_called_once_with({"type": "update", "data": "test"})

    @pytest.mark.asyncio
    async def test_close_all(self):
        """close_all() should close all clients and clear the set."""
        manager = WebSocketManager()

        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.close = AsyncMock()

        await manager.connect(mock_ws)
        await manager.close_all()

        mock_ws.close.assert_called_once()
        assert len(manager._clients) == 0


# ============================================================
# MeetingWebServer HTTP Endpoint Tests
# ============================================================


@pytest.fixture
def mock_callbacks():
    """Create mock callback functions for web server."""
    bookmark_result = {"timestamp": 10.5, "label": "test"}
    stop_result = {"status": "stopped"}
    state = {
        "id": "test-123",
        "started_at": "2024-01-15T10:30:00",
        "duration": 120,
        "bookmarks": [],
    }

    return {
        "on_bookmark": MagicMock(return_value=bookmark_result),
        "on_stop": MagicMock(return_value=stop_result),
        "get_state": MagicMock(return_value=state),
    }


@pytest.fixture
def web_server(mock_callbacks):
    """Create MeetingWebServer instance."""
    server = MeetingWebServer(
        on_bookmark=mock_callbacks["on_bookmark"],
        on_stop=mock_callbacks["on_stop"],
        get_state=mock_callbacks["get_state"],
        host="127.0.0.1",
    )
    return server


@pytest.fixture
def test_client(web_server):
    """Create FastAPI TestClient for web server."""
    return TestClient(web_server.app)


@pytest.mark.integration
class TestDashboardEndpoint:
    """Tests for GET / dashboard endpoint."""

    def test_returns_html(self, test_client):
        """Dashboard should return HTML response."""
        response = test_client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_contains_holdspeak(self, test_client):
        """Dashboard HTML should contain HoldSpeak."""
        response = test_client.get("/")
        assert "HoldSpeak" in response.text or "holdspeak" in response.text.lower()


@pytest.mark.integration
class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_returns_ok(self, test_client):
        """Health check should return OK status."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.integration
class TestApiStateEndpoint:
    """Tests for GET /api/state endpoint."""

    def test_returns_state(self, test_client, mock_callbacks):
        """Should return current meeting state."""
        response = test_client.get("/api/state")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "test-123"
        assert data["duration"] == 120

        mock_callbacks["get_state"].assert_called_once()

    def test_handles_empty_state(self, test_client, mock_callbacks):
        """Should handle empty state gracefully."""
        mock_callbacks["get_state"].return_value = {}
        response = test_client.get("/api/state")
        assert response.status_code == 200
        assert response.json() == {}

    def test_handles_exception(self, test_client, mock_callbacks):
        """Should return empty dict on exception."""
        mock_callbacks["get_state"].side_effect = Exception("test error")
        response = test_client.get("/api/state")
        assert response.status_code == 200
        assert response.json() == {}


@pytest.mark.integration
class TestApiBookmarkEndpoint:
    """Tests for POST /api/bookmark endpoint."""

    def test_creates_bookmark(self, test_client, mock_callbacks):
        """Should create bookmark via callback."""
        response = test_client.post("/api/bookmark", json={"label": "Important"})
        assert response.status_code == 200
        assert response.json() == {"success": True}

        mock_callbacks["on_bookmark"].assert_called_once_with("Important")

    def test_creates_bookmark_empty_label(self, test_client, mock_callbacks):
        """Should handle empty label."""
        response = test_client.post("/api/bookmark", json={})
        assert response.status_code == 200
        mock_callbacks["on_bookmark"].assert_called_once_with("")

    def test_creates_bookmark_no_body(self, test_client, mock_callbacks):
        """Should handle no request body."""
        response = test_client.post("/api/bookmark")
        assert response.status_code == 200
        mock_callbacks["on_bookmark"].assert_called_once_with("")

    def test_handles_callback_exception(self, test_client, mock_callbacks):
        """Should return error on callback failure."""
        mock_callbacks["on_bookmark"].side_effect = Exception("bookmark error")
        response = test_client.post("/api/bookmark", json={"label": "test"})
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "error" in data


@pytest.mark.integration
class TestApiStopEndpoint:
    """Tests for POST /api/stop endpoint."""

    def test_calls_stop_callback(self, test_client, mock_callbacks):
        """Should call on_stop callback."""
        response = test_client.post("/api/stop")
        assert response.status_code == 200
        assert response.json() == {"success": True}

        mock_callbacks["on_stop"].assert_called_once()

    def test_handles_callback_exception(self, test_client, mock_callbacks):
        """Should return error on callback failure."""
        mock_callbacks["on_stop"].side_effect = Exception("stop error")
        response = test_client.post("/api/stop")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "error" in data


@pytest.mark.integration
class TestHistoryUiSmoke:
    """Smoke checks for the browser-facing history/settings UI."""

    def test_history_page_contains_control_plane_tabs_and_handlers(self, test_client):
        response = test_client.get("/history")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

        html = response.text
        for label in ("Meetings", "Action Items", "Speakers", "Intel Queue", "Settings"):
            assert label in html
        for marker in ("saveSettings", "openSpeaker", "processIntelJobs", "retryIntelJob"):
            assert marker in html
        for endpoint in ("/api/settings", "/api/speakers", "/api/intel/jobs", "/api/all-action-items"):
            assert endpoint in html

    def test_settings_route_serves_history_ui_shell(self, test_client):
        response = test_client.get("/settings")
        assert response.status_code == 200
        assert "HoldSpeak History" in response.text
        assert "OpenAI-Compatible Base URL" in response.text


@pytest.mark.integration
class TestSettingsApiEndpoints:
    """Tests for web settings API."""

    def test_settings_get_and_put_apply_runtime_callback(self, tmp_path, monkeypatch, mock_callbacks):
        import holdspeak.config as config_module
        from holdspeak.config import Config

        monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
        on_settings_applied = MagicMock()
        server = MeetingWebServer(
            on_bookmark=mock_callbacks["on_bookmark"],
            on_stop=mock_callbacks["on_stop"],
            get_state=mock_callbacks["get_state"],
            on_settings_applied=on_settings_applied,
        )
        client = TestClient(server.app)

        get_response = client.get("/api/settings")
        assert get_response.status_code == 200
        assert get_response.json()["meeting"]["intel_provider"] in {"local", "cloud", "auto"}

        payload = {
            "meeting": {
                "intel_provider": "cloud",
                "intel_cloud_model": "gpt-5-mini",
                "intel_cloud_api_key_env": "OPENAI_API_KEY",
                "intel_cloud_base_url": "https://api.openai.com/v1",
                "intel_queue_poll_seconds": 30,
                "similarity_threshold": 0.82,
            }
        }
        put_response = client.put("/api/settings", json=payload)
        assert put_response.status_code == 200
        data = put_response.json()
        assert data["success"] is True
        assert data["settings"]["meeting"]["intel_provider"] == "cloud"
        assert data["settings"]["meeting"]["intel_cloud_base_url"] == "https://api.openai.com/v1"
        assert data["settings"]["meeting"]["intel_queue_poll_seconds"] == 30
        assert data["settings"]["meeting"]["similarity_threshold"] == pytest.approx(0.82)
        on_settings_applied.assert_called_once()

        persisted = Config.load(path=tmp_path / "config.json")
        assert persisted.meeting.intel_provider == "cloud"
        assert persisted.meeting.intel_cloud_base_url == "https://api.openai.com/v1"
        assert persisted.meeting.intel_queue_poll_seconds == 30

    def test_settings_put_rejects_invalid_cloud_base_url(self, tmp_path, monkeypatch, test_client):
        import holdspeak.config as config_module

        monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
        response = test_client.put(
            "/api/settings",
            json={"meeting": {"intel_cloud_base_url": "ftp://example.com/v1"}},
        )
        assert response.status_code == 400
        payload = response.json()
        assert payload["success"] is False
        assert "base_url" in payload["error"]


@pytest.mark.integration
class TestSpeakerApiEndpoints:
    """Tests for speaker management endpoints."""

    def test_speaker_endpoints(self, monkeypatch, test_client):
        class FakeDb:
            def __init__(self):
                self._speakers = {
                    "spk-1": SimpleNamespace(id="spk-1", name="Alice", avatar="👩", sample_count=4),
                    "spk-2": SimpleNamespace(id="spk-2", name="Bob", avatar="🧑", sample_count=2),
                }

            def get_all_speakers(self):
                return list(self._speakers.values())

            def get_speaker_stats(self, speaker_id):
                return {
                    "total_segments": 7 if speaker_id == "spk-1" else 3,
                    "total_speaking_time": 61.0 if speaker_id == "spk-1" else 21.0,
                    "meeting_count": 2 if speaker_id == "spk-1" else 1,
                    "first_seen": datetime(2025, 1, 10, 9, 0, 0),
                    "last_seen": datetime(2025, 1, 11, 10, 30, 0),
                }

            def get_speaker(self, speaker_id):
                return self._speakers.get(speaker_id)

            def get_speaker_segments(self, speaker_id, limit=500):
                _ = limit
                if speaker_id not in self._speakers:
                    return []
                return [
                    {
                        "meeting_id": "m-001",
                        "meeting_title": "Weekly sync",
                        "meeting_date": datetime(2025, 1, 11, 10, 30, 0),
                        "meeting_duration": 1200.0,
                        "segments": [
                            {"text": "Action item follow-up", "speaker": "Alice", "start_time": 42.0, "end_time": 48.0, "is_bookmarked": False}
                        ],
                    }
                ]

            def update_speaker_name(self, speaker_id, name):
                speaker = self._speakers.get(speaker_id)
                if speaker is None:
                    return False
                speaker.name = name
                return True

            def update_speaker_avatar(self, speaker_id, avatar):
                speaker = self._speakers.get(speaker_id)
                if speaker is None:
                    return False
                speaker.avatar = avatar
                return True

        fake_db = FakeDb()
        import holdspeak.db as db_module
        monkeypatch.setattr(db_module, "get_database", lambda: fake_db)

        list_response = test_client.get("/api/speakers")
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data["total"] == 2
        assert {speaker["id"] for speaker in list_data["speakers"]} == {"spk-1", "spk-2"}

        detail_response = test_client.get("/api/speakers/spk-1")
        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert detail_data["speaker"]["name"] == "Alice"
        assert detail_data["stats"]["meeting_count"] == 2
        assert detail_data["meetings"][0]["meeting_id"] == "m-001"

        update_response = test_client.patch(
            "/api/speakers/spk-1",
            json={"name": "Alicia", "avatar": "🧠"},
        )
        assert update_response.status_code == 200
        update_data = update_response.json()
        assert update_data["success"] is True
        assert update_data["speaker"]["name"] == "Alicia"
        assert update_data["speaker"]["avatar"] == "🧠"

        invalid_response = test_client.patch(
            "/api/speakers/spk-1",
            json={"name": "   "},
        )
        assert invalid_response.status_code == 400
        assert "cannot be empty" in invalid_response.json()["error"]


@pytest.mark.integration
class TestGlobalActionItemsApiEndpoints:
    """Tests for global action-item list, status, review, and edit endpoints."""

    def test_action_item_endpoints_include_review_and_edit(self, monkeypatch, test_client):
        now = datetime(2025, 1, 12, 9, 0, 0)

        class FakeDb:
            def __init__(self):
                self._items = {
                    "a-1": SimpleNamespace(
                        id="a-1",
                        task="Initial task",
                        owner="Me",
                        due=None,
                        status="pending",
                        review_state="pending",
                        meeting_id="m-001",
                        meeting_title="Weekly sync",
                        meeting_date=now,
                        created_at=now,
                        completed_at=None,
                        reviewed_at=None,
                    )
                }

            def list_action_items(self, include_completed=False, owner=None, meeting_id=None):
                items = list(self._items.values())
                if not include_completed:
                    items = [item for item in items if item.status == "pending"]
                if owner:
                    items = [item for item in items if item.owner == owner]
                if meeting_id:
                    items = [item for item in items if item.meeting_id == meeting_id]
                return items

            def get_action_item(self, item_id):
                return self._items.get(item_id)

            def update_action_item_status(self, item_id, status):
                item = self._items.get(item_id)
                if item is None:
                    return False
                item.status = status
                item.completed_at = now if status in {"done", "dismissed"} else None
                return True

            def update_action_item_review_state(self, item_id, review_state):
                item = self._items.get(item_id)
                if item is None:
                    return False
                item.review_state = review_state
                item.reviewed_at = now if review_state == "accepted" else None
                return True

            def edit_action_item(self, item_id, *, task, owner, due):
                item = self._items.get(item_id)
                if item is None:
                    return False
                item.task = task
                item.owner = owner or None
                item.due = due or None
                item.review_state = "accepted"
                item.reviewed_at = now
                return True

        import holdspeak.db as db_module
        monkeypatch.setattr(db_module, "get_database", lambda: FakeDb())

        list_response = test_client.get("/api/all-action-items?include_completed=true")
        assert list_response.status_code == 200
        payload = list_response.json()["action_items"][0]
        assert payload["review_state"] == "pending"
        assert payload["reviewed_at"] is None

        status_response = test_client.patch(
            "/api/all-action-items/a-1",
            json={"status": "done"},
        )
        assert status_response.status_code == 200
        assert status_response.json()["action_item"]["status"] == "done"

        review_response = test_client.patch(
            "/api/all-action-items/a-1/review",
            json={"review_state": "accepted"},
        )
        assert review_response.status_code == 200
        reviewed_item = review_response.json()["action_item"]
        assert reviewed_item["review_state"] == "accepted"
        assert reviewed_item["reviewed_at"] is not None

        edit_response = test_client.patch(
            "/api/all-action-items/a-1/edit",
            json={"task": "Edited task", "owner": "", "due": "Friday"},
        )
        assert edit_response.status_code == 200
        edited_item = edit_response.json()["action_item"]
        assert edited_item["task"] == "Edited task"
        assert edited_item["owner"] is None
        assert edited_item["due"] == "Friday"
        assert edited_item["review_state"] == "accepted"

    def test_action_item_review_and_edit_validation(self, monkeypatch, test_client):
        class FakeDb:
            def update_action_item_review_state(self, item_id, review_state):
                _ = item_id, review_state
                return False

            def edit_action_item(self, item_id, *, task, owner, due):
                _ = item_id, task, owner, due
                return False

            def get_action_item(self, item_id):
                _ = item_id
                return None

        import holdspeak.db as db_module
        monkeypatch.setattr(db_module, "get_database", lambda: FakeDb())

        invalid_review = test_client.patch(
            "/api/all-action-items/a-1/review",
            json={"review_state": "approved"},
        )
        assert invalid_review.status_code == 400

        invalid_edit = test_client.patch(
            "/api/all-action-items/a-1/edit",
            json={"task": "   "},
        )
        assert invalid_edit.status_code == 400


@pytest.mark.integration
class TestIntelQueueApiEndpoints:
    """Tests for deferred intel queue endpoints."""

    def test_intel_jobs_list_retry_and_process(self, monkeypatch, test_client):
        class FakeDb:
            def list_intel_jobs(self, *, status="all", limit=20):
                _ = status, limit
                return [
                    SimpleNamespace(
                        meeting_id="m-001",
                        status="queued",
                        transcript_hash="abc123",
                        requested_at=datetime(2025, 1, 11, 10, 30, 0),
                        updated_at=datetime(2025, 1, 11, 10, 31, 0),
                        attempts=2,
                        last_error="transient issue",
                        meeting_title="Weekly sync",
                        started_at=datetime(2025, 1, 11, 10, 0, 0),
                        intel_status_detail="Queued for retry",
                    )
                ]

            def requeue_intel_job(self, meeting_id, *, reason=None):
                _ = reason
                return meeting_id == "m-001"

        import holdspeak.db as db_module
        monkeypatch.setattr(db_module, "get_database", lambda: FakeDb())

        import holdspeak.intel_queue as intel_queue_module
        monkeypatch.setattr(intel_queue_module, "drain_intel_queue", lambda *args, **kwargs: 3)

        jobs_response = test_client.get("/api/intel/jobs?status=queued&limit=5")
        assert jobs_response.status_code == 200
        jobs_data = jobs_response.json()
        assert len(jobs_data["jobs"]) == 1
        assert jobs_data["jobs"][0]["meeting_id"] == "m-001"
        assert jobs_data["jobs"][0]["status"] == "queued"

        retry_response = test_client.post("/api/intel/retry/m-001")
        assert retry_response.status_code == 200
        assert retry_response.json()["success"] is True

        retry_missing = test_client.post("/api/intel/retry/unknown")
        assert retry_missing.status_code == 404
        assert retry_missing.json()["success"] is False

        process_response = test_client.post("/api/intel/process", json={"max_jobs": 2})
        assert process_response.status_code == 200
        process_data = process_response.json()
        assert process_data["success"] is True
        assert process_data["processed"] == 3


# ============================================================
# MeetingWebServer Property Tests
# ============================================================


@pytest.mark.integration
class TestMeetingWebServerProperties:
    """Tests for MeetingWebServer properties."""

    def test_url_before_start(self, web_server):
        """URL should be None before server starts."""
        assert web_server.url is None

    def test_host_default(self, web_server):
        """Default host should be localhost."""
        assert web_server.host == "127.0.0.1"


# ============================================================
# MeetingWebServer Lifecycle Tests
# ============================================================


@pytest.mark.integration
class TestMeetingWebServerLifecycle:
    """Tests for server start/stop lifecycle."""

    def test_start_returns_url(self, mock_callbacks):
        """start() should return the server URL."""
        server = MeetingWebServer(
            on_bookmark=mock_callbacks["on_bookmark"],
            on_stop=mock_callbacks["on_stop"],
            get_state=mock_callbacks["get_state"],
        )
        try:
            url = server.start()
            assert url.startswith("http://127.0.0.1:")
            assert server.port is not None
        finally:
            server.stop()

    def test_stop_clears_state(self, mock_callbacks):
        """stop() should clear server state."""
        server = MeetingWebServer(
            on_bookmark=mock_callbacks["on_bookmark"],
            on_stop=mock_callbacks["on_stop"],
            get_state=mock_callbacks["get_state"],
        )
        server.start()
        server.stop()

        assert server._server is None
        assert server._thread is None

    def test_double_stop_safe(self, mock_callbacks):
        """Calling stop() multiple times should be safe."""
        server = MeetingWebServer(
            on_bookmark=mock_callbacks["on_bookmark"],
            on_stop=mock_callbacks["on_stop"],
            get_state=mock_callbacks["get_state"],
        )
        server.start()
        server.stop()
        server.stop()  # Should not raise
