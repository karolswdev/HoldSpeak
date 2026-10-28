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
        "idx_pipeline_events_method",
        "idx_pipeline_events_origin",
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


# ── PERF-HUB 2026-10-28: retention (old reads go, writes stay) ─────────────


def _insert_events(db: Database, rows: list[tuple[str, float]]) -> None:
    import uuid

    with db._connection() as conn:
        conn.executemany(
            "INSERT INTO pipeline_events (event_id, timestamp, service, method, "
            "principal_kind) VALUES (?, ?, 'ProjectService', ?, 'owner')",
            [(uuid.uuid4().hex, ts, method) for method, ts in rows],
        )


def _methods(db: Database) -> list[str]:
    with db._connection() as conn:
        return sorted(r["method"] for r in conn.execute("SELECT method FROM pipeline_events"))


def test_read_set_is_one_rule() -> None:
    from holdspeak.db.pipeline_events_retention import is_read_method
    from holdspeak.services.project_service import ROOM_WRITE_METHODS

    for method in ("list_meetings", "get_project", "room", "board", "needs_you",
                   "proposal_needs", "people_store_state", "search_notes", "preview_send",
                   "standing_pages", "pull", "process_pending", "refresh_due_watches", "status"):
        assert is_read_method(method), method
    for method in ("create_project", "save_ask", "run_sweep", "send", "evaluate_once"):
        assert not is_read_method(method), method
    assert not any(is_read_method(m) for m in ROOM_WRITE_METHODS)


def test_prune_removes_old_reads_and_keeps_writes_and_new_reads(db: Database) -> None:
    from holdspeak.db.pipeline_events_retention import prune_read_events

    now = 1_800_000_000.0
    old, new = now - 20 * 86400, now - 2 * 86400
    _insert_events(db, [
        ("list_meetings", old), ("board", old), ("room", old),
        ("create_project", old), ("update_item", old), ("run_sweep", old),
        ("list_meetings", new), ("create_project", new),
    ])

    gone = prune_read_events(db._connection, days=14, now=now, batch_size=2)

    assert gone == 3
    assert _methods(db) == ["create_project", "create_project", "list_meetings",
                            "run_sweep", "update_item"]


def test_retention_zero_keeps_everything(db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.db.pipeline_events_retention import prune_read_events, retention_days

    monkeypatch.setenv("HOLDSPEAK_EVENT_RETENTION_DAYS", "0")
    assert retention_days() == 0
    _insert_events(db, [("list_meetings", 1.0)])

    assert prune_read_events(db._connection) == 0
    assert _methods(db) == ["list_meetings"]
