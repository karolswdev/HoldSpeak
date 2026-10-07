"""Conductor R3: Codex is gated and supervised like Claude Code.

Every Codex fact here was observed on codex-cli 0.159.0 under an isolated
``CODEX_HOME`` (the PR names each): the PreToolUse payload, the deny output,
the PermissionRequest and Stop payloads, the folder-trust and composer
screens at tmux's default 80x24, and the hook trust rules. The producers are
real (the K2 launch rig: real git, ledger, kernel and receipts; the hook
runner; GateService; the rider registry; the Needs you membership). Codex is
faked only at the process boundary: a fake ``codex`` executable that speaks
the app-server JSON-RPC, and the K2 tmux fake. One smoke runs the real
``codex app-server`` under an isolated CODEX_HOME (skipped without codex).
"""
from __future__ import annotations

import io
import json
import os
import shutil
import stat
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import holdspeak.db as hsdb
from holdspeak import coder_gate
from holdspeak.agent_context import codex_trust
from holdspeak.agent_context.hooks import codex_hook_template, install_agent_hooks
from holdspeak.agent_context.models import is_blocked, wait_kind
from holdspeak.agent_context.sessions import ingest_agent_hook_event
from holdspeak.coder_factory import launch_identity
from holdspeak.coder_gate import load_gate_config, run_hook
from holdspeak.db.gate import APPROVED, HELD
from holdspeak.delivery import first_message
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.gate_service import GateService
from holdspeak.services.needs_you_membership import TO_ANSWER, TO_APPROVE, coder_items
from tests.unit.test_agent_hand import OWNER, _rig, _wait_for, db  # noqa: F401  (db is a fixture)

PREFIX = "uv run --project /opt/hs holdspeak"
SID = "01a113be-d63e-7d42-b2dd-6e5403948cb0"


# ── observed Codex 0.159 payloads and screens ────────────────────────


def _pre_tool_use(cwd: str, command: str, tool_use_id: str = "call_7CHH1AUoz8EMXiLfllIIR7wlCDdHOTDn") -> dict:
    """The PreToolUse payload Codex sent (``codex exec`` and the TUI)."""
    return {
        "session_id": SID, "turn_id": "01a113ab-320d-7473-ae73-9ecda3eba3d0",
        "transcript_path": None, "cwd": cwd, "hook_event_name": "PreToolUse",
        "model": "qwen3.8-27b", "permission_mode": "default", "tool_name": "Bash",
        "tool_input": {"command": command}, "tool_use_id": tool_use_id,
    }


def _permission_request(cwd: str) -> dict:
    return {
        "session_id": SID, "turn_id": "01a113b3-fafa-7270-8706-33a5095c4f4c", "cwd": cwd,
        "hook_event_name": "PermissionRequest", "model": "qwen3.8-27b", "permission_mode": "default",
        "tool_name": "Bash",
        "tool_input": {
            "command": "touch perm.txt",
            "description": "May I run `touch perm.txt` outside the sandbox? The current sandbox is "
                           "read-only, so the file can't be created without escalated permissions.",
        },
    }


def _stop(cwd: str, message: str) -> dict:
    return {
        "session_id": SID, "turn_id": "t1", "cwd": cwd, "hook_event_name": "Stop",
        "model": "qwen3.8-27b", "permission_mode": "default", "stop_hook_active": False,
        "last_assistant_message": message,
    }


def _trust_screen(path: str, cursor_on_yes: bool = True) -> str:
    """Codex's folder-trust screen in its own process (``--no-daemon``), as
    tmux showed it at 80x24: the path breaks at 76 characters."""
    yes, other = ("› ", "  ") if cursor_on_yes else ("  ", "› ")
    rows = [path[i:i + 76] for i in range(0, len(path), 76)]
    return "\n".join([
        "", "  Folder access", *[f"  {row}" for row in rows], "",
        "  Trust this folder? Codex can read, edit, and run files here, subject to your",
        "  permission settings. Folder settings can run code automatically, even",
        "  without a model request. Continue only if you trust these files. Your trust",
        "  decision will be saved.", "",
        f"{yes}1. Trust and continue", f"{other}2. Quit", "",
        "  enter continue · esc quit", "", "", "",
    ])


