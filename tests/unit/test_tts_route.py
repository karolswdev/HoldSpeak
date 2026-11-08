"""The desk's /api/tts speaks through the Line's Pocket TTS (one hub voice, 2026-11-07).

- Status: ``installed`` = the ``line`` extra imports; ``model_ready`` = the
  Line's TTS preset is ready; ``engine`` and ``voice`` name the Line's voice.
- POST streams a WAV at the Line's rate from the engine's PCM chunks.
- 404 ``tts_not_installed`` without the extra; 404 ``tts_model_not_ready``
  before the weights are fetched.
- The download route starts the Line's fetch job once (no second downloader).
"""
from __future__ import annotations

import struct
from typing import Any, Iterator

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.line import models as line_models
from holdspeak.line import speech
from holdspeak.line.audio import RATE
from holdspeak.web.context import WebContext
from holdspeak.web.routes import tts as tts_routes


class FakePocket:
    made: list[str] = []

    def __init__(self, *, voice: str = speech.TTS_VOICE, threads: Any = None) -> None:
        FakePocket.made.append(voice)

    def stream(self, text: str, stop: Any = None) -> Iterator[np.ndarray]:
        yield np.full(160, 1000, dtype=np.int16)
        yield np.full(320, -1000, dtype=np.int16)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    tts_routes._reset_state()
    FakePocket.made = []
    monkeypatch.setattr(tts_routes, "_line_installed", lambda: True)
    monkeypatch.setattr(line_models, "ready", lambda row: True)
    monkeypatch.setattr(speech, "Pocket", FakePocket)
    app = FastAPI()
    app.include_router(tts_routes.build_tts_router(WebContext(get_state=lambda: {})))
    yield TestClient(app)
    tts_routes._reset_state()


def test_status_names_the_line_engine_and_reads_the_preset(client, monkeypatch) -> None:
    seen: list[str] = []
    monkeypatch.setattr(line_models, "ready", lambda row: seen.append(row["role"]) or True)
    data = client.get("/api/tts/status").json()
    assert data == {"installed": True, "model_ready": True, "engine": "pocket", "voice": speech.TTS_VOICE}
    assert seen == ["tts"]

    monkeypatch.setattr(line_models, "ready", lambda row: False)
    assert client.get("/api/tts/status").json()["model_ready"] is False


def test_post_streams_a_wav_of_the_engine_chunks(client) -> None:
    r = client.post("/api/tts", json={"text": "Hello world", "speed": 1.4})
    assert r.status_code == 200, r.text
    assert "audio/wav" in r.headers["content-type"]
    body = r.content
    assert body[:4] == b"RIFF" and body[8:12] == b"WAVE" and body[12:16] == b"fmt "
    channels, rate = struct.unpack("<HI", body[22:28])
    assert (channels, rate) == (1, RATE)
    pcm = np.frombuffer(body[44:], dtype="<i2")
    assert len(pcm) == 480 and pcm[0] == 1000 and pcm[-1] == -1000
    # One engine per process: a second request reuses it.
    assert client.post("/api/tts", json={"text": "Again"}).status_code == 200
    assert FakePocket.made == [speech.TTS_VOICE]


def test_post_without_the_line_extra_is_404(client, monkeypatch) -> None:
    monkeypatch.setattr(tts_routes, "_line_installed", lambda: False)
    r = client.post("/api/tts", json={"text": "Hello"})
    assert r.status_code == 404 and r.json()["code"] == "tts_not_installed"
    status = client.get("/api/tts/status").json()
    assert status["installed"] is False and status["model_ready"] is False
    assert client.post("/api/tts/download").json()["code"] == "tts_not_installed"


def test_the_import_probe_fails_when_pocket_tts_cannot_import(monkeypatch) -> None:
    import builtins

    real = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "pocket_tts":
            raise ImportError("hidden by test")
        return real(name, *args, **kwargs)

    tts_routes._reset_state()
    monkeypatch.setattr(builtins, "__import__", blocked)
    try:
        assert tts_routes._line_installed() is False
    finally:
        tts_routes._reset_state()


def test_post_before_the_weights_is_404(client, monkeypatch) -> None:
    monkeypatch.setattr(line_models, "ready", lambda row: False)
    r = client.post("/api/tts", json={"text": "Hello"})
    assert r.status_code == 404 and r.json()["code"] == "tts_model_not_ready"
    assert FakePocket.made == []


def test_bad_requests_are_400(client) -> None:
    assert client.post("/api/tts", json={}).json()["code"] == "tts_invalid_request"
    r = client.post("/api/tts", json={"text": "Hi", "voice": "nonexistent"})
    assert r.status_code == 400 and r.json()["code"] == "tts_invalid_voice"
    assert "nonexistent" in r.json()["message"]


def test_download_starts_the_line_fetch_once(client, monkeypatch) -> None:
    started: list[str] = []
    monkeypatch.setattr(line_models, "start", lambda preset_id, **_: started.append(preset_id) or {})
    monkeypatch.setattr(line_models, "wait", lambda preset_id, seconds=10.0: None)
    monkeypatch.setattr(line_models, "model_row", lambda row: {"state": "ready"})
    r = client.post("/api/tts/download")
    assert r.status_code == 202, r.text
    data = r.json()
    tts_row = next(row for row in line_models.presets() if row["role"] == "tts")
    assert started == [tts_row["id"]]
    assert data["receipt"]["downloaded"] is True
    assert data["receipt"]["total_bytes"] == tts_row["source"]["download_bytes"]
    assert data["egress"]["host"] == "huggingface.co"
