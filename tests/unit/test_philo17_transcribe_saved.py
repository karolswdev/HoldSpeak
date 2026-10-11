"""PHILO-17 transcribe: a meeting saved with its audio only (speech was not
set up) gets ONE verb, Transcribe, once speech is set up. The kept audio in
the REAL capture journal becomes the transcript of the SAME meeting; the
record-only state is cleared; the meeting then has its "Run summary" verb.

Astra r1 on #1073 fences: a live capture is refused; one claim per meeting
(an overlapping call starts no second job; a stale worker never changes a
completed result; a failure keeps the retry marker); readiness and the
transcriber come from the ADMITTED speech route, never Config, and nothing
is built while speech is not ready; a rename during the run is kept.
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

LINE = "we ship the speech fix on friday"


class _ReplayTranscriber:
    """The transcriber double: one scripted line per window, no model."""

    def __init__(self, gate: threading.Event | None = None) -> None:
        self.windows: list[int] = []
        self.gate = gate
        self.entered = threading.Event()

    def transcribe(self, audio: Any, **_kwargs: Any) -> str:
        self.entered.set()
        if self.gate is not None:
            assert self.gate.wait(30)
        self.windows.append(len(audio))
        return LINE


class _Factory:
    """The observed transcriber factory: every construction is recorded."""

    def __init__(self, transcriber: Any) -> None:
        self.transcriber = transcriber
        self.calls: list[dict[str, str]] = []

    def __call__(self, construct: dict[str, str]) -> Any:
        self.calls.append(dict(construct))
        return self.transcriber


def _migrate_writing_routes(db: Database, broker: Any) -> None:
    """A fully adopted desk: the writing routes are migrated too, so a speech
    session admits ONE route bundle that freezes the speech model
    (``speech_session/session.py`` new_speech_route)."""
    from holdspeak.config import Config
    from holdspeak.speech_session import hold_gesture_principal
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

    capabilities = ("thought.interview", "ask.answer", "speech.intent_classify", "speech.rewrite")
    _profile(db, "p17-writing-profile",
             claims=("language", "structured_output", *(_result_claim(c) for c in capabilities)))
    config = Config()
    config.thoughts.inference_target_id = "p17-writing-profile"
    config.dictation.runtime.profile_id = "p17-writing-profile"
    assert broker.inference_adoption_service.migrate_legacy_config(
        hold_gesture_principal(), config
    )["status"] == "migrated"


def _record_audio_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, route_model: str = "base", intel: bool = True
) -> tuple[Database, Any, Path, Any]:
    """Record a meeting while speech is not set up, through the real journal.

    The speech route is migrated from ``route_model``; the returned config
    may then disagree with it (the route wins)."""
    from tests.unit.test_phase143_meeting_live_cutover import (
        OWNER as MIGRATION_OWNER,
        _assign_meeting_routes_without_speech,
        _meeting_config,
    )

    db = Database(tmp_path / "transcribe.db")
    _assign_meeting_routes_without_speech(db)
    broker = _configure(db)
    config = _meeting_config("meeting-profile")
    config.model = SimpleNamespace(name=route_model, backend="mlx", language="auto")
    assert broker.inference_adoption_service.migrate_speech_recognition_route_assignments(
        MIGRATION_OWNER, config
    )["status"] == "migrated"
    _migrate_writing_routes(db, broker)
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
        intel_enabled=intel,
        intel_deferred_enabled=intel,
        transcriber_factory=lambda frozen: None,  # type: ignore[arg-type,return-value]
        transcription_backend="mlx",
        transcription_model_name=route_model,
        speech_ready=lambda _model, _backend: False,
    )
    session.start()
    stopped = session.stop()
    durable = db.meetings.get_meeting(stopped.id)
    assert durable is not None
    assert durable.transcription_status == "record_only"
    assert durable.transcription_status_detail["reason_code"] == "speech_not_set_up"
    assert durable.segments == []
    monkeypatch.setattr("holdspeak.services.meeting_service.notify_desk_changed", lambda *_a: None)
    return db, stopped, home, config


def _speech(monkeypatch: pytest.MonkeyPatch, *, ready: bool | dict[str, bool]) -> list[tuple[str, str]]:
    """The readiness double; returns every (model, backend) it was asked."""
    asked: list[tuple[str, str]] = []

    def readiness(name: str, backend: str, *, home: Any = None) -> dict[str, Any]:
        asked.append((name, backend))
        here = ready.get(name, False) if isinstance(ready, dict) else ready
        return {"model": name, "backend": backend, "state": "on_device" if here else "will_download",
                "ready": here, "bytes": 0}

    monkeypatch.setattr("holdspeak.whisper_models.speech_readiness", readiness)
    return asked


def _join_worker(meeting_id: str) -> None:
    for thread in threading.enumerate():
        if thread.name == f"meeting-transcribe-{meeting_id}":
            thread.join(timeout=60)


def _owner() -> Any:
    from tests.unit.test_phase143_meeting_live_cutover import OWNER

    return OWNER


def _intel_config(model: str = "base") -> Any:
    return SimpleNamespace(
        meeting=SimpleNamespace(intel_enabled=True, intel_deferred_enabled=True),
        model=SimpleNamespace(name=model, backend="mlx", language="auto"),
    )


def _transcribe(service: MeetingService, meeting_id: str, factory: Any, config: Any = None) -> dict[str, str]:
    return service.transcribe_saved(
        _owner(), meeting_id=meeting_id, config=config or _intel_config(), transcriber_factory=factory
    )


def test_transcribe_turns_kept_audio_into_the_same_meetings_transcript(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, stopped, home, _config = _record_audio_only(tmp_path, monkeypatch)
    folder = home / ".local" / "share" / "holdspeak" / "meeting-captures" / stopped.id
    assert (folder / "capture.json").is_file()
    service = MeetingService(db)
    factory = _Factory(_ReplayTranscriber())
    announced: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        "holdspeak.services.meeting_service.notify_desk_changed",
        lambda kind, obj_id, op: announced.append((kind, obj_id, op)),
    )

    # Speech not set up: refused, and NO transcriber is built (a
    # faster-whisper Transcriber loads its model at construction).
    _speech(monkeypatch, ready=False)
    with pytest.raises(ConflictError) as refused:
        _transcribe(service, stopped.id, factory)
    assert refused.value.code == "speech_not_set_up"
    assert factory.calls == []
    released = db.meetings.get_meeting(stopped.id)
    assert released.intel_status != "importing"
    assert released.transcription_status_detail["reason_code"] == "speech_not_set_up"
    assert "claim" not in released.transcription_status_detail

    # Speech set up: Transcribe runs in the background on the same meeting.
    _speech(monkeypatch, ready=True)
    assert _transcribe(service, stopped.id, factory) == {"meeting_id": stopped.id, "status": "transcribing"}
    _join_worker(stopped.id)

    meeting = db.meetings.get_meeting(stopped.id)
    assert meeting is not None and meeting.id == stopped.id
    assert [seg.text for seg in meeting.segments] == [LINE]
    assert meeting.segments[0].speaker == (meeting.mic_label or "Me")
    assert meeting.transcription_status == "complete"
    assert meeting.transcription_status_detail is None
    # The summary waits for its verb (the existing summary admission).
    assert meeting.intel_status == "disabled"
    assert len(factory.calls) == 1 and factory.transcriber.windows
    assert announced == [("meeting", stopped.id, "update")]
    # The audio is kept (never delete).
    assert (folder / "mic.f32le.partial").stat().st_size > 0

    # A second Transcribe is refused: the meeting is no longer audio-only.
    with pytest.raises(ConflictError) as again:
        _transcribe(service, stopped.id, factory)
    assert again.value.code == "not_audio_only"


def test_readiness_and_the_transcriber_follow_the_admitted_route_not_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The route froze `base`; Config now says `large`. Only `base` is here:
    Transcribe is not refused, and the transcriber is built for `base`."""
    db, stopped, _home, _config = _record_audio_only(tmp_path, monkeypatch, route_model="base")
    asked = _speech(monkeypatch, ready={"base": True, "large": False})
    factory = _Factory(_ReplayTranscriber())

    _transcribe(MeetingService(db), stopped.id, factory, config=_intel_config(model="large"))
    _join_worker(stopped.id)

    assert asked == [("base", "mlx")]
    assert [(call["model_name"], call["backend"]) for call in factory.calls] == [("base", "mlx")]
    assert db.meetings.get_meeting(stopped.id).transcription_status == "complete"


