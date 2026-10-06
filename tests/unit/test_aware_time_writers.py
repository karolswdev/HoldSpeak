"""Real writers store aware UTC stamps (the runtime half of the time census).

Hub in America/Denver. Each case drives a real repository on a real
``Database`` and reads the stored text back with SQL: the text must carry a
zero offset and name the moment of the write. The census
(``test_aware_time_census.py``) keeps a naive source from coming back; this
proves the stamps that reach disk.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import pytest

from holdspeak.timestamps import local_now, parse_stamp


@pytest.fixture()
def denver(monkeypatch):
    monkeypatch.setenv("TZ", "America/Denver")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


@pytest.fixture()
def db(tmp_path, denver):
    from holdspeak.db.core import Database

    return Database(tmp_path / "holdspeak.db")


def _assert_utc_now(text: str, label: str) -> None:
    stamp = datetime.fromisoformat(str(text))
    assert stamp.utcoffset() == timedelta(0), f"{label} is not a UTC stamp: {text!r}"
    age = abs((datetime.now(timezone.utc) - stamp).total_seconds())
    assert age < 120, f"{label} names another moment: {text!r}"


def _row(db, sql: str, *args):
    with db._connection() as conn:
        return conn.execute(sql, args).fetchone()


def test_meeting_save_stores_utc_and_loads_local_wall_time(db):
    from holdspeak.meeting_session import MeetingState

    started = local_now().replace(microsecond=0) - timedelta(minutes=1)
    db.meetings.save_meeting(MeetingState(
        id="m-utc", started_at=started, ended_at=started + timedelta(seconds=30),
        title="Ledger cutover sync", segments=[],
    ))
    row = _row(db, "SELECT started_at, ended_at FROM meetings WHERE id = 'm-utc'")
    _assert_utc_now(row["started_at"], "meetings.started_at")
    _assert_utc_now(row["ended_at"], "meetings.ended_at")
    loaded = db.meetings.get_meeting("m-utc")
    # Repositories hand out the same instant as naive hub-local wall time
    # (the in-memory convention every model and face reads).
    assert loaded.started_at == started.replace(tzinfo=None)
    assert loaded.started_at.tzinfo is None
    assert loaded.duration == 30


def test_a_legacy_naive_meeting_start_is_stored_as_its_utc_instant(db):
    from holdspeak.meeting_session import MeetingState

    wall = datetime(2026, 10, 5, 21, 32)  # 21:32 Denver (MDT, -06:00)
    db.meetings.save_meeting(MeetingState(id="m-naive", started_at=wall, title="t", segments=[]))
    row = _row(db, "SELECT started_at FROM meetings WHERE id = 'm-naive'")
    assert row["started_at"] == "2026-10-06T03:32:00+00:00"


def test_an_old_bare_row_still_reads_as_local_time(db):
    stamp = parse_stamp("2026-10-05T21:32:00")
    assert stamp.utcoffset() == timedelta(hours=-6)
    assert stamp.astimezone(timezone.utc).hour == 3
    assert parse_stamp("2026-10-05 21:32:00").utcoffset() == timedelta(hours=-6)
    assert parse_stamp("2026-10-05 21:32:00").astimezone(timezone.utc).hour == 21


def test_journal_project_correction_milestone_cadence_stamps_are_utc(db):
    from holdspeak.cadence.models import OpenLoop

    entry = db.dictation_journal.record(source="dictation", transcript="hi", final_text="hi")
    entry_id = getattr(entry, "id", entry)
    row = _row(db, "SELECT created_at FROM dictation_journal WHERE id = ?", entry_id)
    _assert_utc_now(row["created_at"], "dictation_journal.created_at")

    db.projects.create_project(project_id="p-utc", name="Ledger")
    row = _row(db, "SELECT created_at, updated_at FROM projects WHERE id = 'p-utc'")
    _assert_utc_now(row["created_at"], "projects.created_at")
    _assert_utc_now(row["updated_at"], "projects.updated_at")

    db.dictation_corrections.record_correction(kind="text", gist="kestrel", value="Kestrel")
    row = _row(db, "SELECT created_at FROM dictation_corrections ORDER BY id DESC LIMIT 1")
    _assert_utc_now(row["created_at"], "dictation_corrections.created_at")

    _assert_utc_now(db.milestones.mark("time.census"), "milestones.achieved_at")

    db.cadence.upsert_loop(OpenLoop(source_type="meeting_action", source_id="a1", title="Ship"))
    row = _row(db, "SELECT created_at, updated_at FROM cadence_loops WHERE source_id = 'a1'")
    _assert_utc_now(row["created_at"], "cadence_loops.created_at")
    _assert_utc_now(row["updated_at"], "cadence_loops.updated_at")


def test_intel_queue_stamps_are_utc(db):
    from holdspeak.meeting_session import MeetingState

    db.meetings.save_meeting(MeetingState(
        id="m-q", started_at=local_now(), title="t", segments=[],
    ))
    db.intel.enqueue_intel_job("m-q", transcript_hash="h1")
    row = _row(db, "SELECT requested_at, updated_at FROM intel_jobs WHERE meeting_id = 'm-q'")
    _assert_utc_now(row["requested_at"], "intel_jobs.requested_at")
    _assert_utc_now(row["updated_at"], "intel_jobs.updated_at")
