"""PHILO-17 transcribe: a meeting saved with its audio only (speech was not
set up) gets ONE verb, Transcribe, once speech is set up. The kept audio in
the REAL capture journal becomes the transcript of the SAME meeting; the
record-only state is cleared; the meeting then has its "Run summary" verb.
"""

from __future__ import annotations

import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.meeting_session import MeetingSession
from holdspeak.services.errors import ConflictError
from holdspeak.services.meeting_service import MeetingService
from tests.unit.test_hs201_record_speech_only import _FixtureRecorder, _configure

pytestmark = pytest.mark.timeout(90, method="signal")


class _ReplayTranscriber:
    """The transcriber double: one scripted line per window, no model."""

    def __init__(self) -> None:
        self.windows: list[int] = []

    def transcribe(self, audio: Any, **_kwargs: Any) -> str:
        self.windows.append(len(audio))
        return "we ship the speech fix on friday"


def _record_audio_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Database, Any, Path]:
    """Record a meeting while speech is not set up, through the real journal."""
    from tests.unit.test_phase143_meeting_live_cutover import (
        OWNER as MIGRATION_OWNER,
        _assign_meeting_routes_without_speech,
        _meeting_config,
    )

    db = Database(tmp_path / "transcribe.db")
    _assign_meeting_routes_without_speech(db)
    broker = _configure(db)
    config = _meeting_config("meeting-profile")
    config.model = SimpleNamespace(name="base", backend="mlx", language="auto")
    assert broker.inference_adoption_service.migrate_speech_recognition_route_assignments(
        MIGRATION_OWNER, config
    )["status"] == "migrated"
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)

    class _JournalingRecorder(_FixtureRecorder):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            self._on_chunk = kwargs.get("on_audio_chunk")

        def start(self) -> None:
            super().start()
            if self._on_chunk is not None:
                self._on_chunk(self._chunk)

    monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", _JournalingRecorder)
    session = MeetingSession(
        None,
        principal=MIGRATION_OWNER,
        intel_enabled=True,
        intel_deferred_enabled=True,
        transcriber_factory=lambda frozen: None,  # type: ignore[arg-type,return-value]
        transcription_backend="mlx",
        transcription_model_name="base",
        speech_ready=lambda _model, _backend: False,
    )
    session.start()
    stopped = session.stop()
    durable = db.meetings.get_meeting(stopped.id)
    assert durable is not None
    assert durable.transcription_status == "record_only"
    assert durable.transcription_status_detail["reason_code"] == "speech_not_set_up"
    assert durable.segments == []
    return db, stopped, home


def _speech(monkeypatch: pytest.MonkeyPatch, *, ready: bool) -> None:
    monkeypatch.setattr(
        "holdspeak.whisper_models.configured_speech_readiness",
        lambda **_kw: {"model": "base", "backend": "mlx", "state": "on_device" if ready else "will_download",
                       "ready": ready, "bytes": 0},
    )


def _join_worker(meeting_id: str) -> None:
    for thread in threading.enumerate():
        if thread.name == f"meeting-transcribe-{meeting_id}":
            thread.join(timeout=60)


def _owner() -> Any:
    from holdspeak.principals import Principal, PrincipalKind

    return Principal(PrincipalKind.OWNER, "meeting-owner")


def _intel_config() -> Any:
    return SimpleNamespace(meeting=SimpleNamespace(intel_enabled=True, intel_deferred_enabled=True))


