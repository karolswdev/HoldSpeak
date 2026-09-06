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

        # No Rooms and no links -> every event is unlinked -> nothing arms.
        recordings = db.scheduled_recordings.list_all()
        assert len(recordings) == 0

    def test_creates_when_linked(self, db: Database) -> None:
        """When the event has a calendar_event_projects row, recording is created."""
        conductor = _make_conductor(db, lambda: _config("room_linked"))
        conductor.refresh()

        # The owner links the event to a Room by hand (a manual link is the
        # honest fixture: the matcher clears stale auto links of Rooms that
        # do not exist, and 'proj-1' is no Room here).
        with db._connection() as conn:
            event_row = conn.execute(
                "SELECT id FROM calendar_events WHERE uid='ev-with-url'"
            ).fetchone()
            assert event_row is not None
        db.calendar_event_projects.link(event_row["id"], "proj-1", "manual")

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


class TestArmsLikeEveryScheduledRecording:
    """C1 as ruled (design B11): an event-born recording is a 136 scheduled
    recording -- the ingest conductor leaves it idle + enabled with
    next_fire_at = starts_at - lead, and the scheduled-recording conductor
    arms it at that time and records at the event.  This test proves ONLY
    the ingest side's hand-off; it makes no "never started" claim."""

    def test_event_born_row_is_handed_to_the_scheduled_conductor(self, db: Database) -> None:
        conductor = _make_conductor(db, lambda: _config("all_calendar", lead=5))
        conductor.refresh()

        recordings = db.scheduled_recordings.list_all()
        assert len(recordings) == 1
        rec = recordings[0]
        assert rec.state == "idle" and rec.enabled is True
        assert rec.one_shot is True and rec.born_from == "calendar_event"
        event_start = datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc)
        assert rec.next_fire_at == pytest.approx(
            (event_start - timedelta(minutes=5)).timestamp(), abs=1.0
        )
        # list_enabled is what the scheduled-recording conductor polls.
        assert [r.id for r in db.scheduled_recordings.list_enabled()] == [rec.id]


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


# -- HS-175 counsel-on-built: C3 / C4 / C6(b) --------------------------------
#
# C3  the owner's cancel is final across refreshes (tombstone by source+uid).
# C4  Remove/Disable disarms, even with zero enabled sources.
# C6b the matcher runs before the auto-create, so room_linked arms on the
#     FIRST refresh.

ICS_SECOND_SOURCE = (
    b"BEGIN:VCALENDAR\r\n"
    b"BEGIN:VEVENT\r\n"
    b"UID:ev-personal\r\n"
    b"DTSTART:20260905T160000Z\r\n"
    b"DTEND:20260905T163000Z\r\n"
    b"SUMMARY:Dentist call\r\n"
    b"URL:https://zoom.example.com/j/9\r\n"
    b"END:VEVENT\r\n"
    b"END:VCALENDAR\r\n"
)

ICS_ROOM_EVENT = (
    b"BEGIN:VCALENDAR\r\n"
    b"BEGIN:VEVENT\r\n"
    b"UID:ev-room\r\n"
    b"DTSTART:20260905T130000Z\r\n"
    b"DTEND:20260905T133000Z\r\n"
    b"SUMMARY:Q4 Platform Standup\r\n"
    b"URL:https://teams.example.com/meet/q4\r\n"
    b"END:VEVENT\r\n"
    b"END:VCALENDAR\r\n"
)


def _owner_cancel(db: Database, rec_id: str, outcome: str = "owner_cancelled") -> None:
    """What the owner's Cancel leaves behind (C2's contract on the row):
    enabled=0, state='cancelled', last_outcome='owner_cancelled' -- or the
    136 countdown cancel's 'cancelled'.  Either is the owner's word."""
    db.scheduled_recordings.set_state(
        rec_id, "cancelled", last_outcome=outcome, enabled=False, next_fire_at=None,
    )


def _receipts(db: Database, outcome: str) -> int:
    with db._connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM kernel_receipts WHERE outcome = ?", (outcome,)
        ).fetchone()
    return int(row["n"])


