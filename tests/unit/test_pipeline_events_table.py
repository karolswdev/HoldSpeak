"""Schema coverage for the HS-124 pipeline observer event log."""

from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.db.core import Database, reset_database


@pytest.fixture
def db(tmp_path: Path):
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def test_fresh_database_has_pipeline_events_table(db: Database) -> None:
    with db._connection() as conn:
        table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            ("pipeline_events",),
        ).fetchone()

    assert table is not None


def test_pipeline_event_insert_select_round_trips_all_fields(db: Database) -> None:
    expected = {
        "event_id": "event-123",
        "timestamp": 1_723_000_000.125,
        "service": "workbench",
        "method": "run_item",
        "principal_kind": "owner",
        "principal_identity": "karol",
        "args_summary": '{"item_id":"item-1"}',
        "result_summary": "completed",
        "error": "transient failure",
        "error_code": "E_TRANSIENT",
        "duration_ms": 42.5,
        "correlation_id": "correlation-123",
        "is_async": 1,
    }
    columns = ", ".join(expected)
    placeholders = ", ".join(f":{column}" for column in expected)

    with db._connection() as conn:
        cursor = conn.execute(
            f"INSERT INTO pipeline_events ({columns}) VALUES ({placeholders})",
            expected,
        )
        event = conn.execute(
            "SELECT * FROM pipeline_events WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    assert event is not None
    assert event["id"] == cursor.lastrowid
    assert {column: event[column] for column in expected} == expected


def test_pipeline_events_indexes_exist(db: Database) -> None:
    expected_indexes = {
        "idx_pipeline_events_timestamp",
        "idx_pipeline_events_service_method",
        "idx_pipeline_events_principal",
        "idx_pipeline_events_correlation",
    }

    with db._connection() as conn:
        indexes = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND name LIKE ?",
                ("idx_pipeline_events_%",),
            )
        }

    assert expected_indexes <= indexes
