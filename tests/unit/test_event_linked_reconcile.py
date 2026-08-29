"""HS-147-03: Event-linked reconciliation -- the honest follow.

Proves the post-replace_projection reconciliation rules:
R1 (refresh in place), R2 (time-shift rebind), R3 (event removed cancel),
X1 (arming/recording never touched), the two-source isolation invariant,
the nearest-occurrence rule for recurring uids, and the
reconcile-vs-conductor interleave seam.
"""
from __future__ import annotations

import math
import time
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.calendar_ingest import CalendarEventCandidate, _projection_id
from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
from holdspeak.config import CalendarConfig, CalendarSource, Config
from holdspeak.db.core import Database, reset_database

# ── helpers ──────────────────────────────────────────────────────

FIXED_NOW = datetime(2026, 8, 29, 10, 0, 0, tzinfo=timezone.utc)
FIXED_NOW_EPOCH = FIXED_NOW.timestamp()

# ICS template: two events from source A, one from source B.
_ICS_TPL = (
    b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
    b"BEGIN:VEVENT\r\nUID:{uid}\r\nDTSTART:{start}\r\nDTEND:{end}\r\n"
    b"SUMMARY:{title}\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
)


def _ics(uid: str, start: str, end: str, title: str = "Event") -> bytes:
    """Build a minimal valid ICS with one VEVENT."""
    return _ICS_TPL.replace(b"{uid}", uid.encode()).replace(
        b"{start}", start.encode()
    ).replace(b"{end}", end.encode()).replace(b"{title}", title.encode())


