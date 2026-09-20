"""HS-201-10 — Import transcribes and stops.

The rehearsal (audits/rehearsal-07-opus.md, defects 2, 9, 10, 11) found
Import running the summary by itself: `_persist_import` enqueued an intel
job carrying only a transcript hash — no route bundle, no selection hash —
so the LAN box was contacted before any gesture and `run_receipt` was null.
Import is the ONLY path a stranger without a microphone can take, so the
whole Phase-201 disclosure contract was unreachable in practice.

These are the fences for the settled rule:

  * an import with meeting intelligence ON enqueues NOTHING, and the queue
    has nothing to drain, so no provider is contacted without a gesture;
  * the saved meeting is the face's "Run summary" shape (a transcript and
    no summary), exactly like a recorded one;
  * the meeting is dated the import moment, not the file's mtime;
  * `transcription_status` reaches its final state once the transcript is
    final — it no longer sits at `active` forever.

The transcriber is a fake (no model load, no microphone); the audio and the
database are real. The fixture WAV is the same 2.79 s file the rehearsal
imported, so the length assertions are about a real duration.
"""

from __future__ import annotations

import os
import wave
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.db import get_database, reset_database
from holdspeak.meeting_import import import_meeting, import_transcript

# The final state a transcript reaches once it can no longer change. The
# product's own constant is asserted to equal it, so the word cannot drift
# apart in the two places.
TRANSCRIPTION_COMPLETE = "complete"

FIXTURE_WAV = Path(__file__).resolve().parents[1] / "fixtures" / "core_path_smoke_16k.wav"
VTT = """WEBVTT

00:00:01.000 --> 00:00:04.000
<v Priya>the rollout starts monday

00:00:04.500 --> 00:00:09.000
<v Sam>i will prepare the release notes
"""


class FakeTranscriber:
    """Scripted text per window; never loads a model."""

    def __init__(self, texts):
        self.texts = list(texts)

    def transcribe(self, audio, **kwargs):
        return self.texts.pop(0) if self.texts else ""


class ProviderProbe:
    """Stands where the summary provider stands. Any use is a contact."""

    def __init__(self):
        self.constructions = 0
        self.analyses = 0

    def factory(self, **_kwargs):
        self.constructions += 1
        return self

    def analyze(self, *_args, **_kwargs):  # pragma: no cover — the fence
        self.analyses += 1
        raise AssertionError("the summary provider was contacted with no gesture")


def _config(intel_enabled=True, deferred=True):
    return SimpleNamespace(
        meeting=SimpleNamespace(
            intel_enabled=intel_enabled, intel_deferred_enabled=deferred
        )
    )


@pytest.fixture()
def db(tmp_path):
    reset_database()
    database = get_database(tmp_path / "import.db")
    yield database
    reset_database()


def _aged(path: Path, source: Path, *, days: int) -> Path:
    """A copy of ``source`` whose mtime is ``days`` in the past."""
    path.write_bytes(source.read_bytes())
    old = (datetime.now() - timedelta(days=days)).timestamp()
    os.utime(path, (old, old))
    return path


def _drain_probe(monkeypatch, db, probe: ProviderProbe) -> bool:
    """Ask the real queue to run the next job. True when it ran one."""
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda *a, **k: db)
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", probe.factory)
    from holdspeak.intel_queue import process_next_intel_job

    return process_next_intel_job(retry_max_attempts=1)


def test_audio_import_with_intel_on_enqueues_nothing_and_contacts_nobody(
    tmp_path, db, monkeypatch
):
    """The fence: intelligence ON, a real transcript, and still no run."""
    wav = _aged(tmp_path / "standup.wav", FIXTURE_WAV, days=108)
    probe = ProviderProbe()

    result = import_meeting(
        wav,
        db=db,
        transcriber=FakeTranscriber(["the quick brown fox jumps over the lazy dog"]),
        config=_config(),
    )

    # Nothing queued: the queue is empty and has nothing to hand a provider.
    assert result.intel_job_enqueued is False
    assert db.intel.list_intel_jobs() == []
    assert _drain_probe(monkeypatch, db, probe) is False
    assert (probe.constructions, probe.analyses) == (0, 0)

    stored = db.meetings.get_meeting(result.state.id)
    assert stored is not None
    # …and the meeting is the face's "Run summary" shape: a transcript, and
    # a summary state the ledger draws as OFF (helpers.ts `needsIntelligence`).
    assert stored.segments, "the import saved no transcript"
    assert stored.intel is None
    assert stored.intel_status == "disabled"
    assert "summary" in (stored.intel_status_detail or "").lower()


