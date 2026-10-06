"""Old zoneless stamps and new UTC stamps compare as instants (2026-10-05).

Before the aware-time change most writers stored ``datetime.now().isoformat()``,
a bare stamp on the hub's wall clock. New writers store UTC with its offset.
SQL compared the two as text: in Denver an old queued retry ran up to six
hours early. Two repairs, fenced here with the hub in America/Denver:

1. ``holdspeak/db/zoneless_stamps.py``: at open, once, every bare stamp in a
   time column becomes the same instant in UTC (DST-correct, values only).
2. The named queries compare ``julianday()`` on both sides, so a SQLite
   ``datetime('now')`` default (space form, UTC) and an ISO UTC stamp also
   compare as instants.

Each old row is minted the way the OLD code wrote it: the real producer makes
the row, then its stamp is set to ``datetime(...).isoformat()`` (naive local),
the exact expression the old writers used.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.db.zoneless_stamps import MILESTONE, zoneless_rows


@pytest.fixture(autouse=True)
def denver(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TZ", "America/Denver")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def _old_local(dt_local: datetime) -> str:
    """A stamp as the OLD naive writers stored it (``datetime.now().isoformat()``)."""
    return dt_local.replace(tzinfo=None).isoformat()


def _reopen(path: Path, db: Database) -> Database:
    """The next hub start on a desk the old code wrote: the repair has not run."""
    with db._connection() as conn:
        conn.execute("DELETE FROM milestones WHERE key = ?", (MILESTONE,))
    db.close()
    reset_database()
    return Database(path)


def _set(db: Database, sql: str, *params) -> None:
    with db._connection() as conn:
        conn.execute(sql, params)


def _local_now() -> datetime:
    return datetime.now().astimezone()


def _insert(db: Database, table: str, values: dict) -> None:
    """One raw row: the named values, and a filler for each other required column."""
    with db._connection() as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        row = dict(values)
        for column in conn.execute(f"PRAGMA table_info({table})"):
            name, declared, notnull, default, pk = column[1], str(column[2]).upper(), column[3], column[4], column[5]
            if name in row or pk or not notnull or default is not None:
                continue
            row[name] = 0 if declared in ("INTEGER", "REAL") else "x"
        conn.execute(
            f"INSERT INTO {table} ({', '.join(row)}) VALUES ({', '.join('?' for _ in row)})",
            tuple(row.values()),
        )


# -- 1. the backfill ----------------------------------------------------------

def test_the_backfill_leaves_no_zoneless_stamp_and_keeps_each_instant(tmp_path: Path) -> None:
    path = tmp_path / "hub.db"
    db = Database(path)
    db.milestones.mark("an old milestone")
    db.projects.create_project(project_id="p-old", name="Old room")
    winter = datetime(2026, 1, 15, 9, 30)   # MST, UTC-7
    summer = datetime(2026, 7, 15, 9, 30)   # MDT, UTC-6
    _set(db, "UPDATE milestones SET achieved_at = ? WHERE key = ?", _old_local(winter), "an old milestone")
    _set(db, "UPDATE projects SET created_at = ?, updated_at = ? WHERE id = ?",
         _old_local(summer), _old_local(winter), "p-old")
    with db._connection() as conn:
        assert zoneless_rows(conn), "the seed holds no old stamp"

    db = _reopen(path, db)
    with db._connection() as conn:
        assert zoneless_rows(conn) == {}
        achieved = conn.execute(
            "SELECT achieved_at FROM milestones WHERE key = ?", ("an old milestone",)
        ).fetchone()[0]
        created, updated = conn.execute(
            "SELECT created_at, updated_at FROM projects WHERE id = 'p-old'"
        ).fetchone()
    assert achieved == "2026-01-15T16:30:00+00:00"
    assert created == "2026-07-15T15:30:00+00:00"
    assert updated == "2026-01-15T16:30:00+00:00"

    # Runs once: a second open changes nothing.
    db.close()
    reset_database()
    again = Database(path)
    with again._connection() as conn:
        assert conn.execute(
            "SELECT created_at FROM projects WHERE id = 'p-old'"
        ).fetchone()[0] == created


def test_a_fresh_desk_has_the_milestone_and_no_zoneless_stamp(tmp_path: Path) -> None:
    db = Database(tmp_path / "fresh.db")
    with db._connection() as conn:
        assert conn.execute("SELECT 1 FROM milestones WHERE key = ?", (MILESTONE,)).fetchone()
        assert zoneless_rows(conn) == {}


# -- 2. the query families ----------------------------------------------------

def _plugin_job(db: Database) -> int:
    assert db.plugins.enqueue_plugin_run_job(
        meeting_id="m-old", window_id="w1", plugin_id="p", plugin_version="1",
        transcript_hash="h", idempotency_key="k-old",
    )
    return db.plugins.list_plugin_run_jobs()[0].id


def test_an_old_queued_plugin_retry_does_not_run_early(tmp_path: Path) -> None:
    path = tmp_path / "hub.db"
    db = Database(path)
    job_id = _plugin_job(db)
    later = _local_now() + timedelta(hours=3)  # due in three hours
    _set(db, "UPDATE plugin_run_jobs SET status='queued', requested_at=? WHERE id=?",
         _old_local(later), job_id)
    db = _reopen(path, db)

    summary = db.plugins.get_plugin_run_job_summary()
    assert (summary.queued_due_jobs, summary.scheduled_retry_jobs) == (0, 1)
    assert db.plugins.claim_next_plugin_run_job() is None


def test_an_old_queued_intel_retry_does_not_run_early(tmp_path: Path) -> None:
    from holdspeak.meeting_session import MeetingState, TranscriptSegment

    path = tmp_path / "hub.db"
    db = Database(path)
    db.meetings.save_meeting(MeetingState(
        id="m-old", started_at=datetime(2026, 10, 1, 10, 0), title="Old",
        segments=[TranscriptSegment(text="x", speaker="Me", start_time=0.0, end_time=1.0)],
    ))
    db.intel.enqueue_intel_job("m-old", transcript_hash="h")
    later = _local_now() + timedelta(hours=3)
    _set(db, "UPDATE intel_jobs SET status='queued', requested_at=? WHERE meeting_id='m-old'",
         _old_local(later))
    db = _reopen(path, db)

    summary = db.intel.get_intel_queue_summary()
    assert summary.queued_due_jobs == 0 and summary.scheduled_retry_jobs == 1, summary
    assert db.intel.claim_next_intel_job() is None


def test_a_sqlite_default_stamp_and_a_utc_stamp_compare_as_instants(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The space form (``datetime('now')``, UTC) sorted before ANY ISO stamp of the
    same day: a retry due at 15:00 UTC ran at 12:00. julianday reads both as
    instants."""
    import holdspeak.db.plugins as plugins_module

    db = Database(tmp_path / "hub.db")
    job_id = _plugin_job(db)
    _set(db, "UPDATE plugin_run_jobs SET status='queued', requested_at=? WHERE id=?",
         "2026-10-05 15:00:00", job_id)
    monkeypatch.setattr(plugins_module, "utc_now_iso", lambda: "2026-10-05T12:00:00+00:00")
    summary = db.plugins.get_plugin_run_job_summary()
    assert (summary.queued_due_jobs, summary.scheduled_retry_jobs) == (0, 1)
    assert db.plugins.claim_next_plugin_run_job() is None


