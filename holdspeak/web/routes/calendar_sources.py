"""HS-175-03: Calendar source status API route.

GET /api/calendar/sources -- per-source facts for the Settings face:
  status (success/failure/idle), label, type (ics/snapshot), host,
  distinct calendar count, last read time, and the auto-record matched
  count for the current week.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
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


def _iso_week_range_utc() -> tuple[str, str]:
    """Return (monday_00:00, next_monday_00:00) in UTC ISO for the current week."""
    now = datetime.now(timezone.utc)
    monday = now - timedelta(days=now.weekday())
    monday_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    next_monday = monday_start + timedelta(days=7)
    return (
        monday_start.isoformat(timespec="seconds").replace("+00:00", "Z"),
        next_monday.isoformat(timespec="seconds").replace("+00:00", "Z"),
    )


def build_calendar_sources_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/calendar/sources", tags=["calendar-sources"])

    @router.get("")
    async def list_sources(request: Request) -> Any:
        """Per-source facts for the Settings Meetings CALENDAR section."""
        try:
            config = Config.load()
            db = get_database()

            sources = config.calendar.sources
            auto_record = config.meeting.auto_record
            lead_minutes = config.meeting.auto_record_lead_minutes

            # Per-source stats from calendar_events.
            source_stats: dict[str, dict[str, Any]] = {}
            try:
                with db._connection() as conn:
                    rows = conn.execute(
                        """SELECT source_id,
                                  COUNT(DISTINCT uid) AS calendar_count,
                                  MAX(last_seen_at) AS last_seen
                           FROM calendar_events
                           GROUP BY source_id"""
                    ).fetchall()
                    for r in rows:
                        sid = str(r["source_id"])
                        source_stats[sid] = {
                            "calendar_count": int(r["calendar_count"]),
                            "last_seen": float(r["last_seen"]) if r["last_seen"] else None,
                        }
            except Exception:
                pass

            # Matched this week: events with calendar_event_projects links.
            week_start, week_end = _iso_week_range_utc()
            matched_this_week = 0
            try:
                with db._connection() as conn:
                    row = conn.execute(
                        """SELECT COUNT(DISTINCT ce.id) AS cnt
                           FROM calendar_events ce
                           INNER JOIN calendar_event_projects cep
                               ON cep.calendar_event_id = ce.id
                           WHERE ce.starts_at >= ? AND ce.starts_at < ?""",
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
                cal_count = stats.get("calendar_count", 0)
                last_seen = stats.get("last_seen")

                # Status: idle (never read), success (has events), failure
                # (placeholder for conductor error tracking; for now idle/success).
                if last_seen is not None and cal_count > 0:
                    status = "success"
                elif last_seen is not None:
                    status = "success"
                else:
                    status = "idle"

                host = _source_host(source)
                label = _source_label(source)
                stype = _source_type(source)

                # Format last_seen as HH:MM.
                last_read = None
                if last_seen is not None:
                    try:
                        dt = datetime.fromtimestamp(last_seen, tz=timezone.utc)
                        last_read = dt.strftime("%H:%M")
                    except Exception:
                        pass

                items.append({
                    "id": sid,
                    "label": label,
                    "type": stype,
                    "status": status,
                    "host": host,
                    "calendar_count": cal_count,
                    "last_read": last_read,
                    "egress": host is not None,
                })

            return JSONResponse({
                "sources": items,
                "auto_record": auto_record,
                "auto_record_lead_minutes": lead_minutes,
                "matched_this_week": matched_this_week,
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to load calendar sources")

    return router
