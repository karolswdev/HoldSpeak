"""PHILO-15 01 ruling — OFF is a deliberate state, never a failure.

Producer-backed: the real queue drain, the real run verb and the real
backlog service, over a real database. The one fake is the provider seam
(``_queue_rig``), and it must never be reached while summaries are OFF.
"""

from __future__ import annotations

import pytest

from holdspeak.services.errors import ConflictError
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_meeting_deferred_admission import OWNER, _queue_rig, _queued_meeting, _rows

pytestmark = pytest.mark.timeout(120, method="thread")

SUMMARY = "meeting.deferred_analysis"


def _off(db) -> None:
    InferenceAssignmentService(db).set_capability_off(OWNER, capability_id=SUMMARY)


def _service(db):
    from holdspeak.services.meeting_intel_service import MeetingIntelService

    return MeetingIntelService(db, None)


def _needs_you_meetings(db) -> list[str]:
    from holdspeak.services.needs_you_membership import _read_summary_attention, meeting_needs_you

    return [str(m.get("id")) for m in _read_summary_attention(db, OWNER) if meeting_needs_you(m)]


def test_a_queued_summary_that_meets_off_ends_skipped_not_failed(tmp_path, monkeypatch):
    from holdspeak.intel_queue import process_next_intel_job

    db, _broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    _queued_meeting(db, "m-off-queued")
    _off(db)

    process_next_intel_job()

    # No summary runs: the provider seam was never reached.
    assert not engine.analyzed and not requests
    jobs = _rows(db, "intel_jobs")
    # The claim planner supersedes the handoff row; its successor meets OFF.
    statuses = [j["status"] for j in jobs]
    assert "failed" not in statuses and statuses.count("skipped") == 1, statuses
    assert set(statuses) <= {"superseded", "skipped"}, statuses
    assert [j["last_error"] for j in jobs if j["status"] == "skipped"] == ["Summaries off."]
    meeting = db.meetings.get_meeting("m-off-queued")
    assert meeting.intel_status == "skipped", meeting.intel_status
    # A receipt, not an error: no Retry, no Needs-you row.
    recovery = _service(db).get_recovery(OWNER, "m-off-queued")
    assert recovery["actions"]["retry"] is False, recovery["actions"]
    assert recovery["planned_route"]["reason_code"] == "summaries off"
    assert "m-off-queued" not in _needs_you_meetings(db)
    outcomes = [r["outcome"] for r in _rows(db, "intel_job_attempts") if r["event_kind"] == "refusal"]
    assert outcomes == ["skipped"], outcomes


def test_a_live_summary_request_under_off_is_an_honest_refusal(tmp_path, monkeypatch):
    db, _broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    _queued_meeting(db, "m-off-live")
    for job in db.intel.list_intel_jobs(status="all"):
        db.intel.skip_remaining_intel(job.meeting_id)
    before = _rows(db, "intel_jobs")
    status_before = db.meetings.get_meeting("m-off-live").intel_status
    _off(db)

    with pytest.raises(ConflictError) as refused:
        _service(db).run_intelligence(OWNER, "m-off-live", expected_selection_hash="any")
    assert refused.value.code == "summaries_off"
    assert refused.value.context["planned_route"]["reason_code"] == "summaries off"
    # Nothing was written: no refusal job, no error on the meeting.
    assert _rows(db, "intel_jobs") == before
    assert db.meetings.get_meeting("m-off-live").intel_status == status_before
    assert "m-off-live" not in _needs_you_meetings(db)
    assert not engine.analyzed and not requests


def test_a_genuine_route_refusal_is_still_a_failure(tmp_path, monkeypatch):
    """Historical truth stays: a drifted selection is still a refusal row."""
    db, *_ = _queue_rig(tmp_path, monkeypatch)
    _queued_meeting(db, "m-drift")
    for job in db.intel.list_intel_jobs(status="all"):
        db.intel.skip_remaining_intel(job.meeting_id)
    with pytest.raises(ConflictError) as refused:
        _service(db).run_intelligence(OWNER, "m-drift", expected_selection_hash="sha256:stale")
    assert refused.value.code == "selection_drift"
    assert db.meetings.get_meeting("m-drift").intel_status == "error"


def test_the_backlog_queues_nothing_under_off_and_drains_when_off_clears(tmp_path, monkeypatch):
    from holdspeak.services.meeting_backlog_service import drain_backlog, mark_if_no_engine

    db, *_ = _queue_rig(tmp_path, monkeypatch)
    _queued_meeting(db, "m-before-off")
    _queued_meeting(db, "m-during-off")
    for job in db.intel.list_intel_jobs(status="all"):
        db.intel.skip_remaining_intel(job.meeting_id)
    # Reset both to "never summarised" so the backlog may take them.
    with db._connection() as conn:
        conn.execute("UPDATE meetings SET intel_status='disabled'")
        conn.execute("DELETE FROM intel_job_attempts")
        conn.execute("DELETE FROM intel_jobs")
    # A mark made before OFF (no engine then).
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meeting_summary_backlog(meeting_id,reason,marked_at) "
            "VALUES ('m-before-off','summary_deferred_no_engine','2026-10-07T00:00:00Z')"
        )
    _off(db)

    # Under OFF: a new meeting is not marked, and nothing waits or queues.
    assert mark_if_no_engine(db, "m-during-off") is False
    assert drain_backlog(db, auto_mode="every") == {"status": "summaries_off", "queued": []}
    assert drain_backlog(db, auto_mode="every")["status"] == "summaries_off"
    marks = [r["meeting_id"] for r in _rows(db, "meeting_summary_backlog")]
    assert marks == ["m-before-off"], marks
    assert _rows(db, "intel_jobs") == []

    # OFF clears (an exact engine for summaries): the old mark drains as today.
    service = InferenceAssignmentService(db)
    current = service.get_assignment(OWNER, {"kind": "capability", "capability_id": SUMMARY})
    service.set_assignment(OWNER, {
        "command_id": "philo15-off-clears",
        "expected_revision": int(current["revision"]),
        "scope": {"kind": "capability", "capability_id": SUMMARY},
        "entries": [{"profile_id": "deferred-queue-model", "profile_revision": 1}],
    })
    drained = drain_backlog(db, auto_mode="every")
    assert drained["status"] == "queued" and drained["queued"] == ["m-before-off"], drained
