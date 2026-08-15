"""HS-132-01 — stopping a meeting never stops the hub; conflicts answer honestly."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient  # noqa: E402

pytestmark = [pytest.mark.integration, pytest.mark.requires_meeting]

from holdspeak.principals import UNAUTHENTICATED  # noqa: E402
from holdspeak.services.errors import ConflictError  # noqa: E402
from holdspeak.services.meeting_service import MeetingService  # noqa: E402
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks  # noqa: E402


def test_stop_without_a_live_meeting_refuses_by_name_and_spares_the_runtime():
    """The runtime-fallback stop (which sets `runtime_stop_event`) is never reached."""
    runtime_fallback_stop = MagicMock(return_value={"status": "stopping_runtime"})

    def no_active_meeting() -> dict[str, object]:
        raise RuntimeError("No active meeting")

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=runtime_fallback_stop,
            on_meeting_stop=no_active_meeting,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    client = TestClient(server.app)

    for path in ("/api/meeting/stop", "/api/stop"):
        response = client.post(path)
        payload = response.json()
        assert payload["success"] is False, path
        assert "No active meeting" in payload["error"], path
    runtime_fallback_stop.assert_not_called()


class _StubConflicts:
    """The narrow meeting-repository surface `resolve_sync_conflict` reads."""

    def __init__(self, conflict: dict[str, Any] | None, *, outcome: Any = "resolved") -> None:
        self._conflict = conflict
        self._outcome = outcome

    def get_meeting(self, meeting_id: str) -> Any:
        return None

    def get_sync_conflict(self, meeting_id: str, conflict_id: str) -> dict[str, Any] | None:
        return self._conflict

    def resolve_sync_conflict(self, *_a: Any, **_k: Any) -> Any:
        if isinstance(self._outcome, Exception):
            raise self._outcome
        return self._outcome

    def list_sync_conflicts(self, meeting_id: str) -> list[dict[str, Any]]:
        return []


class _StubDb:
    def __init__(self, meetings: _StubConflicts) -> None:
        self.meetings = meetings


def _resolve(conflict: dict[str, Any] | None, *, resolution: str, outcome: Any = "resolved") -> Any:
    service = MeetingService(_StubDb(_StubConflicts(conflict, outcome=outcome)))
    return service.resolve_sync_conflict(
        UNAUTHENTICATED, "meeting-1", "conflict-1", {"resolution": resolution}
    )


def test_resolving_an_already_resolved_conflict_refuses():
    with pytest.raises(ConflictError) as exc:
        _resolve({"resolved_at": "2026-08-15T09:00:00", "incoming": {}}, resolution="keep_current")
    assert exc.value.code == "already_resolved"
    assert "already resolved" in exc.value.detail


def test_unreadable_incoming_version_refuses_without_losing_current_work():
    with pytest.raises(ConflictError) as exc:
        _resolve({"resolved_at": None, "incoming": "not-a-mapping"}, resolution="use_incoming")
    assert exc.value.code == "unreadable_incoming"
    assert "current work retained" in exc.value.detail


def test_unparsable_incoming_version_refuses_with_the_parse_reason():
    conflict = {
        "resolved_at": None,
        "incoming": {"deleted": False, "segments": [{"text": "x", "start_time": "not-a-number"}]},
    }
    with pytest.raises(ConflictError) as exc:
        _resolve(conflict, resolution="use_incoming")
    assert exc.value.code == "unreadable_incoming"
    assert "current work retained" in exc.value.detail


def test_a_failed_resolution_keeps_both_versions():
    with pytest.raises(ConflictError) as exc:
        _resolve(
            {"resolved_at": None, "incoming": {}},
            resolution="keep_current",
            outcome=ValueError("store refused"),
        )
    assert exc.value.code == "resolution_failed"
    assert "both versions remain" in exc.value.detail


def test_a_conflict_resolved_underneath_us_refuses():
    with pytest.raises(ConflictError) as exc:
        _resolve(
            {"resolved_at": None, "incoming": {}},
            resolution="keep_current",
            outcome="already_resolved",
        )
    assert exc.value.code == "already_resolved"
    assert "already resolved" in exc.value.detail
