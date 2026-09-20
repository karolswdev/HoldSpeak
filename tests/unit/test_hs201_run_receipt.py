"""HS-201-03 fences: the run gesture binds a disclosed route and receipt."""
from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.intel import ActionItem, IntelResult
from holdspeak.kernel.provider_signals import ProviderPermanentNoGeneration
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.services.errors import ConflictError
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.meeting_intel_service import MeetingIntelService
from holdspeak.services.meeting_route_projection import project_route
from tests.unit.test_hs201_route_contract import OWNER, assign_summary, summary_profile
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim


@pytest.fixture
def ready_meeting(tmp_path: Path):
    db = Database(tmp_path / "receipt.db")
    meeting = MeetingState(
        id="receipt-meeting",
        title="Weekly review",
        started_at=datetime.now(),
        segments=[TranscriptSegment("Ship the report.", "Me", 0.0, 2.0)],
    )
    db.meetings.save_meeting(meeting)
    summary_profile(db, "summary-first")
    assign_summary(db, ["summary-first"])
    return db, meeting


def test_all_run_entry_points_require_the_disclosed_hash_before_queueing(
    ready_meeting, monkeypatch
):
    db, meeting = ready_meeting
    service = MeetingIntelService(db)
    route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    calls = []

    def request(*args, **kwargs):
        calls.append((args, kwargs))
        return "queued"

    monkeypatch.setattr(db.intel, "request_intel_retry", request)
    monkeypatch.setattr(service, "_broadcast_queue", lambda: None)

    for entry in (
        lambda: service.run_intelligence(OWNER, meeting.id, expected_selection_hash=route["selection_hash"]),
        lambda: service.retry_job(OWNER, meeting.id, expected_selection_hash=route["selection_hash"]),
        lambda: service.retry_recovery(OWNER, meeting.id, {"expected_selection_hash": route["selection_hash"]}),
    ):
        entry()
    assert len(calls) == 3
    assert all(call[1].get("planned_route", {}).get("selection_hash") == route["selection_hash"] for call in calls)


def test_missing_or_stale_hash_refuses_before_request_or_provider(ready_meeting, monkeypatch):
    db, meeting = ready_meeting
    service = MeetingIntelService(db)
    route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    calls = []
    monkeypatch.setattr(db.intel, "request_intel_retry", lambda *a, **k: calls.append(1))

    with pytest.raises(ConflictError) as missing:
        service.run_intelligence(OWNER, meeting.id, expected_selection_hash=None)
    assert missing.value.code == "selection_hash_required"

    summary_profile(db, "summary-second")
    assign_summary(db, ["summary-second"], expected_revision=1, command="change-summary")
    with pytest.raises(ConflictError) as drift:
        service.run_intelligence(OWNER, meeting.id, expected_selection_hash=route["selection_hash"])
    assert drift.value.code == "selection_drift"
    assert calls == []
    receipt = db.intel.get_run_receipt(meeting.id)
    assert receipt is not None and receipt["outcome"] == "refused" and receipt["attempts"] == []


@pytest.mark.parametrize("entry", ["run", "retry", "recovery"])
def test_all_run_entry_points_preserve_record_only_no_assignment_reason(
    tmp_path: Path, entry: str
):
    db = Database(tmp_path / f"no-assignment-{entry}.db")
    meeting = MeetingState(
        id=f"no-assignment-{entry}",
        title="Record only",
        started_at=datetime.now(),
        ended_at=datetime.now(),
        intel_status="refused",
        intel_status_detail="Meeting intelligence refused: no_assignment. Recording continues.",
        transcription_status="record_only",
        transcription_status_detail={
            "family": "meeting-route-assignments",
            "reason_code": "no_assignment",
            "repair": "repair_meeting_route_assignment",
        },
    )
    db.meetings.save_meeting(meeting)
    service = MeetingIntelService(db)
    with pytest.raises(ConflictError) as refused:
        if entry == "run":
            service.run_intelligence(OWNER, meeting.id)
        elif entry == "retry":
            service.retry_job(OWNER, meeting.id)
        else:
            service.retry_recovery(OWNER, meeting.id)
    assert refused.value.code == "no_assignment"
    assert "transcript is empty" not in str(refused.value).lower()


