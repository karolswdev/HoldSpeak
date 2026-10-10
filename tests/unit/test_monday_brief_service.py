"""Tests for the persistent Monday Brief generation model."""

from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo

import pytest

from holdspeak.db.core import Database
from holdspeak.services.monday_brief_service import BriefItem, MondayBriefService
from tests.unit.brief_rule_stub import quiet_needs_you  # noqa: F401  (a fixture)


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


def test_a_brief_is_stale_after_a_new_meeting_decision_or_engine(tmp_path, quiet_needs_you):
    from tests.unit.test_hs172_loop_wire import assign_meeting_engine

    real_now = datetime.datetime.now().replace(microsecond=0)
    clock = {"now": real_now}
    db, service = _stale_service(tmp_path, clock)
    base = real_now - datetime.timedelta(minutes=30)  # same day unless run at 00:00-00:30
    brief = service.generate(None, now=base)
    assert service.is_stale(brief) is False

    meeting_at = (base + datetime.timedelta(minutes=5)).isoformat()
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, ended_at, title, duration_seconds, intel_status, capture_status, created_at) "
            "VALUES ('m-new', ?, ?, 'Standup', 60, 'disabled', 'finalized', ?)",
            (meeting_at, meeting_at, meeting_at),  # the row's durable time (Astra r1)
        )
    assert service.is_stale(brief) is True

    brief = service.generate(None, now=base + datetime.timedelta(minutes=10))
    assert service.is_stale(brief) is False
    decided_at = (base + datetime.timedelta(minutes=15)).isoformat()
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO decision_records (id, decision_text, rationale, source_type, source_id, created_at, updated_at) "
            "VALUES ('dr-new', 'Ship it', '', 'decision', 'd1', ?, ?)", (decided_at, decided_at),
        )
    assert service.is_stale(brief) is True

    brief = service.generate(None, now=base + datetime.timedelta(minutes=20))
    assert service.is_stale(brief) is False
    assign_meeting_engine(db)  # an engine assigned now, after the brief was made
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
