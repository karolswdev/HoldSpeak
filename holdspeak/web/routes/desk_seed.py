"""The architect's desk — seed + reset routes (HS-112-03).

Thin wrappers over ``holdspeak.db.seed`` (the same repositories the
primitive routes wrap). Both are POSTs under ``/api/`` with no narrower
right named in ``principals.required_right``, so the centralized edge
gate requires the OWNER principal — reset is the desk's first
destructive act and belongs to the owner alone.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.desk_seed")


def build_desk_seed_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.post("/api/desk/seed")
    async def api_desk_seed() -> Any:
        try:
            from ...db import get_database
            from ...db.seed import apply_seed

            report = apply_seed(get_database())
            return JSONResponse({"success": True, **report.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to seed the desk")

    @router.post("/api/desk/reset")
    async def api_desk_reset() -> Any:
        try:
            from ...db import get_database
            from ...db.seed import reset_desk

            report = reset_desk(get_database())
            seed = report.seed
            return JSONResponse({
                "success": True,
                "tombstoned": dict(report.tombstoned),
                "tombstoned_total": report.tombstoned_total,
                "seeded": dict(seed.applied) if seed else {},
                "seeded_total": seed.total if seed else 0,
                "filed": seed.filed if seed else 0,
                "manifest": seed.manifest if seed else None,
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to reset the desk")

    return router
