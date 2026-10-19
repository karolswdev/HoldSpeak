"""Betterment Q9 "Find the tasks": the note's outcome rows (thin adapter).

The service (holdspeak/services/note_outcomes_service.py) runs the meeting's
extraction over one note and makes the confirmed task or proposed decision.
Owner only: Find calls his engine and Confirm writes on his desk, so each is
his press.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....principals import PrincipalKind, UNAUTHENTICATED
from ....services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ...context import WebContext


def _error(exc: ServiceError) -> JSONResponse:
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

    def service() -> Any:
        from ....db import get_database
        from ....services.note_outcomes_service import NoteOutcomesService

        return NoteOutcomesService(get_database(), people_service=ctx.people_service,
                                   door_service=ctx.door_service)

    def owner(request: Request) -> Any:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        return principal if getattr(principal, "kind", None) is PrincipalKind.OWNER else None

    @router.get("/api/notes/{note_id}/outcomes")
    async def read(note_id: str, request: Request) -> Any:
        principal = owner(request)
        if principal is None:
            return JSONResponse({"error": "owner_required"}, status_code=403)
        try:
            return JSONResponse(service().read(principal, note_id))
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/notes/{note_id}/outcomes/find")
    async def find(note_id: str, request: Request) -> Any:
        principal = owner(request)
        if principal is None:
            return JSONResponse({"error": "owner_required"}, status_code=403)
        try:
            return JSONResponse(service().find(principal, note_id))
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/notes/{note_id}/outcomes/{row_id}/confirm")
    async def confirm(note_id: str, row_id: str, request: Request) -> Any:
        principal = owner(request)
        if principal is None:
            return JSONResponse({"error": "owner_required"}, status_code=403)
        try:
            return JSONResponse(service().confirm(principal, note_id, row_id))
        except ServiceError as exc:
            return _error(exc)

    return router
