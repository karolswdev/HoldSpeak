"""PHILO-17 (owner: Ctrl-C has to work): a hub stop returns within seconds
even while the memory conductor or the intel drainer is inside a long engine
call (a page rewrite held TERM and INT for over 30 s)."""
from __future__ import annotations

import threading
import time

from holdspeak import intel_queue_conductor, memory_conductor


def test_memory_conductor_stop_does_not_wait_for_an_engine_call(monkeypatch) -> None:
    release = threading.Event()

    def stuck(self) -> None:  # a pass inside an engine call that will not return soon
        release.wait(60)

    monkeypatch.setattr(memory_conductor.MemoryWorker, "_run", stuck)
    worker = memory_conductor.MemoryWorker().start()
    try:
        began = time.monotonic()
        worker.stop()
        assert time.monotonic() - began < 5.0
    finally:
        release.set()


def test_the_stop_bounds_are_seconds() -> None:
    assert memory_conductor.STOP_JOIN_SECONDS <= 5.0
    assert intel_queue_conductor.STOP_JOIN_SECONDS <= 5.0
