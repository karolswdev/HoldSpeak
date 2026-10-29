"""The Line's manners on a call (LINE design §5).

The Line keeps the caller's clock. After it hears him and sends ``heard``:

- 1.5 s and no ``say`` yet: "One moment." (made once at start, kept as PCM);
- 10 s: "Still with you, one moment.";
- 25 s: "Sorry, I cannot answer now. Goodbye." and it hangs up
  (``ended_by: "holdspeak"``).

When he speaks while the Line speaks, after 200 ms the Line stops its voice
and answers the ``say`` with ``interrupted`` (barge-in). These manners are
ai-phone's design (github.com/oxnw/ai-phone at 436f9f1b,
``docs/usage.md#agent-commands``; credit to its authors), written new here.
"""
from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional, Union

import numpy as np

from ..logging_config import get_logger
from .audio import RATE, SayPort
from .speech import TTS, say_once

log = get_logger("line.turns")

ONE_MOMENT = "One moment."
STILL_WITH_YOU = "Still with you, one moment."
GIVE_UP = "Sorry, I cannot answer now. Goodbye."


@dataclass
class Timing:
    """The fills' times after ``heard`` (seconds)."""

    first_fill: float = 1.5
    second_fill: float = 10.0
    give_up: float = 25.0


class Voice:
    """Speaks into the call: text through the TTS, or kept PCM.

    ``speak`` answers ``said`` when the last sample went into the call,
    ``interrupted`` on a barge-in (or a newer say), ``ended`` when the call
    ended first."""

    def __init__(self, port: SayPort, tts: TTS) -> None:
        self._port = port
        self._tts = tts
        self._stop: Optional[threading.Event] = None
        self._outcome = ""
        self._lock = asyncio.Lock()
        self.kept: dict[str, np.ndarray] = {}
        #: (text, monotonic time the first chunk was queued, its stream index): measurement.
        self.last_start: Optional[tuple[str, float, int]] = None

    def keep(self, *texts: str) -> None:
        """Make the fills once (at start), so they cost nothing on a call."""
        for text in texts:
            self.kept[text] = say_once(self._tts, text)

    @property
    def speaking(self) -> bool:
        return self._stop is not None or self._port.speaking()

    def interrupt(self, outcome: str = "interrupted") -> bool:
        """Stop the voice now; True when it was speaking."""
        was = self.speaking
        if self._stop is not None:
            self._outcome = outcome
            self._stop.set()
        self._port.flush()
        return was

    async def speak(self, what: Union[str, np.ndarray]) -> str:
        async with self._lock:
            stop = threading.Event()
            self._stop, self._outcome = stop, ""
            loop = asyncio.get_running_loop()
            try:
                if isinstance(what, np.ndarray):
                    self.last_start = ("<pcm>", loop.time(), self._port.queue(what))
                else:
                    text = str(what)
                    kept = self.kept.get(text)
                    if kept is not None:
                        self.last_start = (text, loop.time(), self._port.queue(kept))
                    else:
                        await asyncio.to_thread(self._make, text, stop, loop)
                while not stop.is_set() and self._port.speaking():
                    await asyncio.sleep(0.02)
                return self._outcome if stop.is_set() else "said"
            finally:
                self._stop = None

    def _make(self, text: str, stop: threading.Event, loop: asyncio.AbstractEventLoop) -> None:
        first = True
        for chunk in self._tts.stream(text, stop):
            if stop.is_set():
                return
            index = self._port.queue(chunk)
            if first:
                self.last_start = (text, loop.time(), index)
                first = False


class CallTurns:
    """One call's clock: the fills and the give-up after ``heard``."""

    def __init__(self, voice: Voice, *, timing: Optional[Timing] = None,
                 give_up: Optional[Callable[[], Awaitable[None]]] = None) -> None:
        self.voice = voice
        self.timing = timing or Timing()
        self._give_up = give_up
        self._clock: Optional[asyncio.Task[None]] = None
        self.filled: list[str] = []

    def heard(self) -> None:
        """He finished a turn: start the clock (a newer turn starts it again)."""
        self.stop_clock()
        self._clock = asyncio.ensure_future(self._run_clock())

    def stop_clock(self) -> None:
        clock, self._clock = self._clock, None
        if clock is not None and not clock.done() and clock is not asyncio.current_task():
            clock.cancel()

    async def _run_clock(self) -> None:
        t = self.timing
        loop = asyncio.get_running_loop()
        start = loop.time()
        try:
            for at, words in ((t.first_fill, ONE_MOMENT), (t.second_fill, STILL_WITH_YOU)):
                await asyncio.sleep(max(0.0, start + at - loop.time()))
                self.filled.append(words)
                await self.voice.speak(words)
            await asyncio.sleep(max(0.0, start + t.give_up - loop.time()))
            self.filled.append(GIVE_UP)
            self._clock = None
            await self.voice.speak(GIVE_UP)
            if self._give_up is not None:
                await self._give_up()
        except asyncio.CancelledError:
            pass

    async def say(self, text: str) -> str:
        """The hub's answer: the clock stops, a fill being said is cut."""
        self.stop_clock()
        if self.voice.speaking:
            self.voice.interrupt("replaced")
        return await self.voice.speak(text)

    def close(self) -> None:
        self.stop_clock()
        self.voice.interrupt("ended")


__all__ = ["CallTurns", "GIVE_UP", "ONE_MOMENT", "STILL_WITH_YOU", "Timing", "Voice"]
