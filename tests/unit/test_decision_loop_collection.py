"""HS-125-05 coverage for projecting decision commitments into cadence."""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.cadence.collector import LoopCollector
from holdspeak.db.core import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService
from holdspeak.services.follow_through_service import FollowThroughService


OWNER = Principal(PrincipalKind.OWNER, "decision-loop-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def _accepted_decision(db: Database, decision_id: str = "decision-1") -> str:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("meeting-1", "2026-08-01T09:00:00", "Planning"),
        )
        conn.execute(
            """INSERT INTO decisions
               (id, text, decided_at, source_artifact_id, source_meeting_id, lifecycle)
               VALUES (?, ?, ?, ?, ?, 'recorded')""",
            (
                decision_id,
                "Ship the decision commitment flow",
                "2026-08-01T09:30:00",
                "artifact-1",
                "meeting-1",
            ),
        )
    DecisionLifecycleService(db).transition(OWNER, decision_id, "accept")
    return decision_id


def _committed_decision(db: Database, decision_id: str = "decision-1") -> tuple[str, dict]:
    decision_id = _accepted_decision(db, decision_id)
    commitment = FollowThroughService(db).commit_decision(
        OWNER, decision_id, owner="Ada", due_at="2026-08-14"
    )
    return decision_id, commitment


def test_open_decision_commitment_projects_meeting_decision_loop(db: Database) -> None:
    decision_id, _ = _committed_decision(db)

    LoopCollector(db).collect()

    loop = db.cadence.get_loop_by_source("meeting_decision", decision_id)
    assert loop is not None
    assert loop.source_type == "meeting_decision"
    assert loop.source_id == decision_id
    assert loop.title == "Ship the decision commitment flow"
    assert loop.summary == "Decision from Planning"
    assert loop.owner == "Ada"
    assert loop.due_at == "2026-08-14"


def test_recollecting_decision_commitment_does_not_duplicate_loop(db: Database) -> None:
    decision_id, _ = _committed_decision(db)
    collector = LoopCollector(db)

    collector.collect()
    collector.collect()

    with db._connection() as conn:
        count = conn.execute(
            """SELECT COUNT(*) FROM cadence_loops
               WHERE source_type = 'meeting_decision' AND source_id = ?""",
            (decision_id,),
        ).fetchone()[0]
    assert count == 1


def test_closing_decision_commitment_closes_projected_loop(db: Database) -> None:
    decision_id, commitment = _committed_decision(db)
    collector = LoopCollector(db)
    collector.collect()

    with db._connection() as conn:
        conn.execute(
            "UPDATE decision_commitments SET status = 'closed' WHERE id = ?",
            (commitment["id"],),
        )

    collector.collect()

    loop = db.cadence.get_loop_by_source("meeting_decision", decision_id)
    assert loop is not None
    assert loop.status == "closed"
    assert all(loop.source_id != decision_id for loop in db.cadence.list_loops())


def test_meeting_action_collection_remains_unchanged(db: Database) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("meeting-action", "2026-08-01T09:00:00", "Action meeting"),
        )
        conn.execute(
            """INSERT INTO action_items
               (id, meeting_id, task, owner, status)
               VALUES (?, ?, ?, ?, 'pending')""",
            ("action-1", "meeting-action", "Send the follow-up", "Ada"),
        )

    LoopCollector(db).collect()

    loop = db.cadence.get_loop_by_source("meeting_action", "action-1")
    assert loop is not None
    assert loop.title == "Send the follow-up"
    assert loop.summary == "From Action meeting"
    assert loop.owner == "Ada"
