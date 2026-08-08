"""Unit coverage for the HS-125 follow-through board projection."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.follow_through_service import FollowThroughService


OWNER = Principal(PrincipalKind.OWNER, "follow-through-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def _insert_action(
    db: Database,
    item_id: str,
    *,
    meeting_id: str = "meeting-1",
    task: str = "Follow up",
    owner: str | None = "Ada",
    due: str | None = None,
    status: str = "open",
) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            (meeting_id, "2026-08-01T09:00:00", "Planning"),
        )
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, due, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (item_id, meeting_id, task, owner, due, status),
        )


def _card_ids(cards: list[object]) -> list[str]:
    return [card.id for card in cards]  # type: ignore[attr-defined]


def test_empty_database_returns_empty_lanes(db: Database) -> None:
    board = FollowThroughService(db).board(OWNER)

    assert board.now == []
    assert board.waiting == []
    assert board.unassigned == []
    assert board.overdue == []


def test_past_open_action_is_overdue(db: Database) -> None:
    _insert_action(db, "past", due=(date.today() - timedelta(days=1)).isoformat())

    board = FollowThroughService(db).board(OWNER)

    assert _card_ids(board.overdue) == ["past"]


def test_action_due_today_is_now(db: Database) -> None:
    _insert_action(db, "today", due=date.today().isoformat())

    board = FollowThroughService(db).board(OWNER)

    assert _card_ids(board.now) == ["today"]


def test_action_due_in_five_days_is_waiting(db: Database) -> None:
    _insert_action(db, "later", due=(date.today() + timedelta(days=5)).isoformat())

    board = FollowThroughService(db).board(OWNER)

    assert _card_ids(board.waiting) == ["later"]


def test_ownerless_action_is_unassigned_regardless_of_due_date(db: Database) -> None:
    _insert_action(
        db,
        "unowned",
        owner=None,
        due=(date.today() - timedelta(days=1)).isoformat(),
    )

    board = FollowThroughService(db).board(OWNER)

    assert _card_ids(board.unassigned) == ["unowned"]
    assert board.overdue == []


def test_done_action_is_excluded(db: Database) -> None:
    _insert_action(db, "done", due=date.today().isoformat(), status="done")

    board = FollowThroughService(db).board(OWNER)

    assert board.now == []
    assert board.waiting == []
    assert board.unassigned == []
    assert board.overdue == []


def test_filtering_by_project_id(db: Database) -> None:
    _insert_action(db, "in-project", meeting_id="project-meeting")
    _insert_action(db, "outside-project", meeting_id="other-meeting")
    with db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES (?, ?)", ("project-1", "Project"))
        conn.execute(
            "INSERT INTO meeting_projects (meeting_id, project_id) VALUES (?, ?)",
            ("project-meeting", "project-1"),
        )

    board = FollowThroughService(db).board(OWNER, project_id="project-1")

    assert _card_ids(board.waiting) == ["in-project"]


def test_filtering_by_owner(db: Database) -> None:
    _insert_action(db, "ada", owner="Ada")
    _insert_action(db, "grace", owner="Grace")

    board = FollowThroughService(db).board(OWNER, owner="Grace")

    assert _card_ids(board.waiting) == ["grace"]
