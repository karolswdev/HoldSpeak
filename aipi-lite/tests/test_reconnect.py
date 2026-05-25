"""Unit tests for the WS reconnect-with-jitter scheduler in bridge.py."""

from __future__ import annotations

import asyncio

import pytest
import structlog

from bridge import (
    RECONNECT_FLOOR_S,
    _backoff_seconds,
    reconnect_with_backoff,
)

# ---------- _backoff_seconds ----------


def test_backoff_first_attempt_in_jitter_band():
    """Attempt 1 (base 1.0 s, jitter 0.25) must land in [0.75, 1.25]."""
    for _ in range(50):
        wait = _backoff_seconds(1)
        assert 0.75 <= wait <= 1.25 + 1e-9, f"got {wait}"


def test_backoff_caps_at_last_schedule_entry():
    """Attempts past the schedule pin to the last entry (30 s ± 25 %)."""
    for _ in range(50):
        wait = _backoff_seconds(100)
        assert 22.5 <= wait <= 37.5 + 1e-9, f"got {wait}"


def test_backoff_floor_is_respected():
    """Negative jitter never drives the wait below the floor."""
    wait = _backoff_seconds(1, jitter=10.0)  # absurd jitter
    assert wait >= RECONNECT_FLOOR_S


def test_backoff_zero_jitter_is_deterministic():
    schedule = [1.0, 2.0, 4.0]
    for i, expected in enumerate(schedule, start=1):
        got = _backoff_seconds(i, schedule=schedule, jitter=0.0)
        assert got == max(RECONNECT_FLOOR_S, expected), (
            f"attempt {i}: expected {expected}, got {got}"
        )


def test_backoff_attempt_zero_treated_as_one():
    # Defensive: callers shouldn't pass 0, but if they do, don't crash
    # and don't pick a negative index.
    wait = _backoff_seconds(0, jitter=0.0)
    assert wait == max(RECONNECT_FLOOR_S, 1.0)


# ---------- reconnect_with_backoff ----------


@pytest.mark.asyncio
async def test_reconnect_propagates_cancellation():
    """task.cancel() must surface as CancelledError so callers can clean up."""

    async def factory() -> None:
        await asyncio.sleep(0.01)

    log = structlog.get_logger()

    task = asyncio.create_task(
        reconnect_with_backoff(
            factory,
            name="test",
            log=log,
            schedule=[0.001],
            jitter=0.0,
            floor=0.001,
        )
    )
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_reconnect_swallows_exceptions_and_loops():
    """Non-Cancel exceptions must trigger backoff, not propagate."""
    iterations = 0

    async def factory() -> None:
        nonlocal iterations
        iterations += 1
        raise RuntimeError(f"boom #{iterations}")

    log = structlog.get_logger()

    task = asyncio.create_task(
        reconnect_with_backoff(
            factory,
            name="test",
            log=log,
            schedule=[0.001],
            jitter=0.0,
            floor=0.001,
        )
    )
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert iterations >= 3, f"expected ≥ 3 iterations, got {iterations}"


@pytest.mark.asyncio
async def test_reconnect_resets_attempt_counter_on_clean_return():
    """A clean factory return resets the attempt counter so post-success
    failures back off from attempt 1, not from where we left off."""
    succeed_then_fail: list[bool] = [True, True, False, False]
    iterations = 0
    waits: list[float] = []

    # Capture _backoff_seconds calls via monkey-patch so we observe the
    # attempt sequence from the OUTSIDE. Patch on `bridge.reconnect`
    # (the canonical home of the function) — `reconnect_with_backoff`
    # in that module looks up `_backoff_seconds` via the local module
    # globals, so patching the re-export on `bridge` would be a no-op.
    from bridge import reconnect as _reconnect

    real_backoff = _reconnect._backoff_seconds

    def spy(attempt: int, **kwargs: object) -> float:
        waits.append(attempt)
        return real_backoff(attempt, **kwargs)

    _reconnect._backoff_seconds = spy
    try:

        async def factory() -> None:
            nonlocal iterations
            iterations += 1
            ok = succeed_then_fail[iterations - 1] if iterations - 1 < len(succeed_then_fail) else False
            if not ok:
                raise RuntimeError(f"fail #{iterations}")

        log = structlog.get_logger()

        task = asyncio.create_task(
            reconnect_with_backoff(
                factory,
                name="test",
                log=log,
                schedule=[0.001],
                jitter=0.0,
                floor=0.001,
            )
        )
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    finally:
        _reconnect._backoff_seconds = real_backoff

    # First two iterations succeed → no backoff observed.
    # Iteration 3 fails → first backoff with attempt=1.
    # Iteration 4 fails → second backoff with attempt=2.
    # If the counter wasn't reset, we'd see attempt=3, 4 — i.e. starting
    # from where the previous failure left off.
    assert waits[:2] == [1, 2], (
        f"expected [1, 2] (counter reset on success), got {waits[:2]}"
    )
