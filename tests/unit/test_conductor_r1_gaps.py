"""Conductor R1, the real-use gaps the real loop found (coordinator plan B).

1. In YOLO and Normal a launched Claude edits its worktree with no prompt in
   the pane; Secure is unchanged.
2. A held gate call of a HoldSpeak launch is in Needs you (TO APPROVE).
3. A steer carries only what the owner attached: text that names an item
   pulls nothing in.
"""
from __future__ import annotations

import pytest

from tests.unit.test_web_routes_coders_steer import (  # noqa: F401  (env is a fixture)
    _pin_identity,
    _register,
    _seed_meeting,
    _session,
    env,
)


# ── 3. a steer grounds only what was attached ────────────────────────


def _steer(env, body: dict) -> str:  # noqa: F811
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch)
    env.client.post("/api/coders/claude:abc/arm", json={})
    res = env.client.post("/api/coders/claude:abc/steer", json={"submit": False, **body})
    assert res.status_code == 200, res.json()
    assert res.json()["status"] == "delivered"
    return env.sent[-1]["text"]


@pytest.mark.parametrize("grounding", [
    None,  # nothing attached
    {"meeting_ids": [], "artifact_ids": [], "refs": [], "expand": "summary"},  # an empty pick
])
def test_a_steer_that_names_an_item_pulls_nothing_in(env, grounding) -> None:  # noqa: F811
    """On the real desk a one-line answer that named action:<id> reached the
    agent with five grounded objects (memory recall over the text)."""
    mid = _seed_meeting(env.db)
    text = f"verify; see meeting:{mid} about the ship Friday decision (Kickoff)"
    body = {"text": text} if grounding is None else {"text": text, "grounding": grounding}
    sent = _steer(env, body)
    assert sent == text
    assert "--- from" not in sent and "grounded" not in sent
    assert env.db.steering.list()[0].grounding == []


def test_an_attached_ref_still_rides_along(env) -> None:  # noqa: F811
    mid = _seed_meeting(env.db)
    sent = _steer(env, {"text": "verify", "grounding": {"meeting_ids": [mid]}})
    assert '--- from meeting: "Kickoff"' in sent
    assert sent.rstrip().endswith("(1 object grounded)")


# ── 1. Normal and YOLO accept edits in the worktree ──────────────────

import shlex  # noqa: E402

from holdspeak.delivery import agent_mcp  # noqa: E402
from tests.unit.test_agent_hand import OWNER, _rig, _wait_for, db  # noqa: E402,F401  (db is a fixture)
from tests.unit.test_conductor_k6_agent_mcp import _spawn  # noqa: E402


@pytest.mark.parametrize("mode, accept", [("yolo", True), ("neutral", True), ("safe", False), ("Secure", False)])
def test_a_launched_claude_accepts_edits_in_normal_and_yolo(tmp_path, db, monkeypatch, mode, accept) -> None:  # noqa: F811
    """On the real desk every Edit of a launched Claude asked in the pane
    ("Do you want to make this edit to RUNBOOK.md?"), a TO APPROVE row per
    file change, in YOLO too."""
    rig = _rig(tmp_path / "rig", db, monkeypatch)
    rig.service._control_mode = lambda: mode
    result = rig.hand.hand(OWNER, "action", "ai_1")
    assert result["status"] == "launched", result
    _argv, command = _spawn(rig)
    agent_argv = shlex.split(command.split(" exec ", 1)[1])
    if accept:
        assert agent_argv[agent_argv.index("--permission-mode") + 1] == "acceptEdits"
        assert agent_argv.count("--permission-mode") == 1
    else:
        assert "--permission-mode" not in agent_argv
    # The tool gate still decides Bash; the allow list is last and unchanged.
    assert agent_argv[agent_argv.index("--allowedTools") + 1] == "Bash"
    _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    rig.tmux.ended = True


def test_a_permission_mode_the_launch_names_is_kept() -> None:
    assert agent_mcp.claude_permission_args("yolo", ["claude", "--permission-mode", "plan"]) == []
    assert agent_mcp.claude_permission_args("yolo", ["claude"]) == ["--permission-mode", "acceptEdits"]


