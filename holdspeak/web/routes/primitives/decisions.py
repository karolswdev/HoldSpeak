"""Desk-authored Architecture Decision Record CRUD — thin adapter (HS-122-01)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....services.errors import NotFound
from ....services.primitive_service import PrimitiveService
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body

log = get_logger("web.routes.primitives")


def build_desk_decisions_router(ctx: WebContext) -> APIRouter:
    del ctx
    router = APIRouter()

    def _svc() -> PrimitiveService:
        from ....db import get_database, get_observer
        return PrimitiveService(get_database(), observer=get_observer())

    def _principal(request: Request) -> Any:
        return getattr(request.state, "principal", None)

    @router.get("/api/decisions")
    async def api_list_desk_decisions(request: Request) -> Any:
        try:
            return JSONResponse({"decisions": _svc().list_decisions(_principal(request))})
        except Exception as exc:
            return error_500(exc, log, "Failed to list decisions")

    @router.post("/api/decisions")
    async def api_create_decision(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            decision = _svc().create_decision(
                _principal(request),
                decision_id=str(body.get("id") or "") or None,
                title=str(body.get("title") or "New decision"),
                status=str(body.get("status") or "proposed"),
                deciders=list(body.get("deciders") or []),
                decided_at=body.get("decided_at"),
                context_markdown=str(body.get("context_markdown") or ""),
                decision_markdown=str(body.get("decision_markdown") or ""),
                alternatives=list(body.get("alternatives") or []),
                consequences_markdown=str(body.get("consequences_markdown") or ""),
                tags=list(body.get("tags") or []),
            )
            return JSONResponse({"decision": decision}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create decision")

    @router.get("/api/decisions/{decision_id}")
    async def api_get_desk_decision(decision_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"decision": _svc().get_decision(_principal(request), decision_id)})
        except NotFound:
            return JSONResponse({"error": f"Unknown decision: {decision_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to get decision")

    @router.put("/api/decisions/{decision_id}")
    async def api_update_decision(decision_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            decision = _svc().update_decision(_principal(request), decision_id, **body)
            return JSONResponse({"decision": decision})
        except NotFound:
            return JSONResponse({"error": f"Unknown decision: {decision_id}"}, status_code=404)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to update decision")

    @router.delete("/api/decisions/{decision_id}")
    async def api_delete_decision(decision_id: str, request: Request) -> Any:
        try:
            _svc().delete_decision(_principal(request), decision_id)
            return JSONResponse({"success": True})
        except NotFound:
            return JSONResponse({"error": f"Unknown decision: {decision_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete decision")

    @router.put("/api/decisions/{decision_id}/status")
    async def api_update_decision_status(decision_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            decision = _svc().update_decision_status(
                _principal(request), decision_id, body.get("status", "")
            )
            return JSONResponse({"decision": decision})
        except NotFound:
            return JSONResponse({"error": f"Unknown decision: {decision_id}"}, status_code=404)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to update decision status")

    @router.post("/api/decisions/{decision_id}/supersede")
    async def api_supersede_decision(decision_id: str, request: Request) -> Any:
        try:
            decision = _svc().supersede_decision(_principal(request), decision_id)
            return JSONResponse({"decision": decision}, status_code=201)
        except NotFound:
            return JSONResponse({"error": f"Unknown decision: {decision_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to supersede decision")

    return router
