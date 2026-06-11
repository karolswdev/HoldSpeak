"""Web-first runtime bootstrap for HoldSpeak."""

from __future__ import annotations

import hashlib
import os
import signal
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np

from .audio import AudioRecorder
from .config import Config
from .audio import AudioSource
from .device_audio import DeviceRegistry, ensure_device_psk
from .web_auth import ensure_web_token
from .device_recording_tick import RecordingTicker
from .device_meeting_stats import pick_next_view
from .device_status import (
    DeviceStatusEmitter,
    push_intel_to_devices,
    push_segment_to_devices,
)
from .desktop_presence import DesktopPresenceHost, build_desktop_presence_host
from .dictation_runner import dispatch_voice_command, run_dictation_pipeline
from .hotkey import HotkeyListener
from .voice_typing import VoiceTypingSession
from .logging_config import get_logger
from .meeting_session import MeetingSession
from .plugins.router import (
    DEFAULT_INTENT_THRESHOLD,
    SUPPORTED_INTENTS,
    available_profiles,
    normalize_override_intents,
    normalize_profile,
    preview_route,
)
from .plugins.builtin import register_builtin_plugins
from .plugins.host import PluginHost, build_idempotency_key
from .plugins.project_detector import ProjectDetectorPlugin
from .plugins.queue import drain_plugin_run_queue, process_next_plugin_run_job
from .plugins.signals import extract_intent_signals
from .runtime_activity import RuntimeActivityTracker
from .text_processor import TextProcessor
from .transcribe import Transcriber
from .typer import TextTyper
from .web.runtime_support import _UnknownDeviceError
from .web_server import MeetingWebServer, WebRuntimeCallbacks

log = get_logger("web_runtime")

# HS-32-03: the owner string a meeting uses to hold the shared
# ``VoiceTypingSession`` audio floor. One arbiter for hotkey / device /
# meeting capture; while a meeting holds this, hotkey/device ``begin()``
# is rejected, and a meeting can't start while either holds the floor.
_MEETING_AUDIO_OWNER = "meeting"


def _configured_web_port_from_env() -> int | None:
    raw = os.environ.get("HOLDSPEAK_WEB_PORT")
    if raw is None or not raw.strip():
        return None
    try:
        port = int(raw)
    except ValueError:
        log.warning(f"Ignoring invalid HOLDSPEAK_WEB_PORT={raw!r}")
        return None
    if port <= 0 or port > 65535:
        log.warning(f"Ignoring out-of-range HOLDSPEAK_WEB_PORT={raw!r}")
        return None
    return port


def _dictation_corrections_repo():
    """The durable correction repository, or None if the DB is unavailable.

    HS-40-02: resolves the persistence repo for the live session correction
    store. Defensive — a DB failure must not stop the web runtime from booting;
    the store just falls back to in-memory.
    """
    try:
        from .db import get_database

        return get_database().dictation_corrections
    except Exception as exc:  # pragma: no cover - durability must never block boot
        log.warning(f"Dictation correction persistence unavailable: {exc}")
        return None


def _dictation_journal_repo():
    """The durable dictation-journal repository, or None if the DB is unavailable.

    HS-45-01: resolves the persistence repo for the live session journal
    recorder. Defensive — a DB failure must not stop the web runtime from
    booting; the recorder just becomes a no-op (no journaling, byte-identical).
    """
    try:
        from .db import get_database

        return get_database().dictation_journal
    except Exception as exc:  # pragma: no cover - durability must never block boot
        log.warning(f"Dictation journal persistence unavailable: {exc}")
        return None


