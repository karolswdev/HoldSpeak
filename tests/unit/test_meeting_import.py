"""HS-55-01: the meeting-import engine — file in, meeting out.

Covers decode (PCM WAV natively, the honest ffmpeg refusal, the ffmpeg
fallback), downmix + resample to the transcriber contract, windowed
transcription with real timestamps, persistence parity, and the
live-mirrored intel-enqueue conditions. The transcriber is injected (a fake
that records what it received); the database is the real SQLite layer on a
temp file.
"""
from __future__ import annotations

import json
import os
import wave
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from jsonschema import Draft202012Validator

from holdspeak.db import Database, get_database, reset_database
from holdspeak.meeting_import import (
    DEFAULT_SPEAKER_LABEL,
    TARGET_SAMPLE_RATE,
    MeetingImportError,
    import_meeting,
    import_transcript,
    load_audio,
)
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.sync_service import SyncService
from scripts import graph_walk


class FakeTranscriber:
    """Returns scripted texts and records every array it was handed."""

    def __init__(self, texts):
        self.texts = list(texts)
        self.received: list[np.ndarray] = []

    def transcribe(self, audio, **kwargs):
        # HS-131-09: each window carries the import session's admission.
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
    assert state.title == "Standup recording"  # PHILO-15-07: humanised
    assert state.tags == ["imported", "q3"]
    # HS-201-10: started_at is the import moment, never the file's mtime;
    # the duration matches the audio.
    assert state.started_at != datetime.fromtimestamp(wav.stat().st_mtime)
    assert state.duration == pytest.approx(75.0, abs=0.1)
    assert seen == [(1, 3), (2, 3), (3, 3)]

    # Persisted as a real meeting, and NO summary asked for: Import
    # transcribes and stops (tests/unit/test_hs201_import_no_auto_summary.py
    # holds the fence).
    stored = db.meetings.get_meeting(state.id)
    assert stored is not None
    assert not result.intel_job_enqueued and state.id not in _intel_job_ids(db)
    assert state.intel_status == "disabled"


