"""Tests for the persistent Monday Brief generation model."""
from __future__ import annotations

import datetime
import json
import re
import sys
import time
import uuid
from datetime import datetime as datetime_day
from datetime import datetime as datetime_itself
from datetime import timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.testclient import TestClient

import holdspeak.db as hsdb
import holdspeak.services.observer as observer_module
from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.db.core import Database, reset_database
from holdspeak.delivery import follow_through
from holdspeak.mcp import tools
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.people.keys import MemoryKeyStore
from holdspeak.people.store import EncryptedPeopleStore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition
from holdspeak.runtime.cadence import CadenceMixin
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.document_sources import render_document
from holdspeak.services.errors import NotFound
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.gate_service import GateService
from holdspeak.services.monday_brief_service import (
    BriefItem,
    MondayBriefService,
    _sanitize_detail,
    brief_period_label,
    brief_title,
)
from holdspeak.services.people_service import PeopleService
from holdspeak.services.project_service import ProjectService
from holdspeak.services.sqlite_observer import SQLiteObserver
from holdspeak.timestamps import parse_stamp
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_decisions_router, build_primitives_router
from holdspeak.web.routes import monday_brief as brief_routes
from tests.unit.brief_rule_stub import quiet_needs_you  # noqa: F401  (a fixture)
from tests.unit.test_agent_hand import OWNER as OWNER_day
from tests.unit.test_agent_hand import PROJECT
from tests.unit.test_conductor_k4_follow_through import _launch, _status
from tests.unit.test_conductor_k4_follow_through import db as db_day
from tests.unit.test_factory_launch import T0
from tests.unit.test_philo6_02_brief_truth import EVENTS_AT, GENERATED
from tests.unit.test_philo6_02_brief_truth import OWNER as OWNER_record
from tests.unit.test_philo15_17_merge_reaches_update import ViewGh


def _insert_pipeline_event(
    service,
    *,
    event_id,
    timestamp,
    service_name,
    method,
    correlation_id="",
    args_summary="{}",
    error=None,
):
    with service._db._connection() as conn:
        conn.execute(
            """INSERT INTO pipeline_events
               (event_id, timestamp, service, method, principal_kind, args_summary,
                correlation_id, error)
               VALUES (?, ?, ?, ?, 'test', ?, ?, ?)""",
            (
                event_id,
                timestamp,
                service_name,
                method,
                args_summary,
                correlation_id,
                error,
            ),
        )


def _utc_timestamp(day, hour=12):
    return datetime.datetime(2026, 8, day, hour, tzinfo=datetime.UTC).timestamp()


def test_compute_window_on_monday_starts_previous_friday(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    now = datetime.datetime(2026, 8, 3, 9, 30)

    period_start, period_end = service.compute_window(now)

    assert period_start == datetime.datetime(2026, 7, 31, 0)
    assert period_end == now


def test_compute_window_on_wednesday_starts_previous_day(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    now = datetime.datetime(2026, 8, 5, 9, 30)

    period_start, period_end = service.compute_window(now)

    assert period_start == datetime.datetime(2026, 8, 4, 0)  # PHILO-17: 00:00 of the previous workday
    assert period_end == now


def test_compute_window_preserves_timezone_across_dst(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    eastern = ZoneInfo("America/New_York")
    now = datetime.datetime(2026, 3, 9, 9, 30, tzinfo=eastern)

    period_start, period_end = service.compute_window(now)

    assert period_start == datetime.datetime(2026, 3, 6, 0, tzinfo=eastern)
    assert period_start.utcoffset() == datetime.timedelta(hours=-5)
    assert period_end.utcoffset() == datetime.timedelta(hours=-4)


def test_generate_creates_empty_brief(tmp_path, quiet_needs_you):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    now = datetime.datetime(2026, 8, 3, 9, 30)

    brief = service.generate(None, now=now)

    # A naive (hub-local) clock's window is stored as the same instant in UTC.
    assert datetime.datetime.fromisoformat(brief.period_start) == datetime.datetime(2026, 7, 31, 0, 0).astimezone()
    assert datetime.datetime.fromisoformat(brief.period_end) == now.astimezone()
    assert brief.sections == {
        "this_week": [],
        "changed": [],
        "broke": [],
        "waiting": [],
        "decisions": [],
    }
    assert brief.is_empty is True


def test_generate_is_idempotent_for_same_day(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))

    first = service.generate(None, now=datetime.datetime(2026, 8, 3, 9, 30))
    second = service.generate(None, now=datetime.datetime(2026, 8, 3, 15, 45))

    assert second.id == first.id
    with service._db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM monday_briefs").fetchone()[0] == 1


def test_get_latest_returns_most_recent_brief(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    earlier = service.generate(None, now=datetime.datetime(2026, 8, 3, 9, 30))
    later = service.generate(None, now=datetime.datetime(2026, 8, 4, 9, 30))

    assert service.get_latest(None).id == later.id
    assert later.id != earlier.id


def test_generate_collects_write_operations_as_persisted_changes(tmp_path, monkeypatch, quiet_needs_you):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    monkeypatch.setattr(service, "_collect_breakage", lambda *_: [], raising=False)
    monkeypatch.setattr(service, "_collect_waiting", lambda *_: [], raising=False)
    monkeypatch.setattr(service, "_collect_decisions", lambda *_: [], raising=False)
    _insert_pipeline_event(
        service,
        event_id="created-note",
        timestamp=_utc_timestamp(1),
        # PHILO-6-02 round 3: only a table row the record proves writes a line.
        service_name="DecisionRecordService",
        method="create",
        correlation_id="note-1",
        args_summary='{"title":"Plan"}',
    )

    brief = service.generate(
        None, now=datetime.datetime(2026, 8, 3, 9, 30, tzinfo=datetime.UTC)
    )

    assert [
        (item.section, item.text, item.source_ref) for item in brief.sections["changed"]
    ] == [("changed", "Decision recorded", "pipeline:note-1")]
    assert brief.headline == "1 thing changed."
    with service._db._connection() as conn:
        assert (
            conn.execute("SELECT COUNT(*) FROM monday_brief_items").fetchone()[0] == 1
        )


def test_collect_changes_excludes_read_only_operations(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    for event_id, method in (("list", "list_notes"), ("get", "get_note")):
        _insert_pipeline_event(
            service,
            event_id=event_id,
            timestamp=_utc_timestamp(1),
            service_name="NoteService",
            method=method,
        )

    items, ledger = service._collect_changes(
        "2026-08-01T00:00:00+00:00", "2026-08-02T00:00:00+00:00"
    )
    assert items == []
    assert ledger.operations == 0


def test_collect_changes_collapses_a_correlated_retry(tmp_path):
    """PHILO-6-02 round 3: the real correlated shape. A correlation is set by
    the OUTERMOST observed call (``observer.py``), so a retry inside one
    operation sits under the parent that STARTED first; the operation is one
    line, from that parent."""
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    for event_id, timestamp, method, error in (
        ("parent", _utc_timestamp(1, 12), "create_from_desk", None),
        ("first-attempt", _utc_timestamp(1, 12) + 1, "create", "connection reset"),
        ("retry", _utc_timestamp(1, 12) + 10, "create", None),
    ):
        _insert_pipeline_event(
            service,
            event_id=event_id,
            timestamp=timestamp,
            service_name="DecisionRecordService",
            method=method,
            correlation_id="run-1",
            args_summary='{"desk_decision_id":"weekly"}' if method != "create" else "{}",
            error=error,
        )

    items, _ledger = service._collect_changes(
        "2026-08-01T00:00:00+00:00", "2026-08-02T00:00:00+00:00"
    )

    assert len(items) == 1
    assert items[0].text == "Decision recorded"
    assert items[0].source_ref == "pipeline:run-1"


def test_collect_changes_collapses_an_uncorrelated_failed_retry(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    for event_id, timestamp, error in (
        ("failed", _utc_timestamp(1, 12), "connection reset"),
        ("retry", _utc_timestamp(1, 12) + 10, None),
    ):
        _insert_pipeline_event(
            service,
            event_id=event_id,
            timestamp=timestamp,
            service_name="DecisionRecordService",
            method="create",
            args_summary='{"source_id":"weekly"}',
            error=error,
        )

    items, _ledger = service._collect_changes(
        "2026-08-01T00:00:00+00:00", "2026-08-02T00:00:00+00:00"
    )

    assert len(items) == 1
    assert items[0].source_ref == "pipeline-event:failed"


def test_collect_changes_excludes_events_outside_the_window(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    _insert_pipeline_event(
        service,
        event_id="outside",
        timestamp=_utc_timestamp(3),
        service_name="NoteService",
        method="update_note",
    )

    items, ledger = service._collect_changes(
        "2026-08-01T00:00:00+00:00", "2026-08-02T00:00:00+00:00"
    )
    assert items == []
    assert ledger.operations == 0


def test_collect_changes_returns_no_items_for_an_empty_window(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))

    items, ledger = service._collect_changes(
        "2026-08-01T00:00:00+00:00", "2026-08-02T00:00:00+00:00"
    )
    assert items == []
    assert ledger.operations == 0


def _brief_item(section, item_id, *, priority=0):
    return BriefItem(
        id=item_id,
        section=section,
        text=item_id,
        priority=priority,
    )


def test_compose_headline_mentions_each_populated_section(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    sections = {
        "changed": [_brief_item("changed", "change")],
        "broke": [_brief_item("broke", "break")],
        "waiting": [_brief_item("waiting", "wait")],
        "decisions": [_brief_item("decisions", "decision")],
    }

    headline, composed = service._compose(sections)

    assert headline == "1 thing changed, 1 thing broke, 1 thing waiting, 1 decision waiting."
    assert all(composed[section] for section in sections)


def test_compose_headline_is_specific_to_the_populated_section(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))

    headline, composed = service._compose(
        {
            "changed": [],
            "broke": [_brief_item("broke", "break-1"), _brief_item("broke", "break-2")],
            "waiting": [],
            "decisions": [],
        }
    )

    assert headline == "2 things broke."
    assert composed["changed"] == []
    assert composed["waiting"] == []
    assert composed["decisions"] == []


def test_compose_empty_brief_has_honest_headline(tmp_path, quiet_needs_you):
    service = MondayBriefService(Database(tmp_path / "brief.db"))

    headline, sections = service._compose({})

    assert headline == "No changes"
    assert sections == {"this_week": [], "changed": [], "broke": [], "waiting": [], "decisions": []}
    brief = service.generate(None, now=datetime.datetime(2026, 8, 3, 9, 30))
    assert brief.headline == "No changes"
    assert brief.is_empty is True


def test_compose_sorts_items_within_each_section_by_priority(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))

    _, sections = service._compose(
        {
            "changed": [
                _brief_item("changed", "low", priority=1),
                _brief_item("changed", "high", priority=3),
                _brief_item("changed", "middle", priority=2),
            ]
        }
    )

    assert [item.id for item in sections["changed"]] == ["high", "middle", "low"]


def test_compose_headline_is_deterministic(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    sections = {
        "changed": [_brief_item("changed", "change", priority=1)],
        "broke": [_brief_item("broke", "break", priority=2)],
        "waiting": [],
        "decisions": [],
    }

    first_headline, first_sections = service._compose(sections)
    second_headline, second_sections = service._compose(sections)

    assert first_headline == second_headline
    assert first_sections == second_sections


# ── PHILO-17: the lookback opens at 00:00; a stale brief is said so ─────────


def test_yesterdays_morning_meeting_is_inside_the_window(tmp_path):
    """The walker's 10:00 meeting yesterday was outside a 17:00 window."""
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    now = datetime.datetime(2026, 10, 10, 9, 0)  # Saturday
    start, _end = service.compute_window(now)
    assert start == datetime.datetime(2026, 10, 9, 0, 0)
    assert start <= datetime.datetime(2026, 10, 9, 10, 0)


def _stale_service(tmp_path, clock):
    db = Database(tmp_path / "stale.db")
    return db, MondayBriefService(db, clock=lambda: clock["now"])


def test_a_brief_is_stale_after_a_new_meeting_decision_or_engine(tmp_path, monkeypatch, quiet_needs_you):
    from holdspeak.services import inference_assignment_service
    from tests.unit.test_hs172_loop_wire import assign_meeting_engine

    # Start at midnight and advance one clock for the brief and every event.
    # The real assignment producer must stamp this clock too, not wall time.
    base = datetime.datetime(2026, 10, 17, 0, 0, tzinfo=ZoneInfo("America/Denver"))
    clock = {"now": base}
    monkeypatch.setattr(inference_assignment_service, "_now", lambda: clock["now"].astimezone(datetime.UTC).isoformat())
    db, service = _stale_service(tmp_path, clock)
    brief = service.generate(None, now=clock["now"])
    assert service.is_stale(brief) is False

    clock["now"] = base + datetime.timedelta(minutes=5)
    meeting_at = clock["now"].isoformat()
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, ended_at, title, duration_seconds, intel_status, capture_status,"
            " created_at, updated_at) VALUES ('m-new', ?, ?, 'Standup', 60, 'disabled', 'finalized', ?, ?)",
            (meeting_at, meeting_at, meeting_at, meeting_at),  # the row's durable times (Astra r1/r2)
        )
    assert service.is_stale(brief) is True

    clock["now"] = base + datetime.timedelta(minutes=10)
    brief = service.generate(None, now=clock["now"])
    assert service.is_stale(brief) is False
    clock["now"] = base + datetime.timedelta(minutes=15)
    decided_at = clock["now"].isoformat()
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO decision_records (id, decision_text, rationale, source_type, source_id, created_at, updated_at) "
            "VALUES ('dr-new', 'Ship it', '', 'decision', 'd1', ?, ?)", (decided_at, decided_at),
        )
    assert service.is_stale(brief) is True

    clock["now"] = base + datetime.timedelta(minutes=20)
    brief = service.generate(None, now=clock["now"])
    assert service.is_stale(brief) is False
    clock["now"] = base + datetime.timedelta(minutes=25)
    assign_meeting_engine(db)
    with db._connection() as conn:
        assigned_at = conn.execute("SELECT updated_at FROM inference_assignment_heads").fetchone()[0]
    assert parse_stamp(assigned_at) == clock["now"]
    assert parse_stamp(assigned_at) > parse_stamp(brief.generated_at)
    assert service.is_stale(brief) is True


def test_a_brief_from_an_earlier_day_is_stale(tmp_path, quiet_needs_you):
    clock = {"now": datetime.datetime(2026, 10, 9, 18, 0)}
    _db, service = _stale_service(tmp_path, clock)
    brief = service.generate(None, now=clock["now"])
    assert service.is_stale(brief) is False
    clock["now"] = datetime.datetime(2026, 10, 10, 8, 0)
    assert service.is_stale(brief) is True


def test_a_just_imported_meeting_is_in_the_rebuilt_brief_and_it_stays_fresh(tmp_path, monkeypatch, quiet_needs_you):
    """Astra r1 MUST 1, through the real import producer: a 60-minute
    transcript imported now ENDS now; the rebuilt brief holds it, and a
    reopen does not call it stale again."""
    from types import SimpleNamespace

    from holdspeak.meeting_import import import_transcript

    db = Database(tmp_path / "import-brief.db")
    service = MondayBriefService(db)
    path = tmp_path / "planning.vtt"
    path.write_text(
        "WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<v Priya>we plan the release\n\n"
        "00:59:00.000 --> 01:00:00.000\n<v Sam>that is all\n"
    )
    config = SimpleNamespace(meeting=SimpleNamespace(intel_enabled=False, intel_deferred_enabled=True))
    imported = import_transcript(path, db=db, config=config).state
    assert imported.ended_at <= datetime.datetime.now()  # never in the future

    brief = service.generate(None)  # the view's rebuild
    assert any(item.source_ref == f"meeting:{imported.id}" for item in brief.sections["changed"])
    reopened = service.get_latest(None)
    assert service.is_stale(reopened) is False


@pytest.fixture
def denver(monkeypatch):
    import time

    monkeypatch.setenv("TZ", "America/Denver")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


@pytest.mark.parametrize(
    ("wall", "friday", "friday_offset_h"),
    [
        # Autumn: Monday Nov 2 2026 is MST (-7); Friday Oct 30 00:00 was MDT (-6).
        (datetime.datetime(2026, 11, 2, 9, 30), datetime.date(2026, 10, 30), -6),
        # Spring: Monday Mar 9 2026 is MDT (-6); Friday Mar 6 00:00 was MST (-7).
        (datetime.datetime(2026, 3, 9, 9, 30), datetime.date(2026, 3, 6), -7),
    ],
)
def test_the_scheduled_clock_opens_the_window_at_local_midnight_across_dst(
    tmp_path, monkeypatch, denver, wall, friday, friday_offset_h,
):
    """Astra r1 MUST 3: the cadence passes ``local_now()`` (a FIXED offset).
    Friday 00:00 is resolved in the real local zone, not with Monday's offset."""
    import holdspeak.timestamps as timestamps

    class _Clock(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return wall if tz is None else wall.astimezone(tz)

    monkeypatch.setattr(timestamps, "datetime", _Clock)
    now = timestamps.local_now()  # the producer's own clock (runtime/cadence.py)
    assert isinstance(now.tzinfo, datetime.timezone)

    start, _end = MondayBriefService(Database(tmp_path / "dst.db")).compute_window(now)

    assert start.astimezone(ZoneInfo("America/Denver")).replace(tzinfo=None) == datetime.datetime.combine(
        friday, datetime.time(0, 0)
    )
    assert start.utcoffset() == datetime.timedelta(hours=friday_offset_h)


def test_a_desk_upload_with_no_start_lands_in_a_fresh_brief(tmp_path, quiet_needs_you, monkeypatch):
    """Astra r2 MUST 1, through the ACTUAL upload route: POST a 60-minute
    transcript with no start; the worker ends it at the import moment and
    persists that start; rebuild, reopen: the meeting is there, not stale."""
    import time

    from fastapi.testclient import TestClient

    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    reset_database()
    db = get_database(tmp_path / "upload.db")
    try:
        server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=lambda *_a, **_k: None, on_stop=lambda *_a, **_k: None, get_state=lambda: None,
            ),
            host="127.0.0.1",
        )
        client = TestClient(server.app)
        vtt = (
            "WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<v Priya>we plan the release\n\n"
            "00:59:00.000 --> 01:00:00.000\n<v Sam>that is all\n"
        )
        before = datetime.datetime.now()
        response = client.post(
            "/api/meetings/import", files={"file": ("planning.vtt", vtt.encode(), "text/vtt")},
        )
        assert response.status_code == 202, response.text
        meeting_id = response.json()["meeting_id"]
        deadline = time.time() + 15
        stored = None
        while time.time() < deadline:
            stored = db.meetings.get_meeting(meeting_id)
            if stored is not None and stored.segments and stored.ended_at is not None:
                break
            time.sleep(0.05)
        assert stored is not None and stored.segments and stored.ended_at, "the upload did not finish"
        # The persisted start is the resolved one: the meeting ended at the import.
        assert before - datetime.timedelta(seconds=1) <= stored.ended_at <= datetime.datetime.now()
        assert stored.started_at < before - datetime.timedelta(minutes=59)

        rebuilt = client.post("/api/brief/generate")
        assert rebuilt.status_code == 200, rebuilt.text
        refs = [item["source_ref"] for item in rebuilt.json()["sections"]["changed"]]
        assert f"meeting:{meeting_id}" in refs
        reopened = client.get("/api/brief/latest").json()
        assert reopened["stale"] is False
    finally:
        reset_database()


def test_stop_after_the_brief_makes_it_stale_and_the_rebuild_holds_the_meeting(tmp_path, quiet_needs_you):
    """Astra r2 MUST 2: Start persists the row, a brief made mid-recording
    leaves it out, Stop updates the row (created_at kept): the brief is stale,
    and the rebuild holds the meeting."""
    from holdspeak.meeting_session import MeetingState, TranscriptSegment

    db = Database(tmp_path / "stop.db")
    service = MondayBriefService(db)
    started = datetime.datetime.now() - datetime.timedelta(minutes=30)
    live = MeetingState(id="m-live", started_at=started, title="Design sync", segments=[])
    live.capture_status = "recording"
    db.meetings.save_meeting(live)  # Start

    import time

    time.sleep(1.1)  # the row times are whole seconds
    mid = service.generate(None)
    assert not any(item.source_ref == "meeting:m-live" for item in mid.sections["changed"])
    assert service.is_stale(mid) is False

    time.sleep(1.1)
    stopped = MeetingState(
        id="m-live", started_at=started, ended_at=datetime.datetime.now() - datetime.timedelta(seconds=1),
        title="Design sync", segments=[TranscriptSegment("Ship it.", "Me", 0.0, 1.0)],
    )
    stopped.capture_status = "finalized"
    db.meetings.save_meeting(stopped)  # Stop: same row, created_at kept

    assert service.is_stale(service.get_latest(None)) is True
    rebuilt = service.generate(None)
    assert any(item.source_ref == "meeting:m-live" for item in rebuilt.sections["changed"])


# ── from test_hs175_week_brief.py: HS-175-05: The week brief -- two-window design and new collectors. ──
#
# Proves:
# - compute_window UNCHANGED: lookback to the preceding close.
# - compute_lookahead: now to Sunday 23:59 (the THIS WEEK section).
# - Calendar events collector returns events in the week range.
# - Meeting watch collector returns decisions/commitments counts.
# - Daily fallback without a calendar (empty collector results).
# - The brief's totals are correct.


OWNER = Principal(PrincipalKind.OWNER, "test-owner")


@pytest.fixture()
def db(tmp_path):
    return Database(tmp_path / "test.db")


# ── compute_window (UNCHANGED) ─────────────────────────────────────
# The lookback is NOT widened. These tests confirm it stayed the same.
# Sep 2026 calendar:
#   Mon Tue Wed Thu Fri Sat Sun
#        1   2   3   4   5   6
#    7   8   9  10  11  12  13


class TestComputeWindowUnchanged:

    def test_monday_still_looks_back_to_friday(self, db):
        """On Monday Sep 7, period_start is Friday Sep 4 at 00:00 (PHILO-17)."""
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 7, 9, 30, 0)
        assert now.weekday() == 0  # Monday
        start, end = svc.compute_window(now)

        assert start == datetime.datetime(2026, 9, 4, 0, 0)
        assert end == now

    def test_wednesday_looks_back_to_tuesday(self, db):
        """On Wednesday Sep 2, period_start is Tuesday Sep 1 at 00:00 (PHILO-17)."""
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 2, 14, 30, 0)
        assert now.weekday() == 2  # Wednesday
        start, end = svc.compute_window(now)

        assert start == datetime.datetime(2026, 9, 1, 0, 0)
        assert end == now


