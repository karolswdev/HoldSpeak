"""Phase 133 settings family tests (HS-133-03)."""
from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.mcp import server, tools as mcp_tools
from holdspeak.mcp.server import handle_message
from holdspeak.mcp.families import settings as settings_family
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, ValidationError
from holdspeak.services.settings_service import SECRET_PATHS

OWNER = Principal(PrincipalKind.OWNER, "phase133-settings-test")


@pytest.fixture(autouse=True)
def _isolate_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Wire a stable principal for every MCP call in this module."""
    monkeypatch.setattr(
        server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER)
    )


def _call(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Send a tools/call through handle_message and return the result."""
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": name,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        }
    )
    assert response is not None
    return response["result"]


# ---------- settings.get -------------------------------------------------

def test_settings_get_returns_revision_and_placement() -> None:
    """settings.get returns _revision and _placement with no secret values."""
    result = _call("settings.get")
    assert result["isError"] is False
    data = json.loads(result["content"][0]["text"])

    # Enrichment keys must be present.
    assert "_revision" in data, "missing _revision"
    assert "_placement" in data, "missing _placement"

    # No raw secret value must appear anywhere in the response.
    # SECRET_PATHS maps secret_id -> (section, field); the redacted response
    # must NOT contain the raw field under its section.
    for _secret_id, (section, field) in SECRET_PATHS.items():
        section_data = data.get(section)
        if isinstance(section_data, dict):
            assert field not in section_data, (
                f"Secret field {section}.{field} leaked in settings.get response"
            )


# ---------- settings.update: valid patch ---------------------------------

def test_settings_update_valid_patch_applies(monkeypatch: pytest.MonkeyPatch) -> None:
    """A well-formed, non-secret patch succeeds and echoes the new settings."""
    # Use a mock service that returns a success result.
    captured: dict[str, Any] = {}

    class FakeSettingsService:
        def __init__(self, **kw: Any) -> None:
            pass

        def update_settings(self, principal: Any, patch: dict[str, Any]) -> dict[str, Any]:
            captured["principal"] = principal
            captured["patch"] = patch
            return {"success": True, "settings": {"ui": {"theme": "dark"}, "_revision": "abc123"}}

    monkeypatch.setattr(settings_family, "SettingsService", FakeSettingsService)
    monkeypatch.setattr(settings_family, "get_database", lambda: MagicMock())
    monkeypatch.setattr(settings_family, "get_observer", lambda: None)

    result = _call("settings.update", {"patch": {"ui": {"theme": "dark"}}})
    assert result["isError"] is False

    payload = json.loads(result["content"][0]["text"])
    assert payload["success"] is True
    assert captured["patch"] == {"ui": {"theme": "dark"}}


# ---------- settings.update: secret-path write stripped -------------------

def test_settings_update_secret_path_stripped() -> None:
    """A patch containing a secret-path field is silently stripped, not persisted."""
    # Write a secret through the MCP tool -- the service should strip it.
    # Use the real service so strip_secret_mutations is exercised.
    secret_section, secret_field = SECRET_PATHS["web_token"]  # ("meeting", "web_auth_token")

    result = _call(
        "settings.update",
        {"patch": {secret_section: {secret_field: "leaked-secret-value"}}},
    )
    assert result["isError"] is False

    payload = json.loads(result["content"][0]["text"])
    assert payload["success"] is True

    # The returned (redacted) settings must NOT contain the raw secret field.
    settings_data = payload.get("settings", {})
    section_data = settings_data.get(secret_section, {})
    assert secret_field not in section_data, (
        f"Secret field {secret_section}.{secret_field} appeared in update response"
    )


# ---------- settings.update: validation error -> isError:true -------------

def test_settings_update_validation_error_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A validation failure surfaces as isError:true."""
    class FailingSettingsService:
        def __init__(self, **kw: Any) -> None:
            pass

        def update_settings(self, principal: Any, patch: dict[str, Any]) -> dict[str, Any]:
            raise ValidationError("Invalid theme: neon")

    monkeypatch.setattr(settings_family, "SettingsService", FailingSettingsService)
    monkeypatch.setattr(settings_family, "get_database", lambda: MagicMock())
    monkeypatch.setattr(settings_family, "get_observer", lambda: None)

    result = _call("settings.update", {"patch": {"ui": {"theme": "neon"}}})
    assert result["isError"] is True
    error_text = result["content"][0]["text"]
    assert "Invalid theme" in error_text or "neon" in error_text


# ---------- settings.update: stale revision -> isError:true ---------------

def test_settings_update_stale_revision_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A stale _revision conflict surfaces as isError:true."""
    class ConflictSettingsService:
        def __init__(self, **kw: Any) -> None:
            pass

        def update_settings(self, principal: Any, patch: dict[str, Any]) -> dict[str, Any]:
            raise ConflictError(
                "Settings changed in another surface since you loaded them.",
                code="settings_stale",
                context={"revision": "current-rev"},
            )

    monkeypatch.setattr(settings_family, "SettingsService", ConflictSettingsService)
    monkeypatch.setattr(settings_family, "get_database", lambda: MagicMock())
    monkeypatch.setattr(settings_family, "get_observer", lambda: None)

    result = _call(
        "settings.update",
        {"patch": {"_revision": "stale-bogus", "ui": {"theme": "dark"}}},
    )
    assert result["isError"] is True
    error_text = result["content"][0]["text"]
    assert "changed" in error_text.lower() or "stale" in error_text.lower() or "surface" in error_text.lower()


# ---------- settings.update description: egress warning -------------------

def test_settings_update_description_contains_egress_warning() -> None:
    """The shipped settings.update description includes the counsel-mandated egress sentence."""
    tool_def = next(t for t in settings_family.TOOLS if t["name"] == "settings.update")
    desc = tool_def["description"]

    # The spec mandates this exact content:
    assert "EGRESS" in desc, "Missing EGRESS warning in settings.update description"
    assert "intel_provider" in desc, "Missing intel_provider mention"
    assert "intel_profile_id" in desc, "Missing intel_profile_id mention"
    assert "_placement" in desc, "Missing _placement pointer"
    assert "no live-reload signal" in desc, "Missing no-live-reload caveat"
