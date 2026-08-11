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
from typing import Any, Callable, Optional, TYPE_CHECKING
import json

import numpy as np

from ..meeting_recorder import MeetingRecorder, concatenate_chunks, AudioChunk
from ..transcribe import Transcriber
from ..logging_config import get_logger

if TYPE_CHECKING:
    from ..audio import AudioSource
    from ..device_audio import DeviceDescriptor

# Optional imports for intel
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

log = get_logger("meeting_session")

from .models import (
    Bookmark,
    IntelSnapshot,
    MeetingSaveResult,
    MeetingState,
    TranscriptSegment,
    _device_descriptor_to_dict,
    _iso_or_none,
)

from .intel_admission import IntelAdmissionMixin
from .intel_analysis import IntelAnalysisMixin
from .mutations import MeetingMutationsMixin
from .persistence import PersistenceMixin
from .transcribe_loop import TranscribeLoopMixin
from .bookmarks import BookmarkViewsMixin


class MeetingSession(
    TranscribeLoopMixin,
    IntelAdmissionMixin,
    IntelAnalysisMixin,
    PersistenceMixin,
    MeetingMutationsMixin,
    BookmarkViewsMixin,
):
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
        on_broadcast: Optional[Callable[[str, Any], None]] = None,
        intel_enabled: bool = False,
        intel_model_path: Optional[str] = None,
        intel_provider: str = "local",
        cloud_model: str = "gpt-5-mini",
        cloud_api_key_env: str = "OPENAI_API_KEY",
        cloud_base_url: Optional[str] = None,
        cloud_reasoning_effort: Optional[str] = None,
        cloud_store: bool = False,
        intel_deferred_enabled: bool = True,
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
        mir_disabled_plugins: Optional[list[str]] = None,
        mir_segment_probe: Optional[Any] = None,
        principal: Optional[Any] = None,
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
            on_broadcast: Callback ``(message_type, data)`` the session emits live
                meeting events through (segments, intel tokens/completion, status,
                title/tag updates). Default ``None`` (no-op): the session has no
                knowledge of any web server — an observer (e.g. ``WebRuntime``)
                wires this to its own broadcast channel.
            intel_enabled: Enable LLM-powered meeting intelligence.
            intel_model_path: Path to GGUF model for intel (None for default).
            intel_provider: Meeting intel provider mode (local/cloud/auto).
            cloud_model: Cloud model name when provider uses cloud.
            cloud_api_key_env: Env var containing cloud API key.
            cloud_base_url: Optional OpenAI-compatible base URL.
            cloud_reasoning_effort: Reserved for future cloud tuning.
            cloud_store: Whether cloud requests may be stored server-side.
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
        self.on_broadcast = on_broadcast
        self.intel_enabled = intel_enabled and MeetingIntel is not None
        self.intel_model_path = intel_model_path
        self.intel_provider = intel_provider
        self.cloud_model = cloud_model
        self.cloud_api_key_env = cloud_api_key_env
        self.cloud_base_url = cloud_base_url
        self.cloud_reasoning_effort = cloud_reasoning_effort
        self.cloud_store = cloud_store
        self.intel_deferred_enabled = intel_deferred_enabled
        # HS-131-08: the authenticated principal live meeting intelligence is
        # admitted under. ``None`` (device/auto start with no issued principal)
        # keeps recording available and refuses intelligence by name — an OWNER
        # principal is NEVER synthesized here.
        self.intel_principal = principal
        self._intel_plan: Optional[Any] = None
        self._intel_parent: Optional[Any] = None
        self._intel_refusal: str = ""
        # HS-131-09: why a transcription interval would be dropped, if it is. The
        # parent covers transcription too, so a session that admitted nothing
        # transcribes nothing — never an unadmitted Whisper call.
        self._transcription_refusal: str = ""
        # Once the live parent is closed it is never revived: a later dispatch
        # attempt is refused by name, not silently re-admitted (HS-131-08).
        self._intel_closed: bool = False
        # The structured work the stop handoff displaced onto the deferred job.
        self._intel_displaced_work: tuple[str, ...] = ()
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
        # HS-35-03: per-project plugin enable/disable, threaded into dispatch.
        self._mir_disabled_plugins = list(mir_disabled_plugins or [])
        # HS-36-05: optional LLM-assisted per-segment intent probe. When supplied,
        # each routing window's lexical scores are augmented so brief/paraphrased
        # intents aren't diluted away. None = lexical-only (unchanged behavior).
        self._mir_segment_probe = mir_segment_probe

        self._state: Optional[MeetingState] = None
        self._recorder: Optional[MeetingRecorder] = None
        self._capture_journal: Optional[Any] = None
        self._lock = threading.Lock()
        self._transcribe_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_transcribe_time = 0.0
        # AIPI-4-15 / HS-17 overlap windows: per-stream tail audio kept
        # between transcription passes so a sentence that spans a 10 s
        # boundary doesn't get cut at the boundary. Keyed by stream id
        # ("mic", "system", "device:<id>"). Trade-off: occasional duplicate
        # words at boundary, accepted in exchange for continuous-sentence
        # transcripts.
        self._overlap_tail_seconds: float = 1.5
        self._stream_tails: dict[str, "np.ndarray"] = {}

        # Intel components
        self._intel: Optional["MeetingIntel"] = None
        self._intel_thread: Optional[threading.Thread] = None
        self._segments_since_intel = 0
        self._current_analysis_id: Optional[str] = None  # For handling interruptions
        self._deferred_intel_reason: Optional[str] = None

        # Speaker diarization
        self._diarizer: Optional["SpeakerDiarizer"] = None

        log.info(f"MeetingSession initialized (intel={self.intel_enabled}, diarization={self.diarization_enabled})")

    def _emit_broadcast(self, message_type: str, data: Any) -> None:
        """Emit a live meeting event to the observer's broadcast channel.

        Inversion of control: the session knows nothing about a web server.
        It emits; whoever supplied ``on_broadcast`` (e.g. ``WebRuntime``)
        decides what to do with the event. No-op when no callback is wired.
        """
        callback = self.on_broadcast
        if callback is None:
            return
        try:
            callback(message_type, data)
        except Exception as exc:
            log.debug(f"on_broadcast callback raised for {message_type!r}: {exc}")

    def _emit_actuator_proposal(self, proposal: Any) -> None:
        """Broadcast a newly-persisted actuator proposal (HS-38-04).

        Wired into the finalization-time MIR pipeline as `on_proposal`; the
        dashboard shows it in a live "pending actions" panel and can approve/
        reject on the spot (the existing decision endpoint — no execution here).

        The broadcast payload is deliberately **read-only**: id + lifecycle +
        the human-readable preview only. The machine `payload` (the egress
        source-of-truth) is **never** put on the wire — a live client must not
        receive anything that could itself trigger an effect on receipt.
        """
        try:
            created = getattr(proposal, "created_at", None)
            data = {
                "id": getattr(proposal, "id", ""),
                "meeting_id": getattr(proposal, "meeting_id", ""),
                "plugin_id": getattr(proposal, "plugin_id", ""),
                "status": getattr(proposal, "status", "proposed"),
                "target": getattr(proposal, "target", ""),
                "action": getattr(proposal, "action", ""),
                "preview": getattr(proposal, "preview", ""),
                "reversible": bool(getattr(proposal, "reversible", False)),
                # ISO string — the broadcast bottoms out on json.dumps.
                "created_at": created.isoformat() if hasattr(created, "isoformat") else created,
            }
        except Exception as exc:  # never let a bad record break finalization
            log.debug(f"could not build actuator_proposed payload: {exc}")
            return
        self._emit_broadcast("actuator_proposed", data)

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

    # ------------------------------------------------------------------
    # Phase 14: device-stream attachment (HS-14-06)
    # ------------------------------------------------------------------
    def attach_device(
        self,
        descriptor: "DeviceDescriptor",
        source: "AudioSource",
    ) -> None:
        """Attach a registered device's audio source to the active meeting.

        ``source`` is started immediately so subsequent
        ``RemoteAudioRecorder.push`` calls (driven by the WebSocket
        route) accumulate audio for this meeting. The device's
        descriptor is appended to ``state.devices`` for round-trip
        through ``to_dict``.
        """
        with self._lock:
            if self._state is None or not self._state.is_active:
                raise RuntimeError("No active meeting to attach a device to")
            if self._recorder is None:
                raise RuntimeError("Meeting recorder is not available")
            self._state.devices.append(descriptor)

        try:
            source.start_recording()
        except Exception:
            # Roll back the descriptor append so a failed start
            # doesn't leave a phantom device on the state.
            with self._lock:
                if self._state is not None and self._state.devices:
                    if self._state.devices[-1] is descriptor:
                        self._state.devices.pop()
            raise

        self._recorder.register_device_stream(
            descriptor.id, source, label=descriptor.label
        )
        log.info(
            "meeting_device_attached",
            extra={"device_id": descriptor.id, "label": descriptor.label},
        )

    def detach_device(self, device_id: str) -> None:
        """Drop a previously-attached device from the active meeting.

        Stops the device's recorder (any audio still buffered is
        discarded — the audio for the in-flight drain interval is
        already captured by the most recent ``get_pending_device_chunks``
        call) and removes it from the recorder's registration list.
        The descriptor stays on ``state.devices`` so the saved
        meeting still records who participated.
        """
        if self._recorder is None:
            return

        source = self._recorder._device_sources.get(device_id)  # type: ignore[attr-defined]
        if source is not None:
            try:
                if getattr(source, "is_recording", False):
                    source.stop_recording()
            except Exception:
                pass

        self._recorder.unregister_device_stream(device_id)
        log.info(
            "meeting_device_detached",
            extra={"device_id": device_id},
        )

    def is_device_attached(self, device_id: str) -> bool:
        if self._recorder is None:
            return False
        return device_id in self._recorder.registered_device_ids()

    def update_device_descriptor(self, descriptor: "DeviceDescriptor") -> bool:
        """Refresh the attached-device descriptor stored on active state."""
        with self._lock:
            if self._state is None:
                return False
            for index, existing in enumerate(self._state.devices):
                if getattr(existing, "id", None) == descriptor.id:
                    self._state.devices[index] = descriptor
                    return True
        return False

    def _set_intel_status_locked(
        self,
        status: str,
        detail: Optional[str] = None,
        *,
        requested_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        after_handoff: bool = False,
    ) -> None:
        """Update meeting intel status while already holding the session lock.

        HS-131-08 (D4): once ``stop()`` raised the intelligence closed flag, only
        the handoff itself (``after_handoff=True``) may stamp intel state. A
        lingering live-analysis thread that comes back later is discarded, so no
        late `ready`/`error` can overwrite the honest `queued` handoff.
        """
        if self._state is None:
            return
        if getattr(self, "_intel_closed", False) and not after_handoff:
            log.info(
                "Discarding late intel status '%s': the stop handoff already fired",
                status,
            )
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
        after_handoff: bool = False,
    ) -> None:
        """Update meeting intel status and broadcast it to the web dashboard."""
        with self._lock:
            self._set_intel_status_locked(
                status,
                detail,
                requested_at=requested_at,
                completed_at=completed_at,
                after_handoff=after_handoff,
            )
            state = self._state

        if state is not None:
            self._emit_broadcast("intel_status", state.to_dict().get("intel_status", {}))

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
                capture_status="provisional",
                provenance="desktop",
            )

            # HS-131-08: admit the ONE authenticated `meeting.session` parent over
            # a frozen MeetingIntelPlan@1 before any Intel engine exists. A
            # refusal here disables intelligence with a named status and leaves
            # recording untouched.
            self._admit_intel_session()

            if self._intel_refusal:
                pass  # _admit_intel_session already set the honest named status
            elif self.intel_enabled:
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
                        "cloud_model": self.cloud_model,
                        "cloud_api_key_env": self.cloud_api_key_env,
                        "cloud_base_url": self.cloud_base_url,
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
                                cloud_model=self.cloud_model,
                                cloud_api_key_env=self.cloud_api_key_env,
                                cloud_base_url=self.cloud_base_url,
                            )
                        else:
                            runtime_provider, _ = resolve_intel_provider(
                                self.intel_provider,
                                cloud_model=self.cloud_model,
                                cloud_api_key_env=self.cloud_api_key_env,
                                cloud_base_url=self.cloud_base_url,
                            )

                if runtime_ok:
                    try:
                        kwargs = {}
                        if self.intel_model_path:
                            kwargs["model_path"] = self.intel_model_path
                        kwargs["provider"] = self.intel_provider
                        kwargs["cloud_model"] = self.cloud_model
                        kwargs["cloud_api_key_env"] = self.cloud_api_key_env
                        kwargs["cloud_base_url"] = self.cloud_base_url
                        kwargs["cloud_reasoning_effort"] = self.cloud_reasoning_effort
                        kwargs["cloud_store"] = self.cloud_store
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

            # Initialize speaker diarization if enabled (for system audio or mic)
            if (self.diarization_enabled or self.diarize_mic) and SpeakerDiarizer is not None:
                try:
                    from ..db import get_database
                    db = get_database() if self.cross_meeting_recognition else None
                    self._diarizer = SpeakerDiarizer(
                        db=db,
                        enable_cross_meeting=self.cross_meeting_recognition,
                    )
                    log.info(f"Speaker diarization initialized (system={self.diarization_enabled}, mic={self.diarize_mic})")
                except Exception as e:
                    log.error(f"Failed to initialize speaker diarization: {e}")
                    self._diarizer = None

            # HS-92-04: make the Meeting durable before an audio device is
            # opened. If this transaction fails, no audio is accepted and the
            # caller gets an actionable start failure rather than a ghost take.
            from ..db import get_database

            try:
                get_database().meetings.save_meeting(self._state)
            except Exception as exc:
                self._state.capture_status = "capture_failed"
                self._state.capture_failure = f"Could not create the Meeting: {exc}"
                raise RuntimeError(self._state.capture_failure) from exc

            # Create recorder
            from ..meeting_capture_journal import MeetingCaptureJournal

            try:
                self._capture_journal = MeetingCaptureJournal(self._state.id)
            except Exception as exc:
                self._state.capture_status = "capture_failed"
                self._state.capture_failure = f"Audio journal unavailable: {exc}"
                get_database().meetings.save_meeting(self._state)
                raise RuntimeError(self._state.capture_failure) from exc

            self._recorder = MeetingRecorder(
                mic_device=self.mic_device,
                system_device=self.system_device,
                on_mic_level=self.on_mic_level,
                on_system_level=self.on_system_level,
                on_audio_chunk=lambda chunk: self._capture_journal.append(
                    chunk.source, chunk.audio
                ) if self._capture_journal is not None else None,
            )

            # Start recording
            try:
                self._recorder.start()
            except Exception as exc:
                self._state.capture_status = "capture_failed"
                self._state.capture_failure = str(exc)
                self._state.capture_checkpoint_at = datetime.now()
                get_database().meetings.save_meeting(self._state)
                raise
            self._state.capture_status = "recording"
            self._state.capture_failure = None
            self._state.capture_checkpoint_at = datetime.now()
            get_database().meetings.save_meeting(self._state)
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
                device_chunks = recorder.get_pending_device_chunks()
                # recorder.stop() returns ALL chunks from t=0. Filter to only
                # audio not yet processed by the transcription loop, using the
                # watermark it maintains. Without this, every stop re-transcribes
                # the entire recording, causing the "Stopping..." hang.
                cutoff = self._last_transcribe_time
                mic_chunks = [c for c in mic_chunks if c.timestamp >= cutoff]
                system_chunks = [c for c in system_chunks if c.timestamp >= cutoff]
                if mic_chunks or system_chunks or device_chunks:
                    self._transcribe_chunks(
                        mic_chunks,
                        system_chunks,
                        final=True,
                        device_chunks=device_chunks,
                    )
            except Exception as e:
                log.error(f"Error stopping recorder: {e}")

        with self._lock:
            state = self._state
            intel = self._intel
            diarizer = self._diarizer

        assert state is not None

        # HS-131-08 (Sol Amendment 2): stop CANCELS the live intelligence parent
        # first and then DURABLY enqueues the displaced final work before this
        # method returns. No final provider dispatch happens here any more —
        # final analysis, bookmark refinement, auto-title, and routed plugin work
        # all belong to a separately admitted `meeting.deferred-intel-job`.
        # Nothing may report readiness while that job is still outstanding.
        displaced = self._handoff_intel_at_stop(state)

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
        # HS-131-08: when the displaced-work handoff fired, the provider-backed
        # routing pass is the deferred job's (it runs the admitted plugin chain);
        # running it here as well would be an unadmitted post-close dispatch.
        if (
            not displaced
            and self.mir_routing_enabled
            and self._mir_plugin_host is not None
            and state.segments
        ):
            try:
                from ..plugins.pipeline import process_meeting_state as _mir_process

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
                    disabled_plugins=self._mir_disabled_plugins,
                    segment_probe=self._mir_segment_probe,
                    on_proposal=self._emit_actuator_proposal,
                )
                log.info(
                    "MIR routing finalized: "
                    f"windows={len(self._mir_last_result.windows)}, "
                    f"runs={len(self._mir_last_result.runs)}, "
                    f"errors={len(self._mir_last_result.errors)}"
                )
            except Exception as e:
                log.error(f"MIR routing finalization failed: {e}")

        # HS-93-06 fault plane: die between the last durable checkpoint and the
        # finalize transaction. Everything above already checkpointed; nothing
        # below may be required for recovery — restart must resume this same
        # Meeting identity from `capture_status="recording"` without a duplicate.
        from ..faults import kill_process as _fault_kill

        _fault_kill("meeting.finalize_kill")

        with self._lock:
            # Save speaker embeddings for cross-meeting recognition
            if self._diarizer is diarizer:
                self._diarizer = None

            # Clean up intel/runtime references
            self._intel = None
            self._intel_thread = None
            self._transcribe_thread = None
            self._current_analysis_id = None

            # Mark as ended
            self._state.ended_at = datetime.now()
            self._state.capture_status = "finalized"
            self._state.capture_failure = None
            self._state.capture_checkpoint_at = datetime.now()
            self._state.capture_checkpoint_seconds = self._state.duration
            final_state = self._state

        assert final_state is not None

        # Stop is itself a durable checkpoint; the later compatibility JSON and
        # aftercare work may fail without losing or duplicating the Meeting.
        journal_error: Optional[Exception] = None
        if self._capture_journal is not None:
            try:
                self._capture_journal.finalize()
            except Exception as exc:
                journal_error = exc

        if journal_error is not None:
            with self._lock:
                final_state.capture_status = "recoverable"
                final_state.capture_failure = f"Audio finalization failed: {journal_error}"
            log.error(final_state.capture_failure)
            if self._capture_journal is not None:
                self._capture_journal.mark_recoverable(final_state.capture_failure)
        try:
            from ..db import get_database

            get_database().meetings.save_meeting(final_state)
        except Exception as exc:
            with self._lock:
                final_state.capture_status = "recoverable"
                final_state.capture_failure = f"Final Meeting checkpoint failed: {exc}"
            log.error(final_state.capture_failure)

        # HS-131-08: the live parent was already cancelled and closed by the
        # handoff above. This close is the no-parent / never-admitted case only;
        # it can never turn a cancelled parent into a success.
        self._close_intel_session("succeeded")

        log.info(f"Meeting stopped: {final_state.id}, duration={final_state.format_duration()}")
        return final_state
