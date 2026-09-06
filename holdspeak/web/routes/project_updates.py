"""HS-162-04: Project Update routes -- the verb wire.

GET  /api/projects/{id}/updates       -- list (lifecycle-filterable)
POST /api/projects/{id}/updates/draft -- draft (body {generator})
PUT  /api/updates/{id}                -- save the owner's edit (draft only)
POST /api/updates/{id}/regenerate     -- supersede + fresh draft
POST /api/updates/{id}/publish        -- lifecycle publish + project revision law
GET  /api/updates/{id}/markdown       -- the copyable artifact (text/markdown)

Parse-and-serialize ONLY; the service owns logic.
Owner-scoped; typed errors -> correct statuses.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from ...db.updates import PublishedUpdateError
from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import ConflictError, NotFound, ValidationError
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.project_updates")


def _enrich_update(update: dict[str, Any]) -> dict[str, Any]:
    """Add camelCase provenance keys for the face (HS-173-02)."""
    update["generatorHost"] = update.get("generator_host")
    update["generatorModel"] = update.get("generator_model")
    return update


def _request_hash(payload: dict[str, Any]) -> str:
    """Deterministic hash for idempotency (mirrors project_service)."""
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def build_project_updates_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    # ── GET /api/projects/{project_id}/updates ─────────────────────

    @router.get("/api/projects/{project_id}/updates")
    async def api_list_updates(
        project_id: str, request: Request,
        lifecycle: str | None = None,
    ) -> Any:
        try:
            updates = ctx.project_update_service.list_updates(
                principal(request), project_id, lifecycle=lifecycle,
            )
            return JSONResponse({"updates": [_enrich_update(u) for u in updates]})
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to list updates")

    # ── POST /api/projects/{project_id}/updates/draft ──────────────

    @router.post("/api/projects/{project_id}/updates/draft")
    async def api_draft_update(
        project_id: str, payload: dict[str, Any], request: Request,
    ) -> Any:
        try:
            generator = str(payload.get("generator") or "deterministic").strip()
            cmd_id = payload.get("command_id")
            result = ctx.project_update_service.draft_update_command(
                principal(request), project_id,
                generator=generator, command_id=cmd_id,
            )
            return JSONResponse({"success": True, "update": _enrich_update(result)})
        except NotFound as exc:
            return JSONResponse(
                {"success": False, "code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ValidationError as exc:
            return JSONResponse(
                {"success": False, "code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to draft update")

    # ── PUT /api/updates/{update_id} ───────────────────────────────

    @router.put("/api/updates/{update_id}")
    async def api_save_update(
        update_id: str, payload: dict[str, Any], request: Request,
    ) -> Any:
        try:
            body_md = payload.get("body_md")
            cmd_id = payload.get("command_id")
            result = ctx.project_update_service.save_update(
                principal(request), update_id,
                body_md=body_md, command_id=cmd_id,
            )
            return JSONResponse({"success": True, "update": _enrich_update(result)})
        except PublishedUpdateError as exc:
            return JSONResponse(
                {"success": False, "error_code": "published_update",
                 "error": str(exc)},
                status_code=409,
            )
        except NotFound as exc:
            return JSONResponse(
                {"success": False, "code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ValidationError as exc:
            return JSONResponse(
                {"success": False, "code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to save update")

    # ── POST /api/updates/{update_id}/regenerate ───────────────────

    @router.post("/api/updates/{update_id}/regenerate")
    async def api_regenerate_update(
        update_id: str, payload: dict[str, Any], request: Request,
    ) -> Any:
        try:
            generator = str(payload.get("generator") or "deterministic").strip()
            cmd_id = payload.get("command_id")
            result = ctx.project_update_service.regenerate_update(
                principal(request), update_id,
                generator=generator, command_id=cmd_id,
            )
            return JSONResponse({"success": True, "update": _enrich_update(result)})
        except PublishedUpdateError as exc:
            return JSONResponse(
                {"success": False, "error_code": "published_update",
                 "error": str(exc)},
                status_code=409,
            )
        except NotFound as exc:
            return JSONResponse(
                {"success": False, "code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ValidationError as exc:
            return JSONResponse(
                {"success": False, "code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to regenerate update")

    # ── POST /api/updates/{update_id}/publish ──────────────────────

    @router.post("/api/updates/{update_id}/publish")
    async def api_publish_update(
        update_id: str, request: Request,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        try:
            body = payload or {}
            cmd_id = body.get("command_id")
            result = ctx.project_update_service.publish_update(
                principal(request), update_id, command_id=cmd_id,
            )
            return JSONResponse({"success": True, "update": _enrich_update(result)})
        except PublishedUpdateError as exc:
            return JSONResponse(
                {"success": False, "error_code": "published_update",
                 "error": str(exc)},
                status_code=409,
            )
        except NotFound as exc:
            return JSONResponse(
                {"success": False, "code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to publish update")

    # ── GET /api/updates/{update_id}/markdown ──────────────────────

    @router.get("/api/updates/{update_id}/markdown")
    async def api_update_markdown(update_id: str, request: Request) -> Any:
        try:
            update = ctx.project_update_service.get_update(
                principal(request), update_id,
            )
            return PlainTextResponse(
                update.get("body_md", ""),
                media_type="text/markdown",
            )
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to get update markdown")

    return router
