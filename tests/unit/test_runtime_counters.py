"""Unit tests for `holdspeak.plugins.dictation.runtime_counters`.

Covers HS-3-04 (DIR-O-002 counters) and HS-3-05 (DIR-R-003
cold-start hard-cap).
"""

from __future__ import annotations

import time
from typing import Any

import pytest

from holdspeak.plugins.dictation.runtime_counters import (
    CountingRuntime,
    LLMRuntimeDisabledError,
    get_counters,
    note_constrained_retry,
    reset_counters,
)


class _StubRuntime:
    """Minimal LLMRuntime-shaped stub for wrapper tests."""

    backend = "stub"

    def __init__(
        self,
        *,
        raise_classify: Exception | None = None,
        classify_sleep_s: float = 0.0,
    ) -> None:
        self.load_calls = 0
        self.classify_calls = 0
        self._raise_classify = raise_classify
        self._classify_sleep_s = classify_sleep_s

    def load(self) -> None:
        self.load_calls += 1

    def info(self) -> dict[str, Any]:
        return {"backend": self.backend}

    def classify(
        self,
        prompt: str,
        schema,
        *,
        max_tokens: int = 128,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        self.classify_calls += 1
        if self._classify_sleep_s > 0:
            time.sleep(self._classify_sleep_s)
        if self._raise_classify is not None:
            raise self._raise_classify
        return {"block_id": "stub", "prompt": prompt}


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_counters()
    yield
    reset_counters()


def test_initial_snapshot_is_all_zero() -> None:
    assert get_counters() == {
        "model_loads": 0,
        "classify_calls": 0,
        "classify_failures": 0,
        "constrained_retries": 0,
    }


def test_first_load_advances_model_loads_subsequent_loads_do_not() -> None:
    rt = CountingRuntime(_StubRuntime())
    rt.load()
    rt.load()
    rt.load()
    assert get_counters()["model_loads"] == 1


def test_classify_advances_calls_counter() -> None:
    rt = CountingRuntime(_StubRuntime())
    rt.classify("hello", schema=object())
    rt.classify("world", schema=object())
    snap = get_counters()
    assert snap["classify_calls"] == 2
    assert snap["classify_failures"] == 0


def test_classify_failure_advances_failures_and_re_raises() -> None:
    rt = CountingRuntime(_StubRuntime(raise_classify=RuntimeError("boom")))
    with pytest.raises(RuntimeError, match="boom"):
        rt.classify("x", schema=object())
    snap = get_counters()
    assert snap["classify_calls"] == 1
    assert snap["classify_failures"] == 1


def test_note_constrained_retry_advances_counter() -> None:
    note_constrained_retry()
    note_constrained_retry()
    assert get_counters()["constrained_retries"] == 2


def test_reset_clears_state() -> None:
    rt = CountingRuntime(_StubRuntime())
    rt.load()
    rt.classify("x", schema=object())
    note_constrained_retry()
    reset_counters()
    assert get_counters() == {
        "model_loads": 0,
        "classify_calls": 0,
        "classify_failures": 0,
        "constrained_retries": 0,
    }


def test_wrapper_delegates_backend_attribute() -> None:
    inner = _StubRuntime()
    rt = CountingRuntime(inner)
    assert rt.backend == "stub"


def test_wrapper_delegates_info() -> None:
    inner = _StubRuntime()
    rt = CountingRuntime(inner)
    assert rt.info() == {"backend": "stub"}


# ---------------------------------------------------------------------------
# DIR-R-003 cold-start hard-cap (HS-3-05)
# ---------------------------------------------------------------------------


def test_cold_start_under_cap_does_not_disable() -> None:
    inner = _StubRuntime(classify_sleep_s=0.0)
    rt = CountingRuntime(inner, warm_on_start=False, cold_start_cap_ms=1000)

    result = rt.classify("x", schema=object())
    assert result["block_id"] == "stub"
    assert rt.disabled_for_session is False


def test_cold_start_breach_disables_session_and_raises() -> None:
    inner = _StubRuntime(classify_sleep_s=0.05)  # 50 ms
    rt = CountingRuntime(inner, warm_on_start=False, cold_start_cap_ms=10)

    with pytest.raises(LLMRuntimeDisabledError, match="cold-start exceeded cap"):
        rt.classify("x", schema=object())

    assert rt.disabled_for_session is True
    assert rt.disabled_reason and "cold-start exceeded cap" in rt.disabled_reason


def test_subsequent_classify_short_circuits_without_calling_inner() -> None:
    inner = _StubRuntime(classify_sleep_s=0.05)
    rt = CountingRuntime(inner, warm_on_start=False, cold_start_cap_ms=10)
    with pytest.raises(LLMRuntimeDisabledError):
        rt.classify("first", schema=object())
    inner_calls_after_breach = inner.classify_calls

    with pytest.raises(LLMRuntimeDisabledError):
        rt.classify("second", schema=object())
    with pytest.raises(LLMRuntimeDisabledError):
        rt.classify("third", schema=object())

    # Inner runtime not invoked after the breach.
    assert inner.classify_calls == inner_calls_after_breach


def test_warm_on_start_skips_cold_start_cap() -> None:
    inner = _StubRuntime(classify_sleep_s=0.05)
    rt = CountingRuntime(inner, warm_on_start=True, cold_start_cap_ms=10)

    # warm_on_start=True means the model is pre-loaded, so the first
    # classify is not subject to the cold-start cap.
    result = rt.classify("x", schema=object())
    assert result["block_id"] == "stub"
    assert rt.disabled_for_session is False


def test_no_cap_means_no_disable_even_on_slow_first_call() -> None:
    inner = _StubRuntime(classify_sleep_s=0.05)
    rt = CountingRuntime(inner, warm_on_start=False, cold_start_cap_ms=None)

    result = rt.classify("x", schema=object())
    assert result["block_id"] == "stub"
    assert rt.disabled_for_session is False


def test_cold_start_failure_marks_done_but_not_disabled() -> None:
    """A classify that *raises* on cold-start counts as cold-start-done
    but doesn't trigger the cap-breach disable path."""
    inner = _StubRuntime(raise_classify=RuntimeError("model load failed"))
    rt = CountingRuntime(inner, warm_on_start=False, cold_start_cap_ms=10)

    with pytest.raises(RuntimeError, match="model load failed"):
        rt.classify("x", schema=object())

    assert rt.disabled_for_session is False
    snap = get_counters()
    assert snap["classify_failures"] == 1


def test_build_runtime_wraps_with_counting_and_classify_advances(monkeypatch) -> None:
    """End-to-end: `build_runtime(factories=...)` returns a CountingRuntime
    whose first `load()` + `classify()` advance the module-level counters."""
    from holdspeak.plugins.dictation.runtime import build_runtime

    inner = _StubRuntime()

    def _stub_llama_factory(**kwargs: Any) -> _StubRuntime:
        return inner

    rt = build_runtime(
        backend="llama_cpp",
        factories={
            "mlx": lambda **kw: _StubRuntime(),
            "llama_cpp": _stub_llama_factory,
        },
        on_arm64=lambda: False,
        mlx_importable=lambda: False,
        llama_cpp_importable=lambda: True,
    )

    assert isinstance(rt, CountingRuntime)
    rt.load()
    rt.classify("hello", schema=object())

    snap = get_counters()
    assert snap["model_loads"] == 1
    assert snap["classify_calls"] == 1
    assert snap["classify_failures"] == 0
