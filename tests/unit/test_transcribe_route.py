"""HS-78-01 — the speak-to-fill transcribe route.

Browser-captured WAV (16 kHz mono 16-bit) in; the runtime's OWN
transcriber out. No persistence, no egress; the strict-format and
size-cap refusals are honest 4xx, and a runtime without the callback is
an honest 503.
"""

from __future__ import annotations

import io
import wave

import numpy as np
import pytest

pytest.importorskip("fastapi", reason="route tests drive the real app")

from fastapi.testclient import TestClient

from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


def _wav_bytes(*, rate: int = 16000, channels: int = 1, width: int = 2,
               seconds: float = 0.25) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(width)
        wf.setframerate(rate)
        wf.writeframes(np.zeros(int(rate * seconds), dtype=np.int16).tobytes())
    return buf.getvalue()


def _client(on_transcribe=None) -> TestClient:
    server = MeetingWebServer(WebRuntimeCallbacks(
        on_bookmark=lambda *a, **k: None, on_stop=lambda *a, **k: None,
        get_state=lambda: {"activity": {"state": "idle"}},
        on_transcribe=on_transcribe,
    ), host="127.0.0.1")
    return TestClient(server.app)


def test_transcribes_a_valid_wav_through_the_runtime_verb() -> None:
    heard: list[np.ndarray] = []

    def on_transcribe(audio):
        heard.append(audio)
        return "hello desk"

    client = _client(on_transcribe)
    resp = client.post(
        "/api/dictation/transcribe",
        content=_wav_bytes(),
        headers={"Content-Type": "application/octet-stream"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"success": True, "text": "hello desk"}
    # The route decoded to the pipeline's shape: float32 mono in [-1, 1].
    assert len(heard) == 1
    assert heard[0].dtype == np.float32
    assert heard[0].shape == (4000,)


def test_refuses_wrong_format_wavs() -> None:
    client = _client(lambda a: "never")
    for bad in (
        _wav_bytes(rate=44100),
        _wav_bytes(channels=2),
        _wav_bytes(width=4),
    ):
        resp = client.post("/api/dictation/transcribe", content=bad)
        assert resp.status_code == 400
        assert "16 kHz" in resp.json()["error"]


def test_refuses_garbage_empty_and_oversize() -> None:
    client = _client(lambda a: "never")
    assert client.post("/api/dictation/transcribe", content=b"").status_code == 400
    assert client.post(
        "/api/dictation/transcribe", content=b"not a wav at all"
    ).status_code == 400
    assert client.post(
        "/api/dictation/transcribe", content=b"\0" * 16_000_001
    ).status_code == 413


def test_headless_runtime_is_an_honest_503() -> None:
    client = _client(None)
    resp = client.post("/api/dictation/transcribe", content=_wav_bytes())
    assert resp.status_code == 503


def test_the_runtime_verb_runs_the_real_pipeline_pieces() -> None:
    """The mixin verb: one lock, the transcriber, the punctuation pass."""
    import threading
    from types import SimpleNamespace

    from holdspeak.runtime.dictation_capture import DictationCaptureMixin

    class Rig:
        transcription_lock = threading.Lock()
        text_processor = SimpleNamespace(process=lambda self_, t=None: None)

        def __init__(self):
            self.text_processor = SimpleNamespace(process=lambda t: t.upper())

        def _ensure_transcriber_loaded(self):
            return SimpleNamespace(transcribe=lambda a: "quiet words")

        transcribe_audio = DictationCaptureMixin.transcribe_audio

    rig = Rig()
    assert rig.transcribe_audio(np.zeros(16000, dtype=np.float32)) == "QUIET WORDS"
