"""The live intel cadence (HS-63-02).

The should-run check, the analysis pass, and bookmark-label refinement,
moved verbatim out of MeetingSession; `self` is the session.
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


class IntelAnalysisMixin:
    def _maybe_run_intel(self) -> None:
        """Run intel analysis in background if not already running."""
        if self._intel is None:
            return

        # Check if intel thread is already running
        if self._intel_thread is not None and self._intel_thread.is_alive():
            log.debug("Intel analysis already in progress, skipping")
            return

        self._segments_since_intel = 0
        self._set_intel_status("running", "Analyzing the latest transcript window.")
        self._intel_thread = threading.Thread(
            target=self._run_intel_analysis,
            daemon=True,
        )
        self._intel_thread.start()

    def _run_intel_analysis(self, final: bool = False) -> None:
        """Run intel analysis on current transcript with streaming support."""
        if self._intel is None:
            return

        # Get current transcript
        transcript = self.get_formatted_transcript()
        if not transcript:
            return

        log.info(f"Running intel analysis (final={final}, streaming=True)")

        # Generate a unique analysis ID to handle interruptions
        analysis_id = str(uuid.uuid4())[:8]
        self._current_analysis_id = analysis_id

        try:
            # Use streaming mode
            stream_iter = self._intel.analyze(transcript, stream=True)

            for chunk in stream_iter:
                # Check if this analysis was interrupted by a newer one
                if self._current_analysis_id != analysis_id:
                    log.info(f"Intel analysis {analysis_id} interrupted by newer analysis")
                    return

                if isinstance(chunk, str):
                    # Stream token to any observer (web dashboard)
                    self._emit_broadcast("intel_token", chunk)
                else:
                    # Final IntelResult
                    result = chunk
                    if getattr(result, "error", None):
                        detail = f"Deferred intel required: {result.error}"
                        log.warning(f"Intel analysis deferred: {result.error}")
                        if self.intel_deferred_enabled:
                            self._deferred_intel_reason = result.error
                            with self._lock:
                                self._intel = None
                            self._set_intel_status("queued", detail)
                        else:
                            self._set_intel_status("error", result.error, completed_at=datetime.now())
                        return

                    # Create snapshot - preserve ActionItem objects for status tracking
                    snapshot = IntelSnapshot(
                        timestamp=self.duration,
                        topics=result.topics,
                        action_items=result.action_items,  # Keep ActionItem objects
                        summary=result.summary,
                    )

                    # Update state
                    with self._lock:
                        if self._state:
                            self._state.intel = snapshot
                            self._state.intel_status = "ready"
                            self._state.intel_status_detail = (
                                "Meeting intelligence ready."
                                if not final
                                else "Final meeting intelligence ready."
                            )
                            self._state.intel_completed_at = datetime.now()

                    # Emit completion to any observer (web dashboard)
                    self._emit_broadcast("intel_complete", snapshot.to_dict())
                    self._emit_broadcast(
                        "intel_status",
                        self._get_state_dict().get("intel_status", {}),
                    )

                    # Callback
                    if self.on_intel:
                        try:
                            self.on_intel(snapshot)
                        except Exception as e:
                            log.error(f"on_intel callback error: {e}")

                    log.info(f"Intel analysis complete: {len(snapshot.topics)} topics, {len(snapshot.action_items)} action items")

                    # Refine bookmark labels with full meeting context (final pass only)
                    if final:
                        self._refine_bookmark_labels(snapshot.summary)

        except Exception as e:
            log.error(f"Intel analysis failed: {e}")
            if self.intel_deferred_enabled:
                self._deferred_intel_reason = str(e)
                with self._lock:
                    self._intel = None
                self._set_intel_status("queued", f"Deferred intel required: {e}")
            else:
                self._set_intel_status("error", str(e), completed_at=datetime.now())

    def _refine_bookmark_labels(self, meeting_summary: str) -> None:
        """Refine all bookmark labels using full meeting context.

        Called during final analysis to improve bookmark labels with:
        - High-level meeting summary for grounding
        - Local ±10s context around each bookmark
        """
        if self._intel is None or self._state is None:
            return

        bookmarks = self._state.bookmarks
        if not bookmarks:
            return

        log.info(f"Refining {len(bookmarks)} bookmark labels with meeting context")

        for bookmark in bookmarks:
            try:
                # Get local context around bookmark
                local_context = self._state.get_context_around(bookmark.timestamp, window=10.0)
                if not local_context:
                    continue  # No transcript near this bookmark

                # Generate refined label with meeting context
                label = self._intel.generate_bookmark_label_with_context(
                    local_context=local_context,
                    meeting_summary=meeting_summary,
                )
                if label and label != bookmark.label:
                    old_label = bookmark.label
                    with self._lock:
                        bookmark.label = label
                    log.info(f"Refined bookmark: '{old_label}' -> '{label}'")

            except Exception as e:
                log.error(f"Failed to refine bookmark at {bookmark.timestamp:.1f}s: {e}")
