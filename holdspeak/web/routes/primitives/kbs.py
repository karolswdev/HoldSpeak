"""Knowledge bases CRUD — thin adapter over PrimitiveService (HS-122-01)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....services.primitive_service import NotFound, PrimitiveService, ValidationError
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body

log = get_logger("web.routes.primitives")


def build_kbs_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _svc() -> PrimitiveService:
        from ....db import get_database
        return PrimitiveService(get_database())

    def _principal(request: Request) -> Any:
        return getattr(request.state, "principal", None)

    @router.get("/api/kbs")
    async def api_list_kbs(request: Request) -> Any:
        try:
            return JSONResponse({"kbs": _svc().list_kbs(_principal(request))})
        except Exception as exc:
            return error_500(exc, log, "Failed to list kbs")

    @router.post("/api/kbs")
    async def api_create_kb(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            kb = _svc().create_kb(
                _principal(request),
                kb_id=str(body.get("id") or "") or None,
                name=str(body.get("name") or ""),
                member_ids=list(body.get("member_ids") or []),
            )
            return JSONResponse({"kb": kb}, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create kb")

    @router.get("/api/kbs/{kb_id}")
    async def api_get_kb(kb_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"kb": _svc().get_kb(_principal(request), kb_id)})
        except NotFound:
            return JSONResponse({"error": f"Unknown kb: {kb_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to get kb")

    @router.put("/api/kbs/{kb_id}")
    async def api_update_kb(kb_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            kb = _svc().update_kb(
                _principal(request),
                kb_id,
                name=body.get("name"),
                member_ids=body.get("member_ids"),
            )
            return JSONResponse({"kb": kb})
        except NotFound:
            return JSONResponse({"error": f"Unknown kb: {kb_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to update kb")

    @router.delete("/api/kbs/{kb_id}")
    async def api_delete_kb(kb_id: str, request: Request) -> Any:
        try:
            _svc().delete_kb(_principal(request), kb_id)
            return JSONResponse({"success": True})
        except NotFound:
            return JSONResponse({"error": f"Unknown kb: {kb_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete kb")

    @router.get("/api/kbs/{kb_id}/members")
    async def api_list_kb_members(kb_id: str, request: Request) -> Any:
        try:
            members = _svc().list_kb_members(_principal(request), kb_id)
            return JSONResponse({"members": members})
        except NotFound:
            return JSONResponse({"error": f"Unknown Knowledge: {kb_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to list Knowledge members")

    @router.put("/api/kbs/{kb_id}/members/{resource_ref:path}")
    async def api_add_kb_member(kb_id: str, resource_ref: str, request: Request) -> Any:
        try:
            member = _svc().add_kb_member(_principal(request), kb_id, resource_ref)
            return JSONResponse({"member": member})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to add Knowledge member")

    @router.delete("/api/kbs/{kb_id}/members/{resource_ref:path}")
    async def api_remove_kb_member(kb_id: str, resource_ref: str, request: Request) -> Any:
        try:
            removed = _svc().remove_kb_member(_principal(request), kb_id, resource_ref)
            return JSONResponse({"success": True, "removed": removed})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to remove Knowledge member")

    return router