COMPOSER = "\n".join([
    "  >_ OpenAI Codex (v0.159.0)", "     /private/tmp/…/cx/repo3", "",
    "  How deep does this codebase go?", "", "", "",
    "› Ask Codex to do anything", "",
    "  qwen3.8-27b default · /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpea…",
    "  ? for shortcuts", "", "",
])

HOOKS_REVIEW = "\n".join([
    "  Hooks need review", "  7 hooks are new or changed.",
    "  Hooks can run outside the sandbox after you trust them.", "",
    "› 1. Review hooks", "  2. Trust all and continue",
    "  3. Continue without trusting (hooks won't run)", "", "  enter confirm · esc skip",
])


# ── 1. the hook template and the launch flags ────────────────────────


def test_the_codex_template_holds_bash_as_long_as_claude_code() -> None:
    template = codex_hook_template(gate_command=f"{PREFIX} gate hook --agent codex")["hooks"]
    gate = template["PreToolUse"][0]
    assert gate["matcher"] == "^Bash$"
    assert gate["hooks"][0]["command"].endswith("gate hook --agent codex")
    assert gate["hooks"][0]["timeout"] == coder_gate.HOOK_TIMEOUT_SECONDS == 300
    # Codex's own events: no Notification (Codex has none); its approval prompt.
    assert set(template) == {
        "SessionStart", "UserPromptSubmit", "PreToolUse", "PermissionRequest",
        "PostToolUse", "Stop", "SessionEnd",
    }
    # Codex clamps SessionEnd hooks to 3 s.
    assert all(h["timeout"] <= 3 for e in template["SessionEnd"] for h in e["hooks"])
    # The install template (no gate) never runs the gate on the owner's own sessions.
    plain = codex_hook_template()["hooks"]
    assert all(" gate hook" not in h["command"] for es in plain.values() for e in es for h in e["hooks"])


def test_the_launch_flags_are_toml_and_name_this_checkout() -> None:
    args = coder_gate.codex_spawn_args(PREFIX)
    assert args[0] == "--no-daemon"
    hooks = coder_gate.codex_spawn_hooks(PREFIX)["hooks"]
    pairs = list(zip(args[1::2], args[2::2]))
    assert [flag for flag, _ in pairs] == ["-c"] * len(hooks)
    for _flag, value in pairs:
        key, _, raw = value.partition("=")
        event = key.removeprefix("hooks.")
        assert tomllib.loads(f"v = {raw}")["v"] == hooks[event]
    commands = {h["command"] for es in hooks.values() for e in es for h in e["hooks"]}
    assert commands == {f"{PREFIX} gate hook --agent codex", f"{PREFIX} agent-hook ingest --agent codex"}


# ── 2. the gate speaks Codex ─────────────────────────────────────────