def _ics_multi(events: list[dict[str, str]]) -> bytes:
    """Build a valid ICS with multiple VEVENTs."""
    lines = [b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"]
    for ev in events:
        lines.append(
            b"BEGIN:VEVENT\r\nUID:" + ev["uid"].encode() + b"\r\n"
            b"DTSTART:" + ev["start"].encode() + b"\r\n"
            b"DTEND:" + ev["end"].encode() + b"\r\n"
            b"SUMMARY:" + ev.get("title", "Event").encode() + b"\r\n"
            b"END:VEVENT\r\n"
        )
    lines.append(b"END:VCALENDAR\r\n")
    return b"".join(lines)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%SZ")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "reconcile-test.db")
    yield database
    reset_database()


def _arm_event(db: Database, event_id: str, uid: str, source_id: str) -> str:
    """Create an enabled idle schedule linked to a calendar event."""
    from holdspeak.services.scheduled_recording_service import ScheduledRecordingService
    from holdspeak.principals import Principal, PrincipalKind

    svc = ScheduledRecordingService(db, clock=lambda: FIXED_NOW)
    result = svc.create_schedule(
        Principal(PrincipalKind.OWNER, "test"),
        calendar_event_id=event_id,
    )
    return result["id"]


# ── AC-1: time-shifted event rebinds and fires at the NEW time ───


class TestTimeShiftRebind:
    """R2: a time shift mints a new projection id; the schedule follows."""

    def test_time_shift_rebinds_through_real_ingest(self, db: Database) -> None:
        """Two-source fixture: shift source A's event; source B untouched."""
        event_start = FIXED_NOW + timedelta(hours=2)
        event_end = FIXED_NOW + timedelta(hours=3)

        # Source A: one event
        ics_a_v1 = _ics("uid-a1", _iso(event_start), _iso(event_end), "Meeting A")
        # Source B: one event (untouched throughout)
        src_b_start = FIXED_NOW + timedelta(hours=4)
        src_b_end = FIXED_NOW + timedelta(hours=5)
        ics_b = _ics("uid-b1", _iso(src_b_start), _iso(src_b_end), "Meeting B")

        feeds: dict[str, bytes] = {"/a.ics": ics_a_v1, "/b.ics": ics_b}

        config = Config(calendar=CalendarConfig(sources=[
            CalendarSource(id="src-a", label="A", url="/a.ics", enabled=True),
            CalendarSource(id="src-b", label="B", url="/b.ics", enabled=True),
        ]))

        conductor = CalendarIngestConductor(
            clock=lambda: FIXED_NOW_EPOCH,
            db_factory=lambda: db,
            source_reader=lambda url: feeds[url],
            config_loader=lambda: config,
        )
        # Initial refresh to populate projection
        conductor.refresh()

        events_a = [e for e in db.calendar_events.list_all() if e.source_id == "src-a"]
        events_b = [e for e in db.calendar_events.list_all() if e.source_id == "src-b"]
        assert len(events_a) == 1
        assert len(events_b) == 1

        # Arm both events
        sched_a_id = _arm_event(db, events_a[0].id, "uid-a1", "src-a")
        sched_b_id = _arm_event(db, events_b[0].id, "uid-b1", "src-b")

        old_event_id_a = events_a[0].id
        old_sched_a = db.scheduled_recordings.get(sched_a_id)
        assert old_sched_a is not None
        old_fire_at_a = old_sched_a.next_fire_at

        # Shift source A's event by 1 hour
        shifted_start = event_start + timedelta(hours=1)
        shifted_end = event_end + timedelta(hours=1)
        ics_a_v2 = _ics("uid-a1", _iso(shifted_start), _iso(shifted_end), "Meeting A Shifted")
        feeds["/a.ics"] = ics_a_v2

        # Re-refresh
        conductor.refresh()

        # Source A's schedule should be rebound to the new event
        sched_a = db.scheduled_recordings.get(sched_a_id)
        assert sched_a is not None
        assert sched_a.calendar_event_id != old_event_id_a, \
            "Schedule should have a NEW calendar_event_id after time shift"
        assert sched_a.title == "Meeting A Shifted"
        assert sched_a.enabled is True
        assert sched_a.state == "idle"

        # next_fire_at should be shifted_start - 60s
        expected_fire = (shifted_start - timedelta(seconds=60)).timestamp()
        assert sched_a.next_fire_at is not None
        assert abs(sched_a.next_fire_at - expected_fire) < 2

        # Duration should be 60 min (1 hour event)
        assert sched_a.duration_minutes == 60

        # Source B's schedule should be completely untouched
        sched_b = db.scheduled_recordings.get(sched_b_id)
        assert sched_b is not None
        assert sched_b.state == "idle"
        assert sched_b.enabled is True
        assert sched_b.calendar_event_id == events_b[0].id


class TestEndTimeExtensionR1:
    """R1: an end-time-only change refreshes duration under the SAME id."""

    def test_end_time_extension_refreshes_duration(self, db: Database) -> None:
        event_start = FIXED_NOW + timedelta(hours=2)
        event_end = FIXED_NOW + timedelta(hours=3)  # 60 min
        ics_v1 = _ics("uid-ext", _iso(event_start), _iso(event_end), "Extended Event")

        feeds: dict[str, bytes] = {"/cal.ics": ics_v1}
        config = Config(calendar=CalendarConfig(sources=[
            CalendarSource(id="src-ext", label="Ext", url="/cal.ics", enabled=True),
        ]))
        conductor = CalendarIngestConductor(
            clock=lambda: FIXED_NOW_EPOCH,
            db_factory=lambda: db,
            source_reader=lambda url: feeds[url],
            config_loader=lambda: config,
        )
        conductor.refresh()

        events = db.calendar_events.list_all()
        assert len(events) == 1
        original_id = events[0].id

        sched_id = _arm_event(db, original_id, "uid-ext", "src-ext")
        sched = db.scheduled_recordings.get(sched_id)
        assert sched is not None
        assert sched.duration_minutes == 60

        # Extend end time by 30 minutes (same start -> same projection id)
        extended_end = event_end + timedelta(minutes=30)
        ics_v2 = _ics("uid-ext", _iso(event_start), _iso(extended_end), "Extended Event")
        feeds["/cal.ics"] = ics_v2

        conductor.refresh()

        # The projection id should be UNCHANGED (starts_at didn't move)
        events_after = db.calendar_events.list_all()
        assert len(events_after) == 1
        assert events_after[0].id == original_id

        # Duration should be refreshed to 90 min
        sched_after = db.scheduled_recordings.get(sched_id)
        assert sched_after is not None
        assert sched_after.calendar_event_id == original_id, \
            "R1: projection id should survive end-time-only changes"
        assert sched_after.duration_minutes == 90

    def test_title_change_refreshes_title_r1(self, db: Database) -> None:
        """A title-only change also triggers R1 refresh."""
        event_start = FIXED_NOW + timedelta(hours=2)
        event_end = FIXED_NOW + timedelta(hours=3)
        ics_v1 = _ics("uid-title", _iso(event_start), _iso(event_end), "Old Title")

        feeds: dict[str, bytes] = {"/cal.ics": ics_v1}
        config = Config(calendar=CalendarConfig(sources=[
            CalendarSource(id="src-t", label="T", url="/cal.ics", enabled=True),
        ]))
        conductor = CalendarIngestConductor(
            clock=lambda: FIXED_NOW_EPOCH,
            db_factory=lambda: db,
            source_reader=lambda url: feeds[url],
            config_loader=lambda: config,
        )
        conductor.refresh()

        events = db.calendar_events.list_all()
        sched_id = _arm_event(db, events[0].id, "uid-title", "src-t")

        # Change title only
        ics_v2 = _ics("uid-title", _iso(event_start), _iso(event_end), "New Title")
        feeds["/cal.ics"] = ics_v2
        conductor.refresh()

        sched = db.scheduled_recordings.get(sched_id)
        assert sched is not None
        assert sched.title == "New Title"
        assert sched.calendar_event_id == events[0].id  # Same id (R1)


# ── AC-2: removed event cancels, nothing fires ──────────────────


class TestEventRemovedR3:
    """R3: event removed from feed -> schedule cancelled with event_removed."""

    def test_removed_event_cancels_with_event_removed(self, db: Database) -> None:
        event_start = FIXED_NOW + timedelta(hours=2)
        event_end = FIXED_NOW + timedelta(hours=3)
        ics_v1 = _ics("uid-rm", _iso(event_start), _iso(event_end), "Doomed Meeting")

        feeds: dict[str, bytes] = {"/cal.ics": ics_v1}
        config = Config(calendar=CalendarConfig(sources=[
            CalendarSource(id="src-rm", label="Rm", url="/cal.ics", enabled=True),
        ]))
        conductor = CalendarIngestConductor(
            clock=lambda: FIXED_NOW_EPOCH,
            db_factory=lambda: db,
            source_reader=lambda url: feeds[url],
            config_loader=lambda: config,
        )
        conductor.refresh()

        events = db.calendar_events.list_all()
        sched_id = _arm_event(db, events[0].id, "uid-rm", "src-rm")

        # Remove the event (empty feed)
        feeds["/cal.ics"] = b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n"
        conductor.refresh()

        sched = db.scheduled_recordings.get(sched_id)
        assert sched is not None
        assert sched.state == "cancelled"
        assert sched.last_outcome == "event_removed"
        assert sched.enabled is False
        assert sched.next_fire_at is None

    def test_healthy_source_untouched_during_broken_source_refresh(
        self, db: Database,
    ) -> None:
        """A broken source's refresh does NOT touch another source's arms."""
        # Source A: event that will be removed
        start_a = FIXED_NOW + timedelta(hours=2)
        end_a = FIXED_NOW + timedelta(hours=3)
        ics_a = _ics("uid-a", _iso(start_a), _iso(end_a), "Source A")

        # Source B: healthy event
        start_b = FIXED_NOW + timedelta(hours=4)
        end_b = FIXED_NOW + timedelta(hours=5)
        ics_b = _ics("uid-b", _iso(start_b), _iso(end_b), "Source B")

        feeds: dict[str, bytes] = {"/a.ics": ics_a, "/b.ics": ics_b}
        config = Config(calendar=CalendarConfig(sources=[
            CalendarSource(id="src-a", label="A", url="/a.ics", enabled=True),
            CalendarSource(id="src-b", label="B", url="/b.ics", enabled=True),
        ]))
        conductor = CalendarIngestConductor(
            clock=lambda: FIXED_NOW_EPOCH,
            db_factory=lambda: db,
            source_reader=lambda url: feeds[url],
            config_loader=lambda: config,
        )
        conductor.refresh()

        events = db.calendar_events.list_all()
        event_a = next(e for e in events if e.source_id == "src-a")
        event_b = next(e for e in events if e.source_id == "src-b")

        sched_a_id = _arm_event(db, event_a.id, "uid-a", "src-a")
        sched_b_id = _arm_event(db, event_b.id, "uid-b", "src-b")

        # Remove source A's event
        feeds["/a.ics"] = b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n"
        conductor.refresh()

        # Source A's schedule should be cancelled
        sched_a = db.scheduled_recordings.get(sched_a_id)
        assert sched_a is not None
        assert sched_a.state == "cancelled"
        assert sched_a.last_outcome == "event_removed"

        # Source B's schedule must be completely untouched
        sched_b = db.scheduled_recordings.get(sched_b_id)
        assert sched_b is not None
        assert sched_b.state == "idle"
        assert sched_b.enabled is True
        assert sched_b.calendar_event_id == event_b.id


# ── AC-3: X1 — arming/recording rows survive hostile refresh ────


class TestX1ArmingRecordingImmunity:
    """X1: rows in arming or recording state are NEVER touched."""

    def test_arming_row_survives_event_removal(self, db: Database) -> None:
        start = FIXED_NOW + timedelta(hours=2)
        end = FIXED_NOW + timedelta(hours=3)
        ics_v1 = _ics("uid-x1", _iso(start), _iso(end), "Armed Meeting")

        feeds: dict[str, bytes] = {"/cal.ics": ics_v1}
        config = Config(calendar=CalendarConfig(sources=[
            CalendarSource(id="src-x1", label="X1", url="/cal.ics", enabled=True),
        ]))
        conductor = CalendarIngestConductor(
            clock=lambda: FIXED_NOW_EPOCH,
            db_factory=lambda: db,
            source_reader=lambda url: feeds[url],
            config_loader=lambda: config,
        )
        conductor.refresh()

        events = db.calendar_events.list_all()
        sched_id = _arm_event(db, events[0].id, "uid-x1", "src-x1")

        # Flip to arming state (simulating conductor)
        db.scheduled_recordings.set_state(sched_id, "arming")

        # Remove the event
        feeds["/cal.ics"] = b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n"
        conductor.refresh()

        # The arming row must NOT be touched (X1)
        sched = db.scheduled_recordings.get(sched_id)
        assert sched is not None
        assert sched.state == "arming", \
            f"X1 violated: arming row changed to '{sched.state}'"
        assert sched.enabled is True

    def test_recording_row_survives_event_removal(self, db: Database) -> None:
        start = FIXED_NOW + timedelta(hours=2)
        end = FIXED_NOW + timedelta(hours=3)
        ics_v1 = _ics("uid-x1r", _iso(start), _iso(end), "Recording Meeting")

        feeds: dict[str, bytes] = {"/cal.ics": ics_v1}
        config = Config(calendar=CalendarConfig(sources=[
            CalendarSource(id="src-x1r", label="X1R", url="/cal.ics", enabled=True),
        ]))
        conductor = CalendarIngestConductor(
            clock=lambda: FIXED_NOW_EPOCH,
            db_factory=lambda: db,
            source_reader=lambda url: feeds[url],
            config_loader=lambda: config,
        )
        conductor.refresh()

        events = db.calendar_events.list_all()
        sched_id = _arm_event(db, events[0].id, "uid-x1r", "src-x1r")

        # Flip to recording state
        db.scheduled_recordings.set_state(sched_id, "recording")

        # Remove the event
        feeds["/cal.ics"] = b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n"
        conductor.refresh()

        sched = db.scheduled_recordings.get(sched_id)
        assert sched is not None
        assert sched.state == "recording", \
            f"X1 violated: recording row changed to '{sched.state}'"
        assert sched.enabled is True

    def test_arming_row_survives_time_shift(self, db: Database) -> None:
        """X1 also holds for R2 (time shift): arming rows are not rebound."""
        start = FIXED_NOW + timedelta(hours=2)
        end = FIXED_NOW + timedelta(hours=3)
        ics_v1 = _ics("uid-x1s", _iso(start), _iso(end), "Shifting Armed")

        feeds: dict[str, bytes] = {"/cal.ics": ics_v1}
        config = Config(calendar=CalendarConfig(sources=[
            CalendarSource(id="src-x1s", label="X1S", url="/cal.ics", enabled=True),
        ]))
        conductor = CalendarIngestConductor(
            clock=lambda: FIXED_NOW_EPOCH,
            db_factory=lambda: db,
            source_reader=lambda url: feeds[url],
            config_loader=lambda: config,
        )
        conductor.refresh()

        events = db.calendar_events.list_all()
        sched_id = _arm_event(db, events[0].id, "uid-x1s", "src-x1s")
        old_event_id = events[0].id

        # Flip to arming
        db.scheduled_recordings.set_state(sched_id, "arming")

        # Shift the event
        shifted_start = start + timedelta(hours=1)
        shifted_end = end + timedelta(hours=1)
        feeds["/cal.ics"] = _ics("uid-x1s", _iso(shifted_start), _iso(shifted_end), "Shifted")
        conductor.refresh()

        sched = db.scheduled_recordings.get(sched_id)
        assert sched is not None
        assert sched.state == "arming"
        assert sched.calendar_event_id == old_event_id, \
            "X1: arming row's event id should NOT change during a time shift"


# ── AC-5: recurring-uid rebind picks nearest occurrence ──────────


class TestNearestOccurrenceRule:
    """R2 nearest: when a recurring uid has multiple occurrences, the
    schedule rebinds to the one whose starts_at is closest to the old one."""

    def test_recurring_uid_picks_nearest(self, db: Database) -> None:
        # Three occurrences of the same UID at different times
        base = FIXED_NOW + timedelta(hours=2)
        events_data = [
            {"uid": "uid-recur", "start": _iso(base), "end": _iso(base + timedelta(hours=1)), "title": "Recur 1"},
            {"uid": "uid-recur", "start": _iso(base + timedelta(days=1)), "end": _iso(base + timedelta(days=1, hours=1)), "title": "Recur 2"},
            {"uid": "uid-recur", "start": _iso(base + timedelta(days=7)), "end": _iso(base + timedelta(days=7, hours=1)), "title": "Recur 3"},
        ]
        ics_v1 = _ics_multi(events_data)

        feeds: dict[str, bytes] = {"/cal.ics": ics_v1}
        config = Config(calendar=CalendarConfig(sources=[
            CalendarSource(id="src-rec", label="Rec", url="/cal.ics", enabled=True),
        ]))
        conductor = CalendarIngestConductor(
            clock=lambda: FIXED_NOW_EPOCH,
            db_factory=lambda: db,
            source_reader=lambda url: feeds[url],
            config_loader=lambda: config,
        )
        conductor.refresh()

        # Arm the first occurrence
        all_events = db.calendar_events.list_all()
        first_occ = [e for e in all_events if e.source_id == "src-rec"]
        first_occ.sort(key=lambda e: e.starts_at)
        assert len(first_occ) == 3

        sched_id = _arm_event(db, first_occ[0].id, "uid-recur", "src-rec")

        # Shift the first occurrence by 30 minutes (keeps same uid)
        shifted_start = base + timedelta(minutes=30)
        events_v2 = [
            {"uid": "uid-recur", "start": _iso(shifted_start), "end": _iso(shifted_start + timedelta(hours=1)), "title": "Recur 1 shifted"},
            {"uid": "uid-recur", "start": _iso(base + timedelta(days=1)), "end": _iso(base + timedelta(days=1, hours=1)), "title": "Recur 2"},
            {"uid": "uid-recur", "start": _iso(base + timedelta(days=7)), "end": _iso(base + timedelta(days=7, hours=1)), "title": "Recur 3"},
        ]
        feeds["/cal.ics"] = _ics_multi(events_v2)
        conductor.refresh()

        sched = db.scheduled_recordings.get(sched_id)
        assert sched is not None
        assert sched.state == "idle"
        assert sched.enabled is True

        # Should rebind to the nearest occurrence (the shifted one, not day+1 or day+7)
        new_events = [e for e in db.calendar_events.list_all() if e.source_id == "src-rec"]
        new_events.sort(key=lambda e: e.starts_at)
        # The nearest to the old base should be the shifted start (30 min away)
        # not the day+1 occurrence (24h away)
        assert sched.calendar_event_id == new_events[0].id
        assert sched.title == "Recur 1 shifted"


# ── Reconcile-vs-conductor interleave seam ───────────────────────


class TestReconcileConductorInterleave:
    """An idle->arming flip during an ingest tick: prove no crash and no
    double-write.  The schedule was idle when the pre-replace snapshot
    ran, but flipped to arming between replace and reconcile.

    Since list_linked_for_source filters state='idle', the reconciler
    re-reads and the arming row is simply not in its working set.
    """

    def test_idle_to_arming_between_replace_and_reconcile(self, db: Database) -> None:
        start = FIXED_NOW + timedelta(hours=2)
        end = FIXED_NOW + timedelta(hours=3)
        ics_v1 = _ics("uid-race", _iso(start), _iso(end), "Race Event")

        feeds: dict[str, bytes] = {"/cal.ics": ics_v1}
        config = Config(calendar=CalendarConfig(sources=[
            CalendarSource(id="src-race", label="Race", url="/cal.ics", enabled=True),
        ]))

        # First refresh to populate
        conductor = CalendarIngestConductor(
            clock=lambda: FIXED_NOW_EPOCH,
            db_factory=lambda: db,
            source_reader=lambda url: feeds[url],
            config_loader=lambda: config,
        )
        conductor.refresh()

        events = db.calendar_events.list_all()
        sched_id = _arm_event(db, events[0].id, "uid-race", "src-race")

        # Remove the event from the feed (hostile refresh)
        feeds["/cal.ics"] = b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n"

        # Simulate the interleave: the conductor flips the schedule to
        # arming BETWEEN replace and reconcile.  We do this by patching
        # list_linked_for_source to flip the state after the pre-read
        # but before the post-replace reconcile query.
        original_list = db.scheduled_recordings.list_linked_for_source
        call_count = [0]

        def interleaving_list(source_id: str):
            call_count[0] += 1
            if call_count[0] == 2:
                # This is the reconcile's call: flip to arming first
                db.scheduled_recordings.set_state(sched_id, "arming")
            return original_list(source_id)

        db.scheduled_recordings.list_linked_for_source = interleaving_list  # type: ignore[assignment]

        # This should NOT crash
        conductor.refresh()

        # The schedule should still be arming (X1 protected it)
        sched = db.scheduled_recordings.get(sched_id)
        assert sched is not None
        assert sched.state == "arming", \
            f"Interleave: expected arming, got '{sched.state}'"
        assert sched.enabled is True


# ── Reconcile idempotence (D3b) ──────────────────────────────────


class TestReconcileIdempotence:
    """D3b: reconciliation is idempotent; running it twice produces the
    same result."""

    def test_double_reconcile_is_idempotent(self, db: Database) -> None:
        start = FIXED_NOW + timedelta(hours=2)
        end = FIXED_NOW + timedelta(hours=3)
        ics_v1 = _ics("uid-idem", _iso(start), _iso(end), "Idempotent")

        feeds: dict[str, bytes] = {"/cal.ics": ics_v1}
        config = Config(calendar=CalendarConfig(sources=[
            CalendarSource(id="src-idem", label="Idem", url="/cal.ics", enabled=True),
        ]))
        conductor = CalendarIngestConductor(
            clock=lambda: FIXED_NOW_EPOCH,
            db_factory=lambda: db,
            source_reader=lambda url: feeds[url],
            config_loader=lambda: config,
        )
        conductor.refresh()

        events = db.calendar_events.list_all()
        sched_id = _arm_event(db, events[0].id, "uid-idem", "src-idem")

        # Remove event
        feeds["/cal.ics"] = b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n"
        conductor.refresh()

        sched1 = db.scheduled_recordings.get(sched_id)
        assert sched1 is not None
        assert sched1.state == "cancelled"

        # Refresh again: should not crash; the schedule is already
        # cancelled+disabled so list_linked_for_source won't return it.
        conductor.refresh()

        sched2 = db.scheduled_recordings.get(sched_id)
        assert sched2 is not None
        assert sched2.state == "cancelled"
        assert sched2.last_outcome == "event_removed"
