"""Follow-Through board transport adapters."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request

from ...principals import UNAUTHENTICATED
from ...services.follow_through_service import FollowThroughBoard, FollowThroughService
from ..context import WebContext


def _board_dict(board: FollowThroughBoard) -> dict[str, list[dict[str, Any]]]:
    return {
        "now": [asdict(card) for card in board.now],
        "waiting": [asdict(card) for card in board.waiting],
        "unassigned": [asdict(card) for card in board.unassigned],
        "overdue": [asdict(card) for card in board.overdue],
    }


def build_follow_through_router(ctx: WebContext) -> APIRouter:
    """Expose the Follow-Through board through the Desk's HTTP surface."""
    router = APIRouter(prefix="/api/follow-through", tags=["follow-through"])
    service = ctx.follow_through_service
    if service is None:
        from ...db import get_database, get_observer

        service = FollowThroughService(get_database(), observer=get_observer())
    principal = lambda request: getattr(request.state, "principal", UNAUTHENTICATED)

    @router.get("/board")
    async def board(
        request: Request,
        project_id: str | None = None,
        owner: str | None = None,
        state: str | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        try:
            return _board_dict(
                service.board(principal(request), project_id=project_id, owner=owner, state=state)
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/complete")
    async def complete(request: Request, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return service.complete(
                principal(request),
                str(body.get("card_id") or ""),
                str(body.get("verb") or ""),
                body.get("payload"),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/commit-decision")
    async def commit_decision(request: Request, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return service.commit_decision(
                principal(request),
                str(body.get("decision_id") or ""),
                owner=body.get("owner"),
                due_at=body.get("due_at"),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
