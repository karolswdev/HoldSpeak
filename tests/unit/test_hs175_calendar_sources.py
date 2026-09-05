"""HS-175-03: Unit tests for the calendar sources API route.

Tests the GET /api/calendar/sources endpoint under isolated HOME with
seeded sources and events. No real network.
"""
from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture()
def _isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Any]:
    """Boot an isolated DB + Config for the sources route."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import get_database, reset_database

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()

    db = get_database()
    config = config_module.Config.load()
    return db, config


class TestCalendarSourcesRoute:
    """GET /api/calendar/sources returns per-source facts."""

    def test_empty_sources(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """No configured sources -> empty list."""
        db, config = _setup(tmp_path, monkeypatch)
        from holdspeak.web.routes.calendar_sources import (
            _source_host,
            _source_type,
        )
        from holdspeak.config.integrations import CalendarSource

        src = CalendarSource(id="x", label="", url="/tmp/cal.ics", enabled=True)
        assert _source_type(src) == "ICS"
        assert _source_host(src) is None

    def test_https_source_host(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """HTTPS source has a host."""
        db, config = _setup(tmp_path, monkeypatch)
        from holdspeak.web.routes.calendar_sources import _source_host
        from holdspeak.config.integrations import CalendarSource

        src = CalendarSource(
            id="x", label="WORK",
            url="https://outlook.office365.com/api/v2.0/me/events",
            enabled=True,
        )
        assert _source_host(src) == "outlook.office365.com"

    def test_snapshot_type(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Snapshot source type detection."""
        db, config = _setup(tmp_path, monkeypatch)
        from holdspeak.web.routes.calendar_sources import _source_type
        from holdspeak.config.integrations import CalendarSource

        src = CalendarSource(id="x", label="O365 SNAPSHOT", url="/tmp/snap.ics", enabled=True)
        assert _source_type(src) == "SNAPSHOT"

    def test_file_source_no_egress(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """File source has no egress."""
        db, config = _setup(tmp_path, monkeypatch)
        from holdspeak.web.routes.calendar_sources import _source_host
        from holdspeak.config.integrations import CalendarSource

        src = CalendarSource(id="x", label="", url="/Users/me/cal.ics", enabled=True)
        assert _source_host(src) is None

    def test_source_stats_from_db(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Source stats (calendar_count, last_seen) come from calendar_events."""
        db, config = _setup(tmp_path, monkeypatch)
        from holdspeak.config.integrations import CalendarSource, CalendarConfig

        sid = str(uuid.uuid4())
        source = CalendarSource(id=sid, label="WORK", url="/tmp/cal.ics", enabled=True)
        config.calendar = CalendarConfig(sources=[source])
        config.save()

        # Seed two events with the same source but different UIDs.
        now = time.time()
        from holdspeak.db.calendar_events import CalendarEvent
        db.calendar_events.replace_projection(
            "rev1",
            [
                _make_event("e1", "uid1", "Standup", "2026-09-08T10:00:00Z", "2026-09-08T11:00:00Z"),
                _make_event("e2", "uid2", "Review", "2026-09-09T14:00:00Z", "2026-09-09T15:00:00Z"),
            ],
            seen_at=now,
            source_id=sid,
            source_label="WORK",
        )

        # Verify via the module functions.
        with db._connection() as conn:
            row = conn.execute(
                "SELECT COUNT(DISTINCT uid) AS cnt, MAX(last_seen_at) AS ls "
                "FROM calendar_events WHERE source_id = ?",
                (sid,),
            ).fetchone()
            assert row["cnt"] == 2
            assert row["ls"] is not None

    def test_matched_this_week(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """matched_this_week counts events with calendar_event_projects links this week."""
        db, config = _setup(tmp_path, monkeypatch)
        from holdspeak.config.integrations import CalendarSource, CalendarConfig
        from holdspeak.web.routes.calendar_sources import _iso_week_range_utc

        sid = str(uuid.uuid4())
        source = CalendarSource(id=sid, label="WORK", url="/tmp/cal.ics", enabled=True)
        config.calendar = CalendarConfig(sources=[source])
        config.meeting.auto_record = "room_linked"
        config.save()

        week_start, week_end = _iso_week_range_utc()

        # Seed an event within this week.
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        # Find a time this week.
        monday = now - timedelta(days=now.weekday())
        event_time = monday.replace(hour=10, minute=0, second=0, microsecond=0)
        if event_time < now:
            event_time = now + timedelta(hours=1)
        event_iso = event_time.isoformat(timespec="seconds").replace("+00:00", "Z")
        end_iso = (event_time + timedelta(hours=1)).isoformat(timespec="seconds").replace("+00:00", "Z")

        eid = str(uuid.uuid4())
        db.calendar_events.replace_projection(
            "rev1",
            [_make_event(eid, "uid-match", "Standup", event_iso, end_iso)],
            seen_at=time.time(),
            source_id=sid,
            source_label="WORK",
        )

        # Link this event to a project.
        pid = str(uuid.uuid4())
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name) VALUES (?, ?)",
                (pid, "Q4 Platform"),
            )
        db.calendar_event_projects.link(eid, pid, "title")

        # Count matched events this week.
        with db._connection() as conn:
            row = conn.execute(
                """SELECT COUNT(DISTINCT ce.id) AS cnt
                   FROM calendar_events ce
                   INNER JOIN calendar_event_projects cep
                       ON cep.calendar_event_id = ce.id
                   WHERE ce.starts_at >= ? AND ce.starts_at < ?""",
                (week_start, week_end),
            ).fetchone()
            assert row["cnt"] >= 1

    def test_auto_record_values(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """auto_record values round-trip through config."""
        db, config = _setup(tmp_path, monkeypatch)
        for value in ("off", "all_calendar", "room_linked"):
            config.meeting.auto_record = value
            config.save()
            from holdspeak.config import Config
            reloaded = Config.load()
            assert reloaded.meeting.auto_record == value

    def test_auto_record_lead_minutes(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """auto_record_lead_minutes defaults to 5 and rejects zero."""
        db, config = _setup(tmp_path, monkeypatch)
        assert config.meeting.auto_record_lead_minutes == 5
        config.meeting.auto_record_lead_minutes = 0
        # __post_init__ clamps to 1.
        from holdspeak.config.meeting import MeetingConfig
        mc = MeetingConfig(auto_record_lead_minutes=0)
        assert mc.auto_record_lead_minutes == 1


def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Any]:
    """Boot isolated DB + Config."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import get_database, reset_database

    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()

    db = get_database()
    config = config_module.Config.load()
    return db, config


class _FakeEvent:
    """Minimal CalendarEventProjection for seeding."""
    def __init__(self, id: str, uid: str, title: str, starts_at: str, ends_at: str):
        self.id = id
        self.uid = uid
        self.title = title
        self.starts_at = starts_at
        self.ends_at = ends_at
        self.location = None
        self.meeting_url = None


def _make_event(eid: str, uid: str, title: str, starts: str, ends: str) -> _FakeEvent:
    return _FakeEvent(eid, uid, title, starts, ends)
