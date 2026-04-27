"""Integration tests for HoldSpeak web server."""

from __future__ import annotations

from copy import deepcopy
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

    def test_dashboard_references_runtime_control_endpoints(self, test_client):
        """Dashboard should use runtime-level meeting control endpoints."""
        response = test_client.get("/")
        assert response.status_code == 200
        html = response.text
        assert "/api/runtime/status" in html
        assert "/api/meeting/start" in html
        assert "/api/meeting/stop" in html
        assert "/api/intents/control" in html
        assert "/api/intents/profile" in html
        assert "/api/intents/override" in html
        assert "/api/intents/preview" in html
        assert "/api/plugin-jobs" in html
        assert "/api/plugin-jobs/summary" in html
        assert "/api/plugin-jobs/process" in html
        assert "Routing Profile" in html
        assert "Preview Route" in html
        assert "Deferred Plugin Jobs" in html

    def test_dashboard_includes_idle_mode_guidance_markers(self, test_client):
        """Dashboard should include explicit idle/live control guidance copy."""
        response = test_client.get("/")
        assert response.status_code == 200
        html = response.text
        assert "Idle mode: start a meeting to unlock live editing controls." in html
        assert "History and settings remain available while idle." in html
        assert "Read-only while idle. Start a meeting to edit status, review state, and details." in html

    def test_dashboard_bootstrap_prefers_runtime_status_payload(self, test_client):
        response = test_client.get("/")
        assert response.status_code == 200
        html = response.text
        assert "this.fetchRuntimeStatus();" in html
        assert "await this.fetchInitialState();" in html


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
class TestRuntimeControlEndpoints:
    """Tests for runtime-level meeting control routes."""

    def test_runtime_status_falls_back_to_state(self, test_client):
        response = test_client.get("/api/runtime/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["mode"] == "web"
        assert payload["meeting_active"] is True
        assert payload["meeting"]["id"] == "test-123"
        assert payload["meeting_id"] == "test-123"
        assert payload["state"]["id"] == "test-123"

    def test_runtime_status_prefers_explicit_meeting_active_flag(self, mock_callbacks):
        state = {
            "id": "web-runtime",
            "started_at": "2026-03-29T10:00:00",
            "ended_at": None,
            "meeting_active": False,
        }
        server = MeetingWebServer(
            on_bookmark=mock_callbacks["on_bookmark"],
            on_stop=mock_callbacks["on_stop"],
            get_state=MagicMock(return_value=state),
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        response = client.get("/api/runtime/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["meeting_active"] is False
        assert payload["meeting"] is None
        assert payload["meeting_id"] is None

    def test_runtime_status_normalizes_callback_payload(self, mock_callbacks):
        state = {"id": "runtime", "meeting_active": False, "segments": [], "bookmarks": []}
        server = MeetingWebServer(
            on_bookmark=mock_callbacks["on_bookmark"],
            on_stop=mock_callbacks["on_stop"],
            get_state=MagicMock(return_value=state),
            on_get_status=MagicMock(return_value={"voice_state": "idle"}),
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        response = client.get("/api/runtime/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["mode"] == "web"
        assert payload["meeting_active"] is False
        assert payload["voice_state"] == "idle"
        assert payload["state"]["id"] == "runtime"

    def test_meeting_start_not_supported_without_callback(self, test_client):
        response = test_client.post("/api/meeting/start")
        assert response.status_code == 501
        payload = response.json()
        assert payload["success"] is False

    def test_meeting_stop_uses_stop_callback_by_default(self, test_client, mock_callbacks):
        response = test_client.post("/api/meeting/stop")
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_callbacks["on_stop"].assert_called_once()

    def test_meeting_stop_prefers_on_meeting_stop_callback(self, mock_callbacks):
        on_meeting_stop = MagicMock(return_value={"status": "meeting_stopped"})
        server = MeetingWebServer(
            on_bookmark=mock_callbacks["on_bookmark"],
            on_stop=mock_callbacks["on_stop"],
            on_meeting_stop=on_meeting_stop,
            get_state=mock_callbacks["get_state"],
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        response = client.post("/api/meeting/stop")
        assert response.status_code == 200
        assert response.json()["success"] is True
        on_meeting_stop.assert_called_once()
        mock_callbacks["on_stop"].assert_not_called()


@pytest.mark.integration
class TestIntentRoutingControlEndpoints:
    """Tests for MIR control-plane endpoints."""

    def test_get_intent_controls_returns_safe_default_without_callback(self, test_client):
        response = test_client.get("/api/intents/control")
        assert response.status_code == 200
        payload = response.json()
        assert payload["enabled"] is False
        assert payload["profile"] == "balanced"
        assert payload["available_profiles"] == []
        assert payload["supported_intents"] == []

    def test_intent_profile_and_override_require_callbacks(self, test_client):
        profile_response = test_client.put("/api/intents/profile", json={"profile": "architect"})
        assert profile_response.status_code == 501
        override_response = test_client.put("/api/intents/override", json={"intents": ["architecture"]})
        assert override_response.status_code == 501
        preview_response = test_client.post("/api/intents/preview", json={"profile": "architect"})
        assert preview_response.status_code == 501

    def test_intent_controls_round_trip_with_callbacks(self, mock_callbacks):
        controls = {
            "enabled": True,
            "profile": "balanced",
            "available_profiles": ["balanced", "architect"],
            "supported_intents": ["architecture", "delivery"],
            "override_intents": [],
            "threshold": 0.6,
            "last_preview": None,
        }

        def _get_controls() -> dict[str, object]:
            return deepcopy(controls)

        def _set_profile(profile: str) -> dict[str, object]:
            controls["profile"] = str(profile).strip().lower() or "balanced"
            return _get_controls()

        def _set_override(intents: list[str] | None) -> dict[str, object]:
            controls["override_intents"] = [str(intent).strip().lower() for intent in (intents or []) if str(intent).strip()]
            return _get_controls()

        def _preview_route(**kwargs) -> dict[str, object]:
            _ = kwargs
            route = {
                "profile": controls["profile"],
                "active_intents": list(controls["override_intents"]) or ["architecture"],
                "plugin_chain": ["requirements_extractor", "mermaid_architecture"],
                "intent_scores": {"architecture": 0.84},
                "threshold": 0.6,
                "hysteresis_applied": False,
                "override_intents": list(controls["override_intents"]),
            }
            controls["last_preview"] = route
            return route

        server = MeetingWebServer(
            on_bookmark=mock_callbacks["on_bookmark"],
            on_stop=mock_callbacks["on_stop"],
            get_state=mock_callbacks["get_state"],
            on_get_intent_controls=_get_controls,
            on_set_intent_profile=_set_profile,
            on_set_intent_override=_set_override,
            on_route_preview=_preview_route,
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        initial = client.get("/api/intents/control")
        assert initial.status_code == 200
        assert initial.json()["profile"] == "balanced"

        profile_update = client.put("/api/intents/profile", json={"profile": "architect"})
        assert profile_update.status_code == 200
        assert profile_update.json()["controls"]["profile"] == "architect"

        override_update = client.put("/api/intents/override", json={"intents": ["architecture", "delivery"]})
        assert override_update.status_code == 200
        assert override_update.json()["controls"]["override_intents"] == ["architecture", "delivery"]

        preview = client.post("/api/intents/preview", json={"profile": "architect"})
        assert preview.status_code == 200
        route = preview.json()["route"]
        assert route["profile"] == "architect"
        assert route["active_intents"] == ["architecture", "delivery"]
        assert "mermaid_architecture" in route["plugin_chain"]


@pytest.mark.integration
class TestMirHistoryApiEndpoints:
    """Tests for persisted MIR timeline and plugin-run meeting APIs."""

    def test_meeting_intent_timeline_endpoint(self, monkeypatch, test_client):
        now = datetime(2026, 3, 29, 18, 0, 0)

        class FakeDb:
            def get_meeting(self, meeting_id):
                if meeting_id != "m-001":
                    return None
                return SimpleNamespace(id="m-001")

            def list_intent_windows(self, meeting_id, *, limit=200):
                _ = meeting_id, limit
                return [
                    SimpleNamespace(
                        meeting_id="m-001",
                        window_id="m-001:w0001",
                        start_seconds=0.0,
                        end_seconds=90.0,
                        transcript_hash="h-1",
                        transcript_excerpt="Architecture and scope planning",
                        profile="balanced",
                        threshold=0.6,
                        active_intents=["architecture", "delivery"],
                        intent_scores={"architecture": 0.81, "delivery": 0.72},
                        override_intents=[],
                        tags=["architecture"],
                        metadata={"source": "route_preview"},
                        created_at=now,
                        updated_at=now,
                    ),
                    SimpleNamespace(
                        meeting_id="m-001",
                        window_id="m-001:w0002",
                        start_seconds=30.0,
                        end_seconds=120.0,
                        transcript_hash="h-2",
                        transcript_excerpt="Incident mitigation and handoff",
                        profile="incident_response",
                        threshold=0.5,
                        active_intents=["incident"],
                        intent_scores={"incident": 0.93},
                        override_intents=["incident"],
                        tags=["incident"],
                        metadata={"source": "route_preview"},
                        created_at=now,
                        updated_at=now,
                    ),
                ]

        import holdspeak.db as db_module

        monkeypatch.setattr(db_module, "get_database", lambda: FakeDb())

        response = test_client.get("/api/meetings/m-001/intent-timeline?limit=25")
        assert response.status_code == 200
        payload = response.json()
        assert payload["meeting_id"] == "m-001"
        assert len(payload["windows"]) == 2
        assert payload["windows"][0]["intent_scores"]["architecture"] == pytest.approx(0.81)
        assert payload["windows"][1]["active_intents"] == ["incident"]
        assert len(payload["transitions"]) == 2
        assert payload["transitions"][1]["added"] == ["incident"]

        missing = test_client.get("/api/meetings/missing/intent-timeline")
        assert missing.status_code == 404

    def test_meeting_plugin_runs_endpoint(self, monkeypatch, test_client):
        now = datetime(2026, 3, 29, 18, 0, 0)

        class FakeDb:
            def get_meeting(self, meeting_id):
                if meeting_id != "m-001":
                    return None
                return SimpleNamespace(id="m-001")

            def list_plugin_runs(self, meeting_id, *, window_id=None, limit=500):
                _ = meeting_id, limit
                all_runs = [
                    SimpleNamespace(
                        id=11,
                        meeting_id="m-001",
                        window_id="m-001:w0002",
                        plugin_id="incident_timeline",
                        plugin_version="preview",
                        status="planned",
                        idempotency_key="idem-2",
                        duration_ms=0.0,
                        output={"source": "route_preview"},
                        error=None,
                        deduped=False,
                        created_at=now,
                        updated_at=now,
                    ),
                    SimpleNamespace(
                        id=10,
                        meeting_id="m-001",
                        window_id="m-001:w0001",
                        plugin_id="requirements_extractor",
                        plugin_version="1.0.0",
                        status="success",
                        idempotency_key="idem-1",
                        duration_ms=44.2,
                        output={"requirements": 4},
                        error=None,
                        deduped=False,
                        created_at=now,
                        updated_at=now,
                    ),
                ]
                if window_id:
                    return [run for run in all_runs if run.window_id == window_id]
                return all_runs

        import holdspeak.db as db_module

        monkeypatch.setattr(db_module, "get_database", lambda: FakeDb())

        response = test_client.get("/api/meetings/m-001/plugin-runs?limit=50")
        assert response.status_code == 200
        payload = response.json()
        assert payload["meeting_id"] == "m-001"
        assert len(payload["runs"]) == 2
        assert payload["runs"][0]["plugin_id"] == "incident_timeline"
        assert payload["runs"][1]["status"] == "success"

        filtered = test_client.get("/api/meetings/m-001/plugin-runs?window_id=m-001:w0001")
        assert filtered.status_code == 200
        filtered_payload = filtered.json()
        assert filtered_payload["window_id"] == "m-001:w0001"
        assert len(filtered_payload["runs"]) == 1
        assert filtered_payload["runs"][0]["plugin_id"] == "requirements_extractor"

        missing = test_client.get("/api/meetings/missing/plugin-runs")
        assert missing.status_code == 404

    def test_meeting_artifacts_endpoint(self, monkeypatch, test_client):
        now = datetime(2026, 3, 29, 18, 0, 0)

        class FakeDb:
            def get_meeting(self, meeting_id):
                if meeting_id != "m-001":
                    return None
                return SimpleNamespace(id="m-001")

            def list_artifacts(self, meeting_id, *, limit=200):
                _ = meeting_id, limit
                return [
                    SimpleNamespace(
                        id="art-001",
                        meeting_id="m-001",
                        artifact_type="requirements",
                        title="Requirements Extractor",
                        body_markdown="### Requirements\n\nDefine API acceptance criteria.",
                        structured_json={"plugin_run_ids": ["10"], "window_ids": ["m-001:w0001"]},
                        confidence=0.82,
                        status="draft",
                        plugin_id="requirements_extractor",
                        plugin_version="1.0.0",
                        sources=[
                            {"source_type": "intent_window", "source_ref": "m-001:w0001"},
                            {"source_type": "plugin_run", "source_ref": "10"},
                        ],
                        created_at=now,
                        updated_at=now,
                    )
                ]

        import holdspeak.db as db_module

        monkeypatch.setattr(db_module, "get_database", lambda: FakeDb())

        response = test_client.get("/api/meetings/m-001/artifacts?limit=25")
        assert response.status_code == 200
        payload = response.json()
        assert payload["meeting_id"] == "m-001"
        assert len(payload["artifacts"]) == 1
        artifact = payload["artifacts"][0]
        assert artifact["artifact_type"] == "requirements"
        assert artifact["confidence"] == pytest.approx(0.82)
        refs = {(source["source_type"], source["source_ref"]) for source in artifact["sources"]}
        assert ("intent_window", "m-001:w0001") in refs
        assert ("plugin_run", "10") in refs

        missing = test_client.get("/api/meetings/missing/artifacts")
        assert missing.status_code == 404

    def test_legacy_meeting_without_mir_history_rows_remains_loadable(self, monkeypatch, test_client):
        class FakeDb:
            def get_meeting(self, meeting_id):
                if meeting_id != "m-legacy":
                    return None
                return SimpleNamespace(id="m-legacy")

            def list_intent_windows(self, meeting_id, *, limit=200):
                _ = meeting_id, limit
                return []

            def list_plugin_runs(self, meeting_id, *, window_id=None, limit=500):
                _ = meeting_id, window_id, limit
                return []

            def list_artifacts(self, meeting_id, *, limit=200):
                _ = meeting_id, limit
                return []

        import holdspeak.db as db_module

        monkeypatch.setattr(db_module, "get_database", lambda: FakeDb())

        timeline = test_client.get("/api/meetings/m-legacy/intent-timeline")
        assert timeline.status_code == 200
        timeline_payload = timeline.json()
        assert timeline_payload["meeting_id"] == "m-legacy"
        assert timeline_payload["windows"] == []
        assert timeline_payload["transitions"] == []

        runs = test_client.get("/api/meetings/m-legacy/plugin-runs")
        assert runs.status_code == 200
        runs_payload = runs.json()
        assert runs_payload["meeting_id"] == "m-legacy"
        assert runs_payload["runs"] == []

        artifacts = test_client.get("/api/meetings/m-legacy/artifacts")
        assert artifacts.status_code == 200
        artifacts_payload = artifacts.json()
        assert artifacts_payload["meeting_id"] == "m-legacy"
        assert artifacts_payload["artifacts"] == []

    def test_cli_reroute_persistence_is_visible_in_timeline_api(self, monkeypatch, test_client):
        now = datetime(2026, 3, 29, 19, 30, 0)
        windows_by_id: dict[str, dict[str, object]] = {}
        meeting = SimpleNamespace(
            id="m-reroute",
            title="Reroute Demo",
            tags=["incident"],
            segments=[
                SimpleNamespace(speaker="Me", text="We have an active incident bridge.", end_time=9.0),
                SimpleNamespace(speaker="Remote", text="Draft stakeholder comms and runbook changes.", end_time=18.0),
            ],
            duration=18.0,
            transcript_hash=lambda: "reroute-hash",
        )

        class FakeDb:
            def get_meeting(self, meeting_id):
                if meeting_id != "m-reroute":
                    return None
                return meeting

            def record_intent_window(self, **kwargs):
                windows_by_id[str(kwargs["window_id"])] = dict(kwargs)

            def list_intent_windows(self, meeting_id, *, limit=200):
                _ = limit
                if meeting_id != "m-reroute":
                    return []
                output = []
                for row in windows_by_id.values():
                    output.append(
                        SimpleNamespace(
                            meeting_id=str(row["meeting_id"]),
                            window_id=str(row["window_id"]),
                            start_seconds=float(row.get("start_seconds") or 0.0),
                            end_seconds=float(row.get("end_seconds") or 0.0),
                            transcript_hash=str(row.get("transcript_hash") or ""),
                            transcript_excerpt=str(row.get("transcript_excerpt") or ""),
                            profile=str(row.get("profile") or "balanced"),
                            threshold=float(row.get("threshold") or 0.6),
                            active_intents=list(row.get("active_intents") or []),
                            intent_scores=dict(row.get("intent_scores") or {}),
                            override_intents=list(row.get("override_intents") or []),
                            tags=list(row.get("tags") or []),
                            metadata=dict(row.get("metadata") or {}),
                            created_at=now,
                            updated_at=now,
                        )
                    )
                return output

        fake_db = FakeDb()
        import holdspeak.db as db_module
        import holdspeak.commands.intel as intel_command

        monkeypatch.setattr(db_module, "get_database", lambda: fake_db)
        monkeypatch.setattr(intel_command, "get_database", lambda: fake_db)
        monkeypatch.setattr(
            intel_command,
            "Config",
            SimpleNamespace(
                load=lambda: SimpleNamespace(
                    meeting=SimpleNamespace(mir_profile="balanced"),
                )
            ),
        )

        rc = intel_command.run_intel_command(
            SimpleNamespace(
                process=False,
                retry=None,
                retry_failed=False,
                route_dry_run=None,
                reroute="m-reroute",
                profile="incident",
                threshold=0.65,
                override_intents="incident,comms",
                status="all",
                limit=20,
                max_jobs=None,
            )
        )
        assert rc == 0

        response = test_client.get("/api/meetings/m-reroute/intent-timeline")
        assert response.status_code == 200
        payload = response.json()
        assert payload["meeting_id"] == "m-reroute"
        assert len(payload["windows"]) == 1
        window = payload["windows"][0]
        assert window["window_id"] == "m-reroute:cli-reroute"
        assert window["profile"] == "incident"
        assert window["override_intents"] == ["incident", "comms"]
        assert window["metadata"]["source"] == "cli_reroute"


@pytest.mark.integration
class TestMeetingMetadataEndpoints:
    """Tests for runtime-level meeting metadata updates."""

    def test_meeting_patch_uses_runtime_update_callback(self, mock_callbacks):
        on_update_meeting = MagicMock(
            return_value={
                "id": "meeting-1",
                "meeting_active": True,
                "title": "Planning Sync",
                "tags": ["ops", "planning"],
            }
        )
        server = MeetingWebServer(
            on_bookmark=mock_callbacks["on_bookmark"],
            on_stop=mock_callbacks["on_stop"],
            on_update_meeting=on_update_meeting,
            get_state=mock_callbacks["get_state"],
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        response = client.patch("/api/meeting", json={"title": "Planning Sync", "tags": ["ops", "planning"]})
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["meeting"]["title"] == "Planning Sync"
        assert payload["meeting"]["tags"] == ["ops", "planning"]
        on_update_meeting.assert_called_once_with(title="Planning Sync", tags=["ops", "planning"])

    def test_meeting_patch_falls_back_to_title_and_tags_callbacks(self, mock_callbacks):
        on_set_title = MagicMock()
        on_set_tags = MagicMock()
        get_state = MagicMock(
            return_value={
                "id": "meeting-2",
                "meeting_active": True,
                "title": "Retro",
                "tags": ["team"],
            }
        )
        server = MeetingWebServer(
            on_bookmark=mock_callbacks["on_bookmark"],
            on_stop=mock_callbacks["on_stop"],
            get_state=get_state,
            on_set_title=on_set_title,
            on_set_tags=on_set_tags,
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        response = client.patch("/api/meeting", json={"title": "Retro", "tags": ["team"]})
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["meeting"]["title"] == "Retro"
        assert payload["meeting"]["tags"] == ["team"]
        on_set_title.assert_called_once_with("Retro")
        on_set_tags.assert_called_once_with(["team"])


@pytest.mark.integration
class TestDashboardLifecycleStateTransitions:
    """Integration coverage for dashboard lifecycle controls and WS updates."""

    def test_start_stop_start_cycle_hydrates_state_and_emits_ws_events(self):
        state_holder: dict[str, dict[str, object]] = {
            "state": {
                "id": "web-runtime",
                "mode": "web",
                "meeting_active": False,
                "segments": [],
                "bookmarks": [],
                "intel": {"topics": [], "action_items": [], "summary": ""},
                "intel_status": {
                    "state": "idle",
                    "detail": "No meeting active",
                    "requested_at": None,
                    "completed_at": None,
                },
            }
        }
        meeting_counter = {"value": 0}

        def _active_meeting_state(index: int) -> dict[str, object]:
            return {
                "id": f"meeting-{index}",
                "mode": "web",
                "meeting_active": True,
                "title": f"Sprint Sync {index}",
                "tags": ["ops", f"cycle-{index}"],
                "segments": [
                    {
                        "speaker": "Me",
                        "start_time": 0.0,
                        "end_time": 1.2,
                        "text": f"cycle-{index} kickoff",
                    }
                ],
                "bookmarks": [{"timestamp": 0.6, "label": f"bookmark-{index}"}],
                "intel": {
                    "topics": [f"topic-{index}"],
                    "action_items": [
                        {
                            "id": f"ai-{index}",
                            "task": f"Ship patch {index}",
                            "owner": "Me",
                            "due": "Friday",
                            "status": "pending",
                            "review_state": "pending",
                        }
                    ],
                    "summary": f"summary-{index}",
                },
                "intel_status": {
                    "state": "ready",
                    "detail": f"intel-ready-{index}",
                    "requested_at": None,
                    "completed_at": None,
                },
            }

        def _get_state() -> dict[str, object]:
            return deepcopy(state_holder["state"])

        def _on_start() -> dict[str, object]:
            meeting_counter["value"] += 1
            next_state = _active_meeting_state(meeting_counter["value"])
            state_holder["state"] = deepcopy(next_state)
            return deepcopy(next_state)

        def _on_meeting_stop() -> dict[str, object]:
            stopped_state = deepcopy(state_holder["state"])
            stopped_state["meeting_active"] = False
            stopped_state["ended_at"] = "2026-03-29T18:00:00"
            state_holder["state"] = deepcopy(stopped_state)
            return {"status": "stopped", "meeting": deepcopy(stopped_state)}

        def _on_get_status() -> dict[str, object]:
            state = deepcopy(state_holder["state"])
            return {
                "status": "ok",
                "mode": "web",
                "meeting_active": bool(state.get("meeting_active")),
                "state": state,
            }

        server = MeetingWebServer(
            on_bookmark=MagicMock(return_value={"timestamp": 0.0, "label": "bookmark"}),
            on_stop=_on_meeting_stop,
            on_meeting_stop=_on_meeting_stop,
            on_start=_on_start,
            on_get_status=_on_get_status,
            get_state=_get_state,
            host="127.0.0.1",
        )
        broadcast_events: list[tuple[str, object]] = []
        server.broadcast = lambda message_type, data: broadcast_events.append(
            (message_type, deepcopy(data))
        )
        client = TestClient(server.app)

        initial_status = client.get("/api/runtime/status")
        assert initial_status.status_code == 200
        assert initial_status.json()["meeting_active"] is False
        assert initial_status.json()["state"]["id"] == "web-runtime"

        start_first = client.post("/api/meeting/start")
        assert start_first.status_code == 200
        assert start_first.json()["success"] is True
        assert start_first.json()["meeting"]["id"] == "meeting-1"

        status_after_first_start = client.get("/api/runtime/status")
        assert status_after_first_start.status_code == 200
        assert status_after_first_start.json()["meeting_active"] is True
        assert status_after_first_start.json()["state"]["id"] == "meeting-1"
        assert status_after_first_start.json()["state"]["intel"]["summary"] == "summary-1"

        stop_first = client.post("/api/meeting/stop")
        assert stop_first.status_code == 200
        assert stop_first.json()["success"] is True

        status_after_first_stop = client.get("/api/runtime/status")
        assert status_after_first_stop.status_code == 200
        assert status_after_first_stop.json()["meeting_active"] is False
        assert status_after_first_stop.json()["state"]["id"] == "meeting-1"
        assert status_after_first_stop.json()["state"]["ended_at"] == "2026-03-29T18:00:00"

        start_second = client.post("/api/meeting/start")
        assert start_second.status_code == 200
        assert start_second.json()["success"] is True
        assert start_second.json()["meeting"]["id"] == "meeting-2"

        state_after_second_start = client.get("/api/state")
        assert state_after_second_start.status_code == 200
        assert state_after_second_start.json()["id"] == "meeting-2"
        assert state_after_second_start.json()["segments"][0]["text"] == "cycle-2 kickoff"

        final_status = client.get("/api/runtime/status")
        assert final_status.status_code == 200
        assert final_status.json()["meeting_active"] is True
        assert final_status.json()["state"]["id"] == "meeting-2"
        assert [event[0] for event in broadcast_events] == [
            "meeting_started",
            "stopped",
            "meeting_started",
        ]
        assert broadcast_events[0][1]["id"] == "meeting-1"
        assert broadcast_events[1][1]["meeting"]["id"] == "meeting-1"
        assert broadcast_events[2][1]["id"] == "meeting-2"

    def test_websocket_supports_ping_pong_keepalive(self):
        server = MeetingWebServer(
            on_bookmark=MagicMock(return_value={"timestamp": 0.0, "label": "bookmark"}),
            on_stop=MagicMock(return_value={"status": "stopped"}),
            get_state=lambda: {},
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("ping")
            assert websocket.receive_text() == "pong"


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
        assert "Deferred Plugin Jobs" in html
        for marker in (
            "saveSettings",
            "openSpeaker",
            "processIntelJobs",
            "retryIntelJob",
            "loadPluginJobs",
            "retryPluginJob",
            "cancelPluginJob",
        ):
            assert marker in html
        for endpoint in (
            "/api/settings",
            "/api/speakers",
            "/api/intel/jobs",
            "/api/intel/summary",
            "/api/plugin-jobs",
            "/api/all-action-items",
        ):
            assert endpoint in html
        assert "source_timestamp" in html
        assert "Source ${formatTimestamp" in html
        assert "setActionReviewState" in html
        assert "Mark Needs Review" in html
        assert "actionReviewFilter" in html
        assert "Open Work" in html
        assert "No pending action items need review." in html

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
                "intel_retry_failure_webhook_url": "https://ops.example.com/hooks/holdspeak",
                "intel_retry_failure_webhook_header_name": "Authorization",
                "intel_retry_failure_webhook_header_value": "Bearer test-token",
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
        assert data["settings"]["meeting"]["intel_retry_failure_webhook_header_name"] == "Authorization"
        assert data["settings"]["meeting"]["intel_retry_failure_webhook_header_value"] == "Bearer test-token"
        assert data["settings"]["meeting"]["similarity_threshold"] == pytest.approx(0.82)
        on_settings_applied.assert_called_once()

        persisted = Config.load(path=tmp_path / "config.json")
        assert persisted.meeting.intel_provider == "cloud"
        assert persisted.meeting.intel_cloud_base_url == "https://api.openai.com/v1"
        assert persisted.meeting.intel_queue_poll_seconds == 30
        assert persisted.meeting.intel_retry_failure_webhook_header_name == "Authorization"
        assert persisted.meeting.intel_retry_failure_webhook_header_value == "Bearer test-token"

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

    def test_settings_put_rejects_invalid_retry_webhook_url(self, tmp_path, monkeypatch, test_client):
        import holdspeak.config as config_module

        monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
        response = test_client.put(
            "/api/settings",
            json={"meeting": {"intel_retry_failure_webhook_url": "ftp://example.com/hook"}},
        )
        assert response.status_code == 400
        payload = response.json()
        assert payload["success"] is False
        assert "webhook" in payload["error"].lower()

    def test_settings_put_rejects_partial_retry_webhook_header(self, tmp_path, monkeypatch, test_client):
        import holdspeak.config as config_module

        monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
        response = test_client.put(
            "/api/settings",
            json={"meeting": {"intel_retry_failure_webhook_header_name": "Authorization"}},
        )
        assert response.status_code == 400
        payload = response.json()
        assert payload["success"] is False
        assert "both be set" in payload["error"]

    def test_settings_put_rejects_invalid_retry_webhook_header_name(self, tmp_path, monkeypatch, test_client):
        import holdspeak.config as config_module

        monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
        response = test_client.put(
            "/api/settings",
            json={
                "meeting": {
                    "intel_retry_failure_webhook_header_name": "Authorization:",
                    "intel_retry_failure_webhook_header_value": "Bearer test-token",
                }
            },
        )
        assert response.status_code == 400
        payload = response.json()
        assert payload["success"] is False
        assert "header_name" in payload["error"]


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
                        source_timestamp=125.5,
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
        assert payload["source_timestamp"] == pytest.approx(125.5)

        status_response = test_client.patch(
            "/api/all-action-items/a-1",
            json={"status": "done"},
        )
        assert status_response.status_code == 200
        status_item = status_response.json()["action_item"]
        assert status_item["status"] == "done"
        assert status_item["source_timestamp"] == pytest.approx(125.5)

        review_response = test_client.patch(
            "/api/all-action-items/a-1/review",
            json={"review_state": "accepted"},
        )
        assert review_response.status_code == 200
        reviewed_item = review_response.json()["action_item"]
        assert reviewed_item["review_state"] == "accepted"
        assert reviewed_item["reviewed_at"] is not None
        assert reviewed_item["source_timestamp"] == pytest.approx(125.5)

        pending_review_response = test_client.patch(
            "/api/all-action-items/a-1/review",
            json={"review_state": "pending"},
        )
        assert pending_review_response.status_code == 200
        pending_review_item = pending_review_response.json()["action_item"]
        assert pending_review_item["review_state"] == "pending"
        assert pending_review_item["reviewed_at"] is None
        assert pending_review_item["source_timestamp"] == pytest.approx(125.5)

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
        assert edited_item["source_timestamp"] == pytest.approx(125.5)

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

            def get_intel_queue_summary(self):
                return SimpleNamespace(
                    total_jobs=3,
                    queued_jobs=2,
                    running_jobs=0,
                    failed_jobs=1,
                    queued_due_jobs=1,
                    scheduled_retry_jobs=1,
                    next_retry_at=datetime(2025, 1, 11, 10, 45, 0),
                )

            def list_intel_job_attempts(self, meeting_id, *, limit=5):
                _ = meeting_id, limit
                return [
                    SimpleNamespace(
                        attempt=2,
                        outcome="scheduled_retry",
                        error="transient issue",
                        retry_at=datetime(2025, 1, 11, 10, 35, 0),
                        created_at=datetime(2025, 1, 11, 10, 31, 0),
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
        assert jobs_data["jobs"][0]["retry_scheduled"] is False
        assert "retries_remaining" in jobs_data["jobs"][0]
        assert len(jobs_data["jobs"][0]["retry_history"]) == 1

        summary_response = test_client.get("/api/intel/summary")
        assert summary_response.status_code == 200
        summary_data = summary_response.json()
        assert summary_data["total_jobs"] == 3
        assert summary_data["queued_jobs"] == 2
        assert summary_data["failed_jobs"] == 1
        assert summary_data["scheduled_retry_jobs"] == 1
        assert summary_data["next_retry_at"] is not None

        retry_response = test_client.post("/api/intel/retry/m-001")
        assert retry_response.status_code == 200
        assert retry_response.json()["success"] is True

        retry_missing = test_client.post("/api/intel/retry/unknown")
        assert retry_missing.status_code == 404
        assert retry_missing.json()["success"] is False

        process_response = test_client.post("/api/intel/process", json={"max_jobs": 2, "mode": "retry_now"})
        assert process_response.status_code == 200
        process_data = process_response.json()
        assert process_data["success"] is True
        assert process_data["processed"] == 3
        assert process_data["mode"] == "retry_now"

        process_invalid_mode = test_client.post("/api/intel/process", json={"mode": "invalid"})
        assert process_invalid_mode.status_code == 400


@pytest.mark.integration
class TestPluginRunQueueApiEndpoints:
    """Tests for deferred MIR plugin-run queue endpoints."""

    def test_plugin_jobs_list_retry_and_cancel(self, monkeypatch, test_client):
        now = datetime(2026, 3, 29, 20, 0, 0)

        class FakeDb:
            def __init__(self):
                self.jobs = {
                    1: SimpleNamespace(
                        id=1,
                        meeting_id="m-001",
                        window_id="m-001:w0001",
                        plugin_id="incident_timeline",
                        plugin_version="1.0.0",
                        transcript_hash="hash-1",
                        idempotency_key="idem-1",
                        context={},
                        status="queued",
                        requested_at=datetime(2027, 3, 29, 20, 5, 0),
                        updated_at=now,
                        attempts=1,
                        last_error="Transient issue",
                    ),
                    2: SimpleNamespace(
                        id=2,
                        meeting_id="m-001",
                        window_id="m-001:w0002",
                        plugin_id="risk_heatmap",
                        plugin_version="1.0.0",
                        transcript_hash="hash-2",
                        idempotency_key="idem-2",
                        context={},
                        status="failed",
                        requested_at=datetime(2026, 3, 29, 19, 0, 0),
                        updated_at=now,
                        attempts=4,
                        last_error="Timed out repeatedly",
                    ),
                    3: SimpleNamespace(
                        id=3,
                        meeting_id="m-002",
                        window_id="m-002:w0001",
                        plugin_id="stakeholder_update_drafter",
                        plugin_version="1.0.0",
                        transcript_hash="hash-3",
                        idempotency_key="idem-3",
                        context={},
                        status="running",
                        requested_at=datetime(2026, 3, 29, 19, 30, 0),
                        updated_at=now,
                        attempts=2,
                        last_error=None,
                    ),
                }

            def list_plugin_run_jobs(self, *, status="all", meeting_id=None, limit=200):
                output = list(self.jobs.values())
                if status != "all":
                    output = [job for job in output if job.status == status]
                if meeting_id:
                    output = [job for job in output if job.meeting_id == meeting_id]
                output.sort(key=lambda job: (job.requested_at, job.id))
                return output[:limit]

            def get_plugin_run_job(self, job_id):
                return self.jobs.get(int(job_id))

            def retry_plugin_run_job(self, job_id, *, error, retry_at):
                job = self.jobs[int(job_id)]
                job.status = "queued"
                job.last_error = error
                job.requested_at = retry_at
                job.updated_at = retry_at

            def complete_plugin_run_job(self, job_id):
                self.jobs.pop(int(job_id), None)

            def get_plugin_run_job_summary(self):
                return SimpleNamespace(
                    total_jobs=3,
                    queued_jobs=1,
                    running_jobs=1,
                    failed_jobs=1,
                    queued_due_jobs=0,
                    scheduled_retry_jobs=1,
                    next_retry_at=datetime(2027, 3, 29, 20, 5, 0),
                )

        fake_db = FakeDb()
        import holdspeak.db as db_module

        monkeypatch.setattr(db_module, "get_database", lambda: fake_db)

        jobs_response = test_client.get("/api/plugin-jobs?status=all&limit=10")
        assert jobs_response.status_code == 200
        jobs_data = jobs_response.json()
        assert len(jobs_data["jobs"]) == 3
        jobs_by_id = {job["id"]: job for job in jobs_data["jobs"]}
        assert jobs_by_id[1]["status"] == "queued"
        assert jobs_by_id[1]["retry_scheduled"] is True
        assert jobs_by_id[1]["next_retry_at"] is not None
        assert jobs_by_id[2]["status"] == "failed"
        assert jobs_by_id[2]["retry_scheduled"] is False

        queued_response = test_client.get("/api/plugin-jobs?status=queued&limit=10")
        assert queued_response.status_code == 200
        queued_jobs = queued_response.json()["jobs"]
        assert len(queued_jobs) == 1
        assert queued_jobs[0]["id"] == 1

        summary_response = test_client.get("/api/plugin-jobs/summary")
        assert summary_response.status_code == 200
        summary_data = summary_response.json()
        assert summary_data["total_jobs"] == 3
        assert summary_data["queued_jobs"] == 1
        assert summary_data["running_jobs"] == 1
        assert summary_data["failed_jobs"] == 1
        assert summary_data["queued_due_jobs"] == 0
        assert summary_data["scheduled_retry_jobs"] == 1
        assert summary_data["next_retry_at"] is not None

        retry_response = test_client.post("/api/plugin-jobs/2/retry-now")
        assert retry_response.status_code == 200
        retry_data = retry_response.json()
        assert retry_data["success"] is True
        assert retry_data["job"]["id"] == 2
        assert retry_data["job"]["status"] == "queued"

        cancel_response = test_client.post("/api/plugin-jobs/1/cancel")
        assert cancel_response.status_code == 200
        assert cancel_response.json()["success"] is True
        assert fake_db.get_plugin_run_job(1) is None

        retry_running = test_client.post("/api/plugin-jobs/3/retry-now")
        assert retry_running.status_code == 409
        assert retry_running.json()["success"] is False

        cancel_running = test_client.post("/api/plugin-jobs/3/cancel")
        assert cancel_running.status_code == 409
        assert cancel_running.json()["success"] is False

        missing_retry = test_client.post("/api/plugin-jobs/999/retry-now")
        assert missing_retry.status_code == 404
        assert missing_retry.json()["success"] is False

        missing_cancel = test_client.post("/api/plugin-jobs/999/cancel")
        assert missing_cancel.status_code == 404
        assert missing_cancel.json()["success"] is False

    def test_plugin_jobs_process_requires_runtime_callback(self, test_client):
        response = test_client.post("/api/plugin-jobs/process", json={"mode": "retry_now", "max_jobs": 3})
        assert response.status_code == 501
        payload = response.json()
        assert payload["success"] is False
        assert "not supported" in payload["error"].lower()

    def test_plugin_jobs_process_uses_runtime_callback(self, mock_callbacks):
        callback_calls: list[dict[str, object]] = []
        broadcasts: list[tuple[str, object]] = []

        def _on_process_plugin_jobs(*, max_jobs=None, include_scheduled=False):
            callback_calls.append(
                {
                    "max_jobs": max_jobs,
                    "include_scheduled": include_scheduled,
                }
            )
            if not include_scheduled:
                return {
                    "processed": 0,
                    "skipped_active_meeting": True,
                    "deferred_queue_jobs": 0,
                    "deferred_queue_error": None,
                }
            return {
                "processed": 2,
                "skipped_active_meeting": False,
                "deferred_queue_jobs": 1,
                "deferred_queue_error": None,
            }

        server = MeetingWebServer(
            on_bookmark=mock_callbacks["on_bookmark"],
            on_stop=mock_callbacks["on_stop"],
            get_state=mock_callbacks["get_state"],
            on_process_plugin_jobs=_on_process_plugin_jobs,
            host="127.0.0.1",
        )
        server.broadcast = lambda message_type, data: broadcasts.append((message_type, deepcopy(data)))
        client = TestClient(server.app)

        response = client.post("/api/plugin-jobs/process", json={"mode": "retry_now", "max_jobs": 5})
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["processed"] == 2
        assert payload["mode"] == "retry_now"
        assert callback_calls == [{"max_jobs": 5, "include_scheduled": True}]
        assert broadcasts[0][0] == "plugin_jobs_processed"
        assert broadcasts[0][1]["processed"] == 2

        default_mode = client.post("/api/plugin-jobs/process", json={"max_jobs": 2})
        assert default_mode.status_code == 200
        default_payload = default_mode.json()
        assert default_payload["success"] is True
        assert default_payload["mode"] == "respect_backoff"
        assert default_payload["processed"] == 0
        assert default_payload["skipped_active_meeting"] is True
        assert callback_calls[1] == {"max_jobs": 2, "include_scheduled": False}
        assert broadcasts[1][0] == "plugin_jobs_processed"
        assert broadcasts[1][1]["mode"] == "respect_backoff"

        invalid_mode = client.post("/api/plugin-jobs/process", json={"mode": "invalid"})
        assert invalid_mode.status_code == 400
        assert invalid_mode.json()["success"] is False

        invalid_max_jobs = client.post("/api/plugin-jobs/process", json={"max_jobs": 0})
        assert invalid_max_jobs.status_code == 400
        assert invalid_max_jobs.json()["success"] is False


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
