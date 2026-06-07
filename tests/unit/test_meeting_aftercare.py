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
from holdspeak.meeting_aftercare import (
    build_followup_draft,
    compute_meeting_aftercare,
    resolve_provenance_segment,
)
from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment


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


def _seed_meeting(db, meeting_id, *, started_at, title, action_items=None, segments=None):
    db.meetings.save_meeting(
        MeetingState(
            id=meeting_id,
            started_at=started_at,
            title=title,
            segments=segments or [],
            intel=IntelSnapshot(timestamp=0.0, action_items=action_items or []),
        )
    )


def _segments():
    return [
        TranscriptSegment(text="Kicking off the design", speaker="Me", start_time=0.0, end_time=10.0),
        TranscriptSegment(text="We should use Postgres", speaker="Sam", start_time=10.0, end_time=25.0),
        TranscriptSegment(text="And add a rate limiter", speaker="Priya", start_time=25.0, end_time=40.0),
    ]


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


# --- HS-49-02: transcript provenance (the "show me the moment" seek target) ---


def test_resolve_provenance_picks_segment_at_or_before_timestamp():
    segments = _segments()
    # 18.0 falls inside the second segment [10, 25).
    prov = resolve_provenance_segment(segments, 18.0)
    assert prov["segment_index"] == 1
    assert prov["segment_start"] == 10.0
    assert prov["speaker"] == "Sam"
    assert prov["source_timestamp"] == 18.0


def test_resolve_provenance_clamps_and_guards():
    segments = _segments()
    # A real 0.0 resolves to the opening segment (not a fake jump).
    assert resolve_provenance_segment(segments, 0.0)["segment_index"] == 0
    # Past the last segment start clamps to the last segment.
    assert resolve_provenance_segment(segments, 999.0)["segment_index"] == 2
    # No timestamp / no segments → no affordance.
    assert resolve_provenance_segment(segments, None) is None
    assert resolve_provenance_segment([], 5.0) is None


def test_open_items_carry_provenance_only_when_real(db):
    _seed_meeting(
        db,
        "m1",
        started_at=datetime(2026, 6, 4, 10, 0, 0),
        title="Design",
        segments=_segments(),
        action_items=[
            _action("a1", "Wire the rate limiter", owner="Priya", source_timestamp=30.0),
            _action("a2", "Pick a name"),  # no source_timestamp
        ],
    )
    by_owner = {g["owner"]: g for g in compute_meeting_aftercare(db, "m1")["open_items"]["by_owner"]}
    priya_item = by_owner["Priya"]["items"][0]
    assert priya_item["provenance"]["segment_index"] == 2  # 30.0 → third segment
    unassigned_item = by_owner[None]["items"][0]
    assert unassigned_item["provenance"] is None


def test_decisions_carry_provenance_when_timestamped(db):
    _seed_meeting(db, "m1", started_at=datetime(2026, 6, 4, 10, 0, 0), title="Design", segments=_segments())
    _seed_decisions(
        db,
        "m1",
        [
            {"decision": "Use Postgres", "source_timestamp": 12.0},
            {"decision": "Ship in Q3"},  # no moment
        ],
    )
    decisions = compute_meeting_aftercare(db, "m1")["decisions"]
    assert decisions[0]["provenance"]["segment_index"] == 1
    assert decisions[1]["provenance"] is None


# --- HS-49-04: the local follow-up draft (preview + copy) ---


def test_followup_draft_includes_decisions_owners_and_due(db):
    _seed_meeting(
        db,
        "m1",
        started_at=datetime(2026, 6, 4, 10, 0, 0),
        title="API design",
        action_items=[
            {**_action("a1", "Wire the rate limiter", owner="Priya"), "due": "Friday"},
            _action("a2", "Pick a name"),  # unassigned, no due
        ],
    )
    _seed_decisions(db, "m1", [{"decision": "Use Postgres", "rationale": "Transactions"}])
    draft = build_followup_draft(compute_meeting_aftercare(db, "m1"))
    assert "# Follow-up: API design" in draft
    assert "## What we decided" in draft
    assert "- Use Postgres. Why: Transactions" in draft
    assert "## Open items" in draft
    assert "- Priya: Wire the rate limiter (due Friday)" in draft
    assert "- Unassigned: Pick a name" in draft
    assert "—" not in draft  # no em dashes in the copy


def test_followup_draft_empty_is_honest_not_padded(db):
    _seed_meeting(db, "m1", started_at=datetime(2026, 6, 4, 10, 0, 0), title="Quiet")
    draft = build_followup_draft(compute_meeting_aftercare(db, "m1"))
    assert "Nothing was decided and nothing is open" in draft
    assert "## " not in draft  # no empty section headers


def test_followup_draft_since_section(db):
    _seed_meeting(
        db,
        "prior",
        started_at=datetime(2026, 6, 1, 9, 0, 0),
        title="Kickoff",
        action_items=[_action("p1", "Stand up CI", status="done")],
    )
    _seed_decisions(db, "prior", [{"decision": "Use Postgres"}])
    _seed_meeting(
        db,
        "current",
        started_at=datetime(2026, 6, 4, 10, 0, 0),
        title="Follow-up",
        action_items=[_action("c1", "Wire the API", owner="Sam")],
    )
    _seed_decisions(db, "current", [{"decision": "Adopt feature flags"}])
    draft = build_followup_draft(compute_meeting_aftercare(db, "current"))
    assert "## Since Kickoff" in draft
    assert "New decisions:" in draft and "- Adopt feature flags" in draft
    assert "New action items:" in draft and "- Wire the API" in draft
    assert "Closed since last time:" in draft and "- Stand up CI" in draft


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
