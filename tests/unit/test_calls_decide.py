"""PG-DIRECTION DIR8: the call that decides (DIRECTION-2026-10-31.md §4).

The call script on a rig Program, word by word: the phone half is a stub
(its listen pops his next words; its say can drop the call), the held items
are the rig's real your-turn items as packages (``BriefingService.compose``),
and his yes runs the item's own verb (``program.decide``, ``via="call"``).
Done when (§12 DIR8): a core question is decided after "yes"; "no" and a
dropped call decide nothing; "later, at one" defers to 13:00; "next" is Later
with the default touch; a merge takes the same read back and yes; a waive
waits on the desk; an item answered on another channel first is "answered
already"; each item read gets its ledger line with the transcript Note.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import pytest

from holdspeak.calls import decide
from holdspeak.calls.aiphone import Reply
from holdspeak.calls.decide import DeskHeld, later_at, match_choice
from holdspeak.calls.runner import CallRecord, CallRunner
from holdspeak.services.briefing_service import BriefingService
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig

NOW = datetime(2026, 10, 31, 12, 10).astimezone()


class ScriptPhone:
    """His words in order; the call ends when they run out. ``drop_on``: the
    say that finds the call ended (he hung up while it spoke)."""

    def __init__(self, heard: list[str], *, drop_on: Optional[Callable[[str], bool]] = None,
                 on_say: Optional[Callable[[str], None]] = None) -> None:
        self.heard = list(heard)
        self.said: list[str] = []
        self._drop_on = drop_on
        self._on_say = on_say

    async def listen(self, *, call_id: str = "", timeout: float = 60.0) -> Reply:
        if not self.heard:
            return Reply(0, {"ok": True, "kind": "ended", "ended_by": "them"})
        return Reply(0, {"ok": True, "kind": "heard", "text": self.heard.pop(0)})

    async def say(self, text: str, *, call_id: str = "") -> Reply:
        if self._drop_on is not None and self._drop_on(text):
            return Reply(11, {"ok": False})
        self.said.append(text)
        if self._on_say is not None:
            self._on_say(text)
        return Reply(0, {"ok": True, "result": "said"})

    async def hangup(self, *, say: str = "", call_id: str = "") -> Reply:
        if say:
            self.said.append(say)
        return Reply(0, {"ok": True, "outcome": "completed", "ended_by": "hangup_command"})


class NoTurns:
    """A call that decides needs no model turn: every word here is the hub's."""

    def new_thread(self, title: str) -> str:
        return "t"

    async def run(self, thread_id: str, text: str, *, holds: Any) -> dict[str, Any]:
        raise AssertionError(f"no model turn on a call that decides: {text!r}")

    def hold_words(self, tool_call_id: str, tool: str) -> str:
        return ""

    def decide(self, tool_call_id: str, decision: str) -> bool:
        return False


def _core(tmp_path: Path, control: str = "yolo") -> tuple[Rig, str]:
    """Step 1 touched a file no step owns: a core question (Go on · Park)."""
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Overnight on the home box", goal="Stop the stalls.",
                             repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}", template="fast-cycle",
                             control=control)["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Owned", "brief": "Store the stall reason.", "owns": ["src/a.py"]}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    rig.agent.finish(step["launch_id"], {"src/a.py": "a\n", "other/b.py": "b\n"})
    rig.tick()
    assert [item["kind"] for item in rig.service.needs_you_items()] == ["core"]
    return rig, pid


def _two_merges(tmp_path: Path) -> tuple[Rig, str]:
    """At Secure, two steps with a green check and a passed review: two merge asks."""
    from tests.integration.test_program_run import _build_and_review_first_two, _plan_three, _program

    rig = Rig(tmp_path)
    pid = _program(rig, reviewer_profile="codex-default", control="secure")
    _plan_three(rig, pid)
    rig.service.start(OWNER, pid)
    _build_and_review_first_two(rig, pid, "MUST: none")
    assert [item["kind"] for item in rig.service.needs_you_items()] == ["merge", "merge"]
    return rig, pid