# ── 2. a held call of a launch is in Needs you (TO APPROVE) ──────────

from holdspeak.db.gate import APPROVED, HELD  # noqa: E402
from holdspeak.principals import Principal, PrincipalKind  # noqa: E402
from holdspeak.services.needs_you_membership import (  # noqa: E402
    TO_APPROVE,
    _read_gate_holds,
    compute_needs_you,
)
from tests.unit.test_conductor_k5_supervision import AGENT, _call, _mode, launched  # noqa: E402,F401


def _gate_rows(rig) -> list[dict]:
    holds = _read_gate_holds(rig.db, ledger=rig.launches)
    return [row for row in compute_needs_you(gate_holds=holds)["unmutedItems"] if row["kind"] == "gate"]


def test_a_held_call_of_a_launch_is_a_to_approve_row_and_notifies(launched, tmp_path, monkeypatch) -> None:  # noqa: F811
    """On the real desk `ls /private/tmp/r1w` waited 240 s for the owner and
    Needs you showed nothing."""
    _mode(tmp_path, monkeypatch, "yolo")
    edges: list[str] = []
    launched.gate._on_launch_hold = edges.append
    held = _call(launched, "ls /etc")
    assert held.proposal.state == HELD
    rows = _gate_rows(launched)
    assert [row["id"] for row in rows] == [f"gate:{held.proposal.id}"]
    row = rows[0]
    assert row["why"] == TO_APPROVE and row["openRef"] == f"gate:{held.proposal.id}"
    assert row["title"] == "Approve: ls /etc"
    assert row["launchId"] == launched.launch_id and row["sessionKey"] == AGENT.identity
    assert edges == [f"gate:{held.proposal.id}"]  # the K3 immediate edge, once

    # A call the mode passes is neither a row nor an edge.
    passed = _call(launched, "git status")
    assert passed.proposal.state == APPROVED
    assert [r["id"] for r in _gate_rows(launched)] == [f"gate:{held.proposal.id}"]
    assert len(edges) == 1

    # Decided by the owner: the row goes.
    launched.gate.decide(Principal(PrincipalKind.OWNER, "owner"), held.proposal.id, {"decision": "denied"})
    assert _gate_rows(launched) == []


def test_a_hold_that_is_no_launchs_is_not_a_row(launched, tmp_path, monkeypatch) -> None:  # noqa: F811
    _mode(tmp_path, monkeypatch, "yolo")
    edges: list[str] = []
    launched.gate._on_launch_hold = edges.append
    other = Principal(PrincipalKind.AGENT, "claude:owner-terminal")
    held = _call(launched, "ls /etc", principal=other)
    assert held.proposal.state == HELD
    assert _gate_rows(launched) == [] and edges == []


def test_an_expired_hold_is_not_a_row(launched, tmp_path, monkeypatch) -> None:  # noqa: F811
    _mode(tmp_path, monkeypatch, "yolo")
    held = _call(launched, "ls /etc")
    holds = _read_gate_holds(launched.db, ledger=launched.launches, now=held.proposal.expires_at + 1)
    assert [h["held"] for h in holds] == [False]  # kept only to correlate a wait
    assert [r for r in compute_needs_you(gate_holds=holds)["unmutedItems"] if r["kind"] == "gate"] == []


# ── Astra round 1 on #916 ─────────────────────────────────────────────

import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from pathlib import Path  # noqa: E402
from types import SimpleNamespace  # noqa: E402
from unittest.mock import patch  # noqa: E402

import holdspeak.tmux_transport as tmux_transport  # noqa: E402
from holdspeak import coder_gate  # noqa: E402
from holdspeak.agent_context import list_agent_sessions  # noqa: E402
from holdspeak.agent_context.sessions import ingest_agent_hook_event  # noqa: E402
from holdspeak.coder_gate import load_gate_config, run_hook  # noqa: E402
from holdspeak.tool_gate_rules import EDIT_TOOLS, INSIDE, OUTSIDE, classify_edit  # noqa: E402