def test_an_old_mesh_relay_job_is_not_expired_before_its_deadline(tmp_path: Path) -> None:
    path = tmp_path / "hub.db"
    db = Database(path)
    job = db.mesh_relay.enqueue(node="edge", user_prompt="hello", deadline_seconds=3600)
    deadline = _local_now() + timedelta(hours=1)
    _set(db, "UPDATE mesh_relay_jobs SET deadline_at=? WHERE id=?", _old_local(deadline), job.id)
    db = _reopen(path, db)

    db.mesh_relay._expire_overdue(datetime.now())
    assert db.mesh_relay.get(job.id).status == "queued"


def test_an_old_mesh_worker_seen_a_minute_ago_is_live(tmp_path: Path) -> None:
    path = tmp_path / "hub.db"
    db = Database(path)
    db.mesh_relay.touch_worker("edge")
    _set(db, "UPDATE mesh_workers SET last_seen=? WHERE node='edge'",
         _old_local(_local_now() - timedelta(minutes=1)))
    db = _reopen(path, db)
    assert "edge" in db.mesh_relay.live_nodes(window_seconds=300)


def test_an_old_browser_visit_keeps_its_instant(tmp_path: Path) -> None:
    """Browser visit times were naive UTC, not local: the backfill adds the
    offset without a shift, and the retention window reads them as instants."""
    path = tmp_path / "hub.db"
    db = Database(path)
    seen_utc = datetime.now(timezone.utc) - timedelta(minutes=30)
    db.activity.upsert_activity_record(
        source_browser="firefox", source_profile="work", source_path_hash="h",
        url="https://example.com/a", title="A", domain="example.com", visit_count=1,
        first_seen_at=seen_utc, last_seen_at=seen_utc, last_visit_raw="1",
    )
    _set(db, "UPDATE activity_records SET first_seen_at=?, last_seen_at=?",
         seen_utc.replace(tzinfo=None).isoformat(), seen_utc.replace(tzinfo=None).isoformat())
    db = _reopen(path, db)

    record = db.activity.list_activity_records(limit=5)[0]
    assert record.last_seen_at.astimezone(timezone.utc).replace(microsecond=0) == seen_utc.replace(microsecond=0)
    hour_ago = datetime.now() - timedelta(hours=1)
    assert db.activity.list_activity_records(since=hour_ago, limit=5)
    assert db.activity.delete_activity_records(older_than=hour_ago) == 0


