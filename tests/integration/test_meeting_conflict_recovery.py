"""HS-93-06 — owner-visible, lossless Meeting sync-conflict recovery."""

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
from holdspeak.meeting_session import MeetingState, TranscriptSegment  # noqa: E402
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks  # noqa: E402

CONTESTED_CLOCK = datetime(2030, 1, 1, 12, 0, 0)


@pytest.fixture
def db(tmp_path):
    reset_database()
    database = get_database(tmp_path / "conflicts.db")
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


def _meeting(title: str, words: str) -> MeetingState:
    started = datetime(2026, 7, 11, 9, 0, 0)
    return MeetingState(
        id="meeting-conflict",
        started_at=started,
        ended_at=started + timedelta(minutes=12),
        title=title,
        tags=["delivery"],
        segments=[
            TranscriptSegment(
                text=words,
                speaker="Karol",
                start_time=4.0,
                end_time=9.0,
            )
        ],
        capture_status="finalized",
        provenance="desktop" if title == "Desktop title" else "native",
    )


def _seed_conflict(db) -> str:
    local = _meeting("Desktop title", "Keep the desktop transcript.")
    incoming = _meeting("Device title", "Use the device transcript.")
    db.meetings.save_meeting(local, sync_modified_at=CONTESTED_CLOCK)
    return db.meetings.record_sync_conflict(
        local.id,
        local_value=local.to_dict(),
        incoming_value={"deleted": False, **incoming.to_dict()},
    )


def test_keep_current_resolves_without_changing_the_meeting(client, db) -> None:
    conflict_id = _seed_conflict(db)

    before = client.get("/api/meetings/meeting-conflict/sync-conflicts")
    assert before.status_code == 200
    assert before.json()["conflicts"][0]["local"]["title"] == "Desktop title"
    assert before.json()["conflicts"][0]["incoming"]["title"] == "Device title"

    response = client.post(
        f"/api/meetings/meeting-conflict/sync-conflicts/{conflict_id}/resolve",
        json={"resolution": "keep_current"},
    )
    assert response.status_code == 200
    assert response.json()["resolution"] == "keep_current"
    assert response.json()["remaining_conflicts"] == []
    meeting = db.meetings.get_meeting("meeting-conflict")
    assert meeting.title == "Desktop title"
    assert meeting.sync_modified_at > CONTESTED_CLOCK
    resolved = db.meetings.get_sync_conflict("meeting-conflict", conflict_id)
    assert resolved["winner"] == "local"
    assert resolved["resolved_at"] is not None

    repeated = client.post(
        f"/api/meetings/meeting-conflict/sync-conflicts/{conflict_id}/resolve",
        json={"resolution": "keep_current"},
    )
    assert repeated.status_code == 409
    assert "already resolved" in repeated.json()["error"]


def test_use_incoming_replaces_the_same_identity_atomically(client, db) -> None:
    conflict_id = _seed_conflict(db)

    response = client.post(
        f"/api/meetings/meeting-conflict/sync-conflicts/{conflict_id}/resolve",
        json={"resolution": "use_incoming"},
    )
    assert response.status_code == 200
    assert response.json()["deleted"] is False
    assert response.json()["meeting"]["id"] == "meeting-conflict"
    assert response.json()["meeting"]["title"] == "Device title"

    meeting = db.meetings.get_meeting("meeting-conflict")
    assert meeting.id == "meeting-conflict"
    assert meeting.title == "Device title"
    assert meeting.provenance == "native"
    assert meeting.sync_modified_at > CONTESTED_CLOCK
    assert [segment.text for segment in meeting.segments] == [
        "Use the device transcript."
    ]
    resolved = db.meetings.get_sync_conflict("meeting-conflict", conflict_id)
    assert resolved["winner"] == "incoming"
    assert resolved["resolved_at"] is not None


def test_use_incoming_tombstone_explicitly_deletes_the_meeting(client, db) -> None:
    local = _meeting("Desktop title", "Retained until the owner decides.")
    db.meetings.save_meeting(local)
    conflict_id = db.meetings.record_sync_conflict(
        local.id,
        local_value=local.to_dict(),
        incoming_value={"deleted": True},
    )

    response = client.post(
        f"/api/meetings/{local.id}/sync-conflicts/{conflict_id}/resolve",
        json={"resolution": "use_incoming"},
    )
    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert response.json()["meeting"] is None
    assert db.meetings.get_meeting(local.id) is None


def test_resolution_refuses_unknown_choices_without_touching_versions(client, db) -> None:
    conflict_id = _seed_conflict(db)
    response = client.post(
        f"/api/meetings/meeting-conflict/sync-conflicts/{conflict_id}/resolve",
        json={"resolution": "merge_silently"},
    )
    assert response.status_code == 400
    assert db.meetings.get_meeting("meeting-conflict").title == "Desktop title"
    assert len(db.meetings.list_sync_conflicts("meeting-conflict")) == 1
