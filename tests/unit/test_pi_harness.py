"""pi is the third coding-agent harness (pi spike #1020, docs/internal/CONDUCTOR.md).

The five gaps the spike named, each beside its Claude Code / Codex twin:
the agent name (``pi:<session_id>``, the CLIs), the ``pi-default`` profile on
the hub's engine for coding work, the launch adapter (the launch's own pi
folder, the key off argv, the process-group Stop), the maintained extension
(the payload mapping, fail closed), and the expiry words. The extension runs
here under the real ``node`` with a fake ``pi`` object (skipped without node).
"""
from __future__ import annotations

import io
import json
import os
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak import coder_factory, coder_gate
from holdspeak.agent_context.hooks import PI_HOOKS_FILE, pi_hook_template
from holdspeak.agent_context.models import is_blocked, turn_end, wait_kind
from holdspeak.agent_context.sessions import ingest_agent_hook_event
from holdspeak.delivery import agent_mcp, pi_launch
from holdspeak.delivery.factory_launch import (
    KNOWN_EXECUTABLES,
    AgentProfileStore,
    LaunchRefused,
    LaunchService,
    agent_of_profile,
)
from holdspeak.delivery.pi_launch import PiEngine
from tests.unit._spawn_env import command_of, model_key_of, token_of
from tests.unit.test_agent_hand import OWNER, _rig, _wait_for, db  # noqa: F401  (db is a fixture)

PREFIX = "uv run --project /opt/hs holdspeak"
ENGINE = PiEngine(
    endpoint="http://192.168.1.43:8080/v1", model="qwen3.8-27b", context_window=49152,
    key_slot="HOLDSPEAK_PROFILE_KEY_LAN_BOX", host="192.168.1.43:8080", boundary="private_network",
)


# ── gap 1: the agent name ────────────────────────────────────────────


def test_pi_is_a_gate_agent_and_its_sessions_are_pi_keys() -> None:
    assert coder_gate.GATE_AGENTS == ("claude", "codex", "pi")
    assert coder_gate.agent_identity("01a11d46", "pi") == "pi:01a11d46"
    assert "pi" in KNOWN_EXECUTABLES
    assert [agent_of_profile(p) for p in ("pi-default", "codex-default", "claude-default", None)] == [
        "pi", "codex", "claude", "claude",
    ]


@pytest.mark.parametrize(
    "argv",
    [
        ["gate", "hook", "--agent", "pi"],
        ["agent-hook", "ingest", "--agent", "pi"],
        ["agent-hook", "latest", "--agent", "pi"],
        ["agent-hook", "templates", "--agent", "pi"],
    ],
)
def test_the_hook_clis_take_agent_pi(argv: list[str]) -> None:
    import argparse

    from holdspeak.commands.agent_hook import build_argparse_subparsers
    from holdspeak.commands.gate import build_gate_subparsers

    parser = argparse.ArgumentParser(prog="holdspeak")
    sub = parser.add_subparsers(dest="command")
    build_argparse_subparsers(sub.add_parser("agent-hook"))
    build_gate_subparsers(sub.add_parser("gate"))
    assert parser.parse_args(argv).agent == "pi"


def test_the_gate_hook_denies_a_pi_call_in_the_shape_the_extension_reads(tmp_path, monkeypatch) -> None:
    from holdspeak.commands.gate import _cmd_hook

    worktree = tmp_path / "wt"
    worktree.mkdir()
    gate_file = tmp_path / "gate.json"
    gate_file.write_text(json.dumps({"gate_schema": 1, "armed": True, "repos": {str(worktree): ["Bash"]}}))
    monkeypatch.setattr(coder_gate, "GATE_CONFIG_FILE", gate_file)
    monkeypatch.setenv("HOLDSPEAK_HUB_URL", "http://127.0.0.1:9")  # nothing listens: fail closed
    monkeypatch.setenv("HOLDSPEAK_AGENT_CREDENTIAL", "tok")
    out = io.StringIO()
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "echo hi"},
               "tool_use_id": "call_1", "session_id": "s1", "cwd": str(worktree)}
    assert _cmd_hook(stdin=io.StringIO(json.dumps(payload)), out=out, agent="pi") == 0
    answer = json.loads(out.getvalue())["hookSpecificOutput"]
    assert answer["permissionDecision"] == "deny" and answer["permissionDecisionReason"].strip()


