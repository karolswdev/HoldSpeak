"""Summarise the meetings saved before any engine existed (owner ruling 2026-10-05).

A meeting saved while ``meeting.deferred_analysis`` resolved to no engine gets
no summary job: the queue has no "wait for an engine" state, and a job queued
with no assignment fails when its route plan freezes.  This service pays that
debt once the engine arrives.

The rule:

* When ``meeting.deferred_analysis`` GAINS an engine (no engine -> engine, or
  the first check of this hub process finds one), the meetings that ended
  before that moment and have no summary job are the backlog.
* Each tick queues at most ``limit`` of them, newest first, so the oldest go
  last (the memory conductor's order).  The backlog is drained across ticks.
* Each job goes through the same producer the "Run intelligence" press uses:
  the meeting's summary route is projected (``project_route``) and the job is
  queued with that route (``db.intel.request_intel_retry``).  A route that is
  not ready stops the tick; nothing is queued without an engine.
* Idempotent: a meeting with ANY ``intel_jobs`` row (queued, failed, done) or
  a ``ready`` / ``partial`` / ``queued`` / ``running`` summary is never picked.
  A failed job is the owner's to retry; it is not re-queued here.
* ``meeting.intelligence_auto`` decides scope: ``off`` queues nothing,
  ``room_linked`` only meetings linked to a Room, ``every`` all of them.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional

from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind

log = get_logger("meeting.backlog")

BACKLOG_PRINCIPAL = Principal(PrincipalKind.OWNER, "auto-intel")
BACKLOG_REASON = "auto-intel: saved before an engine existed"
#: Jobs queued per tick.  The drainer runs them one at a time anyway.
BACKLOG_LIMIT = 10


def backlog_meeting_ids(
    db: Any, *, cutoff: str, auto_mode: str, limit: int,
) -> list[str]:
    """Meetings that ended at or before ``cutoff`` with no summary job, newest first."""
    if auto_mode == "off" or limit < 1:
        return []
    room_only = 1 if auto_mode == "room_linked" else 0
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT m.id FROM meetings m
                 WHERE m.parked=0
                   AND m.ended_at IS NOT NULL AND m.ended_at <= ?
                   AND LOWER(COALESCE(m.intel_status,'')) NOT IN ('ready','partial','queued','running')
                   AND EXISTS (SELECT 1 FROM segments s WHERE s.meeting_id=m.id)
                   AND NOT EXISTS (SELECT 1 FROM intel_jobs j WHERE j.meeting_id=m.id)
                   AND (? = 0 OR EXISTS (SELECT 1 FROM meeting_projects mp WHERE mp.meeting_id=m.id))
                 ORDER BY m.ended_at DESC, m.id
                 LIMIT ?""",
            (cutoff, room_only, int(limit)),
        ).fetchall()
    return [str(row["id"]) for row in rows]


def enqueue_backlog(
    db: Any,
    *,
    cutoff: str,
    auto_mode: str,
    limit: int = BACKLOG_LIMIT,
    route_for: Optional[Callable[[Any, str], dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Queue up to ``limit`` backlog meetings through the Run-intelligence producer."""
    if route_for is None:
        from .meeting_route_projection import project_route

        def route_for(database: Any, meeting_id: str) -> dict[str, Any]:
            return project_route(database, invocation_id=f"meeting:{meeting_id}")

    candidates = backlog_meeting_ids(db, cutoff=cutoff, auto_mode=auto_mode, limit=limit)
    queued: list[str] = []
    for meeting_id in candidates:
        route = route_for(db, meeting_id)
        if route.get("status") != "ready":
            # No engine after all (cleared in between): queue nothing more.
            return {"status": "no_route", "queued": queued, "remaining": True}
        outcome = db.intel.request_intel_retry(
            meeting_id, reason=BACKLOG_REASON, planned_route=route,
        )
        if outcome == "queued":
            queued.append(meeting_id)
            _record(db, meeting_id, route)
    remaining = len(candidates) >= limit
    return {"status": "queued" if queued else "empty", "queued": queued, "remaining": remaining}


def _record(db: Any, meeting_id: str, route: dict[str, Any]) -> None:
    """The same ledger event the after-capture auto-intel writes, mode ``backlog``."""
    try:
        from .service_event_ledger import ServiceEventLedger

        host = ((route.get("legs") or [{}])[0] or {}).get("host") or "local"
        with db._connection() as conn:
            ServiceEventLedger(db).append_in_transaction(
                conn, BACKLOG_PRINCIPAL,
                event_type="meeting.auto_intel_enqueued",
                producer="MeetingBacklog",
                subject_ref=f"meeting:{meeting_id}",
                source_revision="",
                facts={"meeting_id": meeting_id, "auto_mode": "backlog", "host": str(host)},
                refs=[f"meeting:{meeting_id}"],
                correlation_id=None,
                causation_id=f"meeting:{meeting_id}",
            )
    except Exception as exc:  # evidence only: the job row is the state
        log.debug("backlog ledger event not written for %s: %s", meeting_id, exc)


class MeetingSummaryBacklog:
    """Watches for ``meeting.deferred_analysis`` gaining an engine; drains the backlog."""

    def __init__(
        self,
        db_factory: Callable[[], Any],
        *,
        has_engine: Optional[Callable[[Any, Principal], bool]] = None,
        auto_mode: Optional[Callable[[], str]] = None,
        limit: int = BACKLOG_LIMIT,
        route_for: Optional[Callable[[Any, str], dict[str, Any]]] = None,
        wake: Optional[Callable[[], Any]] = None,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        if has_engine is None:
            from ..runtime.routing_glue import deferred_analysis_has_engine as has_engine
        self._db_factory = db_factory
        self._has_engine = has_engine
        self._auto_mode = auto_mode or _configured_auto_mode
        self._limit = limit
        self._route_for = route_for
        self._wake = wake
        self._clock = clock
        self._had_engine: Optional[bool] = None
        #: The gain moment while a backlog is being drained; None when idle.
        self._cutoff: Optional[str] = None

    def tick(self) -> dict[str, Any]:
        db = self._db_factory()
        has = bool(self._has_engine(db, BACKLOG_PRINCIPAL))
        gained = has and not self._had_engine
        self._had_engine = has
        if not has:
            self._cutoff = None
            return {"status": "no_engine"}
        if gained:
            self._cutoff = self._clock().isoformat()
        if self._cutoff is None:
            return {"status": "idle"}
        result = enqueue_backlog(
            db, cutoff=self._cutoff, auto_mode=self._auto_mode(),
            limit=self._limit, route_for=self._route_for,
        )
        if not result["remaining"] or not result["queued"]:
            # Drained, or nothing more could be queued: wait for the next gain.
            self._cutoff = None
        if result["queued"]:
            log.info("Queued %d meeting summaries saved before an engine existed.", len(result["queued"]))
            if self._wake is not None:
                try:
                    self._wake()
                except Exception as exc:
                    log.debug("drainer wake failed: %s", exc)
        return result


def _configured_auto_mode() -> str:
    from ..config import Config

    return str(Config.load().meeting.intelligence_auto or "every").strip().lower()
