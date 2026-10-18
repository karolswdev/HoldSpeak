"""Automations on MCP, against a real hub (Betterment MCP slice M3).

A real MeetingWebServer (``_boot``: isolated HOME and DB) and the fake
``claude`` (tests/fixtures/fake_agent_cli.py) first on PATH; the owner's real
CLIs never run. Every call goes through ``/api/mcp``: the owner's credential
(his own Claude Code session) and a CONDUCTOR credential (an agent run).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.glass_infra import _boot
from tests.fixtures.fake_agent_cli import (
    CLAUDE_COST_USD,
    calls,
    install_fake_agent_clis,
    path_with,
    set_claude_answer,
    set_mode,
    set_tool_plan,
)

TOKEN = "desk-automations-mcp"
MEMORY_ASK = "what ONE thing should future runs"

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


def _mcp(base: str, name: str, arguments: dict, *, token: str = TOKEN) -> Any:
    status, reply = _call(base, "POST", "/api/mcp", {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments},
    }, token=token)
    assert status == 200, (status, reply)
    return reply


def _value(reply: Any) -> Any:
    """The tool's value of a successful tools/call answer."""
    assert "result" in reply and not reply["result"].get("isError"), reply
    return json.loads(reply["result"]["content"][0]["text"])


def _refused(reply: Any) -> str:
    if "error" in reply:
        return json.dumps(reply["error"])
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


def _connect_claude(base: str) -> str:
    connected = _ok(base, "POST", "/api/inference/model-library/connect-cli-engine", {"draft": {
        "request_id": "connect-claude", "profile_id": "agent-claude",
        "expected_profile_revision": 0, "preset": "claude",
    }})
    return str(connected["provider"]["profile_id"])


def _conductor_token(run_id: str = "m3test0001") -> str:
    from holdspeak.intel.cli_engine import run_identity
    from holdspeak.mcp.palettes import CONDUCTOR, resolve_palette
    from holdspeak.principals import agent_credentials

    return agent_credentials.issue(
        run_identity(run_id), palette=resolve_palette(CONDUCTOR), palette_name=CONDUCTOR, launch_id=run_id,
    ).token


FRIDAY = {"schedule": {"every": "week", "day": "friday", "time": "15:00"}}


def test_one_owner_call_makes_the_friday_update_and_results_reads_each_run(hub: str, fake_bin: Path) -> None:
    """Done when (M3): one MCP call (the owner's session) creates the Friday
    update automation, complete: Do, About, When (on), With, Put it in and
    its Spend limit. After a run, workbench.results returns the rendered
    text, Looked at, cost and, for a failed run, the failure reason. The
    memory call after the item runs without the desk's tools (M2 follow-up)."""
    note = _ok(hub, "POST", "/api/notes", {"title": "Platform sync", "body_markdown": "Cutover moves to Friday."})["note"]["id"]
    engine = _connect_claude(hub)

    made = _value(_mcp(hub, "automation.create", {
        "name": "Friday update", "do": "Write my Friday team update.", "about": [f"note:{note}"],
        "when": FRIDAY, "with": engine, "put_in": "inbox", "spend_limit": 0.5,
    }))

    assert (made["instruction"], made["sources"], made["output_target"]) == (
        "Write my Friday team update.", [f"note:{note}"], "inbox")
    assert (made["schedule"], made["schedule_enabled"], made["when_kind"]) == ("0 15 * * 5", True, "schedule")
    assert made["next_run_at"] and "notice" not in made
    assert made["assignment_summary"]["profile_id"] == engine
    assert made["spend_limit_usd"] == 0.5
    # The Automations app reads the same automation.
    assert _ok(hub, "GET", f"/api/workbenches/{made['id']}")["workbench"]["schedule_enabled"] is True

    set_tool_plan(fake_bin, "claude", [{"name": "desk.get", "arguments": {"kind": "notes", "id": note}}], once=True)
    set_claude_answer(fake_bin, "## Friday update\n\n- The cutover moves to Friday.")
    _value(_mcp(hub, "automation.run", {"workbench_id": made["id"]}))

    [done] = _value(_mcp(hub, "workbench.results", {"workbench_id": made["id"]}))["results"]
    assert done["status"] == "done" and done["text"].startswith("## Friday update"), done
    assert [row["ref"] for row in done["used"]["looked_at"]] == [f"note:{note}"], done["used"]
    runs = calls(fake_bin, "claude")
    assert done["cost_usd"] == pytest.approx(CLAUDE_COST_USD * len(runs)) and done["error"] is None, done
    # Each item call had the desk's tools; the memory call after it had none.
    memory = [run for run in runs if MEMORY_ASK in run["prompt"]]
    items = [run for run in runs if MEMORY_ASK not in run["prompt"]]
    assert memory and items, runs
    assert all("--mcp-config" in run["argv"] and run["credential"] for run in items)
    assert all("--mcp-config" not in run["argv"] and not run["credential"] for run in memory)
    assert all("--strict-mcp-config" in run["argv"] for run in memory)

    set_mode(fake_bin, "claude", "fail")
    _mcp(hub, "automation.run", {"workbench_id": made["id"]})
    newest, older = _value(_mcp(hub, "automation.results", {"workbench_id": made["id"], "limit": 5}))["results"]
    assert newest["status"] == "failed" and newest["error"] and newest["text"] is None, newest
    assert older["item_id"] == done["item_id"]


