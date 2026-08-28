"""Calendar snapshot extraction and ICS generation service (HS-146-07).

Orchestrates vision-based extraction of calendar events from screenshots,
generates RFC-5545 .ics files, and registers the snapshot as a file-based
CalendarSource through the settings write path.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from ..calendar_ingest import parse_calendar_bytes
from ..config import Config
from ..config.integrations import CalendarSource
from ..logging_config import get_logger

log = get_logger("calendar_snapshot_service")

SNAPSHOT_DIR_NAME = "calendar-snapshots"
SNAPSHOT_SOURCE_LABEL = "O365 SNAPSHOT"
MAX_SCREENSHOTS = 3

EXTRACTION_SYSTEM_PROMPT = """\
You are a calendar event extractor. You receive a screenshot of a week-view \
calendar (typically Outlook/O365). Extract every visible event as structured \
JSON. Return ONLY valid JSON, no commentary.

Output schema:
{
  "anchor_date": "YYYY-MM-DD" or null,
  "anchor_confidence": "visible_header" | "inferred" | "absent",
  "events": [
    {
      "title": "string",
      "weekday": "monday" | "tuesday" | "wednesday" | "thursday" | "friday" | "saturday" | "sunday",
      "start_time": "HH:MM",
      "end_time": "HH:MM",
      "location": "string or null"
    }
  ]
}

