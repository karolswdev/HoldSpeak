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
    set_claude_answer,
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


def _seed_meetings(titles: list[str]) -> list[str]:
    from holdspeak.db import get_database
    from holdspeak.meeting_session import MeetingState, TranscriptSegment

    ids = []
    for n, title in enumerate(titles):
        start = datetime.now() - timedelta(hours=n + 1)
        meeting_id = f"m-looked-{n}"
        get_database().meetings.save_meeting(MeetingState(
            id=meeting_id, started_at=start, ended_at=start + timedelta(minutes=20), title=title,
            segments=[TranscriptSegment(text="We cut over on Friday.", speaker="Me", start_time=1.0, end_time=3.0)]))
        ids.append(meeting_id)
    return ids


def test_a_result_says_what_its_agent_looked_at_and_wrote_and_what_it_cost(
    hub: str, fake_bin: Path, tmp_path: Path,
) -> None:
    """Done when (M2): a fake agent that reads 3 meetings and writes 1 note
    gives a result whose Looked at names the 3 meetings and whose Wrote names
    the 1 note (with Undo: the run made it), each by its title and its ref;
    a send it prepared is listed under Prepared with its send id (he presses
    Send); a refused call and a list name nothing; the result carries the
    run's reported cost (E2's cli_engine_runs row, linked by its item)."""
    from tests.fixtures.fake_agent_cli import CLAUDE_COST_USD

    titles = ["Ledger cutover sync", "Hiring loop debrief", "Platform weekly"]
    meetings = _seed_meetings(titles)
    brief = _ok(hub, "POST", "/api/notes", {"title": "Cutover brief", "body_markdown": "Friday."})["note"]["id"]
    folder = tmp_path / "outbox"
    folder.mkdir()
    destination = _ok(hub, "POST", "/api/channels/destinations",
                      {"name": "Outbox folder", "channel": "file", "folder": str(folder)})["destination"]["id"]
    bench = _ok(hub, "POST", "/api/workbenches", {"name": "Friday update"})["workbench"]["id"]
    _ok(hub, "PUT", f"/api/workbenches/{bench}", {"instruction": "Write my Friday update from my meetings."})
    _assign(hub, "workbench.item", _connect(hub, "claude"))
    set_tool_plan(fake_bin, "claude", [
        {"name": "meeting.list", "arguments": {}},
        *({"name": "meeting.get", "arguments": {"meeting_id": m}} for m in meetings),
        {"name": "desk.create", "arguments": {"kind": "notes", "data": {
            "title": "Friday update draft", "body_markdown": "Cutover on Friday."}}},
        {"name": "channel.prepare", "arguments": {"document_ref": f"note:{brief}", "destination_id": destination}},
        {"name": "channel.send", "arguments": {"send_id": "send-x"}},
    ], once=True)
    set_claude_answer(fake_bin, "## Friday update\n\n- The ledger cutover moves to Friday.\n- Two hiring loops are booked.")

    _ok(hub, "POST", f"/api/workbenches/{bench}/run", {})

    (run,) = mcp_runs(fake_bin, "claude")
    created = run["calls"][4]
    assert created["status"] == 200 and _tool_text(created["reply"]), created
    results = _ok(hub, "GET", f"/api/workbenches/{bench}")["workbench"]["results"]
    assert results and results[0]["status"] == "done", results
    used = results[0]["used"]
    assert used is not None, results[0]
    assert [(row["ref"], row["label"]) for row in used["looked_at"]] == [
        (f"meeting:{m}", t) for m, t in zip(meetings, titles)], used
    [wrote] = used["wrote"]
    assert wrote["ref"].startswith("note:") and wrote["label"] == "Friday update draft" and wrote["undo"] is True, wrote
    note_id = wrote["ref"].removeprefix("note:")
    assert _ok(hub, "GET", f"/api/notes/{note_id}")  # the link names a real note
    [prepared] = used["prepared"]
    assert prepared["ref"] == f"note:{brief}" and prepared["label"] == "Cutover brief", prepared
    assert prepared["destination"] == "Outbox folder" and prepared["send_id"], prepared
    assert list(folder.iterdir()) == []  # prepared only: nothing left the desk
    # One CLI run per engine call (the item; the memory note after it too):
    # the result's cost is their sum.
    engine_calls = len(calls(fake_bin, "claude"))
    assert engine_calls >= 1
    assert results[0]["cost_usd"] == pytest.approx(CLAUDE_COST_USD * engine_calls), (results[0], engine_calls)
    _record_used_step(hub, bench, tmp_path, f"note:{brief}")