def _call(rig: Rig, heard: list[str], *, about: str = "", **phone_kw: Any) -> tuple[list[str], CallRecord]:
    phone = ScriptPhone(["Blue heron.", *heard], **phone_kw)
    record = CallRecord(phone_call_id="c1", direction="out" if about else "in", remote="+12125550142", about=about)

    async def save(rec: CallRecord) -> None:
        rec.note_ref = "note:call-1"

    held = DeskHeld(rig.db, programs=lambda: rig.service, now=lambda: NOW)
    runner = CallRunner(phone, record, turns=NoTurns(), passphrase="blue heron", allowed_numbers=[],
                        greeting="Hello.", emit=lambda *_: None, save_note=save, held=held)
    asyncio.run(asyncio.wait_for(runner.run(), 20))
    return phone.said, record


def _lines(rig: Rig, pid: str, via: str = "call") -> list[str]:
    return [row["line"] for row in reversed(rig.service.store.list_checkpoints(pid)) if row.get("via") == via]


def _kinds(rig: Rig) -> list[str]:
    return [item["kind"] for item in rig.service.needs_you_items()]


# ── the words, by rule ────────────────────────────────────────────────

@pytest.mark.parametrize("words, want", [
    ("later", (14, 10, 0)), ("Not now.", (14, 10, 0)), ("Wait.", (14, 10, 0)), ("Ask me later.", (14, 10, 0)),
    ("Later, at one.", (13, 0, 0)), ("later 2 hours", (14, 10, 0)), ("In two hours.", (14, 10, 0)),
    ("later 30 minutes", (12, 40, 0)), ("at 13:30", (13, 30, 0)), ("Later at five.", (17, 0, 0)),
    ("at 9 am", (9, 0, 1)), ("tonight", (19, 0, 0)), ("Tomorrow.", (7, 0, 1)), ("put it on my desk", (14, 10, 0)),
])
def test_later_words_map_to_the_next_touch(words: str, want: tuple[int, int, int]) -> None:
    assert decide.is_later(words), words
    until = later_at(words, NOW)
    assert (until.hour, until.minute, (until.date() - NOW.date()).days) == want, (words, until)


@pytest.mark.parametrize("words", ["later after the standup", "at 25", "in 0 hours"])
def test_later_with_no_time_we_know_asks_for_one(words: str) -> None:
    with pytest.raises(ValueError):
        later_at(words, NOW)


def test_a_choice_is_heard_by_its_label_and_later_is_never_make_a_task() -> None:
    finding = {"choices": [{"id": "fix_now", "label": "Fix now"}, {"id": "later", "label": "Make a task"},
                           {"id": "skip", "label": "Skip"}]}
    assert match_choice(finding, "Fix it now please") == "fix_now"
    assert match_choice(finding, "make a task") == "later"
    assert match_choice(finding, "later") is None and decide.is_later("later")
    word = {"choices": [{"id": "met", "label": "Met"}, {"id": "unmet", "label": "Unmet"}]}
    assert match_choice(word, "It is met.") == "met"
    assert match_choice(word, "Not met.") == "unmet" and match_choice(word, "unmet") == "unmet"
    limited = {"choices": [{"id": "continue", "label": "Continue"}, {"id": "wait", "label": "Wait"}]}
    assert match_choice(limited, "wait") == "wait"  # a choice first: Wait is the item's own choice here
    assert decide.yes_no("Yes, decide it.") == "yes" and decide.yes_no("No.") == "no"
    assert decide.yes_no("wait") == "" and decide.is_what_waits("What waits on me?")


# ── the call script ───────────────────────────────────────────────────

