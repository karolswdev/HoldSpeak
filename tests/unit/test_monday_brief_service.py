"""Tests for the persistent Monday Brief generation model."""
from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo

from holdspeak.db.core import Database, read_schema_version
from holdspeak.db.schema import SCHEMA_VERSION
from holdspeak.services.monday_brief_service import MondayBriefService


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
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'monday_briefs'"
        ).fetchone() is not None
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'monday_brief_items'"
        ).fetchone() is not None
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name = 'idx_monday_brief_items_brief'"
        ).fetchone() is not None