# 1. [P1] file writes are kept to the worktree by the gate


def test_a_write_is_read_against_the_resolved_worktree(tmp_path) -> None:
    worktree = tmp_path / "wt"
    (worktree / "src").mkdir(parents=True)
    extra = tmp_path / "additional-dir"  # a folder Claude's settings also allow
    extra.mkdir()
    (worktree / "escape").symlink_to(extra)  # an escaping folder link
    (worktree / "leaf.txt").symlink_to(extra / "secret.txt")  # an escaping (dangling) file link
    root = str(worktree)
    inside = {
        str(worktree / "RUNBOOK.md"): "absolute, existing folder",
        "src/new/deep/file.py": "relative, folders not yet made",
    }
    for path in inside:
        assert classify_edit({"file_path": path}, cwd=root, root=root).scope == INSIDE, path
    outside = [
        str(extra / "notes.md"),            # an additional directory
        "escape/notes.md",                  # through a folder symlink
        "escape/new/dir/x.md",              # through it, target not yet there
        "leaf.txt",                         # a file symlink out
        "../additional-dir/notes.md",       # dot-dot
    ]
    for path in outside:
        assert classify_edit({"file_path": path}, cwd=root, root=root).scope == OUTSIDE, path
    assert classify_edit({"notebook_path": str(extra / "n.ipynb")}, cwd=root, root=root).scope == OUTSIDE
    assert classify_edit({}, cwd=root, root=root).scope == "unparsed"


def test_the_launch_settings_put_file_writes_on_the_gate() -> None:
    settings = coder_gate.spawn_settings("holdspeak")
    matchers = {entry.get("matcher") for entry in settings["hooks"]["PreToolUse"]}
    assert "Bash" in matchers
    edit = next(m for m in matchers if m and "Edit" in m)
    assert set(edit.split("|")) == EDIT_TOOLS


def _write(rig, tool: str, path: str, principal=AGENT):  # noqa: F811
    """One file-write PreToolUse arrival through the real hook runner and
    the real GateService (the K5 rig's _call, for a write)."""
    tool_input = {"notebook_path": path} if tool == "NotebookEdit" else {"file_path": path, "content": "x"}
    payload = {
        "hook_event_name": "PreToolUse", "session_id": principal.identity.split(":", 1)[-1],
        "tool_name": tool, "tool_use_id": f"toolu_w{time.monotonic_ns()}",
        "tool_input": tool_input, "cwd": str(rig.worktree),
    }
    clock = {"t": 0.0}

    def sleep(_s: float) -> None:
        clock["t"] += 10_000.0

    decision = run_hook(
        payload, config=load_gate_config(rig.gate_path),
        http_post=lambda url, body, timeout: (200, rig.gate.propose(principal, body)),
        http_get=lambda url, timeout: (200, rig.gate.get_proposal(principal, url.rsplit("/", 1)[-1])),
        sleep=sleep, now=lambda: clock["t"], ttl_seconds=1.0,
    )
    return SimpleNamespace(decision=decision, proposal=rig.gate._db.gate.get(payload["tool_use_id"]))


@pytest.mark.parametrize("mode, inside_passes", [("yolo", True), ("neutral", True), ("safe", False)])
def test_a_launchs_write_outside_its_worktree_is_held_in_every_mode(launched, tmp_path, monkeypatch, mode, inside_passes) -> None:  # noqa: F811
    """Astra on #916: acceptEdits also accepts edits in Claude's additional
    directories, and the gate read Bash only: an outside Write raised no
    gate request at all."""
    _mode(tmp_path, monkeypatch, mode)
    extra = tmp_path / "additional-dir"
    extra.mkdir()
    (launched.worktree / "escape").symlink_to(extra)
    for tool, path in (("Write", str(extra / "x.md")), ("Edit", "escape/x.md"), ("NotebookEdit", str(extra / "n.ipynb"))):
        call = _write(launched, tool, path)
        assert call.proposal is not None and call.proposal.state == HELD, (tool, path)
        assert call.decision.deny is not None
    inside = _write(launched, "Edit", str(launched.worktree / "RUNBOOK.md"))
    assert inside.proposal is not None
    if inside_passes:
        assert inside.proposal.state == APPROVED and inside.decision.deny is None
        assert inside.proposal.operation["tool_call"]["rule"] == "edit_in_worktree"
    else:
        assert inside.proposal.state == HELD


