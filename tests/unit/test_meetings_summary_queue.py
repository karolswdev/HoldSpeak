"""PHILO-3-02 queue notification fences.

These tests deliberately admit work through ``MeetingIntelService`` and drain
it through the production queue binder.  Provider execution is substituted,
and the shared rig supplies inert plugin/router helpers for unrelated work;
database, broker, route admission, queue claim and settlement remain real.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.meeting_intel_service import MeetingIntelService
from holdspeak.services.meeting_route_projection import project_route

from tests.unit.test_meeting_deferred_admission import _queue_rig


OWNER = Principal(PrincipalKind.OWNER, "meeting-owner")


def _meeting(db: Any, meeting_id: str) -> MeetingState:
    state = MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 8, 10, 9, 0, 0),
        ended_at=datetime(2026, 8, 10, 9, 30, 0),
        title="Deferred meeting",
        tags=["architecture"],
        segments=[
            TranscriptSegment(
                text="we shipped the fix", speaker="Me", start_time=0.0, end_time=5.0
            )
        ],
    )
    db.meetings.save_meeting(state)
    return state


def _observe_notifications(db: Any, monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []

    def observe(kind: str, obj_id: str, op: str) -> None:
        assert kind == "meeting"
        assert op == "update"
        meeting = db.meetings.get_meeting(obj_id)
        job = db.intel.get_latest_intel_job(obj_id)
        observations.append(
            {
                "meeting_status": meeting.intel_status if meeting else None,
                "job_status": job.status if job else None,
                "job_id": job.job_id if job else None,
                "job_receipt": job.run_receipt if job else None,
                "receipt": db.intel.get_run_receipt(obj_id),
            }
        )

    monkeypatch.setattr("holdspeak.runtime.composition.notify_desk_changed", observe)
    return observations


def _admit(db: Any, meeting_id: str) -> dict[str, Any]:
    route = project_route(db, invocation_id=f"meeting:{meeting_id}")
    return MeetingIntelService(db).run_intelligence(
        OWNER, meeting_id, expected_selection_hash=route["selection_hash"]
    )


def test_real_admitted_success_notifies_after_running_and_receipt(
    tmp_path, monkeypatch
):
    db, _broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _meeting(db, "m-philo3-success")
    observations = _observe_notifications(db, monkeypatch)

    admitted = _admit(db, state.id)
    assert admitted["state"] == "queued"

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    assert [item["meeting_status"] for item in observations] == ["running", "ready"]
    assert observations[0]["job_status"] in {"claimed", "running"}
    assert observations[1]["job_status"] == "succeeded"
    assert observations[1]["job_receipt"] is not None
    assert observations[1]["receipt"] is not None


def test_real_admitted_retry_notifies_after_scheduled_successor_and_receipt(
    tmp_path, monkeypatch
):
    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _meeting(db, "m-philo3-retry")
    observations = _observe_notifications(db, monkeypatch)
    _admit(db, state.id)
    engine.error = "provider unavailable"

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job(retry_base_seconds=60) is True
    assert [item["meeting_status"] for item in observations] == ["running", "queued"]
    assert observations[1]["job_status"] == "queued"
    assert observations[1]["receipt"] is not None
    assert observations[1]["job_receipt"] is None


def test_real_admitted_terminal_failure_notifies_after_settlement_and_receipt(
    tmp_path, monkeypatch
):
    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _meeting(db, "m-philo3-terminal")
    observations = _observe_notifications(db, monkeypatch)
    _admit(db, state.id)
    engine.error = "provider unavailable"

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job(retry_max_attempts=1) is True
    assert [item["meeting_status"] for item in observations] == ["running", "error"]
    assert observations[1]["job_status"] == "failed"
    assert db.intel.get_latest_intel_job(state.id).last_error == "PROVIDER FAILED"
    assert observations[1]["job_receipt"] is not None
    assert observations[1]["receipt"] is not None


def test_real_admission_refusal_notifies_after_durable_refusal_receipt(
    tmp_path, monkeypatch
):
    db, _broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _meeting(db, "m-philo3-refusal")
    observations = _observe_notifications(db, monkeypatch)
    _admit(db, state.id)

    # The Run gesture froze a real route.  Clear its core assignment through
    # the owner assignment service before the queue claims, modelling a stale
    # desk configuration without replacing the binder or provider boundary.
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    InferenceAssignmentService(db).clear_assignment(
        OWNER,
        {
            "command_id": "philo3-clear-deferred-analysis",
            "expected_revision": 1,
            "scope": {"kind": "capability", "capability_id": "meeting.deferred_analysis"},
            "capability_id": "meeting.deferred_analysis",
        },
    )
    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    assert len(observations) == 1
    assert observations[0]["meeting_status"] == "error"
    assert observations[0]["job_status"] == "failed"
    assert observations[0]["job_receipt"] is not None
    assert observations[0]["receipt"] is not None