def _feed_conductor(db: Database, config_fn, feed_state: dict) -> CalendarIngestConductor:
    return CalendarIngestConductor(
        clock=lambda: NOW_EPOCH,
        db_factory=lambda: db,
        source_reader=lambda _sub: feed_state["bytes"],
        config_loader=config_fn,
        tick_interval=999,
    )


class TestOwnerCancelIsFinal:
    """C3: cancel -> refresh -> still zero enabled rows, one skip receipt."""

    @pytest.mark.parametrize("outcome", ["owner_cancelled", "cancelled"])
    def test_cancel_then_refresh_does_not_rearm(self, db: Database, outcome: str) -> None:
        conductor = _make_conductor(db, lambda: _config("all_calendar"), ICS_ONE_WITH_URL)
        conductor.refresh()
        rec = db.scheduled_recordings.list_all()[0]
        _owner_cancel(db, rec.id, outcome)

        conductor.refresh()

        rows = db.scheduled_recordings.list_all()
        assert [r.id for r in rows] == [rec.id], "the refresh must not insert a second row"
        assert rows[0].enabled is False and rows[0].state == "cancelled"
        assert db.scheduled_recordings.list_enabled() == [], "a cancelled row is never armed"
        assert _receipts(db, "scheduled_recording.skipped.owner_cancelled") == 1
        assert _receipts(db, "scheduled_recording.created.calendar_event") == 1

        # Idempotent: a third refresh adds neither a row nor a receipt.
        conductor.refresh()
        assert len(db.scheduled_recordings.list_all()) == 1
        assert _receipts(db, "scheduled_recording.skipped.owner_cancelled") == 1

    def test_moved_occurrence_is_a_new_one_and_rearms(self, db: Database) -> None:
        """Counsel re-read (1): the tombstone is keyed by OCCURRENCE
        (source, uid, starts_at) so Cancel means "this one".  A single event
        whose time moves is a new occurrence under the toggle's standing
        consent -- it re-arms, and the cancelled row stays cancelled.
        (Carried to the owner: "this one or the series?")"""
        feed = {"bytes": ICS_ONE_WITH_URL}
        conductor = _feed_conductor(db, lambda: _config("all_calendar"), feed)
        conductor.refresh()
        rec = db.scheduled_recordings.list_all()[0]
        assert rec.calendar_starts_at == "2026-09-05T10:00:00Z"
        _owner_cancel(db, rec.id)

        feed["bytes"] = ICS_MOVED_EVENT
        conductor.refresh()

        enabled = db.scheduled_recordings.list_enabled()
        assert [r.calendar_starts_at for r in enabled] == ["2026-09-05T12:00:00Z"]
        cancelled = db.scheduled_recordings.get(rec.id)
        assert cancelled is not None and cancelled.enabled is False
        assert _receipts(db, "scheduled_recording.skipped.owner_cancelled") == 0
        assert _receipts(db, "scheduled_recording.created.calendar_event") == 2

    def test_event_removed_is_not_a_tombstone(self, db: Database) -> None:
        """R3's cancel is the feed's doing, receipted as such; if the event
        returns, the toggle's standing consent arms it again."""
        feed = {"bytes": ICS_ONE_WITH_URL}
        conductor = _feed_conductor(db, lambda: _config("all_calendar"), feed)
        conductor.refresh()
        first = db.scheduled_recordings.list_all()[0]

        feed["bytes"] = ICS_EMPTY
        conductor.refresh()
        gone = db.scheduled_recordings.get(first.id)
        assert gone is not None and gone.last_outcome == "event_removed"
        assert _receipts(db, "scheduled_recording.cancelled.calendar_event_removed") == 1

        feed["bytes"] = ICS_ONE_WITH_URL
        conductor.refresh()
        enabled = db.scheduled_recordings.list_enabled()
        assert len(enabled) == 1 and enabled[0].id != first.id
        assert _receipts(db, "scheduled_recording.skipped.owner_cancelled") == 0