def test_the_rider_reads_a_pi_turn_end_as_its_wait(tmp_path) -> None:
    """pi sends no idle Notification: its Stop (the extension's agent_end) is
    the wait, the last message the ask, as for Codex (R3)."""
    state = tmp_path / "agents.json"
    cwd = str(tmp_path)
    base = {"session_id": "01a11d46", "cwd": cwd}
    started = ingest_agent_hook_event(agent="pi", payload={**base, "hook_event_name": "SessionStart"},
                                      state_path=state, env={})
    assert started.agent == "pi" and not is_blocked(started)
    asks = ingest_agent_hook_event(
        agent="pi", payload={**base, "hook_event_name": "Stop",
                             "last_assistant_message": "Still 0 projects. What name should the new project have?"},
        state_path=state, env={},
    )
    assert is_blocked(asks) and wait_kind(asks) == "answer"
    assert asks.question == "Still 0 projects. What name should the new project have?"
    resumed = ingest_agent_hook_event(agent="pi", payload={**base, "hook_event_name": "UserPromptSubmit",
                                                           "prompt": "Call it Atlas."},
                                      state_path=state, env={})
    assert not is_blocked(resumed)
    done = ingest_agent_hook_event(agent="pi", payload={**base, "hook_event_name": "Stop",
                                                        "last_assistant_message": "There are 0 projects. DONE"},
                                   state_path=state, env={})
    # As for Codex, every turn end is a wait; the lane reads how it ended.
    assert turn_end(asks) == "asks" and turn_end(done) == "idle"
    assert turn_end(done, work_done=True) == "done"


# ── gap 5: the expiry words ──────────────────────────────────────────


def test_an_expiry_deny_closes_like_the_owner_deny() -> None:
    from holdspeak.coder_gate import EXPIRED_CLOSE, _deny_reason

    assert EXPIRED_CLOSE == "This call expired with no decision. Do not try it again in a different form."
    said = _deny_reason({"state": "expired", "reason": "expired: no decision arrived before the hold ran out"})
    assert said.endswith(EXPIRED_CLOSE)
    owner = _deny_reason({"state": "denied", "reason": "no"})
    assert owner.endswith("Do not try it again in a different form.")


def test_a_hold_that_runs_out_in_the_hook_closes_with_the_same_words(tmp_path) -> None:
    gate_file = tmp_path / "gate.json"
    gate_file.write_text(json.dumps({"gate_schema": 1, "armed": True, "repos": {str(tmp_path): ["Bash"]}}))
    clock = {"t": 0.0}

    def sleep(seconds: float) -> None:
        clock["t"] += 10.0

    decision = coder_gate.run_hook(
        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "echo"},
         "tool_use_id": "c1", "session_id": "s", "cwd": str(tmp_path)},
        config=coder_gate.load_gate_config(gate_file),
        http_post=lambda url, body, timeout: (200, {"state": "held"}),
        http_get=lambda url, timeout: (200, {"state": "held"}),
        sleep=sleep, now=lambda: clock["t"], ttl_seconds=5.0, agent="pi",
    )
    assert decision.deny and decision.deny.endswith(coder_gate.EXPIRED_CLOSE)


