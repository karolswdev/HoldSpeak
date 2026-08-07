"""Thin transport adapters for canonical action-item operations."""
from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ....principals import UNAUTHENTICATED
from ....services.errors import NotFound, ValidationError
from ....services.meeting_service import MeetingService
from ....web_requests import (_ActionItemEditRequest, _ActionItemReviewRequest, _ActionItemUpdateRequest, _GlobalActionItemEditRequest, _GlobalActionItemReviewRequest, _GlobalActionItemUpdateRequest)
from ...context import WebContext

def _service(ctx: WebContext) -> MeetingService:
    if ctx.meeting_service_factory is not None:
        service = ctx.meeting_service_factory()
        if isinstance(service, MeetingService): return service
    if isinstance(ctx.meeting_service, MeetingService): return ctx.meeting_service
    raise RuntimeError("Meeting service is not configured")
def _principal(request: Request): return getattr(request.state, "principal", UNAUTHENTICATED)
def _error(exc: Exception) -> JSONResponse:
    if isinstance(exc, ValidationError): return JSONResponse({"success": False, "error": str(exc)}, status_code=400)
    if isinstance(exc, NotFound): return JSONResponse({"success": False, "error": "Action item not found"}, status_code=404)
    return JSONResponse({"success": False, "error": str(exc)}, status_code=500)
def build_action_items_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    @router.patch("/api/action-items/{item_id}")
    async def api_update_action_item(item_id: str, payload: _ActionItemUpdateRequest, request: Request) -> Any:
        try: return JSONResponse(_service(ctx).update_action_item(_principal(request), item_id, payload.model_dump()))
        except Exception as exc: return _error(exc)
    @router.patch("/api/action-items/{item_id}/review")
    async def api_update_action_item_review(item_id: str, payload: _ActionItemReviewRequest, request: Request) -> Any:
        try: return JSONResponse(_service(ctx).review_action_item(_principal(request), item_id, payload.model_dump()))
        except Exception as exc: return _error(exc)
    @router.patch("/api/action-items/{item_id}/edit")
    async def api_edit_action_item(item_id: str, payload: _ActionItemEditRequest, request: Request) -> Any:
        try: return JSONResponse(_service(ctx).edit_action_item(_principal(request), item_id, payload.model_dump()))
        except Exception as exc: return _error(exc)
    @router.get("/api/all-action-items")
    async def api_list_all_action_items(request: Request, include_completed: bool = False, owner: Optional[str] = None, meeting_id: Optional[str] = None) -> Any:
        try: return JSONResponse(_service(ctx).list_all_action_items(_principal(request), {"include_completed": include_completed, "owner": owner, "meeting_id": meeting_id}))
        except Exception as exc: return JSONResponse({"error": str(exc)}, status_code=500)
    @router.patch("/api/all-action-items/{item_id}")
    async def api_update_global_action_item(item_id: str, payload: _GlobalActionItemUpdateRequest, request: Request) -> Any:
        try: return JSONResponse(_service(ctx).update_action_item(_principal(request), item_id, payload.model_dump()))
        except Exception as exc: return _error(exc)
    @router.patch("/api/all-action-items/{item_id}/review")
    async def api_review_global_action_item(item_id: str, payload: _GlobalActionItemReviewRequest, request: Request) -> Any:
        try: return JSONResponse(_service(ctx).review_action_item(_principal(request), item_id, payload.model_dump()))
        except Exception as exc: return _error(exc)
    @router.patch("/api/all-action-items/{item_id}/edit")
    async def api_edit_global_action_item(item_id: str, payload: _GlobalActionItemEditRequest, request: Request) -> Any:
        try: return JSONResponse(_service(ctx).edit_action_item(_principal(request), item_id, payload.model_dump()))
        except Exception as exc: return _error(exc)
    return router
