"""Authenticated long-horizon memory retrieval (HS-109-04)."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

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
            # Off the event loop: a search reads the database and may wait
            # (a bounded time) for the question's embedding.
            return JSONResponse(await run_in_threadpool(
                service.search, request.state.principal, query, kind=kind,
                project_id=project_id, time_from=time_from, time_to=time_to,
                limit=limit, offset=offset,
            ))
        except ValidationError as exc:
            return JSONResponse({"error": exc.detail}, status_code=400)
        except ServiceError as exc:
            response = exc.context.get("response")
            return JSONResponse(response if isinstance(response, dict) else {"error": exc.detail}, status_code=int(exc.context.get("status") or 400))

    @router.get("/recall")
    async def recall_memory(
        request: Request, query: str = "", filter: Optional[str] = "all",
        limit: int = 50, recent: str = "",
    ) -> Any:
        """HS-200-13: the Desk memory face's one read -- CURRENT / SUPERSEDED /
        DISPUTED / OWED over one query (holdspeak/services/recall_service.py).

        HS-202-02: `recent=1` with no query answers the desk's newest memory,
        so the face named "Desk memory" is not a blank field on a desk that
        holds a meeting, decisions and a brief."""
        from ...db import get_database
        from ...services.recall_service import RecallService
        newest = str(recent or "").strip().lower() in {"1", "true", "yes", "on"}
        try:
            payload = RecallService(get_database()).recall(
                request.state.principal, query, filter=filter or "all",
                limit=limit, recent=newest,
            )
            return JSONResponse(payload)
        except ValidationError as exc:
            return JSONResponse({"error": exc.detail}, status_code=400)
        except ServiceError as exc:
            response = exc.context.get("response")
            return JSONResponse(response if isinstance(response, dict) else {"error": exc.detail}, status_code=int(exc.context.get("status") or 400))

    def _meaning() -> Any:
        meaning = getattr(service, "meaning", None)
        if meaning is None:
            raise ServiceError("meaning_search_unavailable", "Meaning search is not available on this hub.", context={"status": 503})
        return meaning

    def _meaning_error(exc: ServiceError) -> JSONResponse:
        return JSONResponse(
            {"code": exc.code, "message": exc.detail}, status_code=int(exc.context.get("status") or 400)
        )

    @router.get("/meaning-search")
    async def meaning_search_status(request: Request) -> Any:
        """OFF / DOWNLOADING / INDEXING / ON for the Settings row."""
        try:
            return JSONResponse(await run_in_threadpool(_meaning().status, request.state.principal))
        except ServiceError as exc:
            return _meaning_error(exc)

    @router.post("/meaning-search/turn-on")
    async def meaning_search_turn_on(request: Request) -> Any:
        """The owner's press.  The only path that can start the model download."""
        try:
            return JSONResponse(await run_in_threadpool(_meaning().turn_on, request.state.principal))
        except ServiceError as exc:
            return _meaning_error(exc)

    @router.post("/meaning-search/turn-off")
    async def meaning_search_turn_off(request: Request) -> Any:
        try:
            return JSONResponse(await run_in_threadpool(_meaning().turn_off, request.state.principal))
        except ServiceError as exc:
            return _meaning_error(exc)

    return router