# ── compute_lookahead (NEW) ─────────────────────────────────────────


class TestComputeLookahead:

    def test_wednesday_to_sunday(self, db):
        """On Wednesday Sep 2 2026, look-ahead extends to Sunday Sep 6."""
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 2, 14, 30, 0)
        assert now.weekday() == 2  # Wednesday
        start, end = svc.compute_lookahead(now)

        assert start == now
        assert end.weekday() == 6  # Sunday
        assert end.date() == datetime.date(2026, 9, 6)
        assert end.hour == 23 and end.minute == 59

    def test_monday_to_sunday(self, db):
        """On Monday Sep 7, look-ahead extends to Sunday Sep 13."""
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 7, 8, 0, 0)
        assert now.weekday() == 0
        _, end = svc.compute_lookahead(now)

        assert end.date() == datetime.date(2026, 9, 13)

    def test_sunday_to_same_sunday(self, db):
        """On Sunday Sep 6, the look-ahead end is Sunday Sep 6 23:59."""
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 6, 10, 0, 0)
        assert now.weekday() == 6  # Sunday
        _, end = svc.compute_lookahead(now)

        assert end.date() == datetime.date(2026, 9, 6)
        assert end.hour == 23

    def test_default_now_is_tz_aware(self, db):
        """When no `now` is passed, the default is tz-aware local time."""
        svc = MondayBriefService(db)
        start, end = svc.compute_lookahead()

        assert start.tzinfo is not None, "Default now should be tz-aware"
        assert end.tzinfo is not None, "End should inherit tzinfo from now"


# ── Calendar events collector ───────────────────────────────────────


class TestCollectCalendarEvents:

    def _seed_calendar_event(self, db, *, event_id=None, title="Standup",
                             starts_at="2026-09-03T10:00:00",
                             meeting_url=None, uid=None):
        eid = event_id or f"evt-{uuid.uuid4().hex[:8]}"
        uid_val = uid or f"uid-{uuid.uuid4().hex[:8]}"
        ends_at = starts_at[:11] + "11:00:00"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO calendar_events
                   (id, uid, title, starts_at, ends_at, last_seen_at,
                    subscription_revision, source_id, source_label)
                   VALUES (?, ?, ?, ?, ?, ?, 'rev1', 'src1', 'WORK')""",
                (eid, uid_val, title, starts_at, ends_at, 1000.0),
            )
        return eid

    def test_counts_events_in_range(self, db):
        svc = MondayBriefService(db)
        self._seed_calendar_event(db, title="Standup", starts_at="2026-09-01T10:00:00")
        self._seed_calendar_event(db, title="Review", starts_at="2026-09-03T14:00:00")
        # Event outside range (next week)
        self._seed_calendar_event(db, title="Next Week", starts_at="2026-09-14T10:00:00")

        items = svc._collect_calendar_events(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59",
            "2026-09-03T08:00:00",
        )

        total_items = [i for i in items if i.source_ref == "calendar:week"]
        assert len(total_items) == 1
        assert "2 meetings this week" in total_items[0].text
        assert total_items[0].section == "this_week"

    def test_next_event_after_now(self, db):
        svc = MondayBriefService(db)
        self._seed_calendar_event(db, title="Past Standup", starts_at="2026-09-01T10:00:00")
        self._seed_calendar_event(db, title="Upcoming Review", starts_at="2026-09-04T14:00:00")

        items = svc._collect_calendar_events(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59",
            "2026-09-03T08:00:00",
        )

        next_items = [i for i in items if i.text.startswith("Next:")]
        assert len(next_items) == 1
        assert "Upcoming Review" in next_items[0].text

    def test_empty_when_no_events(self, db):
        svc = MondayBriefService(db)
        items = svc._collect_calendar_events(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59",
            "2026-09-03T08:00:00",
        )
        assert items == []

    def test_armed_count(self, db):
        svc = MondayBriefService(db)
        eid = self._seed_calendar_event(db, title="Team Standup",
                                        starts_at="2026-09-04T10:00:00",
                                        meeting_url="https://teams.example.com/join")

        # Seed an armed scheduled recording linked to this event
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO scheduled_recordings
                   (id, title, cron_expr, enabled, next_fire_at, state,
                    calendar_event_id, calendar_uid, calendar_source_id,
                    created_at)
                   VALUES (?, 'Team Standup', '0 55 9 * * *', 1, ?, 'idle',
                           ?, 'uid1', 'src1', ?)""",
                (f"sr-{uuid.uuid4().hex[:8]}", time.time(),
                 eid, time.time()),
            )

        items = svc._collect_calendar_events(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59",
            "2026-09-03T08:00:00",
        )

        armed_items = [i for i in items if i.source_ref == "calendar:armed"]
        assert len(armed_items) == 1
        assert "1 armed" in armed_items[0].text


# ── Meeting watch collector ─────────────────────────────────────────


class TestCollectMeetingWatch:

    def _seed_decision_record(self, db, *, meeting_id, text="Decision",
                              created_at="2026-09-03T11:00:00"):
        rid = f"dr-{uuid.uuid4().hex[:8]}"
        sid = f"drs-{uuid.uuid4().hex[:8]}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decision_records
                   (id, decision_text, source_type, source_id, created_at, updated_at)
                   VALUES (?, ?, 'meeting', ?, ?, ?)""",
                (rid, text, meeting_id, created_at, created_at),
            )
            conn.execute(
                """INSERT INTO decision_record_sources
                   (id, record_id, source_type, source_ref, created_at)
                   VALUES (?, ?, 'meeting', ?, ?)""",
                (sid, rid, meeting_id, created_at),
            )
        return rid

    def _seed_commitment(self, db, *, due_at="2026-09-04", status="open"):
        cid = f"dc-{uuid.uuid4().hex[:8]}"
        did = f"d-{uuid.uuid4().hex[:8]}"
        aid = f"ai-{uuid.uuid4().hex[:8]}"
        art_id = f"art-{uuid.uuid4().hex[:8]}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decisions
                   (id, text, rationale, source_artifact_id, source_meeting_id,
                    lifecycle, project_key, decided_at)
                   VALUES (?, 'test', '', ?, '', 'recorded', '', datetime('now'))""",
                (did, art_id),
            )
            conn.execute(
                """INSERT INTO decision_commitments
                   (id, decision_id, action_item_id, owner, due_at, status, created_at, updated_at)
                   VALUES (?, ?, ?, 'karol', ?, ?, datetime('now'), datetime('now'))""",
                (cid, did, aid, due_at, status),
            )
        return cid

    def test_new_decisions(self, db):
        svc = MondayBriefService(db)
        mid = f"mtg-{uuid.uuid4().hex[:8]}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO meetings
                   (id, title, started_at, capture_status)
                   VALUES (?, 'Test', '2026-09-03T10:00:00', 'finalized')""",
                (mid,),
            )
        self._seed_decision_record(db, meeting_id=mid, created_at="2026-09-03T11:00:00")
        self._seed_decision_record(db, meeting_id=mid, created_at="2026-09-03T11:05:00")

        items = svc._collect_meeting_watch(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59",
            "2026-08-31T00:00:00",
        )

        decision_items = [i for i in items if "decision" in i.text.lower()]
        assert len(decision_items) == 1
        assert "2 new decisions" in decision_items[0].text

    def test_commitments_due_this_week(self, db):
        svc = MondayBriefService(db)
        self._seed_commitment(db, due_at="2026-09-02", status="open")
        self._seed_commitment(db, due_at="2026-09-04", status="open")
        # Commitment outside the week
        self._seed_commitment(db, due_at="2026-09-10", status="open")

        items = svc._collect_meeting_watch(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59",
            None,
        )

        due_items = [i for i in items if "commitment" in i.text.lower() and "due" in i.text.lower()]
        assert len(due_items) == 1
        assert "2 commitments due this week" in due_items[0].text

    def test_empty_when_no_data(self, db):
        svc = MondayBriefService(db)
        items = svc._collect_meeting_watch(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59", None,
        )
        assert items == []


# ── Integration: brief generation ───────────────────────────────────


class TestBriefGenerationThisWeek:

    def test_generate_lookback_unchanged(self, db):
        """The generated brief's lookback (period_start) is unchanged."""
        svc = MondayBriefService(db)
        # Thursday Sep 3 2026 -- lookback to Wednesday Sep 2 00:00 (PHILO-17)
        now = datetime.datetime(2026, 9, 3, 14, 0, 0)
        assert now.weekday() == 3  # Thursday
        brief = svc.generate(OWNER, now=now)

        start_dt = datetime.datetime.fromisoformat(brief.period_start)
        # Lookback: Thursday -> previous day 00:00 = Wednesday 00:00 (local;
        # a naive clock's window is stored as the same instant in UTC).
        assert start_dt == datetime.datetime(2026, 9, 2, 0, 0).astimezone()

    def test_sections_include_this_week(self, db):
        """The generated brief always has a this_week key in sections."""
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 3, 14, 0, 0)
        brief = svc.generate(OWNER, now=now)

        assert "this_week" in brief.sections
        assert isinstance(brief.sections["this_week"], list)

    def test_calendar_items_land_in_this_week(self, db):
        """Calendar event items go to this_week, not changed."""
        svc = MondayBriefService(db)
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO calendar_events
                   (id, uid, title, starts_at, ends_at, last_seen_at,
                    subscription_revision, source_id, source_label)
                   VALUES ('evt1', 'uid1', 'Standup',
                           '2026-09-04T10:00:00', '2026-09-04T11:00:00',
                           1000.0, 'rev1', 'src1', 'WORK')"""
            )

        now = datetime.datetime(2026, 9, 3, 14, 0, 0)
        brief = svc.generate(OWNER, now=now)

        tw = brief.sections["this_week"]
        cal_items = [i for i in tw if i.source_ref and "calendar" in i.source_ref]
        assert len(cal_items) > 0, "Calendar items should be in this_week section"

        changed = brief.sections["changed"]
        cal_in_changed = [i for i in changed if i.source_ref and "calendar" in i.source_ref]
        assert len(cal_in_changed) == 0, "Calendar items should NOT be in changed section"

    def test_meeting_watch_items_land_in_this_week(self, db):
        """Meeting watch (commitments due) items go to this_week."""
        svc = MondayBriefService(db)
        art_id = f"art-{uuid.uuid4().hex[:8]}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decisions
                   (id, text, rationale, source_artifact_id, source_meeting_id,
                    lifecycle, project_key, decided_at)
                   VALUES ('d1', 'test', '', ?, '', 'recorded', '', datetime('now'))""",
                (art_id,),
            )
            conn.execute(
                """INSERT INTO decision_commitments
                   (id, decision_id, action_item_id, owner, due_at, status,
                    created_at, updated_at)
                   VALUES ('dc1', 'd1', 'ai1', 'karol', '2026-09-04',
                           'open', datetime('now'), datetime('now'))"""
            )

        now = datetime.datetime(2026, 9, 3, 14, 0, 0)
        brief = svc.generate(OWNER, now=now)

        tw = brief.sections["this_week"]
        watch_items = [i for i in tw if i.source_ref and "meeting_watch" in i.source_ref]
        assert len(watch_items) > 0, "Meeting watch items should be in this_week"

    def test_headline_includes_meeting_count(self, db):
        """When calendar events exist, the headline includes meeting count."""
        svc = MondayBriefService(db)
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO calendar_events
                   (id, uid, title, starts_at, ends_at, last_seen_at,
                    subscription_revision, source_id, source_label)
                   VALUES ('evt1', 'uid1', 'Standup',
                           '2026-09-04T10:00:00', '2026-09-04T11:00:00',
                           1000.0, 'rev1', 'src1', 'WORK')"""
            )
            conn.execute(
                """INSERT INTO calendar_events
                   (id, uid, title, starts_at, ends_at, last_seen_at,
                    subscription_revision, source_id, source_label)
                   VALUES ('evt2', 'uid2', 'Review',
                           '2026-09-05T14:00:00', '2026-09-05T15:00:00',
                           1000.0, 'rev1', 'src1', 'WORK')"""
            )

        now = datetime.datetime(2026, 9, 3, 14, 0, 0)
        brief = svc.generate(OWNER, now=now)

        assert "2 meetings this week" in brief.headline

    def test_commitment_detail_includes_text_and_date(self, db):
        """Commitment due item carries the first commitment's text + date."""
        svc = MondayBriefService(db)
        art_id = f"art-{uuid.uuid4().hex[:8]}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decisions
                   (id, text, rationale, source_artifact_id, source_meeting_id,
                    lifecycle, project_key, decided_at)
                   VALUES ('d1', 'Ania owns the API spec', '', ?, '', 'recorded', '', datetime('now'))""",
                (art_id,),
            )
            conn.execute(
                """INSERT INTO decision_commitments
                   (id, decision_id, action_item_id, owner, due_at, status,
                    created_at, updated_at)
                   VALUES ('dc1', 'd1', 'ai1', 'karol', '2026-09-04',
                           'open', datetime('now'), datetime('now'))"""
            )

        items = svc._collect_meeting_watch(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59", None,
        )

        due_items = [i for i in items if i.source_ref == "meeting_watch:commitments_due"]
        assert len(due_items) == 1
        assert due_items[0].detail is not None
        assert "Ania owns the API spec" in due_items[0].detail
        assert "2026-09-04" in due_items[0].detail


# -- HS-175 counsel-on-built C11: the two windows as ruled -------------------
#
# - compute_window is byte-identical (its body digest is pinned).
# - the forward half reads [now, Sunday 23:59], never from Monday 00:00.
# - boundaries are UTC-normalised against the UTC-stored starts_at; a naive
#   local `now` (what the cadence and the route pass) is read as local.
# - an occurrence already recorded in the lookback is deduped out.
# - _compose counts calendar items as meetings / armed / due, never "watch items".



UTC = datetime.timezone.utc


def _seed_utc_event(db, eid: str, title: str, starts_at: str, *, uid: str | None = None) -> None:
    """Seed the production shape: starts_at/ends_at stored as UTC '+00:00'."""
    start = datetime.datetime.fromisoformat(starts_at)
    end = (start + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO calendar_events
               (id, uid, title, starts_at, ends_at, last_seen_at,
                subscription_revision, source_id, source_label)
               VALUES (?, ?, ?, ?, ?, 1000.0, 'rev1', 'src1', 'WORK')""",
            (eid, uid or f"uid-{eid}", title, starts_at, end),
        )


