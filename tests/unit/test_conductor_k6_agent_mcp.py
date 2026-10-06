"""Conductor K6: every agent HoldSpeak launches gets the HoldSpeak MCP.

Owner, 2026-10-06: "the agent we spin up here - do we inject him with our
HoldSpeak MCP? We certainly should."

1. The CONDUCTOR palette is derived from the one authority table
   (``mcp/tool_authority.py``): every ``work`` tool, no People tool. A new
   tool classifies itself.
2. Admission: a loopback request with a LAUNCH-BOUND agent credential passes
   POST /api/mcp with the Reach switch off, as AGENT with the CONDUCTOR
   palette. A hand-issued agent credential with Reach off: 404, as before.
   Non-loopback: as before. Revoked: refused. Calls are receipted with the
   agent principal.
3. The launch: the spawn issues the launch-bound credential; Claude Code gets
   ``--mcp-config`` (a 0600 file that names environment variables, never the
   token) and, in Normal and YOLO, ``--allowedTools mcp__holdspeak``; Codex
   gets ``-c mcp_servers.holdspeak.*``. Secure pre-approves nothing.
4. Revocation: session end (the rider's self-revoke), K4 cleanup, and a
   failed launch.

Real producers: the real hub app (``MeetingWebServer``) over its HTTP routes,
the real credential store, real kernel receipts, the real K2 launch engine.
Only tmux and the agent process are faked, at the process boundary.
"""
from __future__ import annotations

import json
import shlex
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from starlette.testclient import TestClient

from holdspeak import coder_factory, coder_gate
from holdspeak.db import Database
from holdspeak.delivery import agent_mcp
from holdspeak.mcp.palettes import CONDUCTOR, PALETTE_NAMES, resolve_palette
from holdspeak.mcp.tool_authority import TOOL_AUTHORITY, WORK
from holdspeak.principals import agent_credentials
from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402

from tests.unit.test_agent_hand import OWNER, _rig, _seed, _wait_for  # noqa: E402

REMOTE_HOST = "192.0.2.77"  # TEST-NET-1: never loopback


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    (tmp_path / "hub").mkdir()
    hub = _boot(tmp_path / "hub", monkeypatch)
    store = hub.server.app.state.agent_credentials
    assert store is agent_credentials, "the hub reads the process's one store"
    for credential in store.list_credentials():
        store.revoke(credential.principal.identity)
    yield hub
    for credential in store.list_credentials():
        store.revoke(credential.principal.identity)
    reset_database()
    composition.install(composition.bare(label="pytest"))


@pytest.fixture
def db(tmp_path):
    (tmp_path / "rig").mkdir(exist_ok=True)
    database = Database(tmp_path / "rig" / "launch.db")
    _seed(database)
    return database


def _client(hub: Hub, token: str | None, host: str = "127.0.0.1") -> TestClient:
    client = TestClient(hub.server.app, client=(host, 50000))
    client.headers.pop("x-holdspeak-token", None)  # tests/conftest.py adds the owner's
    if token is not None:
        client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def _reach(hub: Hub, enabled: bool) -> None:
    assert hub.client.put("/api/settings/remote", json={"enabled": enabled}).status_code == 200


def _rpc(client: TestClient, method: str, params: dict[str, Any] | None = None):
    return client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})


