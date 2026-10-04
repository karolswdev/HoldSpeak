"""DST edges in America/Denver (review of #778, 2026-10-03).

1. A schedule's next fire is never in the past in the repeated hour, and a
   wall time inside the spring gap fires at the first valid instant after it.
2. A new artifact's stamp carries its offset, so the repeated hour cannot
   make it one hour old; an old bare local stamp still reads as local time.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from holdspeak.cron import next_cron_fire, next_cron_fire_in_zone

DENVER = ZoneInfo("America/Denver")
MDT = timezone(timedelta(hours=-6))
MST = timezone(timedelta(hours=-7))


def _fire(cron: str, now: datetime) -> datetime:
    epoch = next_cron_fire_in_zone(cron, "America/Denver", now_epoch=now.timestamp())
    assert epoch is not None
    assert epoch > now.timestamp(), "the next fire is in the past"
    return datetime.fromtimestamp(epoch, tz=timezone.utc)


def test_fold_second_pass_never_schedules_into_the_past():
    # 2026-11-01 01:15 MST: the second 01:15. The first 01:30 (MDT) is gone.
    now = datetime(2026, 11, 1, 1, 15, tzinfo=MST)
    assert _fire("30 1 * * *", now) == datetime(2026, 11, 1, 1, 30, tzinfo=MST)


def test_fold_first_pass_takes_the_first_occurrence():
    now = datetime(2026, 11, 1, 1, 15, tzinfo=MDT)
    assert _fire("30 1 * * *", now) == datetime(2026, 11, 1, 1, 30, tzinfo=MDT)


def test_fold_after_both_passes_goes_to_the_next_day():
    now = datetime(2026, 11, 1, 1, 45, tzinfo=MST)
    assert _fire("30 1 * * *", now) == datetime(2026, 11, 2, 1, 30, tzinfo=MST)


def test_gap_fires_at_the_first_valid_instant_after_it():
    # 2026-03-08: 02:00-02:59 does not exist in Denver. 02:30 fires at 03:00 MDT.
    now = datetime(2026, 3, 8, 1, 15, tzinfo=MST)
    assert _fire("30 2 * * *", now) == datetime(2026, 3, 8, 3, 0, tzinfo=MDT)


def test_gap_does_not_fire_twice_on_the_gap_day():
    now = datetime(2026, 3, 8, 3, 0, tzinfo=MDT)
    assert _fire("30 2 * * *", now) == datetime(2026, 3, 9, 2, 30, tzinfo=MDT)


def test_aware_after_in_the_zone_reads_the_same():
    now = datetime(2026, 11, 1, 1, 15, tzinfo=MST).astimezone(DENVER)
    epoch = next_cron_fire("30 1 * * *", after=now)
    assert epoch is not None and epoch > now.timestamp()


@pytest.fixture()
def denver(monkeypatch):
    monkeypatch.setenv("TZ", "America/Denver")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def test_a_new_artifact_stamp_carries_its_offset(tmp_path, denver):
    from holdspeak.db.core import Database
    from holdspeak.db.projections import ProjectionRepository
    from holdspeak.meeting_session import MeetingState

    db = Database(tmp_path / "holdspeak.db")
    start = datetime.now().replace(microsecond=0) - timedelta(minutes=40)
    db.meetings.save_meeting(MeetingState(
        id="m-dst", started_at=start, ended_at=start + timedelta(minutes=30),
        title="Ledger cutover sync", segments=[], intel_status="completed",
    ))
    before = datetime.now(timezone.utc)
    db.plugins.record_artifact(
        artifact_id="m-dst-notes", meeting_id="m-dst", artifact_type="notes",
        title="Notes", body_markdown="Dual-write is stable.", plugin_id="dst-test", status="draft",
    )
    with db._connection() as conn:
        stored = conn.execute("SELECT created_at, updated_at FROM artifacts WHERE id = 'm-dst-notes'").fetchone()
    for column in ("created_at", "updated_at"):
        stamp = datetime.fromisoformat(stored[column])
        assert stamp.utcoffset() is not None, f"{column} has no offset: {stored[column]}"
        assert abs((stamp - before).total_seconds()) < 60
    wire = ProjectionRepository._normalize_timestamp(stored["updated_at"])
    assert abs((datetime.fromisoformat(wire.replace("Z", "+00:00")) - before).total_seconds()) < 60


def test_normalizer_keeps_an_offset_stamp_exact_in_the_repeated_hour(denver):
    from holdspeak.db.projections import ProjectionRepository

    norm = ProjectionRepository._normalize_timestamp
    # The second 01:30 on 2026-11-01 in Denver is 08:30Z.
    assert norm("2026-11-01T08:30:00+00:00") == "2026-11-01T08:30:00Z"
    # An old bare stamp is the hub's local wall time (MDT here): 03:19Z next day.
    assert norm("2026-10-03T21:19:39") == "2026-10-04T03:19:39Z"
    # A SQLite stamp is UTC.
    assert norm("2026-10-04 03:19:39") == "2026-10-04T03:19:39Z"


# -- the upgrade: schedules minted before #778 (fire time computed in UTC) --

def _old_style_schedule(db, *, created: datetime, cron: str, one_shot: bool = True, **extra):
    """A row as the OLD service wrote it: the cron read in UTC at creation."""
    old_fire = next_cron_fire(cron, after=created.astimezone(timezone.utc))
    sched = db.scheduled_recordings.create(
        title="Cutover dry run", cron_expr=cron, tz="America/Denver",
        one_shot=one_shot, duration_minutes=30, enabled=True,
        next_fire_at=old_fire, **extra,
    )
    with db._connection() as conn:
        conn.execute(
            "UPDATE scheduled_recordings SET created_at = ? WHERE id = ?",
            (created.timestamp(), sched.id),
        )
    return sched.id, old_fire


def _boot_conductor(db, now: datetime):
    from unittest.mock import MagicMock

    from holdspeak.scheduled_recording_conductor import ScheduledRecordingConductor

    conductor = ScheduledRecordingConductor(
        clock=lambda: now.timestamp(), db_factory=lambda: db,
        start_meeting_fn=MagicMock(), stop_meeting_fn=MagicMock(),
        voice_floor_fn=lambda: None, countdown_seconds=0.01, tick_interval=0.01,
    )
    conductor._reconcile_on_boot()
    return conductor


def test_upgrade_keeps_an_old_style_0900_schedule_pending_at_0800(tmp_path):
    from holdspeak.db.core import Database

    db = Database(tmp_path / "holdspeak.db")
    monday = datetime(2026, 10, 5, 15, 0, tzinfo=MDT)
    nine = datetime(2026, 10, 6, 9, 0, tzinfo=MDT)
    sid, old_fire = _old_style_schedule(db, created=monday, cron="0 9 6 10 *")
    # The old code stored 09:00 UTC, which is 03:00 in Denver.
    assert datetime.fromtimestamp(old_fire, tz=MDT) == datetime(2026, 10, 6, 3, 0, tzinfo=MDT)

    _boot_conductor(db, datetime(2026, 10, 6, 8, 0, tzinfo=MDT))
    sched = db.scheduled_recordings.get(sid)
    assert sched.enabled is True and sched.state == "idle"
    assert sched.next_fire_at == nine.timestamp()

    # A second restart shifts nothing: still pending just before 09:00 local.
    _boot_conductor(db, datetime(2026, 10, 6, 8, 59, tzinfo=MDT))
    sched = db.scheduled_recordings.get(sid)
    assert sched.enabled is True and sched.state == "idle"
    assert sched.next_fire_at == nine.timestamp()


def test_upgrade_still_reports_a_fire_that_is_truly_past(tmp_path):
    from holdspeak.db.core import Database

    db = Database(tmp_path / "holdspeak.db")
    sid, _ = _old_style_schedule(
        db, created=datetime(2026, 10, 5, 15, 0, tzinfo=MDT), cron="0 9 6 10 *")
    _boot_conductor(db, datetime(2026, 10, 6, 10, 0, tzinfo=MDT))
    sched = db.scheduled_recordings.get(sid)
    assert sched.enabled is False and sched.last_outcome == "missed"


def test_upgrade_repairs_a_recurring_schedule_and_runs_once(tmp_path):
    from holdspeak.db.core import Database

    db = Database(tmp_path / "holdspeak.db")
    sid, old_fire = _old_style_schedule(
        db, created=datetime(2026, 10, 5, 15, 0, tzinfo=MDT), cron="0 9 * * *", one_shot=False)
    _boot_conductor(db, datetime(2026, 10, 5, 16, 0, tzinfo=MDT))
    nine = datetime(2026, 10, 6, 9, 0, tzinfo=MDT).timestamp()
    assert db.scheduled_recordings.get(sid).next_fire_at == nine

    # After the one-time repair, a row that looks old-style is not touched.
    db.scheduled_recordings.update(sid, next_fire_at=old_fire)
    _boot_conductor(db, datetime(2026, 10, 5, 17, 0, tzinfo=MDT))
    assert db.scheduled_recordings.get(sid).next_fire_at == old_fire


def test_upgrade_leaves_calendar_linked_and_utc_schedules_alone(tmp_path):
    from holdspeak.db.core import Database

    db = Database(tmp_path / "holdspeak.db")
    created = datetime(2026, 10, 5, 15, 0, tzinfo=MDT)
    linked, linked_fire = _old_style_schedule(
        db, created=created, cron="0 9 6 10 *", calendar_event_id="evt-1")
    utc_fire = next_cron_fire("0 9 6 10 *", after=created.astimezone(timezone.utc))
    utc = db.scheduled_recordings.create(
        title="UTC", cron_expr="0 9 6 10 *", tz="UTC", one_shot=True,
        duration_minutes=30, enabled=True, next_fire_at=utc_fire)
    _boot_conductor(db, datetime(2026, 10, 5, 16, 0, tzinfo=MDT))
    assert db.scheduled_recordings.get(linked).next_fire_at == linked_fire
    assert db.scheduled_recordings.get(utc.id).next_fire_at == utc_fire