def _seed_recorded_meeting(db, mid: str, *, calendar_event_id: str, started_at: str, ended_at: str) -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO meetings (id, title, started_at, ended_at, capture_status, calendar_event_id)
               VALUES (?, 'Recorded', ?, ?, 'finalized', ?)""",
            (mid, started_at, ended_at, calendar_event_id),
        )


def _this_week(brief, ref: str):
    return [i for i in brief.sections["this_week"] if i.source_ref == ref]


class TestForwardHalfReadsFromNow:
    def test_monday_afternoon_counts_only_what_is_coming(self, db):
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 7, 14, 0, tzinfo=UTC)  # Monday
        _seed_utc_event(db, "e-past", "Morning sync", "2026-09-07T10:00:00+00:00")  # this week, already past
        _seed_utc_event(db, "e-next", "Design review", "2026-09-08T09:00:00+00:00")
        _seed_utc_event(db, "e-sun", "Sunday late", "2026-09-13T23:30:00+00:00")  # inside Sunday 23:59
        _seed_utc_event(db, "e-mon", "Next Monday", "2026-09-14T00:30:00+00:00")  # next week

        brief = svc.generate(OWNER, now=now)

        assert _this_week(brief, "calendar:week")[0].text == "2 meetings this week"
        nxt = [i for i in brief.sections["this_week"] if i.text.startswith("Next:")]
        assert [i.text for i in nxt] == ["Next: Design review at 09:00"]
        assert "2 meetings this week" in brief.headline
        assert "watch item" not in brief.headline
        # The lookback: Monday opens at Friday 00:00 (PHILO-17).
        assert brief.period_start == datetime.datetime(2026, 9, 4, 0, 0, tzinfo=UTC).isoformat()

    def test_naive_local_now_is_read_as_local(self, db, monkeypatch):
        """Counsel H6-1 inverted: under TZ=Europe/Warsaw a naive Saturday
        10:00 local `now` counts the two Saturday meetings and NOT next
        Monday's 00:30 local one; `Next:` is one hour away, in local time."""
        monkeypatch.setenv("TZ", "Europe/Warsaw")
        time.tzset()
        try:
            svc = MondayBriefService(db)
            _seed_utc_event(db, "e-11", "Standup", "2026-09-05T09:00:00+00:00")   # Sat 11:00 local
            _seed_utc_event(db, "e-15", "Review", "2026-09-05T13:00:00+00:00")    # Sat 15:00 local
            _seed_utc_event(db, "e-mon", "Next-week planning", "2026-09-06T22:30:00+00:00")  # Mon 00:30 local

            brief = svc.generate(OWNER, now=datetime.datetime(2026, 9, 5, 10, 0))  # naive, Saturday

            assert _this_week(brief, "calendar:week")[0].text == "2 meetings this week"
            nxt = [i for i in brief.sections["this_week"] if i.text.startswith("Next:")]
            assert [i.text for i in nxt] == ["Next: Standup at 11:00"]
        finally:
            monkeypatch.undo()
            time.tzset()

    def test_commitment_due_today_counts_and_next_week_does_not(self, db):
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 7, 14, 0, tzinfo=UTC)  # Monday
        art = f"art-{uuid.uuid4().hex[:8]}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decisions (id, text, rationale, source_artifact_id, source_meeting_id,
                                          lifecycle, project_key, decided_at)
                   VALUES ('d1', 'Ship the spec', '', ?, '', 'recorded', '', datetime('now'))""",
                (art,),
            )
            for cid, due in (("dc-today", "2026-09-07"), ("dc-sun", "2026-09-13"), ("dc-next", "2026-09-14")):
                conn.execute(
                    """INSERT INTO decision_commitments
                       (id, decision_id, action_item_id, owner, due_at, status, created_at, updated_at)
                       VALUES (?, 'd1', ?, 'karol', ?, 'open', datetime('now'), datetime('now'))""",
                    (cid, f"ai-{cid}", due),
                )

        brief = svc.generate(OWNER, now=now)

        due = _this_week(brief, "meeting_watch:commitments_due")
        assert [i.text for i in due] == ["2 commitments due this week"]
        assert "2 commitments due" in brief.headline


class TestRecordedOccurrenceDedup:
    def test_recorded_occurrence_is_since_fridays_not_this_weeks(self, db):
        """The calendar_uid dedup, occurrence-scoped: an event whose
        recording already sits in the lookback as `Meeting recorded` is
        neither counted nor named in THIS WEEK."""
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 7, 14, 0, tzinfo=UTC)
        _seed_utc_event(db, "e-a", "Standup", "2026-09-07T15:00:00+00:00")  # still 'coming' by the clock
        _seed_utc_event(db, "e-b", "Review", "2026-09-08T09:00:00+00:00")
        # The owner started the armed row early and stopped it: recorded, inside the lookback.
        _seed_recorded_meeting(
            db, "m-a", calendar_event_id="e-a",
            started_at="2026-09-07T13:40:00+00:00", ended_at="2026-09-07T13:58:00+00:00",
        )

        brief = svc.generate(OWNER, now=now)

        assert _this_week(brief, "calendar:week")[0].text == "1 meeting this week"
        assert [i.source_ref for i in brief.sections["this_week"] if i.text.startswith("Next:")] == ["calendar_event:e-b"]
        assert any(i.text.startswith("Meeting recorded") for i in brief.sections["changed"])

    def test_recurring_series_next_occurrence_survives(self, db):
        """Dedup by uid ALONE would hide Tuesday's standup because Monday's
        was recorded; the occurrence key keeps it."""
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 7, 14, 0, tzinfo=UTC)
        _seed_utc_event(db, "e-mon", "Standup", "2026-09-07T09:00:00+00:00", uid="series-1")
        _seed_utc_event(db, "e-tue", "Standup", "2026-09-08T09:00:00+00:00", uid="series-1")
        _seed_recorded_meeting(
            db, "m-mon", calendar_event_id="e-mon",
            started_at="2026-09-07T08:55:00+00:00", ended_at="2026-09-07T09:30:00+00:00",
        )

        brief = svc.generate(OWNER, now=now)

        assert _this_week(brief, "calendar:week")[0].text == "1 meeting this week"
        assert [i.source_ref for i in brief.sections["this_week"] if i.text.startswith("Next:")] == ["calendar_event:e-tue"]


class TestComposeCountsCalendarItems:
    def test_headline_names_meetings_armed_and_due(self):
        """Counsel's repro_compose inverted: no 'watch items' on a desk with
        zero Watch changes; `Next:` is detail, not a count."""
        svc = MondayBriefService(db=None)
        tw = [
            BriefItem("a", "this_week", "3 meetings this week", source_ref="calendar:week", priority=60),
            BriefItem("b", "this_week", "Next: Standup at 07:00", source_ref="calendar_event:x", priority=55),
            BriefItem("c", "this_week", "2 armed", source_ref="calendar:armed", priority=53),
            BriefItem("d", "this_week", "1 commitment due this week", detail="Ship v2 | 2026-09-04",
                      source_ref="meeting_watch:commitments_due", priority=51),
        ]
        headline, _ = svc._compose(
            {"this_week": tw, "changed": [], "broke": [], "waiting": [], "decisions": []}
        )
        assert headline == "3 meetings this week, 2 armed, 1 commitment due."

    def test_headline_with_decisions(self):
        svc = MondayBriefService(db=None)
        tw = [
            BriefItem("a", "this_week", "1 meeting this week", source_ref="calendar:week", priority=60),
            BriefItem("e", "this_week", "2 new decisions from meetings", source_ref="meeting_watch:decisions", priority=52),
        ]
        headline, _ = svc._compose(
            {"this_week": tw, "changed": [], "broke": [], "waiting": [], "decisions": []}
        )
        assert headline == "1 meeting this week, 2 new decisions."


class TestCommitmentSaidOnce:
    """C11 follow-up: a commitment THIS WEEK counts is dropped from the
    lookback's `Commitment due` items -- dedup by commitment id, not text."""

    def _seed(self, db, cid: str, due: str, text: str) -> None:
        art = f"art-{uuid.uuid4().hex[:8]}"
        did = f"d-{cid}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decisions (id, text, rationale, source_artifact_id, source_meeting_id,
                                          lifecycle, project_key, decided_at)
                   VALUES (?, ?, '', ?, '', 'recorded', '', datetime('now'))""",
                (did, text, art),
            )
            conn.execute(
                """INSERT INTO decision_commitments
                   (id, decision_id, action_item_id, owner, due_at, status, created_at, updated_at)
                   VALUES (?, ?, ?, 'karol', ?, 'open', datetime('now'), datetime('now'))""",
                (cid, did, f"ai-{cid}", due),
            )

    def test_commitment_due_today_appears_once_in_this_week(self, db):
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 7, 14, 0, tzinfo=UTC)  # Monday
        self._seed(db, "dc-today", "2026-09-07", "Ship the spec")   # THIS WEEK's
        self._seed(db, "dc-past", "2026-09-01", "Ship the spec")    # overdue: the lookback's, same TEXT

        brief = svc.generate(OWNER, now=now)

        due = _this_week(brief, "meeting_watch:commitments_due")
        assert [i.text for i in due] == ["1 commitment due this week"]
        lookback_due = [i for i in brief.sections["decisions"] if i.text.startswith("Commitment due")]
        # The same text is no dedup key: the overdue one (a different id) stays.
        assert [i.text for i in lookback_due] == ["Commitment due 2026-09-01: Ship the spec"]
        assert not any("2026-09-07" in i.text for i in lookback_due)


class TestShadeReadOfSeededBrief:
    """The shade's read (GET /api/brief/latest) of the hs171 shade rig's seed
    (tests/e2e/test_hs171_shade_glass.py::_seed_brief): a brief row with four
    `waiting` items, generated_at = naive local now.  Mirrored here against
    the route, then a hub-like cadence `generate()` (naive local `now`, the
    same local day) runs AFTER the seed -- the shade must still see the
    seeded brief with its four items.

    The rig hardcodes period_end='2026-09-05'; this test seeds today's date
    so it says what the rig means on any day (a cadence generate on a later
    local day writes a newer brief, which is the shade's own hazard, not
    the seed's)."""

    def _client(self, db, monkeypatch):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from holdspeak.web.routes import monday_brief as brief_routes

        monkeypatch.setattr(brief_routes, "get_database", lambda: db)
        monkeypatch.setattr(brief_routes, "get_observer", lambda: None)
        app = FastAPI()
        app.include_router(brief_routes.build_monday_brief_router(None))
        return TestClient(app)

    def test_latest_returns_the_seed_before_and_after_a_hub_generate(self, db, monkeypatch):
        client = self._client(db, monkeypatch)
        assert client.get("/api/brief/latest").json() is None

        today = datetime.date.today().isoformat()
        brief_id = str(uuid.uuid4())
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO monday_briefs (id, period_start, period_end, headline, generated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (brief_id, "2026-09-01", today, "4 things this week", datetime.datetime.now().isoformat()),
            )
            for i in range(4):
                conn.execute(
                    "INSERT INTO monday_brief_items (id, brief_id, section, text, priority) "
                    "VALUES (?, ?, 'waiting', ?, 0)",
                    (f"brief-item-{i}", brief_id, f"Item {i + 1}"),
                )

        def shade_sees(payload):
            sections = payload["sections"]
            return (
                payload["id"], payload["is_empty"],
                sum(len(v) for v in sections.values()), len(sections.get("this_week", [])),
            )

        first = client.get("/api/brief/latest")
        assert first.status_code == 200
        assert shade_sees(first.json()) == (brief_id, False, 4, 0)

        # The hub's cadence regenerates with a naive local `now` (runtime/cadence.py:112-121).
        generated = MondayBriefService(db).generate(None, now=datetime.datetime.now())
        # PHILO-15-09 (B04, ruling 1): the same local day keeps the brief's id
        # and makes its body again from the current desk (here: nothing).
        assert generated.id == brief_id, "same local day: generate() keeps the brief id"

        again = client.get("/api/brief/latest")
        assert again.status_code == 200
        body = again.json()
        assert body["id"] == brief_id
        # The seed's rows are gone: the body is the current desk's (here at
        # most the NOT READ rows of a read made with no principal, PHILO-15 05).
        texts = [i["text"] for items in body["sections"].values() for i in items]
        assert not [t for t in texts if t.startswith("Item ")], texts
        assert all(t.startswith("NOT READ") for t in texts), texts
        assert client.post("/api/brief/generate").status_code == 200


class TestComposeNeverPrintsABareStop:
    def test_next_row_alone_is_one_item(self):
        """Counsel's H-E: a this_week holding only a `Next:` row (impossible
        in the product) must not headline as '.'."""
        svc = MondayBriefService(db=None)
        tw = [BriefItem("b", "this_week", "Next: Standup at 07:00", source_ref="calendar_event:x", priority=55)]
        headline, _ = svc._compose(
            {"this_week": tw, "changed": [], "broke": [], "waiting": [], "decisions": []}
        )
        assert headline == "1 item this week."


# ── from test_philo12_brief_read.py: PHILO-12-01 -- the brief projection keeps the exact stored id. ──
#
# The Floor can open a brief after a newer producer-day exists.  These fences use
# the real MeetingWebServer and its authenticated HTTP client, with the producer
# clock moved by the test rather than by the machine clock.  The parameter route
# is registered last so the existing ``latest`` and ``shelf`` routes remain
# reachable.


sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot

DAY_ONE = datetime.datetime(2026, 9, 28, 9, 30)


class MovableClock:
    def __init__(self, now: datetime.datetime) -> None:
        self.now = now

    def __call__(self) -> datetime.datetime:
        return self.now


@pytest.fixture
def rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    clock = MovableClock(DAY_ONE)
    hub = _boot(tmp_path, monkeypatch, clock=clock)
    yield hub, clock
    reset_database()
    composition.install(composition.bare(label="pytest"))


def test_exact_id_read_keeps_an_older_brief_after_a_newer_brief_exists(rig) -> None:
    hub, clock = rig
    first_response = hub.client.post("/api/brief/generate")
    assert first_response.status_code == 200, first_response.text
    first = first_response.json()
    previous_latest_response = hub.client.get("/api/brief/latest")
    assert previous_latest_response.status_code == 200, previous_latest_response.text
    previous_latest = previous_latest_response.json()
    # PHILO-17: ``stale`` is a read-time fact of the LATEST read (the view
    # rebuilds a stale brief); the brief itself is the rest of the payload.
    previous_latest.pop("stale", None)
    assert previous_latest == first

    hub.db.desk_decisions.upsert(
        decision_id="philo12-read-decision",
        title="Use the exact brief id",
        status="proposed",
    )
    clock.now += datetime.timedelta(days=1)
    second_response = hub.client.post("/api/brief/generate")
    assert second_response.status_code == 200, second_response.text
    second = second_response.json()
    assert second["id"] != first["id"]

    exact = hub.client.get(f"/api/brief/{first['id']}")
    assert exact.status_code == 200, exact.text
    assert exact.json() == first
    assert exact.json() == previous_latest
    assert hub.client.get("/api/brief/latest").json()["id"] == second["id"]


def test_unknown_exact_id_is_a_404_and_static_routes_keep_priority(rig) -> None:
    hub, _clock = rig
    generated = hub.client.post("/api/brief/generate")
    assert generated.status_code == 200, generated.text

    missing = hub.client.get("/api/brief/brief-does-not-exist")
    assert missing.status_code == 404
    assert missing.json()["detail"] == "brief_not_found"

    latest = hub.client.get("/api/brief/latest")
    assert latest.status_code == 200
    assert latest.json()["id"] == generated.json()["id"]

    shelf = hub.client.get("/api/brief/shelf")
    assert shelf.status_code == 200
    assert shelf.json() == {}


def test_exact_id_route_requires_the_hub_authenticated_principal(rig) -> None:
    hub, _clock = rig
    generated = hub.client.post("/api/brief/generate")
    assert generated.status_code == 200, generated.text

    unauthenticated = TestClient(
        hub.server.app, client=("127.0.0.1", 50001), raise_server_exceptions=False
    )
    unauthenticated.headers.pop("x-holdspeak-token", None)
    unauthenticated.headers.pop("authorization", None)
    response = unauthenticated.get(f"/api/brief/{generated.json()['id']}")
    assert response.status_code == 401, response.text
    assert response.json()["error"] == "principal_right_required"


# ── from test_philo15_05_brief_generates_itself.py: PHILO-15 lane 05, ruling 2 (inventory gap 10): the morning Brief generates ──
# itself.
#
# The cadence thread's Brief job is ON by default and makes the day's Brief
# once per local day at ``brief_hour`` (06:00), before the owner arrives. The
# loop job (project, score, nudge) keeps its default: OFF. Quiet hours do not
# hold the Brief: it is deterministic and sends nothing.
#
# Real producers: the real CadenceMixin tick body, the real
# MondayBriefService.generate over a real database, the real pipeline_events
# receipt. The clock is the one fake.


class _Runtime(CadenceMixin):
    def __init__(self) -> None:
        self.config = Config()  # the shipped defaults
        self.loop_ticks = 0

    def _cadence_service(self):  # the loop job: record, never run
        runtime = self

        class _Loop:
            def tick(self):
                runtime.loop_ticks += 1
                raise AssertionError("the loop job is off by default")

        return _Loop()


def _briefs(db: Database) -> list[str]:
    with db._connection() as conn:
        return [r["generated_at"] for r in conn.execute(
            "SELECT generated_at FROM monday_briefs ORDER BY generated_at"
        ).fetchall()]


def _receipts(db: Database) -> int:
    with db._connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM pipeline_events WHERE method='brief.regenerated'"
        ).fetchone()[0]


