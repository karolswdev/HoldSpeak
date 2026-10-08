"""PR #1022, Astra round 1: the four MUSTs, each through its real producer.

1. Secure: a pi MCP tool that is not a read holds like a Bash call (the real
   launch command, the real gate hook, the real hub routes, the real MCP
   endpoint); a read passes; YOLO leaves it to the palette.
2. pi's read tools: a path inside the worktree passes; a path outside (also
   through a symlink) goes to the gate as ``Read`` and is held OUTSIDE THE
   WORKTREE; the real pi ``read`` tool returns nothing then.
3. Stop ends the launch's recorded process group after its first process
   exited (a real tmux server on a private socket), and only that group.
4. An approved pi Write reaches its terminal kernel receipt.
"""
from __future__ import annotations

import io
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pytest

from holdspeak import coder_factory, coder_gate
from holdspeak.agent_context.hooks import PI_HOOKS_FILE
from holdspeak.delivery import pi_launch
from tests.unit._spawn_env import command_of, token_of
from tests.unit.test_agent_hand import OWNER, _rig, _wait_for
from tests.unit.test_conductor_k5_supervision import _mode
from tests.unit.test_conductor_k6_agent_mcp import _call, _client, _result, hub  # noqa: F401  (hub is a fixture)
from tests.unit.test_pi_harness import ENGINE, db, pi_rig  # noqa: F401  (fixtures)


_LAST: list = []


def _send_to(client):
    """coder_gate._send through the hub's real routes (body and headers)."""

    def send(request, _timeout):
        response = client.request(
            request.get_method(), urlsplit(request.full_url).path,
            headers=dict(request.header_items()), content=request.data,
        )
        try:
            body = response.json()
        except ValueError:
            body = {}
        _LAST.append((response.status_code, body))
        return response.status_code, body if isinstance(body, dict) else {}

    return send


# ── 1. Secure MCP writes hold ────────────────────────────────────────


def _secure_launch(tmp_path, monkeypatch, hub, mode: str):  # noqa: F811
    _mode(tmp_path, monkeypatch, mode)
    made = hub.client.post("/api/projects", json={"name": "Railsproj"})
    assert made.status_code in (200, 201), made.text
    project = made.json()["project"]["id"]
    made = hub.client.post(f"/api/projects/{project}/items", json={"item_type": "workstream", "title": "Before"})
    assert made.status_code in (200, 201), made.text
    item = made.json()["item"]["id"]
    rig = _rig(tmp_path / "rig", hub.db, monkeypatch, agent="pi", project=project, item=("project_item", item))
    rig.service._pi_engine = lambda: ENGINE
    rig.service._control_mode = lambda: mode
    rig.hand._control_mode = lambda: mode
    # The hub's gate reads launches from the hub's launch driver; this rig's
    # driver keeps its ledger in the test folder.
    from holdspeak.services.gate_service import GateService

    monkeypatch.setattr(GateService, "_launch_records", lambda self: (rig.service, rig.service._ledger.list()))
    launched = rig.hand.hand(OWNER, "project_item", item, profile="pi-default")
    assert launched["status"] == "launched", launched
    record = rig.launches.get(launched["launch_id"])
    spawn = next(c for c in rig.tmux.calls if c[1] == "new-session")
    return rig, record, spawn, project, item


def _launch_env(monkeypatch, record, spawn) -> str:
    """The environment the launch command gives pi and its hooks."""
    command = command_of(spawn)
    for word in shlex.split(command):
        if "=" in word and word.split("=", 1)[0] in (coder_gate.MCP_HOLD_ENV, "HOLDSPEAK_PARENT_OPERATION_ID"):
            name, value = word.split("=", 1)
            monkeypatch.setenv(name, value)
    token = token_of(spawn)
    monkeypatch.setenv("HOLDSPEAK_AGENT_CREDENTIAL", token)
    return token


