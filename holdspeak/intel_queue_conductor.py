"""The hub's intel-queue drainer (HS-200-42).

The 2026-09-13 operational-surface audit (§3.1) measured the defect this
module pays: a stopped meeting writes an ``intel_jobs`` row
(``runtime/routing_glue.py``) and **nothing in the running product executes
it**.  ``IntelQueueWorker`` — a complete polling worker with backoff, retry
ceilings and alerting — had zero production callers; ``drain_intel_queue``
was reachable only from the CLI (``commands/intel.py``) and from
``POST /api/intel/process``, a route no face calls.  On the owner's desk
``intel_snapshots`` was 0 and one job had sat ``queued`` since 2026-09-10.

This conductor is the fourth member of the hub lifespan's start/stop set
(workbench, scheduled recording, calendar ingest), under the same HS-200-03
discipline: what the lifespan starts, the lifespan stops.

Three rules it obeys:

* **Ownership.** One process owns the database (``runtime_lock``).  A second
  hub normally refuses to boot at all, but ``HOLDSPEAK_ALLOW_UNOWNED_DB=1``
  starts one anyway *with scheduled work OFF*
  (``runtime/ownership.py:_start_scheduled_work``).  Draining is scheduled
  work, so this start REFUSES when this process does not hold the claim.
* **Enqueue policy is not drain policy.** ``intelligence_auto`` gates the
  ENQUEUE (``routing_glue._maybe_auto_enqueue_intel``).  The drainer drains
  whatever was enqueued, including a manual ``Run intelligence`` taken while
  auto is ``off``.  There is deliberately no second auto check here; ratified
  HS-200-42 (counsel P2-8) -- a second check would silently strand a job the
  owner asked for by hand.
* **Quiet hours govern notification, not computation.** Intelligence has no
  quiet-hours setting of its own; quiet hours in this product gate the
  DESKTOP notification (``desktop_notify.heartbeat_notify``, reached from
  ``services/heartbeat_service.py``).  This conductor computes regardless of
  the hour and sends no desktop notification of its own — the only thing a
  finished job emits from here is the in-browser ``aftercare_ready`` and
  ``runtime_queue`` frames.
"""
from __future__ import annotations

import threading
from typing import Any, Callable, Optional

from .logging_config import get_logger


log = get_logger("intel_queue_conductor")


# The hub polls every 15s (the worker clamps its floor at 5s).  A just-enqueued
# job does not wait for it: `run_intelligence` calls `wake()`.
HUB_POLL_SECONDS = 15.0

_conductor: Any = None
_broadcast: Optional[Callable[[str, dict], None]] = None
_lock = threading.Lock()


def set_broadcast(fn: Callable[[str, dict], None] | None) -> None:
    """Wire the broadcast callback from the hub's WebSocket manager."""
    global _broadcast
    _broadcast = fn


def broadcast(event_type: str, data: dict) -> None:
    if _broadcast is None:
        return
    try:
        _broadcast(event_type, data)
    except Exception as exc:  # pragma: no cover - a frame is never a gate
        log.debug(f"Broadcast emit failed: {exc}")


def owns_database() -> bool:
    """True only when THIS process holds the database owner claim.

    ``current_lock()`` is ``None`` when the process never claimed at all —
    unknown, and therefore not an owner.  A drainer is scheduled work and
    runs in the owner alone.
    """
    try:
        from .runtime_lock import current_lock

        lock = current_lock()
        return bool(lock is not None and lock.held)
    except Exception as exc:  # pragma: no cover
        log.debug(f"Ownership check failed: {exc}")
        return False


def _on_meeting_ready(meeting_id: str) -> None:
    """A finished job reaches the open browser (the route's own callback)."""
    try:
        from .db import get_database
        from .intel_queue import build_runtime_queue_frame
        from .meeting_aftercare import build_aftercare_ready_event

        db = get_database()
        event = build_aftercare_ready_event(db, meeting_id)
        if event:
            broadcast("aftercare_ready", event)
        broadcast("runtime_queue", build_runtime_queue_frame(db))
    except Exception as exc:
        log.debug(f"aftercare_ready broadcast skipped: {exc}")