AUTOMATION_HUB = Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "__tests__" / "fixtures" / "automation-hub"


def _shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _shape(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_shape(v) for v in value]
    return "null" if value is None else type(value).__name__


def _record_used_step(base: str, bench: str, tmp_path: Path, prepared_ref: str) -> None:
    """The automation window's reads after this run (the automation, its
    lessons, and the sends of the document the agent prepared), for its
    vitest (web/src/desk/__tests__/automation.app.test.tsx).
    HOLDSPEAK_WIRE_WRITE=1 rewrites automation-hub/used.json; else this
    fences its shape."""
    import os
    import re

    answers = {
        f"/api/workbenches/{bench}": _ok(base, "GET", f"/api/workbenches/{bench}"),
        f"/api/workbenches/{bench}/memory": _ok(base, "GET", f"/api/workbenches/{bench}/memory"),
        f"/api/channels/sends?document_ref={prepared_ref}": _ok(
            base, "GET", f"/api/channels/sends?document_ref={prepared_ref}"),
    }
    text = re.sub(re.escape(str(tmp_path)), "/tmp/rig", json.dumps(answers))
    scrubbed = json.loads(re.sub(re.escape(base), "http://127.0.0.1:0", text))
    path = AUTOMATION_HUB / "used.json"
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.write_text(json.dumps({
            "_source": "The hub's own answers, captured by tests/integration/test_desk_engines_tools.py "
                       "(a real hub, isolated database, the fake claude CLI reading 3 meetings, writing 1 note "
                       "and preparing 1 send over MCP). HOLDSPEAK_WIRE_WRITE=1 rewrites this file; never hand-edit it.",
            "workbench_id": bench, "gets": scrubbed}, indent=1, ensure_ascii=False) + "\n")
    assert path.exists(), f"no stored answers {path}; run with HOLDSPEAK_WIRE_WRITE=1"
    stored = json.loads(path.read_text())["gets"]
    assert _shape(list(stored.values())) == _shape(list(scrubbed.values())), \
        f"{path.name}: the stored answers are not the hub's shape"


def test_the_automation_spend_limit_reaches_the_cli_and_the_result_cost_is_that_run(
    hub: str, fake_bin: Path,
) -> None:
    """Betterment A4 x M2: the automation's own Spend limit per run is the one
    the agent CLI is given (not the engine's), and the result's cost is the
    cost that limited run reported, for a finished run and for a run the CLI
    stopped at its limit."""
    from tests.fixtures.fake_agent_cli import CLAUDE_COST_USD, set_mode

    bench = _ok(hub, "POST", "/api/workbenches", {"name": "Friday update"})["workbench"]["id"]
    _ok(hub, "PUT", f"/api/workbenches/{bench}", {"instruction": "Write my Friday update."})
    _ok(hub, "POST", "/api/inference/model-library/connect-cli-engine", {"draft": {
        "request_id": "connect-claude-limit", "profile_id": "agent-claude",
        "expected_profile_revision": 0, "preset": "claude", "spend_limit_usd": 2.0,
    }})
    _ok(hub, "PUT", f"/api/workbenches/{bench}/engine", {"profile_id": "agent-claude", "spend_limit_usd": 0.25})
    set_claude_answer(fake_bin, "## Friday update\n\n- The cutover moves to Friday.")

    _ok(hub, "POST", f"/api/workbenches/{bench}/run", {})
    runs = calls(fake_bin, "claude")
    assert runs, "the agent CLI never ran"
    for run in runs:
        argv = run["argv"]
        assert argv[argv.index("--max-budget-usd") + 1] == "0.25", argv
        assert argv.count("--max-budget-usd") == 1, argv
    [done] = _ok(hub, "GET", f"/api/workbenches/{bench}")["workbench"]["results"]
    assert done["status"] == "done" and done["cost_usd"] == pytest.approx(CLAUDE_COST_USD * len(runs)), done

    # The CLI stops at the limit: the result fails, and still says what it cost.
    set_mode(fake_bin, "claude", "error")
    _ok(hub, "POST", f"/api/workbenches/{bench}/run", {})
    stopped = _ok(hub, "GET", f"/api/workbenches/{bench}")["workbench"]["results"][0]
    assert stopped["status"] == "failed" and stopped["cost_usd"] == pytest.approx(CLAUDE_COST_USD), stopped


