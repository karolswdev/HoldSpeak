"""System surface routes (HS-26-05): device health, runtime + companion status,
settings, and the `/ws` broadcast socket.

Handlers move verbatim (`self.` -> `ctx.`). The runtime-status normalizer and the
settings validators are used only here, so they were relocated out of `web_server`.
The device-audio WebSocket keeps its own PSK handshake in `device_audio_ws.py`
(registered in `_create_app`) and is unaffected.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.system")

# Validates outbound webhook header names on the settings PUT path.
_HTTP_HEADER_NAME_RE = re.compile(r"^[A-Za-z0-9-]+$")

# The active reply target stays fresh (matches the device path in web_runtime),
# but the companion overview shows a wider window so the user can see — and
# recover from — sessions that have gone stale.
_COMPANION_TARGET_MAX_AGE_SECONDS = 120
_COMPANION_OVERVIEW_MAX_AGE_SECONDS = 30 * 60


def _session_age_seconds(stamp: Optional[str], now: datetime) -> Optional[int]:
    """Seconds since an ISO-8601 session timestamp, or None if unparseable."""
    if not isinstance(stamp, str) or not stamp.strip():
        return None
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max(0, int((now - parsed).total_seconds()))


def _meeting_active_from_state(state: dict[str, Any]) -> bool:
    if isinstance(state.get("meeting_active"), bool):
        return bool(state.get("meeting_active"))
    return bool(state.get("started_at")) and not bool(state.get("ended_at"))


def _meeting_summary_from_state(state: dict[str, Any]) -> Optional[dict[str, Any]]:
    if not _meeting_active_from_state(state):
        return None
    meeting_id = state.get("id")
    if not meeting_id:
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


def _normalize_runtime_status_payload(raw_payload: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    payload = dict(raw_payload)
    payload_state = payload.get("state")
    if not isinstance(payload_state, dict):
        payload_state = state
    meeting_active = (
        bool(payload.get("meeting_active"))
        if isinstance(payload.get("meeting_active"), bool)
        else _meeting_active_from_state(payload_state)
    )
    payload["status"] = payload.get("status") or "ok"
    payload["mode"] = payload.get("mode") or "web"
    payload["meeting_active"] = meeting_active
    payload["state"] = payload_state
    if "meeting_id" not in payload:
        payload["meeting_id"] = payload_state.get("id") if meeting_active else None
    if "meeting" not in payload:
        payload["meeting"] = _meeting_summary_from_state(payload_state)
    return payload


def _validate_cloud_base_url(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("intel_cloud_base_url must start with http:// or https://")
    return raw


def _merge_dict(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(dst.get(key), dict):
            _merge_dict(dst[key], value)
        else:
            dst[key] = value
    return dst


def build_system_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/devices/health")
    async def api_devices_health() -> Any:
        from ...meeting_session import _device_descriptor_to_dict

        devices = [
            _device_descriptor_to_dict(descriptor)
            for descriptor in ctx.device_registry.active()
        ]
        return JSONResponse({"devices": devices})

    @router.get("/api/runtime/status")
    async def api_runtime_status() -> Any:
        try:
            state = ctx.get_state() or {}
        except Exception as e:
            log.error(f"get_state failed: {e}")
            state = {}

        if ctx.on_get_status is not None:
            try:
                raw_payload = ctx.on_get_status()
            except Exception as e:
                log.error(f"on_get_status failed: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)
            if isinstance(raw_payload, dict):
                return JSONResponse(_normalize_runtime_status_payload(raw_payload, state))
            return JSONResponse({"status": "ok", "runtime_status": raw_payload})

        return JSONResponse(_normalize_runtime_status_payload({}, state))

    @router.get("/api/companion/status")
    async def api_companion_status() -> Any:
        """Return one debug snapshot for the AIPI agent companion loop."""
        from ...agent_context import (
            DEFAULT_STALE_AGENT_SESSION_SECONDS,
            get_recent_awaiting_agent_session,
            list_recent_awaiting_agent_sessions,
        )
        from ...agent_device import AGENT_QUERY_NAMES, build_agent_identity_payload
        from ...config import Config
        from ...meeting_session import _device_descriptor_to_dict

        try:
            state = ctx.get_state() or {}
        except Exception as e:
            log.error(f"get_state failed: {e}")
            state = {}

        runtime_error: str | None = None
        if ctx.on_get_status is not None:
            try:
                raw_payload = ctx.on_get_status()
                if isinstance(raw_payload, dict):
                    runtime_payload = _normalize_runtime_status_payload(raw_payload, state)
                else:
                    runtime_payload = _normalize_runtime_status_payload(
                        {"runtime_status": raw_payload},
                        state,
                    )
            except Exception as e:
                log.error(f"on_get_status failed: {e}")
                runtime_error = str(e)
                runtime_payload = _normalize_runtime_status_payload({}, state)
        else:
            runtime_payload = _normalize_runtime_status_payload({}, state)

        devices = [
            _device_descriptor_to_dict(descriptor)
            for descriptor in ctx.device_registry.active()
        ]
        device_connected = bool(devices)

        agent_error: str | None = None
        try:
            session = get_recent_awaiting_agent_session(
                max_age_seconds=_COMPANION_TARGET_MAX_AGE_SECONDS
            )
            agent_sessions = list_recent_awaiting_agent_sessions(
                max_age_seconds=_COMPANION_OVERVIEW_MAX_AGE_SECONDS,
                limit=8,
            )
        except Exception as e:
            log.error(f"agent companion status failed: {e}")
            agent_error = str(e)
            session = None
            agent_sessions = []
        agent_waiting = bool(session and session.awaiting_response)
        tmux_reply_available = bool(
            session
            and session.awaiting_response
            and getattr(session, "tmux_pane", None)
        )

        dictation_error: str | None = None
        try:
            dictation_cfg = Config.load().dictation
            pipeline_enabled = bool(dictation_cfg.pipeline.enabled)
            pipeline_stages = list(dictation_cfg.pipeline.stages)
            target_profile_override = dictation_cfg.pipeline.target_profile_override
            runtime_backend = dictation_cfg.runtime.backend
        except Exception as e:
            log.error(f"dictation config load failed: {e}")
            dictation_error = str(e)
            pipeline_enabled = False
            pipeline_stages = []
            target_profile_override = None
            runtime_backend = None

        text_injection_known = "text_injection_enabled" in runtime_payload
        text_injection_enabled = (
            bool(runtime_payload.get("text_injection_enabled"))
            if text_injection_known
            else None
        )
        agent_identity = build_agent_identity_payload(
            session,
            text_injection_enabled=text_injection_enabled,
        )
        if session is not None and not any(
            item.agent == session.agent and item.session_id == session.session_id
            for item in agent_sessions
        ):
            agent_sessions.insert(0, session)
        selected_agent_key = (
            (session.agent, session.session_id) if session is not None else None
        )
        agent_session_items = []
        selected_index: int | None = None
        status_now = datetime.now(timezone.utc)
        for index, item in enumerate(agent_sessions):
            item_key = (item.agent, item.session_id)
            selected = item_key == selected_agent_key
            if selected:
                selected_index = index
            age_seconds = _session_age_seconds(item.updated_at, status_now)
            # Pinned sessions are intentionally kept; never badge them stale.
            stale = (
                not item.pinned
                and age_seconds is not None
                and age_seconds > DEFAULT_STALE_AGENT_SESSION_SECONDS
            )
            agent_session_items.append(
                {
                    "index": index,
                    "selected": selected,
                    "pinned": item.pinned,
                    "stale": stale,
                    "age_seconds": age_seconds,
                    "session": item.to_dict(),
                    "identity": build_agent_identity_payload(
                        item,
                        text_injection_enabled=text_injection_enabled,
                    ),
                }
            )

        blockers: list[str] = []
        if not device_connected:
            blockers.append("no_device_connected")
        if not agent_waiting:
            blockers.append("no_agent_waiting")
        if not pipeline_enabled:
            blockers.append("dictation_pipeline_disabled")
        if text_injection_enabled is False and not tmux_reply_available:
            blockers.append("text_injection_unavailable")
        elif text_injection_enabled is None and not tmux_reply_available:
            blockers.append("text_injection_status_unknown")
        if agent_error:
            blockers.append("agent_status_unavailable")
        if dictation_error:
            blockers.append("dictation_config_unavailable")
        if runtime_error:
            blockers.append("runtime_status_unavailable")

        return JSONResponse(
            {
                "status": "ok",
                "ready_for_agent_reply": not blockers,
                "blockers": blockers,
                "checks": {
                    "device_connected": device_connected,
                    "agent_waiting": agent_waiting,
                    "dictation_pipeline_enabled": pipeline_enabled,
                    "text_injection_enabled": text_injection_enabled,
                    "tmux_reply_available": tmux_reply_available,
                    "target_confidence": (
                        agent_identity["target_confidence"] if agent_identity else None
                    ),
                },
                "devices": {
                    "connected": device_connected,
                    "count": len(devices),
                    "items": devices,
                    "query_names": sorted(AGENT_QUERY_NAMES),
                },
                "agent": {
                    "awaiting_response": agent_waiting,
                    "session": session.to_dict() if session else None,
                    "identity": agent_identity,
                    "sessions": {
                        "count": len(agent_session_items),
                        "selected_index": selected_index,
                        "items": agent_session_items,
                    },
                    "max_age_seconds": _COMPANION_TARGET_MAX_AGE_SECONDS,
                    "overview_max_age_seconds": _COMPANION_OVERVIEW_MAX_AGE_SECONDS,
                    "stale_threshold_seconds": DEFAULT_STALE_AGENT_SESSION_SECONDS,
                    "error": agent_error,
                },
                "dictation": {
                    "pipeline_enabled": pipeline_enabled,
                    "stages": pipeline_stages,
                    "target_profile_override": target_profile_override,
                    "runtime_backend": runtime_backend,
                    "error": dictation_error,
                },
                "runtime": {
                    "status": runtime_payload.get("status"),
                    "mode": runtime_payload.get("mode"),
                    "meeting_active": runtime_payload.get("meeting_active"),
                    "meeting_id": runtime_payload.get("meeting_id"),
                    "voice_state": runtime_payload.get("voice_state"),
                    "text_injection_enabled": text_injection_enabled,
                    "text_injection_error": runtime_payload.get("text_injection_error"),
                    "tmux_reply_available": tmux_reply_available,
                    "target_transport": (
                        agent_identity["target_transport"] if agent_identity else None
                    ),
                    "error": runtime_error,
                },
                "companion": {
                    "query_names": sorted(AGENT_QUERY_NAMES),
                    "voice_reply_max_age_seconds": _COMPANION_TARGET_MAX_AGE_SECONDS,
                    "stale_threshold_seconds": DEFAULT_STALE_AGENT_SESSION_SECONDS,
                },
            }
        )

    def _companion_agent_target(payload: Optional[dict[str, Any]]) -> tuple[str, str] | JSONResponse:
        """Pull a required (agent, session_id) pair from a control-route body."""
        body = payload if isinstance(payload, dict) else {}
        agent = body.get("agent")
        session_id = body.get("session_id")
        if not isinstance(agent, str) or not agent.strip():
            return JSONResponse({"error": "agent is required"}, status_code=400)
        if not isinstance(session_id, str) or not session_id.strip():
            return JSONResponse({"error": "session_id is required"}, status_code=400)
        return agent, session_id

    @router.post("/api/companion/select")
    async def api_companion_select(payload: Optional[dict[str, Any]] = None) -> Any:
        """Select a specific waiting session as AI PI's active reply target."""
        from ...agent_context import select_awaiting_agent_session

        target = _companion_agent_target(payload)
        if isinstance(target, JSONResponse):
            return target
        agent, session_id = target
        session = select_awaiting_agent_session(agent, session_id)
        if session is None:
            return JSONResponse(
                {"success": False, "error": "unknown_session", "session": None},
                status_code=404,
            )
        return JSONResponse({"success": True, "session": session.to_dict()})

    @router.post("/api/companion/dismiss")
    async def api_companion_dismiss(payload: Optional[dict[str, Any]] = None) -> Any:
        """Clear a waiting session's captured response (non-destructive)."""
        from ...agent_context import clear_agent_session_response

        target = _companion_agent_target(payload)
        if isinstance(target, JSONResponse):
            return target
        agent, session_id = target
        session = clear_agent_session_response(agent=agent, session_id=session_id)
        return JSONResponse(
            {
                "success": session is not None,
                "session": session.to_dict() if session else None,
            }
        )

    @router.post("/api/companion/pin")
    async def api_companion_pin(payload: Optional[dict[str, Any]] = None) -> Any:
        """Pin or unpin a waiting session as the sticky reply target."""
        from ...agent_context import pin_agent_session

        target = _companion_agent_target(payload)
        if isinstance(target, JSONResponse):
            return target
        agent, session_id = target
        body = payload if isinstance(payload, dict) else {}
        pinned = bool(body.get("pinned", True))
        session = pin_agent_session(agent, session_id, pinned)
        if session is None:
            return JSONResponse(
                {"success": False, "error": "unknown_session", "session": None},
                status_code=404,
            )
        return JSONResponse({"success": True, "session": session.to_dict()})

    @router.post("/api/companion/clear-stale")
    async def api_companion_clear_stale(payload: Optional[dict[str, Any]] = None) -> Any:
        """Clear all non-pinned waiting sessions older than the threshold."""
        from ...agent_context import (
            DEFAULT_STALE_AGENT_SESSION_SECONDS,
            clear_stale_agent_sessions,
        )

        body = payload if isinstance(payload, dict) else {}
        raw_age = body.get("max_age_seconds")
        try:
            max_age_seconds = int(raw_age) if raw_age is not None else DEFAULT_STALE_AGENT_SESSION_SECONDS
        except (TypeError, ValueError):
            return JSONResponse({"error": "max_age_seconds must be an integer"}, status_code=400)
        if max_age_seconds < 0:
            return JSONResponse({"error": "max_age_seconds must be >= 0"}, status_code=400)
        cleared = clear_stale_agent_sessions(max_age_seconds=max_age_seconds)
        return JSONResponse(
            {"success": True, "cleared": cleared, "max_age_seconds": max_age_seconds}
        )

    @router.get("/api/settings")
    async def api_get_settings() -> Any:
        try:
            from ...config import Config
            from ...plugins.dictation.runtime_counters import get_counters, get_session_status

            config = Config.load()
            payload = config.to_dict()
            # WFS-CFG-004: surface runtime counters + session-disabled state
            # alongside the persisted config. Read-only — clients should
            # not echo this back on PUT.
            payload["_runtime_status"] = {
                "counters": get_counters(),
                "session": get_session_status(),
            }
            return JSONResponse(payload)
        except Exception as e:
            return error_500(e, log, "Failed to load settings")

    @router.put("/api/settings")
    async def api_update_settings(payload: dict[str, Any]) -> Any:
        """Persist app settings from web UI."""
        try:
            from ...config import (
                Config,
                DeviceConfig,
                DictationConfig,
                DictationConfigError,
                DictationPipelineConfig,
                HotkeyConfig,
                KEY_DISPLAY,
                KEY_MAP,
                LLMRuntimeConfig,
                MacrosConfig,
                MeetingConfig,
                ModelConfig,
                PresenceConfig,
                UIConfig,
                VoiceMacroError,
            )

            current = Config.load()
            merged = deepcopy(current.to_dict())
            _merge_dict(merged, payload or {})

            hotkey_data = merged.get("hotkey", {})
            model_data = merged.get("model", {})
            ui_data = merged.get("ui", {})
            meeting_data = merged.get("meeting", {})
            device_data = merged.get("device", {})
            presence_data = merged.get("presence", {})

            hotkey_key = str(hotkey_data.get("key", current.hotkey.key))
            if hotkey_key not in KEY_MAP:
                return JSONResponse(
                    {"success": False, "error": f"Invalid hotkey key: {hotkey_key}"},
                    status_code=400,
                )
            hotkey_data["key"] = hotkey_key
            hotkey_data["display"] = KEY_DISPLAY.get(hotkey_key, hotkey_key)

            model_name = str(model_data.get("name", current.model.name))
            if model_name not in {"tiny", "base", "small", "medium", "large"}:
                return JSONResponse(
                    {"success": False, "error": f"Invalid model name: {model_name}"},
                    status_code=400,
                )
            model_data["name"] = model_name
            model_data["warm_on_start"] = bool(
                model_data.get("warm_on_start", current.model.warm_on_start)
            )

            # --- UIConfig validation ---
            theme = str(ui_data.get("theme", current.ui.theme)).strip().lower()
            if theme not in {"dark", "light", "dracula", "monokai"}:
                return JSONResponse(
                    {"success": False, "error": f"Invalid theme: {theme}"},
                    status_code=400,
                )
            ui_data["theme"] = theme

            history_lines = int(ui_data.get("history_lines", current.ui.history_lines))
            if not (1 <= history_lines <= 100):
                return JSONResponse(
                    {"success": False, "error": "history_lines must be between 1 and 100"},
                    status_code=400,
                )
            ui_data["history_lines"] = history_lines
            ui_data["show_audio_meter"] = bool(
                ui_data.get("show_audio_meter", current.ui.show_audio_meter)
            )

            # --- Optional string / bool fields in MeetingConfig ---
            meeting_data["mic_device"] = (
                str(meeting_data.get("mic_device") or "").strip() or None
            )
            meeting_data["system_audio_device"] = (
                str(meeting_data.get("system_audio_device") or "").strip() or None
            )
            meeting_data["auto_export"] = bool(
                meeting_data.get("auto_export", current.meeting.auto_export)
            )
            meeting_data["intel_summary_model"] = (
                str(meeting_data.get("intel_summary_model") or "").strip() or None
            )
            meeting_data["intel_cloud_reasoning_effort"] = (
                str(meeting_data.get("intel_cloud_reasoning_effort") or "").strip() or None
            )

            export_format = str(meeting_data.get("export_format", current.meeting.export_format))
            if export_format not in {"txt", "markdown", "json", "srt"}:
                return JSONResponse(
                    {"success": False, "error": f"Invalid export format: {export_format}"},
                    status_code=400,
                )
            meeting_data["export_format"] = export_format

            intel_provider = str(meeting_data.get("intel_provider", current.meeting.intel_provider)).lower()
            if intel_provider not in {"local", "cloud", "auto"}:
                return JSONResponse(
                    {"success": False, "error": f"Invalid intel provider: {intel_provider}"},
                    status_code=400,
                )
            meeting_data["intel_provider"] = intel_provider

            from ...plugins.router import available_profiles

            meeting_data["mir_enabled"] = bool(
                meeting_data.get("mir_enabled", current.meeting.mir_enabled)
            )
            mir_profile = str(
                meeting_data.get("mir_profile", current.meeting.mir_profile)
            ).strip().lower()
            if mir_profile not in set(available_profiles()):
                return JSONResponse(
                    {"success": False, "error": f"Invalid mir profile: {mir_profile}"},
                    status_code=400,
                )
            meeting_data["mir_profile"] = mir_profile

            poll_seconds = int(meeting_data.get("intel_queue_poll_seconds", current.meeting.intel_queue_poll_seconds))
            if poll_seconds < 5:
                return JSONResponse(
                    {"success": False, "error": "intel_queue_poll_seconds must be at least 5"},
                    status_code=400,
                )
            meeting_data["intel_queue_poll_seconds"] = poll_seconds

            retry_base_seconds = int(
                meeting_data.get("intel_retry_base_seconds", current.meeting.intel_retry_base_seconds)
            )
            if retry_base_seconds < 1:
                return JSONResponse(
                    {"success": False, "error": "intel_retry_base_seconds must be at least 1"},
                    status_code=400,
                )
            meeting_data["intel_retry_base_seconds"] = retry_base_seconds

            retry_max_seconds = int(
                meeting_data.get("intel_retry_max_seconds", current.meeting.intel_retry_max_seconds)
            )
            if retry_max_seconds < retry_base_seconds:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "intel_retry_max_seconds must be >= intel_retry_base_seconds",
                    },
                    status_code=400,
                )
            meeting_data["intel_retry_max_seconds"] = retry_max_seconds

            retry_max_attempts = int(
                meeting_data.get("intel_retry_max_attempts", current.meeting.intel_retry_max_attempts)
            )
            if retry_max_attempts < 1:
                return JSONResponse(
                    {"success": False, "error": "intel_retry_max_attempts must be at least 1"},
                    status_code=400,
                )
            meeting_data["intel_retry_max_attempts"] = retry_max_attempts

            failure_alert_percent = float(
                meeting_data.get(
                    "intel_retry_failure_alert_percent",
                    current.meeting.intel_retry_failure_alert_percent,
                )
            )
            if not (0.0 <= failure_alert_percent <= 100.0):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "intel_retry_failure_alert_percent must be between 0 and 100",
                    },
                    status_code=400,
                )
            meeting_data["intel_retry_failure_alert_percent"] = failure_alert_percent

            failure_hysteresis_minutes = float(
                meeting_data.get(
                    "intel_retry_failure_hysteresis_minutes",
                    current.meeting.intel_retry_failure_hysteresis_minutes,
                )
            )
            if failure_hysteresis_minutes < 0.0:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "intel_retry_failure_hysteresis_minutes must be >= 0",
                    },
                    status_code=400,
                )
            meeting_data["intel_retry_failure_hysteresis_minutes"] = failure_hysteresis_minutes

            webhook_url = str(
                meeting_data.get(
                    "intel_retry_failure_webhook_url",
                    current.meeting.intel_retry_failure_webhook_url or "",
                )
                or ""
            ).strip()
            if webhook_url:
                parsed_webhook = urlparse(webhook_url)
                if parsed_webhook.scheme not in {"http", "https"} or not parsed_webhook.netloc:
                    return JSONResponse(
                        {
                            "success": False,
                            "error": "intel_retry_failure_webhook_url must be a valid http(s) URL",
                        },
                        status_code=400,
                    )
            meeting_data["intel_retry_failure_webhook_url"] = webhook_url or None
            webhook_header_name = str(
                meeting_data.get(
                    "intel_retry_failure_webhook_header_name",
                    current.meeting.intel_retry_failure_webhook_header_name or "",
                )
                or ""
            ).strip()
            webhook_header_value = str(
                meeting_data.get(
                    "intel_retry_failure_webhook_header_value",
                    current.meeting.intel_retry_failure_webhook_header_value or "",
                )
                or ""
            ).strip()
            if bool(webhook_header_name) != bool(webhook_header_value):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "intel_retry_failure_webhook_header_name and intel_retry_failure_webhook_header_value must both be set or both be empty",
                    },
                    status_code=400,
                )
            if webhook_header_name and not _HTTP_HEADER_NAME_RE.match(webhook_header_name):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "intel_retry_failure_webhook_header_name must contain only letters, digits, and hyphens",
                    },
                    status_code=400,
                )
            meeting_data["intel_retry_failure_webhook_header_name"] = webhook_header_name or None
            meeting_data["intel_retry_failure_webhook_header_value"] = webhook_header_value or None

            similarity = float(meeting_data.get("similarity_threshold", current.meeting.similarity_threshold))
            if not (0.0 <= similarity <= 1.0):
                return JSONResponse(
                    {"success": False, "error": "similarity_threshold must be between 0.0 and 1.0"},
                    status_code=400,
                )
            meeting_data["similarity_threshold"] = similarity

            try:
                meeting_data["intel_cloud_base_url"] = _validate_cloud_base_url(
                    meeting_data.get("intel_cloud_base_url")
                )
            except ValueError as e:
                return JSONResponse({"success": False, "error": str(e)}, status_code=400)

            meeting_data["intel_cloud_api_key_env"] = str(
                meeting_data.get("intel_cloud_api_key_env", current.meeting.intel_cloud_api_key_env)
            ).strip() or "OPENAI_API_KEY"
            meeting_data["intel_cloud_model"] = str(
                meeting_data.get("intel_cloud_model", current.meeting.intel_cloud_model)
            ).strip() or "gpt-5-mini"

            # WFS-CFG-004: validate the dictation slice (preserves
            # current values when payload omits them; merged already
            # carries `current.to_dict()["dictation"]` as the base).
            # Drops the read-only `_runtime_status` enrichment if the
            # client echoed it back.
            merged.pop("_runtime_status", None)
            dictation_data = merged.get("dictation", {}) or {}
            pipeline_data = dictation_data.get("pipeline", {}) or {}
            runtime_data = dictation_data.get("runtime", {}) or {}

            pipeline_data["enabled"] = bool(pipeline_data.get(
                "enabled", current.dictation.pipeline.enabled
            ))
            raw_stages = pipeline_data.get("stages", current.dictation.pipeline.stages)
            if not isinstance(raw_stages, list) or not all(
                isinstance(stage, str) for stage in raw_stages
            ):
                return JSONResponse(
                    {"success": False, "error": "dictation.pipeline.stages must be a list of strings"},
                    status_code=400,
                )
            pipeline_data["stages"] = list(raw_stages)
            try:
                max_lat = int(pipeline_data.get(
                    "max_total_latency_ms",
                    current.dictation.pipeline.max_total_latency_ms,
                ))
            except (TypeError, ValueError):
                return JSONResponse(
                    {"success": False, "error": "dictation.pipeline.max_total_latency_ms must be an integer"},
                    status_code=400,
                )
            if max_lat <= 0:
                return JSONResponse(
                    {"success": False, "error": "dictation.pipeline.max_total_latency_ms must be > 0"},
                    status_code=400,
                )
            pipeline_data["max_total_latency_ms"] = max_lat
            target_override = str(pipeline_data.get(
                "target_profile_override",
                current.dictation.pipeline.target_profile_override,
            )).strip().lower() or "auto"
            allowed_target_overrides = {
                "auto",
                "claude_code",
                "codex_cli",
                "terminal_shell",
                "browser",
                "editor",
                "chat",
            }
            if target_override not in allowed_target_overrides:
                return JSONResponse(
                    {
                        "success": False,
                        "error": (
                            "dictation.pipeline.target_profile_override must be one of: "
                            + ", ".join(sorted(allowed_target_overrides))
                        ),
                    },
                    status_code=400,
                )
            pipeline_data["target_profile_override"] = target_override

            # HS-40-01: the four Phase-39 depth knobs. They already flow
            # through via the merge + `DictationPipelineConfig(**pipeline_data)`
            # construction below (and `__post_init__` is the single source of
            # truth for the 1–5 / 0–1 bounds), but coerce the numeric/bool
            # types explicitly here so a non-numeric payload returns a clean
            # 4xx instead of a raw "'<=' not supported" TypeError. Defaults
            # come from `current` so an omitted knob is preserved, never reset.
            try:
                rewrite_passes = int(pipeline_data.get(
                    "rewrite_passes", current.dictation.pipeline.rewrite_passes
                ))
            except (TypeError, ValueError):
                return JSONResponse(
                    {"success": False, "error": "dictation.pipeline.rewrite_passes must be an integer"},
                    status_code=400,
                )
            pipeline_data["rewrite_passes"] = rewrite_passes
            try:
                target_detect_below = float(pipeline_data.get(
                    "target_detect_llm_below",
                    current.dictation.pipeline.target_detect_llm_below,
                ))
            except (TypeError, ValueError):
                return JSONResponse(
                    {"success": False, "error": "dictation.pipeline.target_detect_llm_below must be a number"},
                    status_code=400,
                )
            pipeline_data["target_detect_llm_below"] = target_detect_below
            pipeline_data["corrections_enabled"] = bool(pipeline_data.get(
                "corrections_enabled", current.dictation.pipeline.corrections_enabled
            ))
            pipeline_data["target_detect_llm_enabled"] = bool(pipeline_data.get(
                "target_detect_llm_enabled",
                current.dictation.pipeline.target_detect_llm_enabled,
            ))

            backend = str(runtime_data.get(
                "backend", current.dictation.runtime.backend
            )).strip().lower()
            if backend not in {"auto", "mlx", "llama_cpp", "openai_compatible"}:
                return JSONResponse(
                    {"success": False, "error": f"Invalid dictation backend: {backend!r}"},
                    status_code=400,
                )
            runtime_data["backend"] = backend
            runtime_data["mlx_model"] = str(runtime_data.get(
                "mlx_model", current.dictation.runtime.mlx_model
            )).strip() or current.dictation.runtime.mlx_model
            runtime_data["llama_cpp_model_path"] = str(runtime_data.get(
                "llama_cpp_model_path", current.dictation.runtime.llama_cpp_model_path
            )).strip() or current.dictation.runtime.llama_cpp_model_path
            runtime_data["openai_compatible_model"] = str(runtime_data.get(
                "openai_compatible_model", current.dictation.runtime.openai_compatible_model
            )).strip() or current.dictation.runtime.openai_compatible_model
            runtime_data["openai_compatible_base_url"] = str(runtime_data.get(
                "openai_compatible_base_url", current.dictation.runtime.openai_compatible_base_url
            )).strip() or current.dictation.runtime.openai_compatible_base_url
            try:
                _validate_cloud_base_url(runtime_data["openai_compatible_base_url"])
            except ValueError:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "dictation.runtime.openai_compatible_base_url must start with http:// or https://",
                    },
                    status_code=400,
                )
            runtime_data["openai_compatible_api_key_env"] = str(runtime_data.get(
                "openai_compatible_api_key_env",
                current.dictation.runtime.openai_compatible_api_key_env,
            )).strip()
            try:
                timeout_seconds = float(runtime_data.get(
                    "openai_compatible_timeout_seconds",
                    current.dictation.runtime.openai_compatible_timeout_seconds,
                ))
            except (TypeError, ValueError):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "dictation.runtime.openai_compatible_timeout_seconds must be a number",
                    },
                    status_code=400,
                )
            if timeout_seconds <= 0:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "dictation.runtime.openai_compatible_timeout_seconds must be > 0",
                    },
                    status_code=400,
                )
            runtime_data["openai_compatible_timeout_seconds"] = timeout_seconds
            runtime_data["warm_on_start"] = bool(runtime_data.get(
                "warm_on_start", current.dictation.runtime.warm_on_start
            ))

            # HS-52-02: voice command macros. Validate the section so a malformed
            # macro returns a clean 4xx with a clear message, never a 500 and never a
            # silently-dropped command. `merged` already carries `current`'s macros as
            # the base, so omitting the section preserves it.
            macros_data = dictation_data.get("macros", {}) or {}
            macros_enabled = bool(
                macros_data.get("enabled", current.dictation.macros.enabled)
            )
            raw_macros = macros_data.get("items", [])
            if not isinstance(raw_macros, list):
                return JSONResponse(
                    {"success": False, "error": "dictation.macros.items must be a list"},
                    status_code=400,
                )
            try:
                macros_cfg = MacrosConfig(enabled=macros_enabled, items=raw_macros)
            except VoiceMacroError as exc:
                return JSONResponse(
                    {"success": False, "error": f"Invalid voice macro: {exc}"},
                    status_code=400,
                )

            try:
                dictation_cfg = DictationConfig(
                    pipeline=DictationPipelineConfig(**pipeline_data),
                    runtime=LLMRuntimeConfig(**runtime_data),
                    macros=macros_cfg,
                )
            except DictationConfigError as exc:
                return JSONResponse(
                    {"success": False, "error": str(exc)},
                    status_code=400,
                )
            except TypeError as exc:
                return JSONResponse(
                    {"success": False, "error": f"Invalid dictation field: {exc}"},
                    status_code=400,
                )

            updated = Config(
                hotkey=HotkeyConfig(**hotkey_data),
                model=ModelConfig(**model_data),
                ui=UIConfig(**ui_data),
                meeting=MeetingConfig(**meeting_data),
                dictation=dictation_cfg,
                device=DeviceConfig(**device_data),
                presence=PresenceConfig(**presence_data),
            )
            updated.save()

            if ctx.on_settings_applied is not None:
                try:
                    ctx.on_settings_applied(updated)
                except Exception as e:
                    log.error(f"on_settings_applied failed: {e}")

            return JSONResponse({"success": True, "settings": updated.to_dict()})
        except Exception as e:
            log.error(f"Failed to update settings: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        log.info(f"WebSocket connection attempt from {websocket.client}")
        try:
            await ctx.ws.connect(websocket)
            log.info("WebSocket connected successfully")
        except Exception as e:
            log.error(f"WebSocket connect failed: {e}", exc_info=True)
            return

        try:
            # Optional initial state push via REST endpoint; for WS we at
            # least emit current duration immediately if available.
            duration = ctx.current_formatted_duration()
            if duration is not None:
                await websocket.send_json({"type": "duration", "data": duration})

            while True:
                # Keep connection alive; ignore client messages for now.
                message = await websocket.receive_text()
                if message == "ping":
                    await websocket.send_text("pong")
                elif message.startswith("{"):
                    # Accept JSON no-op messages without error.
                    try:
                        json.loads(message)
                    except Exception:
                        pass
        except WebSocketDisconnect:
            pass
        except Exception as e:
            log.debug(f"WebSocket error: {e}")
        finally:
            await ctx.ws.disconnect(websocket)

    return router
