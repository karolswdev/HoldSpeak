"""Notes CRUD.

Bodies moved verbatim from routes/primitives.py (HS-79-03, the Phase-63 discipline).
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.primitives")
from ._shared import _json_body, _new_id


def build_notes_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/notes")
    async def api_list_notes() -> Any:
        try:
            from ....db import get_database
            notes = get_database().notes.list()
            return JSONResponse({"notes": [n.to_dict() for n in notes]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list notes")

    @router.post("/api/notes")
    async def api_create_note(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ....db import get_database
            note = get_database().notes.upsert(
                note_id=str(body.get("id") or _new_id("note")),
                title=str(body.get("title") or ""),
                body_markdown=str(body.get("body_markdown") or ""),
                tags=list(body.get("tags") or []),
            )
            return JSONResponse({"note": note.to_dict()}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create note")

    @router.get("/api/notes/{note_id}")
    async def api_get_note(note_id: str) -> Any:
        try:
            from ....db import get_database
            note = get_database().notes.get(note_id)
            if note is None:
                return JSONResponse({"error": f"Unknown note: {note_id}"}, status_code=404)
            return JSONResponse({"note": note.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to get note")

    @router.put("/api/notes/{note_id}")
    async def api_update_note(note_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ....db import get_database
            db = get_database()
            existing = db.notes.get(note_id)
            if existing is None:
                return JSONResponse({"error": f"Unknown note: {note_id}"}, status_code=404)
            note = db.notes.upsert(
                note_id=note_id,
                title=str(body["title"]) if "title" in body else existing.title,
                body_markdown=str(body["body_markdown"]) if "body_markdown" in body else existing.body_markdown,
                tags=list(body["tags"]) if "tags" in body else existing.tags,
            )
            return JSONResponse({"note": note.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to update note")

    @router.delete("/api/notes/{note_id}")
    async def api_delete_note(note_id: str) -> Any:
        try:
            from ....db import get_database
            removed = get_database().notes.delete(note_id)
            if not removed:
                return JSONResponse({"error": f"Unknown note: {note_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete note")

    # ── Agents (personas) ────────────────────────────────────────────────

    return router
