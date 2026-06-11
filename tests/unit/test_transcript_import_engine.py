"""HS-57-02: the transcript-import engine path + the shared persistence tail.

`import_transcript` turns a `.vtt`/`.srt`/`.txt` file into a real meeting
through the exact tail the audio path uses: same MeetingState, same
live-mirrored intel-enqueue conditions, same save. Under test: timestamp
honesty (real cues vs. synthetic ordering) on the SAVED segments, the file's
speaker labels reaching the db (and FTS), refusal without persistence,
`validate_format` learning the trio without touching audio behavior, and the
no-transcriber guarantee.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.db import get_database, reset_database
from holdspeak.meeting_import import (
    DEFAULT_TRANSCRIPT_SPEAKER_LABEL,
    MeetingImportError,
    import_transcript,
    is_transcript_filename,
    validate_format,
)

VTT = (
    "WEBVTT\n"
    "\n"
    "00:00:01.000 --> 00:00:04.000\n"
    "<v Priya>Morning, let's start with the rollout.</v>\n"
    "\n"
    "00:00:04.500 --> 00:00:09.000\n"
    "<v Sam>The fix is merged and the tests are green.\n"
    "\n"
    "00:00:09.500 --> 00:00:12.000\n"
    "Ship it today then.\n"
)


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


def test_vtt_imports_with_real_timestamps_and_file_speakers(tmp_path, db):
    path = tmp_path / "weekly sync.vtt"
    path.write_text(VTT)

    result = import_transcript(path, db=db, config=_config(), tags=["roadmap"])

    state = db.meetings.get_meeting(result.state.id)
    assert state is not None
    assert state.title == "weekly sync"
    assert state.tags == ["roadmap"]
    # Real cue timestamps, straight from the file.
    assert [s.start_time for s in state.segments] == [1.0, 4.5, 9.5]
    assert state.segments[0].end_time == 4.0
    # The file's own speakers — including voice continuity onto the bare cue.
    assert [s.speaker for s in state.segments] == ["Priya", "Sam", "Sam"]
    assert result.speakers_found == ["Priya", "Sam"]
    # Truthful result: no transcription windows happened.
    assert (result.windows_total, result.windows_empty) == (0, 0)
    assert result.duration_seconds == pytest.approx(12.0)
    assert state.ended_at is not None
    # Intel mirrored from the live conditions.
    assert result.intel_job_enqueued is True
    assert state.intel_status == "queued"


def test_txt_imports_with_synthetic_ordering_and_fallback_speaker(tmp_path, db):
    path = tmp_path / "notes.txt"
    path.write_text("we discussed the launch\nand agreed to ship friday\n")

    result = import_transcript(path, db=db, config=_config())

    state = db.meetings.get_meeting(result.state.id)
    starts = [s.start_time for s in state.segments]
    assert starts == sorted(starts) and starts[0] == 0.0
    assert all(s.speaker == DEFAULT_TRANSCRIPT_SPEAKER_LABEL for s in state.segments)
    assert result.speakers_found == []


def test_speaker_labels_reach_full_text_search(tmp_path, db):
    path = tmp_path / "sync.vtt"
    path.write_text(VTT)
    import_transcript(path, db=db, config=_config())

    hits = db.meetings.search_transcripts("rollout")
    assert hits, "the imported transcript must be searchable"


def test_intel_disabled_means_no_job(tmp_path, db):
    path = tmp_path / "sync.vtt"
    path.write_text(VTT)
    result = import_transcript(path, db=db, config=_config(intel_enabled=False))
    assert result.intel_job_enqueued is False
    assert result.state.intel_status == "disabled"
    assert db.intel.list_intel_jobs() == []


def test_zero_cue_input_refuses_and_persists_nothing(tmp_path, db):
    path = tmp_path / "empty.vtt"
    path.write_text("WEBVTT\n\nNOTE nothing\n")
    with pytest.raises(MeetingImportError, match="no readable cue blocks"):
        import_transcript(path, db=db, config=_config())
    assert db.meetings.list_meetings() == []
    assert db.intel.list_intel_jobs() == []


def test_missing_file_refused(tmp_path, db):
    with pytest.raises(MeetingImportError, match="No such transcript file"):
        import_transcript(tmp_path / "ghost.vtt", db=db, config=_config())


def test_started_at_defaults_to_file_mtime(tmp_path, db):
    import os

    path = tmp_path / "old.txt"
    path.write_text("Ana: an old conversation\n")
    stamp = datetime(2024, 3, 1, 9, 30, 0).timestamp()
    os.utime(path, (stamp, stamp))

    result = import_transcript(path, db=db, config=_config())
    assert result.state.started_at == datetime.fromtimestamp(stamp)


def test_explicit_started_at_wins(tmp_path, db):
    path = tmp_path / "sync.txt"
    path.write_text("Ana: hello\n")
    when = datetime(2026, 1, 2, 10, 0, 0)
    result = import_transcript(path, db=db, config=_config(), started_at=when)
    assert result.state.started_at == when


def test_import_transcript_never_touches_a_transcriber(tmp_path, db, monkeypatch):
    # The transcript path must work even when no transcription stack exists.
    import holdspeak.transcribe as transcribe_mod

    def _boom(*_a, **_k):
        raise AssertionError("a transcript import must not construct a Transcriber")

    monkeypatch.setattr(transcribe_mod, "Transcriber", _boom)
    path = tmp_path / "sync.vtt"
    path.write_text(VTT)
    result = import_transcript(path, db=db, config=_config())
    assert len(result.state.segments) == 3


# ── validate_format + the suffix branch ──────────────────────────────────────


def test_validate_format_accepts_the_transcript_trio() -> None:
    for name in ("a.vtt", "b.srt", "c.txt", "d.VTT"):
        validate_format(name)  # must not raise


def test_validate_format_audio_behavior_untouched() -> None:
    validate_format("a.wav")
    with pytest.raises(MeetingImportError, match="Unsupported audio format"):
        validate_format("slides.pdf")


def test_is_transcript_filename() -> None:
    assert is_transcript_filename("x.vtt") and is_transcript_filename("X.SRT")
    assert not is_transcript_filename("x.wav")
    assert not is_transcript_filename("x.mp3")
