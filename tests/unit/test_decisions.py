"""HS-109-01 durable decision identity and lifecycle."""
from __future__ import annotations

import pytest

from holdspeak.db import Database
from holdspeak.db.decisions import (
    DecisionTransitionRefused,
    anchor_decision_timestamp,
    derive_decision_id,
    validate_source_timestamp,
)


def _meeting(db: Database, meeting_id: str, started_at: str = "2026-07-01T09:30:00") -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id,started_at,title) VALUES (?,?,?)",
            (meeting_id, started_at, meeting_id),
        )


def _segments(db: Database, meeting_id: str, *segments: tuple[str, float, float]) -> None:
    with db._connection() as conn:
        for text, start, end in segments:
            conn.execute(
                "INSERT INTO segments (meeting_id,text,speaker,start_time,end_time) VALUES (?,?,?,?,?)",
                (meeting_id, text, "Owner", start, end),
            )


def _artifact(
    db: Database,
    artifact_id: str,
    meeting_id: str,
    entries: list[dict],
) -> None:
    db.plugins.record_artifact(
        artifact_id=artifact_id,
        meeting_id=meeting_id,
        artifact_type="decisions",
        title="Decisions",
        structured_json={"decisions": entries},
        plugin_id="decision_capture",
    )


def test_derived_id_is_stable_and_source_scoped() -> None:
    first = {"decision": "Ship the desk", "rationale": "Owner approved"}
    reordered = {"rationale": "Owner approved", "decision": "Ship the desk"}
    assert derive_decision_id("meeting-1", "artifact-1", first) == derive_decision_id(
        "meeting-1", "artifact-1", reordered
    )
    assert derive_decision_id("meeting-1", "artifact-1", first) != derive_decision_id(
        "meeting-2", "artifact-1", first
    )
    assert derive_decision_id("meeting-1", "artifact-1", first) != derive_decision_id(
        "meeting-1", "artifact-2", first
    )


def test_projection_is_idempotent(tmp_path) -> None:
    db = Database(tmp_path / "decisions.db")
    _meeting(db, "meeting-1")
    db.projects.create_project(project_id="project-1", name="Long memory")
    db.projects.associate_meeting_project(
        meeting_id="meeting-1", project_id="project-1", source="manual", confidence=1.0
    )
    _artifact(
        db,
        "artifact-1",
        "meeting-1",
        [{"decision": "Ship the desk", "rationale": "Owner approved"}],
    )

    # Persisting the artifact IS the projection (the record_artifact
    # chokepoint) — the record exists before any explicit reconcile.
    decision = db.decisions.list()[0]
    first = db.decisions.reconcile_artifact("artifact-1")
    second = db.decisions.reconcile_artifact("artifact-1")

    assert first["unchanged"] == 1 and first["inserted"] == 0
    assert second == {
        "artifacts": 1,
        "decisions": 1,
        "inserted": 0,
        "updated": 0,
        "unchanged": 1,
        "skipped": 0,
    }
    assert [row.id for row in db.decisions.list()] == [decision.id]
    assert [row.id for row in db.decisions.list(project_key="project-1")] == [decision.id]
    assert [row.id for row in db.decisions.list(meeting_id="meeting-1")] == [decision.id]
    assert [row.id for row in db.decisions.list(lifecycle="recorded")] == [decision.id]
    assert decision.project_key == "project-1"
    assert decision.date_basis == "meeting_date"


def test_timestamp_validation_anchor_and_date_basis_transitions(tmp_path) -> None:
    segments = [
        {"text": "We will Ship   the Desk this week", "start_time": 5.0, "end_time": 9.0},
        {"text": "Next topic", "start_time": 10.0, "end_time": 14.0},
    ]
    assert validate_source_timestamp(segments, 5.0) == 5.0
    assert validate_source_timestamp(segments, 14.0) == 14.0
    assert validate_source_timestamp(segments, 14.001) is None
    assert anchor_decision_timestamp(segments, "ship the desk") == 5.0
    assert anchor_decision_timestamp(segments, "ship a desk") is None

    db = Database(tmp_path / "moments.db")
    _meeting(db, "meeting-1", "2026-07-01T09:30:00")
    _segments(
        db,
        "meeting-1",
        ("We will ship the desk this week", 5.0, 9.0),
        ("Next topic", 10.0, 14.0),
    )
    _artifact(
        db,
        "artifact-1",
        "meeting-1",
        [
            {"decision": "Ship the desk", "source_timestamp": 8.5},
            {"decision": "Keep the fuzzy near match absent"},
        ],
    )
    rows = {row.text: row for row in db.decisions.list()}
    reported = rows["Ship the desk"]
    absent = rows["Keep the fuzzy near match absent"]
    assert reported.source_timestamp == 8.5
    assert reported.provenance_label == "reported"
    assert reported.date_basis == "transcript_moment"
    assert reported.decided_at == "2026-07-01T09:30:08.500000"
    assert absent.source_timestamp is None
    assert absent.provenance_label is None
    assert absent.date_basis == "meeting_date"
    assert absent.decided_at == "2026-07-01T09:30:00"


