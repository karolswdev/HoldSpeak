"""PHILO-15-03: a WAV import always reaches a final status.

The placeholder row is born with ``transcription_status = "active"`` (the
model default). Only the success tail moved it to ``complete``; a failing
worker wrote ``intel_status = import_failed`` and left ``active`` behind, so
every reader that waits on the transcription (the J4/J5 atlas cases) waited
out its whole 300 s bound. These tests drive the real service worker.
"""
from __future__ import annotations

import tempfile
import threading
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.meeting_import import TARGET_SAMPLE_RATE, MeetingImportError
from holdspeak.services.meeting_service import MeetingService
from tests.unit.test_phase143_inference_assignments import OWNER


class _Words:
    def transcribe(self, audio, **_admission):
        return "imported words"


class _Explodes:
    def transcribe(self, audio, **_admission):
        raise RuntimeError("model fell over")


def _wav(tmp: Path, seconds: float = 2.0) -> Path:
    t = np.linspace(0, seconds, int(seconds * TARGET_SAMPLE_RATE), endpoint=False)
    tone = (np.sin(2 * np.pi * 440 * t) * 0.3 * 32767).astype(np.int16)
    path = Path(tempfile.mkstemp(suffix=".wav", dir=tmp)[1])
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TARGET_SAMPLE_RATE)
        w.writeframes(tone.tobytes())
    return path


def _import(tmp_path: Path, factory) -> tuple[Database, str]:
    db = Database(tmp_path / "import.db")
    service = MeetingService(db)
    before = set(threading.enumerate())
    result = service.import_meeting(
        OWNER,
        tmp_path=_wav(tmp_path),
        filename="standup.wav",
        title="Standup",
        speaker=None,
        tags=[],
        started_at=datetime.now(),
        config=Config(),
        transcriber_factory=factory,
    )
    meeting_id = result["meeting_id"]
    for worker in set(threading.enumerate()) - before:
        if worker.name == f"meeting-import-{meeting_id}":
            worker.join(timeout=30)
            assert not worker.is_alive(), "the import worker did not finish"
    return db, meeting_id


def test_the_placeholder_is_active_while_the_worker_runs(tmp_path):
    db = Database(tmp_path / "import.db")
    gate = threading.Event()

    class _Held:
        def transcribe(self, audio, **_admission):
            gate.wait(10)
            return "held"

    service = MeetingService(db)
    result = service.import_meeting(
        OWNER, tmp_path=_wav(tmp_path), filename="held.wav", title=None,
        speaker=None, tags=[], started_at=datetime.now(), config=Config(),
        transcriber_factory=lambda _cfg: _Held(),
    )
    row = db.meetings.get_meeting(result["meeting_id"])
    assert row.intel_status == "importing"
    assert row.transcription_status == "active"
    gate.set()


def test_a_succeeding_import_writes_complete(tmp_path):
    db, meeting_id = _import(tmp_path, lambda _cfg: _Words())
    row = db.meetings.get_meeting(meeting_id)
    assert row.transcription_status == "complete"
    assert row.transcription_status_detail is None
    assert row.intel_status != "import_failed"
    assert [s.text for s in row.segments] == ["imported words"]


def test_a_failing_transcription_writes_import_failed_and_failed(tmp_path):
    db, meeting_id = _import(tmp_path, lambda _cfg: _Explodes())
    row = db.meetings.get_meeting(meeting_id)
    assert row.intel_status == "import_failed"
    assert row.intel_status_detail == "UNEXPECTED ERROR"
    assert row.transcription_status == "failed"
    assert row.transcription_status_detail == {
        "reason_code": "import_failed", "cause": "UNEXPECTED ERROR",
    }


def test_a_transcriber_that_cannot_load_writes_failed(tmp_path):
    """The isolated-HOME case: the model cannot load before any window runs."""

    def no_model(_cfg):
        raise OSError("We couldn't connect to 'https://huggingface.co' (HF_HUB_OFFLINE)")

    db, meeting_id = _import(tmp_path, no_model)
    row = db.meetings.get_meeting(meeting_id)
    assert row.intel_status == "import_failed"
    assert row.transcription_status == "failed"


def test_a_named_import_error_keeps_its_short_cause(tmp_path):
    def refused(_cfg):
        raise MeetingImportError("Speech is not set up on this device.", cause="NO SPEECH ENGINE")

    db, meeting_id = _import(tmp_path, refused)
    row = db.meetings.get_meeting(meeting_id)
    assert row.intel_status_detail == "NO SPEECH ENGINE"
    assert row.transcription_status == "failed"
    assert row.transcription_status_detail["cause"] == "NO SPEECH ENGINE"


@pytest.mark.parametrize("factory", [lambda _cfg: _Words(), lambda _cfg: _Explodes()])
def test_the_status_never_stays_active_after_the_worker(tmp_path, factory):
    db, meeting_id = _import(tmp_path, factory)
    assert db.meetings.get_meeting(meeting_id).transcription_status in {"complete", "failed"}
