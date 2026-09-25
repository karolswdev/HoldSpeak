"""Notes CRUD — thin adapter (HS-122-01).

PHILO-7-01: every route is a call to the application-operation contract
(``holdspeak.operations``: note.create / read / update / delete / list), bound
at hub composition to the hub's one live ``PrimitiveService``. Each route maps
its request onto the operation's arguments and maps the result back exactly as
before.
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


def _service_error(exc: Exception) -> JSONResponse:
    if isinstance(exc, ConflictError):
        return JSONResponse({"error": exc.code, **exc.context}, status_code=409)
    if isinstance(exc, ValidationError):
        return JSONResponse({"error": exc.code, **exc.context}, status_code=422)
    raise exc


def build_notes_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _ops() -> operations.OperationRegistry:
        # In the hub: ctx.operations, bound to the ONE composed instance (it
        # carries the ``desk_changed`` hook, HS-200-45). A partially wired
        # context binds the bare service (``operations.for_context``).
        return operations.for_context(ctx, "primitive_service")

    def _principal(request: Request) -> Any:
        return getattr(request.state, "principal", None)

    @router.get("/api/notes")
    async def api_list_notes(request: Request) -> Any:
        try:
            tag = request.query_params.get("tag")
            args = {"tag": tag} if tag is not None else {}
            return JSONResponse({"notes": _ops().invoke(_principal(request), "note.list", args)})
        except Exception as exc:
            return error_500(exc, log, "Failed to list notes")

    @router.post("/api/notes")
    async def api_create_note(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            note = _ops().invoke(_principal(request), "note.create", {
                "note_id": str(body.get("id") or "") or None,
                "title": str(body.get("title") or ""),
                "body_markdown": str(body.get("body_markdown") or ""),
                "tags": list(body.get("tags") or []),
            })
            return JSONResponse({"note": note}, status_code=201)
        except (ConflictError, ValidationError) as exc:
            return _service_error(exc)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create note")

    @router.get("/api/notes/{note_id}")
    async def api_get_note(note_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"note": _ops().invoke(_principal(request), "note.read", {"note_id": note_id})})
        except NotFound:
            return JSONResponse({"error": f"Unknown note: {note_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to get note")

    @router.put("/api/notes/{note_id}")
    async def api_update_note(note_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            note = _ops().invoke(_principal(request), "note.update", {
                "note_id": note_id,
                "title": body.get("title"),
                "body_markdown": body.get("body_markdown"),
                "tags": body.get("tags"),
                "expected_aggregate_revision": body.get("expected_aggregate_revision"),
                "expected_working_revision": body.get("expected_working_revision"),
            })
            return JSONResponse({"note": note})
        except (ConflictError, ValidationError) as exc:
            return _service_error(exc)
        except NotFound:
            return JSONResponse({"error": f"Unknown note: {note_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to update note")

    @router.delete("/api/notes/{note_id}")
    async def api_delete_note(note_id: str, request: Request) -> Any:
        try:
            body = await _json_body(request)
            result, kernel = _ops().invoke_receipted(_principal(request), "note.delete", {
                "note_id": note_id,
                "expected_aggregate_revision": body.get("expected_aggregate_revision") if body else None,
                "expected_lifecycle_revision": body.get("expected_lifecycle_revision") if body else None,
            })
            # PHILO-7-02: a Thought's note delete is ADMITTED (its tombstone
            # unfiles the note); the response carries its receipt.
            payload = {"success": True, "note": result} if isinstance(result, dict) else {"success": True}
            return JSONResponse({**payload, **_kernel_fields(kernel)})
        except (ConflictError, ValidationError) as exc:
            return _service_error(exc)
        except NotFound as exc:
            return JSONResponse({"error": f"Unknown note: {note_id}", **_refusal_kernel(exc)}, status_code=404)
        except ServiceError as exc:
            return JSONResponse({"error": exc.code, "detail": exc.detail, **exc.context},
                                status_code=int(exc.context.get("status") or 409))
        except Exception as exc:
            return error_500(exc, log, "Failed to delete note")

    return router
