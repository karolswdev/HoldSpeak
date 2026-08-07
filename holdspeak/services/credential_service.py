"""Transport-neutral, write-only settings credential lifecycle."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import re
from copy import deepcopy
from dataclasses import replace
from typing import Any, Callable, Optional
from urllib.parse import urlparse

from ..db.core import Database
from ..principals import Principal
from .errors import NotFound, ValidationError

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
    """Return editable settings without credential material."""
    from ..config import LEGACY_ENDPOINT_FIELDS

    payload = deepcopy(config.to_dict())
    for section_path, legacy_fields in LEGACY_ENDPOINT_FIELDS.items():
        node: Any = payload
        for part in section_path.split("."):
            node = node.get(part) if isinstance(node, dict) else None
        if isinstance(node, dict):
            for legacy_field in legacy_fields:
                node.pop(legacy_field, None)
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
    meeting = clean.get("meeting")
    if isinstance(meeting, dict):
        meeting.pop("intel_retry_failure_webhook_header_name", None)
    return clean


@observe_service
class CredentialService:
    """Persist credentials while returning only redacted metadata."""

    def __init__(
        self,
        db: Database,
        on_settings_applied: Callable[[Any], None] | None = None,
        *,
        observer: PipelineObserver | None = None,
    ) -> None:
        self._db = db
        self._on_settings_applied = on_settings_applied
        self._observer = observer or NullObserver()

    def list_redacted(self, principal: Principal) -> dict[str, dict[str, Any]]:
        from ..config import Config

        return redacted_settings(Config.load())["_secrets"]

    def get_redacted(self, principal: Principal, secret_id: str) -> dict[str, Any]:
        try:
            return self.list_redacted(principal)[secret_id]
        except KeyError as exc:
            raise NotFound("secret setting", secret_id) from exc

    def replace(
        self,
        principal: Principal,
        secret_id: str,
        value: Any,
        metadata_or_patch: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, Any]]:
        self._require_secret(secret_id)
        clean = self._validated_secret(secret_id, value)
        patch = metadata_or_patch or {}
        from ..config import Config

        current = Config.load()
        section_name, field_name = SECRET_PATHS[secret_id]
        section = deepcopy(getattr(current, section_name))
        setattr(section, field_name, clean)
        if secret_id == "failure_webhook_credential":
            header_name = str(patch.get("header_name") or "Authorization").strip()
            if not _HTTP_HEADER_NAME_RE.match(header_name):
                raise ValidationError(
                    "failure webhook header name may contain only letters, digits, and hyphens"
                )
            section.intel_retry_failure_webhook_header_name = header_name
        return self._apply(replace(current, **{section_name: section}))

    def rotate(
        self,
        principal: Principal,
        secret_id: str,
        rotation_input: Any = None,
    ) -> dict[str, dict[str, Any]]:
        if secret_id not in ROTATABLE_SECRET_IDS:
            raise ValidationError("This secret must be replaced explicitly")
        from ..config import Config
        from ..web_auth import generate_web_token

        current = Config.load()
        section_name, field_name = SECRET_PATHS[secret_id]
        section = deepcopy(getattr(current, section_name))
        setattr(section, field_name, generate_web_token())
        return self._apply(replace(current, **{section_name: section}))

    def delete(self, principal: Principal, secret_id: str) -> dict[str, dict[str, Any]]:
        self._require_secret(secret_id)
        from ..config import Config

        current = Config.load()
        section_name, field_name = SECRET_PATHS[secret_id]
        section = deepcopy(getattr(current, section_name))
        setattr(section, field_name, "")
        if secret_id == "failure_webhook_credential":
            section.intel_retry_failure_webhook_header_name = None
            section.intel_retry_failure_webhook_header_value = None
        return self._apply(replace(current, **{section_name: section}))

    def _apply(self, updated: Any) -> dict[str, dict[str, Any]]:
        updated.save()
        if self._on_settings_applied is not None:
            self._on_settings_applied(updated)
        return redacted_settings(updated)["_secrets"]

    @staticmethod
    def _require_secret(secret_id: str) -> None:
        if secret_id not in SECRET_PATHS:
            raise NotFound("secret setting", secret_id)

    @staticmethod
    def _validated_secret(secret_id: str, value: Any) -> str:
        clean = str(value or "").strip()
        if not clean:
            raise ValidationError("secret value must not be empty; use DELETE to remove it")
        if any(ch in clean for ch in "\r\n"):
            raise ValidationError("secret value must be one line")
        if secret_id == "failure_webhook_url":
            parsed = urlparse(clean)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValidationError("failure webhook URL must be a valid http(s) URL")
        elif secret_id in {"slack_webhook_url", "companion_webhook_url"}:
            from ..slack_export import slack_webhook_host

            try:
                slack_webhook_host(clean)
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc
        return clean
