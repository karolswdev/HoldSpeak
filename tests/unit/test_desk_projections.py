from __future__ import annotations

import json
from datetime import datetime

from holdspeak.cadence.models import OpenLoop
from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState


def _seed(db: Database) -> str:
    meeting = MeetingState(
        id="m1", started_at=datetime.now(), title="Architecture review",
        capture_status="recoverable", capture_failure="private failure detail",
    )
    db.meetings.save_meeting(meeting)
    proposal = db.actuators.record_proposal(
        meeting_id="m1", window_id="w1", plugin_id="slack", plugin_version="1",
        idempotency_key="projection-proposal", target="slack", action="send_message",
        preview="PRIVATE PROPOSAL TEXT", payload={"text": "PRIVATE PAYLOAD"},
    )
    db.recipes.upsert(recipe_id="scout", name="Scout")
    db.capability_invocations.begin(
        invocation_id="run1", definition_ref="persona:scout",
        input_snapshot={"text": "PRIVATE RUN INPUT"}, requested_placement="lan",
    )
    db.capability_invocations.start_attempt(
        invocation_id="run1", attempt_id="attempt1", destination="lan",
        actual_placement={"target_name": "Studio box"},
    )
    db.capability_invocations.finish_attempt("attempt1", state="failed", error="PRIVATE ERROR")
    db.capability_invocations.finish("run1", state="failed", error="PRIVATE ERROR")
    db.steering.record(
        session_key="claude:s1", agent="claude", pane_id="%7",
        text="PRIVATE STEER TEXT", outcome="pane_mismatch",
    )
    db.dictation_journal.record(
        source="dictation", transcript="PRIVATE DICTATION TRANSCRIPT",
        final_text="PRIVATE DICTATION OUTPUT", target_profile="Terminal",
        project_root="/work/holdspeak", warnings=["PRIVATE DICTATION WARNING"],
    )
    db.meetings.record_sync_conflict(
        "m1", local_value={"title": "PRIVATE LOCAL"},
        incoming_value={"title": "PRIVATE REMOTE"},
    )
    db.plugins.record_artifact(
        artifact_id="a1", meeting_id="m1", artifact_type="summary",
        title="Review summary", body_markdown="PRIVATE ARTIFACT BODY", status="draft",
    )
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO intel_jobs
               (meeting_id,status,transcript_hash,attempts,last_error)
               VALUES ('m1','failed','hash',3,'PRIVATE JOB ERROR')"""
        )
    db.cadence.upsert_loop(OpenLoop(
        source_type="proposal", source_id=proposal.id,
        title="Approve architecture follow-up", status="open",
    ))
    return proposal.id


def test_projection_index_covers_subjects_without_copying_sensitive_payloads(tmp_path) -> None:
    db = Database(tmp_path / "projections.db")
    _seed(db)
    result = db.projections.list(limit=200)
    rows = result["projections"]
    source_kinds = {row["source_kind"] for row in rows}
    assert {
        "actuator_proposal", "capability_invocation", "dictation_journal",
        "steering_audit", "meeting",
        "meeting_sync_conflict", "artifact", "intel_job", "cadence_loop",
    }.issubset(source_kinds)
    assert {"meeting:m1", "persona:scout", "coder_session:claude:s1"}.issubset(
        {row["subject_ref"] for row in rows}
    )
    run = next(row for row in rows if row["source_kind"] == "capability_invocation")
    assert run["actual_destination"] == "Studio box"
    assert run["authority_basis"] == "explicit_run"
    assert run["attempt"] == 1
    assert run["outcome"] == "failed"
    assert run["source_api"] == "/api/invocations/run1"
    serialized = json.dumps(result)
    for secret in (
        "PRIVATE PROPOSAL TEXT", "PRIVATE PAYLOAD", "PRIVATE RUN INPUT",
        "PRIVATE STEER TEXT", "PRIVATE LOCAL", "PRIVATE REMOTE",
        "PRIVATE ARTIFACT BODY", "PRIVATE JOB ERROR",
        "PRIVATE DICTATION TRANSCRIPT", "PRIVATE DICTATION OUTPUT",
        "PRIVATE DICTATION WARNING",
    ):
        assert secret not in serialized


def test_dismiss_and_acknowledge_change_projection_only(tmp_path) -> None:
    db = Database(tmp_path / "projections.db")
    proposal_id = _seed(db)
    proposal = db.actuators.get_proposal(proposal_id)
    projection_id = f"actuator:{proposal_id}:proposed"
    assert db.projections.set_presentation(projection_id, action="dismiss") is True
    assert projection_id not in {row["id"] for row in db.projections.list(limit=200)["projections"]}
    hidden = db.projections.list(include_dismissed=True, limit=200)["projections"]
    assert next(row for row in hidden if row["id"] == projection_id)["dismissed"] is True
    assert db.actuators.get_proposal(proposal_id) == proposal

    assert db.projections.set_presentation(projection_id, action="restore") is True
    assert db.projections.set_presentation(projection_id, action="acknowledge") is True
    restored = db.projections.list(limit=200)["projections"]
    assert next(row for row in restored if row["id"] == projection_id)["attention_state"] == "acknowledged"


def test_subject_badges_do_not_follow_drawer_filters(tmp_path) -> None:
    db = Database(tmp_path / "projections.db")
    _seed(db)
    result = db.projections.list(search="no row can match this", projection_kind="receipt")
    assert result["projections"] == []
    assert result["page"]["total"] == 0
    assert result["subject_counts"]["meeting:m1"]["needs_attention"] > 0


def test_projection_pagination_has_no_silent_truncation(tmp_path) -> None:
    db = Database(tmp_path / "projections.db")
    for index in range(225):
        db.steering.record(
            session_key=f"codex:{index}", pane_id=f"%{index}", text="x",
            outcome="delivered",
        )
    first = db.projections.list(limit=100)
    second = db.projections.list(offset=100, limit=100)
    third = db.projections.list(offset=200, limit=100)
    assert first["page"] == {"offset": 0, "limit": 100, "total": 225, "has_more": True}
    assert len(first["projections"]) == len(second["projections"]) == 100
    assert len(third["projections"]) == 25
    assert len({row["id"] for row in first["projections"] + second["projections"] + third["projections"]}) == 225
