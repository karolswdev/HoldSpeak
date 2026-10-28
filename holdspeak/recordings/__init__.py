"""Recordings (2026-10-28): record a desk session, watch it on the iPhone.

The browser captures (``getDisplayMedia`` + ``MediaRecorder``) and posts 5 s
chunks; the hub appends them, encodes one H.264 mp4 with ffmpeg off the loop,
and serves it behind a per-recording share token. Design:
``docs/internal/betterment/recordings/RECORDINGS-DESIGN-2026-10-28.md``.
"""
from .service import RECORDINGS, RecordingsService, recordings_on
from .store import KEEP_DAYS, STALE_SECONDS, Recording, RecordingStore, RecordingRefused

__all__ = [
    "KEEP_DAYS",
    "RECORDINGS",
    "STALE_SECONDS",
    "Recording",
    "RecordingRefused",
    "RecordingStore",
    "RecordingsService",
    "recordings_on",
]
