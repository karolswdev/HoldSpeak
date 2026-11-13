"""The read of failed door jobs stays cheap on a large kernel journal.

Needs you and Today both call ``engine_door.failure_items`` on every read. Its
query asks, for each door job, for the time of its Stop: a correlated subquery
on ``kernel_operations.parent_operation_id``. With no index on that column the
subquery scanned the whole journal one time for each door job: 24 s on the
owner's journal of 99,000 rows (2026-11-13), and the Needs you window stood
empty for that time. The property: the subquery reads an index, on a new
database and on an old one.
"""
from __future__ import annotations

from pathlib import Path

from holdspeak.db import Database
from holdspeak.services import engine_door


def _cancel_subquery_plan(db: Database) -> list[str]:
    with db._connection() as conn:
        rows = conn.execute("EXPLAIN QUERY PLAN " + engine_door.FAILURE_ROWS_SQL).fetchall()
    details = [str(row[-1]) for row in rows]
    return [detail for detail in details if " c " in f" {detail} " or detail.endswith(" c")]


def _assert_the_stop_lookup_reads_an_index(db: Database) -> None:
    plan = _cancel_subquery_plan(db)
    assert plan, "the plan names the Stop lookup (alias c)"
    assert all("SCAN" not in step for step in plan), plan
    assert any("idx_kernel_operations_parent" in step for step in plan), plan


def test_the_stop_lookup_of_failed_door_jobs_reads_an_index(tmp_path: Path) -> None:
    db = Database(tmp_path / "door.db")
    try:
        _assert_the_stop_lookup_reads_an_index(db)
        assert engine_door.failure_items(db) == []
    finally:
        db.close()


def test_an_old_database_gains_the_index_when_it_opens(tmp_path: Path) -> None:
    path = tmp_path / "old.db"
    db = Database(path)
    with db._connection() as conn:
        conn.execute("DROP INDEX idx_kernel_operations_parent")
        conn.commit()
    db.close()

    reopened = Database(path)
    try:
        _assert_the_stop_lookup_reads_an_index(reopened)
    finally:
        reopened.close()
