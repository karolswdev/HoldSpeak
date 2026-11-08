"""`.hs` project-context + project-doc-suggestion routes — HS-34-01 split.

`/api/dictation/project-hs` (get/put). The project-doc-suggestion store
is owned by `build_dictation_router` and shared with the dry-run path (pipeline)
and block from-template (blocks), so it is passed in.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ._helpers import (
    _project_hs_payload,
    _resolve_project_context,
    _write_project_hs_files,
)

log = get_logger("web.routes.dictation")


def build_project_docs_router(
    ctx: WebContext,
    project_doc_suggestions: dict[str, dict[str, str]],
    dismissed_signatures: set[str] | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/dictation/project-hs")
    def api_dictation_project_hs_get(project_root: Optional[str] = None) -> Any:
        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400 if project_root else 404)
        return JSONResponse(_project_hs_payload(project))

    @router.put("/api/dictation/project-hs")
    def api_dictation_project_hs_put(
        payload: dict[str, Any],
        project_root: Optional[str] = None,
    ) -> Any:
        files = payload.get("files") if isinstance(payload, dict) else None
        if not isinstance(files, dict):
            return JSONResponse(
                {"error": "request body must be {'files': {<filename>: <content>, ...}}"},
                status_code=400,
            )
        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400 if project_root else 404)
        root = Path(project["root"])
        try:
            _write_project_hs_files(root, files)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        redetected = _resolve_project_context(project_root)
        if ctx.on_dictation_config_changed is not None:
            try:
                ctx.on_dictation_config_changed()
            except Exception as exc:
                log.error(f"on_dictation_config_changed failed: {exc}")
        return JSONResponse(_project_hs_payload(redetected))

    return router
