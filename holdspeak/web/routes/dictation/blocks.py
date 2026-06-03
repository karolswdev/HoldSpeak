"""Dictation block-config routes — HS-34-01 split of `dictation.py`.

`/api/dictation/block-templates` and `/api/dictation/blocks*` CRUD (incl.
from-template, which can run a dry-run that writes to the shared suggestion store).
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ._helpers import (
    _STARTER_BLOCK_TEMPLATES,
    _read_blocks_document,
    _resolve_blocks_target,
    _resolve_project_context,
    _run_dictation_dry_run_text,
    _starter_template,
    _unique_block_id,
)

log = get_logger("web.routes.dictation")


def build_blocks_router(
    ctx: WebContext,
    project_doc_suggestions: dict[str, dict[str, str]],
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/dictation/block-templates")
    async def api_dictation_block_templates() -> Any:
        return JSONResponse(
            {
                "templates": [
                    {
                        "id": template["id"],
                        "title": template["title"],
                        "description": template["description"],
                        "sample_utterance": template["sample_utterance"],
                        "requires_project": template["requires_project"],
                        "block": deepcopy(template["block"]),
                    }
                    for template in _STARTER_BLOCK_TEMPLATES
                ]
            }
        )

    @router.get("/api/dictation/blocks")
    async def api_dictation_blocks_list(
        scope: str = "global",
        project_root: Optional[str] = None,
    ) -> Any:
        from ....plugins.dictation.blocks import BlockConfigError, load_blocks_yaml

        try:
            path, project = _resolve_blocks_target(scope, project_root)
        except ValueError as exc:
            status = 404 if "no project detected" in str(exc) else 400
            return JSONResponse({"error": str(exc)}, status_code=status)
        try:
            document, exists = _read_blocks_document(path)
            if exists:
                load_blocks_yaml(path)  # validate, surface errors to UI
        except BlockConfigError as exc:
            return JSONResponse(
                {"error": str(exc), "scope": scope, "path": str(path)},
                status_code=422,
            )
        except Exception as exc:
            log.error(f"Failed to read blocks document: {exc}")
            return JSONResponse({"error": str(exc)}, status_code=500)
        return JSONResponse(
            {
                "scope": scope,
                "path": str(path),
                "exists": exists,
                "project": project,
                "document": document,
            }
        )

    @router.post("/api/dictation/blocks")
    async def api_dictation_blocks_create(
        payload: dict[str, Any],
        scope: str = "global",
        project_root: Optional[str] = None,
    ) -> Any:
        from ....plugins.dictation.blocks import BlockConfigError, save_blocks_yaml

        block = payload.get("block") if isinstance(payload, dict) else None
        if not isinstance(block, dict):
            return JSONResponse(
                {"error": "request body must be {'block': {...}}"},
                status_code=400,
            )
        try:
            path, _project = _resolve_blocks_target(scope, project_root)
        except ValueError as exc:
            status = 404 if "no project detected" in str(exc) else 400
            return JSONResponse({"error": str(exc)}, status_code=status)

        try:
            document, _exists = _read_blocks_document(path)
        except Exception as exc:
            log.error(f"Failed to read blocks document: {exc}")
            return JSONResponse({"error": str(exc)}, status_code=500)

        new_id = block.get("id")
        existing_ids = {b.get("id") for b in document["blocks"] if isinstance(b, dict)}
        if new_id in existing_ids:
            return JSONResponse(
                {"error": f"block id {new_id!r} already exists"},
                status_code=409,
            )
        document["blocks"].append(block)
        try:
            save_blocks_yaml(path, document)
        except BlockConfigError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        if ctx.on_dictation_config_changed is not None:
            try:
                ctx.on_dictation_config_changed()
            except Exception as exc:
                log.error(f"on_dictation_config_changed failed: {exc}")
        return JSONResponse(
            {"scope": scope, "path": str(path), "document": document},
            status_code=201,
        )

    @router.post("/api/dictation/blocks/from-template")
    async def api_dictation_blocks_create_from_template(
        payload: dict[str, Any],
        scope: str = "global",
        project_root: Optional[str] = None,
    ) -> Any:
        from ....plugins.dictation.blocks import BlockConfigError, save_blocks_yaml

        template_id = payload.get("template_id") if isinstance(payload, dict) else None
        if not isinstance(template_id, str) or not template_id.strip():
            return JSONResponse(
                {"error": "request body must include template_id"},
                status_code=400,
            )
        template = _starter_template(template_id.strip())
        if template is None:
            return JSONResponse(
                {"error": f"unknown starter template {template_id!r}"},
                status_code=404,
            )
        run_dry_run = bool(payload.get("dry_run", False))
        if "dry_run" in payload and not isinstance(payload.get("dry_run"), bool):
            return JSONResponse(
                {"error": "dry_run must be a boolean when provided"},
                status_code=400,
            )
        try:
            path, project = _resolve_blocks_target(scope, project_root)
        except ValueError as exc:
            status = 404 if "no project detected" in str(exc) else 400
            return JSONResponse({"error": str(exc)}, status_code=status)
        if run_dry_run and project_root:
            try:
                _resolve_project_context(project_root)
            except ValueError as exc:
                return JSONResponse({"error": str(exc)}, status_code=400)

        requested_block_id = payload.get("block_id") if isinstance(payload, dict) else None
        if requested_block_id is not None and not isinstance(requested_block_id, str):
            return JSONResponse(
                {"error": "block_id must be a string when provided"},
                status_code=400,
            )
        try:
            document, _exists = _read_blocks_document(path)
        except Exception as exc:
            log.error(f"Failed to read blocks document: {exc}")
            return JSONResponse({"error": str(exc)}, status_code=500)

        block = deepcopy(template["block"])
        base_id = (requested_block_id or block["id"]).strip()
        if not base_id:
            return JSONResponse({"error": "block_id cannot be empty"}, status_code=400)
        block["id"] = _unique_block_id(base_id, document)
        document["blocks"].append(block)
        try:
            save_blocks_yaml(path, document)
        except BlockConfigError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        if ctx.on_dictation_config_changed is not None:
            try:
                ctx.on_dictation_config_changed()
            except Exception as exc:
                log.error(f"on_dictation_config_changed failed: {exc}")
        response_payload = {
            "scope": scope,
            "path": str(path),
            "project": project,
            "template": {
                "id": template["id"],
                "title": template["title"],
                "sample_utterance": template["sample_utterance"],
            },
            "block": block,
            "document": document,
        }
        if run_dry_run:
            try:
                dry_run = _run_dictation_dry_run_text(
                    str(template["sample_utterance"]),
                    project_root,
                    suggestions=project_doc_suggestions,
                )
            except ValueError as exc:
                return JSONResponse({"error": str(exc)}, status_code=400)
            except Exception as exc:
                log.error(f"Template dry-run failed: {exc}")
                return JSONResponse({"error": str(exc)}, status_code=500)
            dry_run["created_block_id"] = block["id"]
            dry_run["template_id"] = template["id"]
            dry_run["template_title"] = template["title"]
            dry_run["sample_utterance"] = template["sample_utterance"]
            response_payload["dry_run"] = dry_run
        return JSONResponse(response_payload, status_code=201)

    @router.put("/api/dictation/blocks/{block_id}")
    async def api_dictation_blocks_update(
        block_id: str,
        payload: dict[str, Any],
        scope: str = "global",
        project_root: Optional[str] = None,
    ) -> Any:
        from ....plugins.dictation.blocks import BlockConfigError, save_blocks_yaml

        block = payload.get("block") if isinstance(payload, dict) else None
        if not isinstance(block, dict):
            return JSONResponse(
                {"error": "request body must be {'block': {...}}"},
                status_code=400,
            )
        try:
            path, _project = _resolve_blocks_target(scope, project_root)
        except ValueError as exc:
            status = 404 if "no project detected" in str(exc) else 400
            return JSONResponse({"error": str(exc)}, status_code=status)
        if not path.exists():
            return JSONResponse(
                {"error": f"no blocks file at {path}"},
                status_code=404,
            )
        try:
            document, _exists = _read_blocks_document(path)
        except Exception as exc:
            log.error(f"Failed to read blocks document: {exc}")
            return JSONResponse({"error": str(exc)}, status_code=500)

        blocks = document["blocks"]
        target_idx = next(
            (i for i, b in enumerate(blocks) if isinstance(b, dict) and b.get("id") == block_id),
            None,
        )
        if target_idx is None:
            return JSONResponse(
                {"error": f"unknown block id {block_id!r}"},
                status_code=404,
            )
        new_id = block.get("id", block_id)
        if new_id != block_id and any(
            isinstance(b, dict) and b.get("id") == new_id for b in blocks
        ):
            return JSONResponse(
                {"error": f"block id {new_id!r} already exists"},
                status_code=409,
            )
        blocks[target_idx] = block
        try:
            save_blocks_yaml(path, document)
        except BlockConfigError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        if ctx.on_dictation_config_changed is not None:
            try:
                ctx.on_dictation_config_changed()
            except Exception as exc:
                log.error(f"on_dictation_config_changed failed: {exc}")
        return JSONResponse(
            {"scope": scope, "path": str(path), "document": document}
        )

    @router.delete("/api/dictation/blocks/{block_id}")
    async def api_dictation_blocks_delete(
        block_id: str,
        scope: str = "global",
        project_root: Optional[str] = None,
    ) -> Any:
        from ....plugins.dictation.blocks import BlockConfigError, save_blocks_yaml

        try:
            path, _project = _resolve_blocks_target(scope, project_root)
        except ValueError as exc:
            status = 404 if "no project detected" in str(exc) else 400
            return JSONResponse({"error": str(exc)}, status_code=status)
        if not path.exists():
            return JSONResponse(
                {"error": f"no blocks file at {path}"},
                status_code=404,
            )
        try:
            document, _exists = _read_blocks_document(path)
        except Exception as exc:
            log.error(f"Failed to read blocks document: {exc}")
            return JSONResponse({"error": str(exc)}, status_code=500)
        blocks = document["blocks"]
        kept = [b for b in blocks if not (isinstance(b, dict) and b.get("id") == block_id)]
        if len(kept) == len(blocks):
            return JSONResponse(
                {"error": f"unknown block id {block_id!r}"},
                status_code=404,
            )
        document["blocks"] = kept
        try:
            save_blocks_yaml(path, document)
        except BlockConfigError as exc:
            # save_blocks_yaml requires at least one block; an empty list is
            # rejected by `_build_match`/`blocks` shape rules. Surface the
            # 422 to the caller — they should DELETE-then-recreate or use
            # a "deactivate" toggle (out of scope for v1).
            return JSONResponse({"error": str(exc)}, status_code=422)
        if ctx.on_dictation_config_changed is not None:
            try:
                ctx.on_dictation_config_changed()
            except Exception as exc:
                log.error(f"on_dictation_config_changed failed: {exc}")
        return JSONResponse(
            {"scope": scope, "path": str(path), "document": document}
        )

    return router
