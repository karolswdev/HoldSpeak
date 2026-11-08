"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/watches.py``: GET /api/watches.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""HS-159-04: Watch routes -- the universal Watch surface on the wire.

GET  /api/watches                           -- list all watches
GET  /api/projects/{project_id}/watches     -- list project watches
GET  /api/watches/{watch_id}                -- get watch with rules
PATCH /api/watches/{watch_id}               -- update (material-edit semantics)
POST /api/watches/{watch_id}/test           -- bounded read test
POST /api/watches/{watch_id}/baseline       -- establish baseline
POST /api/watches/{watch_id}/pause          -- pause
POST /api/watches/{watch_id}/resume         -- resume
POST /api/watches/{watch_id}/retire         -- retire
PUT  /api/watches/{watch_id}/rules          -- replace rules

Parse-and-serialize ONLY; owner-scoped; typed errors -> correct statuses.
"""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
from .... import operations
from ....operations import OperationRefused
from ....services.errors import NotFound, ServiceError, ValidationError
from ...context import WebContext
from ...runtime_support import error_500
from .._room_kernel import kernel_fields, kernel_refusal, refusal_fields

log = get_logger("web.routes.watches")


def parked_build_watches_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["watches"])

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    # ── GET /api/watches ─────────────────────────────────────────

    @router.get("/api/watches")
    def list_watches(
        request: Request,
        state: str | None = None,
        connector: str | None = None,
    ) -> Any:
        try:
            watches = ctx.watch_service.list_watches(
                principal(request), state=state, connector=connector,
            )
            return JSONResponse({"watches": watches})
        except Exception as exc:
            return error_500(exc, log, "Failed to list watches")

    # ── GET /api/projects/{project_id}/watches ───────────────────

    def ops() -> Any:
        return operations.for_context(ctx)

    def _refused(exc: ServiceError) -> JSONResponse:
        if (refused := kernel_refusal(exc)) is not None:
            return refused
        if isinstance(exc, NotFound):
            return JSONResponse({"code": exc.code, "message": exc.detail, **refusal_fields(exc)}, status_code=404)
        if isinstance(exc, ValidationError):
            return JSONResponse({"code": exc.code, "message": exc.detail,
                                 **({"errors": exc.context["errors"]} if "errors" in exc.context else {}),
                                 **refusal_fields(exc)}, status_code=400)
        status = int((exc.context or {}).get("status", 400))
        return JSONResponse({"code": exc.code, "message": exc.detail, **refusal_fields(exc)}, status_code=status)

    #: HTTP reaches every watch row (the MCP tools, graduated rows only).
    _ALL_ROWS = {"graduated_only": False}

    async def _admitted(request: Request, watch_id: str, name: str, args: dict[str, Any] | None = None,
                        *, held: bool = True, wrap: Any = None, what: str) -> Any:
        """PHILO-9-02: one admitted watch operation -- one kernel operation and its receipt."""
        p = principal(request)
        try:
            payload = {"watch_id": watch_id, **(args or {})}
            result, kernel = (ops().invoke_receipted(p, name, payload, held=_ALL_ROWS) if held
                              else ops().invoke_receipted(p, name, payload))
            body = wrap(result) if wrap is not None else result
            return JSONResponse({**body, **kernel_fields(kernel)} if isinstance(body, dict) else body)
        except OperationRefused as exc:
            return JSONResponse({"code": "invalid_arguments", "message": exc.detail, **refusal_fields(exc)},
                                status_code=400)
        except ServiceError as exc:
            return _refused(exc)
        except Exception as exc:
            return error_500(exc, log, f"Failed to {what}")

    # ── GET /api/watches/{watch_id} ──────────────────────────────

    # ── PATCH /api/watches/{watch_id} (admitted: the charter's HTTP capability exceptions) ─

    # ── POST /api/watches/{watch_id}/test ────────────────────────

    # ── POST /api/watches/{watch_id}/baseline (admitted: egress) ─

    # ── POST /api/watches/{watch_id}/pause ───────────────────────

    # ── POST /api/watches/{watch_id}/resume ──────────────────────

    # ── POST /api/watches/{watch_id}/retire ──────────────────────

    # ── PUT /api/watches/{watch_id}/rules ────────────────────────

    return router
