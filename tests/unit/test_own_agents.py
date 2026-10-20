"""AG15 own-agent discovery and owner-gesture proof on an isolated command rig."""
from __future__ import annotations

from datetime import datetime, timezone
from subprocess import CompletedProcess
from typing import Any

import pytest

from holdspeak.agent_context.own_agents import _command_agent, answer_own_agent, list_own_agents
from holdspeak.agent_context.screen_watch import ScreenAnswerRefused, ScreenStore


ASK = """● I found two places. Should it live in config or env? Answer 1 for config, 2 for env.
────────────────────────────────────────────────────────────────
  1. config
  2. env
────────────────────────────────────────────────────────────────
❯
────────────────────────────────────────────────────────────────
  ? for shortcuts"""
PERMISSION = """ Bash command

   rm -rf build/ && make release

 Do you want to proceed?
 ❯ 1. Yes
   2. No, and tell Claude what to do differently (esc)

 Esc to cancel"""
SECRET = "sk-abcdefghijklmnopqrstuvwxyz"


class TmuxRig:
    def __init__(self) -> None:
        self.screen = ASK
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str], **_: Any) -> CompletedProcess[str]:
        self.calls.append(list(argv))
        if argv[:3] == ["tmux", "list-panes", "-a"]:
            out = "%1\t100\towner\t0\t✳ fake-claude\t/tmp/project\n%2\t110\towned\t0\t✳ launch\t/tmp/owned\n"
        elif argv[:2] == ["tmux", "capture-pane"]:
            out = self.screen
        elif argv[:2] == ["tmux", "display-message"]:
            out = "✳ fake-claude\n"
        elif argv[:2] == ["ps", "-A"] and "command=" in argv[-1]:
            out = "100 1 200 300 /bin/zsh\n101 100 200 300 /tmp/claude --interactive\n110 1 210 310 /bin/zsh\n111 110 210 310 /tmp/claude --launch\n"
        elif argv[:2] == ["ps", "-A"]:
            out = "100 200 300\n101 200 300\n110 210 310\n111 210 310\n"
        else:
            return CompletedProcess(argv, 1, "", "unknown")
        return CompletedProcess(argv, 0, out, "")


def _records() -> list[dict[str, Any]]:
    return [{"state": "registered", "session": "owned", "target": {"pane_id": "%2"}}]


def test_discovers_native_process_group_and_redacts_screen(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOLDSPEAK_OWN_AGENTS", raising=False)
    rig = TmuxRig()
    rig.screen = ASK.replace("config or env", f"config (token={SECRET}) or env")
    agents = list_own_agents(records=_records(), runner=rig, store=ScreenStore(), now=datetime(2026, 10, 19, tzinfo=timezone.utc))
    assert [agent["pane_id"] for agent in agents] == ["%1"]
    row = agents[0]
    assert row["agent"] == "claude"
    assert row["process"] == {"pid": 101, "group": 200}
    assert row["screen"]["state"] == "asks"
    assert row["screen"]["choices"] == [{"n": "1", "label": "config"}, {"n": "2", "label": "env"}]
    assert SECRET not in str(row)


def test_answer_rereads_prompt_and_reaches_actual_admitted_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOLDSPEAK_OWN_AGENTS", raising=False)
    rig = TmuxRig()
    store = ScreenStore()
    now = datetime(2026, 10, 19, tzinfo=timezone.utc)
    first = list_own_agents(records=[], runner=rig, store=store, now=now)[0]
    sent: list[dict[str, Any]] = []

    def send(**kwargs: Any) -> dict[str, Any]:
        sent.append(kwargs)
        return {"operation_id": "op-own-1"}

    result = answer_own_agent(
        "%1", since=str(first["screen"]["since"]), keys=["1"], records=[], runner=rig,
        store=store, send=send, now=now,
    )
    assert result["status"] == "delivered"
    assert sent == [{"pane": "%1", "keys": [{"literal": "1"}], "session_key": "own:%1", "agent": "claude"}]

    rig.screen = PERMISSION
    with pytest.raises(ScreenAnswerRefused, match="question changed"):
        answer_own_agent(
            "%1", since=str(first["screen"]["since"]), keys=["1"], records=[], runner=rig,
            store=store, send=send, now=now,
        )
    assert len(sent) == 1


def test_off_switch_makes_no_tmux_call(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOLDSPEAK_OWN_AGENTS", "off")
    calls: list[list[str]] = []

    def runner(argv: list[str], **_: Any) -> CompletedProcess[str]:
        calls.append(argv)
        raise AssertionError("tmux/ps must not run when own-agent discovery is off")

    assert list_own_agents(runner=runner) == []
    assert calls == []


def test_command_arguments_do_not_impersonate_an_agent() -> None:
    assert _command_agent("echo claude") is None
    assert _command_agent("python unrelated.py claude") is None
    assert _command_agent("python /tmp/claude --interactive") == "claude"
