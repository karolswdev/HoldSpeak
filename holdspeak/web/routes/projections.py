"""Thin HTTP adapters for durable Desk projections (HS-123-05)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import NotFound, ValidationError
from ...services.projection_service import ProjectionService
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.projections")


def build_projections_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/desk/projections", tags=["desk"])
    service: ProjectionService = ctx.projection_service

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    @router.get("")
    async def api_list_projections(
        request: Request, q: str = "", kind: str | None = None,
        attention_state: str | None = None, subject_ref: str | None = None,
        include_dismissed: bool = False, offset: int = 0, limit: int = 50,
    ) -> Any:
        try:
            result = service.list(principal(request), {"q": q, "kind": kind,
                "attention_state": attention_state, "subject_ref": subject_ref,
                "include_dismissed": include_dismissed, "offset": offset, "limit": limit})
            return JSONResponse({"version": 1, **result})
        except ValidationError as exc:
            return JSONResponse({"error": exc.detail}, status_code=400)
        except (TypeError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to project Desk attention and receipts")

    @router.put("/{projection_id}/presentation")
    async def api_set_projection_presentation(projection_id: str, request: Request) -> Any:
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            return JSONResponse(service.set_presentation(principal(request), projection_id, body))
        except NotFound:
            return JSONResponse({"error": "Projection not found"}, status_code=404)
        except ValidationError as exc:
            return JSONResponse({"error": exc.detail}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to update projection presentation")

    return router


__all__ = ["build_projections_router"]
