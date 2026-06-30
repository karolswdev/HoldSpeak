"""HS-69-08 — the additive `audio_level` WS frame (the reactive waveform source).

The recorders already compute a 0..1 level per chunk (AudioRecorder.on_level /
MeetingSession on_mic_level/on_system_level); the runtime's `_emit_audio_level`
throttles + broadcasts it as `{"type": "audio_level", "data": {...}}`. These
lock the broadcast shape, the clamp, the throttle, and the no-server guard
without booting the full runtime.
"""
from __future__ import annotations

from unittest.mock import MagicMock

from holdspeak.web_runtime import WebRuntime


def _runtime(server):
    rt = WebRuntime.__new__(WebRuntime)  # skip the heavy __init__
    rt.server = server
    rt._last_audio_level_ts = 0.0
    return rt


def test_emit_broadcasts_audio_level_frame():
    server = MagicMock()
    rt = _runtime(server)
    rt._emit_audio_level(0.5, "dictation")
    server.broadcast.assert_called_once()
    msg_type, data = server.broadcast.call_args[0]
    assert msg_type == "audio_level"
    assert data == {"level": 0.5, "source": "dictation"}


def test_emit_is_throttled():
    server = MagicMock()
    rt = _runtime(server)
    rt._emit_audio_level(0.5, "dictation")
    server.broadcast.reset_mock()
    # an immediate second call (well under the ~66 ms window) is dropped
    rt._emit_audio_level(0.9, "dictation")
    server.broadcast.assert_not_called()
    # but after the window elapses it broadcasts again
    rt._last_audio_level_ts -= 1.0
    rt._emit_audio_level(0.9, "dictation")
    server.broadcast.assert_called_once()


def test_emit_clamps_to_unit_range():
    server = MagicMock()
    rt = _runtime(server)
    rt._emit_audio_level(2.5, "meeting_mic")
    assert server.broadcast.call_args[0][1]["level"] == 1.0
    rt._last_audio_level_ts -= 1.0
    rt._emit_audio_level(-0.3, "meeting_mic")
    assert server.broadcast.call_args[0][1]["level"] == 0.0


def test_emit_no_server_is_silent():
    rt = _runtime(None)
    rt._emit_audio_level(0.5, "dictation")  # must not raise
