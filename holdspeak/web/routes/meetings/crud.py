"""DB-backed meeting listing, facets, detail, delete, and export routes.

These read routes delegate through the composition-bound meeting service.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
from ....services.meeting_service import MeetingService
from ....services.errors import NotFound, ValidationError
from ...context import WebContext

log = get_logger("web.routes.meetings")


def _service(ctx: WebContext) -> MeetingService:
    if isinstance(ctx.meeting_service, MeetingService):
        return ctx.meeting_service
    from ....db import get_database, get_observer

    service = MeetingService(get_database(), observer=get_observer())  # _service composition
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
    async def api_meeting_facets(request: Request) -> Any:
        """Distinct speakers + tags for the /history filter row (HS-55-04)."""
        try:
            return JSONResponse(_service(ctx).facets(_principal(request)))
        except Exception as e:
            log.error(f"Failed to list meeting facets: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

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
    async def api_recover_meeting_capture(meeting_id: str, request: Request) -> Any:
        """Keep the last atomic checkpoint as an honestly partial Meeting."""
        try:
            return JSONResponse(_service(ctx).recover_capture(_principal(request), meeting_id))
        except NotFound:
            return JSONResponse({"error": "Meeting not found"}, status_code=404)
        except Exception as exc:
            return JSONResponse({"error": f"Recovery failed; the original Meeting is retained: {exc}. Retry recovery."}, status_code=500)

    @router.get("/api/meetings/{meeting_id}/sync-conflicts")
    async def api_meeting_sync_conflicts(meeting_id: str, request: Request) -> Any:
        try:
            return JSONResponse(_service(ctx).list_sync_conflicts(_principal(request), meeting_id))
        except NotFound:
            return JSONResponse({"error": "Meeting not found"}, status_code=404)
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @router.post(
        "/api/meetings/{meeting_id}/sync-conflicts/{conflict_id}/resolve"
    )
    async def api_resolve_meeting_sync_conflict(
        meeting_id: str,
        conflict_id: str,
        payload: dict[str, Any],
        request: Request,
    ) -> Any:
        """Apply the owner's explicit choice between two Meeting versions."""
        try:
            return JSONResponse(_service(ctx).resolve_sync_conflict(_principal(request), meeting_id, conflict_id, payload))
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except NotFound:
            return JSONResponse({"error": "Meeting conflict not found"}, status_code=404)
        except Exception as exc:
            from ....services.errors import ConflictError
            if isinstance(exc, ConflictError):
                return JSONResponse({"error": str(exc)}, status_code=409)
            log.error("Failed to resolve Meeting sync conflict: %s", exc)
            return JSONResponse({"error": f"Conflict recovery failed; both versions remain: {exc}. Retry the resolution."}, status_code=500)

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
