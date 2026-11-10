"""The control mode over HTTP, produced from ``holdspeak/settings_operations.py``.

``GET /api/authority/policy`` (``authority.policy``) and
``PUT /api/authority/control-mode`` (``authority.control_mode.set``: owner
only, his press, no MCP tool). The answers keep the hand-written words:
``{error}`` with 400 on a refused value, 409 on a conflict.
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ...settings_operations import SETTINGS_ROUTE_OPERATIONS
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router

log = get_logger("web.routes.authority")


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except operations.OperationOwnerRequired as exc:
        return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=403)
    except OperationRefused as exc:
        return JSONResponse({"error": exc.detail, "code": exc.code},
                            status_code=403 if exc.code == "owner_required" else 400)
    except ValidationError as exc:
        return JSONResponse({"error": exc.detail}, status_code=400)
    except ConflictError as exc:
        return JSONResponse({"error": exc.detail}, status_code=409)
    except NotFound:
        return JSONResponse({"error": "Proposed action not found"}, status_code=404)
    except ServiceError as exc:
        return JSONResponse({"error": exc.detail}, status_code=400)
    except Exception as exc:
        return error_500(exc, log, "Failed to read or change the control mode")


def build_authority_router(ctx: WebContext) -> APIRouter:
    if ctx.authority_service is None:
        raise RuntimeError("AuthorityService must be supplied at application composition")
    router = APIRouter()
    rows = tuple(d for d in SETTINGS_ROUTE_OPERATIONS if d.name.startswith("authority."))
    mount_router(router, operation_router(rows, lambda: operations.for_context(ctx), _answer, module=__name__))
    return router
