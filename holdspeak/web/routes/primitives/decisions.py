"""Desk-authored Architecture Decision Record CRUD (HS-113-08)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body, _new_id

log = get_logger("web.routes.primitives")


def _decision_payload(record: Any) -> dict[str, Any]:
    return record.to_dict()


def build_desk_decisions_router(ctx: WebContext) -> APIRouter:
    del ctx
    router = APIRouter()

    @router.get("/api/decisions")
    async def api_list_desk_decisions() -> Any:
        try:
            from ....db import get_database
            return JSONResponse({"decisions": [_decision_payload(row) for row in get_database().desk_decisions.list()]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list decisions")

    @router.post("/api/decisions")
    async def api_create_decision(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ....db import get_database
            decision = get_database().desk_decisions.upsert(
                decision_id=str(body.get("id") or _new_id("decision")),
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
            return JSONResponse({"decision": _decision_payload(decision)}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create decision")

    @router.get("/api/decisions/{decision_id}")
    async def api_get_desk_decision(decision_id: str) -> Any:
        try:
            from ....db import get_database
            decision = get_database().desk_decisions.get(decision_id)
            if decision is None:
                return JSONResponse({"error": f"Unknown decision: {decision_id}"}, status_code=404)
            return JSONResponse({"decision": _decision_payload(decision)})
        except Exception as exc:
            return error_500(exc, log, "Failed to get decision")

    @router.put("/api/decisions/{decision_id}")
    async def api_update_decision(decision_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ....db import get_database
            decision = get_database().desk_decisions.update(decision_id, **body)
            if decision is None:
                return JSONResponse({"error": f"Unknown decision: {decision_id}"}, status_code=404)
            return JSONResponse({"decision": _decision_payload(decision)})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to update decision")

    @router.delete("/api/decisions/{decision_id}")
    async def api_delete_decision(decision_id: str) -> Any:
        try:
            from ....db import get_database
            if not get_database().desk_decisions.delete(decision_id):
                return JSONResponse({"error": f"Unknown decision: {decision_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete decision")

    @router.put("/api/decisions/{decision_id}/status")
    async def api_update_decision_status(decision_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ....db import get_database
            decision = get_database().desk_decisions.update(decision_id, status=body.get("status"))
            if decision is None:
                return JSONResponse({"error": f"Unknown decision: {decision_id}"}, status_code=404)
            return JSONResponse({"decision": _decision_payload(decision)})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to update decision status")

    @router.post("/api/decisions/{decision_id}/supersede")
    async def api_supersede_decision(decision_id: str) -> Any:
        try:
            from ....db import get_database
            successor = get_database().desk_decisions.supersede(decision_id, _new_id("decision"))
            if successor is None:
                return JSONResponse({"error": f"Unknown decision: {decision_id}"}, status_code=404)
            return JSONResponse({"decision": _decision_payload(successor) }, status_code=201)
        except Exception as exc:
            return error_500(exc, log, "Failed to supersede decision")

    return router