# ── gap 3: the launch adapter ────────────────────────────────────────


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def test_the_launch_folder_is_private_and_names_no_secret(tmp_path) -> None:
    hooks = coder_gate.pi_spawn_hooks(PREFIX)
    folder = pi_launch.write_pi_dir("launch_pi01", ENGINE, hub_url="http://127.0.0.1:8791",
                                    hooks=hooks, keyed=True, directory=tmp_path)
    assert folder == tmp_path / "pi-launch_pi01"
    assert _mode(folder) == 0o700 and _mode(folder / "sessions") == 0o700
    for name in ("models.json", "mcp.json", PI_HOOKS_FILE):
        assert _mode(folder / name) == 0o600, name
    models = json.loads((folder / "models.json").read_text())["providers"]["lan"]
    assert models["baseUrl"] == "http://192.168.1.43:8080/v1" and models["api"] == "openai-completions"
    assert models["apiKey"] == "${HOLDSPEAK_PI_MODEL_KEY}"  # a reference: pi reads its environment
    assert models["models"] == [{"id": "qwen3.8-27b", "contextWindow": 49152}]
    server = json.loads((folder / "mcp.json").read_text())["mcpServers"]["holdspeak"]
    # pi does not expand ${VAR} in url: the URL is text; the header is a variable.
    assert server["url"] == "http://127.0.0.1:8791/api/mcp"
    assert server["headers"] == {"Authorization": "Bearer ${HOLDSPEAK_AGENT_CREDENTIAL}"}
    assert server["exposure"] == "deferred"
    assert {k for k, v in server["toolExposure"].items() if v == "direct"} == set(pi_launch.DIRECT_TOOLS)
    assert {"project.*", "desk.needs_you", "follow_through.*", "decision_record.*", "meeting.get"} <= set(
        pi_launch.DIRECT_TOOLS
    )
    doc = json.loads((folder / PI_HOOKS_FILE).read_text())
    assert doc["gate"]["argv"] == [*shlex.split(PREFIX), "gate", "hook", "--agent", "pi"]
    assert doc["rider"]["argv"] == [*shlex.split(PREFIX), "agent-hook", "ingest", "--agent", "pi"]
    assert doc["tools"] == {"bash": "Bash", "edit": "Edit", "write": "Write"}
    # A keyless engine gets pi's dummy key, never a variable it cannot fill.
    keyless = pi_launch.models_document(ENGINE, keyed=False)["providers"]["lan"]
    assert keyless["apiKey"] == "none"


def test_the_launch_folder_goes_with_the_mcp_config(tmp_path) -> None:
    pi_launch.write_pi_dir("launch_pi02", ENGINE, hub_url="http://h", hooks={}, keyed=False, directory=tmp_path)
    agent_mcp.write_mcp_config("launch_pi02", tmp_path)
    assert agent_mcp.remove_mcp_config("launch_pi02", tmp_path) is True
    assert not (tmp_path / "pi-launch_pi02").exists()
    assert not agent_mcp.mcp_config_path("launch_pi02", tmp_path).exists()
    # A pi launch that never wrote a --mcp-config still loses its folder.
    pi_launch.write_pi_dir("launch_pi03", ENGINE, hub_url="http://h", hooks={}, keyed=False, directory=tmp_path)
    assert agent_mcp.remove_mcp_config("launch_pi03", tmp_path) is True
    assert not (tmp_path / "pi-launch_pi03").exists()


def test_the_model_key_rides_the_one_shot_file_never_argv(tmp_path) -> None:
    env_file = coder_factory.write_credential_env("tok123", tmp_path, model_key="sekret-key")
    assert _mode(env_file) == 0o600
    probe = 'printf "%s|%s" "$HOLDSPEAK_AGENT_CREDENTIAL" "${HOLDSPEAK_PI_MODEL_KEY-unset}"'
    done = subprocess.run(
        coder_factory.session_argv(env_file, probe), capture_output=True, text=True, timeout=20,
        env={"PATH": "/usr/bin:/bin", "SHELL": "/bin/sh"},
    )
    assert done.stdout == "tok123|sekret-key" and not env_file.exists()
    # No second line: the variable is unset, never an empty key.
    plain = coder_factory.write_credential_env("tok123", tmp_path)
    done = subprocess.run(coder_factory.session_argv(plain, probe), capture_output=True, text=True,
                          timeout=20, env={"PATH": "/usr/bin:/bin", "SHELL": "/bin/sh",
                                           "HOLDSPEAK_PI_MODEL_KEY": "inherited"})
    assert done.stdout == "tok123|unset"
    with pytest.raises(ValueError):
        coder_factory.write_credential_env("tok", tmp_path, model_key="two\nlines")


@pytest.fixture
def pi_rig(tmp_path, db, monkeypatch):  # noqa: F811
    monkeypatch.setenv(ENGINE.key_slot, "sekret-lan-key")
    rig = _rig(tmp_path, db, monkeypatch, agent="pi")
    rig.service._pi_engine = lambda: ENGINE
    yield rig
    rig.tmux.ended = True


