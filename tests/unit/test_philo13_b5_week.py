"""PHILO-13-10 B5: the deterministic update reads a linked project week."""
from __future__ import annotations

import json
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.db.decisions import backfill_decisions
from holdspeak.meeting_session import IntelSnapshot, MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.project_delta_service import ProjectDeltaService
from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
from holdspeak.services.proposal_bridge_service import ProposalBridgeService
from holdspeak.services.project_service import ProjectService
from holdspeak.services.project_update_service import ProjectUpdateService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_projects_router


OWNER = Principal(PrincipalKind.OWNER, "philo13-b5-owner")


@pytest.fixture
def week(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "b5-week.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    project_service = ProjectService(db)
    project = project_service.create_project(OWNER, {"name": "Payments ledger cutover"})
    meeting_id = "philo13-b5-meeting"
    db.meetings.save_meeting(MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 9, 29, 9, 0),
        title="Ledger cutover sync",
        intel=IntelSnapshot(
            timestamp=1.0,
            summary="The ledger cutover is ready for the controlled migration.",
            action_items=[
                {
                    "id": "philo13-b5-action-1",
                    "task": "Confirm the migration window",
                    "owner": "Avery",
                    "due": "2026-10-06",
                    "status": "pending",
                    "review_state": "accepted",
                },
                {
                    "id": "philo13-b5-action-2",
                    "task": "Send the rollback checklist",
                    "owner": "Morgan",
                    "due": "2026-10-07",
                    "status": "pending",
                    "review_state": "accepted",
                },
            ],
        ),
    ))
    db.plugins.record_artifact(
        artifact_id="philo13-b5-decisions",
        meeting_id=meeting_id,
        artifact_type="decisions",
        title="Ledger cutover decisions",
        structured_json={"decisions": [{
            "decision": "Use the controlled migration window",
            "rationale": "The rollback path is tested.",
        }]},
        plugin_id="philo13-b5-test-producer",
    )
    db.plugins.record_artifact(
        artifact_id="philo13-b5-bridge-actions",
        meeting_id=meeting_id,
        artifact_type="action_items",
        title="Ledger cutover actions",
        structured_json={"action_items": [{
            "task": "Publish the bridge rollback checklist",
            "owner": "Taylor",
            "due": "2026-10-08",
        }]},
        plugin_id="action_owner_enforcer",
    )
    with db._connection() as conn:
        backfill_decisions(conn)
    decision = db.decisions.list(meeting_id=meeting_id)[0]
    DecisionRecordService(db).create_from_meeting(OWNER, decision.id)
    bridge = ProposalBridgeService(db)
    bridge_action = next(
        proposal for proposal in bridge.bridge_meeting_artifacts(meeting_id)
        if proposal.kind == "action"
    )
    assert "error" not in bridge.confirm_proposal(
        OWNER, bridge_action.id, owner="Taylor",
    )

    # These sources are durable but must not enter a project's linked week.
    db.meetings.save_meeting(MeetingState(
        id="philo13-b5-unlinked",
        started_at=datetime(2026, 9, 30, 9, 0),
        title="Unlinked planning sync",
        intel=IntelSnapshot(
            timestamp=1.0,
            summary="UNLINKED SUMMARY MUST STAY OUT",
            action_items=[{
                "id": "philo13-b5-unlinked-action",
                "task": "UNLINKED ACTION MUST STAY OUT",
                "owner": "Unlinked Owner",
                "status": "pending",
            }],
        ),
    ))
    parked_id = "philo13-b5-parked"
    db.meetings.save_meeting(MeetingState(
        id=parked_id,
        started_at=datetime(2026, 9, 28, 9, 0),
        title="Parked planning sync",
        intel=IntelSnapshot(
            timestamp=1.0,
            summary="PARKED SUMMARY MUST STAY OUT",
            action_items=[{
                "id": "philo13-b5-parked-action",
                "task": "PARKED ACTION MUST STAY OUT",
                "owner": "Parked Owner",
                "status": "pending",
            }],
        ),
    ))
    db.plugins.record_artifact(
        artifact_id="philo13-b5-parked-decision",
        meeting_id=parked_id,
        artifact_type="decisions",
        title="Parked decision",
        structured_json={"decisions": [{
            "decision": "Keep the parked decision record",
            "rationale": "The record remains independently promoted.",
        }]},
        plugin_id="philo13-b5-test-producer",
    )
    with db._connection() as conn:
        backfill_decisions(conn)
    parked_decision = db.decisions.list(meeting_id=parked_id)[0]
    DecisionRecordService(db).create_from_meeting(OWNER, parked_decision.id)
    db.projects.associate_meeting_project(
        meeting_id=parked_id, project_id=project["id"],
        source="test", confidence=1.0,
    )
    assert db.meetings.delete_meeting(parked_id) is True

    app = FastAPI()

    @app.middleware("http")
    async def _owner_edge(request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_projects_router(WebContext(
        get_state=lambda: {}, project_service=project_service,
    )))
    client = TestClient(app)
    assert client.post(f"/api/projects/{project['id']}/meetings/{meeting_id}").status_code == 200

    yield db, project_service, project["id"], meeting_id
    reset_database()