def _call(client: TestClient, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    response = _rpc(client, "tools/call", {"name": name, "arguments": arguments})
    assert response.status_code == 200, response.text
    return response.json()


def _launch_credential(launch_id: str = "launch_k6test0001", scope: tuple[str, ...] = (), project: str = ""):
    return agent_credentials.issue(
        coder_factory.launch_identity(launch_id),
        palette=resolve_palette(CONDUCTOR), palette_name=CONDUCTOR, launch_id=launch_id,
        **({"scope_items": scope} if scope else {}),
        **({"project_id": project} if project else {}),
    )


def _result(body: dict[str, Any]) -> tuple[bool, Any]:
    result = body["result"]
    return result["isError"], json.loads(result["content"][0]["text"])


def _refused_by_palette(body: dict[str, Any]) -> bool:
    return (body.get("error") or {}).get("code") == -32005


# ── 1. The palette, from the authority table ─────────────────────────


def test_conductor_palette_is_every_work_tool_except_people() -> None:
    from holdspeak.mcp.tools import TOOLS

    registered = {t["name"] for t in TOOLS}
    palette = resolve_palette(CONDUCTOR)
    from holdspeak.mcp.palettes import CONDUCTOR_OWNER_CONFIRM

    expected = {
        name for name in registered
        if TOOL_AUTHORITY.get(name) == WORK and not name.startswith("people.")
        and name not in CONDUCTOR_OWNER_CONFIRM
    }
    assert palette == expected
    assert not any(TOOL_AUTHORITY[name] != WORK for name in palette)
    assert not any(name.startswith("people.") for name in palette)
    # The brief's named effects are offered; egress, authority and config are not.
    assert {"desk.create", "door.add_item", "follow_through.complete", "project.list",
            "memory.search", "desk.snapshot", "decision_record.search"} <= palette
    assert {"agent.hand", "channel.send", "nudge.send", "settings.update",
            "project.archive", "channel.save_destination"}.isdisjoint(palette)
    # The owner's Confirm stays his: the agent proposes, never confirms.
    assert CONDUCTOR_OWNER_CONFIRM.isdisjoint(palette)
    # Only a launch issues it: the owner's Reach well does not offer it.
    assert CONDUCTOR not in PALETTE_NAMES


def test_a_new_tool_classifies_itself(monkeypatch) -> None:
    from holdspeak.mcp import tool_authority, tools

    for name, cls in (("k6.work_probe", WORK), ("k6.egress_probe", tool_authority.EGRESS)):
        monkeypatch.setitem(tool_authority.TOOL_AUTHORITY, name, cls)
        monkeypatch.setattr(tools, "TOOLS", [*tools.TOOLS, {"name": name, "inputSchema": {}}])
    palette = resolve_palette(CONDUCTOR)
    assert "k6.work_probe" in palette and "k6.egress_probe" not in palette


# ── 2. Admission over the real hub ───────────────────────────────────


def test_a_loopback_launch_credential_is_admitted_with_reach_off(hub: Hub) -> None:
    _reach(hub, False)
    credential = _launch_credential()
    agent = _client(hub, credential.token)

    listed = _rpc(agent, "tools/list")
    assert listed.status_code == 200, listed.text
    names = {t["name"] for t in listed.json()["result"]["tools"]}
    assert names == resolve_palette(CONDUCTOR)

    # File a note: a work effect, done, attributed to the agent.
    note = _call(agent, "desk.create", {"kind": "notes", "data": {"title": "From the agent", "body_markdown": "found it"}})
    assert note["result"]["isError"] is False, note
    made = json.loads(note["result"]["content"][0]["text"])
    assert made["title"] == "From the agent"
    # Ask the owner: a Door item.
    door = _call(agent, "door.add_item", {"task": "Agent asks: keep the old API?"})
    assert door["result"]["isError"] is False, door
    item = json.loads(door["result"]["content"][0]["text"])
    # Update an item's status.
    done = _call(agent, "follow_through.complete", {"card_id": item["id"], "verb": "done"})
    assert done["result"]["isError"] is False, done

    # Every call is observed with the agent principal, from loopback.
    events = json.loads(_call(agent, "pipeline.events", {"limit": 50})["result"]["content"][0]["text"])
    mine = [e for e in events if e.get("caller_identity") == "agent:launch:launch_k6test0001"]
    assert mine and all(e["origin"] == "local" for e in mine)
    assert any(e["principal_kind"] == "agent" for e in mine)


def test_a_hand_issued_agent_credential_still_needs_reach(hub: Hub) -> None:
    _reach(hub, False)
    issued = hub.client.post("/api/settings/remote/credentials", json={"identity": "reach-agent", "palette": "DESK"})
    assert issued.status_code in (200, 201), issued.text
    agent = _client(hub, issued.json()["token"])
    assert _rpc(agent, "tools/list").status_code == 404
    _reach(hub, True)
    assert _rpc(agent, "tools/list").status_code == 200


def test_a_launch_credential_from_elsewhere_needs_reach(hub: Hub) -> None:
    _reach(hub, False)
    credential = _launch_credential()
    remote = _client(hub, credential.token, host=REMOTE_HOST)
    assert _rpc(remote, "tools/list").status_code == 404
    _reach(hub, True)
    listed = _rpc(remote, "tools/list")
    assert listed.status_code == 200
    # Still the CONDUCTOR palette: egress refused.
    assert {t["name"] for t in listed.json()["result"]["tools"]} == resolve_palette(CONDUCTOR)
    assert _refused_by_palette(_call(remote, "channel.send", {"send_id": "x"}))


def test_a_revoked_launch_credential_is_refused(hub: Hub) -> None:
    _reach(hub, False)
    credential = _launch_credential()
    agent = _client(hub, credential.token)
    assert _rpc(agent, "tools/list").status_code == 200
    assert coder_factory.revoke_launch("launch_k6test0001") is True
    # The edge derives no principal from a revoked token: 401, Reach on or off.
    assert _rpc(agent, "tools/list").status_code == 401
    _reach(hub, True)
    assert _rpc(agent, "tools/list").status_code == 401


def test_the_owner_guards_are_unchanged(hub: Hub) -> None:
    _reach(hub, False)
    from test_philo5_the_loop import TOKEN

    assert _rpc(_client(hub, TOKEN), "tools/list").status_code == 200  # loopback owner
    assert _rpc(_client(hub, TOKEN, host=REMOTE_HOST), "tools/list").status_code == 404
    _reach(hub, True)
    assert _rpc(_client(hub, TOKEN, host=REMOTE_HOST), "tools/list").status_code == 403
    assert _rpc(_client(hub, None), "tools/list").status_code == 401


def test_egress_authority_config_and_people_are_refused(hub: Hub) -> None:
    _reach(hub, False)
    agent = _client(hub, _launch_credential().token)

    egress = _call(agent, "channel.send", {"send_id": "snd_1"})
    assert _refused_by_palette(egress), egress
    receipt = egress["error"]["data"]["receipt"]
    assert receipt["outcome"] == "mcp_palette_refused"
    # The refusal receipt names the agent, never the owner.
    row = hub.client.get(f"/api/kernel/operations/{egress['error']['data']['operation_id']}")
    if row.status_code == 200:
        assert "owner-session" not in row.text
    assert _refused_by_palette(_call(agent, "agent.hand", {"kind": "action", "id": "ai_1"}))
    assert _refused_by_palette(_call(agent, "settings.update", {}))
    assert _refused_by_palette(_call(agent, "project.archive", {"project_id": "p"}))
    assert _refused_by_palette(_call(agent, "people.relationship.list", {}))
    # A mixed tool is classed on its arguments: a schedule is authority.
    assert _refused_by_palette(_call(agent, "workbench.create", {"fields": {"name": "w", "schedule_enabled": True}}))
    assert not _refused_by_palette(_call(agent, "workbench.create", {"fields": {"name": "w"}}))
    # The People resources: hidden and refused.
    resources = _rpc(agent, "resources/list").json()["result"]
    uris = [r["uri"] for r in resources["resources"]] + [r["uriTemplate"] for r in resources["resourceTemplates"]]
    assert uris and not any(uri.startswith("holdspeak://people/") for uri in uris)
    read = _rpc(agent, "resources/read", {"uri": "holdspeak://people/relationships"}).json()
    assert read["error"]["code"] == -32005


def test_the_kernel_receipt_of_an_agent_call_names_the_agent(hub: Hub) -> None:
    _reach(hub, False)
    agent = _client(hub, _launch_credential().token)
    # A decision is an admitted kernel operation: the agent's attempt leaves a
    # receipt that names the agent (without the launch's grant it is refused).
    body = _call(agent, "desk.create", {"kind": "decisions", "data": {"title": "Use SQLite", "status": "proposed"}})
    payload = json.loads(body["result"]["content"][0]["text"])
    assert payload["receipt"]["actor_kind"] == "agent"
    assert payload["receipt"]["actor_identity"] == "agent:launch:launch_k6test0001"


# ── 3. The launch wires the MCP ──────────────────────────────────────


def _spawn(rig) -> tuple[list[str], str]:
    argv = next(c for c in rig.tmux.calls if c[1] == "new-session")
    return argv, argv[argv.index("-s") + 2]


def _env_token(argv: list[str]) -> str:
    entry = next(a for a in argv if a.startswith("HOLDSPEAK_AGENT_CREDENTIAL="))
    return entry.split("=", 1)[1]


def test_a_claude_launch_gets_the_mcp_and_its_credential(tmp_path, db, monkeypatch, hub, caplog) -> None:
    import logging

    caplog.set_level(logging.DEBUG)
    _reach(hub, False)
    rig = _rig(tmp_path / "rig", db, monkeypatch)
    rig.service._control_mode = lambda: "yolo"
    result = rig.hand.hand(OWNER, "action", "ai_1")
    assert result["status"] == "launched", result
    launch_id = result["launch_id"]
    argv, command = _spawn(rig)
    token = _env_token(argv)

    # The credential: launch-bound, CONDUCTOR, the launch's identity.
    credential = agent_credentials.derive_credential(token)
    assert credential is not None
    assert credential.launch_id == launch_id
    assert credential.palette_name == CONDUCTOR
    assert credential.principal.identity == f"agent:launch:{launch_id}"

    # The config file: 0600, the two variables, never the token.
    path = tmp_path / "rig" / "mcp" / f"{launch_id}.json"
    assert path.exists()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    content = path.read_text(encoding="utf-8")
    assert json.loads(content) == {
        "mcpServers": {"holdspeak": {
            "type": "http",
            "url": "${HOLDSPEAK_HUB_URL}/api/mcp",
            "headers": {"Authorization": "Bearer ${HOLDSPEAK_AGENT_CREDENTIAL}"},
        }}
    }
    assert token not in content

    # The agent's argv: the config and one allow list (gated Bash + the server).
    agent_argv = shlex.split(command.split(" exec ", 1)[1])
    assert agent_argv[0] == "claude"
    assert agent_argv[agent_argv.index("--mcp-config") + 1] == str(path)
    assert agent_argv[agent_argv.index("--allowedTools"):] == ["--allowedTools", "Bash", "mcp__holdspeak"]
    # The token is in the session environment only: not in the agent's
    # command, the launch record, the receipts or the log.
    assert token not in command
    assert token not in (tmp_path / "rig" / "launches.json").read_text(encoding="utf-8")
    for stored in (tmp_path / "rig").glob("*.db*"):  # the receipts, WAL included
        assert token.encode() not in stored.read_bytes(), stored
    assert token not in caplog.text
    record = rig.launches.get(launch_id)
    assert record["mcp"] == {
        "server": "holdspeak", "palette": "CONDUCTOR", "pre_approved": True,
        "decision_proposals": "granted",  # the hub is up and the owner pressed
        # The rig's Project is not a Project row in the hub: nothing to add to.
        "project_additions": "not_granted",
    }

    # End to end: the token the session holds reaches the hub's MCP with
    # Reach off, as the agent, with the CONDUCTOR palette.
    agent = _client(hub, token)
    listed = _rpc(agent, "tools/list")
    assert listed.status_code == 200
    assert {t["name"] for t in listed.json()["result"]["tools"]} == resolve_palette(CONDUCTOR)
    _wait_for(lambda: rig.launches.get(launch_id), "instruction_state", "sent")
    rig.tmux.ended = True


def test_the_brief_names_the_mcp_tools(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path / "rig", db, monkeypatch)
    result = rig.hand.hand(OWNER, "action", "ai_1")
    _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    typed = "\n".join(text for _pane, text in rig.typed)
    assert (
        "- The holdspeak MCP tools are yours for this launch. Use them to read the desk "
        "and memory (People data is cut), file notes, propose decisions (the owner "
        "confirms them), update the status of this item or of items you add, and ask "
        "the owner with a Door item. You cannot send anything out or change settings."
    ) in typed
    rig.tmux.ended = True


def test_secure_does_not_pre_approve(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path / "rig", db, monkeypatch)
    rig.service._control_mode = lambda: "Secure"  # the label maps to the wire value
    result = rig.hand.hand(OWNER, "action", "ai_1")
    assert result["status"] == "launched", result
    _argv, command = _spawn(rig)
    agent_argv = shlex.split(command.split(" exec ", 1)[1])
    assert "--mcp-config" in agent_argv
    assert agent_argv[agent_argv.index("--allowedTools"):] == ["--allowedTools", "Bash"]
    assert "mcp__holdspeak" not in command
    assert rig.launches.get(result["launch_id"])["mcp"]["pre_approved"] is False
    _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    rig.tmux.ended = True


def _codex_launch(tmp_path, db, monkeypatch, mode: str):
    rig = _rig(tmp_path / "rig", db, monkeypatch, agent="codex")
    rig.service._control_mode = lambda: mode
    result = rig.hand.hand(OWNER, "action", "ai_1", profile="codex-default")
    assert result["status"] == "launched", result
    argv, command = _spawn(rig)
    rig.tmux.ended = True
    return rig, result, argv, command


def test_a_codex_launch_gets_the_mcp_flags(tmp_path, db, monkeypatch) -> None:
    rig, result, argv, command = _codex_launch(tmp_path, db, monkeypatch, "neutral")
    token = _env_token(argv)
    credential = agent_credentials.derive_credential(token)
    assert credential is not None and credential.launch_id == result["launch_id"]
    agent_argv = shlex.split(command.split(" exec ", 1)[1])
    hub_url = agent_credentials.hub_url
    assert agent_argv == [
        "codex",
        "-c", f'mcp_servers.holdspeak.url="{hub_url}/api/mcp"',
        "-c", 'mcp_servers.holdspeak.bearer_token_env_var="HOLDSPEAK_AGENT_CREDENTIAL"',
        "-c", 'mcp_servers.holdspeak.default_tools_approval_mode="approve"',
    ]
    assert token not in command
    # No --mcp-config file for Codex.
    assert not (tmp_path / "rig" / "mcp" / f"{result['launch_id']}.json").exists()


def test_a_secure_codex_launch_does_not_pre_approve(tmp_path, db, monkeypatch) -> None:
    _rig_, _result, _argv, command = _codex_launch(tmp_path, db, monkeypatch, "safe")
    assert "mcp_servers.holdspeak.url" in command
    assert "default_tools_approval_mode" not in command


@pytest.mark.skipif(shutil.which("codex") is None, reason="codex is not installed")
def test_the_real_codex_reads_the_flags(tmp_path) -> None:
    """The flags parse in the installed Codex: a streamable HTTP server with
    its bearer variable (``codex mcp get --json``, isolated HOME)."""
    flags = agent_mcp.codex_args("http://127.0.0.1:8765", "yolo")
    home = tmp_path / "codex-home"
    home.mkdir()
    completed = subprocess.run(
        ["codex", *flags, "mcp", "get", "holdspeak", "--json"],
        capture_output=True, text=True, timeout=60,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin:" + str(Path(shutil.which("codex")).parent)},
    )
    assert completed.returncode == 0, completed.stderr
    server = json.loads(completed.stdout[completed.stdout.index("{"):])
    assert server["transport"] == {
        "type": "streamable_http",
        "url": "http://127.0.0.1:8765/api/mcp",
        "bearer_token_env_var": "HOLDSPEAK_AGENT_CREDENTIAL",
        "http_headers": None, "env_http_headers": None, "http_headers_helper": None,
    }


# ── 4. Revocation ────────────────────────────────────────────────────


def test_session_end_self_revokes_the_launch_credential(hub: Hub, monkeypatch) -> None:
    """The rider's SessionEnd hook (``coder_gate.run_session_end``) sends
    DELETE /api/principals/self with the session's credential."""
    _reach(hub, False)
    credential = _launch_credential()
    agent = _client(hub, credential.token)
    assert _rpc(agent, "tools/list").status_code == 200

    from urllib.parse import urlsplit

    def send(request, _timeout):  # urllib's request, answered by the real hub
        response = agent.request(
            request.get_method(), urlsplit(request.full_url).path,
            headers=dict(request.header_items()),
        )
        return response.status_code, response.json()

    monkeypatch.setattr(coder_gate, "_send", send)
    monkeypatch.setenv("HOLDSPEAK_AGENT_CREDENTIAL", credential.token)
    assert coder_gate.run_session_end({"session_id": "s1"}, hub_url="http://127.0.0.1:8765") is True
    assert agent_credentials.derive(credential.token) is None
    assert _rpc(agent, "tools/list").status_code == 401


def test_k4_cleanup_revokes_and_removes_the_config(tmp_path, db, monkeypatch) -> None:
    from tests.unit.test_conductor_k4_follow_through import _launch, _pr, _sweep

    rig = _launch(tmp_path, db, monkeypatch)
    launch_id = rig.result["launch_id"]
    token = _env_token(_spawn(rig)[0])
    path = tmp_path / "mcp" / f"{launch_id}.json"
    assert path.exists() and agent_credentials.derive(token) is not None
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    _sweep(rig)
    assert agent_credentials.derive(token) is None
    assert not path.exists()
    assert rig.launches.get(launch_id)["follow_through"]["cleanup"]["mcp"] == "released"


def test_k4_cleanup_revokes_when_the_session_ended_on_its_own(tmp_path, db, monkeypatch) -> None:
    from tests.unit.test_conductor_k4_follow_through import _launch, _pr, _sweep

    rig = _launch(tmp_path, db, monkeypatch)
    launch_id = rig.result["launch_id"]
    token = _env_token(_spawn(rig)[0])
    rig.tmux.sessions.clear()
    rig.tmux.meta.clear()
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    _sweep(rig)
    cleanup = rig.launches.get(launch_id)["follow_through"]["cleanup"]
    assert cleanup["session"] == "session_gone"
    assert cleanup["mcp"] == "released"
    assert agent_credentials.derive(token) is None


def test_a_spawn_failure_leaves_no_credential_and_no_config(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path / "rig", db, monkeypatch)
    rig.tmux.fail_new_session = True
    before = {c.principal.identity for c in agent_credentials.list_credentials()}
    result = rig.hand.hand(OWNER, "action", "ai_1")
    assert result["status"] == "failed" and result["failure"]["stage"] == "spawn"
    after = {c.principal.identity for c in agent_credentials.list_credentials()}
    assert f"agent:launch:{result['launch_id']}" not in after and after <= before
    assert not (tmp_path / "rig" / "mcp" / f"{result['launch_id']}.json").exists()


def test_a_target_failure_revokes_the_spawned_credential(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path / "rig", db, monkeypatch)
    monkeypatch.setattr(rig.service._targets, "issue", lambda _ref: {"status": "pane_gone"})
    result = rig.hand.hand(OWNER, "action", "ai_1")
    assert result["status"] == "failed" and result["failure"]["stage"] == "target"
    token = _env_token(_spawn(rig)[0])
    assert agent_credentials.derive(token) is None
    assert not (tmp_path / "rig" / "mcp" / f"{result['launch_id']}.json").exists()
    # The session itself is retained and named, as before (a kill is gated).
    assert rig.launches.get(result["launch_id"])["rollback"]["session"] == "retained"
    rig.tmux.ended = True


# ── 5. Rulings on #903: memory, decision proposals, item scope, /clear ─


def _owner_note(hub: Hub, title: str, body: str) -> str:
    is_error, note = hub.mcp("desk.create", {"kind": "notes", "data": {"title": title, "body_markdown": body}})
    assert is_error is False, note
    return note["id"]


def test_a_launch_reads_memory_with_the_people_cut(hub: Hub) -> None:
    _reach(hub, False)
    plain = _owner_note(hub, "Rollout plan", "We use blue-green for the zebra rollout.")
    people = _owner_note(hub, "Zebra 1:1 prep", "zebra notes\npeople:rel_42 wants more ownership")
    # The owner reads both.
    _err, mine = hub.mcp("memory.search", {"query": "zebra"})
    assert {h["source_ref"] for h in mine["hits"]} == {f"note:{plain}", f"note:{people}"}

    credential = _launch_credential()
    agent = _client(hub, credential.token)
    is_error, found = _result(_call(agent, "memory.search", {"query": "zebra"}))
    assert is_error is False, found
    assert [h["source_ref"] for h in found["hits"]] == [f"note:{plain}"]
    assert found["people_cut"] == 1 and found["page"]["total"] == 1
    for name, args in (("memory.observations", {}), ("memory.page", {"slug": "what-i-owe", "scope": "desk"})):
        is_error, read = _result(_call(agent, name, args))
        assert is_error is False, (name, read)

    # Revoked with the credential: a hand-issued agent has no read right.
    coder_factory.revoke_launch("launch_k6test0001")
    _reach(hub, True)
    issued = hub.client.post("/api/settings/remote/credentials", json={"identity": "reach-reader", "palette": "ALL"})
    is_error, refused = _result(_call(_client(hub, issued.json()["token"]), "memory.search", {"query": "zebra"}))
    assert is_error is True and refused["code"] == "read_forbidden"


def _grant(launch_id: str = "launch_k6test0001") -> dict[str, Any]:
    from holdspeak.services.conductor_launch import grant_decision_proposals
    from tests.unit.test_agent_hand import OWNER as OWNER_PRESS

    granted = grant_decision_proposals(OWNER_PRESS, coder_factory.launch_identity(launch_id), ttl_seconds=3600)
    assert granted is not None
    return granted


def test_a_launch_proposes_decisions_and_nothing_else(hub: Hub) -> None:
    _reach(hub, False)
    credential = _launch_credential()
    agent = _client(hub, credential.token)
    identity = coder_factory.launch_identity("launch_k6test0001")
    # Before the grant: refused, as every agent is today.
    is_error, refused = _result(_call(agent, "desk.create", {"kind": "decisions", "data": {"title": "Use SQLite"}}))
    assert is_error and refused["code"] == "desk_delegation_required"
    _grant()

    is_error, made = _result(_call(agent, "desk.create", {"kind": "decisions", "data": {"title": "Use SQLite", "decision_markdown": "SQLite"}}))
    assert is_error is False, made
    decision_id = made["id"]
    assert made["status"] == "proposed"
    # Receipted with the agent principal (its identity carries the launch id)
    # under the launch's grant.
    with hub.db._connection() as conn:
        row = conn.execute(
            "SELECT o.principal_identity, o.authority_basis FROM kernel_operations o "
            "WHERE o.name='decision.create' ORDER BY o.rowid DESC LIMIT 1"
        ).fetchone()
        grant = conn.execute(
            "SELECT id, operations_json, state FROM kernel_desk_delegations WHERE agent_identity=?", (identity,)
        ).fetchone()
    assert row["principal_identity"] == identity
    assert row["authority_basis"].startswith(f"desk-delegation:{grant['id']}:")
    assert json.loads(grant["operations_json"]) == ["decision.create"] and grant["state"] == "LIVE"

    # Never a confirmed decision, never a record, never another desk write.
    assert _refused_by_palette(_call(agent, "desk.create", {"kind": "decisions", "data": {"title": "X", "status": "accepted"}}))
    assert _refused_by_palette(_call(agent, "desk.verb", {"verb_id": "desk.create", "arguments": {"kind": "decisions", "data": {"title": "X", "status": "accepted"}}}))
    assert _refused_by_palette(_call(agent, "decision_record.create_from_desk", {"decision_id": decision_id}))
    assert _refused_by_palette(_call(agent, "proposal.confirm", {"proposal_id": "p"}))
    is_error, refused = _result(_call(agent, "desk.update", {"kind": "decisions", "id": decision_id, "data": {"status": "accepted"}}))
    assert is_error and refused.get("code") == "desk_delegation_required", refused
    is_error, refused = _result(_call(agent, "desk.delete", {"kind": "decisions", "id": decision_id}))
    assert is_error and refused.get("code") == "desk_delegation_required", refused
    # Filing even its own proposal is a desk write the grant does not hold.
    is_error, refused = _result(_call(agent, "zone.file", {"directory_id": "hs-seed-inbox", "primitive_id": f"decision:{decision_id}"}))
    assert is_error and refused.get("code") == "desk_delegation_required", refused

    # The grant goes with the credential.
    coder_factory.revoke_launch("launch_k6test0001")
    with hub.db._connection() as conn:
        state = conn.execute("SELECT state, revocation_reason FROM kernel_desk_delegations WHERE id=?", (grant["id"],)).fetchone()
    assert (state["state"], state["revocation_reason"]) == ("REVOKED", "credential_revoked")


def test_item_state_tools_act_only_on_this_launchs_items(hub: Hub) -> None:
    _reach(hub, False)
    _err, origin = hub.mcp("door.add_item", {"task": "The origin item"})
    _err, other = hub.mcp("door.add_item", {"task": "Somebody else's item"})
    agent = _client(hub, _launch_credential(scope=(origin["id"],)).token)

    is_error, refused = _result(_call(agent, "follow_through.complete", {"card_id": other["id"], "verb": "done"}))
    assert is_error and refused["code"] == "not_this_launch" and refused["item_id"] == other["id"]
    is_error, refused = _result(_call(agent, "project.item.transition", {"project_id": "p", "item_id": "it_x", "verb": "done"}))
    assert is_error and refused["code"] == "not_this_launch"

    is_error, done = _result(_call(agent, "follow_through.complete", {"card_id": origin["id"], "verb": "done"}))
    assert is_error is False, done
    # An item the agent adds joins its scope.
    _is_error, mine = _result(_call(agent, "door.add_item", {"task": "Agent asks: which DB?"}))
    is_error, done = _result(_call(agent, "follow_through.complete", {"card_id": mine["id"], "verb": "done"}))
    assert is_error is False, done
    with hub.db._connection() as conn:
        status = {r["id"]: r["status"] for r in conn.execute("SELECT id, status FROM action_items")}
    assert status[origin["id"]] == "done" and status[mine["id"]] == "done" and status[other["id"]] == "open"


def test_the_launch_scopes_the_origin_and_grants_proposals(tmp_path, db, monkeypatch, hub) -> None:
    _reach(hub, False)
    rig = _rig(tmp_path / "rig", db, monkeypatch)
    result = rig.hand.hand(OWNER, "action", "ai_1")
    assert result["status"] == "launched", result
    launch_id = result["launch_id"]
    assert agent_credentials.in_scope(launch_id, "ai_1")
    assert rig.launches.get(launch_id)["mcp"]["decision_proposals"] == "granted"
    agent = _client(hub, _env_token(_spawn(rig)[0]))
    is_error, made = _result(_call(agent, "desk.create", {"kind": "decisions", "data": {"title": "Proposed by the agent"}}))
    assert is_error is False and made["status"] == "proposed", made
    _wait_for(lambda: rig.launches.get(launch_id), "instruction_state", "sent")
    rig.tmux.ended = True


@pytest.mark.parametrize("reason,revoked", [
    ("clear", False), ("resume", False),
    ("logout", True), ("prompt_input_exit", True), ("other", True),
])
def test_session_end_revokes_only_when_the_process_ends(hub: Hub, monkeypatch, reason, revoked) -> None:
    from urllib.parse import urlsplit

    _reach(hub, False)
    credential = _launch_credential()
    agent = _client(hub, credential.token)

    def send(request, _timeout):
        response = agent.request(request.get_method(), urlsplit(request.full_url).path,
                                 headers=dict(request.header_items()))
        return response.status_code, response.json()

    monkeypatch.setattr(coder_gate, "_send", send)
    monkeypatch.setenv("HOLDSPEAK_AGENT_CREDENTIAL", credential.token)
    coder_gate.run_session_end({"session_id": "s1", "reason": reason}, hub_url="http://127.0.0.1:8765")
    assert (agent_credentials.derive(credential.token) is None) is revoked
    assert _rpc(agent, "tools/list").status_code == (401 if revoked else 200)


def test_a_session_that_ended_is_released_at_the_next_sweep(tmp_path, db, monkeypatch) -> None:
    """No hook ran (a crash, a kill): the Heartbeat sweep finds the tmux
    session gone and revokes, before any PR exists."""
    from tests.unit.test_conductor_k4_follow_through import _launch, _sweep

    rig = _launch(tmp_path, db, monkeypatch)
    launch_id = rig.result["launch_id"]
    token = _env_token(_spawn(rig)[0])
    _sweep(rig)
    assert agent_credentials.derive(token) is not None, "a live session keeps its credential"
    rig.tmux.ended = True  # tmux has-session now fails
    _sweep(rig)
    assert agent_credentials.derive(token) is None
    assert not (tmp_path / "mcp" / f"{launch_id}.json").exists()


def test_the_agent_edits_only_what_it_created(hub: Hub) -> None:
    """Round 3 ruling: the owner's desk records are not the agent's to edit
    or delete. The owner's note is made by the hub's own PrimitiveService."""
    from tests.unit.test_agent_hand import OWNER as OWNER_PRESS

    _reach(hub, False)
    owner_note = hub.root.primitive_service.create_note(OWNER_PRESS, title="Owner plan", body_markdown="keep")
    owner_id = owner_note["id"]
    agent = _client(hub, _launch_credential().token)

    def refused(name: str, args: dict[str, Any]) -> None:
        is_error, body = _result(_call(agent, name, args))
        assert is_error and body["code"] == "not_this_launch", (name, body)

    refused("desk.update", {"kind": "notes", "id": owner_id, "data": {"title": "Hijacked"}})
    refused("desk.delete", {"kind": "notes", "id": owner_id})
    refused("desk.verb", {"verb_id": "desk.update", "arguments": {"kind": "notes", "id": owner_id, "data": {"title": "x"}}})
    refused("desk.verb", {"verb_id": "desk.delete", "arguments": {"kind": "notes", "id": owner_id}})
    refused("zone.unfile", {"directory_id": "hs-seed-inbox", "primitive_id": f"note:{owner_id}"})
    refused("kb.remove_member", {"kb_id": "kb_x", "ref": f"note:{owner_id}"})
    refused("thought.adopt_note", {"request_id": "r", "note_id": owner_id,
                                   "expected_source_content_sha256": "x", "expected_source_last_modified": "x"})
    refused("meeting.delete", {"meeting_id": "m_owner"})
    refused("workbench.delete", {"workbench_id": "wb_owner"})
    _err, kept = hub.mcp("desk.get", {"kind": "notes", "id": owner_id})
    assert kept["title"] == "Owner plan" and not kept.get("deleted"), kept

    # The agent's own note: created, edited, deleted.
    is_error, mine = _result(_call(agent, "desk.create", {"kind": "notes", "data": {"title": "Agent note"}}))
    assert is_error is False, mine
    is_error, edited = _result(_call(agent, "desk.update", {"kind": "notes", "id": mine["id"], "data": {"title": "Agent note v2"}}))
    assert is_error is False and edited["title"] == "Agent note v2", edited
    is_error, gone = _result(_call(agent, "desk.delete", {"kind": "notes", "id": mine["id"]}))
    assert is_error is False, gone
    # Another launch does not own it.
    other = _client(hub, _launch_credential("launch_k6other0002").token)
    is_error, body = _result(_call(other, "desk.update", {"kind": "notes", "id": owner_id, "data": {"title": "x"}}))
    assert is_error and body["code"] == "not_this_launch"


def test_the_agent_adds_to_its_own_project_and_writes_no_other(hub: Hub) -> None:
    """Round 4 ruling: add links and resources to the launch's own Project;
    never edit, unlink, restore or archive; never write another Project."""
    from datetime import datetime as _dt

    from holdspeak.meeting_session import MeetingState, TranscriptSegment
    from holdspeak.services.conductor_launch import grant_project_additions
    from tests.unit.test_agent_hand import OWNER as OWNER_PRESS

    _reach(hub, False)
    own = hub.client.post("/api/projects", json={"name": "Launch project"}).json()["project"]
    other = hub.client.post("/api/projects", json={"name": "Second project"}).json()["project"]
    hub.db.meetings.save_meeting(MeetingState(
        id="m-k6", started_at=_dt(2026, 10, 6, 9, 0), ended_at=_dt(2026, 10, 6, 9, 30), title="Cutover", tags=[],
        segments=[TranscriptSegment(text="Plan the cutover.", speaker="Me", start_time=0.0, end_time=2.0)]))
    owner_note = hub.root.primitive_service.create_note(OWNER_PRESS, title="Spec", body_markdown="s")["id"]
    _err, owner_res = hub.mcp("project.resource.add", {"project_id": own["id"], "resource_ref": f"note:{owner_note}"})
    assert _err is False, owner_res

    identity = coder_factory.launch_identity("launch_k6test0001")
    agent = _client(hub, _launch_credential(project=own["id"]).token)
    # Without the launch's grant the kernel refuses the link, with a receipt.
    is_error, body = _result(_call(agent, "project.link", {"project_id": own["id"], "meeting_id": "m-k6"}))
    assert is_error and body["code"] == "project_delegation_required", body
    # Another agent (not a launch) is still refused as owner-only.
    _reach(hub, True)
    reach = hub.client.post("/api/settings/remote/credentials", json={"identity": "reach-agent-2", "palette": "ALL"})
    is_error, body = _result(_call(_client(hub, reach.json()["token"]), "project.link",
                                    {"project_id": own["id"], "meeting_id": "m-k6"}))
    assert is_error and body["code"] == "owner_principal_required", body
    _reach(hub, False)
    assert grant_project_additions(OWNER_PRESS, identity, own["id"], ttl_seconds=3600) is not None

    def refused(name: str, args: dict[str, Any]) -> None:
        is_error, body = _result(_call(agent, name, args))
        assert is_error and body["code"] == "not_this_launch", (name, body)

    # Never, on any Project.
    for pid in (own["id"], other["id"]):
        refused("project.update", {"project_id": pid, "patch": {"name": "Hijacked"}})
        refused("project.unlink", {"project_id": pid, "meeting_id": "m-k6"})
        refused("project.restore", {"project_id": pid})
    # Never another Project, and nothing that names none.
    refused("project.link", {"project_id": other["id"], "meeting_id": "m-k6"})
    refused("project.resource.add", {"project_id": other["id"], "resource_ref": f"note:{owner_note}"})
    refused("project.create", {"name": "Agent project"})
    # The owner's resource stays his.
    refused("project.resource.remove", {"project_id": own["id"], "resource_ref": f"note:{owner_note}"})

    # Adding to its own Project: a link and a resource, receipted as the agent.
    is_error, linked = _result(_call(agent, "project.link", {"project_id": own["id"], "meeting_id": "m-k6"}))
    assert is_error is False, linked
    is_error, mine = _result(_call(agent, "desk.create", {"kind": "notes", "data": {"title": "Agent findings"}}))
    is_error, added = _result(_call(agent, "project.resource.add", {"project_id": own["id"], "resource_ref": f"note:{mine['id']}"}))
    assert is_error is False, added
    with hub.db._connection() as conn:
        actors = {(r["name"], r["principal_identity"]) for r in conn.execute(
            "SELECT name, principal_identity FROM kernel_operations WHERE name IN ('project.link','project.resource.add') "
            "AND state='succeeded'")}
    assert ("project.link", identity) in actors and ("project.resource.add", identity) in actors
    # ... and removing the resource it added.
    is_error, removed = _result(_call(agent, "project.resource.remove", {"project_id": own["id"], "resource_ref": f"note:{mine['id']}"}))
    assert is_error is False, removed

    # The owner's Projects: names unchanged, the second one untouched.
    _err, read_own = hub.mcp("project.get", {"project_id": own["id"]})
    _err, read_other = hub.mcp("project.get", {"project_id": other["id"]})
    assert json.dumps(read_own).count("Launch project") and "Hijacked" not in json.dumps(read_own)
    _err, other_res = hub.mcp("project.resource.list", {"project_id": other["id"]})
    assert f"note:{owner_note}" not in json.dumps(other_res) and "m-k6" not in json.dumps(read_other)
    _err, own_res = hub.mcp("project.resource.list", {"project_id": own["id"]})
    assert f"note:{owner_note}" in json.dumps(own_res)

    # The grant goes with the credential.
    coder_factory.revoke_launch("launch_k6test0001")
    from holdspeak.services import project_delegation

    assert project_delegation.live_projects(identity, database=hub.db) == []