def test_receipt_keeps_failed_and_fallback_dispatches_and_survives_restart(ready_meeting):
    db, meeting = ready_meeting
    route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    job_id = db.intel.enqueue_intel_job(
        meeting.id,
        transcript_hash="transcript",
        planned_route={
            **route,
            "legs": [
                {**route["legs"][0], "ordinal": 1},
                {**route["legs"][0], "ordinal": 2, "host": "fallback-host"},
            ],
        },
    )
    receipt = db.intel.record_run_receipt(
        meeting.id,
        job_id,
        route["selection_hash"],
        "succeeded",
        {
            "attempts": [
                {"route_leg_ordinal": 1, "send_phase": "provider_no_generation", "outcome": "failed", "child_operation_id": "op-1"},
                {"route_leg_ordinal": 2, "send_phase": "provider_returned", "outcome": "succeeded", "child_operation_id": "op-2"},
                {"route_leg_ordinal": 3, "send_phase": None, "outcome": None, "child_operation_id": "reserved"},
            ]
        },
    )
    assert [(a["leg_ordinal"], a["host"], a["outcome"]) for a in receipt["attempts"]] == [
        (1, route["legs"][0]["host"], "failed"),
        (2, "fallback-host", "succeeded"),
    ]
    db.close()
    reopened = Database(Path(db.db_path))
    assert reopened.intel.get_run_receipt(meeting.id) == receipt
    assert reopened.intel.get_latest_intel_job(meeting.id).run_receipt == receipt


def test_receipt_preserves_and_fails_a_destination_outside_the_disclosed_legs(ready_meeting):
    db, meeting = ready_meeting
    route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    job_id = db.intel.enqueue_intel_job(
        meeting.id, transcript_hash="transcript", planned_route=route
    )
    receipt = db.intel.record_run_receipt(
        meeting.id,
        job_id,
        route["selection_hash"],
        "failed",
        {"attempts": [{"route_leg_ordinal": 2, "send_phase": "provider_no_generation", "outcome": "failed", "child_operation_id": "unexpected-provider"}]},
    )
    assert receipt["outcome"] == "failed"
    assert receipt["attempts"] == [{
        "leg_ordinal": 2,
        "host": "undisclosed",
        "outcome": "failed",
        "operation_id": "unexpected-provider",
    }]
    assert db.intel.get_run_receipt_for_job(job_id) == receipt


def test_real_queue_drainer_records_failed_primary_and_successful_fallback(
    tmp_path: Path, monkeypatch
):
    """The receipt is projected from real admitted dispatches, not fabricated rows."""
    from tests.unit.test_meeting_deferred_admission import _queue_rig, _queued_meeting

    db, _broker, _initial_engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    claim = ("language", "structured_output", _result_claim("meeting.deferred_analysis"))
    _profile(db, "receipt-first", claims=claim, modalities=("language", "text"))
    _profile(db, "receipt-second", claims=claim, modalities=("language", "text"))
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "receipt-two-leg-route",
            "expected_revision": 1,
            "scope": {"kind": "capability", "capability_id": "meeting.deferred_analysis"},
            "entries": [
                {"profile_id": "receipt-first", "profile_revision": 1},
                {"profile_id": "receipt-second", "profile_revision": 1},
            ],
        },
    )
    meeting = _queued_meeting(db, "receipt-real-drainer")
    route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    assert route["status"] == "ready" and len(route["legs"]) == 2
    db.intel.enqueue_intel_job(
        meeting.id, transcript_hash=meeting.transcript_hash(), planned_route=route,
    )

    calls: list[str] = []

    class _FailingEngine:
        active_provider = "stub-local"
        active_model = "receipt-first"

        def analyze(self, _transcript: str, *, stream: bool = False):
            assert stream is False
            calls.append("receipt-first")
            raise ProviderPermanentNoGeneration()

    class _SuccessfulEngine:
        active_provider = "stub-local"
        active_model = "receipt-second"

        def analyze(self, _transcript: str, *, stream: bool = False):
            assert stream is False
            calls.append("receipt-second")
            return IntelResult(
                topics=["receipt"],
                action_items=[ActionItem(task="Keep the receipt", owner="Me")],
                summary="Fallback generated this summary.",
                raw_response="{}",
            )

    failing, successful = _FailingEngine(), _SuccessfulEngine()

    def build_stub(**kwargs):
        path = str(kwargs.get("model_path") or "")
        return failing if "receipt-first" in path else successful

    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", build_stub)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: successful)

    from holdspeak.intel_queue import process_next_intel_job

    # A successful terminal job is removed from the current-job read model; the
    # durable receipt and stub call log are the evidence that this drain turn ran.
    assert process_next_intel_job() is True
    receipt = db.intel.get_run_receipt(meeting.id)
    assert receipt is not None
    assert [(item["leg_ordinal"], item["outcome"]) for item in receipt["attempts"]] == [
        (1, "failed"),
        (2, "succeeded"),
    ]
    assert [item["host"] for item in receipt["attempts"]] == [
        route["legs"][0]["host"], route["legs"][1]["host"],
    ]
    assert calls == ["receipt-first", "receipt-second"]
