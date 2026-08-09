"""HTTP transport for application settings (HS-123-03)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
from ....services.errors import ConflictError, ValidationError
from ....services.settings_service import SettingsService
from ...context import WebContext
from ...runtime_support import error_500
from .settings_secrets import register_settings_secret_routes

log = get_logger("web.routes.system")


def _principal(request: Request):
    return getattr(request.state, "principal", UNAUTHENTICATED)


def _service(ctx: WebContext) -> SettingsService:
    if not isinstance(ctx.settings_service, SettingsService):
        raise RuntimeError("SettingsService was not supplied at application composition")
    return ctx.settings_service


def build_settings_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/settings")
    async def api_get_settings(request: Request) -> Any:
        try:
            from ....plugins.dictation.runtime_counters import get_counters, get_session_status

            payload = _service(ctx).get_settings(_principal(request))
            # Runtime fields are read-only enrichment, retained verbatim from the
            # previous HTTP response rather than becoming persisted service state.
            payload["_runtime_status"] = {
                "counters": get_counters(),
                "session": get_session_status(),
            }
            return JSONResponse(payload)
        except Exception as exc:
            return error_500(exc, log, "Failed to load settings")

    @router.put("/api/settings")
    async def api_update_settings(payload: dict[str, Any], request: Request) -> Any:
        try:
            return JSONResponse(_service(ctx).update_settings(_principal(request), payload))
        except ConflictError as exc:
            # HS-130-07: a stale partial-tree write. Reject with 409 and hand
            # back the current revision so the client can reload + reconcile.
            return JSONResponse(
                {
                    "success": False,
                    "error": exc.detail,
                    "revision": exc.context.get("revision", ""),
                },
                status_code=409,
            )
        except ValidationError as exc:
            return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
        except Exception as exc:
            log.error("Failed to update settings: %s", exc)
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

    register_settings_secret_routes(router, ctx)
    return router
