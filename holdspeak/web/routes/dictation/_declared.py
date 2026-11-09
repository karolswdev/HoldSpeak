"""The dictation routes produced from ``holdspeak/dictation_operations.py`` (2026-11-09), through
``OperationRegistry.invoke``; a refusal keeps the status and the body the hand-written handler answered with."""
from __future__ import annotations

from typing import Any, Callable

from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .... import operations
from ....db import get_observer
from ....logging_config import get_logger
from ....services.dictation_service import DictationService, bind_dictation_runtime
from ....services.errors import NotFound, ServiceError, ValidationError
from ...context import WebContext
from ...operation_routes import operation_router
from .._mount import mount_router

log = get_logger("web.routes.dictation")


def _service(ctx: WebContext) -> DictationService:
    """The context's service, else one over the context's journal (a partial route context)."""
    service = ctx.dictation_service if isinstance(ctx.dictation_service, DictationService) else DictationService(
        journal_repository=getattr(ctx.journal, "repository", None),
        journal_available=ctx.journal is not None,
        delivery_repository=ctx.dictation_deliveries,
        observer=get_observer(),
    )
    return bind_dictation_runtime(service, ctx)


def registry_for(ctx: WebContext) -> Callable[[], operations.OperationRegistry]:
    """The hub's bound contract, else one over this context's service."""
    built: list[Any] = []

    def registry() -> operations.OperationRegistry:
        bound = getattr(ctx, "operations", None)
        if bound is not None:
            return bound
        if not built:
            built.append(operations.bind_available({"dictation_service": _service(ctx)}))
        return built[0]

    return registry


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except NotFound as exc:
        return JSONResponse({"error": exc.detail}, status_code=404)
    except ValidationError as exc:
        return JSONResponse(exc.context.get("body") or {"error": exc.detail},
                            status_code=int(exc.context.get("status") or 400))
    except ServiceError as exc:
        return JSONResponse(exc.context.get("body") or {"error": exc.detail, "code": exc.code},
                            status_code=int(exc.context.get("status") or 400))
    except Exception as exc:
        log.error(f"dictation verb failed: {exc}")
        return JSONResponse({"error": str(exc)}, status_code=500)


def build_declared_router(ctx: WebContext, names: tuple[str, ...]) -> Any:
    """The routes of the named dictation operations, in the order named."""
    by_name = {descriptor.name: descriptor for descriptor in operations.DICTATION_OPERATIONS}
    produced = operation_router([by_name[name] for name in names], registry_for(ctx), _answer, module=__name__)
    from fastapi import APIRouter

    router = APIRouter()
    mount_router(router, produced)
    return router


__all__ = ["build_declared_router", "registry_for"]
