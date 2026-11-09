"""PARKED 20261108 (evening, the unreached-routes census): routes no client calls.

Parked from ``holdspeak/web/routes/dictation/kb.py``: DELETE /api/dictation/project-kb.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""Project-KB routes (`/api/dictation/project-kb*`) — HS-34-01 split."""


from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ._helpers import _STARTER_PROJECT_KB, _resolve_project_context

log = get_logger("web.routes.dictation")




def parked_build_kb_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.delete("/api/dictation/project-kb")
    def api_dictation_project_kb_delete(project_root: Optional[str] = None) -> Any:
        from ....plugins.dictation.project_kb import delete_project_kb

        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            return JSONResponse(
                {"error": str(exc)},
                status_code=400 if project_root else 404,
            )
        root = Path(project["root"])
        removed = delete_project_kb(root)
        if not removed:
            return JSONResponse(
                {"error": f"no project.yaml at {root / '.holdspeak' / 'project.yaml'}"},
                status_code=404,
            )
        if ctx.on_dictation_config_changed is not None:
            try:
                ctx.on_dictation_config_changed()
            except Exception as exc:
                log.error(f"on_dictation_config_changed failed: {exc}")
        return JSONResponse({"detected": dict(project), "kb": None, "kb_path": None})

    return router
