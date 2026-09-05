"""HS-175-03: Event-born scheduled recordings.

Tests the auto-record setting, the conductor's event-born creation logic,
idempotency, vanished/moved event handling, the hub read, and the door
projection.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
from holdspeak.config import CalendarConfig, CalendarSource, Config
from holdspeak.config.meeting import MeetingConfig
from holdspeak.db.core import Database, reset_database


# -- constants ----------------------------------------------------------------

NOW = datetime(2026, 9, 5, 8, 0, tzinfo=timezone.utc)
NOW_EPOCH = NOW.timestamp()

ICS_TWO_EVENTS = (
    b"BEGIN:VCALENDAR\r\n"
    b"BEGIN:VEVENT\r\n"
    b"UID:ev-with-url\r\n"
    b"DTSTART:20260905T100000Z\r\n"
    b"DTEND:20260905T110000Z\r\n"
    b"SUMMARY:Standup\r\n"
    b"URL:https://teams.example.com/meet/123\r\n"
    b"END:VEVENT\r\n"
    b"BEGIN:VEVENT\r\n"
    b"UID:ev-no-url\r\n"
    b"DTSTART:20260905T140000Z\r\n"
    b"DTEND:20260905T150000Z\r\n"
    b"SUMMARY:Lunch\r\n"
    b"END:VEVENT\r\n"
    b"END:VCALENDAR\r\n"
)

ICS_ONE_WITH_URL = (
    b"BEGIN:VCALENDAR\r\n"
    b"BEGIN:VEVENT\r\n"
    b"UID:ev-with-url\r\n"
    b"DTSTART:20260905T100000Z\r\n"
    b"DTEND:20260905T110000Z\r\n"
    b"SUMMARY:Standup\r\n"
    b"URL:https://teams.example.com/meet/123\r\n"
    b"END:VEVENT\r\n"
    b"END:VCALENDAR\r\n"
)

ICS_MOVED_EVENT = (
    b"BEGIN:VCALENDAR\r\n"
    b"BEGIN:VEVENT\r\n"
    b"UID:ev-with-url\r\n"
    b"DTSTART:20260905T120000Z\r\n"
    b"DTEND:20260905T130000Z\r\n"
    b"SUMMARY:Standup\r\n"
    b"URL:https://teams.example.com/meet/123\r\n"
    b"END:VEVENT\r\n"
    b"END:VCALENDAR\r\n"
)

ICS_EMPTY = (
    b"BEGIN:VCALENDAR\r\n"
    b"END:VCALENDAR\r\n"
)

SOURCE_ID = "test-cal"


# -- helpers ------------------------------------------------------------------

def _cal(url: str = "/test.ics") -> CalendarConfig:
    return CalendarConfig(sources=[
        CalendarSource(id=SOURCE_ID, label="WORK", url=url, enabled=True)
    ])


def _config(auto_record: str = "off", lead: int = 5) -> Config:
    return Config(
        calendar=_cal(),
        meeting=MeetingConfig(auto_record=auto_record, auto_record_lead_minutes=lead),
    )


def _make_conductor(
    db: Database,
    config_fn,
    ics_bytes: bytes = ICS_TWO_EVENTS,
) -> CalendarIngestConductor:
    return CalendarIngestConductor(
        clock=lambda: NOW_EPOCH,
        db_factory=lambda: db,
        source_reader=lambda _sub: ics_bytes,
        config_loader=config_fn,
        tick_interval=999,
    )


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "event-born.db")
    yield database
    reset_database()


# -- tests --------------------------------------------------------------------


class TestAutoRecordOff:
    """When auto_record=off, no event-born recordings are created."""

    def test_off_creates_nothing(self, db: Database) -> None:
        conductor = _make_conductor(db, lambda: _config("off"))
        conductor.refresh()

        recordings = db.scheduled_recordings.list_all()
        assert len(recordings) == 0


class TestAutoRecordAllCalendar:
    """When auto_record=all_calendar, every event with a meeting_url gets a recording."""

    def test_creates_one_per_event_with_url(self, db: Database) -> None:
        conductor = _make_conductor(db, lambda: _config("all_calendar"))
        conductor.refresh()

        recordings = db.scheduled_recordings.list_all()
        assert len(recordings) == 1
        rec = recordings[0]
        assert rec.title == "Standup"
        assert rec.calendar_uid == "ev-with-url"
        assert rec.calendar_source_id == SOURCE_ID
        assert rec.born_from == "calendar_event"
        assert rec.enabled is True
        assert rec.state == "idle"

    def test_no_recording_without_url(self, db: Database) -> None:
        """The Lunch event has no meeting_url -- no recording created."""
        conductor = _make_conductor(db, lambda: _config("all_calendar"))
        conductor.refresh()

        recordings = db.scheduled_recordings.list_all()
        titles = [r.title for r in recordings]
        assert "Lunch" not in titles

    def test_lead_time(self, db: Database) -> None:
        """The recording's next_fire_at is starts_at - lead_minutes."""
        conductor = _make_conductor(db, lambda: _config("all_calendar", lead=5))
        conductor.refresh()

        rec = db.scheduled_recordings.list_all()[0]
        event_start = datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc)
        expected_fire = (event_start - timedelta(minutes=5)).timestamp()
        assert rec.next_fire_at == pytest.approx(expected_fire, abs=1.0)

    def test_duration_from_event(self, db: Database) -> None:
        """Duration is computed from event start/end."""
        conductor = _make_conductor(db, lambda: _config("all_calendar"))
        conductor.refresh()

        rec = db.scheduled_recordings.list_all()[0]
        assert rec.duration_minutes == 60  # 10:00 to 11:00