def test_the_brief_job_fires_once_per_local_day_at_its_hour(tmp_path: Path) -> None:
    db = Database(tmp_path / "brief.db")
    runtime = _Runtime()
    assert runtime._cadence_jobs_enabled() is True  # the thread starts on defaults
    clock = {"now": datetime_itself(2026, 10, 8, 5, 55)}

    def tick() -> None:
        with patch("holdspeak.db.get_database", return_value=db), patch(
            "holdspeak.runtime.cadence.local_now", side_effect=lambda: clock["now"]
        ):
            runtime._cadence_tick_body()

    tick()  # 05:55: before the Brief hour (inside quiet hours)
    assert _briefs(db) == [] and _receipts(db) == 0

    clock["now"] = datetime_itself(2026, 10, 8, 6, 0)
    tick()  # 06:00: the Brief is made, still inside quiet hours
    assert len(_briefs(db)) == 1 and _receipts(db) == 1

    for minute in (5, 30, 55):
        clock["now"] = datetime_itself(2026, 10, 8, 7, minute)
        tick()  # the same local day: never twice
    clock["now"] = datetime_itself(2026, 10, 8, 23, 50)
    tick()
    assert len(_briefs(db)) == 1 and _receipts(db) == 1

    clock["now"] = datetime_itself(2026, 10, 9, 6, 1)
    tick()  # the next local day: once more
    assert len(_briefs(db)) == 2 and _receipts(db) == 2
    assert runtime.loop_ticks == 0  # the loop job kept its default: off


def test_the_brief_job_off_makes_no_brief(tmp_path: Path) -> None:
    db = Database(tmp_path / "off.db")
    runtime = _Runtime()
    runtime.config.cadence.brief_enabled = False
    assert runtime._cadence_jobs_enabled() is False  # no thread at all
    with patch("holdspeak.db.get_database", return_value=db), patch(
        "holdspeak.runtime.cadence.local_now", return_value=datetime_itself(2026, 10, 8, 9, 0)
    ):
        runtime._cadence_tick_body()
    assert _briefs(db) == [] and _receipts(db) == 0


def test_the_cadence_status_names_the_brief_job(tmp_path: Path) -> None:
    # The Rhythm row's DAILY token reads this (web/src/pages/cores/CadenceCore.tsx).
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.cadence_service import CadenceService

    db = Database(tmp_path / "status.db")
    owner = Principal(PrincipalKind.OWNER, "philo15-05")
    status = CadenceService(db, Config().cadence).status(owner)
    assert status["enabled"] is False
    assert status["brief_job"] == {"enabled": True, "hour": 6}


# ── Astra r1 (#975) P1: the scheduled Brief never hides work ──────────────


