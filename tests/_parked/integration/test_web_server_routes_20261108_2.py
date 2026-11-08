"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/integration/test_web_server.py``: test_pin_marks_session_and_exempts_from_clear_stale, test_missing_fields_return_400, TestApiStopEndpoint, test_meeting_plugin_runs_endpoint, test_legacy_meeting_without_mir_history_rows_remains_loadable, TestSpeakerApiEndpoints, TestGlobalActionItemsApiEndpoints. Not collected.
"""
from __future__ import annotations
"""Integration tests for HoldSpeak web server."""


from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
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
    WebRuntimeCallbacks,
    MeetingWebServer,
    WebSocketManager,
    BroadcastMessage,
    _format_duration,
    _find_free_port,
    _parse_iso_datetime,
)
from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
from tests.unit.test_hs201_route_contract import assign_summary, summary_profile


# ============================================================
# Utility Function Tests
# ============================================================


# ============================================================
# BroadcastMessage Tests
# ============================================================


# ============================================================
# WebSocketManager Tests
# ============================================================


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
def isolated_db(tmp_path):
    """HS-132-12: the REAL database the composed app consults.

    `MeetingWebServer._create_app` composes every service against
    `get_database()` at construction time (`web_server.py:631-648`), so a
    `monkeypatch.setattr(holdspeak.db, "get_database", ...)` executed inside a
    test body arrives far too late — the live routes keep answering from the
    handle captured at composition. Route tests below therefore SEED this
    database instead of faking one; the seam is the `get_database` singleton,
    swapped to a per-test file before the server is built.
    """
    from holdspeak.db import get_database, reset_database

    reset_database()
    db = get_database(tmp_path / "holdspeak-web-server-test.db")
    yield db
    reset_database()


@pytest.fixture
def web_server(mock_callbacks, isolated_db):
    """Create MeetingWebServer instance composed against `isolated_db`."""
    _ = isolated_db  # must be resolved BEFORE the app composes its services
    server = MeetingWebServer(
                 WebRuntimeCallbacks(
                     on_bookmark=mock_callbacks["on_bookmark"],
                     on_stop=mock_callbacks["on_stop"],
                     get_state=mock_callbacks["get_state"],
                 ),
                 host="127.0.0.1",
             )
    return server


@pytest.mark.integration
class TestCompanionControlEndpoints:
    """HS-24-02: select / dismiss / pin / clear-stale companion controls."""

    @pytest.fixture
    def companion(self, tmp_path, monkeypatch, test_client):
        import json
        from datetime import timezone

        import holdspeak.agent_context as agent_context_module

        state = tmp_path / "agent_sessions.json"
        monkeypatch.setattr(agent_context_module, "AGENT_CONTEXT_FILE", state)
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        def ingest(session_id, text, *, agent="codex", now=None):
            transcript = tmp_path / f"{agent}-{session_id}.jsonl"
            transcript.write_text(
                json.dumps({"role": "assistant", "content": text}) + "\n",
                encoding="utf-8",
            )
            agent_context_module.ingest_agent_hook_event(
                agent=agent,
                payload={
                    "session_id": session_id,
                    "hook_event_name": "Stop",
                    "cwd": str(repo),
                    "transcript_path": str(transcript),
                },
                state_path=state,
                now=now,
                capture_messages=True,
            )

        return SimpleNamespace(
            client=test_client,
            state=state,
            ingest=ingest,
            module=agent_context_module,
            old=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

    def _status_items(self, client):
        payload = client.get("/api/coders/status").json()
        return payload["agent"]["sessions"]["items"]

    def test_pin_marks_session_and_exempts_from_clear_stale(self, companion):
        companion.ingest("stale", "Stale?")
        companion.ingest("kept", "Kept?")

        pin = companion.client.post(
            "/api/coders/pin",
            json={"agent": "codex", "session_id": "kept", "pinned": True},
        )
        assert pin.status_code == 200
        assert pin.json()["session"]["pinned"] is True

        kept = next(
            item
            for item in self._status_items(companion.client)
            if item["session"]["session_id"] == "kept"
        )
        assert kept["pinned"] is True
        assert kept["stale"] is False

        # Force everything stale, then clear: only the unpinned session goes.
        for session_id in ("stale", "kept"):
            companion.ingest(session_id, "again?", now=companion.old)
        companion.client.post(
            "/api/coders/pin",
            json={"agent": "codex", "session_id": "kept", "pinned": True},
        )
        clear = companion.client.post("/api/coders/clear-stale", json={})
        assert clear.status_code == 200
        assert clear.json() == {"success": True, "cleared": 1, "max_age_seconds": 120}

        remaining = {
            item.session_id
            for item in companion.module.list_recent_awaiting_agent_sessions(
                state_path=companion.state, max_age_seconds=10**9
            )
        }
        assert remaining == {"kept"}

    def test_missing_fields_return_400(self, companion):
        assert companion.client.post("/api/coders/select", json={}).status_code == 400
        assert (
            companion.client.post(
                "/api/coders/pin", json={"agent": "codex"}
            ).status_code
            == 400
        )
        assert (
            companion.client.post(
                "/api/coders/clear-stale", json={"max_age_seconds": "soon"}
            ).status_code
            == 400
        )

    # ── HSM-17-02: the live set at GET /api/coders/sessions ─────────────

    def _live_sessions(self, client, **params):
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = "/api/coders/sessions" + (f"?{query}" if query else "")
        response = client.get(url)
        assert response.status_code == 200
        return response.json()

@pytest.mark.integration
class TestApiStopEndpoint:
    """Tests for POST /api/stop endpoint."""

    def test_calls_stop_callback(self, test_client, mock_callbacks):
        """Should call on_stop callback."""
        response = test_client.post("/api/stop")
        assert response.status_code == 200
        assert response.json() == {"success": True, "status": "stopped"}

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
class TestMirHistoryApiEndpoints:
    plugins = property(lambda self: self)
    """Tests for persisted MIR timeline and plugin-run meeting APIs."""

    def test_meeting_plugin_runs_endpoint(self, isolated_db, test_client):
        now = datetime(2026, 3, 29, 18, 0, 0)
        isolated_db.meetings.save_meeting(MeetingState(id="m-001", started_at=now))
        # Recorded oldest-first: `list_plugin_runs` answers newest-first
        # (ORDER BY created_at DESC, id DESC).
        isolated_db.plugins.record_plugin_run(
            meeting_id="m-001",
            window_id="m-001:w0001",
            plugin_id="requirements_extractor",
            plugin_version="1.0.0",
            status="success",
            idempotency_key="idem-1",
            duration_ms=44.2,
            output={"requirements": 4},
        )
        isolated_db.plugins.record_plugin_run(
            meeting_id="m-001",
            window_id="m-001:w0002",
            plugin_id="incident_timeline",
            plugin_version="preview",
            status="planned",
            idempotency_key="idem-2",
            duration_ms=0.0,
            output={"source": "route_preview"},
        )

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

    def test_legacy_meeting_without_mir_history_rows_remains_loadable(self, isolated_db, test_client):
        # A pre-MIR meeting: the row exists, none of the history tables do.
        isolated_db.meetings.save_meeting(
            MeetingState(id="m-legacy", started_at=datetime(2026, 3, 29, 18, 0, 0))
        )

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

@pytest.mark.integration
class TestHistoryUiSmoke:
    """Smoke checks for the browser-facing history/settings UI."""




@pytest.mark.integration
class TestCompanionUiSmoke:
    """Smoke checks for the /companion surface.

    Since HS-69-12, /companion is the **Agent Desk** — a live desk of the real
    agents + the companion link (React over /api/agents +
    /api/coders/status), not the old static docs portal. This smoke check
    asserts the desk's stable structure + the preserved connection/credential
    facts. HS-111-04: the surface is the crew board — blocked-first ledger
    rows, and the "How it connects" facts moved behind the gear door as
    tokens (probe / token / relay / autonomous send), never prose.
    """



@pytest.mark.integration
class TestCadenceUiSmoke:
    """CAD-2-04 — the /cadence coach page serves and drives /api/cadence/*."""




@pytest.mark.integration
class TestSpeakerApiEndpoints:
    """Tests for speaker management endpoints."""

    def test_speaker_endpoints(self, isolated_db, test_client):
        import numpy as np

        from holdspeak.speaker_intel import SpeakerEmbedding

        def _embedding(seed: int):
            return np.full(256, float(seed), dtype=np.float32)

        isolated_db.meetings.save_speaker(
            SpeakerEmbedding(id="spk-1", name="Alice", embedding=_embedding(1), sample_count=4, avatar="👩")
        )
        isolated_db.meetings.save_speaker(
            SpeakerEmbedding(id="spk-2", name="Bob", embedding=_embedding(2), sample_count=2, avatar="🧑")
        )
        # spk-1 speaks in TWO meetings so `meeting_count` is a real aggregate;
        # m-001 is the more recent, so it leads the grouped detail payload.
        isolated_db.meetings.save_meeting(
            MeetingState(
                id="m-000",
                started_at=datetime(2025, 1, 10, 9, 0, 0),
                ended_at=datetime(2025, 1, 10, 9, 20, 0),
                title="Kickoff",
                segments=[
                    TranscriptSegment(
                        text="Kickoff notes", speaker="Alice", start_time=0.0, end_time=10.0, speaker_id="spk-1"
                    )
                ],
            )
        )
        isolated_db.meetings.save_meeting(
            MeetingState(
                id="m-001",
                started_at=datetime(2025, 1, 11, 10, 30, 0),
                ended_at=datetime(2025, 1, 11, 10, 50, 0),
                title="Weekly sync",
                segments=[
                    TranscriptSegment(
                        text="Action item follow-up",
                        speaker="Alice",
                        start_time=42.0,
                        end_time=48.0,
                        speaker_id="spk-1",
                    ),
                    TranscriptSegment(
                        text="Agreed", speaker="Bob", start_time=48.0, end_time=52.0, speaker_id="spk-2"
                    ),
                ],
            )
        )

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

    def test_action_item_endpoints_include_review_and_edit(self, isolated_db, test_client):
        now = datetime(2025, 1, 12, 9, 0, 0)
        isolated_db.meetings.save_meeting(
            MeetingState(
                id="m-001",
                started_at=now,
                ended_at=datetime(2025, 1, 12, 9, 30, 0),
                title="Weekly sync",
                intel=IntelSnapshot(
                    timestamp=10.0,
                    topics=[],
                    action_items=[
                        {
                            "id": "a-1",
                            "task": "Initial task",
                            "owner": "Me",
                            "due": None,
                            "status": "pending",
                            "review_state": "pending",
                            "source_timestamp": 125.5,
                        }
                    ],
                    summary="Weekly sync",
                ),
            )
        )

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
            meetings = property(lambda self: self)
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


# ============================================================
# MeetingWebServer Property Tests
# ============================================================


# ============================================================
# MeetingWebServer Lifecycle Tests
# ============================================================