def test_a_core_question_is_read_chosen_read_back_and_decided_on_his_yes(tmp_path) -> None:
    rig, pid = _core(tmp_path)
    said, record = _call(rig, ["What waits on me?", "Go on.", "Yes.", "That's all, thanks."])
    package, read_back = said[2], said[3]
    assert package.startswith("Overnight on the home box, step 1. Step 1 asks you: ")
    assert "Go on: the step goes on with this change. Park: the step stops." in package
    assert package.endswith("Say Go on, Park, or later."), package
    assert read_back == ("You said Go on for step 1 of Overnight on the home box: the step goes on with this "
                         "change. Say yes to decide, or no.")
    assert said[4:] == ["Decided.", "That is all. One decided.", "Goodbye."], said
    assert "core" not in _kinds(rig)
    decided, asked = _lines(rig, pid)
    assert decided.startswith("Go on: ") and decided.endswith(" · decided on a call"), decided
    assert asked.startswith("Asked on a call 12:10 · Go on, decided · transcript: Call · "), asked
    ledger = [row for row in rig.service.store.list_checkpoints(pid) if row["line"] == asked]
    assert ledger[0]["undo"] == {"note_ref": "note:call-1"}
    assert record.results[-1]["effect"] == "decided" and "(passphrase)" in [line.text for line in record.transcript]


def test_no_changes_nothing_and_the_question_is_asked_again_once(tmp_path) -> None:
    rig, pid = _core(tmp_path)
    said, _ = _call(rig, ["What waits on me?", "Go on.", "No.", "Park.", "Yes."])
    assert said[4] == "Nothing changed. Say Go on, Park, or later.", said
    assert said[5].startswith("You said Park for step 1 of Overnight on the home box: the step stops.")
    assert said[6] == "Decided."
    decided = _lines(rig, pid)[0]
    assert decided.startswith("Park") and decided.endswith(" · decided on a call"), decided
    assert "core" not in _kinds(rig)


def test_later_at_a_time_defers_with_no_read_back_and_decides_nothing(tmp_path) -> None:
    rig, pid = _core(tmp_path)
    said, _ = _call(rig, ["What waits on me?", "Later, at one."])
    assert said[3] == "Later, at 13:00. I will ask again then.", said
    assert said[4] == "That is all. One later at 13:00."
    assert _kinds(rig) == ["core"]  # it keeps its place
    assert _lines(rig, pid) == ["Asked on a call 12:10 · later, back at 13:00 · transcript: Call · "
                                + _lines(rig, pid)[0].rsplit("Call · ", 1)[1]]


def test_wait_on_the_read_back_is_later_never_no(tmp_path) -> None:
    rig, _pid = _core(tmp_path)
    said, _ = _call(rig, ["What waits on me?", "Go on.", "Wait."])
    assert said[4] == "Later, at 14:10. I will ask again then.", said
    assert _kinds(rig) == ["core"]


def test_a_time_it_cannot_read_asks_for_one(tmp_path) -> None:
    rig, _pid = _core(tmp_path)
    said, _ = _call(rig, ["What waits on me?", "Later, after the standup.", "Two hours."])
    assert said[3:5] == ["Say a time, for example 14:30.", "Later, at 14:10. I will ask again then."], said


def test_next_is_later_with_the_default_touch_and_a_merge_takes_the_same_yes(tmp_path) -> None:
    rig, pid = _two_merges(tmp_path)
    said, _ = _call(rig, ["What waits on me?", "Next.", "Merge.", "Yes."])
    assert said[2] == "Two things wait on you."
    assert said[3].startswith("The hub stops stalling, step 1. ") and said[3].endswith("Say Merge, Not yet, or later.")
    assert said[4] == "Later, at 14:10. I will ask again then."
    assert said[6] == ("You said Merge for step 2 of The hub stops stalling: HoldSpeak merges the PR. "
                       "Say yes to decide, or no.")
    assert said[7:] == ["Decided.", "That is all. One decided, one later at 14:10."], said
    assert rig.step(pid, 2)["state"] in ("merged", "done") and rig.step(pid, 1)["state"] == "merge_ask"


def test_a_hang_up_mid_read_decides_nothing_and_leaves_the_item_held(tmp_path) -> None:
    rig, pid = _core(tmp_path)
    said, _ = _call(rig, ["What waits on me?"], drop_on=lambda text: text.startswith("Overnight on the home box"))
    assert said == ["Hello. Say your passphrase.", "Hello."], said
    assert _kinds(rig) == ["core"]
    assert _lines(rig, pid) == [f"Asked on a call 12:10 · no answer · transcript: {_lines(rig, pid)[0].split(': ', 1)[1]}"]


