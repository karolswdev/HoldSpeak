"""Authenticated long-horizon memory retrieval (HS-109-04)."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...services.errors import ServiceError, ValidationError
from ..context import WebContext


def build_memory_router(ctx: WebContext) -> APIRouter:
    service = ctx.memory_service
    if service is None:
        raise RuntimeError("MemoryService must be supplied at application composition")
    router = APIRouter(prefix="/api/memory", tags=["memory"])

    @router.get("/search")
    async def search_memory(
        request: Request, query: str, kind: Optional[str] = None,
        project_id: Optional[str] = None, time_from: Optional[str] = None,
        time_to: Optional[str] = None, limit: int = 50, offset: int = 0,
    ) -> Any:
        try:
            return JSONResponse(service.search(request.state.principal, query, kind=kind, project_id=project_id, time_from=time_from, time_to=time_to, limit=limit, offset=offset))
        except ValidationError as exc:
            return JSONResponse({"error": exc.detail}, status_code=400)
        except ServiceError as exc:
            response = exc.context.get("response")
            return JSONResponse(response if isinstance(response, dict) else {"error": exc.detail}, status_code=int(exc.context.get("status") or 400))

    @router.get("/recall")
    async def recall_memory(
        request: Request, query: str = "", filter: Optional[str] = "all", limit: int = 50,
    ) -> Any:
        """HS-200-13: the Desk memory face's one read -- CURRENT / SUPERSEDED /
        DISPUTED / OWED over one query (holdspeak/services/recall_service.py)."""
        from ...db import get_database
        from ...services.recall_service import RecallService
        try:
            payload = RecallService(get_database()).recall(
                request.state.principal, query, filter=filter or "all", limit=limit,
            )
            return JSONResponse(payload)
        except ValidationError as exc:
            return JSONResponse({"error": exc.detail}, status_code=400)
        except ServiceError as exc:
            response = exc.context.get("response")
            return JSONResponse(response if isinstance(response, dict) else {"error": exc.detail}, status_code=int(exc.context.get("status") or 400))

    return router