def test_import_completion_publishes_resolved_start_and_transcript_together(tmp_path, db, monkeypatch):
    """Every committed completed import has its resolved start, even with a placeholder."""
    import sqlite3
    from contextlib import contextmanager

    import holdspeak.meeting_import as importer
    from holdspeak.timestamps import parse_stamp

    moment = datetime(2026, 10, 16, 12, 0)
    meeting_id = "import-placeholder"
    placeholder = MeetingState(id=meeting_id, started_at=moment, title="Planning", segments=[])
    placeholder.intel_status = "importing"
    db.meetings.save_meeting(placeholder)
    transcript = tmp_path / "planning.vtt"
    transcript.write_text("WEBVTT\n\n00:00:00.000 --> 01:00:00.000\nRelease plan\n", encoding="utf-8")
    monkeypatch.setattr(importer, "_import_moment", lambda: moment)
    connection = db._connection
    published = []

    @contextmanager
    def observe_commits():
        with connection() as conn:
            yield conn
        # A separate reader sees only committed state, exactly as the
        # upload poll or a Brief rebuild can while the worker is running.
        with sqlite3.connect(db.db_path) as reader:
            row = reader.execute("SELECT started_at, ended_at FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
            segments = reader.execute("SELECT COUNT(*) FROM segments WHERE meeting_id = ?", (meeting_id,)).fetchone()[0]
        if row[1] is not None and segments:
            published.append((parse_stamp(row[0]), parse_stamp(row[1])))

    monkeypatch.setattr(db.meetings, "_connection", observe_commits)
    monkeypatch.setattr(db, "_connection", observe_commits)
    result = import_transcript(transcript, db=db, config=_config(intel_enabled=False), meeting_id=meeting_id)

    assert published, "the completed import was not committed"
    assert all(end - start == timedelta(hours=1) for start, end in published), published
    assert result.state.started_at == moment - timedelta(hours=1)


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


# ── from test_hs201_import_no_auto_summary.py: HS-201-10 — Import transcribes and stops. ──
#
# The rehearsal (audits/rehearsal-07-opus.md, defects 2, 9, 10, 11) found
# Import running the summary by itself: `_persist_import` enqueued an intel
# job carrying only a transcript hash — no route bundle, no selection hash —
# so the LAN box was contacted before any gesture and `run_receipt` was null.
# Import is the ONLY path a stranger without a microphone can take, so the
# whole Phase-201 disclosure contract was unreachable in practice.
#
# These are the fences for the settled rule:
#
#   * an import with meeting intelligence ON enqueues NOTHING, and the queue
#     has nothing to drain, so no provider is contacted without a gesture;
#   * the saved meeting is the face's "Run summary" shape (a transcript and
#     no summary), exactly like a recorded one;
#   * the meeting is dated the import moment, not the file's mtime;
#   * `transcription_status` reaches its final state once the transcript is
#     final — it no longer sits at `active` forever.
#
# The transcriber is a fake (no model load, no microphone); the audio and the
# database are real. The fixture WAV is the same 2.79 s file the rehearsal
# imported, so the length assertions are about a real duration.


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


class FakeTranscriber_summary:
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
        transcriber=FakeTranscriber_summary(["the quick brown fox jumps over the lazy dog"]),
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
        wav, db=db, transcriber=FakeTranscriber_summary(["hello"]), config=_config()
    ).state

    # PHILO-17: the meeting ENDS at the import moment (never in the future).
    assert state.ended_at >= before
    assert state.ended_at <= datetime.now()
    assert abs((state.started_at - mtime).total_seconds()) > 60 * 60 * 24

    vtt = tmp_path / "old transcript.vtt"
    vtt.write_text(VTT)
    old = (datetime.now() - timedelta(days=108)).timestamp()
    os.utime(vtt, (old, old))
    parsed = import_transcript(vtt, db=db, config=_config()).state
    assert parsed.ended_at >= before

    # An explicit start still wins: the caller (sync, a fixture, a future
    # "the file's date" gesture) keeps its say.
    chosen = datetime(2026, 1, 2, 3, 4, 5)
    explicit = import_meeting(
        wav,
        db=db,
        transcriber=FakeTranscriber_summary(["hello"]),
        config=_config(),
        started_at=chosen,
    ).state
    assert explicit.started_at == chosen


def test_transcription_status_is_final_once_the_transcript_is_final(tmp_path, db):
    """Defect 11: `active` after the transcript was final and would never move."""
    wav = _aged(tmp_path / "final.wav", FIXTURE_WAV, days=1)
    state = import_meeting(
        wav, db=db, transcriber=FakeTranscriber_summary(["hello"]), config=_config()
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
        transcriber=FakeTranscriber_summary(["hello"]),
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
        transcriber=FakeTranscriber_summary(["hello"]),
        config=_config(),
    ).state
    assert state.duration == pytest.approx(seconds, abs=0.05)
    stored = db.meetings.get_meeting(state.id)
    assert stored.duration == pytest.approx(seconds, abs=0.05)


# ── from test_philo16_import_transcriber_guard.py: PHILO-16 R2 (Astra MUST on 3671b90aa): a replyless import_transcriber is refused first. ──
#
# A declared import_transcriber boundary without `reply` used to read as "no
# double": the hub booted with the REAL Transcriber, and a case ordered
# [fixture import, boundary] uploaded the WAV through it before the boundary
# step refused. The rig now refuses the case before the hub starts, and the
# schema requires `reply` on that boundary.


REPO = Path(__file__).resolve().parents[2]
SCHEMA = REPO / "docs/internal/philo/graph/atlas.schema.json"

IMPORT = {
    "kind": "fixture",
    "path": "tests/fixtures/philo3_architect_meeting.wav",
    "route": {"method": "POST", "path": "/api/meetings/import"},
    "field": "file",
    "capture_as": "meeting_id",
    "capture_path": "meeting_id",
    "adapter": "http-route",
    "expect_status": 202,
}
REPLYLESS = {
    "kind": "boundary",
    "substitute": "import_transcriber",
    "label": "a transcript double that names no transcript",
    "adapter": "labelled-substitution",
}


