"""HS-201-02: recording keeps its speech path independent of text intelligence."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import threading
from types import SimpleNamespace
from typing import Any
import wave

import numpy as np
import pytest

from holdspeak.db import Database
from holdspeak.meeting_recorder import AudioChunk
from holdspeak.meeting_session import MeetingSession, MeetingState
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.errors import ConflictError
from holdspeak.services.meeting_intel_service import MeetingIntelService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim, _set


pytestmark = pytest.mark.timeout(90, method="signal")

OWNER = Principal(PrincipalKind.OWNER, "meeting-owner")
SPEECH_PROFILE = "hs201-speech-profile"
TEXT_PROFILE = "hs201-text-profile"
FIXTURE_WAV = Path(__file__).parents[1] / "fixtures" / "core_path_smoke_16k.wav"


class _FixtureJournal:
    def __init__(self, meeting_id: str) -> None:
        self.meeting_id = meeting_id

    def append(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def finalize(self) -> None:
        return None

    def checkpoint(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def mark_recoverable(self, _reason: str) -> None:
        return None


class _FixtureRecorder:
    def __init__(self, **_kwargs: Any) -> None:
        self.started = False
        with wave.open(str(FIXTURE_WAV), "rb") as wav:
            audio = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        self._chunk = AudioChunk(
            audio=audio,
            timestamp=0.0,
            source="mic",
            duration=len(audio) / 16000.0,
        )

    def start(self) -> None:
        self.started = True

    def stop(self) -> tuple[list[AudioChunk], list[AudioChunk]]:
        return [self._chunk], []

    def get_pending_chunks(self, since: float = 0.0) -> tuple[list[AudioChunk], list[AudioChunk]]:
        return ([self._chunk] if self._chunk.timestamp >= since else []), []

    def get_pending_device_chunks(self) -> dict[str, list[AudioChunk]]:
        return {}


class _FixtureTranscriber:
    backend = "faster-whisper"
    model_name = "hs201-speech"

    def transcribe(self, _audio: Any, **_kwargs: Any) -> str:
        return "fixture speech transcript"


def _speech_only_db(tmp_path: Path) -> Database:
    db = Database(tmp_path / "hs201-meeting.db")
    _profile(
        db,
        SPEECH_PROFILE,
        claims=("language", "audio", _result_claim("speech.transcribe")),
        modalities=("audio",),
    )
    assignments = InferenceAssignmentService(db)
    scope = {"kind": "capability", "capability_id": "speech.transcribe"}
    try:
        expected = int(assignments.get_assignment(OWNER, scope)["revision"])
    except Exception:
        expected = 0
    _set(assignments, "hs201-speech-assignment", scope, SPEECH_PROFILE, expected=expected)
    return db


def _speech_only_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Database, MeetingSession]:
    db = _speech_only_db(tmp_path)
    _configure(db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", _FixtureRecorder)
    monkeypatch.setattr("holdspeak.meeting_capture_journal.MeetingCaptureJournal", _FixtureJournal)
    session = MeetingSession(
        _FixtureTranscriber(),  # type: ignore[arg-type]
        principal=OWNER,
        intel_enabled=False,
        intel_deferred_enabled=True,
    )
    return db, session


def _no_speech_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Database, MeetingSession]:
    db = Database(tmp_path / "hs201-no-speech.db")
    _configure(db)
    with db._connection() as conn:
        conn.execute(
            "DELETE FROM inference_assignment_heads WHERE assignment_key=?",
            ("capability:speech.transcribe",),
        )
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", _FixtureRecorder)
    monkeypatch.setattr("holdspeak.meeting_capture_journal.MeetingCaptureJournal", _FixtureJournal)
    return db, MeetingSession(
        _FixtureTranscriber(),  # type: ignore[arg-type]
        principal=OWNER,
        intel_enabled=False,
        intel_deferred_enabled=True,
    )


def _speech_and_text_db(tmp_path: Path) -> Database:
    db = _speech_only_db(tmp_path)
    text_capabilities = (
        "meeting.live_analysis",
        "meeting.bookmark_label",
        "meeting.auto_title",
    )
    _profile(
        db,
        TEXT_PROFILE,
        claims=(
            "language",
            "structured_output",
            *(_result_claim(capability) for capability in text_capabilities),
        ),
        modalities=("language", "text"),
    )
    assignments = InferenceAssignmentService(db)
    for ordinal, capability in enumerate(text_capabilities, 1):
        scope = {"kind": "capability", "capability_id": capability}
        try:
            expected = int(assignments.get_assignment(OWNER, scope)["revision"])
        except Exception:
            expected = 0
        _set(assignments, f"hs201-text-assignment-{ordinal}", scope, TEXT_PROFILE, expected=expected)
    return db


def _speech_and_text_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Database, MeetingSession]:
    db = _speech_and_text_db(tmp_path)
    _configure(db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", _FixtureRecorder)
    monkeypatch.setattr("holdspeak.meeting_capture_journal.MeetingCaptureJournal", _FixtureJournal)
    return db, MeetingSession(
        _FixtureTranscriber(),  # type: ignore[arg-type]
        principal=OWNER,
        intel_enabled=False,
        intel_deferred_enabled=True,
    )


def test_speech_only_recording_admits_without_text_routes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A speech assignment is sufficient when intelligence is disabled."""
    db, session = _speech_only_session(tmp_path, monkeypatch)

    state = session.start()

    assert state.capture_status == "recording"
    assert state.transcription_status == "active"
    assert state.transcription_status_detail is None
    assert session._route_bundle is not None
    assert {
        member["capability_id"] for member in session._route_bundle["members"]
    } == {"speech.transcribe", "speech.preload"}
    assert db.meetings.get_meeting(state.id) is not None