def test_transcribe_turns_kept_audio_into_the_same_meetings_transcript(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, stopped, home = _record_audio_only(tmp_path, monkeypatch)
    folder = home / ".local" / "share" / "holdspeak" / "meeting-captures" / stopped.id
    assert (folder / "capture.json").is_file()
    service = MeetingService(db)
    transcriber = _ReplayTranscriber()
    announced: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        "holdspeak.services.meeting_service.notify_desk_changed",
        lambda kind, obj_id, op: announced.append((kind, obj_id, op)),
    )

    # Speech not set up: refused, and no model is loaded.
    _speech(monkeypatch, ready=False)
    with pytest.raises(ConflictError) as refused:
        service.transcribe_saved(_owner(), meeting_id=stopped.id, config=_intel_config(),
                                 transcriber_factory=lambda _c: transcriber)
    assert refused.value.code == "speech_not_set_up"
    assert transcriber.windows == []

    # Speech set up: Transcribe runs in the background on the same meeting.
    _speech(monkeypatch, ready=True)
    started = service.transcribe_saved(_owner(), meeting_id=stopped.id, config=_intel_config(),
                                       transcriber_factory=lambda _c: transcriber)
    assert started == {"meeting_id": stopped.id, "status": "transcribing"}
    _join_worker(stopped.id)

    meeting = db.meetings.get_meeting(stopped.id)
    assert meeting is not None
    assert meeting.id == stopped.id
    assert [seg.text for seg in meeting.segments] == ["we ship the speech fix on friday"]
    assert meeting.segments[0].speaker == (meeting.mic_label or "Me")
    assert meeting.transcription_status == "complete"
    assert meeting.transcription_status_detail is None
    # The summary waits for its verb (the existing summary admission).
    assert meeting.intel_status == "disabled"
    assert transcriber.windows  # the kept audio was heard
    assert announced == [("meeting", stopped.id, "update")]
    # The audio is kept (never delete).
    assert (folder / "mic.f32le.partial").stat().st_size > 0

    # A second Transcribe is refused: the meeting is no longer audio-only.
    with pytest.raises(ConflictError) as again:
        service.transcribe_saved(_owner(), meeting_id=stopped.id, config=_intel_config(),
                                 transcriber_factory=lambda _c: transcriber)
    assert again.value.code == "not_audio_only"


def test_a_failed_transcribe_keeps_the_meeting_audio_only_with_its_cause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, stopped, _home = _record_audio_only(tmp_path, monkeypatch)
    monkeypatch.setattr("holdspeak.services.meeting_service.notify_desk_changed", lambda *_a: None)
    _speech(monkeypatch, ready=True)

    class _Silent:
        def transcribe(self, _audio: Any, **_kwargs: Any) -> str:
            return ""

    MeetingService(db).transcribe_saved(_owner(), meeting_id=stopped.id, config=_intel_config(),
                                        transcriber_factory=lambda _c: _Silent())
    _join_worker(stopped.id)
    meeting = db.meetings.get_meeting(stopped.id)
    assert meeting is not None
    assert meeting.transcription_status == "record_only"
    assert meeting.transcription_status_detail["reason_code"] == "speech_not_set_up"
    assert meeting.transcription_status_detail["last_error"] == "NO SPEECH FOUND"
    assert meeting.intel_status == "disabled"


def test_an_interrupted_transcribe_returns_to_audio_only_at_hub_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, stopped, _home = _record_audio_only(tmp_path, monkeypatch)
    meeting = db.meetings.get_meeting(stopped.id)
    meeting.intel_status = "importing"
    db.meetings.save_meeting(meeting)

    assert MeetingService(db).recover_interrupted_imports() == 1
    after = db.meetings.get_meeting(stopped.id)
    assert after.intel_status == "disabled"
    assert after.transcription_status == "record_only"
    assert after.transcription_status_detail["last_error"] == "INTERRUPTED BY A RESTART"


def test_transcribe_is_one_owner_only_operation_on_http_and_mcp() -> None:
    from holdspeak import operations
    from holdspeak.mcp.tool_authority import TOOL_AUTHORITY
    from holdspeak.mcp.tools import TOOLS

    descriptor = {d.name: d for d in operations.DESCRIPTORS}["meeting.transcribe"]
    assert descriptor.owner_only is True
    assert descriptor.held == ("config", "transcriber_factory")
    assert descriptor.exposure == ("http:POST /api/meetings/{meeting_id}/transcribe", "mcp:meeting.transcribe")
    assert "meeting.transcribe" in {tool["name"] for tool in TOOLS}
    assert TOOL_AUTHORITY["meeting.transcribe"] == "work"
