"""HS-93-06 — truthful partial Meeting intelligence recovery."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.integration, pytest.mark.requires_meeting]

from holdspeak.db import get_database, reset_database  # noqa: E402
from holdspeak.db.intel import MANUAL_INTEL_RETRY_REASON  # noqa: E402
from holdspeak.meeting_session import (  # noqa: E402
    IntelSnapshot,
    MeetingState,
    TranscriptSegment,
)
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks  # noqa: E402


@pytest.fixture
def db(tmp_path):
    reset_database()
    database = get_database(tmp_path / "intel-recovery.db")
    yield database
    reset_database()


@pytest.fixture
def client(db) -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    return TestClient(server.app)


def _seed_failed_partial_intel(db) -> MeetingState:
    started = datetime(2026, 7, 11, 9, 0, 0)
    meeting = MeetingState(
        id="meeting-partial-intel",
        started_at=started,
        ended_at=started + timedelta(minutes=18),
        title="Delivery review",
        segments=[
            TranscriptSegment(
                text="Ship the durable recovery path.",
                speaker="Karol",
                start_time=2.0,
                end_time=7.0,
            ),
            TranscriptSegment(
                text="Keep completed artifacts if routing fails.",
                speaker="Alex",
                start_time=9.0,
                end_time=15.0,
            ),
        ],
        intel=IntelSnapshot(
            timestamp=18 * 60,
            topics=["Recovery"],
            action_items=[],
            summary="The Meeting and completed work must remain saved.",
        ),
        intel_status="ready",
        intel_completed_at=datetime(2026, 7, 11, 9, 19, 0),
    )
    db.meetings.save_meeting(meeting)
    db.plugins.record_artifact(
        artifact_id="artifact-retained",
        meeting_id=meeting.id,
        artifact_type="decision",
        title="Recovery decision",
        body_markdown="Retain completed work.",
        structured_json={},
        confidence=0.92,
        status="draft",
        plugin_id="decision_extractor",
        plugin_version="1.0.0",
        sources=[],
    )
    db.intel.enqueue_intel_job(
        meeting.id,
        transcript_hash=meeting.transcript_hash(),
        reason="Routed intelligence queued.",
    )
    assert db.intel.claim_next_intel_job() is not None
    db.intel.mark_intel_job_partial(meeting.id, "Decision extraction timed out.")
    return meeting


def test_partial_intel_names_retained_work_and_supports_retry_or_skip(
    client, db
) -> None:
    meeting = _seed_failed_partial_intel(db)

    response = client.get(f"/api/meetings/{meeting.id}/intel-recovery")
    assert response.status_code == 200
    recovery = response.json()
    assert recovery["headline"] == "Meeting saved · intelligence incomplete"
    assert recovery["state"] == "partial"
    assert recovery["actions"] == {"retry": True, "skip": True}
    assert recovery["remaining"] == {
        "label": "Routed meeting intelligence",
        "detail": "Decision extraction timed out.",
    }
    assert recovery["completed"] == [
        {"label": "Meeting", "detail": "Saved"},
        {"label": "Transcript", "detail": "2 saved segments"},
        {
            "label": "Meeting analysis",
            "detail": "Summary, topics, and action items saved",
        },
        {"label": "Artifacts", "detail": "1 saved artifact"},
    ]

    skipped = client.post(f"/api/meetings/{meeting.id}/intel-recovery/skip")
    assert skipped.status_code == 200
    skipped_recovery = skipped.json()["recovery"]
    assert skipped_recovery["headline"] == "Meeting saved · intelligence skipped"
    assert skipped_recovery["actions"] == {"retry": True, "skip": False}

    retained = db.meetings.get_meeting(meeting.id)
    assert retained is not None
    assert retained.id == meeting.id
    assert retained.intel_status == "skipped"
    assert retained.intel_completed_at is None
    assert len(retained.segments) == 2
    assert retained.intel is not None
    assert db.plugins.list_artifacts(meeting.id)[0].id == "artifact-retained"
    assert db.intel.list_intel_job_attempts(meeting.id)[0].outcome == "skipped"

    retried = client.post(f"/api/meetings/{meeting.id}/intel-recovery/retry")
    assert retried.status_code == 200
    assert retried.json()["recovery"]["state"] == "queued"
    assert retried.json()["recovery"]["actions"] == {
        "retry": False,
        "skip": True,
    }
    queued = db.intel.get_intel_job(meeting.id)
    assert queued is not None
    assert queued.attempts == 0
    assert queued.transcript_hash == retained.transcript_hash()
    assert queued.last_error == MANUAL_INTEL_RETRY_REASON

    claimed = db.intel.claim_next_intel_job()
    assert claimed is not None
    assert claimed.last_error == MANUAL_INTEL_RETRY_REASON
    competing_skip = client.post(f"/api/meetings/{meeting.id}/intel-recovery/skip")
    assert competing_skip.status_code == 409
    assert "running" in competing_skip.json()["error"]
    assert db.intel.get_intel_job(meeting.id).status == "running"
