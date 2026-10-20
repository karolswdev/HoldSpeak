"""C10 — native capture belongs to a child process with a bounded Stop."""

from __future__ import annotations

import multiprocessing as mp
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from holdspeak.capture_process import run_capture_process
from holdspeak.db import Database
from holdspeak.meeting_capture_journal import MeetingCaptureJournal
from holdspeak.meeting_recorder import AudioChunk, MeetingRecorder, MeetingRecorderError
from holdspeak.meeting_session import MeetingSession, MeetingState
from holdspeak.runtime.meeting_stop import finish_meeting_stop
from holdspeak.voice_typing import VoiceTypingSession


pytestmark = pytest.mark.integration


def _run_capture_child(
    connection, config: dict[str, object], hang: bool, exit_early: bool = False,
) -> None:
    """A real child process double with durable PCM and a controllable hang."""
    root = Path(str(config["capture_directory"]))
    journal = MeetingCaptureJournal(
        str(config["meeting_id"]),
        sample_rate=int(config["sample_rate"]),
        directory=root,
    )
    audio = np.arange(32, dtype=np.float32)
    journal.append("mic", audio)
    journal.checkpoint()
    connection.send({"type": "ready"})
    connection.send(
        {
            "type": "chunk",
            "source": "mic",
            "timestamp": 0.0,
            "duration": len(audio) / int(config["sample_rate"]),
            "audio": audio.astype("<f4").tobytes(),
        }
    )
    if exit_early:
        connection.close()
        return
    try:
        while True:
            if not connection.poll(0.01):
                continue
            command = connection.recv()
            if command.get("command") != "stop":
                continue
            if hang:
                # The parent must enforce its deadline and terminate this
                # actual child.  The checkpoint above remains the source of
                # truth after termination.
                while True:
                    time.sleep(0.01)
            journal.seal()
            connection.send({"type": "stopped"})
            return
    finally:
        connection.close()


def _recorder(
    tmp_path: Path, *, hang: bool, exit_early: bool = False,
) -> tuple[MeetingRecorder, Path]:
    root = tmp_path / "captures"

    def process_factory(*, target, args, daemon):
        _ = target, daemon
        connection, config = args
        context = mp.get_context("spawn")
        return context.Process(
            target=_run_capture_child,
            args=(connection, config, hang, exit_early),
            daemon=daemon,
        )

    recorder = MeetingRecorder(
        sample_rate=16_000,
        mic_device=0,
        system_device=1,
        capture_directory=root,
        meeting_id="c10-meeting",
        process_factory=process_factory,
    )
    return recorder, root


def _wait_for_chunk(recorder: MeetingRecorder) -> None:
    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline:
        mic, _system = recorder.get_pending_chunks()
        if mic:
            return
        time.sleep(0.005)
    raise AssertionError("capture child did not publish its accepted PCM")


def test_child_owns_durable_audio_and_hung_stop_exits_under_deadline(tmp_path):
    recorder, root = _recorder(tmp_path, hang=True)
    recorder.start()
    _wait_for_chunk(recorder)
    child_pid = recorder.capture_process_pid
    assert child_pid and child_pid != os.getpid()

    started = time.monotonic()
    mic, system = recorder.stop()
    elapsed = time.monotonic() - started

    assert elapsed < 1.5
    assert len(mic) == 1 and system == []
    assert recorder.capture_process_exited is True
    assert recorder.device_cleanup_error and "child terminated" in recorder.device_cleanup_error
    assert recorder.capture_failure and "recover the journal" in recorder.capture_failure
    failed_record_warning = recorder.device_cleanup_error
    with pytest.raises(MeetingRecorderError, match="Not recording"):
        recorder.stop()

    [manifest] = MeetingCaptureJournal.recoverable(root)
    assert manifest["meeting_id"] == "c10-meeting"
    assert manifest["durable_bytes"] == {"mic": 32 * 4}
    audio_path = root / "c10-meeting" / "mic.f32le.partial"
    assert audio_path.read_bytes() == np.arange(32, dtype="<f4").tobytes()

    # A child timeout is local to that capture.  The next Record can reuse
    # the desk recorder after the child has exited.
    recorder.start()
    assert recorder.device_cleanup_error is None
    _wait_for_chunk(recorder)
    next_mic, next_system = recorder.stop()
    assert len(next_mic) == 1 and next_system == []
    assert failed_record_warning and "child terminated" in failed_record_warning


