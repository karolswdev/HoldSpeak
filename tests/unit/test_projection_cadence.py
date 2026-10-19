"""Cadence attention projections keep real action-item doors."""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.db import Database


def _add_loop(db: Database, *, loop_id: str, action_id: str, title: str) -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO cadence_loops
               (id, source_type, source_id, title, status, priority,
                updated_at, nudge_count)
               VALUES (?, 'meeting_action', ?, ?, 'open', 'normal', ?, 1)""",
            (loop_id, action_id, title, "2026-10-19T10:00:00+00:00"),
        )


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "projection.db")


def test_automation_result_projection_uses_artifact_door_and_item_title(db: Database) -> None:
    """A Needs-you automation result must not become meeting:None or /cadence."""
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO action_items
               (id, meeting_id, task, owner, due, status, review_state,
                source_type, source_ref)
               VALUES (?, NULL, ?, 'me', '2026-10-19', 'pending', 'reviewed',
                       'automation_result', ?)""",
            ("automation-action", "Review the generated report", "artifact:run-artifact"),
        )
    _add_loop(db, loop_id="automation-loop", action_id="automation-action", title="stale loop title")

    rows = db.projections.list(subject_ref="artifact:run-artifact")["projections"]

    row = next(row for row in rows if row["source_kind"] == "cadence_loop")
    assert row["subject_ref"] == "artifact:run-artifact"
    assert row["detail_url"] == "/?open=artifact:run-artifact"
    assert row["subject_label"] == "Review the generated report"
    assert row["title"] == "Needs you"
    assert row["summary"] == ""
    assert "Cadence" not in row["title"]
    assert "Cadence" not in row["summary"]
    assert "meeting:None" not in row["detail_url"]


def test_meeting_action_projection_keeps_meeting_door(db: Database) -> None:
    """A meeting-backed Door action keeps its meeting ref and title."""
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO meetings (id, title, started_at, created_at)
               VALUES ('meeting-1', 'Planning', '2026-10-19T09:00:00',
                       '2026-10-19T09:00:00')"""
        )
        conn.execute(
            """INSERT INTO action_items
               (id, meeting_id, task, owner, status, review_state)
               VALUES ('meeting-action', 'meeting-1', 'Send the plan', 'me',
                       'pending', 'reviewed')"""
        )
    _add_loop(db, loop_id="meeting-loop", action_id="meeting-action", title="old loop title")

    rows = db.projections.list(subject_ref="meeting:meeting-1")["projections"]

    row = next(row for row in rows if row["source_kind"] == "cadence_loop")
    assert row["subject_ref"] == "meeting:meeting-1"
    assert row["detail_url"] == "/?open=meeting:meeting-1"
    assert row["title"] == "Needs you"
    assert row["summary"] == ""