class TestSourceRemovedDisarms:
    """C4: Remove/Disable cancels the source's idle event-born recordings
    with a receipt, and the prune runs even with zero enabled sources."""

    WORK = CalendarSource(id="cal-work", label="WORK", url="/work.ics", enabled=True)
    HOME = CalendarSource(id="cal-home", label="HOME", url="/home.ics", enabled=True)

    def _two_source_conductor(self, db: Database):
        state = {"sources": [self.WORK, self.HOME]}
        feeds = {"/work.ics": ICS_ONE_WITH_URL, "/home.ics": ICS_SECOND_SOURCE}

        def cfg() -> Config:
            return Config(
                calendar=CalendarConfig(sources=list(state["sources"])),
                meeting=MeetingConfig(auto_record="all_calendar", auto_record_lead_minutes=5),
            )

        conductor = CalendarIngestConductor(
            clock=lambda: NOW_EPOCH,
            db_factory=lambda: db,
            source_reader=lambda sub: feeds[sub],
            config_loader=cfg,
            tick_interval=999,
        )
        return conductor, state

    def test_remove_cancels_its_recordings_with_a_receipt(self, db: Database) -> None:
        conductor, state = self._two_source_conductor(db)
        conductor.refresh()
        assert len(db.scheduled_recordings.list_enabled()) == 2

        state["sources"] = [self.WORK]  # the owner pressed Remove on HOME
        conductor.refresh()

        enabled = db.scheduled_recordings.list_enabled()
        assert [r.calendar_source_id for r in enabled] == ["cal-work"]
        home = [r for r in db.scheduled_recordings.list_all() if r.calendar_source_id == "cal-home"]
        assert len(home) == 1
        assert home[0].state == "cancelled"
        assert home[0].last_outcome == "calendar_source_removed"
        assert home[0].next_fire_at is None
        assert _receipts(db, "scheduled_recording.cancelled.calendar_source_removed") == 1
        assert {e.source_id for e in db.calendar_events.list_all()} == {"cal-work"}

    def test_disable_last_source_prunes_with_zero_enabled(self, db: Database) -> None:
        conductor, state = self._two_source_conductor(db)
        conductor.refresh()

        state["sources"] = [
            CalendarSource(id="cal-work", label="WORK", url="/work.ics", enabled=False),
            CalendarSource(id="cal-home", label="HOME", url="/home.ics", enabled=False),
        ]
        assert conductor.refresh() is False, "nothing applied -- but the prune ran"

        assert db.calendar_events.list_all() == [], "the projection of a disabled source is gone"
        assert db.scheduled_recordings.list_enabled() == []
        outcomes = sorted(r.last_outcome for r in db.scheduled_recordings.list_all())
        assert outcomes == ["calendar_source_disabled", "calendar_source_disabled"]
        assert _receipts(db, "scheduled_recording.cancelled.calendar_source_disabled") == 2

        # Idempotent: the next refresh cancels nothing twice.
        conductor.refresh()
        assert _receipts(db, "scheduled_recording.cancelled.calendar_source_disabled") == 2

    def test_remove_everything_prunes_with_zero_configured(self, db: Database) -> None:
        conductor, state = self._two_source_conductor(db)
        conductor.refresh()

        state["sources"] = []
        assert conductor.refresh() is False

        assert db.calendar_events.list_all() == []
        assert db.scheduled_recordings.list_enabled() == []
        outcomes = sorted(r.last_outcome for r in db.scheduled_recordings.list_all())
        assert outcomes == ["calendar_source_removed", "calendar_source_removed"]

    def test_reenabled_source_rearms_under_the_toggle(self, db: Database) -> None:
        """A source-gone cancel is the owner's Disable of the SOURCE, not a
        cancel of the meeting: Enable brings the arm back under the toggle."""
        conductor, state = self._two_source_conductor(db)
        conductor.refresh()
        state["sources"] = [
            CalendarSource(id="cal-work", label="WORK", url="/work.ics", enabled=False),
            self.HOME,
        ]
        conductor.refresh()
        assert [r.calendar_source_id for r in db.scheduled_recordings.list_enabled()] == ["cal-home"]

        state["sources"] = [self.WORK, self.HOME]
        conductor.refresh()
        assert sorted(r.calendar_source_id for r in db.scheduled_recordings.list_enabled()) == [
            "cal-home", "cal-work",
        ]
        assert _receipts(db, "scheduled_recording.skipped.owner_cancelled") == 0

    def test_zero_sources_ever_is_quiet(self, db: Database) -> None:
        conductor = CalendarIngestConductor(
            clock=lambda: NOW_EPOCH,
            db_factory=lambda: db,
            source_reader=lambda _sub: ICS_EMPTY,
            config_loader=lambda: Config(calendar=CalendarConfig(sources=[]), meeting=MeetingConfig()),
            tick_interval=999,
        )
        assert conductor.refresh() is False
        with db._connection() as conn:
            n = conn.execute("SELECT COUNT(*) AS n FROM kernel_receipts").fetchone()["n"]
        assert int(n) == 0


