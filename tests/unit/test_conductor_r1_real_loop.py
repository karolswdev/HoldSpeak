"""Conductor R1: what the real loop with real Claude Code and real Codex broke.

Each test pins one defect found on the owner's machine (2026-10-06) with
Claude Code 2.1.288 and Codex 0.159.0 launched by the real hub: the walk log
is in the R1 pull request. Producers are the product's own (the K2 rig, the
real gate service, the real hook ingest); tmux and the agents are faked only
at the process edge.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

import holdspeak.tmux_transport as tmux_transport
from holdspeak.agent_context import hooks as agent_hooks
from holdspeak.agent_context.models import is_blocked
from holdspeak.agent_context.sessions import ingest_agent_hook_event
from holdspeak.coder_factory import launch_identity
from holdspeak.db.gate import APPROVED, HELD
from holdspeak.delivery import agent_mcp
from holdspeak.delivery.first_message import codex_screen_ready
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.agent_hand_service import codex_hooks_installed
from holdspeak.services.gate_service import _is_launch_caller
from holdspeak.services.needs_you_membership import TO_ANSWER, coder_items
from tests.unit.test_agent_hand import OWNER, _rig, _wait_for, db  # noqa: F401  (db is a fixture)
from tests.unit.test_conductor_k5_supervision import _call, _mode, launched  # noqa: F401  (launched is a fixture)


# ── 1. the gate knows a launched agent by its launch credential ──────


def test_the_launch_credential_is_the_launchs_own_caller(launched, tmp_path, monkeypatch) -> None:  # noqa: F811
    """K6 puts HOLDSPEAK_AGENT_CREDENTIAL (agent:launch:<id>) in the pane's
    environment, and the gate hook sends that credential first. On the real
    desk every Bash call of a YOLO launch waited as not_a_holdspeak_launch."""
    _mode(tmp_path, monkeypatch, "yolo")
    caller = Principal(PrincipalKind.AGENT, launch_identity(launched.launch_id))
    call = _call(launched, "git status", principal=caller)
    assert call.proposal.policy_snapshot["reason_code"] == "yolo_inside_own_worktree"
    assert call.proposal.state == APPROVED and call.proposal.decided_by == "control-mode"
    assert call.proposal.operation["tool_call"]["launch_id"] == launched.launch_id
    # The launch credential gets no wider scope: outside the worktree waits.
    outside = _call(launched, "ls /etc", principal=caller)
    assert outside.proposal.state == HELD
    assert outside.proposal.policy_snapshot["reason_code"] == "yolo_outside_own_worktree"


def test_another_launchs_credential_keeps_the_hold(launched, tmp_path, monkeypatch) -> None:  # noqa: F811
    _mode(tmp_path, monkeypatch, "yolo")
    stranger = Principal(PrincipalKind.AGENT, launch_identity("launch_someone_else"))
    call = _call(launched, "git status", principal=stranger)
    assert call.proposal.state == HELD
    assert call.proposal.policy_snapshot["reason_code"] == "not_a_holdspeak_launch"


def test_a_launch_credential_needs_the_registration_first() -> None:
    record = {"launch_id": "launch_1", "session_key": "", "state": "launched"}
    assert not _is_launch_caller(record, launch_identity("launch_1"))
    record["session_key"] = "claude:s1"
    assert _is_launch_caller(record, launch_identity("launch_1"))
    assert _is_launch_caller(record, "claude:s1")
    assert not _is_launch_caller(record, "claude:s2")
    assert not _is_launch_caller(record, launch_identity("launch_2"))


# ── 2. a question in the Stop payload is a wait (Needs you) ──────────


@pytest.mark.parametrize("agent", ["claude", "codex"])
def test_a_question_in_the_stop_payload_reaches_needs_you(tmp_path, agent) -> None:
    """Claude Code 2.1.288 and Codex 0.159 send the turn's last assistant
    message in the Stop payload. The launched agent's rider hooks do not opt
    in to transcript capture, so the agent's question never became a wait."""
    state = tmp_path / "sessions.json"
    base = {"session_id": "s1", "cwd": str(tmp_path)}
    ingest_agent_hook_event(agent=agent, payload={**base, "hook_event_name": "UserPromptSubmit", "prompt": "go"}, state_path=state)
    session = ingest_agent_hook_event(
        agent=agent,
        payload={
            **base, "hook_event_name": "Stop", "stop_hook_active": False,
            "last_assistant_message": "Step 2 done.\n\nWhich verb for the runbook line: restart or reboot?",
        },
        state_path=state,
    )
    record = session.to_dict()
    assert record["awaiting_response"] is True
    assert record["question"].endswith("Which verb for the runbook line: restart or reboot?")
    assert record["last_assistant_text"] is None  # only the question is kept
    assert is_blocked(record)
    rows = coder_items([record])
    assert [row["why"] for row in rows] == [TO_ANSWER]