# 4. [P2] the equals form of the permission flag is a named mode


def test_an_equals_form_permission_mode_is_kept(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    """A stored profile ["--permission-mode=plan"] got an extra
    --permission-mode acceptEdits."""
    from holdspeak.delivery.factory_launch import AGENT_PROFILES_SCHEMA

    rig_dir = tmp_path / "rig"
    rig_dir.mkdir()
    (rig_dir / "profiles.json").write_text(json.dumps({
        "agent_profiles_schema": AGENT_PROFILES_SCHEMA,
        "profiles": [{"profile_id": "claude-default", "label": "Claude Code", "executable": "claude",
                      "args": ["--permission-mode=plan"], "option_slots": {}}],
    }), encoding="utf-8")
    rig = _rig(rig_dir, db, monkeypatch)
    rig.service._control_mode = lambda: "yolo"
    result = rig.hand.hand(OWNER, "action", "ai_1")
    assert result["status"] == "launched", result
    _argv, command = _spawn(rig)
    agent_argv = shlex.split(command.split(" exec ", 1)[1])
    modes = [t for t in agent_argv if t == "--permission-mode" or t.startswith("--permission-mode=")]
    assert modes == ["--permission-mode=plan"]
    _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    rig.tmux.ended = True
    assert agent_mcp.claude_permission_args("yolo", ["claude", "--permission-mode=default"]) == []


# 2. [P1] typed text carries no terminal control: the bytes a real pane gets


@pytest.fixture
def real_pane(monkeypatch):
    if shutil.which("tmux") is None:
        pytest.skip("tmux is not installed")
    sock = tempfile.mkdtemp(prefix="r1t", dir="/tmp")
    monkeypatch.setenv("TMUX_TMPDIR", sock)
    monkeypatch.delenv("TMUX", raising=False)
    out = Path(sock) / "out.bin"
    subprocess.run(["tmux", "new-session", "-d", "-s", "r1t", "-x", "200", "-y", "50",
                    f"stty raw -echo; exec cat > {out}"], check=True)
    pane = subprocess.run(["tmux", "list-panes", "-t", "r1t", "-F", "#{pane_id}"],
                          capture_output=True, text=True, check=True).stdout.strip()
    time.sleep(0.5)  # stty has run
    yield SimpleNamespace(pane=pane, out=out)
    subprocess.run(["tmux", "kill-server"], check=False)
    shutil.rmtree(sock, ignore_errors=True)


def _received(out: Path, want: bytes, *, wait: float = 3.0) -> bytes:
    end = time.monotonic() + wait
    data = b""
    while time.monotonic() < end:
        data = out.read_bytes() if out.exists() else b""
        if data == want:
            break
        time.sleep(0.05)
    return data


def test_a_real_pane_gets_exactly_the_plain_text(real_pane) -> None:
    text = "Line one\r\nLine\ttwo ü — 你好\nlast"
    tmux_transport.send_text_to_pane(pane=real_pane.pane, text=text, submit=False)
    want = "Line one\nLine\ttwo ü — 你好\nlast".encode()
    assert _received(real_pane.out, want) == want


@pytest.mark.parametrize("text", [
    "brief\x1b[201~\x03rm -rf ~\r",   # an embedded paste terminator, Ctrl-C and CR
    "one line\x1b[200~",              # the opening bracket
    "two\nlines\x03",                 # Ctrl-C in a pasted text
    "c\rd",                           # a lone CR
    "x\x7fy",                         # DEL
    "x\u009by",                       # C1 CSI
])
def test_a_control_in_the_text_is_refused_and_nothing_reaches_the_pane(real_pane, text) -> None:
    with pytest.raises(tmux_transport.TmuxTransportError, match="terminal control"):
        tmux_transport.send_text_to_pane(pane=real_pane.pane, text=text, submit=True)
    with pytest.raises(tmux_transport.TmuxTransportError, match="terminal control"):
        tmux_transport.send_keys_to_pane(pane=real_pane.pane, keys=[("named", "Down"), ("literal", text)])
    time.sleep(0.5)
    assert real_pane.out.read_bytes() == b""


# 3. [P2] a held call and the same session's permission wait are one ask


def test_a_held_call_and_its_permission_wait_are_one_row_one_notification(launched, tmp_path, monkeypatch) -> None:  # noqa: F811
    _mode(tmp_path, monkeypatch, "yolo")
    state = tmp_path / "sessions.json"
    session = AGENT.identity.split(":", 1)[1]
    base = {"session_id": session, "cwd": str(launched.worktree)}
    held = _call(launched, "ls /etc")  # the real gate producer
    ingest_agent_hook_event(  # the real hook producer: the same session's permission wait
        agent="claude", state_path=state,
        payload={**base, "hook_event_name": "Notification", "notification_type": "permission_prompt",
                 "message": "Claude needs your permission to use Bash"},
    )
    pid = held.proposal.id

    def rows():
        holds = _read_gate_holds(launched.db, ledger=launched.launches)
        result = compute_needs_you(coders=list_agent_sessions(state_path=state), gate_holds=holds)
        return [r for r in result["unmutedItems"] if r["kind"] in ("gate", "coder")], result

    from tests.unit.test_conductor_k3_coder_needs_you import _Clock, _service

    calls: list = []
    noon = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
    svc = _service(launched.db, calls, _Clock(noon))

    def edge() -> dict:
        def build(principal=None):
            current, result = rows()
            return {"count": result["count"], "projects": [], "items": result["unmutedItems"],
                    "members": result["members"], "coverage": [], "complete": True}
        with patch.object(svc, "_build_aggregate_via_canonical", side_effect=build):
            return svc.notify_coder_edge(OWNER, session_key=AGENT.identity)

    current, _ = rows()
    assert [(r["id"], r["why"], r["notifyKey"]) for r in current] == [(f"gate:{pid}", TO_APPROVE, f"gate:{pid}")]
    assert edge()["outcome"] == "sent"
    assert edge()["outcome"] == "held_no_edge"

    # Decided: the permission wait that began during the hold keeps its identity.
    launched.gate.decide(Principal(PrincipalKind.OWNER, "owner"), pid, {"decision": "approved"})
    current, _ = rows()
    assert [(r["kind"], r["notifyKey"]) for r in current] == [("coder", f"gate:{pid}")]
    assert edge()["outcome"] == "held_no_edge"
    assert len(calls) == 1

    # An independent question stays its own row and notifies.
    ingest_agent_hook_event(agent="claude", state_path=state, payload={**base, "hook_event_name": "UserPromptSubmit", "prompt": "go"})
    ingest_agent_hook_event(agent="claude", state_path=state, payload={
        **base, "hook_event_name": "Stop", "last_assistant_message": "Restart or reboot?"})
    current, _ = rows()
    assert [r["why"] for r in current] == ["TO ANSWER"] and current[0]["notifyKey"] != f"gate:{pid}"
    assert edge()["outcome"] == "sent" and len(calls) == 2


# ── Astra round 2 on #916: her five probes, as fences ─────────────────


@pytest.mark.parametrize("mode", ["neutral", "yolo"])
@pytest.mark.parametrize("parts", [
    ("link", "..", "sentinel.txt"),                      # her probe
    ("link", "..", "new", "deeper", "sentinel.txt"),     # not-yet-existing tail after the escape
    ("sub", "link2", "..", "..", "sentinel.txt"),        # a link in a nested folder
    ("link", "inner", "..", "..", "sentinel.txt"),       # through the link, down, then up twice
])
def test_a_symlink_then_dotdot_write_is_held(launched, tmp_path, monkeypatch, mode, parts) -> None:  # noqa: F811
    """`wt/link/../sentinel.txt` with link -> outside/subdir was read as
    inside (abspath collapsed `..` before the link was resolved); Normal and
    YOLO approved it and the write reached outside/sentinel.txt."""
    _mode(tmp_path, monkeypatch, mode)
    outside = tmp_path / "outside"
    (outside / "subdir" / "inner").mkdir(parents=True)
    (outside / "subdir" / "deeper").mkdir(parents=True)
    (launched.worktree / "link").symlink_to(outside / "subdir")
    (launched.worktree / "sub").mkdir()
    (launched.worktree / "sub" / "link2").symlink_to(outside / "subdir" / "inner")
    target = Path(launched.worktree, *parts)
    assert not str(Path(os.path.realpath(target))).startswith(str(Path(os.path.realpath(launched.worktree))))
    call = _write(launched, "Write", str(target))
    assert call.proposal.state == HELD, call.proposal.operation["tool_call"]
    assert call.decision.deny is not None


def test_a_dotdot_that_stays_inside_still_passes(launched, tmp_path, monkeypatch) -> None:  # noqa: F811
    _mode(tmp_path, monkeypatch, "yolo")
    (launched.worktree / "a" / "b").mkdir(parents=True)
    call = _write(launched, "Write", str(launched.worktree / "a" / "b" / ".." / "x.md"))
    assert call.proposal.state == APPROVED


def test_literal_keys_are_sent_normalized(real_pane) -> None:
    """A real pane received b'first\\r\\nsecond': the run was checked, then
    the original was sent."""
    tmux_transport.send_keys_to_pane(pane=real_pane.pane, keys=[("literal", "first\r\nsecond")])
    assert _received(real_pane.out, b"first\nsecond") == b"first\nsecond"


@pytest.mark.parametrize("previous", ["automatic", "owner_decided"])
def test_a_recent_approval_cannot_take_a_new_holds_wait(launched, tmp_path, monkeypatch, previous) -> None:  # noqa: F811
    """An approval, a new hold 0.4 s later and its permission wait 0.3 s
    after that gave two rows and two notifications."""
    _mode(tmp_path, monkeypatch, "yolo")
    now = {"t": time.time()}
    monkeypatch.setattr(launched.db.gate, "_now", lambda: now["t"])
    old = _call(launched, "git status" if previous == "automatic" else "ls /etc")
    if previous == "owner_decided":
        launched.gate.decide(OWNER, old.proposal.id, {"decision": "approved"})
    now["t"] += 0.4
    held = _call(launched, "cat /etc/hosts")
    assert held.proposal.state == HELD
    state = tmp_path / "sessions.json"
    calls: list = []
    from tests.unit.test_conductor_k3_coder_needs_you import _Clock, _service

    svc = _service(launched.db, calls, _Clock(datetime.now(timezone.utc).replace(hour=12)))

    def rows():
        holds = _read_gate_holds(launched.db, ledger=launched.launches, now=now["t"])
        return compute_needs_you(coders=list_agent_sessions(state_path=state), gate_holds=holds,
                                 now=datetime.fromtimestamp(now["t"], timezone.utc))

    def edge():
        def build(principal=None):
            result = rows()
            return {"count": result["count"], "projects": [], "items": result["unmutedItems"],
                    "members": result["members"], "coverage": [], "complete": True}
        with patch.object(svc, "_build_aggregate_via_canonical", side_effect=build):
            return svc.notify_coder_edge(OWNER, session_key=AGENT.identity)

    assert edge()["outcome"] == "sent"
    now["t"] += 0.3
    ingest_agent_hook_event(agent="claude", state_path=state, now=datetime.fromtimestamp(now["t"], timezone.utc), payload={
        "session_id": AGENT.identity.split(":", 1)[1], "cwd": str(launched.worktree),
        "hook_event_name": "Notification", "notification_type": "permission_prompt",
        "message": "Claude needs your permission to use Bash"})
    current = [(r["kind"], r["notifyKey"]) for r in rows()["unmutedItems"]]
    assert (current, edge()["outcome"], len(calls)) == ([("gate", f"gate:{held.proposal.id}")], "held_no_edge", 1)
