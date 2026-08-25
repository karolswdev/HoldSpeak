"""Story 143-08: transcription repair state is safe under meeting sync."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path

from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.sync_service import SyncService


OWNER = Principal(PrincipalKind.OWNER, "sync-meeting-status-owner")
DETAIL = {
    "family": "speech-recognition-route-assignments",
    "reason_code": "no_assignment",
    "repair": "repair_meeting_route_assignment",
}


def test_record_only_transcription_state_round_trips_and_cannot_be_resurrected(
    tmp_path: Path,
) -> None:
    source = Database(tmp_path / "source.db")
    destination = Database(tmp_path / "destination.db")
    source.meetings.save_meeting(
        MeetingState(
            id="record-only-meeting",
            started_at=datetime(2026, 8, 22, 12, 0, 0),
            transcription_status="record_only",
            transcription_status_detail=DETAIL,
        )
    )

    payload = SyncService(source).pull(OWNER)
    SyncService(destination).push(OWNER, payload)
    restored = destination.meetings.get_meeting("record-only-meeting")
    assert restored is not None
    assert restored.transcription_status == "record_only"
    assert restored.transcription_status_detail == DETAIL

    hostile = deepcopy(payload)
    hostile["meetings"][0]["meta"]["last_modified"] = "2099-01-01T00:00:00Z"
    hostile["meetings"][0]["value"]["transcription_status"] = "active"
    hostile["meetings"][0]["value"]["transcription_status_detail"] = None
    SyncService(destination).push(OWNER, hostile)

    protected = destination.meetings.get_meeting("record-only-meeting")
    assert protected is not None
    assert protected.transcription_status == "record_only"
    assert protected.transcription_status_detail == DETAIL
