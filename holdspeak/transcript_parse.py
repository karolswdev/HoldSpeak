"""HS-57-01: transcript parsers — VTT / SRT / TXT into honest cues.

Pure module (no I/O, no db, no config): text in, :class:`ParsedTranscript`
out. The honesty contract lives in two flags downstream surfaces rely on:

- ``has_real_timestamps`` — True only when the file itself carried cue
  timings (VTT/SRT). Plain text gets evenly-spaced synthetic times so the
  meeting orders and renders, but nothing downstream may present them as
  real moments.
- ``speakers_found`` — only labels the FILE carried (VTT ``<v Name>`` voice
  tags; conservative ``Name:`` line prefixes in SRT/TXT). Never invented.

Wild-caught transcripts are messy: BOMs, CRLF, hour-less VTT timings, voice
tags without closing tags, cue-identifier lines, NOTE/STYLE/REGION blocks,
inline styling tags. The parsers tolerate all of that; what they refuse —
with an actionable :class:`TranscriptParseError` — is input that yields no
cues at all (binary garbage, an empty file, a header-only VTT). An import
must never silently produce an empty meeting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "ParsedTranscript",
    "TranscriptCue",
    "TranscriptParseError",
    "TRANSCRIPT_SUFFIXES",
    "parse_transcript",
]

#: The transcript formats import understands (the v1 trio).
TRANSCRIPT_SUFFIXES = frozenset({".vtt", ".srt", ".txt"})

#: Synthetic spacing for timestamp-less plain text: enough to order and to
#: give the meeting a plausible duration, never presented as a real moment.
SYNTHETIC_CUE_SECONDS = 6.0


class TranscriptParseError(Exception):
    """Raised when a file yields no usable cues; the message is actionable."""


@dataclass(frozen=True)
class TranscriptCue:
    text: str
    speaker: str
    start: float
    end: float


@dataclass(frozen=True)
class ParsedTranscript:
    cues: list[TranscriptCue]
    has_real_timestamps: bool
    speakers_found: list[str] = field(default_factory=list)


# ── shared helpers ───────────────────────────────────────────────────────────

# HH:MM:SS.mmm with optional hours; VTT uses '.', SRT uses ',' — accept both.
_TIME_RE = re.compile(r"(?:(\d{1,3}):)?(\d{1,2}):(\d{2})[.,](\d{1,3})")
_ARROW_RE = re.compile(
    r"((?:\d{1,3}:)?\d{1,2}:\d{2}[.,]\d{1,3})\s*-->\s*((?:\d{1,3}:)?\d{1,2}:\d{2}[.,]\d{1,3})"
)
_TAG_RE = re.compile(r"<[^>]*>")
_VOICE_RE = re.compile(r"<v(?:\.[^ >]*)?\s+([^>]+)>")

# A conservative "Name:" prefix: starts with a letter, letters/spaces/.'-
# only (no digits, so clock times never match), at most 3 words (real names
# rarely exceed that; sentence fragments usually do), and a real space after
# the colon (so URLs like https://… never match).
_NAME_RE = re.compile(r"^([A-Za-z][A-Za-z.'\- ]{0,39}?)\s*:\s+(\S.*)$")
#: Common labels that look name-shaped but are document structure, not people.
_NAME_BLOCKLIST = frozenset(
    {
        "note", "notes", "nb", "ps", "re", "action", "actions", "agenda",
        "summary", "topic", "subject", "date", "time", "location",
        "attendees", "warning", "important", "todo", "decision", "decisions",
    }
)


def _normalize(text: str) -> str:
    return text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")


def _parse_time(token: str) -> float:
    match = _TIME_RE.fullmatch(token.strip())
    if match is None:
        raise ValueError(f"unparseable timestamp: {token!r}")
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    millis = int(match.group(4).ljust(3, "0"))
    return hours * 3600 + minutes * 60 + seconds + millis / 1000.0


def _name_prefix(line: str) -> tuple[str, str] | None:
    """``Name: text`` → (name, text) under the conservative rule, else None."""
    match = _NAME_RE.match(line)
    if match is None:
        return None
    name = match.group(1).strip()
    if not name or len(name.split()) > 3:
        return None
    if name.lower() in _NAME_BLOCKLIST:
        return None
    return name, match.group(2).strip()


def _looks_like_text(content: str) -> bool:
    """A cheap binary-garbage gate: mostly printable, some letters."""
    if not content.strip():
        return False
    sample = content[:4000]
    printable = sum(1 for ch in sample if ch.isprintable() or ch in "\n\t")
    if printable / len(sample) < 0.85:
        return False
    return any(ch.isalpha() for ch in sample)


def _record_speaker(name: str, seen: list[str]) -> None:
    if name and name not in seen:
        seen.append(name)


# ── VTT ──────────────────────────────────────────────────────────────────────


def _parse_vtt(content: str, filename: str, fallback_speaker: str) -> ParsedTranscript:
    lines = content.split("\n")
    first = next((l for l in lines if l.strip()), "")
    if not first.strip().upper().startswith("WEBVTT"):
        raise TranscriptParseError(
            f"{filename} has a .vtt suffix but no WEBVTT header — not a WebVTT file."
        )

    cues: list[TranscriptCue] = []
    speakers: list[str] = []
    current_speaker = fallback_speaker

    # Split into blocks on blank lines; skip the header block and metadata.
    blocks: list[list[str]] = []
    block: list[str] = []
    for line in lines:
        if line.strip():
            block.append(line)
        elif block:
            blocks.append(block)
            block = []
    if block:
        blocks.append(block)

    for blk in blocks:
        head = blk[0].strip().upper()
        if head.startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            continue
        timing_index = next((i for i, l in enumerate(blk) if "-->" in l), None)
        if timing_index is None:
            continue  # identifier-only / stray block
        arrow = _ARROW_RE.search(blk[timing_index])
        if arrow is None:
            continue
        try:
            start = _parse_time(arrow.group(1))
            end = _parse_time(arrow.group(2))
        except ValueError:
            continue
        if end <= start:
            end = start + 0.01

        text_lines = blk[timing_index + 1 :]
        raw = " ".join(l.strip() for l in text_lines if l.strip())
        voice = _VOICE_RE.search(raw)
        if voice is not None:
            current_speaker = voice.group(1).strip() or current_speaker
            _record_speaker(current_speaker, speakers)
        text = _TAG_RE.sub("", raw).strip()
        if not text:
            continue
        cues.append(
            TranscriptCue(text=text, speaker=current_speaker, start=start, end=end)
        )

    if not cues:
        raise TranscriptParseError(
            f"No cues could be parsed from {filename}. The file has a WEBVTT "
            "header but no readable cue blocks — nothing was imported."
        )
    cues.sort(key=lambda c: c.start)
    return ParsedTranscript(cues=cues, has_real_timestamps=True, speakers_found=speakers)


# ── SRT ──────────────────────────────────────────────────────────────────────


def _parse_srt(content: str, filename: str, fallback_speaker: str) -> ParsedTranscript:
    cues: list[TranscriptCue] = []
    speakers: list[str] = []
    current_speaker = fallback_speaker

    blocks: list[list[str]] = []
    block: list[str] = []
    for line in content.split("\n"):
        if line.strip():
            block.append(line)
        elif block:
            blocks.append(block)
            block = []
    if block:
        blocks.append(block)

    for blk in blocks:
        timing_index = next((i for i, l in enumerate(blk) if "-->" in l), None)
        if timing_index is None:
            continue
        arrow = _ARROW_RE.search(blk[timing_index])
        if arrow is None:
            continue
        try:
            start = _parse_time(arrow.group(1))
            end = _parse_time(arrow.group(2))
        except ValueError:
            continue
        if end <= start:
            end = start + 0.01

        text = " ".join(l.strip() for l in blk[timing_index + 1 :] if l.strip())
        text = _TAG_RE.sub("", text).strip()
        if not text:
            continue
        named = _name_prefix(text)
        if named is not None:
            current_speaker, text = named
            _record_speaker(current_speaker, speakers)
        cues.append(
            TranscriptCue(text=text, speaker=current_speaker, start=start, end=end)
        )

    if not cues:
        raise TranscriptParseError(
            f"No cues could be parsed from {filename}. Expected SubRip blocks "
            "(an index, a `00:00:01,000 --> 00:00:04,000` timing line, text) — "
            "nothing was imported."
        )
    cues.sort(key=lambda c: c.start)
    return ParsedTranscript(cues=cues, has_real_timestamps=True, speakers_found=speakers)


# ── TXT ──────────────────────────────────────────────────────────────────────


def _parse_txt(content: str, filename: str, fallback_speaker: str) -> ParsedTranscript:
    cues: list[TranscriptCue] = []
    speakers: list[str] = []
    current_speaker = fallback_speaker

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        named = _name_prefix(line)
        if named is not None:
            current_speaker, text = named
            _record_speaker(current_speaker, speakers)
        else:
            # A continuation line keeps the current voice (chat-style logs
            # wrap long turns onto unlabeled lines).
            text = line
        start = len(cues) * SYNTHETIC_CUE_SECONDS
        cues.append(
            TranscriptCue(
                text=text,
                speaker=current_speaker,
                start=start,
                end=start + SYNTHETIC_CUE_SECONDS,
            )
        )

    if not cues:
        raise TranscriptParseError(
            f"{filename} contains no transcript lines — nothing was imported."
        )
    return ParsedTranscript(cues=cues, has_real_timestamps=False, speakers_found=speakers)


# ── entry point ──────────────────────────────────────────────────────────────


def parse_transcript(
    text: str, filename: str, *, fallback_speaker: str = "Transcript"
) -> ParsedTranscript:
    """Parse one transcript file's text into honest cues.

    Dispatches on the filename suffix (`.vtt` / `.srt` / `.txt`); content
    beginning with a WEBVTT header is parsed as VTT regardless of suffix
    (tools mislabel exports). Raises :class:`TranscriptParseError` when no
    cues can be parsed — an import must never produce an empty meeting.
    """
    content = _normalize(text or "")
    if not _looks_like_text(content):
        raise TranscriptParseError(
            f"{filename} does not look like a text transcript (empty or "
            "binary content) — nothing was imported."
        )
    suffix = Path(filename).suffix.lower()
    if suffix not in TRANSCRIPT_SUFFIXES:
        raise TranscriptParseError(
            f"Unsupported transcript format: {suffix or filename}. "
            "Supported: .vtt, .srt, .txt."
        )
    fallback = (fallback_speaker or "Transcript").strip() or "Transcript"

    first = next((l for l in content.split("\n") if l.strip()), "")
    if suffix == ".vtt" or first.strip().upper().startswith("WEBVTT"):
        return _parse_vtt(content, filename, fallback)
    if suffix == ".srt":
        return _parse_srt(content, filename, fallback)
    return _parse_txt(content, filename, fallback)
