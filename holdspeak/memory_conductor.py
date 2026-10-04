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
import time
from typing import Any, Iterable, Optional

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
#: Seconds the conductor waits after a wake before it runs.  A write that
#: touches many objects (or many writes close together) is then one tick.
WAKE_GAP_SECONDS = 2.0

_conductor: Optional["MemoryWorker"] = None
_lock = threading.Lock()


def _principal() -> Any:
    from .principals import Principal, PrincipalKind

    return Principal(PrincipalKind.OWNER, "memory-conductor")


def _assigned(db: Any) -> bool:
    """True when ``memory.embed`` has its own assignment now (one row read)."""
    from .memory.engine import _assignment_head

    with db._connection() as conn:
        return _assignment_head(conn) is not None


def tick(
    db: Any, broker: Any, *, should_stop: Any = None, refs: Optional[Iterable[str]] = None
) -> dict[str, Any]:
    """One pass: sweep, find the engine, embed.  Returns what it did.

    ``refs`` is None on the slow timer: the full sweep.  A wake gives the
    refs of the sources that changed, and the pass reads only those: its
    work is proportional to the number of changes, not to the desk.  A wake
    while ``memory.embed`` is unassigned does no work at all; the slow full
    sweep keeps the chunk index (and the keyword tables) current.
    """
    from .memory.engine import resolve_embedder
    from .memory.retain import embed_pending, sweep, sweep_refs

    if refs is not None:
        if not _assigned(db):
            return {"swept": {}, "engine": "", "embedded": 0, "error": "", "skipped": 1}
        swept = sweep_refs(db, refs)
    else:
        swept = sweep(db)
    report: dict[str, Any] = {"swept": swept, "engine": "", "embedded": 0, "error": ""}
    try:
        embedder = resolve_embedder(broker, _principal())
    except Exception as exc:  # a route that cannot resolve is "no engine"
        log.warning("memory.embed engine could not be resolved: %s", exc)
        embedder = None
    current = db.memory.embedder
    if embedder is None:
        db.memory.set_embedder(None)
        return report
    same = (
        current is not None
        and getattr(current, "revision_id", None) == embedder.revision_id
        and getattr(current, "assignment_head", None) == embedder.assignment_head
    )
    if same:
        embedder = current  # keep its question cache
    else:
        db.memory.set_embedder(embedder)
    report["engine"] = embedder.model_id
    local = embedder.boundary == "local"
    try:
        report["embedded"] = embed_pending(
            db,
            embedder,
            batch_size=LOCAL_BATCH if local else REMOTE_BATCH,
            pause_seconds=LOCAL_PAUSE_SECONDS if local else 0.0,
            should_stop=should_stop,
        )
        if refs is None:
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
        self._changes_lock = threading.Lock()
        #: Refs of the sources that changed since the last pass.
        self._changed: set[str] = set()
        #: A wake with no named change (the assignment changed): a full pass.
        self._full = False
        self._thread = threading.Thread(target=self._run, name="memory-conductor", daemon=True)
        self.last_report: dict[str, Any] = {}

    def start(self) -> "MemoryWorker":
        self._thread.start()
        return self

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    def wake(self, refs: Optional[Iterable[str]] = None) -> None:
        with self._changes_lock:
            if refs is None:
                self._full = True
            else:
                self._changed.update(refs)
        self._wake.set()

    def stop(self, timeout: float = STOP_JOIN_SECONDS) -> None:
        self._stop.set()
        self._wake.set()
        if self._thread.is_alive():
            self._thread.join(timeout)

    def _take(self) -> tuple[bool, list[str]]:
        with self._changes_lock:
            full, refs = self._full, sorted(self._changed)
            self._full = False
            self._changed.clear()
        return full, refs

    def _run(self) -> None:
        from .db import get_database
        from .kernel.runtime import _service

        next_full = 0.0  # the first pass is a full one
        while not self._stop.is_set():
            retry = False
            try:
                full, refs = self._take()
                if full or time.monotonic() >= next_full:
                    # The slow timer (or a changed assignment): the full sweep.
                    self.last_report = tick(get_database(), _service(), should_stop=self._stop.is_set)
                    next_full = time.monotonic() + self.poll_seconds
                elif refs:
                    report = tick(
                        get_database(), _service(), should_stop=self._stop.is_set, refs=refs
                    )
                    if not report.get("skipped"):
                        self.last_report = report
                retry = bool(self.last_report.get("error"))
            except Exception as exc:  # the thread must not die on one bad tick
                log.warning("memory conductor tick failed: %s", exc)
                retry = True
            if retry:
                next_full = min(next_full, time.monotonic() + RETRY_SECONDS)
            # A wake never moves the slow timer: the full sweep stays on it.
            if self._wake.wait(max(0.0, next_full - time.monotonic())):
                self._stop.wait(WAKE_GAP_SECONDS)
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


def last_report() -> dict[str, Any]:
    """What the last tick did, or {} when no conductor runs here."""
    worker = _conductor
    return dict(worker.last_report) if worker is not None else {}


def wake(changes: Optional[Iterable[tuple[str, str]]] = None) -> None:
    """Ask for a pass now.  Speed only: the slow full sweep sees every source.

    ``changes`` is the ``(kind, id)`` list of one ``desk_changed`` frame: the
    pass then reads only those sources.  With no ``changes`` (the assignment
    changed) the pass is a full one.
    """
    worker = _conductor
    if worker is None:
        return
    if changes is None:
        worker.wake()
        return
    from .memory.retain import refs_for_change

    refs = [ref for kind, resource_id in changes for ref in refs_for_change(kind, resource_id)]
    if refs:
        worker.wake(refs)


__all__ = ["MemoryWorker", "last_report", "start_memory_conductor", "stop_memory_conductor", "tick", "wake"]