# ── Betterment A10: an agent works in a folder (workbench/RECIPE.md A10) ──────


def _git_folder(root: Path) -> Path:
    import subprocess

    root.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    (root / "ledger.py").write_text("def cut_over():\n    return True\n")
    (root / "risky_migration.sql").write_text("ALTER TABLE ledger DROP COLUMN legacy_id;\n")
    (root / "README.md").write_text("# Ledger\n")
    return root


def test_an_agent_works_in_the_chosen_folder_read_only_for_a_press_and_a_review_request(
    hub: str, fake_bin: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Done when (A10): with a fake CLI that lists its cwd, the result names the
    folder's files; a recorded review-request event produces the summary, run
    in the same folder. Claude Code gets its read tools only, never the
    folder's own settings, and only HoldSpeak's MCP server; the egress chip
    names the vendor; the folder is unchanged."""
    import asyncio
    import subprocess

    import holdspeak.delivery.registry as registry
    from holdspeak.db import get_database
    from holdspeak.services.reaction_service import ReactionService
    from holdspeak.services.watch_sources import GitHubWatchSource
    from tests.fixtures.fake_agent_cli import set_mode

    from holdspeak.principals import Principal, PrincipalKind

    monkeypatch.setattr(registry, "DEFAULT_REGISTRY_PATH", tmp_path / "home" / ".holdspeak" / "delivery_sources.json")
    folder = _git_folder(tmp_path / "repos" / "ledger")
    before = sorted(p.name for p in folder.iterdir())
    registered = _ok(hub, "POST", "/api/repositories", {"path": str(folder)})
    repo = registered["repository"]

    bench = _ok(hub, "POST", "/api/workbenches", {"name": "Review summary"})["workbench"]["id"]
    _ok(hub, "PUT", f"/api/workbenches/{bench}", {
        "instruction": "Summarize the PR and the risky files.", "sources": [f"repository:{repo['id']}"]})
    _connect(hub, "claude")
    _ok(hub, "PUT", f"/api/workbenches/{bench}/engine", {"profile_id": "agent-claude"})
    detail = _ok(hub, "GET", f"/api/workbenches/{bench}")["workbench"]
    assert [(s["kind"], s["label"], s["missing"]) for s in detail["sources_shown"]] == [("folder", "ledger", False)]
    assert detail["assignment_summary"]["vendor"] == "Anthropic"
    assert str(folder) not in json.dumps(detail)  # the path stays on the hub

    # Run now: the agent works in the folder and names its files.
    set_mode(fake_bin, "claude", "list")
    _ok(hub, "POST", f"/api/workbenches/{bench}/run", {})
    first = calls(fake_bin, "claude")[0]
    assert first["cwd"] == str(folder.resolve()), first["cwd"]
    assert first["argv"][:3] == ["-p", "--tools", "Read,Glob,Grep"]
    assert first["argv"][first["argv"].index("--setting-sources") + 1] == "user"
    assert "--strict-mcp-config" in first["argv"]
    assert "Summarize the PR and the risky files." in first["prompt"]
    assert f"You work in the folder {folder.resolve()}" in first["prompt"]
    [done] = _ok(hub, "GET", f"/api/workbenches/{bench}")["workbench"]["results"]
    assert done["status"] == "done" and "ledger.py" in done["text"] and "risky_migration.sql" in done["text"], done
    _record_folder_step(hub, bench, tmp_path, registered)

    # A recorded review-request event: one result about that PR, made in the folder.
    wire = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "automations"
                       / "gh_pr_review_requested.json").read_text())

    def snapshot(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        def replay(command, **_kwargs):
            assert command[:3] == ["gh", "pr", "list"]
            return subprocess.CompletedProcess(command, 0, json.dumps(rows), "")
        return GitHubWatchSource(runner=replay).snapshot(
            owner, query_kind="pull_requests", query={"repository": wire["repository"]})

    owner = Principal(PrincipalKind.OWNER, "desk-engines-a10")
    reactions = ReactionService(get_database())
    watch = reactions.create_watch(owner, connector_id="gh", query_kind="pull_requests",
                                   query={"repository": wire["repository"]}, watch_id="watch-a10")
    reactions.create_reaction(owner, watch_id=watch["id"], event_pattern="github.pr.review_requested",
                              workbench_id=bench, reaction_id="reaction-a10", enabled=True, auto_run=True)
    asyncio.run(reactions.refresh_watch(owner, watch["id"], snapshot(wire["before"])))
    seen = len(calls(fake_bin, "claude"))
    asyncio.run(reactions.refresh_watch(owner, watch["id"], snapshot(wire["after"])))
    event_run = calls(fake_bin, "claude")[seen]
    assert event_run["cwd"] == str(folder.resolve())
    assert "https://github.com/acme/ledger/pull/418" in event_run["prompt"]
    newest = _ok(hub, "GET", f"/api/workbenches/{bench}")["workbench"]["results"][0]
    assert newest["title"] == "Move the ledger cutover behind a flag" and newest["status"] == "done", newest
    assert "risky_migration.sql" in newest["text"]
    event_step = _record_folder_step(hub, bench, tmp_path, registered, "folder-event")
    assert event_step[f"/api/workbenches/{bench}"]["workbench"]["event_starts"], "the event start is listed"

    # Read only: the folder is as it was.
    assert sorted(p.name for p in folder.iterdir()) == before


def _record_folder_step(base: str, bench: str, tmp_path: Path, registered: dict,
                        name: str = "folder-ran") -> dict[str, Any]:
    """The automation window's reads after the folder run, for its vitest
    (automation-hub/folder-ran.json; HOLDSPEAK_WIRE_WRITE=1 rewrites it, else
    this fences its shape)."""
    import os
    import re

    answers = {
        f"/api/workbenches/{bench}": _ok(base, "GET", f"/api/workbenches/{bench}"),
        f"/api/workbenches/{bench}/memory": _ok(base, "GET", f"/api/workbenches/{bench}/memory"),
        # The Add folder press's answer (the folder's path never comes back).
        "POST /api/repositories": registered,
    }
    text = re.sub(re.escape(str(tmp_path)), "/tmp/rig", json.dumps(answers))
    scrubbed = json.loads(re.sub(re.escape(base), "http://127.0.0.1:0", text))
    path = AUTOMATION_HUB / f"{name}.json"
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.write_text(json.dumps({
            "_source": "The hub's own answers, captured by tests/integration/test_desk_engines_tools.py "
                       "(a real hub, isolated database, the fake claude CLI listing the folder it works in). "
                       "HOLDSPEAK_WIRE_WRITE=1 rewrites this file; never hand-edit it.",
            "workbench_id": bench, "gets": scrubbed}, indent=1, ensure_ascii=False) + "\n")
    assert path.exists(), f"no stored answers {path}; run with HOLDSPEAK_WIRE_WRITE=1"
    stored = json.loads(path.read_text())["gets"]
    assert _shape(list(stored.values())) == _shape(list(scrubbed.values())), \
        f"{path.name}: the stored answers are not the hub's shape"
    return scrubbed
