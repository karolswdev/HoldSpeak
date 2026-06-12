"""HS-60-02 — arm, capture, and the pipeline (fakes end to end).

The conditions under test: a detection arms visibly and captures through
the ArmedCapture state machine; the floor model blocks arming while any
owner holds the audio floor; the preview default NEVER touches the typing
seam (the journal + broadcast + one-shot token are the outcome); the type
action is the explicit opt-in that types the pipeline result; an expired
window disarms silently; a disabled config constructs nothing.
"""
from __future__ import annotations

import queue as queue_mod
import threading
from types import SimpleNamespace

import numpy as np
import pytest

import holdspeak.web_runtime as web_runtime
from holdspeak.voice_typing import VoiceTypingSession
from holdspeak.wake_word import FRAME_SAMPLES, ArmedCapture
from holdspeak.web_runtime import WebRuntime

LOUD = (np.ones(FRAME_SAMPLES) * 3000).astype(np.int16)
QUIET = np.zeros(FRAME_SAMPLES, dtype=np.int16)


# ── ArmedCapture ─────────────────────────────────────────────────────────────


def test_capture_waits_then_captures_until_silence():
    cap = ArmedCapture(window_seconds=8.0, silence_seconds=0.16)  # 2 silent frames
    assert cap.feed(QUIET) == "waiting"
    assert cap.feed(LOUD) == "capturing"
    assert cap.feed(LOUD) == "capturing"
    cap.feed(QUIET)
    assert cap.feed(QUIET) == "captured"
    audio = cap.result()
    assert audio is not None and audio.dtype == np.float32
    assert len(audio) == 4 * FRAME_SAMPLES  # loud, loud, quiet, quiet


def test_capture_expires_when_nothing_is_spoken():
    cap = ArmedCapture(window_seconds=0.16)  # a 2-frame window
    cap.feed(QUIET)
    assert cap.feed(QUIET) == "expired"
    assert cap.result() is None


def test_capture_caps_a_runaway_utterance():
    cap = ArmedCapture(window_seconds=8.0, max_utterance_seconds=0.24)  # 3 frames
    cap.feed(LOUD)
    cap.feed(LOUD)
    assert cap.feed(LOUD) == "captured"
    assert cap.result() is not None


# ── the runtime glue, via a bare WebRuntime ─────────────────────────────────


class _ServerSpy:
    def __init__(self):
        self.broadcasts: list[tuple[str, dict]] = []
        self.dictation_journal = None
        self.dictation_corrections = None
        self.dictation_telemetry = None

    def broadcast(self, message_type, data):
        self.broadcasts.append((message_type, data))


class _TyperSpy:
    def __init__(self):
        self.typed: list[str] = []

    def type_text(self, text):
        self.typed.append(text)


def _bare_runtime(action="preview", window_seconds=8.0):
    rt = WebRuntime.__new__(WebRuntime)
    rt.config = SimpleNamespace(
        wake_word=SimpleNamespace(
            enabled=True,
            model="hey_jarvis",
            threshold=0.5,
            armed_window_seconds=window_seconds,
            action=action,
        ),
    )
    rt.voice_session = VoiceTypingSession()
    rt.runtime_stop_event = threading.Event()
    rt.transcription_lock = threading.Lock()
    rt.server = _ServerSpy()
    rt.typer = _TyperSpy()
    rt.wake_previews = {}
    rt._wake_listener = None
    rt._wake_stream = None
    rt._wake_queue = queue_mod.Queue()
    rt.activities = []
    rt._set_runtime_activity = lambda state, **kw: rt.activities.append((state, kw))
    from holdspeak.text_processor import TextProcessor

    rt.text_processor = TextProcessor()
    rt._ensure_transcriber_loaded = lambda: SimpleNamespace(
        transcribe=lambda audio: "ship the fix period"
    )
    return rt


def test_detect_arms_captures_and_hands_off(monkeypatch):
    rt = _bare_runtime()
    handed: list[np.ndarray] = []
    rt._transcribe_wake = handed.append
    for frame in (QUIET, LOUD, LOUD) + (QUIET,) * 16:
        rt._wake_queue.put(frame)
    rt._on_wake_detect(0.9)

    assert [s for s, _ in rt.activities][0] == "armed"
    assert [t for t, _ in rt.server.broadcasts] == ["wake_armed"]
    assert len(handed) == 1 and handed[0].dtype == np.float32
    # The floor was released.
    assert rt.voice_session.active_owner is None


def test_detect_skips_silently_while_the_floor_is_held():
    rt = _bare_runtime()
    rt._transcribe_wake = lambda audio: pytest.fail("must not capture")
    assert rt.voice_session.acquire("hotkey")
    rt._on_wake_detect(0.9)
    assert rt.activities == []
    assert rt.server.broadcasts == []
    rt.voice_session.release("hotkey")


def test_expired_window_disarms_silently():
    rt = _bare_runtime(window_seconds=2.0)  # 25 frames
    rt._transcribe_wake = lambda audio: pytest.fail("nothing was spoken")
    for _ in range(30):
        rt._wake_queue.put(QUIET)
    rt._on_wake_detect(0.9)
    states = [s for s, _ in rt.activities]
    assert states[0] == "armed" and states[-1] == "complete"
    assert rt.activities[-1][1]["last_event"] == "wake_disarmed"
    assert rt.voice_session.active_owner is None


def test_preview_default_never_types(monkeypatch):
    rt = _bare_runtime(action="preview")
    seen: dict = {}

    def fake_pipeline(text, **kwargs):
        seen.update(kwargs, text=text)
        return text.upper()

    monkeypatch.setattr(web_runtime, "run_dictation_pipeline", fake_pipeline)
    rt._transcribe_wake(np.zeros(16000, dtype=np.float32))

    assert rt.typer.typed == []  # the condition: preview NEVER types
    assert seen["journal_source"] == "wake"
    (kind, data), = [b for b in rt.server.broadcasts if b[0] == "wake_preview"]
    assert data["text"] == "SHIP THE FIX."
    token = data["token"]
    assert rt.consume_wake_preview(token) == "SHIP THE FIX."
    assert rt.consume_wake_preview(token) is None  # one-shot: burned


def test_type_action_is_the_explicit_opt_in(monkeypatch):
    rt = _bare_runtime(action="type")
    monkeypatch.setattr(web_runtime, "run_dictation_pipeline", lambda text, **kw: text)
    rt._transcribe_wake(np.zeros(16000, dtype=np.float32))
    assert rt.typer.typed == ["ship the fix."]
    assert all(t != "wake_preview" for t, _ in rt.server.broadcasts)


def test_a_new_preview_invalidates_the_old(monkeypatch):
    rt = _bare_runtime(action="preview")
    monkeypatch.setattr(web_runtime, "run_dictation_pipeline", lambda text, **kw: text)
    rt._transcribe_wake(np.zeros(16000, dtype=np.float32))
    first = list(rt.wake_previews)[0]
    rt._transcribe_wake(np.zeros(16000, dtype=np.float32))
    assert rt.consume_wake_preview(first) is None
    assert len(rt.wake_previews) == 1


def test_disabled_config_constructs_nothing():
    rt = _bare_runtime()
    rt.config.wake_word.enabled = False
    rt._start_wake_listener = lambda: pytest.fail("must not start when disabled")
    rt._sync_wake_word()
    assert rt._wake_listener is None