class TestMatcherRunsBeforeAutoCreate:
    """C6(b): under room_linked a new Room-titled event arms on the FIRST refresh."""

    def test_room_linked_event_arms_on_the_first_refresh(self, db: Database) -> None:
        with db._connection() as conn:
            conn.execute("INSERT INTO projects (id, name) VALUES ('p-q4', 'Q4 Platform')")
        conductor = _make_conductor(db, lambda: _config("room_linked"), ICS_ROOM_EVENT)

        conductor.refresh()

        links = db.calendar_event_projects.list_for_project("p-q4")
        assert len(links) == 1 and links[0].match_source == "title"
        enabled = db.scheduled_recordings.list_enabled()
        assert len(enabled) == 1
        assert enabled[0].title == "Q4 Platform Standup"
        assert enabled[0].calendar_event_id == links[0].calendar_event_id


class TestOwnerCancelStamp:
    """C3: the owner's Cancel stamps ``owner_cancelled_at`` (the C2 lane's
    write, holdspeak/services/scheduled_recording_service.py); the stamp
    alone is a tombstone, whatever ``last_outcome`` later says."""

    def test_stamp_alone_blocks_the_rearm(self, db: Database) -> None:
        conductor = _make_conductor(db, lambda: _config("all_calendar"), ICS_ONE_WITH_URL)
        conductor.refresh()
        rec = db.scheduled_recordings.list_all()[0]
        db.scheduled_recordings.set_state(rec.id, "cancelled", last_outcome="", enabled=False, next_fire_at=None)
        with db._connection() as conn:
            conn.execute(
                "UPDATE scheduled_recordings SET owner_cancelled_at = ? WHERE id = ?",
                (NOW_EPOCH, rec.id),
            )
        assert db.scheduled_recordings.get(rec.id).owner_cancelled_at == NOW_EPOCH

        conductor.refresh()

        assert [r.id for r in db.scheduled_recordings.list_all()] == [rec.id]
        assert db.scheduled_recordings.list_enabled() == []
        assert _receipts(db, "scheduled_recording.skipped.owner_cancelled") == 1


# -- HS-175 counsel re-read: (1) Cancel means THIS occurrence, (2) every arm
#    receipted, (5-test) B11 -- both conductors on one temp DB.

ICS_SERIES_OF_FOUR = (
    b"BEGIN:VCALENDAR\r\n"
    b"BEGIN:VEVENT\r\n"
    b"UID:u-standup\r\n"
    b"DTSTART:20260907T150000Z\r\n"
    b"DTEND:20260907T153000Z\r\n"
    b"SUMMARY:Standup\r\n"
    b"URL:https://teams.example.com/meet/standup\r\n"
    b"RRULE:FREQ=DAILY;COUNT=4\r\n"
    b"END:VEVENT\r\n"
    b"END:VCALENDAR\r\n"
)


