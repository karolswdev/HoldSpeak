"""Unit tests for MeetingSession runtime behavior."""

from __future__ import annotations

from datetime import datetime
import threading
from pathlib import Path

import numpy as np
import holdspeak.db as db_module

from holdspeak.meeting import AudioChunk
from holdspeak.meeting_session import MeetingSession, MeetingState, TranscriptSegment


class _FakeTranscriber:
    def transcribe(self, audio) -> str:
        _ = audio
        return "final transcript"


class _FakeRecorder:
    def stop(self) -> tuple[list[AudioChunk], list[AudioChunk]]:
        chunk = AudioChunk(
            audio=np.ones(16000, dtype=np.float32),
            timestamp=0.0,
            source="mic",
            duration=1.0,
        )
        return [chunk], []


def test_stop_completes_without_deadlock_during_final_transcription_and_intel() -> None:
    """stop() should not hold the session lock across finalization work."""
    session = MeetingSession(transcriber=_FakeTranscriber())
    session._state = MeetingState(
        id="meeting-1",
        started_at=datetime.now(),
        title="Already titled",
    )
    session._recorder = _FakeRecorder()
    session._intel = object()  # Non-None enables the final intel path.

    intel_calls: list[tuple[bool, str]] = []

    def fake_run_intel_analysis(final: bool = False) -> None:
        intel_calls.append((final, session.get_formatted_transcript()))

    session._run_intel_analysis = fake_run_intel_analysis  # type: ignore[method-assign]

    outcome: dict[str, object] = {"state": None, "error": None}

    def run_stop() -> None:
        try:
            outcome["state"] = session.stop()
        except Exception as exc:  # pragma: no cover - assertion below handles this
            outcome["error"] = exc

    thread = threading.Thread(target=run_stop, daemon=True)
    thread.start()
    thread.join(timeout=1.5)

    assert not thread.is_alive(), "MeetingSession.stop() deadlocked during finalization"
    assert outcome["error"] is None

    state = outcome["state"]
    assert isinstance(state, MeetingState)
    assert state.ended_at is not None
    assert [segment.text for segment in state.segments] == ["final transcript"]
    assert intel_calls == [(True, "[00:00:00] Me: final transcript")]


def test_save_reports_partial_failure_when_db_write_fails(tmp_path: Path) -> None:
    """save() should surface DB failure even when JSON persistence succeeds."""
    session = MeetingSession(transcriber=_FakeTranscriber())
    session._state = MeetingState(
        id="meeting-2",
        started_at=datetime(2024, 1, 15, 10, 30, 0),
        ended_at=datetime(2024, 1, 15, 10, 45, 0),
    )

    original_get_database = db_module.get_database

    def broken_get_database(*args, **kwargs):
        _ = args, kwargs
        raise RuntimeError("db unavailable")

    db_module.get_database = broken_get_database
    try:
        result = session.save(tmp_path)
    finally:
        db_module.get_database = original_get_database

    assert result.database_saved is False
    assert result.json_saved is True
    assert result.json_path == tmp_path / "meeting_meeting-2_20240115_103000.json"
    assert result.json_path is not None and result.json_path.exists()
    assert result.database_error == "RuntimeError: db unavailable"
    assert result.json_error is None


def test_save_reports_success_when_both_db_and_json_succeed(tmp_path: Path) -> None:
    """save() should mark both persistence paths successful when they work."""
    session = MeetingSession(transcriber=_FakeTranscriber())
    session._state = MeetingState(
        id="meeting-3",
        started_at=datetime(2024, 1, 15, 11, 0, 0),
        ended_at=datetime(2024, 1, 15, 11, 5, 0),
    )

    class _FakeDatabase:
        def __init__(self) -> None:
            self.saved = []

        def save_meeting(self, state: MeetingState) -> None:
            self.saved.append(state.id)

    fake_db = _FakeDatabase()
    original_get_database = db_module.get_database
    db_module.get_database = lambda *args, **kwargs: fake_db
    try:
        result = session.save(tmp_path)
    finally:
        db_module.get_database = original_get_database

    assert fake_db.saved == ["meeting-3"]
    assert result.database_saved is True
    assert result.json_saved is True
    assert result.database_error is None
    assert result.json_error is None
    assert result.json_path == tmp_path / "meeting_meeting-3_20240115_110000.json"


def test_save_enqueues_deferred_intel_job_when_meeting_status_is_queued(tmp_path: Path) -> None:
    """save() should enqueue deferred intel work for queued meetings."""
    session = MeetingSession(
        transcriber=_FakeTranscriber(),
        intel_enabled=True,
        intel_deferred_enabled=True,
    )
    session._state = MeetingState(
        id="meeting-4",
        started_at=datetime(2024, 1, 15, 11, 0, 0),
        ended_at=datetime(2024, 1, 15, 11, 5, 0),
        intel_status="queued",
        intel_status_detail="Queued for later processing.",
    )
    session._state.segments.append(
        TranscriptSegment(
            text="Need to follow up later.",
            speaker="Me",
            start_time=0.0,
            end_time=2.0,
        )
    )

    class _FakeDatabase:
        def __init__(self) -> None:
            self.saved: list[str] = []
            self.enqueued: list[tuple[str, str, str | None]] = []

        def save_meeting(self, state: MeetingState) -> None:
            self.saved.append(state.id)

        def enqueue_intel_job(self, meeting_id: str, *, transcript_hash: str, reason: str | None = None) -> None:
            self.enqueued.append((meeting_id, transcript_hash, reason))

    fake_db = _FakeDatabase()
    original_get_database = db_module.get_database
    db_module.get_database = lambda *args, **kwargs: fake_db
    try:
        result = session.save(tmp_path)
    finally:
        db_module.get_database = original_get_database

    assert result.database_saved is True
    assert result.intel_job_enqueued is True
    assert fake_db.saved == ["meeting-4"]
    assert len(fake_db.enqueued) == 1
    meeting_id, transcript_hash, reason = fake_db.enqueued[0]
    assert meeting_id == "meeting-4"
    assert transcript_hash == session._state.transcript_hash()
    assert reason == "Queued for later processing."
