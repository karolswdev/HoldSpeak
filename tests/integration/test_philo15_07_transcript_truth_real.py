"""PHILO-15-07 (B01) on real metal: the rehearsal fixture through real Whisper.

Rehearsal 1 part A imported ``tests/fixtures/philo3_architect_meeting.wav``
(35 s) on the real hub: the hard 30 s cut made Whisper `base` loop at the end
of window 1 ("finally" about 250 times; on this machine also "kekeke", "team
team", "avash avash") and Priya Shah's action item was lost.

Run with HF_HOME at a cache that holds mlx-community/whisper-base-mlx and
HF_HUB_OFFLINE=1; without the model it skips (no download in a test).
"""
from __future__ import annotations

import itertools
import os
import re
import shutil
import tempfile
import time
from collections import Counter
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from holdspeak.config import Config
from holdspeak.db import get_database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

REPO = Path(__file__).resolve().parents[2]
WAV = REPO / "tests/fixtures/philo3_architect_meeting.wav"


def _whisper_cached(repo: str) -> bool:
    hf_home = Path(os.environ.get("HF_HOME") or Path.home() / ".cache/huggingface")
    folder = hf_home / "hub" / ("models--" + repo.replace("/", "--"))
    return any(folder.glob("snapshots/*/*"))


@pytest.fixture
def client(monkeypatch):
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    get_database(temp_dir / "test.db")
    config = Config()
    config.model.name = "base"
    monkeypatch.setattr(Config, "load", classmethod(lambda cls, *a, **k: config))
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    yield TestClient(server.app)
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.slow
@pytest.mark.timeout(300)
def test_the_rehearsal_fixture_keeps_priyas_action_and_never_loops(client):
    if not _whisper_cached("mlx-community/whisper-base-mlx"):
        pytest.skip("whisper-base-mlx is not in the HF cache; set HF_HOME to a cache that has it")
    response = client.post(
        "/api/meetings/import",
        files={"file": (WAV.name, WAV.read_bytes(), "audio/wav")},
    )
    assert response.status_code == 202, response.text
    meeting_id = response.json()["meeting_id"]

    row: dict = {}
    started = time.monotonic()
    while time.monotonic() - started < 240:
        row = client.get(f"/api/meetings/{meeting_id}").json()
        if row.get("transcription_status") != "active":
            break
        time.sleep(0.25)
    assert row.get("transcription_status") == "complete", row

    text = " ".join(segment["text"] for segment in row["segments"])
    lowered = text.lower()
    # Priya Shah's action item: her name beside the action, once, and its
    # words ("will add the name(d) failure fence before ship") whole.
    assert lowered.count("before ship") == 1, text
    assert re.search(r"priya shah will add the name\w* failure", lowered), text
    # No token repeated ten times in a row anywhere in the transcript.
    words = re.findall(r"[\w']+", lowered)
    runs = [len(list(g)) for _k, g in itertools.groupby(words)]
    assert max(runs) < 10, text
    most = Counter(words).most_common(1)[0]
    assert most[1] < 10, most
    assert row["unclearSpans"] == 0, text
    # B30: the title is the file name humanised, never the raw stem.
    assert row["title"] == "Philo3 architect meeting"