def test_the_gate_hook_denies_a_codex_call_in_the_shape_codex_reads(tmp_path, monkeypatch) -> None:
    from holdspeak.commands.gate import _cmd_hook

    worktree = tmp_path / "wt"
    worktree.mkdir()
    gate_file = tmp_path / "gate.json"
    gate_file.write_text(json.dumps({"gate_schema": 1, "armed": True, "repos": {str(worktree): ["Bash"]}}))
    monkeypatch.setattr(coder_gate, "GATE_CONFIG_FILE", gate_file)
    monkeypatch.setenv("HOLDSPEAK_HUB_URL", "http://127.0.0.1:9")  # nothing listens: fail closed
    monkeypatch.setenv("HOLDSPEAK_AGENT_CREDENTIAL", "tok")
    out = io.StringIO()
    stdin = io.StringIO(json.dumps(_pre_tool_use(str(worktree), "touch blocked.txt")))
    assert _cmd_hook(stdin=stdin, out=out, agent="codex") == 0
    answer = json.loads(out.getvalue())
    # Codex 0.159 blocks on exactly this; a deny needs a non-empty reason.
    assert answer["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert answer["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert answer["hookSpecificOutput"]["permissionDecisionReason"].strip()


def test_an_inert_codex_call_gets_no_output(tmp_path, monkeypatch) -> None:
    """Codex refuses ``permissionDecision: allow`` (unsupported): an allow is no output."""
    from holdspeak.commands.gate import _cmd_hook

    monkeypatch.setattr(coder_gate, "GATE_CONFIG_FILE", tmp_path / "absent.json")
    monkeypatch.delenv("HOLDSPEAK_PARENT_OPERATION_ID", raising=False)
    out = io.StringIO()
    stdin = io.StringIO(json.dumps(_pre_tool_use(str(tmp_path), "ls")))
    assert _cmd_hook(stdin=stdin, out=out, agent="codex") == 0
    assert out.getvalue() == ""


def test_a_codex_session_credential_names_codex(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("HOLDSPEAK_AGENT_CREDENTIAL", raising=False)
    monkeypatch.setattr(coder_gate, "_owner_token", lambda: "owner")
    sent: list[dict] = []

    def send(request, timeout):
        sent.append(json.loads(request.data.decode()))
        return 201, {"credential": "cred-x"}

    monkeypatch.setattr(coder_gate, "_send", send)
    assert coder_gate.issue_agent_credential("abc", "http://hub", agent="codex") == "cred-x"
    assert sent == [{"identity": "codex:abc"}]
    with pytest.raises(ValueError):
        coder_gate.agent_identity("abc", "other")


# ── 3. a Codex launch, gated and decided by the Control mode ─────────


def _mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    config = tmp_path / "config.json"
    monkeypatch.setattr("holdspeak.config.CONFIG_FILE", config)
    config.write_text(json.dumps({"control_mode": mode}), encoding="utf-8")


@pytest.fixture
def codex_launched(tmp_path, db, monkeypatch):  # noqa: F811
    rig = _rig(tmp_path, db, monkeypatch, agent="codex")
    result = rig.hand.hand(OWNER, "action", "ai_1", profile="codex-default")
    assert result["status"] == "launched" and result["gate"] == "gated", result
    _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    hsdb.reset_database()
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    _configure(db)
    rig.gate = GateService(db, launches=lambda: rig.service)
    rig.launch_id = result["launch_id"]
    yield rig
    rig.tmux.ended = True
    _wait_for(lambda: rig.launches.get(rig.launch_id), "state", "complete")
    hsdb.reset_database()


_N = {"n": 0}


def _codex_call(rig: Any, command: str, principal: Principal) -> Any:
    """One observed-shape Codex PreToolUse through the real hook runner into
    the real GateService (only the HTTP hop is skipped)."""
    _N["n"] += 1
    payload = _pre_tool_use(str(rig.worktree), command, tool_use_id=f"call_r3_{_N['n']}")

    def post(url, body, timeout):
        return 200, rig.gate.propose(principal, body)

    def get(url, timeout):
        return 200, rig.gate.get_proposal(principal, url.rsplit("/", 1)[-1])

    clock = {"t": 0.0}

    def sleep(seconds: float) -> None:
        clock["t"] += 10_000.0

    decision = run_hook(
        payload, config=load_gate_config(rig.gate_path), http_post=post, http_get=get,
        sleep=sleep, now=lambda: clock["t"], ttl_seconds=1.0, agent="codex",
    )
    return SimpleNamespace(decision=decision, proposal=rig.gate._db.gate.get(payload["tool_use_id"]))


def test_a_codex_launch_is_armed_and_carries_its_hooks(codex_launched) -> None:
    rig = codex_launched
    gate = json.loads(rig.gate_path.read_text(encoding="utf-8"))
    assert gate["repos"] == {str(rig.worktree): ["Bash"]} and gate["armed_paths"] == [str(rig.worktree)]
    spawn = next(c for c in rig.tmux.calls if c[1] == "new-session")
    command = spawn[spawn.index("-s") + 2]
    assert " exec codex --no-daemon -c " in command
    assert "gate hook --agent codex" in command and "--settings" not in command
    assert rig.launches.get(rig.launch_id)["session_key"] == "codex:smoke-session"


@pytest.mark.parametrize("identity", ["codex:smoke-session", "launch"])
def test_yolo_passes_a_codex_call_in_its_own_worktree(codex_launched, tmp_path, monkeypatch, identity) -> None:
    """Inside a launch the hook authenticates with the launch credential its
    tmux session carries (``agent:launch:<id>``): that is its own launch too."""
    _mode(tmp_path, monkeypatch, "yolo")
    rig = codex_launched
    who = launch_identity(rig.launch_id) if identity == "launch" else identity
    call = _codex_call(rig, "pytest -q && git add -A", Principal(PrincipalKind.AGENT, who))
    assert call.decision.deny is None
    assert call.proposal.state == APPROVED and call.proposal.decided_by == "control-mode"
    assert call.proposal.operation["tool_call"]["launch_id"] == rig.launch_id


def test_secure_holds_every_codex_call(codex_launched, tmp_path, monkeypatch) -> None:
    _mode(tmp_path, monkeypatch, "safe")
    rig = codex_launched
    call = _codex_call(rig, "git status", Principal(PrincipalKind.AGENT, launch_identity(rig.launch_id)))
    assert call.proposal.state != APPROVED
    assert call.decision.deny  # the hold expired with no decision: denied, never allowed


def test_another_launchs_credential_is_not_this_launch(codex_launched, tmp_path, monkeypatch) -> None:
    _mode(tmp_path, monkeypatch, "yolo")
    rig = codex_launched
    call = _codex_call(rig, "ls", Principal(PrincipalKind.AGENT, launch_identity("launch_other")))
    assert call.proposal.operation["tool_call"]["launch_id"] == ""
    assert call.proposal.state in (HELD, "expired", "denied")


def test_an_untrusted_codex_launch_refuses_before_anything_runs(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    rig = _rig(tmp_path, db, monkeypatch, agent="codex")
    asked: list[list[str]] = []
    rig.service._codex_trust = lambda flags: asked.append(list(flags)) or ["/<session-flags>/config.toml:pre_tool_use:0:0"]
    from holdspeak.services.agent_hand_service import AgentHandRefused

    with pytest.raises(AgentHandRefused) as exc:
        rig.hand.hand(OWNER, "action", "ai_1", profile="codex-default")
    assert exc.value.reason == "codex_hooks_untrusted"
    assert asked and asked[0] == coder_gate.codex_hook_flags(coder_gate.spawn_prefix())
    assert not rig.worktree.exists()
    assert not any(c[1] == "new-session" for c in rig.tmux.calls)
    held = json.loads(rig.gate_path.read_text())["repos"] if rig.gate_path.exists() else {}
    assert held == {}  # nothing armed, or the arm released


# ── 4. Codex's start: folder trust once, never hooks review, then the brief ──


def test_the_codex_trust_screen_matches_only_its_exact_worktree() -> None:
    path = "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-1/work/hs-action-ai_1"
    lines = _trust_screen(path).split("\n")
    assert first_message.codex_trust_prompt_for(lines, path)["cursor"] == "yes"
    assert first_message.codex_trust_prompt_for(lines, path + "0") is None
    assert first_message.codex_trust_prompt_for(lines, path[:-1]) is None
    other = _trust_screen(path, cursor_on_yes=False).split("\n")
    assert first_message.codex_trust_prompt_for(other, path)["cursor"] == "other"
    # A screen left in the scrollback is not live.
    assert first_message.parse_codex_trust_prompt((_trust_screen(path) + COMPOSER).split("\n")) is None


def test_only_the_composer_is_ready() -> None:
    assert first_message.codex_ready(COMPOSER.split("\n"))
    assert not first_message.codex_ready(_trust_screen("/tmp/x").split("\n"))
    assert not first_message.codex_ready(HOOKS_REVIEW.split("\n"))
    assert not first_message.codex_ready("OpenAI Codex\nLoading the model...".split("\n"))


def test_codex_trust_is_answered_once_and_the_brief_goes_on_the_composer(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    """Codex fires no hook before its first prompt: the brief is typed when
    the composer shows, and the session registers after it."""
    typed_once = {"done": False}
    rig = _rig(tmp_path, db, monkeypatch, agent="codex",
               screen=lambda worktree: _trust_screen(str(worktree)),
               register_when=lambda tmux: typed_once["done"])

    def on_keys(pane, keys):
        if keys == ["Enter"]:
            rig.tmux.meta[pane]["content"] = COMPOSER

    rig.tmux.on_keys = on_keys
    original = rig.text_transport

    def text_transport(*, pane, text, submit=True):
        original(pane=pane, text=text, submit=submit)
        typed_once["done"] = True

    rig.commands.processor._text_transport = text_transport
    result = rig.hand.hand(OWNER, "action", "ai_1", profile="codex-default")
    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "state", "registered")
    rig.tmux.ended = True
    assert [key for _pane, keys in rig.keys_sent for key in keys] == ["Enter"]
    assert record["trust_state"] == "answered" and record["commands"]["trust"]
    assert len(rig.typed) == 1 and record["session_key"] == "codex:smoke-session"


def test_hooks_review_is_never_answered(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    rig = _rig(tmp_path, db, monkeypatch, agent="codex", screen=lambda worktree: HOOKS_REVIEW,
               register_when=lambda tmux: False)
    result = rig.hand.hand(OWNER, "action", "ai_1", profile="codex-default")
    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "trust_state", "hooks_review")
    import time

    time.sleep(0.3)
    rig.tmux.ended = True
    assert rig.keys_sent == [] and rig.typed == []
    assert record["instruction_state"] == "pending"


def test_the_submit_waits_for_codex_paste_handling(monkeypatch) -> None:
    import holdspeak.tmux_transport as transport

    events: list[Any] = []
    monkeypatch.setattr(transport.shutil, "which", lambda _name: "/usr/bin/tmux")
    monkeypatch.setattr(transport.subprocess, "run", lambda cmd, **_kw: events.append(cmd[-1])
                        or SimpleNamespace(returncode=0, stdout="", stderr=""))
    monkeypatch.setattr(transport.time, "sleep", lambda s: events.append(("sleep", s)))
    transport.send_text_to_pane(pane="%1", text="line one\nline two")
    assert events == ["line one\nline two", ("sleep", transport.SUBMIT_PAUSE_SECONDS), "\r"]
    assert transport.SUBMIT_PAUSE_SECONDS >= 0.1  # Codex 0.159 swallowed a \r sent at once


# ── 5. Codex waits: Needs you and the responder ──────────────────────


def test_a_codex_permission_request_is_a_wait_to_approve(tmp_path) -> None:
    state = tmp_path / "agents.json"
    cwd = str(tmp_path)
    ingest_agent_hook_event(agent="codex", payload=_pre_tool_use(cwd, "touch perm.txt"), state_path=state, env={})
    session = ingest_agent_hook_event(agent="codex", payload=_permission_request(cwd), state_path=state, env={})
    assert is_blocked(session) and wait_kind(session) == "approve"
    assert "outside the sandbox" in session.question
    rows = coder_items([session])
    assert [row["why"] for row in rows] == [TO_APPROVE] and rows[0]["waitKind"] == "approve"
    # Codex runs the call: the wait ends.
    after = ingest_agent_hook_event(agent="codex", payload={**_pre_tool_use(cwd, "touch perm.txt"),
                                                            "hook_event_name": "PostToolUse"},
                                    state_path=state, env={})
    assert not is_blocked(after)


def test_a_codex_turn_end_is_a_wait_to_answer(tmp_path) -> None:
    state = tmp_path / "agents.json"
    cwd = str(tmp_path)
    session = ingest_agent_hook_event(
        agent="codex", payload=_stop(cwd, "Tests pass. Should I open the pull request now?"),
        state_path=state, env={},
    )
    assert is_blocked(session) and wait_kind(session) == "answer"
    assert session.question == "Tests pass. Should I open the pull request now?"
    assert [row["why"] for row in coder_items([session])] == [TO_ANSWER]
    resumed = ingest_agent_hook_event(
        agent="codex", payload={"session_id": SID, "cwd": cwd, "hook_event_name": "UserPromptSubmit",
                                "prompt": "Yes."},
        state_path=state, env={},
    )
    assert not is_blocked(resumed)


def test_the_responder_never_answers_a_codex_permission_request(tmp_path) -> None:
    from holdspeak.services.agent_responder import AgentResponder

    state = tmp_path / "agents.json"
    session = ingest_agent_hook_event(agent="codex", payload=_permission_request(str(tmp_path)),
                                      state_path=state, env={})
    key = f"codex:{SID}"
    responder = AgentResponder.__new__(AgentResponder)
    responder._launch_for = lambda k: {"launch_id": "launch_x"}
    assert responder._triage_one(key, session, "yolo") == "notify"


# ── 6. trust: only HoldSpeak's hooks, through Codex's own writer ─────


_FAKE_CODEX = r'''#!PYTHON
"""A fake codex app-server: hooks/list and config/batchWrite over JSON-RPC
stdio. Session-flag hooks come from its own -c hooks.<Event>=... argv."""
import hashlib, json, os, re, sys, tomllib
state_path = os.environ["FAKE_CODEX_STATE"]
def load():
    with open(state_path) as f: return json.load(f)
def save(s):
    with open(state_path, "w") as f: json.dump(s, f)
args = sys.argv[1:]
if not args or args[0] != "app-server":
    sys.exit(2)
st = load(); st.setdefault("runs", []).append(args); save(st)
snake = lambda e: re.sub(r"(?<!^)(?=[A-Z])", "_", e).lower()
flag_hooks = []
it = iter(args[1:])
for a in it:
    if a == "-c":
        key, _, raw = next(it).partition("=")
        if key.startswith("hooks."):
            event = key[len("hooks."):]
            for g, group in enumerate(tomllib.loads("v = " + raw)["v"]):
                for h, handler in enumerate(group["hooks"]):
                    ident = json.dumps([event, group.get("matcher"), handler], sort_keys=True)
                    flag_hooks.append({"key": f"/<session-flags>/config.toml:{snake(event)}:{g}:{h}",
                                       "command": handler["command"], "source": "sessionFlags",
                                       "currentHash": "sha256:" + hashlib.sha256(ident.encode()).hexdigest()})
for line in sys.stdin:
    msg = json.loads(line)
    if "id" not in msg:
        continue
    st = load(); method = msg["method"]
    if method == "initialize":
        result = {"userAgent": "fake"}
    elif method == "hooks/list":
        hooks = [dict(h, trustStatus="trusted" if st["trusted"].get(h["key"]) == h["currentHash"] else "untrusted")
                 for h in st["file_hooks"] + flag_hooks]
        result = {"data": [{"cwd": msg["params"]["cwds"][0], "hooks": hooks, "warnings": [], "errors": []}]}
    elif method == "config/batchWrite":
        for edit in msg["params"]["edits"]:
            st.setdefault("edits", []).append(edit)
            m = re.fullmatch(r'hooks\.state\."((?:[^"\\]|\\.)*)"\.trusted_hash', edit["keyPath"])
            key = re.sub(r"\\(.)", r"\1", m.group(1))
            st["trusted"][key] = edit["value"]
        save(st)
        result = {"status": "ok"}
    else:
        print(json.dumps({"id": msg["id"], "error": {"message": "unknown method"}}), flush=True)
        continue
    print(json.dumps({"id": msg["id"], "result": result}), flush=True)
'''

OURS = f"{PREFIX} agent-hook ingest --agent codex"
FOREIGN = "/usr/local/bin/my-own-hook"


def make_fake_codex(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """A fake ``codex`` on disk (the process boundary) and its state file."""
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir()
    exe = bin_dir / "codex"
    exe.write_text(_FAKE_CODEX.replace("#!PYTHON", f"#!{sys.executable}"))
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    state = tmp_path / "fake-codex.json"
    hooks_json = "/home/u/.codex/hooks.json"
    state.write_text(json.dumps({"trusted": {}, "file_hooks": [
        {"key": f"{hooks_json}:stop:0:0", "command": FOREIGN, "source": "user", "currentHash": "sha256:f1"},
        {"key": f"{hooks_json}:stop:1:0", "command": OURS, "source": "user", "currentHash": "sha256:o1"},
        {"key": f'{hooks_json}:with"quote:0:0', "command": OURS, "source": "user", "currentHash": "sha256:o2"},
    ]}))
    monkeypatch.setenv("FAKE_CODEX_STATE", str(state))
    return SimpleNamespace(exe=str(exe), state=state, read=lambda: json.loads(state.read_text()))


@pytest.fixture
def fake_codex(tmp_path, monkeypatch):
    return make_fake_codex(tmp_path, monkeypatch)


def test_trust_writes_only_holdspeak_hooks(fake_codex, tmp_path) -> None:
    flags = coder_gate.codex_hook_flags(PREFIX)
    assert codex_trust.untrusted_launch_hooks(flags, cwd=str(tmp_path), executable=fake_codex.exe)
    summary = codex_trust.trust_holdspeak_hooks(flags, cwd=str(tmp_path), executable=fake_codex.exe)
    state = fake_codex.read()
    assert summary["untrusted"] == [] and summary["already"] == 0
    assert FOREIGN not in json.dumps(summary)
    assert "/home/u/.codex/hooks.json:stop:0:0" not in state["trusted"]  # the foreign hook stays untrusted
    assert state["trusted"]['/home/u/.codex/hooks.json:with"quote:0:0'] == "sha256:o2"  # key escaping
    assert all(e["mergeStrategy"] == "upsert" for e in state["edits"])
    assert codex_trust.untrusted_launch_hooks(flags, cwd=str(tmp_path), executable=fake_codex.exe) == []
    # Idempotent: a second press writes nothing new.
    again = codex_trust.trust_holdspeak_hooks(flags, cwd=str(tmp_path), executable=fake_codex.exe)
    assert again["trusted"] == [] and again["already"] == len(summary["trusted"])


def test_a_changed_launch_hook_is_untrusted_again(fake_codex, tmp_path) -> None:
    codex_trust.trust_holdspeak_hooks(coder_gate.codex_hook_flags(PREFIX), cwd=str(tmp_path), executable=fake_codex.exe)
    moved = coder_gate.codex_hook_flags("uv run --project /elsewhere holdspeak")
    assert codex_trust.untrusted_launch_hooks(moved, cwd=str(tmp_path), executable=fake_codex.exe)


def test_no_codex_is_a_named_failure(tmp_path) -> None:
    with pytest.raises(codex_trust.CodexTrustError) as exc:
        codex_trust.untrusted_launch_hooks([], cwd=str(tmp_path), executable=str(tmp_path / "absent"))
    assert exc.value.reason == "codex_unavailable"


# ── 7. the real Codex (isolated CODEX_HOME): list, trust, list ───────


@pytest.mark.skipif(shutil.which("codex") is None, reason="codex is not installed")
def test_the_real_codex_trusts_exactly_the_holdspeak_hooks(tmp_path, monkeypatch) -> None:
    home = tmp_path / "codex-home"
    home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(home))
    hooks = home / "hooks.json"
    hooks.write_text(json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": FOREIGN}]}]}}))
    install_agent_hooks(hooks, codex_hook_template())
    flags = coder_gate.codex_hook_flags(PREFIX)
    env = {**os.environ, "CODEX_HOME": str(home)}
    before = codex_trust.untrusted_launch_hooks(flags, cwd=str(tmp_path), env=env)
    assert len(before) == sum(len(e) for e in coder_gate.codex_spawn_hooks(PREFIX)["hooks"].values())
    summary = codex_trust.trust_holdspeak_hooks(flags, cwd=str(tmp_path), env=env)
    assert summary["untrusted"] == []
    assert codex_trust.untrusted_launch_hooks(flags, cwd=str(tmp_path), env=env) == []
    listed = codex_trust.list_hooks(flags, cwd=str(tmp_path), env=env)
    foreign = [h for h in listed if h["command"] == FOREIGN]
    assert foreign and all(h["trustStatus"] != "trusted" for h in foreign)
    config = tomllib.loads((home / "config.toml").read_text())
    assert all(
        codex_trust.is_holdspeak_hook(next(h for h in listed if h["key"] == key))
        for key in config["hooks"]["state"]
    )
