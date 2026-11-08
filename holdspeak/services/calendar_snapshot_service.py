"""Calendar snapshot extraction and ICS generation service (HS-146-07).

Orchestrates vision-based extraction of calendar events from screenshots,
generates RFC-5545 .ics files, and registers the snapshot as a file-based
CalendarSource through the settings write path.
"""
from __future__ import annotations

import hashlib
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


def _strip_code_fence(text: str) -> str:
    """Strip markdown code fences wrapping a JSON payload (HS-151-04).

    Real vision models (Qwythos-9B proven on metal) habitually wrap JSON
    output in ```json ... ``` fences.  Mirrors the existing precedent in
    project_doc_suggestions._strip_code_fence and voice_resolver.
    """
    match = re.match(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", text, flags=re.DOTALL)
    return match.group(1).strip() if match else text


def parse_extraction_json(raw: str) -> ExtractionResult:
    """Parse and validate the model's extraction JSON.

    Returns a named refusal for unreadable screenshots; never empty success.
    """
    try:
        cleaned = _strip_code_fence(raw.strip())
        data = json.loads(cleaned)
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
        # The times the owner reads off a calendar screenshot are wall-clock
        # LOCAL times; stamping them UTC shifted every imported event by the
        # UTC offset on the rail (close-counsel should-fix, 2026-08-28).
        local_tz = datetime.now().astimezone().tzinfo
        starts_at = datetime(
            event_date.year, event_date.month, event_date.day,
            h_start, m_start, tzinfo=local_tz,
        )
        ends_at = datetime(
            event_date.year, event_date.month, event_date.day,
            h_end, m_end, tzinfo=local_tz,
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


def _snapshot_uid(event: dict[str, Any]) -> str:
    """Content-deterministic UID for snapshot events (D5, HS-147-03).

    sha256(title + "\\0" + starts_at + "\\0" + ends_at + "\\0" + location)[:16]
    + "@holdspeak-snapshot".  Re-confirming identical content yields identical
    uids so linked arms survive re-import.
    """
    parts = "\0".join([
        str(event.get("title") or ""),
        str(event.get("starts_at") or ""),
        str(event.get("ends_at") or ""),
        str(event.get("location") or ""),
    ])
    digest = hashlib.sha256(parts.encode("utf-8")).hexdigest()[:16]
    return f"{digest}@holdspeak-snapshot"


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
        uid = _snapshot_uid(event)
        # Convert honestly to UTC before formatting — string surgery on ISO
        # offsets corrupts any non-UTC timestamp (close-counsel round).
        starts_at = (
            datetime.fromisoformat(event["starts_at"])
            .astimezone(timezone.utc)
            .strftime("%Y%m%dT%H%M%SZ")
        )
        ends_at = (
            datetime.fromisoformat(event["ends_at"])
            .astimezone(timezone.utc)
            .strftime("%Y%m%dT%H%M%SZ")
        )
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


def is_generated_ics(path: Any) -> bool:
    """True when ``path`` is a file INSIDE the snapshot directory -- the
    only files this service ever created and may delete."""
    try:
        candidate = Path(str(path or "")).expanduser().resolve()
        root = snapshot_dir().resolve()
    except Exception:
        return False
    if not str(path or "").strip():
        return False
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return candidate.suffix.lower() == ".ics"


def delete_generated_ics(path: Any, *, db: Any = None) -> bool:
    """HS-175 counsel C4 (the Remove half): delete the ICS the Snapshot verb
    generated when its CalendarSource is removed, receipted
    (``calendar.source.removed`` with the path).

    Custody: only a file inside ``snapshot_dir()`` is ever deleted -- an
    owner's own ICS path (a file source outside the directory) is never
    touched.  Returns True when a file was deleted.  Never raises.
    """
    if not is_generated_ics(path):
        return False
    target = Path(str(path)).expanduser().resolve()
    if not target.is_file():
        return False
    try:
        target.unlink()
    except OSError as exc:
        log.warning("snapshot ICS removal failed for %s: %s", target, exc)
        return False
    _write_snapshot_receipt(
        db, kind="calendar.source.removed", path=str(target),
    )
    log.info("snapshot ICS removed with its source: %s", target)
    return True


def _write_snapshot_receipt(db: Any, *, kind: str, path: str) -> None:
    """Kernel receipt for a snapshot file effect (Article V:2, XI.2).

    Mirrors HeartbeatService._write_receipt; never raises.
    """
    import time as _time

    try:
        if db is None:
            from ..db import get_database
            db = get_database()
        receipt_id = f"snap_rcpt_{uuid.uuid4().hex[:12]}"
        operation_id = f"snap_op_{uuid.uuid4().hex[:12]}"
        idem_key = f"{kind}:{path}:{uuid.uuid4().hex[:8]}"
        now = _time.time()
        outcome = json.dumps({"kind": kind, "path": path}, separators=(",", ":"))
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO kernel_operations
                   (operation_id, request_id, idempotency_key, name, version,
                    principal_kind, principal_identity, target_ref, placement,
                    envelope_sha256, policy_version, authority_basis,
                    state, revision, native_id, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?,?)""",
                (
                    operation_id, idem_key, idem_key, kind, 1,
                    "owner", "settings-write", f"calendar_source_file:{path}",
                    "local", "", "", "owner-remove", "succeeded",
                    operation_id, now, now,
                ),
            )
            conn.execute(
                """INSERT INTO kernel_receipts
                   (receipt_id, operation_id, state, outcome, result_ref, created_at)
                   VALUES (?,?,?,?,?,?)""",
                (receipt_id, operation_id, "succeeded", outcome, f"calendar_source_file:{path}", now),
            )
    except Exception as exc:
        log.warning("snapshot receipt write failed (%s %s): %s", kind, path, exc)


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


def _vision_capable(profile: Any, db: Any) -> bool:
    """Pre-filter: can this profile plausibly handle a vision payload?

    Checks the v2 model-profile capability manifest first (the source of
    truth when a binding exists).  Falls back to the profile kind for
    unbound legacy profiles: ``openAICompatible`` endpoints commonly
    accept multi-part image content; ``onDevice`` GGUF models do not.
    """
    profile_id = str(getattr(profile, "id", "") or "").strip()
    if not profile_id:
        return False
    try:
        with db._connection() as conn:
            row = conn.execute(
                """SELECT capability_manifest_json
                     FROM model_profile_revisions
                    WHERE profile_id = ?
                    ORDER BY revision DESC LIMIT 1""",
                (profile_id,),
            ).fetchone()
            if row is not None:
                manifest = json.loads(str(row["capability_manifest_json"]))
                return "vision" in (manifest.get("claims") or [])
    except Exception:
        pass
    # No v2 profile — fall back to the kind heuristic.
    kind = str(getattr(profile, "kind", "") or "")
    return kind == "openAICompatible"


def extract_via_router(
    principal: Any,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Production extraction: one job through the engine door.

    The engine is the one assigned to ``calendar.snapshot_extract``; with no
    assignment, the nearest ready vision-capable engine (local and LAN before
    cloud). Returns ``{"output": str, "egress": {...}}``: the raw model JSON
    and where the image went. The egress is known before the image leaves and
    is returned on failure too.
    """
    from ..kernel.vision_prompt_adapter import VisionPromptAdapter
    from . import engine_door

    broker = _service()
    egress: dict[str, Any] | None = None
    try:
        from ..db import get_database

        engine, egress = _snapshot_engine(broker, get_database(), capture=True)
        if engine is None:
            return _no_vision(None)
        answer = engine_door.run(
            broker, principal, SNAPSHOT_CAPABILITY_ID, payload, engine=engine,
            contract="calendar.snapshot.extract", adapter=VisionPromptAdapter(),
            invocation_id="snapshot_" + uuid.uuid4().hex,
        )
    except engine_door.EngineDoorError as exc:
        return {
            "output": json.dumps({"error": f"vision_extraction_failed:{exc.outcome or exc.code}", "events": []}),
            "egress": egress,
        }
    except Exception as exc:
        log.warning("Snapshot dispatch failed: %s", exc)
        return _no_vision(egress)
    return {"output": answer.output, "egress": egress}


def _no_vision(egress: dict[str, Any] | None) -> dict[str, Any]:
    return {"output": json.dumps({"error": "no_vision_model_assigned", "events": []}), "egress": egress}


def _snapshot_engine(broker: Any, db: Any, *, capture: bool) -> tuple[Any, dict[str, Any] | None]:
    """The engine a Snapshot runs on and where its image goes: the assigned
    engine, else the first ranked vision target. ``(None, None)`` when there
    is none. ``capture=False`` reads the vision ranking without writing a
    deployment revision (the face's egress chip)."""
    from . import engine_door

    engine = None
    if broker is not None:
        try:
            engine = engine_door.engine_for(broker, SNAPSHOT_CAPABILITY_ID)
        except Exception:  # no assignment, or no broker to read it: the ranking decides
            engine = None
    if engine is not None:
        revision = db.deployment_revisions.get(engine.revision)
        scope = engine_door.egress_of(broker, engine)
        return engine, _egress_for_scope(
            scope, getattr(revision, "endpoint", "") or "", getattr(revision, "node", "") or "",
        )
    targets = _rank_vision_targets(db)
    if not targets:
        return None, None
    target = targets[0]
    scope = _TARGET_BOUNDARY_SCOPE.get(target.boundary, "cloud")
    if not capture:
        deployment = getattr(target, "deployment", None)
        return None, _egress_for_scope(
            scope,
            getattr(deployment, "endpoint", "") if deployment else "",
            getattr(deployment, "node", "") if deployment else "",
        )
    from ..deployment_revisions import capture_deployment_revision

    revision = capture_deployment_revision(db, target)
    return engine_door.Engine(revision.id), _egress_for_scope(
        _TARGET_BOUNDARY_SCOPE.get(revision.boundary, "cloud"),
        revision.endpoint or "",
        getattr(revision, "node", "") or "",
    )


# ── HS-175 counsel C10: ONE egress resolution, read before the upload ──
#
# The dispatch below and the Settings face's chip beside ``Snapshot`` read
# the SAME ranking: the routed assignment's route plan when one exists
# (boundaries ``local < mesh < private_network < cloud``), else the direct
# dispatch's vision-capable profile ranking (``same_device < paired_device
# < private_network < external_service``).  Scope ``local`` carries no
# host; every other scope names the host bytes leave for (a paired
# device names its endpoint host or node).

_TARGET_BOUNDARY_RANK = {
    "same_device": 0, "paired_device": 1,
    "private_network": 2, "external_service": 3,
}
_TARGET_BOUNDARY_SCOPE = {
    "same_device": "local", "paired_device": "mesh",
    "private_network": "private_network",
    "external_service": "cloud",
}
SNAPSHOT_CAPABILITY_ID = "calendar.snapshot_extract"


def _egress_for_scope(scope: str, endpoint: str = "", node: str = "") -> dict[str, Any]:
    """``{"scope", "host"?}`` -- the host for every non-local scope."""
    from urllib.parse import urlparse

    egress: dict[str, Any] = {"scope": scope}
    if scope != "local":
        host = ""
        try:
            host = urlparse(endpoint or "").hostname or ""
        except Exception:
            host = ""
        host = host or (node or "")
        egress["host"] = host
    return egress


def _rank_vision_targets(db: Any) -> list[Any]:
    """Ready, vision-capable targets, nearest boundary first (direct path).

    HS-147-05 pre-filter + HS-175 N4 ranking: local/LAN before cloud so a
    cloud model is only selected when it is the only option.
    """
    from ..inference_targets import target_from_profile

    candidates: list[tuple[int, Any]] = []
    for profile in db.profiles.list():
        if profile.deleted:
            continue
        if not _vision_capable(profile, db):
            continue
        candidate = target_from_profile(profile, db)
        if candidate.ready:
            rank = _TARGET_BOUNDARY_RANK.get(candidate.boundary, 99)
            candidates.append((rank, candidate))
    candidates.sort(key=lambda pair: pair[0])
    return [candidate for _rank, candidate in candidates]


def resolve_snapshot_egress(db: Any = None) -> dict[str, Any] | None:
    """Read-only: where the NEXT Snapshot upload's image would go.

    Returns ``{"scope": "local"}`` / ``{"scope": ..., "host": ...}`` from the
    same resolution ``extract_via_router`` runs on, or ``None`` when no
    vision model is resolvable (the upload would refuse by name,
    ``no_vision_model_assigned``).
    """
    try:
        if db is None:
            from ..db import get_database
            db = get_database()
        try:
            broker = _service()
        except Exception:
            broker = None
        _engine, egress = _snapshot_engine(broker, db, capture=False)
        return egress
    except Exception as exc:
        log.info("Snapshot egress unavailable (%s)", exc)
        return None


