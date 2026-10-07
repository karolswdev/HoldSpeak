"""Summarise the meetings saved while no engine could (owner ruling 2026-10-05).

A meeting saved while ``meeting.deferred_analysis`` had no ready route gets no
summary job: a job queued with no route fails when its plan freezes.  This
module pays that debt, and only that debt.

The rule:

* **The mark is durable and per meeting.**  At Stop, a meeting with a
  transcript whose summary route is not ready is marked
  ``summary_deferred_no_engine`` (table ``meeting_summary_backlog``).  The
  backlog is exactly the marked meetings: never inferred from a restart, a
  clock, or an "engine gained" moment.  A meeting saved WITH an engine is never
  marked, so the backlog never queues it (the Stop decision of HS-201-02 stands:
  ``runtime/meeting_glue.py``).
* **Skip clears it.**  ``MeetingIntelService.skip_recovery`` removes the mark;
  a skipped meeting is never queued.
* **Same route as the queue.**  Each marked meeting's route is projected with
  ``project_route`` (the queue's own service route for
  ``meeting.deferred_analysis``; meeting-intel-queue@2 inherits the owner's
  global "Default for AI work").  Not ready: the marks stay, and the next tick
  tries again.  Pending work is never dropped.
* **Consent.**  The backlog drains by itself only to an engine whose
  assignment runs on this machine (LOCAL lamp) or that the owner chose by his
  own press (``made_by='owner'``).  Anything else: the marks wait.
* **Bounded.**  At most ``limit`` jobs per tick, newest first (oldest last),
  through the "Run intelligence" producer (``db.intel.request_intel_retry``
  with the projected route).  A queued job removes the mark.
* ``meeting.intelligence_auto``: ``off`` drains nothing (marks stay),
  ``room_linked`` only meetings linked to a Room, ``every`` all marked ones.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Optional

from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind

log = get_logger("meeting.backlog")

BACKLOG_PRINCIPAL = Principal(PrincipalKind.OWNER, "auto-intel")
BACKLOG_REASON = "auto-intel: saved before an engine could summarise it"
#: The receipt on a meeting OFF skipped, queued again once summaries are on.
SUMMARIES_ON_REASON = "SUMMARIES ON · queued"
MARK_REASON = "summary_deferred_no_engine"
#: Jobs queued per tick.  The drainer runs them one at a time anyway.
BACKLOG_LIMIT = 10
CAPABILITY_ID = "meeting.deferred_analysis"

RouteFor = Callable[[Any, str], dict[str, Any]]


def _project_route(db: Any, meeting_id: str) -> dict[str, Any]:
    from .meeting_route_projection import project_route

    return project_route(db, invocation_id=f"meeting:{meeting_id}")


def mark_if_no_engine(db: Any, meeting_id: str, *, route_for: Optional[RouteFor] = None) -> bool:
    """At save: mark a transcript-bearing meeting whose summary route is not ready."""
    with db._connection() as conn:
        has_transcript = conn.execute(
            "SELECT 1 FROM segments WHERE meeting_id=? LIMIT 1", (str(meeting_id),)
        ).fetchone() is not None
    if not has_transcript:
        return False
    route = (route_for or _project_route)(db, str(meeting_id))
    if route.get("status") == "ready":
        return False
    if _is_off(db, route):
        # PHILO-15 01 ruling: OFF is the owner's choice, not a missing
        # engine. Nothing is marked, so nothing waits for an engine.
        return False
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meeting_summary_backlog (meeting_id, reason, marked_at) VALUES (?,?,?)",
            (str(meeting_id), MARK_REASON, datetime.now(timezone.utc).isoformat()),
        )
    return True


def _reason_for(db: Any, meeting_id: str) -> str:
    """A meeting OFF skipped carries the SUMMARIES ON receipt; others the backlog's."""
    from ..db.intel import SUMMARIES_OFF_DETAIL

    with db._connection() as conn:
        row = conn.execute(
            "SELECT intel_status, intel_status_detail FROM meetings WHERE id=?", (str(meeting_id),)
        ).fetchone()
    if row is not None and row["intel_status"] == "skipped" and row["intel_status_detail"] == SUMMARIES_OFF_DETAIL:
        return SUMMARIES_ON_REASON
    return BACKLOG_REASON


def _is_off(db: Any, route: Optional[dict[str, Any]]) -> bool:
    from .meeting_route_projection import route_is_off, summaries_off

    return route_is_off(route) or summaries_off(db)


def clear_mark(db: Any, meeting_id: str) -> None:
    with db._connection() as conn:
        conn.execute("DELETE FROM meeting_summary_backlog WHERE meeting_id=?", (str(meeting_id),))


