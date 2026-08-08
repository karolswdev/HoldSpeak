"""HS-125-07 write-through verbs update follow-through sources together."""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.follow_through_service import FollowThroughService


OWNER = Principal(PrincipalKind.OWNER, "write-through-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def _seed_card(db: Database, *, with_commitment: bool = True) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("meeting-1", "2026-08-01T09:00:00", "Planning"),
        )
        conn.execute(
            """INSERT INTO action_items (id, meeting_id, task, owner, due, status)
               VALUES ('action-1', 'meeting-1', 'Send the proposal', 'Ada', '2026-08-12', 'open')"""
        )
        conn.execute(
            """INSERT INTO cadence_loops
               (id, source_type, source_id, title, status, owner)
               VALUES ('loop-1', 'meeting_action', 'action-1', 'Send the proposal', 'open', 'Ada')"""
        )
        if with_commitment:
            conn.execute(
                """INSERT INTO decision_commitments
                   (id, decision_id, action_item_id, owner, due_at, status, created_at, updated_at)
                   VALUES ('commitment-1', 'decision-1', 'action-1', 'Ada', '2026-08-12',
                           'open', '2026-08-01T09:00:00', '2026-08-01T09:00:00')"""
            )


def _states(db: Database) -> tuple[str, str, str | None]:
    with db._connection() as conn:
        action = conn.execute("SELECT status FROM action_items WHERE id = 'action-1'").fetchone()
        loop = conn.execute("SELECT status FROM cadence_loops WHERE id = 'loop-1'").fetchone()
        commitment = conn.execute(
            "SELECT status FROM decision_commitments WHERE action_item_id = 'action-1'"
        ).fetchone()
    return action["status"], loop["status"], commitment["status"] if commitment else None


def test_done_marks_action_loop_and_commitment_terminal(db: Database) -> None:
    _seed_card(db)

    FollowThroughService(db).complete(OWNER, "action-1", "done")

    assert _states(db) == ("done", "closed", "closed")


def test_dismiss_marks_action_loop_and_commitment_terminal(db: Database) -> None:
    _seed_card(db)

    FollowThroughService(db).complete(OWNER, "action-1", "dismiss")

    assert _states(db) == ("dismissed", "closed", "closed")


def test_snooze_preserves_action_and_snoozes_its_loop(db: Database) -> None:
    _seed_card(db)

    FollowThroughService(db).complete(OWNER, "action-1", "snooze", {"until": "2099-01-01"})

    with db._connection() as conn:
        action_status = conn.execute(
            "SELECT status FROM action_items WHERE id = 'action-1'"
        ).fetchone()[0]
        loop = conn.execute(
            "SELECT status, snoozed_until FROM cadence_loops WHERE id = 'loop-1'"
        ).fetchone()
    assert action_status == "open"
    assert dict(loop) == {"status": "snoozed", "snoozed_until": "2099-01-01"}


def test_delegate_updates_action_and_commitment_owner(db: Database) -> None:
    _seed_card(db)

    FollowThroughService(db).complete(OWNER, "action-1", "delegate", {"to": "maya"})

    with db._connection() as conn:
        action_owner = conn.execute("SELECT owner FROM action_items WHERE id = 'action-1'").fetchone()[0]
        commitment_owner = conn.execute(
            "SELECT owner FROM decision_commitments WHERE action_item_id = 'action-1'"
        ).fetchone()[0]
    assert (action_owner, commitment_owner) == ("maya", "maya")


def test_reopen_after_done_restores_all_linked_records(db: Database) -> None:
    _seed_card(db)
    service = FollowThroughService(db)
    service.complete(OWNER, "action-1", "done")

    service.complete(OWNER, "action-1", "reopen")

    assert _states(db) == ("open", "open", "open")


def test_board_reflects_verb_immediately(db: Database) -> None:
    _seed_card(db)
    service = FollowThroughService(db)

    service.complete(OWNER, "action-1", "done")
    assert all(card.id != "action-1" for lane in service.board(OWNER).__dict__.values() for card in lane)

    service.complete(OWNER, "action-1", "reopen")
    assert any(
        card.id == "action-1"
        for lane in service.board(OWNER).__dict__.values()
        for card in lane
    )


def test_action_only_card_can_complete(db: Database) -> None:
    _seed_card(db, with_commitment=False)

    result = FollowThroughService(db).complete(OWNER, "action-1", "done")

    assert result["commitment_ids"] == []
    assert _states(db) == ("done", "closed", None)