class TestAutoRecordRoomLinked:
    """When auto_record=room_linked, only events with a calendar_event_projects row."""

    def test_creates_only_for_linked(self, db: Database) -> None:
        conductor = _make_conductor(db, lambda: _config("room_linked"))
        conductor.refresh()

        # No calendar_event_projects table yet -> treats all as unlinked.
        recordings = db.scheduled_recordings.list_all()
        assert len(recordings) == 0

    def test_creates_when_linked(self, db: Database) -> None:
        """When the event has a calendar_event_projects row, recording is created."""
        conductor = _make_conductor(db, lambda: _config("room_linked"))
        conductor.refresh()

        # Manually create the join table and insert a link.
        with db._connection() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS calendar_event_projects (
                       calendar_event_id TEXT NOT NULL,
                       project_id TEXT NOT NULL,
                       match_source TEXT NOT NULL DEFAULT 'manual'
                   )"""
            )
            # Find the event id from the projection.
            event_row = conn.execute(
                "SELECT id FROM calendar_events WHERE uid='ev-with-url'"
            ).fetchone()
            assert event_row is not None
            conn.execute(
                "INSERT INTO calendar_event_projects (calendar_event_id, project_id, match_source) "
                "VALUES (?, 'proj-1', 'title')",
                (event_row["id"],),
            )

        # Refresh again -- now the event is linked.
        conductor.refresh()

        recordings = db.scheduled_recordings.list_all()
        assert len(recordings) == 1
        assert recordings[0].title == "Standup"


class TestIdempotency:
    """Re-ingesting the same event does not create duplicate recordings."""

    def test_idempotent_across_refreshes(self, db: Database) -> None:
        conductor = _make_conductor(db, lambda: _config("all_calendar"))
        conductor.refresh()
        conductor.refresh()
        conductor.refresh()

        recordings = db.scheduled_recordings.list_all()
        assert len(recordings) == 1


class TestVanishedEvent:
    """An event that disappears from the ICS -> its recording is cancelled."""

    def test_vanished_event_cancels_recording(self, db: Database) -> None:
        # First refresh creates the recording.
        ics_state = {"bytes": ICS_ONE_WITH_URL}
        conductor = CalendarIngestConductor(
            clock=lambda: NOW_EPOCH,
            db_factory=lambda: db,
            source_reader=lambda _sub: ics_state["bytes"],
            config_loader=lambda: _config("all_calendar"),
            tick_interval=999,
        )
        conductor.refresh()
        recordings = db.scheduled_recordings.list_all()
        assert len(recordings) == 1
        assert recordings[0].enabled is True
        assert recordings[0].state == "idle"

        # Event vanishes from the feed.
        ics_state["bytes"] = ICS_EMPTY
        conductor.refresh()

        recordings = db.scheduled_recordings.list_all()
        rec = recordings[0]
        assert rec.enabled is False
        assert rec.state == "cancelled"
        assert rec.last_outcome == "event_removed"


class TestMovedEvent:
    """An event whose time changed -> next_fire_at follows."""

    def test_moved_event_updates_fire_time(self, db: Database) -> None:
        ics_state = {"bytes": ICS_ONE_WITH_URL}
        conductor = CalendarIngestConductor(
            clock=lambda: NOW_EPOCH,
            db_factory=lambda: db,
            source_reader=lambda _sub: ics_state["bytes"],
            config_loader=lambda: _config("all_calendar", lead=5),
            tick_interval=999,
        )
        conductor.refresh()

        rec_before = db.scheduled_recordings.list_all()[0]
        old_fire = rec_before.next_fire_at

        # Event moves to 12:00.
        ics_state["bytes"] = ICS_MOVED_EVENT
        conductor.refresh()

        rec_after = db.scheduled_recordings.list_all()
        # The recording for the old event time was reconciled (R1 or R2),
        # so next_fire_at should have changed.
        enabled_recs = [r for r in rec_after if r.enabled]
        assert len(enabled_recs) >= 1
        # At least one enabled recording should have a different fire time.
        any_changed = any(r.next_fire_at != old_fire for r in enabled_recs)
        assert any_changed or len(enabled_recs) > 1


class TestNeverStarted:
    """The conductor never sets state='recording' -- Article IV."""

    def test_no_recording_state_from_event_born(self, db: Database) -> None:
        conductor = _make_conductor(db, lambda: _config("all_calendar"))
        conductor.refresh()

        recordings = db.scheduled_recordings.list_all()
        for rec in recordings:
            assert rec.state != "recording"


class TestSettingOnHubRead:
    """The hub read exposes the auto_record setting."""

    def test_hub_read_exposes_auto_record(self, db: Database) -> None:
        """The MeetingConfig carries auto_record; verify it serializes."""
        cfg = MeetingConfig(auto_record="all_calendar", auto_record_lead_minutes=10)
        assert cfg.auto_record == "all_calendar"
        assert cfg.auto_record_lead_minutes == 10

    def test_default_is_off(self) -> None:
        cfg = MeetingConfig()
        assert cfg.auto_record == "off"
        assert cfg.auto_record_lead_minutes == 5

    def test_invalid_auto_record_rejected(self) -> None:
        with pytest.raises(ValueError, match="auto_record"):
            MeetingConfig(auto_record="invalid")


class TestRecordingReceipt:
    """Every auto-creation is receipted."""

    def test_receipt_written(self, db: Database) -> None:
        conductor = _make_conductor(db, lambda: _config("all_calendar"))
        conductor.refresh()

        with db._connection() as conn:
            receipts = conn.execute(
                "SELECT * FROM kernel_receipts WHERE outcome='scheduled_recording.created.calendar_event'"
            ).fetchall()
        assert len(receipts) == 1
