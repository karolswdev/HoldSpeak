"""Knowledge bases CRUD.

Bodies moved verbatim from routes/primitives.py (HS-79-03, the Phase-63 discipline).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body, _new_id

log = get_logger("web.routes.primitives")


def build_kbs_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/kbs")
    async def api_list_kbs() -> Any:
        try:
            from ....db import get_database
            kbs = get_database().kbs.list()
            return JSONResponse({"kbs": [k.to_dict() for k in kbs]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list kbs")

    @router.post("/api/kbs")
    async def api_create_kb(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if not str(body.get("name") or "").strip():
            return JSONResponse({"error": "kb name is required"}, status_code=400)
        try:
            from ....db import get_database
            kb = get_database().kbs.upsert(
                kb_id=str(body.get("id") or _new_id("kb")),
                name=str(body.get("name") or ""),
                member_ids=list(body.get("member_ids") or []),
            )
            return JSONResponse({"kb": kb.to_dict()}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create kb")

    @router.get("/api/kbs/{kb_id}")
    async def api_get_kb(kb_id: str) -> Any:
        try:
            from ....db import get_database
            kb = get_database().kbs.get(kb_id)
            if kb is None:
                return JSONResponse({"error": f"Unknown kb: {kb_id}"}, status_code=404)
            return JSONResponse({"kb": kb.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to get kb")

    @router.put("/api/kbs/{kb_id}")
    async def api_update_kb(kb_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ....db import get_database
            db = get_database()
            existing = db.kbs.get(kb_id)
            if existing is None:
                return JSONResponse({"error": f"Unknown kb: {kb_id}"}, status_code=404)
            kb = db.kbs.upsert(
                kb_id=kb_id,
                name=str(body["name"]) if "name" in body else existing.name,
                member_ids=list(body["member_ids"]) if "member_ids" in body else existing.member_ids,
            )
            return JSONResponse({"kb": kb.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to update kb")

    @router.delete("/api/kbs/{kb_id}")
    async def api_delete_kb(kb_id: str) -> Any:
        try:
            from ....db import get_database
            removed = get_database().kbs.delete(kb_id)
            if not removed:
                return JSONResponse({"error": f"Unknown kb: {kb_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete kb")

    @router.get("/api/kbs/{kb_id}/members")
    async def api_list_kb_members(kb_id: str) -> Any:
        try:
            from ....db import get_database
            db = get_database()
            if db.kbs.get(kb_id) is None:
                return JSONResponse({"error": f"Unknown Knowledge: {kb_id}"}, status_code=404)
            members = db.knowledge_memberships.list_for_knowledge(kb_id)
            return JSONResponse({"members": [member.to_dict() for member in members]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list Knowledge members")

    @router.put("/api/kbs/{kb_id}/members/{resource_ref:path}")
    async def api_add_kb_member(kb_id: str, resource_ref: str) -> Any:
        try:
            from ....db import get_database
            member = get_database().knowledge_memberships.upsert(
                knowledge_id=kb_id, resource_ref=resource_ref
            )
            return JSONResponse({"member": member.to_dict()})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to add Knowledge member")

    @router.delete("/api/kbs/{kb_id}/members/{resource_ref:path}")
    async def api_remove_kb_member(kb_id: str, resource_ref: str) -> Any:
        try:
            from ....db import get_database
            removed = get_database().knowledge_memberships.delete(kb_id, resource_ref)
            return JSONResponse({"success": True, "removed": removed})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to remove Knowledge member")

    # ── Chains (crews) ────────────────────────────────────────────────────

    return router
