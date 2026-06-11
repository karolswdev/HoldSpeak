"""HS-55-02 — POST /api/meetings/import: upload → importing row → real meeting.

The route returns 202 fast with a meeting id, the row is immediately visible
in an honest ``importing`` state, the engine runs on a background thread
(other routes stay responsive), progress lands in ``intel_status_detail``,
success resolves to the live-mirrored intel posture, and failures mark the
row ``import_failed`` with the actionable detail. The transcriber factory is
monkeypatched — no Whisper model loads in tests.
"""
from __future__ import annotations

import shutil
import tempfile
import threading
import time
import wave
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

from holdspeak.db import get_database, reset_database
from holdspeak.meeting_import import TARGET_SAMPLE_RATE
from holdspeak.web.routes import meeting_import as import_route
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def temp_db_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def db(temp_db_dir):
    reset_database()
    return get_database(temp_db_dir / "test.db")


@pytest.fixture
def client(db):
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    return TestClient(server.app)


class InstantTranscriber:
    def transcribe(self, audio):
        return "imported text"


class SlowTranscriber:
    """Blocks until released — lets tests observe the importing state."""

    def __init__(self):
        self.release = threading.Event()

    def transcribe(self, audio):
        self.release.wait(timeout=10)
        return "slow text"


class ExplodingTranscriber:
    def transcribe(self, audio):
        raise RuntimeError("model fell over")


def _wav_bytes(seconds: float) -> bytes:
    t = np.linspace(0, seconds, int(seconds * TARGET_SAMPLE_RATE), endpoint=False)
    tone = (np.sin(2 * np.pi * 440 * t) * 0.3 * 32767).astype(np.int16)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TARGET_SAMPLE_RATE)
        w.writeframes(tone.tobytes())
    data = Path(tmp.name).read_bytes()
    Path(tmp.name).unlink()
    return data


def _intel_state(payload) -> str:
    # The detail endpoint nests intel_status as {"state", "detail", ...}.
    status = payload.get("intel_status") or {}
    return status.get("state") if isinstance(status, dict) else status


def _wait_for_status(client, meeting_id, statuses, timeout=10.0):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        detail = client.get(f"/api/meetings/{meeting_id}")
        if detail.status_code == 200:
            last = detail.json()
            if _intel_state(last) in statuses:
                return last
        time.sleep(0.05)
    raise AssertionError(
        f"meeting never reached {statuses}; last={last and _intel_state(last)}"
    )


def test_import_happy_path_progresses_to_a_real_meeting(client, db, monkeypatch):
    monkeypatch.setattr(import_route, "_transcriber_factory", lambda cfg: InstantTranscriber())

    response = client.post(
        "/api/meetings/import",
        files={"file": ("standup.wav", _wav_bytes(35.0), "audio/wav")},
        data={"title": "Imported standup", "speaker": "Team", "tags": "imported,q3"},
    )
    assert response.status_code == 202
    meeting_id = response.json()["meeting_id"]

    # The row is visible immediately (importing or already resolved).
    listing = client.get("/api/meetings").json()
    assert any(m["id"] == meeting_id for m in listing["meetings"])

    final = _wait_for_status(client, meeting_id, {"queued", "disabled"})
    assert [s["text"] for s in final["segments"]] == ["imported text", "imported text"]
    assert final["title"] == "Imported standup"
    assert all(s["speaker"] == "Team" for s in final["segments"])


def test_unsupported_format_and_missing_ffmpeg_refuse_up_front(client, db, monkeypatch):
    bad = client.post(
        "/api/meetings/import",
        files={"file": ("notes.txt", b"not audio", "text/plain")},
    )
    assert bad.status_code == 400
    assert "Unsupported audio format" in bad.json()["error"]

    monkeypatch.setattr("holdspeak.meeting_import.ffmpeg_available", lambda: False)
    refused = client.post(
        "/api/meetings/import",
        files={"file": ("call.mp3", b"\xff\xfb fake", "audio/mpeg")},
    )
    assert refused.status_code == 400
    assert "ffmpeg" in refused.json()["error"]
    # Neither refusal leaves a mystery row behind.
    listing = client.get("/api/meetings").json()
    assert all(m.get("intel_status") != "importing" for m in listing["meetings"])


def test_mid_transcription_failure_marks_the_row_honestly(client, db, monkeypatch):
    monkeypatch.setattr(import_route, "_transcriber_factory", lambda cfg: ExplodingTranscriber())

    response = client.post(
        "/api/meetings/import",
        files={"file": ("doomed.wav", _wav_bytes(3.0), "audio/wav")},
    )
    assert response.status_code == 202
    meeting_id = response.json()["meeting_id"]

    failed = _wait_for_status(client, meeting_id, {"import_failed"})
    assert "model fell over" in ((failed.get("intel_status") or {}).get("detail") or "")
    # The honest row can be removed via the existing delete path.
    deleted = client.delete(f"/api/meetings/{meeting_id}")
    assert deleted.status_code in (200, 204)


def test_server_stays_responsive_during_an_import(client, db, monkeypatch):
    slow = SlowTranscriber()
    monkeypatch.setattr(import_route, "_transcriber_factory", lambda cfg: slow)

    response = client.post(
        "/api/meetings/import",
        files={"file": ("long.wav", _wav_bytes(35.0), "audio/wav")},
    )
    assert response.status_code == 202
    meeting_id = response.json()["meeting_id"]

    # While the worker is blocked, the row reports importing and other
    # routes answer.
    row = _wait_for_status(client, meeting_id, {"importing"})
    assert _intel_state(row) == "importing"
    assert client.get("/api/meetings").status_code == 200

    slow.release.set()
    _wait_for_status(client, meeting_id, {"queued", "disabled"})
