"""Local git repository drawer routes (HS-113-06), produced from their declared rows (2026-11-09).

The verbs live in ``services/repository_drawer_service.py`` and are declared
in ``holdspeak/repository_operations.py``; each route here is produced from its
row through ``OperationRegistry.invoke``. A refusal answers ``{"error": words}``
with its status, as the hand-written routes did. The four writes that take a
worktree scope read it from the query AND the body (a conflict is refused), so
they keep a thin handler that passes the query's scope as ``query_worktree_id``.
"""
from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...delivery import DeliveryRegistry
from ...logging_config import get_logger
from ...redaction import redact_error
from ...repository_operations import REPOSITORY_DRAWER_OPERATIONS
from ...services.errors import ServiceError
from ...services.repository_drawer_service import RepositoryDrawerService
from ...services.repository_workspace import safe_path
from ..context import WebContext
from ..operation_routes import ContractRefusal, _body, _invoke, _principal
from ._produced import produced

log = get_logger("web.routes.repositories")

_safe_path = safe_path

#: The writes whose worktree scope may come from the query too.
_SCOPED = frozenset({"repository.write_file", "repository.stage", "repository.commit", "repository.checkout"})


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except ContractRefusal as exc:
        return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=400)
    except operations.OperationOwnerRequired as exc:
        return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=403)
    except ServiceError as exc:
        return JSONResponse({"error": exc.detail}, status_code=int(exc.context.get("status") or 400))
    except Exception as exc:
        log.error("repository route failed: %s", redact_error(exc))
        return JSONResponse({"error": "repository request failed"}, status_code=500)


def _scoped_handler(registry: Callable[[], Any]) -> Callable[[Any], Callable[..., Any]]:
    def build(descriptor: Any) -> Callable[..., Any]:
        names = [part[1:-1].split(":", 1)[0] for part in descriptor.http[1].split("/") if part.startswith("{")]

        async def endpoint(request: Request, **params: str) -> Any:
            principal = _principal(request)
            args = {**await _body(request), **params}
            if "worktree_id" in request.query_params:
                args["query_worktree_id"] = request.query_params["worktree_id"]
            return await _answer(lambda: _invoke(registry, principal, descriptor.name, args))

        endpoint.__signature__ = inspect.Signature(  # type: ignore[attr-defined]
            [inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY, annotation=str) for name in names]
            + [inspect.Parameter("request", inspect.Parameter.KEYWORD_ONLY, annotation=Request)],
            return_annotation=Any,
        )
        endpoint.__name__ = endpoint.__qualname__ = descriptor.handler
        endpoint.__module__ = __name__
        return endpoint

    return build


def build_repositories_router(
    ctx: WebContext,
    *,
    registry: Optional[DeliveryRegistry] = None,
    registry_path: Optional[Path] = None,
    map_path: Optional[Path] = None,
) -> APIRouter:
    """The drawer's routes. ``registry``/``registry_path``/``map_path``: a context the hub did not
    compose (a test) binds one service over them; the hub's routes reach its composed service."""
    drawer = RepositoryDrawerService(registry=registry, registry_path=registry_path, map_path=map_path)

    def ops() -> operations.OperationRegistry:
        return operations.for_context(ctx, repository_drawer_service=lambda: drawer)

    build = _scoped_handler(ops)
    return produced(ctx, REPOSITORY_DRAWER_OPERATIONS, _answer, module=__name__,
                    hand_written={name: build for name in _SCOPED},
                    repository_drawer_service=lambda: drawer)
