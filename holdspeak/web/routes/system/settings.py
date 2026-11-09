"""HTTP transport for application settings (HS-123-03), produced from ``holdspeak/settings_operations.py``.

``/api/settings`` (read and write), the hub read and the heartbeat are each
``OperationRegistry.invoke`` over a declared row. The answers keep the words
the hand-written handlers answered with: a stale write is a 409 with the
current ``revision``; a refused value a 400 ``{success: false, error}``.
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .... import operations
from ....logging_config import get_logger
from ....operations import OperationRefused
from ....services.errors import ConflictError, ServiceError, ValidationError
from ....principals import UNAUTHENTICATED
from ....settings_operations import LIVE_HEARTBEAT_SERVICE, SETTINGS_ROUTE_OPERATIONS
from ...context import WebContext
from ...operation_routes import operation_router
from ...runtime_support import error_500
from .._mount import mount_router
from .settings_secrets import register_settings_secret_routes

log = get_logger("web.routes.system")

#: The rows this module produces (the authority and Reach rows live beside their own routes).
_SETTINGS = tuple(d for d in SETTINGS_ROUTE_OPERATIONS if d.http and d.http[1].startswith("/api/settings"))


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except OperationRefused as exc:
        return JSONResponse({"success": False, "code": exc.code, "error": exc.detail},
                            status_code=403 if exc.code == "owner_required" else 400)
    except ConflictError as exc:
        # HS-130-07: a stale partial-tree write; the client reloads and reconciles.
        return JSONResponse({"success": False, "error": exc.detail, "revision": exc.context.get("revision", "")},
                            status_code=409)
    except ValidationError as exc:
        return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
    except ServiceError as exc:
        return JSONResponse({"success": False, "error": exc.detail}, status_code=int(exc.context.get("status") or 400))
    except Exception as exc:
        return error_500(exc, log, "Settings failed")


def _update(ops: Callable[[], Any], descriptor: Any) -> Callable[..., Any]:
    """PUT /api/settings: the body IS the patch. It is passed as ``patch``, so a
    settings section named like an authority field (``owner``) stays data."""

    async def api_update_settings(request: Request) -> Any:
        try:
            body = await request.json()
        except Exception:
            body = None
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        return await _answer(lambda: ops().invoke(principal, descriptor.name, {"patch": body}, shape="web"))

    return api_update_settings


def build_settings_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def hub() -> Any:  # a partially wired context's hub read, over the services it carries
        from ....services.settings_hub_service import SettingsHubService

        return SettingsHubService(model_library_service=ctx.model_library_service,
                                  inference_assignment_service=ctx.inference_assignment_service,
                                  cadence_service=ctx.cadence_service)

    def ops() -> Any:
        return operations.for_context(ctx, settings_hub_service=hub,
                                      heartbeat_service=lambda: LIVE_HEARTBEAT_SERVICE)

    mount_router(router, operation_router(
        [d for d in _SETTINGS if d.name != "settings.update"], ops, _answer, module=__name__,
    ))
    mount_router(router, operation_router(
        [d for d in _SETTINGS if d.name == "settings.update"], ops, _answer, module=__name__,
        hand_written={"settings.update": lambda descriptor: _update(ops, descriptor)},
    ))
    register_settings_secret_routes(router, ctx)
    return router
