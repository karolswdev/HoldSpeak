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
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.watches")


def build_watches_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["watches"])

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    # ── GET /api/watches ─────────────────────────────────────────

    @router.get("/api/watches")
    async def list_watches(
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

    @router.get("/api/projects/{project_id}/watches")
    async def list_project_watches(
        project_id: str, request: Request,
        state: str | None = None,
    ) -> Any:
        try:
            watches = ctx.watch_service.list_watches(
                principal(request),
                project_id=project_id,
                state=state,
            )
            return JSONResponse({"watches": watches})
        except Exception as exc:
            return error_500(exc, log, "Failed to list project watches")

    # ── GET /api/watches/{watch_id} ──────────────────────────────

    @router.get("/api/watches/{watch_id}")
    async def get_watch(watch_id: str, request: Request) -> Any:
        try:
            return JSONResponse(
                ctx.watch_service.get_watch(principal(request), watch_id),
            )
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to get watch")

    # ── PATCH /api/watches/{watch_id} ────────────────────────────

    @router.patch("/api/watches/{watch_id}")
    async def update_watch(watch_id: str, request: Request) -> Any:
        try:
            body = await request.json()
            result = ctx.watch_service.update_watch(
                principal(request),
                watch_id,
                name=body.get("name"),
                intent=body.get("intent"),
                subject_kind=body.get("subject_kind"),
                query=body.get("query"),
                trigger_kind=body.get("trigger_kind"),
                trigger=body.get("trigger"),
            )
            return JSONResponse(result)
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ValidationError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to update watch")

    # ── POST /api/watches/{watch_id}/test ────────────────────────

    @router.post("/api/watches/{watch_id}/test")
    async def test_watch(watch_id: str, request: Request) -> Any:
        try:
            return JSONResponse(
                ctx.watch_service.test_watch(principal(request), watch_id),
            )
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ServiceError as exc:
            status = int((exc.context or {}).get("status", 400))
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=status,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to test watch")

    # ── POST /api/watches/{watch_id}/baseline ────────────────────

    @router.post("/api/watches/{watch_id}/baseline")
    async def baseline_watch(watch_id: str, request: Request) -> Any:
        try:
            return JSONResponse(
                ctx.watch_service.baseline_watch(principal(request), watch_id),
            )
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ServiceError as exc:
            status = int((exc.context or {}).get("status", 400))
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=status,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to baseline watch")

    # ── POST /api/watches/{watch_id}/pause ───────────────────────

    @router.post("/api/watches/{watch_id}/pause")
    async def pause_watch(watch_id: str, request: Request) -> Any:
        try:
            return JSONResponse(
                ctx.watch_service.pause_watch(principal(request), watch_id),
            )
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ServiceError as exc:
            status = int((exc.context or {}).get("status", 400))
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=status,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to pause watch")

    # ── POST /api/watches/{watch_id}/resume ──────────────────────

    @router.post("/api/watches/{watch_id}/resume")
    async def resume_watch(watch_id: str, request: Request) -> Any:
        try:
            return JSONResponse(
                ctx.watch_service.resume_watch(principal(request), watch_id),
            )
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ServiceError as exc:
            status = int((exc.context or {}).get("status", 400))
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=status,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to resume watch")

    # ── POST /api/watches/{watch_id}/retire ──────────────────────

    @router.post("/api/watches/{watch_id}/retire")
    async def retire_watch(watch_id: str, request: Request) -> Any:
        try:
            return JSONResponse(
                ctx.watch_service.retire_watch(principal(request), watch_id),
            )
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ServiceError as exc:
            status = int((exc.context or {}).get("status", 400))
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=status,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to retire watch")

    # ── PUT /api/watches/{watch_id}/rules ────────────────────────

    @router.put("/api/watches/{watch_id}/rules")
    async def set_rules(watch_id: str, request: Request) -> Any:
        try:
            body = await request.json()
            rules = body.get("rules", [])
            return JSONResponse(
                ctx.watch_service.set_rules(
                    principal(request), watch_id, rules,
                ),
            )
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ValidationError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail,
                 "errors": (exc.context or {}).get("errors", [])},
                status_code=400,
            )
        except ServiceError as exc:
            status = int((exc.context or {}).get("status", 400))
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=status,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to set watch rules")

    return router
