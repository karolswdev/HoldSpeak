"""Project-KB routes (`/api/dictation/project-kb*`) — HS-34-01 split."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ._helpers import _STARTER_PROJECT_KB, _resolve_project_context

log = get_logger("web.routes.dictation")


def build_kb_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/dictation/project-kb")
    async def api_dictation_project_kb_get(project_root: Optional[str] = None) -> Any:
        from ....plugins.dictation.project_kb import ProjectKBError, read_project_kb

        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            if project_root:
                return JSONResponse({"error": str(exc)}, status_code=400)
            return JSONResponse({
                "detected": None,
                "kb": None,
                "kb_path": None,
                "message": f"no project root detected from cwd={Path.cwd()}",
            })
        root = Path(project["root"])
        try:
            kb = read_project_kb(root)
        except ProjectKBError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        return JSONResponse({
            "detected": dict(project),
            "kb": kb,
            "kb_path": str(root / ".holdspeak" / "project.yaml"),
        })

    @router.put("/api/dictation/project-kb")
    async def api_dictation_project_kb_put(
        payload: dict[str, Any],
        project_root: Optional[str] = None,
    ) -> Any:
        from ....plugins.dictation.project_kb import (
            ProjectKBError,
            kb_path_for,
            read_project_kb,
            write_project_kb,
        )

        kb = payload.get("kb") if isinstance(payload, dict) else None
        if not isinstance(kb, dict):
            return JSONResponse(
                {"error": "request body must be {'kb': {<key>: <value>, ...}}"},
                status_code=400,
            )
        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            return JSONResponse(
                {"error": str(exc)},
                status_code=400 if project_root else 404,
            )
        root = Path(project["root"])
        try:
            write_project_kb(root, kb)
        except ProjectKBError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        if ctx.on_dictation_config_changed is not None:
            try:
                ctx.on_dictation_config_changed()
            except Exception as exc:
                log.error(f"on_dictation_config_changed failed: {exc}")
        try:
            fresh_kb = read_project_kb(root)
        except ProjectKBError as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)
        # Re-detect so the caller sees the upgraded anchor signal
        # when this PUT just created `<root>/.holdspeak/`.
        redetected = _resolve_project_context(project_root) if project_root else project
        return JSONResponse({
            "detected": dict(redetected),
            "kb": fresh_kb,
            "kb_path": str(kb_path_for(root)),
        })

    @router.post("/api/dictation/project-kb/starter")
    async def api_dictation_project_kb_starter(project_root: Optional[str] = None) -> Any:
        from ....plugins.dictation.project_kb import (
            ProjectKBError,
            kb_path_for,
            read_project_kb,
            write_project_kb,
        )

        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            return JSONResponse(
                {"error": str(exc)},
                status_code=400 if project_root else 404,
            )
        root = Path(project["root"])
        path = kb_path_for(root)
        if path.exists():
            return JSONResponse(
                {"error": f"project KB already exists at {path}"},
                status_code=409,
            )
        try:
            write_project_kb(root, _STARTER_PROJECT_KB)
        except ProjectKBError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        if ctx.on_dictation_config_changed is not None:
            try:
                ctx.on_dictation_config_changed()
            except Exception as exc:
                log.error(f"on_dictation_config_changed failed: {exc}")
        try:
            fresh_kb = read_project_kb(root)
        except ProjectKBError as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)
        redetected = _resolve_project_context(project_root) if project_root else project
        return JSONResponse(
            {
                "detected": dict(redetected),
                "kb": fresh_kb,
                "kb_path": str(path),
                "starter": True,
            },
            status_code=201,
        )

    @router.delete("/api/dictation/project-kb")
    async def api_dictation_project_kb_delete(project_root: Optional[str] = None) -> Any:
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
