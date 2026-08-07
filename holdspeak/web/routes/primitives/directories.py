"""Directories (zones) + membership edges — thin adapter (HS-122-01)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....services.errors import ConflictError, NotFound, ValidationError
from ....services.primitive_service import PrimitiveService
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body

log = get_logger("web.routes.primitives")


def build_directories_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _svc() -> PrimitiveService:
        from ....db import get_database
        return PrimitiveService(get_database())

    def _principal(request: Request) -> Any:
        return getattr(request.state, "principal", None)

    @router.get("/api/directories")
    async def api_list_directories(request: Request) -> Any:
        try:
            return JSONResponse({"directories": _svc().list_directories(_principal(request))})
        except Exception as exc:
            return error_500(exc, log, "Failed to list directories")

    @router.post("/api/directories")
    async def api_create_directory(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            directory = _svc().create_directory(
                _principal(request),
                directory_id=str(body.get("id") or "") or None,
                name=str(body.get("name") or ""),
                parent_id=body.get("parent_id") or None,
            )
            return JSONResponse({"directory": directory}, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        except ConflictError as exc:
            return JSONResponse(
                {"error": "zone_name_taken", "existing_name": exc.existing_name},
                status_code=409,
            )
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create directory")

    @router.get("/api/directories/{directory_id}")
    async def api_get_directory(directory_id: str, request: Request) -> Any:
        try:
            return JSONResponse(_svc().get_directory(_principal(request), directory_id))
        except NotFound:
            return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to get directory")

    @router.put("/api/directories/{directory_id}")
    async def api_update_directory(directory_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            directory = _svc().update_directory(
                _principal(request),
                directory_id,
                name=body.get("name"),
                parent_id=body.get("parent_id") if "parent_id" in body else ...,
            )
            return JSONResponse({"directory": directory})
        except NotFound:
            return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        except ConflictError as exc:
            return JSONResponse(
                {"error": "zone_name_taken", "existing_name": exc.existing_name},
                status_code=409,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to update directory")

    @router.delete("/api/directories/{directory_id}")
    async def api_delete_directory(directory_id: str, request: Request) -> Any:
        try:
            _svc().delete_directory(_principal(request), directory_id)
            return JSONResponse({"success": True})
        except NotFound:
            return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete directory")

    @router.get("/api/directories/{directory_id}/members")
    async def api_list_directory_members(directory_id: str, request: Request) -> Any:
        try:
            members = _svc().list_directory_members(_principal(request), directory_id)
            return JSONResponse({"directory_id": directory_id, "members": members})
        except NotFound:
            return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to list directory members")

    @router.put("/api/directories/{directory_id}/members/{primitive_id:path}")
    async def api_file_member(directory_id: str, primitive_id: str, request: Request) -> Any:
        try:
            membership = _svc().file_member(_principal(request), directory_id, primitive_id)
            return JSONResponse({"membership": membership})
        except NotFound:
            return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to file directory member")

    @router.delete("/api/directories/{directory_id}/members/{primitive_id:path}")
    async def api_unfile_member(directory_id: str, primitive_id: str, request: Request) -> Any:
        try:
            _svc().unfile_member(_principal(request), directory_id, primitive_id)
            return JSONResponse({"success": True})
        except NotFound:
            return JSONResponse(
                {"error": f"{primitive_id} is not filed in {directory_id}"},
                status_code=404,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to unfile directory member")

    return router
