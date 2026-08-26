"""HS-143-11 S1 — Model Library MCP twins retain HTTP authority/custody laws."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.mcp.families import model_library
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError

OWNER = Principal(PrincipalKind.OWNER, "mcp-library-owner")
AGENT = Principal(PrincipalKind.AGENT, "mcp-library-agent")
MODEL_TURN = Principal(PrincipalKind.SERVICE, "mcp-library-turn")


_EXPECTED = {
    "model_library.get",
    "model_library.download",
    "model_library.add_to_library",
    "model_library.use_model_file",
    "model_library.connect_hosted_model",
    "model_library.define_endpoint",
    "model_library.connect_paired_device",
}


def test_model_library_mcp_catalogue_is_closed_and_contains_all_http_twins() -> None:
    tools = {tool["name"]: tool["inputSchema"] for tool in model_library.TOOLS}
    assert set(tools) == _EXPECTED
    for name, schema in tools.items():
        assert schema["$id"] == f"holdspeak://mcp/{name}@1"
        assert schema["additionalProperties"] is False
    assert tools["model_library.connect_hosted_model"]["properties"]["draft"]["additionalProperties"] is False
    assert tools["model_library.connect_hosted_model"]["properties"]["secret"]["additionalProperties"] is False
    upload = tools["model_library.use_model_file"]
    assert upload["properties"]["bytes_base64"]["maxLength"] == model_library.MAX_MODEL_FILE_BASE64_CHARS
    assert "path" not in upload["properties"]


def test_model_library_mcp_is_owner_before_every_body_read(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(model_library, "get_database", lambda: Database(tmp_path / "library-mcp.db"))
    malformed = {"secret": {"value": "do-not-read"}, "path": "/private/owner.gguf"}
    for name in _EXPECTED:
        for principal in (None, AGENT, MODEL_TURN):
            with pytest.raises(ServiceError) as refusal:
                model_library.dispatch(name, malformed, principal)  # type: ignore[arg-type]
            assert refusal.value.code == "model_library_owner_required"


def test_model_library_mcp_stages_base64_and_never_returns_secret_or_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    db = Database(tmp_path / "library-mcp.db")
    monkeypatch.setattr(model_library, "get_database", lambda: db)
    result = model_library.dispatch(
        "model_library.use_model_file",
        {"request_id": "base64-upload", "filename": "owner.gguf", "bytes_base64": "R0dVRm1jcC1maXh0dXJl"},
        OWNER,
    )
    assert result["receipt"]["assignments_unchanged"] is True
    rendered = json.dumps(result, sort_keys=True)
    assert str(tmp_path) not in rendered
    assert "local_locator" not in rendered

    secret = "mcp-secret-sentinel-should-not-return"
    provider = model_library.dispatch(
        "model_library.connect_hosted_model",
        {
            "draft": {
                "request_id": "hosted-anthropic", "profile_id": "mcp-anthropic",
                "expected_profile_revision": 0, "label": "MCP Anthropic", "provider_family": "anthropic",
                "model": "claude-safe", "requires_key": True,
            },
            "secret": {"value": secret},
        },
        OWNER,
    )
    provider_rendered = json.dumps(provider, sort_keys=True)
    for forbidden in (secret, "secret_slot", "endpoint"):
        assert forbidden not in provider_rendered
    assert provider["provider"]["secret"] == {"required": True, "present": True}


def test_model_library_mcp_refuses_paths_and_oversized_encoded_input_before_staging(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(model_library, "get_database", lambda: Database(tmp_path / "library-mcp.db"))
    with pytest.raises(ServiceError) as path:
        model_library.dispatch(
            "model_library.use_model_file",
            {"request_id": "bad-path", "filename": "/client/path.gguf", "bytes_base64": "R0dVRg=="}, OWNER,
        )
    assert path.value.code == "model_library_upload_invalid"
    with pytest.raises(ServiceError) as oversized:
        model_library.dispatch(
            "model_library.use_model_file",
            {
                "request_id": "too-large", "filename": "large.gguf",
                "bytes_base64": "A" * (model_library.MAX_MODEL_FILE_BASE64_CHARS + 1),
            }, OWNER,
        )
    assert oversized.value.code == "model_library_upload_invalid"
    with pytest.raises(ServiceError) as empty:
        model_library.dispatch(
            "model_library.use_model_file",
            {"request_id": "empty", "filename": "empty.gguf", "bytes_base64": ""}, OWNER,
        )
    assert empty.value.code == "model_library_upload_invalid"
