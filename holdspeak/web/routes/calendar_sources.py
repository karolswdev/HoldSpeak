"""HS-175-03: Calendar source status API route.

GET /api/calendar/sources -- per-source facts for the Settings face:
  status (success/failure/idle), label, type (ics/snapshot), host,
  distinct event count, last read time, the auto-record matched count for
  the current LOCAL week, and the snapshot's vision egress (HS-175 counsel
  C8 / C9b / C10).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...config import Config
from ...config.integrations import (
    CalendarSource,
    _source_label,
    calendar_subscription_summary,
)
from ...db import get_database
from ...logging_config import get_logger
from ...services.project_service import local_week_bounds, utc_z
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.calendar_sources")


def _source_type(source: CalendarSource) -> str:
    """Derive the type token: ICS for file/URL sources, SNAPSHOT for vision."""
    # The snapshot adapter registers sources with label "O365 SNAPSHOT"
    # (calendar_snapshot_service.py:26).  Any source whose label ends with
    # SNAPSHOT is treated as a snapshot source.
    label = (source.label or "").upper()
    if label.endswith("SNAPSHOT"):
        return "SNAPSHOT"
    return "ICS"


def _source_host(source: CalendarSource) -> str | None:
    """Derive the egress host: hostname for HTTPS sources, None for file."""
    url = (source.url or "").strip()
    if not url:
        return None
    parsed = urlsplit(url)
    if parsed.scheme and parsed.scheme.lower() == "https" and parsed.hostname:
        return str(parsed.hostname).lower()
    return None


def _iso_week_range_local(now: datetime | None = None) -> tuple[str, str]:
    """(local Monday 00:00, next local Monday 00:00) as stored-form UTC ``...Z``.

    HS-175 counsel C8: the week is the hub's LOCAL week (one helper,
    ``project_service.local_week_bounds``), compared against the UTC
    ``starts_at`` the ingest stores.
    """
    monday, next_monday = local_week_bounds(now)
    return utc_z(monday), utc_z(next_monday)


def read_calendar_sources(
    config: Config, db: Any, *, now: datetime | None = None,
    snapshot_egress: Any = None,
) -> dict[str, Any]:
    """The GET payload, as a pure read over config + DB (testable).

    ``snapshot_egress`` is the resolved vision egress for the ``Snapshot``
    verb (C10) -- passed in so the route resolves it once; ``None`` when no
    vision model resolves.
    """
    sources = config.calendar.sources
    auto_record = config.meeting.auto_record
    lead_minutes = config.meeting.auto_record_lead_minutes

    # Per-source stats from calendar_events.  C9(b): ``COUNT(DISTINCT uid)``
    # counts EVENTS (VEVENT uids), and the face names it so.
    source_stats: dict[str, dict[str, Any]] = {}
    try:
        with db._connection() as conn:
            rows = conn.execute(
                """SELECT source_id,
                          COUNT(DISTINCT uid) AS event_count,
                          MAX(last_seen_at) AS last_seen
                   FROM calendar_events
                   GROUP BY source_id"""
            ).fetchall()
            for r in rows:
                sid = str(r["source_id"])
                source_stats[sid] = {
                    "event_count": int(r["event_count"]),
                    "last_seen": float(r["last_seen"]) if r["last_seen"] else None,
                }
    except Exception:
        pass

    # Matched this week: linked events inside the hub's local week.
    week_start, week_end = _iso_week_range_local(now)
    matched_this_week = 0
    try:
        with db._connection() as conn:
            row = conn.execute(
                """SELECT COUNT(DISTINCT ce.id) AS cnt
                   FROM calendar_events ce
                   INNER JOIN calendar_event_projects cep
                       ON cep.calendar_event_id = ce.id
                   WHERE cep.match_source != 'suppressed'
                     AND ce.starts_at >= ? AND ce.starts_at < ?""",
                (week_start, week_end),
            ).fetchone()
            if row:
                matched_this_week = int(row["cnt"])
    except Exception:
        pass

    items = []
    for source in sources:
        if not source.enabled:
            continue
        sid = source.id
        stats = source_stats.get(sid, {})
        event_count = stats.get("event_count", 0)
        last_seen = stats.get("last_seen")

        # Status: idle (never read), success (read at least once); failure
        # awaits per-source conductor status (BACKLOG).
        status = "success" if last_seen is not None else "idle"

        host = _source_host(source)
        label = _source_label(source)
        stype = _source_type(source)

        # C8: the last read leaves as an offset-carrying ISO instant so the
        # face prints the VIEWER's local clock; ``last_read`` keeps the
        # hub-local HH:MM for readers that want a string.
        last_read = None
        last_read_at = None
        if last_seen is not None:
            try:
                instant = datetime.fromtimestamp(last_seen, tz=timezone.utc)
                last_read_at = instant.isoformat(timespec="seconds").replace("+00:00", "Z")
                last_read = instant.astimezone().strftime("%H:%M")
            except Exception:
                pass

        items.append({
            "id": sid,
            "label": label,
            "type": stype,
            "status": status,
            "host": host,
            "event_count": event_count,
            "last_read": last_read,
            "last_read_at": last_read_at,
            "egress": host is not None,
        })

    return {
        "sources": items,
        "auto_record": auto_record,
        "auto_record_lead_minutes": lead_minutes,
        "matched_this_week": matched_this_week,
        # C10: {scope, host} of the vision model the next upload reaches,
        # or null when no vision model resolves.
        "snapshot_egress": snapshot_egress,
    }


def build_calendar_sources_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/calendar/sources", tags=["calendar-sources"])

    @router.get("")
    async def list_sources(request: Request) -> Any:
        """Per-source facts for the Settings Meetings CALENDAR section."""
        try:
            config = Config.load()
            db = get_database()
            snapshot_egress = None
            try:
                from ...services.calendar_snapshot_service import resolve_snapshot_egress

                snapshot_egress = resolve_snapshot_egress(db)
            except Exception as exc:
                log.info("snapshot egress unresolved: %s", exc)
            return JSONResponse(
                read_calendar_sources(config, db, snapshot_egress=snapshot_egress)
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to load calendar sources")

    return router
