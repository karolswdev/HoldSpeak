"""PHILO-3-02: the Queue HUD count follows the current queue leaf."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.services.meeting_intel_service import MeetingIntelService
from holdspeak.services.meeting_route_projection import project_route
from holdspeak.principals import Principal, PrincipalKind
from tests.unit.test_meeting_deferred_admission import _queue_rig


OWNER = Principal(PrincipalKind.OWNER, "summary-count-owner")


@pytest.fixture()
def runtime_queue_frames():
    from holdspeak.intel_queue_conductor import set_broadcast

    frames: list[tuple[str, dict[str, Any]]] = []
    set_broadcast(lambda event, frame: frames.append((event, frame)))
    try:
        yield frames
    finally:
        set_broadcast(None)


def _meeting(db: Any, meeting_id: str) -> MeetingState:
    state = MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 8, 10, 9, 0, 0),
        ended_at=datetime(2026, 8, 10, 9, 30, 0),
        title="Summary count fence",
        segments=[
            TranscriptSegment(
                text="We will ship the boundary change on Tuesday.",
                speaker="Me",
                start_time=0.0,
                end_time=5.0,
            )
        ],
    )
    db.meetings.save_meeting(state)
    return state


def _admit(db: Any, meeting_id: str) -> dict[str, Any]:
    route = project_route(db, invocation_id=f"meeting:{meeting_id}")
    return MeetingIntelService(db).run_intelligence(
        OWNER, meeting_id, expected_selection_hash=route["selection_hash"]
    )


def test_terminal_failure_is_not_still_queued_in_runtime_frame(
    tmp_path, monkeypatch, runtime_queue_frames
):
    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _meeting(db, "m-philo3-summary-count-failed")
    _admit(db, state.id)

    from holdspeak.intel_queue import build_runtime_queue_frame, process_next_intel_job

    assert build_runtime_queue_frame(db)["queued"] == 1
    engine.error = "provider unavailable"
    assert process_next_intel_job(retry_max_attempts=1) is True

    frame = build_runtime_queue_frame(db)
    assert frame["queued"] == 0
    assert frame["failed"] == 1

    emitted = [
        frame for event, frame in runtime_queue_frames if event == "runtime_queue"
    ]
    assert emitted
    assert emitted[-1]["queued"] == 0
    assert emitted[-1]["failed"] == 1

    summary = MeetingIntelService(db).queue_summary(OWNER)
    assert summary["queued_jobs"] == 0
    assert summary["failed_jobs"] == 1


def test_scheduled_retry_is_counted_as_queued_and_retrying(
    tmp_path, monkeypatch, runtime_queue_frames
):
    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _meeting(db, "m-philo3-summary-count-retry")
    _admit(db, state.id)

    from holdspeak.intel_queue import build_runtime_queue_frame, process_next_intel_job

    engine.error = "provider unavailable"
    assert process_next_intel_job(retry_base_seconds=60) is True

    frame = build_runtime_queue_frame(db)
    assert frame["queued"] == 1
    assert frame["failed"] == 0
    assert frame["scheduled_retries"] == 1

    emitted = [
        frame for event, frame in runtime_queue_frames if event == "runtime_queue"
    ]
    assert emitted
    assert emitted[-1]["queued"] == 1
    assert emitted[-1]["failed"] == 0
    assert emitted[-1]["scheduled_retries"] == 1

    summary = MeetingIntelService(db).queue_summary(OWNER)
    assert summary["queued_jobs"] == 1
    assert summary["failed_jobs"] == 0
    assert summary["scheduled_retry_jobs"] == 1
