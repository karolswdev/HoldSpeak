"""The first Enter of a brief, dropped while Claude Code starts.

The fix proof of 2026-11-02 (launch_aeff60584b0e40ba): the brief was typed
1 s after the spawn; the text sat in Claude Code's composer and its Enter
was dropped (steering audit: one send, ``submit=1``, delivered). The first
message now waits for the composer before it types, and a brief that still
sits in the composer on an idle pane gets its Enter once more.
"""
from __future__ import annotations

import time

from tests.unit.test_agent_hand import OWNER, _rig, _wait_for, db  # noqa: F401

RULE = "─" * 80
BANNER = " ▐▛███▜▌   Claude Code v2.1.316\n▝▜█████▛▘  Fable 5.1 with medium effort"


def _screen(composer: str | None) -> str:
    if composer is None:
        return BANNER + "\n"
    return f"{BANNER}\n\n{RULE}\n❯ {composer}\n{RULE}\n  ⏵⏵ accept edits on (shift+tab to cycle)"


def _claude_pane(rig, *, takes_first_enter: bool, draw_after: int = 3):
    """A pane that draws its composer after a few looks, shows typed text in
    it, and (``takes_first_enter=False``) drops the Enter typed with it."""
    state = {"looks": 0, "entered": False}

    class Pane(type(rig.tmux)):
        def __call__(self, argv, cwd=None):
            if argv[0] == "tmux" and argv[1] == "capture-pane":
                state["looks"] += 1
                typed = rig.typed[-1][1] if rig.typed else ""
                if state["looks"] <= draw_after and not typed:
                    content = _screen(None)
                elif typed and not state["entered"] and not takes_first_enter:
                    content = _screen(" ".join(typed.split())[:70])
                else:
                    content = _screen("")
                for meta in self.meta.values():
                    meta["content"] = content
            return super().__call__(argv, cwd)

    rig.tmux.__class__ = Pane

    def on_keys(pane, keys):
        if keys == ["C-m"]:
            state["entered"] = True

    rig.tmux.on_keys = on_keys
    return state


def _fast(monkeypatch):
    monkeypatch.setattr("holdspeak.delivery.first_message.ENTER_AGAIN_AFTER_SECONDS", 0.3, raising=False)
    monkeypatch.setattr("holdspeak.delivery.first_message.ENTER_GUARD_SECONDS", 5.0, raising=False)
    monkeypatch.setattr("holdspeak.delivery.first_message.CLAUDE_READY_WAIT_SECONDS", 5.0, raising=False)


def test_a_dropped_first_enter_is_sent_again_once_and_the_launch_says_so(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    _fast(monkeypatch)
    rig = _rig(tmp_path, db, monkeypatch)
    state = _claude_pane(rig, takes_first_enter=False)
    result = rig.hand.hand(OWNER, "action", "ai_1")
    _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    deadline = time.monotonic() + 10
    while not (rig.launches.get(result["launch_id"]) or {}).get("enter_again") and time.monotonic() < deadline:
        time.sleep(0.05)
    record = rig.launches.get(result["launch_id"])
    rig.tmux.ended = True
    assert record["ready_state"] == "ready"   # it waited for the composer before it typed
    assert len(rig.typed) == 1 and "action:ai_1" in rig.typed[0][1]
    assert record["instruction_state"] == "sent"
    assert record["enter_again"]["outcome"] == "delivered" and record["commands"]["enter_again"]
    assert [keys for _pane, keys in rig.keys_sent] == [["C-m"]]   # once
    assert state["entered"]


def test_a_brief_whose_enter_was_taken_gets_no_second_enter(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    _fast(monkeypatch)
    rig = _rig(tmp_path, db, monkeypatch)
    _claude_pane(rig, takes_first_enter=True)
    result = rig.hand.hand(OWNER, "action", "ai_1")
    _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    time.sleep(1.0)   # past the guard's 0.3 s
    record = rig.launches.get(result["launch_id"])
    rig.tmux.ended = True
    assert "enter_again" not in record
    assert rig.keys_sent == []
