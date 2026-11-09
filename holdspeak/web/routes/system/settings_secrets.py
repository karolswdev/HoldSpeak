"""Write-only credential routes, produced from ``holdspeak/settings_operations.py``.

Each route is ``OperationRegistry.invoke`` over a declared row (owner-only,
no MCP tool). The answer keeps the words the hand-written handlers answered
with: ``{success: true, secrets}``, a 404 ``Unknown secret setting`` and a
400 with the refusal's detail.
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .... import operations
from ....logging_config import get_logger
from ....services.credential_service import redacted_settings, strip_secret_mutations
from ....services.errors import NotFound, ServiceError
from ...context import WebContext
from ...operation_routes import operation_router
from ...runtime_support import error_500
from .._mount import mount_router

log = get_logger("web.routes.system.settings_secrets")


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except NotFound:
        return JSONResponse({"success": False, "error": "Unknown secret setting"}, status_code=404)
    except ServiceError as exc:
        return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
    except Exception as exc:
        return error_500(exc, log, "Failed to change secret setting")


def register_settings_secret_routes(router: APIRouter, ctx: WebContext) -> None:
    if ctx.credential_service is None:
        raise RuntimeError("CredentialService must be supplied at application composition")
    mount_router(router, operation_router(
        operations.SETTINGS_OPERATIONS, lambda: operations.for_context(ctx), _answer, module=__name__,
    ))


__all__ = [
    "redacted_settings",
    "register_settings_secret_routes",
    "strip_secret_mutations",
]
