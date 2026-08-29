"""HS-147-01: Event-linked arm — service, route, MCP, door, and conductor tests.

Tests the arm-from-event computation (D2), the three named refusals,
the L1 uniqueness invariant, the remainder rule, the 60 s lead, the
door armed_schedule_id projection, and the full lifecycle through the
real conductor with fakes only at the engine-factory level.
"""
from __future__ import annotations

import json
import math
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional
from unittest.mock import MagicMock

import pytest

from holdspeak.calendar_ingest import CalendarEventCandidate
from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, NotFound, ValidationError
from holdspeak.services.scheduled_recording_service import ScheduledRecordingService

OWNER = Principal(PrincipalKind.OWNER, "test-owner")
# A fixed reference "now" for deterministic service tests (clock-injected).
FIXED_NOW = datetime(2026, 8, 28, 14, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "test.db")


def _svc(db: Database) -> ScheduledRecordingService:
    """Service with a fixed clock for deterministic tests."""
    return ScheduledRecordingService(db, clock=lambda: FIXED_NOW)


def _insert_event(
    db: Database,
    event_id: str,
    *,
    title: str = "Team Standup",
    starts_at: str | None = None,
    ends_at: str | None = None,
    uid: str = "uid-1",
    source_id: str = "src-1",
    source_label: str = "Work",
) -> None:
    """Insert a calendar event into the projection table."""
    if starts_at is None:
        starts_at = (FIXED_NOW + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    if ends_at is None:
        ends_at = (FIXED_NOW + timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    db.calendar_events.replace_projection(
        "rev-test",
        [
            CalendarEventCandidate(
                id=event_id,
                uid=uid,
                title=title,
                starts_at=starts_at,
                ends_at=ends_at,
                location=None,
                meeting_url=None,
            ),
        ],
        seen_at=FIXED_NOW.timestamp(),
        source_id=source_id,
        source_label=source_label,
    )


def _insert_event_relative(
    db: Database,
    event_id: str,
    *,
    title: str = "Team Standup",
    starts_delta: timedelta = timedelta(hours=1),
    ends_delta: timedelta = timedelta(hours=2),
    uid: str = "uid-1",
    source_id: str = "src-1",
    source_label: str = "Work",
) -> None:
    """Insert a calendar event relative to real wall-clock time.

    Used for route/MCP tests where the service uses real datetime.now().
    """
    now = datetime.now(tz=timezone.utc)
    starts_at = (now + starts_delta).isoformat().replace("+00:00", "Z")
    ends_at = (now + ends_delta).isoformat().replace("+00:00", "Z")
    db.calendar_events.replace_projection(
        "rev-test",
        [
            CalendarEventCandidate(
                id=event_id,
                uid=uid,
                title=title,
                starts_at=starts_at,
                ends_at=ends_at,
                location=None,
                meeting_url=None,
            ),
        ],
        seen_at=now.timestamp(),
        source_id=source_id,
        source_label=source_label,
    )


# ────────────────────────────────────────────────────────────────
# AC-1: one tap creates a correct event-linked schedule
# ────────────────────────────────────────────────────────────────


class TestArmFromEventComputation:
    """Service computes title/one_shot/enabled/tz/duration/next_fire_at from the event."""

    def test_future_event_computes_correct_fields(self, db: Database) -> None:
        starts = FIXED_NOW + timedelta(hours=1)
        ends = FIXED_NOW + timedelta(hours=1, minutes=45)
        _insert_event(
            db, "ce_future",
            title="Design Review",
            starts_at=starts.isoformat().replace("+00:00", "Z"),
            ends_at=ends.isoformat().replace("+00:00", "Z"),
        )
        result = _svc(db).create_schedule(OWNER, calendar_event_id="ce_future")

        assert result["title"] == "Design Review"
        assert result["one_shot"] is True
        assert result["enabled"] is True
        assert result["duration_minutes"] == 45  # ceil(45min)
        assert result["calendar_event_id"] == "ce_future"
        assert result["calendar_uid"] == "uid-1"
        assert result["calendar_source_id"] == "src-1"
        # next_fire_at should be starts_at - 60s
        nf = datetime.fromisoformat(result["next_fire_at"].replace("Z", "+00:00"))
        expected_nf = starts - timedelta(seconds=60)
        assert abs((nf - expected_nf).total_seconds()) < 2

    def test_duration_480_cap(self, db: Database) -> None:
        """An event > 480 minutes is capped at 480."""
        starts = FIXED_NOW + timedelta(hours=1)
        ends = starts + timedelta(hours=10)  # 600 minutes
        _insert_event(
            db, "ce_long",
            starts_at=starts.isoformat().replace("+00:00", "Z"),
            ends_at=ends.isoformat().replace("+00:00", "Z"),
        )
        result = _svc(db).create_schedule(OWNER, calendar_event_id="ce_long")
        assert result["duration_minutes"] == 480

    def test_short_event_duration_ceil(self, db: Database) -> None:
        """A 25-second event gets ceil'd to 1 minute."""
        starts = FIXED_NOW + timedelta(hours=1)
        ends = starts + timedelta(seconds=25)
        _insert_event(
            db, "ce_short",
            starts_at=starts.isoformat().replace("+00:00", "Z"),
            ends_at=ends.isoformat().replace("+00:00", "Z"),
        )
        result = _svc(db).create_schedule(OWNER, calendar_event_id="ce_short")
        assert result["duration_minutes"] == 1

    def test_link_fields_in_list_and_get(self, db: Database) -> None:
        """List and get responses expose the calendar link fields."""
        _insert_event(db, "ce_list")
        svc = _svc(db)
        created = svc.create_schedule(OWNER, calendar_event_id="ce_list")
        schedule_id = created["id"]

        # get
        got = svc.get_schedule(OWNER, schedule_id)
        assert got["calendar_event_id"] == "ce_list"
        assert got["calendar_uid"] == "uid-1"
        assert got["calendar_source_id"] == "src-1"

        # list
        listed = svc.list_schedules(OWNER)
        match = [s for s in listed if s["id"] == schedule_id]
        assert len(match) == 1
        assert match[0]["calendar_event_id"] == "ce_list"

    def test_manual_schedule_still_works(self, db: Database) -> None:
        """The manual (non-event) path is unbroken."""
        result = _svc(db).create_schedule(
            OWNER, cron_expr="0 9 * * 1", title="Manual", duration_minutes=30,
        )
        assert result["title"] == "Manual"
        assert result["calendar_event_id"] == ""


# ────────────────────────────────────────────────────────────────
# AC-2: remainder rule for in-progress events
# ────────────────────────────────────────────────────────────────


class TestRemainderRule:
    """An in-progress event arms for the remainder; fires now."""

    def test_in_progress_fires_now_with_remainder_duration(self, db: Database) -> None:
        starts = FIXED_NOW - timedelta(minutes=10)
        ends = FIXED_NOW + timedelta(minutes=50)  # 50 min remaining
        _insert_event(
            db, "ce_inprogress",
            starts_at=starts.isoformat().replace("+00:00", "Z"),
            ends_at=ends.isoformat().replace("+00:00", "Z"),
        )
        result = _svc(db).create_schedule(OWNER, calendar_event_id="ce_inprogress")
        assert result["duration_minutes"] == 50
        # next_fire_at should be approximately FIXED_NOW (fire-now semantics)
        nf = datetime.fromisoformat(result["next_fire_at"].replace("Z", "+00:00"))
        assert abs((nf - FIXED_NOW).total_seconds()) < 5


# ────────────────────────────────────────────────────────────────
# AC-3: named refusals
# ────────────────────────────────────────────────────────────────


class TestNamedRefusals:
    """The three named refusals: not found, already ended, already armed."""

    def test_calendar_event_not_found(self, db: Database) -> None:
        with pytest.raises(NotFound) as exc_info:
            _svc(db).create_schedule(OWNER, calendar_event_id="ce_nonexistent")
        assert exc_info.value.code == "not_found"

    def test_event_already_ended(self, db: Database) -> None:
        starts = FIXED_NOW - timedelta(hours=2)
        ends = FIXED_NOW - timedelta(hours=1)
        _insert_event(
            db, "ce_ended",
            starts_at=starts.isoformat().replace("+00:00", "Z"),
            ends_at=ends.isoformat().replace("+00:00", "Z"),
        )
        with pytest.raises(ValidationError) as exc_info:
            _svc(db).create_schedule(OWNER, calendar_event_id="ce_ended")
        assert exc_info.value.code == "event_already_ended"

    def test_event_already_armed(self, db: Database) -> None:
        _insert_event(db, "ce_armed")
        svc = _svc(db)
        # First arm succeeds
        svc.create_schedule(OWNER, calendar_event_id="ce_armed")
        # Second arm is refused
        with pytest.raises(ConflictError) as exc_info:
            svc.create_schedule(OWNER, calendar_event_id="ce_armed")
        assert exc_info.value.code == "event_already_armed"

    def test_re_arm_after_terminal_outcome(self, db: Database) -> None:
        """After the first schedule reaches a terminal outcome (disabled),
        the event is armable again (L1 frees on disable)."""
        _insert_event(db, "ce_rearm")
        svc = _svc(db)
        first = svc.create_schedule(OWNER, calendar_event_id="ce_rearm")
        # Simulate terminal: one-shot disables
        db.scheduled_recordings.update(first["id"], enabled=False)
        # Re-arm succeeds
        second = svc.create_schedule(OWNER, calendar_event_id="ce_rearm")
        assert second["id"] != first["id"]
        assert second["calendar_event_id"] == "ce_rearm"


class TestL1UniqueIndex:
    """The partial unique index enforces L1 at the DB level as a backstop."""

    def test_db_unique_index_prevents_double_arm(self, db: Database) -> None:
        """Direct DB insert of two enabled records with the same calendar_event_id
        should raise IntegrityError."""
        import sqlite3
        db.scheduled_recordings.create(
            title="First",
            cron_expr="0 9 * * *",
            enabled=True,
            calendar_event_id="ce_double",
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.scheduled_recordings.create(
                title="Second",
                cron_expr="0 9 * * *",
                enabled=True,
                calendar_event_id="ce_double",
            )

    def test_db_allows_same_event_when_first_disabled(self, db: Database) -> None:
        """Two records with the same calendar_event_id are fine if the first is disabled."""
        first = db.scheduled_recordings.create(
            title="First",
            cron_expr="0 9 * * *",
            enabled=True,
            calendar_event_id="ce_freed",
        )
        db.scheduled_recordings.update(first.id, enabled=False)
        second = db.scheduled_recordings.create(
            title="Second",
            cron_expr="0 9 * * *",
            enabled=True,
            calendar_event_id="ce_freed",
        )
        assert second.calendar_event_id == "ce_freed"
        assert second.enabled is True

    def test_empty_calendar_event_id_not_unique(self, db: Database) -> None:
        """Empty calendar_event_id (manual schedules) never collide via the index."""
        db.scheduled_recordings.create(
            title="Manual 1", cron_expr="0 9 * * *", enabled=True,
        )
        db.scheduled_recordings.create(
            title="Manual 2", cron_expr="0 10 * * *", enabled=True,
        )
        # Both enabled with empty calendar_event_id: no error


# ────────────────────────────────────────────────────────────────
# AC-4: door upcoming items carry armed_schedule_id
# ────────────────────────────────────────────────────────────────


class TestDoorArmedProjection:
    """DoorService._calendar_event_item projects armed_schedule_id."""

    def test_unarmed_event_has_no_armed_schedule_id(self, db: Database) -> None:
        from holdspeak.services.door_service import DoorService
        from holdspeak.services.follow_through_service import FollowThroughService
        from holdspeak.services.refinement_thought_service import (
            INBOX_DIRECTORY_ID,
            RefinementThoughtService,
        )

        db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
        starts = FIXED_NOW + timedelta(hours=1)
        _insert_event(
            db, "ce_unarmed",
            starts_at=starts.isoformat().replace("+00:00", "Z"),
            ends_at=(starts + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
        )
        door = DoorService(
            FollowThroughService(db),
            RefinementThoughtService(db),
            db.scheduled_recordings,
            db.calendar_events,
            clock=lambda: FIXED_NOW,
        )
        upcoming = door.get(OWNER)["upcoming"]
        event_item = next(i for i in upcoming if i["id"] == "ce_unarmed")
        assert "armed_schedule_id" not in event_item

    def test_armed_event_carries_armed_schedule_id(self, db: Database) -> None:
        from holdspeak.services.door_service import DoorService
        from holdspeak.services.follow_through_service import FollowThroughService
        from holdspeak.services.refinement_thought_service import (
            INBOX_DIRECTORY_ID,
            RefinementThoughtService,
        )

        db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
        starts = FIXED_NOW + timedelta(hours=1)
        _insert_event(
            db, "ce_door_armed",
            starts_at=starts.isoformat().replace("+00:00", "Z"),
            ends_at=(starts + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
        )
        # Arm the event
        armed = _svc(db).create_schedule(OWNER, calendar_event_id="ce_door_armed")

        door = DoorService(
            FollowThroughService(db),
            RefinementThoughtService(db),
            db.scheduled_recordings,
            db.calendar_events,
            clock=lambda: FIXED_NOW,
        )
        upcoming = door.get(OWNER)["upcoming"]
        event_item = next(i for i in upcoming if i["id"] == "ce_door_armed")
        assert event_item["armed_schedule_id"] == armed["id"]


# ────────────────────────────────────────────────────────────────
# AC-5: full lifecycle through the REAL conductor
# ────────────────────────────────────────────────────────────────


class FakeClock:
    """Injectable clock for deterministic time control."""

    def __init__(self, epoch: float):
        self._time = epoch
        self._lock = threading.Lock()

    def __call__(self) -> float:
        with self._lock:
            return self._time

    def advance(self, seconds: float) -> None:
        with self._lock:
            self._time += seconds

    def set(self, epoch: float) -> None:
        with self._lock:
            self._time = epoch


class TestEventLinkedLifecycle:
    """Arm a near-immediate linked event and prove arm -> countdown -> fire ->
    auto-stop -> terminal advance against the REAL conductor with fakes only
    at the engine-factory level (the stub law)."""

    def test_full_lifecycle(self, db: Database) -> None:
        from holdspeak.scheduled_recording_conductor import ScheduledRecordingConductor

        # Set up: event starting 2 minutes in the future relative to FIXED_NOW.
        # next_fire_at = starts_at - 60 = FIXED_NOW + 60s (still in the future).
        clock = FakeClock(FIXED_NOW.timestamp())

        event_starts = FIXED_NOW + timedelta(minutes=2)
        event_ends = FIXED_NOW + timedelta(minutes=7)  # 5 min event
        _insert_event(
            db, "ce_lifecycle",
            title="Quick sync",
            starts_at=event_starts.isoformat().replace("+00:00", "Z"),
            ends_at=event_ends.isoformat().replace("+00:00", "Z"),
        )

        # Arm via service (clock-injected)
        svc = _svc(db)
        armed = svc.create_schedule(OWNER, calendar_event_id="ce_lifecycle")
        schedule_id = armed["id"]
        assert armed["enabled"] is True
        assert armed["one_shot"] is True

        # Verify the schedule is in idle state, enabled, with next_fire_at set
        rec = db.scheduled_recordings.get(schedule_id)
        assert rec is not None
        assert rec.state == "idle"
        assert rec.enabled is True
        assert rec.next_fire_at is not None
        # next_fire_at should be starts_at - 60 = FIXED_NOW + 60s
        assert rec.next_fire_at > FIXED_NOW.timestamp(), \
            "next_fire_at should be in the future so boot reconcile doesn't mark it missed"

        start_fn = MagicMock()
        stop_fn = MagicMock()

        conductor = ScheduledRecordingConductor(
            clock=clock,
            db_factory=lambda: db,
            start_meeting_fn=start_fn,
            stop_meeting_fn=stop_fn,
            voice_floor_fn=lambda: None,
            countdown_seconds=0.01,  # near-instant countdown for test
            tick_interval=0.01,
        )

        # Start conductor BEFORE advancing clock past next_fire_at.
        # Boot reconciliation sees the schedule as not-yet-due (clock < next_fire_at).
        conductor.start()
        try:
            # Now advance the clock past next_fire_at so the tick fires it.
            clock.set(rec.next_fire_at + 1)

            # Wait for the conductor to arm and fire
            deadline = time.time() + 5.0
            while time.time() < deadline:
                rec = db.scheduled_recordings.get(schedule_id)
                if rec and rec.state == "recording":
                    break
                time.sleep(0.05)

            rec = db.scheduled_recordings.get(schedule_id)
            assert rec is not None
            assert rec.state == "recording", f"Expected 'recording', got '{rec.state}'"
            assert start_fn.called, "start_meeting_fn should have been called"

            # The conductor's auto-stop timer fires after duration_minutes.
            # Our duration is ~5 min but the conductor uses a threading.Timer
            # based on wall time. For testing, we verify the state machine
            # by manually triggering auto-stop (this is what the existing
            # conductor tests do).
            conductor._auto_stop(db, schedule_id)

            rec = db.scheduled_recordings.get(schedule_id)
            assert rec is not None
            assert rec.state == "stopped"
            assert rec.last_outcome == "auto_stopped"
            assert stop_fn.called, "stop_meeting_fn should have been called"

            # Terminal advance: one-shot should now be disabled
            assert rec.enabled is False, "One-shot should be disabled after terminal outcome"

            # L1 freed: event is armable again
            # Insert a fresh future event with the same id
            event_starts2 = FIXED_NOW + timedelta(hours=2)
            event_ends2 = event_starts2 + timedelta(minutes=30)
            _insert_event(
                db, "ce_lifecycle",  # same id
                title="Quick sync",
                starts_at=event_starts2.isoformat().replace("+00:00", "Z"),
                ends_at=event_ends2.isoformat().replace("+00:00", "Z"),
            )
            re_armed = svc.create_schedule(OWNER, calendar_event_id="ce_lifecycle")
            assert re_armed["id"] != schedule_id
            assert re_armed["calendar_event_id"] == "ce_lifecycle"
        finally:
            conductor.stop()


# ────────────────────────────────────────────────────────────────
# Route tests for the event-linked arm path
# ────────────────────────────────────────────────────────────────


@pytest.fixture
def route_client(db: Database, monkeypatch: Any) -> Any:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.scheduled_recordings import build_scheduled_recordings_router

    monkeypatch.setattr(
        "holdspeak.web.routes.scheduled_recordings.get_database", lambda: db
    )
    app = FastAPI()
    ctx = WebContext(get_state=lambda: {})
    app.include_router(build_scheduled_recordings_router(ctx))
    return TestClient(app)


class TestEventLinkedRoutes:
    """HTTP route tests for the event-linked arm path."""

    def test_arm_event_via_post(self, db: Database, route_client: Any) -> None:
        _insert_event_relative(db, "ce_route")
        resp = route_client.post("/api/scheduled-recordings", json={
            "calendar_event_id": "ce_route",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        sched = body["schedule"]
        assert sched["calendar_event_id"] == "ce_route"
        assert sched["one_shot"] is True
        assert sched["enabled"] is True

    def test_arm_nonexistent_event_returns_404(self, route_client: Any) -> None:
        resp = route_client.post("/api/scheduled-recordings", json={
            "calendar_event_id": "ce_ghost",
        })
        assert resp.status_code == 404
        body = resp.json()
        assert body["code"] == "not_found"

    def test_arm_ended_event_returns_422(self, db: Database, route_client: Any) -> None:
        _insert_event_relative(
            db, "ce_route_ended",
            starts_delta=timedelta(hours=-2),
            ends_delta=timedelta(hours=-1),
        )
        resp = route_client.post("/api/scheduled-recordings", json={
            "calendar_event_id": "ce_route_ended",
        })
        assert resp.status_code == 422
        assert resp.json()["code"] == "event_already_ended"

    def test_double_arm_returns_409(self, db: Database, route_client: Any) -> None:
        _insert_event_relative(db, "ce_route_double")
        resp1 = route_client.post("/api/scheduled-recordings", json={
            "calendar_event_id": "ce_route_double",
        })
        assert resp1.status_code == 201

        resp2 = route_client.post("/api/scheduled-recordings", json={
            "calendar_event_id": "ce_route_double",
        })
        assert resp2.status_code == 409
        assert resp2.json()["code"] == "event_already_armed"

    def test_manual_schedule_still_works(self, route_client: Any) -> None:
        """The manual (non-event) path is unbroken."""
        resp = route_client.post("/api/scheduled-recordings", json={
            "title": "Manual", "cron_expr": "0 9 * * 1", "duration_minutes": 30,
        })
        assert resp.status_code == 201
        assert resp.json()["schedule"]["title"] == "Manual"


# ────────────────────────────────────────────────────────────────
# MCP tests for the event-linked arm path
# ────────────────────────────────────────────────────────────────


def _setup_mcp(db: Database, monkeypatch: Any) -> None:
    from holdspeak.mcp import server
    from holdspeak.mcp import tools as mcp_tools

    monkeypatch.setattr(mcp_tools, "get_database", lambda: db)
    monkeypatch.setattr(mcp_tools, "get_observer", lambda: None)
    monkeypatch.setattr(
        server, "resolve_auth",
        lambda: SimpleNamespace(principal=Principal(PrincipalKind.OWNER, "test")),
    )
    monkeypatch.setattr(mcp_tools, "MeetingService", lambda db, **kw: object())
    monkeypatch.setattr(mcp_tools, "DictationService", lambda db, **kw: object())
    monkeypatch.setattr(mcp_tools, "DeskService", lambda db, **kw: object())
    monkeypatch.setattr(mcp_tools, "DecisionRecordService", lambda db, **kw: object())
    monkeypatch.setattr(mcp_tools, "EventQueryService", lambda db: object())
    monkeypatch.setattr(mcp_tools, "FollowThroughService", lambda db, **kw: object())
    monkeypatch.setattr(mcp_tools, "MondayBriefService", lambda db, **kw: object())


class TestEventLinkedMCP:
    """MCP tool tests for the event-linked arm path."""

    def test_arm_event_via_mcp(self, db: Database, monkeypatch: Any) -> None:
        from holdspeak.mcp.server import handle_message
        _setup_mcp(db, monkeypatch)
        _insert_event_relative(db, "ce_mcp")

        response = handle_message({
            "jsonrpc": "2.0", "id": "test", "method": "tools/call",
            "params": {
                "name": "scheduled_recording.create",
                "arguments": {"calendar_event_id": "ce_mcp"},
            },
        })
        assert response is not None
        result = response["result"]
        assert result["isError"] is False
        value = json.loads(result["content"][0]["text"])
        assert value["calendar_event_id"] == "ce_mcp"
        assert value["one_shot"] is True
        assert value["enabled"] is True

    def test_arm_nonexistent_event_via_mcp(self, db: Database, monkeypatch: Any) -> None:
        from holdspeak.mcp.server import handle_message
        _setup_mcp(db, monkeypatch)

        response = handle_message({
            "jsonrpc": "2.0", "id": "test", "method": "tools/call",
            "params": {
                "name": "scheduled_recording.create",
                "arguments": {"calendar_event_id": "ce_ghost"},
            },
        })
        assert response is not None
        result = response["result"]
        assert result["isError"] is True
        error_text = result["content"][0]["text"]
        assert "not_found" in error_text.lower() or "unknown" in error_text.lower()

    def test_calendar_event_id_in_tool_schema(self, db: Database, monkeypatch: Any) -> None:
        """The MCP tool schema includes calendar_event_id."""
        from holdspeak.mcp.server import handle_message
        _setup_mcp(db, monkeypatch)

        response = handle_message({
            "jsonrpc": "2.0", "id": 1, "method": "tools/list",
        })
        tools = response["result"]["tools"]
        create_tool = next(t for t in tools if t["name"] == "scheduled_recording.create")
        assert "calendar_event_id" in create_tool["inputSchema"]["properties"]
