"""HS-103-04 — endpoint health: an honest circuit breaker across HoldSpeak's
LLM endpoint call sites (dictation runtime, meeting intel).

Adapted from a pattern two independent research-pass analysts (architecture
and feasibility, run with no shared context) both landed on unprompted in
`ViuGiaLai/researchmind`'s `backend/chat/provider_resilience.py` — reimplemented
from scratch (not vendored: ~50 lines, and this project's call sites are a
sync/async mix that wants its own lock shape) per this project's greenfield
craft posture.

The real value here is NOT redundant-provider failover — HoldSpeak has one
live provider on the common path today. It's not hammering a dead endpoint
with a fresh timeout on every call, and giving an honest, named "this
endpoint has been unreachable" reason instead. Circuit-open calls fail FAST
without attempting the network call at all.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

# Named thresholds (expect to revisit once real usage data exists):
# three consecutive failures is enough to distinguish "this endpoint is down"
# from "one request had a transient hiccup," without waiting through a long
# run of failed calls first; thirty seconds is long enough that a flapping
# endpoint doesn't get hammered every request, short enough that a genuinely
# recovered endpoint isn't refused for minutes on end.
DEFAULT_FAILURE_THRESHOLD = 3
DEFAULT_COOLDOWN_SECONDS = 30.0


@dataclass
class _EndpointState:
    consecutive_failures: int = 0
    total_calls: int = 0
    total_failures: int = 0
    last_latency_ms: float = 0.0
    opened_at: Optional[float] = None  # monotonic time the circuit opened


class EndpointHealth:
    """A small, thread-safe circuit breaker keyed by endpoint identity
    (a profile id or base URL). One instance's state is shared by every
    call site that keys into it with the same identity."""

    def __init__(
        self,
        *,
        failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
        cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._cooldown_seconds = cooldown_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._states: dict[str, _EndpointState] = {}

    def check(self, key: str) -> tuple[bool, Optional[str]]:
        """Before calling out: `(ok, refusal_reason)`. `ok=False` means the
        circuit is open — the caller must NOT attempt the network call, and
        should raise/refuse with `refusal_reason` instead. After the cooldown
        elapses, one probe call is allowed through (half-open) so a genuinely
        recovered endpoint isn't refused forever."""
        with self._lock:
            st = self._states.get(key)
            if st is None or st.opened_at is None:
                return True, None
            elapsed = self._clock() - st.opened_at
            if elapsed >= self._cooldown_seconds:
                return True, None
            remaining = self._cooldown_seconds - elapsed
            return False, (
                f"endpoint {key!r} has been unreachable for "
                f"{st.consecutive_failures} consecutive calls; "
                f"retrying in {remaining:.0f}s"
            )

    def record_success(self, key: str, *, latency_ms: float = 0.0) -> None:
        with self._lock:
            st = self._states.setdefault(key, _EndpointState())
            st.consecutive_failures = 0
            st.opened_at = None
            st.total_calls += 1
            st.last_latency_ms = latency_ms

    def record_failure(self, key: str) -> None:
        with self._lock:
            st = self._states.setdefault(key, _EndpointState())
            st.consecutive_failures += 1
            st.total_calls += 1
            st.total_failures += 1
            if st.opened_at is None and st.consecutive_failures >= self._failure_threshold:
                st.opened_at = self._clock()

    def snapshot(self) -> dict[str, dict[str, object]]:
        """A read-only view for the doctor/health surface: every endpoint
        this process has recorded a call for, and whether its circuit is
        currently open."""
        with self._lock:
            out: dict[str, dict[str, object]] = {}
            for key, st in self._states.items():
                is_open = (
                    st.opened_at is not None
                    and (self._clock() - st.opened_at) < self._cooldown_seconds
                )
                out[key] = {
                    "consecutive_failures": st.consecutive_failures,
                    "total_calls": st.total_calls,
                    "total_failures": st.total_failures,
                    "last_latency_ms": st.last_latency_ms,
                    "circuit_open": is_open,
                }
            return out

    def reset(self) -> None:
        """Test-only: forget every endpoint's recorded state."""
        with self._lock:
            self._states.clear()


# HS-103-04: one process-wide breaker — every call site keys into the SAME
# state, so a dictation call and a meeting-intel call against the same
# endpoint identity share one circuit.
default_health = EndpointHealth()


__all__ = [
    "DEFAULT_COOLDOWN_SECONDS",
    "DEFAULT_FAILURE_THRESHOLD",
    "EndpointHealth",
    "default_health",
]
