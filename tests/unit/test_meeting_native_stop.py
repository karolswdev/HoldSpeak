"""Stop preserves accepted PCM even when native audio teardown never returns."""

from __future__ import annotations

import asyncio
import json
import threading
import time
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import numpy as np
import pytest
from fastapi import FastAPI

import holdspeak.meeting_recorder as recorder_module
from holdspeak.db import Database
from holdspeak.meeting_capture_journal import MeetingCaptureJournal
from holdspeak.meeting_recorder import MeetingRecorder, MeetingRecorderError
from holdspeak.meeting_session import MeetingSession, MeetingState
from holdspeak.runtime.meeting_glue import MeetingGlueMixin
from holdspeak.services.meeting_service import MeetingService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.meetings.live import build_live_router
from holdspeak.voice_typing import VoiceTypingSession


def _recorder(monkeypatch, on_audio_chunk=None):
    # Device discovery is the only native boundary needed for construction.
    monkeypatch.setattr(MeetingRecorder, "_resolve_mic_device", staticmethod(lambda _: 0))
    monkeypatch.setattr(MeetingRecorder, "_resolve_system_device", staticmethod(lambda _: 1))
    recorder = MeetingRecorder(on_audio_chunk=on_audio_chunk)
    recorder._recording = True
    recorder._start_time = time.time()
    return recorder


class _BlockedStream:
    def __init__(self, release, *, block="stop"):
        self.release = release
        self.block = block
        self.entered = threading.Event()
        self.closed = threading.Event()
        self.daemon = None

    def start(self):
        pass

    def stop(self):
        self.daemon = threading.current_thread().daemon
        if self.block == "stop":
            self.entered.set()
            self.release.wait(5)

    def close(self):
        if self.block == "close":
            self.entered.set()
            self.release.wait(5)
        self.closed.set()


def test_native_cleanup_uses_one_shared_deadline_and_independent_daemons(monkeypatch):
    monkeypatch.setattr(recorder_module, "_NATIVE_STOP_TIMEOUT_SECONDS", 0.15)
    recorder = _recorder(monkeypatch)
    release = threading.Event()
    streams = [_BlockedStream(release), _BlockedStream(release)]
    recorder._mic_stream, recorder._system_stream = streams
    try:
        before = time.monotonic()
        assert recorder.stop() == ([], [])
        elapsed = time.monotonic() - before
        assert elapsed < 0.27, "two devices must share one 0.15 s budget"
        assert all(stream.entered.is_set() and stream.daemon for stream in streams)
        assert recorder.device_cleanup_error is not None
        assert "mic" in recorder.device_cleanup_error
        assert "system" in recorder.device_cleanup_error
        assert recorder._mic_stream is None and recorder._system_stream is None
        with pytest.raises(MeetingRecorderError, match="Audio device did not close"):
            recorder.start()
    finally:
        release.set()
        assert all(stream.closed.wait(1) for stream in streams)


@pytest.mark.parametrize("block", ["stop", "close"])
def test_a_native_stop_or_close_wedge_cannot_withhold_captured_chunks(monkeypatch, block):
    monkeypatch.setattr(recorder_module, "_NATIVE_STOP_TIMEOUT_SECONDS", 0.02)
    recorder = _recorder(monkeypatch)
    pcm = np.arange(16, dtype=np.float32)
    assert recorder._commit_audio_chunk(pcm, 0, "mic")
    release = threading.Event()
    stream = _BlockedStream(release, block=block)
    recorder._mic_stream = stream
    try:
        mic, system = recorder.stop()
        assert len(mic) == 1 and system == []
        np.testing.assert_array_equal(mic[0].audio, pcm)
        assert recorder.device_cleanup_error is not None
    finally:
        release.set()
        assert stream.closed.wait(1)


def test_close_failure_is_reported_even_when_native_stop_returns(monkeypatch):
    recorder = _recorder(monkeypatch)
    recorder._mic_stream = SimpleNamespace(
        stop=lambda: None,
        close=Mock(side_effect=RuntimeError("device refused close")),
    )
    assert recorder.stop() == ([], [])
    assert "mic audio device did not close" in recorder.device_cleanup_error


