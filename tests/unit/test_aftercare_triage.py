"""HS-125-04 — aftercare triage for incomplete open actions."""
from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.db import get_database, reset_database
from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
from holdspeak.principals import UNAUTHENTICATED
from holdspeak.services.meeting_aftercare_service import MeetingAftercareService


@pytest.fixture
def db():
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    database = get_database(temp_dir / "test.db")
    yield database
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


def _action(
    item_id: str,
    *,
    owner: str | None = "Sam",
    due: str | None = "2026-08-14",
    status: str = "pending",
    review_state: str = "accepted",
    source_timestamp: float | None = 12.0,
) -> dict[str, object]:
    return {
        "id": item_id,
        "task": f"Action {item_id}",
        "owner": owner,
        "due": due,
        "status": status,
        "review_state": review_state,
        "source_timestamp": source_timestamp,
        "created_at": datetime(2026, 8, 7, 10, 0, 0).isoformat(),
    }


def _aftercare(db, actions):
    db.meetings.save_meeting(
        MeetingState(
            id="meeting-1",
            started_at=datetime(2026, 8, 7, 10, 0, 0),
            title="Triage meeting",
            segments=[
                TranscriptSegment(
                    text="We need to follow up.",
                    speaker="Sam",
                    start_time=10.0,
                    end_time=20.0,
                )
            ],
            intel=IntelSnapshot(timestamp=20.0, action_items=actions),
        )
    )
    return MeetingAftercareService(db).get_aftercare(UNAUTHENTICATED, "meeting-1")


def test_fully_specified_actions_have_empty_triage(db):
    digest = _aftercare(db, [_action("complete")])

    assert digest["triage"] == []


def test_ownerless_action_has_no_owner_gap(db):
    digest = _aftercare(db, [_action("ownerless", owner=None)])

    assert digest["triage"][0]["id"] == "ownerless"
    assert digest["triage"][0]["gaps"] == ["no_owner"]
    assert digest["triage"][0]["source"] == {
        "meeting_id": "meeting-1",
        "source_timestamp": 12.0,
        "segment": {
            "source_timestamp": 12.0,
            "segment_index": 0,
            "segment_start": 10.0,
            "speaker": "Sam",
            "text_preview": "We need to follow up.",
        },
    }


def test_undated_action_has_no_date_gap(db):
    digest = _aftercare(db, [_action("undated", due=None)])

    assert digest["triage"][0]["gaps"] == ["no_date"]


def test_pending_review_action_has_needs_review_gap(db):
    digest = _aftercare(db, [_action("unreviewed", review_state="pending")])

    assert digest["triage"][0]["gaps"] == ["needs_review"]


def test_action_with_multiple_gaps_lists_each_gap(db):
    digest = _aftercare(
        db,
        [_action("incomplete", owner=" ", due="", review_state="pending")],
    )

    triage = digest["triage"][0]
    assert triage["text"] == "Action incomplete"
    assert triage["status"] == "pending"
    assert triage["gaps"] == ["needs_review", "no_owner", "no_date"]


@pytest.mark.parametrize("status", ["done", "dismissed"])
def test_closed_actions_do_not_appear_in_triage(db, status):
    digest = _aftercare(
        db,
        [_action("closed", owner=None, due=None, review_state="pending", status=status)],
    )

    assert digest["triage"] == []