def _seed(db: Database) -> None:
    """A desk with work waiting: a meeting with an unowned action item (and,
    on a fresh desk, the no-engine blocker the needs-you rule raises)."""
    from datetime import timedelta

    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    start = datetime_itself(2026, 10, 7, 15, 0)
    db.meetings.save_meeting(MeetingState(
        id="m-ledger", started_at=start, ended_at=start + timedelta(minutes=30), title="Ledger sync",
        segments=[TranscriptSegment(text="Someone writes the runbook.", speaker="Me", start_time=1.0, end_time=3.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["ledger"], summary="Runbook needed.", action_items=[{
            "id": "m-ledger-a1", "task": "Write the rollback runbook", "owner": None, "due": None,
            "status": "pending", "review_state": "accepted", "source_timestamp": None,
            "created_at": start.isoformat()}]),
        intel_status="completed"))


def _items(brief) -> dict[str, list[str]]:
    return {section: sorted(item.text for item in items) for section, items in brief.sections.items() if items}


def test_the_scheduled_brief_holds_the_same_items_as_the_owners_generate(tmp_path: Path) -> None:
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.monday_brief_service import MondayBriefService

    six = datetime_itself(2026, 10, 8, 6, 0).astimezone()
    scheduled_db = Database(tmp_path / "scheduled.db")
    owner_db = Database(tmp_path / "owner.db")
    _seed(scheduled_db)
    _seed(owner_db)

    runtime = _Runtime()
    with patch("holdspeak.db.get_database", return_value=scheduled_db), patch(
        "holdspeak.runtime.cadence.local_now", return_value=six
    ):
        runtime._cadence_tick_body()
    scheduled = MondayBriefService(scheduled_db).get_latest(Principal(PrincipalKind.OWNER, "owner-session"))
    owners = MondayBriefService(owner_db).generate(Principal(PrincipalKind.OWNER, "owner-session"), now=six)

    assert scheduled is not None
    assert _items(scheduled) == _items(owners), (scheduled.headline, owners.headline)
    # The work the r1 scheduled Brief hid: the blocker and the unowned item.
    # Betterment daily D8: no meeting waits for a summary, so the blocker is
    # speech alone ("No engine for summaries" asks only when one waits).
    assert _items(scheduled)["waiting"] == ["No engine for speech", "Unassigned: Write the rollback runbook"]
    assert scheduled.headline == owners.headline
    assert scheduled.headline != "No changes"
    assert not any(text.startswith("NOT READ") for texts in _items(scheduled).values() for text in texts)


def test_an_unread_source_is_a_not_read_row_never_a_silent_zero(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.people.store import production_people_store
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.monday_brief_service import (
        NOT_READ_REF,
        PEOPLE_NOT_READ_TEXT,
        MondayBriefService,
    )

    db = Database(tmp_path / "partial.db")
    # The People store is pinned inside the test (test diet 2026-10-11): the
    # brief finds it through the production store, which the old seed left
    # to the machine (the keystore env or the default path). Lane A read 3
    # NOT READ rows on a real hub's partial brief: that brief was the
    # key-free one with a People store; both shapes are fenced below.
    keyfile = tmp_path / "people.key"
    keyfile.write_text("{}")
    keyfile.chmod(0o600)
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
    when = datetime_itself(2026, 10, 8, 6, 0).astimezone()
    # A principal the needs-you rule cannot read for (the r1 defect's shape).
    heartbeat = Principal(PrincipalKind.SERVICE, "heartbeat")

    def unread_rows(people_reads: bool = True) -> tuple[list[str], str]:
        brief = MondayBriefService(db).generate(heartbeat, now=when, regenerate=True, people_reads=people_reads)
        waiting = brief.sections.get("waiting") or []
        return sorted(i.text for i in waiting if str(i.source_ref).startswith(NOT_READ_REF)), brief.headline

    # No People store: two sources not read.
    unread, headline = unread_rows()
    assert unread == ["NOT READ · AI models", "NOT READ · Decisions"], unread
    assert headline != "No changes"
    assert headline.startswith("2 sources not read")

    # The People store changes nothing on this path (it reads People itself)...
    production_people_store().initialize()
    assert unread_rows() == (unread, headline)
    # ...but the key-free brief (the scheduled one, `people_reads=False`) asks
    # for no key, so a People store that exists is its third NOT READ row:
    # the 3 rows lane A read on a real hub's partial brief.
    unread, headline = unread_rows(people_reads=False)
    assert unread == sorted(["NOT READ · AI models", "NOT READ · Decisions", PEOPLE_NOT_READ_TEXT]), unread
    assert headline.startswith("3 sources not read"), headline


def test_a_rule_that_cannot_be_read_at_all_is_a_not_read_row(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services import project_service
    from holdspeak.services.monday_brief_service import MondayBriefService

    def broken(self, principal):
        raise RuntimeError("needs-you store is locked")

    monkeypatch.setattr(project_service.ProjectService, "needs_you", broken)
    db = Database(tmp_path / "broken.db")
    brief = MondayBriefService(db).generate(
        Principal(PrincipalKind.OWNER, "owner-session"), now=datetime_itself(2026, 10, 8, 6, 0).astimezone(),
    )
    texts = [item.text for item in brief.sections.get("waiting") or []]
    assert "NOT READ · Needs you" in texts, texts
    assert brief.headline != "No changes"


def test_a_failed_door_read_is_a_not_read_row_and_keeps_the_rest(tmp_path: Path, monkeypatch) -> None:
    """Astra r2 (#975): with DoorService.asking_board failing, the Brief said
    "1 thing waiting." with no NOT READ row, no PARTIAL, and lost the blocker."""
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services import door_service
    from holdspeak.services.monday_brief_service import NOT_READ_REF, MondayBriefService

    def broken(self, principal):
        raise RuntimeError("door store is locked")

    monkeypatch.setattr(door_service.DoorService, "asking_board", broken)
    db = Database(tmp_path / "door.db")
    _seed(db)
    brief = MondayBriefService(db).generate(
        Principal(PrincipalKind.OWNER, "owner-session"), now=datetime_itself(2026, 10, 8, 6, 0).astimezone(),
    )
    waiting = brief.sections.get("waiting") or []
    texts = [item.text for item in waiting]
    assert "NOT READ · Door" in texts, texts
    # PARTIAL: the face reads any not_read row (BriefView.briefIsPartial).
    assert any(str(item.source_ref).startswith(NOT_READ_REF) for item in waiting)
    # The rule's other rows stay: the engine blocker is not lost (D8: speech
    # alone, since no meeting waits for a summary).
    assert "No engine for speech" in texts, texts
    assert "source not read" in brief.headline and brief.headline != "No changes", brief.headline


# ── Astra r2 (#975): the scheduled Brief's authority is READ, nothing more ─


def test_the_brief_principal_holds_read_only_and_cannot_write_elsewhere(tmp_path: Path, monkeypatch) -> None:
    import holdspeak.db.core as db_core
    from holdspeak import operations
    from holdspeak.db import get_database, reset_database
    from holdspeak.principals import Principal, PrincipalKind, PrincipalRight
    from holdspeak.runtime.cadence import BRIEF_PRINCIPAL_IDENTITY
    from holdspeak.services.inference_assignment_service import (
        InferenceAssignmentService,
    )
    from holdspeak.services.model_profile_service import ModelProfileService
    from holdspeak.services.primitive_service import PrimitiveService
    from holdspeak.services.profile_service import ProfileService

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "authority.db")
    reset_database()
    db = get_database()
    brief = Principal(PrincipalKind.BRIEF_CONDUCTOR, BRIEF_PRINCIPAL_IDENTITY)
    assert brief.rights == frozenset({PrincipalRight.READ})

    # The reads the Brief makes (needs-you: the model roster, decisions).
    InferenceAssignmentService(db).assignment_summary(brief)

    # Astra's write: a destination profile. Refused, and nothing stored.
    with pytest.raises(Exception, match="Owner access is required"):
        ProfileService(db).create_profile(brief, {
            "id": "authority-probe", "name": "Review", "kind": "openAICompatible",
            "base_url": "http://127.0.0.1:9/v1", "model": "review",
        })
    assert db.profiles.get("authority-probe") is None
    with pytest.raises(Exception, match="Owner access is required"):
        ModelProfileService(db).create_profile(brief, {"profile_id": "authority-probe"})
    with pytest.raises(Exception, match="Owner access is required"):
        InferenceAssignmentService(db).set_assignment(brief, {
            "command_id": "authority-probe", "expected_revision": 0, "scope": {"kind": "global"}, "entries": [],
        })
    # Any decision, through the one operation path every transport uses.
    registry = operations.bind_available({"primitive_service": PrimitiveService(db)})
    with pytest.raises(Exception, match="refused decision.create"):
        registry.invoke(brief, "decision.create", {"title": "authority probe"})
    assert db.desk_decisions.list(limit=10) == []
    reset_database()


def test_the_scheduled_job_runs_as_the_brief_principal(tmp_path: Path) -> None:
    from holdspeak.principals import PrincipalKind
    from holdspeak.services.monday_brief_service import MondayBriefService

    db = Database(tmp_path / "who.db")
    seen: list = []
    original = MondayBriefService.generate

    def spy(self, principal, **kw):
        seen.append(principal)
        return original(self, principal, **kw)

    runtime = _Runtime()
    with patch("holdspeak.db.get_database", return_value=db), patch(
        "holdspeak.runtime.cadence.local_now", return_value=datetime_itself(2026, 10, 8, 6, 0)
    ), patch.object(MondayBriefService, "generate", spy):
        runtime._cadence_tick_body()
    assert [p.kind for p in seen] == [PrincipalKind.BRIEF_CONDUCTOR]


# ── from test_philo15_09_brief_truth.py: PHILO-15-09 (B04): the Brief tells the truth about the day. ──
#
# Rehearsal 1a (docs/internal/philo/phase-15/rehearsal-1a/BOUNCES.md, B04): after
# a meeting, a decision, a person and a Project, the Brief said "No changes", a
# second Generate returned the 10:50 brief unchanged, it was titled "Monday
# Brief" on a Wednesday, and its two date ranges disagreed.
#
# Rulings fenced here:
#   1. Generate on the same day REGENERATES from the current desk: same id, new
#      body; an unchanged item keeps its shelf state.
#   2. The title is "Brief · <weekday> <date>".
#   3. One date range, computed once (the window head and the sent document).
#   4. "No changes" only when the collectors found nothing: the rehearsal's day
#      (meeting + decision + person + Project) is listed.


OWNER_truth = Principal(PrincipalKind.OWNER, "philo15-09-owner")


def _texts(brief) -> list[str]:
    return [item.text for items in brief.sections.values() for item in items]


def _item(brief, text: str):
    return next(item for items in brief.sections.values() for item in items if item.text == text)


def _desk(tmp_path):
    db = Database(tmp_path / "hub.db")
    people = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    people.initialize()
    return db, people, MondayBriefService(db, people_store=people)


def _the_rehearsal_day(db: Database, people: EncryptedPeopleStore) -> None:
    """What the owner did in rehearsal 1a: a meeting, a decision, a person, a Project."""
    ended = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(minutes=1)
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO meetings (id, started_at, ended_at, title, duration_seconds, capture_status)
               VALUES (?, ?, ?, ?, ?, 'finalized')""",
            ("meeting-day-one", (ended - datetime.timedelta(seconds=35)).isoformat(),
             ended.isoformat(), "Architect sync", 35.0),
        )
    db.desk_decisions.upsert(
        decision_id="decision-sqlite", title="Use SQLite for the local meeting ledger",
        status="accepted",
    )
    db.projects.create_project(project_id="project-ledger", name="Local ledger")
    PeopleService(people).create_relationship(OWNER_truth, {"display_name": "Priya Shah"})


def test_the_rehearsal_day_is_listed_and_generate_regenerates(tmp_path):
    db, people, service = _desk(tmp_path)

    morning = service.generate(OWNER_truth)
    # A cold desk: at most the setup row (no summary engine), none of the day.
    assert not [t for t in _texts(morning) if t.startswith(("Meeting recorded", "Decision made", "Project added"))]

    _the_rehearsal_day(db, people)
    again = service.generate(OWNER_truth)

    assert again.id == morning.id, "the same day keeps the brief's id"
    assert again.generated_at > morning.generated_at, "a newer GENERATED time"
    assert again.headline != morning.headline
    texts = _texts(again)
    for wanted in (
        "Meeting recorded: Architect sync",
        "Decision made: Use SQLite for the local meeting ledger",
        "Project added: Local ledger",
        "Person added",
    ):
        assert wanted in texts, (wanted, texts)
    # The brief is sent to other places: no People content in it.
    assert not [t for t in texts if "Priya" in t]
    # The decision he made is not one he must review.
    assert "Review decision: Use SQLite for the local meeting ledger" not in texts
    assert service.get_latest(None).id == morning.id
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM monday_briefs").fetchone()[0] == 1


def test_an_unchanged_item_keeps_its_shelf_state_and_a_gone_one_leaves(tmp_path):
    db, people, service = _desk(tmp_path)
    _the_rehearsal_day(db, people)
    first = service.generate(OWNER_truth)
    project = _item(first, "Project added: Local ledger")
    service.shelve(None, project.id, "acknowledged")

    db.projects.create_project(project_id="project-two", name="Second Project")
    db.desk_decisions.delete("decision-sqlite")
    second = service.generate(OWNER_truth)

    kept = _item(second, "Project added: Local ledger")
    assert kept.id == project.id
    assert second.shelf == {project.id: "acknowledged"}
    assert "Project added: Second Project" in _texts(second)
    assert "Decision made: Use SQLite for the local meeting ledger" not in _texts(second)


def test_a_proposed_decision_is_reviewed_not_made(tmp_path):
    db, _people, service = _desk(tmp_path)
    db.desk_decisions.upsert(decision_id="decision-agent", title="Adopt the queue", status="proposed")
    texts = _texts(service.generate(OWNER_truth))
    assert "Review decision: Adopt the queue" in texts
    assert "Decision made: Adopt the queue" not in texts


def test_the_title_is_the_briefs_own_day_and_the_range_is_one():
    # Wednesday 7 Oct 2026: never "Monday" unless it is.
    assert brief_title("2026-10-07T10:50:00-06:00") == "Brief · Wednesday 7 Oct 2026"
    assert brief_title("2026-10-05T08:00:00-06:00") == "Brief · Monday 5 Oct 2026"
    # The window (yesterday 17:00 to now), never the week.
    assert brief_period_label("2026-10-06T17:00:00-06:00", "2026-10-07T10:50:00-06:00") == "OCT 06-07"
    assert brief_period_label("2026-09-30T17:00:00-06:00", "2026-10-01T09:00:00-06:00") == "SEP 30 - OCT 01"


def test_the_sent_document_says_the_same_title_and_range(tmp_path):
    db, people, service = _desk(tmp_path)
    _the_rehearsal_day(db, people)
    brief = service.generate(OWNER_truth)
    document = render_document(db, f"monday_brief:{brief.id}")
    title = brief_title(brief.period_end)
    label = brief_period_label(brief.period_start, brief.period_end)
    assert document.title == title
    assert document.body_md.startswith(f"# {title}\nPeriod: {label}\n")
    assert "Monday Brief" not in document.body_md


def test_the_schedule_keeps_one_brief_a_day(tmp_path):
    db, people, service = _desk(tmp_path)
    morning = service.generate(OWNER_truth, regenerate=False)
    _the_rehearsal_day(db, people)
    scheduled = service.generate(OWNER_truth, regenerate=False)
    assert scheduled.id == morning.id and scheduled.generated_at == morning.generated_at
    assert scheduled.headline == morning.headline
    assert _texts(scheduled) == _texts(morning)


# ── Astra r1 (P1): the Brief never asks for the People key ────────────


class _SpyKeys(MemoryKeyStore):
    """A key store that counts every key request and can be locked."""

    def __init__(self) -> None:
        super().__init__()
        self.gets = 0
        self.locked = False

    def get(self, key_id: str) -> bytes:
        self.gets += 1
        if self.locked:
            from holdspeak.people.keys import PeopleKeyError

            raise PeopleKeyError("people_key_missing")
        return super().get(key_id)


def _hub_door(db: Database, people: EncryptedPeopleStore):
    """The Door as the hub composes it (web_server.py: People projection on)."""
    from holdspeak.services.door_service import DoorService
    from holdspeak.services.follow_through_service import FollowThroughService
    from holdspeak.services.refinement_thought_service import RefinementThoughtService

    people_service = PeopleService(people)
    return DoorService(
        FollowThroughService(db, people_projection=people_service), RefinementThoughtService(db),
        db.scheduled_recordings, db.calendar_events, db=db, people_service=people_service,
    )


def _keyed_desk(tmp_path, monkeypatch):
    from holdspeak.services import needs_you_membership

    db = Database(tmp_path / "hub.db")
    keys = _SpyKeys()
    people = EncryptedPeopleStore(tmp_path / "people.sqlite3", keys)
    people.initialize()
    _the_rehearsal_day(db, people)
    service = PeopleService(people)
    rel = service.create_relationship(OWNER_truth, {"display_name": "Sam Rivera"})
    request = service.create_request(OWNER_truth, rel["id"], {"body": "Sam: send the status by Thursday"})
    service.accept_request(OWNER_truth, request["id"])
    door = _hub_door(db, people)
    monkeypatch.setattr(
        needs_you_membership, "_hub_service",
        lambda name, build: door if name == "door_service" else build(),
    )
    return db, people, keys


def _conductor():
    """The scheduled job's own principal (runtime/cadence.py, #975)."""
    from holdspeak.runtime.cadence import BRIEF_PRINCIPAL_IDENTITY

    return Principal(PrincipalKind.BRIEF_CONDUCTOR, BRIEF_PRINCIPAL_IDENTITY)


PRINCIPALS = pytest.mark.parametrize("who", ["owner", "brief_conductor"])


def _who(name: str):
    return OWNER_truth if name == "owner" else _conductor()


@PRINCIPALS
def test_the_scheduled_brief_asks_for_no_key(tmp_path, monkeypatch, who):
    db, people, keys = _keyed_desk(tmp_path, monkeypatch)
    # Control: the hub's own Needs read (the owner's face) asks for the key.
    from holdspeak.services.project_service import ProjectService

    keys.gets = 0
    ProjectService(db).needs_you(OWNER_truth)
    assert keys.gets > 0, "the control must reach the People store"

    keys.gets = 0
    # The scheduled path (runtime/cadence.py): its brief-conductor principal
    # (#975), and the OWNER too (Astra r2: both principals).
    brief = MondayBriefService(db, people_store=people).generate(
        _who(who), regenerate=False, people_reads=False)
    assert keys.gets == 0, "the scheduled Brief asked for the People key"
    texts = _texts(brief)
    assert "Person added" not in texts  # two people: the plural line
    assert "2 people added" in texts
    assert not [t for t in texts if "Sam" in t or "Priya" in t]
    # The scheduled Brief says what it skipped: one counted NOT READ row.
    from holdspeak.services.monday_brief_service import PEOPLE_NOT_READ_TEXT

    assert texts.count(PEOPLE_NOT_READ_TEXT) == 1, texts
    row = next(i for i in brief.sections["waiting"] if i.text == PEOPLE_NOT_READ_TEXT)
    assert row.source_ref == "not_read:people"
    assert brief.headline.startswith("1 source not read"), brief.headline
    # The guard is what holds: the owner's own Generate (people_reads) reaches
    # the key, and the full brief has no NOT READ row.
    keys.gets = 0
    full = MondayBriefService(db, people_store=people).generate(OWNER_truth)
    assert keys.gets > 0
    assert PEOPLE_NOT_READ_TEXT not in _texts(full)
    assert full.id == brief.id


@PRINCIPALS
def test_a_locked_people_store_makes_the_same_brief(tmp_path, monkeypatch, who):
    db, people, keys = _keyed_desk(tmp_path, monkeypatch)
    service = MondayBriefService(db, people_store=people)
    open_store = service.generate(_who(who), people_reads=False)
    keys.locked = True
    keys.gets = 0
    locked = service.generate(_who(who), people_reads=False)
    assert keys.gets == 0
    assert locked.id == open_store.id
    assert sorted(_texts(locked)) == sorted(_texts(open_store))
    assert locked.headline == open_store.headline


def test_the_cadence_job_makes_the_brief_key_free(tmp_path):
    """The scheduled job (runtime/cadence.py) asks for no regeneration and no
    People read: nobody is at the desk to answer a key request."""
    from unittest.mock import MagicMock, patch

    from holdspeak.runtime.cadence import CadenceMixin

    db = Database(tmp_path / "hub.db")
    mixin = MagicMock()
    mixin._brief_due.return_value = True
    calls: list[dict] = []
    brief = MagicMock(item_count=0)
    with patch("holdspeak.db.get_database", return_value=db), patch(
        "holdspeak.services.monday_brief_service.MondayBriefService.generate",
        side_effect=lambda *a, **kw: (calls.append(kw), brief)[1],
    ):
        CadenceMixin._maybe_regenerate_brief(mixin)
    assert len(calls) == 1
    assert calls[0]["regenerate"] is False
    assert calls[0]["people_reads"] is False


def test_no_people_store_means_nothing_skipped(tmp_path):
    db = Database(tmp_path / "hub.db")
    absent = EncryptedPeopleStore(tmp_path / "none.sqlite3", MemoryKeyStore())
    from holdspeak.services.monday_brief_service import PEOPLE_NOT_READ_TEXT

    brief = MondayBriefService(db, people_store=absent).generate(OWNER_truth, people_reads=False)
    assert PEOPLE_NOT_READ_TEXT not in _texts(brief)


def test_the_owners_generate_keeps_the_people_row_when_its_read_fails(tmp_path, monkeypatch):
    """Astra r2, P1: the owner's Generate with the key request refused: People
    was not read, so the NOT READ row stays and the brief is PARTIAL (a
    ``not_read:`` row; ChairHome's briefIsPartial)."""
    from holdspeak.services.monday_brief_service import (
        NOT_READ_REF,
        PEOPLE_NOT_READ_TEXT,
    )

    db, people, keys = _keyed_desk(tmp_path, monkeypatch)
    keys.locked = True
    keys.gets = 0
    brief = MondayBriefService(db, people_store=people).generate(OWNER_truth)
    assert keys.gets > 0, "the owner's Generate asked for the key"
    row = next(i for i in brief.sections["waiting"] if i.text == PEOPLE_NOT_READ_TEXT)
    assert row.source_ref.startswith(NOT_READ_REF)
    assert "source not read" in brief.headline or "sources not read" in brief.headline, brief.headline
    # Unlocked, the owner's Generate reads People and the row leaves.
    keys.locked = False
    full = MondayBriefService(db, people_store=people).generate(OWNER_truth)
    assert PEOPLE_NOT_READ_TEXT not in _texts(full)


def test_an_unread_source_is_said_once(tmp_path, monkeypatch):
    """Astra r2, P2: a failed coder registry is ONE source not read, never also
    a thing waiting (the hub's count includes it; the Brief's waiting count is
    the members)."""
    from holdspeak.services import needs_you_membership as membership

    db = Database(tmp_path / "hub.db")

    def broken():
        raise RuntimeError("registry unreadable")

    monkeypatch.setattr(membership, "_read_coders", broken)
    brief = MondayBriefService(db).generate(OWNER_truth)
    waiting = brief.sections["waiting"]
    coders = [i for i in waiting if i.source_ref == "not_read:coders"]
    assert len(coders) == 1, [(i.text, i.source_ref) for i in waiting]
    members = [i for i in waiting if not str(i.source_ref).startswith(("not_read:", "coverage:"))]
    assert re.search(r"(\d+) sources? not read", brief.headline).group(1) == str(len(waiting) - len(members))
    things = re.search(r"(\d+) things? waiting", brief.headline)
    assert (int(things.group(1)) if things else 0) == len(members), (brief.headline, members)


# ── from test_philo15_19_brief_carries_the_day.py: PHILO-15 lane 19: the Brief carries the day (rehearsal 2: B58, B59, B65, B73). ──
#
# B58: the morning Brief listed "meeting recorded / project added / summary
# requested" and missed the day's confirmed decision, the agent launch, its PR,
# the merge and the sent update. Each is now a Changed row in plain words, with
# the title and the local time, and a ref the face opens.
#
# B59: a hub started after the Brief's hour, with no Brief for the day, makes it
# at start (it waited one tick interval, 5 minutes).
#
# B65: a NEW PR of a launch is found by the 2-minute poll (one bounded
# ``gh pr list --head <branch>``), not only by the 15-minute sweep.
#
# B73: a Brief row carries no JSON, no record id, no digest and no UTC stamp.
#
# Producer-backed: K2's real hand-to-agent launch, the real K4 follow-through
# (its poll), the real proposal confirm, the real FollowThroughService close,
# the real update publish and the real folder Send through the hub. Only ``gh``
# and ``tmux`` are faked, at their process boundary, and the producers' clocks
# are set to the rig's launch day.


PR_URL = "https://github.com/acme/railsproj/pull/7"
OPENED = T0 + timedelta(minutes=10)
MERGED = T0 + timedelta(minutes=50)
DONE = T0 + timedelta(minutes=55)  # the producers' clock after the merge
BRIEF_NOW = (T0 + timedelta(hours=3)).astimezone()


def _z(moment: datetime_day) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pr(branch: str, head: str, state: str) -> dict[str, Any]:
    merged = state == "MERGED"
    return {
        "number": 7, "title": "Fix the login timeout", "url": PR_URL,
        "headRefName": branch, "baseRefName": "main", "headRefOid": head, "baseRefOid": "",
        "state": state, "isDraft": False, "statusCheckRollup": [], "author": {"login": "agent"},
        "reviewDecision": "", "createdAt": _z(OPENED),
        "mergedAt": _z(MERGED) if merged else None,
        "mergeCommit": {"oid": "f" * 40} if merged else None, "isCrossRepository": False,
        "headRepositoryOwner": {"login": "acme"}, "headRepository": {"name": "railsproj"},
    }


def _rig(tmp_path, db_day, monkeypatch):
    rig = _launch(tmp_path, db_day, monkeypatch)
    rig.gh = ViewGh()
    rig.receipts._runner = rig.gh
    return rig


def _hm(stamp: Any) -> str:
    """The local clock time a person reads (the rig's day is the Brief's day)."""
    return parse_stamp(stamp).astimezone().strftime("%H:%M")


def _rows(brief) -> dict[str, Any]:
    return {item.text: item for items in brief.sections.values() for item in items}


_RAW = re.compile(r"[{}\[\]]|\d{4}-\d{2}-\d{2}T|sha256|launch-|prop-|brief-|ai_1|\bm1\b")


def _assert_plain(brief) -> None:
    for items in brief.sections.values():
        for item in items:
            for text in (item.text, item.detail or ""):
                assert not _RAW.search(text), (item.text, item.detail)


# ── B65: the poll finds a NEW PR ─────────────────────────────────────


def test_the_poll_finds_a_new_pr_by_its_branch(tmp_path, db_day, monkeypatch) -> None:
    rig = _rig(tmp_path, db_day, monkeypatch)
    try:
        launch_id = rig.result["launch_id"]
        # No PR yet: the poll lists the branch, finds nothing, keeps nothing.
        receipt = rig.observer.poll_open_prs(OWNER_day)
        assert receipt["discovered"] == [{"launch_id": launch_id, "gh_state": "live", "prs": 0}]
        assert "found" not in receipt
        argv = rig.gh.calls[-1]
        assert argv[:3] == ["gh", "pr", "list"]
        assert argv[argv.index("--head") + 1] == rig.branch
        assert argv[argv.index("--limit") + 1] == "5"

        # The agent opens its PR: the next poll keeps it (it was the sweep's).
        rig.gh.prs = [_pr(rig.branch, rig.head, "OPEN")]
        receipt = rig.observer.poll_open_prs(OWNER_day)
        assert receipt["found"] == [launch_id]
        state = rig.launches.get(launch_id)["follow_through"]
        assert state["pr"]["number"] == 7 and state["pr"]["state"] == "open"
        assert state["pr_opened_at"] == _z(OPENED), "gh's own createdAt"

        # From now on it is a known PR: one `gh pr view`, no branch list.
        calls = len(rig.gh.calls)
        rig.gh.prs = [_pr(rig.branch, rig.head, "MERGED")]
        receipt = rig.observer.poll_open_prs(OWNER_day)
        assert rig.gh.calls[calls][:3] == ["gh", "pr", "view"]
        assert receipt["discovered"] == [] and receipt["closed"], receipt
        assert _status(db_day, "ai_1") == "done"
    finally:
        rig.tmux.ended = True


def test_the_discovery_is_inside_the_poll_ceiling(tmp_path, db_day, monkeypatch) -> None:
    rig = _rig(tmp_path, db_day, monkeypatch)
    try:
        monkeypatch.setattr(follow_through, "POLL_MAX_PRS", 0)
        rig.gh.prs = [_pr(rig.branch, rig.head, "OPEN")]
        receipt = rig.observer.poll_open_prs(OWNER_day)
        assert receipt["discovered"] == [] and rig.gh.calls == []
    finally:
        rig.tmux.ended = True


def test_a_found_pr_announces_one_desk_change(tmp_path, db_day, monkeypatch) -> None:
    """The ledger is a file: the hub names the found PR itself, so the lane,
    the drawer and Needs re-read within the poll."""
    from holdspeak.services.heartbeat_service import HeartbeatService

    rig = _rig(tmp_path, db_day, monkeypatch)
    sent: list[Any] = []

    class _Sender:
        broadcast = True

        def _send_desk_changed(self, changes):
            sent.append(list(changes))

    monkeypatch.setattr(composition, "_installed", _Sender())
    try:
        rig.gh.prs = [_pr(rig.branch, rig.head, "OPEN")]
        heartbeat = HeartbeatService(db_day, follow_through=rig.observer, notifier=lambda *_a, **_k: True)
        receipt = heartbeat.poll_open_prs(OWNER_day)
        assert receipt["found"] == [rig.result["launch_id"]]
        assert len(sent) == 1, sent
    finally:
        rig.tmux.ended = True


# ── B58 + B73: the Brief carries the day ─────────────────────────────


def _the_day(tmp_path, db_day, monkeypatch):
    """The rehearsal's day on the rig: a decision confirmed, the agent
    launched on the action, its PR opened and merged, the action done."""
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    monkeypatch.setattr("holdspeak.db.proposals.utc_now_iso", lambda: _z(T0 + timedelta(minutes=5)))
    monkeypatch.setattr("holdspeak.services.follow_through_service.utc_now_iso", lambda: _z(DONE))
    proposal = db_day.proposals.create_proposal(
        meeting_id="m1", project_id=PROJECT, kind="decision",
        text="Squash merges only on the rehearsal repository", source_plugin="rehearsal",
    )
    assert ProposalBridgeService(db_day).confirm_proposal(OWNER_day, proposal.id)["decision_record_id"]
    rig = _rig(tmp_path, db_day, monkeypatch)
    rig.gh.prs = [_pr(rig.branch, rig.head, "OPEN")]
    assert rig.observer.poll_open_prs(OWNER_day)["found"]
    rig.gh.prs = [_pr(rig.branch, rig.head, "MERGED")]
    assert rig.observer.poll_open_prs(OWNER_day)["closed"]
    assert _status(db_day, "ai_1") == "done"
    return rig


def test_the_brief_carries_the_decision_the_agent_its_pr_the_merge_and_the_done_action(
    tmp_path, db_day, monkeypatch,
) -> None:
    rig = _the_day(tmp_path, db_day, monkeypatch)
    try:
        launch_id = rig.result["launch_id"]
        brief = MondayBriefService(db_day, launch_ledger=rig.launches).generate(OWNER_day, now=BRIEF_NOW)
        rows = _rows(brief)
        wanted = {
            "Decision confirmed: Squash merges only on the rehearsal repository": (
                "meeting:m1", _hm(T0 + timedelta(minutes=5))),
            "Agent launched: Fix the login timeout": (f"launch:{launch_id}", _hm(T0)),
            "PR opened: Fix the login timeout (PR #7)": (f"launch:{launch_id}", _hm(OPENED)),
            "PR merged: Fix the login timeout (PR #7)": (f"launch:{launch_id}", _hm(MERGED)),
            "Action done: Fix the login timeout": ("action_item:ai_1", _hm(DONE)),
        }
        for text, (ref, clock) in wanted.items():
            assert text in rows, (text, sorted(rows))
            item = rows[text]
            assert item.section == "changed"
            assert item.source_ref == ref, (text, item.source_ref)
            assert item.detail and item.detail.endswith(clock), (text, item.detail)
        assert "Claude Code" in rows["Agent launched: Fix the login timeout"].detail
        # ORDER RULING (Astra r1, 2): merge, (sent update), opened PR,
        # confirmed decision, done action, launch, then the rest.
        kinds = [item.text.split(": ", 1)[0] for item in brief.sections["changed"]]
        assert kinds[:5] == ["PR merged", "PR opened", "Decision confirmed", "Action done",
                             "Agent launched"], kinds
        # Said once: the merge and the close are one row each.
        assert sum(t.startswith("PR merged: ") for t in rows) == 1
        assert not any(t.startswith("Follow-up completed: Fix the login timeout") for t in rows)
        assert "things changed" in brief.headline
        _assert_plain(brief)

        # The owner's Generate later the same day gives the same rows.
        again = MondayBriefService(db_day, launch_ledger=rig.launches).generate(
            OWNER_day, now=BRIEF_NOW + timedelta(minutes=7))
        assert set(wanted) <= set(_rows(again))
        assert again.id == brief.id
    finally:
        rig.tmux.ended = True


def test_the_scheduled_brief_carries_the_day_key_free(tmp_path, db_day, monkeypatch) -> None:
    """The 07:10 Brief runs under the read-only brief-conductor principal
    with no People reads: it says the same day."""
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.runtime.cadence import BRIEF_PRINCIPAL_IDENTITY

    rig = _the_day(tmp_path, db_day, monkeypatch)
    try:
        principal = Principal(PrincipalKind.BRIEF_CONDUCTOR, BRIEF_PRINCIPAL_IDENTITY)
        brief = MondayBriefService(db_day, launch_ledger=rig.launches).generate(
            principal, now=BRIEF_NOW, regenerate=False, people_reads=False)
        texts = set(_rows(brief))
        assert {"Decision confirmed: Squash merges only on the rehearsal repository",
                "PR merged: Fix the login timeout (PR #7)",
                "Action done: Fix the login timeout"} <= texts, sorted(texts)
        _assert_plain(brief)
    finally:
        rig.tmux.ended = True


def test_a_corrupt_launch_file_is_a_not_read_row(tmp_path, db_day, monkeypatch) -> None:
    """Astra r1 (1): the REAL ledger over a REAL corrupt file, through the
    real service's default ledger: NOT READ · Agents with the reason."""
    from holdspeak.delivery.factory_launch import LaunchLedger, LaunchLedgerNotRead

    bad = tmp_path / "agent_launches.json"
    bad.write_text('{"launches_schema": 1, "launches": [', encoding="utf-8")
    monkeypatch.setattr("holdspeak.delivery.factory_launch.DEFAULT_LAUNCHES_PATH", bad)
    assert LaunchLedger().list() == [], "the old read still answers empty"
    with pytest.raises(LaunchLedgerNotRead):
        LaunchLedger().read_all()

    brief = MondayBriefService(db_day).generate(OWNER_day)
    waiting = {item.text: item for item in brief.sections["waiting"]}
    assert "NOT READ · Agents" in waiting, sorted(waiting)
    assert waiting["NOT READ · Agents"].detail == "the launch file is not valid JSON"
    assert "source not read" in brief.headline

    # An absent file is no launches, not a NOT READ row.
    bad.unlink()
    brief = MondayBriefService(db_day).generate(OWNER_day)
    assert not any(i.text == "NOT READ · Agents" for i in brief.sections["waiting"])


def test_a_corrupt_room_merge_record_is_a_not_read_row(tmp_path, db_day) -> None:
    """Astra r1 (1): a Room merge record that cannot be read, written through
    the real observation repository, is a NOT READ row, never a silent zero."""
    from holdspeak.delivery.follow_through import MERGED_OBSERVATION

    db_day.project_observations.insert_observation(
        observation_id="pobs-corrupt-19", project_id=PROJECT, source_id="github:acme/railsproj",
        observation_kind=MERGED_OBSERVATION, subject_ref="https://github.com/acme/railsproj/pull/9",
        source_version="v1", observed_at=_z(BRIEF_NOW - timedelta(minutes=5)),
        fact_json='{"event": "pr_merged", "pr_url": ', content_hash="x",
    )
    brief = MondayBriefService(db_day, launch_ledger=_NoLaunches()).generate(OWNER_day, now=BRIEF_NOW)
    waiting = {item.text: item for item in brief.sections["waiting"]}
    assert "NOT READ · Room merges" in waiting, sorted(waiting)
    assert waiting["NOT READ · Room merges"].detail == "1 merge record cannot be read"


# ── Astra r1 (3, 4): the opened stamp backfills; discovery retires ──


def test_a_pr_kept_before_the_stamp_gains_gh_created_at(tmp_path, db_day, monkeypatch) -> None:
    rig = _rig(tmp_path, db_day, monkeypatch)
    try:
        launch_id = rig.result["launch_id"]
        rig.gh.prs = [_pr(rig.branch, rig.head, "OPEN")]
        assert rig.observer.poll_open_prs(OWNER_day)["found"]
        # The upgrade state: a launch record written before this change kept
        # its PR and has no opened stamp.
        state = dict(rig.launches.get(launch_id)["follow_through"])
        state.pop("pr_opened_at")
        rig.launches.update(launch_id, follow_through=state)
        receipt = rig.observer.poll_open_prs(OWNER_day)
        assert receipt["polled"] and receipt["discovered"] == []
        assert rig.launches.get(launch_id)["follow_through"]["pr_opened_at"] == _z(OPENED)
    finally:
        rig.tmux.ended = True


def test_discovery_retires_when_the_branch_is_gone(tmp_path, db_day, monkeypatch) -> None:
    import subprocess

    rig = _rig(tmp_path, db_day, monkeypatch)
    try:
        launch_id = rig.result["launch_id"]
        subprocess.run(["git", "-C", str(rig.repo), "worktree", "remove", "--force", str(rig.worktree)],
                       check=True, capture_output=True)
        subprocess.run(["git", "-C", str(rig.repo), "branch", "-D", rig.branch],
                       check=True, capture_output=True)
        receipt = rig.observer.poll_open_prs(OWNER_day)
        assert receipt["retired"] == [launch_id]
        follow = rig.launches.get(launch_id)["follow_through"]
        assert (follow["discovery"], follow["discovery_reason"]) == ("retired", "branch_gone")
        calls = len(rig.gh.calls)
        assert rig.observer.poll_open_prs(OWNER_day)["discovered"] == []
        assert len(rig.gh.calls) == calls, "a retired launch reads no gh"
    finally:
        rig.tmux.ended = True


def test_a_working_agent_with_no_pr_is_not_retired(tmp_path, db_day, monkeypatch) -> None:
    rig = _rig(tmp_path, db_day, monkeypatch)
    try:
        for _ in range(3):
            assert "retired" not in rig.observer.poll_open_prs(OWNER_day)
        assert len(rig.gh.calls) == 3, "one branch list per poll while the branch exists"
    finally:
        rig.tmux.ended = True


def test_a_stopped_or_done_launch_is_not_discovered(tmp_path, db_day, monkeypatch) -> None:
    rig = _rig(tmp_path, db_day, monkeypatch)
    try:
        launch_id = rig.result["launch_id"]
        rig.launches.update(launch_id, stopped={"at": "2026-10-07T23:00:00Z"})
        assert rig.observer.poll_open_prs(OWNER_day)["discovered"] == []
        rig.launches.update(launch_id, stopped=None, follow_through={"done": True})
        assert rig.observer.poll_open_prs(OWNER_day)["discovered"] == []
        assert rig.gh.calls == []
    finally:
        rig.tmux.ended = True


# ── B73: plain words ─────────────────────────────────────────────────


def test_a_recorded_call_detail_is_plain_words_never_json() -> None:
    assert _sanitize_detail('{"meeting_id":"23c66417","expected_selection_hash":"sha256:3e52aa"}') is None
    assert _sanitize_detail('{"path": "/Users/karol/.config/holdspeak/settings.json"}') is None
    assert _sanitize_detail("{}") is None
    assert _sanitize_detail('{"verb": "done", "card_id": "ai_1"}') == "verb done"


def test_a_summary_request_row_reads_its_title_and_local_time(tmp_path, db_day) -> None:
    import json
    import uuid

    stamp = BRIEF_NOW - timedelta(minutes=30)
    with db_day._connection() as conn:
        conn.execute(
            """INSERT INTO pipeline_events (event_id, timestamp, service, method, principal_kind,
               principal_identity, args_summary, result_summary, error, error_code, duration_ms,
               correlation_id, is_async) VALUES (?, ?, 'MeetingIntelService', 'run_intelligence',
               'owner', 'karol', ?, '{"state":"queued"}', NULL, NULL, 3, '', 0)""",
            (str(uuid.uuid4()), stamp.timestamp(),
             json.dumps({"meeting_id": "m1", "expected_selection_hash": "sha256:3e52aa"})),
        )
    brief = MondayBriefService(db_day, launch_ledger=_NoLaunches()).generate(OWNER_day, now=BRIEF_NOW)
    row = _rows(brief)["Summary requested: Planning sync"]
    assert row.detail == stamp.strftime("%H:%M")
    _assert_plain(brief)


class _NoLaunches:
    def list(self):
        return []


# ── B58: the update he sent, through the hub ─────────────────────────


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setenv("HOME", str(fake))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("XDG_DOCUMENTS_DIR", raising=False)
    monkeypatch.setattr("holdspeak.delivery.factory_launch.DEFAULT_LAUNCHES_PATH", tmp_path / "launches.json")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _philo10_send import _boot

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def test_the_sent_update_is_a_brief_row_that_opens_its_room(hub) -> None:
    from _philo10_send import room, send, send_body

    pid, update = room(hub, name="Rehearsal repo hygiene")
    resp = send(hub, send_body(hub, "inline", update, "holdspeak-folder", "k-b58"))
    assert resp.status_code == 200, resp.text
    brief = hub.client.post("/api/brief/generate").json()
    rows = {i["text"]: i for items in brief["sections"].values() for i in items}
    row = rows.get("Update sent: Rehearsal repo hygiene")
    assert row is not None, sorted(rows)
    assert row["source_ref"] == f"project:{pid}"
    assert re.fullmatch(r"HoldSpeak folder · \d{2}:\d{2}", row["detail"]), row["detail"]
    # One row per update: sent, not also "published".
    assert "Update published: Rehearsal repo hygiene" not in rows
    # Astra r1 (2, 6): the sent update leads the recorded/added rows; the
    # project row carries its time.
    changed = [i["text"] for i in brief["sections"]["changed"]]
    assert changed.index("Update sent: Rehearsal repo hygiene") < changed.index(
        "Project added: Rehearsal repo hygiene"), changed
    assert re.fullmatch(r"\d{2}:\d{2}", rows["Project added: Rehearsal repo hygiene"]["detail"])


# ── B59: the first tick at start ─────────────────────────────────────


def _runtime(stop_after_start: bool = True):
    import threading

    from holdspeak.config import Config
    from holdspeak.runtime.cadence import CadenceMixin

    class Runtime(CadenceMixin):
        def __init__(self) -> None:
            self.config = Config()
            self.runtime_stop_event = threading.Event()
            self.ticks = 0

        def _cadence_tick_once(self) -> None:
            self.ticks += 1
            self._cadence_tick_body()

        def _cadence_service(self):  # the loop job is off by default
            raise AssertionError("the loop job is off")

    runtime = Runtime()
    if stop_after_start:
        runtime.runtime_stop_event.set()
    return runtime


def _briefs_day(db_day) -> int:
    with db_day._connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM monday_briefs").fetchone()[0]


def test_a_hub_started_at_0705_makes_the_days_brief_at_start(tmp_path) -> None:
    from holdspeak.db import Database

    db_day = Database(tmp_path / "hub.db")
    runtime = _runtime()
    with patch("holdspeak.db.get_database", return_value=db_day), patch(
        "holdspeak.runtime.cadence.local_now", return_value=datetime_day(2026, 10, 8, 7, 5)
    ):
        runtime._cadence_loop()  # the stop event is set: only the start runs
        assert runtime.ticks == 1 and _briefs_day(db_day) == 1
        # The day's Brief exists: the next start makes no tick.
        again = _runtime()
        again._cadence_loop()
        assert again.ticks == 0 and _briefs_day(db_day) == 1


def test_a_hub_started_before_the_briefs_hour_waits(tmp_path) -> None:
    from holdspeak.db import Database

    db_day = Database(tmp_path / "hub.db")
    runtime = _runtime()
    with patch("holdspeak.db.get_database", return_value=db_day), patch(
        "holdspeak.runtime.cadence.local_now", return_value=datetime_day(2026, 10, 8, 5, 30)
    ):
        runtime._cadence_loop()
    assert runtime.ticks == 0 and _briefs_day(db_day) == 0


# ── Astra r1 (5): the REAL next-morning transition, through the cadence ──


@pytest.fixture
def denver_day(monkeypatch):
    """The hub's zone, pinned: the rehearsal's machine (America/Denver)."""
    import time

    monkeypatch.setenv("TZ", "America/Denver")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def test_the_next_mornings_scheduled_brief_carries_last_evening(tmp_path, db_day, monkeypatch, denver_day) -> None:
    """The cadence path untouched (regenerate=False, key-free): Wednesday's
    Brief exists; the evening's decision and done action land after it; the
    clock passes midnight (no Brief before its hour) and 07:10 Thursday makes
    Thursday's Brief, which covers Wednesday 00:00 (PHILO-17) through 07:10."""
    from holdspeak.services.follow_through_service import FollowThroughService
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    monkeypatch.setattr("holdspeak.delivery.factory_launch.DEFAULT_LAUNCHES_PATH", tmp_path / "none.json")
    wed = datetime_day(2026, 10, 7)

    def at(hour: int, minute: int, days: int = 0) -> datetime_day:
        return wed + timedelta(days=days, hours=hour, minutes=minute)

    runtime = _runtime()

    def tick(moment: datetime_day) -> None:
        with patch("holdspeak.db.get_database", return_value=db_day), patch(
            "holdspeak.runtime.cadence.local_now", return_value=moment
        ):
            runtime._cadence_tick_body()

    tick(at(7, 10))  # Wednesday's scheduled Brief
    assert _briefs_day(db_day) == 1

    decided = at(21, 14).astimezone()
    monkeypatch.setattr("holdspeak.db.proposals.utc_now_iso", lambda: _z(decided))
    monkeypatch.setattr("holdspeak.services.follow_through_service.utc_now_iso",
                        lambda: _z(at(21, 40).astimezone()))
    proposal = db_day.proposals.create_proposal(
        meeting_id="m1", project_id=PROJECT, kind="decision",
        text="Squash merges only on the rehearsal repository", source_plugin="rehearsal")
    ProposalBridgeService(db_day).confirm_proposal(OWNER_day, proposal.id)
    FollowThroughService(db_day).complete(OWNER_day, "ai_1", "done", {})

    tick(at(23, 59))
    tick(at(0, 30, days=1))  # past midnight, before the Brief's hour
    assert _briefs_day(db_day) == 1
    tick(at(7, 10, days=1))
    assert _briefs_day(db_day) == 2

    latest = MondayBriefService(db_day).get_latest(OWNER_day)
    assert latest.period_end.startswith("2026-10-08T07:10")
    assert latest.period_start.startswith("2026-10-07T00:00")
    rows = _rows(latest)
    assert rows["Decision confirmed: Squash merges only on the rehearsal repository"].detail == "Wed 21:14"
    assert rows["Action done: Fix the login timeout"].detail == "Wed 21:40"
    _assert_plain(latest)


# ── Astra r2: the never-delete law on the launch file ────────────────

CORRUPT = b'{"launches_schema": 1, "launches": [{"launch_id": "lost-'


def _parked(path: Path) -> list[Path]:
    return sorted(path.parent.glob(f"{path.name}.not-read-*"))


def test_a_real_launch_parks_a_corrupt_ledger_byte_for_byte(tmp_path, db_day, monkeypatch) -> None:
    """Astra's producer probe: corrupt file -> a real launch -> the parked
    copy is byte-identical and the new file holds the launch."""
    import json

    from tests.unit.test_agent_hand import _rig as hand_rig

    rig = hand_rig(tmp_path, db_day, monkeypatch)
    path = rig.launches._path
    path.write_bytes(CORRUPT)
    try:
        result = rig.hand.hand(OWNER_day, "action", "ai_1")
        assert result["status"] == "launched", result
        parked = _parked(path)
        assert len(parked) == 1 and parked[0].read_bytes() == CORRUPT
        doc = json.loads(path.read_text(encoding="utf-8"))
        assert [r["launch_id"] for r in doc["launches"]] == [result["launch_id"]]
    finally:
        rig.tmux.ended = True


def test_a_poll_on_a_loaded_ledger_parks_a_corrupt_file(tmp_path, db_day, monkeypatch) -> None:
    """The poll's polled_ns save on an instance that read the file before."""
    rig = _rig(tmp_path, db_day, monkeypatch)
    try:
        path = rig.launches._path
        path.write_bytes(CORRUPT)
        rig.observer.poll_open_prs(OWNER_day)
        parked = _parked(path)
        assert len(parked) == 1 and parked[0].read_bytes() == CORRUPT
        assert rig.launches.read_all(), "the file is readable again"
    finally:
        rig.tmux.ended = True


def test_no_park_no_overwrite(tmp_path) -> None:
    import os
    import stat

    from holdspeak.delivery.factory_launch import LaunchLedger, LaunchLedgerNotRead

    folder = tmp_path / "ledger"
    folder.mkdir()
    path = folder / "agent_launches.json"
    path.write_bytes(CORRUPT)
    ledger = LaunchLedger(path)
    os.chmod(folder, stat.S_IRUSR | stat.S_IXUSR)
    try:
        with pytest.raises(LaunchLedgerNotRead, match="could not be parked"):
            ledger.record({"launch_id": "launch-new"})
    finally:
        os.chmod(folder, stat.S_IRWXU)
    assert path.read_bytes() == CORRUPT and _parked(path) == []
    with pytest.raises(LaunchLedgerNotRead):
        ledger.read_all()


def test_a_removed_file_clears_the_cached_launches(tmp_path) -> None:
    from holdspeak.delivery.factory_launch import LaunchLedger

    path = tmp_path / "agent_launches.json"
    ledger = LaunchLedger(path)
    ledger.record({"launch_id": "launch-a"})
    assert [r["launch_id"] for r in ledger.list()] == ["launch-a"]
    path.unlink()
    assert ledger.list() == [] and ledger.read_all() == []


# ── from test_philo3_03_brief_clock.py: PHILO-3-03 (A3): the brief producer's day moves under test, never the machine clock. ──
#
# The defect: ``MondayBriefService.generate`` read ``datetime.datetime.now()``
# directly (holdspeak/services/monday_brief_service.py compute_window) and the
# route passed no ``now``, so a same-day Generate returned the existing brief
# and the NEXT producer-day could not be reached by any case: recording a
# decision after an empty brief proved nothing about inclusion (COUNCIL.md A3,
# Astra's finding). The seam is ONE injectable clock: ``MondayBriefService(clock=)``,
# defaulting to the real wall clock, wired from the app factory through
# ``MeetingWebServer(brief_clock=)`` -> ``WebContext.brief_clock`` -> the brief
# router. Production never passes it.


TITLE = "Adopt the one desk bus"
ITEM = f"Review decision: {TITLE}"
# A Wednesday, so the window rule is the plain "yesterday 17:00" one.
DAY_ONE_clock = datetime.datetime(2026, 9, 23, 9, 30)


class MovableClock_clock:
    """The test's producer clock: a fixed instant the test moves by hand."""

    def __init__(self, start: datetime.datetime) -> None:
        self.now = start

    def __call__(self) -> datetime.datetime:
        return self.now

    def advance(self, **delta: int) -> None:
        self.now = self.now + datetime.timedelta(**delta)


def test_the_producer_clock_moves_the_brief_day_and_keeps_the_same_day_id(tmp_path, quiet_needs_you):
    db = Database(tmp_path / "brief.db")
    clock = MovableClock_clock(DAY_ONE_clock)
    service = MondayBriefService(db, clock=clock)

    empty = service.generate(None)
    assert empty.is_empty and ITEM not in _texts(empty)
    assert empty.period_end.startswith("2026-09-23")

    db.desk_decisions.upsert(decision_id="decision-a3", title=TITLE, status="proposed")

    same_day = service.generate(None)
    # PHILO-15-09 (B04, ruling 1): the same producer-day keeps the id and
    # makes the body again from the current desk.
    assert same_day.id == empty.id, "same producer-day: the same brief id"
    assert ITEM in _texts(same_day)

    clock.advance(days=1)
    next_day = service.generate(None)
    assert next_day.id != empty.id, "a new producer-day mints a new brief"
    assert next_day.period_end.startswith("2026-09-24")
    assert ITEM in _texts(next_day)
    assert service.get_latest(None).id == next_day.id


def test_the_default_clock_is_the_wall_clock(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    before = datetime.datetime.now().astimezone()
    brief = service.generate(None)
    after = datetime.datetime.now().astimezone()
    generated = datetime.datetime.fromisoformat(brief.generated_at)
    assert before <= generated <= after


def _hub_app(db: Database, monkeypatch, tmp_path, clock) -> TestClient:
    """The routes the hub mounts, with the clock wired the way the app factory wires it."""
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setattr(brief_routes, "get_database", lambda: db)
    monkeypatch.setattr(brief_routes, "get_observer", lambda: None)
    # never the owner's keychain: the People overlay reads a file key store
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people.key"))
    app = FastAPI()

    @app.middleware("http")
    async def owner(request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "test-owner")
        return await call_next(request)

    ctx = WebContext(get_state=lambda: {}, brief_clock=clock)
    app.include_router(build_decisions_router(None))
    app.include_router(build_primitives_router(ctx))
    app.include_router(brief_routes.build_monday_brief_router(ctx))
    return TestClient(app, raise_server_exceptions=False)


def test_the_route_reads_the_wired_clock_across_a_producer_day(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    clock = MovableClock_clock(DAY_ONE_clock)
    client = _hub_app(db, monkeypatch, tmp_path, clock)

    first = client.post("/api/brief/generate")
    assert first.status_code == 200, first.text
    first_id = first.json()["id"]
    assert first.json()["generated_label"] == "GENERATED SEP 23 09:30"

    created = client.post("/api/decisions", json={"title": TITLE, "status": "proposed"})
    assert created.status_code == 201, created.text

    again = client.post("/api/brief/generate")
    assert again.json()["id"] == first_id
    # PHILO-15-09 (B04, ruling 1): Generate on the same day regenerates.
    assert ITEM in again.text

    clock.advance(days=1)
    next_day = client.post("/api/brief/generate")
    assert next_day.status_code == 200, next_day.text
    body = next_day.json()
    assert body["id"] != first_id
    assert ITEM in [item["text"] for item in body["sections"]["decisions"]]
    assert body["generated_label"] == "GENERATED SEP 24 09:30"

    latest = client.get("/api/brief/latest").json()
    assert latest["id"] == body["id"]
    # PHILO-15-09 (B04, ruling 3): the label is the brief's own window
    # (Wednesday 17:00 to Thursday), the range the sent document says too.
    assert latest["period_label"] == "SEP 23-24"
    assert latest["title"] == "Brief · Thursday 24 Sep 2026"


def test_the_web_server_carries_the_clock_to_the_brief_route(tmp_path, monkeypatch, quiet_needs_you):
    """The app factory's one wire: MeetingWebServer(brief_clock=) reaches the brief route."""
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    db = Database(tmp_path / "hub.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setattr(brief_routes, "get_database", lambda: db)
    monkeypatch.setattr(brief_routes, "get_observer", lambda: None)
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people.key"))
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *a, **k: None, on_stop=lambda *a, **k: None, get_state=lambda: {}),
        brief_clock=MovableClock_clock(DAY_ONE_clock),
    )
    made = TestClient(server.app).post("/api/brief/generate")
    assert made.status_code == 200, made.text
    assert made.json()["generated_label"] == "GENERATED SEP 23 09:30"


# ── from test_walk_monday_brief_126.py: HS-126-09 end-to-end walk for the Monday Brief delivery path. ──


OWNER_brief = Principal(PrincipalKind.OWNER, "monday-brief-walk-owner")
NOW = datetime.datetime(2026, 8, 3, 9, 30, tzinfo=datetime.UTC)


@pytest.fixture
def db_brief(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(tools, "get_database", lambda: database)
    monkeypatch.setattr(tools, "get_observer", lambda: None)
    yield database
    reset_database()


def _seed_window(db_brief: Database) -> None:
    timestamp = datetime.datetime(2026, 8, 1, 12, tzinfo=datetime.UTC).timestamp()
    with db_brief._connection() as conn:
        conn.execute(
            """INSERT INTO pipeline_events
               (event_id, timestamp, service, method, principal_kind, args_summary,
                correlation_id, error)
               VALUES (?, ?, ?, ?, 'test', ?, ?, ?)""",
            ("write-note", timestamp, "DecisionRecordService", "create", '{"title":"Plan"}', "note-1", None),
        )
        conn.execute(
            """INSERT INTO pipeline_events
               (event_id, timestamp, service, method, principal_kind, args_summary,
                correlation_id, error)
               VALUES (?, ?, ?, ?, 'test', ?, ?, ?)""",
            ("failed-run", timestamp + 1, "WorkflowService", "run_workflow", "{}", "run-1", "connection reset"),
        )
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("brief-meeting", "2026-08-01T09:00:00", "Brief planning"),
        )
        conn.execute(
            """INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state)
               VALUES (?, ?, ?, ?, ?, 'open', 'accepted')""",
            ("overdue-action", "brief-meeting", "Call the customer", "Ada", (datetime.date.today() - datetime.timedelta(days=1)).isoformat()),
        )
    db_brief.desk_decisions.upsert(
        decision_id="proposed-brief-decision",
        title="Adopt the Monday Brief",
        status="proposed",
    )


def test_walk_generates_and_delivers_all_four_sections(db_brief: Database) -> None:
    _seed_window(db_brief)
    service = MondayBriefService(db_brief)

    brief = service.generate(OWNER_brief, now=NOW)

    assert brief.sections["changed"]
    assert brief.sections["broke"]
    assert brief.sections["waiting"]
    assert brief.sections["decisions"]
    # PHILO-6-02 round 3: only a table row the record proves writes a line.
    assert any(item.text == "Decision recorded" for item in brief.sections["changed"])
    assert brief.sections["broke"][0].text == "Workflow did not complete"
    assert any("Call the customer" in item.text for item in brief.sections["waiting"])
    assert any("Adopt the Monday Brief" in item.text for item in brief.sections["decisions"])

    mcp_brief = tools.dispatch("monday_brief.get", {}, OWNER_brief)
    assert mcp_brief["id"] == brief.id
    assert any(item["source_ref"] == "pipeline:note-1" for item in mcp_brief["sections"]["changed"])

    regenerated = service.generate(OWNER_brief, now=NOW + datetime.timedelta(hours=2))
    assert regenerated.id == brief.id


def test_walk_empty_window_is_honest(db_brief: Database) -> None:
    brief = MondayBriefService(db_brief).generate(OWNER_brief, now=NOW)

    # An empty window on a hub with no summary engine: the one needs-you rule
    # has one member (the meeting-path blocker, the same one the bell counts),
    # and the brief says exactly that. No row is invented for the window.
    # Betterment daily D8: no meeting waits for a summary, so it is speech.
    assert brief.headline == "1 thing waiting."
    assert [item.source_ref for item in brief.sections["waiting"]] == ["blocker:speech"]
    assert not any(brief.sections[name] for name in ("this_week", "changed", "broke", "decisions"))


# ── from test_philo6_02_round3_record_truth.py: PHILO-6-02 round 3 — a brief line states only what the RECORD proves. ──
#
# Astra's round-two check (``pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/
# checks/lane-a-built-astra.md``, "Round two"):
#
# * finding 1 — delegating, reopening or dating work stored ``Follow-up
#   completed``: the fallback read the method NAME (``complete``) as the outcome
#   of all six actions the method takes;
# * finding 2 — "the last event is the outermost outcome" is false: the observer
#   stores CALL-START time (``holdspeak/services/observer.py:113``) and the
#   collector orders by that time, so a nested call sorts AFTER its parent. The
#   round-2 positive control froze the clock, so insertion order decided and
#   masked the field the collector reads;
# * finding 4 — table words that claim more than the call proves (a cached
#   brief is not a made brief; a reconciliation can change nothing).
#
# Every producer below is REAL and observed by the REAL ``@observe_service`` +
# ``SQLiteObserver`` on an ADVANCING clock (each ``time.time()`` read moves the
# clock 1 ms, so a nested call starts after its parent). The brief is the REAL
# ``MondayBriefService.generate``. Each asserted line is checked against the DB
# state it names.


TITLE_record = "Keep retrieval local"


def _advancing_clock(monkeypatch) -> dict[str, float]:
    """The observer's clock moves 1 ms per read: never frozen."""
    now = {"t": EVENTS_AT.timestamp()}

    def tick() -> float:
        now["t"] += 0.001
        return now["t"]

    monkeypatch.setattr(observer_module, "time", SimpleNamespace(time=tick))
    return now


def _events(db: Database) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                """SELECT id, timestamp, service, method, correlation_id, error
                   FROM pipeline_events ORDER BY id ASC"""
            )
        ]


def _brief(db: Database, day: datetime.datetime = GENERATED) -> dict[str, list[str]]:
    brief = MondayBriefService(db).generate(OWNER_record, now=day)
    return {
        section: [item.text for item in items]
        for section, items in brief.sections.items()
    }


def _pipeline_changed(db: Database) -> list[str]:
    with db._connection() as conn:
        return [
            str(row["text"])
            for row in conn.execute(
                """SELECT text FROM monday_brief_items
                   WHERE section = 'changed' AND source_ref LIKE 'pipeline%'"""
            )
        ]


def _desk_decision(db: Database, decision_id: str = "philo603-present") -> str:
    db.desk_decisions.upsert(
        decision_id=decision_id,
        title=TITLE_record,
        status="accepted",
        decision_markdown="Keep retrieval local.",
    )
    return decision_id


# ── finding 2: the outermost call is the one that STARTED first ─────────────


def test_nested_success_keeps_the_parents_title_on_an_advancing_clock(
    tmp_path, monkeypatch
):
    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    decision_id = _desk_decision(db)
    record = DecisionRecordService(
        db, observer=SQLiteObserver(db._connection)
    ).create_from_desk(OWNER_record, decision_id)

    events = _events(db)
    parent = next(e for e in events if e["method"] == "create_from_desk")
    child = next(e for e in events if e["method"] == "create")
    # The real shape the collector reads: one correlation, the parent STARTED
    # first, and the child's receipt was INSERTED first (it finished first).
    assert parent["correlation_id"] == child["correlation_id"]
    assert parent["timestamp"] < child["timestamp"], (parent, child)
    assert child["id"] < parent["id"], (parent, child)

    changed = _brief(db)["changed"]
    # DB evidence: the record the line names exists, minted from this desk
    # decision.
    with db._connection() as conn:
        row = conn.execute(
            "SELECT source_type, source_id FROM decision_records WHERE id = ?",
            (record["id"],),
        ).fetchone()
    assert (row["source_type"], row["source_id"]) == ("desk", decision_id)
    assert f"Decision recorded: {TITLE_record}" in changed, changed
    # One operation, one line: the inner call is never the headline.
    assert _pipeline_changed(db) == [f"Decision recorded: {TITLE_record}"]


def test_nested_failure_stores_only_the_broke_line(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    with pytest.raises(NotFound):
        DecisionRecordService(
            db, observer=SQLiteObserver(db._connection)
        ).create_from_desk(OWNER_record, "philo603-absent")
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM decision_records").fetchone()[0] == 0
    sections = _brief(db)
    assert _pipeline_changed(db) == [], sections["changed"]
    assert sections["broke"] == ["Decision did not record"], sections["broke"]


def test_an_existing_record_is_not_recorded_again(tmp_path, monkeypatch):
    """``create_from_desk`` returns the EXISTING record when one exists: the
    call succeeded but recorded nothing, so it makes no Changed line."""
    db = Database(tmp_path / "hub.db")
    decision_id = _desk_decision(db)
    DecisionRecordService(db).create_from_desk(OWNER_record, decision_id)  # unobserved
    _advancing_clock(monkeypatch)
    again = DecisionRecordService(
        db, observer=SQLiteObserver(db._connection)
    ).create_from_desk(OWNER_record, decision_id)
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM decision_records").fetchone()[0] == 1
    assert [e["method"] for e in _events(db)] == ["create_from_desk"], again
    changed = _brief(db)["changed"]
    assert _pipeline_changed(db) == [], changed


# ── finding 1: the follow-up line comes from the recorded ACTION ────────────


def _action(db: Database, card_id: str, *, status: str = "pending") -> str:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO action_items
               (id, meeting_id, task, owner, due, status, review_state,
                created_at, source_type, source_ref)
               VALUES (?, NULL, ?, NULL, NULL, ?, 'accepted', ?, 'thread', '')""",
            (card_id, f"Task {card_id}", status, "2026-09-24T00:00:00"),
        )
    return card_id


def _action_row(db: Database, card_id: str) -> dict[str, Any]:
    with db._connection() as conn:
        return dict(
            conn.execute(
                "SELECT status, owner, due FROM action_items WHERE id = ?", (card_id,)
            ).fetchone()
        )


def test_delegate_reopen_and_date_never_say_completed(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    service = FollowThroughService(db, observer=SQLiteObserver(db._connection))
    service.complete(OWNER_record, _action(db, "ai-delegate"), "delegate", {"to": "Ana"})
    service.complete(OWNER_record, _action(db, "ai-reopen", status="done"), "reopen")
    service.complete(OWNER_record, _action(db, "ai-due"), "due", {"due_at": "2026-09-30"})

    # DB evidence: none of the three is complete.
    assert _action_row(db, "ai-delegate") == {"status": "pending", "owner": "Ana", "due": None}
    assert _action_row(db, "ai-reopen")["status"] == "open"
    assert _action_row(db, "ai-due") == {"status": "pending", "owner": None, "due": "2026-09-30"}

    _brief(db)
    changed = _pipeline_changed(db)
    assert [text for text in changed if "completed" in text.lower()] == [], changed
    assert sorted(changed) == sorted([
        "Follow-up delegated: Task ai-delegate",
        "Follow-up reopened: Task ai-reopen",
        "Follow-up date set: Task ai-due",
    ]), changed


def test_done_says_completed_and_a_replay_says_nothing(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    already = _action(db, "ai-already", status="done")
    _advancing_clock(monkeypatch)
    service = FollowThroughService(db, observer=SQLiteObserver(db._connection))
    service.complete(OWNER_record, _action(db, "ai-done"), "done")
    replay = service.complete(OWNER_record, already, "done")
    assert replay.get("replayed") is True
    assert _action_row(db, "ai-done")["status"] == "done"

    _brief(db)
    assert _pipeline_changed(db) == ["Follow-up completed: Task ai-done"]


def test_dismiss_and_snooze_make_no_line(tmp_path, monkeypatch):
    """No table row names these actions: the brief says nothing rather than
    a word the record does not prove."""
    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    service = FollowThroughService(db, observer=SQLiteObserver(db._connection))
    service.complete(OWNER_record, _action(db, "ai-dismiss"), "dismiss")
    service.complete(
        OWNER_record, _action(db, "ai-snooze"), "snooze", {"until": "2026-09-30"}
    )
    assert _action_row(db, "ai-dismiss")["status"] == "dismissed"
    _brief(db)
    assert _pipeline_changed(db) == []


def test_a_failed_follow_up_is_told_once_in_broke(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    service = FollowThroughService(db, observer=SQLiteObserver(db._connection))
    with pytest.raises(ValueError):
        service.complete(OWNER_record, "ai-absent", "done")
    sections = _brief(db)
    assert _pipeline_changed(db) == []
    assert sections["broke"] == ["Follow-up did not complete"], sections["broke"]


# ── finding 4: a cached brief, a reconciliation, an unknown call ────────────


def test_a_cached_brief_is_not_a_made_brief(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    observed = MondayBriefService(db, observer=SQLiteObserver(db._connection))
    # The day before: the two observed calls land (clock EVENTS_AT) inside the
    # NEXT day's lookback, the brief that reads them.
    thursday = GENERATED - datetime.timedelta(days=1)
    first = observed.generate(OWNER_record, now=thursday)
    cached = observed.generate(OWNER_record, now=thursday)
    assert cached.id == first.id  # the second call made nothing
    assert [e["method"] for e in _events(db)].count("generate") == 2
    texts = [t for items in _brief(db).values() for t in items]
    assert [t for t in texts if t.startswith("Brief made")] == [], texts


def test_a_reconciliation_that_changed_nothing_makes_no_line(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    observer = SQLiteObserver(db._connection)
    assert ProjectService(db, observer=observer).recover_ask_tasks_on_startup() == []
    flipped, recovered = GateService(db, observer=observer).invalidate_held_on_startup()
    assert (flipped, recovered) == ([], 0)
    assert {e["method"] for e in _events(db)} == {
        "recover_ask_tasks_on_startup", "invalidate_held_on_startup",
    }
    sections = _brief(db)
    assert _pipeline_changed(db) == [], sections["changed"]
    assert sections["broke"] == []


def test_an_unknown_success_writes_nothing_and_its_failure_names_the_object(
    tmp_path, monkeypatch
):
    """A lifecycle transition is outside the table: its success is omitted, its
    failure is ``<Object> did not complete`` (the service's object)."""
    from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService

    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    with pytest.raises(Exception):  # noqa: B017 - NotFound is the producer fact
        DecisionLifecycleService(
            db, observer=SQLiteObserver(db._connection)
        ).transition(OWNER_record, "philo603-absent", "accept")
    sections = _brief(db)
    assert _pipeline_changed(db) == []
    assert sections["broke"] == ["Decision did not complete"], sections["broke"]


# ── the coverage: every row that can write a Changed line, run for real ─────


def _run_desk_record(db: Database, tmp_path, monkeypatch) -> tuple[str, Any]:
    decision_id = _desk_decision(db)
    DecisionRecordService(db, observer=SQLiteObserver(db._connection)).create_from_desk(
        OWNER_record, decision_id
    )
    return f"Decision recorded: {TITLE_record}", lambda: _count(
        db, "SELECT COUNT(*) FROM decision_records WHERE source_id = ?", decision_id
    ) == 1


def _run_meeting_record(db: Database, tmp_path, monkeypatch) -> tuple[str, Any]:
    from tests.unit.test_decision_record_service import _accepted_meeting_decision

    _accepted_meeting_decision(db, "philo603-meeting")
    DecisionRecordService(db, observer=SQLiteObserver(db._connection)).create_from_meeting(
        OWNER_record, "philo603-meeting"
    )
    return "Decision recorded", lambda: _count(
        db, "SELECT COUNT(*) FROM decision_records WHERE source_id = ?", "philo603-meeting"
    ) == 1


def _run_plain_record(db: Database, tmp_path, monkeypatch) -> tuple[str, Any]:
    record = DecisionRecordService(db, observer=SQLiteObserver(db._connection)).create(
        OWNER_record, decision_text="Keep retrieval local.", source_type="desk",
        source_id="philo603-direct",
    )
    return "Decision recorded", lambda: _count(
        db, "SELECT COUNT(*) FROM decision_records WHERE id = ?", record["id"]
    ) == 1


def _run_summary_request(db: Database, tmp_path, monkeypatch) -> tuple[str, Any]:
    from holdspeak.services.meeting_intel_service import MeetingIntelService
    from holdspeak.services.meeting_route_projection import project_route
    from tests.unit.test_meeting_deferred_admission import _queue_rig

    (tmp_path / "rig").mkdir()
    rig_db, *_ = _queue_rig(tmp_path / "rig", monkeypatch)
    meeting = MeetingState(
        id="m-queue",
        started_at=datetime.datetime(2026, 9, 25, 5, 0),
        ended_at=datetime.datetime(2026, 9, 25, 5, 30),
        title="Architecture review",
        tags=[],
        segments=[
            TranscriptSegment(text="we keep retrieval local", speaker="Me",
                              start_time=0.0, end_time=4.0)
        ],
    )
    rig_db.meetings.save_meeting(meeting)
    route = project_route(rig_db, invocation_id=f"meeting:{meeting.id}")
    admitted = MeetingIntelService(
        rig_db, observer=SQLiteObserver(rig_db._connection)
    ).run_intelligence(OWNER_record, meeting.id, expected_selection_hash=route["selection_hash"])
    assert admitted["state"] == "queued"
    return "Summary requested: Architecture review", (
        lambda: rig_db.intel.get_intel_job(meeting.id) is not None
    ), rig_db


def _follow_up(verb: str, payload: dict[str, Any] | None, status: str,
               line: str, proof: dict[str, Any]):
    def run(db: Database, tmp_path, monkeypatch) -> tuple[str, Any]:
        card = _action(db, f"ai-{verb}", status=status)
        FollowThroughService(db, observer=SQLiteObserver(db._connection)).complete(
            OWNER_record, card, verb, payload
        )
        return f"{line}: Task {card}", lambda: all(
            _action_row(db, card)[key] == value for key, value in proof.items()
        )

    return run


def _count(db: Database, sql: str, *args: Any) -> int:
    with db._connection() as conn:
        return int(conn.execute(sql, args).fetchone()[0])


# (service, method, discriminator) -> the producer that runs it for real.
PRODUCERS = {
    ("DecisionRecordService", "create_from_desk", None): _run_desk_record,
    ("DecisionRecordService", "create_from_meeting", None): _run_meeting_record,
    ("DecisionRecordService", "create", None): _run_plain_record,
    ("MeetingIntelService", "run_intelligence", None): _run_summary_request,
    ("FollowThroughService", "complete", "done"): _follow_up(
        "done", None, "pending", "Follow-up completed", {"status": "done"}),
    ("FollowThroughService", "complete", "delegate"): _follow_up(
        "delegate", {"to": "Ana"}, "pending", "Follow-up delegated", {"owner": "Ana"}),
    ("FollowThroughService", "complete", "reopen"): _follow_up(
        "reopen", None, "done", "Follow-up reopened", {"status": "open"}),
    ("FollowThroughService", "complete", "due"): _follow_up(
        "due", {"due_at": "2026-09-30"}, "pending", "Follow-up date set",
        {"due": "2026-09-30"}),
}


def test_every_changed_row_has_a_real_producer():
    from holdspeak.services.monday_brief_service import changed_line_rows

    assert sorted(changed_line_rows(), key=str) == sorted(PRODUCERS, key=str)


@pytest.mark.parametrize("row", sorted(PRODUCERS, key=str), ids=str)
def test_each_changed_row_names_a_change_the_db_holds(tmp_path, monkeypatch, row):
    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    produced = PRODUCERS[row](db, tmp_path, monkeypatch)
    line, proof = produced[0], produced[1]
    if len(produced) == 3:  # the summary rig keeps its own database
        db = produced[2]
    assert proof(), (row, "the change the line names is not in the DB")
    _brief(db)
    changed = _pipeline_changed(db)
    assert changed == [line], (row, changed)
    assert json.dumps(changed)  # plain strings only
