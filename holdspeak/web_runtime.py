"""Web-first runtime bootstrap for HoldSpeak."""

from __future__ import annotations

import hashlib
import os
import signal
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
from .device_recording_tick import RecordingTicker
from .device_meeting_stats import CYCLE_ORDER, pick_next_view
from .device_status import (
    DeviceStatusEmitter,
    push_intel_to_devices,
    push_segment_to_devices,
)
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
from .text_processor import TextProcessor
from .transcribe import Transcriber
from .typer import TextTyper
from .web_server import MeetingWebServer, _UnknownDeviceError

log = get_logger("web_runtime")


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


def run_web_runtime(
    *,
    no_open: bool = False,
    stop_event: Optional[threading.Event] = None,
    register_signal_handlers: bool = True,
) -> None:
    """Start HoldSpeak web runtime and keep it alive until stop."""
    import sys

    config = Config.load()
    runtime_started_at = datetime.now()
    runtime_stop_event = stop_event or threading.Event()
    state_lock = threading.Lock()
    meeting_lock = threading.Lock()
    bookmarks: list[dict[str, object]] = []
    pending_title: Optional[str] = None
    pending_tags: Optional[list[str]] = None
    last_meeting_snapshot: Optional[dict[str, object]] = None
    pending_intent_windows: list[dict[str, object]] = []
    pending_plugin_runs: list[dict[str, object]] = []
    preview_window_seq = 0
    mir_enabled = bool(getattr(config.meeting, "mir_enabled", False))
    mir_profile = normalize_profile(getattr(config.meeting, "mir_profile", None))
    mir_override_intents: list[str] = []
    last_route_preview: Optional[dict[str, object]] = None
    runtime_url: Optional[str] = None

    hotkey_listener: Optional[HotkeyListener] = None
    recorder: Optional[AudioRecorder] = None
    transcriber: Optional[Transcriber] = None
    server: Optional[MeetingWebServer] = None
    meeting_session: Optional[MeetingSession] = None
    device_registry = DeviceRegistry()
    device_status = DeviceStatusEmitter(label_lookup=device_registry)
    # HS-17-05: periodic Recording-tick emitter for attached devices.
    # Started in `_start_meeting`, stopped in `_stop_active_meeting`.
    recording_ticker = RecordingTicker(
        status_sender=lambda ids, text: device_status.broadcast(
            ids, text, ttl_ms=0
        ),
    )
    voice_session = VoiceTypingSession()
    transcription_lock = threading.Lock()
    text_processor = TextProcessor()
    from .activity_context import ActivityContextProvider

    plugin_host = PluginHost(default_timeout_seconds=0.35)
    plugin_host.register_context_provider(ActivityContextProvider(refresh=True, refresh_once=True))
    register_builtin_plugins(plugin_host)

    # Project knowledge-base detector (runs first in every chain)
    project_detector = ProjectDetectorPlugin()
    try:
        from .db import get_database as _get_db_for_projects
        project_detector.reload_projects(_get_db_for_projects().get_all_projects_for_detector())
    except Exception as _proj_init_err:
        log.warning(f"Could not load projects for detector at startup: {_proj_init_err}")
    plugin_host.register(project_detector)

    plugin_queue_thread: Optional[threading.Thread] = None

    try:
        typer: Optional[TextTyper] = TextTyper()
        text_injection_enabled = True
    except Exception as exc:
        typer = None
        text_injection_enabled = False
        log.warning(f"Text injection unavailable in web mode: {exc}")

    runtime_status: dict[str, object] = {
        "voice_state": "idle",
        "last_transcription": "",
        "last_error": "",
        "transcription_model": config.model.name,
        "transcription_warm_on_start": bool(getattr(config.model, "warm_on_start", True)),
        "transcription_status": "not_loaded",
        "transcription_error": "",
        "global_hotkey_available": False,
        "global_hotkey_error": "",
        "text_injection_enabled": text_injection_enabled,
        "text_injection_error": "" if text_injection_enabled else "TextTyper unavailable",
    }

    def _transcription_warm_on_start_enabled() -> bool:
        return bool(getattr(config.model, "warm_on_start", True))

    def _set_transcription_status(status: str, *, error: str = "") -> None:
        with state_lock:
            runtime_status["transcription_model"] = config.model.name
            runtime_status["transcription_warm_on_start"] = _transcription_warm_on_start_enabled()
            runtime_status["transcription_status"] = status
            runtime_status["transcription_error"] = error

    def _ensure_transcriber_loaded() -> Transcriber:
        nonlocal transcriber
        if transcriber is None or getattr(transcriber, "model_name", None) != config.model.name:
            _set_transcription_status("loading")
            try:
                transcriber = Transcriber(model_name=config.model.name, backend=config.model.backend)
            except Exception as exc:
                _set_transcription_status("error", error=f"{type(exc).__name__}: {exc}")
                raise
        _set_transcription_status("loaded")
        return transcriber

    def _warm_transcriber_in_background() -> None:
        if not _transcription_warm_on_start_enabled():
            return

        def _warm() -> None:
            with transcription_lock:
                try:
                    _ensure_transcriber_loaded()
                except Exception as exc:
                    _set_transcription_status("error", error=f"{type(exc).__name__}: {exc}")
                    with state_lock:
                        runtime_status["last_error"] = f"Transcription warmup failed: {exc}"
                    log.error(f"Transcription warmup failed: {exc}", exc_info=True)

        _set_transcription_status("warming")
        threading.Thread(
            target=_warm,
            name="HoldSpeakTranscriptionWarmup",
            daemon=True,
        ).start()

    def _active_meeting_session() -> Optional[MeetingSession]:
        with meeting_lock:
            session = meeting_session
        if session is None or not session.is_active:
            return None
        return session

    def _set_voice_state(value: str) -> None:
        with state_lock:
            runtime_status["voice_state"] = value

    def _normalize_tags(tags: Optional[list[str]]) -> list[str]:
        if not isinstance(tags, list):
            return []
        return [str(tag).strip().lower() for tag in tags if str(tag).strip()]

    def _meeting_summary_from_state(state: dict[str, object]) -> Optional[dict[str, object]]:
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

    def _mir_controls_payload() -> dict[str, object]:
        with state_lock:
            return {
                "enabled": bool(mir_enabled),
                "profile": str(mir_profile),
                "available_profiles": available_profiles(),
                "supported_intents": list(SUPPORTED_INTENTS),
                "override_intents": list(mir_override_intents),
                "last_preview": dict(last_route_preview) if isinstance(last_route_preview, dict) else None,
                "threshold": float(DEFAULT_INTENT_THRESHOLD),
            }

    def _runtime_idle_state() -> dict[str, object]:
        runtime_uptime = max(0.0, (datetime.now() - runtime_started_at).total_seconds())
        with state_lock:
            idle_title = pending_title or ""
            idle_tags = list(pending_tags) if pending_tags is not None else []
            runtime_snapshot = dict(runtime_status)
            mir_snapshot = {
                "enabled": bool(mir_enabled),
                "profile": str(mir_profile),
                "available_profiles": available_profiles(),
                "supported_intents": list(SUPPORTED_INTENTS),
                "override_intents": list(mir_override_intents),
                "last_preview": dict(last_route_preview) if isinstance(last_route_preview, dict) else None,
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
            "web_url": runtime_url,
            "runtime_started_at": runtime_started_at.isoformat(),
            "runtime_uptime": runtime_uptime,
            "bookmarks": list(bookmarks),
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
        }

    def _get_state() -> dict[str, object]:
        session = _active_meeting_session()
        if session is None:
            return _runtime_idle_state()

        state = session.state
        if state is None:
            return _runtime_idle_state()

        payload = state.to_dict()
        payload["mode"] = "web"
        payload["meeting_active"] = session.is_active
        payload["meeting_id"] = payload.get("id")
        payload["runtime_started_at"] = runtime_started_at.isoformat()
        payload["runtime_uptime"] = max(0.0, (datetime.now() - runtime_started_at).total_seconds())
        if runtime_url and not payload.get("web_url"):
            payload["web_url"] = runtime_url
        with state_lock:
            payload["runtime"] = dict(runtime_status)
        payload["mir"] = _mir_controls_payload()
        return payload

    def _broadcast_intel_status() -> None:
        if server is None:
            return
        state = _get_state()
        intel_status = state.get("intel_status")
        if intel_status is not None:
            server.broadcast("intel_status", intel_status)

    def _on_meeting_segment(segment) -> None:
        if server is not None:
            try:
                server.broadcast("segment", segment.to_dict())
            except Exception as exc:
                log.debug(f"Failed to broadcast segment: {exc}")
        # HS-17-08: push each finalized segment to attached AIPI-Lite
        # devices as a 3s flash so the LCD reflects what's being
        # transcribed in real time. No-op when no devices attached.
        try:
            active = _active_meeting_session()
            if active is not None and active.state is not None:
                attached_ids = [d.id for d in active.state.devices]
                push_segment_to_devices(device_status, attached_ids, segment)
        except Exception as exc:
            log.debug(f"Failed to push segment to device LCD: {exc}")

    def _on_meeting_intel(intel) -> None:
        if server is not None:
            try:
                server.broadcast("intel_complete", intel.to_dict())
            except Exception as exc:
                log.debug(f"Failed to broadcast intel_complete: {exc}")
        _broadcast_intel_status()
        # HS-17-07: push the intel summary to attached AIPI-Lite LCDs
        # so the user gets visible feedback when intel finishes (topics,
        # actions, summary — all landed in the middle slot).
        try:
            active = _active_meeting_session()
            if active is not None and active.state is not None:
                attached_ids = [d.id for d in active.state.devices]
                push_intel_to_devices(device_status, attached_ids, intel)
        except Exception as exc:
            log.debug(f"Failed to push intel to device LCD: {exc}")

    def _apply_updated_config(updated_config: Config) -> None:
        nonlocal config, transcriber
        previous_model = config.model.name
        config = updated_config
        model_changed = transcriber is not None and getattr(transcriber, "model_name", None) != config.model.name
        if model_changed:
            transcriber = None
        if previous_model != config.model.name or model_changed:
            _set_transcription_status("not_loaded")
        else:
            _set_transcription_status(
                "loaded" if transcriber is not None else "not_loaded",
                error="",
            )
        _warm_transcriber_in_background()
        if hotkey_listener is not None:
            try:
                hotkey_listener.hotkey = config.hotkey.key
            except Exception as exc:
                log.debug(f"Failed to apply runtime hotkey update: {exc}")
        if recorder is not None:
            recorder.device = config.meeting.mic_device

    def _start_meeting(*, devices: Optional[list[str]] = None) -> dict[str, object]:
        nonlocal meeting_session, transcriber, pending_title, pending_tags, preview_window_seq
        if _active_meeting_session() is not None:
            raise RuntimeError("Meeting already active")

        # Validate every requested device id is currently registered
        # *before* spinning up a session — surfaces 404 to the caller
        # without leaving an empty meeting on disk.
        device_pairs: list[tuple[object, object]] = []  # (descriptor, source)
        if devices:
            for device_id in devices:
                descriptor = device_registry.get(device_id)
                if descriptor is None:
                    raise _UnknownDeviceError(device_id)
                source = device_registry.recorder_for(device_id)
                if source is None:
                    raise _UnknownDeviceError(device_id)
                device_pairs.append((descriptor, source))

        if transcriber is None or getattr(transcriber, "model_name", None) != config.model.name:
            transcriber = _ensure_transcriber_loaded()

        session = MeetingSession(
            transcriber=transcriber,
            mic_label=config.meeting.mic_label,
            remote_label=config.meeting.remote_label,
            mic_device=config.meeting.mic_device,
            system_device=config.meeting.system_audio_device,
            on_segment=_on_meeting_segment,
            on_mic_level=lambda _level: None,
            on_system_level=lambda _level: None,
            on_intel=_on_meeting_intel,
            on_settings_applied=_apply_updated_config,
            intel_enabled=config.meeting.intel_enabled,
            intel_model_path=config.meeting.intel_realtime_model,
            intel_provider=config.meeting.intel_provider,
            intel_cloud_model=config.meeting.intel_cloud_model,
            intel_cloud_api_key_env=config.meeting.intel_cloud_api_key_env,
            intel_cloud_base_url=config.meeting.intel_cloud_base_url,
            intel_cloud_reasoning_effort=config.meeting.intel_cloud_reasoning_effort,
            intel_cloud_store=config.meeting.intel_cloud_store,
            intel_deferred_enabled=config.meeting.intel_deferred_enabled,
            web_enabled=False,
            diarization_enabled=config.meeting.diarization_enabled,
            diarize_mic=config.meeting.diarize_mic,
            cross_meeting_recognition=config.meeting.cross_meeting_recognition,
        )
        state = session.start()
        with state_lock:
            title_override = pending_title
            tags_override = list(pending_tags) if pending_tags is not None else None
            pending_title = None
            pending_tags = None
        if title_override is not None:
            session.set_title(title_override)
            state = session.state or state
        if tags_override is not None:
            session.set_tags(tags_override)
            state = session.state or state
        if runtime_url:
            state.web_url = runtime_url

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

        with meeting_lock:
            meeting_session = session

        if attached_ids:
            attached_for_status = [d for d in attached_ids if d]
            device_status.broadcast(
                attached_for_status,
                "Recording 00:00",
                ttl_ms=0,
            )
            # HS-17-05: schedule the periodic Recording-tick. The 0:00
            # paint above is done synchronously; subsequent ticks fire
            # every 5 s on a daemon thread that exits cleanly on
            # `_stop_active_meeting`.
            recording_ticker.start(
                started_at_monotonic=time.monotonic(),
                device_ids=attached_for_status,
            )
        with state_lock:
            pending_intent_windows.clear()
            pending_plugin_runs.clear()
            preview_window_seq = 0
        with state_lock:
            runtime_status["last_error"] = ""

        _broadcast_intel_status()
        return state.to_dict()

    def _stop_active_meeting(*, allow_runtime_fallback: bool) -> dict[str, object]:
        nonlocal meeting_session, last_meeting_snapshot
        session = _active_meeting_session()
        if session is None:
            if allow_runtime_fallback:
                runtime_stop_event.set()
                return {"status": "stopping_runtime"}
            raise RuntimeError("No active meeting")

        # HS-14-07: notify any attached devices that we are about to
        # stop and persist. Captured *before* ``session.stop`` flips
        # the state and clears the device list.
        attached_ids = [d.id for d in session.state.devices] if session.state else []
        # HS-17-05: stop the Recording-tick *before* the
        # `Saving meeting...` broadcast so a stale tick can't land
        # after the user has been told the meeting is saving.
        recording_ticker.stop()
        # AIPI-4-14: reset per-device cycle indexes so the next meeting
        # starts the double-tap rotation back at view 0.
        device_stats_cycle.clear()
        if attached_ids:
            device_status.broadcast(attached_ids, "Saving meeting...", ttl_ms=0)

        final_state = session.stop()
        final_state_payload = final_state.to_dict()
        meeting_id = str(final_state_payload.get("id") or "")
        with state_lock:
            last_meeting_snapshot = dict(final_state_payload)
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
            queue_flush = _flush_deferred_plugin_runs_to_db()
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
                mir_history = _persist_pending_mir_history(meeting_id)
                save_payload["intent_windows_saved"] = int(mir_history.get("intent_windows_saved") or 0)
                save_payload["plugin_runs_saved"] = int(mir_history.get("plugin_runs_saved") or 0)
                save_payload["mir_save_error"] = mir_history.get("error")
                artifacts_result = _synthesize_and_persist_artifacts(meeting_id)
                save_payload["artifacts_saved"] = int(artifacts_result.get("artifacts_saved") or 0)
                save_payload["artifact_synthesis_error"] = artifacts_result.get("error")
                project_result = _associate_meeting_with_projects(meeting_id)
                save_payload["projects_associated"] = int(project_result.get("projects_associated") or 0)
                save_payload["project_association_error"] = project_result.get("error")
        except Exception as exc:
            save_error = str(exc)
            log.error(f"Failed to save meeting from web runtime: {exc}")

        with meeting_lock:
            if meeting_session is session:
                meeting_session = None

        with state_lock:
            runtime_status["last_error"] = save_error or ""

        return {
            "status": "stopped",
            "meeting": final_state_payload,
            "save": save_payload,
            "save_error": save_error,
        }

    def _flush_deferred_plugin_runs_to_db() -> dict[str, object]:
        """Persist host-deferred heavy plugin jobs into DB queue storage."""
        queued_jobs = 0
        flush_error: Optional[str] = None
        try:
            from .db import get_database

            db = get_database()
            while True:
                queued_run = plugin_host.pop_next_deferred_run()
                if queued_run is None:
                    break
                db.enqueue_plugin_run_job(
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

    def _process_deferred_plugin_queue_once(*, include_scheduled: bool = False) -> bool:
        """Run one deferred MIR queue job if available."""
        if _active_meeting_session() is not None:
            return False
        try:
            from .db import get_database

            db = get_database()
            return process_next_plugin_run_job(
                host=plugin_host,
                db=db,
                include_scheduled=include_scheduled,
            )
        except Exception as exc:
            log.error(f"Deferred MIR queue processing failed: {exc}")
            return False

    def _process_deferred_plugin_queue(
        *,
        max_jobs: Optional[int] = None,
        include_scheduled: bool = False,
    ) -> dict[str, object]:
        """Drain deferred MIR queue through runtime-owned plugin host."""
        if _active_meeting_session() is not None:
            return {"processed": 0, "skipped_active_meeting": True}
        try:
            from .db import get_database

            db = get_database()
            processed = drain_plugin_run_queue(
                host=plugin_host,
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

    def _deferred_plugin_queue_loop() -> None:
        while not runtime_stop_event.is_set():
            processed = _process_deferred_plugin_queue_once()
            if processed:
                continue
            runtime_stop_event.wait(0.6)

    def _get_runtime_status() -> dict[str, object]:
        state = _get_state()
        runtime = state.get("runtime") if isinstance(state.get("runtime"), dict) else {}
        meeting_active = bool(state.get("meeting_active"))
        meeting = _meeting_summary_from_state(state)
        with state_lock:
            last_meeting = dict(last_meeting_snapshot) if isinstance(last_meeting_snapshot, dict) else None
            runtime_snapshot = dict(runtime_status)
        return {
            "status": "ok",
            "mode": "web",
            "url": runtime_url,
            "meeting_active": meeting_active,
            "meeting_id": state.get("id") if meeting_active else None,
            "meeting": meeting,
            "last_meeting": last_meeting,
            "voice_state": runtime.get("voice_state", runtime_snapshot.get("voice_state", "idle")),
            "text_injection_enabled": runtime_snapshot.get("text_injection_enabled"),
            "text_injection_error": runtime_snapshot.get("text_injection_error", ""),
            "transcription": {
                "model": runtime_snapshot.get("transcription_model", config.model.name),
                "warm_on_start": runtime_snapshot.get("transcription_warm_on_start", False),
                "status": runtime_snapshot.get("transcription_status", "not_loaded"),
                "error": runtime_snapshot.get("transcription_error", ""),
            },
            "mir": _mir_controls_payload(),
            "state": state,
        }

    def _on_bookmark(label: str) -> dict[str, object]:
        session = _active_meeting_session()
        if session is not None:
            bookmark = session.add_bookmark(label=label, auto_label=not bool(label))
            if bookmark is not None:
                attached_ids = [d.id for d in session.state.devices] if session.state else []
                if attached_ids:
                    device_status.broadcast(
                        attached_ids,
                        f"Bookmark @ {bookmark.timestamp:.0f}s",
                        ttl_ms=2500,
                    )
                return bookmark.to_dict()
            raise RuntimeError("No active meeting")

        entry = {
            "timestamp": max(0.0, (datetime.now() - runtime_started_at).total_seconds()),
            "label": label or "",
        }
        with state_lock:
            bookmarks.append(entry)
        return entry

    def _on_stop() -> dict[str, object]:
        return _stop_active_meeting(allow_runtime_fallback=True)

    def _on_meeting_stop() -> dict[str, object]:
        return _stop_active_meeting(allow_runtime_fallback=False)

    def _on_update_meeting(*, title: Optional[str], tags: Optional[list[str]]) -> dict[str, object]:
        nonlocal pending_title, pending_tags
        session = _active_meeting_session()
        clean_tags = _normalize_tags(tags) if tags is not None else None

        if session is not None:
            if title is not None:
                session.set_title(title)
            if clean_tags is not None:
                session.set_tags(clean_tags)
            state = session.state
            return state.to_dict() if state is not None else _runtime_idle_state()

        with state_lock:
            if title is not None:
                pending_title = str(title).strip()
            if clean_tags is not None:
                pending_tags = clean_tags
        return _runtime_idle_state()

    def _on_process_plugin_jobs(
        *,
        max_jobs: Optional[int],
        include_scheduled: bool,
    ) -> dict[str, object]:
        queue_flush = _flush_deferred_plugin_runs_to_db()
        queue_result = _process_deferred_plugin_queue(
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

    def _infer_intent_scores(*, transcript: Optional[str], tags: Optional[list[str]]) -> dict[str, float]:
        return extract_intent_signals(transcript, tags=tags)

    def _derive_preview_transcript_hash(
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
        *,
        transcript: Optional[str],
        route_payload: dict[str, object],
    ) -> Optional[dict[str, object]]:
        nonlocal preview_window_seq
        session = _active_meeting_session()
        if session is None:
            return None

        state = session.state
        if state is None:
            return None

        meeting_id = str(state.id or "").strip()
        if not meeting_id:
            return None

        preview_window_seq += 1
        transcript_hash, transcript_excerpt = _derive_preview_transcript_hash(
            transcript=transcript,
            intent_scores=route_payload.get("intent_scores") if isinstance(route_payload.get("intent_scores"), dict) else None,
        )
        state_payload = state.to_dict()
        end_seconds = float(state_payload.get("duration") or 0.0)
        start_seconds = max(0.0, end_seconds - 90.0)
        return {
            "meeting_id": meeting_id,
            "window_id": f"{meeting_id}:preview-{preview_window_seq:04d}",
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "transcript_hash": transcript_hash,
            "transcript_excerpt": transcript_excerpt,
        }

    def _record_route_preview_history(
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

        with state_lock:
            pending_intent_windows.append(
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
                pending_plugin_runs.append(
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

    def _persist_pending_mir_history(meeting_id: str) -> dict[str, object]:
        with state_lock:
            windows_to_save = [dict(item) for item in pending_intent_windows if str(item.get("meeting_id")) == meeting_id]
            runs_to_save = [dict(item) for item in pending_plugin_runs if str(item.get("meeting_id")) == meeting_id]
            pending_intent_windows[:] = [
                item for item in pending_intent_windows if str(item.get("meeting_id")) != meeting_id
            ]
            pending_plugin_runs[:] = [
                item for item in pending_plugin_runs if str(item.get("meeting_id")) != meeting_id
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
                db.record_intent_window(**record)
                saved_windows += 1
            for record in runs_to_save:
                db.record_plugin_run(**record)
                saved_runs += 1
        except Exception as exc:
            save_error = str(exc)
            log.error(f"Failed to persist MIR history for meeting {meeting_id}: {exc}")

        return {
            "intent_windows_saved": saved_windows,
            "plugin_runs_saved": saved_runs,
            "error": save_error,
        }

    def _synthesize_and_persist_artifacts(meeting_id: str) -> dict[str, object]:
        clean_meeting_id = str(meeting_id).strip()
        if not clean_meeting_id:
            return {"artifacts_saved": 0, "error": None}

        try:
            from .db import get_database
            from .plugins.synthesis import synthesize_meeting_artifacts

            db = get_database()
            runs = db.list_plugin_runs(clean_meeting_id, limit=5000)
            artifacts = synthesize_meeting_artifacts(
                meeting_id=clean_meeting_id,
                plugin_runs=runs,
                max_artifacts=500,
            )
            for artifact in artifacts:
                db.record_artifact(
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

    def _associate_meeting_with_projects(meeting_id: str) -> dict[str, object]:
        """Auto-associate a meeting with projects based on project_detector plugin runs."""
        clean_meeting_id = str(meeting_id).strip()
        if not clean_meeting_id:
            return {"projects_associated": 0, "error": None}

        try:
            from .db import get_database
            db = get_database()
            runs = db.list_plugin_runs(clean_meeting_id, limit=5000)

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
                    db.log_project_detection(
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
                    db.associate_meeting_project(
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

    def _on_get_intent_controls() -> dict[str, object]:
        return _mir_controls_payload()

    def _on_set_intent_profile(profile: str) -> dict[str, object]:
        nonlocal mir_profile
        with state_lock:
            mir_profile = normalize_profile(profile)
        return _mir_controls_payload()

    def _on_set_intent_override(intents: Optional[list[str]]) -> dict[str, object]:
        nonlocal mir_override_intents
        with state_lock:
            mir_override_intents = normalize_override_intents(intents)
        return _mir_controls_payload()

    def _on_route_preview(
        *,
        profile: Optional[str] = None,
        threshold: Optional[float] = None,
        intent_scores: Optional[dict[str, float]] = None,
        override_intents: Optional[list[str]] = None,
        previous_intents: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        transcript: Optional[str] = None,
    ) -> dict[str, object]:
        nonlocal last_route_preview

        controls = _mir_controls_payload()
        profile_value = normalize_profile(profile or str(controls.get("profile") or ""))
        threshold_value = DEFAULT_INTENT_THRESHOLD if threshold is None else float(threshold)

        inferred_scores = _infer_intent_scores(transcript=transcript, tags=tags)
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
        window_context = _build_active_preview_window_context(
            transcript=transcript,
            route_payload=route_payload,
        )
        transcript_hash, _ = _derive_preview_transcript_hash(
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
        run_results = plugin_host.execute_chain(
            list(route_payload.get("plugin_chain") or []),
            context=execution_context,
            meeting_id=execution_meeting_id,
            window_id=execution_window_id,
            transcript_hash=transcript_hash,
        )
        route_payload["plugin_runs"] = [result.to_dict() for result in run_results]
        queue_flush = _flush_deferred_plugin_runs_to_db()
        route_payload["deferred_queue_jobs"] = int(queue_flush.get("queued_jobs") or 0)
        if queue_flush.get("error"):
            route_payload["deferred_queue_error"] = str(queue_flush["error"])

        if isinstance(window_context, dict):
            _record_route_preview_history(
                route_payload=route_payload,
                tags=tags,
                window_context=window_context,
                plugin_runs=route_payload["plugin_runs"],  # type: ignore[arg-type]
            )

        with state_lock:
            last_route_preview = dict(route_payload)

        return route_payload

    def _on_update_action_item(item_id: str, status: str):
        session = _active_meeting_session()
        if session is None:
            return None
        return session.update_action_item(item_id, status)

    def _on_update_action_item_review(item_id: str, review_state: str):
        session = _active_meeting_session()
        if session is None:
            return None
        return session.update_action_item_review(item_id, review_state)

    def _on_edit_action_item(item_id: str, *, task: str, owner: Optional[str], due: Optional[str]):
        session = _active_meeting_session()
        if session is None:
            return None
        return session.edit_action_item(item_id, task=task, owner=owner, due=due)

    def _transcribe_and_type(
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
        with transcription_lock:
            try:
                text = _ensure_transcriber_loaded().transcribe(audio)
                if not text:
                    return
                text = text_processor.process(text)
                text = _maybe_run_dictation_pipeline(
                    text,
                    audio_duration_s=len(audio) / 16000.0,
                    transcribed_at=datetime.now(),
                    agent_reply_session=agent_reply_session,
                )
                completed_text = text
                with state_lock:
                    runtime_status["last_transcription"] = text
                    runtime_status["last_error"] = ""
                print(f"-> {text}")
                delivered = _try_tmux_agent_reply(text, agent_reply_session)
                if not delivered and typer is not None:
                    try:
                        paste_target_profile = _paste_target_profile(agent_reply_session)
                        typer.type_text(
                            text,
                            target_profile=paste_target_profile,
                            submit=agent_reply_session is not None,
                        )
                    except Exception as exc:
                        with state_lock:
                            runtime_status["last_error"] = f"Typing failed: {exc}"
                            runtime_status["text_injection_enabled"] = False
                            runtime_status["text_injection_error"] = f"{type(exc).__name__}: {exc}"
                        log.warning(f"Typing failed in web mode: {exc}")
            except Exception as exc:
                with state_lock:
                    runtime_status["last_error"] = f"Transcription failed: {exc}"
                log.error(f"Transcription failed in web mode: {exc}")
            finally:
                _set_voice_state("idle")
        if on_complete is not None and completed_text is not None:
            try:
                on_complete(completed_text)
            except Exception as exc:
                log.warning(f"on_complete hook raised: {exc}")

    def _kick_off_transcribe(
        audio: np.ndarray,
        *,
        on_complete: Optional[Callable[[str], None]] = None,
        agent_reply_session: Any | None = None,
    ) -> None:
        if len(audio) < 1600:
            _set_voice_state("idle")
            return
        _set_voice_state("transcribing")
        threading.Thread(
            target=lambda: _transcribe_and_type(
                audio,
                on_complete=on_complete,
                agent_reply_session=agent_reply_session,
            ),
            daemon=True,
        ).start()

    def _maybe_run_dictation_pipeline(
        text: str,
        *,
        audio_duration_s: float,
        transcribed_at: datetime,
        agent_reply_session: Any | None = None,
    ) -> str:
        dictation_cfg = getattr(config, "dictation", None)
        pipeline_cfg = getattr(dictation_cfg, "pipeline", None)
        if dictation_cfg is None or pipeline_cfg is None or not bool(getattr(pipeline_cfg, "enabled", False)):
            return text

        try:
            from holdspeak.activity_context import build_activity_context
            from holdspeak.agent_context import get_recent_agent_session
            from holdspeak.agent_device import target_profile_override_for_agent
            from holdspeak.plugins.dictation.assembly import build_pipeline
            from holdspeak.plugins.dictation.contracts import Utterance
            from holdspeak.plugins.dictation.project_root import detect_project_for_cwd
            from holdspeak.target_profile import detect_active_target_profile

            if agent_reply_session is not None and getattr(agent_reply_session, "cwd", None):
                project = detect_project_for_cwd(
                    Path(str(agent_reply_session.cwd)),
                    prefer_agent_session=False,
                )
            else:
                project = detect_project_for_cwd()
            project_root = Path(project["root"]) if project else None
            result = build_pipeline(dictation_cfg, project_root=project_root)
            if result.runtime_status != "loaded":
                return text

            target_override = (
                target_profile_override_for_agent(agent_reply_session)
                or getattr(pipeline_cfg, "target_profile_override", "auto")
            )
            activity = build_activity_context(limit=20, refresh=False).to_dict()
            activity["target"] = detect_active_target_profile(target_override).to_dict()
            recent_agent = agent_reply_session or get_recent_agent_session(max_age_seconds=120)
            if recent_agent is not None and bool(getattr(recent_agent, "awaiting_response", False)):
                agent_project_root = getattr(recent_agent, "repo_root", None)
                if not project_root or not agent_project_root or str(project_root) == str(agent_project_root):
                    activity["agent"] = recent_agent.to_dict()

            run = result.pipeline.run(
                Utterance(
                    raw_text=text,
                    audio_duration_s=audio_duration_s,
                    transcribed_at=transcribed_at,
                    project=project,
                    activity=activity,
                )
            )
            return run.final_text
        except Exception as exc:
            log.warning(f"Web dictation pipeline raised; falling back to processed text: {exc}")
            return text

    def _paste_target_profile(agent_reply_session: Any | None) -> str | None:
        if agent_reply_session is None:
            return None
        try:
            from holdspeak.agent_device import target_profile_override_for_agent

            return target_profile_override_for_agent(agent_reply_session)
        except Exception:
            return None

    def _try_tmux_agent_reply(text: str, agent_reply_session: Any | None) -> bool:
        pane = _agent_tmux_pane(agent_reply_session)
        if not pane:
            return False
        try:
            from holdspeak.tmux_transport import send_text_to_pane

            send_text_to_pane(pane=pane, text=text, submit=True)
            return True
        except Exception as exc:
            with state_lock:
                runtime_status["last_error"] = f"tmux reply failed; fell back to typing: {exc}"
            log.warning(f"tmux reply failed; falling back to text injection: {exc}")
            return False

    def _agent_tmux_pane(agent_reply_session: Any | None) -> str | None:
        if agent_reply_session is None:
            return None
        pane = getattr(agent_reply_session, "tmux_pane", None)
        return str(pane).strip() if pane else None

    def _agent_reply_deliverable(agent_reply_session: Any | None) -> bool:
        if agent_reply_session is None:
            return True
        if _agent_tmux_pane(agent_reply_session):
            return True
        return typer is not None

    def _on_hotkey_press() -> None:
        if runtime_stop_event.is_set():
            return
        if _active_meeting_session() is not None:
            return
        if recorder is None:
            return
        try:
            accepted = voice_session.begin(recorder, owner="hotkey")
        except Exception as exc:
            with state_lock:
                runtime_status["last_error"] = f"Recording failed: {exc}"
            _set_voice_state("idle")
            log.error(f"Recording failed in web mode: {exc}")
            return
        if not accepted:
            log.info("hotkey_press_ignored_session_active")
            return
        _set_voice_state("recording")

    def _on_hotkey_release() -> None:
        if _active_meeting_session() is not None:
            _set_voice_state("idle")
            return
        try:
            audio = voice_session.end(owner="hotkey")
        except Exception as exc:
            with state_lock:
                runtime_status["last_error"] = f"Recording error: {exc}"
            _set_voice_state("idle")
            log.error(f"Recording error in web mode: {exc}")
            return
        if audio is None:
            _set_voice_state("idle")
            return

        _kick_off_transcribe(audio)

    def _on_device_voice_start(device_id: str, source: AudioSource) -> bool:
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
        active_meeting = _active_meeting_session()
        if active_meeting is not None:
            if active_meeting.is_device_attached(device_id):
                return True
            return False
        from .agent_context import get_recent_awaiting_agent_session

        agent_reply_session = get_recent_awaiting_agent_session(max_age_seconds=120)
        if not _agent_reply_deliverable(agent_reply_session):
            with state_lock:
                runtime_status["last_error"] = "Agent reply target unavailable"
            device_status.send(device_id, "No reply target", ttl_ms=3000)
            log.info(
                "device_voice_start_rejected_no_agent_reply_target",
                extra={"device_id": device_id},
            )
            return False
        owner = f"device:{device_id}"
        try:
            accepted = voice_session.begin(source, owner=owner)
        except Exception as exc:
            log.error(f"Device voice-typing start failed: {exc}")
            return False
        if not accepted:
            return False
        _set_voice_state("recording")
        # AIPI-4-13: TX state lives in the device's firmware-side
        # tx_label glyph (top-right, ↑ during right-button hold).
        # No "Listening..." pushback — would clobber the bottom
        # widget's persistent meeting/idle text.
        return True

    def _on_device_voice_stop(
        device_id: str, source: AudioSource
    ) -> Optional[np.ndarray]:
        active_meeting = _active_meeting_session()
        if active_meeting is not None and active_meeting.is_device_attached(device_id):
            # The meeting owns this device's audio routing.
            return None
        owner = f"device:{device_id}"
        try:
            audio = voice_session.end(owner=owner)
        except Exception as exc:
            log.error(f"Device voice-typing stop failed: {exc}")
            _set_voice_state("idle")
            return None
        if audio is None:
            _set_voice_state("idle")
            return None

        # AIPI-4-13: no "Thinking..." pushback to bottom — the absent
        # tx_label arrow after release already signals "we're done
        # capturing, processing now". Transcript snippet lands in
        # the middle slot below.

        from .agent_context import get_recent_awaiting_agent_session

        agent_reply_session = get_recent_awaiting_agent_session(max_age_seconds=120)

        def _device_transcript_complete(text: str) -> None:
            snippet = (text or "").strip()[:150]
            device_status.send(device_id, snippet, ttl_ms=4000)

        _kick_off_transcribe(
            audio,
            on_complete=_device_transcript_complete,
            agent_reply_session=agent_reply_session,
        )
        return audio

    def _on_device_voice_cancel(device_id: str) -> None:
        voice_session.cancel(owner=f"device:{device_id}")

    # AIPI-4-14: per-device cycle index for the meeting-stats double-tap
    # rotation. ``-1`` means "advance to view 0 on the next double-tap".
    # Reset whenever a meeting ends so each new meeting starts at view 0.
    device_stats_cycle: dict[str, int] = {}

    def _on_device_event(device_id: str, name: str, at: Optional[float]) -> None:
        """Inbound device event from the WS.

        - ``long_press`` (HS-14-07): bookmark gesture in an active
          meeting where this device is attached.
        - ``double_left_click`` (AIPI-4-14): cycle through meeting-stat
          views (Numbers → Speakers → Intel) on the device's middle
          slot.
        """
        if name == "long_press":
            active = _active_meeting_session()
            if active is None or not active.is_device_attached(device_id):
                return
            bookmark = active.add_bookmark(label="", auto_label=True)
            if bookmark is None:
                return
            attached_ids = [d.id for d in active.state.devices] if active.state else []
            device_status.broadcast(
                attached_ids,
                f"Bookmark @ {bookmark.timestamp:.0f}s",
                ttl_ms=2500,
            )
            return

        if name == "double_left_click":
            active = _active_meeting_session()
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
            current = device_stats_cycle.get(device_id, -1)
            next_index, view_id, formatter = pick_next_view(current)
            device_stats_cycle[device_id] = next_index
            payload = formatter(active.state)
            device_status.send(device_id, payload, ttl_ms=4000)
            log.info(
                "device_event_double_tap_cycled",
                extra={"device_id": device_id, "view": view_id, "index": next_index},
            )
            return

        log.info(
            "device_event_ignored",
            extra={"device_id": device_id, "event_name": name},
        )

    def _on_device_health(descriptor: object) -> None:
        active = _active_meeting_session()
        if active is None:
            return
        updater = getattr(active, "update_device_descriptor", None)
        if callable(updater):
            updater(descriptor)
        if server is not None:
            try:
                from .meeting_session import _device_descriptor_to_dict

                server.broadcast("device_health", _device_descriptor_to_dict(descriptor))
            except Exception as exc:
                log.debug(f"Failed to broadcast device health: {exc}")

    def _on_device_query(
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
        active = _active_meeting_session()
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

    try:
        server = MeetingWebServer(
            on_bookmark=_on_bookmark,
            on_stop=_on_stop,
            on_start=_start_meeting,
            on_meeting_stop=_on_meeting_stop,
            on_get_status=_get_runtime_status,
            on_update_meeting=_on_update_meeting,
            on_get_intent_controls=_on_get_intent_controls,
            on_set_intent_profile=_on_set_intent_profile,
            on_set_intent_override=_on_set_intent_override,
            on_route_preview=_on_route_preview,
            on_process_plugin_jobs=_on_process_plugin_jobs,
            get_state=_get_state,
            on_update_action_item=_on_update_action_item,
            on_update_action_item_review=_on_update_action_item_review,
            on_edit_action_item=_on_edit_action_item,
            on_settings_applied=_apply_updated_config,
            project_detector=project_detector,
            device_registry=device_registry,
            device_psk_provider=lambda: ensure_device_psk(config),
            on_device_voice_start=_on_device_voice_start,
            on_device_voice_stop=_on_device_voice_stop,
            on_device_voice_cancel=_on_device_voice_cancel,
            device_status_emitter=device_status,
            on_device_event=_on_device_event,
            on_device_health=_on_device_health,
            on_device_query=_on_device_query,
            host="127.0.0.1",
            port=_configured_web_port_from_env(),
        )
        runtime_url = server.start()
    except Exception as exc:
        print(f"Failed to start HoldSpeak web mode: {exc}", file=sys.stderr)
        print("Install optional web dependencies with: uv pip install -e '.[meeting]'", file=sys.stderr)
        print("Fallback option: run `holdspeak tui`.", file=sys.stderr)
        log.error(f"Failed to start web mode: {exc}", exc_info=True)
        raise SystemExit(1) from exc

    plugin_queue_thread = threading.Thread(
        target=_deferred_plugin_queue_loop,
        name="HoldSpeakMirPluginQueue",
        daemon=True,
    )
    plugin_queue_thread.start()
    _warm_transcriber_in_background()

    try:
        recorder = AudioRecorder(
            device=config.meeting.mic_device,
            on_level=lambda _level: None,
        )
        hotkey_listener = HotkeyListener(
            on_press=_on_hotkey_press,
            on_release=_on_hotkey_release,
            hotkey=config.hotkey.key,
        )
        hotkey_listener.start()
        with state_lock:
            runtime_status["global_hotkey_available"] = True
            runtime_status["global_hotkey_error"] = ""
    except Exception as exc:
        hotkey_listener = None
        recorder = None
        with state_lock:
            runtime_status["global_hotkey_available"] = False
            runtime_status["global_hotkey_error"] = f"{type(exc).__name__}: {exc}"
            runtime_status["last_error"] = f"Global hotkey unavailable: {exc}"
        log.warning(f"Global hotkey unavailable in web mode: {exc}")

    log.info(f"HoldSpeak web runtime active at {runtime_url}")
    print(f"HoldSpeak web runtime is running at: {runtime_url}")
    print(f"History and settings are available at: {runtime_url}/history")
    if hotkey_listener is not None:
        print(f"Voice typing hotkey is active: hold {config.hotkey.display}, speak, release.")
    else:
        print("Voice typing hotkey unavailable in web mode; check permissions or use `holdspeak tui` focused hold-to-talk.")
    if not no_open and config.meeting.web_auto_open:
        webbrowser.open(runtime_url)
        print("Opened web dashboard in your default browser.")
    elif no_open:
        print("Headless mode active (`--no-open`): browser auto-open disabled.")
    else:
        print("Browser auto-open is disabled in config (`meeting.web_auto_open=false`).")
    print("Press Ctrl+C to stop.")

    def _signal_handler(sig, frame) -> None:
        _ = sig, frame
        runtime_stop_event.set()

    if register_signal_handlers:
        signal.signal(signal.SIGINT, _signal_handler)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, _signal_handler)

    try:
        while not runtime_stop_event.wait(0.2):
            pass
    finally:
        _flush_deferred_plugin_runs_to_db()
        if hotkey_listener is not None:
            hotkey_listener.stop()
        active = _active_meeting_session()
        if active is not None:
            try:
                final_state = active.stop()
                active.save()
                if getattr(final_state, "id", None):
                    meeting_id = str(final_state.id)
                    _persist_pending_mir_history(meeting_id)
                    _synthesize_and_persist_artifacts(meeting_id)
            except Exception as exc:
                log.error(f"Failed to finalize active meeting during shutdown: {exc}")
        if server is not None:
            server.stop()
        if plugin_queue_thread is not None:
            plugin_queue_thread.join(timeout=2.0)