def test_a_pi_hand_launches_gated_on_the_engine_for_coding(pi_rig, tmp_path) -> None:
    rig = pi_rig
    result = rig.hand.hand(OWNER, "action", "ai_1", profile="pi-default")
    assert result["status"] == "launched" and result["gate"] == "gated", result
    gate = json.loads(rig.gate_path.read_text(encoding="utf-8"))
    assert gate["repos"] == {str(rig.worktree): ["Bash"]}
    spawn = next(c for c in rig.tmux.calls if c[1] == "new-session")
    command = command_of(spawn)
    folder = tmp_path / "mcp" / f"pi-{result['launch_id']}"
    assert f"PI_CODING_AGENT_DIR={shlex.quote(str(folder))}" in command
    assert "PI_OFFLINE=1" in command and "PI_TELEMETRY=0" in command
    assert " exec pi --model lan/qwen3.8-27b --session-dir " in command
    assert f"-e {shlex.quote(str(pi_launch.EXTENSION_PATH))}" in command
    assert pi_launch.EXTENSION_PATH.is_file()
    # The key is in no argv and no command record: the spawn named its slot.
    for call in rig.tmux.calls:
        assert not any("sekret-lan-key" in str(arg) for arg in call), call
    _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    with rig.db._connection() as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for table in tables:
            for row in conn.execute(f'SELECT * FROM "{table}"'):
                assert "sekret-lan-key" not in json.dumps([str(v) for v in tuple(row)]), table
    assert "sekret-lan-key" not in (tmp_path / "launches.json").read_text()
    # ... and it reached the session's one-shot file, line two.
    assert token_of(spawn) and model_key_of(spawn) == "sekret-lan-key"
    assert rig.launches.get(result["launch_id"])["profile_id"] == "pi-default"


def test_a_pi_hand_with_no_engine_refuses_by_the_route_word(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    from holdspeak.services.agent_hand_service import AgentHandRefused

    rig = _rig(tmp_path, db, monkeypatch, agent="pi")

    def no_engine():
        raise LaunchRefused("no_assignment", "pi has no engine for coding work")

    rig.service._pi_engine = no_engine
    with pytest.raises(AgentHandRefused) as refused:
        rig.hand.hand(OWNER, "action", "ai_1", profile="pi-default")
    assert refused.value.code == "no_assignment"
    assert not [c for c in rig.tmux.calls if c[1] == "new-session"]
    # And with no resolver at all, the same word.
    bare = LaunchService(profiles=AgentProfileStore(tmp_path / "p2.json"), registry=None, targets=None,
                         commands=None, attempts=None, runner=lambda argv: None)
    with pytest.raises(LaunchRefused) as again:
        bare._preflight(bare._profiles.get("pi-default"))
    assert again.value.reason == "no_assignment"


def test_a_profile_file_from_before_pi_gets_pi_default(tmp_path) -> None:
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps({"agent_profiles_schema": 1, "profiles": [
        {"profile_id": "claude-default", "label": "Claude Code", "executable": "claude", "args": [],
         "option_slots": {}},
    ]}))
    store = AgentProfileStore(path)
    assert store.get("pi-default")["executable"] == "pi"
    assert store.get("codex-default") is None  # only a later default joins
    saved = json.loads(path.read_text())
    assert [p["profile_id"] for p in saved["profiles"]] == ["claude-default", "pi-default"]


# ── the Stop: the pane's whole process group ─────────────────────────