def test_resolver_maps_offset_to_meetings_own_segment(tmp_path) -> None:
    db = Database(tmp_path / "resolver.db")
    _meeting(db, "meeting-1")
    _meeting(db, "meeting-2")
    _segments(
        db,
        "meeting-1",
        ("Opening", 0.0, 4.0),
        ("The decision", 4.0, 9.0),
    )
    _segments(db, "meeting-2", ("Wrong meeting", 4.0, 9.0))

    moment = db.decisions.resolve_segment("meeting-1", 9.0)

    assert moment is not None
    assert moment.meeting_id == "meeting-1"
    assert moment.segment_index == 1
    assert moment.segment_start == 4.0
    assert moment.segment_end == 9.0
    assert moment.text == "The decision"
    assert db.decisions.resolve_segment("meeting-1", 9.001) is None


def test_lifecycle_transitions_and_bidirectional_supersession(tmp_path) -> None:
    db = Database(tmp_path / "lifecycle.db")
    _meeting(db, "meeting-1")
    _artifact(
        db,
        "artifact-1",
        "meeting-1",
        [
            {"decision": "Use the old design"},
            {"decision": "Use the finished web spec"},
            {"decision": "Drop the experiment"},
        ],
    )
    db.decisions.reconcile_artifact("artifact-1")
    rows = {row.text: row for row in db.decisions.list()}

    accepted = db.decisions.accept(rows["Use the old design"].id, actor="owner-session")
    assert accepted.operation == "decision.accept"
    assert accepted.from_lifecycle == "recorded"
    assert accepted.to_lifecycle == "accepted"
    with pytest.raises(
        DecisionTransitionRefused, match="illegal_decision_lifecycle_transition"
    ):
        db.decisions.reject(rows["Use the old design"].id, actor="owner-session")

    db.decisions.reject(rows["Drop the experiment"].id, actor="owner-session")
    receipt = db.decisions.supersede(
        rows["Use the old design"].id,
        rows["Use the finished web spec"].id,
        actor="owner-session",
    )
    assert receipt.to_lifecycle == "superseded"
    old_lineage = db.decisions.get_with_lineage(rows["Use the old design"].id)
    new_lineage = db.decisions.get_with_lineage(rows["Use the finished web spec"].id)
    assert old_lineage["lineage"]["superseded_by"]["id"] == rows[
        "Use the finished web spec"
    ].id
    assert [row["id"] for row in new_lineage["lineage"]["supersedes"]] == [
        rows["Use the old design"].id
    ]


def test_meeting_delete_severs_source_without_deleting_decision(tmp_path) -> None:
    db = Database(tmp_path / "sever.db")
    _meeting(db, "meeting-1")
    _artifact(db, "artifact-1", "meeting-1", [{"decision": "Memory survives"}])
    db.decisions.reconcile_artifact("artifact-1")
    decision_id = db.decisions.list()[0].id

    assert db.meetings.delete_meeting("meeting-1") is True
    survivor = db.decisions.get(decision_id)
    assert survivor is not None
    assert survivor.source_state == "source_deleted"
    assert survivor.source_meeting_id == "meeting-1"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] == 0


def test_identity_survives_provenance_reruns() -> None:
    """A rerun that gains a timestamp or sharper rationale updates the SAME
    record — identity anchors on the decision text (HS-109-02)."""
    bare = {"decision": "Ship the desk", "rationale": "v1"}
    timed = {"decision": "Ship the desk", "rationale": "sharper",
             "source_timestamp": 6.0}
    spaced = {"decision": "  Ship   the desk "}
    assert (
        derive_decision_id("m", "a", bare)
        == derive_decision_id("m", "a", timed)
        == derive_decision_id("m", "a", spaced)
    )
    assert derive_decision_id("m", "a", bare) != derive_decision_id(
        "m", "a", {"decision": "Do not ship the desk"}
    )
