"""Tests for pipeline event query access."""

from __future__ import annotations

import time
import uuid
from pathlib import Path

import pytest

from holdspeak.db.core import Database
from holdspeak.services.event_query_service import EventQueryService


@pytest.fixture
def db(tmp_path: Path):
    from holdspeak.db.core import Database, reset_database

    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def _insert_event(db: Database, **overrides: object) -> None:
    defaults = dict(
        event_id=str(uuid.uuid4()),
        timestamp=time.time(),
        service="TestService",
        method="do_thing",
        principal_kind="OWNER",
        principal_identity="test",
        args_summary="{}",
        result_summary="{}",
        error=None,
        error_code=None,
        duration_ms=5.0,
        correlation_id="",
        is_async=0,
    )
    defaults.update(overrides)
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO pipeline_events "
            "(event_id, timestamp, service, method, principal_kind, "
            "principal_identity, args_summary, result_summary, error, error_code, "
            "duration_ms, correlation_id, is_async) "
            "VALUES (:event_id, :timestamp, :service, :method, :principal_kind, "
            ":principal_identity, :args_summary, :result_summary, :error, "
            ":error_code, :duration_ms, :correlation_id, :is_async)",
            defaults,
        )


def test_recent_returns_events_newest_first(db: Database) -> None:
    for timestamp in range(1, 6):
        _insert_event(db, timestamp=float(timestamp), method=f"method_{timestamp}")

    events = EventQueryService(db).recent(None)

    assert [event["timestamp"] for event in events] == [5.0, 4.0, 3.0, 2.0, 1.0]


def test_recent_filters_by_service(db: Database) -> None:
    _insert_event(db, service="Alpha")
    _insert_event(db, service="Beta")
    _insert_event(db, service="Alpha")

    events = EventQueryService(db).recent(None, service="Alpha")

    assert len(events) == 2
    assert {event["service"] for event in events} == {"Alpha"}


def test_recent_filters_errors_only(db: Database) -> None:
    for _ in range(3):
        _insert_event(db)
    _insert_event(db, error="failed")
    _insert_event(db, error="also failed")

    events = EventQueryService(db).recent(None, errors_only=True)

    assert len(events) == 2
    assert all(event["error"] is not None for event in events)


def test_recent_limit(db: Database) -> None:
    for timestamp in range(10):
        _insert_event(db, timestamp=float(timestamp))

    events = EventQueryService(db).recent(None, limit=3)

    assert len(events) == 3


def test_stats_counts_and_averages(db: Database) -> None:
    _insert_event(db, service="Alpha", duration_ms=5.0)
    _insert_event(db, service="Alpha", duration_ms=10.0)
    _insert_event(db, service="Beta", duration_ms=20.0)

    stats = EventQueryService(db).stats(None)

    assert stats["total_events"] == 3
    assert stats["by_service"] == [
        {"service": "Alpha", "count": 2, "error_count": 0, "avg_ms": 7.5},
        {"service": "Beta", "count": 1, "error_count": 0, "avg_ms": 20.0},
    ]


def test_stats_error_count(db: Database) -> None:
    _insert_event(db, service="Alpha")
    _insert_event(db, service="Alpha", error="failed")
    _insert_event(db, service="Beta", error="failed")

    stats = EventQueryService(db).stats(None)

    errors_by_service = {
        service["service"]: service["error_count"] for service in stats["by_service"]
    }
    assert errors_by_service == {"Alpha": 1, "Beta": 1}


def test_by_correlation_returns_chain(db: Database) -> None:
    for timestamp in (3.0, 1.0, 2.0):
        _insert_event(db, timestamp=timestamp, correlation_id="chain-1")
    _insert_event(db, correlation_id="chain-2")
    _insert_event(db, correlation_id="chain-3")

    events = EventQueryService(db).by_correlation(None, "chain-1")

    assert [event["timestamp"] for event in events] == [1.0, 2.0, 3.0]


def test_recent_empty(db: Database) -> None:
    assert EventQueryService(db).recent(None) == []
