"""MCP coverage for the HS-125 Follow-Through board surface."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import resources, tools
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService


OWNER = Principal(PrincipalKind.OWNER, "follow-through-mcp-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


@pytest.fixture
def mcp_db(db: Database, monkeypatch: pytest.MonkeyPatch) -> Database:
    monkeypatch.setattr(tools, "get_database", lambda: db)
    monkeypatch.setattr(tools, "get_observer", lambda: None)
    monkeypatch.setattr(resources, "get_database", lambda: db)
    return db


def _insert_action(db: Database, item_id: str = "action-1") -> str:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("meeting-1", "2026-08-01T09:00:00", "Planning"),
        )
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state) "
            "VALUES (?, ?, ?, ?, ?, 'open', 'accepted')",
            (item_id, "meeting-1", "Follow up with the customer", "Ada", date.today().isoformat()),
        )
    return item_id


def _accepted_decision(db: Database, decision_id: str = "decision-1") -> str:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("decision-meeting", "2026-08-01T09:00:00", "Decision meeting"),
        )
        conn.execute(
            "INSERT INTO decisions (id, text, decided_at, source_artifact_id, source_meeting_id, lifecycle) "
            "VALUES (?, ?, ?, ?, ?, 'recorded')",
            (decision_id, "Ship the commitment flow", "2026-08-01T09:30:00", "artifact-1", "decision-meeting"),
        )
    DecisionLifecycleService(db).transition(OWNER, decision_id, "accept")
    return decision_id


def test_follow_through_board_tool_returns_lane_structure(mcp_db: Database) -> None:
    _insert_action(mcp_db)

    board = tools.dispatch("follow_through.board", {}, OWNER)

    assert set(board) == {"now", "waiting", "unassigned", "overdue"}
    assert board["now"][0]["id"] == "action-1"
    assert board["now"][0]["provenance"]["available"] is False


def test_follow_through_complete_tool_applies_verb(mcp_db: Database) -> None:
    action_id = _insert_action(mcp_db)

    result = tools.dispatch(
        "follow_through.complete", {"card_id": action_id, "verb": "done"}, OWNER
    )

    assert result["card_id"] == action_id
    assert result["verb"] == "done"
    assert all(not cards for cards in tools.dispatch("follow_through.board", {}, OWNER).values())


def test_follow_through_commit_decision_tool_creates_commitment(mcp_db: Database) -> None:
    decision_id = _accepted_decision(mcp_db)

    result = tools.dispatch(
        "follow_through.commit_decision",
        {"decision_id": decision_id, "owner": "Ada", "due_at": "2026-08-14"},
        OWNER,
    )

    assert result["decision_id"] == decision_id
    assert result["owner"] == "Ada"
    with mcp_db._connection() as conn:
        stored = conn.execute(
            "SELECT decision_id, owner, due_at FROM decision_commitments WHERE id = ?", (result["id"],)
        ).fetchone()
    assert dict(stored) == {"decision_id": decision_id, "owner": "Ada", "due_at": "2026-08-14"}


def test_follow_through_resource_returns_board_data(mcp_db: Database) -> None:
    _insert_action(mcp_db)

    result = resources.read_resource("holdspeak://follow-through/board", OWNER)

    contents = result["contents"][0]
    assert contents["mimeType"] == "application/json"
    board = json.loads(contents["text"])
    assert board["now"][0]["id"] == "action-1"
