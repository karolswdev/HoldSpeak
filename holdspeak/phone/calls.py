"""The call state machine and its ring timer (design §4).

::

    held ─his press→ ringing                     (an agent's call waits for him)
    ringing ─accept→ answered ─end→ ended
    ringing ─decline→ declined
    ringing ─30 s→ missed ─urgent, once, 60 s later→ ringing
    ringing | held ─the desk ends it→ ended

A missed call (after its one urgent re-ring) becomes one message with the
reason, which he can answer from the lock screen, and a Needs you row; the
service does that in ``on_missed``. The timers are daemon threads, off the
hub's loop; a test gives short ones.

The machine (ringing → accept / decline / timeout, a ring timer per call,
the urgent call) is agentring's (``relay/src/routes/calls.ts``); the
re-ring-once rule stands in for its Do Not Disturb bypass until his
critical-alerts entitlement exists.
"""
from __future__ import annotations

import threading
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("phone.calls")

RING_SECONDS = 30.0
RERING_SECONDS = 60.0

#: state -> the states it may move to.
TRANSITIONS: dict[str, frozenset[str]] = {
    "held": frozenset({"ringing", "ended"}),
    "ringing": frozenset({"answered", "declined", "missed", "ended"}),
    "missed": frozenset({"ringing"}),  # the urgent re-ring, once
    "answered": frozenset({"ended"}),
    "declined": frozenset(),
    "ended": frozenset(),
}
FINAL = frozenset({"declined", "ended"})


class CallRefused(Exception):
    def __init__(self, code: str, detail: str, status: int = 409) -> None:
        super().__init__(detail)
        self.code, self.detail, self.status = code, detail, status


def can_move(state: str, to: str) -> bool:
    return to in TRANSITIONS.get(str(state), frozenset())


class RingTimers:
    """One timer per ringing call: on expiry, ``on_timeout(call_id)``; an
    urgent call that was missed rings again once after ``rering_seconds``."""

    def __init__(self, *, on_timeout: Callable[[str], None], on_rering: Callable[[str], None],
                 ring_seconds: float = RING_SECONDS, rering_seconds: float = RERING_SECONDS) -> None:
        self._on_timeout = on_timeout
        self._on_rering = on_rering
        self.ring_seconds = float(ring_seconds)
        self.rering_seconds = float(rering_seconds)
        self._timers: dict[str, threading.Timer] = {}
        self._rings: dict[str, int] = {}
        self._lock = threading.Lock()

    def _start(self, call_id: str, seconds: float, fn: Callable[[str], None]) -> None:
        def fire() -> None:
            with self._lock:
                self._timers.pop(call_id, None)
            try:
                fn(call_id)
            except Exception as exc:
                log.warning(f"phone call timer failed for {call_id}: {exc}")

        timer = threading.Timer(max(0.0, seconds), fire)
        timer.daemon = True
        with self._lock:
            old = self._timers.pop(call_id, None)
            self._timers[call_id] = timer
        if old is not None:
            old.cancel()
        timer.start()

    def ringing(self, call_id: str, seconds: Optional[float] = None) -> int:
        """The call rings now; its ring count (1 first, 2 on the re-ring)."""
        with self._lock:
            self._rings[call_id] = self._rings.get(call_id, 0) + 1
            count = self._rings[call_id]
        self._start(call_id, self.ring_seconds if seconds is None else seconds, self._on_timeout)
        return count

    def rings(self, call_id: str) -> int:
        with self._lock:
            return self._rings.get(call_id, 0)

    def rering_later(self, call_id: str) -> None:
        self._start(call_id, self.rering_seconds, self._on_rering)

    def stop(self, call_id: str) -> None:
        with self._lock:
            timer = self._timers.pop(call_id, None)
        if timer is not None:
            timer.cancel()

    def stop_all(self) -> None:
        with self._lock:
            timers, self._timers = list(self._timers.values()), {}
        for timer in timers:
            timer.cancel()


def missed_words(call: Mapping[str, Any]) -> str:
    """The message a missed call leaves: the reason, then the ask."""
    reason = str(call.get("reason") or "").strip().rstrip(".")
    return (f"Missed call: {reason}. Reply here, or call the desk." if reason
            else "Missed call from your desk. Reply here, or call the desk.")


__all__ = ["CallRefused", "FINAL", "RERING_SECONDS", "RING_SECONDS", "RingTimers", "TRANSITIONS", "can_move",
           "missed_words"]
