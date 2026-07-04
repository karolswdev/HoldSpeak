"""HS-55-01: the meeting-import engine — file in, meeting out.

Covers decode (PCM WAV natively, the honest ffmpeg refusal, the ffmpeg
fallback), downmix + resample to the transcriber contract, windowed
transcription with real timestamps, persistence parity, and the
live-mirrored intel-enqueue conditions. The transcriber is injected (a fake
that records what it received); the database is the real SQLite layer on a
temp file.
"""

from __future__ import annotations

import wave
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from holdspeak.db import get_database, reset_database
from holdspeak.meeting_import import (
    DEFAULT_SPEAKER_LABEL,
    MeetingImportError,
    TARGET_SAMPLE_RATE,
    import_meeting,
    load_audio,
)


class FakeTranscriber:
    """Returns scripted texts and records every array it was handed."""

    def __init__(self, texts):
        self.texts = list(texts)
        self.received: list[np.ndarray] = []

    def transcribe(self, audio):
        self.received.append(np.asarray(audio))
        return self.texts.pop(0) if self.texts else ""


def _config(intel_enabled=True, deferred=True):
    return SimpleNamespace(
        meeting=SimpleNamespace(
            intel_enabled=intel_enabled, intel_deferred_enabled=deferred
        )
    )


def _write_wav(path: Path, seconds: float, *, rate=TARGET_SAMPLE_RATE, channels=1):
    t = np.linspace(0, seconds, int(seconds * rate), endpoint=False)
    tone = (np.sin(2 * np.pi * 440 * t) * 0.3 * 32767).astype(np.int16)
    if channels == 2:
        tone = np.column_stack([tone, tone]).reshape(-1)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(tone.tobytes())
    return path


@pytest.fixture()
def db(tmp_path):
    reset_database()
    database = get_database(tmp_path / "import.db")
    yield database
    reset_database()


def _intel_job_ids(database):
    summary = database.intel.list_intel_jobs()
    return [job.meeting_id for job in summary]


def test_happy_path_windows_timestamps_and_persistence(tmp_path, db):
    wav = _write_wav(tmp_path / "standup recording.wav", seconds=75.0)
    transcriber = FakeTranscriber(["first window", "second window", "third window"])
    seen = []

    result = import_meeting(
        wav,
        db=db,
        transcriber=transcriber,
        config=_config(),
        tags=["imported", " q3 "],
        progress=lambda done, total: seen.append((done, total)),
    )

    state = result.state
    assert result.windows_total == 3 and result.windows_empty == 0
    assert [s.text for s in state.segments] == [
        "first window",
        "second window",
        "third window",
    ]
    # Window-level timestamps; the last window is clipped to the real duration.
    assert [(s.start_time, s.end_time) for s in state.segments] == [
        (0.0, 30.0),
        (30.0, 60.0),
        (60.0, 75.0),
    ]
    assert all(s.speaker == DEFAULT_SPEAKER_LABEL for s in state.segments)
    assert state.title == "standup recording"
    assert state.tags == ["imported", "q3"]
    # started_at honors the file's mtime; the duration matches the audio.
    assert state.started_at == datetime.fromtimestamp(wav.stat().st_mtime)
    assert state.duration == pytest.approx(75.0, abs=0.1)
    assert seen == [(1, 3), (2, 3), (3, 3)]

    # Persisted as a real meeting + the intel job enqueued (live conditions).
    stored = db.meetings.get_meeting(state.id)
    assert stored is not None
    assert result.intel_job_enqueued and state.id in _intel_job_ids(db)
    assert state.intel_status == "queued"


def test_stereo_44k_is_downmixed_and_resampled_before_transcription(tmp_path, db):
    wav = _write_wav(tmp_path / "hifi.wav", seconds=4.0, rate=44100, channels=2)
    transcriber = FakeTranscriber(["hello"])

    import_meeting(wav, db=db, transcriber=transcriber, config=_config())

    assert len(transcriber.received) == 1
    chunk = transcriber.received[0]
    assert chunk.ndim == 1  # mono
    assert len(chunk) == pytest.approx(4.0 * TARGET_SAMPLE_RATE, rel=0.01)
    assert chunk.dtype == np.float32