@pytest.mark.parametrize("source", ["mic", "system"])
def test_callback_already_resampling_cannot_append_after_stop(monkeypatch, source):
    written = []
    recorder = _recorder(monkeypatch, written.append)
    monkeypatch.setattr(recorder_module, "sd", SimpleNamespace(CallbackFlags=object))
    callbacks = []
    stream = SimpleNamespace(start=lambda: None, stop=lambda: None, close=lambda: None)
    recorder._open_stream = lambda _device, callback: (callbacks.append(callback) or stream, 32000)
    getattr(recorder, f"_start_{source}_stream")()
    entered, release = threading.Event(), threading.Event()

    def resample(pcm, *_args):
        entered.set()
        assert release.wait(2)
        return pcm

    monkeypatch.setattr(recorder_module, "_linear_resample_mono", resample)
    callback = threading.Thread(
        target=callbacks[0], args=(np.ones((16, 1), dtype=np.float32), 16, None, False), daemon=True,
    )
    callback.start()
    try:
        assert entered.wait(1)
        assert recorder.stop() == ([], [])
    finally:
        release.set()
        callback.join(1)
    assert not callback.is_alive()
    assert written == []
    assert recorder._buffer.get_all_chunks() == ([], [])


def test_accepted_journal_commit_finishes_before_stop_snapshot(tmp_path, monkeypatch):
    journal = MeetingCaptureJournal("accepted", directory=tmp_path)
    entered, release, stopped = threading.Event(), threading.Event(), threading.Event()

    def append(chunk):
        entered.set()
        assert release.wait(2)
        journal.append(chunk.source, chunk.audio)

    recorder = _recorder(monkeypatch, append)
    pcm = np.arange(16, dtype=np.float32)
    callback = threading.Thread(target=recorder._commit_audio_chunk, args=(pcm, 0, "mic"), daemon=True)
    callback.start()
    assert entered.wait(1)
    result = []

    def stop():
        result.append(recorder.stop())
        journal.finalize()
        stopped.set()

    worker = threading.Thread(target=stop, daemon=True)
    worker.start()
    try:
        assert not stopped.wait(0.03), "Stop must include an already accepted journal write"
    finally:
        release.set()
        callback.join(1)
        worker.join(1)
    assert stopped.is_set()
    assert len(result[0][0]) == 1
    np.testing.assert_array_equal(result[0][0][0].audio, pcm)
    assert not recorder._commit_audio_chunk(pcm, 1, "mic")
    manifest = json.loads(journal.manifest_path.read_text())
    assert manifest["status"] == "finalized"
    assert manifest["durable_bytes"] == {"mic": pcm.nbytes}


