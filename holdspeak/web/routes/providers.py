"""Provider routes (HS-161-04, HS-166, HS-174-07): GitHub, Jira and Confluence.

Produced from ``holdspeak/provider_operations.py`` (2026-11-09): every
``/api/providers`` route is ``OperationRegistry.invoke`` over its declared
row, served by the composed adapters through ``services/provider_service.py``;
the ``provider.*`` MCP tools come from the same rows. A refusal answers
``{code, message}`` with its status (``provider_not_configured`` 404, a
validation 400). The hand-written bodies are parked
(``_parked/providers_handwritten_20261109.py``).

Kept hand-written here: ``POST /api/watches/{watch_id}/evaluate`` holds
``graduated_only`` for the declared ``project.watch.evaluate`` (a produced
route passes no held input) and answers with its receipt.
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...principals import UNAUTHENTICATED
from ...provider_operations import PROVIDER_OPERATIONS
from ...services.errors import NotFound, ServiceError, ValidationError
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router

log = get_logger("web.routes.providers")


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except OperationRefused as exc:
        return JSONResponse({"code": exc.code, "message": exc.detail}, status_code=400)
    except ServiceError as exc:
        status = 404 if isinstance(exc, NotFound) else 400 if isinstance(exc, ValidationError) \
            else int((exc.context or {}).get("status") or 400)
        return JSONResponse({"code": exc.code, "message": exc.detail}, status_code=status)
    except Exception as exc:
        return error_500(exc, log, "The provider request failed")


def build_providers_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["providers"])

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def registry() -> Any:
        from ...services.provider_service import from_context

        return operations.for_context(ctx, provider_service=lambda: from_context(ctx))

    mount_router(router, operation_router(PROVIDER_OPERATIONS, registry, _answer, module=__name__))

    @router.post("/api/watches/{watch_id}/evaluate")
    def evaluate_watch(watch_id: str, request: Request) -> Any:
        """Manual evaluate_once: the declared project.watch.evaluate, admitted (egress), with its receipt."""
        from ._room_kernel import kernel_fields, kernel_refusal, refusal_fields

        try:
            result, kernel = operations.for_context(ctx).invoke_receipted(
                principal(request), "project.watch.evaluate", {"watch_id": watch_id},
                held={"graduated_only": False},
            )
            return JSONResponse({"success": True, **result, **kernel_fields(kernel)})
        except ServiceError as exc:
            if (refused := kernel_refusal(exc)) is not None:
                return refused
            status = 404 if isinstance(exc, NotFound) else int((exc.context or {}).get("status", 400))
            return JSONResponse(
                {"code": exc.code, "message": exc.detail, **refusal_fields(exc)},
                status_code=status,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to evaluate watch")

    return router
