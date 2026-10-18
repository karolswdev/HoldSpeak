"""Engines, against a real hub: an agent CLI run gets the desk's tools (Betterment M1).

A real MeetingWebServer (``_boot``: isolated HOME and DB). The fake
``claude``/``codex`` (tests/fixtures/fake_agent_cli.py) are first on PATH and
speak MCP to this hub through exactly what the real CLIs are given: Claude
Code the 0600 ``--mcp-config`` file (``${VAR}`` expanded from its
environment), Codex the ``-c mcp_servers.holdspeak.*`` settings. The owner's
real CLIs never run.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.glass_infra import _boot
from tests.fixtures.fake_agent_cli import (
    calls,
    install_fake_agent_clis,
    mcp_runs,
    path_with,
    set_tool_plan,
)

TOKEN = "desk-engines-tools"

pytestmark = pytest.mark.timeout(180, method="thread")


def _call(base: str, method: str, path: str, body: Any = None, *, token: str = TOKEN) -> tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {token}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{base}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, json.loads(raw) if raw else {}


def _ok(base: str, method: str, path: str, body: Any = None) -> Any:
    status, payload = _call(base, method, path, body)
    assert status < 300, (status, path, payload)
    return payload


def _mcp(base: str, name: str, arguments: dict, *, token: str = TOKEN) -> tuple[int, Any]:
    return _call(base, "POST", "/api/mcp", {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments},
    }, token=token)


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


def _connect(base: str, preset: str) -> dict:
    connected = _ok(base, "POST", "/api/inference/model-library/connect-cli-engine", {"draft": {
        "request_id": f"connect-{preset}", "profile_id": f"agent-{preset}",
        "expected_profile_revision": 0, "preset": preset,
    }})
    return {
        "profile_id": connected["provider"]["profile_id"],
        "profile_revision": int(connected["provider"]["profile_revision"]),
    }


def _assign(base: str, capability: str, entry: dict) -> None:
    _ok(base, "POST", "/api/inference/assignments/set", {
        "command_id": f"assign-{capability}", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": capability}, "entries": [entry],
    })


def _seed_meeting() -> None:
    from holdspeak.db import get_database
    from holdspeak.meeting_session import MeetingState, TranscriptSegment

    start = datetime.now() - timedelta(minutes=30)
    get_database().meetings.save_meeting(MeetingState(
        id="m-cutover", started_at=start, ended_at=start + timedelta(minutes=20), title="Ledger cutover sync",
        segments=[TranscriptSegment(text="We cut over on Friday.", speaker="Me", start_time=1.0, end_time=3.0)]))


def _tool_text(reply: Any) -> str:
    """The text of a successful tools/call answer ('' for an error)."""
    if not isinstance(reply, dict) or "result" not in reply or reply["result"].get("isError"):
        return ""
    return "\n".join(str(part.get("text") or "") for part in reply["result"].get("content") or [])


def _refused(reply: Any) -> str:
    """The refusal of a tools/call answer, as text ('' when it succeeded)."""
    if isinstance(reply, dict) and "error" in reply:
        return json.dumps(reply["error"])
    if isinstance(reply, dict) and reply.get("result", {}).get("isError"):
        return json.dumps(reply["result"])
    return ""


@pytest.mark.parametrize("preset", ["claude", "codex"])
def test_a_run_reads_real_rows_and_is_refused_a_send_and_the_owners_records(
    hub: str, fake_bin: Path, preset: str,
) -> None:
    """Done when (M1): meeting.list through the given config returns the rig's
    rows; channel.send is refused (no egress in the CONDUCTOR set); the run may
    not delete the owner's automation (it changes only what it made); after
    the run the credential is dead and the config is gone."""
    _seed_meeting()
    owners = _ok(hub, "POST", "/api/workbenches", {"name": "Owner's bench"})["workbench"]["id"]
    _assign(hub, "ask.answer", _connect(hub, preset))
    set_tool_plan(fake_bin, preset, [
        {"name": "meeting.list", "arguments": {}},
        {"name": "channel.send", "arguments": {"send_id": "send-x"}},
        {"name": "workbench.delete", "arguments": {"workbench_id": owners}},
    ])

    _ok(hub, "POST", "/api/ask", {"prompt": "Which meetings did I have?"})

    (run,) = mcp_runs(fake_bin, preset)
    assert run["server"]["url"].endswith("/api/mcp") and run["server"]["url"].startswith("http://127.0.0.1:")
    assert run["initialize"] == 200, run
    listed, sent, deleted = run["calls"]
    assert listed["status"] == 200 and "Ledger cutover sync" in _tool_text(listed["reply"]), listed
    assert sent["status"] == 200 and "MCP-005" in _refused(sent["reply"]), sent
    assert deleted["status"] == 200 and _refused(deleted["reply"]), deleted
    assert _ok(hub, "GET", f"/api/workbenches/{owners}")["workbench"]["id"] == owners  # still there

    (call,) = calls(fake_bin, preset)
    assert call["cwd_entries"] == []
    if preset == "claude":
        assert "--strict-mcp-config" in call["argv"] and call["mcp_config_mode"] == "0o600"
        assert not Path(call["mcp_config"]).exists(), "the run config outlived the run"
    else:
        assert "features.apps=false" in call["argv"]
    # The run credential is dead after the run.
    status, _ = _mcp(hub, "meeting.list", {}, token=run["token"])
    assert status == 401, status


def test_a_run_whose_agent_reads_its_own_automation_does_not_hang(hub: str, fake_bin: Path) -> None:
    """MODEL.md section 3: workbench.run over MCP holds the automation's lock
    for the whole run. The agent inside reads that automation; its read must
    answer at once, not wait for the run to time out."""
    recipe = _ok(hub, "POST", "/api/recipes", {"name": "Chase", "system_prompt": "Do the work."})["recipe"]["id"]
    bench = _ok(hub, "POST", "/api/workbenches", {"name": "Cutover bench", "recipe_id": recipe})["workbench"]["id"]
    _ok(hub, "POST", f"/api/workbenches/{bench}/items", {"title": "Draft the runbook"})
    _assign(hub, "workbench.item", _connect(hub, "claude"))
    set_tool_plan(fake_bin, "claude", [
        {"name": "workbench.get", "arguments": {"workbench_id": bench}},
        {"name": "workbench.list_runs", "arguments": {"workbench_id": bench}},
    ], timeout=20.0)

    status, ran = _mcp(hub, "workbench.run", {"workbench_id": bench})

    assert status == 200, ran
    runs = mcp_runs(fake_bin, "claude")
    assert runs, f"the CLI never ran: {ran}"
    got, listed = runs[0]["calls"]
    assert got["status"] == 200 and "Cutover bench" in _tool_text(got["reply"]), got
    assert listed["status"] == 200 and _tool_text(listed["reply"]), listed
    assert got["seconds"] < 10 and listed["seconds"] < 10, runs[0]["calls"]
