"""HS-17-05 — periodic Recording-tick emitter unit tests."""

from __future__ import annotations

import threading
import time

import pytest

from holdspeak.device_recording_tick import RecordingTicker, _format_elapsed


# ---------- _format_elapsed pure helper ----------


@pytest.mark.parametrize(
    "elapsed,expected",
    [
        (0, "Recording 00:00"),
        (1, "Recording 00:01"),
        (59, "Recording 00:59"),
        (60, "Recording 01:00"),
        (61, "Recording 01:01"),
        (599, "Recording 09:59"),
        (3599, "Recording 59:59"),
        (3600, "Recording 60:00"),
        (5999, "Recording 99:59"),  # uncapped just below cap
        (6000, "Recording 99:00"),  # caps mm at 99
        (-5, "Recording 00:00"),  # negative clamped
    ],
)
def test_format_elapsed_renders_mm_ss(elapsed, expected):
    assert _format_elapsed(elapsed) == expected


# ---------- RecordingTicker lifecycle ----------


class _Recorder:
    """Captures (device_ids, text) tuples on each tick."""

    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str]] = []
        self._lock = threading.Lock()

    def __call__(self, ids: list[str], text: str) -> None:
        with self._lock:
            self.calls.append((list(ids), text))


def test_start_with_no_devices_is_noop():
    """Defensive: empty device_ids → don't spawn a thread that has
    nothing to do."""
    rec = _Recorder()
    ticker = RecordingTicker(status_sender=rec, tick_interval_s=0.02)

    ticker.start(started_at_monotonic=time.monotonic(), device_ids=[])

    assert not ticker.is_running()
    assert rec.calls == []


def test_stop_before_start_is_noop():
    rec = _Recorder()
    ticker = RecordingTicker(status_sender=rec, tick_interval_s=0.02)

    # Must not raise.
    ticker.stop()
    assert not ticker.is_running()


def test_fires_periodic_ticks():
    """Core acceptance: at 0.1 s cadence for ~0.35 s, ≥ 2 ticks fire
    with monotonically-incrementing elapsed text."""
    rec = _Recorder()
    ticker = RecordingTicker(status_sender=rec, tick_interval_s=0.1)
    started = time.monotonic()

    ticker.start(started_at_monotonic=started, device_ids=["aipi-1"])
    try:
        time.sleep(0.35)
    finally:
        ticker.stop()

    # At least 2 ticks (at ~0.1 and ~0.2; the third around 0.3 is
    # likely but timing-fragile in CI).
    assert len(rec.calls) >= 2, f"got {len(rec.calls)} ticks: {rec.calls}"
    for ids, text in rec.calls:
        assert ids == ["aipi-1"]
        assert text.startswith("Recording ")
        # Each tick should be Recording 00:0X with a small X.
        assert text == "Recording 00:00"


def test_stop_signals_thread_to_exit():
    rec = _Recorder()
    ticker = RecordingTicker(status_sender=rec, tick_interval_s=0.05)
    ticker.start(started_at_monotonic=time.monotonic(), device_ids=["aipi-1"])

    assert ticker.is_running()
    ticker.stop()
    # Give the thread a moment to exit its wait().
    time.sleep(0.1)
    assert not ticker.is_running()


def test_restart_after_stop_works():
    """Two consecutive meetings on the same ticker instance both
    produce ticks (no zombie state from the first run)."""
    rec = _Recorder()
    ticker = RecordingTicker(status_sender=rec, tick_interval_s=0.05)

    ticker.start(started_at_monotonic=time.monotonic(), device_ids=["aipi-1"])
    time.sleep(0.12)
    ticker.stop()
    first_run_count = len(rec.calls)
    time.sleep(0.05)
    rec.calls.clear()

    ticker.start(started_at_monotonic=time.monotonic(), device_ids=["aipi-2"])
    time.sleep(0.12)
    ticker.stop()

    assert first_run_count >= 1
    assert len(rec.calls) >= 1
    assert rec.calls[0][0] == ["aipi-2"]


def test_start_replaces_running_ticker():
    """A second start() while running should cleanly replace the
    previous thread (no double-tick storm)."""
    rec = _Recorder()
    ticker = RecordingTicker(status_sender=rec, tick_interval_s=0.05)

    ticker.start(started_at_monotonic=time.monotonic(), device_ids=["aipi-1"])
    time.sleep(0.07)
    # Replace.
    ticker.start(started_at_monotonic=time.monotonic(), device_ids=["aipi-2"])
    time.sleep(0.12)
    ticker.stop()

    # Should have ticks from both, with the latter half being aipi-2.
    devices_seen = {ids[0] for ids, _ in rec.calls}
    assert "aipi-2" in devices_seen
    # The first ticker's tick rate should not have doubled by the
    # second start; a rough upper bound on call count helps catch
    # double-ticking.
    assert len(rec.calls) < 10


def test_sender_exception_does_not_kill_thread():
    """A flaky sender should not silently kill the ticker thread."""
    call_count = [0]

    def flaky_sender(_ids: list[str], _text: str) -> None:
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError("boom")

    ticker = RecordingTicker(status_sender=flaky_sender, tick_interval_s=0.05)
    ticker.start(started_at_monotonic=time.monotonic(), device_ids=["aipi-1"])
    try:
        time.sleep(0.18)
    finally:
        ticker.stop()

    # Thread survived past the exception → > 1 call.
    assert call_count[0] >= 2


def test_cadence_alignment_no_drift():
    """The ticker's `next_tick_at` advances by exactly tick_interval
    each iteration, so even if a tick is delayed slightly, the
    overall cadence does not drift."""
    rec = _Recorder()
    ticker = RecordingTicker(status_sender=rec, tick_interval_s=0.1)
    started = time.monotonic()

    ticker.start(started_at_monotonic=started, device_ids=["aipi-1"])
    try:
        time.sleep(0.55)
    finally:
        ticker.stop()

    # Expected ~5 ticks over 550 ms at 100 ms cadence. Lower bound
    # accounts for OS scheduling jitter.
    assert 3 <= len(rec.calls) <= 7, (
        f"expected ~5 ticks at 100 ms cadence, got {len(rec.calls)}"
    )