def test_unexpected_capture_child_exit_marks_session_recoverable(tmp_path, monkeypatch):
    db = Database(tmp_path / "meetings.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    recorder, root = _recorder(tmp_path, hang=False, exit_early=True)
    recorder.start()
    _wait_for_chunk(recorder)

    session = MeetingSession(intel_enabled=False)
    session._state = MeetingState(
        id="c10-meeting", started_at=datetime.now(), capture_status="recording"
    )
    session._recorder = recorder
    session._capture_journal = MeetingCaptureJournal("c10-meeting", directory=root)

    stopped = session.stop()
    assert stopped.capture_status == "recoverable"
    assert stopped.capture_failure and "terminal status" in stopped.capture_failure
    saved = db.meetings.get_meeting("c10-meeting")
    assert saved is not None and saved.capture_status == "recoverable"


class _PressureRecorder:
    """Native double used through the production child runner, not its seam."""

    capture_failure = None
    device_cleanup_error = None

    def __init__(self, *, on_mic_level, on_audio_chunk, **_kwargs):
        self._on_mic_level = on_mic_level
        self._on_audio_chunk = on_audio_chunk

    def start(self):
        for index in range(5_000):
            self._on_mic_level(index / 5_000)
        audio = np.arange(8, dtype=np.float32)
        self._on_audio_chunk(AudioChunk(audio, 0.0, "mic", 0.5))

    def stop(self):
        raise RuntimeError("native close failed")


def test_production_capture_runner_delivers_pcm_and_terminal_failure_under_level_pressure(
    tmp_path, monkeypatch,
):
    monkeypatch.setattr("holdspeak.meeting_recorder.MeetingRecorder", _PressureRecorder)
    context = mp.get_context("spawn")
    parent_connection, child_connection = context.Pipe(duplex=True)
    runner = threading.Thread(
        target=run_capture_process,
        args=(child_connection, {
            "meeting_id": "production-c10",
            "capture_directory": str(tmp_path / "captures"),
            "sample_rate": 16_000,
            "mic_device": 0,
            "system_device": 1,
        }),
        daemon=True,
    )
    runner.start()
    events: list[dict[str, object]] = []
    deadline = time.monotonic() + 5.0
    try:
        while time.monotonic() < deadline:
            if parent_connection.poll(0.05):
                events.append(parent_connection.recv())
                if any(e.get("type") == "ready" for e in events) and any(
                    e.get("type") == "chunk" for e in events
                ):
                    break
        assert any(e.get("type") == "ready" for e in events)
        chunks = [e for e in events if e.get("type") == "chunk"]
        assert len(chunks) == 1
        assert np.frombuffer(chunks[0]["audio"], dtype="<f4").tolist() == list(range(8))
        assert len([e for e in events if e.get("type") == "level"]) < 5_000

        parent_connection.send({"command": "stop"})
        while time.monotonic() < deadline and not any(
            e.get("type") == "stopped" for e in events
        ):
            if parent_connection.poll(0.05):
                events.append(parent_connection.recv())
        stopped = next(e for e in events if e.get("type") == "stopped")
        assert stopped["error"] == "Capture child stop failed: native close failed"
    finally:
        parent_connection.close()
        runner.join(timeout=2.0)
    assert not runner.is_alive()


def test_child_exit_releases_floor_for_the_next_manual_record(tmp_path):
    recorder, _root = _recorder(tmp_path, hang=False)
    recorder.start()
    _wait_for_chunk(recorder)
    recorder.stop()

    floor = VoiceTypingSession()
    assert floor.acquire("meeting")
    runtime = SimpleNamespace(
        recording_ticker=SimpleNamespace(stop=lambda: None),
        device_stats_cycle={},
        voice_session=floor,
        meeting_session=None,
        state_lock=threading.Lock(),
        meeting_lock=threading.Lock(),
        runtime_status={},
        last_meeting_snapshot=None,
        _set_runtime_activity=lambda *args, **kwargs: None,
        _flush_deferred_plugin_runs_to_db=lambda: {},
        _persist_pending_mir_history=lambda _meeting_id: {},
        _synthesize_and_persist_artifacts=lambda _meeting_id: {},
        _associate_meeting_with_projects=lambda _meeting_id: {},
    )
    state = SimpleNamespace(devices=[], to_dict=lambda: {"id": ""})
    session = SimpleNamespace(
        state=state,
        capture_process_exited=True,
        device_cleanup_error="Capture process did not exit within 1 second; child terminated.",
        stop=lambda: state,
        save=lambda: SimpleNamespace(
            database_saved=True,
            json_saved=False,
            json_path=None,
            intel_job_enqueued=False,
        ),
    )

    result = finish_meeting_stop(runtime, session, audio_owner="meeting")
    assert result["status"] == "stopped"
    assert floor.acquire("meeting") is True

