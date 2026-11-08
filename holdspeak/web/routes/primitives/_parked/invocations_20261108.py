"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/primitives/invocations.py``: POST /api/invocations/{invocation_id}/cancel.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""Read-only capability run receipts for retry, inspection, and return."""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .....logging_config import get_logger
from .....principals import Principal, PrincipalKind
from .....services.errors import ConflictError, NotFound
from .....services.invocation_service import InvocationService
from ....context import WebContext
from ....runtime_support import error_500

log = get_logger("web.routes.primitives.invocations")


def recover_inference_on_startup() -> list[str]:
    """Project hub-killed, actually claimed inference attempts as unknown."""
    return InvocationService.recover_inference_on_startup()


def parked_build_invocations_router(ctx: WebContext) -> APIRouter:
    del ctx
    router = APIRouter()
    service = InvocationService.from_runtime()

    def _principal(request: Request | None = None) -> Principal:
        return getattr(
            getattr(request, "state", None),
            "principal",
            Principal(PrincipalKind.OWNER, "owner-session"),
        )

    @router.post("/api/invocations/{invocation_id}/cancel")
    def api_cancel_invocation(invocation_id: str, request: Request) -> Any:
        """Submit, claim, and receipt an owner cancellation signal."""
        try:
            result = service.cancel(_principal(request), invocation_id)
            return JSONResponse(result, status_code=202)
        except NotFound:
            return JSONResponse({"error": f"Unknown inference run: {invocation_id}"}, status_code=404)
        except ConflictError as exc:
            if exc.code == "cancellation_refused":
                return JSONResponse(exc.context["handle"], status_code=409)
            return JSONResponse({"error": str(exc)}, status_code=409)
        except Exception as exc:
            return error_500(exc, log, "Failed to cancel capability invocation")

    return router