def start_intel_queue_conductor(
    *,
    broadcast: Callable[[str, dict], None] | None = None,
    poll_seconds: float = HUB_POLL_SECONDS,
) -> Any:
    """Create the one process-global intel drainer, at most once.

    Returns the live worker, or ``None`` when this process does not own the
    database (a second hub under ``HOLDSPEAK_ALLOW_UNOWNED_DB``, or any
    process that never claimed).
    """
    global _conductor
    if broadcast is not None:
        set_broadcast(broadcast)
    with _lock:
        if _conductor is not None:
            # Counsel P2-9: a cached worker whose thread has died (an
            # unhandled error escaped `_run`, or a stop timed out) is not a
            # drainer. Returning it would report "running" forever over a
            # queue nothing touches -- the exact lie this story exists to end.
            if _conductor.is_alive():
                return _conductor
            log.warning("Intel drainer thread was dead; replacing it.")
            _conductor = None
        if not owns_database():
            log.warning(
                "Intel queue drainer is OFF: this process does not own the database."
            )
            return None
        from .config import Config
        from .intel_queue import start_intel_queue_worker

        cfg = Config.load().meeting
        _conductor = start_intel_queue_worker(
            cfg.intel_realtime_model,
            provider=cfg.intel_provider,
            retry_base_seconds=cfg.intel_retry_base_seconds,
            retry_max_seconds=cfg.intel_retry_max_seconds,
            retry_max_attempts=cfg.intel_retry_max_attempts,
            on_meeting_ready=_on_meeting_ready,
            poll_seconds=poll_seconds,
        )
        log.info("Intel queue drainer started (poll %.0fs)", _conductor.poll_seconds)
        return _conductor


# A drain iteration can be inside a model call.  Counsel P1-1: the hub must
# not hand the database owner lock back while a daemon thread is still writing
# rows, so the join is long enough for an ordinary provider call to finish.
STOP_JOIN_SECONDS = 60.0


def stop_intel_queue_conductor(*, timeout: float = STOP_JOIN_SECONDS) -> None:
    """Stop and clear the global drainer during hub shutdown (HS-200-03).

    Bounded and honest (counsel P1-1): the join waits up to ``timeout`` for an
    in-flight model call to finish.  If the thread is STILL alive after that,
    this says so by name -- the meeting whose job is in flight, and the fact
    that the executor lease takeover recovers it -- and returns anyway.  A hub
    that refused to exit would be worse than one that exits loudly.
    """
    global _conductor
    # The join happens INSIDE the lock so a second caller (the hub runtime,
    # after the app shutdown hook) blocks until the first join has returned
    # rather than finding `None` and racing ahead to release the lock.
    with _lock:
        worker = _conductor
        if worker is None:
            return
        # Counsel N2: a 60s silence during shutdown reads as a hang. Say what
        # is being waited for, before waiting for it.
        log.info(
            "Stopping the intel drainer; waiting up to %.0fs for an in-flight "
            "model call to finish.",
            timeout,
        )
        worker.stop(timeout=timeout)
        _conductor = None
    if not worker.is_alive():
        return
    log.warning(
        "Intel drainer did not stop within %.0fs; the database lock is being "
        "released with %s still in flight. Its executor lease expires and the "
        "next hub's takeover recovers the job (db.intel.take_over_stale_bound_executor).",
        timeout,
        _in_flight_description(),
    )


def _in_flight_description() -> str:
    """Name the meeting/job a stuck drainer is holding, for the warning."""
    try:
        from .db import get_database

        rows = get_database().intel.list_intel_jobs(status="all", limit=20)
        live = [
            job for job in rows
            if str(getattr(job, "status", "")).strip() in {"claimed", "running"}
        ]
        if not live:
            return "an unidentified job (nothing claimed or running in the queue)"
        return ", ".join(
            f"meeting {job.meeting_id} (job {getattr(job, 'job_id', '?')})"
            for job in live
        )
    except Exception as exc:  # pragma: no cover - the warning must never raise
        return f"an unidentified job (queue read failed: {type(exc).__name__}: {exc})"


def current_intel_queue_conductor() -> Any:
    """The live worker, or ``None``."""
    return _conductor


def drainer_state() -> str:
    """``"running"`` when a live drainer will execute the queue, else ``"absent"``."""
    worker = _conductor
    if worker is not None and worker.is_alive():
        return "running"
    return "absent"


def wake_intel_queue_conductor() -> bool:
    """Ask the drainer to drain now. ``False`` when there is no drainer."""
    worker = _conductor
    if worker is None or not worker.is_alive():
        return False
    worker.wake()
    return True