@pytest.mark.parametrize("decision", ["denied", "approved"])
def test_secure_pi_mcp_write_holds_until_the_owner_decides(tmp_path, monkeypatch, hub, decision) -> None:  # noqa: F811
    rig, record, spawn, project, item = _secure_launch(tmp_path, monkeypatch, hub, "safe")
    try:
        assert record["mcp"]["pre_approved"] is False
        assert f"{coder_gate.MCP_HOLD_ENV}=1" in command_of(spawn)
        token = _launch_env(monkeypatch, record, spawn)
        agent = _client(hub, token)
        monkeypatch.setattr(coder_gate, "_send", _send_to(agent))
        args = {"project_id": project, "item_id": item, "patch": {"title": "After"}}
        seen: dict[str, Any] = {}

        def owner_decides(_seconds: float) -> None:
            if "decided" in seen:
                return
            held = rig.db.gate.get("call_write")
            seen["held"] = held.state if held else None
            # Held: the agent's MCP call has not run; nothing changed.
            seen["title_while_held"] = hub.db.projects.get_project_item(item)["title"]
            answer = hub.client.post("/api/gate/proposals/call_write/decide",
                                     json={"decision": decision, "reason": "owner"})
            assert answer.status_code == 200, answer.text
            seen["decided"] = True

        payload = {"hook_event_name": "PreToolUse", "tool_name": "mcp__holdspeak__project_item_update",
                   "tool_input": args, "tool_use_id": "call_write", "session_id": "smoke-session",
                   "cwd": str(rig.worktree)}
        verdict = coder_gate.run_hook(payload, config=coder_gate.load_gate_config(rig.gate_path),
                                      hub_url="http://hub.test", sleep=owner_decides, agent="pi")
        assert seen.get("held") == "held", {"verdict": verdict.deny, "seen": seen, "last": _LAST[-2:]}
        assert seen["title_while_held"] == "Before"
        if decision == "denied":
            assert verdict.deny and "The owner denied this call" in verdict.deny
            assert hub.db.projects.get_project_item(item)["title"] == "Before"
        else:
            assert verdict.deny is None
            # The extension lets the call run: the real MCP endpoint, scoped.
            is_error, _body = _result(_call(agent, "project.item.update", args))
            assert is_error is False
            assert hub.db.projects.get_project_item(item)["title"] == "After"

        # A read passes with no proposal in Secure.
        read = coder_gate.run_hook({**payload, "tool_name": "mcp__holdspeak__project_list", "tool_input": {},
                                    "tool_use_id": "call_read"},
                                   config=coder_gate.load_gate_config(rig.gate_path), hub_url="http://hub.test",
                                   agent="pi")
        assert read.deny is None and rig.db.gate.get("call_read") is None
    finally:
        rig.tmux.ended = True


def test_yolo_leaves_pi_mcp_tools_to_the_palette(tmp_path, monkeypatch, hub) -> None:  # noqa: F811
    rig, record, spawn, project, item = _secure_launch(tmp_path, monkeypatch, hub, "yolo")
    try:
        assert record["mcp"]["pre_approved"] is True
        assert coder_gate.MCP_HOLD_ENV not in command_of(spawn)
        monkeypatch.delenv(coder_gate.MCP_HOLD_ENV, raising=False)
        _launch_env(monkeypatch, record, spawn)
        payload = {"hook_event_name": "PreToolUse", "tool_name": "mcp__holdspeak__project_item_update",
                   "tool_input": {"project_id": project}, "tool_use_id": "call_y", "session_id": "s",
                   "cwd": str(rig.worktree)}
        verdict = coder_gate.run_hook(payload, config=coder_gate.load_gate_config(rig.gate_path),
                                      http_post=lambda *a: pytest.fail("no proposal in YOLO"),
                                      http_get=lambda *a: pytest.fail("no read in YOLO"), agent="pi")
        assert verdict.deny is None
    finally:
        rig.tmux.ended = True


