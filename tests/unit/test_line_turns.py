"""The Line (2026-10-29): the manners on a call (the fills at 1.5 s and 10 s,
the hang-up at 25 s, barge-in) and the guards (the AI disclosure, emergency
numbers, the daily limit)."""
from __future__ import annotations

import asyncio
import time
from datetime import date

import numpy as np

from holdspeak.line.guards import DISCLOSURE, DailyCount, disclosure, is_emergency
from holdspeak.line.turns import GIVE_UP, ONE_MOMENT, STILL_WITH_YOU, CallTurns, Timing, Voice
from tests.fixtures.fake_baresip import ToneTTS


class PlayedPort:
    """A say port that plays in real time (as the call does)."""

    def __init__(self) -> None:
        self.until = 0.0
        self.queued: list[int] = []

    def queue(self, pcm: np.ndarray) -> int:
        now = time.monotonic()
        self.until = max(self.until, now) + len(pcm) / 16000
        self.queued.append(len(pcm))
        return sum(self.queued)

    def speaking(self) -> bool:
        return time.monotonic() < self.until

    def flush(self) -> int:
        self.until = 0.0
        return 0


def _turns(timing: Timing, gave_up: list[float]) -> CallTurns:
    voice = Voice(PlayedPort(), ToneTTS())  # type: ignore[arg-type]
    voice.keep(ONE_MOMENT, STILL_WITH_YOU, GIVE_UP)

    async def give_up() -> None:
        gave_up.append(time.monotonic())

    return CallTurns(voice, timing=timing, give_up=give_up)


def test_the_default_times_are_the_designs() -> None:
    t = Timing()
    assert (t.first_fill, t.second_fill, t.give_up) == (1.5, 10.0, 25.0)


def test_with_no_answer_the_line_fills_twice_then_says_goodbye_and_hangs_up() -> None:
    async def walk() -> tuple:
        gave_up: list[float] = []
        turns = _turns(Timing(0.15, 0.9, 1.8), gave_up)
        start = time.monotonic()
        turns.heard()
        await asyncio.sleep(3.8)
        return turns.filled, [t - start for t in gave_up]

    filled, gave_up = asyncio.run(walk())
    assert filled == [ONE_MOMENT, STILL_WITH_YOU, GIVE_UP]
    # The goodbye (1.44 s of this voice) is said first, then the hang-up.
    assert len(gave_up) == 1 and 1.8 + 1.4 <= gave_up[0] < 3.8, gave_up


def test_an_answer_in_time_stops_the_clock_and_cuts_a_fill() -> None:
    async def walk() -> tuple:
        gave_up: list[float] = []
        quick = _turns(Timing(0.3, 0.6, 0.9), gave_up)
        quick.heard()
        await asyncio.sleep(0.05)
        said = await quick.say("Done.")
        await asyncio.sleep(1.2)
        late = _turns(Timing(0.1, 0.8, 1.2), gave_up)
        late.heard()
        await asyncio.sleep(0.15)  # "One moment." is being said
        cut = await late.say("Done: added a task.")
        await asyncio.sleep(1.4)
        return quick.filled, said, late.filled, cut, gave_up

    quick, said, late, cut, gave_up = asyncio.run(walk())
    assert quick == [] and said == "said"
    assert late == [ONE_MOMENT] and cut == "said"
    assert gave_up == []


def test_he_speaks_over_the_line_and_its_voice_stops() -> None:
    async def walk() -> str:
        turns = _turns(Timing(), [])
        speaking = asyncio.ensure_future(turns.say("A long answer about the runbook and the release."))
        await asyncio.sleep(0.3)
        assert turns.voice.speaking
        turns.voice.interrupt("interrupted")  # the frame handler's call after 200 ms of his speech
        return await speaking

    assert asyncio.run(walk()) == "interrupted"


def test_the_disclosure_names_holdspeak_as_an_ai_and_the_owner() -> None:
    assert disclosure("Karol") == "This is HoldSpeak, an AI assistant, calling for Karol."
    assert disclosure("") == "This is HoldSpeak, an AI assistant."
    assert "AI" in DISCLOSURE


def test_emergency_numbers_are_never_dialled() -> None:
    for number in ("911", "+911", "112", "tel:112", "sip:999@sip.telnyx.com", "000", "(911)", "988"):
        assert is_emergency(number), number
    for number in ("+1 212 555 0142", "sip:agent@100.64.0.9", "sip:holdspeak@karol", "9110", "+44 20 7946 0999", ""):
        assert not is_emergency(number), number


def test_the_daily_limit_counts_placed_calls_per_day(tmp_path) -> None:
    count = DailyCount(tmp_path / "placed.json")
    today, tomorrow = date(2026, 10, 29), date(2026, 10, 30)
    assert count.allow(2, on=today)
    count.add(on=today)
    count.add(on=today)
    assert not count.allow(2, on=today) and count.today(on=today) == 2
    assert count.allow(2, on=tomorrow) and count.allow(0, on=today)  # 0 is no limit
