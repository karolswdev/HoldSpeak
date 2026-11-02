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


def _screen(composer: str | None, *, wrap: int = 0) -> str:
    if composer is None:
        return BANNER + "\n"
    rows = [composer]
    if wrap and len(composer) > wrap:   # the composer wraps a long brief over several lines
        rows = [composer[i:i + wrap] for i in range(0, len(composer), wrap)]
    inner = "\n".join([f"❯ {rows[0]}", *(f"  {row}" for row in rows[1:])])
    return f"{BANNER}\n\n{RULE}\n{inner}\n{RULE}\n  ⏵⏵ accept edits on (shift+tab to cycle)"


def _claude_pane(rig, *, takes_first_enter: bool, draw_after: int = 3, wrap: int = 0, lag: int = 0):
    """A pane that draws its composer after a few looks, shows typed text in
    it, and (``takes_first_enter=False``) drops the Enter typed with it."""
    state = {"looks": 0, "entered": False, "composer_at": None, "typed_at": None, "looks_since_typed": 0}

    class Pane(type(rig.tmux)):
        def __call__(self, argv, cwd=None):
            if argv[0] == "tmux" and argv[1] == "capture-pane":
                state["looks"] += 1
                typed = rig.typed[-1][1] if rig.typed else ""
                if typed and state["typed_at"] is None:
                    state["typed_at"] = time.monotonic()
                if typed:
                    state["looks_since_typed"] += 1
                if state["looks"] <= draw_after and not typed:
                    content = _screen(None)
                elif typed and state["looks_since_typed"] <= lag:
                    content = _screen("")   # the typed text is not drawn yet
                elif typed and not state["entered"] and not takes_first_enter:
                    content = _screen(" ".join(typed.split())[:200], wrap=wrap)
                else:
                    content = _screen("")
                if content != _screen(None) and state["composer_at"] is None:
                    state["composer_at"] = time.monotonic()
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
    monkeypatch.setattr("holdspeak.delivery.first_message.CLAUDE_READY_SETTLE_SECONDS", 0.5, raising=False)


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


#: Pane %55 on 2026-11-02 at 07:17 UTC: the re-hand brief wrapped in the composer, its Enter dropped.
LIVE_WRAPPED = """ ▐▛███▛█   Claude Code v2.1.316
▝▜██████▀  Fable 5.1 with medium effort · Claude Ultra
 ▝▝   ▝▝   ~/…/scratch-pg-audit-20261101-165845/hs-program-step-28e577a75ad3
────────────────────────────────────────────────────────────────────────────────
❯ Your work is checked green; wait for the review. Do not start a reviewer;
  HoldSpeak starts it.
────────────────────────────────────────────────────────────────────────────────
  ⏵⏵ accept edits on (shift+tab to cycle)"""


def test_a_wrapped_two_line_composer_is_one_composer() -> None:
    from holdspeak.delivery.first_message import _brief_sits, claude_composer

    composer = claude_composer(LIVE_WRAPPED.split("\n"))
    assert composer == "Your work is checked green; wait for the review. Do not start a reviewer; HoldSpeak starts it."
    assert _brief_sits(composer, "Your work is checked green; wait for the review. Do not start a reviewer; HoldSpeak starts it.")
    assert claude_composer(_screen("").split("\n")) == ""


def test_a_dropped_enter_on_a_wrapped_brief_is_sent_again_once(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    _fast(monkeypatch)
    rig = _rig(tmp_path, db, monkeypatch)
    state = _claude_pane(rig, takes_first_enter=False, wrap=40)
    result = rig.hand.hand(OWNER, "action", "ai_1")
    _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    deadline = time.monotonic() + 10
    while not (rig.launches.get(result["launch_id"]) or {}).get("enter_again") and time.monotonic() < deadline:
        time.sleep(0.05)
    record = rig.launches.get(result["launch_id"])
    rig.tmux.ended = True
    assert record.get("enter_again", {}).get("outcome") == "delivered", record.get("enter_again")
    assert [keys for _pane, keys in rig.keys_sent] == [["C-m"]]   # once
    assert state["entered"]
    # The brief waited the settle after the composer first showed.
    assert state["typed_at"] - state["composer_at"] >= 0.5


def test_an_empty_composer_right_after_the_send_is_not_a_submit(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    """The fix proof of 2026-11-02 (pane %56): the guard's first look came
    before the pane drew the typed brief, saw an empty composer, and took it
    for a submit. It now decides only at the mark."""
    _fast(monkeypatch)
    rig = _rig(tmp_path, db, monkeypatch)
    state = _claude_pane(rig, takes_first_enter=False, wrap=40, lag=3)
    result = rig.hand.hand(OWNER, "action", "ai_1")
    _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    deadline = time.monotonic() + 10
    while not (rig.launches.get(result["launch_id"]) or {}).get("enter_again") and time.monotonic() < deadline:
        time.sleep(0.05)
    record = rig.launches.get(result["launch_id"])
    rig.tmux.ended = True
    assert record.get("enter_again", {}).get("outcome") == "delivered", record.get("enter_again")
    assert [keys for _pane, keys in rig.keys_sent] == [["C-m"]]   # once
    assert state["entered"]