def test_deterministic_draft_reads_real_linked_week(week) -> None:
    db, _project_service, project_id, meeting_id = week
    collector = ProjectEvidenceCollector(db)
    delta_service = ProjectDeltaService(db, collector)
    project_service = ProjectService(db, delta_service=delta_service)
    service = ProjectUpdateService(
        db, project_service=project_service, delta_service=delta_service,
    )

    draft = service.draft_update(OWNER, project_id)
    body = draft["body_md"]
    claims = json.loads(draft["claims_json"])
    refs = {ref for claim in claims for ref in claim["refs"]}

    assert "The ledger cutover is ready for the controlled migration." in body
    assert "Use the controlled migration window" in body
    assert "Confirm the migration window" in body
    assert "Avery" in body
    assert "Send the rollback checklist" in body
    assert "Morgan" in body
    assert f"meeting:{meeting_id}" in refs
    assert "action_item:philo13-b5-action-1" in refs
    assert "action_item:philo13-b5-action-2" in refs
    assert any(ref.startswith("decision:") for ref in refs)
    assert "No decisions in this window." not in body
    assert "No upcoming actions." not in body
    assert "All sources consulted successfully." in body
    assert draft["generator"] == "deterministic"


def test_failed_linked_summary_read_is_named_in_coverage(week, monkeypatch) -> None:
    db, _project_service, project_id, _meeting_id = week
    collector = ProjectEvidenceCollector(db)
    delta_service = ProjectDeltaService(db, collector)
    project_service = ProjectService(db, delta_service=delta_service)
    service = ProjectUpdateService(
        db, project_service=project_service, delta_service=delta_service,
    )

    def fail_summary_read(_meeting_id: str, *, include_parked: bool = False):
        raise RuntimeError("summary store unavailable")

    monkeypatch.setattr(db.meetings, "get_meeting", fail_summary_read)
    draft = service.draft_update(OWNER, project_id)

    body = draft["body_md"]
    manifest = json.loads(draft["source_manifest_json"])
    assert "All sources consulted successfully." not in body
    # The failed read is NAMED in coverage, in plain words (PHILO-15 B53:
    # the update is sent; it carries no raw code); the manifest keeps the code.
    assert "Meetings partly read: meeting summary read failed" in body
    assert "meeting_summary_read_failed" not in body
    assert any(
        caveat["reason"] == "meeting_summary_read_failed"
        for caveat in manifest["caveats"]
    )


def test_week_excludes_unlinked_and_parked_sources_but_keeps_promoted_decision(week) -> None:
    db, _project_service, project_id, _meeting_id = week
    collector = ProjectEvidenceCollector(db)
    delta_service = ProjectDeltaService(db, collector)
    project_service = ProjectService(db, delta_service=delta_service)
    service = ProjectUpdateService(
        db, project_service=project_service, delta_service=delta_service,
    )

    draft = service.draft_update(OWNER, project_id)
    body = draft["body_md"]
    claims = json.loads(draft["claims_json"])
    refs = {ref for claim in claims for ref in claim["refs"]}
    decisions = body.split("## Decisions\n", 1)[1].split("## Risks", 1)[0]

    assert "UNLINKED SUMMARY MUST STAY OUT" not in body
    assert "UNLINKED ACTION MUST STAY OUT" not in body
    assert "PARKED SUMMARY MUST STAY OUT" not in body
    assert "PARKED ACTION MUST STAY OUT" not in body
    assert "Keep the parked decision record" in body
    assert "Publish the bridge rollback checklist" in body
    assert "Publish the bridge rollback checklist" not in decisions
    assert not any("bridge rollback checklist" in claim["text"]
                    for claim in claims if claim["section"] == "decisions")
    assert "meeting:philo13-b5-unlinked" not in refs
    assert "meeting:philo13-b5-parked" not in refs
    assert "action_item:philo13-b5-unlinked-action" not in refs
    assert "action_item:philo13-b5-parked-action" not in refs


def test_deterministic_draft_never_calls_model_boundary(week) -> None:
    db, _project_service, project_id, _meeting_id = week
    collector = ProjectEvidenceCollector(db)
    delta_service = ProjectDeltaService(db, collector)
    project_service = ProjectService(db, delta_service=delta_service)

    class ForbiddenBroker:
        @property
        def inference_runner(self):
            raise AssertionError("deterministic draft called the model boundary")

    service = ProjectUpdateService(
        db,
        project_service=project_service,
        delta_service=delta_service,
        broker=ForbiddenBroker(),
    )
    draft = service.draft_update(OWNER, project_id)

    assert draft["generator"] == "deterministic"
