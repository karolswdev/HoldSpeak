"""DIR-O-002 runtime counters for the dictation LLM runtime.

Spec: `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §9.7. The LLM
runtime layer reports four counters:

  - `model_loads` — `LLMRuntime.load()` advanced past first-time init.
  - `classify_calls` — `LLMRuntime.classify()` invoked.
  - `classify_failures` — `classify()` raised.
  - `constrained_retries` — re-attempts under tightened structured-output
    constraints. Both shipped backends currently use single-shot
    constrained decoding (GBNF / outlines) with no retry path, so this
    counter will read 0 in dogfood today; the surface is in place for
    when a future backend (or an LLM-driven repair pass) lands.

Counters are process-scoped, threadsafe, and exposed via a
zero-arg `get_counters()` snapshot for `holdspeak doctor` (HS-3-04).

The runtime layer wraps the concrete backends with
`CountingRuntime` at `build_runtime` time so the increments happen
in one place — neither `runtime_mlx.py` nor `runtime_llama_cpp.py`
needs to know about counters.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any

from holdspeak.plugins.dictation.grammars import StructuredOutputSchema
from holdspeak.plugins.dictation.runtime import LLMRuntime


@dataclass
class _CounterState:
    model_loads: int = 0
    classify_calls: int = 0
    classify_failures: int = 0
    constrained_retries: int = 0


_LOCK = threading.Lock()
_STATE = _CounterState()


def get_counters() -> dict[str, int]:
    """Return a snapshot of the four DIR-O-002 counters."""
    with _LOCK:
        return {
            "model_loads": _STATE.model_loads,
            "classify_calls": _STATE.classify_calls,
            "classify_failures": _STATE.classify_failures,
            "constrained_retries": _STATE.constrained_retries,
        }


def reset_counters() -> None:
    """Reset all counters to zero. Intended for test isolation."""
    global _STATE
    with _LOCK:
        _STATE = _CounterState()


def _bump(field: str, delta: int = 1) -> None:
    with _LOCK:
        setattr(_STATE, field, getattr(_STATE, field) + delta)


class CountingRuntime:
    """Counter-instrumenting wrapper around any `LLMRuntime`.

    Implements the `LLMRuntime` Protocol by delegation. The first
    successful `load()` advances `model_loads`; every `classify()`
    call advances `classify_calls`; an exception out of `classify()`
    (re-raised) advances `classify_failures`.
    """

    def __init__(self, inner: LLMRuntime) -> None:
        self._inner = inner
        self._loaded = False

    @property
    def backend(self) -> str:
        return self._inner.backend

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
        _bump("classify_calls")
        try:
            return self._inner.classify(
                prompt,
                schema,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception:
            _bump("classify_failures")
            raise


def note_constrained_retry() -> None:
    """Advance `constrained_retries` from a backend that re-attempts under tightened constraints.

    No shipped backend calls this today (single-shot constrained
    decoding). Provided so a future runtime can report retries
    without coupling to the counter module's internals.
    """
    _bump("constrained_retries")
