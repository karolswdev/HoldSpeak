"""DB-backed meeting listing, detail, delete, and export routes.

These read routes delegate through the composition-bound meeting service. The
readiness, facets, rename, restore, recover, sync-conflict, speaker and
insight routes are produced from their declared operations
(``meeting_operations.py``).
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
from .._mount import mount_router
from . import _declared

log = get_logger("web.routes.meetings")


def _service(ctx: WebContext) -> MeetingService:
    if ctx.meeting_service is not None:
        return ctx.meeting_service
    return _declared.registry_for(ctx)().target("meeting.list")  # a partial context's


def _principal(request: Request):
    return getattr(request.state, "principal", UNAUTHENTICATED)


def build_crud_router(ctx: WebContext) -> APIRouter:
    # Produced first: /ready and /facets come before /{meeting_id}.
    router = _declared.router(ctx, ("meeting.ready_list", "meeting.ready_read", "meeting.facets"), module=__name__)
    _ops = _declared.registry_for(ctx)

    @router.get("/api/meetings")
    def api_list_meetings(
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
        parked: bool = False,
        summary_attention: bool = False,
    ) -> Any:
        """List meetings, with HS-55-04 server-side facets composing with search.

        Facets filter in SQL over the whole archive. With ``search``, the
        full-text hits flow through the same faceted query, so both branches
        return the same summary shape (this also fixed search results
        previously returning full ``to_dict`` payloads whose nested
        ``intel_status`` broke the status pill).

        Each row includes ``attendees: list[str]``: saved segment speakers
        plus the linked calendar event's attendee emails, trimmed, with
        blanks and exact duplicates removed, in case-sensitive lexical
        order. The field is an empty list when neither source has values.
        """
        if q is not None:
            return JSONResponse(
                {"error": "unsupported query parameter 'q'; use 'search'"},
                status_code=422,
            )
        try:
            result = _ops().invoke(_principal(request), "meeting.list", {
                "query": search,
                "from_date": date_from,
                "to_date": date_to,
                "limit": limit,
                "cursor": offset,
                "speaker": speaker,
                "tag": tag,
                "has_open_actions": has_open_actions,
                "parked": parked,
                "summary_attention": summary_attention,
            })
            # The legacy endpoint was offset-based and did not expose cursors.
            result.pop("next_cursor", None)
            return JSONResponse(result)
        except Exception as e:
            log.error(f"Failed to list meetings: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    @router.get("/api/meetings/{meeting_id}")
    def api_get_meeting(
        meeting_id: str, request: Request, include_parked: bool = False
    ) -> Any:
        """Get meeting details from database."""
        try:
            return JSONResponse(_ops().invoke(_principal(request), "meeting.read", {"meeting_id": meeting_id, "include_parked": include_parked}))
        except NotFound:
            return JSONResponse({"error": "Meeting not found"}, status_code=404)
        except Exception as e:
            log.error(f"Failed to get meeting: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    @router.delete("/api/meetings/{meeting_id}")
    def api_delete_meeting(meeting_id: str, request: Request) -> Any:
        """Park a meeting while retaining its transcript and related work."""
        try:
            _service(ctx).delete_meeting(_principal(request), meeting_id)
            return JSONResponse({"parked": meeting_id})
        except NotFound:
            return JSONResponse({"error": "Meeting not found"}, status_code=404)
        except Exception as e:
            log.error(f"Failed to delete meeting: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    @router.get("/api/meetings/{meeting_id}/export")
    def api_export_meeting(
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

    mount_router(router, _declared.router(ctx, (
        "meeting.rename", "meeting.restore", "meeting.recover_capture", "meeting.sync_conflicts",
        "meeting.resolve_sync_conflict", "speaker.list", "meeting.intent_timeline", "meeting.artifacts",
        "meeting.prepared"), module=__name__))
    return router
