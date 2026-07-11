"""Write-only credential operations for app settings (HS-92-02)."""
from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import replace
from typing import Any, Optional
from urllib.parse import urlparse

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.system.settings_secrets")
_HTTP_HEADER_NAME_RE = re.compile(r"^[A-Za-z0-9-]+$")

SECRET_PATHS: dict[str, tuple[str, str]] = {
    "web_token": ("meeting", "web_auth_token"),
    "device_psk": ("device", "psk"),
    "telegram_bot_token": ("cadence_telegram", "bot_token"),
    "telegram_pairing_code": ("cadence_telegram", "pairing_code"),
    "failure_webhook_url": ("meeting", "intel_retry_failure_webhook_url"),
    "failure_webhook_credential": (
        "meeting",
        "intel_retry_failure_webhook_header_value",
    ),
    "slack_webhook_url": ("meeting", "slack_webhook_url"),
    "companion_webhook_url": ("meeting", "companion_webhook_url"),
}
ROTATABLE_SECRET_IDS = {"web_token", "device_psk", "telegram_pairing_code"}


def _secret_destination(secret_id: str, value: str) -> Optional[str]:
    if secret_id not in {
        "failure_webhook_url",
        "slack_webhook_url",
        "companion_webhook_url",
    }:
        return None
    parsed = urlparse(value)
    return parsed.hostname.lower() if parsed.hostname else None


def redacted_settings(config: Any) -> dict[str, Any]:
    """Return the editable settings shape without any credential values."""
    payload = deepcopy(config.to_dict())
    states: dict[str, dict[str, Any]] = {}
    for secret_id, (section, field) in SECRET_PATHS.items():
        section_data = payload.get(section)
        if not isinstance(section_data, dict):
            continue
        value = str(section_data.pop(field, "") or "")
        state: dict[str, Any] = {"configured": bool(value)}
        destination = _secret_destination(secret_id, value)
        if destination:
            state["destination"] = destination
        states[secret_id] = state
    payload["_secrets"] = states
    return payload


def strip_secret_mutations(payload: dict[str, Any]) -> dict[str, Any]:
    """Generic settings writes may never set, clear, or echo credentials."""
    clean = deepcopy(payload)
    clean.pop("_secrets", None)
    for section, field in SECRET_PATHS.values():
        section_data = clean.get(section)
        if isinstance(section_data, dict):
            section_data.pop(field, None)
    # Material to the dedicated credential operation; never mutate it alone.
    meeting = clean.get("meeting")
    if isinstance(meeting, dict):
        meeting.pop("intel_retry_failure_webhook_header_name", None)
    return clean


def _validated_secret(secret_id: str, value: Any) -> str:
    clean = str(value or "").strip()
    if not clean:
        raise ValueError("secret value must not be empty; use DELETE to remove it")
    if any(ch in clean for ch in "\r\n"):
        raise ValueError("secret value must be one line")
    if secret_id == "failure_webhook_url":
        parsed = urlparse(clean)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("failure webhook URL must be a valid http(s) URL")
    elif secret_id in {"slack_webhook_url", "companion_webhook_url"}:
        from ....slack_export import slack_webhook_host

        slack_webhook_host(clean)
    return clean


def register_settings_secret_routes(router: APIRouter, ctx: WebContext) -> None:
    async def apply_change(updated: Any) -> JSONResponse:
        updated.save()
        if ctx.on_settings_applied is not None:
            try:
                ctx.on_settings_applied(updated)
            except Exception as exc:
                log.error(f"on_settings_applied failed: {exc}")
        return JSONResponse(
            {"success": True, "secrets": redacted_settings(updated)["_secrets"]}
        )

    @router.put("/api/settings/secrets/{secret_id}")
    async def api_replace_secret(secret_id: str, body: dict[str, Any]) -> Any:
        if secret_id not in SECRET_PATHS:
            return JSONResponse(
                {"success": False, "error": "Unknown secret setting"}, status_code=404
            )
        try:
            from ....config import Config

            current = Config.load()
            value = _validated_secret(secret_id, body.get("value"))
            section_name, field_name = SECRET_PATHS[secret_id]
            section = deepcopy(getattr(current, section_name))
            setattr(section, field_name, value)
            if secret_id == "failure_webhook_credential":
                header_name = str(body.get("header_name") or "Authorization").strip()
                if not _HTTP_HEADER_NAME_RE.match(header_name):
                    raise ValueError(
                        "failure webhook header name may contain only letters, digits, and hyphens"
                    )
                section.intel_retry_failure_webhook_header_name = header_name
            return await apply_change(replace(current, **{section_name: section}))
        except ValueError as exc:
            return JSONResponse(
                {"success": False, "error": str(exc)}, status_code=400
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to replace secret setting")

    @router.post("/api/settings/secrets/{secret_id}/rotate")
    async def api_rotate_secret(secret_id: str) -> Any:
        if secret_id not in ROTATABLE_SECRET_IDS:
            return JSONResponse(
                {"success": False, "error": "This secret must be replaced explicitly"},
                status_code=400,
            )
        try:
            from ....config import Config
            from ....web_auth import generate_web_token

            current = Config.load()
            section_name, field_name = SECRET_PATHS[secret_id]
            section = deepcopy(getattr(current, section_name))
            setattr(section, field_name, generate_web_token())
            return await apply_change(replace(current, **{section_name: section}))
        except Exception as exc:
            return error_500(exc, log, "Failed to rotate secret setting")

    @router.delete("/api/settings/secrets/{secret_id}")
    async def api_delete_secret(secret_id: str) -> Any:
        if secret_id not in SECRET_PATHS:
            return JSONResponse(
                {"success": False, "error": "Unknown secret setting"}, status_code=404
            )
        try:
            from ....config import Config

            current = Config.load()
            section_name, field_name = SECRET_PATHS[secret_id]
            section = deepcopy(getattr(current, section_name))
            setattr(section, field_name, "")
            if secret_id == "failure_webhook_credential":
                section.intel_retry_failure_webhook_header_name = None
                section.intel_retry_failure_webhook_header_value = None
            return await apply_change(replace(current, **{section_name: section}))
        except Exception as exc:
            return error_500(exc, log, "Failed to delete secret setting")


__all__ = [
    "redacted_settings",
    "register_settings_secret_routes",
    "strip_secret_mutations",
]
