"""Betterment D3 follow-up: a kept promise is an open loop.

Confirm (and D3's keep on arrival) writes an action item ``open``;
``list_action_items(include_completed=False)`` read ``pending`` only, so the
cadence collector made no loop for any kept item. A decision commitment's
action (also ``open``) stays the decision's one loop.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.cadence.collector import LoopCollector
from holdspeak.db.core import Database, reset_database


@pytest.fixture
def db(tmp_path: Path):
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def _seed(db: Database) -> None:
    with db._connection() as conn:
        conn.execute("INSERT INTO meetings (id, started_at, title) VALUES ('m1', '2026-10-16T09:00:00', 'Platform sync')")
        for item_id, task, status, review in (
            ("a-pending", "Review the rollout plan", "pending", "pending"),
            ("a-kept", "Send Mira the runbook", "open", "accepted"),
            ("a-done", "Book the room", "done", "accepted"),
            ("a-dismissed", "Old idea", "dismissed", "accepted"),
            ("a-committed", "Ship the cutover", "open", "accepted"),
        ):
            conn.execute(
                "INSERT INTO action_items (id, meeting_id, task, owner, status, review_state, created_at)"
                " VALUES (?, 'm1', ?, 'Me', ?, ?, '2026-10-16T09:30:00')",
                (item_id, task, status, review),
            )
        conn.execute(
            "INSERT INTO decision_commitments (id, decision_id, action_item_id, status, created_at, updated_at)"
            " VALUES ('c1', 'd1', 'a-committed', 'open', '2026-10-16', '2026-10-16')")


def test_list_action_items_reads_pending_and_kept_items(db: Database) -> None:
    _seed(db)
    live = {item.id for item in db.meetings.list_action_items(include_completed=False)}
    assert live == {"a-pending", "a-kept", "a-committed"}
    every = {item.id for item in db.meetings.list_action_items(include_completed=True)}
    assert every == {"a-pending", "a-kept", "a-done", "a-dismissed", "a-committed"}


def test_the_collector_makes_a_loop_for_a_kept_item_and_none_twice(db: Database) -> None:
    _seed(db)
    LoopCollector(db).collect()

    kept = db.cadence.get_loop_by_source("meeting_action", "a-kept")
    assert kept is not None and kept.title == "Send Mira the runbook" and not kept.needs_review
    assert db.cadence.get_loop_by_source("meeting_action", "a-pending") is not None
    for gone in ("a-done", "a-dismissed", "a-committed"):
        assert db.cadence.get_loop_by_source("meeting_action", gone) is None, gone