def test_no_speech_assignment_records_named_refusal_immediately(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, session = _no_speech_session(tmp_path, monkeypatch)

    state = session.start()

    assert state.capture_status == "recording"
    assert state.transcription_status == "record_only"
    assert state.transcription_status_detail == {
        "family": "meeting-route-assignments",
        "reason_code": "no_assignment",
        "repair": "repair_meeting_route_assignment",
    }
    durable = db.meetings.get_meeting(state.id)
    assert durable is not None
    assert durable.transcription_status_detail == state.transcription_status_detail


def test_speech_only_stop_saves_transcript_and_closes_parent_without_queue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, session = _speech_only_session(tmp_path, monkeypatch)
    state = session.start()

    stopped = session.stop()

    assert stopped.capture_status == "finalized"
    assert [segment.text for segment in stopped.segments] == ["fixture speech transcript"]
    assert stopped.intel_status == "disabled"
    assert db.intel.get_intel_job(stopped.id) is None
    parent_id = str(session._route_bundle["parent_operation_id"])
    with db._connection() as conn:
        parent = conn.execute(
            "SELECT state FROM kernel_parent_runs WHERE operation_id=?", (parent_id,)
        ).fetchone()
        receipt = conn.execute(
            "SELECT outcome FROM kernel_receipts WHERE operation_id=?", (parent_id,)
        ).fetchone()
    assert parent is not None and parent["state"] != "OPEN"
    assert receipt is not None and receipt["outcome"] in {"cancelled", "succeeded"}


def test_speech_only_ignores_available_text_engine_until_summary_gesture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Available text routes do not become live or Stop work by implication."""
    db, session = _speech_and_text_session(tmp_path, monkeypatch)
    state = session.start()

    stopped = session.stop()
    assert db.intel.get_intel_job(stopped.id) is None
    assert stopped.intel_status == "disabled"
    assert session._route_bundle is not None
    assert {
        member["capability_id"] for member in session._route_bundle["members"]
    } == {"speech.transcribe", "speech.preload"}


def test_retry_preserves_no_assignment_reason_instead_of_empty_transcript(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "hs201-refusal.db")
    meeting = MeetingState(
        id="hs201-no-assignment",
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

    with pytest.raises(ConflictError) as refused:
        MeetingIntelService(db).retry_job(OWNER, meeting.id)

    assert getattr(refused.value, "code", None) == "no_assignment"
    assert "transcript is empty" not in str(refused.value).lower()


def test_web_record_constructs_capture_only_session_before_summary_gesture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The normal Record callback does not opt into live text intelligence."""
    from holdspeak.runtime import meeting_glue

    captured: dict[str, Any] = {}

    class _State:
        id = "hs201-runtime-meeting"
        title = None
        tags: list[str] = []
        web_url = None
        calendar_event_id = None
        devices: list[Any] = []

        def to_dict(self) -> dict[str, Any]:
            return {"id": self.id, "title": self.title, "tags": self.tags}

    class _Session:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)
            self._state = _State()

        @property
        def is_active(self) -> bool:
            return True

        @property
        def state(self) -> _State:
            return self._state

        def start(self) -> _State:
            return self._state

        def attach_device(self, *_args: Any, **_kwargs: Any) -> None:
            return None

        def set_title(self, title: str) -> None:
            self._state.title = title

        def set_tags(self, tags: list[str]) -> None:
            self._state.tags = tags

    class _Floor:
        active_owner = None

        def acquire(self, _owner: str) -> bool:
            return True

        def release(self, _owner: str) -> None:
            return None

    meeting_config = SimpleNamespace(
        intent_segment_probe_enabled=False,
        mic_label="Me",
        remote_label="Remote",
        mic_device=None,
        system_audio_device=None,
        intel_enabled=True,
        intel_realtime_model="",
        intel_provider="local",
        intel_deferred_enabled=True,
        intel_cloud_reasoning_effort=None,
        intel_cloud_store=False,
        diarization_enabled=False,
        diarize_mic=False,
        cross_meeting_recognition=False,
    )
    harness = meeting_glue.MeetingGlueMixin.__new__(meeting_glue.MeetingGlueMixin)
    harness.meeting_lock = threading.Lock()
    harness.meeting_session = None
    harness.transcriber = _FixtureTranscriber()
    harness.config = SimpleNamespace(
        meeting=meeting_config,
        model=SimpleNamespace(backend="auto", name="base"),
    )
    harness.device_registry = SimpleNamespace(get=lambda _id: None)
    harness.voice_session = _Floor()
    harness.runtime_url = None
    harness.state_lock = threading.Lock()
    harness.pending_title = None
    harness.pending_calendar_event_id = None
    harness.pending_tags = None
    harness.pending_intent_windows = []
    harness.pending_plugin_runs = []
    harness.preview_window_seq = 0
    harness.runtime_status = {"last_error": ""}
    harness._ensure_transcriber_loaded = lambda **_kwargs: harness.transcriber
    harness._set_runtime_activity = lambda *_args, **_kwargs: None
    harness._broadcast_intel_status = lambda: None
    harness._apply_updated_config = lambda: None
    harness._on_meeting_segment = lambda *_args, **_kwargs: None
    harness._on_meeting_intel = lambda *_args, **_kwargs: None
    harness._on_meeting_broadcast = lambda *_args, **_kwargs: None
    harness._emit_audio_level = lambda *_args, **_kwargs: None
    monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", _FixtureRecorder)
    monkeypatch.setattr("holdspeak.runtime.meeting_glue.MeetingSession", _Session)
    monkeypatch.setattr(
        "holdspeak.intel.providers.effective_intel_cloud",
        lambda _config: SimpleNamespace(
            reason="", model="", api_key_env="OPENAI_API_KEY", base_url=None
        ),
    )

    result = harness._start_meeting(principal=OWNER)

    assert result["id"] == "hs201-runtime-meeting"
    assert captured["intel_enabled"] is False
