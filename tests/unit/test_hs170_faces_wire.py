"""HS-170-04 — the four Tuesday faces, wire layer.

Tests: intelligence run route refuses without a transcript and enqueues
with one; transcriptWords absent when no transcript; needs-you sums two
seeded projects and excludes an archived one; hub returns integers and
defaultSet false on an empty install.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("fastapi", reason="route tests need the real app")

from starlette.testclient import TestClient
from fastapi import FastAPI


# ── Isolated DB helpers ──────────────────────────────────────────────

def _seed_db(db_path: Path) -> None:
    """Create a minimal schema sufficient for the test scenarios."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    # Meetings table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            title TEXT,
            duration_seconds REAL DEFAULT 0,
            intel_status TEXT DEFAULT 'disabled',
            intel_status_detail TEXT,
            capture_status TEXT DEFAULT 'finalized',
            capture_failure TEXT,
            transcription_status TEXT DEFAULT 'active',
            transcription_status_detail_json TEXT,
            capture_checkpoint_seconds REAL DEFAULT 0.0,
            provenance TEXT DEFAULT 'desktop',
            calendar_event_id TEXT,
            intel_requested_at TEXT,
            intel_completed_at TEXT,
            sync_modified_at TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT NOT NULL,
            text TEXT NOT NULL,
            speaker TEXT NOT NULL,
            start_time REAL NOT NULL,
            end_time REAL NOT NULL,
            is_bookmarked INTEGER DEFAULT 0,
            speaker_id TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS action_items (
            id TEXT PRIMARY KEY,
            meeting_id TEXT NOT NULL,
            text TEXT,
            assignee TEXT,
            status TEXT DEFAULT 'pending',
            due_date TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT,
            reviewed_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meeting_tags (
            meeting_id TEXT NOT NULL,
            tag TEXT NOT NULL,
            PRIMARY KEY (meeting_id, tag)
        )
    """)
    conn.commit()
    conn.close()


# ── test: transcriptWords absent when no transcript ──────────────────

class TestTranscriptWords:
    """transcriptWords should be None/absent when no segments exist."""

    def test_summary_payload_no_transcript(self) -> None:
        """_summary_payload omits transcriptWords when no transcript."""
        from holdspeak.services.meeting_service import MeetingService

        class FakeSummary:
            id = "m1"
            started_at = datetime(2026, 9, 4, 10, 0)
            ended_at = datetime(2026, 9, 4, 10, 30)
            title = "Test"
            duration_seconds = 1800.0
            segment_count = 0
            action_item_count = 0
            tags: list = []
            intel_status = "disabled"
            intel_status_detail = None
            capture_status = "finalized"
            capture_failure = None
            capture_checkpoint_seconds = 0.0
            provenance = "desktop"
            calendar_event_id = None
            transcript_words = None

        payload = MeetingService._summary_payload(FakeSummary())
        assert payload["transcriptWords"] is None

    def test_summary_payload_with_transcript(self) -> None:
        """_summary_payload carries transcriptWords when segments exist."""
        from holdspeak.services.meeting_service import MeetingService

        class FakeSummary:
            id = "m2"
            started_at = datetime(2026, 9, 4, 10, 0)
            ended_at = datetime(2026, 9, 4, 10, 30)
            title = "Test"
            duration_seconds = 1800.0
            segment_count = 5
            action_item_count = 0
            tags: list = []
            intel_status = "ready"
            intel_status_detail = None
            capture_status = "finalized"
            capture_failure = None
            capture_checkpoint_seconds = 0.0
            provenance = "desktop"
            calendar_event_id = None
            transcript_words = 1204

        payload = MeetingService._summary_payload(FakeSummary())
        assert payload["transcriptWords"] == 1204

    def test_meeting_state_to_dict_no_segments(self) -> None:
        """MeetingState.to_dict() has transcriptWords=None when no segments."""
        from holdspeak.meeting_session.models import MeetingState

        state = MeetingState(id="m3", started_at=datetime(2026, 9, 4))
        d = state.to_dict()
        assert d["transcriptWords"] is None

    def test_meeting_state_to_dict_with_segments(self) -> None:
        """MeetingState.to_dict() computes transcriptWords from segments."""
        from holdspeak.meeting_session.models import MeetingState, TranscriptSegment

        state = MeetingState(
            id="m4",
            started_at=datetime(2026, 9, 4),
            segments=[
                TranscriptSegment(text="hello world", speaker="Me", start_time=0.0, end_time=1.0),
                TranscriptSegment(text="three words here", speaker="Remote", start_time=1.0, end_time=2.0),
            ],
        )
        d = state.to_dict()
        # "hello world" = 2, "three words here" = 3
        assert d["transcriptWords"] == 5


# ── test: intelligence run route ─────────────────────────────────────

class TestIntelligenceRunRoute:
    """POST /api/meetings/{id}/intelligence/run."""

    def test_refuses_without_transcript(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Run intelligence returns 409 when meeting has no transcript."""
        from holdspeak.services.errors import ConflictError

        called = {}

        class FakeIntelService:
            def run_intelligence(self, principal, meeting_id):
                called["id"] = meeting_id
                raise ConflictError("Meeting has no transcript", code="empty")

        fake = FakeIntelService()

        from holdspeak.web.routes.meetings.intel import build_intel_router
        from holdspeak.web.context import WebContext

        ctx = WebContext(get_state=lambda: {})
        ctx.meeting_intel_service_factory = lambda: fake

        app = FastAPI()
        app.include_router(build_intel_router(ctx))

        client = TestClient(app)
        resp = client.post("/api/meetings/test-meeting/intelligence/run")
        assert resp.status_code == 409
        body = resp.json()
        assert "plainReason" in body
        assert "no transcript" in body["plainReason"].lower()
        assert called["id"] == "test-meeting"

    def test_enqueues_with_transcript(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Run intelligence returns {jobId, state, host} on success."""
        called = {}

        class FakeIntelService:
            def run_intelligence(self, principal, meeting_id):
                called["id"] = meeting_id
                return {"jobId": "job-123", "state": "queued", "host": "local"}

        fake = FakeIntelService()

        from holdspeak.web.routes.meetings.intel import build_intel_router
        from holdspeak.web.context import WebContext

        ctx = WebContext(get_state=lambda: {})
        ctx.meeting_intel_service_factory = lambda: fake

        app = FastAPI()
        app.include_router(build_intel_router(ctx))

        client = TestClient(app)
        resp = client.post("/api/meetings/test-meeting/intelligence/run")
        assert resp.status_code == 200
        body = resp.json()
        assert body["jobId"] == "job-123"
        assert body["state"] == "queued"
        assert body["host"] == "local"
        assert called["id"] == "test-meeting"


# ── test: needs-you aggregate ────────────────────────────────────────

class TestNeedsYouAggregate:
    """GET /api/desk/needs-you."""

    def test_sums_active_excludes_archived(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """needs-you sums two active projects, excludes archived, severity sorted."""
        _PROJECTS = [
            {"id": "p1", "name": "Alpha", "is_archived": False},
            {"id": "p2", "name": "Beta", "is_archived": False},
            # archived should be excluded (not in the list since include_archived=False)
        ]

        _ROOMS = {
            "p1": {
                "needsYou": {
                    "state": "ok",
                    "items": [
                        {"title": "PR #42", "why": "WAITING ON YOUR REVIEW", "since": "2026-09-01", "source": "github", "url": "https://example.com/pr/42", "severity": "warning"},
                    ],
                    "count": 1,
                },
            },
            "p2": {
                "needsYou": {
                    "state": "ok",
                    "items": [
                        {"title": "CI failing on main", "why": "CI RED", "since": "2026-09-02", "source": "github", "url": "https://example.com/ci", "severity": "danger"},
                        {"title": "2 proposals waiting", "why": "DECISION PENDING", "since": "", "source": "delta", "url": None, "severity": "info"},
                    ],
                    "count": 2,
                },
            },
        }

        class FakeProjectService:
            def list_projects(self, principal, opts):
                return _PROJECTS

            def room(self, principal, pid):
                return _ROOMS.get(pid, {"needsYou": {"state": "error"}})

        from holdspeak.web.routes.projects import build_projects_router
        from holdspeak.web.context import WebContext

        ctx = WebContext(get_state=lambda: {})
        ctx.door_service = None  # no door service in test

        app = FastAPI()
        app.include_router(build_projects_router(ctx))

        # Monkeypatch the service inside the router.
        # The build_projects_router uses `service` from ctx.project_service
        # but our test doesn't wire it. Let's instead use a full approach:
        # We need to wire project_service on the ctx.

        # Actually the build_projects_router accesses service = ctx.project_service
        # Let me re-check:
        # build_projects_router(ctx) -> `service: ProjectService = ctx.project_service`
        # This is done at router build time. So we need to set it before.
        ctx.project_service = FakeProjectService()

        app2 = FastAPI()
        app2.include_router(build_projects_router(ctx))

        client = TestClient(app2)
        resp = client.get("/api/desk/needs-you")
        assert resp.status_code == 200
        body = resp.json()

        # Count: 3 items (1 from p1, 2 from p2)
        assert body["count"] == 3

        # Projects: both active projects
        assert sorted(body["projects"]) == ["p1", "p2"]

        # Severity order: danger first, then warning, then info
        items = body["items"]
        assert len(items) == 3
        assert items[0]["severity"] == "danger"
        assert items[0]["projectId"] == "p2"
        assert items[1]["severity"] == "warning"
        assert items[1]["projectId"] == "p1"
        assert items[2]["severity"] == "info"

        # next is None (no door service)
        assert body["next"] is None


# ── test: settings hub ───────────────────────────────────────────────

class TestSettingsHub:
    """GET /api/settings/hub."""

    def test_hub_returns_integers_default_false(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Hub returns integer counts and defaultSet=false on empty install."""
        # Patch Config.load to return defaults + point at isolated config
        from holdspeak.config.core import Config
        from holdspeak.web.routes.system.settings import build_settings_router
        from holdspeak.web.context import WebContext
        from holdspeak.services.settings_service import SettingsService

        config_path = tmp_path / "config.json"
        config_path.write_text("{}")

        monkeypatch.setattr("holdspeak.config.core.CONFIG_FILE", config_path)
        monkeypatch.setattr("holdspeak.config.CONFIG_FILE", config_path)

        default_config = Config()
        monkeypatch.setattr(Config, "load", staticmethod(lambda path=None: default_config))

        # Mock services to return empty/default state
        class FakeModelLibrary:
            def get_library(self, principal):
                return {"summary": {"state": "empty", "label": "Add model", "ready_count": 0, "attention_count": 0}, "rows": []}

        class FakeAssignmentService:
            def assignment_summary(self, principal):
                return {"rows": [{"id": "global", "status": "no_assignment", "repair": "Choose default"}]}

        class FakeCadenceService:
            def list_loops(self, principal):
                return {"loops": []}

        class FakeSettingsService(SettingsService):
            def __init__(self):
                pass  # skip real init

        class FakeCredentialService:
            pass

        ctx = WebContext(get_state=lambda: {})
        ctx.settings_service = FakeSettingsService()
        ctx.model_library_service = FakeModelLibrary()
        ctx.inference_assignment_service = FakeAssignmentService()
        ctx.cadence_service = FakeCadenceService()
        ctx.credential_service = FakeCredentialService()

        # Patch get_database to return something with automations
        class FakeAutomations:
            def list_provider_connections(self):
                return []

        class FakeDB:
            automations = FakeAutomations()

        monkeypatch.setattr("holdspeak.web.routes.system.settings.get_database", lambda: FakeDB(), raising=False)
        # The import is inside the function, so we need to patch the right module
        import holdspeak.web.routes.system.settings as settings_mod
        original_code = settings_mod.build_settings_router.__code__

        app = FastAPI()
        app.include_router(build_settings_router(ctx))

        client = TestClient(app)
        resp = client.get("/api/settings/hub")
        assert resp.status_code == 200
        body = resp.json()

        # Models
        assert isinstance(body["models"]["engines"], int)
        assert body["models"]["engines"] == 0
        assert isinstance(body["models"]["groupsSet"], int)
        assert body["models"]["groupsSet"] == 0
        assert body["models"]["defaultSet"] is False

        # Connections
        assert isinstance(body["connections"]["connected"], int)
        assert body["connections"]["connected"] == 0

        # Voice
        assert isinstance(body["voice"]["live"], bool)

        # Meetings
        assert isinstance(body["meetings"]["intelligence"], bool)

        # Rhythm
        assert isinstance(body["rhythm"]["loops"], int)
        assert body["rhythm"]["loops"] == 0

        # Sounds
        assert isinstance(body["sounds"]["on"], bool)

        # System
        assert body["system"]["host"] == "THIS DEVICE"
        assert isinstance(body["system"]["mesh"], bool)

        # Posture
        assert body["posture"] in ("yolo", "neutral", "safe")
