"""HS-49-01 — the meeting aftercare aggregation.

Exercises `compute_meeting_aftercare` directly against a real (temp) Database:
open-by-owner, decisions, the since-last-meeting diff, and the honesty rules
(quiet at no-prior / no-change, no fabricated deltas, read-only).
"""
from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.db import get_database, reset_database
from holdspeak.meeting_aftercare import compute_meeting_aftercare
from holdspeak.meeting_session import IntelSnapshot, MeetingState


@pytest.fixture
def db():
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    database = get_database(temp_dir / "test.db")
    yield database
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


def _action(item_id, task, *, owner=None, status="pending", source_timestamp=None):
    return {
        "id": item_id,
        "task": task,
        "owner": owner,
        "due": None,
        "status": status,
        "review_state": "pending",
        "source_timestamp": source_timestamp,
        "created_at": datetime(2026, 6, 4, 10, 0, 0).isoformat(),
    }


def _seed_meeting(db, meeting_id, *, started_at, title, action_items=None):
    db.meetings.save_meeting(
        MeetingState(
            id=meeting_id,
            started_at=started_at,
            title=title,
            intel=IntelSnapshot(timestamp=0.0, action_items=action_items or []),
        )
    )


def _seed_decisions(db, meeting_id, decisions):
    db.plugins.record_artifact(
        artifact_id=f"{meeting_id}-decisions",
        meeting_id=meeting_id,
        artifact_type="decisions",
        title="Decisions",
        structured_json={"decisions": decisions},
        plugin_id="decision_capture",
    )


def test_unknown_meeting_returns_none(db):
    assert compute_meeting_aftercare(db, "nope") is None


def test_empty_meeting_is_quiet(db):
    _seed_meeting(db, "m1", started_at=datetime(2026, 6, 4, 10, 0, 0), title="Solo")
    digest = compute_meeting_aftercare(db, "m1")
    assert digest["is_empty"] is True
    assert digest["open_items"]["total"] == 0
    assert digest["decisions"] == []
    assert digest["since_last_meeting"] is None  # no prior meeting


def test_open_items_grouped_by_owner_unassigned_last(db):
    _seed_meeting(
        db,
        "m1",
        started_at=datetime(2026, 6, 4, 10, 0, 0),
        title="Planning",
        action_items=[
            _action("a1", "Ship the thing", owner="Bob"),
            _action("a2", "Write the doc", owner="alice"),
            _action("a3", "Pick a name"),  # unassigned
            _action("a4", "Done already", owner="alice", status="done"),
        ],
    )
    digest = compute_meeting_aftercare(db, "m1")
    assert digest["is_empty"] is False
    assert digest["open_items"]["total"] == 3  # the done one is excluded
    owners = [g["owner"] for g in digest["open_items"]["by_owner"]]
    assert owners == ["alice", "Bob", None]  # A→Z, unassigned last
    alice = digest["open_items"]["by_owner"][0]
    assert alice["count"] == 1
    assert alice["items"][0]["task"] == "Write the doc"


def test_decisions_surface_with_provenance(db):
    _seed_meeting(db, "m1", started_at=datetime(2026, 6, 4, 10, 0, 0), title="Arch")
    _seed_decisions(
        db,
        "m1",
        [
            {"decision": "Use Postgres", "rationale": "We need transactions", "source_timestamp": 42.5},
            {"decision": "Ship in Q3", "rationale": ""},
            {"decision": "", "rationale": "ignored — no text"},
        ],
    )
    digest = compute_meeting_aftercare(db, "m1")
    assert [d["decision"] for d in digest["decisions"]] == ["Use Postgres", "Ship in Q3"]
    assert digest["decisions"][0]["source_timestamp"] == 42.5
    assert digest["decisions"][1]["rationale"] is None


def test_since_last_meeting_real_diff(db):
    # Prior meeting: one decision, two action items (one later marked done).
    _seed_meeting(
        db,
        "prior",
        started_at=datetime(2026, 6, 1, 9, 0, 0),
        title="Kickoff",
        action_items=[
            _action("p1", "Set up CI", owner="Bob", status="done"),
            _action("p2", "Draft spec", owner="alice"),
        ],
    )
    _seed_decisions(db, "prior", [{"decision": "Use Postgres"}])

    # Current meeting: keeps the Postgres decision, adds a new one; carries the
    # spec task forward and adds a brand-new task.
    _seed_meeting(
        db,
        "current",
        started_at=datetime(2026, 6, 4, 10, 0, 0),
        title="Follow-up",
        action_items=[
            _action("c1", "Draft spec", owner="alice"),  # carried over (not new)
            _action("c2", "Wire the API", owner="Bob"),  # new
        ],
    )
    _seed_decisions(
        db,
        "current",
        [{"decision": "Use Postgres"}, {"decision": "Adopt feature flags"}],
    )

    digest = compute_meeting_aftercare(db, "current")
    since = digest["since_last_meeting"]
    assert since is not None
    assert since["previous_meeting"]["id"] == "prior"
    assert since["changed"] is True
    assert [d["decision"] for d in since["new_decisions"]] == ["Adopt feature flags"]
    assert [a["task"] for a in since["new_actions"]] == ["Wire the API"]
    assert [a["task"] for a in since["closed_actions"]] == ["Set up CI"]


def test_no_change_since_last_meeting_is_quiet(db):
    _seed_meeting(
        db,
        "prior",
        started_at=datetime(2026, 6, 1, 9, 0, 0),
        title="Kickoff",
        action_items=[_action("p1", "Draft spec", owner="alice")],
    )
    _seed_decisions(db, "prior", [{"decision": "Use Postgres"}])
    # Current: identical decision text, identical open task — nothing changed.
    _seed_meeting(
        db,
        "current",
        started_at=datetime(2026, 6, 4, 10, 0, 0),
        title="Repeat",
        action_items=[_action("c1", "Draft spec", owner="alice")],
    )
    _seed_decisions(db, "current", [{"decision": "Use Postgres"}])

    digest = compute_meeting_aftercare(db, "current")
    since = digest["since_last_meeting"]
    assert since["changed"] is False
    assert since["new_decisions"] == []
    assert since["new_actions"] == []
    assert since["closed_actions"] == []