def test_a_hang_up_between_the_choice_and_the_yes_decides_nothing(tmp_path) -> None:
    rig, pid = _core(tmp_path)
    said, _ = _call(rig, ["What waits on me?", "Go on."])
    assert said[-1].startswith("You said Go on for step 1"), said
    assert _kinds(rig) == ["core"]
    assert [line.split(" · transcript")[0] for line in _lines(rig, pid)] == ["Asked on a call 12:10 · no answer"]


def test_a_waive_waits_on_the_desk(tmp_path) -> None:
    rig, _pid = _core(tmp_path)
    said, _ = _call(rig, ["What waits on me?", "Waive it.", "That is all."])
    assert said[3] == "A waive waits for you on the desk. Say Go on, Park, or later.", said
    assert said[4] == "That is all. One still waits."
    assert _kinds(rig) == ["core"]


def test_a_call_the_desk_placed_about_a_step_reads_it_first_without_being_asked(tmp_path) -> None:
    rig, pid = _core(tmp_path)
    step = rig.step(pid, 1)
    said, _ = _call(rig, ["Park.", "Yes."], about=step["id"])
    assert said[2].startswith("Overnight on the home box, step 1. Step 1 asks you: "), said
    assert said[4:6] == ["Decided.", "That is all. One decided."]
    assert rig.step(pid, 1)["state"] == "parked"


def test_an_item_answered_on_another_channel_first_is_answered_already(tmp_path) -> None:
    rig, pid = _two_merges(tmp_path)
    briefing = BriefingService(rig.db, programs=lambda: rig.service)
    second = next(item for item in rig.service.needs_you_items() if item["step_id"] == rig.step(pid, 2)["id"])
    page = briefing.make(OWNER, [f"program:{pid}:{second['id']}"])
    done: list[bool] = []

    def on_say(text: str) -> None:
        if text.startswith("The hub stops stalling, step 1.") and not done:
            done.append(True)  # he presses Merge on the page while the call reads step 1
            briefing.answer(page["token"], f"program:{pid}:{second['id']}", "merge")

    said, _ = _call(rig, ["What waits on me?", "Not yet.", "Yes."], on_say=on_say)
    assert said[5] == "Decided.", said
    assert said[6].startswith("Step 2 of The hub stops stalling is answered already: Merge"), said
    assert said[6].endswith("decided from the briefing page."), said
    assert said[7] == "That is all. One decided."


def test_nothing_waits_says_so(tmp_path) -> None:
    rig = Rig(tmp_path)
    said, _ = _call(rig, ["What waits on me?"])
    assert said[2] == "Nothing waits on you.", said


# ── the model's way: a held program.decide on the call's turn ─────────

class _Executor:
    """``ThreadService._tool_executor`` as DeskTurns reads it: the held
    handles and their decision."""

    def __init__(self) -> None:
        self._handles: dict[str, Any] = {}
        self.decided: dict[str, str] = {}

    def decide(self, handle: Any, decision: str) -> None:
        self.decided[handle.call_id] = decision
        handle.state = "admitted" if decision == "approve" else "denied"


def _desk_turns(rig: Rig, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, _Executor]:
    from types import SimpleNamespace

    from holdspeak.calls.service import DeskTurns
    from holdspeak.services import program_service
    from holdspeak.services.thread_service import ThreadService

    executor = _Executor()
    monkeypatch.setattr(ThreadService, "_tool_executor", executor)
    monkeypatch.setattr(program_service, "default_program_service", lambda db=None: rig.service)

    def hold(call_id: str, **args: Any) -> None:
        executor._handles[call_id] = SimpleNamespace(call_id=call_id, args=args, state="awaiting_decision")

    turns = DeskTurns(rig.db, lambda **_kw: None)
    turns.hold = hold  # type: ignore[attr-defined]
    return turns, executor


