"""Betterment Q9 "Find the tasks": the note's outcome rows (thin adapter).

Every route is a call to the application-operation contract
(``holdspeak.operations``: note.outcomes.read / find, note.outcome.edit /
dismiss / confirm), bound at hub composition to the hub's one
``NoteOutcomesService``; the MCP tools reach the same operations. Owner only
over HTTP: Find calls his engine and Confirm writes on his desk, so each is his
press on the face.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .... import operations
from ....principals import PrincipalKind, UNAUTHENTICATED
from ....services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ...context import WebContext
from ._shared import _json_body


def _error(exc: Exception) -> JSONResponse:
    if isinstance(exc, operations.OperationRefused):
        return JSONResponse({"error": exc.code, "message": str(exc)}, status_code=422)
    assert isinstance(exc, ServiceError)
    body = {"error": exc.code, "message": exc.detail}
    if isinstance(exc, NotFound):
        return JSONResponse(body, status_code=404)
    if isinstance(exc, ConflictError):
        return JSONResponse(body, status_code=409)
    status = exc.context.get("status") if isinstance(exc.context, dict) else None
    fallback = 422 if isinstance(exc, ValidationError) else 400
    return JSONResponse(body, status_code=int(status) if isinstance(status, int) else fallback)


def build_note_outcomes_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _ops() -> operations.OperationRegistry:
        # The hub's one registry, bound to its one NoteOutcomesService.
        return operations.for_context(ctx)

    def owner(request: Request) -> Any:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        return principal if getattr(principal, "kind", None) is PrincipalKind.OWNER else None

    def call(request: Request, name: str, args: dict[str, Any]) -> JSONResponse:
        principal = owner(request)
        if principal is None:
            return JSONResponse({"error": "owner_required"}, status_code=403)
        try:
            return JSONResponse(_ops().invoke(principal, name, args))
        except (ServiceError, operations.OperationRefused) as exc:
            return _error(exc)

    @router.get("/api/notes/{note_id}/outcomes")
    async def read(note_id: str, request: Request) -> Any:
        return call(request, "note.outcomes.read", {"note_id": note_id})

    @router.post("/api/notes/{note_id}/outcomes/find")
    def find(note_id: str, request: Request) -> Any:
        # A plain def: the engine call runs off the event loop (blocking_io).
        return call(request, "note.find_tasks", {"note_id": note_id})

    @router.post("/api/notes/{note_id}/outcomes/{row_id}/edit")
    async def edit(note_id: str, row_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        fields = {key: body[key] for key in ("text", "owner_name", "due") if isinstance(body.get(key), str)}
        if set(body) - {"text", "owner_name", "due"}:
            return JSONResponse({"error": "invalid_arguments", "message": "only text, owner_name and due change"},
                                status_code=422)
        return call(request, "note.outcome.edit", {"note_id": note_id, "row_id": row_id, **fields})

    @router.post("/api/notes/{note_id}/outcomes/{row_id}/dismiss")
    async def dismiss(note_id: str, row_id: str, request: Request) -> Any:
        return call(request, "note.outcome.dismiss", {"note_id": note_id, "row_id": row_id})

    @router.post("/api/notes/{note_id}/outcomes/{row_id}/confirm")
    async def confirm(note_id: str, row_id: str, request: Request) -> Any:
        return call(request, "note.outcome.confirm", {"note_id": note_id, "row_id": row_id})

    return router
