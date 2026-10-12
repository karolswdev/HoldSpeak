"""Walk 125: Follow-Through end-to-end proof.

Proves the complete follow-through pipeline: meeting → actions → triage →
decision → commitment → board → verbs → provenance → MCP — nothing gets lost.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import tools
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.event_query_service import EventQueryService
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.meeting_aftercare_service import MeetingAftercareService
from holdspeak.services.sqlite_observer import SQLiteObserver


OWNER = Principal(PrincipalKind.OWNER, "walk-125-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def _card(board: object, card_id: str) -> object:
    for lane in (board.now, board.waiting, board.unassigned, board.overdue):  # type: ignore[attr-defined]
        for card in lane:
            if card.id == card_id:
                return card
    raise AssertionError(f"Expected board card {card_id!r} was not found")


def test_walk_follow_through_pipeline(db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
    """Walk real meeting data through triage, follow-through, MCP, and observation."""
    today = date.today()
    observer = SQLiteObserver(db._connection)
    follow_through = FollowThroughService(db, observer=observer)
    aftercare = MeetingAftercareService(db, observer=observer)

    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("walk-meeting", f"{today.isoformat()}T09:00:00", "Follow-through walk"),
        )
        conn.execute(
            "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) "
            "VALUES (?, ?, ?, ?, ?)",
            ("walk-meeting", "Ada will send the launch brief today.", "Ada", 10.0, 30.0),
        )
        conn.executemany(
            "INSERT INTO action_items "
            "(id, meeting_id, task, owner, due, status, review_state, source_timestamp) "
            "VALUES (?, 'walk-meeting', ?, ?, ?, 'pending', 'accepted', ?)",
            [
                ("fully-specified", "Send the launch brief", "Ada", today.isoformat(), 15.0),
                ("ownerless", "Choose an incident lead", None, today.isoformat(), None),
                ("overdue", "Close the prior-week follow-up", "Ben", (today - timedelta(days=1)).isoformat(), None),
                ("future", "Schedule the retrospective", "Cara", (today + timedelta(days=7)).isoformat(), None),
            ],
        )

    digest = aftercare.get_aftercare(OWNER, "walk-meeting")
    assert any(item["id"] == "ownerless" for item in digest["triage"]), (
        "Aftercare triage must retain the meeting action that has no owner"
    )

    # Acceptance makes the extracted actions live work for the board projection.
    with db._connection() as conn:
        conn.execute("UPDATE action_items SET status = 'open' WHERE meeting_id = ?", ("walk-meeting",))

    board = follow_through.board(OWNER)
    assert any(card.id == "overdue" for card in board.overdue), (
        "Past-due meeting action must be shown in the Overdue lane"
    )
    assert any(card.id == "ownerless" for card in board.unassigned), (
        "Ownerless meeting action must be shown in the Unassigned lane"
    )
    assert any(card.id == "future" for card in board.waiting), (
        "Future-due meeting action must be shown in the Waiting lane"
    )
    assert any(card.id == "fully-specified" for card in board.now), (
        "Fully specified action due today must be shown in the Now lane"
    )

    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("decision-meeting", f"{today.isoformat()}T10:00:00", "Decision meeting"),
        )
        conn.execute(
            "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) "
            "VALUES (?, ?, ?, ?, ?)",
            ("decision-meeting", "We accepted the rollout plan.", "Maya", 40.0, 80.0),
        )
        conn.execute(
            "INSERT INTO decisions "
            "(id, text, decided_at, source_artifact_id, source_meeting_id, "
            "source_timestamp, lifecycle, deleted) "
            "VALUES (?, ?, ?, ?, ?, ?, 'accepted', 0)",
            (
                "accepted-rollout",
                "Execute the accepted rollout plan",
                f"{today.isoformat()}T10:30:00",
                "walk-artifact",
                "decision-meeting",
                60.0,
            ),
        )

    commitment = follow_through.commit_decision(
        OWNER,
        "accepted-rollout",
        owner="Nina",
        due_at=(today + timedelta(days=8)).isoformat(),
    )
    board = follow_through.board(OWNER)
    commitment_card = _card(board, commitment["action_item_id"])
    assert commitment_card.decision_id == "accepted-rollout", (
        "Decision commitment card must preserve its originating decision ID"
    )

    sourced_card = _card(board, "fully-specified")
    assert sourced_card.provenance is not None and sourced_card.provenance.available is True, (
        "Action with a verified meeting segment must expose available provenance"
    )
    assert commitment_card.provenance is not None and commitment_card.provenance.available is True, (
        "Decision commitment with a verified decision moment must expose provenance"
    )
    unsourced_card = _card(board, "future")
    assert unsourced_card.provenance is not None and unsourced_card.provenance.available is False, (
        "Action without source data must explicitly report unavailable provenance"
    )

    done = follow_through.complete(OWNER, "overdue", "done")
    assert done["verb"] == "done", "Done verb must report the verb it applied"
    board = follow_through.board(OWNER)
    assert all(card.id != "overdue" for card in board.overdue), (
        "Done card must no longer appear on the follow-through board"
    )

    delegated = follow_through.complete(
        OWNER, commitment["action_item_id"], "delegate", {"to": "maya"}
    )
    assert delegated["verb"] == "delegate", "Delegate verb must report the verb it applied"
    board = follow_through.board(OWNER)
    assert _card(board, commitment["action_item_id"]).owner == "maya", (
        "Delegating a commitment must write its owner through to the board"
    )

    monkeypatch.setattr(tools, "get_database", lambda: db)
    monkeypatch.setattr(tools, "get_observer", lambda: observer)
    mcp_board = tools.dispatch("follow_through.board", {}, OWNER)
    assert any(card["id"] == commitment["action_item_id"] for card in mcp_board["waiting"]), (
        "MCP board tool must return the delegated commitment card"
    )
    mcp_complete = tools.dispatch(
        "follow_through.complete",
        {"card_id": "fully-specified", "verb": "done"},
        OWNER,
    )
    assert mcp_complete["card_id"] == "fully-specified" and mcp_complete["verb"] == "done", (
        "MCP complete tool must apply the requested done verb"
    )
    mcp_board_after_done = tools.dispatch("follow_through.board", {}, OWNER)
    assert all(card["id"] != "fully-specified" for card in mcp_board_after_done["now"]), (
        "MCP completion must be reflected by the subsequent MCP board read"
    )

    events = EventQueryService(db).recent(OWNER, service="FollowThroughService", limit=100)
    methods = {event["method"] for event in events}
    assert {"board", "commit_decision", "complete"}.issubset(methods), (
        "Observer must record the follow-through board, commitment, and verb service calls"
    )
    assert all(event["error"] is None for event in events), (
        "The recorded follow-through service calls must complete without errors"
    )
