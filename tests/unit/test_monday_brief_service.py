"""Tests for the persistent Monday Brief generation model."""

from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo

from holdspeak.db.core import Database, read_schema_version
from holdspeak.db.schema import SCHEMA_VERSION
from holdspeak.services.monday_brief_service import BriefItem, MondayBriefService


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

    assert period_start == datetime.datetime(2026, 7, 31, 17)
    assert period_end == now


def test_compute_window_on_wednesday_starts_previous_day(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    now = datetime.datetime(2026, 8, 5, 9, 30)

    period_start, period_end = service.compute_window(now)

    assert period_start == datetime.datetime(2026, 8, 4, 17)
    assert period_end == now


def test_compute_window_preserves_timezone_across_dst(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    eastern = ZoneInfo("America/New_York")
    now = datetime.datetime(2026, 3, 9, 9, 30, tzinfo=eastern)

    period_start, period_end = service.compute_window(now)

    assert period_start == datetime.datetime(2026, 3, 6, 17, tzinfo=eastern)
    assert period_start.utcoffset() == datetime.timedelta(hours=-5)
    assert period_end.utcoffset() == datetime.timedelta(hours=-4)


def test_generate_creates_empty_brief(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    now = datetime.datetime(2026, 8, 3, 9, 30)

    brief = service.generate(None, now=now)

    assert brief.period_start == "2026-07-31T17:00:00"
    assert brief.period_end == now.isoformat()
    assert brief.sections == {
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


def test_generate_collects_write_operations_as_persisted_changes(tmp_path, monkeypatch):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    monkeypatch.setattr(service, "_collect_breakage", lambda *_: [], raising=False)
    monkeypatch.setattr(service, "_collect_waiting", lambda *_: [], raising=False)
    monkeypatch.setattr(service, "_collect_decisions", lambda *_: [], raising=False)
    _insert_pipeline_event(
        service,
        event_id="created-note",
        timestamp=_utc_timestamp(1),
        service_name="NoteService",
        method="create_note",
        correlation_id="note-1",
        args_summary='{"title":"Plan"}',
    )

    brief = service.generate(
        None, now=datetime.datetime(2026, 8, 3, 9, 30, tzinfo=datetime.UTC)
    )

    assert [
        (item.section, item.text, item.source_ref) for item in brief.sections["changed"]
    ] == [("changed", "NoteService.create_note", "pipeline:note-1")]
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

    assert (
        service._collect_changes(
            "2026-08-01T00:00:00+00:00", "2026-08-02T00:00:00+00:00"
        )
        == []
    )


def test_collect_changes_collapses_a_correlated_retry(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    for event_id, timestamp, error in (
        ("first-attempt", _utc_timestamp(1, 12), "connection reset"),
        ("retry", _utc_timestamp(1, 12) + 10, None),
    ):
        _insert_pipeline_event(
            service,
            event_id=event_id,
            timestamp=timestamp,
            service_name="WorkflowService",
            method="run_workflow",
            correlation_id="run-1",
            args_summary='{"workflow_id":"weekly"}',
            error=error,
        )

    changes = service._collect_changes(
        "2026-08-01T00:00:00+00:00", "2026-08-02T00:00:00+00:00"
    )

    assert len(changes) == 1
    assert changes[0].text == "WorkflowService.run_workflow"
    assert changes[0].source_ref == "pipeline:run-1"


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
            service_name="NoteService",
            method="update_note",
            args_summary='{"note_id":"weekly"}',
            error=error,
        )

    changes = service._collect_changes(
        "2026-08-01T00:00:00+00:00", "2026-08-02T00:00:00+00:00"
    )

    assert len(changes) == 1
    assert changes[0].source_ref == "pipeline-event:failed"


def test_collect_changes_excludes_events_outside_the_window(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    _insert_pipeline_event(
        service,
        event_id="outside",
        timestamp=_utc_timestamp(3),
        service_name="NoteService",
        method="update_note",
    )

    assert (
        service._collect_changes(
            "2026-08-01T00:00:00+00:00", "2026-08-02T00:00:00+00:00"
        )
        == []
    )


def test_collect_changes_returns_no_items_for_an_empty_window(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))

    assert (
        service._collect_changes(
            "2026-08-01T00:00:00+00:00", "2026-08-02T00:00:00+00:00"
        )
        == []
    )


def test_schema_migrates_v39_to_v40(tmp_path):
    path = tmp_path / "v39.db"
    Database(path)
    with Database(path)._connection() as conn:
        conn.execute("DROP TABLE monday_brief_items")
        conn.execute("DROP TABLE monday_briefs")
        conn.execute("DELETE FROM schema_version")
        conn.execute("INSERT INTO schema_version (version) VALUES (39)")

    migrated = Database(path)

    assert SCHEMA_VERSION == 40
    assert read_schema_version(path) == 40
    with migrated._connection() as conn:
        assert (
            conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'monday_briefs'"
            ).fetchone()
            is not None
        )
        assert (
            conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'monday_brief_items'"
            ).fetchone()
            is not None
        )
        assert (
            conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND name = 'idx_monday_brief_items_brief'"
            ).fetchone()
            is not None
        )


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


def test_compose_empty_brief_has_honest_headline(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))

    headline, sections = service._compose({})

    assert headline == "Nothing material changed."
    assert sections == {"changed": [], "broke": [], "waiting": [], "decisions": []}
    brief = service.generate(None, now=datetime.datetime(2026, 8, 3, 9, 30))
    assert brief.headline == "Nothing material changed."
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
