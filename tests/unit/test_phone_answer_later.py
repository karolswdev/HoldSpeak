"""Phone (2026-10-28): answer later in the Calls turn loop.

A hand slower than ``ANSWER_LATER_SECONDS`` (20 s) says "working on it"; the
call goes on, and the answer is said as a later turn when it is ready. The
phone half is a stub (its listen waits on a queue the test fills), so the
order of words is exact.
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable

import pytest

from holdspeak.calls import runner
from holdspeak.calls.aiphone import Reply
from holdspeak.calls.runner import CallRecord, CallRunner


class StubPhone:
    def __init__(self) -> None:
        self.heard: asyncio.Queue[str] = asyncio.Queue()
        self.said: list[str] = []

    async def listen(self, *, call_id: str = "", timeout: float = 60.0) -> Reply:
        try:
            text = await asyncio.wait_for(self.heard.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return Reply(10, {"ok": True, "kind": "timeout"})
        return Reply(0, {"ok": True, "kind": "heard", "text": text})

    async def say(self, text: str, *, call_id: str = "") -> Reply:
        self.said.append(text)
        return Reply(0, {"ok": True, "result": "said"})

    async def hangup(self, *, say: str = "", call_id: str = "") -> Reply:
        if say:
            self.said.append(say)
        return Reply(0, {"ok": True, "outcome": "completed", "ended_by": "hangup_command"})


class SlowTurns:
    def __init__(self, delay: float) -> None:
        self.delay = delay

    def new_thread(self, title: str) -> str:
        return "t"

    async def run(self, thread_id: str, text: str, *, holds: Callable[[list[dict[str, Any]]], None]) -> dict[str, Any]:
        await asyncio.sleep(self.delay)
        return {"text": f"CI is green on {text}", "used": {}, "error": None}

    def hold_words(self, tool_call_id: str, tool: str) -> str:
        return "Change your desk"

    def decide(self, tool_call_id: str, decision: str) -> bool:
        return True


def test_a_slow_hand_says_working_on_it_and_answers_as_a_later_turn(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "ANSWER_LATER_SECONDS", 0.1)
    monkeypatch.setattr(runner, "KEEPALIVE_SECONDS", 0.05)
    later: list[str] = []

    async def scenario() -> list[str]:
        phone = StubPhone()
        record = CallRecord(phone_call_id="c1", direction="out", remote="+12125550142")

        async def save(_record: Any) -> None:
            return None

        call = CallRunner(phone, record, turns=SlowTurns(0.4), passphrase="blue heron", allowed_numbers=[],
                          greeting="Hello.", emit=lambda *_: None, save_note=save,
                          later=lambda _rec, words: later.append(words))
        running = asyncio.ensure_future(call.run())
        for words in ("Blue heron.", "the runbook PR"):
            await phone.heard.put(words)
        await asyncio.sleep(0.9)  # the slow turn finishes while he is silent
        await phone.heard.put("That's all, thanks.")
        await asyncio.wait_for(running, 5)
        return phone.said

    said = [words for words in asyncio.run(scenario()) if words != runner.STILL_WORKING]
    assert said[:2] == ["Hello. Say your passphrase.", "Hello."]
    assert said[2] == runner.WORKING_ON_IT
    assert said[3] == runner.LATER_PREFIX + "CI is green on the runbook PR"
    assert said[-1] == "Goodbye."
    assert later == []  # answered on the call, so no message after it
