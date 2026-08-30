"""HS-151-03: StreamCadence flushes at 500 chars, at 2 s, and at done."""
from __future__ import annotations

import pytest

from holdspeak.kernel.inference_stream import StreamCadence


class _FakeClock:
    """Injectable monotonic clock for deterministic time tests."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


def test_flush_at_char_threshold() -> None:
    """500 chars accumulated triggers a flush."""
    clock = _FakeClock()
    cadence = StreamCadence(clock=clock)
    # Feed 499 chars -- no flush.
    result = cadence.feed("x" * 499)
    assert result is False
    # One more char -> flush.
    result = cadence.feed("x")
    assert result is True
    assert cadence.pending == "x" * 500


def test_flush_at_time_threshold() -> None:
    """2 seconds elapsed triggers a flush even for tiny text."""
    clock = _FakeClock()
    cadence = StreamCadence(clock=clock)
    cadence.feed("hello")
    assert cadence.feed("") is False  # no time passed
    clock.advance(2.0)
    result = cadence.feed("!")
    assert result is True


def test_flush_at_done() -> None:
    """finish() returns True when there is unflushed text."""
    clock = _FakeClock()
    cadence = StreamCadence(clock=clock)
    cadence.feed("hello")
    assert cadence.finish() is True


def test_finish_empty_buffer() -> None:
    """finish() returns False when everything was already flushed."""
    clock = _FakeClock()
    cadence = StreamCadence(clock=clock)
    assert cadence.finish() is False


def test_never_flush_same_text_twice() -> None:
    """After mark_flushed, the same chars do not re-trigger."""
    clock = _FakeClock()
    cadence = StreamCadence(clock=clock)
    cadence.feed("x" * 500)
    cadence.mark_flushed()
    # Feeding one more char should not trigger (only 1 new char).
    assert cadence.feed("y") is False
    # finish() should return True for the unflushed "y".
    assert cadence.finish() is True


def test_mark_flushed_resets_time() -> None:
    """mark_flushed resets the time threshold."""
    clock = _FakeClock()
    cadence = StreamCadence(clock=clock)
    cadence.feed("a")
    clock.advance(1.5)
    cadence.mark_flushed()
    # Now 0 s since last flush.
    assert cadence.feed("b") is False
    clock.advance(1.5)
    # Still only 1.5 s since mark_flushed, not 3 s total.
    assert cadence.feed("c") is False
    clock.advance(0.5)
    # 2.0 s since mark_flushed -> flush.
    assert cadence.feed("d") is True


def test_pending_reflects_only_unflushed_text() -> None:
    """pending returns only the text since the last flush."""
    clock = _FakeClock()
    cadence = StreamCadence(clock=clock)
    cadence.feed("hello")
    cadence.feed(" world")
    assert cadence.pending == "hello world"
    assert cadence.total_text == "hello world"
    # After flushing, pending resets but total_text stays.
    cadence.mark_flushed()
    assert cadence.pending == ""
    cadence.feed("!")
    assert cadence.pending == "!"
    assert cadence.total_text == "hello world!"


def test_feed_after_finish_is_ignored() -> None:
    """Once finished, feed returns False."""
    clock = _FakeClock()
    cadence = StreamCadence(clock=clock)
    cadence.feed("hello")
    cadence.finish()
    assert cadence.feed("x" * 1000) is False


def test_multiple_flush_cycles() -> None:
    """Multiple feed/mark_flushed cycles work correctly."""
    clock = _FakeClock()
    cadence = StreamCadence(clock=clock)
    # First cycle: char threshold.
    cadence.feed("x" * 500)
    cadence.mark_flushed()
    # Second cycle: time threshold.
    cadence.feed("y")
    clock.advance(2.0)
    result = cadence.feed("z")
    assert result is True
    cadence.mark_flushed()
    # Third cycle: done.
    cadence.feed("end")
    assert cadence.finish() is True
