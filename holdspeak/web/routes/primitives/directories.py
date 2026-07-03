"""Directories (zones) + membership edges.

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


def build_directories_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/directories")
    async def api_list_directories() -> Any:
        try:
            from ....db import get_database
            db = get_database()
            directories = db.directories.list()
            out = []
            for d in directories:
                item = d.to_dict()
                members = db.directory_memberships.list_for_directory(d.id)
                item["member_ids"] = [m.primitive_id for m in members]
                out.append(item)
            return JSONResponse({"directories": out})
        except Exception as exc:
            return error_500(exc, log, "Failed to list directories")

    @router.post("/api/directories")
    async def api_create_directory(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if not str(body.get("name") or "").strip():
            return JSONResponse({"error": "directory name is required"}, status_code=400)
        try:
            from ....db import get_database
            directory = get_database().directories.upsert(
                directory_id=str(body.get("id") or _new_id("dir")),
                name=str(body.get("name") or ""),
                parent_id=(body.get("parent_id") or None),
            )
            return JSONResponse({"directory": directory.to_dict()}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create directory")

    @router.get("/api/directories/{directory_id}")
    async def api_get_directory(directory_id: str) -> Any:
        try:
            from ....db import get_database
            db = get_database()
            directory = db.directories.get(directory_id)
            if directory is None:
                return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
            members = db.directory_memberships.list_for_directory(directory_id)
            return JSONResponse({
                "directory": directory.to_dict(),
                "member_ids": [m.primitive_id for m in members],
                "members": [m.to_dict() for m in members],
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to get directory")

    @router.put("/api/directories/{directory_id}")
    async def api_update_directory(directory_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ....db import get_database
            db = get_database()
            existing = db.directories.get(directory_id)
            if existing is None:
                return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
            directory = db.directories.upsert(
                directory_id=directory_id,
                name=str(body["name"]) if "name" in body else existing.name,
                parent_id=(body["parent_id"] or None) if "parent_id" in body else existing.parent_id,
            )
            return JSONResponse({"directory": directory.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to update directory")

    @router.delete("/api/directories/{directory_id}")
    async def api_delete_directory(directory_id: str) -> Any:
        try:
            from ....db import get_database
            removed = get_database().directories.delete(directory_id)
            if not removed:
                return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete directory")

    # ── Directory membership (the synced filing map; supersedes `filed`) ───
    @router.get("/api/directories/{directory_id}/members")
    async def api_list_directory_members(directory_id: str) -> Any:
        try:
            from ....db import get_database
            db = get_database()
            if db.directories.get(directory_id) is None:
                return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
            members = db.directory_memberships.list_for_directory(directory_id)
            return JSONResponse({
                "directory_id": directory_id,
                "members": [m.to_dict() for m in members],
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to list directory members")

    @router.put("/api/directories/{directory_id}/members/{primitive_id}")
    async def api_file_member(directory_id: str, primitive_id: str) -> Any:
        """File a primitive into a directory (idempotent; a re-file moves it).

        Membership is keyed by `primitive_id` (a primitive lives in one
        directory), so PUTting the same primitive elsewhere overwrites the edge.
        """
        try:
            from ....db import get_database
            db = get_database()
            if db.directories.get(directory_id) is None:
                return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
            membership = db.directory_memberships.upsert(
                primitive_id=primitive_id,
                directory_id=directory_id,
            )
            return JSONResponse({"membership": membership.to_dict()})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to file directory member")

    @router.delete("/api/directories/{directory_id}/members/{primitive_id}")
    async def api_unfile_member(directory_id: str, primitive_id: str) -> Any:
        """Unfile a primitive from a directory (tombstone).

        404 if the primitive isn't currently filed into THIS directory.
        """
        try:
            from ....db import get_database
            db = get_database()
            existing = db.directory_memberships.get(primitive_id)
            if existing is None or existing.directory_id != directory_id:
                return JSONResponse(
                    {"error": f"{primitive_id} is not filed in {directory_id}"},
                    status_code=404,
                )
            db.directory_memberships.delete(primitive_id)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to unfile directory member")


    return router