def test_a_held_decide_is_asked_as_its_read_back_and_always_via_call(tmp_path, monkeypatch) -> None:
    rig, pid = _core(tmp_path)
    turns, executor = _desk_turns(rig, monkeypatch)
    step_id = rig.step(pid, 1)["id"]
    turns.hold("c1", program_id=pid, step_id=step_id, kind="core", choice="go_on", via="desk")
    assert turns.nothing_to_ask("c1", "program.decide") is False
    assert executor._handles["c1"].args["via"] == "call"  # his spoken yes is a call's answer
    assert turns.hold_question("c1", "program.decide") == (
        "You said Go on for step 1 of Overnight on the home box: the step goes on with this change. "
        "Say yes to decide, or no.")
    assert turns.hold_words("c1", "program.decide") == "Decide Go on for step 1 of Overnight on the home box"
    assert turns.decide("c1", "approve") and executor.decided["c1"] == "approve"


@pytest.mark.parametrize("args", [
    {"kind": "core", "choice": "waive"},  # a waive never decides from a call
    {"kind": "core", "choice": "go_on", "program_id": "program-none"},  # nothing waits there
])
def test_a_held_decide_a_call_may_not_take_is_denied_without_a_question(tmp_path, monkeypatch, args) -> None:
    rig, pid = _core(tmp_path)
    turns, executor = _desk_turns(rig, monkeypatch)
    turns.hold("c2", **{"program_id": pid, "step_id": rig.step(pid, 1)["id"], **args})
    assert turns.nothing_to_ask("c2", "program.decide") is True
    assert turns.decide("c2", "approve") and executor.decided["c2"] == "deny"
    assert _kinds(rig) == ["core"]


def test_later_on_a_held_decide_decides_nothing(tmp_path, monkeypatch) -> None:
    rig, pid = _core(tmp_path)
    turns, executor = _desk_turns(rig, monkeypatch)
    turns.hold("c3", program_id=pid, step_id=rig.step(pid, 1)["id"], kind="core", choice="park")
    assert turns.nothing_to_ask("c3", "program.decide") is False
    assert turns.decide("c3", "later") and executor.decided["c3"] == "deny"
    assert _kinds(rig) == ["core"]


class _HeldDecideTurns:
    """A turn whose model calls program.decide: the call asks its read back."""

    def __init__(self) -> None:
        self.decisions: list[str] = []
        self._decided = asyncio.Event()

    def new_thread(self, title: str) -> str:
        return "t"

    async def run(self, thread_id: str, text: str, *, holds: Any) -> dict[str, Any]:
        holds([{"call_id": "d1", "tool": "program.decide"}])
        await asyncio.wait_for(self._decided.wait(), 5)
        return {"text": "Step 1 goes on." if self.decisions[-1] == "approve" else "It waits.", "used": {},
                "error": None}

    def hold_words(self, tool_call_id: str, tool: str) -> str:
        return "Decide Go on for step 1 of Overnight on the home box"

    def hold_question(self, tool_call_id: str, tool: str) -> str:
        return "You said Go on for step 1 of Overnight on the home box: the step goes on. Say yes to decide, or no."

    def decide(self, tool_call_id: str, decision: str) -> bool:
        self.decisions.append(decision)
        self._decided.set()
        return True


@pytest.mark.parametrize("answer, decision", [("Yes.", "approve"), ("No.", "deny"), ("Wait.", "later"),
                                              ("Not now.", "later")])
def test_the_call_asks_a_held_decide_once_and_wait_is_later_never_no(answer: str, decision: str) -> None:
    phone = ScriptPhone(["Blue heron.", "Go on with the overnight step.", answer, "That's all."])
    record = CallRecord(phone_call_id="c1", direction="in", remote="+12125550142")
    turns = _HeldDecideTurns()

    async def save(_rec: CallRecord) -> None:
        return None

    runner = CallRunner(phone, record, turns=turns, passphrase="blue heron", allowed_numbers=[], greeting="Hello.",
                        emit=lambda *_: None, save_note=save)
    asyncio.run(asyncio.wait_for(runner.run(), 10))
    assert phone.said[2] == turns.hold_question("d1", "program.decide"), phone.said
    assert turns.decisions == [decision]
    assert [row["kind"] for row in record.results] == (["program_decision"] if decision == "approve" else [])
