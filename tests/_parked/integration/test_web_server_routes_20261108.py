"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/integration/test_web_server.py``: test_plugin_jobs_list_retry_and_cancel. Not collected.
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


@pytest.mark.integration
class TestFormatDuration:
    """Tests for _format_duration helper function."""

@pytest.mark.integration
class TestFindFreePort:
    """Tests for _find_free_port helper function."""

@pytest.mark.integration
class TestParseIsoDatetime:
    """Tests for _parse_iso_datetime helper function."""

# ============================================================
# BroadcastMessage Tests
# ============================================================


@pytest.mark.integration
class TestBroadcastMessage:
    """Tests for BroadcastMessage dataclass."""

# ============================================================
# WebSocketManager Tests
# ============================================================


@pytest.mark.integration
class TestWebSocketManager:
    """Tests for WebSocketManager."""

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
class TestDashboardEndpoint:
    """Tests for GET /live dashboard endpoint (moved off `/` in HS-70-02)."""

    def _bundled_runtime_js(self, test_client) -> str:
        # W2-LIVE (2026-10-27): the Live window is LiveCore plus its
        # transcript document; its old gear wing (routing, try a phrase,
        # background work, devices) moved to Settings ▸ Meetings as
        # LiveMeetingTools. W2-LIVE-2: the ready sheet is LiveReady. The source
        # of all four is the runtime face.
        del test_client
        cores = Path(__file__).resolve().parents[2] / "web/src/pages/cores"
        return "\n".join(
            (cores / name).read_text()
            for name in ("LiveCore.tsx", "LiveReady.tsx", "LiveTranscript.tsx", "LiveMeetingTools.tsx")
        )

@pytest.mark.integration
class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

@pytest.mark.integration
class TestDeviceHealthEndpoint:
    """HS-17-01/03: browser-readable device-health snapshot."""

@pytest.mark.integration
class TestCompanionStatusEndpoint:
    """HS-20-03: companion setup/debug snapshot."""

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

    # ── HSM-17-02: the live set at GET /api/coders/sessions ─────────────

    def _live_sessions(self, client, **params):
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = "/api/coders/sessions" + (f"?{query}" if query else "")
        response = client.get(url)
        assert response.status_code == 200
        return response.json()

@pytest.mark.integration
class TestApiStateEndpoint:
    """Tests for GET /api/state endpoint."""

@pytest.mark.integration
class TestApiBookmarkEndpoint:
    """Tests for POST /api/bookmark endpoint."""

@pytest.mark.integration
class TestApiStopEndpoint:
    """Tests for POST /api/stop endpoint."""

@pytest.mark.integration
class TestRuntimeControlEndpoints:
    """Tests for runtime-level meeting control routes."""

@pytest.mark.integration
class TestIntentRoutingControlEndpoints:
    """Tests for MIR control-plane endpoints."""

@pytest.mark.integration
class TestMirHistoryApiEndpoints:
    plugins = property(lambda self: self)
    """Tests for persisted MIR timeline and plugin-run meeting APIs."""

@pytest.mark.integration
class TestMeetingMetadataEndpoints:
    """Tests for runtime-level meeting metadata updates."""

@pytest.mark.integration
class TestDashboardLifecycleStateTransitions:
    """Integration coverage for dashboard lifecycle controls and WS updates."""

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
class TestSettingsApiEndpoints:
    """Tests for web settings API."""

@pytest.mark.integration
class TestSpeakerApiEndpoints:
    """Tests for speaker management endpoints."""

@pytest.mark.integration
class TestGlobalActionItemsApiEndpoints:
    """Tests for global action-item list, status, review, and edit endpoints."""

@pytest.mark.integration
class TestIntelQueueApiEndpoints:
    intel = property(lambda self: self)
    """Tests for deferred intel queue endpoints."""

@pytest.mark.integration
class TestPluginRunQueueApiEndpoints:
    plugins = property(lambda self: self)
    """Tests for deferred MIR plugin-run queue endpoints."""

    def test_plugin_jobs_list_retry_and_cancel(self, monkeypatch, test_client):
        now = datetime(2026, 3, 29, 20, 0, 0)

        class FakeDb:
            plugins = property(lambda self: self)
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
        import holdspeak.web.routes.activity.plugin_jobs as pj_route
        monkeypatch.setattr(pj_route, "get_database", lambda: fake_db)

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
        assert fake_db.plugins.get_plugin_run_job(1) is None

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

# ============================================================
# MeetingWebServer Property Tests
# ============================================================


@pytest.mark.integration
class TestMeetingWebServerProperties:
    """Tests for MeetingWebServer properties."""

# ============================================================
# MeetingWebServer Lifecycle Tests
# ============================================================


@pytest.mark.integration
class TestMeetingWebServerLifecycle:
    """Tests for server start/stop lifecycle."""