def test_mcp_reads_and_writes_are_known() -> None:
    assert coder_gate.mcp_tool_is_read("mcp__holdspeak__project_list")
    assert coder_gate.mcp_tool_is_read("mcp__holdspeak__meeting_get")
    assert not coder_gate.mcp_tool_is_read("mcp__holdspeak__project_item_update")
    assert not coder_gate.mcp_tool_is_read("mcp__holdspeak__note_create")
    assert not coder_gate.mcp_tool_is_read("mcp__other__thing_get")  # another server: never a read


# ── 2. pi's read tools ───────────────────────────────────────────────

_DRIVER = r"""
const ext = (await import(process.argv[2])).default;
const handlers = {};
ext({ on: (name, fn) => { handlers[name] = fn; } });
const ctx = { cwd: process.argv[3], sessionManager: { getSessionId: () => "s1", getSessionFile: () => null } };
const event = JSON.parse(process.argv[4]);
const decision = await handlers.tool_call(event, ctx);
let text = null;
if (!decision?.block && process.argv[5]) {
  const { createReadToolDefinition } = await import(process.argv[5]);
  const result = await createReadToolDefinition(ctx.cwd).execute("p", event.input, new AbortController().signal, undefined, ctx);
  text = result.content.filter((c) => c.type === "text").map((c) => c.text).join("\n");
}
console.log(JSON.stringify({ decision: decision ?? null, text }));
"""

_GATE = r"""
import json, sys
payload = json.load(sys.stdin)
with open(sys.argv[1], "a") as log:
    log.write(json.dumps(payload) + "\n")
sys.path.insert(0, sys.argv[2])
from holdspeak.coder_gate import _classify, HookDecision
verdict = _classify(payload["tool_name"], payload, cwd=payload["cwd"], root=sys.argv[3])
if verdict["scope"] != "inside":
    print(json.dumps(HookDecision(deny="held: " + verdict["scope"] + " " + verdict["rule"]).to_hook_output()))
"""


def _pi_read_module() -> str | None:
    root = os.environ.get("HOLDSPEAK_TEST_PI_PACKAGE") or ""
    module = Path(root) / "dist" / "core" / "tools" / "read.js"
    return str(module) if root and module.is_file() else None


def _read(tmp_path: Path, worktree: Path, path: str) -> tuple[dict, list]:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    folder = tmp_path / "pi"
    folder.mkdir(exist_ok=True)
    log = tmp_path / "gate.log"
    gate = tmp_path / "gate.py"
    gate.write_text(_GATE)
    doc = coder_gate.pi_spawn_hooks("holdspeak")
    doc["gate"]["argv"] = [sys.executable, str(gate), str(log), str(Path(coder_gate.__file__).parents[1]),
                           str(worktree)]
    doc["rider"]["argv"] = [sys.executable, "-c", "pass"]
    (folder / PI_HOOKS_FILE).write_text(json.dumps(doc))
    driver = tmp_path / "driver.mjs"
    driver.write_text(_DRIVER)
    argv = [node, "--no-warnings", str(driver), str(pi_launch.EXTENSION_PATH), str(worktree),
            json.dumps({"toolName": "read", "toolCallId": "r1", "input": {"path": path}})]
    module = _pi_read_module()
    if module:
        argv.append(module)
    done = subprocess.run(argv, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "PI_CODING_AGENT_DIR": str(folder)})
    assert done.returncode == 0, done.stderr
    rows = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    return json.loads(done.stdout.strip().splitlines()[-1]), rows


@pytest.fixture
def owner_secret(tmp_path):
    """The real producer writes the owner token under this test's HOME."""
    from holdspeak.config import Config
    from holdspeak.web_auth import ensure_web_token

    config = Path.home() / ".config" / "holdspeak" / "config.json"
    assert str(config).startswith(str(Path(os.environ["HOME"]))) and "Users/karol/.config" not in str(config)
    config.parent.mkdir(parents=True, exist_ok=True)
    token = ensure_web_token(Config(), save_path=config)
    assert token and token in config.read_text()
    return config, token


