"""HS-92-04 — provisional identity, bounded-loss journal, recovery and conflicts."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import numpy as np

from holdspeak.db import Database
from holdspeak.meeting_capture_journal import MeetingCaptureJournal
from holdspeak.meeting_session import MeetingSession, MeetingState, TranscriptSegment


def test_provisional_meeting_round_trips_and_recovers_same_id(tmp_path):
    db = Database(tmp_path / "meetings.db")
    started = datetime.now() - timedelta(seconds=12)
    checkpoint = started + timedelta(seconds=10)
    state = MeetingState(
        id="meeting-1",
        started_at=started,
        segments=[TranscriptSegment("durable words", "Me", 0, 8)],
        capture_status="recording",
        capture_checkpoint_at=checkpoint,
        capture_checkpoint_seconds=10,
        provenance="desktop",
    )

    db.meetings.save_meeting(state)
    provisional = db.meetings.get_meeting("meeting-1")
    assert provisional is not None
    assert provisional.ended_at is None
    assert provisional.capture_status == "recording"
    assert [segment.text for segment in provisional.segments] == ["durable words"]

    recovered = db.meetings.recover_capture("meeting-1")
    assert recovered is not None
    assert recovered.id == "meeting-1"
    assert recovered.ended_at == checkpoint
    assert recovered.capture_status == "recovered"


def test_desktop_opens_recorder_only_after_provisional_commit(
    tmp_path, monkeypatch
):
    import holdspeak.db as db_module
    import holdspeak.meeting_session.session as session_module

    db = Database(tmp_path / "meetings.db")
    monkeypatch.setattr(db_module, "get_database", lambda: db)
    monkeypatch.setenv("HOME", str(tmp_path))
    observed: dict[str, str] = {}

    class Recorder:
        def __init__(self, **kwargs):
            self.on_audio_chunk = kwargs.get("on_audio_chunk")

        def start(self):
            rows = db.meetings.list_meetings()
            assert len(rows) == 1, "the Meeting must commit before capture.start"
            observed["status_at_open"] = rows[0].capture_status

        def stop(self):
            return [], []

        def get_pending_device_chunks(self):
            return {}

    class Transcriber:
        def transcribe(self, _audio):
            return ""

    monkeypatch.setattr(session_module, "MeetingRecorder", Recorder)
    session = MeetingSession(transcriber=Transcriber())
    started = session.start()
    assert observed == {"status_at_open": "provisional"}
    assert db.meetings.get_meeting(started.id).capture_status == "recording"

    stopped = session.stop()
    assert stopped.id == started.id
    assert db.meetings.get_meeting(started.id).capture_status == "finalized"


def test_audio_journal_manifest_only_claims_fsynced_bytes(tmp_path):
    root = tmp_path / "captures"
    journal = MeetingCaptureJournal(
        "meeting-2", sample_rate=4, directory=root, checkpoint_seconds=1
    )
    journal.append("mic", np.asarray([0.1, 0.2, 0.3, 0.4], dtype=np.float32))

    manifest = json.loads(journal.manifest_path.read_text())
    assert manifest["status"] == "recording"
    assert manifest["durable_bytes"] == {"mic": 16}
    assert MeetingCaptureJournal.recoverable(root)[0]["meeting_id"] == "meeting-2"

    journal.finalize()
    manifest = json.loads(journal.manifest_path.read_text())
    assert manifest["status"] == "finalized"
    assert MeetingCaptureJournal.recoverable(root) == []


def test_equal_clock_conflict_keeps_losing_value_once(tmp_path):
    db = Database(tmp_path / "meetings.db")
    state = MeetingState(id="meeting-3", started_at=datetime.now(), title="Local")
    db.meetings.save_meeting(state)

    first = db.meetings.record_sync_conflict(
        "meeting-3",
        local_value=state.to_dict(),
        incoming_value={**state.to_dict(), "title": "Native"},
    )
    second = db.meetings.record_sync_conflict(
        "meeting-3",
        local_value=state.to_dict(),
        incoming_value={**state.to_dict(), "title": "Native"},
    )

    conflicts = db.meetings.list_sync_conflicts("meeting-3")
    assert first == second
    assert len(conflicts) == 1
    assert conflicts[0]["winner"] == "local"
    assert conflicts[0]["incoming"]["title"] == "Native"
