"""Meeting session management for HoldSpeak.

Handles background recording with incremental transcription, bookmarks,
and session persistence.
"""

from __future__ import annotations

import hashlib
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
import json

import numpy as np

from .meeting import MeetingRecorder, concatenate_chunks, AudioChunk
from .transcribe import Transcriber
from .logging_config import get_logger

# Optional imports for intel and web server
try:
    from .intel import (
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
    from .web_server import MeetingWebServer
except ImportError:
    MeetingWebServer = None  # type: ignore

try:
    from .speaker_intel import SpeakerDiarizer
except ImportError:
    SpeakerDiarizer = None  # type: ignore

log = get_logger("meeting_session")


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
        }


class MeetingSession:
    """Manages a background meeting recording session.

    Runs recording in background while allowing normal app operation.
    Transcribes incrementally and accumulates segments.
    """

    # Transcription interval in seconds
    TRANSCRIBE_INTERVAL = 10.0
    # Minimum audio duration to transcribe (seconds)
    MIN_CHUNK_DURATION = 1.0
    # Intel analysis interval (segments between analysis)
    INTEL_SEGMENT_INTERVAL = 5

    def __init__(
        self,
        transcriber: Transcriber,
        *,
        mic_label: str = "Me",
        remote_label: str = "Remote",
        mic_device: Optional[str] = None,
        system_device: Optional[str] = None,
        on_segment: Optional[Callable[[TranscriptSegment], None]] = None,
        on_mic_level: Optional[Callable[[float], None]] = None,
        on_system_level: Optional[Callable[[float], None]] = None,
        on_intel: Optional[Callable[[IntelSnapshot], None]] = None,
        on_settings_applied: Optional[Callable[[Any], None]] = None,
        intel_enabled: bool = False,
        intel_model_path: Optional[str] = None,
        intel_provider: str = "local",
        intel_cloud_model: str = "gpt-5-mini",
        intel_cloud_api_key_env: str = "OPENAI_API_KEY",
        intel_cloud_base_url: Optional[str] = None,
        intel_cloud_reasoning_effort: Optional[str] = None,
        intel_cloud_store: bool = False,
        intel_deferred_enabled: bool = True,
        web_enabled: bool = False,
        diarization_enabled: bool = False,
        diarize_mic: bool = False,
        cross_meeting_recognition: bool = True,
        mir_routing_enabled: bool = False,
        mir_profile: str = "balanced",
        mir_plugin_host: Optional[Any] = None,
        mir_db: Optional[Any] = None,
        mir_window_seconds: float = 90.0,
        mir_step_seconds: float = 30.0,
        mir_score_threshold: float = 0.6,
        mir_hysteresis: float = 0.05,
        mir_synthesize: bool = False,
    ) -> None:
        """Initialize meeting session.

        Args:
            transcriber: Whisper transcriber instance.
            mic_label: Label for mic audio (default "Me").
            remote_label: Label for system audio (default "Remote").
            mic_device: Microphone device name (None for system default).
            system_device: System audio device name (None for auto-detect BlackHole).
            on_segment: Callback when new segment is transcribed.
            on_mic_level: Callback for mic level updates.
            on_system_level: Callback for system level updates.
            on_intel: Callback when new intel snapshot is generated.
            on_settings_applied: Callback invoked when settings are saved via web UI.
            intel_enabled: Enable LLM-powered meeting intelligence.
            intel_model_path: Path to GGUF model for intel (None for default).
            intel_provider: Meeting intel provider mode (local/cloud/auto).
            intel_cloud_model: Cloud model name when provider uses cloud.
            intel_cloud_api_key_env: Env var containing cloud API key.
            intel_cloud_base_url: Optional OpenAI-compatible base URL.
            intel_cloud_reasoning_effort: Reserved for future cloud tuning.
            intel_cloud_store: Whether cloud requests may be stored server-side.
            web_enabled: Enable per-meeting web dashboard.
            diarization_enabled: Enable speaker diarization for system audio.
            diarize_mic: Also diarize mic input (for on-site meetings).
            cross_meeting_recognition: Recognize speakers across meetings.
        """
        self.transcriber = transcriber
        self.mic_label = mic_label
        self.remote_label = remote_label
        self.mic_device = mic_device
        self.system_device = system_device
        self.on_segment = on_segment
        self.on_mic_level = on_mic_level
        self.on_system_level = on_system_level
        self.on_intel = on_intel
        self.on_settings_applied = on_settings_applied
        self.intel_enabled = intel_enabled and MeetingIntel is not None
        self.intel_model_path = intel_model_path
        self.intel_provider = intel_provider
        self.intel_cloud_model = intel_cloud_model
        self.intel_cloud_api_key_env = intel_cloud_api_key_env
        self.intel_cloud_base_url = intel_cloud_base_url
        self.intel_cloud_reasoning_effort = intel_cloud_reasoning_effort
        self.intel_cloud_store = intel_cloud_store
        self.intel_deferred_enabled = intel_deferred_enabled
        self.web_enabled = web_enabled and MeetingWebServer is not None
        self.diarization_enabled = diarization_enabled and SpeakerDiarizer is not None
        self.diarize_mic = diarize_mic and SpeakerDiarizer is not None
        self.cross_meeting_recognition = cross_meeting_recognition
        # MIR-01 routing pipeline (HS-2-06). Off by default; when enabled,
        # `stop()` runs windowing + scoring + dispatch + persistence over the
        # finalized meeting state. Production wiring of `mir_plugin_host` /
        # `mir_db` happens in HS-2-09 (config + feature flags).
        self.mir_routing_enabled = bool(mir_routing_enabled)
        self.mir_profile = str(mir_profile or "balanced")
        self._mir_plugin_host = mir_plugin_host
        self._mir_db = mir_db
        self._mir_last_result: Optional[Any] = None
        # HS-2-09: pipeline tuning knobs (sourced from MeetingConfig at
        # construction time by the caller; defaults match the in-code
        # defaults of build_intent_windows / DEFAULT_INTENT_THRESHOLD).
        self._mir_window_seconds = float(mir_window_seconds)
        self._mir_step_seconds = float(mir_step_seconds)
        self._mir_score_threshold = float(mir_score_threshold)
        self._mir_hysteresis = float(mir_hysteresis)
        self._mir_synthesize = bool(mir_synthesize)

        self._state: Optional[MeetingState] = None
        self._recorder: Optional[MeetingRecorder] = None
        self._lock = threading.Lock()
        self._transcribe_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_transcribe_time = 0.0

        # Intel components
        self._intel: Optional["MeetingIntel"] = None
        self._intel_thread: Optional[threading.Thread] = None
        self._segments_since_intel = 0
        self._current_analysis_id: Optional[str] = None  # For handling interruptions
        self._deferred_intel_reason: Optional[str] = None

        # Web server
        self._web_server: Optional["MeetingWebServer"] = None

        # Speaker diarization
        self._diarizer: Optional["SpeakerDiarizer"] = None

        log.info(f"MeetingSession initialized (intel={self.intel_enabled}, web={self.web_enabled}, diarization={self.diarization_enabled})")

    @property
    def is_active(self) -> bool:
        """Check if meeting is currently active."""
        with self._lock:
            return self._state is not None and self._state.is_active

    @property
    def state(self) -> Optional[MeetingState]:
        """Get current meeting state."""
        with self._lock:
            return self._state

    @property
    def duration(self) -> float:
        """Get current meeting duration in seconds."""
        with self._lock:
            if self._state is None:
                return 0.0
            return self._state.duration

    @property
    def has_system_audio(self) -> bool:
        """Check if system audio capture is available."""
        if self._recorder is None:
            return False
        return self._recorder.has_system_audio

    def _set_intel_status_locked(
        self,
        status: str,
        detail: Optional[str] = None,
        *,
        requested_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> None:
        """Update meeting intel status while already holding the session lock."""
        if self._state is None:
            return

        self._state.intel_status = status
        self._state.intel_status_detail = detail
        if requested_at is not None:
            self._state.intel_requested_at = requested_at
        if completed_at is not None or status in {"ready", "error"}:
            self._state.intel_completed_at = completed_at

    def _set_intel_status(
        self,
        status: str,
        detail: Optional[str] = None,
        *,
        requested_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> None:
        """Update meeting intel status and broadcast it to the web dashboard."""
        with self._lock:
            self._set_intel_status_locked(
                status,
                detail,
                requested_at=requested_at,
                completed_at=completed_at,
            )
            state = self._state
            web_server = self._web_server

        if state is not None and web_server is not None:
            try:
                web_server.broadcast("intel_status", state.to_dict().get("intel_status", {}))
            except Exception as exc:
                log.debug(f"Failed to broadcast intel_status: {exc}")

    def start(self) -> MeetingState:
        """Start a new meeting session.

        Returns:
            The new meeting state.

        Raises:
            RuntimeError: If meeting is already active.
        """
        with self._lock:
            if self._state is not None and self._state.is_active:
                raise RuntimeError("Meeting already active")

            # Create new state
            self._state = MeetingState(
                id=str(uuid.uuid4())[:8],
                started_at=datetime.now(),
                mic_label=self.mic_label,
                remote_label=self.remote_label,
            )

            if self.intel_enabled:
                self._state.intel_requested_at = datetime.now()
                self._state.intel_status = "initializing"
                self._state.intel_status_detail = "Checking meeting intelligence runtime."
            else:
                self._state.intel_status = "disabled"
                self._state.intel_status_detail = "Meeting intelligence disabled in config."

            # Initialize intel if enabled
            if self.intel_enabled and MeetingIntel is not None:
                runtime_ok = True
                runtime_error: Optional[str] = None
                runtime_provider: Optional[str] = None
                if get_intel_runtime_status is not None:
                    runtime_kwargs = {
                        "provider": self.intel_provider,
                        "cloud_model": self.intel_cloud_model,
                        "cloud_api_key_env": self.intel_cloud_api_key_env,
                        "cloud_base_url": self.intel_cloud_base_url,
                    }
                    if self.intel_model_path:
                        runtime_ok, runtime_error = get_intel_runtime_status(self.intel_model_path, **runtime_kwargs)
                    else:
                        runtime_ok, runtime_error = get_intel_runtime_status(**runtime_kwargs)
                    if runtime_ok and resolve_intel_provider is not None:
                        if self.intel_model_path:
                            runtime_provider, _ = resolve_intel_provider(
                                self.intel_provider,
                                model_path=self.intel_model_path,
                                cloud_model=self.intel_cloud_model,
                                cloud_api_key_env=self.intel_cloud_api_key_env,
                                cloud_base_url=self.intel_cloud_base_url,
                            )
                        else:
                            runtime_provider, _ = resolve_intel_provider(
                                self.intel_provider,
                                cloud_model=self.intel_cloud_model,
                                cloud_api_key_env=self.intel_cloud_api_key_env,
                                cloud_base_url=self.intel_cloud_base_url,
                            )

                if runtime_ok:
                    try:
                        kwargs = {}
                        if self.intel_model_path:
                            kwargs["model_path"] = self.intel_model_path
                        kwargs["provider"] = self.intel_provider
                        kwargs["cloud_model"] = self.intel_cloud_model
                        kwargs["cloud_api_key_env"] = self.intel_cloud_api_key_env
                        kwargs["cloud_base_url"] = self.intel_cloud_base_url
                        kwargs["cloud_reasoning_effort"] = self.intel_cloud_reasoning_effort
                        kwargs["cloud_store"] = self.intel_cloud_store
                        self._intel = MeetingIntel(**kwargs)
                        self._segments_since_intel = 0
                        self._state.intel_status = "live"
                        if runtime_provider == "cloud":
                            self._state.intel_status_detail = "Cloud meeting intelligence active."
                        elif runtime_provider == "local":
                            self._state.intel_status_detail = "Local meeting intelligence active."
                        else:
                            self._state.intel_status_detail = "Meeting intelligence active."
                        self._deferred_intel_reason = None
                        log.info("Meeting intel initialized")
                    except Exception as e:
                        log.error(f"Failed to initialize intel: {e}")
                        self._intel = None
                        self._deferred_intel_reason = str(e)
                        if self.intel_deferred_enabled:
                            self._state.intel_status = "queued"
                            self._state.intel_status_detail = f"Queued for later processing: {e}"
                        else:
                            self._state.intel_status = "error"
                            self._state.intel_status_detail = str(e)
                else:
                    self._intel = None
                    self._deferred_intel_reason = runtime_error
                    if self.intel_deferred_enabled:
                        self._state.intel_status = "queued"
                        self._state.intel_status_detail = (
                            f"Queued for later processing: {runtime_error}"
                            if runtime_error
                            else "Queued for later processing."
                        )
                    else:
                        self._state.intel_status = "error"
                        self._state.intel_status_detail = runtime_error or "Meeting intelligence unavailable."

            # Initialize web server if enabled
            if self.web_enabled and MeetingWebServer is not None:
                try:
                    self._web_server = MeetingWebServer(
                        on_bookmark=self.add_bookmark,
                        on_stop=self.stop,
                        get_state=self._get_state_dict,
                        on_update_action_item=self.update_action_item,
                        on_update_action_item_review=self.update_action_item_review,
                        on_edit_action_item=self.edit_action_item,
                        on_set_title=self.set_title,
                        on_set_tags=self.set_tags,
                        on_settings_applied=self.on_settings_applied,
                    )
                    url = self._web_server.start()
                    self._state.web_url = url
                    log.info(f"Meeting web server started: {url}")
                except Exception as e:
                    log.error(f"Failed to start web server: {e}")
                    self._web_server = None

            # Initialize speaker diarization if enabled (for system audio or mic)
            if (self.diarization_enabled or self.diarize_mic) and SpeakerDiarizer is not None:
                try:
                    from .db import get_database
                    db = get_database() if self.cross_meeting_recognition else None
                    self._diarizer = SpeakerDiarizer(
                        db=db,
                        enable_cross_meeting=self.cross_meeting_recognition,
                    )
                    log.info(f"Speaker diarization initialized (system={self.diarization_enabled}, mic={self.diarize_mic})")
                except Exception as e:
                    log.error(f"Failed to initialize speaker diarization: {e}")
                    self._diarizer = None

            # Create recorder
            self._recorder = MeetingRecorder(
                mic_device=self.mic_device,
                system_device=self.system_device,
                on_mic_level=self.on_mic_level,
                on_system_level=self.on_system_level,
            )

            # Start recording
            self._recorder.start()
            self._stop_event.clear()
            self._last_transcribe_time = 0.0

            # Start transcription thread
            self._transcribe_thread = threading.Thread(
                target=self._transcribe_loop,
                daemon=True,
            )
            self._transcribe_thread.start()

            log.info(f"Meeting started: {self._state.id}")
            return self._state

    def _get_state_dict(self) -> dict:
        """Get current state as dictionary (for web server)."""
        with self._lock:
            if self._state is None:
                return {}
            return self._state.to_dict()

    def stop(self) -> MeetingState:
        """Stop the current meeting session.

        Returns:
            The final meeting state.

        Raises:
            RuntimeError: If no meeting is active.
        """
        with self._lock:
            if self._state is None or not self._state.is_active:
                raise RuntimeError("No active meeting")

            # Signal stop
            self._stop_event.set()
            transcribe_thread = self._transcribe_thread
            intel_thread = self._intel_thread
            recorder = self._recorder
            # Detach the recorder under lock so no other thread can attempt to use it.
            self._recorder = None

        # Wait for transcription thread
        if transcribe_thread is not None:
            transcribe_thread.join(timeout=5.0)

        # Wait for any pending intel thread
        if intel_thread is not None:
            intel_thread.join(timeout=10.0)

        # Stop recorder and do final transcription outside the session lock. The
        # final transcription path appends segments under self._lock.
        if recorder is not None:
            try:
                mic_chunks, system_chunks = recorder.stop()
                self._transcribe_chunks(mic_chunks, system_chunks, final=True)
            except Exception as e:
                log.error(f"Error stopping recorder: {e}")

        with self._lock:
            state = self._state
            intel = self._intel
            web_server = self._web_server
            diarizer = self._diarizer

        assert state is not None

        # Run final intel analysis outside the lock. The analysis path calls
        # back into methods like get_formatted_transcript(), which also use
        # self._lock.
        if intel is not None and state.segments:
            try:
                self._run_intel_analysis(final=True)
            except Exception as e:
                log.error(f"Final intel analysis failed: {e}")

        # Auto-generate title if not manually set.
        if intel is not None and not state.title and state.segments:
            try:
                transcript = "\n".join(str(s) for s in state.segments)
                title = intel.generate_title(transcript)
                if title:
                    with self._lock:
                        if self._state is not None and not self._state.title:
                            self._state.title = title
                    log.info(f"Auto-generated meeting title: {title}")
            except Exception as e:
                log.error(f"Auto-title generation failed: {e}")

        # Stop web server outside the lock because shutdown can block while the
        # server loop is draining websocket clients.
        if web_server is not None:
            try:
                web_server.stop()
            except Exception as e:
                log.error(f"Error stopping web server: {e}")

        # Save speaker embeddings outside the lock because it performs DB I/O.
        if diarizer is not None:
            try:
                diarizer.save_speakers()
                log.info("Speaker embeddings saved")
            except Exception as e:
                log.error(f"Failed to save speaker embeddings: {e}")

        # MIR-01 routing pass over the finalized meeting state (HS-2-06).
        # Off by default; runs only when the session was constructed with
        # `mir_routing_enabled=True` and a plugin host. Per-stage failures
        # degrade gracefully (MIR-F-012); nothing here can raise into the
        # caller and nothing holds `self._lock`.
        if self.mir_routing_enabled and self._mir_plugin_host is not None and state.segments:
            try:
                from .plugins.pipeline import process_meeting_state as _mir_process

                self._mir_last_result = _mir_process(
                    state,
                    self._mir_plugin_host,
                    profile=self.mir_profile,
                    threshold=self._mir_score_threshold,
                    hysteresis=self._mir_hysteresis,
                    window_seconds=self._mir_window_seconds,
                    step_seconds=self._mir_step_seconds,
                    db=self._mir_db,
                    synthesize=self._mir_synthesize,
                )
                log.info(
                    "MIR routing finalized: "
                    f"windows={len(self._mir_last_result.windows)}, "
                    f"runs={len(self._mir_last_result.runs)}, "
                    f"errors={len(self._mir_last_result.errors)}"
                )
            except Exception as e:
                log.error(f"MIR routing finalization failed: {e}")

        with self._lock:
            # Save speaker embeddings for cross-meeting recognition
            if self._web_server is web_server:
                self._web_server = None
            if self._diarizer is diarizer:
                self._diarizer = None

            # Clean up intel/runtime references
            self._intel = None
            self._intel_thread = None
            self._transcribe_thread = None
            self._current_analysis_id = None

            # Mark as ended
            self._state.ended_at = datetime.now()
            final_state = self._state

        assert final_state is not None

        log.info(f"Meeting stopped: {final_state.id}, duration={final_state.format_duration()}")
        return final_state

    def add_bookmark(self, label: str = "", auto_label: bool = True) -> Optional[Bookmark]:
        """Add a bookmark at the current time.

        Args:
            label: Optional label for the bookmark. If empty and auto_label=True,
                   a label will be generated from context.
            auto_label: If True and label is empty, generate a label from context.

        Returns:
            The created bookmark, or None if no meeting active.
        """
        with self._lock:
            if self._state is None or not self._state.is_active:
                return None

            timestamp = self._state.duration

            # Format timestamp for fallback label
            mins = int(timestamp // 60)
            secs = int(timestamp % 60)
            timestamp_label = f"Bookmark @ {mins:02d}:{secs:02d}"

            bookmark = Bookmark(
                timestamp=timestamp,
                label=label or timestamp_label,
            )
            self._state.bookmarks.append(bookmark)
            log.info(f"Bookmark added at {bookmark.timestamp:.1f}s: {bookmark.label}")

            # Try to generate a better label asynchronously if not provided
            if not label and auto_label and self._intel is not None:
                context = self._state.get_context_around(timestamp, window=10.0)
                if context:
                    thread = threading.Thread(
                        target=self._generate_bookmark_label,
                        args=(bookmark, context),
                        daemon=True,
                    )
                    thread.start()
                # If no context, keep the timestamp label (already set above)

            return bookmark

    def _generate_bookmark_label(self, bookmark: Bookmark, context: str) -> None:
        """Generate and update bookmark label in background."""
        try:
            if self._intel is None:
                return
            label = self._intel.generate_bookmark_label(context)
            if label:
                with self._lock:
                    bookmark.label = label
                log.info(f"Bookmark label updated: {label}")
        except Exception as exc:
            log.error(f"Bookmark label generation failed: {exc}")

    def update_action_item(self, item_id: str, status: str) -> Optional[dict]:
        """Update the status of an action item.

        Args:
            item_id: The unique ID of the action item.
            status: New status ("done", "pending", or "dismissed").

        Returns:
            The updated action item as a dict, or None if not found.
        """
        with self._lock:
            if self._state is None or self._state.intel is None:
                return None

            normalized = str(status).strip().lower()
            if normalized not in {"done", "pending", "dismissed"}:
                log.warning(f"Unknown action item status: {status}")
                return None

            for item in self._state.intel.action_items:
                if hasattr(item, "id") and item.id == item_id:
                    if normalized == "done":
                        item.mark_done()
                    elif normalized == "dismissed":
                        item.dismiss()
                    else:
                        item.status = "pending"
                        item.completed_at = None
                    log.info(f"Action item {item_id} updated to status={normalized}")
                    return item.to_dict()

                if isinstance(item, dict) and item.get("id") == item_id:
                    item["status"] = normalized
                    if normalized == "pending":
                        item["completed_at"] = None
                    else:
                        item["completed_at"] = datetime.now().isoformat()
                    log.info(f"Action item {item_id} updated to status={normalized}")
                    return item

            log.warning(f"Action item not found: {item_id}")
            return None

    def update_action_item_review(self, item_id: str, review_state: str) -> Optional[dict]:
        """Update review state of an action item.

        Args:
            item_id: The unique ID of the action item.
            review_state: New review state ("pending" or "accepted").

        Returns:
            Updated action item dict, or None if not found/invalid.
        """
        with self._lock:
            if self._state is None or self._state.intel is None:
                return None

            normalized = str(review_state).strip().lower()
            if normalized not in {"pending", "accepted"}:
                log.warning(f"Unknown action item review_state: {review_state}")
                return None

            for item in self._state.intel.action_items:
                if hasattr(item, "id") and item.id == item_id:
                    if normalized == "accepted":
                        if hasattr(item, "accept"):
                            item.accept()
                        else:
                            item.review_state = "accepted"
                            item.reviewed_at = datetime.now().isoformat()
                    else:
                        item.review_state = "pending"
                        item.reviewed_at = None
                    log.info(f"Action item {item_id} updated to review_state={normalized}")
                    return item.to_dict()

                if isinstance(item, dict) and item.get("id") == item_id:
                    item["review_state"] = normalized
                    item["reviewed_at"] = datetime.now().isoformat() if normalized == "accepted" else None
                    log.info(f"Action item {item_id} updated to review_state={normalized}")
                    return item

            log.warning(f"Action item not found: {item_id}")
            return None

    def edit_action_item(
        self,
        item_id: str,
        *,
        task: str,
        owner: Optional[str],
        due: Optional[str],
    ) -> Optional[dict]:
        """Edit action-item content and mark it accepted.

        Args:
            item_id: The unique ID of the action item.
            task: New task text.
            owner: Optional owner text (None/empty clears).
            due: Optional due text (None/empty clears).

        Returns:
            Updated action item dict, or None if not found/invalid.
        """
        clean_task = str(task).strip()
        if not clean_task:
            return None

        clean_owner = owner.strip() if isinstance(owner, str) else None
        clean_due = due.strip() if isinstance(due, str) else None

        with self._lock:
            if self._state is None or self._state.intel is None:
                return None

            for item in self._state.intel.action_items:
                if hasattr(item, "id") and item.id == item_id:
                    item.task = clean_task
                    item.owner = clean_owner or None
                    item.due = clean_due or None
                    if hasattr(item, "accept"):
                        item.accept()
                    else:
                        item.review_state = "accepted"
                        item.reviewed_at = datetime.now().isoformat()
                    log.info(f"Action item {item_id} edited and accepted")
                    return item.to_dict()

                if isinstance(item, dict) and item.get("id") == item_id:
                    item["task"] = clean_task
                    item["owner"] = clean_owner or None
                    item["due"] = clean_due or None
                    item["review_state"] = "accepted"
                    item["reviewed_at"] = datetime.now().isoformat()
                    log.info(f"Action item {item_id} edited and accepted")
                    return item

            log.warning(f"Action item not found: {item_id}")
            return None

    def set_title(self, title: str) -> None:
        """Set meeting title.

        Args:
            title: The meeting title. Empty string clears the title.
        """
        with self._lock:
            if self._state:
                self._state.title = title.strip() or None
                log.info(f"Meeting title set: {self._state.title}")
                if self._web_server:
                    self._web_server.broadcast("meeting_updated", {
                        "title": self._state.title,
                        "tags": self._state.tags,
                    })

    def get_title(self) -> Optional[str]:
        """Get current meeting title."""
        with self._lock:
            if self._state:
                return self._state.title
            return None

    def add_tag(self, tag: str) -> bool:
        """Add a tag to the meeting.

        Args:
            tag: Tag to add (will be lowercased and trimmed).

        Returns:
            True if tag was added, False if already exists or invalid.
        """
        with self._lock:
            if self._state and tag.strip():
                clean_tag = tag.strip().lower()
                if clean_tag not in self._state.tags:
                    self._state.tags.append(clean_tag)
                    log.info(f"Tag added: {clean_tag}")
                    if self._web_server:
                        self._web_server.broadcast("meeting_updated", {
                            "title": self._state.title,
                            "tags": self._state.tags,
                        })
                    return True
        return False

    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from the meeting.

        Args:
            tag: Tag to remove.

        Returns:
            True if tag was removed, False if not found.
        """
        with self._lock:
            if self._state:
                clean_tag = tag.strip().lower()
                if clean_tag in self._state.tags:
                    self._state.tags.remove(clean_tag)
                    log.info(f"Tag removed: {clean_tag}")
                    if self._web_server:
                        self._web_server.broadcast("meeting_updated", {
                            "title": self._state.title,
                            "tags": self._state.tags,
                        })
                    return True
        return False

    def set_tags(self, tags: list[str]) -> None:
        """Replace all tags with a new list.

        Args:
            tags: List of tags (will be lowercased and trimmed).
        """
        with self._lock:
            if self._state:
                self._state.tags = [t.strip().lower() for t in tags if t.strip()]
                log.info(f"Tags set: {self._state.tags}")
                if self._web_server:
                    self._web_server.broadcast("meeting_updated", {
                        "title": self._state.title,
                        "tags": self._state.tags,
                    })

    def get_tags(self) -> list[str]:
        """Get current meeting tags."""
        with self._lock:
            if self._state:
                return list(self._state.tags)
            return []

    def get_transcript(self) -> list[TranscriptSegment]:
        """Get all transcript segments."""
        with self._lock:
            if self._state is None:
                return []
            return list(self._state.segments)

    def get_bookmarks(self) -> list[Bookmark]:
        """Get all bookmarks."""
        with self._lock:
            if self._state is None:
                return []
            return list(self._state.bookmarks)

    def get_formatted_transcript(self) -> str:
        """Get transcript as formatted string."""
        segments = self.get_transcript()
        if not segments:
            return ""
        return "\n".join(str(s) for s in segments)

    def _transcribe_loop(self) -> None:
        """Background thread that transcribes audio periodically."""
        log.debug("Transcription loop started")

        while not self._stop_event.is_set():
            # Wait for interval or stop
            self._stop_event.wait(self.TRANSCRIBE_INTERVAL)

            if self._stop_event.is_set():
                break

            with self._lock:
                if self._recorder is None:
                    continue

                # Get chunks since last transcription
                mic_chunks, system_chunks = self._recorder.get_pending_chunks(
                    since=self._last_transcribe_time
                )

            if mic_chunks or system_chunks:
                self._transcribe_chunks(mic_chunks, system_chunks)

        log.debug("Transcription loop ended")

    def _transcribe_chunks(
        self,
        mic_chunks: list[AudioChunk],
        system_chunks: list[AudioChunk],
        final: bool = False,
    ) -> None:
        """Transcribe audio chunks and add to segments."""
        current_time = time.time()
        new_segments: list[TranscriptSegment] = []

        # Process mic chunks
        if mic_chunks:
            mic_audio = concatenate_chunks(mic_chunks)
            duration = len(mic_audio) / 16000

            if duration >= self.MIN_CHUNK_DURATION:
                start_time = mic_chunks[0].timestamp
                end_time = mic_chunks[-1].end_time

                try:
                    text = self.transcriber.transcribe(mic_audio)
                    if text and text.strip():
                        # Optionally diarize mic audio (for on-site meetings)
                        speaker_id: Optional[str] = None
                        speaker_name = self.mic_label
                        if self.diarize_mic and self._diarizer is not None:
                            try:
                                speaker_id, speaker_name = self._diarizer.identify_speaker(mic_audio)
                            except Exception as e:
                                log.error(f"Mic speaker diarization error: {e}")

                        segment = TranscriptSegment(
                            text=text.strip(),
                            speaker=speaker_name,
                            speaker_id=speaker_id,
                            start_time=start_time,
                            end_time=end_time,
                        )
                        with self._lock:
                            if self._state:
                                self._state.segments.append(segment)
                        new_segments.append(segment)
                        if self.on_segment:
                            try:
                                self.on_segment(segment)
                            except Exception as e:
                                log.error(f"on_segment callback error: {e}")
                        log.debug(f"Mic segment: {segment}")
                except Exception as e:
                    log.error(f"Mic transcription error: {e}")

        # Process system chunks
        if system_chunks:
            system_audio = concatenate_chunks(system_chunks)
            duration = len(system_audio) / 16000

            if duration >= self.MIN_CHUNK_DURATION:
                start_time = system_chunks[0].timestamp
                end_time = system_chunks[-1].end_time

                try:
                    text = self.transcriber.transcribe(system_audio)
                    if text and text.strip():
                        # Identify speaker via diarization
                        speaker_id: Optional[str] = None
                        speaker_name = self.remote_label
                        if self._diarizer is not None:
                            try:
                                speaker_id, speaker_name = self._diarizer.identify_speaker(system_audio)
                            except Exception as e:
                                log.error(f"Speaker diarization error: {e}")

                        segment = TranscriptSegment(
                            text=text.strip(),
                            speaker=speaker_name,
                            speaker_id=speaker_id,
                            start_time=start_time,
                            end_time=end_time,
                        )
                        with self._lock:
                            if self._state:
                                self._state.segments.append(segment)
                        new_segments.append(segment)
                        if self.on_segment:
                            try:
                                self.on_segment(segment)
                            except Exception as e:
                                log.error(f"on_segment callback error: {e}")
                        log.debug(f"System segment: {segment}")
                except Exception as e:
                    log.error(f"System transcription error: {e}")

        # Broadcast new segments via web server
        if new_segments and self._web_server is not None:
            for segment in new_segments:
                try:
                    self._web_server.broadcast("segment", segment.to_dict())
                except Exception as e:
                    log.error(f"Failed to broadcast segment: {e}")

        # Update last transcribe time
        if mic_chunks or system_chunks:
            max_end = 0.0
            if mic_chunks:
                max_end = max(max_end, mic_chunks[-1].end_time)
            if system_chunks:
                max_end = max(max_end, system_chunks[-1].end_time)
            self._last_transcribe_time = max_end

        # Trigger intel analysis periodically
        if new_segments:
            self._segments_since_intel += len(new_segments)
            if self._intel is not None and self._segments_since_intel >= self.INTEL_SEGMENT_INTERVAL:
                self._maybe_run_intel()

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
            from .db import get_database

            db = get_database()
            db.save_meeting(state)
            database_saved = True
            if (
                self.intel_enabled
                and self.intel_deferred_enabled
                and state.intel_status == "queued"
                and state.segments
            ):
                db.enqueue_intel_job(
                    state.id,
                    transcript_hash=state.transcript_hash(),
                    reason=state.intel_status_detail,
                )
                intel_job_enqueued = True
            log.info(f"Meeting saved to database: {state.id}")
        except Exception as e:
            database_error = f"{type(e).__name__}: {e}"
            log.error(f"Failed to save meeting to database: {e}")

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
                    # Stream token to dashboard
                    if self._web_server is not None:
                        try:
                            self._web_server.broadcast("intel_token", chunk)
                        except Exception as e:
                            log.debug(f"Failed to broadcast intel token: {e}")
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

                    # Broadcast completion via web server
                    if self._web_server is not None:
                        try:
                            self._web_server.broadcast("intel_complete", snapshot.to_dict())
                            self._web_server.broadcast(
                                "intel_status",
                                self._get_state_dict().get("intel_status", {}),
                            )
                        except Exception as e:
                            log.error(f"Failed to broadcast intel_complete: {e}")

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
