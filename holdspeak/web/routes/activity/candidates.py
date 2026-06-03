"""Meeting-candidate routes — HS-34-02 split of `activity.py`.

`/api/activity/meeting-candidates*` (preview/list/create/status/start/delete).
The candidate payload shaper and `_meeting_payload_id` are used only here.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....web_requests import (
    _ActivityMeetingCandidateRequest,
    _ActivityMeetingCandidateStatusRequest,
)
from ...context import WebContext
from ...runtime_support import _meeting_callback_payload, _parse_iso_datetime, error_500

log = get_logger("web.routes.activity")


def _activity_meeting_candidate_payload(candidate: Any) -> dict[str, Any]:
    return {
        "id": getattr(candidate, "id", None),
        "source_connector_id": candidate.source_connector_id,
        "source_activity_record_id": candidate.source_activity_record_id,
        "dedupe_key": getattr(candidate, "dedupe_key", ""),
        "title": candidate.title,
        "starts_at": candidate.starts_at.isoformat() if candidate.starts_at else None,
        "ends_at": candidate.ends_at.isoformat() if candidate.ends_at else None,
        "meeting_url": candidate.meeting_url,
        "started_meeting_id": getattr(candidate, "started_meeting_id", None),
        "confidence": candidate.confidence,
        "status": getattr(candidate, "status", "preview"),
        "created_at": candidate.created_at.isoformat() if getattr(candidate, "created_at", None) else None,
        "updated_at": candidate.updated_at.isoformat() if getattr(candidate, "updated_at", None) else None,
    }


def _meeting_payload_id(meeting_data: Any) -> Optional[str]:
    if not isinstance(meeting_data, dict):
        return None
    meeting_id = meeting_data.get("id")
    if meeting_id not in (None, ""):
        return str(meeting_id)
    nested = meeting_data.get("meeting")
    if isinstance(nested, dict) and nested.get("id") not in (None, ""):
        return str(nested["id"])
    return None


def build_candidates_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/activity/meeting-candidates/preview")
    async def api_preview_activity_meeting_candidates(limit: int = 50) -> Any:
        try:
            from ....activity_candidates import preview_calendar_meeting_candidates
            from ....db import get_database

            db = get_database()
            records = db.activity.list_activity_records(limit=max(1, min(int(limit), 500)))
            previews = preview_calendar_meeting_candidates(records, limit=limit)
            return JSONResponse(
                {
                    "count": len(previews),
                    "candidates": [_activity_meeting_candidate_payload(candidate) for candidate in previews],
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to preview activity meeting candidates")

    @router.get("/api/activity/meeting-candidates")
    async def api_activity_meeting_candidates(
        source_connector_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> Any:
        try:
            from ....db import get_database

            db = get_database()
            candidates = db.activity.list_activity_meeting_candidates(
                source_connector_id=source_connector_id,
                status=status,
                limit=limit,
            )
            return JSONResponse(
                {
                    "count": len(candidates),
                    "candidates": [_activity_meeting_candidate_payload(candidate) for candidate in candidates],
                }
            )
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            return error_500(e, log, "Failed to list activity meeting candidates")

    @router.post("/api/activity/meeting-candidates")
    async def api_create_activity_meeting_candidate(
        payload: _ActivityMeetingCandidateRequest,
    ) -> Any:
        try:
            from ....db import get_database

            db = get_database()
            candidate = db.activity.create_activity_meeting_candidate(
                source_connector_id=payload.source_connector_id or "calendar_activity",
                source_activity_record_id=payload.source_activity_record_id,
                title=payload.title or "",
                starts_at=_parse_iso_datetime(payload.starts_at),
                ends_at=_parse_iso_datetime(payload.ends_at),
                meeting_url=payload.meeting_url,
                confidence=payload.confidence if payload.confidence is not None else 0.0,
                status=payload.status or "candidate",
            )
            return JSONResponse({"candidate": _activity_meeting_candidate_payload(candidate)})
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            return error_500(e, log, "Failed to create activity meeting candidate")

    @router.put("/api/activity/meeting-candidates/{candidate_id}/status")
    async def api_update_activity_meeting_candidate_status(
        candidate_id: str,
        payload: _ActivityMeetingCandidateStatusRequest,
    ) -> Any:
        try:
            from ....db import get_database

            db = get_database()
            candidate = db.activity.update_activity_meeting_candidate_status(
                candidate_id,
                payload.status,
            )
            if candidate is None:
                return JSONResponse({"error": "activity meeting candidate not found"}, status_code=404)
            return JSONResponse({"candidate": _activity_meeting_candidate_payload(candidate)})
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            return error_500(e, log, "Failed to update activity meeting candidate")

    @router.post("/api/activity/meeting-candidates/{candidate_id}/start")
    async def api_start_activity_meeting_candidate(candidate_id: str) -> Any:
        if ctx.on_start is None:
            return JSONResponse(
                {"success": False, "error": "Meeting start control not supported"},
                status_code=501,
            )

        try:
            from ....db import get_database

            db = get_database()
            candidate = db.activity.get_activity_meeting_candidate(candidate_id)
            if candidate is None:
                return JSONResponse({"error": "activity meeting candidate not found"}, status_code=404)

            result = ctx.on_start()
            meeting_data = _meeting_callback_payload(result)

            title_warning = None
            if ctx.on_update_meeting is not None and str(candidate.title or "").strip():
                try:
                    updated = ctx.on_update_meeting(title=candidate.title, tags=None)
                    updated_payload = _meeting_callback_payload(updated)
                    if updated_payload is not None:
                        meeting_data = updated_payload
                except Exception as e:
                    title_warning = str(e)
                    log.error(f"Failed to apply candidate title to started meeting: {e}")

            meeting_id = _meeting_payload_id(meeting_data)
            candidate = db.activity.mark_activity_meeting_candidate_started(
                candidate.id,
                meeting_id=meeting_id,
            )
            if candidate is None:
                return JSONResponse({"error": "activity meeting candidate not found"}, status_code=404)

            if meeting_data is not None:
                ctx.broadcast(
                    "meeting_started",
                    {
                        **meeting_data,
                        "activity_meeting_candidate_id": candidate.id,
                        "activity_meeting_candidate_title": candidate.title,
                        "activity_meeting_candidate_url": candidate.meeting_url,
                    },
                )
            response_payload: dict[str, Any] = {
                "success": True,
                "candidate": _activity_meeting_candidate_payload(candidate),
                "meeting": meeting_data,
            }
            if title_warning:
                response_payload["warning"] = f"Meeting started, but title update failed: {title_warning}"
            return JSONResponse(response_payload)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            log.error(f"Failed to start activity meeting candidate: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.delete("/api/activity/meeting-candidates")
    async def api_delete_activity_meeting_candidates(
        source_connector_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Any:
        try:
            from ....db import get_database

            db = get_database()
            deleted = db.activity.delete_activity_meeting_candidates(
                source_connector_id=source_connector_id,
                status=status,
            )
            return JSONResponse({"deleted": deleted})
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            return error_500(e, log, "Failed to delete activity meeting candidates")

    return router
