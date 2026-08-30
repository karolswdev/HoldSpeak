"""Notes CRUD — thin adapter over PrimitiveService (HS-122-01)."""
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


def _service_error(exc: Exception) -> JSONResponse:
    if isinstance(exc, ConflictError):
        return JSONResponse({"error": exc.code, **exc.context}, status_code=409)
    if isinstance(exc, ValidationError):
        return JSONResponse({"error": exc.code, **exc.context}, status_code=422)
    raise exc


def build_notes_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _svc() -> PrimitiveService:
        from ....db import get_database, get_observer
        return PrimitiveService(get_database(), observer=get_observer())

    def _principal(request: Request) -> Any:
        return getattr(request.state, "principal", None)

    @router.get("/api/notes")
    async def api_list_notes(request: Request) -> Any:
        try:
            tag = request.query_params.get("tag")
            if tag is not None:
                return JSONResponse({"notes": _svc().list_notes(_principal(request), tag=tag)})
            return JSONResponse({"notes": _svc().list_notes(_principal(request))})
        except Exception as exc:
            return error_500(exc, log, "Failed to list notes")

    @router.post("/api/notes")
    async def api_create_note(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            note = _svc().create_note(
                _principal(request),
                note_id=str(body.get("id") or "") or None,
                title=str(body.get("title") or ""),
                body_markdown=str(body.get("body_markdown") or ""),
                tags=list(body.get("tags") or []),
            )
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
            return JSONResponse({"note": _svc().get_note(_principal(request), note_id)})
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
            note = _svc().update_note(
                _principal(request),
                note_id,
                title=body.get("title"),
                body_markdown=body.get("body_markdown"),
                tags=body.get("tags"),
                expected_aggregate_revision=body.get("expected_aggregate_revision"),
                expected_working_revision=body.get("expected_working_revision"),
            )
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
            result = _svc().delete_note(
                _principal(request), note_id,
                expected_aggregate_revision=body.get("expected_aggregate_revision") if body else None,
                expected_lifecycle_revision=body.get("expected_lifecycle_revision") if body else None,
            )
            return JSONResponse({"success": True, "note": result} if isinstance(result, dict) else {"success": True})
        except (ConflictError, ValidationError) as exc:
            return _service_error(exc)
        except NotFound:
            return JSONResponse({"error": f"Unknown note: {note_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete note")

    return router
