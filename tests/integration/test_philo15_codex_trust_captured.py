"""PHILO-15 lane 14 (B41): the hub answers Codex's real folder-trust screen.

The screen was captured from Codex 0.159 on 2026-10-07, in the first launch
of rehearsal lane 14 (``tests/fixtures/codex/trust_screen_worktree_note_80x24.txt``):
a worktree of a repository, so Codex adds "Note: You're in a subdirectory of
a Git project. Trusting will apply to the repository root: ..." between the
path and the question. Before the fix the parser joined the Note into the
path and the screen was never answered (rehearsal 1 part B: 3 minutes, a
human pressed Enter).

1. A real tmux pane shows the captured screen; the hub's real pane read
   (``coder_steering.peek_pane``) and the parser find exactly that worktree.
2. The real K2 launch engine (real git worktree, kernel, receipts, steering
   chokepoint, the launch's first-message waiter) on the captured screen
   re-drawn for its own worktree: one Enter, ``trust_state: answered``, the
   brief typed once after it, and the brief's delivery time on the launch.
   Only tmux and the agent process are canned (``tests/unit/test_agent_hand``).
"""
from __future__ import annotations

import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from holdspeak import coder_steering
from holdspeak.delivery import first_message
from tests.unit.test_agent_hand import OWNER, _rig, _wait_for, db  # noqa: F401  (db is a fixture)

CAPTURED = Path(__file__).resolve().parents[1] / "fixtures" / "codex" / "trust_screen_worktree_note_80x24.txt"
CAPTURED_WORKTREE = "/private/tmp/hs14.G9nv/hs-project_item-pitem_7dead93a465b4032976f3dd82a6d9195"
CAPTURED_ROOT = "/private/tmp/hs14.G9nv/holdspeak-dayone-rehearsal-1558"
WIDTH = 76  # Codex breaks a path at the pane width less its 4-column margin (80x24)

COMPOSER = "\n".join([
    "  >_ OpenAI Codex (v0.159.0)", "", "› Ask Codex to do anything", "",
    "  qwen3.8-27b default · /private/tmp/…", "  ? for shortcuts", "",
])


def _wrapped(path: str) -> list[str]:
    return [f"  {path[i:i + WIDTH]}" for i in range(0, len(path), WIDTH)]


def redraw(worktree: str, root: str) -> str:
    """The captured screen with its two paths replaced, broken as Codex
    breaks them; every other row is the capture's own text."""
    rows = CAPTURED.read_text(encoding="utf-8").split("\n")
    out: list[str] = []
    skip_path = skip_root = False
    for row in rows:
        stripped = row.strip()
        if skip_path:
            if stripped:
                continue
            skip_path = False
        if skip_root:
            if stripped and not stripped.startswith("Trust this folder?"):
                continue
            skip_root = False
        out.append(row)
        if stripped == "Folder access":
            out.extend(_wrapped(worktree))
            skip_path = True
        elif stripped.endswith("repository root:"):
            out.extend(_wrapped(root))
            skip_root = True
    return "\n".join(out)


def test_the_redraw_keeps_the_capture() -> None:
    assert redraw(CAPTURED_WORKTREE, CAPTURED_ROOT) == CAPTURED.read_text(encoding="utf-8")


@pytest.mark.skipif(shutil.which("tmux") is None, reason="tmux is required")
def test_a_real_pane_with_the_captured_screen_names_the_worktree(tmp_path: Path) -> None:
    name = f"hs1514_{tmp_path.name[-12:]}"
    subprocess.run(
        ["tmux", "new-session", "-d", "-s", name, "-x", "80", "-y", "24",
         f"cat {CAPTURED}; sleep 30"],
        check=True,
    )
    try:
        pane = subprocess.run(
            ["tmux", "display-message", "-p", "-t", name, "#{pane_id}"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        lines: list[str] = []
        for _ in range(50):
            peek = coder_steering.peek_pane(pane, lines=60)
            lines = list(peek.get("lines") or [])
            if any("enter continue" in row for row in lines):
                break
            subprocess.run(["sleep", "0.1"], check=False)
        prompt = first_message.codex_trust_prompt_for(lines, CAPTURED_WORKTREE)
        assert prompt is not None, lines
        assert prompt["cursor"] == "yes" and prompt["root"] == CAPTURED_ROOT
        assert first_message.codex_trust_prompt_for(lines, CAPTURED_ROOT) is None
    finally:
        subprocess.run(["tmux", "kill-session", "-t", name], capture_output=True, check=False)


def test_the_launch_answers_the_captured_screen_once_then_sends_the_brief(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    typed_once = {"done": False}
    rig = _rig(
        tmp_path, db, monkeypatch, agent="codex",
        screen=lambda worktree: redraw(str(worktree), str(Path(worktree).parent / "repo")),
        register_when=lambda tmux: typed_once["done"],
    )
    root = str(rig.repo.resolve())
    rig.tmux.screen = lambda: redraw(str(rig.worktree), root)
    assert first_message.codex_trust_prompt_for(redraw(str(rig.worktree), root).split("\n"), str(rig.worktree))

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
    assert result["status"] == "launched", result
    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "state", "registered")
    rig.tmux.ended = True
    assert [key for _pane, keys in rig.keys_sent for key in keys] == ["Enter"], "one Enter, ever"
    assert record["trust_state"] == "answered" and len(record["commands"]["trust"]) == 1
    assert len(rig.typed) == 1, "the brief is typed once, after the trust answer"
    assert datetime.strptime(record["brief_sent_at"], "%Y-%m-%dT%H:%M:%SZ")
