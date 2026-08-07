"""DB-backed meeting listing, facets, detail, delete, and export routes.

These read routes close over no server state and call the module-level
`get_database()` directly, exactly as before the Phase-72 package split.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
from ....services.meeting_service import MeetingService
from ....services.primitive_service import NotFound, ValidationError
from ...context import WebContext

log = get_logger("web.routes.meetings")


def _service(ctx: WebContext) -> MeetingService:
    if isinstance(ctx.meeting_service, MeetingService):
        return ctx.meeting_service
    from ....db import get_database

    service = MeetingService(get_database())
    ctx.meeting_service = service
    return service


def _principal(request: Request):
    return getattr(request.state, "principal", UNAUTHENTICATED)


def build_crud_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/meetings")
    async def api_list_meetings(
        request: Request,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        q: Optional[str] = None,
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
        if q is not None:
            return JSONResponse(
                {"error": "unsupported query parameter 'q'; use 'search'"},
                status_code=422,
            )
        try:
            result = _service(ctx).list_meetings(
                _principal(request),
                query=search,
                from_date=date_from,
                to_date=date_to,
                limit=limit,
                cursor=offset,
                speaker=speaker,
                tag=tag,
                has_open_actions=has_open_actions,
            )
            # The legacy endpoint was offset-based and did not expose cursors.
            result.pop("next_cursor", None)
            return JSONResponse(result)
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
    async def api_get_meeting(meeting_id: str, request: Request) -> Any:
        """Get meeting details from database."""
        try:
            return JSONResponse(_service(ctx).get_meeting(_principal(request), meeting_id))
        except NotFound:
            return JSONResponse({"error": "Meeting not found"}, status_code=404)
        except Exception as e:
            log.error(f"Failed to get meeting: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    @router.delete("/api/meetings/{meeting_id}")
    async def api_delete_meeting(meeting_id: str, request: Request) -> Any:
        """Delete a meeting (HS-55-02: e.g. a failed import's honest row)."""
        try:
            _service(ctx).delete_meeting(_principal(request), meeting_id)
            return JSONResponse({"deleted": meeting_id})
        except NotFound:
            return JSONResponse({"error": "Meeting not found"}, status_code=404)
        except Exception as e:
            log.error(f"Failed to delete meeting: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    @router.post("/api/meetings/{meeting_id}/capture/recover")
    async def api_recover_meeting_capture(meeting_id: str) -> Any:
        """Keep the last atomic checkpoint as an honestly partial Meeting."""
        try:
            from ....db import get_database

            meeting = get_database().meetings.recover_capture(meeting_id)
            if meeting is None:
                return JSONResponse({"error": "Meeting not found"}, status_code=404)
            return JSONResponse({"meeting": meeting.to_dict(), "recovered": True})
        except Exception as exc:
            return JSONResponse(
                {"error": f"Recovery failed; the original Meeting is retained: {exc}. Retry recovery."},
                status_code=500,
            )

    @router.get("/api/meetings/{meeting_id}/sync-conflicts")
    async def api_meeting_sync_conflicts(meeting_id: str) -> Any:
        from ....db import get_database

        return JSONResponse({
            "conflicts": get_database().meetings.list_sync_conflicts(meeting_id)
        })

    @router.post(
        "/api/meetings/{meeting_id}/sync-conflicts/{conflict_id}/resolve"
    )
    async def api_resolve_meeting_sync_conflict(
        meeting_id: str,
        conflict_id: str,
        payload: dict[str, Any],
    ) -> Any:
        """Apply the owner's explicit choice between two Meeting versions."""
        resolution = str(payload.get("resolution") or "").strip()
        if resolution not in {"keep_current", "use_incoming"}:
            return JSONResponse(
                {"error": "resolution must be keep_current or use_incoming"},
                status_code=400,
            )

        from ....db import get_database

        db = get_database()
        conflict = db.meetings.get_sync_conflict(meeting_id, conflict_id)
        if conflict is None:
            return JSONResponse({"error": "Meeting conflict not found"}, status_code=404)
        if conflict.get("resolved_at") is not None:
            return JSONResponse(
                {"error": "Meeting conflict was already resolved; reload the Meeting."},
                status_code=409,
            )

        incoming_state = None
        incoming = conflict.get("incoming")
        if resolution == "use_incoming" and not (
            isinstance(incoming, dict) and bool(incoming.get("deleted"))
        ):
            if not isinstance(incoming, dict):
                return JSONResponse(
                    {"error": "Incoming Meeting version is unreadable; current work retained."},
                    status_code=409,
                )
            try:
                from ..sync import meeting_state_from_sync_value

                incoming_state = meeting_state_from_sync_value(
                    {**incoming, "id": meeting_id}
                )
            except (TypeError, ValueError) as exc:
                return JSONResponse(
                    {
                        "error": (
                            "Incoming Meeting version is unreadable; current work retained: "
                            f"{exc}"
                        )
                    },
                    status_code=409,
                )

        try:
            outcome = db.meetings.resolve_sync_conflict(
                meeting_id,
                conflict_id,
                resolution=resolution,
                incoming_state=incoming_state,
            )
        except (TypeError, ValueError) as exc:
            return JSONResponse(
                {"error": f"Conflict was not changed; both versions remain: {exc}. Choose a version and retry."},
                status_code=409,
            )
        except Exception as exc:
            log.error("Failed to resolve Meeting sync conflict: %s", exc)
            return JSONResponse(
                {"error": f"Conflict recovery failed; both versions remain: {exc}. Retry the resolution."},
                status_code=500,
            )

        if outcome == "missing":
            return JSONResponse({"error": "Meeting conflict not found"}, status_code=404)
        if outcome == "already_resolved":
            return JSONResponse(
                {"error": "Meeting conflict was already resolved; reload the Meeting."},
                status_code=409,
            )

        meeting = db.meetings.get_meeting(meeting_id)
        return JSONResponse(
            {
                "resolution": resolution,
                "deleted": outcome == "deleted",
                "meeting": meeting.to_dict() if meeting is not None else None,
                "remaining_conflicts": db.meetings.list_sync_conflicts(meeting_id),
            }
        )

    @router.get("/api/meetings/{meeting_id}/export")
    async def api_export_meeting(
        meeting_id: str,
        request: Request,
        format: str = "markdown",
    ) -> Any:
        """Render a saved meeting handoff export."""
        try:
            export = _service(ctx).export_meeting(
                _principal(request), meeting_id, format
            )
            return Response(
                content=export["content"],
                media_type=export["media_type"],
                headers={"Content-Disposition": 'attachment; filename="%s"' % export["filename"]},
            )
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except NotFound:
            return JSONResponse({"error": "Meeting not found"}, status_code=404)
        except Exception as e:
            log.error(f"Failed to export meeting: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    return router
