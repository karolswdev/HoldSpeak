"""Write-only credential routes, produced from ``holdspeak/settings_operations.py``.

Each route is ``OperationRegistry.invoke`` over a declared row (owner-only,
no MCP tool). The answer keeps the words the hand-written handlers answered
with: ``{success: true, secrets}``, a 404 ``Unknown secret setting`` and a
400 with the refusal's detail.
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .... import operations
from ....logging_config import get_logger
from ....services.credential_service import redacted_settings, strip_secret_mutations
from ....services.errors import NotFound, ServiceError
from ....settings_operations import CREDENTIAL_OPERATIONS
from ...context import WebContext
from ...operation_routes import operation_router
from ...runtime_support import error_500
from .._mount import mount_router

log = get_logger("web.routes.system.settings_secrets")


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except operations.OperationOwnerRequired:
        return JSONResponse({"success": False, "error": "owner_required"}, status_code=403)
    except operations.OperationRefused as exc:
        return JSONResponse({"success": False, "error": exc.code},
                            status_code=403 if exc.code == "owner_required" else 400)
    except NotFound:
        return JSONResponse({"success": False, "error": "Unknown secret setting"}, status_code=404)
    except ServiceError as exc:
        return JSONResponse({"success": False, "error": exc.detail}, status_code=int(exc.context.get("status") or 400))
    except Exception as exc:
        return error_500(exc, log, "Failed to change secret setting")


def register_settings_secret_routes(router: APIRouter, ctx: WebContext) -> None:
    if ctx.credential_service is None:
        raise RuntimeError("CredentialService must be supplied at application composition")
    def held_replace(descriptor: Any) -> Any:
        async def api_replace_secret(secret_id: str, request: Request) -> Any:
            from ....principals import UNAUTHENTICATED
            principal = getattr(request.state, "principal", UNAUTHENTICATED)
            registry = operations.for_context(ctx)
            # Authorize before parsing a credential, and never put it in args.
            try:
                registry.authorize(principal, descriptor.name)
            except operations.OperationOwnerRequired as exc:
                return JSONResponse({"success": False, "error": exc.code}, status_code=403)
            try:
                body = await request.json()
            except ValueError:
                body = None
            if not isinstance(body, dict):
                return JSONResponse({"success": False, "error": "expected a JSON object"}, status_code=400)
            value = body.pop("value", None)
            if body.get("secret_id", secret_id) != secret_id:
                return JSONResponse({"success": False, "error": "secret_id must match the path"}, status_code=400)
            # Only the documented metadata reaches the observer.
            args = {"secret_id": secret_id}
            if "header_name" in body:
                args["header_name"] = body["header_name"]
            return await _answer(lambda: registry.invoke(principal, descriptor.name, args, held={"value": value}))
        return api_replace_secret

    mount_router(router, operation_router(
        CREDENTIAL_OPERATIONS, lambda: operations.for_context(ctx), _answer, module=__name__,
        hand_written={"settings.secret.replace": held_replace},
    ))


__all__ = [
    "redacted_settings",
    "register_settings_secret_routes",
    "strip_secret_mutations",
]
