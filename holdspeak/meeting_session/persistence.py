"""Meeting persistence (HS-63-02).

`save()` — the DB + JSON write and the deferred-intel enqueue — moved
verbatim out of MeetingSession; `self` is the session.
"""

from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, TYPE_CHECKING
import json

import numpy as np

from ..meeting import MeetingRecorder, concatenate_chunks, AudioChunk
from ..transcribe import Transcriber
from ..logging_config import get_logger

if TYPE_CHECKING:
    from ..audio import AudioSource
    from ..device_audio import DeviceDescriptor

# Optional imports for intel (the same guarded pattern as session.py).
try:
    from ..intel import (
        MeetingIntel,
        IntelResult,
        ActionItem,
        get_intel_runtime_status,
        resolve_intel_provider,
    )
except ImportError:
    MeetingIntel = None  # type: ignore
    IntelResult = None  # type: ignore
    ActionItem = None  # type: ignore
    get_intel_runtime_status = None  # type: ignore
    resolve_intel_provider = None  # type: ignore

try:
    from ..speaker_intel import SpeakerDiarizer
except ImportError:
    SpeakerDiarizer = None  # type: ignore

from .models import (
    Bookmark,
    IntelSnapshot,
    MeetingSaveResult,
    MeetingState,
    TranscriptSegment,
)

log = get_logger("meeting_session")


class PersistenceMixin:
    def save(self, directory: Optional[Path] = None) -> MeetingSaveResult:
        """Save meeting state to disk (JSON and SQLite database).

        Args:
            directory: Directory to save JSON to (default: ~/.local/share/holdspeak/meetings/).

        Returns:
            Structured save result covering both DB and JSON persistence.
        """
        with self._lock:
            if self._state is None:
                raise RuntimeError("No meeting to save")
            state = self._state

        database_saved = False
        json_saved = False
        database_error: Optional[str] = None
        json_error: Optional[str] = None
        json_path: Optional[Path] = None
        intel_job_enqueued = False

        # Save to SQLite database.
        try:
            from ..db import get_database

            db = get_database()
            db.meetings.save_meeting(state)
            database_saved = True
            if (
                self.intel_enabled
                and self.intel_deferred_enabled
                and state.intel_status == "queued"
                and state.segments
            ):
                db.intel.enqueue_intel_job(
                    state.id,
                    transcript_hash=state.transcript_hash(),
                    reason=state.intel_status_detail,
                )
                intel_job_enqueued = True
            log.info(f"Meeting saved to database: {state.id}")
        except Exception as e:
            database_error = f"{type(e).__name__}: {e}"
            log.error(f"Failed to save meeting to database: {e}")

        # HS-56-04: a wrapped meeting with open work / decisions is a moment
        # the presence mascot reflects. Fires only for a finished meeting
        # (ended_at set), only when the digest is non-empty, and never breaks
        # the save.
        if database_saved and state.ended_at is not None:
            try:
                from ..db import get_database as _get_db
                from ..meeting_aftercare import build_aftercare_ready_event

                event = build_aftercare_ready_event(_get_db(), state.id)
                if event is not None:
                    self._emit_broadcast("aftercare_ready", event)
            except Exception as exc:  # observational only
                log.debug(f"aftercare_ready broadcast skipped: {exc}")

        # Save to JSON (backward compatibility).
        if directory is None:
            directory = Path.home() / ".local" / "share" / "holdspeak" / "meetings"

        filename = f"meeting_{state.id}_{state.started_at.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = directory / filename

        try:
            directory.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w") as f:
                json.dump(state.to_dict(), f, indent=2)
            json_saved = True
            json_path = filepath
            log.info(f"Meeting saved to JSON: {filepath}")
        except Exception as e:
            json_error = f"{type(e).__name__}: {e}"
            log.error(f"Failed to save meeting to JSON: {e}")

        return MeetingSaveResult(
            database_saved=database_saved,
            json_saved=json_saved,
            json_path=json_path,
            database_error=database_error,
            json_error=json_error,
            intel_job_enqueued=intel_job_enqueued,
        )
