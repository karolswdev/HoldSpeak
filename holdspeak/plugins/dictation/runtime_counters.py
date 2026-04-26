"""DIR-O-002 runtime counters + DIR-R-003 cold-start cap for the dictation LLM runtime.

Spec: `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §9.6 + §9.7.
The LLM runtime layer reports four counters and enforces a
session-scoped cold-start hard-cap:

  - `model_loads` — `LLMRuntime.load()` advanced past first-time init.
  - `classify_calls` — `LLMRuntime.classify()` invoked.
  - `classify_failures` — `classify()` raised.
  - `constrained_retries` — re-attempts under tightened structured-output
    constraints. Both shipped backends currently use single-shot
    constrained decoding (GBNF / outlines) with no retry path, so this
    counter will read 0 in dogfood today; the surface is in place for
    when a future backend (or an LLM-driven repair pass) lands.

  - **Cold-start cap (DIR-R-003):** when `warm_on_start=False`, the
    first `classify()` call must complete within `cold_start_cap_ms`
    (typically `max_total_latency_ms × 5`). If it exceeds the cap,
    the wrapper logs a structured WARN, sets a session-scoped
    `_disabled` flag, and raises `LLMRuntimeDisabledError`. All
    subsequent `classify()` calls short-circuit to the same error
    without invoking the inner runtime. The disable is *session-scoped*
    — a fresh `holdspeak` launch retries.

Counters are process-scoped, threadsafe, and exposed via a
zero-arg `get_counters()` snapshot for `holdspeak doctor` (HS-3-04).
The disabled flag is exposed via `CountingRuntime.disabled_for_session`.

The runtime layer wraps the concrete backends with
`CountingRuntime` at `build_runtime` time so the increments happen
in one place — neither `runtime_mlx.py` nor `runtime_llama_cpp.py`
needs to know about counters or the cold-start cap.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any

from holdspeak.plugins.dictation.grammars import StructuredOutputSchema
from holdspeak.plugins.dictation.runtime import LLMRuntime

log = logging.getLogger(__name__)


class LLMRuntimeDisabledError(RuntimeError):
    """Raised by `CountingRuntime.classify()` when the runtime is disabled for the session.

    Triggered by the DIR-R-003 cold-start hard-cap: the first
    `classify()` call after launch with `warm_on_start=False`
    exceeded the configured cap. The IntentRouter's existing
    exception-handling treats this as a no-match (DIR-F-011),
    so the dictation pipeline falls back to the lexical / no-LLM
    path without raising.
    """


@dataclass
class _CounterState:
    model_loads: int = 0
    classify_calls: int = 0
    classify_failures: int = 0
    constrained_retries: int = 0


_LOCK = threading.Lock()
_STATE = _CounterState()

# DIR-R-003: process-scoped disabled flag. The wrapper sets it when
# the cold-start cap is breached; doctor reads it via
# `get_session_status()`. Distinct from per-instance
# `CountingRuntime.disabled_for_session` only in scope: process vs.
# wrapper. They mirror each other in a single-runtime process.
_SESSION_DISABLED: bool = False
_SESSION_DISABLED_REASON: str | None = None


def get_counters() -> dict[str, int]:
    """Return a snapshot of the four DIR-O-002 counters."""
    with _LOCK:
        return {
            "model_loads": _STATE.model_loads,
            "classify_calls": _STATE.classify_calls,
            "classify_failures": _STATE.classify_failures,
            "constrained_retries": _STATE.constrained_retries,
        }


def get_session_status() -> dict[str, Any]:
    """Return process-scoped session-level state (DIR-R-003)."""
    with _LOCK:
        return {
            "llm_disabled_for_session": _SESSION_DISABLED,
            "disabled_reason": _SESSION_DISABLED_REASON,
        }


def reset_counters() -> None:
    """Reset all counters + session state to zero. Intended for test isolation."""
    global _STATE, _SESSION_DISABLED, _SESSION_DISABLED_REASON
    with _LOCK:
        _STATE = _CounterState()
        _SESSION_DISABLED = False
        _SESSION_DISABLED_REASON = None


def _bump(field: str, delta: int = 1) -> None:
    with _LOCK:
        setattr(_STATE, field, getattr(_STATE, field) + delta)


def _set_session_disabled(reason: str) -> None:
    global _SESSION_DISABLED, _SESSION_DISABLED_REASON
    with _LOCK:
        _SESSION_DISABLED = True
        _SESSION_DISABLED_REASON = reason


class CountingRuntime:
    """Counter-instrumenting wrapper around any `LLMRuntime`.

    Implements the `LLMRuntime` Protocol by delegation. The first
    successful `load()` advances `model_loads`; every `classify()`
    call advances `classify_calls`; an exception out of `classify()`
    (re-raised) advances `classify_failures`.
    """

    def __init__(
        self,
        inner: LLMRuntime,
        *,
        warm_on_start: bool = False,
        cold_start_cap_ms: int | None = None,
    ) -> None:
        self._inner = inner
        self._loaded = False
        # DIR-R-003: cold-start hard-cap state.
        self._warm_on_start = warm_on_start
        self._cold_start_cap_ms = cold_start_cap_ms
        self._cold_start_done = warm_on_start  # warm starts skip the cap check
        self._disabled = False
        self._disabled_reason: str | None = None

    @property
    def backend(self) -> str:
        return self._inner.backend

    @property
    def disabled_for_session(self) -> bool:
        return self._disabled

    @property
    def disabled_reason(self) -> str | None:
        return self._disabled_reason

    def load(self) -> None:
        was_loaded = self._loaded
        self._inner.load()
        if not was_loaded:
            _bump("model_loads")
            self._loaded = True

    def info(self) -> dict[str, Any]:
        return self._inner.info()

    def __getattr__(self, name: str) -> Any:
        # Delegate unknown attributes to the inner runtime so callers
        # can introspect backend-specific state (e.g. `.kwargs` on test
        # stubs) without piercing the wrapper. Called only when the
        # attribute is *not* on `CountingRuntime` itself.
        return getattr(self._inner, name)

    def classify(
        self,
        prompt: str,
        schema: StructuredOutputSchema,
        *,
        max_tokens: int = 128,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        # DIR-R-003: short-circuit if a prior cold-start breach
        # disabled the runtime for this session.
        if self._disabled:
            raise LLMRuntimeDisabledError(self._disabled_reason or "runtime disabled for session")

        _bump("classify_calls")
        is_cold_start = not self._cold_start_done
        start = time.perf_counter()
        try:
            result = self._inner.classify(
                prompt,
                schema,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception:
            _bump("classify_failures")
            self._cold_start_done = True
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        if is_cold_start:
            self._cold_start_done = True
            cap = self._cold_start_cap_ms
            if cap is not None and elapsed_ms > cap:
                reason = (
                    f"cold-start exceeded cap: {elapsed_ms:.0f}ms > {cap}ms; "
                    "LLM stage disabled for this session"
                )
                self._disabled = True
                self._disabled_reason = reason
                _set_session_disabled(reason)
                log.warning(
                    "dictation cold-start cap breached: backend=%s elapsed_ms=%.0f cap_ms=%d; "
                    "LLM stage disabled for session (DIR-R-003)",
                    self._inner.backend,
                    elapsed_ms,
                    cap,
                )
                raise LLMRuntimeDisabledError(reason)
        return result


def note_constrained_retry() -> None:
    """Advance `constrained_retries` from a backend that re-attempts under tightened constraints.

    No shipped backend calls this today (single-shot constrained
    decoding). Provided so a future runtime can report retries
    without coupling to the counter module's internals.
    """
    _bump("constrained_retries")
