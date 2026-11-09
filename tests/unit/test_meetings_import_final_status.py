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
    before = set(threading.enumerate())
    result = service.import_meeting(
        OWNER, tmp_path=_wav(tmp_path), filename="held.wav", title=None,
        speaker=None, tags=[], started_at=datetime.now(), config=Config(),
        transcriber_factory=lambda _cfg: _Held(),
    )
    workers = [w for w in set(threading.enumerate()) - before
               if w.name == f"meeting-import-{result['meeting_id']}"]
    try:
        row = db.meetings.get_meeting(result["meeting_id"])
        assert row.intel_status == "importing"
        assert row.transcription_status == "active"
    finally:
        # Join before teardown removes the DB, even when an assert fails.
        gate.set()
        for worker in workers:
            worker.join(timeout=30)
    assert db.meetings.get_meeting(result["meeting_id"]).transcription_status == "complete"


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


def _placeholder(db: Database, meeting_id: str = "stuck-import") -> str:
    from holdspeak.meeting_session import MeetingState

    row = MeetingState(id=meeting_id, started_at=datetime.now(), title="Stuck", segments=[])
    row.intel_status = "importing"
    row.intel_status_detail = "Transcribing — window 1 of 4."
    db.meetings.save_meeting(row)
    return meeting_id


def test_hub_start_recovery_ends_an_interrupted_import_failed(tmp_path):
    db = Database(tmp_path / "import.db")
    meeting_id = _placeholder(db)
    assert db.meetings.get_meeting(meeting_id).transcription_status == "active"

    assert MeetingService(db).recover_interrupted_imports() == 1

    row = db.meetings.get_meeting(meeting_id)
    assert row.intel_status == "import_failed"
    assert row.transcription_status == "failed"
    assert row.transcription_status_detail == {
        "reason_code": "import_failed", "cause": "INTERRUPTED BY A RESTART",
    }
    assert MeetingService(db).recover_interrupted_imports() == 0


def test_recovery_leaves_finished_and_live_meetings_alone(tmp_path):
    from holdspeak.meeting_session import MeetingState

    db = Database(tmp_path / "import.db")
    live = MeetingState(id="live-recording", started_at=datetime.now(), segments=[])
    db.meetings.save_meeting(live)  # disabled / active: a live recording
    _db, done = _import(tmp_path, lambda _cfg: _Words())
    assert MeetingService(_db).recover_interrupted_imports() == 0
    assert MeetingService(db).recover_interrupted_imports() == 0
    assert db.meetings.get_meeting("live-recording").transcription_status == "active"
    assert _db.meetings.get_meeting(done).transcription_status == "complete"


def test_a_cancelled_worker_writes_failed_and_reraises(tmp_path):
    db = Database(tmp_path / "import.db")
    meeting_id = _placeholder(db)

    class _Cancelled:
        def transcribe(self, audio, **_admission):
            raise KeyboardInterrupt  # a BaseException, like CancelledError

    with pytest.raises(KeyboardInterrupt):
        MeetingService(db)._run_import_job(
            principal=OWNER, config=Config(), meeting_id=meeting_id,
            tmp_path=_wav(tmp_path), title="Stuck", speaker=None, tags=[],
            started_at=datetime.now(), transcriber_factory=lambda _cfg: _Cancelled(),
        )
    row = db.meetings.get_meeting(meeting_id)
    assert row.transcription_status == "failed"
    assert row.intel_status_detail == "CANCELLED"


def test_a_thread_that_cannot_start_writes_failed(tmp_path, monkeypatch):
    db = Database(tmp_path / "import.db")

    def refuse(self):
        raise RuntimeError("can't start new thread")

    monkeypatch.setattr(threading.Thread, "start", refuse)
    with pytest.raises(RuntimeError):
        MeetingService(db).import_meeting(
            OWNER, tmp_path=_wav(tmp_path), filename="x.wav", title="Never started",
            speaker=None, tags=[], started_at=datetime.now(), config=Config(),
            transcriber_factory=lambda _cfg: _Words(),
        )
    rows = db.meetings.list_meetings()
    assert len(rows) == 1
    row = db.meetings.get_meeting(rows[0].id)
    assert row.transcription_status == "failed"
    assert row.intel_status_detail == "IMPORT DID NOT START"


def test_a_failure_write_that_fails_is_logged_and_stays_active(tmp_path, monkeypatch, caplog):
    """The one honest limit: the next hub start recovers this row."""
    db = Database(tmp_path / "import.db")
    meeting_id = _placeholder(db)
    service = MeetingService(db)
    real_save = db.meetings.save_meeting

    def broken(*_a, **_k):
        raise RuntimeError("disk full")

    monkeypatch.setattr(db.meetings, "save_meeting", broken)
    assert service._fail_import(meeting_id, "UNEXPECTED ERROR") is False
    assert "could not write its failed status" in caplog.text
    monkeypatch.setattr(db.meetings, "save_meeting", real_save)
    assert db.meetings.get_meeting(meeting_id).transcription_status == "active"
    assert service.recover_interrupted_imports() == 1
    assert db.meetings.get_meeting(meeting_id).transcription_status == "failed"
