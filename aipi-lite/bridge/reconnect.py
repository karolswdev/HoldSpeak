"""Exponential-backoff retry loop for WS + UDP listener restarts.

Both the HoldSpeak WebSocket leg and the device's UDP audio listener
are wrapped in `reconnect_with_backoff` so transient errors retry on
the same exponential schedule. `_close_code_reason` is here too —
it's only used by callers wrapping `websockets.ConnectionClosed`
exceptions into structured logs.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import Any

import websockets

# Schedule: 1, 2, 4, 8, 16, 30 s (cap), each ± 25 % jitter.
RECONNECT_SCHEDULE_S: list[float] = [1.0, 2.0, 4.0, 8.0, 16.0, 30.0]
RECONNECT_JITTER: float = 0.25
RECONNECT_FLOOR_S: float = 0.5


def _backoff_seconds(
    attempt: int,
    *,
    schedule: list[float] = RECONNECT_SCHEDULE_S,
    jitter: float = RECONNECT_JITTER,
    floor: float = RECONNECT_FLOOR_S,
) -> float:
    """Return seconds to wait before retry attempt `attempt` (1-based).

    Pure helper — exposed for unit tests. Caps at the last entry of
    `schedule`; jitter is uniform in ±jitter * base around the base.
    Never returns less than `floor` so we always insert *some* delay.
    """
    if not schedule:
        return floor
    idx = min(max(attempt, 1) - 1, len(schedule) - 1)
    base = schedule[idx]
    delta = random.uniform(-jitter, jitter) * base
    return max(floor, base + delta)


def _close_code_reason(exc: websockets.ConnectionClosed) -> tuple[int | None, str]:
    """Extract `(code, reason)` from a `websockets.ConnectionClosed`.

    Prefers the server-received close frame (`exc.rcvd`) and falls back
    to the locally-sent one (`exc.sent`); returns `(None, "")` if
    neither is set (e.g. a network drop with no close frame on either
    side). Wraps the modern attribute path so we can drop the bridge's
    use of the deprecated `exc.code` / `exc.reason` shortcuts.
    """
    src = exc.rcvd or exc.sent
    if src is None:
        return None, ""
    return src.code, (src.reason or "")


async def reconnect_with_backoff(
    coro_factory: Callable[[], Awaitable[None]],
    *,
    name: str,
    log: Any,
    schedule: list[float] = RECONNECT_SCHEDULE_S,
    jitter: float = RECONNECT_JITTER,
    floor: float = RECONNECT_FLOOR_S,
) -> None:
    """Run `coro_factory()` forever, restarting with exponential backoff + jitter.

    On a clean return from `coro_factory()` (e.g. server-initiated close),
    the attempt counter resets so the next failure starts at attempt 1.
    `asyncio.CancelledError` propagates so `task.cancel()` works.

    `floor` is exposed so unit tests can drive sub-second cycles. Production
    callers should leave it at the default — half a second is the cheapest
    barrier against tight retry loops on a fast-flapping endpoint.
    """
    attempt = 0
    while True:
        try:
            await coro_factory()
            attempt = 0  # success → reset backoff
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            attempt += 1
            wait = _backoff_seconds(attempt, schedule=schedule, jitter=jitter, floor=floor)
            log.warning(
                "reconnect",
                target=name,
                attempt=attempt,
                wait_ms=int(wait * 1000),
                error=type(exc).__name__,
                error_msg=str(exc)[:300],
            )
            await asyncio.sleep(wait)
