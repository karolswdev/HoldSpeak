"""App settings, read and write (the deep-merged PUT).

Bodies moved verbatim from routes/system.py (HS-79-02, the Phase-63 discipline).
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.system")


# Validates outbound webhook header names on the settings PUT path.
_HTTP_HEADER_NAME_RE = re.compile(r"^[A-Za-z0-9-]+$")
# HSM-14: a GitHub `owner/name` slug for the companion GitHub connector.
_GITHUB_REPO_RE = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")
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




def build_settings_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/settings")
    async def api_get_settings() -> Any:
        try:
            from ....config import Config
            from ....plugins.dictation.runtime_counters import get_counters, get_session_status

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
            from ....config import (
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
                WakeWordConfig,
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
            # HS-59: validate the transcription language at the boundary so a
            # typo fails the settings write, not a dictation later. Store the
            # normalized code ("auto" for detection).
            from ....languages import normalize_language

            raw_language = model_data.get("language", current.model.language)
            try:
                normalized = normalize_language(raw_language)
            except ValueError as exc:
                return JSONResponse(
                    {"success": False, "error": str(exc)}, status_code=400
                )
            model_data["language"] = normalized or "auto"

            # --- HS-60: wake-word validation (strict at the boundary) ---
            wake_data = merged.get("wake_word", {}) or {}
            current_wake = getattr(current, "wake_word", WakeWordConfig())
            wake_action = str(wake_data.get("action", current_wake.action)).strip().lower()
            if wake_action not in ("preview", "type"):
                return JSONResponse(
                    {"success": False, "error": f"wake_word.action must be 'preview' or 'type', got {wake_action!r}"},
                    status_code=400,
                )
            wake_data["action"] = wake_action
            try:
                wake_threshold = float(wake_data.get("threshold", current_wake.threshold))
            except (TypeError, ValueError):
                return JSONResponse(
                    {"success": False, "error": "wake_word.threshold must be a number"},
                    status_code=400,
                )
            if not (0.0 <= wake_threshold <= 1.0):
                return JSONResponse(
                    {"success": False, "error": "wake_word.threshold must be between 0 and 1"},
                    status_code=400,
                )
            wake_data["threshold"] = wake_threshold
            try:
                wake_window = float(
                    wake_data.get("armed_window_seconds", current_wake.armed_window_seconds)
                )
            except (TypeError, ValueError):
                return JSONResponse(
                    {"success": False, "error": "wake_word.armed_window_seconds must be a number"},
                    status_code=400,
                )
            if not (2.0 <= wake_window <= 30.0):
                return JSONResponse(
                    {"success": False, "error": "wake_word.armed_window_seconds must be between 2 and 30"},
                    status_code=400,
                )
            wake_data["armed_window_seconds"] = wake_window
            wake_model = str(wake_data.get("model", current_wake.model)).strip()
            if not wake_model:
                return JSONResponse(
                    {"success": False, "error": "wake_word.model must not be empty"},
                    status_code=400,
                )
            wake_data["model"] = wake_model
            wake_data["enabled"] = bool(wake_data.get("enabled", current_wake.enabled))

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

            from ....plugins.router import available_profiles

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

            # HS-61-01: the Send-to-Slack incoming-webhook URL. Empty = the
            # feature is off; anything else must pass THE shared rule (https
            # with a host; plain http for loopback only). The URL's host is
            # exactly what the Slack connector may POST to.
            slack_url = str(
                meeting_data.get(
                    "slack_webhook_url", current.meeting.slack_webhook_url or ""
                )
                or ""
            ).strip()
            if slack_url:
                from ....slack_export import slack_webhook_host

                try:
                    slack_webhook_host(slack_url)
                except ValueError as exc:
                    return JSONResponse(
                        {"success": False, "error": f"slack_webhook_url: {exc}"},
                        status_code=400,
                    )
            meeting_data["slack_webhook_url"] = slack_url

            # HSM-14: the iPad desk's Webhook connector URL. Same consent posture
            # as Slack — empty = the connector is off; anything else must pass THE
            # shared rule (https with a host; plain http for loopback only). The
            # URL's host is exactly what the Webhook connector may POST to, and the
            # URL is a credential: it stays on the host and never rides a payload.
            companion_webhook_url = str(
                meeting_data.get(
                    "companion_webhook_url",
                    current.meeting.companion_webhook_url or "",
                )
                or ""
            ).strip()
            if companion_webhook_url:
                from ....slack_export import slack_webhook_host

                try:
                    slack_webhook_host(companion_webhook_url)
                except ValueError as exc:
                    return JSONResponse(
                        {"success": False, "error": f"companion_webhook_url: {exc}"},
                        status_code=400,
                    )
            meeting_data["companion_webhook_url"] = companion_webhook_url

            # HSM-14: the iPad desk's GitHub connector default repo (owner/name).
            # Auth is the host's already-authenticated local `gh` — no token is
            # stored or crosses the wire. Empty = the connector is off; otherwise
            # it must be a plain `owner/name` slug.
            companion_github_repo = str(
                meeting_data.get(
                    "companion_github_repo",
                    current.meeting.companion_github_repo or "",
                )
                or ""
            ).strip()
            if companion_github_repo and not _GITHUB_REPO_RE.match(companion_github_repo):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "companion_github_repo must be of the form owner/name",
                    },
                    status_code=400,
                )
            meeting_data["companion_github_repo"] = companion_github_repo

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
                    spoken_symbols=dictation_data.get("spoken_symbols", []) or [],
                    # HS-75-03: the preview-before-type knob rides the same
                    # boundary (a plain bool; absent falls back to current).
                    preview_before_type=bool(
                        dictation_data.get(
                            "preview_before_type",
                            current.dictation.preview_before_type,
                        )
                    ),
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
                wake_word=WakeWordConfig(**wake_data),
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


    return router
