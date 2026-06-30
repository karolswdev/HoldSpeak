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


def _configured_web_host_from_env() -> str:
    """The bind host, defaulting to loopback.

    HSM-12: a Companion client (iPhone/iPad) points at the same desktop a coding
    session runs against, so the runtime must be able to bind off-loopback on the
    owner's own LAN. The default stays ``127.0.0.1`` (byte-identical to before);
    set ``HOLDSPEAK_WEB_HOST=0.0.0.0`` to expose it. A non-loopback bind is already
    refused without an auth token (``web_auth.nonloopback_bind_blocked``), so the
    token path is enforced the moment this opens.
    """
    raw = os.environ.get("HOLDSPEAK_WEB_HOST")
    if raw is None or not raw.strip():
        return "127.0.0.1"
    return raw.strip()


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


from .runtime.activity import RuntimeActivityMixin
from .runtime.cadence import CadenceMixin
from .runtime.device_glue import DeviceGlueMixin
from .runtime.dictation_capture import DictationCaptureMixin
from .runtime.meeting_glue import MeetingGlueMixin
from .runtime.plugin_queue import PluginQueueMixin
from .runtime.routing_glue import RoutingGlueMixin
from .runtime.transcriber_state import TranscriberStateMixin
from .runtime.wake_glue import WakeWordGlueMixin


class WebRuntime(
    TranscriberStateMixin,
    RuntimeActivityMixin,
    MeetingGlueMixin,
    RoutingGlueMixin,
    PluginQueueMixin,
    DictationCaptureMixin,
    WakeWordGlueMixin,
    DeviceGlueMixin,
    CadenceMixin,
):
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
        # HS-69-08: throttle the additive `audio_level` WS frame. The level
        # callbacks fire on the PortAudio thread at chunk rate; the meter only
        # needs ~15 Hz, and `broadcast` schedules a coroutine per call.
        self._last_audio_level_ts = 0.0
        self.transcriber: Optional[Transcriber] = None
        # HS-63-06: serializes transcriber construction. The boot-time warmup
        # thread and the first dictation/meeting both call
        # _ensure_transcriber_loaded; an unlocked check-then-construct let two
        # _MlxTranscriber instances exist, and mlx_whisper's process-level
        # model cache then binds the model to the FIRST instance's pinned
        # thread — the second instance's transcribe dies with the
        # process-fatal "no Stream(gpu, N) in current thread" (the Phase-60
        # crash class, one level up). A dedicated leaf lock, NOT
        # transcription_lock: the warmup already holds that one around its
        # call and would deadlock.
        self._transcriber_init_lock = threading.Lock()
        self.server: Optional[MeetingWebServer] = None
        self.meeting_session: Optional[MeetingSession] = None
        # HS-41-03/04: the opt-in desktop presence host (None unless
        # HOLDSPEAK_DESKTOP_PRESENCE=1 and a native renderer is available). The
        # url_provider is read lazily (the macOS renderer loads <url>/presence on
        # first show), so it resolves after the server has a port.
        # HS-60: the wake word. All None/empty until _sync_wake_word() starts
        # it (config-gated; the engine is optional). `wake_previews` is the
        # one-shot preview store the Type-it route consumes (HS-60-03).
        self._wake_listener: Any = None
        self._wake_stream: Any = None
        self._wake_queue: Any = None
        self.wake_previews: dict[str, dict[str, Any]] = {}
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
        self.cadence_thread: Optional[threading.Thread] = None  # CAD-1-04 (off by default)
        self._cadence_service_obj = None

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

    def _emit_audio_level(self, level: float, source: str) -> None:
        """Broadcast the additive `audio_level` WS frame, throttled to ~15 Hz.

        HS-69-08: the reactive mic waveform's source. The 0..1 level is already
        computed by the recorders (AudioRecorder.on_level / MeetingSession's
        on_mic_level / on_system_level); this just throttles + broadcasts it.
        Runs on the audio thread, so it stays cheap and never raises.
        """
        if self.server is None:
            return
        now = time.monotonic()
        if now - self._last_audio_level_ts < 0.066:  # ~15 Hz cap
            return
        self._last_audio_level_ts = now
        try:
            self.server.broadcast(
                "audio_level",
                {"level": max(0.0, min(1.0, float(level))), "source": source},
            )
        except Exception:  # pragma: no cover - a meter frame must never break capture
            pass

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
        try:
            self._sync_wake_word()
        except Exception as exc:
            log.debug(f"wake-word sync failed: {exc}")

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
                on_remote_dictation=self._deliver_remote_dictation,
                on_wake_type=self._type_wake_preview,
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
                host=_configured_web_host_from_env(),
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
        # The Cadence Engine tick — OFF BY DEFAULT (CAD-1-04). The thread starts only
        # when the user has opted in; otherwise the runtime is byte-identical to a
        # build without cadence.
        if self._cadence_enabled():
            self.cadence_thread = threading.Thread(
                target=self._cadence_loop,
                name="HoldSpeakCadenceEngine",
                daemon=True,
            )
            self.cadence_thread.start()
        self._warm_transcriber_in_background()

        try:
            self.recorder = AudioRecorder(
                device=self.config.meeting.mic_device,
                on_level=lambda level: self._emit_audio_level(level, "dictation"),
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

        # HS-60: the wake word (config-gated; a no-op when disabled).
        try:
            self._sync_wake_word()
        except Exception as exc:
            log.warning(f"Wake word unavailable: {exc}")

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
            self._stop_wake_listener()
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
            if self.cadence_thread is not None:
                self.cadence_thread.join(timeout=2.0)


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
