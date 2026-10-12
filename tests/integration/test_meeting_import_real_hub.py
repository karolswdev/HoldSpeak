"""PHILO-15-03: a WAV import on the real hub always reaches a final status.

The route, the service worker and the production transcriber factory
(``meeting_import._default_transcriber_factory`` -> ``Transcriber``) run
unpatched; only the configuration is pinned. The J4/J5 atlas cases waited
300 s on ``transcription_status == complete`` because a failed import left
``active`` behind; these fences read the same field the cases read.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from holdspeak.config import Config
from holdspeak.db import get_database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

REPO = Path(__file__).resolve().parents[2]
WAV = REPO / "tests/fixtures/core_path_smoke_16k.wav"  # 3 s: "The quick brown fox ..."


@pytest.fixture
def client(monkeypatch):
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    get_database(temp_dir / "test.db")
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    yield TestClient(server.app), temp_dir
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


def _pin_model(monkeypatch, name: str) -> None:
    config = Config()
    config.model.name = name
    monkeypatch.setattr(Config, "load", classmethod(lambda cls, *a, **k: config))


def _final(client, meeting_id: str, bound_s: float) -> tuple[dict, float]:
    started = time.monotonic()
    last: dict = {}
    while time.monotonic() - started < bound_s:
        detail = client.get(f"/api/meetings/{meeting_id}")
        if detail.status_code == 200:
            last = detail.json()
            if last.get("transcription_status") != "active":
                return last, time.monotonic() - started
        time.sleep(0.25)
    raise AssertionError(f"transcription_status stayed active for {bound_s}s: {last}")


def _post(client) -> str:
    response = client.post(
        "/api/meetings/import",
        files={"file": ("fixture.wav", WAV.read_bytes(), "audio/wav")},
        data={"title": "Fixture import"},
    )
    assert response.status_code == 202, response.text
    return response.json()["meeting_id"]


def test_an_import_whose_model_cannot_load_reaches_failed(client, monkeypatch):
    """No model on disk (the isolated-HOME case): final `failed`, fast."""
    http, temp_dir = client
    empty_model = temp_dir / "no-model-here"
    empty_model.mkdir()
    _pin_model(monkeypatch, str(empty_model))
    meeting_id = _post(http)

    row, elapsed = _final(http, meeting_id, bound_s=120)

    assert row["transcription_status"] == "failed", row
    assert (row.get("intel_status") or {}).get("state") == "import_failed", row
    assert row["transcription_status_detail"]["reason_code"] == "import_failed"
    assert elapsed < 120


def _whisper_cached(repo: str) -> bool:
    hf_home = Path(os.environ.get("HF_HOME") or Path.home() / ".cache/huggingface")
    folder = hf_home / "hub" / ("models--" + repo.replace("/", "--"))
    return any(folder.glob("snapshots/*/*"))


@pytest.mark.slow
def test_a_real_whisper_import_reaches_complete(client, monkeypatch):
    """The real Whisper `base` model transcribes the fixture: final `complete`.

    Run with HF_HOME at a cache that holds mlx-community/whisper-base-mlx and
    HF_HUB_OFFLINE=1; without the model it skips (no download in a test).
    """
    if not _whisper_cached("mlx-community/whisper-base-mlx"):
        pytest.skip("whisper-base-mlx is not in the HF cache; set HF_HOME to a cache that has it")
    http, _temp_dir = client
    _pin_model(monkeypatch, "base")
    meeting_id = _post(http)

    row, _elapsed = _final(http, meeting_id, bound_s=240)

    assert row["transcription_status"] == "complete", row
    assert row["segments"], row
    assert "fox" in " ".join(s["text"] for s in row["segments"]).lower(), row["segments"]
    assert (row.get("intel_status") or {}).get("state") != "import_failed"


def test_hub_start_ends_an_interrupted_import_failed(client):
    """Astra r1 #2: a row a killed hub left `importing / active` ends `failed`
    when the hub starts again (no import worker survives a restart)."""
    from datetime import datetime

    from holdspeak.meeting_session import MeetingState

    _unused, _temp_dir = client
    row = MeetingState(id="interrupted-import", started_at=datetime.now(), title="Killed", segments=[])
    row.intel_status = "importing"
    row.intel_status_detail = "Transcribing — window 2 of 9."
    get_database().meetings.save_meeting(row)

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    with TestClient(server.app) as started:  # runs the hub's startup handlers
        detail = started.get("/api/meetings/interrupted-import").json()

    assert detail["transcription_status"] == "failed", detail
    assert (detail.get("intel_status") or {}).get("state") == "import_failed"
    assert detail["transcription_status_detail"]["cause"] == "INTERRUPTED BY A RESTART"
