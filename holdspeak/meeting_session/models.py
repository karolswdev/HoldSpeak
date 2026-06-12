"""The meeting data models (HS-63-01).

The pure data layer of a meeting — bookmarks, transcript segments, intel
snapshots, save results, and the meeting state itself — carved verbatim out
of `meeting_session.py` so the session machinery and the data it carries
stop sharing one file. `holdspeak.meeting_session` re-exports every name
here; it stays the canonical import point.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Bookmark:
    """A marked moment in the meeting."""
    timestamp: float  # Seconds since meeting start
    label: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "label": self.label,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class TranscriptSegment:
    """A transcribed segment with speaker label."""
    text: str
    speaker: str  # Display name: "Me", "Speaker 1", "John", etc.
    start_time: float  # Seconds since meeting start
    end_time: float
    is_bookmarked: bool = False
    speaker_id: Optional[str] = None  # Link to speaker identity (None for "Me")
    # Phase 14: id of the AIPI-Lite-class device that produced this
    # segment, or ``None`` for the legacy local-mic + system-audio
    # paths. ``speaker`` resolves to the device's registered label
    # at meeting-attach time.
    device_id: Optional[str] = None

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "speaker": self.speaker,
            "speaker_id": self.speaker_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "is_bookmarked": self.is_bookmarked,
            "device_id": self.device_id,
        }

    def format_timestamp(self) -> str:
        """Format start time as HH:MM:SS."""
        return time.strftime("%H:%M:%S", time.gmtime(self.start_time))

    def __str__(self) -> str:
        return f"[{self.format_timestamp()}] {self.speaker}: {self.text}"


@dataclass
class IntelSnapshot:
    """A snapshot of intel extracted at a point in time."""
    timestamp: float  # When this intel was generated
    topics: list[str] = field(default_factory=list)
    action_items: list = field(default_factory=list)  # List of ActionItem or dict
    summary: str = ""

    def to_dict(self) -> dict:
        # Convert ActionItem objects to dicts if needed
        items = []
        for item in self.action_items:
            if hasattr(item, "to_dict"):
                items.append(item.to_dict())
            elif isinstance(item, dict):
                items.append(item)
        return {
            "timestamp": self.timestamp,
            "topics": self.topics,
            "action_items": items,
            "summary": self.summary,
        }

    def get_action_item_by_id(self, item_id: str) -> Optional[object]:
        """Find an action item by its ID."""
        for item in self.action_items:
            if hasattr(item, "id") and item.id == item_id:
                return item
            elif isinstance(item, dict) and item.get("id") == item_id:
                return item
        return None


@dataclass(frozen=True)
class MeetingSaveResult:
    """Structured result for persisting a meeting."""

    database_saved: bool
    json_saved: bool
    json_path: Optional[Path]
    database_error: Optional[str] = None
    json_error: Optional[str] = None
    intel_job_enqueued: bool = False


@dataclass
class MeetingState:
    """Current state of a meeting session."""
    id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    title: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    segments: list[TranscriptSegment] = field(default_factory=list)
    bookmarks: list[Bookmark] = field(default_factory=list)
    intel: Optional[IntelSnapshot] = None  # Latest intel snapshot
    intel_status: str = "disabled"
    intel_status_detail: Optional[str] = None
    intel_requested_at: Optional[datetime] = None
    intel_completed_at: Optional[datetime] = None
    mic_label: str = "Me"
    remote_label: str = "Remote"
    web_url: Optional[str] = None  # URL of web dashboard
    # Phase 14: registered AIPI-Lite devices contributing audio to
    # this meeting. Captured at attach time; ``DeviceDescriptor.id``
    # is what surfaces on each ``TranscriptSegment.device_id``.
    devices: list = field(default_factory=list)  # list[DeviceDescriptor]

    @property
    def is_active(self) -> bool:
        return self.ended_at is None

    @property
    def duration(self) -> float:
        """Duration in seconds."""
        end = self.ended_at or datetime.now()
        return (end - self.started_at).total_seconds()

    def format_duration(self) -> str:
        """Format duration as MM:SS or HH:MM:SS."""
        total_secs = int(self.duration)
        hours, remainder = divmod(total_secs, 3600)
        mins, secs = divmod(remainder, 60)
        if hours:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def get_context_around(self, timestamp: float, window: float = 10.0) -> str:
        """Get transcript text around a timestamp.

        Args:
            timestamp: The center timestamp in seconds.
            window: Seconds before and after to include.

        Returns:
            Concatenated transcript text from segments in the window.
        """
        start = max(0, timestamp - window)
        end = timestamp + window
        context_segments = [
            seg for seg in self.segments
            if start <= seg.start_time <= end or start <= seg.end_time <= end
        ]
        if not context_segments:
            return ""
        return " ".join(seg.text for seg in context_segments)

    def transcript_hash(self) -> str:
        """Return a stable digest of the current transcript contents."""
        payload = "\n".join(
            f"{seg.start_time:.3f}|{seg.end_time:.3f}|{seg.speaker}|{seg.text}"
            for seg in self.segments
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration": self.duration,
            "formatted_duration": self.format_duration(),
            "title": self.title,
            "tags": self.tags,
            "segments": [s.to_dict() for s in self.segments],
            "bookmarks": [b.to_dict() for b in self.bookmarks],
            "intel": self.intel.to_dict() if self.intel else None,
            "intel_status": {
                "state": self.intel_status,
                "detail": self.intel_status_detail,
                "requested_at": self.intel_requested_at.isoformat() if self.intel_requested_at else None,
                "completed_at": self.intel_completed_at.isoformat() if self.intel_completed_at else None,
            },
            "mic_label": self.mic_label,
            "remote_label": self.remote_label,
            "web_url": self.web_url,
            "devices": [_device_descriptor_to_dict(d) for d in self.devices],
        }


def _device_descriptor_to_dict(descriptor: object) -> dict:
    """Serialize a ``DeviceDescriptor`` to JSON-safe dict.

    Lives at module scope (not on the descriptor class) to keep
    the ``device_audio`` module free of meeting-side concerns.
    """
    return {
        "id": getattr(descriptor, "id", None),
        "label": getattr(descriptor, "label", None),
        "connected_at": _iso_or_none(getattr(descriptor, "connected_at", None)),
        "last_seen": _iso_or_none(getattr(descriptor, "last_seen", None)),
        "queue_depth": int(getattr(descriptor, "queue_depth", 0) or 0),
        "battery_pct": getattr(descriptor, "battery_pct", None),
        "rssi_dbm": getattr(descriptor, "rssi_dbm", None),
        "last_health_at": getattr(descriptor, "last_health_at", None),
    }


def _iso_or_none(value: object) -> Optional[str]:
    if value is None:
        return None
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        try:
            return isoformat()
        except Exception:
            return None
    return None
