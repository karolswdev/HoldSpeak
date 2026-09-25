"""Directories (zones) + membership edges — thin adapter (HS-122-01).

PHILO-7-01: the zone routes are calls to the application-operation contract
(zone.create / read / update / delete / list), bound at hub composition to the
hub's one live ``PrimitiveService``. PHILO-7-02: the membership routes are the
declared zone.file / zone.unfile / zone.members operations; every ADMITTED
write (filing, unfiling, a move, a delete) answers with its ``operation_id``
and terminal kernel ``receipt`` beside the envelope it always had.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .... import operations
from ....logging_config import get_logger
from ....services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body, _kernel_fields, _refusal_kernel

log = get_logger("web.routes.primitives")


def _service_refusal(exc: ServiceError) -> JSONResponse:
    """A named refusal the routes did not map before (PHILO-7-02: a kernel refusal)."""
    return JSONResponse({"error": exc.code, "detail": exc.detail, **exc.context},
                        status_code=int(exc.context.get("status") or 409))


def build_directories_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _ops() -> operations.OperationRegistry:
        # In the hub: ctx.operations, bound to the ONE composed instance (it
        # carries the ``desk_changed`` hook, HS-200-45). A partially wired
        # context binds the bare service (``operations.for_context``).
        return operations.for_context(ctx, "primitive_service")

    def _principal(request: Request) -> Any:
        return getattr(request.state, "principal", None)

    @router.get("/api/directories")
    async def api_list_directories(request: Request) -> Any:
        try:
            return JSONResponse({"directories": _ops().invoke(_principal(request), "zone.list", {})})
        except Exception as exc:
            return error_500(exc, log, "Failed to list directories")

    @router.post("/api/directories")
    async def api_create_directory(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            # PHILO-7-02 class 4: an admitted operation's non-object body leaves a
            # refusal receipt (a conditional one's does not: nothing identifies it).
            kernel = _ops().refuse(_principal(request), "zone.create", "invalid_arguments", None) or {}
            return JSONResponse({"error": "expected a JSON object", **kernel}, status_code=400)
        try:
            directory, kernel = _ops().invoke_receipted(_principal(request), "zone.create", {
                "directory_id": str(body.get("id") or "") or None,
                "name": str(body.get("name") or ""),
                "parent_id": body.get("parent_id") or None,
            })
            return JSONResponse({"directory": directory, **_kernel_fields(kernel)}, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc), **_refusal_kernel(exc)}, status_code=422)
        except ConflictError as exc:
            return JSONResponse(
                {"error": "zone_name_taken", "existing_name": exc.existing_name, **_refusal_kernel(exc)},
                status_code=409,
            )
        except ValueError as exc:
            return JSONResponse({"error": str(exc), **_refusal_kernel(exc)}, status_code=400)
        except ServiceError as exc:
            return _service_refusal(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to create directory")

    @router.get("/api/directories/{directory_id}")
    async def api_get_directory(directory_id: str, request: Request) -> Any:
        try:
            return JSONResponse(_ops().invoke(_principal(request), "zone.read", {"directory_id": directory_id}))
        except NotFound:
            return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to get directory")

    @router.put("/api/directories/{directory_id}")
    async def api_update_directory(directory_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            # PHILO-7-02 class 4: an admitted operation's non-object body leaves a
            # refusal receipt (a conditional one's does not: nothing identifies it).
            kernel = _ops().refuse(_principal(request), "zone.update", "invalid_arguments", None) or {}
            return JSONResponse({"error": "expected a JSON object", **kernel}, status_code=400)
        try:
            args: dict[str, Any] = {"directory_id": directory_id, "name": body.get("name")}
            if "parent_id" in body:
                # Absent is not null: absent keeps the parent, null is the root.
                args["parent_id"] = body.get("parent_id")
            directory, kernel = _ops().invoke_receipted(_principal(request), "zone.update", args)
            return JSONResponse({"directory": directory, **_kernel_fields(kernel)})
        except NotFound as exc:
            return JSONResponse({"error": f"Unknown directory: {directory_id}", **_refusal_kernel(exc)}, status_code=404)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc), **_refusal_kernel(exc)}, status_code=422)
        except ConflictError as exc:
            return JSONResponse(
                {"error": "zone_name_taken", "existing_name": exc.existing_name, **_refusal_kernel(exc)},
                status_code=409,
            )
        except ServiceError as exc:
            return _service_refusal(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to update directory")

    @router.delete("/api/directories/{directory_id}")
    async def api_delete_directory(directory_id: str, request: Request) -> Any:
        try:
            _deleted, kernel = _ops().invoke_receipted(_principal(request), "zone.delete", {"directory_id": directory_id})
            return JSONResponse({"success": True, **_kernel_fields(kernel)})
        except NotFound as exc:
            return JSONResponse({"error": f"Unknown directory: {directory_id}", **_refusal_kernel(exc)}, status_code=404)
        except ServiceError as exc:
            return _service_refusal(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete directory")

    @router.get("/api/directories/{directory_id}/members")
    async def api_list_directory_members(directory_id: str, request: Request) -> Any:
        try:
            members = _ops().invoke(_principal(request), "zone.members", {"directory_id": directory_id})
            return JSONResponse({"directory_id": directory_id, "members": members})
        except NotFound:
            return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to list directory members")

    @router.put("/api/directories/{directory_id}/members/{primitive_id:path}")
    async def api_file_member(directory_id: str, primitive_id: str, request: Request) -> Any:
        try:
            membership, kernel = _ops().invoke_receipted(_principal(request), "zone.file", {
                "directory_id": directory_id, "primitive_id": primitive_id})
            return JSONResponse({"membership": membership, **_kernel_fields(kernel)})
        except NotFound as exc:
            return JSONResponse({"error": f"Unknown directory: {directory_id}", **_refusal_kernel(exc)}, status_code=404)
        except ValueError as exc:
            return JSONResponse({"error": str(exc), **_refusal_kernel(exc)}, status_code=400)
        except ServiceError as exc:
            # Inherited: a named refusal here (thought_tombstoned) still answers
            # 500 as on main (BACKLOG, "PHILO-7-02 round two"); its refusal
            # receipt rides the body now.
            log.error(f"Failed to file directory member: {exc}")
            return JSONResponse({"error": str(exc), **_refusal_kernel(exc)}, status_code=500)
        except Exception as exc:
            return error_500(exc, log, "Failed to file directory member")

    @router.delete("/api/directories/{directory_id}/members/{primitive_id:path}")
    async def api_unfile_member(directory_id: str, primitive_id: str, request: Request) -> Any:
        try:
            _unfiled, kernel = _ops().invoke_receipted(_principal(request), "zone.unfile", {
                "directory_id": directory_id, "primitive_id": primitive_id})
            return JSONResponse({"success": True, **_kernel_fields(kernel)})
        except NotFound as exc:
            return JSONResponse(
                {"error": f"{primitive_id} is not filed in {directory_id}", **_refusal_kernel(exc)},
                status_code=404,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to unfile directory member")

    return router