def test_a_stop_without_a_question_is_not_a_wait(tmp_path) -> None:
    state = tmp_path / "sessions.json"
    session = ingest_agent_hook_event(
        agent="claude",
        payload={"session_id": "s1", "cwd": str(tmp_path), "hook_event_name": "Stop",
                 "last_assistant_message": "Done. PR created."},
        state_path=state,
    )
    assert session.to_dict()["awaiting_response"] is False
    assert coder_items([session]) == []


# ── 3. a brief is pasted whole, never typed in guessed chunks ────────


def _capture(monkeypatch: pytest.MonkeyPatch) -> list[tuple[list[str], object]]:
    calls: list[tuple[list[str], object]] = []
    monkeypatch.setattr(tmux_transport.shutil, "which", lambda _name: "/usr/bin/tmux")
    monkeypatch.setattr(
        tmux_transport.subprocess, "run",
        lambda cmd, **kwargs: calls.append((list(cmd), kwargs.get("input")))
        or SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    return calls


def test_a_multi_line_brief_is_one_bracketed_paste_then_cr(monkeypatch) -> None:
    """On the real desk the agent got only the last lines of the brief: typed
    with send-keys -l, Claude Code read it as several guessed paste chunks."""
    calls = _capture(monkeypatch)
    brief = "HoldSpeak hands you one item.\n\nStep 1.\nStep 2."
    tmux_transport.send_text_to_pane(pane="%3", text=brief, submit=True)
    (load, stdin), (paste, _), (enter, _) = calls
    buffer = load[load.index("-b") + 1]
    assert load == ["tmux", "load-buffer", "-b", buffer, "-"] and stdin == brief
    assert paste == ["tmux", "paste-buffer", "-p", "-r", "-d", "-b", buffer, "-t", "%3"]
    assert enter == ["tmux", "send-keys", "-t", "%3", "-l", "\r"]
    assert buffer.startswith("hs-")


def test_a_long_single_line_is_pasted_and_a_short_answer_is_typed(monkeypatch) -> None:
    calls = _capture(monkeypatch)
    tmux_transport.send_text_to_pane(pane="%3", text="x" * 201, submit=False)
    assert [cmd[1] for cmd, _ in calls] == ["load-buffer", "paste-buffer"]
    calls.clear()
    tmux_transport.send_text_to_pane(pane="%3", text="restart", submit=True)
    assert [cmd for cmd, _ in calls] == [
        ["tmux", "send-keys", "-t", "%3", "-l", "restart"],
        ["tmux", "send-keys", "-t", "%3", "-l", "\r"],
    ]


# ── 4. the hook runs the hub's own checkout, with time to start ──────


def test_the_hook_command_is_the_hubs_own_holdspeak(tmp_path, monkeypatch) -> None:
    """A holdspeak on PATH can be another checkout (~/.local/bin/holdspeak
    wrapping an older venv): the walk's one-press install wrote that one."""
    venv = tmp_path / "venv" / "bin"
    venv.mkdir(parents=True)
    own = venv / "holdspeak"
    own.write_text("#!/bin/sh\n", encoding="utf-8")
    own.chmod(0o755)
    monkeypatch.setattr(agent_hooks.sys, "executable", str(venv / "python"))
    monkeypatch.setattr(agent_hooks.shutil, "which", lambda _name: "/elsewhere/bin/holdspeak")
    assert agent_hooks.holdspeak_executable() == str(own)
    assert agent_hooks.claude_hook_template()["hooks"]["Stop"][0]["hooks"][0]["command"].startswith(str(own))
    own.unlink()
    assert agent_hooks.holdspeak_executable() == "/elsewhere/bin/holdspeak"


def test_the_rider_hooks_have_time_to_start(monkeypatch) -> None:
    """One ingest took 4 to 7 s on a loaded machine; Codex killed it at 5 s."""
    for template in (agent_hooks.claude_hook_template(), agent_hooks.codex_hook_template()):
        timeouts = {hook["timeout"] for entries in template["hooks"].values() for entry in entries for hook in entry["hooks"]}
        assert timeouts == {agent_hooks.HOOK_INGEST_TIMEOUT_SECONDS} and agent_hooks.HOOK_INGEST_TIMEOUT_SECONDS >= 30


# ── 5. Codex: CODEX_HOME, its startup screens, its readiness ─────────


def test_codex_hooks_are_read_where_codex_reads_them(tmp_path, monkeypatch) -> None:
    """The one-press install writes $CODEX_HOME/hooks.json; the launch read
    ~/.codex only and held the brief as hooks_missing."""
    home, codex_home = tmp_path / "home", tmp_path / "codexhome"
    home.mkdir()
    codex_home.mkdir()
    (codex_home / "hooks.json").write_text(
        json.dumps({"hooks": {"Stop": [{"hooks": [{"command": "holdspeak agent-hook ingest --agent codex"}]}]}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    assert codex_hooks_installed() is True
    monkeypatch.delenv("CODEX_HOME")
    assert codex_hooks_installed() is False


def test_codex_starts_with_no_screen_in_the_way(tmp_path) -> None:
    """Codex 0.159 asked "Trust this folder?" and then "Hooks need review"
    before its composer; nothing answered either, so the launch stopped."""
    args = agent_mcp.codex_launch_args(str(tmp_path / "hs-action-ai_1"))
    real = os.path.realpath(str(tmp_path / "hs-action-ai_1"))
    assert args == ["-c", "projects={" + json.dumps(real) + '={trust_level="trusted"}}', "--dangerously-bypass-hook-trust"]


def test_a_codex_launch_carries_the_startup_flags(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    _enable_codex_hooks(tmp_path, monkeypatch)
    rig = _rig(tmp_path, db, monkeypatch, agent="codex")
    result = rig.hand.hand(OWNER, "action", "ai_1", profile="codex-default")
    assert result["status"] == "launched", result
    spawn = next(call for call in rig.tmux.calls if call[:2] == ["tmux", "new-session"])
    command = spawn[-1]
    assert "--dangerously-bypass-hook-trust" in command
    assert "trust_level" in command and str(rig.worktree.name) in command
    rig.tmux.ended = True


_CODEX_IDLE = (
    "  >_ OpenAI Codex (v0.159.0)\n     ~/dev/hs-action-ai_1\n"
    "› Ask Codex to do anything\n  GPT-6-Luna low · ~/dev/hs-action-ai_1\n"
    "  ? for shortcuts                                     ⚠ 3 warnings · f2 to view"
)
_CODEX_TRUST = (
    "  Folder access\n  Trust this folder? Codex can read, edit, and run files here.\n"
    "› 1. Trust and continue\n  2. Quit\n  enter continue · esc quit"
)
_CODEX_HOOK_REVIEW = (
    "  Hooks need review\n  12 hooks are new or changed.\n› 1. Review hooks\n"
    "  2. Trust all and continue\n  3. Continue without trusting (hooks won't run)\n  enter confirm · esc skip"
)


def test_the_codex_composer_is_read_as_ready() -> None:
    assert codex_screen_ready(_CODEX_IDLE.splitlines())
    assert not codex_screen_ready(_CODEX_TRUST.splitlines())
    assert not codex_screen_ready(_CODEX_HOOK_REVIEW.splitlines())
    assert not codex_screen_ready((_CODEX_HOOK_REVIEW + "\n  ? for shortcuts").splitlines())
    assert not codex_screen_ready(["OpenAI Codex", "Loading the model..."])
    assert not codex_screen_ready([])


def _enable_codex_hooks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    (home / ".codex" / "hooks.json").write_text('{"hooks": {"x": "holdspeak agent-hook ingest --agent codex"}}')
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CODEX_HOME", raising=False)


def test_codex_gets_its_brief_on_its_composer_and_then_registers(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    """Codex reports SessionStart only with its first prompt: a launch that
    waited for registration before typing waited forever (on the real desk:
    instruction_state pending, the brief never typed)."""
    _enable_codex_hooks(tmp_path, monkeypatch)
    prompted = {"yes": False}
    rig = _rig(
        tmp_path, db, monkeypatch, agent="codex",
        register_when=lambda tmux: prompted["yes"],
        screen=lambda worktree: _CODEX_IDLE,
    )

    result = rig.hand.hand(OWNER, "action", "ai_1", profile="codex-default")
    assert result["instruction_state"] == "pending"
    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    assert len(rig.typed) == 1 and "action:ai_1" in rig.typed[0][1]
    assert not record.get("session_key")  # typed before any registration
    prompted["yes"] = True  # the first prompt makes Codex report SessionStart
    registered = _wait_for(lambda: rig.launches.get(result["launch_id"]), "state", "registered")
    assert registered["session_key"] == "codex:smoke-session"
    rig.tmux.ended = True


def test_a_codex_startup_screen_gets_nothing(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    _enable_codex_hooks(tmp_path, monkeypatch)
    rig = _rig(tmp_path, db, monkeypatch, agent="codex", register_when=lambda tmux: False,
               screen=lambda worktree: _CODEX_TRUST)
    result = rig.hand.hand(OWNER, "action", "ai_1", profile="codex-default")
    time.sleep(0.5)
    assert rig.typed == [] and rig.keys_sent == []
    assert rig.launches.get(result["launch_id"])["instruction_state"] == "pending"
    rig.tmux.ended = True
