"""Live slice 3 (2026-10-28): the hub facts the Live window draws.

Canvas ``docs/internal/betterment/canvases/live-direction-2026-10-27.html``,
direction A. Two facts the hub did not say before:

* ``POST /api/meeting/mic-check`` — Before: what the meeting microphone hears
  now (one short sample, the macOS grant read first, never asked for).
* the ``transcript_pass`` frame — During: the engine writes / listens, and how
  far the saved transcript reaches.
"""
from __future__ import annotations

import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_desk_needs_you as seeds  # noqa: E402
from holdspeak import desktop_permissions
from holdspeak.meeting_session import MeetingState, mic_check
from holdspeak.meeting_session.transcribe_loop import TranscribeLoopMixin
from holdspeak.realtime_frames import RUNTIME_FRAME_TYPES


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from holdspeak.db import reset_database
    from holdspeak.runtime import composition

    monkeypatch.delenv(mic_check.MIC_CHECK_ENV, raising=False)
    yield seeds._boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _grant(monkeypatch: pytest.MonkeyPatch, state: str, source: str = "AVCaptureDevice.authorizationStatusForMediaType") -> None:
    monkeypatch.setitem(desktop_permissions._PROBES, desktop_permissions.MICROPHONE, lambda: (state, source))


def _sample(monkeypatch: pytest.MonkeyPatch, rms: float | Exception) -> list[Any]:
    calls: list[Any] = []

    def record(device: Any, seconds: float) -> Any:
        calls.append((device, seconds))
        if isinstance(rms, Exception):
            raise rms
        return np.full(int(seconds * mic_check.SAMPLE_RATE), rms, dtype=np.float32)

    monkeypatch.setattr(mic_check, "_record_sample", record)
    return calls


def _check(hub: Any) -> dict[str, Any]:
    response = hub.client.post("/api/meeting/mic-check")
    assert response.status_code == 200, response.text
    return response.json()


def test_mic_check_hears_a_voice_on_the_configured_microphone(hub: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _grant(monkeypatch, desktop_permissions.GRANTED)
    calls = _sample(monkeypatch, 0.05)  # about -26 dBFS: a voice
    answer = _check(hub)
    assert answer["state"] == "hearing"
    assert answer["permission"] == "granted"
    assert 0.6 < answer["level"] <= 1.0
    assert answer["settings_url"].startswith("x-apple.systempreferences:")
    # One short sample from the meeting microphone (None = the system default).
    assert calls == [(None, mic_check.SAMPLE_SECONDS)]


def test_mic_check_says_quiet_for_digital_silence(hub: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _grant(monkeypatch, desktop_permissions.GRANTED)
    _sample(monkeypatch, 0.0)
    answer = _check(hub)
    assert answer["state"] == "quiet"
    assert answer["level"] == 0.0


@pytest.mark.parametrize(
    ("grant", "state"),
    [(desktop_permissions.DENIED, "not_allowed"), (desktop_permissions.NOT_DETERMINED, "not_asked"),
     (desktop_permissions.UNKNOWN, "unknown")],
)
def test_mic_check_opens_no_device_without_a_grant(hub: Any, monkeypatch: pytest.MonkeyPatch, grant: str, state: str) -> None:
    """Checking never prompts: a refused, unasked or unreadable grant on a Mac opens nothing."""
    _grant(monkeypatch, grant)
    calls = _sample(monkeypatch, 0.05)
    answer = _check(hub)
    assert answer["state"] == state
    assert answer["level"] is None
    assert calls == []


def test_mic_check_listens_off_a_mac(hub: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _grant(monkeypatch, desktop_permissions.UNKNOWN, source="not macOS (Linux)")
    calls = _sample(monkeypatch, 0.05)
    assert _check(hub)["state"] == "hearing"
    assert len(calls) == 1


def test_mic_check_leaves_a_live_meeting_its_microphone(hub: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _grant(monkeypatch, desktop_permissions.GRANTED)
    calls = _sample(monkeypatch, 0.05)
    hub.server.get_state.return_value = {"meeting_active": True, "id": "m-live"}
    assert _check(hub)["state"] == "in_use"
    assert calls == []


def test_mic_check_switch_keeps_a_rig_off_the_microphone(hub: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _grant(monkeypatch, desktop_permissions.GRANTED)
    calls = _sample(monkeypatch, 0.05)
    monkeypatch.setenv(mic_check.MIC_CHECK_ENV, "off")
    assert _check(hub)["state"] == "off"
    assert calls == []


def test_mic_check_names_a_device_that_does_not_answer(hub: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _grant(monkeypatch, desktop_permissions.GRANTED)
    _sample(monkeypatch, RuntimeError("Error opening InputStream: Invalid device"))
    answer = _check(hub)
    assert answer["state"] == "failed"
    assert "Invalid device" in answer["error"]


# ── transcript_pass: the engine writes, then listens ─────────────────────


class _Stop:
    """`_stop_event` that lets the loop run one pass, then stops it."""

    def __init__(self) -> None:
        self.waits = 0

    def wait(self, _timeout: float) -> bool:
        self.waits += 1
        return self.waits > 1

    def is_set(self) -> bool:
        return self.waits > 1


class _Recorder:
    def get_pending_chunks(self, since: float) -> tuple[list[str], list[str]]:
        return (["mic-chunk"], [])

    def get_pending_device_chunks(self) -> dict[str, list[str]]:
        return {}


class _Session(TranscribeLoopMixin):
    TRANSCRIBE_INTERVAL = 10.0

    def __init__(self, transcriber: Any = object()) -> None:
        self.transcriber = transcriber
        self._lock = threading.Lock()
        self._state = MeetingState(id="m-pass", started_at=datetime(2026, 10, 28, 10, 0, 0))
        self._recorder = _Recorder()
        self._last_transcribe_time = 0.0
        self._stop_event = _Stop()
        self.frames: list[tuple[str, dict[str, Any]]] = []

    def _emit_broadcast(self, message_type: str, data: Any) -> None:
        self.frames.append((message_type, data))

    def _transcribe_chunks(self, mic: Any, system: Any, **_: Any) -> None:
        # The pass checkpoints the transcript as the real one does.
        self.frames.append(("_pass", {}))
        self._state.capture_checkpoint_seconds = 41.5
        self._state.capture_checkpoint_at = datetime(2026, 10, 28, 10, 0, 42)


def test_transcript_pass_frames_bracket_each_pass() -> None:
    session = _Session()
    session._transcribe_loop()
    kinds = [kind for kind, _ in session.frames]
    assert kinds == ["transcript_pass", "_pass", "transcript_pass"]
    writing, listening = session.frames[0][1], session.frames[2][1]
    assert writing == {"meeting_id": "m-pass", "state": "writing", "saved_through": 0.0, "saved_at": None, "every": 10.0}
    assert listening["state"] == "listening"
    assert listening["saved_through"] == 41.5
    assert listening["saved_at"] == "2026-10-28T10:00:42"


def test_transcript_pass_is_silent_without_speech() -> None:
    """No transcriber (speech not set up): nothing is written, so nothing is said."""
    session = _Session(transcriber=None)
    session._transcribe_loop()
    assert [kind for kind, _ in session.frames] == ["_pass"]


def test_transcript_pass_is_a_registered_frame() -> None:
    assert "transcript_pass" in RUNTIME_FRAME_TYPES
