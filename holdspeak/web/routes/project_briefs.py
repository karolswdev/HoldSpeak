"""HS-200-11: the preparation brief routes -- the verb wire.

GET  /api/projects/{id}/briefs/route    -- the route the model drafter would use (no dispatch)
GET  /api/projects/{id}/briefs/manifest -- the manifest a prepare would bind now (no write)
POST /api/projects/{id}/briefs/prepare  -- prepare (body {purpose, generator?, attempt_id?})
POST /api/projects/{id}/briefs/stop     -- stop an attempt (body {attempt_id}); no orphan draft
GET  /api/projects/{id}/briefs          -- list (lifecycle-filterable; discarded hidden)
GET  /api/briefs/{id}                   -- one brief, manifest integrity re-verified
POST /api/briefs/{id}/keep              -- the lifecycle flip
POST /api/briefs/{id}/discard           -- a state, never a DELETE

Parse-and-serialize ONLY; the service owns logic.  A refused preparation is a
409 carrying the bounded route state AND the purpose, so the face keeps the
owner's words and draws the repair (AC5).
"""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ...services.preparation_brief_service import PreparationRefused
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.project_briefs")


def build_project_briefs_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def service() -> Any:
        svc = ctx.project_brief_service
        if svc is None:
            raise RuntimeError("project_brief_service is not configured")
        return svc

    def refused(exc: ServiceError, status: int) -> JSONResponse:
        body: dict[str, Any] = dict(exc.context)
        body.pop("status", None)
        body.setdefault("error", exc.detail)
        body.setdefault("error_code", exc.code)
        return JSONResponse(body, status_code=status)

    @router.get("/api/projects/{project_id}/briefs/route")
    async def api_brief_route(project_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"route": service().route(principal(request), project_id)})
        except NotFound as exc:
            return refused(exc, 404)
        except Exception as exc:
            return error_500(exc, log, "Failed to read the brief route")

    @router.get("/api/projects/{project_id}/briefs/manifest")
    async def api_brief_manifest(project_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"manifest": service().preview_manifest(principal(request), project_id)})
        except NotFound as exc:
            return refused(exc, 404)
        except Exception as exc:
            return error_500(exc, log, "Failed to preview the brief manifest")

    @router.post("/api/projects/{project_id}/briefs/prepare")
    async def api_prepare_brief(project_id: str, payload: dict[str, Any], request: Request) -> Any:
        """The run leaves the event loop (a model call is seconds), so the
        stop route can land while it is out -- and the route itself watches
        for the client leaving: a Stop that aborted the fetch cancels the
        kernel operation and the completing run writes no draft (P1-4)."""
        attempt_id = str(payload.get("attempt_id") or "").strip()
        who = principal(request)
        svc = service()

        def _run() -> dict[str, Any]:
            return svc.prepare(
                who, project_id,
                str(payload.get("purpose") or ""),
                generator=str(payload.get("generator") or "model"),
                attempt_id=attempt_id,
            )

        try:
            task = asyncio.ensure_future(asyncio.to_thread(_run))
            while not task.done():
                await asyncio.wait({task}, timeout=0.25)
                if task.done():
                    break
                if attempt_id:
                    try:
                        gone = await request.is_disconnected()
                    except Exception:
                        gone = False
                    if gone:
                        svc.stop(attempt_id)
            brief = task.result()
            return JSONResponse({"success": True, "brief": brief})
        except PreparationRefused as exc:
            return refused(exc, 409)
        except NotFound as exc:
            return refused(exc, 404)
        except ValidationError as exc:
            return refused(exc, 422)
        except Exception as exc:
            return error_500(exc, log, "Failed to prepare the brief")

    @router.post("/api/projects/{project_id}/briefs/stop")
    async def api_stop_brief(project_id: str, payload: dict[str, Any], request: Request) -> Any:
        del project_id
        try:
            return JSONResponse(service().stop(str(payload.get("attempt_id") or "")))
        except ValidationError as exc:
            return refused(exc, 422)
        except Exception as exc:
            return error_500(exc, log, "Failed to stop the brief")

    @router.get("/api/projects/{project_id}/briefs")
    async def api_list_briefs(
        project_id: str, request: Request, lifecycle: str | None = None, limit: int = 20,
    ) -> Any:
        try:
            briefs = service().list_briefs(
                principal(request), project_id, lifecycle=lifecycle, limit=limit,
            )
            return JSONResponse({"briefs": briefs})
        except NotFound as exc:
            return refused(exc, 404)
        except Exception as exc:
            return error_500(exc, log, "Failed to list briefs")

    @router.get("/api/briefs/{brief_id}")
    async def api_get_brief(brief_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"brief": service().get_brief(principal(request), brief_id)})
        except NotFound as exc:
            return refused(exc, 404)
        except Exception as exc:
            return error_500(exc, log, "Failed to read the brief")

    @router.post("/api/briefs/{brief_id}/keep")
    async def api_keep_brief(brief_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"success": True, "brief": service().keep(principal(request), brief_id)})
        except NotFound as exc:
            return refused(exc, 404)
        except ConflictError as exc:
            return refused(exc, 409)
        except Exception as exc:
            return error_500(exc, log, "Failed to keep the brief")

    @router.post("/api/briefs/{brief_id}/discard")
    async def api_discard_brief(brief_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"success": True, "brief": service().discard(principal(request), brief_id)})
        except NotFound as exc:
            return refused(exc, 404)
        except ConflictError as exc:
            return refused(exc, 409)
        except Exception as exc:
            return error_500(exc, log, "Failed to discard the brief")

    return router
