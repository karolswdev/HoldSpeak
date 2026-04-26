"""Unit tests for `holdspeak.plugins.dictation.runtime_counters` (HS-3-04, DIR-O-002)."""

from __future__ import annotations

from typing import Any

import pytest

from holdspeak.plugins.dictation.runtime_counters import (
    CountingRuntime,
    get_counters,
    note_constrained_retry,
    reset_counters,
)


class _StubRuntime:
    """Minimal LLMRuntime-shaped stub for wrapper tests."""

    backend = "stub"

    def __init__(self, *, raise_classify: Exception | None = None) -> None:
        self.load_calls = 0
        self.classify_calls = 0
        self._raise_classify = raise_classify

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
