"""Settings family -- MCP tools for the SettingsService surface."""
from __future__ import annotations

from typing import Any

from holdspeak.db import get_database, get_observer
from holdspeak.principals import Principal
from holdspeak.services.errors import ConflictError, ValidationError
from holdspeak.services.settings_service import SettingsService

TOOLS: list[dict[str, Any]] = [
    {
        "name": "settings.get",
        "description": (
            "Read the current HoldSpeak settings. Secrets are redacted; "
            "_revision enables optimistic concurrency."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "settings.update",
        "description": (
            "Update HoldSpeak settings with a partial patch. EGRESS: an HTTPS "
            "calendar.subscription is fetched by the hub without credentials or headers; "
            "intel_provider and intel_profile_id are retired routing controls; "
            "_placement inference assignments and secrets cannot be written through "
            "this tool. Echo _revision from settings.get for optimistic concurrency; omit it "
            "for last-writer-wins. Settings are persisted "
            "immediately; a running HoldSpeak web server picks up the new "
            "values on its next settings read (no live-reload signal is "
            "sent from the MCP sidecar)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "patch": {
                    "type": "object",
                    "description": "Partial settings object. Only supplied keys are changed.",
                },
            },
            "required": ["patch"],
            "additionalProperties": False,
        },
    },
]


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call.  Raises LookupError for unowned names."""
    if name not in ("settings.get", "settings.update"):
        raise LookupError(name)

    svc = SettingsService(
        db=get_database(),
        on_settings_applied=None,
        observer=get_observer(),
    )

    if name == "settings.get":
        return svc.get_settings(principal)

    # name == "settings.update"
    patch = arguments.get("patch")
    if not isinstance(patch, dict):
        raise ValueError("patch must be an object")
    try:
        return svc.update_settings(principal, patch)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
    except ConflictError as exc:
        raise ValueError(str(exc)) from exc
