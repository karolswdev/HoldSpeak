"""HS-201 refusal history keeps the last executed receipt readable."""

from pathlib import Path

from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak.services.meeting_intel_service import MeetingIntelService
from holdspeak.services.meeting_service import MeetingService
from tests.unit.test_hs201_route_counsel import _http_app, _ready_db
from tests.unit.test_hs201_route_contract import OWNER
from holdspeak.services.errors import ConflictError
from holdspeak.services.meeting_route_projection import project_route


def _failed_execution(db: Database, meeting_id: str) -> dict:
    route = project_route(db, invocation_id=f"meeting:{meeting_id}")
    job_id = db.intel.enqueue_intel_job(
        meeting_id,
        transcript_hash="transcript",
        planned_route=route,
    )
    receipt = db.intel.record_run_receipt(
        meeting_id,
        job_id,
        route["selection_hash"],
        "failed",
        {
            "attempts": [
                {
                    "route_leg_ordinal": 1,
                    "send_phase": "provider_no_generation",
                    "outcome": "failed",
                    "child_operation_id": "op-failed-primary",
                }
            ]
        },
    )
    with db._connection() as conn:
        conn.execute(
            "UPDATE intel_jobs SET status='failed', lifecycle_posture='terminal' WHERE job_id=?",
            (job_id,),
        )
        conn.execute(
            "UPDATE meetings SET intel_status='error' WHERE id=?",
            (meeting_id,),
        )
    return receipt


def _meeting_reads(db: Database, meeting_id: str) -> list[dict]:
    return [
        MeetingService(db).get_meeting(OWNER, meeting_id),
        MeetingService(db).list_meetings(OWNER)["meetings"][0],
        MeetingIntelService(db).get_recovery(OWNER, meeting_id),
    ]


def test_failed_execution_survives_restart_and_later_refusals(tmp_path: Path):
    db, meeting = _ready_db(tmp_path, "refusal-history")
    executed = _failed_execution(db, meeting.id)
    db_path = Path(db.db_path)
    db.close()
    db = Database(db_path)
    service = MeetingIntelService(db)

    refusal_ids: list[str] = []
    for expected_hash in (None, "stale-selection"):
        try:
            service.run_intelligence(
                OWNER,
                meeting.id,
                expected_selection_hash=expected_hash,
            )
        except ConflictError as exc:
            assert exc.code in {"selection_hash_required", "selection_drift"}
            assert exc.context["run_receipt"] == executed
            refusal = exc.context["last_refusal"]
            refusal_ids.append(refusal["receipt_id"])
            assert refusal["outcome"] == "refused"
            assert refusal["attempts"] == []
        else:  # pragma: no cover - the refusal fence is the contract under test
            raise AssertionError("route refusal unexpectedly admitted")

        for read in _meeting_reads(db, meeting.id):
            assert read["run_receipt"] == executed
            assert read["last_refusal"]["receipt_id"] == refusal_ids[-1]
            assert read["last_refusal"] != executed

    assert len(set(refusal_ids)) == 2
    assert db.intel.get_run_receipt(meeting.id) == executed
    assert db.intel.get_last_refusal(meeting.id)["receipt_id"] == refusal_ids[-1]

    with TestClient(_http_app(service)) as client:
        response = client.post(
            f"/api/meetings/{meeting.id}/intelligence/run",
            json={"expected_selection_hash": "still-stale"},
        )
    assert response.status_code == 409
    body = response.json()
    assert body["run_receipt"] == executed
    assert body["last_refusal"]["outcome"] == "refused"
    assert body["last_refusal"]["receipt_id"] != refusal_ids[-1]
    latest_refusal_id = body["last_refusal"]["receipt_id"]

    route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    next_job = db.intel.enqueue_intel_job(
        meeting.id,
        transcript_hash="transcript",
        displaced_work=("fresh-execution",),
        planned_route=route,
    )
    next_receipt = db.intel.record_run_receipt(
        meeting.id,
        next_job,
        route["selection_hash"],
        "succeeded",
        {
            "attempts": [
                {
                    "route_leg_ordinal": 1,
                    "send_phase": "provider_returned",
                    "outcome": "succeeded",
                    "child_operation_id": "op-success-after-refusal",
                }
            ]
        },
    )
    assert db.intel.get_run_receipt(meeting.id) == next_receipt
    assert db.intel.get_last_refusal(meeting.id)["receipt_id"] == latest_refusal_id
