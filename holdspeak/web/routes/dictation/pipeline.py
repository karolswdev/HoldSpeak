"""Dictation readiness + dry-run routes — HS-34-01 split of `dictation.py`.

`/api/dictation/readiness` and `/api/dictation/dry-run`. The dry-run path writes
detected project-doc suggestions into the shared store owned by
`build_dictation_router`, so it is passed in.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ._helpers import (
    _block_summary,
    _resolve_blocks_target,
    _resolve_project_context,
    _run_dictation_dry_run_text,
    _runtime_readiness,
)

log = get_logger("web.routes.dictation")


def build_pipeline_router(
    ctx: WebContext,
    project_doc_suggestions: dict[str, dict[str, str]],
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/dictation/readiness")
    async def api_dictation_readiness(project_root: Optional[str] = None) -> Any:
        """Return one browser-facing readiness snapshot for dictation setup."""
        from ....agent_context import get_recent_agent_session
        from ....config import Config
        from ....plugins.dictation.project_kb import ProjectKBError, kb_path_for, read_project_kb
        from ....target_profile import detect_active_target_profile, detect_target_profile_with_override

        cfg = Config.load().dictation
        warnings: list[dict[str, Any]] = []

        project: Optional[dict[str, Any]]
        project_error: Optional[str] = None
        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            if project_root:
                return JSONResponse({"error": str(exc)}, status_code=400)
            project = None
            project_error = str(exc)

        global_path, _ = _resolve_blocks_target("global")
        global_blocks = _block_summary(global_path)

        project_blocks: Optional[dict[str, Any]] = None
        project_root_path: Optional[Path] = None
        if project is not None:
            project_root_path = Path(project["root"])
            project_blocks = _block_summary(project_root_path / ".holdspeak" / "blocks.yaml")

        resolved_blocks = (
            project_blocks
            if project_blocks is not None and project_blocks["exists"]
            else global_blocks
        )
        resolved_scope = (
            "project"
            if project_blocks is not None and project_blocks["exists"]
            else "global"
        )

        kb_payload: dict[str, Any] = {
            "path": None,
            "exists": False,
            "valid": True,
            "keys": [],
            "error": None,
        }
        if project_root_path is not None:
            kb_path = kb_path_for(project_root_path)
            kb_payload["path"] = str(kb_path)
            kb_payload["exists"] = kb_path.exists()
            try:
                kb = read_project_kb(project_root_path)
                kb_payload["keys"] = sorted((kb or {}).keys())
            except ProjectKBError as exc:
                kb_payload["valid"] = False
                kb_payload["error"] = str(exc)

        runtime_payload = _runtime_readiness(cfg)
        try:
            target_payload = detect_active_target_profile(
                cfg.pipeline.target_profile_override
            ).to_dict()
        except Exception:
            target_payload = detect_target_profile_with_override(
                {},
                cfg.pipeline.target_profile_override,
            ).to_dict()
        agent_hooks_payload: dict[str, Any] = {}
        for agent in ("claude", "codex"):
            latest = get_recent_agent_session(agent=agent, max_age_seconds=7 * 24 * 60 * 60)
            agent_hooks_payload[agent] = {
                "fresh": latest is not None,
                "latest_session": latest.to_dict() if latest else None,
            }

        if not cfg.pipeline.enabled:
            warnings.append({
                "code": "pipeline_disabled",
                "message": "Dictation pipeline is disabled.",
                "action": "Enable the dictation pipeline from Runtime.",
                "section": "runtime",
                "runtime_action": "enable_pipeline",
            })
        if project is None:
            warnings.append({
                "code": "no_project",
                "message": project_error or "No project root detected.",
                "action": "Set a project root override or launch holdspeak from a project directory.",
                "section": "readiness",
            })
        if not resolved_blocks["exists"] or int(resolved_blocks["count"]) == 0:
            warnings.append({
                "code": "no_blocks",
                "message": "No dictation blocks are loaded for the selected project.",
                "action": "Create the Action item starter and run its sample.",
                "section": "blocks",
                "template_id": "action_item",
                "template_action": "create_dry_run",
                "template_scope": "project" if project is not None else "global",
            })
        if not global_blocks["valid"] or (project_blocks is not None and not project_blocks["valid"]):
            warnings.append({
                "code": "invalid_blocks",
                "message": "A blocks.yaml file is invalid.",
                "action": "Open Blocks and fix the validation error.",
                "section": "blocks",
            })
        if project is not None and not kb_payload["exists"]:
            warnings.append({
                "code": "missing_project_kb",
                "message": "Project KB file is missing.",
                "action": "Create a starter Project KB file.",
                "section": "kb",
                "kb_action": "create_starter",
            })
        if not kb_payload["valid"]:
            warnings.append({
                "code": "invalid_project_kb",
                "message": "Project KB file is invalid.",
                "action": "Open Project KB and fix the validation error.",
                "section": "kb",
            })
        if runtime_payload["status"] == "unavailable":
            warnings.append({
                "code": "runtime_unavailable",
                "message": runtime_payload["detail"],
                "action": "Install the selected runtime extra or change backend.",
                "section": "runtime",
                "guidance": runtime_payload.get("guidance"),
            })
        elif runtime_payload["status"] == "missing_model":
            warnings.append({
                "code": "runtime_model_missing",
                "message": runtime_payload["detail"],
                "action": "Download the model or update the runtime model path.",
                "section": "runtime",
                "guidance": runtime_payload.get("guidance"),
            })

        ready = (
            cfg.pipeline.enabled
            and project is not None
            and bool(resolved_blocks["valid"])
            and int(resolved_blocks["count"]) > 0
            and bool(kb_payload["valid"])
            and runtime_payload["status"] == "available"
        )

        return JSONResponse(
            {
                "ready": ready,
                "project": project,
                "config": {
                    "pipeline_enabled": cfg.pipeline.enabled,
                    "max_total_latency_ms": cfg.pipeline.max_total_latency_ms,
                    "backend": cfg.runtime.backend,
                },
                "blocks": {
                    "global": global_blocks,
                    "project": project_blocks,
                    "resolved_scope": resolved_scope,
                    "resolved": resolved_blocks,
                },
                "project_kb": kb_payload,
                "runtime": runtime_payload,
                "telemetry": runtime_payload.get("telemetry"),
                "target": target_payload,
                "agent_hooks": agent_hooks_payload,
                "warnings": warnings,
            }
        )

    @router.post("/api/dictation/dry-run")
    async def api_dictation_dry_run(payload: dict[str, Any]) -> Any:
        utterance = payload.get("utterance") if isinstance(payload, dict) else None
        if not isinstance(utterance, str):
            return JSONResponse(
                {
                    "error": "utterance must be a string",
                    "detail": {"utterance": "required string"},
                },
                status_code=400,
            )
        text = utterance.strip()
        if not text:
            return JSONResponse(
                {
                    "error": "utterance must not be empty",
                    "detail": {"utterance": "must not be empty"},
                },
                status_code=400,
            )
        project_root_override = payload.get("project_root") if isinstance(payload, dict) else None
        if project_root_override is not None and not isinstance(project_root_override, str):
            return JSONResponse(
                {
                    "error": "project_root must be a string when provided",
                    "detail": {"project_root": "optional string path"},
                },
                status_code=400,
            )
        target_hints = payload.get("target") if isinstance(payload, dict) else None
        if target_hints is not None and not isinstance(target_hints, dict):
            return JSONResponse(
                {
                    "error": "target must be an object when provided",
                    "detail": {"target": "optional object of app/window/process hints"},
                },
                status_code=400,
            )

        try:
            return JSONResponse(
                _run_dictation_dry_run_text(
                    text,
                    project_root_override,
                    target_hints,
                    suggestions=project_doc_suggestions,
                    corrections=ctx.corrections,
                )
            )
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            log.error(f"Dictation dry-run failed: {exc}")
            return JSONResponse({"error": str(exc)}, status_code=500)

    @router.get("/api/dictation/corrections")
    async def api_dictation_corrections_list() -> Any:
        from ....config import Config
        from ....plugins.dictation.corrections import CORRECTION_KINDS

        store = ctx.corrections
        cfg = Config.load().dictation
        return JSONResponse(
            {
                "enabled": bool(getattr(cfg.pipeline, "corrections_enabled", False)),
                "kinds": list(CORRECTION_KINDS),
                "size": len(store) if store is not None else 0,
                "items": [c.to_dict() for c in store.recent()] if store is not None else [],
            }
        )

    @router.post("/api/dictation/corrections")
    async def api_dictation_corrections_record(payload: dict[str, Any]) -> Any:
        from ....plugins.dictation.corrections import CORRECTION_KINDS

        store = ctx.corrections
        if store is None:
            return JSONResponse({"error": "correction store unavailable"}, status_code=503)
        kind = payload.get("kind") if isinstance(payload, dict) else None
        text = payload.get("text") if isinstance(payload, dict) else None
        value = payload.get("value") if isinstance(payload, dict) else None
        if kind not in CORRECTION_KINDS:
            return JSONResponse(
                {"error": f"kind must be one of {list(CORRECTION_KINDS)}"}, status_code=400
            )
        if not isinstance(text, str) or not text.strip():
            return JSONResponse({"error": "text must be a non-empty string"}, status_code=400)
        if not isinstance(value, str) or not value.strip():
            return JSONResponse({"error": "value must be a non-empty string"}, status_code=400)
        recorded = store.record(kind, text, value)
        return JSONResponse({"recorded": bool(recorded), "size": len(store)})

    return router
