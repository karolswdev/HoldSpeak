"""Engines on MCP, against a real hub (Betterment MCP slice M4).

A real MeetingWebServer (``_boot``: isolated HOME and DB) and the fake
``claude``/``codex`` (tests/fixtures/fake_agent_cli.py) first on PATH; the
owner's real CLIs never run. Every call goes through ``/api/mcp``.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.glass_infra import _boot
from tests.fixtures.fake_agent_cli import calls, install_fake_agent_clis, path_with, set_claude_answer

TOKEN = "desk-engines-mcp"

pytestmark = pytest.mark.timeout(180, method="thread")


def _mcp(base: str, name: str, arguments: dict, *, token: str = TOKEN) -> Any:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": name, "arguments": arguments}}).encode()
    request = urllib.request.Request(f"{base}/api/mcp", data=body, method="POST", headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return {"http_status": exc.code, "body": exc.read().decode()}


def _value(reply: Any) -> Any:
    assert "result" in reply and not reply["result"].get("isError"), reply
    return json.loads(reply["result"]["content"][0]["text"])


def _refused(reply: Any) -> str:
    if "error" in reply or "http_status" in reply:
        return json.dumps(reply)
    if reply.get("result", {}).get("isError"):
        return json.dumps(reply["result"])
    return ""


@pytest.fixture()
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        yield base
    finally:
        server.stop()


@pytest.fixture()
def fake_bin(hub: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    bin_dir = install_fake_agent_clis(tmp_path / "home" / "bin")
    monkeypatch.setenv("PATH", path_with(bin_dir))
    monkeypatch.setenv("HOLDSPEAK_CLI_ENGINES", "on")
    return bin_dir


def _agents(detected: dict) -> dict[str, dict]:
    return {row["id"]: row for row in detected["engines"] if row.get("kind") == "agent"}


def test_add_claude_code_and_use_it_for_answers_through_mcp_alone(hub: str, fake_bin: Path) -> None:
    """Done when (M4): from an owner session, "add Claude Code and use it for
    Answers" works through MCP alone: concierge.detect lists the CLI it
    finds, model_library.connect_cli_engine adds it, inference_assignment.set
    gives it Answers, and an Ask answers on it. set_spend_limit changes its
    limit in place; the run is given that limit."""
    found = _agents(_value(_mcp(hub, "concierge.detect", {})))
    assert found["agent:found:claude"]["name"] and found["agent:found:claude"]["agentPreset"] == "claude"
    assert "agent:found:codex" in found

    added = _value(_mcp(hub, "model_library.connect_cli_engine", {"draft": {
        "request_id": "mcp-add-claude", "profile_id": "agent-claude",
        "expected_profile_revision": 0, "preset": "claude"}}))
    profile = added["provider"]
    assert profile["profile_id"] == "agent-claude"
    after = _agents(_value(_mcp(hub, "concierge.detect", {})))
    assert "agent:found:claude" not in after  # an engine now, no longer "found"
    [engine] = [row for row in after.values() if row.get("agentPreset") == "claude"]
    assert engine["state"] == "READY" and engine["spend"]["limitUsd"] is None, engine

    _value(_mcp(hub, "inference_assignment.set", {
        "command_id": "mcp-answers-claude", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "ask.answer"},
        "entries": [{"profile_id": profile["profile_id"], "profile_revision": int(profile["profile_revision"])}],
    }))
    limited = _value(_mcp(hub, "model_library.set_spend_limit", {
        "request_id": "mcp-limit", "profile_id": "agent-claude", "spend_limit_usd": 0.4}))
    assert limited["provider"]["profile_id"] == "agent-claude"
    [engine] = [row for row in _agents(_value(_mcp(hub, "concierge.detect", {}))).values()
                if row.get("agentPreset") == "claude"]
    assert engine["spend"]["limitUsd"] == 0.4, engine

    set_claude_answer(fake_bin, "You met about the ledger cutover.")
    asked = _value(_mcp(hub, "ask.run", {"question": "What did I meet about?"}))
    assert "ledger cutover" in json.dumps(asked), asked
    runs = calls(fake_bin, "claude")
    assert runs, "the agent CLI never ran"
    for run in runs:
        assert run["argv"][run["argv"].index("--max-budget-usd") + 1] == "0.40", run["argv"]

    # No limit again; and Codex cannot enforce one, in words.
    _value(_mcp(hub, "model_library.set_spend_limit", {
        "request_id": "mcp-no-limit", "profile_id": "agent-claude", "spend_limit_usd": None}))
    _value(_mcp(hub, "model_library.connect_cli_engine", {"draft": {
        "request_id": "mcp-add-codex", "profile_id": "agent-codex", "expected_profile_revision": 0, "preset": "codex"}}))
    refused = _mcp(hub, "model_library.set_spend_limit", {
        "request_id": "mcp-codex-limit", "profile_id": "agent-codex", "spend_limit_usd": 1.0})
    assert "cannot stop a run at a spend limit" in _refused(refused), refused
    refused = _mcp(hub, "model_library.set_spend_limit", {
        "request_id": "mcp-no-engine", "profile_id": "no-such-engine", "spend_limit_usd": 1.0})
    assert "Only an agent engine" in _refused(refused), refused


def test_define_endpoint_keeps_the_servers_context_over_the_hubs_mcp(
    hub: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FOLLOWUPS E3 (E5 added it; covered here end to end): an agent defines a
    LAN engine with the context its server runs (49,152), not 16,384."""
    monkeypatch.setattr("holdspeak.setup_runtime.discover_endpoint_models",
                        lambda *_a, **_k: {"ok": True, "models": ["qwen-lan"]})
    _value(_mcp(hub, "model_library.define_endpoint", {"draft": {
        "request_id": "mcp-lan", "profile_id": "lan-qwen", "expected_profile_revision": 0,
        "label": "LAN Qwen", "provider_family": "private_endpoint", "model": "qwen-lan",
        "endpoint": "http://192.168.1.43:8080/v1", "requires_key": False, "context_tokens": 49152,
    }, "secret": None}))
    from holdspeak.db import get_database

    assert get_database().profiles.get("library_provider_lan-qwen").context_limit == 49152


def test_an_agent_run_never_adds_an_engine_or_changes_its_limit(hub: str) -> None:
    """The engine tools are config: a CONDUCTOR credential (an agent run) is
    refused, as a Thread is (tool_authority)."""
    from holdspeak.intel.cli_engine import run_identity
    from holdspeak.mcp.palettes import CONDUCTOR, resolve_palette
    from holdspeak.principals import agent_credentials

    token = agent_credentials.issue(run_identity("m4test0001"), palette=resolve_palette(CONDUCTOR),
                                    palette_name=CONDUCTOR, launch_id="m4test0001").token
    for name, arguments in (
        ("model_library.connect_cli_engine", {"draft": {"request_id": "x", "profile_id": "agent-claude",
                                                         "expected_profile_revision": 0, "preset": "claude"}}),
        ("model_library.set_spend_limit", {"request_id": "y", "profile_id": "agent-claude", "spend_limit_usd": 5}),
    ):
        assert _refused(_mcp(hub, name, arguments, token=token)), name
    assert _value(_mcp(hub, "concierge.detect", {}, token=token))["engines"] is not None  # a read