def test_an_old_nudge_from_this_morning_counts_today(tmp_path: Path) -> None:
    from holdspeak.cadence.service import CadenceService
    from holdspeak.config import CadenceConfig

    path = tmp_path / "hub.db"
    db = Database(path)
    now = _local_now().replace(hour=12, minute=0, second=0, microsecond=0)
    morning = now.replace(hour=1)  # 01:00 local = 08:00 UTC, after local midnight (07:00 UTC)
    _insert(db, "cadence_nudges", {"created_at": _old_local(morning)})
    db = _reopen(path, db)
    assert CadenceService(db, CadenceConfig())._nudged_today(now) == 1


def test_an_old_decision_inside_the_brief_window_is_found(tmp_path: Path) -> None:
    from holdspeak.services.monday_brief_service import MondayBriefService

    path = tmp_path / "hub.db"
    db = Database(path)
    since_local = datetime(2026, 10, 2, 17, 0)        # Friday 17:00 local (bare, as the window passes it)
    decided = datetime(2026, 10, 4, 21, 0)            # Sunday 21:00 local = Monday 03:00 UTC
    week_end = datetime(2026, 10, 5, 2, 0, tzinfo=timezone.utc)  # Sunday 20:00 local
    _insert(db, "decision_records", {
        "id": "d-old", "decision_text": "Ship it", "deleted": 0,
        "created_at": _old_local(decided), "updated_at": _old_local(decided),
    })
    _insert(db, "decision_record_sources", {
        "record_id": "d-old", "source_type": "meeting", "source_ref": "m-old",
        "created_at": _old_local(decided),
    })
    db = _reopen(path, db)
    # Sunday 21:00 local is AFTER the window end (Sunday 20:00 local): not found.
    items = MondayBriefService(db)._collect_meeting_watch(
        "", week_end.isoformat(), None, decisions_since=since_local.isoformat(),
    )
    assert not [item for item in items if item.source_ref == "meeting_watch:decisions"], items
    # Window end Monday 04:00 UTC (Sunday 22:00 local): found.
    items = MondayBriefService(db)._collect_meeting_watch(
        "", datetime(2026, 10, 5, 4, 0, tzinfo=timezone.utc).isoformat(), None,
        decisions_since=since_local.isoformat(),
    )
    assert [item for item in items if item.source_ref == "meeting_watch:decisions"], items
    # A bare-local "since" (the window's own shape) is local time: a decision
    # at Friday 12:00 local is before Friday 17:00 local, so it is not new.
    _set(db, "UPDATE decision_records SET created_at=? WHERE id='d-old'",
         datetime(2026, 10, 2, 12, 0).astimezone().astimezone(timezone.utc).isoformat())
    items = MondayBriefService(db)._collect_meeting_watch(
        "", datetime(2026, 10, 5, 4, 0, tzinfo=timezone.utc).isoformat(), None,
        decisions_since=since_local.isoformat(),
    )
    assert not [item for item in items if item.source_ref == "meeting_watch:decisions"], items