def test_a_read_inside_the_worktree_passes(tmp_path) -> None:
    worktree = tmp_path / "wt"
    worktree.mkdir()
    (worktree / "NOTES.md").write_text("inside line\n")
    out, rows = _read(tmp_path, worktree, "NOTES.md")
    assert out["decision"] is None and rows == []  # no hook at all
    if _pi_read_module():
        assert "inside line" in out["text"]


def test_a_read_of_the_owner_config_outside_is_held(tmp_path, owner_secret) -> None:
    config, token = owner_secret
    worktree = tmp_path / "wt"
    worktree.mkdir()
    out, rows = _read(tmp_path, worktree, str(config))
    assert out["decision"]["block"] is True and "outside" in out["decision"]["reason"]
    assert rows[0]["tool_name"] == "Read" and rows[0]["tool_input"] == {"file_path": str(config)}
    assert out["text"] is None or token not in out["text"]


def test_a_symlink_inside_to_a_file_outside_is_held(tmp_path, owner_secret) -> None:
    config, token = owner_secret
    worktree = tmp_path / "wt"
    worktree.mkdir()
    (worktree / "notes-link.json").symlink_to(config)
    out, rows = _read(tmp_path, worktree, "notes-link.json")
    assert out["decision"]["block"] is True
    assert rows[0]["tool_name"] == "Read"
    assert out["text"] is None or token not in out["text"]


def test_an_outside_read_is_held_by_the_real_hub_in_yolo(pi_rig, tmp_path, monkeypatch) -> None:  # noqa: F811
    """The Read the extension sends reaches the real GateService as OUTSIDE
    THE WORKTREE, and YOLO does not pass it."""
    import holdspeak.db as hsdb
    from holdspeak.kernel.runtime import _configure
    from holdspeak.principals import agent_credentials
    from holdspeak.services.gate_service import GateService

    rig = pi_rig
    _mode(tmp_path, monkeypatch, "yolo")
    result = rig.hand.hand(OWNER, "action", "ai_1", profile="pi-default")
    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    spawn = next(c for c in rig.tmux.calls if c[1] == "new-session")
    token = token_of(spawn)
    principal = agent_credentials.derive(token)
    monkeypatch.setenv("HOLDSPEAK_PARENT_OPERATION_ID", record["operation_id"])
    monkeypatch.setenv("HOLDSPEAK_AGENT_CREDENTIAL", token)
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: rig.db)
    _configure(rig.db)
    service = GateService(rig.db, launches=lambda: rig.service)
    outside = tmp_path / "outside-secret.json"
    outside.write_text("{}")
    clock = {"t": 0.0}
    verdict = coder_gate.run_hook(
        {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {"file_path": str(outside)},
         "tool_use_id": "read_out", "session_id": "smoke-session", "cwd": str(rig.worktree)},
        config=coder_gate.load_gate_config(rig.gate_path), agent="pi", ttl_seconds=1.0,
        http_post=lambda url, body, timeout: (200, service.propose(principal, body)),
        http_get=lambda url, timeout: (200, service.get_proposal(principal, url.rsplit("/", 1)[-1])),
        sleep=lambda s: clock.__setitem__("t", clock["t"] + 10), now=lambda: clock["t"],
    )
    proposal = rig.db.gate.get("read_out")
    assert proposal.operation["tool_call"]["scope"] == "outside"
    assert proposal.operation["tool_call"]["rule"] == "edit_outside_worktree"
    assert proposal.state != "approved" and verdict.deny  # YOLO holds it; it never ran


# ── 3. Stop after the first process exited ───────────────────────────


