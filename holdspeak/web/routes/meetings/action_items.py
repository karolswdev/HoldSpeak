"""Action-item routes: meeting-scoped mutations (callback-backed) and the
DB-backed global /api/all-action-items listing + mutations.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....web_requests import (
    _ActionItemEditRequest,
    _ActionItemReviewRequest,
    _ActionItemUpdateRequest,
    _GlobalActionItemEditRequest,
    _GlobalActionItemReviewRequest,
    _GlobalActionItemUpdateRequest,
)
from ...context import WebContext

log = get_logger("web.routes.meetings")


def build_action_items_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.patch("/api/action-items/{item_id}")
    async def api_update_action_item(
        item_id: str, payload: _ActionItemUpdateRequest
    ) -> Any:
        if ctx.on_update_action_item is None:
            return JSONResponse(
                {"success": False, "error": "Action item updates not supported"},
                status_code=501,
            )

        status = payload.status
        if status not in ("done", "pending", "dismissed"):
            return JSONResponse(
                {"success": False, "error": f"Invalid status: {status}"},
                status_code=400,
            )

        try:
            result = ctx.on_update_action_item(item_id, status)
        except Exception as e:
            log.error(f"on_update_action_item failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        if result is None:
            return JSONResponse(
                {"success": False, "error": "Action item not found"},
                status_code=404,
            )

        # Broadcast the update to all connected clients
        ctx.broadcast("action_item_updated", result)

        return JSONResponse({"success": True, "action_item": result})

    @router.patch("/api/action-items/{item_id}/review")
    async def api_update_action_item_review(
        item_id: str, payload: _ActionItemReviewRequest
    ) -> Any:
        if ctx.on_update_action_item_review is None:
            return JSONResponse(
                {"success": False, "error": "Action item review updates not supported"},
                status_code=501,
            )

        review_state = str(payload.review_state or "").strip().lower()
        if review_state not in ("pending", "accepted"):
            return JSONResponse(
                {"success": False, "error": f"Invalid review_state: {review_state}"},
                status_code=400,
            )

        try:
            result = ctx.on_update_action_item_review(item_id, review_state)
        except Exception as e:
            log.error(f"on_update_action_item_review failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        if result is None:
            return JSONResponse(
                {"success": False, "error": "Action item not found"},
                status_code=404,
            )

        ctx.broadcast("action_item_updated", result)
        return JSONResponse({"success": True, "action_item": result})

    @router.patch("/api/action-items/{item_id}/edit")
    async def api_edit_action_item(
        item_id: str, payload: _ActionItemEditRequest
    ) -> Any:
        if ctx.on_edit_action_item is None:
            return JSONResponse(
                {"success": False, "error": "Action item edits not supported"},
                status_code=501,
            )

        task = str(payload.task or "").strip()
        if not task:
            return JSONResponse(
                {"success": False, "error": "Action item task cannot be empty"},
                status_code=400,
            )

        try:
            result = ctx.on_edit_action_item(
                item_id,
                task=task,
                owner=payload.owner,
                due=payload.due,
            )
        except Exception as e:
            log.error(f"on_edit_action_item failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        if result is None:
            return JSONResponse(
                {"success": False, "error": "Action item not found"},
                status_code=404,
            )

        ctx.broadcast("action_item_updated", result)
        return JSONResponse({"success": True, "action_item": result})

    @router.get("/api/all-action-items")
    async def api_list_all_action_items(
        include_completed: bool = False,
        owner: Optional[str] = None,
        meeting_id: Optional[str] = None,
    ) -> Any:
        """List action items across all meetings from database."""
        try:
            from ....db import get_database
            db = get_database()
            items = db.meetings.list_action_items(
                include_completed=include_completed,
                owner=owner,
                meeting_id=meeting_id,
            )
            return JSONResponse({
                "action_items": [
                    {
                        "id": item.id,
                        "task": item.task,
                        "owner": item.owner,
                        "due": item.due,
                        "status": item.status,
                        "review_state": item.review_state,
                        "source_timestamp": item.source_timestamp,
                        "meeting_id": item.meeting_id,
                        "meeting_title": item.meeting_title,
                        "meeting_date": item.meeting_date.isoformat(),
                        "created_at": item.created_at.isoformat(),
                        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                        "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
                    }
                    for item in items
                ]
            })
        except Exception as e:
            log.error(f"Failed to list action items: {e}")
            return JSONResponse(
                {"error": str(e)}, status_code=500
            )

    @router.patch("/api/all-action-items/{item_id}")
    async def api_update_global_action_item(
        item_id: str, payload: _GlobalActionItemUpdateRequest
    ) -> Any:
        """Update action item status in database."""
        status = payload.status
        if status not in ("done", "pending", "dismissed"):
            return JSONResponse(
                {"success": False, "error": f"Invalid status: {status}"},
                status_code=400,
            )

        try:
            from ....db import get_database
            db = get_database()
            success = db.meetings.update_action_item_status(item_id, status)
            if not success:
                return JSONResponse(
                    {"success": False, "error": "Action item not found"},
                    status_code=404,
                )
            updated = db.meetings.get_action_item(item_id) if hasattr(db.meetings, "get_action_item") else None
            return JSONResponse(
                {
                    "success": True,
                    "action_item": (
                        {
                            "id": updated.id,
                            "task": updated.task,
                            "owner": updated.owner,
                            "due": updated.due,
                            "status": updated.status,
                            "review_state": updated.review_state,
                            "source_timestamp": updated.source_timestamp,
                            "meeting_id": updated.meeting_id,
                            "meeting_title": updated.meeting_title,
                            "meeting_date": updated.meeting_date.isoformat(),
                            "created_at": updated.created_at.isoformat(),
                            "completed_at": (
                                updated.completed_at.isoformat()
                                if updated.completed_at
                                else None
                            ),
                            "reviewed_at": (
                                updated.reviewed_at.isoformat()
                                if updated.reviewed_at
                                else None
                            ),
                        }
                        if updated is not None
                        else None
                    ),
                }
            )
        except Exception as e:
            log.error(f"Failed to update action item: {e}")
            return JSONResponse(
                {"success": False, "error": str(e)}, status_code=500
            )

    @router.patch("/api/all-action-items/{item_id}/review")
    async def api_review_global_action_item(
        item_id: str, payload: _GlobalActionItemReviewRequest
    ) -> Any:
        """Update action item review state."""
        review_state = str(payload.review_state or "").strip().lower()
        if review_state not in ("pending", "accepted"):
            return JSONResponse(
                {"success": False, "error": f"Invalid review_state: {review_state}"},
                status_code=400,
            )

        try:
            from ....db import get_database
            db = get_database()
            success = db.meetings.update_action_item_review_state(item_id, review_state)
            if not success:
                return JSONResponse(
                    {"success": False, "error": "Action item not found"},
                    status_code=404,
                )
            updated = db.meetings.get_action_item(item_id) if hasattr(db.meetings, "get_action_item") else None
            return JSONResponse(
                {
                    "success": True,
                    "action_item": (
                        {
                            "id": updated.id,
                            "task": updated.task,
                            "owner": updated.owner,
                            "due": updated.due,
                            "status": updated.status,
                            "review_state": updated.review_state,
                            "source_timestamp": updated.source_timestamp,
                            "meeting_id": updated.meeting_id,
                            "meeting_title": updated.meeting_title,
                            "meeting_date": updated.meeting_date.isoformat(),
                            "created_at": updated.created_at.isoformat(),
                            "completed_at": (
                                updated.completed_at.isoformat()
                                if updated.completed_at
                                else None
                            ),
                            "reviewed_at": (
                                updated.reviewed_at.isoformat()
                                if updated.reviewed_at
                                else None
                            ),
                        }
                        if updated is not None
                        else None
                    ),
                }
            )
        except Exception as e:
            log.error(f"Failed to update action item review state: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.patch("/api/all-action-items/{item_id}/edit")
    async def api_edit_global_action_item(
        item_id: str, payload: _GlobalActionItemEditRequest
    ) -> Any:
        """Edit action item details and auto-accept the item."""
        task = str(payload.task or "").strip()
        if not task:
            return JSONResponse(
                {"success": False, "error": "Action item task cannot be empty"},
                status_code=400,
            )

        owner = payload.owner
        due = payload.due
        try:
            from ....db import get_database
            db = get_database()
            success = db.meetings.edit_action_item(
                item_id,
                task=task,
                owner=owner,
                due=due,
            )
            if not success:
                return JSONResponse(
                    {"success": False, "error": "Action item not found"},
                    status_code=404,
                )
            updated = db.meetings.get_action_item(item_id) if hasattr(db.meetings, "get_action_item") else None
            return JSONResponse(
                {
                    "success": True,
                    "action_item": (
                        {
                            "id": updated.id,
                            "task": updated.task,
                            "owner": updated.owner,
                            "due": updated.due,
                            "status": updated.status,
                            "review_state": updated.review_state,
                            "source_timestamp": updated.source_timestamp,
                            "meeting_id": updated.meeting_id,
                            "meeting_title": updated.meeting_title,
                            "meeting_date": updated.meeting_date.isoformat(),
                            "created_at": updated.created_at.isoformat(),
                            "completed_at": (
                                updated.completed_at.isoformat()
                                if updated.completed_at
                                else None
                            ),
                            "reviewed_at": (
                                updated.reviewed_at.isoformat()
                                if updated.reviewed_at
                                else None
                            ),
                        }
                        if updated is not None
                        else None
                    ),
                }
            )
        except ValueError as e:
            return JSONResponse({"success": False, "error": str(e)}, status_code=400)
        except Exception as e:
            log.error(f"Failed to edit action item: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    return router