def test_a_schedule_without_an_engine_is_made_and_kept_off_with_its_reason(hub: str) -> None:
    """The automation exists after the one call (no duplicate on a retry);
    its schedule is stored, off, and the answer says why."""
    made = _value(_mcp(hub, "workbench.create", {"name": "Friday update", "do": "Write it.", "when": FRIDAY}))
    assert (made["schedule"], made["schedule_enabled"]) == ("0 15 * * 5", False)
    assert "choose an engine" in made["notice"]
    # A bad When refuses before anything is written.
    before = len(_value(_mcp(hub, "automation.list", {})))
    bad = _mcp(hub, "automation.create", {"name": "Bad", "when": {"schedule": {"every": "week", "time": "15:00"}}})
    assert "day of the week" in _refused(bad)
    bad = _mcp(hub, "automation.create", {"name": "Bad", "when": {"event": "a-meeting-ends"}})
    assert "events the hub can deliver" in _refused(bad)
    assert len(_value(_mcp(hub, "automation.list", {}))) == before
    # Nothing is running: cancel says so.
    assert "Nothing is running" in _refused(_mcp(hub, "automation.cancel", {"workbench_id": made["id"]}))


def test_an_agent_run_drafts_an_automation_but_never_turns_it_on_or_picks_its_engine(hub: str) -> None:
    """A CONDUCTOR credential (an agent run) may write the content of an
    automation it makes and read its results. when (authority), with and
    spend_limit (config) stop for the owner's press; so does a change to the
    owner's own automation."""
    token = _conductor_token()
    owners = _value(_mcp(hub, "workbench.create", {"name": "Owner's update", "do": "Mine."}))["id"]

    for words in ({"when": FRIDAY}, {"with": "agent-claude"}, {"spend_limit": 1.0}):
        refused = _mcp(hub, "automation.create", {"name": "Agent's", **words}, token=token)
        assert _refused(refused), (words, refused)
    drafted = _value(_mcp(hub, "automation.create", {
        "name": "Agent's draft", "do": "Summarize the week.", "about": ["meetings:this_week"]}, token=token))
    assert (drafted["schedule_enabled"], drafted["instruction"]) == (False, "Summarize the week.")
    changed = _value(_mcp(hub, "automation.update", {"workbench_id": drafted["id"], "do": "Summarize it."}, token=token))
    assert changed["instruction"] == "Summarize it."
    assert _value(_mcp(hub, "automation.results", {"workbench_id": drafted["id"]}, token=token))["results"] == []
    assert _refused(_mcp(hub, "automation.update", {"workbench_id": drafted["id"], "when": {"manual": True}}, token=token))
    assert _refused(_mcp(hub, "automation.update", {"workbench_id": owners, "do": "Hijacked."}, token=token))
    assert _refused(_mcp(hub, "automation.run", {"workbench_id": drafted["id"]}, token=token))
    assert _ok(hub, "GET", f"/api/workbenches/{owners}")["workbench"]["instruction"] == "Mine."


def test_cancel_cancels_the_newest_running_run_by_its_parent_operation(
    hub: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """workbench.cancel finds the run that is running and hands its parent
    operation to the kernel's cancel (the same seam as the window's Cancel)."""
    from holdspeak.db import get_database
    from holdspeak.services.workbench_service import WorkbenchService

    bench = _value(_mcp(hub, "workbench.create", {"name": "Long one", "do": "Take a while."}))["id"]
    with get_database()._connection() as conn:
        for run_id, started, status, op in (("run-old", "2026-10-01T09:00:00", "running", "op-old"),
                                            ("run-new", "2026-10-02T09:00:00", "running", "op-new"),
                                            ("run-done", "2026-10-03T09:00:00", "completed", "op-done")):
            conn.execute("INSERT INTO workbench_runs(id,workbench_id,started_at,parent_operation_id,"
                         "parent_receipt_id,child_links_json,status) VALUES(?,?,?,?,'','[]',?)",
                         (run_id, bench, started, op, status))
    cancelled: list[str] = []
    monkeypatch.setattr(WorkbenchService, "cancel_run",
                        lambda self, principal, op: cancelled.append(op) or "cancelled")

    assert _value(_mcp(hub, "automation.cancel", {"workbench_id": bench})) == {
        "run_id": "run-new", "disposition": "cancelled"}
    assert _value(_mcp(hub, "workbench.cancel", {"workbench_id": bench, "run_id": "run-old"}))["run_id"] == "run-old"
    assert cancelled == ["op-new", "op-old"]
    assert "Nothing is running" in _refused(_mcp(hub, "workbench.cancel", {"workbench_id": bench, "run_id": "run-done"}))