def test_stop_kills_the_panes_process_group_with_a_waiting_child(tmp_path, monkeypatch) -> None:
    """The spike scar: a hook child that waits on a hold outlived pi. The kill
    ends the group: the agent and the child it started."""
    from holdspeak import coder_steering

    # A pane: a leader (the agent) with a child that waits (the held hook).
    leader = subprocess.Popen(["/bin/sh", "-c", "sleep 300 & wait"], start_new_session=True)
    try:
        deadline = time.monotonic() + 10
        child = None
        while time.monotonic() < deadline and child is None:
            out = subprocess.run(["pgrep", "-P", str(leader.pid)], capture_output=True, text=True).stdout.split()
            child = int(out[0]) if out else None
            time.sleep(0.05)
        assert child is not None
        seen: list[list[str]] = []

        def real_tmux(argv, cwd=None):
            seen.append(list(argv))
            if argv[:2] == ["tmux", "list-panes"]:
                return SimpleNamespace(returncode=0, stdout=f"{leader.pid}\n", stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        monkeypatch.setattr(coder_steering, "_default_runner", real_tmux)
        monkeypatch.setattr(coder_steering, "require_grant",
                            lambda *a, **k: {"status": "ok", "pane_id": "%9"})
        result = coder_factory.kill("pi:s1", current_target="%9", scope="session", audit=lambda **_: 1)
        assert result["status"] == "killed"
        assert ["tmux", "kill-session", "-t", "%9"] in seen
        leader.wait(timeout=10)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                os.kill(child, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        with pytest.raises(ProcessLookupError):
            os.kill(child, 0)
    finally:
        try:
            os.killpg(leader.pid, signal.SIGKILL)
        except OSError:
            pass


def test_a_fake_runner_never_signals_a_process(monkeypatch) -> None:
    from holdspeak import coder_steering

    monkeypatch.setattr(coder_steering, "require_grant", lambda *a, **k: {"status": "ok", "pane_id": "%9"})
    signalled: list = []
    monkeypatch.setattr(os, "killpg", lambda *a: signalled.append(a))
    fake = lambda argv, cwd=None: SimpleNamespace(returncode=0, stdout=f"{os.getpid()}\n", stderr="")  # noqa: E731
    assert coder_factory.kill("pi:s", current_target="%9", scope="session", runner=fake,
                              audit=lambda **_: 1)["status"] == "killed"
    assert signalled == []


# ── gap 4: the extension (real node, fake pi) ────────────────────────

_DRIVER = r"""
const ext = (await import(process.argv[2])).default;
const handlers = {};
ext({ on: (name, fn) => { handlers[name] = fn; } });
const ctx = { cwd: process.argv[3], sessionManager: { getSessionId: () => "01a11d46", getSessionFile: () => "/t/s.jsonl" } };
const calls = JSON.parse(process.argv[4]);
const out = [];
for (const [name, event] of calls) {
  out.push(await handlers[name](event, ctx));
}
await new Promise((r) => setTimeout(r, 1500));
console.log(JSON.stringify({ events: Object.keys(handlers).sort(), out }));
"""

_FAKE_GATE = r"""
import json, sys
payload = json.load(sys.stdin)
with open(sys.argv[1], "a") as log:
    log.write(json.dumps(payload) + "\n")
command = (payload.get("tool_input") or {}).get("command") or ""
if payload.get("hook_event_name") == "PreToolUse" and "rm " in command:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": "denied from the desk: no. The owner denied this call. Do not try it again in a different form."}}))
if payload.get("hook_event_name") == "PreToolUse" and "boom" in command:
    sys.exit(3)
if payload.get("hook_event_name") == "PreToolUse" and "garble" in command:
    print("not json")
"""


def _run_extension(tmp_path: Path, calls: list, *, document: bool = True) -> tuple[dict, list, list]:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    folder = tmp_path / "pi"
    folder.mkdir(exist_ok=True)
    gate_log, rider_log = tmp_path / "gate.log", tmp_path / "rider.log"
    fake = tmp_path / "fake_hook.py"
    fake.write_text(_FAKE_GATE)
    if document:
        doc = pi_hook_template(gate_command="x")
        doc["gate"]["argv"] = [sys.executable, str(fake), str(gate_log)]
        doc["rider"]["argv"] = [sys.executable, str(fake), str(rider_log)]
        (folder / PI_HOOKS_FILE).write_text(json.dumps(doc))
    driver = tmp_path / "driver.mjs"
    driver.write_text(_DRIVER)
    done = subprocess.run(
        [node, "--no-warnings", str(driver), str(pi_launch.EXTENSION_PATH), str(tmp_path), json.dumps(calls)],
        capture_output=True, text=True, timeout=60,
        env={**os.environ, "PI_CODING_AGENT_DIR": str(folder)},
    )
    assert done.returncode == 0, done.stderr
    result = json.loads(done.stdout.strip().splitlines()[-1])

    def rows(path: Path) -> list:
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    return result, rows(gate_log), rows(rider_log)


def test_the_extension_maps_pi_tools_to_the_gate_names_and_blocks_on_a_deny(tmp_path) -> None:
    calls = [
        ["session_start", {"type": "session_start", "reason": "startup"}],
        ["before_agent_start", {"type": "before_agent_start", "prompt": "the brief"}],
        ["tool_call", {"toolName": "bash", "toolCallId": "call_1", "input": {"command": "rm -rf /tmp/x"}}],
        ["tool_call", {"toolName": "bash", "toolCallId": "call_2", "input": {"command": "ls"}}],
        ["tool_call", {"toolName": "edit", "toolCallId": "p/1", "input": {"path": "a.py", "edits": []}}],
        ["tool_call", {"toolName": "write", "toolCallId": "call_4", "input": {"path": "b.py", "content": "x"}}],
        ["tool_call", {"toolName": "mcp__holdspeak__project_list", "toolCallId": "call_5", "input": {}}],
        ["tool_call", {"toolName": "read", "toolCallId": "call_6", "input": {"path": "a.py"}}],
        ["tool_result", {"toolName": "bash", "toolCallId": "call_2", "input": {"command": "ls"}, "isError": False}],
        ["agent_end", {"messages": [{"role": "user", "content": []}, {"role": "assistant", "stopReason": "stop",
                                    "content": [{"type": "text", "text": "Done.</think>\n\nShould I open the PR?"}]}]}],
        ["session_shutdown", {"type": "session_shutdown", "reason": "quit"}],
    ]
    result, gate, rider = _run_extension(tmp_path, calls)
    assert result["events"] == ["agent_end", "before_agent_start", "session_shutdown", "session_start",
                                "tool_call", "tool_result"]
    out = result["out"]
    assert out[2] == {"block": True, "reason": "denied from the desk: no. The owner denied this call. "
                                                "Do not try it again in a different form."}
    assert out[3] is None and out[4] is None and out[5] is None and out[6] is None and out[7] is None
    pre = [row for row in gate if row["hook_event_name"] == "PreToolUse"]
    assert [(r["tool_name"], r["tool_use_id"]) for r in pre] == [
        ("Bash", "call_1"), ("Bash", "call_2"), ("Edit", "p-1"), ("Write", "call_4"),
        ("mcp__holdspeak__project_list", "call_5"),
    ]  # read is not sent; a nested id loses its "/"
    assert pre[0]["tool_input"] == {"command": "rm -rf /tmp/x"}
    assert pre[2]["tool_input"]["file_path"] == "a.py" and pre[3]["tool_input"]["file_path"] == "b.py"
    assert all(r["session_id"] == "01a11d46" and r["cwd"] == str(tmp_path) for r in pre)
    assert {r["hook_event_name"] for r in gate} == {"SessionStart", "PreToolUse", "PostToolUse", "SessionEnd"}
    events = [r["hook_event_name"] for r in rider]
    assert events == ["SessionStart", "UserPromptSubmit", "PostToolUse", "Stop", "SessionEnd"]
    stop = next(r for r in rider if r["hook_event_name"] == "Stop")
    assert stop["last_assistant_message"] == "Done.\n\nShould I open the PR?"
    assert next(r for r in rider if r["hook_event_name"] == "SessionEnd")["reason"] == "prompt_input_exit"


def test_the_extension_fails_closed(tmp_path) -> None:
    calls = [
        ["tool_call", {"toolName": "bash", "toolCallId": "c1", "input": {"command": "boom"}}],
        ["tool_call", {"toolName": "bash", "toolCallId": "c2", "input": {"command": "garble"}}],
    ]
    result, _gate, _rider = _run_extension(tmp_path, calls)
    assert [o["block"] for o in result["out"]] == [True, True]
    assert "exit 3" in result["out"][0]["reason"]
    # No hook document (a launch HoldSpeak did not write): every gated call blocks.
    nodoc = tmp_path / "nodoc"
    nodoc.mkdir()
    result, _g, _r = _run_extension(nodoc, [
        ["tool_call", {"toolName": "bash", "toolCallId": "c3", "input": {"command": "ls"}}],
    ], document=False)
    assert result["out"][0]["block"] is True


# ── the Agents card and the doctor ───────────────────────────────────


def test_detect_agents_has_a_pi_row_with_its_hooks_shipped(tmp_path) -> None:
    from holdspeak.services.onboarding_service import detect_agents

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    which = {"pi": str(bin_dir / "pi"), "tmux": "/usr/bin/tmux"}.get
    rows = {row["id"]: row for row in detect_agents(which=which, home=tmp_path, environ={})["agents"]}
    assert set(rows) == {"claude", "codex", "pi"}
    pi = rows["pi"]
    assert pi["installed"] and pi["hooks"] == "installed" and pi["ready"] and pi["verb"] is None
    assert rows["claude"]["installed"] is False

