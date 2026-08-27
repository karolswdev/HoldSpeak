"""HS-143-11 S1 — Assignment MCP twins retain one owner service truth."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.mcp.families import inference_assignments
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from tests.unit.test_phase143_inference_assignments import _profile

OWNER = Principal(PrincipalKind.OWNER, "mcp-assignment-owner")
AGENT = Principal(PrincipalKind.AGENT, "mcp-assignment-agent")
MODEL_TURN = Principal(PrincipalKind.SERVICE, "mcp-assignment-turn")

_EXPECTED = {
    "inference_assignment.summary",
    "inference_assignment.editor",
    "inference_assignment.set",
    "inference_assignment.preview_use_default",
    "inference_assignment.clear",
}


def test_assignment_mcp_catalogue_is_closed_to_versioned_recursive_dtos() -> None:
    tools = {tool["name"]: tool["inputSchema"] for tool in inference_assignments.TOOLS}
    assert set(tools) == _EXPECTED
    for name, schema in tools.items():
        assert schema["$id"] == f"holdspeak://mcp/{name}@1"
        assert schema["additionalProperties"] is False
    scope = tools["inference_assignment.set"]["properties"]["scope"]
    assert all(variant["additionalProperties"] is False for variant in scope["oneOf"])
    entry = tools["inference_assignment.set"]["properties"]["entries"]["items"]
    assert entry["additionalProperties"] is False


def test_assignment_mcp_is_owner_before_every_command_body(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(inference_assignments, "get_database", lambda: Database(tmp_path / "assignments-mcp.db"))
    malformed = {"secret": "do-not-discover", "private_locator": "/not-a-body-oracle"}
    for name in _EXPECTED:
        for principal in (None, AGENT, MODEL_TURN):
            with pytest.raises(ServiceError) as refusal:
                inference_assignments.dispatch(name, malformed, principal)  # type: ignore[arg-type]
            assert refusal.value.code == "inference_assignment_owner_required"


def test_assignment_mcp_preserves_set_clear_replay_and_committed_effect(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    db = Database(tmp_path / "assignments-mcp.db")
    monkeypatch.setattr(inference_assignments, "get_database", lambda: db)
    _profile(db, "mcp-primary")
    body = {
        "command_id": "mcp-set", "expected_revision": 0, "scope": {"kind": "global"},
        "entries": [{"profile_id": "mcp-primary", "profile_revision": 1}], "retry_policy_id": None,
    }
    first = inference_assignments.dispatch("inference_assignment.set", body, OWNER)
    replay = inference_assignments.dispatch("inference_assignment.set", body, OWNER)
    assert replay == first
    assert replay["committed_effect"] == first["committed_effect"]
    assert replay["committed_effect"]["sha256"].startswith("sha256:")
    rendered = json.dumps(replay, sort_keys=True)
    for forbidden in ("local_locator", "secret_slot", "endpoint", "/private/"):
        assert forbidden not in rendered

    preview = inference_assignments.dispatch(
        "inference_assignment.preview_use_default",
        {"scope": {"kind": "global"}, "capability_id": "ask.answer"}, OWNER,
    )
    cleared = inference_assignments.dispatch(
        "inference_assignment.clear",
        {
            "command_id": "mcp-clear", "expected_revision": preview["expected_revision"],
            "scope": {"kind": "global"}, "capability_id": "ask.answer",
        },
        OWNER,
    )
    assert inference_assignments.dispatch(
        "inference_assignment.clear",
        {
            "command_id": "mcp-clear", "expected_revision": preview["expected_revision"],
            "scope": {"kind": "global"}, "capability_id": "ask.answer",
        }, OWNER,
    ) == cleared


def test_assignment_mcp_refuses_unknown_nested_fields_without_echo(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    db = Database(tmp_path / "assignments-mcp.db")
    monkeypatch.setattr(inference_assignments, "get_database", lambda: db)
    with pytest.raises(ServiceError) as refusal:
        inference_assignments.dispatch(
            "inference_assignment.editor",
            {"scope": {"kind": "global", "private_locator": "/no"}, "capability_id": "ask.answer"}, OWNER,
        )
    assert refusal.value.code == "inference_assignment_invalid"
    assert "private_locator" not in refusal.value.detail
