"""Authenticated long-horizon memory retrieval (HS-109-04)."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...principals import PrincipalKind, PrincipalRight, UNAUTHENTICATED, refusal
from ..context import WebContext


def _read_refusal(request: Request) -> Optional[JSONResponse]:
    principal = getattr(request.state, "principal", UNAUTHENTICATED)
    if principal.permits(PrincipalRight.READ):
        return None
    status = 401 if principal.kind is PrincipalKind.NONE else 403
    return JSONResponse(refusal(principal, PrincipalRight.READ), status_code=status)


def build_memory_router(ctx: WebContext) -> APIRouter:
    del ctx
    router = APIRouter(prefix="/api/memory", tags=["memory"])

    @router.get("/search")
    async def search_memory(
        request: Request,
        query: str,
        kind: Optional[str] = None,
        project_id: Optional[str] = None,
        time_from: Optional[str] = None,
        time_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Any:
        denied = _read_refusal(request)
        if denied is not None:
            return denied
        try:
            from ...db import get_database

            result = get_database().memory.search(
                query,
                kinds=kind,
                project_id=project_id,
                time_from=time_from,
                time_to=time_to,
                limit=limit,
                offset=offset,
            )
            return JSONResponse(result.to_dict())
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)

    return router
