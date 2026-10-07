"""Conductor R1: what the real loop with real Claude Code and real Codex broke.

Each test pins one defect found on the owner's machine (2026-10-06) with
Claude Code 2.1.288 and Codex 0.159.0 launched by the real hub: the walk log
is in the R1 pull request. Producers are the product's own (the K2 rig, the
real gate service, the real hook ingest); tmux and the agents are faked only
at the process edge.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

import holdspeak.tmux_transport as tmux_transport
from holdspeak.agent_context import hooks as agent_hooks
from holdspeak.agent_context.models import is_blocked
from holdspeak.agent_context.sessions import ingest_agent_hook_event
from holdspeak.services.agent_hand_service import codex_hooks_installed
from holdspeak.services.needs_you_membership import TO_ANSWER, coder_items


# ── 2. a question in the Stop payload is a wait (Needs you) ──────────


@pytest.mark.parametrize("agent", ["claude"])  # Codex's Stop is R3's (every Stop a wait)
def test_a_question_in_the_stop_payload_reaches_needs_you(tmp_path, agent) -> None:
    """Claude Code 2.1.288 sends the turn's last assistant message in the
    Stop payload. The launched agent's rider hooks do not opt
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


# ── 4. the hook runs the hub's own checkout ────────────────────────


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


# ── 5. Codex: its hooks are read where Codex reads them ─────────────


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