def marked_meeting_ids(db: Any, *, auto_mode: str, limit: int) -> list[str]:
    """Marked meetings still without a summary job, newest first."""
    if auto_mode == "off" or limit < 1:
        return []
    room_only = 1 if auto_mode == "room_linked" else 0
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT b.meeting_id FROM meeting_summary_backlog b
                 JOIN meetings m ON m.id=b.meeting_id
                WHERE NOT EXISTS (SELECT 1 FROM intel_jobs j WHERE j.meeting_id=b.meeting_id
                                    AND j.status NOT IN ('skipped','superseded'))
                  AND LOWER(COALESCE(m.intel_status,'')) NOT IN ('ready','partial','queued','running')
                  AND (? = 0 OR EXISTS (SELECT 1 FROM meeting_projects mp WHERE mp.meeting_id=b.meeting_id))
                ORDER BY COALESCE(m.ended_at, m.started_at) DESC, b.meeting_id
                LIMIT ?""",
            (room_only, int(limit)),
        ).fetchall()
    return [str(row["meeting_id"]) for row in rows]


def backlog_consent(db: Any) -> dict[str, Any]:
    """May the backlog drain by itself?  LOCAL, or chosen by the owner's press.

    Reads the assignment the queue route resolves through (capability, then
    group, then global; meeting-intel-queue@2).
    """
    from ..inference_capabilities import process_inference_capability_registry
    from ..inference_locality import assignment_lamp

    capability = process_inference_capability_registry().require(CAPABILITY_ID)
    keys = (f"capability:{CAPABILITY_ID}", f"group:{capability.group_id}", "global")
    with db._connection() as conn:
        for key in keys:
            row = conn.execute(
                """SELECT h.assignment_id,h.revision,r.made_by
                     FROM inference_assignment_heads h
                     JOIN inference_assignment_revisions r
                       ON r.assignment_id=h.assignment_id AND r.revision=h.revision
                    WHERE h.assignment_key=? AND h.cleared=0""",
                (key,),
            ).fetchone()
            if row is None:
                continue
            lamp = assignment_lamp(conn, str(row["assignment_id"]), int(row["revision"]))
            made_by = str(row["made_by"])
            return {
                "allowed": lamp == "local" or made_by == "owner",
                "lamp": lamp, "made_by": made_by, "source": key,
            }
    return {"allowed": False, "lamp": None, "made_by": None, "source": None}


def drain_backlog(
    db: Any,
    *,
    auto_mode: str,
    limit: int = BACKLOG_LIMIT,
    route_for: Optional[RouteFor] = None,
) -> dict[str, Any]:
    """Queue up to ``limit`` marked meetings; marks stay whenever a job is not queued."""
    route_for = route_for or _project_route
    if _is_off(db, None):
        # PHILO-15 01 ruling: under OFF the backlog queues nothing and waits
        # for nothing. Marks made before OFF stay; when OFF clears, they
        # drain as before.
        return {"status": "summaries_off", "queued": []}
    candidates = marked_meeting_ids(db, auto_mode=auto_mode, limit=limit)
    if not candidates:
        return {"status": "idle", "queued": []}
    consent = backlog_consent(db)
    if not consent["allowed"]:
        return {"status": "waiting_consent", "queued": [], "consent": consent}
    queued: list[str] = []
    for meeting_id in candidates:
        route = route_for(db, meeting_id)
        if route.get("status") != "ready":
            # Detection and routing are the same call: not ready means wait.
            return {"status": "waiting_route", "queued": queued}
        outcome = db.intel.request_intel_retry(
            meeting_id, reason=_reason_for(db, meeting_id), planned_route=route,
        )
        if outcome == "queued":
            clear_mark(db, meeting_id)
            queued.append(meeting_id)
            _record(db, meeting_id, route)
        elif outcome in {"ready", "empty", "missing"}:
            clear_mark(db, meeting_id)  # nothing left to summarise
    return {"status": "queued" if queued else "idle", "queued": queued}


def _record(db: Any, meeting_id: str, route: dict[str, Any]) -> None:
    """The ledger event the after-capture auto-intel writes, mode ``backlog``."""
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
    """One tick of the defaults watcher: drain the marked meetings, bounded."""

    def __init__(
        self,
        db_factory: Callable[[], Any],
        *,
        auto_mode: Optional[Callable[[], str]] = None,
        limit: int = BACKLOG_LIMIT,
        route_for: Optional[RouteFor] = None,
        wake: Optional[Callable[[], Any]] = None,
    ) -> None:
        self._db_factory = db_factory
        self._auto_mode = auto_mode or _configured_auto_mode
        self._limit = limit
        self._route_for = route_for
        self._wake = wake

    def tick(self) -> dict[str, Any]:
        result = drain_backlog(
            self._db_factory(), auto_mode=self._auto_mode(),
            limit=self._limit, route_for=self._route_for,
        )
        if result["queued"]:
            log.info("Queued %d meeting summaries saved while no engine could run them.", len(result["queued"]))
            if self._wake is not None:
                try:
                    self._wake()
                except Exception as exc:
                    log.debug("drainer wake failed: %s", exc)
        return result


def _configured_auto_mode() -> str:
    from ..config import Config

    return str(Config.load().meeting.intelligence_auto or "every").strip().lower()