@pytest.fixture
def private_tmux(tmp_path, monkeypatch):
    if shutil.which("tmux") is None:
        pytest.skip("tmux is not installed")
    import tempfile

    socket_dir = Path(tempfile.mkdtemp(prefix="pi-r1-tmux-", dir="/tmp"))
    monkeypatch.setenv("TMUX_TMPDIR", str(socket_dir))
    monkeypatch.delenv("TMUX", raising=False)
    monkeypatch.delenv("TMUX_PANE", raising=False)
    ledger = tmp_path / "launches.json"
    from holdspeak.delivery import factory_launch

    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", ledger)
    yield socket_dir
    subprocess.run(["tmux", "kill-server"], capture_output=True, timeout=10)
    shutil.rmtree(socket_dir, ignore_errors=True)


def _leader_with_child(tmp_path: Path, name: str, *, retain: bool) -> dict[str, Any]:
    child = tmp_path / f"{name}-child.py"
    child.write_text(
        "import os, signal, time\nfrom pathlib import Path\nsignal.signal(signal.SIGHUP, signal.SIG_IGN)\n"
        f"Path({str(tmp_path / (name + '-ready'))!r}).write_text(str(os.getpid()))\ntime.sleep(120)\n"
    )
    leader = tmp_path / f"{name}-leader.py"
    leader.write_text(
        "import subprocess, sys, time\nfrom pathlib import Path\n"
        f"subprocess.Popen([sys.executable, {str(child)!r}])\n"
        f"while not Path({str(tmp_path / (name + '-exit'))!r}).exists(): time.sleep(0.02)\n"
    )
    assert subprocess.run(["tmux", "new-session", "-d", "-s", name,
                           "exec " + shlex.join([sys.executable, str(leader)])], timeout=10).returncode == 0
    if retain:
        subprocess.run(["tmux", "set-option", "-t", name, "remain-on-exit", "on"], timeout=10)
    deadline = time.monotonic() + 10
    while not (tmp_path / f"{name}-ready").exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    pane = subprocess.run(["tmux", "display-message", "-p", "-t", name, "#{pane_id}"],
                          capture_output=True, text=True, timeout=10).stdout.strip()
    # What the launch records while its first process lives.
    group = coder_factory.pane_process_group(pane)
    assert group is not None
    from holdspeak.delivery.factory_launch import LaunchLedger

    LaunchLedger().record({"launch_schema": 1, "launch_id": f"launch_{name}", "session": name,
                           "target": {"pane_id": pane}, "process_group": group})
    return {"pane": pane, "child": int((tmp_path / f"{name}-ready").read_text()), "group": group,
            "exit": tmp_path / f"{name}-exit"}


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def _wait_dead_leader(leader: int) -> None:
    deadline = time.monotonic() + 10
    while _alive(leader) and time.monotonic() < deadline:
        time.sleep(0.02)
    assert not _alive(leader)


@pytest.mark.parametrize("retain", [True, False], ids=["pane-kept", "pane-closed"])
def test_stop_ends_the_recorded_group_after_its_leader_exited(tmp_path, private_tmux, retain) -> None:
    from holdspeak import coder_steering

    launch = _leader_with_child(tmp_path, f"r1{'k' if retain else 'c'}", retain=retain)
    bystander = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"], start_new_session=True)
    try:
        if retain:
            assert coder_steering.arm("pi:r1", launch["pane"])["status"] == "armed"
        launch["exit"].touch()
        _wait_dead_leader(launch["group"]["leader"])
        assert _alive(launch["child"])  # the spike scar: the child lives on
        if not retain:
            # The pane closed with its first process: no grant can be armed.
            assert coder_steering.arm("pi:r1", launch["pane"])["status"] != "armed"
        result = coder_factory.kill("pi:r1", current_target=launch["pane"], scope="session", audit=lambda **_: 1)
        deadline = time.monotonic() + 5
        while _alive(launch["child"]) and time.monotonic() < deadline:
            time.sleep(0.05)
        assert not _alive(launch["child"]), result
        if retain:
            assert result["status"] == "killed"
        else:
            assert result.get("launch_processes") == "ended", result
        assert _alive(bystander.pid)  # an unrelated group is never touched
    finally:
        bystander.kill()
        try:
            os.kill(launch["child"], signal.SIGKILL)
        except OSError:
            pass