class WebRuntime:
    """Web-first runtime: owns the web server, hotkey/device capture, the
    meeting session, and the MIR plugin pipeline.

    State that the old ``run_web_runtime()`` god-function threaded through
    ``nonlocal`` variables now lives on instance attributes; the inline
    closures are methods. ``run()`` performs startup, the keep-alive loop,
    and shutdown. This is the sole interactive runtime.
    """

    def __init__(
        self,
        *,
        no_open: bool = False,
        stop_event: Optional[threading.Event] = None,
        register_signal_handlers: bool = True,
    ) -> None:
        self.no_open = no_open
        self.register_signal_handlers = register_signal_handlers

        self.config = Config.load()
        self.runtime_started_at = datetime.now()
        self.runtime_stop_event = stop_event or threading.Event()
        self.state_lock = threading.Lock()
        self.meeting_lock = threading.Lock()
        self.bookmarks: list[dict[str, object]] = []
        self.pending_title: Optional[str] = None
        self.pending_tags: Optional[list[str]] = None
        self.last_meeting_snapshot: Optional[dict[str, object]] = None
        self.pending_intent_windows: list[dict[str, object]] = []
        self.pending_plugin_runs: list[dict[str, object]] = []
        self.preview_window_seq = 0
        self.mir_enabled = bool(getattr(self.config.meeting, "mir_enabled", False))
        self.mir_profile = normalize_profile(getattr(self.config.meeting, "mir_profile", None))
        self.mir_override_intents: list[str] = []
        self.last_route_preview: Optional[dict[str, object]] = None
        self.runtime_url: Optional[str] = None

        self.hotkey_listener: Optional[HotkeyListener] = None
        self.recorder: Optional[AudioRecorder] = None
        self.transcriber: Optional[Transcriber] = None
        self.server: Optional[MeetingWebServer] = None
        self.meeting_session: Optional[MeetingSession] = None
        # HS-41-03/04: the opt-in desktop presence host (None unless
        # HOLDSPEAK_DESKTOP_PRESENCE=1 and a native renderer is available). The
        # url_provider is read lazily (the macOS renderer loads <url>/presence on
        # first show), so it resolves after the server has a port.
        self.desktop_presence: Optional[DesktopPresenceHost] = build_desktop_presence_host(
            url_provider=lambda: self.runtime_url,
            config_enabled=self._presence_config_enabled(),
        )
        self.device_registry = DeviceRegistry()
        self.device_status = DeviceStatusEmitter(label_lookup=self.device_registry)
        # HS-17-05: periodic Recording-tick emitter for attached devices.
        # Started in `_start_meeting`, stopped in `_stop_active_meeting`.
        self.recording_ticker = RecordingTicker(
            status_sender=lambda ids, text: self.device_status.broadcast(
                ids, text, ttl_ms=0
            ),
        )
        self.voice_session = VoiceTypingSession()
        self.transcription_lock = threading.Lock()
        self.text_processor = TextProcessor(
            spoken_symbols=getattr(self.config.dictation, "spoken_symbols", [])
        )
        self.activity_tracker = RuntimeActivityTracker()
        from .activity_context import ActivityContextProvider

        # HS-16-02: enable the "llm" plugin capability iff a meeting-intel
        # provider resolves. Without this, LLM-backed plugins (e.g.
        # mermaid_architecture) always block; resolution failure is non-fatal
        # — they just stay blocked.
        from .intel import resolve_llm_capability

        self.llm_capability_enabled = resolve_llm_capability(self.config.meeting)
        log.info(f"intel.llm_capability enabled={self.llm_capability_enabled}")

        self.plugin_host = PluginHost(
            default_timeout_seconds=0.35,
            enabled_capabilities={"llm"} if self.llm_capability_enabled else None,
        )
        self.plugin_host.register_context_provider(
            ActivityContextProvider(refresh=True, refresh_once=True)
        )
        register_builtin_plugins(self.plugin_host)

        # Project knowledge-base detector (runs first in every chain)
        self.project_detector = ProjectDetectorPlugin()
        try:
            from .db import get_database as _get_db_for_projects

            self.project_detector.reload_projects(
                _get_db_for_projects().projects.get_all_projects_for_detector()
            )
        except Exception as _proj_init_err:
            log.warning(f"Could not load projects for detector at startup: {_proj_init_err}")
        self.plugin_host.register(self.project_detector)

        # HS-35-02: discover + register plugin packs (first-party + local user
        # packs from ~/.holdspeak/plugin_packs/) alongside the built-ins. The
        # 14 built-ins are unchanged; packs only augment the host registry.
        # Discovery is fully defensive — a bad pack surfaces a logged error and
        # never crashes startup.
        try:
            from .plugin_pack_loader import load_and_register_plugin_packs

            builtin_ids = frozenset(self.plugin_host.list_plugins())
            registered_packs, pack_errors = load_and_register_plugin_packs(
                self.plugin_host, forbidden_ids=builtin_ids
            )
            for pack_error in pack_errors:
                log.warning(f"plugin pack discovery: {pack_error}")
            if registered_packs:
                log.info(f"registered plugin packs: {registered_packs}")
        except Exception as _pack_err:
            log.warning(f"plugin pack discovery failed: {_pack_err}")

        self.plugin_queue_thread: Optional[threading.Thread] = None

        try:
            self.typer: Optional[TextTyper] = TextTyper()
            self.text_injection_enabled = True
        except Exception as exc:
            self.typer = None
            self.text_injection_enabled = False
            log.warning(f"Text injection unavailable in web mode: {exc}")

        self.runtime_status: dict[str, object] = {
            "voice_state": "idle",
            "last_transcription": "",
            "last_error": "",
            "transcription_model": self.config.model.name,
            "transcription_warm_on_start": bool(getattr(self.config.model, "warm_on_start", True)),
            "transcription_status": "not_loaded",
            "transcription_error": "",
            "global_hotkey_available": False,
            "global_hotkey_error": "",
            "text_injection_enabled": self.text_injection_enabled,
            "text_injection_error": "" if self.text_injection_enabled else "TextTyper unavailable",
            "activity": self.activity_tracker.snapshot(),
        }

        # AIPI-4-14: per-device cycle index for the meeting-stats double-tap
        # rotation. ``-1`` means "advance to view 0 on the next double-tap".
        # Reset whenever a meeting ends so each new meeting starts at view 0.
        self.device_stats_cycle: dict[str, int] = {}

    def _transcription_warm_on_start_enabled(self) -> bool:
        return bool(getattr(self.config.model, "warm_on_start", True))

    def _set_transcription_status(self, status: str, *, error: str = "") -> None:
        with self.state_lock:
            self.runtime_status["transcription_model"] = self.config.model.name
            self.runtime_status["transcription_warm_on_start"] = self._transcription_warm_on_start_enabled()
            self.runtime_status["transcription_status"] = status
            self.runtime_status["transcription_error"] = error
        if status == "warming":
            self._set_runtime_activity(
                "processing",
                source="runtime",
                label="Warming model",
                detail=f"Preparing transcription model {self.config.model.name}.",
                last_event="transcription_warming",
                last_error="",
            )
        elif status == "loading":
            self._set_runtime_activity(
                "processing",
                source="runtime",
                label="Loading model",
                detail=f"Loading transcription model {self.config.model.name}.",
                last_event="transcription_loading",
                last_error="",
            )
        elif status == "error":
            self._set_runtime_activity(
                "error",
                source="runtime",
                detail="Transcription model unavailable.",
                last_event="transcription_status_error",
                last_error=error,
            )

    def _ensure_transcriber_loaded(self) -> Transcriber:
        if self.transcriber is None or getattr(self.transcriber, "model_name", None) != self.config.model.name:
            self._set_transcription_status("loading")
            try:
                self.transcriber = Transcriber(
                    model_name=self.config.model.name,
                    backend=self.config.model.backend,
                    language=getattr(self.config.model, "language", "auto"),
                )
            except Exception as exc:
                self._set_transcription_status("error", error=f"{type(exc).__name__}: {exc}")
                raise
        self._set_transcription_status("loaded")
        return self.transcriber

    def _warm_transcriber_in_background(self) -> None:
        if not self._transcription_warm_on_start_enabled():
            return

        def _warm() -> None:
            with self.transcription_lock:
                try:
                    self._ensure_transcriber_loaded()
                except Exception as exc:
                    self._set_transcription_status("error", error=f"{type(exc).__name__}: {exc}")
                    with self.state_lock:
                        self.runtime_status["last_error"] = f"Transcription warmup failed: {exc}"
                    log.error(f"Transcription warmup failed: {exc}", exc_info=True)

        self._set_transcription_status("warming")
        threading.Thread(
            target=_warm,
            name="HoldSpeakTranscriptionWarmup",
            daemon=True,
        ).start()

    def _active_meeting_session(self) -> Optional[MeetingSession]:
        with self.meeting_lock:
            session = self.meeting_session
        if session is None or not session.is_active:
            return None
        return session

    def _broadcast_runtime_activity(self, activity: dict[str, object]) -> None:
        # Fan the activity snapshot out to: (1) the opt-in desktop presence host
        # (HS-41-03 — None unless HOLDSPEAK_DESKTOP_PRESENCE=1 and a native
        # renderer is available), and (2) web clients over the websocket.
        if self.desktop_presence is not None:
            try:
                self.desktop_presence.handle_activity(activity)
            except Exception as exc:
                log.debug(f"Desktop presence update failed: {exc}")
        if self.server is None:
            return
        try:
            self.server.broadcast("runtime_activity", activity)
        except Exception as exc:
            log.debug(f"Failed to broadcast runtime_activity: {exc}")

    def _set_runtime_activity(
        self,
        state: str,
        *,
        source: str = "runtime",
        label: Optional[str] = None,
        detail: str = "",
        last_event: str = "",
        last_error: Optional[str] = None,
    ) -> dict[str, object]:
        with self.state_lock:
            activity = self.activity_tracker.update(
                state,
                source=source,
                label=label,
                detail=detail,
                last_event=last_event,
                last_error=last_error,
            )
            self.runtime_status["activity"] = activity
        self._broadcast_runtime_activity(activity)
        return activity

    def _set_voice_state(
        self,
        value: str,
        *,
        source: str = "voice",
        detail: str = "",
        last_event: str = "",
        last_error: Optional[str] = None,
        update_activity: bool = True,
    ) -> None:
        with self.state_lock:
            self.runtime_status["voice_state"] = value
        if not update_activity:
            return
        activity_state = value if value in {"idle", "recording", "transcribing"} else "processing"
        self._set_runtime_activity(
            activity_state,
            source=source,
            detail=detail,
            last_event=last_event,
            last_error=last_error,
        )

    def _normalize_tags(self, tags: Optional[list[str]]) -> list[str]:
        if not isinstance(tags, list):
            return []
        return [str(tag).strip().lower() for tag in tags if str(tag).strip()]

    def _meeting_summary_from_state(self, state: dict[str, object]) -> Optional[dict[str, object]]:
        if not bool(state.get("meeting_active")):
            return None
        meeting_id = state.get("id")
        if not isinstance(meeting_id, str) or not meeting_id:
            return None
        return {
            "id": meeting_id,
            "title": state.get("title"),
            "tags": state.get("tags") if isinstance(state.get("tags"), list) else [],
            "started_at": state.get("started_at"),
            "ended_at": state.get("ended_at"),
            "duration": state.get("duration"),
            "formatted_duration": state.get("formatted_duration"),
        }

    def _mir_controls_payload(self) -> dict[str, object]:
        with self.state_lock:
            return {
                "enabled": bool(self.mir_enabled),
                "profile": str(self.mir_profile),
                "available_profiles": available_profiles(),
                "supported_intents": list(SUPPORTED_INTENTS),
                "override_intents": list(self.mir_override_intents),
                "last_preview": dict(self.last_route_preview) if isinstance(self.last_route_preview, dict) else None,
                "threshold": float(DEFAULT_INTENT_THRESHOLD),
            }

    def _runtime_idle_state(self) -> dict[str, object]:
        runtime_uptime = max(0.0, (datetime.now() - self.runtime_started_at).total_seconds())
        with self.state_lock:
            idle_title = self.pending_title or ""
            idle_tags = list(self.pending_tags) if self.pending_tags is not None else []
            runtime_snapshot = dict(self.runtime_status)
            mir_snapshot = {
                "enabled": bool(self.mir_enabled),
                "profile": str(self.mir_profile),
                "available_profiles": available_profiles(),
                "supported_intents": list(SUPPORTED_INTENTS),
                "override_intents": list(self.mir_override_intents),
                "last_preview": dict(self.last_route_preview) if isinstance(self.last_route_preview, dict) else None,
                "threshold": float(DEFAULT_INTENT_THRESHOLD),
            }

        return {
            "id": "web-runtime",
            "mode": "web",
            "meeting_active": False,
            "meeting_id": None,
            "started_at": None,
            "ended_at": None,
            "duration": 0.0,
            "formatted_duration": "00:00",
            "title": idle_title,
            "tags": idle_tags,
            "web_url": self.runtime_url,
            "runtime_started_at": self.runtime_started_at.isoformat(),
            "runtime_uptime": runtime_uptime,
            "bookmarks": list(self.bookmarks),
            "segments": [],
            "topics": [],
            "action_items": [],
            "summary": "",
            "intel_status": {
                "state": "idle",
                "detail": "No meeting active. Start a meeting from web controls.",
                "requested_at": None,
                "completed_at": None,
            },
            "mir": mir_snapshot,
            "runtime": runtime_snapshot,
            "activity": runtime_snapshot.get("activity") if isinstance(runtime_snapshot.get("activity"), dict) else {},
        }

    def _get_state(self) -> dict[str, object]:
        session = self._active_meeting_session()
        if session is None:
            return self._runtime_idle_state()

        state = session.state
        if state is None:
            return self._runtime_idle_state()

        payload = state.to_dict()
        payload["mode"] = "web"
        payload["meeting_active"] = session.is_active
        payload["meeting_id"] = payload.get("id")
        payload["runtime_started_at"] = self.runtime_started_at.isoformat()
        payload["runtime_uptime"] = max(0.0, (datetime.now() - self.runtime_started_at).total_seconds())
        if self.runtime_url and not payload.get("web_url"):
            payload["web_url"] = self.runtime_url
        with self.state_lock:
            payload["runtime"] = dict(self.runtime_status)
            payload["activity"] = (
                dict(self.runtime_status["activity"])
                if isinstance(self.runtime_status.get("activity"), dict)
                else {}
            )
        payload["mir"] = self._mir_controls_payload()
        return payload

    def _broadcast_intel_status(self) -> None:
        if self.server is None:
            return
        state = self._get_state()
        intel_status = state.get("intel_status")
        if intel_status is not None:
            self.server.broadcast("intel_status", intel_status)

    def _on_meeting_segment(self, segment) -> None:
        try:
            speaker = str(getattr(segment, "speaker", "") or "Speaker")
            text = str(getattr(segment, "text", "") or "").strip()
            detail = f"{speaker}: {text}" if text else "Transcript segment captured."
            self._set_runtime_activity(
                "meeting_live",
                source="meeting",
                label="Segment captured",
                detail=detail[:220],
                last_event="meeting_segment",
                last_error="",
            )
        except Exception as exc:
            log.debug(f"Failed to map meeting segment activity: {exc}")
        if self.server is not None:
            try:
                self.server.broadcast("segment", segment.to_dict())
            except Exception as exc:
                log.debug(f"Failed to broadcast segment: {exc}")
        # HS-17-08: push each finalized segment to attached AIPI-Lite
        # devices as a 3s flash so the LCD reflects what's being
        # transcribed in real time. No-op when no devices attached.
        try:
            active = self._active_meeting_session()
            if active is not None and active.state is not None:
                attached_ids = [d.id for d in active.state.devices]
                push_segment_to_devices(self.device_status, attached_ids, segment)
        except Exception as exc:
            log.debug(f"Failed to push segment to device LCD: {exc}")

    def _on_meeting_intel(self, intel) -> None:
        self._set_runtime_activity(
            "complete",
            source="meeting",
            label="Intel ready",
            detail="Meeting intelligence finished.",
            last_event="meeting_intel_complete",
            last_error="",
        )
        if self.server is not None:
            try:
                self.server.broadcast("intel_complete", intel.to_dict())
            except Exception as exc:
                log.debug(f"Failed to broadcast intel_complete: {exc}")
        self._broadcast_intel_status()
        # HS-17-07: push the intel summary to attached AIPI-Lite LCDs
        # so the user gets visible feedback when intel finishes (topics,
        # actions, summary — all landed in the middle slot).
        try:
            active = self._active_meeting_session()
            if active is not None and active.state is not None:
                attached_ids = [d.id for d in active.state.devices]
                push_intel_to_devices(self.device_status, attached_ids, intel)
        except Exception as exc:
            log.debug(f"Failed to push intel to device LCD: {exc}")

    # Events the meeting session emits that have a *dedicated* runtime path
    # already (`_on_meeting_segment` / `_on_meeting_intel` broadcast these,
    # and also drive the device LCDs). Forwarding them again from the generic
    # `on_broadcast` seam would double-broadcast, so they are filtered out.
    _BROADCAST_VIA_DEDICATED_HANDLER = frozenset({"segment", "intel_complete", "intel_status"})

    def _on_meeting_broadcast(self, message_type: str, data: object) -> None:
        """Observe live events `MeetingSession` emits (HS-32-02 inversion).

        The session no longer reaches into a web server; it emits, and the
        runtime forwards to its broadcast channel. ``segment`` /
        ``intel_complete`` / ``intel_status`` already flow via the dedicated
        ``on_segment`` / ``on_intel`` handlers, so only ``intel_token`` and
        ``meeting_updated`` — previously delivered solely to the now-removed
        embedded per-meeting server, and dead in the flagship runtime — are
        forwarded here.
        """
        if message_type in self._BROADCAST_VIA_DEDICATED_HANDLER:
            return
        self._map_meeting_broadcast_activity(message_type, data)
        if self.server is None:
            return
        try:
            self.server.broadcast(message_type, data)
        except Exception as exc:
            log.debug(f"Failed to forward meeting broadcast {message_type!r}: {exc}")

    def _map_meeting_broadcast_activity(self, message_type: str, data: object) -> None:
        if message_type == "intel_token":
            self._set_runtime_activity(
                "processing",
                source="meeting",
                label="Intel streaming",
                detail="Meeting intelligence is streaming.",
                last_event="meeting_intel_streaming",
                last_error="",
            )
            return
        if message_type == "actuator_proposed":
            label = "Action proposed"
            detail = "An actuator proposed an external action."
            if isinstance(data, dict):
                title = str(data.get("title") or data.get("preview") or "").strip()
                target = str(data.get("target") or "").strip()
                if title and target:
                    detail = f"{target}: {title}"
                elif title:
                    detail = title
            self._set_runtime_activity(
                "complete",
                source="meeting",
                label=label,
                detail=detail[:220],
                last_event="actuator_proposed",
                last_error="",
            )

    def _apply_updated_config(self, updated_config: Config) -> None:
        previous_model = self.config.model.name
        self.config = updated_config
        model_changed = self.transcriber is not None and getattr(self.transcriber, "model_name", None) != self.config.model.name
        if model_changed:
            self.transcriber = None
        if previous_model != self.config.model.name or model_changed:
            self._set_transcription_status("not_loaded")
        else:
            self._set_transcription_status(
                "loaded" if self.transcriber is not None else "not_loaded",
                error="",
            )
        self._warm_transcriber_in_background()
        if self.hotkey_listener is not None:
            try:
                self.hotkey_listener.hotkey = self.config.hotkey.key
            except Exception as exc:
                log.debug(f"Failed to apply runtime hotkey update: {exc}")
        if self.recorder is not None:
            self.recorder.device = self.config.meeting.mic_device
        self._sync_desktop_presence()

    def _presence_config_enabled(self) -> bool:
        """`config.presence.enabled`, defensively (a config without the field = off)."""
        return bool(getattr(getattr(self.config, "presence", None), "enabled", False))

    def _sync_desktop_presence(self) -> None:
        """HS-43-04: start/stop the presence host live when the config toggle flips.

        Lets the UI switch presence on/off with no env var and no relaunch. Fully
        defensive — a renderer that can't construct (e.g. headless) just leaves the
        host None, and an error never disrupts the runtime.
        """
        from .desktop_presence import desktop_presence_enabled

        want = desktop_presence_enabled(config_enabled=self._presence_config_enabled())
        have = self.desktop_presence is not None
        if want == have:
            return
        try:
            if want:
                self.desktop_presence = build_desktop_presence_host(
                    url_provider=lambda: self.runtime_url,
                    config_enabled=True,
                )
            else:
                if self.desktop_presence is not None:
                    self.desktop_presence.close()
                self.desktop_presence = None
        except Exception as exc:  # pragma: no cover - presence must never disrupt
            log.warning(f"Failed to apply desktop-presence toggle: {exc}")

    def _start_meeting(self, *, devices: Optional[list[str]] = None) -> dict[str, object]:
        if self._active_meeting_session() is not None:
            raise RuntimeError("Meeting already active")

        # Validate every requested device id is currently registered
        # *before* spinning up a session — surfaces 404 to the caller
        # without leaving an empty meeting on disk.
        device_pairs: list[tuple[object, object]] = []  # (descriptor, source)
        if devices:
            for device_id in devices:
                descriptor = self.device_registry.get(device_id)
                if descriptor is None:
                    raise _UnknownDeviceError(device_id)
                source = self.device_registry.recorder_for(device_id)
                if source is None:
                    raise _UnknownDeviceError(device_id)
                device_pairs.append((descriptor, source))

        if self.transcriber is None or getattr(self.transcriber, "model_name", None) != self.config.model.name:
            self.transcriber = self._ensure_transcriber_loaded()

        # HS-32-03: claim the shared audio floor before opening any recorder, so
        # a hotkey/device voice-typing session can't already hold the mic (and so
        # one can't grab it while the meeting runs). Released in
        # `_stop_active_meeting` / shutdown; released here if start-up fails
        # before the meeting is registered.
        if not self.voice_session.acquire(_MEETING_AUDIO_OWNER):
            raise RuntimeError(
                f"Cannot start meeting: audio floor held by {self.voice_session.active_owner!r}"
            )
        # HS-36-05: build the LLM-assisted per-segment intent probe only when the
        # config knob is on. Defensive: any failure to construct it (missing optional
        # deps, unconfigured endpoint) leaves it None and routing falls back to the
        # lexical path — meeting start must never break on this.
        segment_probe = None
        if getattr(self.config.meeting, "intent_segment_probe_enabled", False):
            try:
                from .plugins.segment_probe import build_segment_probe

                segment_probe = build_segment_probe()
            except Exception:
                log.warning("segment intent probe unavailable; using lexical scoring", exc_info=True)
                segment_probe = None

        try:
            session = MeetingSession(
                transcriber=self.transcriber,
                mic_label=self.config.meeting.mic_label,
                remote_label=self.config.meeting.remote_label,
                mic_device=self.config.meeting.mic_device,
                system_device=self.config.meeting.system_audio_device,
                on_segment=self._on_meeting_segment,
                on_mic_level=lambda _level: None,
                on_system_level=lambda _level: None,
                on_intel=self._on_meeting_intel,
                on_settings_applied=self._apply_updated_config,
                on_broadcast=self._on_meeting_broadcast,
                intel_enabled=self.config.meeting.intel_enabled,
                intel_model_path=self.config.meeting.intel_realtime_model,
                intel_provider=self.config.meeting.intel_provider,
                intel_cloud_model=self.config.meeting.intel_cloud_model,
                intel_cloud_api_key_env=self.config.meeting.intel_cloud_api_key_env,
                intel_cloud_base_url=self.config.meeting.intel_cloud_base_url,
                intel_cloud_reasoning_effort=self.config.meeting.intel_cloud_reasoning_effort,
                intel_cloud_store=self.config.meeting.intel_cloud_store,
                intel_deferred_enabled=self.config.meeting.intel_deferred_enabled,
                diarization_enabled=self.config.meeting.diarization_enabled,
                diarize_mic=self.config.meeting.diarize_mic,
                cross_meeting_recognition=self.config.meeting.cross_meeting_recognition,
                mir_disabled_plugins=list(
                    getattr(self.config.meeting, "disabled_plugins", []) or []
                ),
                mir_segment_probe=segment_probe,
            )
            state = session.start()
            with self.state_lock:
                title_override = self.pending_title
                tags_override = list(self.pending_tags) if self.pending_tags is not None else None
                self.pending_title = None
                self.pending_tags = None
            if title_override is not None:
                session.set_title(title_override)
                state = session.state or state
            if tags_override is not None:
                session.set_tags(tags_override)
                state = session.state or state
            if self.runtime_url:
                state.web_url = self.runtime_url

            attached_ids: list[str] = []
            for descriptor, source in device_pairs:
                try:
                    session.attach_device(descriptor, source)  # type: ignore[arg-type]
                    attached_ids.append(getattr(descriptor, "id", ""))
                except Exception as exc:
                    log.error(f"Failed to attach device {getattr(descriptor, 'id', '?')}: {exc}")
                    # Best effort: continue with whatever attached successfully.
                    # The descriptors that *did* attach remain on state.devices.
                    continue

            with self.meeting_lock:
                self.meeting_session = session
        except Exception:
            # Roll back the floor claim if the meeting never came up.
            self.voice_session.release(_MEETING_AUDIO_OWNER)
            self._set_runtime_activity(
                "error",
                source="meeting",
                detail="Meeting start failed.",
                last_event="meeting_start_failed",
                last_error="Meeting start failed",
            )
            raise

        if attached_ids:
            attached_for_status = [d for d in attached_ids if d]
            self.device_status.broadcast(
                attached_for_status,
                "Recording 00:00",
                ttl_ms=0,
            )
            # HS-17-05: schedule the periodic Recording-tick. The 0:00
            # paint above is done synchronously; subsequent ticks fire
            # every 5 s on a daemon thread that exits cleanly on
            # `_stop_active_meeting`.
            self.recording_ticker.start(
                started_at_monotonic=time.monotonic(),
                device_ids=attached_for_status,
            )
        with self.state_lock:
            self.pending_intent_windows.clear()
            self.pending_plugin_runs.clear()
            self.preview_window_seq = 0
        with self.state_lock:
            self.runtime_status["last_error"] = ""
        self._set_runtime_activity(
            "meeting_live",
            source="meeting",
            detail="Meeting recording is live.",
            last_event="meeting_started",
            last_error="",
        )

        self._broadcast_intel_status()
        return state.to_dict()

    def _stop_active_meeting(self, *, allow_runtime_fallback: bool) -> dict[str, object]:
        session = self._active_meeting_session()
        if session is None:
            if allow_runtime_fallback:
                self.runtime_stop_event.set()
                return {"status": "stopping_runtime"}
            raise RuntimeError("No active meeting")

        # HS-14-07: notify any attached devices that we are about to
        # stop and persist. Captured *before* ``session.stop`` flips
        # the state and clears the device list.
        attached_ids = [d.id for d in session.state.devices] if session.state else []
        # HS-17-05: stop the Recording-tick *before* the
        # `Saving meeting...` broadcast so a stale tick can't land
        # after the user has been told the meeting is saving.
        self.recording_ticker.stop()
        # AIPI-4-14: reset per-device cycle indexes so the next meeting
        # starts the double-tap rotation back at view 0.
        self.device_stats_cycle.clear()
        if attached_ids:
            self.device_status.broadcast(attached_ids, "Saving meeting...", ttl_ms=0)
        self._set_runtime_activity(
            "saving",
            source="meeting",
            detail="Stopping and saving meeting.",
            last_event="meeting_saving",
            last_error="",
        )

        final_state = session.stop()
        # HS-32-03: the meeting's recorder is now closed — release the shared
        # audio floor immediately (before the slower save/intel work, none of
        # which touches the mic) so hotkey/device voice typing can resume.
        self.voice_session.release(_MEETING_AUDIO_OWNER)
        final_state_payload = final_state.to_dict()
        meeting_id = str(final_state_payload.get("id") or "")
        with self.state_lock:
            self.last_meeting_snapshot = dict(final_state_payload)
        save_error: Optional[str] = None
        save_payload = {
            "database_saved": False,
            "json_saved": False,
            "json_path": None,
            "intel_job_enqueued": False,
            "intent_windows_saved": 0,
            "plugin_runs_saved": 0,
            "mir_save_error": None,
            "artifacts_saved": 0,
            "artifact_synthesis_error": None,
        }
        queue_flush_error: Optional[str] = None
        try:
            queue_flush = self._flush_deferred_plugin_runs_to_db()
            queue_flush_error = str(queue_flush.get("error") or "") or None
            save_result = session.save()
            save_payload = {
                "database_saved": bool(save_result.database_saved),
                "json_saved": bool(save_result.json_saved),
                "json_path": str(save_result.json_path) if save_result.json_path else None,
                "intel_job_enqueued": bool(save_result.intel_job_enqueued),
                "intent_windows_saved": 0,
                "plugin_runs_saved": 0,
                "mir_save_error": None,
                "artifacts_saved": 0,
                "artifact_synthesis_error": None,
                "projects_associated": 0,
                "project_association_error": None,
                "deferred_queue_jobs": int(queue_flush.get("queued_jobs") or 0),
                "deferred_queue_error": queue_flush_error,
            }
            if meeting_id:
                mir_history = self._persist_pending_mir_history(meeting_id)
                save_payload["intent_windows_saved"] = int(mir_history.get("intent_windows_saved") or 0)
                save_payload["plugin_runs_saved"] = int(mir_history.get("plugin_runs_saved") or 0)
                save_payload["mir_save_error"] = mir_history.get("error")
                artifacts_result = self._synthesize_and_persist_artifacts(meeting_id)
                save_payload["artifacts_saved"] = int(artifacts_result.get("artifacts_saved") or 0)
                save_payload["artifact_synthesis_error"] = artifacts_result.get("error")
                project_result = self._associate_meeting_with_projects(meeting_id)
                save_payload["projects_associated"] = int(project_result.get("projects_associated") or 0)
                save_payload["project_association_error"] = project_result.get("error")
        except Exception as exc:
            save_error = str(exc)
            log.error(f"Failed to save meeting from web runtime: {exc}")

        with self.meeting_lock:
            if self.meeting_session is session:
                self.meeting_session = None

        with self.state_lock:
            self.runtime_status["last_error"] = save_error or ""
        if save_error:
            self._set_runtime_activity(
                "error",
                source="meeting",
                detail="Meeting save failed.",
                last_event="meeting_save_failed",
                last_error=save_error,
            )
        else:
            self._set_runtime_activity(
                "complete",
                source="meeting",
                label="Saved",
                detail="Meeting saved.",
                last_event="meeting_saved",
                last_error="",
            )

        return {
            "status": "stopped",
            "meeting": final_state_payload,
            "save": save_payload,
            "save_error": save_error,
        }

    def _flush_deferred_plugin_runs_to_db(self) -> dict[str, object]:
        """Persist host-deferred heavy plugin jobs into DB queue storage."""
        queued_jobs = 0
        flush_error: Optional[str] = None
        try:
            from .db import get_database

            db = get_database()
            while True:
                queued_run = self.plugin_host.pop_next_deferred_run()
                if queued_run is None:
                    break
                db.plugins.enqueue_plugin_run_job(
                    meeting_id=queued_run.meeting_id,
                    window_id=queued_run.window_id,
                    plugin_id=queued_run.plugin_id,
                    plugin_version=queued_run.plugin_version,
                    transcript_hash=queued_run.transcript_hash,
                    idempotency_key=queued_run.idempotency_key,
                    context=queued_run.context,
                )
                queued_jobs += 1
        except Exception as exc:
            flush_error = str(exc)
            log.error(f"Failed to persist deferred plugin queue: {exc}")

        return {"queued_jobs": queued_jobs, "error": flush_error}

    def _process_deferred_plugin_queue_once(self, *, include_scheduled: bool = False) -> bool:
        """Run one deferred MIR queue job if available."""
        if self._active_meeting_session() is not None:
            return False
        try:
            from .db import get_database

            db = get_database()
            return process_next_plugin_run_job(
                host=self.plugin_host,
                db=db,
                include_scheduled=include_scheduled,
            )
        except Exception as exc:
            log.error(f"Deferred MIR queue processing failed: {exc}")
            return False

    def _process_deferred_plugin_queue(
        self,
        *,
        max_jobs: Optional[int] = None,
        include_scheduled: bool = False,
    ) -> dict[str, object]:
        """Drain deferred MIR queue through runtime-owned plugin host."""
        if self._active_meeting_session() is not None:
            return {"processed": 0, "skipped_active_meeting": True}
        try:
            from .db import get_database

            db = get_database()
            processed = drain_plugin_run_queue(
                host=self.plugin_host,
                db=db,
                max_jobs=max_jobs,
                include_scheduled=include_scheduled,
            )
            return {"processed": int(processed), "skipped_active_meeting": False}
        except Exception as exc:
            log.error(f"Deferred MIR queue drain failed: {exc}")
            return {
                "processed": 0,
                "skipped_active_meeting": False,
                "error": str(exc),
            }

    def _deferred_plugin_queue_loop(self) -> None:
        while not self.runtime_stop_event.is_set():
            processed = self._process_deferred_plugin_queue_once()
            if processed:
                continue
            self.runtime_stop_event.wait(0.6)

    def _get_runtime_status(self) -> dict[str, object]:
        state = self._get_state()
        runtime = state.get("runtime") if isinstance(state.get("runtime"), dict) else {}
        meeting_active = bool(state.get("meeting_active"))
        meeting = self._meeting_summary_from_state(state)
        with self.state_lock:
            last_meeting = dict(self.last_meeting_snapshot) if isinstance(self.last_meeting_snapshot, dict) else None
            runtime_snapshot = dict(self.runtime_status)
        return {
            "status": "ok",
            "mode": "web",
            "url": self.runtime_url,
            "meeting_active": meeting_active,
            "meeting_id": state.get("id") if meeting_active else None,
            "meeting": meeting,
            "last_meeting": last_meeting,
            "voice_state": runtime.get("voice_state", runtime_snapshot.get("voice_state", "idle")),
            "activity": runtime_snapshot.get("activity") if isinstance(runtime_snapshot.get("activity"), dict) else {},
            "text_injection_enabled": runtime_snapshot.get("text_injection_enabled"),
            "text_injection_error": runtime_snapshot.get("text_injection_error", ""),
            "llm_capability_enabled": self.llm_capability_enabled,
            "transcription": {
                "model": runtime_snapshot.get("transcription_model", self.config.model.name),
                "warm_on_start": runtime_snapshot.get("transcription_warm_on_start", False),
                "status": runtime_snapshot.get("transcription_status", "not_loaded"),
                "error": runtime_snapshot.get("transcription_error", ""),
            },
            "intel_egress": self._intel_egress_payload(),
            "mir": self._mir_controls_payload(),
            "state": state,
        }

    def _intel_egress_payload(self) -> dict[str, object]:
        """Egress posture for the web intel-status surface (HS-25-01).

        Lets the UI state plainly whether transcripts can leave the machine
        without anyone reading logs.
        """
        from .intel import intel_egress_posture

        meeting = self.config.meeting
        if not meeting.intel_enabled:
            return {
                "enabled": False,
                "provider": meeting.intel_provider,
                "can_transmit_offmachine": False,
                "egress": "Disabled — no transcript leaves this machine.",
            }
        can_transmit, description = intel_egress_posture(meeting.intel_provider)
        return {
            "enabled": True,
            "provider": meeting.intel_provider,
            "can_transmit_offmachine": can_transmit,
            "egress": description,
        }

    def _print_setup_nudge(self) -> None:
        """HS-42-03: point a first-run or hard-blocked user at /setup on launch.

        Uses the cheap (`skip_network`) setup-status read so it never delays
        startup, and is fully defensive — a status failure prints nothing and
        never blocks the runtime. A healthy returning user gets no nudge.
        """
        try:
            from .db import get_database
            from .setup_status import build_setup_status

            setup = build_setup_status(database=get_database())
            url = self.runtime_url
            unmet = sum(
                1 for s in setup.get("sections", []) if s.get("status") in ("fail", "warn")
            )
            if setup.get("first_run"):
                # HS-43-06: a brand-new user gets the guided wizard.
                print(f"  → Welcome! Get set up in a minute: open {url}/welcome")
            elif setup.get("overall") == "blocked":
                suffix = f" — {unmet} thing{'' if unmet == 1 else 's'} need{'s' if unmet == 1 else ''} attention" if unmet else ""
                print(f"  → Setup needs attention: open {url}/setup{suffix}")
                action = (setup.get("primary_action") or {}).get("label")
                if action:
                    print(f"    Next: {action}")
            elif setup.get("overall") == "needs_attention":
                print(f"  → Setup ready (some optional items to review): {url}/setup")
        except Exception as exc:  # pragma: no cover - a nudge must never block boot
            log.debug(f"setup nudge skipped: {exc}")

    def _mark_first_dictation(self) -> None:
        """HS-42-04: record the durable first-dictation milestone on a real,
        successful dictation (text delivered to an agent session or typed into
        the active app). This flips `first_run` false so the `/setup` welcome no
        longer fronts the dashboard. Idempotent (the runtime sets it at most once)
        and fully defensive — a DB hiccup never disrupts dictation.
        """
        if getattr(self, "_first_dictation_marked", False):
            return
        try:
            from .db import FIRST_DICTATION_SUCCESS, get_database

            get_database().milestones.mark(FIRST_DICTATION_SUCCESS)
            self._first_dictation_marked = True
        except Exception as exc:  # pragma: no cover - never block dictation
            log.debug(f"first-dictation milestone not recorded: {exc}")

    def _on_bookmark(self, label: str) -> dict[str, object]:
        session = self._active_meeting_session()
        if session is not None:
            bookmark = session.add_bookmark(label=label, auto_label=not bool(label))
            if bookmark is not None:
                attached_ids = [d.id for d in session.state.devices] if session.state else []
                if attached_ids:
                    self.device_status.broadcast(
                        attached_ids,
                        f"Bookmark @ {bookmark.timestamp:.0f}s",
                        ttl_ms=2500,
                    )
                return bookmark.to_dict()
            raise RuntimeError("No active meeting")

        entry = {
            "timestamp": max(0.0, (datetime.now() - self.runtime_started_at).total_seconds()),
            "label": label or "",
        }
        with self.state_lock:
            self.bookmarks.append(entry)
        return entry

    def _on_stop(self) -> dict[str, object]:
        return self._stop_active_meeting(allow_runtime_fallback=True)

    def _on_meeting_stop(self) -> dict[str, object]:
        return self._stop_active_meeting(allow_runtime_fallback=False)

    def _on_update_meeting(self, *, title: Optional[str], tags: Optional[list[str]]) -> dict[str, object]:
        session = self._active_meeting_session()
        clean_tags = self._normalize_tags(tags) if tags is not None else None

        if session is not None:
            if title is not None:
                session.set_title(title)
            if clean_tags is not None:
                session.set_tags(clean_tags)
            state = session.state
            return state.to_dict() if state is not None else self._runtime_idle_state()

        with self.state_lock:
            if title is not None:
                self.pending_title = str(title).strip()
            if clean_tags is not None:
                self.pending_tags = clean_tags
        return self._runtime_idle_state()

    def _on_process_plugin_jobs(
        self,
        *,
        max_jobs: Optional[int],
        include_scheduled: bool,
    ) -> dict[str, object]:
        queue_flush = self._flush_deferred_plugin_runs_to_db()
        queue_result = self._process_deferred_plugin_queue(
            max_jobs=max_jobs,
            include_scheduled=include_scheduled,
        )
        return {
            "processed": int(queue_result.get("processed") or 0),
            "skipped_active_meeting": bool(queue_result.get("skipped_active_meeting")),
            "deferred_queue_jobs": int(queue_flush.get("queued_jobs") or 0),
            "deferred_queue_error": queue_flush.get("error"),
            "error": queue_result.get("error"),
        }

    def _infer_intent_scores(self, *, transcript: Optional[str], tags: Optional[list[str]]) -> dict[str, float]:
        return extract_intent_signals(transcript, tags=tags)

    def _derive_preview_transcript_hash(
        self,
        *,
        transcript: Optional[str],
        intent_scores: Optional[dict[str, object]],
    ) -> tuple[str, str]:
        transcript_text = str(transcript or "").strip()
        if transcript_text:
            return hashlib.sha256(transcript_text.encode("utf-8")).hexdigest(), transcript_text[:400]
        score_blob = str(intent_scores if isinstance(intent_scores, dict) else {})
        return hashlib.sha256(score_blob.encode("utf-8")).hexdigest(), ""

    def _build_active_preview_window_context(
        self,
        *,
        transcript: Optional[str],
        route_payload: dict[str, object],
    ) -> Optional[dict[str, object]]:
        session = self._active_meeting_session()
        if session is None:
            return None

        state = session.state
        if state is None:
            return None

        meeting_id = str(state.id or "").strip()
        if not meeting_id:
            return None

        self.preview_window_seq += 1
        transcript_hash, transcript_excerpt = self._derive_preview_transcript_hash(
            transcript=transcript,
            intent_scores=route_payload.get("intent_scores") if isinstance(route_payload.get("intent_scores"), dict) else None,
        )
        state_payload = state.to_dict()
        end_seconds = float(state_payload.get("duration") or 0.0)
        start_seconds = max(0.0, end_seconds - 90.0)
        return {
            "meeting_id": meeting_id,
            "window_id": f"{meeting_id}:preview-{self.preview_window_seq:04d}",
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "transcript_hash": transcript_hash,
            "transcript_excerpt": transcript_excerpt,
        }

    def _record_route_preview_history(
        self,
        *,
        route_payload: dict[str, object],
        tags: Optional[list[str]],
        window_context: dict[str, object],
        plugin_runs: list[dict[str, object]],
    ) -> None:
        meeting_id = str(window_context.get("meeting_id") or "").strip()
        window_id = str(window_context.get("window_id") or "").strip()
        transcript_hash = str(window_context.get("transcript_hash") or "").strip()
        if not meeting_id or not window_id:
            return

        active_intents = route_payload.get("active_intents") if isinstance(route_payload.get("active_intents"), list) else []
        override_intents = route_payload.get("override_intents") if isinstance(route_payload.get("override_intents"), list) else []
        intent_scores = route_payload.get("intent_scores") if isinstance(route_payload.get("intent_scores"), dict) else {}
        clean_tags = [str(tag).strip().lower() for tag in (tags or []) if str(tag).strip()]

        with self.state_lock:
            self.pending_intent_windows.append(
                {
                    "meeting_id": meeting_id,
                    "window_id": window_id,
                    "start_seconds": float(window_context.get("start_seconds") or 0.0),
                    "end_seconds": float(window_context.get("end_seconds") or 0.0),
                    "transcript_hash": transcript_hash,
                    "transcript_excerpt": str(window_context.get("transcript_excerpt") or ""),
                    "profile": str(route_payload.get("profile") or "balanced"),
                    "threshold": float(route_payload.get("threshold") or DEFAULT_INTENT_THRESHOLD),
                    "active_intents": [str(intent).strip().lower() for intent in active_intents if str(intent).strip()],
                    "intent_scores": {
                        str(intent).strip().lower(): float(score)
                        for intent, score in intent_scores.items()
                        if str(intent).strip()
                    },
                    "override_intents": [str(intent).strip().lower() for intent in override_intents if str(intent).strip()],
                    "tags": clean_tags,
                    "metadata": {
                        "source": "route_preview",
                        "hysteresis_applied": bool(route_payload.get("hysteresis_applied")),
                    },
                }
            )

            for run in plugin_runs:
                plugin_id = str(run.get("plugin_id") or "").strip()
                if not plugin_id:
                    continue
                run_transcript_hash = str(run.get("transcript_hash") or transcript_hash)
                self.pending_plugin_runs.append(
                    {
                        "meeting_id": meeting_id,
                        "window_id": window_id,
                        "plugin_id": plugin_id,
                        "plugin_version": str(run.get("plugin_version") or "unknown"),
                        "status": str(run.get("status") or "unknown"),
                        "idempotency_key": str(run.get("idempotency_key") or "").strip()
                        or build_idempotency_key(
                            meeting_id=meeting_id,
                            window_id=window_id,
                            plugin_id=plugin_id,
                            transcript_hash=run_transcript_hash,
                        ),
                        "duration_ms": float(run.get("duration_ms") or 0.0),
                        "output": run.get("output") if isinstance(run.get("output"), dict) else None,
                        "error": str(run.get("error")) if run.get("error") else None,
                        "deduped": bool(run.get("deduped")),
                    }
                )

    def _persist_pending_mir_history(self, meeting_id: str) -> dict[str, object]:
        with self.state_lock:
            windows_to_save = [dict(item) for item in self.pending_intent_windows if str(item.get("meeting_id")) == meeting_id]
            runs_to_save = [dict(item) for item in self.pending_plugin_runs if str(item.get("meeting_id")) == meeting_id]
            self.pending_intent_windows[:] = [
                item for item in self.pending_intent_windows if str(item.get("meeting_id")) != meeting_id
            ]
            self.pending_plugin_runs[:] = [
                item for item in self.pending_plugin_runs if str(item.get("meeting_id")) != meeting_id
            ]

        saved_windows = 0
        saved_runs = 0
        save_error: Optional[str] = None
        if not windows_to_save and not runs_to_save:
            return {
                "intent_windows_saved": 0,
                "plugin_runs_saved": 0,
                "error": None,
            }

        try:
            from .db import get_database

            db = get_database()
            for record in windows_to_save:
                db.plugins.record_intent_window(**record)
                saved_windows += 1
            for record in runs_to_save:
                db.plugins.record_plugin_run(**record)
                saved_runs += 1
        except Exception as exc:
            save_error = str(exc)
            log.error(f"Failed to persist MIR history for meeting {meeting_id}: {exc}")

        return {
            "intent_windows_saved": saved_windows,
            "plugin_runs_saved": saved_runs,
            "error": save_error,
        }

    def _synthesize_and_persist_artifacts(self, meeting_id: str) -> dict[str, object]:
        clean_meeting_id = str(meeting_id).strip()
        if not clean_meeting_id:
            return {"artifacts_saved": 0, "error": None}

        try:
            from .db import get_database
            from .plugins.synthesis import synthesize_meeting_artifacts

            db = get_database()
            runs = db.plugins.list_plugin_runs(clean_meeting_id, limit=5000)
            artifacts = synthesize_meeting_artifacts(
                meeting_id=clean_meeting_id,
                plugin_runs=runs,
                max_artifacts=500,
            )
            for artifact in artifacts:
                db.plugins.record_artifact(
                    artifact_id=artifact.artifact_id,
                    meeting_id=artifact.meeting_id,
                    artifact_type=artifact.artifact_type,
                    title=artifact.title,
                    body_markdown=artifact.body_markdown,
                    structured_json=artifact.structured_json,
                    confidence=artifact.confidence,
                    status=artifact.status,
                    plugin_id=artifact.plugin_id,
                    plugin_version=artifact.plugin_version,
                    sources=[source.to_dict() for source in artifact.sources],
                )
            return {"artifacts_saved": len(artifacts), "error": None}
        except Exception as exc:
            message = str(exc)
            log.error(f"Failed to synthesize artifacts for meeting {clean_meeting_id}: {message}")
            return {"artifacts_saved": 0, "error": message}

    def _associate_meeting_with_projects(self, meeting_id: str) -> dict[str, object]:
        """Auto-associate a meeting with projects based on project_detector plugin runs."""
        clean_meeting_id = str(meeting_id).strip()
        if not clean_meeting_id:
            return {"projects_associated": 0, "error": None}

        try:
            from .db import get_database
            db = get_database()
            runs = db.plugins.list_plugin_runs(clean_meeting_id, limit=5000)

            # Filter to successful project_detector runs
            detector_runs = [
                r for r in runs
                if r.plugin_id == "project_detector" and r.status in ("success", "deduped")
                and r.output
            ]

            if not detector_runs:
                return {"projects_associated": 0, "error": None}

            # Aggregate max score per project across all windows
            project_max_scores: dict[str, dict[str, object]] = {}
            for run in detector_runs:
                matched = run.output.get("matched_projects") or []
                for match in matched:
                    pid = str(match.get("project_id") or "").strip()
                    if not pid:
                        continue
                    score = float(match.get("score") or 0)
                    threshold = float(match.get("detection_threshold") or 0.4)
                    existing = project_max_scores.get(pid)
                    if existing is None or score > float(existing["max_score"]):
                        project_max_scores[pid] = {
                            "max_score": score,
                            "threshold": threshold,
                        }
                    # Log each window detection
                    db.projects.log_project_detection(
                        meeting_id=clean_meeting_id,
                        project_id=pid,
                        window_id=run.window_id,
                        score=score,
                        keyword_hits=match.get("keyword_hits"),
                        member_hits=match.get("member_hits"),
                    )

            # Associate meeting with projects that exceed their threshold
            associated = 0
            for pid, data in project_max_scores.items():
                max_score = float(data["max_score"])
                threshold = float(data["threshold"])
                if max_score >= threshold:
                    db.projects.associate_meeting_project(
                        meeting_id=clean_meeting_id,
                        project_id=pid,
                        source="auto",
                        confidence=max_score,
                    )
                    associated += 1

            return {"projects_associated": associated, "error": None}
        except Exception as exc:
            message = str(exc)
            log.error(f"Failed to associate meeting {clean_meeting_id} with projects: {message}")
            return {"projects_associated": 0, "error": message}

    def _on_get_intent_controls(self) -> dict[str, object]:
        return self._mir_controls_payload()

    def _on_set_intent_profile(self, profile: str) -> dict[str, object]:
        with self.state_lock:
            self.mir_profile = normalize_profile(profile)
        return self._mir_controls_payload()

    def _on_set_intent_override(self, intents: Optional[list[str]]) -> dict[str, object]:
        with self.state_lock:
            self.mir_override_intents = normalize_override_intents(intents)
        return self._mir_controls_payload()

    def _on_route_preview(
        self,
        *,
        profile: Optional[str] = None,
        threshold: Optional[float] = None,
        intent_scores: Optional[dict[str, float]] = None,
        override_intents: Optional[list[str]] = None,
        previous_intents: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        transcript: Optional[str] = None,
    ) -> dict[str, object]:
        controls = self._mir_controls_payload()
        profile_value = normalize_profile(profile or str(controls.get("profile") or ""))
        threshold_value = DEFAULT_INTENT_THRESHOLD if threshold is None else float(threshold)

        inferred_scores = self._infer_intent_scores(transcript=transcript, tags=tags)
        provided_scores = intent_scores if isinstance(intent_scores, dict) else {}
        effective_scores = dict(inferred_scores)
        effective_scores.update(provided_scores)

        if isinstance(override_intents, list):
            effective_override = normalize_override_intents(override_intents)
        else:
            effective_override = normalize_override_intents(controls.get("override_intents"))  # type: ignore[arg-type]

        route = preview_route(
            profile=profile_value,
            intent_scores=effective_scores,
            threshold=threshold_value,
            previous_intents=previous_intents,
            override_intents=effective_override,
        )
        route_payload = route.to_dict()
        route_payload["mir_enabled"] = bool(controls.get("enabled"))
        window_context = self._build_active_preview_window_context(
            transcript=transcript,
            route_payload=route_payload,
        )
        transcript_hash, _ = self._derive_preview_transcript_hash(
            transcript=transcript,
            intent_scores=route_payload.get("intent_scores") if isinstance(route_payload.get("intent_scores"), dict) else None,
        )

        execution_meeting_id = (
            str(window_context.get("meeting_id"))
            if isinstance(window_context, dict) and window_context.get("meeting_id")
            else "web-runtime-preview"
        )
        execution_window_id = (
            str(window_context.get("window_id"))
            if isinstance(window_context, dict) and window_context.get("window_id")
            else f"{execution_meeting_id}:preview"
        )
        execution_context = {
            "transcript": str(transcript or ""),
            "tags": [str(tag).strip().lower() for tag in (tags or []) if str(tag).strip()],
            "active_intents": list(route_payload.get("active_intents") or []),
            "intent_scores": dict(route_payload.get("intent_scores") or {}),
            "profile": route_payload.get("profile"),
            "threshold": route_payload.get("threshold"),
        }
        run_results = self.plugin_host.execute_chain(
            list(route_payload.get("plugin_chain") or []),
            context=execution_context,
            meeting_id=execution_meeting_id,
            window_id=execution_window_id,
            transcript_hash=transcript_hash,
        )
        route_payload["plugin_runs"] = [result.to_dict() for result in run_results]
        queue_flush = self._flush_deferred_plugin_runs_to_db()
        route_payload["deferred_queue_jobs"] = int(queue_flush.get("queued_jobs") or 0)
        if queue_flush.get("error"):
            route_payload["deferred_queue_error"] = str(queue_flush["error"])

        if isinstance(window_context, dict):
            self._record_route_preview_history(
                route_payload=route_payload,
                tags=tags,
                window_context=window_context,
                plugin_runs=route_payload["plugin_runs"],  # type: ignore[arg-type]
            )

        with self.state_lock:
            self.last_route_preview = dict(route_payload)

        return route_payload

    def _on_update_action_item(self, item_id: str, status: str):
        session = self._active_meeting_session()
        if session is None:
            return None
        return session.update_action_item(item_id, status)

    def _on_update_action_item_review(self, item_id: str, review_state: str):
        session = self._active_meeting_session()
        if session is None:
            return None
        return session.update_action_item_review(item_id, review_state)

    def _on_edit_action_item(self, item_id: str, *, task: str, owner: Optional[str], due: Optional[str]):
        session = self._active_meeting_session()
        if session is None:
            return None
        return session.edit_action_item(item_id, task=task, owner=owner, due=due)

    def _transcribe_and_type(
        self,
        audio: np.ndarray,
        *,
        on_complete: Optional[Callable[[str], None]] = None,
        agent_reply_session: Any | None = None,
    ) -> None:
        """Run transcription, text processing, and typing for a captured chunk.

        Shared between the local hotkey path and the device-driven
        voice-typing path (HS-14-05). Always flips voice state back
        to ``idle`` in its ``finally``. ``on_complete`` (HS-14-07)
        receives the typed text on success and is intentionally
        invoked outside the typing try-block — typing failures
        still surface the transcript to the device.
        """
        completed_text: Optional[str] = None
        with self.transcription_lock:
            try:
                text = self._ensure_transcriber_loaded().transcribe(audio)
                if not text:
                    self._set_runtime_activity(
                        "complete",
                        source="dictation",
                        label="No speech",
                        detail="No speech detected.",
                        last_event="dictation_no_speech",
                        last_error="",
                    )
                    return
                text = self.text_processor.process(text)
                # HS-52-04: voice command dispatch. A configured, enabled keyword fires
                # an action instead of being typed; on a match we return early and type
                # nothing. Off by default and on no match this is inert (byte-identical).
                voice_command = self._maybe_dispatch_voice_command(text, agent_reply_session)
                if voice_command is not None:
                    if voice_command.ok:
                        self._set_runtime_activity(
                            "complete",
                            source="dictation",
                            label="Command",
                            detail=voice_command.preview,
                            last_event="voice_command_fired",
                            last_error="",
                        )
                        self._mark_first_dictation()
                    else:
                        with self.state_lock:
                            self.runtime_status["last_error"] = (
                                f"Voice command failed: {voice_command.error}"
                            )
                        self._set_runtime_activity(
                            "error",
                            source="dictation",
                            label="Command failed",
                            detail=voice_command.preview,
                            last_event="voice_command_failed",
                            last_error=voice_command.error,
                        )
                    return
                self._set_runtime_activity(
                    "processing",
                    source="dictation",
                    detail="Processing dictation.",
                    last_event="dictation_processing",
                    last_error="",
                )
                text = self._maybe_run_dictation_pipeline(
                    text,
                    audio_duration_s=len(audio) / 16000.0,
                    transcribed_at=datetime.now(),
                    agent_reply_session=agent_reply_session,
                )
                completed_text = text
                with self.state_lock:
                    self.runtime_status["last_transcription"] = text
                    self.runtime_status["last_error"] = ""
                print(f"-> {text}")
                delivered = self._try_tmux_agent_reply(text, agent_reply_session)
                if delivered:
                    self._set_runtime_activity(
                        "complete",
                        source="dictation",
                        label="Sent",
                        detail="Sent dictated text to the agent session.",
                        last_event="dictation_delivered",
                        last_error="",
                    )
                    self._mark_first_dictation()
                if not delivered and self.typer is not None:
                    try:
                        paste_target_profile = self._paste_target_profile(agent_reply_session)
                        self._set_runtime_activity(
                            "typing",
                            source="dictation",
                            detail="Typing dictated text.",
                            last_event="dictation_typing",
                            last_error="",
                        )
                        self.typer.type_text(
                            text,
                            target_profile=paste_target_profile,
                            submit=agent_reply_session is not None,
                        )
                        self._set_runtime_activity(
                            "complete",
                            source="dictation",
                            label="Typed",
                            detail="Dictated text was inserted.",
                            last_event="dictation_typed",
                            last_error="",
                        )
                        self._mark_first_dictation()
                    except Exception as exc:
                        with self.state_lock:
                            self.runtime_status["last_error"] = f"Typing failed: {exc}"
                            self.runtime_status["text_injection_enabled"] = False
                            self.runtime_status["text_injection_error"] = f"{type(exc).__name__}: {exc}"
                        self._set_runtime_activity(
                            "error",
                            source="dictation",
                            detail="Typing failed.",
                            last_event="dictation_typing_failed",
                            last_error=f"{type(exc).__name__}: {exc}",
                        )
                        log.warning(f"Typing failed in web mode: {exc}")
            except Exception as exc:
                with self.state_lock:
                    self.runtime_status["last_error"] = f"Transcription failed: {exc}"
                self._set_runtime_activity(
                    "error",
                    source="dictation",
                    detail="Transcription failed.",
                    last_event="dictation_transcription_failed",
                    last_error=f"{type(exc).__name__}: {exc}",
                )
                log.error(f"Transcription failed in web mode: {exc}")
            finally:
                self._set_voice_state("idle", update_activity=False)
        if on_complete is not None and completed_text is not None:
            try:
                on_complete(completed_text)
            except Exception as exc:
                log.warning(f"on_complete hook raised: {exc}")

    def _kick_off_transcribe(
        self,
        audio: np.ndarray,
        *,
        on_complete: Optional[Callable[[str], None]] = None,
        agent_reply_session: Any | None = None,
        source: str = "dictation",
    ) -> None:
        if len(audio) < 1600:
            self._set_voice_state("idle", update_activity=False)
            self._set_runtime_activity(
                "complete",
                source=source,
                label="Too short",
                detail="Recording was too short.",
                last_event="dictation_too_short",
                last_error="",
            )
            return
        self._set_voice_state(
            "transcribing",
            source=source,
            detail="Transcribing audio.",
            last_event="dictation_transcribing",
            last_error="",
        )
        threading.Thread(
            target=lambda: self._transcribe_and_type(
                audio,
                on_complete=on_complete,
                agent_reply_session=agent_reply_session,
            ),
            daemon=True,
        ).start()

    def _maybe_dispatch_voice_command(
        self, text: str, agent_reply_session: Any | None = None
    ) -> Any:
        # HS-52-04: thin delegate to the carved dispatch seam. Injects the runtime
        # typer for `type_text` macros and surfaces a matched command as a runtime
        # activity. Returns a VoiceCommandResult if a command fired (caller types
        # nothing), else None.
        def _type(t: str) -> None:
            if self.typer is not None:
                self.typer.type_text(
                    t, target_profile=self._paste_target_profile(agent_reply_session)
                )

        def _activity(label: str) -> None:
            self._set_runtime_activity(
                "processing",
                source="dictation",
                label=label,
                detail=label,
                last_event="voice_command_match",
                last_error="",
            )

        return dispatch_voice_command(
            text,
            config=self.config,
            type_writer=_type,
            on_activity=_activity,
        )

    def _maybe_run_dictation_pipeline(
        self,
        text: str,
        *,
        audio_duration_s: float,
        transcribed_at: datetime,
        agent_reply_session: Any | None = None,
    ) -> str:
        # HS-52-01: the orchestration was carved out of this god-object into
        # `holdspeak.dictation_runner`; this stays as the thin delegate the
        # transcription path calls. Behaviour is unchanged.
        return run_dictation_pipeline(
            text,
            config=self.config,
            server=self.server,
            audio_duration_s=audio_duration_s,
            transcribed_at=transcribed_at,
            agent_reply_session=agent_reply_session,
        )

    def _paste_target_profile(self, agent_reply_session: Any | None) -> str | None:
        if agent_reply_session is None:
            return None
        try:
            from holdspeak.agent_device import target_profile_override_for_agent

            return target_profile_override_for_agent(agent_reply_session)
        except Exception:
            return None

    def _try_tmux_agent_reply(self, text: str, agent_reply_session: Any | None) -> bool:
        pane = self._agent_tmux_pane(agent_reply_session)
        if not pane:
            return False
        try:
            from holdspeak.tmux_transport import send_text_to_pane

            send_text_to_pane(pane=pane, text=text, submit=True)
            return True
        except Exception as exc:
            with self.state_lock:
                self.runtime_status["last_error"] = f"tmux reply failed; fell back to typing: {exc}"
            log.warning(f"tmux reply failed; falling back to text injection: {exc}")
            return False

    def _agent_tmux_pane(self, agent_reply_session: Any | None) -> str | None:
        if agent_reply_session is None:
            return None
        pane = getattr(agent_reply_session, "tmux_pane", None)
        return str(pane).strip() if pane else None

    def _agent_reply_deliverable(self, agent_reply_session: Any | None) -> bool:
        if agent_reply_session is None:
            return True
        if self._agent_tmux_pane(agent_reply_session):
            return True
        return self.typer is not None

    def _on_hotkey_press(self) -> None:
        if self.runtime_stop_event.is_set():
            return
        if self.recorder is None:
            self._set_runtime_activity(
                "error",
                source="hotkey",
                detail="Voice typing hotkey is unavailable.",
                last_event="dictation_hotkey_unavailable",
                last_error=str(self.runtime_status.get("global_hotkey_error") or ""),
            )
            return
        # HS-32-03: no explicit "is a meeting active?" check — the shared
        # `voice_session` arbiter is the single owner model. While a meeting
        # holds the floor (owner="meeting"), `begin()` returns False here.
        try:
            accepted = self.voice_session.begin(self.recorder, owner="hotkey")
        except Exception as exc:
            with self.state_lock:
                self.runtime_status["last_error"] = f"Recording failed: {exc}"
            self._set_voice_state(
                "idle",
                source="hotkey",
                detail="Recording failed.",
                last_event="dictation_recording_failed",
                last_error=f"{type(exc).__name__}: {exc}",
            )
            log.error(f"Recording failed in web mode: {exc}")
            return
        if not accepted:
            log.info("hotkey_press_ignored_session_active")
            self._set_runtime_activity(
                "complete",
                source="hotkey",
                label="Busy",
                detail="Another HoldSpeak audio session is active.",
                last_event="dictation_recording_busy",
                last_error="",
            )
            return
        self._set_voice_state(
            "recording",
            source="hotkey",
            detail="HoldSpeak is listening.",
            last_event="dictation_recording_started",
            last_error="",
        )

    def _on_hotkey_release(self) -> None:
        # No meeting check: `end("hotkey")` returns None when the hotkey
        # doesn't own the floor (e.g. a meeting holds it), so this is a no-op.
        try:
            audio = self.voice_session.end(owner="hotkey")
        except Exception as exc:
            with self.state_lock:
                self.runtime_status["last_error"] = f"Recording error: {exc}"
            self._set_voice_state(
                "idle",
                source="hotkey",
                detail="Recording stop failed.",
                last_event="dictation_recording_stop_failed",
                last_error=f"{type(exc).__name__}: {exc}",
            )
            log.error(f"Recording error in web mode: {exc}")
            return
        if audio is None:
            self._set_voice_state("idle", source="hotkey", last_event="dictation_recording_ignored")
            return

        self._kick_off_transcribe(audio, source="hotkey")

    def _on_device_voice_start(self, device_id: str, source: AudioSource) -> bool:
        """Begin a device-driven voice-typing session.

        Returns ``False`` (so the WS dispatcher emits a
        ``session_busy`` error frame) when:
        - a meeting is active and this device is *not* attached
          to it (meeting holds the audio floor);
        - the local hotkey or another device already owns the
          voice session.

        When this device *is* attached to the active meeting, the
        meeting already started its recorder — return ``True``
        without claiming the voice session so the WS keeps pumping
        binary frames into the meeting's drain path.
        """
        active_meeting = self._active_meeting_session()
        if active_meeting is not None:
            if active_meeting.is_device_attached(device_id):
                return True
            self._set_runtime_activity(
                "complete",
                source="device",
                label="Device busy",
                detail="Meeting audio is already active.",
                last_event="device_dictation_busy",
                last_error="",
            )
            return False
        from .agent_context import get_recent_awaiting_agent_session

        agent_reply_session = get_recent_awaiting_agent_session(max_age_seconds=120)
        if not self._agent_reply_deliverable(agent_reply_session):
            with self.state_lock:
                self.runtime_status["last_error"] = "Agent reply target unavailable"
            self.device_status.send(device_id, "No reply target", ttl_ms=3000)
            log.info(
                "device_voice_start_rejected_no_agent_reply_target",
                extra={"device_id": device_id},
            )
            self._set_runtime_activity(
                "error",
                source="device",
                detail="Agent reply target unavailable.",
                last_event="device_dictation_no_reply_target",
                last_error="Agent reply target unavailable",
            )
            return False
        owner = f"device:{device_id}"
        try:
            accepted = self.voice_session.begin(source, owner=owner)
        except Exception as exc:
            log.error(f"Device voice-typing start failed: {exc}")
            self._set_runtime_activity(
                "error",
                source="device",
                detail="Device recording failed.",
                last_event="device_dictation_recording_failed",
                last_error=f"{type(exc).__name__}: {exc}",
            )
            return False
        if not accepted:
            self._set_runtime_activity(
                "complete",
                source="device",
                label="Device busy",
                detail="Another HoldSpeak audio session is active.",
                last_event="device_dictation_busy",
                last_error="",
            )
            return False
        self._set_voice_state(
            "recording",
            source="device",
            detail="Device voice input is recording.",
            last_event="device_dictation_recording_started",
            last_error="",
        )
        # AIPI-4-13: TX state lives in the device's firmware-side
        # tx_label glyph (top-right, ↑ during right-button hold).
        # No "Listening..." pushback — would clobber the bottom
        # widget's persistent meeting/idle text.
        return True

    def _on_device_voice_stop(
        self, device_id: str, source: AudioSource
    ) -> Optional[np.ndarray]:
        active_meeting = self._active_meeting_session()
        if active_meeting is not None and active_meeting.is_device_attached(device_id):
            # The meeting owns this device's audio routing.
            return None
        owner = f"device:{device_id}"
        try:
            audio = self.voice_session.end(owner=owner)
        except Exception as exc:
            log.error(f"Device voice-typing stop failed: {exc}")
            self._set_voice_state(
                "idle",
                source="device",
                detail="Device recording stop failed.",
                last_event="device_dictation_recording_stop_failed",
                last_error=f"{type(exc).__name__}: {exc}",
            )
            return None
        if audio is None:
            self._set_voice_state("idle", source="device", last_event="device_dictation_recording_ignored")
            return None

        # AIPI-4-13: no "Thinking..." pushback to bottom — the absent
        # tx_label arrow after release already signals "we're done
        # capturing, processing now". Transcript snippet lands in
        # the middle slot below.

        from .agent_context import get_recent_awaiting_agent_session

        agent_reply_session = get_recent_awaiting_agent_session(max_age_seconds=120)

        def _device_transcript_complete(text: str) -> None:
            snippet = (text or "").strip()[:150]
            self.device_status.send(device_id, snippet, ttl_ms=4000)

        self._kick_off_transcribe(
            audio,
            on_complete=_device_transcript_complete,
            agent_reply_session=agent_reply_session,
            source="device",
        )
        return audio

    def _on_device_voice_cancel(self, device_id: str) -> None:
        self.voice_session.cancel(owner=f"device:{device_id}")

    def _on_device_event(self, device_id: str, name: str, at: Optional[float]) -> None:
        """Inbound device event from the WS.

        - ``long_press`` (HS-14-07): bookmark gesture in an active
          meeting where this device is attached.
        - ``double_left_click`` (AIPI-4-14): cycle through meeting-stat
          views (Numbers → Speakers → Intel) on the device's middle
          slot.
        """
        if name == "long_press":
            active = self._active_meeting_session()
            if active is None or not active.is_device_attached(device_id):
                return
            bookmark = active.add_bookmark(label="", auto_label=True)
            if bookmark is None:
                return
            attached_ids = [d.id for d in active.state.devices] if active.state else []
            self.device_status.broadcast(
                attached_ids,
                f"Bookmark @ {bookmark.timestamp:.0f}s",
                ttl_ms=2500,
            )
            return

        if name == "double_left_click":
            active = self._active_meeting_session()
            if active is None or active.state is None:
                log.info(
                    "device_event_double_tap_ignored",
                    extra={"device_id": device_id, "reason": "no_active_meeting"},
                )
                return
            if not active.is_device_attached(device_id):
                log.info(
                    "device_event_double_tap_ignored",
                    extra={"device_id": device_id, "reason": "device_not_attached"},
                )
                return
            current = self.device_stats_cycle.get(device_id, -1)
            next_index, view_id, formatter = pick_next_view(current)
            self.device_stats_cycle[device_id] = next_index
            payload = formatter(active.state)
            self.device_status.send(device_id, payload, ttl_ms=4000)
            log.info(
                "device_event_double_tap_cycled",
                extra={"device_id": device_id, "view": view_id, "index": next_index},
            )
            return

        log.info(
            "device_event_ignored",
            extra={"device_id": device_id, "event_name": name},
        )

    def _on_device_health(self, descriptor: object) -> None:
        active = self._active_meeting_session()
        if active is None:
            return
        updater = getattr(active, "update_device_descriptor", None)
        if callable(updater):
            updater(descriptor)
        if self.server is not None:
            try:
                from .meeting_session import _device_descriptor_to_dict

                self.server.broadcast("device_health", _device_descriptor_to_dict(descriptor))
            except Exception as exc:
                log.debug(f"Failed to broadcast device health: {exc}")

    def _on_device_query(
        self,
        device_id: str,
        name: str,
        at: Optional[float],
    ) -> Optional[dict[str, object]]:
        from .agent_context import (
            get_recent_awaiting_agent_session,
            select_next_awaiting_agent_session,
        )
        from .agent_device import (
            AGENT_NEXT_QUERY,
            AGENT_QUERY_NAMES,
            build_agent_query_response,
        )

        if name in AGENT_QUERY_NAMES:
            if name == AGENT_NEXT_QUERY:
                session = select_next_awaiting_agent_session(max_age_seconds=120)
                response_name = "agent_status"
            else:
                session = get_recent_awaiting_agent_session(max_age_seconds=120)
                response_name = name
            response = build_agent_query_response(response_name, session)
            if response is not None:
                return response

        if name != "last_segment":
            log.info(
                "device_query_ignored",
                extra={"device_id": device_id, "query_name": name, "at": at},
            )
            return {"text": f"Unknown query: {name}"[:500], "ttl_ms": 3000}
        active = self._active_meeting_session()
        if active is None or active.state is None:
            return {"text": "No transcript yet", "ttl_ms": 5000}
        for segment in reversed(active.state.segments):
            if getattr(segment, "device_id", None) != device_id:
                continue
            speaker = getattr(segment, "speaker", None) or "?"
            text = getattr(segment, "text", "") or ""
            return {
                "text": f"{speaker}: {text}"[:500],
                "ttl_ms": 5000,
            }
        return {"text": "No transcript yet", "ttl_ms": 5000}

    def _signal_handler(self, sig, frame) -> None:
        _ = sig, frame
        self.runtime_stop_event.set()

    def run(self) -> None:
        """Start the web server + capture stack and keep it alive until stop."""
        try:
            self.server = MeetingWebServer(
                WebRuntimeCallbacks(
                    on_bookmark=self._on_bookmark,
                    on_stop=self._on_stop,
                    on_start=self._start_meeting,
                    on_meeting_stop=self._on_meeting_stop,
                    on_get_status=self._get_runtime_status,
                    on_update_meeting=self._on_update_meeting,
                    on_get_intent_controls=self._on_get_intent_controls,
                    on_set_intent_profile=self._on_set_intent_profile,
                    on_set_intent_override=self._on_set_intent_override,
                    on_route_preview=self._on_route_preview,
                    on_process_plugin_jobs=self._on_process_plugin_jobs,
                    get_state=self._get_state,
                    on_update_action_item=self._on_update_action_item,
                    on_update_action_item_review=self._on_update_action_item_review,
                    on_edit_action_item=self._on_edit_action_item,
                    on_settings_applied=self._apply_updated_config,
                    project_detector=self.project_detector,
                    device_registry=self.device_registry,
                    device_psk_provider=lambda: ensure_device_psk(self.config),
                    on_device_voice_start=self._on_device_voice_start,
                    on_device_voice_stop=self._on_device_voice_stop,
                    on_device_voice_cancel=self._on_device_voice_cancel,
                    device_status_emitter=self.device_status,
                    on_device_event=self._on_device_event,
                    on_device_health=self._on_device_health,
                    on_device_query=self._on_device_query,
                ),
                host="127.0.0.1",
                port=_configured_web_port_from_env(),
                # HS-25-02: token exists/persists now so it is ready the moment a
                # non-loopback bind is introduced (Phase 15); dormant on loopback.
                auth_token=ensure_web_token(self.config),
                # HS-40-02: back the session correction store with the durable
                # repository so routing learning survives a restart. Only the
                # live runtime wires this; bare servers (tests/dry-run) stay
                # in-memory and byte-identical.
                dictation_corrections_repository=_dictation_corrections_repo(),
                # HS-45-01: back the session journal recorder with the durable
                # repository so the dictation loop gets a reviewable, replayable
                # afterlife. Only the live runtime wires this; bare servers
                # (tests/dry-run-only) stay no-op and byte-identical.
                dictation_journal_repository=_dictation_journal_repo(),
            )
            self.runtime_url = self.server.start()
        except Exception as exc:
            print(f"Failed to start HoldSpeak web mode: {exc}", file=sys.stderr)
            print("Install optional web dependencies with: uv pip install -e '.[meeting]'", file=sys.stderr)
            log.error(f"Failed to start web mode: {exc}", exc_info=True)
            raise SystemExit(1) from exc

        self.plugin_queue_thread = threading.Thread(
            target=self._deferred_plugin_queue_loop,
            name="HoldSpeakMirPluginQueue",
            daemon=True,
        )
        self.plugin_queue_thread.start()
        self._warm_transcriber_in_background()

        try:
            self.recorder = AudioRecorder(
                device=self.config.meeting.mic_device,
                on_level=lambda _level: None,
            )
            self.hotkey_listener = HotkeyListener(
                on_press=self._on_hotkey_press,
                on_release=self._on_hotkey_release,
                hotkey=self.config.hotkey.key,
            )
            self.hotkey_listener.start()
            with self.state_lock:
                self.runtime_status["global_hotkey_available"] = True
                self.runtime_status["global_hotkey_error"] = ""
        except Exception as exc:
            self.hotkey_listener = None
            self.recorder = None
            with self.state_lock:
                self.runtime_status["global_hotkey_available"] = False
                self.runtime_status["global_hotkey_error"] = f"{type(exc).__name__}: {exc}"
                self.runtime_status["last_error"] = f"Global hotkey unavailable: {exc}"
            log.warning(f"Global hotkey unavailable in web mode: {exc}")

        log.info(f"HoldSpeak web runtime active at {self.runtime_url}")
        print(f"HoldSpeak web runtime is running at: {self.runtime_url}")
        self._print_setup_nudge()
        print(f"Settings: {self.runtime_url}/settings · History: {self.runtime_url}/history")
        if self.hotkey_listener is not None:
            print(f"Voice typing hotkey is active: hold {self.config.hotkey.display}, speak, release.")
        else:
            print("Voice typing hotkey unavailable; grant Accessibility/Input Monitoring permission and restart.")
        if not self.no_open and self.config.meeting.web_auto_open:
            webbrowser.open(self.runtime_url)
            print("Opened web dashboard in your default browser.")
        elif self.no_open:
            print("Headless mode active (`--no-open`): browser auto-open disabled.")
        else:
            print("Browser auto-open is disabled in config (`meeting.web_auto_open=false`).")
        print("Press Ctrl+C to stop.")

        if self.register_signal_handlers:
            signal.signal(signal.SIGINT, self._signal_handler)
            if hasattr(signal, "SIGTERM"):
                signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            while not self.runtime_stop_event.wait(0.2):
                pass
        finally:
            self._flush_deferred_plugin_runs_to_db()
            if self.hotkey_listener is not None:
                self.hotkey_listener.stop()
            active = self._active_meeting_session()
            if active is not None:
                try:
                    final_state = active.stop()
                    # HS-32-03: meeting recorder closed — release the audio floor.
                    self.voice_session.release(_MEETING_AUDIO_OWNER)
                    active.save()
                    if getattr(final_state, "id", None):
                        meeting_id = str(final_state.id)
                        self._persist_pending_mir_history(meeting_id)
                        self._synthesize_and_persist_artifacts(meeting_id)
                except Exception as exc:
                    log.error(f"Failed to finalize active meeting during shutdown: {exc}")
            if self.server is not None:
                self.server.stop()
            if self.desktop_presence is not None:
                try:
                    self.desktop_presence.close()
                except Exception as exc:
                    log.debug(f"Desktop presence close failed: {exc}")
            if self.plugin_queue_thread is not None:
                self.plugin_queue_thread.join(timeout=2.0)


def run_web_runtime(
    *,
    no_open: bool = False,
    stop_event: Optional[threading.Event] = None,
    register_signal_handlers: bool = True,
) -> None:
    """Start HoldSpeak web runtime and keep it alive until stop.

    Thin shim over :class:`WebRuntime` so the entry point (and the web/runtime
    test suite) call exactly as before.
    """
    WebRuntime(
        no_open=no_open,
        stop_event=stop_event,
        register_signal_handlers=register_signal_handlers,
    ).run()