def test_empty_windows_are_skipped_and_all_empty_refuses(tmp_path, db):
    wav = _write_wav(tmp_path / "sparse.wav", seconds=65.0)
    transcriber = FakeTranscriber(["something", "   "])
    result = import_meeting(wav, db=db, transcriber=transcriber, config=_config())
    assert len(result.state.segments) == 1
    assert result.windows_empty == 2  # the blank window + the script-exhausted one

    silent = _write_wav(tmp_path / "silence.wav", seconds=5.0)
    with pytest.raises(MeetingImportError, match="No speech"):
        import_meeting(silent, db=db, transcriber=FakeTranscriber([]), config=_config())


def test_compressed_without_ffmpeg_is_refused_honestly(tmp_path, db, monkeypatch):
    monkeypatch.setattr("holdspeak.meeting_import.ffmpeg_available", lambda: False)
    mp3 = tmp_path / "call.mp3"
    mp3.write_bytes(b"\xff\xfb fake mp3 bytes")
    with pytest.raises(MeetingImportError, match="ffmpeg"):
        import_meeting(mp3, db=db, transcriber=FakeTranscriber(["x"]), config=_config())


def test_compressed_with_ffmpeg_decodes_via_ffmpeg(tmp_path, db, monkeypatch):
    monkeypatch.setattr("holdspeak.meeting_import.ffmpeg_available", lambda: True)
    fake_audio = np.zeros(TARGET_SAMPLE_RATE * 2, dtype=np.float32)
    monkeypatch.setattr(
        "holdspeak.meeting_import._decode_with_ffmpeg",
        lambda path: (fake_audio, TARGET_SAMPLE_RATE),
    )
    mp3 = tmp_path / "call.mp3"
    mp3.write_bytes(b"\xff\xfb fake mp3 bytes")
    result = import_meeting(
        mp3, db=db, transcriber=FakeTranscriber(["from ffmpeg"]), config=_config()
    )
    assert [s.text for s in result.state.segments] == ["from ffmpeg"]


def test_unsupported_format_is_refused(tmp_path):
    weird = tmp_path / "notes.txt"
    weird.write_text("not audio")
    with pytest.raises(MeetingImportError, match="Unsupported audio format"):
        load_audio(weird)


def test_intel_disabled_means_no_job_and_honest_status(tmp_path, db):
    wav = _write_wav(tmp_path / "no-intel.wav", seconds=3.0)
    result = import_meeting(
        wav,
        db=db,
        transcriber=FakeTranscriber(["text"]),
        config=_config(intel_enabled=False),
    )
    assert not result.intel_job_enqueued
    assert result.state.intel_status == "disabled"
    assert result.state.id not in _intel_job_ids(db)


def test_missing_file_and_speaker_label_override(tmp_path, db):
    with pytest.raises(MeetingImportError, match="No such audio file"):
        import_meeting(
            tmp_path / "ghost.wav",
            db=db,
            transcriber=FakeTranscriber([]),
            config=_config(),
        )

    wav = _write_wav(tmp_path / "labeled.wav", seconds=2.0)
    result = import_meeting(
        wav,
        db=db,
        transcriber=FakeTranscriber(["hi"]),
        config=_config(),
        speaker="Quarterly review",
        title="Q3 planning",
    )
    assert result.state.segments[0].speaker == "Quarterly review"
    assert result.state.title == "Q3 planning"


def test_import_command_exits_nonzero_on_unsupported_format(tmp_path, capsys):
    # F-04 lock: the recorded dogfood run claimed `hs import <bad>` exited 0;
    # the survey could not reproduce it (exits 1). This pins the honest exit
    # code so a regression is caught where the finding was filed.
    from types import SimpleNamespace

    from holdspeak.commands.import_recording import run_import_command

    bad = tmp_path / "PROTOCOL.md"
    bad.write_text("# not importable")
    args = SimpleNamespace(file=str(bad), title=None, speaker=None, tag=[])

    rc = run_import_command(args)

    assert rc == 1
    assert "Unsupported audio format" in capsys.readouterr().err
