"""DB-backed meeting listing, facets, detail, delete, and export routes.

These read routes close over no server state and call the module-level
`get_database()` directly, exactly as before the Phase-72 package split.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

from ....logging_config import get_logger
from ...context import WebContext
from ._shared import _parse_facet_date

log = get_logger("web.routes.meetings")


def build_crud_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/meetings")
    async def api_list_meetings(
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        speaker: Optional[str] = None,
        tag: Optional[str] = None,
        has_open_actions: bool = False,
    ) -> Any:
        """List meetings, with HS-55-04 server-side facets composing with search.

        Facets filter in SQL over the whole archive. With ``search``, the
        full-text hits flow through the same faceted query, so both branches
        return the same summary shape (this also fixed search results
        previously returning full ``to_dict`` payloads whose nested
        ``intel_status`` broke the status pill).
        """
        try:
            from ....db import get_database
            db = get_database()

            parsed_from = _parse_facet_date(date_from)
            parsed_to = _parse_facet_date(date_to, end_of_day=True)

            search_ids: Optional[list[str]] = None
            if search:
                results = db.meetings.search_transcripts(search, limit=500)
                search_ids = list(dict.fromkeys([r[0] for r in results]))

            meetings = db.meetings.list_meetings(
                limit=limit,
                offset=offset,
                date_from=parsed_from,
                date_to=parsed_to,
                tag=tag,
                speaker=speaker,
                has_open_actions=has_open_actions,
                meeting_ids=search_ids,
            )
            filtered = bool(search or date_from or date_to or speaker or tag or has_open_actions)
            return JSONResponse({
                "meetings": [
                    {
                        "id": m.id,
                        "started_at": m.started_at.isoformat(),
                        "ended_at": m.ended_at.isoformat() if m.ended_at else None,
                        "title": m.title,
                        "duration_seconds": m.duration_seconds,
                        "segment_count": m.segment_count,
                        "action_item_count": m.action_item_count,
                        "tags": m.tags,
                        "intel_status": m.intel_status,
                        "intel_status_detail": m.intel_status_detail,
                    }
                    for m in meetings
                ],
                "total": len(meetings) if filtered else db.meetings.get_meeting_count(),
            })
        except Exception as e:
            log.error(f"Failed to list meetings: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    @router.get("/api/meetings/facets")
    async def api_meeting_facets() -> Any:
        """Distinct speakers + tags for the /history filter row (HS-55-04).

        Registered before ``/api/meetings/{meeting_id}`` so "facets" never
        matches as a meeting id.
        """
        try:
            from ....db import get_database
            db = get_database()
            return JSONResponse(db.meetings.list_facet_values())
        except Exception as e:
            log.error(f"Failed to list meeting facets: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    @router.get("/api/meetings/{meeting_id}")
    async def api_get_meeting(meeting_id: str) -> Any:
        """Get meeting details from database."""
        try:
            from ....db import get_database
            db = get_database()
            meeting = db.meetings.get_meeting(meeting_id)
            if meeting is None:
                return JSONResponse(
                    {"error": "Meeting not found"}, status_code=404
                )
            return JSONResponse(meeting.to_dict())
        except Exception as e:
            log.error(f"Failed to get meeting: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    @router.delete("/api/meetings/{meeting_id}")
    async def api_delete_meeting(meeting_id: str) -> Any:
        """Delete a meeting (HS-55-02: e.g. a failed import's honest row)."""
        try:
            from ....db import get_database
            db = get_database()
            if not db.meetings.delete_meeting(meeting_id):
                return JSONResponse(
                    {"error": "Meeting not found"}, status_code=404
                )
            return JSONResponse({"deleted": meeting_id})
        except Exception as e:
            log.error(f"Failed to delete meeting: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    @router.get("/api/meetings/{meeting_id}/export")
    async def api_export_meeting(
        meeting_id: str,
        format: str = "markdown",
    ) -> Any:
        """Render a saved meeting handoff export."""
        export_format = str(format or "").strip().lower()
        if export_format == "md":
            export_format = "markdown"
        if export_format not in {"markdown", "json"}:
            return JSONResponse(
                {"error": f"Invalid export format: {format}"},
                status_code=400,
            )

        try:
            from ....db import get_database
            from ....meeting_exports import render_meeting_export

            db = get_database()
            meeting = db.meetings.get_meeting(meeting_id)
            if meeting is None:
                return JSONResponse(
                    {"error": "Meeting not found"}, status_code=404
                )

            artifacts = db.plugins.list_artifacts(meeting_id, limit=200)
            content = render_meeting_export(
                meeting,
                export_format,  # type: ignore[arg-type]
                artifacts=artifacts,
            )
            extension = "md" if export_format == "markdown" else "json"
            media_type = (
                "text/markdown; charset=utf-8"
                if export_format == "markdown"
                else "application/json; charset=utf-8"
            )
            filename = f"holdspeak-meeting-{meeting_id}.{extension}"
            return Response(
                content=content,
                media_type=media_type,
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except Exception as e:
            log.error(f"Failed to export meeting: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    return router
