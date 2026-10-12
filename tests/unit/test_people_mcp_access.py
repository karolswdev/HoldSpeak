"""Conductor R7: People MCP access is a persisted setting, default on.

Owner, 2026-10-06: "the default should be on, for HOLDSPEAK_MCP_PEOPLE_ACCESS,
and I guess there's an affordance to set it somewhere, right?"

- ``people.mcp_access`` (off | read | write) persists in the config; the
  default is ``write`` (on). The env var overrides it when set.
- GET/PUT /api/settings/people-access and the MCP tool ``people.access.set``:
  the owner's press, an admitted kernel operation with a receipt (CONFIG).
- A launched agent reads People unless the effective access is ``off``; it
  never sets the access and never writes People.

Real hub app, real config file (in the test's directory), real kernel.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_conductor_k6_agent_mcp import (  # noqa: E402
    _call, _client, _launch_credential, _reach, _refused_by_palette, _result, _rpc, hub,  # noqa: F401
)

from holdspeak.mcp.families.people import READ_TOOLS, access_source  # noqa: E402


@pytest.fixture(autouse=True)
def config_file(tmp_path, monkeypatch):
    import holdspeak.config as config_facade

    path = tmp_path / "config.json"
    monkeypatch.setattr(config_facade, "CONFIG_FILE", path)
    monkeypatch.delenv("HOLDSPEAK_MCP_PEOPLE_ACCESS", raising=False)
    return path


def _people_tools(agent: Any) -> set[str]:
    return {t["name"] for t in _rpc(agent, "tools/list").json()["result"]["tools"] if t["name"].startswith("people.")}


def test_the_default_is_on(config_file) -> None:
    assert access_source({}) == ("write", "default")
    from holdspeak.config import Config

    assert Config().people.mcp_access == "write"


def test_the_env_overrides_the_setting(config_file) -> None:
    config_file.write_text(json.dumps({"people": {"mcp_access": "read"}}), encoding="utf-8")
    assert access_source({}) == ("read", "config")
    assert access_source({"HOLDSPEAK_MCP_PEOPLE_ACCESS": "off"}) == ("off", "env")


def test_the_owner_sets_it_with_a_receipt_and_agents_follow(hub, config_file) -> None:
    _reach(hub, False)
    shown = hub.client.get("/api/settings/people-access").json()
    # The hub wrote its default config on boot: the saved default is on.
    assert shown["mode"] == "write" and shown["effective"] == "write" and shown["agents"] == "read", shown
    assert shown["source"] in ("default", "config")
    agent = _client(hub, _launch_credential().token)
    assert _people_tools(agent) == set(READ_TOOLS)

    put = hub.client.put("/api/settings/people-access", json={"mode": "off"})
    assert put.status_code == 200, put.text
    body = put.json()
    assert body["mode"] == "off" and body["agents"] == "off"
    assert body["receipt"]["outcome"] == "succeeded" and body["operation_id"]
    assert json.loads(config_file.read_text(encoding="utf-8"))["people"]["mcp_access"] == "off"
    assert _people_tools(agent) == set()
    assert _refused_by_palette(_call(agent, "people.relationship.list", {}))

    # Over MCP, the owner's own client sets it back (CONFIG: his press).
    is_error, answer = hub.mcp("people.access.set", {"mode": "write"})
    assert is_error is False and answer["mode"] == "write", answer
    assert _people_tools(agent) == set(READ_TOOLS)
    # An unknown mode is refused by name.
    bad = hub.client.put("/api/settings/people-access", json={"mode": "loud"})
    assert bad.status_code >= 400


def test_an_agent_never_sets_the_access(hub, config_file) -> None:
    _reach(hub, False)
    cred = _launch_credential()
    agent = _client(hub, cred.token)
    assert agent.put("/api/settings/people-access", json={"mode": "write"}).status_code == 403
    assert agent.get("/api/settings/people-access").status_code == 403
    assert "people.access.set" not in {t["name"] for t in _rpc(agent, "tools/list").json()["result"]["tools"]}
    assert _refused_by_palette(_call(agent, "people.access.set", {"mode": "write"}))
    from holdspeak.mcp.tool_authority import CONFIG, TOOL_AUTHORITY

    assert TOOL_AUTHORITY["people.access.set"] == CONFIG
    if config_file.exists():  # unchanged: still the default
        assert json.loads(config_file.read_text())["people"]["mcp_access"] == "write"


def test_doctor_names_the_effective_value_and_its_source(config_file) -> None:
    from holdspeak.commands.doctor import _check_people_mcp_access

    check = _check_people_mcp_access({})
    assert check.detail == "write (from default); agents: read"
    config_file.write_text(json.dumps({"people": {"mcp_access": "read"}}), encoding="utf-8")
    assert _check_people_mcp_access({}).detail == "read (from people.mcp_access); agents: read"
    assert _check_people_mcp_access({"HOLDSPEAK_MCP_PEOPLE_ACCESS": "off"}).detail == (
        "off (from HOLDSPEAK_MCP_PEOPLE_ACCESS); agents: off")


def test_the_variable_holds_the_setting_server_side(hub, config_file, monkeypatch) -> None:
    """Ratified 2026-10-07 ("Of course it should, buddy!"): while the variable is set, the PUT
    is refused by name, with a receipt, and the setting does not change."""
    monkeypatch.setenv("HOLDSPEAK_MCP_PEOPLE_ACCESS", "off")
    shown = hub.client.get("/api/settings/people-access").json()
    assert shown["source"] == "env" and shown["env_var"] == "HOLDSPEAK_MCP_PEOPLE_ACCESS"
    assert shown["effective"] == "off" and shown["agents"] == "off"
    before = config_file.read_text(encoding="utf-8") if config_file.exists() else ""
    put = hub.client.put("/api/settings/people-access", json={"mode": "read"})
    assert put.status_code == 409, put.text
    body = put.json()
    assert body["code"] == "people_access_env_override", body
    assert body.get("operation_id") or body.get("receipt"), body
    after = config_file.read_text(encoding="utf-8") if config_file.exists() else ""
    assert before == after
    is_error, answer = hub.mcp("people.access.set", {"mode": "read"})
    assert is_error is True and answer.get("code") == "people_access_env_override", answer


# ── Astra round 1 on #919 (her probes, ported) ──────────────────────────


def _owner_people_discovery(hub) -> tuple[list, list, list]:
    tools = [t["name"] for t in _rpc(hub.client, "tools/list").json()["result"]["tools"] if t["name"].startswith("people.")]
    listed = _rpc(hub.client, "resources/list").json()["result"]
    resources = [r["uri"] for r in listed["resources"] if r["uri"].startswith("holdspeak://people/")]
    templates = [r["uriTemplate"] for r in listed["resourceTemplates"] if r["uriTemplate"].startswith("holdspeak://people/")]
    return tools, resources, templates


def test_off_hides_people_from_owner_discovery(hub, config_file) -> None:
    """Finding 3: a receipted PUT to off takes People out of the owner's MCP
    discovery; people.access.set stays, so access can come back from MCP."""
    tools, resources, templates = _owner_people_discovery(hub)
    assert len(tools) > 1 and resources and templates
    response = hub.client.put("/api/settings/people-access", json={"mode": "off"})
    assert response.status_code == 200 and response.json()["receipt"]["outcome"] == "succeeded"
    assert _owner_people_discovery(hub) == (["people.access.set"], [], [])
    is_error, answer = hub.mcp("people.access.set", {"mode": "write"})
    assert is_error is False and answer["mode"] == "write"
    tools, resources, templates = _owner_people_discovery(hub)
    assert len(tools) > 1 and resources and templates


def test_env_off_hides_people_from_owner_discovery(hub, config_file, monkeypatch) -> None:
    monkeypatch.setenv("HOLDSPEAK_MCP_PEOPLE_ACCESS", "off")
    assert _owner_people_discovery(hub) == (["people.access.set"], [], [])
    # The stdio path (handle_message) lists the same.
    from holdspeak.mcp.server import handle_message

    listed = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert [t["name"] for t in listed["result"]["tools"] if t["name"].startswith("people.")] == ["people.access.set"]


def test_door_keeps_real_people_commitment_for_launch(hub, config_file) -> None:
    """Finding 1: a real accepted People commitment reaches the launched
    agent's board and Door, as it reaches the owner's."""
    from test_conductor_k6_agent_mcp import _people_rig

    person = _people_rig(hub)
    error, request = hub.mcp("people.request.create", {"relationship_id": person["id"], "body": "R7 commitment sentinel"})
    assert not error
    error, commitment = hub.mcp("people.request.accept", {"request_id": request["id"]})
    assert not error and commitment["visibility"] == "shared_intent"
    agent = _client(hub, _launch_credential().token)
    error, direct = _result(_call(agent, "people.relationship.get", {"relationship_id": person["id"]}))
    assert not error and "R7 commitment sentinel" in json.dumps(direct)
    error, owner_door = hub.mcp("door.get", {})
    assert not error and "R7 commitment sentinel" in json.dumps(owner_door)
    error, agent_door = _result(_call(agent, "door.get", {}))
    assert not error and "active" not in agent_door["board"]
    assert "R7 commitment sentinel" in json.dumps(agent_door)
    error, board = _result(_call(agent, "follow_through.board", {}))
    assert not error and "R7 commitment sentinel" in json.dumps(board)
    # Its transition stays the owner's.
    from holdspeak.services.people_service import PeopleServiceError

    service = hub.root.web_context.people_service
    with pytest.raises(PeopleServiceError) as refused:
        service.transition(agent_credentials_principal(agent), f"people:{commitment['id']}", "done")
    assert str(refused.value) == "people_owner_required" or getattr(refused.value, "code", "") == "people_owner_required"


def agent_credentials_principal(agent) -> Any:
    from holdspeak.principals import agent_credentials

    token = agent.headers["Authorization"].split(" ", 1)[1]
    return agent_credentials.derive(token)
