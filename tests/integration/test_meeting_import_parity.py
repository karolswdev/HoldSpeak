"""HS-55-01 — an imported meeting is a real meeting, downstream.

The engine's persistence parity: a meeting created by ``import_meeting``
lists via ``GET /api/meetings``, is found by full-text transcript search,
and exports — exactly like a live-captured one. No import-specific rendering
or storage anywhere downstream.
"""
from __future__ import annotations

import shutil
import tempfile
import wave
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

from holdspeak.db import get_database, reset_database
from holdspeak.meeting_import import TARGET_SAMPLE_RATE, import_meeting
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


class FakeTranscriber:
    def __init__(self, texts):
        self.texts = list(texts)

    def transcribe(self, audio):
        return self.texts.pop(0) if self.texts else ""


def _write_wav(path: Path, seconds: float):
    t = np.linspace(0, seconds, int(seconds * TARGET_SAMPLE_RATE), endpoint=False)
    tone = (np.sin(2 * np.pi * 440 * t) * 0.3 * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(TARGET_SAMPLE_RATE)
        wav.writeframes(tone.tobytes())
    return path


def _config():
    return SimpleNamespace(
        meeting=SimpleNamespace(intel_enabled=True, intel_deferred_enabled=True)
    )


def test_imported_meeting_is_indistinguishable_downstream(tmp_path, db, client):
    wav = _write_wav(tmp_path / "kickoff.wav", seconds=35.0)
    result = import_meeting(
        wav,
        db=db,
        transcriber=FakeTranscriber(
            ["we agreed to ship the import flow", "and the zanzibar follow-up"]
        ),
        config=_config(),
        title="Imported kickoff",
        tags=["imported"],
    )
    meeting_id = result.state.id

    # Lists like any meeting, with its segments counted.
    listing = client.get("/api/meetings").json()
    row = next(m for m in listing["meetings"] if m["id"] == meeting_id)
    assert row["title"] == "Imported kickoff"
    assert row["segment_count"] == 2
    assert row["intel_status"] == "queued"

    # Full-text transcript search finds its text.
    found = client.get("/api/meetings", params={"search": "zanzibar"}).json()
    assert any(m["id"] == meeting_id for m in found["meetings"])

    # Detail + export behave like a live meeting.
    detail = client.get(f"/api/meetings/{meeting_id}").json()
    texts = [s["text"] for s in detail["segments"]]
    assert "we agreed to ship the import flow" in texts
    export = client.get(f"/api/meetings/{meeting_id}/export", params={"format": "markdown"})
    assert export.status_code == 200
    assert "import flow" in export.text