def test_an_old_related_artifact_is_expanded_by_its_instant(tmp_path: Path) -> None:
    """Memory's one-hop expansion read each neighbour's time as text."""
    path = tmp_path / "hub.db"
    db = Database(path)
    db.projects.create_project(project_id="p1", name="Launch")
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings(id,started_at,title) VALUES ('m1',?,'Launch review')",
            (_old_local(datetime(2026, 2, 2, 9, 0)),),
        )
        conn.execute(
            "INSERT INTO segments(meeting_id,text,speaker,start_time,end_time) "
            "VALUES ('m1','The zephyr rollout starts Friday','Ada',0,4)"
        )
        conn.execute(
            "INSERT INTO meeting_projects(meeting_id,project_id,source,confidence) "
            "VALUES ('m1','p1','manual',1)"
        )
    db.plugins.record_artifact(
        artifact_id="a1", meeting_id="m1", artifact_type="memo",
        title="Rollout checklist", body_markdown="Owners and gates",
    )
    # 19:00 local on the 2nd = 02:00Z on the 3rd: a later UTC date than the
    # local window's text, and inside the window as an instant.
    _set(db, "UPDATE artifacts SET created_at=?, updated_at=? WHERE id='a1'",
         _old_local(datetime(2026, 2, 2, 19, 0)), _old_local(datetime(2026, 2, 2, 19, 0)))
    db = _reopen(path, db)

    start = datetime(2026, 2, 2, 0, 0).astimezone().isoformat()
    inside = datetime(2026, 2, 2, 20, 0).astimezone().isoformat()   # the window ends 20:00 local
    before = datetime(2026, 2, 2, 18, 0).astimezone().isoformat()   # the window ends 18:00 local
    refs = [hit.source_ref for hit in db.memory.search(
        "zephyr", project_id="p1", time_from=start, time_to=inside).hits]
    assert "meeting:m1" in refs and "artifact:a1" in refs, refs
    refs = [hit.source_ref for hit in db.memory.search(
        "zephyr", project_id="p1", time_from=start, time_to=before).hits]
    assert "meeting:m1" in refs and "artifact:a1" not in refs, refs


# -- 3. review of #872 (Astra): DST round trips, legacy sync rows, producers --

