"""Import an existing recording — or transcript — as a real meeting.

The engine behind ``holdspeak import`` and ``POST /api/meetings/import``:
file in, meeting out. A recording (WAV natively via the stdlib ``wave``
module; common compressed formats by shelling out to ``ffmpeg`` when it is
on PATH) is transcribed in fixed windows through the normal ``Transcriber``
so segments carry real start/end times. A transcript (``.vtt``/``.srt``/
``.txt``, HS-57) skips transcription entirely: the parser produces honest
cues (real timestamps and speaker names when the file carries them). Both
paths share one persistence tail: a normal ``MeetingState`` via
``db.meetings.save_meeting``. The tail stops there (HS-201-10): an import
transcribes and asks for no summary, so the meeting arrives with its "Run
summary" verb and the disclosed route beside it, like a recorded one.

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
from typing import Any, Callable, Optional, Sequence

import numpy as np

from .errors import HoldSpeakError
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
# HS-201-10 — the terminal transcription state. A live meeting is `active`
# while audio still arrives and `record_only` when the route refused it; an
# import's transcript is finished the moment it is saved, so it says so.
TRANSCRIPTION_COMPLETE = "complete"

ProgressCallback = Callable[[int, int], None]


class MeetingImportError(HoldSpeakError):
    """A user-actionable import failure (bad file, missing ffmpeg, no speech).

    PHILO-6-01 round 3 (UX-CANON A.3): ``cause`` is the SHORT class the face
    shows (``LAST ERROR · <cause>``): no path, no file name, no sentence. The
    message stays the actionable detail for logs and the CLI.
    """

    code: str = "MEETING_IMPORT_ERROR"

    def __init__(
        self, *args: object, code: str | None = None, cause: str = "IMPORT ERROR"
    ) -> None:
        super().__init__(*args, code=code)
        self.cause = cause


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


def _import_moment() -> datetime:
    """When an import with no stated start happened: now.

    HS-201-10 (rehearsal defect 10). The old default was the FILE's mtime,
    which is not a fact about the meeting at all — a WAV copied onto the
    disk in June dated the meeting JUN 03 and filed it three months back in
    the ledger, where the owner had no reason to look. A caller with a real
    start (sync, a fixture, a future "use the file's date" gesture) still
    passes ``started_at`` and keeps its say.
    """
    return datetime.now()


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
        raise MeetingImportError(
            f"ffmpeg could not decode {path.name}: {tail}", cause="AUDIO DID NOT DECODE"
        )
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
                "WAV files import without it.",
                cause="FFMPEG NOT INSTALLED"
            )
        return
    raise MeetingImportError(
        f"Unsupported audio format: {suffix or filename}. Supported: .wav natively; "
        + ", ".join(sorted(FFMPEG_SUFFIXES))
        + " with ffmpeg installed; transcripts: "
        + ", ".join(sorted(TRANSCRIPT_SUFFIXES))
        + ".",
        cause="UNSUPPORTED TYPE"
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
                "import compressed or non-PCM audio (e.g. `brew install ffmpeg`).",
                cause="UNSUPPORTED TYPE"
            ) from exc
    if suffix in FFMPEG_SUFFIXES:
        if not ffmpeg_available():
            raise MeetingImportError(
                f"Importing {suffix} audio requires ffmpeg on your PATH "
                "(e.g. `brew install ffmpeg` or your package manager). "
                "WAV files import without it.",
                cause="FFMPEG NOT INSTALLED"
            )
        return _decode_with_ffmpeg(path)
    raise MeetingImportError(
        f"Unsupported audio format: {suffix or path.name}. Supported: .wav natively; "
        + ", ".join(sorted(FFMPEG_SUFFIXES))
        + " with ffmpeg installed.",
        cause="UNSUPPORTED TYPE"
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
    principal: Any = None,
) -> ImportResult:
    """Import one recording as a meeting; returns the persisted state.

    ``transcriber`` is anything with a ``transcribe(np.ndarray) -> str``
    (the normal ``Transcriber``; injected for testability). ``config`` is the
    loaded :class:`~holdspeak.config.Config` — the intel-enqueue conditions
    mirror the live capture path exactly.
    """
    path = Path(path)
    if not path.is_file():
        raise MeetingImportError(f"No such audio file: {path}", cause="FILE NOT FOUND")

    audio, rate = load_audio(path)
    if rate != TARGET_SAMPLE_RATE:
        audio = _linear_resample_mono(audio, rate, TARGET_SAMPLE_RATE)
    duration = len(audio) / float(TARGET_SAMPLE_RATE)
    if duration < 0.5:
        raise MeetingImportError(
            f"{path.name} contains less than half a second of audio — nothing to import.",
            cause="AUDIO TOO SHORT"
        )

    if started_at is None:
        started_at = _import_moment()

    window_samples = max(1, int(window_seconds * TARGET_SAMPLE_RATE))
    windows_total = int(np.ceil(len(audio) / window_samples))
    speaker_label = (speaker or DEFAULT_SPEAKER_LABEL).strip() or DEFAULT_SPEAKER_LABEL

    segments: list[TranscriptSegment] = []
    windows_empty = 0
    # HS-131-09: importing a recording transcribes with the same local Whisper as
    # live capture, so it runs under its own finite admitted session — one child
    # per window, bounded by the windows this file actually has.
    from .speech_session import admit_speech_session, hold_gesture_principal

    session = admit_speech_session(
        kind="dictation.session",
        principal=principal or hold_gesture_principal(),
        insertion_aim="recording-import",
        config_snapshot=config,
        registry_snapshot=db,
        deadline_seconds=max(300.0, 60.0 * windows_total),
        child_budget=2 * windows_total + 4,
    )
    admission = session.transcription()
    try:
        segments, windows_empty = _transcribe_import_windows(
            transcriber, audio, admission,
            windows_total=windows_total, window_samples=window_samples,
            window_seconds=window_seconds, duration=duration,
            speaker_label=speaker_label, progress=progress,
        )
    except BaseException:
        session.cancel_and_close()
        raise
    else:
        session.close("succeeded")

    if not segments:
        raise MeetingImportError(
            f"No speech could be transcribed from {path.name} "
            f"({windows_total} window(s) checked). Nothing was imported.",
            cause="NO SPEECH FOUND"
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


def _transcribe_import_windows(
    transcriber: Any,
    audio: Any,
    admission: Any,
    *,
    windows_total: int,
    window_samples: int,
    window_seconds: float,
    duration: float,
    speaker_label: str,
    progress: Any = None,
) -> tuple[list[TranscriptSegment], int]:
    """One admitted transcription child per import window."""
    segments: list[TranscriptSegment] = []
    windows_empty = 0
    for index in range(windows_total):
        chunk = audio[index * window_samples : (index + 1) * window_samples]
        text = (transcriber.transcribe(chunk, admission=admission) or "").strip()
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
    return segments, windows_empty


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
    normal ``MeetingState``, saves it via the normal ``save_meeting``, and
    stops. **Import transcribes and stops** (HS-201-10): it asks for no
    summary, so no provider is contacted until the owner asks for one.
    """
    state = MeetingState(
        id=meeting_id or str(uuid.uuid4())[:8],
        started_at=started_at,
        ended_at=started_at + timedelta(seconds=duration),
        title=title,
        tags=[t for t in (tag.strip() for tag in tags) if t],
        segments=segments,
    )

    # HS-201-10 — Import does not run the summary by itself.
    #
    # This tail used to enqueue an intel job with only a transcript hash: no
    # route bundle, no selection hash (the ledgered "hashless legacy entry
    # point", lane-a-handoff.md). The 2026-09-20 rehearsal watched it contact
    # 192.168.1.43 before any gesture, with `run_receipt: null` and no "Run
    # summary" verb ever drawn — and Import is the only path a stranger
    # without a microphone can take, so the whole Phase-201 disclosure
    # contract (stories 03 and 04) was unreachable in practice.
    # Article III wants the host disclosed AT THE POINT OF DECISION, and the
    # decision belongs to the owner. So the imported meeting lands in the
    # same shape as a recorded one: a transcript, no summary, and the "Run
    # summary" verb with its disclosed route beside it.
    meeting_cfg = config.meeting
    state.intel_status = "disabled"
    if meeting_cfg.intel_enabled and meeting_cfg.intel_deferred_enabled:
        state.intel_status_detail = (
            "No summary yet. Import does not run the summary — "
            "ask for it on the meeting."
        )
    else:
        state.intel_status_detail = "Meeting intelligence disabled in config."
    # The transcript this import produced cannot change again, so its
    # transcription state is final (rehearsal defect 11: `active` forever).
    state.transcription_status = TRANSCRIPTION_COMPLETE
    state.transcription_status_detail = None

    db.meetings.save_meeting(state)

    log.info(
        f"Imported meeting {state.id} from {source_name}: "
        f"{len(segments)} segment(s), {duration:.1f}s, intel_enqueued=False"
    )
    return ImportResult(
        state=state,
        intel_job_enqueued=False,
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
        raise MeetingImportError(f"No such transcript file: {path}", cause="FILE NOT FOUND")
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise MeetingImportError(
            f"Could not read {path.name}: {exc}", cause="FILE NOT READABLE"
        ) from exc

    fallback = (speaker or DEFAULT_TRANSCRIPT_SPEAKER_LABEL).strip() or (
        DEFAULT_TRANSCRIPT_SPEAKER_LABEL
    )
    try:
        parsed = parse_transcript(text, path.name, fallback_speaker=fallback)
    except TranscriptParseError as exc:
        raise MeetingImportError(str(exc), cause=exc.cause) from exc

    segments = [
        TranscriptSegment(
            text=cue.text, speaker=cue.speaker, start_time=cue.start, end_time=cue.end
        )
        for cue in parsed.cues
    ]
    duration = max(cue.end for cue in parsed.cues)

    if started_at is None:
        started_at = _import_moment()

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
