"""Follow-Through board transport adapters.

The owner's enriched board is a private service read. The MCP board stays person-free;
the service observer withholds both board results from durable events.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request

from ...principals import UNAUTHENTICATED
from ...services.follow_through_service import FollowThroughService
from ..context import WebContext


def build_follow_through_router(ctx: WebContext) -> APIRouter:
    """Expose the Follow-Through board through the Desk's HTTP surface."""
    router = APIRouter(prefix="/api/follow-through", tags=["follow-through"])
    service = ctx.follow_through_service
    if service is None:
        from ...db import get_database, get_observer

        service = FollowThroughService(get_database(), observer=get_observer())
    principal = lambda request: getattr(request.state, "principal", UNAUTHENTICATED)

    @router.post("/complete")
    def complete(request: Request, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return service.complete(
                principal(request),
                str(body.get("card_id") or ""),
                str(body.get("verb") or ""),
                body.get("payload"),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    from ... import operations
    from ...parity_operations import PARITY_OPERATIONS
    from ..operation_routes import operation_router
    from ._mount import mount_router
    from ._produced import envelope
    def ops():
        return operations.for_context(ctx, follow_through_service=lambda: service)
    async def board(request: Request, project_id: str | None = None, owner: str | None = None,
                    state: str | None = None, focus_id: str | None = None) -> Any:
        from fastapi.responses import JSONResponse
        from starlette.concurrency import run_in_threadpool
        try:
            result = await run_in_threadpool(ops().invoke, principal(request), "follow_through.owner_board", {
                "project_id": project_id, "owner_filter": owner, "state": state, "focus_id": focus_id})
            return JSONResponse(result)
        except operations.OperationOwnerRequired as exc:
            return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=403)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    # The global row uses the absolute path; mount outside the prefixed legacy router.
    outer = APIRouter()
    mount_router(outer, operation_router(
        [d for d in PARITY_OPERATIONS if d.name == "follow_through.owner_board"], ops,
        envelope(__import__("logging").getLogger(__name__), "Failed to read follow-through"), module=__name__, hand_written={"follow_through.owner_board": lambda d: board}))
    mount_router(outer, router)
    return outer
