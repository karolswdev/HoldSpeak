"""HS-25-04: CountingRuntime serializes inference across threads.

The concrete adapters (MLX, llama.cpp) are not thread-safe. `CountingRuntime`
(which `build_runtime` always wraps them in) must guarantee single-flight
`classify`/`rewrite`/`load` so concurrent callers block rather than corrupt
backend state.
"""

from __future__ import annotations

import threading
import time

import pytest

from holdspeak.plugins.dictation.runtime_counters import CountingRuntime, reset_counters


class _OverlapDetectingRuntime:
    """Inner runtime that flags if two calls are ever in-flight at once."""

    backend = "fake"

    def __init__(self) -> None:
        self.in_flight = 0
        self.max_in_flight = 0
        self.calls = 0
        self._guard = threading.Lock()

    def _enter(self) -> None:
        with self._guard:
            self.in_flight += 1
            self.calls += 1
            self.max_in_flight = max(self.max_in_flight, self.in_flight)

    def _exit(self) -> None:
        with self._guard:
            self.in_flight -= 1

    def load(self) -> None:
        return None

    def info(self) -> dict:
        return {}

    def classify(self, prompt, schema, *, max_tokens=128, temperature=0.0):
        self._enter()
        try:
            time.sleep(0.01)  # widen the race window
            return {"matched": False, "block_id": None, "confidence": 0.0, "extras": {}}
        finally:
            self._exit()

    def rewrite(self, prompt, *, max_tokens=512, temperature=0.15):
        self._enter()
        try:
            time.sleep(0.01)
            return "rewritten"
        finally:
            self._exit()


@pytest.fixture(autouse=True)
def _reset():
    reset_counters()
    yield
    reset_counters()


def test_concurrent_classify_calls_are_serialized():
    inner = _OverlapDetectingRuntime()
    runtime = CountingRuntime(inner)

    errors: list[BaseException] = []

    def worker():
        try:
            runtime.classify("hi", {"type": "object"})
        except BaseException as exc:  # noqa: BLE001 - surface any thread error
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert inner.calls == 8
    # The invariant: never more than one call inside the inner runtime at once.
    assert inner.max_in_flight == 1


def test_concurrent_mixed_classify_and_rewrite_are_serialized():
    inner = _OverlapDetectingRuntime()
    runtime = CountingRuntime(inner)
    errors: list[BaseException] = []

    def classify_worker():
        try:
            runtime.classify("hi", {"type": "object"})
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    def rewrite_worker():
        try:
            runtime.rewrite("hi")
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [
        threading.Thread(target=classify_worker if i % 2 else rewrite_worker)
        for i in range(8)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert inner.calls == 8
    assert inner.max_in_flight == 1
