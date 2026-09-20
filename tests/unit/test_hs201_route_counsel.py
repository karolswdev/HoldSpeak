"""Counsel regressions for the HS-201 route and receipt boundary."""

from datetime import datetime
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.mcp import tools as mcp_tools
from holdspeak.services.errors import ConflictError
from holdspeak.services.meeting_intel_service import MeetingIntelService
from holdspeak.services.meeting_route_projection import project_route
from holdspeak.services.meeting_service import MeetingService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.meetings.intel import build_intel_router
from tests.unit.test_hs201_route_contract import OWNER, assign_summary, summary_profile


def _ready_db(tmp_path: Path, meeting_id: str = "counsel-meeting"):
    db = Database(tmp_path / f"{meeting_id}.db")
    meeting = MeetingState(
        id=meeting_id,
        title="Counsel meeting",
        started_at=datetime.now(),
        segments=[TranscriptSegment("Ship the report.", "Me", 0.0, 1.0)],
    )
    db.meetings.save_meeting(meeting)
    summary_profile(db, "counsel-summary")
    assign_summary(db, ["counsel-summary"])
    return db, meeting


def _http_app(service: MeetingIntelService) -> FastAPI:
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_intel_router(WebContext(
        get_state=lambda: {}, meeting_intel_service=service,
    )))
    return app


def test_missing_hash_does_not_replace_a_completed_run(tmp_path: Path):
    db, meeting = _ready_db(tmp_path, "counsel-complete")
    route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    job_id = db.intel.enqueue_intel_job(
        meeting.id, transcript_hash=meeting.transcript_hash(), planned_route=route,
    )
    receipt = db.intel.record_run_receipt(
        meeting.id, job_id, route["selection_hash"], "succeeded", None,
    )
    with db._connection() as conn:
        conn.execute(
            "UPDATE intel_jobs SET status='succeeded', lifecycle_posture='terminal' WHERE job_id=?",
            (job_id,),
        )
        conn.execute(
            "UPDATE meetings SET intel_status='ready', intel_completed_at=datetime('now') WHERE id=?",
            (meeting.id,),
        )
    with pytest.raises(ConflictError) as refused:
        MeetingIntelService(db).run_intelligence(OWNER, meeting.id)
    assert refused.value.code == "ready"
    assert db.intel.get_run_receipt(meeting.id) == receipt
    assert db.intel.get_latest_intel_job(meeting.id).job_id == job_id
    assert db.meetings.get_meeting(meeting.id).intel_status == "ready"


def test_missing_or_stale_hash_does_not_hide_a_queued_owner(tmp_path: Path):
    db, meeting = _ready_db(tmp_path, "counsel-queued")
    route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    job_id = db.intel.enqueue_intel_job(
        meeting.id, transcript_hash=meeting.transcript_hash(), planned_route=route,
    )
    service = MeetingIntelService(db)
    with pytest.raises(ConflictError) as missing:
        service.run_intelligence(OWNER, meeting.id)
    assert missing.value.code == "queued"
    with pytest.raises(ConflictError) as stale:
        service.run_intelligence(OWNER, meeting.id, expected_selection_hash="stale")
    assert stale.value.code == "selection_drift"
    jobs = db.intel.list_intel_jobs(status="all", limit=20)
    assert [job.job_id for job in jobs] == [job_id]
    assert db.intel.get_intel_job(meeting.id).status == "queued"


@pytest.mark.parametrize("protected", ["running", "reserved"])
def test_protected_state_wins_before_hash_fence(tmp_path: Path, monkeypatch, protected: str):
    db, meeting = _ready_db(tmp_path, f"counsel-{protected}")
    service = MeetingIntelService(db)
    monkeypatch.setattr(db.intel, "get_gesture_state", lambda _meeting_id: protected)
    with pytest.raises(ConflictError) as refused:
        service.run_intelligence(OWNER, meeting.id)
    assert refused.value.code == protected
    assert db.intel.list_intel_jobs(status="all", limit=20) == []


@pytest.mark.parametrize("path", [
    "/api/meetings/counsel-http/intelligence/run",
    "/api/intel/retry/counsel-http",
    "/api/meetings/counsel-http/intel-recovery/retry",
])
def test_all_http_route_refusals_expose_the_same_contract(tmp_path: Path, path: str):
    db, meeting = _ready_db(tmp_path, "counsel-http")
    service = MeetingIntelService(db)
    with TestClient(_http_app(service)) as client:
        response = client.post(path, json={})
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "selection_hash_required"
    assert body["planned_route"] == body["current_planned_route"]
    assert body["run_receipt"]["outcome"] == "refused"
    assert body["run_receipt"]["attempts"] == []


def test_undisclosed_kernel_attempt_is_kept_and_fails_receipt(tmp_path: Path):
    db, meeting = _ready_db(tmp_path, "counsel-receipt")
    route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    job_id = db.intel.enqueue_intel_job(
        meeting.id, transcript_hash=meeting.transcript_hash(), planned_route=route,
    )
    receipt = db.intel.record_run_receipt(
        meeting.id,
        job_id,
        route["selection_hash"],
        "succeeded",
        {"attempts": [{"route_leg_ordinal": 99, "send_phase": "provider_returned", "outcome": "succeeded", "child_operation_id": "op-99"}]},
    )
    assert receipt["outcome"] == "failed"
    assert receipt["attempts"] == [{
        "leg_ordinal": 99,
        "host": "undisclosed",
        "outcome": "succeeded",
        "operation_id": "op-99",
    }]


def test_scheduled_retry_claim_refusal_has_no_terminal_receipt(tmp_path: Path):
    db, meeting = _ready_db(tmp_path, "counsel-retry")
    route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    job_id = db.intel.enqueue_intel_job(
        meeting.id, transcript_hash=meeting.transcript_hash(), planned_route=route,
    )
    assert db.intel.settle_bound_claim_refusal(job_id, ValueError("temporary route check"))
    assert db.intel.get_run_receipt_for_job(job_id) is None


def test_mcp_run_requires_a_disclosed_hash_before_dispatch():
    with pytest.raises(mcp_tools.ToolError):
        mcp_tools._validate_tool_arguments("meeting.run_intelligence", {"meeting_id": "m"})
    schema = mcp_tools._tool_schema("meeting.run_intelligence")
    assert schema is not None
    assert "expected_selection_hash" in schema["required"]


def test_meeting_list_resolves_global_route_once(tmp_path: Path, monkeypatch):
    db, meeting = _ready_db(tmp_path, "counsel-list")
    calls: list[str] = []
    route = project_route(db, invocation_id=f"meeting:{meeting.id}")

    def resolve(_db, *, invocation_id):
        calls.append(str(invocation_id))
        return route

    monkeypatch.setattr("holdspeak.services.meeting_route_projection.project_route", resolve)
    result = MeetingService(db).list_meetings(OWNER)
    assert result["meetings"]
    assert calls == ["meetings:list"]