Rules:
- anchor_date: the Monday of the displayed week if visible in a header; \
null if not visible.
- anchor_confidence: "visible_header" when the date header is clearly \
readable; "inferred" when the date can be guessed from context; \
"absent" when no date information is visible.
- If the screenshot is unreadable or not a calendar, return: \
{"error": "unreadable_screenshot", "events": []}
- Weekday must be lowercase English.
- Times in 24-hour HH:MM format.
- Extract ALL visible events, including short ones."""

EXTRACTION_USER_PROMPT = "Extract all calendar events from this screenshot."

WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

VALID_WEEKDAYS = frozenset(WEEKDAY_MAP.keys())
VALID_CONFIDENCES = frozenset({"visible_header", "inferred", "absent"})
TIME_RE = re.compile(r"^\d{2}:\d{2}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class ExtractedEvent:
    """One event extracted from a screenshot."""

    title: str
    weekday: str
    start_time: str
    end_time: str
    location: str | None = None


@dataclass(frozen=True)
class ExtractionResult:
    """Result of vision extraction from one or more screenshots."""

    anchor_date: str | None
    anchor_confidence: str
    events: list[ExtractedEvent]
    error: str | None = None


def parse_extraction_json(raw: str) -> ExtractionResult:
    """Parse and validate the model's extraction JSON.

    Returns a named refusal for unreadable screenshots; never empty success.
    """
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return ExtractionResult(
            anchor_date=None,
            anchor_confidence="absent",
            events=[],
            error="unreadable_screenshot",
        )

    if not isinstance(data, dict):
        return ExtractionResult(
            anchor_date=None,
            anchor_confidence="absent",
            events=[],
            error="unreadable_screenshot",
        )

    if data.get("error"):
        return ExtractionResult(
            anchor_date=None,
            anchor_confidence="absent",
            events=[],
            error=str(data["error"]),
        )

    anchor_date = data.get("anchor_date")
    if anchor_date and not DATE_RE.match(str(anchor_date)):
        anchor_date = None

    confidence = str(data.get("anchor_confidence", "absent"))
    if confidence not in VALID_CONFIDENCES:
        confidence = "absent"

    raw_events = data.get("events", [])
    if not isinstance(raw_events, list):
        return ExtractionResult(
            anchor_date=anchor_date,
            anchor_confidence=confidence,
            events=[],
            error="unreadable_screenshot",
        )

    events: list[ExtractedEvent] = []
    for entry in raw_events:
        if not isinstance(entry, dict):
            continue
        title = str(entry.get("title", "")).strip()
        weekday = str(entry.get("weekday", "")).lower().strip()
        start_time = str(entry.get("start_time", "")).strip()
        end_time = str(entry.get("end_time", "")).strip()
        location = entry.get("location")
        if location is not None:
            location = str(location).strip() or None

        if not title or weekday not in VALID_WEEKDAYS:
            continue
        if not TIME_RE.match(start_time) or not TIME_RE.match(end_time):
            continue

        events.append(
            ExtractedEvent(
                title=title,
                weekday=weekday,
                start_time=start_time,
                end_time=end_time,
                location=location,
            )
        )

    if not events and not data.get("error"):
        return ExtractionResult(
            anchor_date=anchor_date,
            anchor_confidence=confidence,
            events=[],
            error="unreadable_screenshot",
        )

    return ExtractionResult(
        anchor_date=str(anchor_date) if anchor_date else None,
        anchor_confidence=confidence,
        events=events,
    )


def merge_extractions(results: list[ExtractionResult]) -> ExtractionResult:
    """Merge multiple screenshot extractions with exact-match dedup."""
    if len(results) == 1:
        return results[0]

    anchor_date: str | None = None
    anchor_confidence = "absent"
    all_events: list[ExtractedEvent] = []
    seen: set[tuple[str, str, str, str]] = set()
    any_error = True

    for result in results:
        if result.error:
            continue
        any_error = False
        if result.anchor_date and anchor_confidence != "visible_header":
            anchor_date = result.anchor_date
            anchor_confidence = result.anchor_confidence
        for event in result.events:
            key = (event.title, event.weekday, event.start_time, event.end_time)
            if key not in seen:
                seen.add(key)
                all_events.append(event)

    if any_error and not all_events:
        return ExtractionResult(
            anchor_date=None,
            anchor_confidence="absent",
            events=[],
            error="unreadable_screenshot",
        )

    return ExtractionResult(
        anchor_date=anchor_date,
        anchor_confidence=anchor_confidence,
        events=all_events,
    )


def resolve_anchor_date(anchor_str: str) -> date:
    """Parse an anchor date string to a date, raising ValueError if invalid."""
    try:
        d = date.fromisoformat(anchor_str)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid anchor date: {anchor_str}") from exc
    # Snap to Monday of that week
    return d - timedelta(days=d.weekday())


def resolve_events_to_timestamps(
    events: list[ExtractedEvent],
    anchor_monday: date,
) -> list[dict[str, Any]]:
    """Resolve weekday + time to absolute ISO timestamps."""
    resolved: list[dict[str, Any]] = []
    for event in events:
        day_offset = WEEKDAY_MAP[event.weekday]
        event_date = anchor_monday + timedelta(days=day_offset)
        h_start, m_start = int(event.start_time[:2]), int(event.start_time[3:])
        h_end, m_end = int(event.end_time[:2]), int(event.end_time[3:])
        starts_at = datetime(
            event_date.year, event_date.month, event_date.day,
            h_start, m_start, tzinfo=timezone.utc,
        )
        ends_at = datetime(
            event_date.year, event_date.month, event_date.day,
            h_end, m_end, tzinfo=timezone.utc,
        )
        resolved.append({
            "title": event.title,
            "weekday": event.weekday,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "location": event.location,
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
        })
    return resolved


def generate_ics(
    events: list[dict[str, Any]],
    *,
    source_id: str,
) -> bytes:
    """Generate a minimal RFC-5545 .ics from resolved events."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//HoldSpeak//CalendarSnapshot//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for event in events:
        uid = f"{uuid.uuid4()}@holdspeak-snapshot"
        starts_at = event["starts_at"].replace("-", "").replace(":", "").replace("+00:00", "Z")
        if not starts_at.endswith("Z"):
            starts_at = starts_at.split("+")[0] + "Z"
        ends_at = event["ends_at"].replace("-", "").replace(":", "").replace("+00:00", "Z")
        if not ends_at.endswith("Z"):
            ends_at = ends_at.split("+")[0] + "Z"
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTART:{starts_at}")
        lines.append(f"DTEND:{ends_at}")
        lines.append(f"SUMMARY:{_ics_escape(event['title'])}")
        if event.get("location"):
            lines.append(f"LOCATION:{_ics_escape(event['location'])}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


def _ics_escape(text: str) -> str:
    """Escape text for ICS property values."""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def snapshot_dir() -> Path:
    """The canonical directory for snapshot .ics files."""
    return Path.home() / ".local" / "share" / "holdspeak" / SNAPSHOT_DIR_NAME


def write_ics_atomic(source_id: str, ics_bytes: bytes) -> Path:
    """Write .ics atomically (temp + rename) to the snapshot directory."""
    directory = snapshot_dir()
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{source_id}.ics"
    fd, tmp_path = tempfile.mkstemp(dir=str(directory), suffix=".ics.tmp")
    try:
        os.write(fd, ics_bytes)
        os.close(fd)
        os.replace(tmp_path, str(target))
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return target


def register_snapshot_source(
    source_id: str,
    ics_path: Path,
    *,
    settings_service: Any,
    principal: Any,
) -> dict[str, Any]:
    """Register or update the snapshot CalendarSource via the settings write path.

    Uses the settings service's validated write path ONLY — no side door.
    """
    config = Config.load()
    existing = [s for s in config.calendar.sources if s.id == source_id]
    if existing:
        # Update the existing source's URL to point to the ICS file
        sources = [
            {
                "id": s.id,
                "label": s.label if s.id != source_id else SNAPSHOT_SOURCE_LABEL,
                "url": str(ics_path) if s.id == source_id else s.url,
                "enabled": s.enabled,
            }
            for s in config.calendar.sources
        ]
    else:
        # Add a new source
        sources = [
            {"id": s.id, "label": s.label, "url": s.url, "enabled": s.enabled}
            for s in config.calendar.sources
        ]
        sources.append({
            "id": source_id,
            "label": SNAPSHOT_SOURCE_LABEL,
            "url": str(ics_path),
            "enabled": True,
        })

    return settings_service.update_settings(
        principal,
        {"calendar": {"sources": sources}},
    )


def trigger_calendar_refresh() -> bool:
    """Poke the module-level conductor to refresh immediately."""
    from ..calendar_ingest_conductor import _conductor

    if _conductor is not None:
        return _conductor.refresh()
    return False


def _service():
    """Late-bound broker accessor (patchable in tests)."""
    from ..kernel.runtime import _service as runtime_service
    return runtime_service()


def extract_via_router(
    principal: Any,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Production extraction: dispatch through the real inference machinery.

    Template: AskService (ask_service.py:209+) — dual-path: the routed admission
    path (Phase 143 assignments) when configured, falling back to a direct
    InferenceRunner dispatch (the same path the ask spine test exercises) when
    no assignment exists.

    Returns {"output": str, "egress": {...}} where output is the raw model
    JSON and egress carries the resolved boundary truth.
    """
    from ..kernel.runtime import _as_principal
    from ..kernel.vision_prompt_adapter import VisionPromptAdapter
    from ..kernel.inference_runner import InvocationRequest, ServiceContract
    from ..kernel.model import KernelRefused
    from .errors import ServiceError

    broker = _service()
    adoption = broker.inference_adoption_service

    invocation_id = "snapshot_" + uuid.uuid4().hex
    command_id = f"admit-{invocation_id}"

    # Try the routed admission path first (Phase 143 assignments)
    try:
        admitted = adoption.admit(
            principal,
            command_id=command_id,
            capability_id="calendar.snapshot_extract",
            operation_id=invocation_id,
            payload=payload,
            invocation_id=invocation_id,
            reserved_output_tokens=4096,
        )
    except Exception as exc:
        code = getattr(exc, "code", "")
        log.info("Snapshot routed admission unavailable (code=%s), trying direct dispatch", code)
        # Fall through to the direct dispatch path below
        admitted = None

    if admitted is not None:
        # --- Routed path: assignment found, dispatch through the controller ---
        route_plan = admitted.get("route_plan", {})
        entries = route_plan.get("entries", ())
        boundary_rank = {"local": 0, "mesh": 1, "private_network": 2, "cloud": 3}
        boundaries = [str(e.get("boundary", "")) for e in entries]
        widest = max(boundaries, key=lambda b: boundary_rank.get(b, 0)) if boundaries else "local"
        egress: dict[str, Any] = {"scope": widest}
        if widest in {"cloud", "private_network"}:
            for entry in entries:
                if str(entry.get("boundary", "")) == widest:
                    dep_id = str(entry.get("deployment_revision_id", ""))
                    if dep_id:
                        try:
                            from ..db import get_database
                            with get_database()._connection() as conn:
                                row = conn.execute(
                                    "SELECT endpoint FROM deployment_revisions WHERE id=?",
                                    (dep_id,),
                                ).fetchone()
                                if row:
                                    from urllib.parse import urlparse
                                    egress["host"] = urlparse(str(row["endpoint"])).hostname or ""
                        except Exception:
                            pass
                    break

        adapter = VisionPromptAdapter()
        routed = adoption.execute(
            principal,
            execution_id=str(admitted["execution"]["id"]),
            adapter=adapter,
        )
        if routed["outcome"] != "succeeded" or not isinstance(routed.get("result"), dict):
            receipt = routed.get("receipt", {})
            receipt_outcome = str(receipt.get("outcome", ""))
            return {
                "output": json.dumps({
                    "error": f"vision_extraction_failed:{receipt_outcome}",
                    "events": [],
                }),
                "egress": egress,
            }
        raw_output = str(routed["result"].get("output", ""))
        return {"output": raw_output, "egress": egress}

    # --- Direct dispatch path: no assignment, use the runner directly ---
    # Template: AskService legacy path (ask_service.py:307-356) — resolve
    # placement, capture deployment, dispatch through the runner with the
    # VisionPromptAdapter.
    import time
    from ..deployment_revisions import capture_deployment_revision
    from ..inference_targets import resolve_placement

    runner = broker.inference_runner
    adapter = VisionPromptAdapter()
    try:
        from ..db import get_database
        db = get_database()
        # Try each available profile for a ready target
        target = None
        for profile in db.profiles.list():
            if profile.deleted:
                continue
            from ..inference_targets import target_from_profile
            candidate = target_from_profile(profile, db)
            if candidate.ready:
                target = candidate
                break
        if target is None:
            placement = resolve_placement(db)
            target = placement.target
        if not target.ready:
            return {
                "output": json.dumps({
                    "error": "no_vision_model_assigned",
                    "events": [],
                }),
                "egress": None,
            }
        revision = capture_deployment_revision(db, target)
        captured_result: list[dict[str, Any]] = []

        def publish_capture(output: Any) -> str:
            if isinstance(output, dict):
                captured_result.append(dict(output))
            return f"snapshot:{invocation_id}"

        with _as_principal(principal):
            outcome = runner.invoke(
                InvocationRequest(
                    revision.id,
                    ServiceContract.for_payload(
                        "calendar.snapshot.extract", "1", payload,
                    ),
                    time.time() + 120,
                    payload,
                    invocation_id,
                ),
                adapter,
                publish=publish_capture,
            )
    except (KernelRefused, Exception) as exc:
        log.warning("Snapshot direct dispatch failed: %s", exc)
        return {
            "output": json.dumps({
                "error": "no_vision_model_assigned",
                "events": [],
            }),
            "egress": None,
        }

    if outcome.outcome == "succeeded" and captured_result:
        raw_output = str(captured_result[0].get("output", ""))
        provider = str(captured_result[0].get("provider", ""))
        scope = "local" if provider == "local" else "cloud"
        return {"output": raw_output, "egress": {"scope": scope}}

    return {
        "output": json.dumps({
            "error": "no_vision_model_assigned",
            "events": [],
        }),
        "egress": None,
    }