def test_a_recorded_group_with_another_session_is_not_signalled(tmp_path, private_tmux) -> None:
    """A recycled group id names another program: its session differs."""
    stranger = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"], start_new_session=True)
    try:
        pgid = os.getpgid(stranger.pid)
        assert coder_factory._members([(pgid, os.getsid(stranger.pid) + 1)]) == []
        assert coder_factory._members([(pgid, os.getsid(stranger.pid))]) == [stranger.pid]
        assert coder_factory._end_groups([(pgid, os.getsid(stranger.pid) + 1)]) == []
        assert _alive(stranger.pid)
    finally:
        stranger.kill()


def test_the_launch_records_its_process_group(pi_rig, monkeypatch) -> None:  # noqa: F811
    rig = pi_rig
    monkeypatch.setattr(coder_factory, "pane_process_group",
                        lambda pane, runner=None: {"pgid": 4242, "sid": 4242, "leader": 4242})
    result = rig.hand.hand(OWNER, "action", "ai_1", profile="pi-default")
    assert rig.launches.get(result["launch_id"])["process_group"] == {"pgid": 4242, "sid": 4242, "leader": 4242}


# ── 4. An approved Write reaches its terminal receipt ────────────────


def test_an_approved_pi_write_reaches_its_terminal_receipt(pi_rig, tmp_path, monkeypatch) -> None:  # noqa: F811
    import holdspeak.db as hsdb
    from holdspeak.kernel.runtime import _configure
    from holdspeak.principals import agent_credentials
    from holdspeak.services.gate_service import GateService

    rig = pi_rig
    _mode(tmp_path, monkeypatch, "yolo")
    result = rig.hand.hand(OWNER, "action", "ai_1", profile="pi-default")
    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    spawn = next(c for c in rig.tmux.calls if c[1] == "new-session")
    token = token_of(spawn)
    principal = agent_credentials.derive(token)
    monkeypatch.setenv("HOLDSPEAK_PARENT_OPERATION_ID", record["operation_id"])
    monkeypatch.setenv("HOLDSPEAK_AGENT_CREDENTIAL", token)
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: rig.db)
    _configure(rig.db)
    service = GateService(rig.db, launches=lambda: rig.service)
    cfg = coder_gate.load_gate_config(rig.gate_path)
    payload = {"hook_event_name": "PreToolUse", "session_id": "smoke-session", "tool_name": "Write",
               "tool_use_id": "pi-write", "tool_input": {"file_path": "NOTES.md", "content": "x"},
               "cwd": str(rig.worktree)}
    decision = coder_gate.run_hook(
        payload, config=cfg, agent="pi",
        http_post=lambda url, body, timeout: (200, service.propose(principal, body)),
        http_get=lambda url, timeout: (200, service.get_proposal(principal, url.rsplit("/", 1)[-1])),
    )
    proposal = rig.db.gate.get("pi-write")
    assert decision.deny is None and proposal.state == "approved"
    (rig.worktree / "NOTES.md").write_text("x")
    monkeypatch.setattr(coder_gate, "_default_post", lambda url, body, timeout, **kw: (
        200, service.record_receipt(principal, "pi-write", body)))
    assert coder_gate.run_post_tool_hook({**payload, "hook_event_name": "PostToolUse"}, config=cfg, agent="pi")
    operation = str(proposal.operation["kernel_operation_id"])
    with rig.db._connection() as conn:
        state = conn.execute("SELECT state FROM kernel_operations WHERE operation_id=?", (operation,)).fetchone()[0]
    assert state == "succeeded"
