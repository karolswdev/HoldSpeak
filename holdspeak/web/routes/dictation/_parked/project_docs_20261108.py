"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/dictation/project_docs.py``: GET /api/dictation/project-doc-suggestion, POST /api/dictation/project-doc-suggestion/apply, POST /api/dictation/project-doc-suggestion/dismiss.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""`.hs` project-context + project-doc-suggestion routes — HS-34-01 split.

`/api/dictation/project-hs` (get/put) and
`/api/dictation/project-doc-suggestion` (get/apply/dismiss). The suggestion store
is owned by `build_dictation_router` and shared with the dry-run path (pipeline)
and block from-template (blocks), so it is passed in.
"""


from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .....logging_config import get_logger
from ....context import WebContext
from .._helpers import (
    _project_suggestion_key,
    _resolve_project_context,
    _validate_project_doc_suggestion_body,
    _write_project_doc_suggestion,
)

log = get_logger("web.routes.dictation")


def parked_build_project_docs_router(
    ctx: WebContext,
    project_doc_suggestions: dict[str, dict[str, str]],
    dismissed_signatures: set[str] | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/dictation/project-doc-suggestion")
    def api_dictation_project_doc_suggestion_get(
        project_root: Optional[str] = None,
    ) -> Any:
        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400 if project_root else 404)
        return JSONResponse(
            {
                "detected": dict(project),
                "suggestion": project_doc_suggestions.get(_project_suggestion_key(project)),
            }
        )

    @router.post("/api/dictation/project-doc-suggestion/apply")
    def api_dictation_project_doc_suggestion_apply(
        payload: dict[str, Any],
        project_root: Optional[str] = None,
    ) -> Any:
        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400 if project_root else 404)
        try:
            suggestion = _validate_project_doc_suggestion_body(payload if isinstance(payload, dict) else {})
            target = _write_project_doc_suggestion(Path(project["root"]), suggestion)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        project_doc_suggestions.pop(_project_suggestion_key(project), None)
        if ctx.on_dictation_config_changed is not None:
            try:
                ctx.on_dictation_config_changed()
            except Exception as exc:
                log.error(f"on_dictation_config_changed failed: {exc}")
        return JSONResponse(
            {
                "detected": dict(project),
                "applied": True,
                "path": str(target),
                "suggestion": suggestion.to_dict(),
            }
        )

    @router.post("/api/dictation/project-doc-suggestion/dismiss")
    def api_dictation_project_doc_suggestion_dismiss(
        project_root: Optional[str] = None,
    ) -> Any:
        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400 if project_root else 404)
        removed = project_doc_suggestions.pop(_project_suggestion_key(project), None)
        # HS-39-04: remember the dismissal so a near-duplicate doesn't recur.
        if removed is not None and dismissed_signatures is not None:
            from .....project_doc_suggestions import suggestion_signature

            dismissed_signatures.add(
                suggestion_signature(
                    str(removed.get("target_path") or ""),
                    str(removed.get("content") or ""),
                )
            )
        return JSONResponse(
            {
                "detected": dict(project),
                "dismissed": removed is not None,
                "suggestion": None,
            }
        )

    return router
