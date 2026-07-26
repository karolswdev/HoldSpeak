"""PR-receipt routes (HS-104-04).

Read-only rows for registered sources; refresh is the surface verb
(one batched `gh` per source), the diff is local-only with the honest
absence + explicit-fetch offer. Reads never shell out; the cadence
hook runs only for sources whose registry entry explicitly set
`pr_refresh_seconds`. Blocking work runs off the event loop (the
Phase-85 rule); assembly is lazy (the delivery-router precedent).
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ..context import WebContext

log = get_logger("web.routes.delivery_prs")


def _classified_500(exc: Exception, detail: str) -> JSONResponse:
    log.error(f"{detail}: {exc}")
    return JSONResponse({"error": detail}, status_code=500)


def build_delivery_prs_router(
    ctx: WebContext,
    *,
    service: Any = None,
    attempts_service: Any = None,
    registry_path: Optional[Path] = None,
    map_path: Optional[Path] = None,
    runner: Any = None,
) -> APIRouter:
    _ = ctx
    router = APIRouter()
    holder: dict[str, Any] = {"service": service, "attempts": attempts_service}

    def _service() -> Any:
        if holder["service"] is None:
            from ...delivery import DeliveryRegistry
            from ...delivery.pr_receipts import PrReceiptsService

            registry = DeliveryRegistry(registry_path, map_path=map_path)
            holder["service"] = PrReceiptsService(registry, runner=runner)
        return holder["service"]

    def _attempt_story_ids() -> list[str]:
        """Story ids from the durable Work attempts — the heuristic
        correlation input. Best-effort: an empty list only means no
        heuristic labels, never a failure."""
        try:
            if holder["attempts"] is not None:
                rows = holder["attempts"].list()
            else:
                from ...db import get_database

                rows = get_database().work_attempts.list()
            ids = []
            for row in rows:
                story_id = getattr(row, "story_id", None) or (
                    row.get("story_id") if isinstance(row, dict) else None
                )
                if story_id:
                    ids.append(str(story_id))
            return sorted(set(ids))
        except Exception:
            return []

    @router.get("/api/delivery/prs")
    async def api_delivery_prs() -> Any:
        """Cached rows + freshness. Never shells; the only side path
        is the explicitly configured per-source cadence."""
        try:
            def read() -> dict[str, Any]:
                service = _service()
                service.maybe_cadence_refresh(_attempt_story_ids())
                return service.rows_view()

            return await asyncio.to_thread(read)
        except Exception as exc:
            return _classified_500(exc, "pr receipts read failed")

    @router.post("/api/delivery/prs/refresh")
    async def api_delivery_prs_refresh(source_id: Optional[str] = None) -> Any:
        """The manual verb — the one place a poll is asked for."""
        try:
            return await asyncio.to_thread(
                lambda: _service().refresh(source_id, attempt_story_ids=_attempt_story_ids())
            )
        except Exception as exc:
            return _classified_500(exc, "pr receipts refresh failed")

    @router.get("/api/delivery/prs/{source_id}/{number}/diff")
    async def api_delivery_pr_diff(source_id: str, number: int) -> Any:
        try:
            result = await asyncio.to_thread(lambda: _service().diff(source_id, number))
            status = 404 if result.get("status") == "unknown_pr" else 200
            return JSONResponse(result, status_code=status)
        except Exception as exc:
            return _classified_500(exc, "pr diff failed")

    @router.post("/api/delivery/prs/{source_id}/{number}/fetch")
    async def api_delivery_pr_fetch(source_id: str, number: int) -> Any:
        """The explicit egress act the diff absence offers."""
        try:
            result = await asyncio.to_thread(lambda: _service().fetch(source_id, number))
            status = 404 if result.get("status") == "unknown_pr" else 200
            return JSONResponse(result, status_code=status)
        except Exception as exc:
            return _classified_500(exc, "pr fetch failed")

    return router
