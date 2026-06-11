"""Import an existing recording — or transcript — as a real meeting.

The engine behind ``holdspeak import`` and ``POST /api/meetings/import``:
file in, meeting out. A recording (WAV natively via the stdlib ``wave``
module; common compressed formats by shelling out to ``ffmpeg`` when it is
on PATH) is transcribed in fixed windows through the normal ``Transcriber``
so segments carry real start/end times. A transcript (``.vtt``/``.srt``/
``.txt``, HS-57) skips transcription entirely: the parser produces honest
cues (real timestamps and speaker names when the file carries them). Both
paths share one persistence tail: a normal ``MeetingState`` via
``db.meetings.save_meeting`` and deferred meeting intelligence enqueued
under the same conditions as a live capture.

Honest limits, by design:

* one user-provided speaker label for the whole recording (there is no
  single-file diarization dependency; live meetings get labels from their
  separate mic/system streams, not from magic);
* the source audio is read, transcribed, and **not retained** — the
  transcript is the artifact, exactly like a live meeting;
* compressed formats require ``ffmpeg``; without it the import is refused
  with an actionable message rather than half-decoded.

An imported meeting is a real meeting: everything downstream (history,
search, exports, intel, aftercare) treats it identically.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import uuid
import wave
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional, Sequence

import numpy as np

from .audio import _linear_resample_mono
from .meeting_session import MeetingState, TranscriptSegment
from .transcript_parse import (
    TRANSCRIPT_SUFFIXES,
    TranscriptParseError,
    parse_transcript,
)

log = logging.getLogger("holdspeak.meeting_import")

# The transcriber contract: mono float32 at 16 kHz.
TARGET_SAMPLE_RATE = 16000
# Window-level timing is the honest timestamp story: one transcribe() call
# returns one text blob, so each ~30 s window becomes one segment stamped
# with the window's real start/end.
DEFAULT_WINDOW_SECONDS = 30.0
# Formats ffmpeg can decode for us. WAV is handled natively first.
FFMPEG_SUFFIXES = {".mp3", ".m4a", ".aac", ".ogg", ".oga", ".opus", ".flac", ".webm", ".mp4"}
DEFAULT_SPEAKER_LABEL = "Recording"
# The fallback voice for transcript imports whose file carries no labels.
DEFAULT_TRANSCRIPT_SPEAKER_LABEL = "Transcript"

ProgressCallback = Callable[[int, int], None]


class MeetingImportError(Exception):
    """A user-actionable import failure (bad file, missing ffmpeg, no speech)."""


@dataclass
class ImportResult:
    """What an import produced."""

    state: MeetingState
    intel_job_enqueued: bool
    windows_total: int
    windows_empty: int
    duration_seconds: float
    warnings: list[str] = field(default_factory=list)
    # HS-57-02: transcript imports only — the speaker labels the FILE carried
    # (never invented; empty for audio imports and unlabeled transcripts).
    speakers_found: list[str] = field(default_factory=list)


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _decode_wav(path: Path) -> tuple[np.ndarray, int]:
    """Decode a PCM WAV with the stdlib; raises ``wave.Error`` on non-PCM."""
    with wave.open(str(path), "rb") as wav:
        rate = wav.getframerate()
        channels = wav.getnchannels()
        sampwidth = wav.getsampwidth()
        frames = wav.readframes(wav.getnframes())
    if sampwidth == 2:
        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 4:
        audio = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
    elif sampwidth == 1:
        # 8-bit WAV is unsigned.
        audio = (np.frombuffer(frames, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    else:
        raise wave.Error(f"unsupported PCM sample width: {sampwidth}")
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    return audio, rate


def _decode_with_ffmpeg(path: Path) -> tuple[np.ndarray, int]:
    """Decode any ffmpeg-readable file straight to 16 kHz mono PCM."""
    cmd = [
        "ffmpeg",
        "-v", "error",
        "-i", str(path),
        "-f", "s16le",
        "-ac", "1",
        "-ar", str(TARGET_SAMPLE_RATE),
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, timeout=600)
    if proc.returncode != 0:
        detail = proc.stderr.decode(errors="replace").strip().splitlines()
        tail = detail[-1] if detail else "unknown ffmpeg error"
        raise MeetingImportError(f"ffmpeg could not decode {path.name}: {tail}")
    audio = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    return audio, TARGET_SAMPLE_RATE


def is_transcript_filename(filename: str) -> bool:
    """True when ``filename`` names a transcript import (HS-57)."""
    return Path(filename).suffix.lower() in TRANSCRIPT_SUFFIXES


def validate_format(filename: str) -> None:
    """Cheap suffix/ffmpeg validation so callers can refuse before decoding.

    Raises :class:`MeetingImportError` with the same actionable messages
    ``load_audio`` would produce for an unsupported format or missing ffmpeg.
    Transcript suffixes (HS-57) validate without any decoder dependency.
    """
    suffix = Path(filename).suffix.lower()
    if suffix == ".wav":
        return
    if suffix in TRANSCRIPT_SUFFIXES:
        return
    if suffix in FFMPEG_SUFFIXES:
        if not ffmpeg_available():
            raise MeetingImportError(
                f"Importing {suffix} audio requires ffmpeg on your PATH "
                "(e.g. `brew install ffmpeg` or your package manager). "
                "WAV files import without it."
            )
        return
    raise MeetingImportError(
        f"Unsupported audio format: {suffix or filename}. Supported: .wav natively; "
        + ", ".join(sorted(FFMPEG_SUFFIXES))
        + " with ffmpeg installed; transcripts: "
        + ", ".join(sorted(TRANSCRIPT_SUFFIXES))
        + "."
    )


def load_audio(path: Path) -> tuple[np.ndarray, int]:
    """Decode ``path`` to mono float32 + its sample rate.

    WAV decodes natively; anything else (or a non-PCM WAV) needs ffmpeg on
    PATH and is refused with an actionable message without it.
    """
    suffix = path.suffix.lower()
    if suffix == ".wav":
        try:
            return _decode_wav(path)
        except wave.Error as exc:
            if ffmpeg_available():
                log.info(f"Non-PCM WAV ({exc}); falling back to ffmpeg for {path.name}")
                return _decode_with_ffmpeg(path)
            raise MeetingImportError(
                f"{path.name} is not a plain PCM WAV ({exc}). Install ffmpeg to "
                "import compressed or non-PCM audio (e.g. `brew install ffmpeg`)."
            ) from exc
    if suffix in FFMPEG_SUFFIXES:
        if not ffmpeg_available():
            raise MeetingImportError(
                f"Importing {suffix} audio requires ffmpeg on your PATH "
                "(e.g. `brew install ffmpeg` or your package manager). "
                "WAV files import without it."
            )
        return _decode_with_ffmpeg(path)
    raise MeetingImportError(
        f"Unsupported audio format: {suffix or path.name}. Supported: .wav natively; "
        + ", ".join(sorted(FFMPEG_SUFFIXES))
        + " with ffmpeg installed."
    )


def import_meeting(
    path: Path | str,
    *,
    db,
    transcriber,
    config,
    title: Optional[str] = None,
    speaker: str = DEFAULT_SPEAKER_LABEL,
    tags: Sequence[str] = (),
    started_at: Optional[datetime] = None,
    window_seconds: float = DEFAULT_WINDOW_SECONDS,
    progress: Optional[ProgressCallback] = None,
    meeting_id: Optional[str] = None,
) -> ImportResult:
    """Import one recording as a meeting; returns the persisted state.

    ``transcriber`` is anything with a ``transcribe(np.ndarray) -> str``
    (the normal ``Transcriber``; injected for testability). ``config`` is the
    loaded :class:`~holdspeak.config.Config` — the intel-enqueue conditions
    mirror the live capture path exactly.
    """
    path = Path(path)
    if not path.is_file():
        raise MeetingImportError(f"No such audio file: {path}")

    audio, rate = load_audio(path)
    if rate != TARGET_SAMPLE_RATE:
        audio = _linear_resample_mono(audio, rate, TARGET_SAMPLE_RATE)
    duration = len(audio) / float(TARGET_SAMPLE_RATE)
    if duration < 0.5:
        raise MeetingImportError(
            f"{path.name} contains less than half a second of audio — nothing to import."
        )

    if started_at is None:
        # An old recording should sort where it happened, not where it was
        # imported — the file's mtime is the best honest default.
        started_at = datetime.fromtimestamp(path.stat().st_mtime)

    window_samples = max(1, int(window_seconds * TARGET_SAMPLE_RATE))
    windows_total = int(np.ceil(len(audio) / window_samples))
    speaker_label = (speaker or DEFAULT_SPEAKER_LABEL).strip() or DEFAULT_SPEAKER_LABEL

    segments: list[TranscriptSegment] = []
    windows_empty = 0
    for index in range(windows_total):
        chunk = audio[index * window_samples : (index + 1) * window_samples]
        text = (transcriber.transcribe(chunk) or "").strip()
        if text:
            segments.append(
                TranscriptSegment(
                    text=text,
                    speaker=speaker_label,
                    start_time=index * window_seconds,
                    end_time=min((index + 1) * window_seconds, duration),
                )
            )
        else:
            windows_empty += 1
        if progress is not None:
            progress(index + 1, windows_total)

    if not segments:
        raise MeetingImportError(
            f"No speech could be transcribed from {path.name} "
            f"({windows_total} window(s) checked). Nothing was imported."
        )

    return _persist_import(
        db=db,
        config=config,
        segments=segments,
        duration=duration,
        started_at=started_at,
        title=(title or path.stem).strip() or path.stem,
        tags=tags,
        meeting_id=meeting_id,
        source_name=path.name,
        windows_total=windows_total,
        windows_empty=windows_empty,
    )


def _persist_import(
    *,
    db,
    config,
    segments: list[TranscriptSegment],
    duration: float,
    started_at: datetime,
    title: str,
    tags: Sequence[str],
    meeting_id: Optional[str],
    source_name: str,
    windows_total: int = 0,
    windows_empty: int = 0,
    speakers_found: Optional[list[str]] = None,
) -> ImportResult:
    """The shared persistence tail: segments in, a real meeting out.

    One tail, every import path (audio HS-55, transcripts HS-57): builds the
    normal ``MeetingState``, mirrors the live capture's intel posture, saves
    via the normal ``save_meeting``, and enqueues deferred intel under the
    same conditions as a live capture.
    """
    state = MeetingState(
        id=meeting_id or str(uuid.uuid4())[:8],
        started_at=started_at,
        ended_at=started_at + timedelta(seconds=duration),
        title=title,
        tags=[t for t in (tag.strip() for tag in tags) if t],
        segments=segments,
    )

    # Mirror the live capture's intel posture (meeting_session.save()): defer
    # to the existing queue when intel is on, state the disablement when not.
    meeting_cfg = config.meeting
    if meeting_cfg.intel_enabled and meeting_cfg.intel_deferred_enabled:
        state.intel_status = "queued"
        state.intel_status_detail = "Queued for processing after import."
    else:
        state.intel_status = "disabled"
        state.intel_status_detail = "Meeting intelligence disabled in config."

    db.meetings.save_meeting(state)
    intel_job_enqueued = False
    if state.intel_status == "queued" and state.segments:
        db.intel.enqueue_intel_job(
            state.id,
            transcript_hash=state.transcript_hash(),
            reason=state.intel_status_detail,
        )
        intel_job_enqueued = True

    log.info(
        f"Imported meeting {state.id} from {source_name}: "
        f"{len(segments)} segment(s), {duration:.1f}s, intel_enqueued={intel_job_enqueued}"
    )
    return ImportResult(
        state=state,
        intel_job_enqueued=intel_job_enqueued,
        windows_total=windows_total,
        windows_empty=windows_empty,
        duration_seconds=duration,
        speakers_found=list(speakers_found or []),
    )


def import_transcript(
    path: Path | str,
    *,
    db,
    config,
    title: Optional[str] = None,
    speaker: str = DEFAULT_TRANSCRIPT_SPEAKER_LABEL,
    tags: Sequence[str] = (),
    started_at: Optional[datetime] = None,
    meeting_id: Optional[str] = None,
) -> ImportResult:
    """Import one transcript file (`.vtt`/`.srt`/`.txt`) as a real meeting.

    The cheaper sibling of :func:`import_meeting`: no transcriber, no ffmpeg
    — parse (HS-57-01), build honest segments, and run the same persistence
    tail. Segments carry the file's real cue timestamps (VTT/SRT) or the
    parser's synthetic ordering (TXT); speakers are the file's own labels,
    falling back to ``speaker`` for unlabeled content. The file is read and
    **not retained** — the meeting record is the artifact.
    """
    path = Path(path)
    if not path.is_file():
        raise MeetingImportError(f"No such transcript file: {path}")
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise MeetingImportError(f"Could not read {path.name}: {exc}") from exc

    fallback = (speaker or DEFAULT_TRANSCRIPT_SPEAKER_LABEL).strip() or (
        DEFAULT_TRANSCRIPT_SPEAKER_LABEL
    )
    try:
        parsed = parse_transcript(text, path.name, fallback_speaker=fallback)
    except TranscriptParseError as exc:
        raise MeetingImportError(str(exc)) from exc

    segments = [
        TranscriptSegment(
            text=cue.text, speaker=cue.speaker, start_time=cue.start, end_time=cue.end
        )
        for cue in parsed.cues
    ]
    duration = max(cue.end for cue in parsed.cues)

    if started_at is None:
        # An old transcript should sort where the meeting happened, not where
        # it was imported — the file's mtime is the best honest default.
        started_at = datetime.fromtimestamp(path.stat().st_mtime)

    return _persist_import(
        db=db,
        config=config,
        segments=segments,
        duration=duration,
        started_at=started_at,
        title=(title or path.stem).strip() or path.stem,
        tags=tags,
        meeting_id=meeting_id,
        source_name=path.name,
        speakers_found=parsed.speakers_found,
    )
