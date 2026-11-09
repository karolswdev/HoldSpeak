"""Parked 2026-11-08 (the slow tier): the slow-marked cases of tests/integration/test_meeting_import_real_hub.py, moved as text. Not collected."""


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
