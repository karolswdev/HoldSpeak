"""Unit coverage for the HS-125 follow-through board projection."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

import holdspeak.services.follow_through_service as follow_through_module
from holdspeak.db.core import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService
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
    review_state: str = "accepted",
) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            (meeting_id, "2026-08-01T09:00:00", "Planning"),
        )
        conn.execute(
            "INSERT INTO action_items "
            "(id, meeting_id, task, owner, due, status, review_state) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (item_id, meeting_id, task, owner, due, status, review_state),
        )


def _card_ids(cards: list[object]) -> list[str]:
    return [card.id for card in cards]  # type: ignore[attr-defined]


def _insert_accepted_decision(db: Database, decision_id: str = "decision-1") -> str:
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("decision-meeting", "2026-08-01T09:00:00", "Decision meeting"),
        )
        conn.execute(
            """INSERT INTO decisions
               (id, text, decided_at, source_artifact_id, source_meeting_id, lifecycle)
               VALUES (?, ?, ?, ?, ?, 'recorded')""",
            (
                decision_id,
                "Ship the accountable commitment flow",
                "2026-08-01T09:30:00",
                "decision-artifact",
                "decision-meeting",
            ),
        )
    DecisionLifecycleService(db).transition(OWNER, decision_id, "accept")
    return decision_id


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


def test_commit_decision_creates_action_and_commitment(db: Database) -> None:
    decision_id = _insert_accepted_decision(db)

    commitment = FollowThroughService(db).commit_decision(OWNER, decision_id)

    assert commitment["decision_id"] == decision_id
    assert commitment["status"] == "open"
    with db._connection() as conn:
        action = conn.execute(
            "SELECT task, meeting_id FROM action_items WHERE id = ?",
            (commitment["action_item_id"],),
        ).fetchone()
        stored = conn.execute(
            "SELECT * FROM decision_commitments WHERE id = ?", (commitment["id"],)
        ).fetchone()
    assert action["task"] == "Ship the accountable commitment flow"
    assert action["meeting_id"] == "decision-meeting"
    assert stored["decision_id"] == decision_id
    assert stored["action_item_id"] == commitment["action_item_id"]


def test_commit_decision_keeps_owner_and_due_date(db: Database) -> None:
    decision_id = _insert_accepted_decision(db)

    commitment = FollowThroughService(db).commit_decision(
        OWNER, decision_id, owner="Ada", due_at="2026-08-14"
    )

    assert commitment["owner"] == "Ada"
    assert commitment["due_at"] == "2026-08-14"
    with db._connection() as conn:
        action = conn.execute(
            "SELECT owner, due FROM action_items WHERE id = ?",
            (commitment["action_item_id"],),
        ).fetchone()
    assert dict(action) == {"owner": "Ada", "due": "2026-08-14"}


def test_board_shows_decision_on_commitment_card(db: Database) -> None:
    decision_id = _insert_accepted_decision(db)
    commitment = FollowThroughService(db).commit_decision(OWNER, decision_id, owner="Ada")

    board = FollowThroughService(db).board(OWNER)
    card = next(card for card in board.waiting if card.id == commitment["action_item_id"])

    assert card.decision_id == decision_id
    assert card.source == "action_item"


def test_accepting_decision_without_commitment_remains_supported(db: Database) -> None:
    decision_id = _insert_accepted_decision(db)

    with db._connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM decision_commitments WHERE decision_id = ?", (decision_id,)
        ).fetchone()[0]
    assert count == 0


def test_pending_review_action_with_past_due_is_unassigned_not_overdue(db: Database) -> None:
    _insert_action(
        db,
        "needs-review",
        due=(date.today() - timedelta(days=1)).isoformat(),
        review_state="pending",
    )

    board = FollowThroughService(db).board(OWNER)

    assert _card_ids(board.unassigned) == ["needs-review"]
    assert board.overdue == []


def test_accepted_review_action_with_past_due_is_overdue(db: Database) -> None:
    _insert_action(
        db,
        "reviewed-overdue",
        due=(date.today() - timedelta(days=1)).isoformat(),
        review_state="accepted",
    )

    board = FollowThroughService(db).board(OWNER)

    assert _card_ids(board.overdue) == ["reviewed-overdue"]


def test_due_lane_changes_as_today_advances(db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
    start = date(2026, 8, 7)
    _insert_action(db, "time-travel", due=(start + timedelta(days=3)).isoformat())

    class FrozenDate(date):
        @classmethod
        def today(cls) -> date:
            return current_day[0]

    current_day = [start]
    monkeypatch.setattr(follow_through_module, "date", FrozenDate)
    service = FollowThroughService(db)

    assert _card_ids(service.board(OWNER).waiting) == ["time-travel"]
    current_day[0] = start + timedelta(days=1)
    assert _card_ids(service.board(OWNER).now) == ["time-travel"]
    current_day[0] = start + timedelta(days=4)
    assert _card_ids(service.board(OWNER).overdue) == ["time-travel"]


def test_snoozed_action_loop_is_excluded_from_active_lanes(db: Database) -> None:
    _insert_action(db, "snoozed", due=(date.today() - timedelta(days=1)).isoformat())
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO cadence_loops
               (id, source_type, source_id, title, status, snoozed_until)
               VALUES (?, 'meeting_action', ?, ?, 'snoozed', ?)""",
            (
                "loop-snoozed",
                "snoozed",
                "Follow up",
                (date.today() + timedelta(days=1)).isoformat(),
            ),
        )

    board = FollowThroughService(db).board(OWNER)

    assert board.now == []
    assert board.waiting == []
    assert board.unassigned == []
    assert board.overdue == []
