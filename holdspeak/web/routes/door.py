"""Dashboard Door transport adapter."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...principals import UNAUTHENTICATED
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

    return router