def test_the_meeting_payload_says_the_readiness_of_the_route_transcribe_will_use(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Astra r2: the face reads the meeting's own `transcribe_speech`, asked
    for the route's `base`, never Config's `large`."""
    db, stopped, _home, _config = _record_audio_only(tmp_path, monkeypatch, route_model="base")
    monkeypatch.setattr("holdspeak.config.Config.load", lambda *a, **k: _intel_config(model="large"))
    asked = _speech(monkeypatch, ready={"base": True, "large": False})
    service = MeetingService(db)

    detail = service.get_meeting(_owner(), stopped.id)
    listed = next(row for row in service.list_meetings(_owner())["meetings"] if row["id"] == stopped.id)

    assert detail["transcribe_speech"]["ready"] is True
    assert listed["transcribe_speech"]["ready"] is True
    assert set(asked) == {("base", "mlx")}


def test_a_failed_completion_write_releases_the_claim_and_keeps_the_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sqlite3

    db, stopped, _home, _config = _record_audio_only(tmp_path, monkeypatch)
    _speech(monkeypatch, ready=True)

    def broken(*_args: Any, **_kwargs: Any) -> bool:
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(db.meetings, "complete_transcription", broken)
    _transcribe(MeetingService(db), stopped.id, _Factory(_ReplayTranscriber()))
    _join_worker(stopped.id)

    meeting = db.meetings.get_meeting(stopped.id)
    assert meeting.intel_status != "importing"
    assert meeting.transcription_status == "record_only"
    detail = meeting.transcription_status_detail
    assert detail["reason_code"] == "speech_not_set_up"
    assert detail["last_error"] == "UNEXPECTED ERROR"
    assert "claim" not in detail


def test_a_live_capture_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db, stopped, _home, _config = _record_audio_only(tmp_path, monkeypatch)
    live = db.meetings.get_meeting(stopped.id)
    live.capture_status = "recording"
    live.ended_at = None
    db.meetings.save_meeting(live)
    _speech(monkeypatch, ready=True)
    factory = _Factory(_ReplayTranscriber())

    with pytest.raises(ConflictError) as refused:
        _transcribe(MeetingService(db), stopped.id, factory)
    assert refused.value.code == "capture_live"
    assert factory.calls == []
    # The claim itself refuses a live capture too (the race with Stop).
    assert db.meetings.claim_transcription(stopped.id, "direct") is False


def test_overlapping_calls_start_one_job_and_a_rename_during_it_is_kept(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, stopped, _home, _config = _record_audio_only(tmp_path, monkeypatch)
    _speech(monkeypatch, ready=True)
    gate = threading.Event()
    factory = _Factory(_ReplayTranscriber(gate))
    service = MeetingService(db)

    results: list[Any] = []

    def call() -> None:
        try:
            results.append(_transcribe(service, stopped.id, factory))
        except ConflictError as exc:
            results.append(exc.code)

    callers = [threading.Thread(target=call) for _ in range(2)]
    for caller in callers:
        caller.start()
    for caller in callers:
        caller.join(30)
    assert sorted(map(str, results)) == sorted(
        [str({"meeting_id": stopped.id, "status": "transcribing"}), "transcribing"]
    ), results
    assert factory.transcriber.entered.wait(30)
    # The owner renames and tags the meeting while it transcribes.
    assert db.meetings.update_meeting_metadata(stopped.id, "Renamed mid-run", ["kept"])
    gate.set()
    _join_worker(stopped.id)

    meeting = db.meetings.get_meeting(stopped.id)
    assert len(factory.calls) == 1
    assert meeting.title == "Renamed mid-run"
    assert meeting.tags == ["kept"]
    assert [seg.text for seg in meeting.segments] == [LINE]
    assert meeting.transcription_status == "complete"


def test_a_stale_worker_never_changes_a_completed_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.meeting_session import TranscriptSegment

    db, stopped, _home, _config = _record_audio_only(tmp_path, monkeypatch)
    meetings = db.meetings
    assert meetings.claim_transcription(stopped.id, "first")
    assert meetings.claim_transcription(stopped.id, "second") is False  # one claim at a time
    assert meetings.release_transcription(stopped.id, "first")
    assert meetings.claim_transcription(stopped.id, "second")
    done = [TranscriptSegment(text=LINE, speaker="Me", start_time=0.0, end_time=1.0)]
    assert meetings.complete_transcription(stopped.id, "first", [], intel_status_detail="x") is False
    assert meetings.complete_transcription(stopped.id, "second", done, intel_status_detail="x")
    # The losing worker fails late: nothing changes.
    assert meetings.release_transcription(stopped.id, "first", cause="UNEXPECTED ERROR") is False
    assert meetings.note_transcription_progress(stopped.id, "first", "late") is False
    after = meetings.get_meeting(stopped.id)
    assert after.transcription_status == "complete"
    assert [seg.text for seg in after.segments] == [LINE]


def test_a_failed_transcribe_keeps_the_meeting_audio_only_with_its_cause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, stopped, _home, _config = _record_audio_only(tmp_path, monkeypatch)
    _speech(monkeypatch, ready=True)

    class _Silent:
        def transcribe(self, _audio: Any, **_kwargs: Any) -> str:
            return ""

    _transcribe(MeetingService(db), stopped.id, _Factory(_Silent()))
    _join_worker(stopped.id)
    meeting = db.meetings.get_meeting(stopped.id)
    assert meeting is not None
    assert meeting.transcription_status == "record_only"
    detail = meeting.transcription_status_detail
    assert detail["reason_code"] == "speech_not_set_up"  # Transcribe is offered again
    assert detail["last_error"] == "NO SPEECH FOUND"
    assert "claim" not in detail and "prior_intel_status" not in detail
    assert meeting.intel_status != "importing"


def test_an_interrupted_transcribe_returns_to_audio_only_at_hub_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, stopped, _home, _config = _record_audio_only(tmp_path, monkeypatch)
    assert db.meetings.claim_transcription(stopped.id, "worker-that-died")

    assert MeetingService(db).recover_interrupted_imports() == 1
    after = db.meetings.get_meeting(stopped.id)
    assert after.intel_status != "importing"
    assert after.transcription_status == "record_only"
    assert after.transcription_status_detail["reason_code"] == "speech_not_set_up"
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


@pytest.mark.parametrize("consent", [True, False])
def test_a_transcribed_meeting_follows_the_summary_after_every_meeting_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, consent: bool
) -> None:
    """#1064's rule, as at Stop and Import: with the owner's consent (a
    chosen or local engine) the summary is queued with its disclosed route;
    without it the meeting waits in the backlog and no job is made."""
    # The web Record is capture-only (no live summary), as here: Stop
    # queues no job over the empty transcript.
    from tests.unit.test_hs172_loop_wire import assign_meeting_engine

    db, stopped, _home, _config = _record_audio_only(tmp_path, monkeypatch, intel=False)
    assign_meeting_engine(db)  # a summary engine: the route is ready
    _speech(monkeypatch, ready=True)
    woke: list[bool] = []
    monkeypatch.setattr("holdspeak.services.meeting_backlog_service._configured_auto_mode", lambda: "every")
    monkeypatch.setattr("holdspeak.services.meeting_backlog_service.backlog_consent",
                        lambda _db: {"allowed": consent})
    monkeypatch.setattr("holdspeak.intel_queue_conductor.wake_intel_queue_conductor", lambda: woke.append(True))
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM intel_jobs").fetchone()[0] == 0
    from holdspeak.services import meeting_backlog_service

    real = meeting_backlog_service.queue_after_save
    outcomes: list[Any] = []

    def spy(*args: Any, **kwargs: Any) -> Any:
        try:
            outcome = real(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 — the fence names it
            outcomes.append(repr(exc))
            raise
        outcomes.append(outcome)
        return outcome

    monkeypatch.setattr(meeting_backlog_service, "queue_after_save", spy)

    _transcribe(MeetingService(db), stopped.id, _Factory(_ReplayTranscriber()))
    _join_worker(stopped.id)

    assert db.meetings.get_meeting(stopped.id).transcription_status == "complete"
    with db._connection() as conn:
        jobs = {str(r["meeting_id"]): str(r["status"]) for r in conn.execute("SELECT meeting_id, status FROM intel_jobs")}
        marks = {str(r[0]) for r in conn.execute("SELECT meeting_id FROM meeting_summary_backlog")}
    if consent:
        assert outcomes == [{"queued": True, "reason": "queued"}], outcomes
        assert jobs == {stopped.id: "queued"} and woke == [True]
    else:
        assert outcomes == [{"queued": False, "reason": "waiting_consent"}], outcomes
        assert jobs == {} and marks == {stopped.id} and woke == []
