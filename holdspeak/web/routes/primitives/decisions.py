"""Desk-authored Architecture Decision Record CRUD — thin adapter (HS-122-01).

PHILO-5-01: create, update, read and list are calls to the application-operation
contract (``holdspeak.operations``), bound at hub composition to the hub's one
live ``PrimitiveService``. Each route maps its request onto the operation's
arguments and maps the result back exactly as before. PHILO-7-02: delete,
status and supersede are declared operations too, and every decision write is
ADMITTED (Article XI, D3): the response carries ``operation_id`` and the
terminal kernel ``receipt`` beside the envelope it always had.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .... import operations
from ....logging_config import get_logger
from ....services.errors import NotFound, ServiceError
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body, _kernel_fields, _refusal_kernel

log = get_logger("web.routes.primitives")


def _service_refusal(exc: ServiceError) -> JSONResponse:
    """A named refusal the routes did not map before (PHILO-7-02: a kernel refusal).

    Its status comes from the error (``desk_delegation_*``: 403); the body names
    the code and carries the refusal receipt.
    """
    status = int(exc.context.get("status") or 409)
    return JSONResponse({"error": exc.code, "detail": exc.detail, **exc.context}, status_code=status)


def build_desk_decisions_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _ops() -> operations.OperationRegistry:
        return operations.for_context(ctx, "primitive_service")

    def _principal(request: Request) -> Any:
        return getattr(request.state, "principal", None)

    @router.get("/api/decisions")
    async def api_list_desk_decisions(request: Request) -> Any:
        try:
            return JSONResponse({"decisions": _ops().invoke(_principal(request), "decision.list", {})})
        except Exception as exc:
            return error_500(exc, log, "Failed to list decisions")

    @router.post("/api/decisions")
    async def api_create_decision(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            decision, kernel = _ops().invoke_receipted(_principal(request), "decision.create", {
                "decision_id": str(body.get("id") or "") or None,
                "title": str(body.get("title") or "New decision"),
                "status": str(body.get("status") or "proposed"),
                "deciders": list(body.get("deciders") or []),
                "decided_at": body.get("decided_at"),
                "context_markdown": str(body.get("context_markdown") or ""),
                "decision_markdown": str(body.get("decision_markdown") or ""),
                "alternatives": list(body.get("alternatives") or []),
                "consequences_markdown": str(body.get("consequences_markdown") or ""),
                "tags": list(body.get("tags") or []),
            })
            return JSONResponse({"decision": decision, **_kernel_fields(kernel)}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc), **_refusal_kernel(exc)}, status_code=400)
        except ServiceError as exc:
            return _service_refusal(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to create decision")

    @router.get("/api/decisions/{decision_id}")
    async def api_get_desk_decision(decision_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"decision": _ops().invoke(
                _principal(request), "decision.read", {"decision_id": decision_id})})
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
            decision, kernel = _ops().invoke_receipted(
                _principal(request), "decision.update", operations.update_args(body, decision_id))
            return JSONResponse({"decision": decision, **_kernel_fields(kernel)})
        except NotFound as exc:
            return JSONResponse({"error": f"Unknown decision: {decision_id}", **_refusal_kernel(exc)}, status_code=404)
        except ValueError as exc:
            return JSONResponse({"error": str(exc), **_refusal_kernel(exc)}, status_code=400)
        except ServiceError as exc:
            return _service_refusal(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to update decision")

    @router.delete("/api/decisions/{decision_id}")
    async def api_delete_decision(decision_id: str, request: Request) -> Any:
        try:
            _deleted, kernel = _ops().invoke_receipted(
                _principal(request), "decision.delete", {"decision_id": decision_id})
            return JSONResponse({"success": True, **_kernel_fields(kernel)})
        except NotFound as exc:
            return JSONResponse({"error": f"Unknown decision: {decision_id}", **_refusal_kernel(exc)}, status_code=404)
        except ServiceError as exc:
            return _service_refusal(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete decision")

    @router.put("/api/decisions/{decision_id}/status")
    async def api_update_decision_status(decision_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            decision, kernel = _ops().invoke_receipted(_principal(request), "decision.status", {
                "decision_id": decision_id, "status": body.get("status", "")})
            return JSONResponse({"decision": decision, **_kernel_fields(kernel)})
        except NotFound as exc:
            return JSONResponse({"error": f"Unknown decision: {decision_id}", **_refusal_kernel(exc)}, status_code=404)
        except ValueError as exc:
            return JSONResponse({"error": str(exc), **_refusal_kernel(exc)}, status_code=400)
        except ServiceError as exc:
            return _service_refusal(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to update decision status")

    @router.post("/api/decisions/{decision_id}/supersede")
    async def api_supersede_decision(decision_id: str, request: Request) -> Any:
        try:
            decision, kernel = _ops().invoke_receipted(
                _principal(request), "decision.supersede", {"decision_id": decision_id})
            return JSONResponse({"decision": decision, **_kernel_fields(kernel)}, status_code=201)
        except NotFound as exc:
            return JSONResponse({"error": f"Unknown decision: {decision_id}", **_refusal_kernel(exc)}, status_code=404)
        except ServiceError as exc:
            return _service_refusal(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to supersede decision")

    return router