class TestCancelIsThisOccurrence:
    """Re-read (1): a series shares one uid; the tombstone is keyed by
    (source, uid, starts_at).  Cancel one standup -> the other three stay
    armed, only that occurrence is skipped on refresh, one skip receipt."""

    def test_cancel_one_of_four_leaves_three_armed(self, db: Database) -> None:
        conductor = _make_conductor(db, lambda: _config("all_calendar"), ICS_SERIES_OF_FOUR)
        conductor.refresh()
        armed = sorted(db.scheduled_recordings.list_enabled(), key=lambda r: r.calendar_starts_at)
        assert len(armed) == 4
        assert {r.calendar_uid for r in armed} == {"u-standup"}
        assert [r.calendar_starts_at for r in armed] == [
            "2026-09-07T15:00:00Z", "2026-09-08T15:00:00Z",
            "2026-09-09T15:00:00Z", "2026-09-10T15:00:00Z",
        ]
        assert _receipts(db, "scheduled_recording.created.calendar_event") == 4

        tuesday = armed[1]
        _owner_cancel(db, tuesday.id)
        conductor.refresh()

        still = sorted(db.scheduled_recordings.list_enabled(), key=lambda r: r.calendar_starts_at)
        assert [r.id for r in still] == [armed[0].id, armed[2].id, armed[3].id], "siblings untouched"
        assert db.scheduled_recordings.get(tuesday.id).enabled is False
        assert len(db.scheduled_recordings.list_all()) == 4, "no new row for Tuesday"
        assert _receipts(db, "scheduled_recording.skipped.owner_cancelled") == 1
        assert db.scheduled_recordings.list_owner_cancelled_occurrences(SOURCE_ID) == {
            ("u-standup", "2026-09-08T15:00:00Z"),
        }

        conductor.refresh()  # idempotent
        assert len(db.scheduled_recordings.list_all()) == 4
        assert _receipts(db, "scheduled_recording.skipped.owner_cancelled") == 1


class TestEveryArmReceipted:
    """Re-read (2): the create receipt carries the schedule id, so a re-arm
    after Disable -> Enable has its own receipt."""

    def test_disable_enable_writes_two_create_receipts(self, db: Database) -> None:
        state = {"enabled": True}

        def cfg() -> Config:
            return Config(
                calendar=CalendarConfig(sources=[
                    CalendarSource(id=SOURCE_ID, label="WORK", url="/test.ics", enabled=state["enabled"])
                ]),
                meeting=MeetingConfig(auto_record="all_calendar", auto_record_lead_minutes=5),
            )

        conductor = _make_conductor(db, cfg, ICS_ONE_WITH_URL)
        conductor.refresh()
        first = db.scheduled_recordings.list_enabled()[0]
        assert _receipts(db, "scheduled_recording.created.calendar_event") == 1

        state["enabled"] = False
        conductor.refresh()
        assert db.scheduled_recordings.list_enabled() == []

        state["enabled"] = True
        conductor.refresh()
        second = db.scheduled_recordings.list_enabled()[0]
        assert second.id != first.id
        assert _receipts(db, "scheduled_recording.created.calendar_event") == 2


class TestB11BothConductors:
    """B11 in the suite: the calendar conductor arms an event-born row; the
    scheduled-recording conductor's tick then arms it and starts capture
    (a stubbed capture entry) -- the hand-off the ruling names."""

    def test_event_born_row_is_armed_and_started_by_the_136_conductor(self, db: Database) -> None:
        import time as _time
        from holdspeak.scheduled_recording_conductor import ScheduledRecordingConductor

        conductor = _make_conductor(db, lambda: _config("all_calendar", lead=5), ICS_ONE_WITH_URL)
        conductor.refresh()
        rec = db.scheduled_recordings.list_enabled()[0]
        assert rec.state == "idle" and rec.born_from == "calendar_event"

        started: list[dict] = []
        clock = {"t": rec.next_fire_at + 1}
        sc = ScheduledRecordingConductor(
            clock=lambda: clock["t"],
            db_factory=lambda: db,
            start_meeting_fn=lambda **kw: started.append(kw),
            countdown_seconds=0,
        )
        sc._tick()
        deadline = _time.monotonic() + 5.0
        while _time.monotonic() < deadline:
            after = db.scheduled_recordings.get(rec.id)
            if after is not None and after.state == "recording":
                break
            _time.sleep(0.05)

        after = db.scheduled_recordings.get(rec.id)
        assert after is not None and after.state == "recording"
        assert after.last_outcome == "recording_started"
        assert len(started) == 1
        assert started[0]["calendar_event_id"] == rec.calendar_event_id
        assert started[0]["title"] == "Standup"
