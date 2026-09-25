"""Knowledge bases CRUD — thin adapter (HS-122-01).

PHILO-7-01: the knowledge base routes are calls to the application-operation
contract (kb.create / read / update / delete / list), bound at hub composition
to the hub's one live ``PrimitiveService``. The membership routes are not on
the contract yet (PHILO-7-02); they use the SAME instance the contract is bound
to.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .... import operations
from ....logging_config import get_logger
from ....services.errors import NotFound, ValidationError
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body

log = get_logger("web.routes.primitives")


def build_kbs_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _ops() -> operations.OperationRegistry:
        # In the hub: ctx.operations, bound to the ONE composed instance (it
        # carries the ``desk_changed`` hook, HS-200-45). A partially wired
        # context binds the bare service (``operations.for_context``).
        return operations.for_context(ctx, "primitive_service")

    def _svc() -> Any:
        # The instance the contract is bound to (the membership routes, 7-02).
        return _ops().target("kb.read")

    def _principal(request: Request) -> Any:
        return getattr(request.state, "principal", None)

    @router.get("/api/kbs")
    async def api_list_kbs(request: Request) -> Any:
        try:
            return JSONResponse({"kbs": _ops().invoke(_principal(request), "kb.list", {})})
        except Exception as exc:
            return error_500(exc, log, "Failed to list kbs")

    @router.post("/api/kbs")
    async def api_create_kb(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            kb = _ops().invoke(_principal(request), "kb.create", {
                "kb_id": str(body.get("id") or "") or None,
                "name": str(body.get("name") or ""),
                "member_ids": list(body.get("member_ids") or []),
            })
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
            return JSONResponse({"kb": _ops().invoke(_principal(request), "kb.read", {"kb_id": kb_id})})
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
            kb = _ops().invoke(_principal(request), "kb.update", {
                "kb_id": kb_id,
                "name": body.get("name"),
                "member_ids": body.get("member_ids"),
            })
            return JSONResponse({"kb": kb})
        except NotFound:
            return JSONResponse({"error": f"Unknown kb: {kb_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to update kb")

    @router.delete("/api/kbs/{kb_id}")
    async def api_delete_kb(kb_id: str, request: Request) -> Any:
        try:
            _ops().invoke(_principal(request), "kb.delete", {"kb_id": kb_id})
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
