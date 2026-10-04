"""The memory conductor: one hub thread that keeps the memory index current
(docs/internal/MEMORY-DESIGN.md §3).

Each tick it runs the sweep (chunks need no model), finds the ``memory.embed``
engine through the router, gives that engine to recall, and embeds the chunks
that have no current vector.  It copies the intel drainer's shape: one
thread, started and stopped by the hub, only in the process that owns the
database.

* No engine assigned: chunks are still built; recall is the keyword +
  relation search; nothing waits and nothing fails.
* The engine fails or is busy (a live local model call holds the runtime):
  the tick ends, the batches already written stay, and the next tick goes on
  from there.
"""
from __future__ import annotations

import threading
from typing import Any, Optional

from .logging_config import get_logger

log = get_logger("memory_conductor")

#: Seconds between two ticks when nothing wakes the conductor.
POLL_SECONDS = 120.0
#: Seconds until the next try after an engine error.
RETRY_SECONDS = 30.0
#: A local engine shares this device with live model calls: small batches
#: and a gap, so a chat or dictation call seldom meets a busy runtime.
LOCAL_BATCH = 16
LOCAL_PAUSE_SECONDS = 0.25
REMOTE_BATCH = 64
STOP_JOIN_SECONDS = 60.0

_conductor: Optional["MemoryWorker"] = None
_lock = threading.Lock()


def _principal() -> Any:
    from .principals import Principal, PrincipalKind

    return Principal(PrincipalKind.OWNER, "memory-conductor")


def tick(db: Any, broker: Any, *, should_stop: Any = None) -> dict[str, Any]:
    """One pass: sweep, find the engine, embed.  Returns what it did."""
    from .memory.engine import resolve_embedder
    from .memory.retain import embed_pending, sweep

    report: dict[str, Any] = {"swept": sweep(db), "engine": "", "embedded": 0, "error": ""}
    try:
        embedder = resolve_embedder(broker, _principal())
    except Exception as exc:  # a route that cannot resolve is "no engine"
        log.warning("memory.embed engine could not be resolved: %s", exc)
        embedder = None
    current = db.memory.embedder
    if embedder is None:
        db.memory.set_embedder(None)
        return report
    if current is None or getattr(current, "revision_id", None) != embedder.revision_id:
        db.memory.set_embedder(embedder)
    report["engine"] = embedder.model_id
    local = embedder.boundary in ("same_device", "local", "")
    try:
        report["embedded"] = embed_pending(
            db,
            embedder,
            batch_size=LOCAL_BATCH if local else REMOTE_BATCH,
            pause_seconds=LOCAL_PAUSE_SECONDS if local else 0.0,
            should_stop=should_stop,
        )
        # The new model's set is complete: the old model's vectors can go.
        db.memory_index.drop_other_models(embedder.model_id)
    except Exception as exc:
        report["error"] = str(exc)
        log.info("memory embed pass stopped; the next tick goes on: %s", exc)
    return report


class MemoryWorker:
    def __init__(self, *, poll_seconds: float = POLL_SECONDS) -> None:
        self.poll_seconds = max(5.0, float(poll_seconds))
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread = threading.Thread(target=self._run, name="memory-conductor", daemon=True)
        self.last_report: dict[str, Any] = {}

    def start(self) -> "MemoryWorker":
        self._thread.start()
        return self

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    def wake(self) -> None:
        self._wake.set()

    def stop(self, timeout: float = STOP_JOIN_SECONDS) -> None:
        self._stop.set()
        self._wake.set()
        if self._thread.is_alive():
            self._thread.join(timeout)

    def _run(self) -> None:
        while not self._stop.is_set():
            wait = self.poll_seconds
            try:
                from .db import get_database
                from .kernel.runtime import _service

                self.last_report = tick(get_database(), _service(), should_stop=self._stop.is_set)
                if self.last_report.get("error"):
                    wait = min(wait, RETRY_SECONDS)
            except Exception as exc:  # the thread must not die on one bad tick
                log.warning("memory conductor tick failed: %s", exc)
                wait = min(wait, RETRY_SECONDS)
            self._wake.wait(wait)
            self._wake.clear()


def start_memory_conductor(*, poll_seconds: float = POLL_SECONDS) -> Optional[MemoryWorker]:
    """Start the one memory conductor, at most once.  Returns None when this
    process does not own the database."""
    global _conductor
    from .intel_queue_conductor import owns_database

    with _lock:
        if _conductor is not None:
            if _conductor.is_alive():
                return _conductor
            log.warning("Memory conductor thread was dead; replacing it.")
            _conductor = None
        if not owns_database():
            log.warning("Memory conductor is OFF: this process does not own the database.")
            return None
        _conductor = MemoryWorker(poll_seconds=poll_seconds).start()
        log.info("Memory conductor started (poll %.0fs)", _conductor.poll_seconds)
        return _conductor


def stop_memory_conductor(*, timeout: float = STOP_JOIN_SECONDS) -> None:
    global _conductor
    with _lock:
        worker = _conductor
        if worker is None:
            return
        worker.stop(timeout=timeout)
        _conductor = None
    if worker.is_alive():
        log.warning(
            "Memory conductor did not stop within %.0fs. Each of its writes is one "
            "transaction, so the index is whole; the next hub goes on from the ledger.",
            timeout,
        )


def wake() -> None:
    """Ask for a tick now.  Speed only: the next tick sees the source anyway."""
    worker = _conductor
    if worker is not None:
        worker.wake()


__all__ = ["MemoryWorker", "start_memory_conductor", "stop_memory_conductor", "tick", "wake"]
