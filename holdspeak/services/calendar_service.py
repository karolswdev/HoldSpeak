"""The calendar's reads and the snapshot's two steps, as one service (2026-11-09, ops/connections).

``GET /api/calendar/sources`` and ``POST /api/calendar/snapshot/confirm`` are
produced from ``holdspeak/calendar_operations.py``; the screenshot upload
(``POST /api/calendar/snapshot``) stays a hand-written route, because a
produced route takes no file, and calls :meth:`CalendarService.extract`.
The source facts (HS-175-03), the extraction (HS-146-07) and the confirm
moved here from the route modules unchanged.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

from ..config import Config
from ..config.integrations import CalendarSource, _source_label
from ..logging_config import get_logger
from .calendar_snapshot_service import (
    MAX_SCREENSHOTS,
    SNAPSHOT_SOURCE_LABEL,
    ExtractionResult,
    generate_ics,
    merge_extractions,
    parse_extraction_json,
    register_snapshot_source,
    resolve_anchor_date,
    resolve_events_to_timestamps,
    trigger_calendar_refresh,
    write_ics_atomic,
)
from .errors import ServiceError
from .project_definitions import local_week_bounds, utc_z

log = get_logger("services.calendar")

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB per file

IMAGE_MEDIA_TYPES = {
    "image/png": "image/png",
    "image/jpeg": "image/jpeg",
    "image/jpg": "image/jpeg",
    "image/webp": "image/webp",
}


class CalendarRefused(ServiceError):
    """A snapshot step refused: ``{success: false, error}`` with its status (422)."""

    def __init__(self, detail: str, status: int = 422) -> None:
        super().__init__("calendar_snapshot_refused", detail, context={"status": status})


def _source_type(source: CalendarSource) -> str:
    """Derive the type token: ICS for file/URL sources, SNAPSHOT for vision."""
    # The snapshot adapter registers sources with label "O365 SNAPSHOT"
    # (calendar_snapshot_service.py:26).  Any source whose label ends with
    # SNAPSHOT is treated as a snapshot source.
    label = (source.label or "").upper()
    if label.endswith("SNAPSHOT"):
        return "SNAPSHOT"
    # A calendar in the macOS Calendar app (holdspeak/macos_calendar.py).
    if (source.url or "").strip().lower().startswith("eventkit:"):
        return "MACOS"
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


class CalendarService:
    """The Settings calendar facts and the Snapshot verb's extract and confirm.

    ``source``: the hub's context, read at each call (``settings_service``, the
    test seam ``_snapshot_extractor``). ``db``: the database; ``None`` reads the
    process's one database at each call.
    """

    def __init__(self, source: Any = None, *, db: Any = None) -> None:
        self._source = source
        self._db = db

    def _database(self) -> Any:
        if self._db is not None:
            return self._db
        from ..db import get_database

        return get_database()

    def sources(self, principal: Any) -> dict[str, Any]:
        """Per-source facts for the Settings calendar section (HS-175-03)."""
        db = self._database()
        snapshot_egress = None
        try:
            from .calendar_snapshot_service import resolve_snapshot_egress

            snapshot_egress = resolve_snapshot_egress(db)
        except Exception as exc:
            log.info("snapshot egress unresolved: %s", exc)
        return read_calendar_sources(Config.load(), db, snapshot_egress=snapshot_egress)

    def extract(self, principal: Any, images: list[tuple[str, bytes]]) -> dict[str, Any]:
        """Read the week's events from up to MAX_SCREENSHOTS images ``(content type, bytes)`` with the vision model."""
        if len(images) > MAX_SCREENSHOTS:
            raise CalendarRefused(f"At most {MAX_SCREENSHOTS} screenshots allowed")
        if not images:
            raise CalendarRefused("No files provided")
        extractions: list[ExtractionResult] = []
        per_image_egress = None
        for idx, (content_type, raw) in enumerate(images):
            content_type = (content_type or "").lower()
            if content_type not in IMAGE_MEDIA_TYPES:
                raise CalendarRefused(f"File {idx + 1}: unsupported type {content_type}; use PNG, JPEG, or WebP")
            if len(raw) > MAX_FILE_BYTES:
                raise CalendarRefused(f"File {idx + 1}: exceeds 10 MB limit")
            payload = {
                "system_prompt": EXTRACTION_SYSTEM_PROMPT,
                "user_prompt": EXTRACTION_USER_PROMPT,
                "image_base64": base64.b64encode(raw).decode("ascii"),
                "image_media_type": IMAGE_MEDIA_TYPES[content_type],
            }
            # Test seam: an injected extractor; the default is the engine door's vision call.
            extractor = getattr(self._source, "_snapshot_extractor", None)
            if extractor:
                raw_output = extractor(payload)
                per_image_egress = None
            else:
                from .calendar_snapshot_service import extract_via_router

                routed = extract_via_router(principal, payload)
                raw_output = routed["output"]
                per_image_egress = routed.get("egress")
            extractions.append(parse_extraction_json(raw_output))
        merged = merge_extractions(extractions)
        response: dict[str, Any] = {
            "success": True,
            "anchor_date": merged.anchor_date,
            "anchor_confidence": merged.anchor_confidence,
            "events": [{"title": e.title, "weekday": e.weekday, "start_time": e.start_time,
                        "end_time": e.end_time, "location": e.location} for e in merged.events],
            "error": merged.error,
        }
        # Egress truth from the resolved assignment's frozen route.
        if per_image_egress is not None:
            response["egress"] = per_image_egress
        return response

    def confirm(self, principal: Any, anchor_date: Any, events: Any) -> dict[str, Any]:
        """Write the reviewed events as an ICS file and add it as the snapshot calendar source."""
        from .calendar_snapshot_service import ExtractedEvent

        if not anchor_date:
            raise CalendarRefused("anchor_date is required")
        try:
            anchor_monday = resolve_anchor_date(str(anchor_date))
        except ValueError as exc:
            raise CalendarRefused(str(exc)) from exc
        if not isinstance(events, list):
            raise CalendarRefused("events must be a list")
        resolved = resolve_events_to_timestamps([
            ExtractedEvent(
                title=str(entry.get("title", "")),
                # The extract path lower-cases it too; WEEKDAY_MAP keys are lower-case.
                weekday=str(entry.get("weekday", "")).lower().strip(),
                start_time=str(entry.get("start_time", "")),
                end_time=str(entry.get("end_time", "")),
                location=entry.get("location"),
            )
            for entry in events if isinstance(entry, dict)
        ], anchor_monday)
        # The snapshot source: reuse the one there is, else a new id.
        source_id = next((s.id for s in Config.load().calendar.sources if s.label == SNAPSHOT_SOURCE_LABEL), "")
        if not source_id:
            import uuid

            source_id = str(uuid.uuid4())
        ics_bytes = generate_ics(resolved, source_id=source_id)
        # The bounded ICS parser is the ONE trust boundary: model output goes through it like any hostile feed.
        from ..calendar_ingest import parse_calendar_bytes

        parsed = parse_calendar_bytes(ics_bytes, now=datetime.now(timezone.utc),
                                      subscription_revision=f"snapshot:{source_id}")
        if not parsed.succeeded:
            raise CalendarRefused(f"Generated ICS failed parser validation: {parsed.feed_error}")
        ics_path = write_ics_atomic(source_id, ics_bytes)
        settings_service = getattr(self._source, "settings_service", None)
        if settings_service:
            register_snapshot_source(source_id, ics_path, settings_service=settings_service, principal=principal)
        trigger_calendar_refresh()
        return {"success": True, "source_id": source_id, "source_label": SNAPSHOT_SOURCE_LABEL,
                "events_count": len(resolved), "ics_path": str(ics_path)}


from .calendar_snapshot_service import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_USER_PROMPT  # noqa: E402