def _sync_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Database:
    import holdspeak.db as hsdb

    db = Database(tmp_path / "sync.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    return db


def _meeting_record(mid: str, start: str, end: str, lm: str) -> dict:
    return {
        "meta": {"id": mid, "kind": "meeting", "last_modified": lm, "deleted": False},
        "value": {
            "id": mid, "title": "Fold", "started_at": start, "ended_at": end,
            "segments": [{"text": "words", "speaker": "Me", "start_time": 0.0, "end_time": 1.0}],
            "capture_status": "finalized", "provenance": "native",
        },
    }


@pytest.mark.parametrize(("start", "end"), [
    ("2026-11-01T07:30:00Z", "2026-11-01T07:45:00Z"),  # the first 01:30 in Denver (MDT)
    ("2026-11-01T08:30:00Z", "2026-11-01T08:45:00Z"),  # the second 01:30 (MST)
    ("2026-03-08T09:30:00Z", "2026-03-08T09:45:00Z"),  # 03:30 MDT, just after the spring gap
])
def test_a_synced_meeting_keeps_its_instants_across_dst_load_and_save(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, start: str, end: str,
) -> None:
    """Astra's repro: 08:30Z / 08:45Z on 2026-11-01 were stored 07:30Z / 07:45Z,
    and a load and save moved the end before the start."""
    from holdspeak.services.sync_service import _merge_meetings

    db = _sync_db(tmp_path, monkeypatch)
    assert _merge_meetings(db, [_meeting_record("m-fold", start, end, end)]) == 1

    def stored() -> tuple[str, str]:
        with db._connection() as conn:
            row = conn.execute("SELECT started_at, ended_at FROM meetings WHERE id='m-fold'").fetchone()
        return row[0], row[1]

    want = (start.replace("Z", "+00:00"), end.replace("Z", "+00:00"))
    assert stored() == want
    # Load and save, twice: nothing moves.
    for _ in range(2):
        meeting = db.meetings.get_meeting("m-fold")
        from holdspeak.timestamps import aware
        assert aware(meeting.started_at) < aware(meeting.ended_at)
        db.meetings.save_meeting(meeting)
        assert stored() == want


def test_a_naive_wall_time_keeps_its_fold() -> None:
    from holdspeak.timestamps import parse_wall, utc_iso

    for stamp in ("2026-11-01T07:30:00+00:00", "2026-11-01T08:30:00+00:00",
                  "2026-03-08T09:30:00+00:00", "2026-07-01T12:00:00+00:00"):
        assert utc_iso(parse_wall(stamp)) == stamp


def _main_sync_parse_dt(value):
    """``_parse_dt`` exactly as main shipped it before this branch: an incoming
    ``...Z`` cut to its UTC wall clock, returned naive."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo is not None else value
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    return parsed.replace(tzinfo=None) if parsed.tzinfo is not None else parsed


def test_a_legacy_ipad_synced_meeting_is_not_shifted_by_the_backfill(tmp_path: Path) -> None:
    """Astra, #872: main's sync stored "2026-10-05T15:00:00Z" as bare 15:00 (UTC
    wall time); a backfill that reads bare as local made it 21:00+00:00."""
    path = tmp_path / "hub.db"
    db = Database(path)
    incoming = {"started_at": "2026-10-05T15:00:00Z", "ended_at": "2026-10-05T15:30:00Z",
                "sync_modified_at": "2026-10-05T15:31:00Z"}
    # Main's writer: the meetings row stored ``value.isoformat()`` of the parsed time.
    stored = {k: _main_sync_parse_dt(v).isoformat() for k, v in incoming.items()}
    _insert(db, "meetings", {"id": "m-ipad", "title": "iPad capture", **stored})
    db.plugins.record_artifact(
        artifact_id="a-ipad", meeting_id="m-ipad", artifact_type="memo",
        title="Synced", body_markdown="x",
        updated_at=_main_sync_parse_dt("2026-10-05T15:40:00Z").isoformat(),
    )
    db = _reopen(path, db)
    with db._connection() as conn:
        row = conn.execute(
            "SELECT started_at, ended_at, sync_modified_at FROM meetings WHERE id='m-ipad'"
        ).fetchone()
        artifact = conn.execute("SELECT updated_at FROM artifacts WHERE id='a-ipad'").fetchone()[0]
    assert tuple(row) == (stored["started_at"], stored["ended_at"], stored["sync_modified_at"])
    assert artifact == "2026-10-05T15:40:00"


def test_a_brief_and_a_draft_command_store_no_zoneless_stamp(tmp_path: Path) -> None:
    """Astra, #872: the Brief serialised its naive clock and the draft command
    claim stored ``datetime.now()``; both on a fresh desk after the repair."""
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.monday_brief_service import MondayBriefService
    from holdspeak.services.project_update_service import ProjectUpdateService

    db = Database(tmp_path / "fresh.db")
    owner = Principal(PrincipalKind.OWNER, "the-owner")
    MondayBriefService(db).generate(owner)
    db.projects.create_project(project_id="p-draft", name="Draft room")
    ProjectUpdateService(db, project_service=None)._claim_draft_command("cmd-1", "p-draft", "hash")
    with db._connection() as conn:
        assert zoneless_rows(conn) == {}
        assert conn.execute("SELECT COUNT(*) FROM monday_briefs").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM project_commands").fetchone()[0] == 1


def test_the_plugin_queue_names_the_earliest_retry_by_instant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Astra, #872: MIN(requested_at) as text picked '2026-10-05 15:00:00' over
    '2026-10-05T14:00:00+00:00'."""
    import holdspeak.db.plugins as plugins_module
    from holdspeak.timestamps import aware

    db = Database(tmp_path / "hub.db")
    for key in ("k-a", "k-b"):
        db.plugins.enqueue_plugin_run_job(
            meeting_id="m-q", window_id=key, plugin_id="p", plugin_version="1",
            transcript_hash="h", idempotency_key=key,
        )
    ids = sorted(job.id for job in db.plugins.list_plugin_run_jobs())
    for job_id, stamp in zip(ids, ("2026-10-05 15:00:00", "2026-10-05T14:00:00+00:00")):
        _set(db, "UPDATE plugin_run_jobs SET status='queued', last_error='x', requested_at=? WHERE id=?",
             stamp, job_id)
    monkeypatch.setattr(plugins_module, "utc_now_iso", lambda: "2026-10-05T12:00:00+00:00")
    summary = db.plugins.get_plugin_run_job_summary()
    assert aware(summary.next_retry_at) == datetime(2026, 10, 5, 14, 0, tzinfo=timezone.utc)


def test_the_intel_queue_names_the_earliest_retry_by_instant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import holdspeak.db.intel as intel_module
    from holdspeak.meeting_session import MeetingState, TranscriptSegment
    from holdspeak.timestamps import aware

    db = Database(tmp_path / "hub.db")
    for mid, stamp in (("m-a", "2026-10-05 15:00:00"), ("m-b", "2026-10-05T14:00:00+00:00")):
        db.meetings.save_meeting(MeetingState(
            id=mid, started_at=datetime(2026, 10, 1, 10, 0), title=mid,
            segments=[TranscriptSegment(text="x", speaker="Me", start_time=0.0, end_time=1.0)],
        ))
        db.intel.enqueue_intel_job(mid, transcript_hash="h")
        _set(db, "UPDATE intel_jobs SET status='queued', last_error='x', requested_at=? WHERE meeting_id=?",
             stamp, mid)
    monkeypatch.setattr(intel_module, "utc_now_iso", lambda: "2026-10-05T12:00:00+00:00")
    summary = db.intel.get_intel_queue_summary()
    assert aware(summary.next_retry_at) == datetime(2026, 10, 5, 14, 0, tzinfo=timezone.utc), summary