def _atlas(tmp_path: Path, boundary: dict) -> Path:
    case = {
        "id": "case.r2.import_before_boundary",
        "job": "j4",
        "edge_ids": [],
        "state_id": "state.r2",
        "applicability": "applicable",
        "preconditions": [],
        "setup": [IMPORT, boundary],
        "trigger": {"kind": "api", "method": "GET", "path": "/api/meetings", "body": None},
        "expected": {"predicate": {"kind": "protocol_field", "path": "/meetings/0/id",
                                   "value": "{meeting_id}"},
                     "observe_at": "protocol: GET /api/meetings"},
        "completion_bound_s": 5,
        "viewports": [],
    }
    path = tmp_path / "atlas.json"
    path.write_text(json.dumps({"schema_version": 1, "cases": [case], "states": []}))
    return path


@pytest.mark.parametrize("boundary", [REPLYLESS, {**REPLYLESS, "reply": ""}, {**REPLYLESS, "reply": "  "}])
def test_import_before_a_replyless_boundary_is_refused_before_any_upload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, boundary: dict,
) -> None:
    hubs: list[object] = []
    uploads: list[object] = []

    class _NoHub:
        def __init__(self, *args, **kwargs) -> None:
            hubs.append((args, kwargs))
            raise AssertionError("a hub was started for a refused case")

    monkeypatch.setattr(graph_walk, "Hub", _NoHub)
    monkeypatch.setattr(graph_walk, "_multipart_upload",
                        lambda *a, **k: uploads.append(a) or {"status": 202})

    record = graph_walk.run_case(
        _atlas(tmp_path, boundary), "case.r2.import_before_boundary",
        brain="muaddib", viewport=1440, out=tmp_path / "out",
        engine="none", build=False, headless=True,
    )

    assert record["verdict"] == "blocked"
    assert any("import_transcriber boundary declares no `reply`" in n for n in record["notes"]), record["notes"]
    assert hubs == [] and uploads == []


def test_schema_requires_a_reply_on_an_import_transcriber_boundary() -> None:
    schema = json.loads(SCHEMA.read_text())
    step_validator = Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/step"})
    assert list(step_validator.iter_errors(REPLYLESS))
    assert list(step_validator.iter_errors({**REPLYLESS, "reply": ""}))
    good = {**REPLYLESS, "reply": "tests/fixtures/philo16_import_transcript.json"}
    assert not list(step_validator.iter_errors(good))


# ── from test_sync_meeting_transcription_status_143.py: Story 143-08: transcription repair state is safe under meeting sync. ──


OWNER = Principal(PrincipalKind.OWNER, "sync-meeting-status-owner")
DETAIL = {
    "family": "speech-recognition-route-assignments",
    "reason_code": "no_assignment",
    "repair": "repair_meeting_route_assignment",
}


def test_record_only_transcription_state_round_trips_and_cannot_be_resurrected(
    tmp_path: Path,
) -> None:
    source = Database(tmp_path / "source.db")
    destination = Database(tmp_path / "destination.db")
    source.meetings.save_meeting(
        MeetingState(
            id="record-only-meeting",
            started_at=datetime(2026, 8, 22, 12, 0, 0),
            transcription_status="record_only",
            transcription_status_detail=DETAIL,
        )
    )

    payload = SyncService(source).pull(OWNER)
    SyncService(destination).push(OWNER, payload)
    restored = destination.meetings.get_meeting("record-only-meeting")
    assert restored is not None
    assert restored.transcription_status == "record_only"
    assert restored.transcription_status_detail == DETAIL

    hostile = deepcopy(payload)
    hostile["meetings"][0]["meta"]["last_modified"] = "2099-01-01T00:00:00Z"
    hostile["meetings"][0]["value"]["transcription_status"] = "active"
    hostile["meetings"][0]["value"]["transcription_status_detail"] = None
    SyncService(destination).push(OWNER, hostile)

    protected = destination.meetings.get_meeting("record-only-meeting")
    assert protected is not None
    assert protected.transcription_status == "record_only"
    assert protected.transcription_status_detail == DETAIL