def test_blocked_journal_writer_does_not_block_callback_and_preserves_same_id_pcm(
    tmp_path, monkeypatch
):
    """The callback only admits PCM; Stop waits for that admitted item to land."""
    db = Database(tmp_path / "meetings.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    journal = MeetingCaptureJournal("blocked-writer", directory=tmp_path / "captures")
    writer_entered, release = threading.Event(), threading.Event()
    aborted = threading.Event()

    def blocked_append(chunk):
        writer_entered.set()
        assert release.wait(2)
        journal.append(chunk.source, chunk.audio)

    recorder = _recorder(monkeypatch, blocked_append)
    callbacks = []
    stream = SimpleNamespace(
        start=lambda: None,
        abort=aborted.set,
        close=lambda: None,
    )
    recorder._open_stream = lambda _device, callback: (callbacks.append(callback) or stream, 16_000)
    recorder._start_mic_stream()
    # Real start() creates the writer before opening the stream.  Do that here
    # too so this timing fence measures only callback admission, not thread boot.
    recorder._ensure_writer_started()

    pcm = np.arange(160, dtype=np.float32).reshape(-1, 1)
    started = time.perf_counter()
    callbacks[0](pcm, len(pcm), None, False)
    callback_elapsed = time.perf_counter() - started
    assert callback_elapsed < 0.005
    assert writer_entered.wait(1)

    state = MeetingState(
        id="blocked-writer",
        started_at=datetime.now(),
        capture_status="recording",
    )
    session = MeetingSession(intel_enabled=False)
    session._state = state
    session._recorder = recorder
    session._capture_journal = journal
    session._transcribe_chunks = Mock()
    stopped = []
    stop_thread = threading.Thread(target=lambda: stopped.append(session.stop()), daemon=True)
    stop_thread.start()
    assert not stopped and stop_thread.is_alive()

    release.set()
    stop_thread.join(2)
    assert not stop_thread.is_alive()
    assert aborted.is_set()
    assert stopped[0].id == "blocked-writer"
    recovered = db.meetings.recover_capture("blocked-writer")
    assert recovered is not None and recovered.id == "blocked-writer"
    assert (journal.directory / "mic.f32le.partial").read_bytes() == pcm[:, 0].astype("<f4").tobytes()
    manifest = json.loads(journal.manifest_path.read_text())
    assert manifest["status"] == "finalized"
    assert manifest["durable_bytes"] == {"mic": pcm[:, 0].nbytes}


def test_session_finalizes_and_saves_same_meeting_despite_native_wedge(tmp_path, monkeypatch):
    monkeypatch.setattr(recorder_module, "_NATIVE_STOP_TIMEOUT_SECONDS", 0.02)
    db = Database(tmp_path / "meetings.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    journal = MeetingCaptureJournal("same-meeting", directory=tmp_path / "captures")
    recorder = _recorder(monkeypatch, lambda chunk: journal.append(chunk.source, chunk.audio))
    pcm = np.ones(1600, dtype=np.float32)
    recorder._commit_audio_chunk(pcm, 0, "mic")
    release = threading.Event()
    stream = _BlockedStream(release)
    recorder._mic_stream = stream
    session = MeetingSession()
    session._state = MeetingState(id="same-meeting", started_at=datetime.now(), capture_status="recording")
    session._recorder = recorder
    session._capture_journal = journal
    session._transcribe_chunks = Mock()
    try:
        state = session.stop()
        saved = session.save(directory=tmp_path / "meetings")
        assert saved.database_saved and saved.json_saved
        assert state.id == "same-meeting" and state.ended_at is not None
        assert state.capture_status == "finalized" and state.capture_failure is None
        assert session.device_cleanup_error is not None
        assert [row.id for row in db.meetings.list_meetings()] == [state.id]
        assert db.meetings.get_meeting(state.id).capture_status == "finalized"
        manifest = json.loads(journal.manifest_path.read_text())
        assert manifest["status"] == "finalized"
        assert manifest["durable_bytes"] == {"mic": pcm.nbytes}
    finally:
        release.set()
        assert stream.closed.wait(1)


def test_concurrent_stop_is_refused_before_a_second_finalization(tmp_path, monkeypatch):
    db = Database(tmp_path / "meetings.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    entered, release = threading.Event(), threading.Event()

    def stop_recorder():
        entered.set()
        assert release.wait(2)
        return [], []

    session = MeetingSession()
    session._state = MeetingState(id="single-stop", started_at=datetime.now())
    session._recorder = SimpleNamespace(stop=stop_recorder, get_pending_device_chunks=lambda: {})
    outcomes = []
    first = threading.Thread(target=lambda: outcomes.append(session.stop()), daemon=True)
    first.start()
    try:
        assert entered.wait(1)
        with pytest.raises(RuntimeError, match="already stopping"):
            session.stop()
    finally:
        release.set()
        first.join(2)
    assert not first.is_alive()
    assert len(outcomes) == 1 and outcomes[0].ended_at is not None


@pytest.mark.parametrize("cleanup_error", [None, "mic audio device did not close. Restart HoldSpeak."])
def test_runtime_keeps_device_error_separate_from_successful_save(monkeypatch, cleanup_error):
    monkeypatch.setattr("holdspeak.db.get_database", lambda: object())
    monkeypatch.setattr("holdspeak.services.meeting_backlog_service.queue_after_save", lambda *_: {})
    state = MeetingState(id="saved", started_at=datetime.now(), ended_at=datetime.now())

    class Runtime(MeetingGlueMixin):
        pass

    runtime = Runtime()
    runtime.state_lock = threading.Lock()
    runtime.meeting_lock = threading.Lock()
    runtime.runtime_status = {}
    runtime.recording_ticker = Mock()
    runtime.device_stats_cycle = {}
    runtime.voice_session = Mock()
    runtime._set_runtime_activity = Mock()
    runtime._flush_deferred_plugin_runs_to_db = lambda: {}
    runtime._persist_pending_mir_history = lambda _: {}
    runtime._synthesize_and_persist_artifacts = lambda _: {}
    runtime._associate_meeting_with_projects = lambda _: {}
    runtime.meeting_session = SimpleNamespace(
        is_active=True, state=state, stop=lambda: state, device_cleanup_error=cleanup_error,
        save=lambda: SimpleNamespace(database_saved=True, json_saved=True, json_path=None, intel_job_enqueued=False),
    )
    result = runtime._stop_active_meeting(allow_runtime_fallback=False)
    assert result["status"] == "stopped" and result["save_error"] is None
    assert result["save"]["database_saved"] is True
    assert result["device_cleanup_error"] == cleanup_error
    assert runtime.meeting_session is None
    assert runtime.runtime_status["last_error"] == (cleanup_error or "")
    if cleanup_error:
        runtime.voice_session.release.assert_not_called()
        assert runtime._set_runtime_activity.call_args.kwargs["label"] == "Saved"
        assert runtime._set_runtime_activity.call_args.kwargs["last_error"] == cleanup_error
    else:
        runtime.voice_session.release.assert_called_once_with("meeting")


def _runtime_for_stop(session, monkeypatch):
    monkeypatch.setattr("holdspeak.services.meeting_backlog_service.queue_after_save", lambda *_: {})

    class Runtime(MeetingGlueMixin):
        pass

    runtime = Runtime()
    runtime.state_lock = threading.Lock()
    runtime.meeting_lock = threading.Lock()
    runtime.runtime_status = {}
    runtime.recording_ticker = Mock()
    runtime.device_stats_cycle = {}
    runtime.voice_session = VoiceTypingSession()
    assert runtime.voice_session.acquire("meeting")
    runtime._set_runtime_activity = Mock()
    runtime._flush_deferred_plugin_runs_to_db = lambda: {}
    runtime._persist_pending_mir_history = lambda _: {}
    runtime._synthesize_and_persist_artifacts = lambda _: {}
    runtime._associate_meeting_with_projects = lambda _: {}
    runtime.meeting_session = session
    return runtime


@pytest.mark.parametrize("failed_source", ["mic", "system"])
def test_cleanup_worker_start_failure_preserves_audio_save_and_unavailable_floor(
    tmp_path, monkeypatch, failed_source,
):
    db = Database(tmp_path / "meetings.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    meeting_id = "cleanup-start-failure"
    journal = MeetingCaptureJournal(meeting_id, directory=tmp_path / "captures")
    recorder = _recorder(monkeypatch, lambda chunk: journal.append(chunk.source, chunk.audio))
    pcm = np.arange(16, dtype=np.float32)
    for source in ("mic", "system"):
        assert recorder._commit_audio_chunk(pcm, 0, source)
    streams = {source: SimpleNamespace(stop=Mock(), close=Mock()) for source in ("mic", "system")}
    recorder._mic_stream, recorder._system_stream = streams["mic"], streams["system"]
    started = []
    native_start = threading.Thread.start

    def start(thread):
        started.append(thread.name)
        if thread.name == f"meeting-{failed_source}-cleanup":
            raise RuntimeError("cannot start cleanup worker")
        return native_start(thread)

    monkeypatch.setattr(threading.Thread, "start", start)
    session = MeetingSession()
    session._state = MeetingState(id=meeting_id, started_at=datetime.now(), capture_status="recording")
    session._recorder = recorder
    session._capture_journal = journal
    session._transcribe_chunks = Mock()
    save = session.save
    session.save = Mock(side_effect=lambda: save(directory=tmp_path / "meetings"))
    runtime = _runtime_for_stop(session, monkeypatch)

    result = runtime._stop_active_meeting(allow_runtime_fallback=False)

    assert result["device_cleanup_error"] is not None
    assert f"{failed_source} audio device did not close" in result["device_cleanup_error"]
    assert started == ["meeting-mic-cleanup", "meeting-system-cleanup"]
    other = "system" if failed_source == "mic" else "mic"
    streams[other].stop.assert_called_once_with()
    streams[other].close.assert_called_once_with()
    # Never run uncertain native cleanup on the calling Stop thread.
    streams[failed_source].stop.assert_not_called()
    streams[failed_source].close.assert_not_called()
    mic, system = session._transcribe_chunks.call_args.args
    np.testing.assert_array_equal(mic[0].audio, pcm)
    np.testing.assert_array_equal(system[0].audio, pcm)
    assert not recorder._commit_audio_chunk(pcm, 1, "mic")
    assert result["meeting"]["id"] == meeting_id and result["meeting"]["capture_status"] == "finalized"
    assert result["save_error"] is None
    assert result["save"]["database_saved"] and result["save"]["json_saved"]
    session.save.assert_called_once_with()
    assert [row.id for row in db.meetings.list_meetings()] == [meeting_id]
    manifest = json.loads(journal.manifest_path.read_text())
    assert manifest["status"] == "finalized"
    assert manifest["durable_bytes"] == {"mic": pcm.nbytes, "system": pcm.nbytes}
    assert runtime.voice_session.active_owner == "meeting"
    assert not runtime.voice_session.acquire("hotkey")
    assert runtime.runtime_status["last_error"] == result["device_cleanup_error"]
    assert runtime._set_runtime_activity.call_args.kwargs["label"] == "Saved"


def test_delayed_duplicate_stop_cannot_replace_the_winners_saved_activity(tmp_path, monkeypatch):
    db = Database(tmp_path / "meetings.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    entered, finish_winner = threading.Event(), threading.Event()
    duplicate_reached, finish_duplicate = threading.Event(), threading.Event()
    meeting_id = "single-runtime-stop"

    def stop_recorder():
        entered.set()
        assert finish_winner.wait(3)
        return [], []

    session = MeetingSession()
    session._state = MeetingState(id=meeting_id, started_at=datetime.now())
    session._recorder = SimpleNamespace(stop=stop_recorder, get_pending_device_chunks=lambda: {})
    save = session.save
    session.save = Mock(side_effect=lambda: save(directory=tmp_path / "meetings"))
    runtime = _runtime_for_stop(session, monkeypatch)

    def stop_ticker():
        if threading.current_thread().name == "duplicate-stop":
            duplicate_reached.set()
            assert finish_duplicate.wait(3)

    runtime.recording_ticker.stop.side_effect = stop_ticker
    results, failures = {}, {}

    def stop(name):
        try:
            results[name] = runtime._stop_active_meeting(allow_runtime_fallback=False)
        except Exception as exc:
            failures[name] = exc
        finally:
            if name == "duplicate":
                duplicate_reached.set()

    winner = threading.Thread(target=stop, args=("winner",), name="winner-stop", daemon=True)
    duplicate = threading.Thread(target=stop, args=("duplicate",), name="duplicate-stop", daemon=True)
    winner.start()
    try:
        assert entered.wait(1)
        duplicate.start()
        # Either the old preamble is now held or the new guard refused it.
        assert duplicate_reached.wait(1)
        finish_winner.set()
        winner.join(3)
        assert not winner.is_alive() and "winner" in results, failures
        assert runtime._set_runtime_activity.call_args.kwargs["label"] == "Saved"
    finally:
        finish_winner.set()
        finish_duplicate.set()
        winner.join(3)
        if duplicate.ident is not None:
            duplicate.join(3)
    assert not duplicate.is_alive()
    assert [call.args[0] for call in runtime._set_runtime_activity.call_args_list] == ["saving", "complete"]
    assert runtime.recording_ticker.stop.call_count == 1
    assert isinstance(failures.get("duplicate"), RuntimeError)
    assert str(failures["duplicate"]) == "Meeting is already stopping"
    assert "duplicate" not in results
    assert results["winner"]["meeting"]["id"] == meeting_id
    assert results["winner"]["save_error"] is None
    assert results["winner"]["save"]["database_saved"] and results["winner"]["save"]["json_saved"]
    session.save.assert_called_once_with()
    assert [row.id for row in db.meetings.list_meetings()] == [meeting_id]
    assert runtime.meeting_session is None and runtime.runtime_status["last_error"] == ""
    assert runtime.voice_session.active_owner is None


@pytest.mark.parametrize("path", ["/api/meeting/stop", "/api/stop"])
def test_stop_route_keeps_loop_responsive_and_broadcasts_warning_on_loop(path):
    async def exercise():
        entered, release = threading.Event(), threading.Event()
        loop_thread = threading.get_ident()
        broadcasts = []

        def stop():
            assert threading.get_ident() != loop_thread
            entered.set()
            assert release.wait(3)
            return {"status": "stopped", "device_cleanup_error": "Audio device did not close."}

        service = MeetingService(None)
        service.bind_lifecycle(on_stop=stop)
        ctx = WebContext(
            get_state=lambda: {}, meeting_service=service,
            broadcast=lambda *args: broadcasts.append((threading.get_ident(), args)),
        )
        app = FastAPI()
        app.include_router(build_live_router(ctx))

        @app.get("/health")
        async def health():
            return {"ok": True}

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            stopping = asyncio.create_task(client.post(path))
            try:
                assert await asyncio.to_thread(entered.wait, 1)
                assert not stopping.done()
                response = await asyncio.wait_for(client.get("/health"), timeout=0.5)
                assert response.json() == {"ok": True}
            finally:
                release.set()
            response = await stopping
        assert response.status_code == 200
        assert response.json() == {"success": True, "warning": "Audio device did not close."}
        assert len(broadcasts) == 1 and broadcasts[0][0] == loop_thread
        assert broadcasts[0][1][0] == "stopped"
        assert broadcasts[0][1][1]["device_cleanup_error"] == "Audio device did not close."

    asyncio.run(exercise())


@pytest.mark.parametrize("path", ["/api/meeting/stop", "/api/stop"])
def test_second_stop_answers_conflict(path):
    async def exercise():
        def stop():
            raise RuntimeError("Meeting is already stopping")

        service = MeetingService(None)
        service.bind_lifecycle(on_stop=stop)
        app = FastAPI()
        app.include_router(build_live_router(WebContext(get_state=lambda: {}, meeting_service=service)))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(path)
        assert response.status_code == 409
        assert response.json() == {"success": False, "error": "Meeting is already stopping"}

    asyncio.run(exercise())


def test_queue_overflow_is_refused_and_saved_as_capture_failure(tmp_path, monkeypatch):
    db = Database(tmp_path / "meetings.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    monkeypatch.setattr(recorder_module, "_CAPTURE_QUEUE_MAX_CHUNKS", 1)
    journal = MeetingCaptureJournal("overflow", directory=tmp_path / "captures")
    entered, release = threading.Event(), threading.Event()

    def append(chunk):
        entered.set()
        assert release.wait(2)
        journal.append(chunk.source, chunk.audio)

    recorder = _recorder(monkeypatch, append)
    pcm = np.ones(160, dtype=np.float32)
    try:
        assert recorder._commit_audio_chunk(pcm, 0, "mic")
        assert entered.wait(1)
        assert recorder._commit_audio_chunk(pcm, 1, "mic")
        assert not recorder._commit_audio_chunk(pcm, 2, "mic")
    finally:
        release.set()
    session = MeetingSession(intel_enabled=False)
    session._state = MeetingState(id="overflow", started_at=datetime.now(), capture_status="recording")
    session._recorder = recorder
    session._capture_journal = journal
    session._transcribe_chunks = Mock()
    state = session.stop()
    assert state.capture_status == "recoverable"
    assert "overflow" in state.capture_failure.lower()
    stored = db.meetings.get_meeting("overflow")
    assert stored.capture_failure == state.capture_failure
    manifest = json.loads(journal.manifest_path.read_text())
    assert manifest["status"] == "recoverable"
    assert manifest["durable_bytes"] == {"mic": 2 * pcm.nbytes}
