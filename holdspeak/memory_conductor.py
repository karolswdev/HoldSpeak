"""The memory conductor: one hub thread that keeps the memory index current
(docs/internal/MEMORY-DESIGN.md §3).

Each tick it runs the sweep (chunks need no model), finds the ``memory.embed``
engine through the router, gives that engine to recall, and embeds the chunks
that have no current vector.  Then, when ``memory.extract`` has an engine, it
runs the extract jobs that wait (slice 3): facts and entities from the chunks.
It copies the intel drainer's shape: one thread, started and stopped by the
hub, only in the process that owns the database.

* Consolidation (slice 4) runs after extraction on the same call budget and
  the same yield rule; it first retires observations with no live evidence
  (no engine needed).
* Pages (slice 5) run after consolidation on the same call budget and the
  same yield rule, when ``memory.page`` has an engine.
* Extraction yields: before each source it stops for a live meeting, and
  for a local engine also for a live local model call (or one that ended
  less than ``LOCAL_IDLE_SECONDS`` ago).  A pass makes at most
  ``EXTRACT_CALLS_PER_PASS`` engine calls; a backlog goes on in the next
  pass, ``EXTRACT_GAP_SECONDS`` later.

* No engine assigned: chunks are still built; recall is the keyword +
  relation search; nothing waits and nothing fails.
* The engine fails or is busy (a live local model call holds the runtime):
  the tick ends, the batches already written stay, and the next tick goes on
  from there.
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable, Iterable, Optional

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
#: Engine calls (one per chunk) one pass may make for extraction.  No new
#: source starts after this; the rest waits for the next pass.
EXTRACT_CALLS_PER_PASS = 24
#: Seconds between two extract-only passes while a backlog waits.
EXTRACT_GAP_SECONDS = 5.0
#: A local extract engine shares the one local runtime with live calls: it
#: waits until no local model call ran for this long.
LOCAL_IDLE_SECONDS = 20.0

#: The hub's check for a live meeting (``set_live_check``).  It returns a
#: reason, or "" when nothing live runs.
_live_check: Optional[Callable[[], str]] = None

_conductor: Optional["MemoryWorker"] = None
_lock = threading.Lock()


def _principal() -> Any:
    from .principals import Principal, PrincipalKind

    return Principal(PrincipalKind.OWNER, "memory-conductor")


def _assigned(db: Any) -> bool:
    """True when ``memory.embed``, ``memory.extract``, ``memory.consolidate``
    or ``memory.page`` has its own assignment now (four row reads)."""
    from .memory.consolidate import CONSOLIDATE_CAPABILITY
    from .memory.engine import _assignment_head
    from .memory.extract import EXTRACT_CAPABILITY
    from .memory.pages import PAGE_CAPABILITY

    with db._connection() as conn:
        return (
            _assignment_head(conn) is not None
            or _assignment_head(conn, EXTRACT_CAPABILITY) is not None
            or _assignment_head(conn, CONSOLIDATE_CAPABILITY) is not None
            or _assignment_head(conn, PAGE_CAPABILITY) is not None
        )


def set_live_check(check: Optional[Callable[[], str]]) -> None:
    """The hub gives the check for a live meeting (a reason, or "")."""
    global _live_check
    _live_check = check


#: A call open longer than this is a call a crashed process left behind.
OPEN_CALL_SECONDS = 600.0


def live_work(db: Any, extractor: Any) -> str:
    """Why extraction must wait now, or "" (MEMORY-DESIGN.md §9: the backlog
    yields to any live meeting or model call).  The extract job asks before
    EVERY engine call.

    * A live meeting, always.
    * A model call that is open now on the SAME engine (the same deployment,
      or the same endpoint and model, or the same model file), whatever its
      boundary: a chat turn, an Ask or a meeting call on the owner's LAN
      model is never queued behind a background chunk.
    * For a LOCAL engine also any live local model call (an active local
      runtime lease) or one that ended less than ``LOCAL_IDLE_SECONDS`` ago:
      a local extract call holds the one local runtime for its whole length.
    """
    from .memory.extract import OWN_OPERATIONS

    check = _live_check
    if check is not None:
        try:
            reason = str(check() or "")
        except Exception:  # a broken check never stops memory for good
            reason = ""
        if reason:
            return reason
    own = set(OWN_OPERATIONS) | set(getattr(extractor, "operation_ids", ()) or ())
    revision = str(getattr(extractor, "revision_id", "") or "")
    with db._connection() as conn:
        if revision:
            mine = conn.execute(
                "SELECT endpoint,model,COALESCE(model_path,'') model_path"
                " FROM deployment_revisions WHERE id=?",
                (revision,),
            ).fetchone()
            rows = conn.execute(
                """SELECT o.operation_id FROM kernel_operations o
                    JOIN deployment_revisions d ON o.target_ref='deployment-revision:'||d.id
                    WHERE o.name='inference.invoke'
                      AND o.state IN ('admitting','awaiting_decision','awaiting_execution','claimed')
                      AND o.updated_at>=? AND o.principal_identity<>'memory-conductor'
                      AND (d.id=?
                           OR (d.endpoint<>'' AND d.endpoint=? AND d.model=?)
                           OR (COALESCE(d.model_path,'')<>'' AND d.model_path=?))""",
                (
                    time.time() - OPEN_CALL_SECONDS, revision,
                    str(mine["endpoint"]) if mine else "", str(mine["model"]) if mine else "",
                    str(mine["model_path"]) if mine else "",
                ),
            ).fetchall()
            if any(str(row[0]) not in own for row in rows):
                return "a model call on the same engine is live"
        if str(getattr(extractor, "boundary", "") or "") != "local":
            return ""
        rows = conn.execute(
            "SELECT operation_id,state,updated_at FROM inference_runtime_leases"
            " WHERE state='active' OR updated_at>=?",
            (time.time() - LOCAL_IDLE_SECONDS,),
        ).fetchall()
    for row in rows:
        if str(row["operation_id"]) in own:
            continue
        return "a local model call is live" if row["state"] == "active" else "a local model call ended just now"
    return ""


def _extract_step(db: Any, broker: Any, should_stop: Any, budget: Any = None) -> dict[str, Any]:
    """The extract jobs that wait, when ``memory.extract`` has an engine.

    No engine: nothing is called and nothing is written (one row read).
    ``budget`` is the pass's call budget, shared with consolidation; the
    report's ``calls`` is what this step attempted, also when the engine
    raised.
    """
    from .memory.extract import CallBudget, extract_pending, resolve_extractor

    budget = budget if budget is not None else CallBudget(EXTRACT_CALLS_PER_PASS)
    report: dict[str, Any] = {"engine": "", "sources": 0, "facts": 0, "calls": 0, "more": 0, "yielded": "", "error": ""}
    try:
        extractor = resolve_extractor(broker, _principal())
    except Exception as exc:  # a route that cannot resolve is "no engine"
        log.warning("memory.extract engine could not be resolved: %s", exc)
        extractor = None
    if extractor is None:
        return report
    report["engine"] = extractor.model_id
    start = budget.calls
    try:
        stats = extract_pending(
            db,
            extractor,
            budget=budget,
            should_stop=should_stop,
            yield_check=lambda: live_work(db, extractor),
        )
        report.update({key: stats[key] for key in ("sources", "facts", "calls", "more", "yielded")})
        report["failed"] = stats["failed"]
    except Exception as exc:
        report["error"] = str(exc)
        log.info("memory extract pass stopped; the next tick goes on: %s", exc)
    # The true count: a call that raised was still made.
    report["calls"] = budget.calls - start
    return report


#: Engine calls one pass may make for consolidation (inside the pass's
#: shared budget): a backlog of scopes goes on in the next pass.
CONSOLIDATE_CALLS_PER_PASS = 6


def _consolidate_step(db: Any, broker: Any, should_stop: Any, budget: Any) -> dict[str, Any]:
    """After extraction: retire what lost its evidence (no engine needed),
    then the consolidate jobs that wait, when ``memory.consolidate`` has an
    engine.  Same budget, same yield rule before EVERY call as extraction.

    No engine: one row read for the retire check, and nothing is called.
    """
    from .memory.consolidate import consolidate_pending, refresh_observations, resolve_consolidator

    report: dict[str, Any] = {
        "engine": "", "jobs": 0, "created": 0, "updated": 0, "calls": 0, "more": 0,
        "yielded": "", "error": "", "retired": 0,
    }
    try:
        report["retired"] = int(refresh_observations(db)["retired"])
    except Exception as exc:  # readers check liveness themselves
        log.warning("memory observation refresh failed: %s", exc)
    try:
        consolidator = resolve_consolidator(broker, _principal())
    except Exception as exc:  # a route that cannot resolve is "no engine"
        log.warning("memory.consolidate engine could not be resolved: %s", exc)
        consolidator = None
    if consolidator is None:
        return report
    report["engine"] = consolidator.model_id
    start = budget.calls
    try:
        stats = consolidate_pending(
            db,
            consolidator,
            budget=budget,
            max_calls=CONSOLIDATE_CALLS_PER_PASS,
            should_stop=should_stop,
            yield_check=lambda: live_work(db, consolidator),
        )
        report.update({key: stats[key] for key in ("jobs", "created", "updated", "more", "yielded")})
        report["failed"] = stats["failed"]
    except Exception as exc:
        report["error"] = str(exc)
        log.info("memory consolidate pass stopped; the next tick goes on: %s", exc)
    report["calls"] = budget.calls - start
    return report


#: Engine calls one pass may make for pages (inside the pass's shared
#: budget): the pages still due go on in the next pass.
PAGE_CALLS_PER_PASS = 4


def _page_step(db: Any, broker: Any, should_stop: Any, budget: Any) -> dict[str, Any]:
    """After consolidation: the pages that are due, when ``memory.page`` has
    an engine (MEMORY-DESIGN.md §3.4).  Same budget, same yield rule before
    EVERY call.  No engine: one row read, nothing called, nothing written."""
    from .memory.pages import resolve_page_writer, write_pending

    report: dict[str, Any] = {"engine": "", "pages": 0, "calls": 0, "more": 0, "yielded": "", "error": ""}
    try:
        writer = resolve_page_writer(broker, _principal())
    except Exception as exc:  # a route that cannot resolve is "no engine"
        log.warning("memory.page engine could not be resolved: %s", exc)
        writer = None
    if writer is None:
        return report
    report["engine"] = writer.model_id
    start = budget.calls
    try:
        stats = write_pending(
            db,
            writer,
            budget=budget,
            max_calls=PAGE_CALLS_PER_PASS,
            should_stop=should_stop,
            yield_check=lambda: live_work(db, writer),
        )
        report.update({key: stats[key] for key in ("pages", "more", "yielded")})
        report["failed"] = stats["failed"]
    except Exception as exc:
        report["error"] = str(exc)
        log.info("memory page pass stopped; the next tick goes on: %s", exc)
    report["calls"] = budget.calls - start
    return report


def _stopped(step: dict[str, Any], should_stop: Any) -> bool:
    return bool(step.get("yielded") or step.get("error") or (should_stop is not None and should_stop()))


def _model_steps(db: Any, broker: Any, should_stop: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """Extraction, then consolidation, then pages, on ONE call budget.  A
    step runs only when the step before it did not stop for a live call, a
    stop or an error.  The page report rides in the consolidate report
    (``pages``)."""
    from .memory.extract import CallBudget

    budget = CallBudget(EXTRACT_CALLS_PER_PASS)
    extract = _extract_step(db, broker, should_stop, budget)
    if _stopped(extract, should_stop):
        return extract, {"engine": "", "calls": 0, "more": 1, "yielded": extract.get("yielded", ""), "error": ""}
    consolidate = _consolidate_step(db, broker, should_stop, budget)
    if _stopped(consolidate, should_stop):
        consolidate["pages"] = {"engine": "", "calls": 0, "more": 1,
                                "yielded": consolidate.get("yielded", ""), "error": ""}
        return extract, consolidate
    consolidate["pages"] = _page_step(db, broker, should_stop, budget)
    return extract, consolidate


def tick(
    db: Any,
    broker: Any,
    *,
    should_stop: Any = None,
    refs: Optional[Iterable[str]] = None,
    extract_only: bool = False,
) -> dict[str, Any]:
    """One pass: sweep, find the engine, embed, extract.  Returns what it did.

    ``refs`` is None on the slow timer: the full sweep.  A wake gives the
    refs of the sources that changed, and the pass reads only those: its
    work is proportional to the number of changes, not to the desk.  A wake
    while neither ``memory.embed`` nor ``memory.extract`` is assigned does no
    work at all; the slow full sweep keeps the chunk index (and the keyword
    tables) current.  ``extract_only`` runs the extract step alone (a
    backlog goes on between two sweeps).
    """
    from .memory.retain import sweep, sweep_refs

    if extract_only:
        extract, consolidate = _model_steps(db, broker, should_stop)
        return {"swept": {}, "engine": "", "embedded": 0, "error": "",
                "extract": extract, "consolidate": consolidate}
    if refs is not None:
        if not _assigned(db):
            return {"swept": {}, "engine": "", "embedded": 0, "error": "", "skipped": 1}
        swept = sweep_refs(db, refs)
    else:
        swept = sweep(db)
    report: dict[str, Any] = {"swept": swept, "engine": "", "embedded": 0, "error": ""}
    _embed_step(db, broker, report, should_stop=should_stop, full=refs is None)
    report["extract"], report["consolidate"] = _model_steps(db, broker, should_stop)
    return report


def _embed_step(db: Any, broker: Any, report: dict[str, Any], *, should_stop: Any, full: bool) -> None:
    from .memory.engine import resolve_embedder
    from .memory.retain import embed_pending

    try:
        embedder = resolve_embedder(broker, _principal())
    except Exception as exc:  # a route that cannot resolve is "no engine"
        log.warning("memory.embed engine could not be resolved: %s", exc)
        embedder = None
    current = db.memory.embedder
    if embedder is None:
        db.memory.set_embedder(None)
        return
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
        if full:
            # The new model's set is complete: the old model's vectors can go.
            db.memory_index.drop_other_models(embedder.model_id)
    except Exception as exc:
        report["error"] = str(exc)
        log.info("memory embed pass stopped; the next tick goes on: %s", exc)


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
        #: When the extract backlog goes on (an extract-only pass), or None.
        next_extract: Optional[float] = None
        while not self._stop.is_set():
            retry = False
            ran: Optional[dict[str, Any]] = None
            try:
                full, refs = self._take()
                if full or time.monotonic() >= next_full:
                    # The slow timer (or a changed assignment): the full sweep.
                    ran = tick(get_database(), _service(), should_stop=self._stop.is_set)
                    next_full = time.monotonic() + self.poll_seconds
                elif refs:
                    ran = tick(
                        get_database(), _service(), should_stop=self._stop.is_set, refs=refs
                    )
                    if ran.get("skipped"):
                        ran = None
                elif next_extract is not None and time.monotonic() >= next_extract:
                    ran = tick(
                        get_database(), _service(), should_stop=self._stop.is_set, extract_only=True
                    )
                if ran is not None:
                    self.last_report = ran
                    extract = ran.get("extract") or {}
                    consolidate = ran.get("consolidate") or {}
                    pages = consolidate.get("pages") or {}
                    retry = bool(ran.get("error") or extract.get("error") or consolidate.get("error")
                                 or pages.get("error"))
                    more = bool(extract.get("more") or (consolidate.get("engine") and consolidate.get("more"))
                                or (pages.get("engine") and pages.get("more")))
                    yielded = extract.get("yielded") or consolidate.get("yielded") or pages.get("yielded")
                    # A backlog goes on soon; a yield or an error waits longer.
                    next_extract = (
                        time.monotonic() + EXTRACT_GAP_SECONDS
                        if more and not yielded and not retry
                        else (time.monotonic() + RETRY_SECONDS if more else None)
                    )
            except Exception as exc:  # the thread must not die on one bad tick
                log.warning("memory conductor tick failed: %s", exc)
                retry = True
            if retry:
                next_full = min(next_full, time.monotonic() + RETRY_SECONDS)
            # A wake never moves the slow timer: the full sweep stays on it.
            due = next_full if next_extract is None else min(next_full, next_extract)
            if self._wake.wait(max(0.0, due - time.monotonic())):
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
    set_live_check(None)
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


__all__ = [
    "MemoryWorker", "last_report", "live_work", "set_live_check", "start_memory_conductor",
    "stop_memory_conductor", "tick", "wake",
]
