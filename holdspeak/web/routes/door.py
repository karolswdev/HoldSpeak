"""Dashboard Door transport adapter."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...principals import PrincipalKind, UNAUTHENTICATED
from ...services.errors import ServiceError
from ..context import WebContext
from .primitives.thoughts import _error


def build_door_router(ctx: WebContext) -> APIRouter:
    service = ctx.door_service
    if service is None:
        raise RuntimeError("Door service is not composed")
    router = APIRouter(prefix="/api/door", tags=["door"])

    @router.get("")
    async def get_door(request: Request) -> Any:
        try:
            return JSONResponse(service.get(getattr(request.state, "principal", UNAUTHENTICATED)))
        except ServiceError as exc:
            return _error(exc)

    @router.post("/items")
    async def add_door_item(request: Request) -> Any:
        """Create an owner-confirmed task from a Desk object.

        MCP keeps its broader Door write contract for agents.  The web face is
        deliberately owner-only: pressing Add is the owner's consent and the
        task is already accepted for Follow-through.
        """
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            return JSONResponse({"error": "owner_required"}, status_code=403)
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        source_type = str(body.get("source_type") or "").strip().lower()
        if source_type not in {"meeting", "thread", "thought"}:
            return JSONResponse({"error": "invalid_source_type"}, status_code=422)
        try:
            item = service.add_item(
                principal,
                str(body.get("task") or ""),
                owner=(str(body["owner"]).strip() if body.get("owner") is not None else None),
                due=(str(body["due"]).strip() if body.get("due") is not None else None),
                source_type=source_type,
                source_ref=str(body.get("source_ref") or "").strip(),
            )
            return JSONResponse({"item": item}, status_code=201)
        except ServiceError as exc:
            return _error(exc)

    return router
