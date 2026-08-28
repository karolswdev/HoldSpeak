"""Calendar snapshot upload and confirm route (HS-146-07).

POST /api/calendar/snapshot — upload screenshot(s), extract events via vision.
POST /api/calendar/snapshot/confirm — confirm reviewed events, write .ics.
"""
from __future__ import annotations

import base64
from typing import Any

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import JSONResponse

from ...config import Config
from ...principals import UNAUTHENTICATED
from ...services.calendar_snapshot_service import (
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
from ..context import WebContext

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB per file

IMAGE_MEDIA_TYPES = {
    "image/png": "image/png",
    "image/jpeg": "image/jpeg",
    "image/jpg": "image/jpeg",
    "image/webp": "image/webp",
}


def build_calendar_snapshot_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/calendar/snapshot", tags=["calendar-snapshot"])

    @router.post("")
    async def extract_snapshot(request: Request, files: list[UploadFile] = File(...)) -> Any:
        if len(files) > MAX_SCREENSHOTS:
            return JSONResponse(
                {"success": False, "error": f"At most {MAX_SCREENSHOTS} screenshots allowed"},
                status_code=422,
            )

        if not files:
            return JSONResponse(
                {"success": False, "error": "No files provided"},
                status_code=422,
            )

        extractions: list[ExtractionResult] = []
        for idx, upload in enumerate(files):
            content_type = (upload.content_type or "").lower()
            if content_type not in IMAGE_MEDIA_TYPES:
                return JSONResponse(
                    {
                        "success": False,
                        "error": f"File {idx + 1}: unsupported type {content_type}; "
                        "use PNG, JPEG, or WebP",
                    },
                    status_code=422,
                )

            raw = await upload.read()
            if len(raw) > MAX_FILE_BYTES:
                return JSONResponse(
                    {
                        "success": False,
                        "error": f"File {idx + 1}: exceeds 10 MB limit",
                    },
                    status_code=422,
                )

            image_b64 = base64.b64encode(raw).decode("ascii")
            media_type = IMAGE_MEDIA_TYPES[content_type]

            # Build the extraction payload for the vision model
            extraction_payload = {
                "system_prompt": _extraction_system_prompt(),
                "user_prompt": _extraction_user_prompt(),
                "image_base64": image_b64,
                "image_media_type": media_type,
            }

            # Test seam: injected extractor for unit/e2e tests.
            # Default: the production router dispatch through the real
            # inference machinery (admission -> runner -> vision adapter).
            extractor = getattr(ctx, "_snapshot_extractor", None)
            if extractor:
                raw_output = extractor(extraction_payload)
                per_image_egress = None
            else:
                from ...services.calendar_snapshot_service import extract_via_router

                principal = getattr(request.state, "principal", UNAUTHENTICATED)
                routed = extract_via_router(principal, extraction_payload)
                raw_output = routed["output"]
                per_image_egress = routed.get("egress")

            result = parse_extraction_json(raw_output)
            extractions.append(result)

        merged = merge_extractions(extractions)

        response: dict[str, Any] = {
            "success": True,
            "anchor_date": merged.anchor_date,
            "anchor_confidence": merged.anchor_confidence,
            "events": [
                {
                    "title": e.title,
                    "weekday": e.weekday,
                    "start_time": e.start_time,
                    "end_time": e.end_time,
                    "location": e.location,
                }
                for e in merged.events
            ],
            "error": merged.error,
        }
        # Egress truth from the resolved assignment's frozen route
        if per_image_egress is not None:
            response["egress"] = per_image_egress
        return JSONResponse(response)

    @router.post("/confirm")
    async def confirm_snapshot(request: Request) -> Any:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                {"success": False, "error": "Invalid JSON body"},
                status_code=422,
            )

        anchor_str = body.get("anchor_date", "")
        if not anchor_str:
            return JSONResponse(
                {"success": False, "error": "anchor_date is required"},
                status_code=422,
            )

        try:
            anchor_monday = resolve_anchor_date(str(anchor_str))
        except ValueError as exc:
            return JSONResponse(
                {"success": False, "error": str(exc)},
                status_code=422,
            )

        raw_events = body.get("events", [])
        if not isinstance(raw_events, list):
            return JSONResponse(
                {"success": False, "error": "events must be a list"},
                status_code=422,
            )

        # Reconstruct ExtractedEvent-like dicts for resolution
        from ...services.calendar_snapshot_service import ExtractedEvent

        events = []
        for entry in raw_events:
            if not isinstance(entry, dict):
                continue
            events.append(
                ExtractedEvent(
                    title=str(entry.get("title", "")),
                    weekday=str(entry.get("weekday", "")),
                    start_time=str(entry.get("start_time", "")),
                    end_time=str(entry.get("end_time", "")),
                    location=entry.get("location"),
                )
            )

        resolved = resolve_events_to_timestamps(events, anchor_monday)

        # Determine source_id — reuse existing snapshot source or create new
        config = Config.load()
        source_id = ""
        for s in config.calendar.sources:
            if s.label == SNAPSHOT_SOURCE_LABEL:
                source_id = s.id
                break
        if not source_id:
            import uuid as _uuid

            source_id = str(_uuid.uuid4())

        ics_bytes = generate_ics(resolved, source_id=source_id)

        # Validate through the REAL parser (the bounded ICS parser is the
        # ONE trust boundary — model output goes through it like any hostile feed)
        from ...calendar_ingest import parse_calendar_bytes
        from datetime import datetime, timezone

        parse_result = parse_calendar_bytes(
            ics_bytes,
            now=datetime.now(timezone.utc),
            subscription_revision=f"snapshot:{source_id}",
        )
        if not parse_result.succeeded:
            return JSONResponse(
                {
                    "success": False,
                    "error": f"Generated ICS failed parser validation: {parse_result.feed_error}",
                },
                status_code=422,
            )

        ics_path = write_ics_atomic(source_id, ics_bytes)

        settings_service = ctx.settings_service
        if settings_service:
            register_snapshot_source(
                source_id,
                ics_path,
                settings_service=settings_service,
                principal=principal,
            )

        trigger_calendar_refresh()

        return JSONResponse({
            "success": True,
            "source_id": source_id,
            "source_label": SNAPSHOT_SOURCE_LABEL,
            "events_count": len(resolved),
            "ics_path": str(ics_path),
        })

    return router


def _extraction_system_prompt() -> str:
    from ...services.calendar_snapshot_service import EXTRACTION_SYSTEM_PROMPT

    return EXTRACTION_SYSTEM_PROMPT


def _extraction_user_prompt() -> str:
    from ...services.calendar_snapshot_service import EXTRACTION_USER_PROMPT

    return EXTRACTION_USER_PROMPT


def _default_extract(payload: dict[str, Any]) -> str:
    """Fallback stub kept only for e2e test injection compatibility."""
    return '{"error": "unreadable_screenshot", "events": []}'
