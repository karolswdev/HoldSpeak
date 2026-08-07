"""Persistence coverage for the HS-124 SQLite pipeline observer."""

from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.services.observer import PipelineEvent
from holdspeak.services.sqlite_observer import SQLiteObserver


@pytest.fixture
def db(tmp_path: Path):
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def _make_event(**overrides: object) -> PipelineEvent:
    defaults = dict(
        event_id="evt-1",
        timestamp=1723000000.0,
        service="TestService",
        method="do_thing",
        principal_kind="OWNER",
        principal_identity="test",
        args_summary="{}",
        result_summary="{}",
        error=None,
        error_code=None,
        duration_ms=5.0,
        correlation_id="corr-1",
        is_async=False,
    )
    defaults.update(overrides)
    return PipelineEvent(**defaults)


def test_on_event_inserts_and_round_trips(db: Database) -> None:
    event = _make_event(
        timestamp=1723000000.125,
        args_summary='{"input":"value"}',
        result_summary='{"status":"ok"}',
        error="transient failure",
        error_code="E_TRANSIENT",
        duration_ms=42.5,
        is_async=True,
    )

    SQLiteObserver(db._connection).on_event(event)

    with db._connection() as conn:
        row = conn.execute(
            "SELECT * FROM pipeline_events WHERE event_id = ?", (event.event_id,)
        ).fetchone()

    assert row is not None
    assert row["event_id"] == event.event_id
    assert row["timestamp"] == event.timestamp
    assert row["service"] == event.service
    assert row["method"] == event.method
    assert row["principal_kind"] == event.principal_kind
    assert row["principal_identity"] == event.principal_identity
    assert row["args_summary"] == event.args_summary
    assert row["result_summary"] == event.result_summary
    assert row["error"] == event.error
    assert row["error_code"] == event.error_code
    assert row["duration_ms"] == event.duration_ms
    assert row["correlation_id"] == event.correlation_id
    assert row["is_async"] == int(event.is_async)


def test_on_event_broken_connection_does_not_raise() -> None:
    def broken_connection() -> None:
        raise RuntimeError("database unavailable")

    SQLiteObserver(broken_connection).on_event(_make_event())


def test_bulk_insert_and_ordering(db: Database) -> None:
    observer = SQLiteObserver(db._connection)
    events = [
        _make_event(event_id=f"evt-{index}", timestamp=1723000000.0 + index)
        for index in range(100)
    ]

    for event in events:
        observer.on_event(event)

    with db._connection() as conn:
        rows = conn.execute(
            "SELECT event_id FROM pipeline_events ORDER BY timestamp DESC"
        ).fetchall()

    assert len(rows) == 100
    assert [row["event_id"] for row in rows] == [event.event_id for event in reversed(events)]
