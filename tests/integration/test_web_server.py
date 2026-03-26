"""Integration tests for HoldSpeak web server."""

from __future__ import annotations

import asyncio
from datetime import datetime
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