def test_transcript_import_with_intel_on_enqueues_nothing(tmp_path, db, monkeypatch):
    path = tmp_path / "weekly sync.vtt"
    path.write_text(VTT)
    probe = ProviderProbe()

    result = import_transcript(path, db=db, config=_config())

    assert result.intel_job_enqueued is False
    assert db.intel.list_intel_jobs() == []
    assert _drain_probe(monkeypatch, db, probe) is False
    assert probe.constructions == 0
    assert db.meetings.get_meeting(result.state.id).intel_status == "disabled"


def test_an_imported_meeting_is_dated_the_import_moment(tmp_path, db):
    """Defect 10: a file copied to disk in June dated the meeting JUN 03."""
    before = datetime.now()
    wav = _aged(tmp_path / "old recording.wav", FIXTURE_WAV, days=108)
    mtime = datetime.fromtimestamp(wav.stat().st_mtime)

    state = import_meeting(
        wav, db=db, transcriber=FakeTranscriber(["hello"]), config=_config()
    ).state

    assert state.started_at >= before
    assert state.started_at <= datetime.now()
    assert abs((state.started_at - mtime).total_seconds()) > 60 * 60 * 24

    vtt = tmp_path / "old transcript.vtt"
    vtt.write_text(VTT)
    old = (datetime.now() - timedelta(days=108)).timestamp()
    os.utime(vtt, (old, old))
    parsed = import_transcript(vtt, db=db, config=_config()).state
    assert parsed.started_at >= before

    # An explicit start still wins: the caller (sync, a fixture, a future
    # "the file's date" gesture) keeps its say.
    chosen = datetime(2026, 1, 2, 3, 4, 5)
    explicit = import_meeting(
        wav,
        db=db,
        transcriber=FakeTranscriber(["hello"]),
        config=_config(),
        started_at=chosen,
    ).state
    assert explicit.started_at == chosen


def test_transcription_status_is_final_once_the_transcript_is_final(tmp_path, db):
    """Defect 11: `active` after the transcript was final and would never move."""
    wav = _aged(tmp_path / "final.wav", FIXTURE_WAV, days=1)
    state = import_meeting(
        wav, db=db, transcriber=FakeTranscriber(["hello"]), config=_config()
    ).state
    from holdspeak import meeting_import

    assert meeting_import.TRANSCRIPTION_COMPLETE == TRANSCRIPTION_COMPLETE
    assert state.transcription_status == TRANSCRIPTION_COMPLETE
    assert state.transcription_status != "active"
    assert state.transcription_status_detail is None

    stored = db.meetings.get_meeting(state.id)
    assert stored.transcription_status == TRANSCRIPTION_COMPLETE

    path = tmp_path / "final.vtt"
    path.write_text(VTT)
    parsed = import_transcript(path, db=db, config=_config()).state
    assert parsed.transcription_status == TRANSCRIPTION_COMPLETE


def test_intel_disabled_in_config_still_says_so(tmp_path, db):
    """The honest disabled case keeps its own words, not the not-run ones."""
    wav = _aged(tmp_path / "off.wav", FIXTURE_WAV, days=1)
    state = import_meeting(
        wav,
        db=db,
        transcriber=FakeTranscriber(["hello"]),
        config=_config(intel_enabled=False),
    ).state
    assert state.intel_status == "disabled"
    assert "config" in (state.intel_status_detail or "")


def test_the_fixture_wav_is_the_length_the_row_must_tell_the_truth_about(tmp_path, db):
    """Defect 9: `1 MIN` for a 2.79 s file. The wire must carry 2.79."""
    with wave.open(str(FIXTURE_WAV), "rb") as wav_file:
        seconds = wav_file.getnframes() / float(wav_file.getframerate())
    assert 2.0 < seconds < 3.0

    state = import_meeting(
        _aged(tmp_path / "short.wav", FIXTURE_WAV, days=1),
        db=db,
        transcriber=FakeTranscriber(["hello"]),
        config=_config(),
    ).state
    assert state.duration == pytest.approx(seconds, abs=0.05)
    stored = db.meetings.get_meeting(state.id)
    assert stored.duration == pytest.approx(seconds, abs=0.05)
