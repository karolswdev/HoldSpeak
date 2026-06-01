"""Dictation / agent-hook / intent-control routes (HS-26-03).

The dictation pipeline cluster moved off `MeetingWebServer._create_app`: intent
controls (`/api/intents/*`), agent-context + agent-hook routes, the `.hs` /
project-doc-suggestion routes, block-config CRUD, project-KB routes, and the
dry-run endpoint. Handlers + their private helpers move verbatim; only the
closure target changes (`self.` -> `ctx.`) and the package-relative imports gain
one dot (this module sits one package deeper than `web_server`).

The global blocks path comes from the canonical
`plugins.dictation.assembly.DEFAULT_GLOBAL_BLOCKS_PATH` — the same constant the
dictation CLI + doctor read — imported lazily inside the helpers so tests that
`monkeypatch.setattr(assembly, "DEFAULT_GLOBAL_BLOCKS_PATH", ...)` still apply.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...web_requests import (
    _IntentOverrideRequest,
    _IntentPreviewRequest,
    _IntentProfileRequest,
)
from ..context import WebContext

log = get_logger("web.routes.dictation")


def build_dictation_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/intents/control")
    async def api_get_intent_controls() -> Any:
        if ctx.on_get_intent_controls is None:
            return JSONResponse(
                {
                    "enabled": False,
                    "profile": "balanced",
                    "available_profiles": [],
                    "supported_intents": [],
                    "override_intents": [],
                }
            )
        try:
            payload = ctx.on_get_intent_controls()
        except Exception as e:
            log.error(f"on_get_intent_controls failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)
        return JSONResponse(payload if isinstance(payload, dict) else {"controls": payload})

    @router.put("/api/intents/profile")
    async def api_set_intent_profile(payload: _IntentProfileRequest) -> Any:
        if ctx.on_set_intent_profile is None:
            return JSONResponse(
                {"success": False, "error": "Intent profile updates not supported"},
                status_code=501,
            )
        try:
            result = ctx.on_set_intent_profile(payload.profile)
        except Exception as e:
            log.error(f"on_set_intent_profile failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        if isinstance(result, dict):
            ctx.broadcast("intent_controls_updated", result)
        return JSONResponse({"success": True, "controls": result})

    @router.put("/api/intents/override")
    async def api_set_intent_override(payload: _IntentOverrideRequest) -> Any:
        if ctx.on_set_intent_override is None:
            return JSONResponse(
                {"success": False, "error": "Intent override updates not supported"},
                status_code=501,
            )
        try:
            result = ctx.on_set_intent_override(payload.intents)
        except Exception as e:
            log.error(f"on_set_intent_override failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        if isinstance(result, dict):
            ctx.broadcast("intent_controls_updated", result)
        return JSONResponse({"success": True, "controls": result})

    @router.post("/api/intents/preview")
    async def api_preview_intent_route(payload: Optional[_IntentPreviewRequest] = None) -> Any:
        if ctx.on_route_preview is None:
            return JSONResponse(
                {"success": False, "error": "Intent route preview not supported"},
                status_code=501,
            )
        try:
            result = ctx.on_route_preview(
                profile=payload.profile if payload is not None else None,
                threshold=payload.threshold if payload is not None else None,
                intent_scores=payload.intent_scores if payload is not None else None,
                override_intents=payload.override_intents if payload is not None else None,
                previous_intents=payload.previous_intents if payload is not None else None,
                tags=payload.tags if payload is not None else None,
                transcript=payload.transcript if payload is not None else None,
            )
        except Exception as e:
            log.error(f"on_route_preview failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)
        return JSONResponse({"success": True, "route": result})

    # ── Dictation block-config endpoints (WFS-CFG-001 + WFS-CFG-002) ──

    def _resolve_project_context(project_root: Optional[str] = None) -> dict[str, Any]:
        """Return detected/manual project context for dictation project APIs."""
        from ...plugins.dictation.project_root import detect_project_for_cwd

        if project_root is None or not str(project_root).strip():
            project = detect_project_for_cwd()
            if project is None:
                raise ValueError("no project detected for current working directory")
            return dict(project)

        root = Path(str(project_root)).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError(f"project_root must be an existing directory: {root}")

        project = detect_project_for_cwd(root)
        if project is not None:
            return dict(project)
        return {"name": root.name, "root": str(root), "anchor": "manual"}

    def _resolve_blocks_target(
        scope: str,
        project_root: Optional[str] = None,
    ) -> tuple[Path, Optional[dict[str, Any]]]:
        """Return `(path, project_ctx)` for the requested scope.

        Raises `ValueError` with a user-facing message on bad input.
        """
        from ...plugins.dictation.assembly import DEFAULT_GLOBAL_BLOCKS_PATH

        if scope == "global":
            return DEFAULT_GLOBAL_BLOCKS_PATH, None
        if scope == "project":
            project = _resolve_project_context(project_root)
            return Path(project["root"]) / ".holdspeak" / "blocks.yaml", dict(project)
        raise ValueError(f"scope must be 'global' or 'project', got {scope!r}")

    @router.get("/api/dictation/project-context")
    async def api_dictation_project_context(project_root: Optional[str] = None) -> Any:
        """Validate and describe the active/manual dictation project root."""
        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400 if project_root else 404)
        root = Path(project["root"])
        return JSONResponse(
            {
                "project": project,
                "paths": {
                    "blocks": str(root / ".holdspeak" / "blocks.yaml"),
                    "project_kb": str(root / ".holdspeak" / "project.yaml"),
                },
            }
        )

    @router.get("/api/dictation/agent-context")
    async def api_dictation_agent_context(project_root: Optional[str] = None) -> Any:
        """Return the latest captured agent question for the selected project."""
        from ...agent_context import get_recent_awaiting_agent_session

        project: dict[str, Any] | None = None
        project_error: str | None = None
        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            if project_root:
                return JSONResponse({"error": str(exc)}, status_code=400)
            project_error = str(exc)

        session = (
            get_recent_awaiting_agent_session(project_root=project["root"], max_age_seconds=120)
            if project
            else None
        )
        return JSONResponse(
            {
                "project": project,
                "project_error": project_error,
                "session": session.to_dict() if session else None,
                "awaiting_response": bool(session and session.awaiting_response),
                "max_age_seconds": 120,
            }
        )

    @router.get("/api/dictation/agent-hooks")
    async def api_dictation_agent_hooks(capture_messages: bool = True) -> Any:
        """Return copy-ready Claude/Codex hook templates and recent status."""
        from ...agent_context import (
            AGENT_CONTEXT_FILE,
            claude_hook_template,
            codex_hook_template,
            get_recent_agent_session,
        )
        from ...agent_summarizer import summarizer_provider_statuses

        templates = {
            "claude": claude_hook_template(capture_messages=capture_messages),
            "codex": codex_hook_template(capture_messages=capture_messages),
        }
        agents: dict[str, dict[str, Any]] = {}
        for agent, template in templates.items():
            latest = get_recent_agent_session(agent=agent, max_age_seconds=7 * 24 * 60 * 60)
            agents[agent] = {
                "latest_session": latest.to_dict() if latest else None,
                "template": template,
                "template_json": json.dumps(template, indent=2, sort_keys=True),
            }
        return JSONResponse(
            {
                "capture_messages": capture_messages,
                "registry_path": str(AGENT_CONTEXT_FILE),
                "destinations": {
                    "claude": "~/.claude/settings.json or project .claude/settings.json",
                    "codex": "~/.codex/hooks.json or project .codex/hooks.json",
                },
                "summarizers": summarizer_provider_statuses(),
                "agents": agents,
            }
        )

    @router.post("/api/dictation/agent-context/clear")
    async def api_dictation_agent_context_clear(
        payload: Optional[dict[str, Any]] = None,
        project_root: Optional[str] = None,
    ) -> Any:
        """Clear the captured assistant text shown by the Dictation page."""
        from ...agent_context import clear_agent_session_response

        body = payload if isinstance(payload, dict) else {}
        body_project_root = body.get("project_root")
        effective_project_root = project_root or (body_project_root if isinstance(body_project_root, str) else None)
        try:
            project = _resolve_project_context(effective_project_root)
        except ValueError as exc:
            if effective_project_root:
                return JSONResponse({"error": str(exc)}, status_code=400)
            project = None

        session = clear_agent_session_response(
            agent=body.get("agent") if isinstance(body.get("agent"), str) else None,
            session_id=body.get("session_id") if isinstance(body.get("session_id"), str) else None,
            project_root=project["root"] if project else None,
            max_age_seconds=120,
        )
        return JSONResponse(
            {
                "cleared": session is not None,
                "session": session.to_dict() if session else None,
            }
        )

    @router.post("/api/dictation/agent-context/summarize")
    async def api_dictation_agent_context_summarize(
        payload: Optional[dict[str, Any]] = None,
        project_root: Optional[str] = None,
    ) -> Any:
        """Generate and persist a bounded external-agent context summary."""
        from ...agent_context import (
            get_recent_awaiting_agent_session,
            set_agent_session_summary,
        )
        from ...agent_summarizer import summarize_agent_session

        body = payload if isinstance(payload, dict) else {}
        provider = str(body.get("provider") or "").strip().lower()
        if provider not in {"codex", "claude"}:
            return JSONResponse(
                {"error": "provider must be one of: codex, claude"},
                status_code=400,
            )
        body_project_root = body.get("project_root")
        effective_project_root = project_root or (body_project_root if isinstance(body_project_root, str) else None)
        try:
            project = _resolve_project_context(effective_project_root)
        except ValueError as exc:
            if effective_project_root:
                return JSONResponse({"error": str(exc)}, status_code=400)
            project = None

        session = get_recent_awaiting_agent_session(
            project_root=project["root"] if project else None,
            agent=body.get("agent") if isinstance(body.get("agent"), str) else None,
            max_age_seconds=120,
        )
        if session is None:
            return JSONResponse(
                {"error": "no recent captured agent message is awaiting a response"},
                status_code=404,
            )
        try:
            summary = summarize_agent_session(
                session,
                provider=provider,  # type: ignore[arg-type]
                timeout_seconds=float(body.get("timeout_seconds") or 20.0),
            )
        except FileNotFoundError as exc:
            return JSONResponse({"error": str(exc)}, status_code=404)
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=502)

        updated = set_agent_session_summary(
            agent=session.agent,
            session_id=session.session_id,
            summary=summary.to_dict(),
        )
        return JSONResponse(
            {
                "summary": summary.to_dict(),
                "session": updated.to_dict() if updated else None,
            }
        )

    project_doc_suggestions: dict[str, dict[str, str]] = {}

    def _project_suggestion_key(project: dict[str, Any]) -> str:
        return str(Path(project["root"]).resolve())

    def _extract_project_doc_suggestion(stages: list[dict[str, Any]]) -> dict[str, str] | None:
        from ...project_doc_suggestions import validate_project_doc_suggestion_payload

        for stage in stages:
            metadata = stage.get("metadata") if isinstance(stage, dict) else None
            raw = metadata.get("project_doc_suggestion") if isinstance(metadata, dict) else None
            if not isinstance(raw, dict):
                continue
            try:
                return validate_project_doc_suggestion_payload(
                    target_path=str(raw.get("target_path") or ""),
                    rationale=str(raw.get("rationale") or ""),
                    content=str(raw.get("content") or ""),
                ).to_dict()
            except ValueError:
                continue
        return None

    def _store_project_doc_suggestion(
        project: dict[str, Any] | None,
        stages: list[dict[str, Any]],
    ) -> None:
        if not project:
            return
        suggestion = _extract_project_doc_suggestion(stages)
        if suggestion is not None:
            project_doc_suggestions[_project_suggestion_key(project)] = suggestion
        else:
            project_doc_suggestions.pop(_project_suggestion_key(project), None)

    def _validate_project_doc_suggestion_body(payload: dict[str, Any]) -> Any:
        from ...project_doc_suggestions import validate_project_doc_suggestion_payload

        raw = payload.get("suggestion") if isinstance(payload.get("suggestion"), dict) else payload
        if not isinstance(raw, dict):
            raise ValueError("request body must include a suggestion object")
        return validate_project_doc_suggestion_payload(
            target_path=str(raw.get("target_path") or ""),
            rationale=str(raw.get("rationale") or ""),
            content=str(raw.get("content") or ""),
        )

    def _write_project_doc_suggestion(root: Path, suggestion: Any) -> Path:
        target = (root / suggestion.target_path).resolve()
        resolved_root = root.resolve()
        if resolved_root not in target.parents:
            raise ValueError("target_path must stay inside the project root")
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(suggestion.content, encoding="utf-8")
        os.replace(tmp, target)
        return target

    def _project_hs_payload(project: dict[str, Any]) -> dict[str, Any]:
        from ...agent_context import (
            DEFAULT_CONTEXT_HARD_FILE_MAX_BYTES,
            HS_CONTEXT_FILES,
            load_hs_project_context,
        )

        root = Path(project["root"])
        hs_dir = root / ".hs"
        loaded = load_hs_project_context(
            root,
            max_bytes=DEFAULT_CONTEXT_HARD_FILE_MAX_BYTES * 8,
            per_file_max_bytes=DEFAULT_CONTEXT_HARD_FILE_MAX_BYTES,
        )
        loaded_files = loaded.get("files") if isinstance(loaded.get("files"), dict) else {}
        files: dict[str, dict[str, Any]] = {}
        for name in (*HS_CONTEXT_FILES, "ignore"):
            path = hs_dir / name
            loaded_entry = loaded_files.get(name) if isinstance(loaded_files, dict) else None
            entry = loaded_entry if isinstance(loaded_entry, dict) else {}
            files[name] = {
                "path": str(path),
                "exists": path.is_file(),
                "actual_path": str(entry.get("path") or path),
                "content": str(entry.get("content") or ""),
                "source": str(entry.get("source") or "directory"),
                "read_only": bool(entry.get("read_only")),
                "truncated": bool(entry.get("truncated")),
            }
        return {
            "detected": dict(project),
            "context_dir": str(hs_dir),
            "exists": bool(loaded.get("exists")),
            "context_dir_exists": hs_dir.is_dir(),
            "files": files,
            "flat_files": loaded.get("flat_files") if isinstance(loaded.get("flat_files"), dict) else {},
            "skipped": loaded.get("skipped") if isinstance(loaded.get("skipped"), list) else [],
            "warnings": loaded.get("warnings") if isinstance(loaded.get("warnings"), list) else [],
            "write_policy": loaded.get("write_policy") if isinstance(loaded.get("write_policy"), dict) else {},
        }

    def _write_project_hs_files(root: Path, files: dict[str, Any]) -> None:
        from ...agent_context import HS_CONTEXT_FILES

        allowed = set(HS_CONTEXT_FILES) | {"ignore"}
        unknown = sorted(set(files) - allowed)
        if unknown:
            raise ValueError(f"unknown .hs file(s): {unknown}; allowed: {sorted(allowed)}")
        hs_dir = root / ".hs"
        hs_dir.mkdir(parents=True, exist_ok=True)
        for name, raw_content in files.items():
            if not isinstance(raw_content, str):
                raise ValueError(f".hs/{name} content must be a string")
            if len(raw_content.encode("utf-8")) > 128_000:
                raise ValueError(f".hs/{name} is too large; max is 128KB")
            path = hs_dir / name
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(raw_content, encoding="utf-8")
            os.replace(tmp, path)

    @router.get("/api/dictation/project-hs")
    async def api_dictation_project_hs_get(project_root: Optional[str] = None) -> Any:
        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400 if project_root else 404)
        return JSONResponse(_project_hs_payload(project))

    @router.put("/api/dictation/project-hs")
    async def api_dictation_project_hs_put(
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

    @router.get("/api/dictation/project-doc-suggestion")
    async def api_dictation_project_doc_suggestion_get(
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
    async def api_dictation_project_doc_suggestion_apply(
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
    async def api_dictation_project_doc_suggestion_dismiss(
        project_root: Optional[str] = None,
    ) -> Any:
        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400 if project_root else 404)
        removed = project_doc_suggestions.pop(_project_suggestion_key(project), None)
        return JSONResponse(
            {
                "detected": dict(project),
                "dismissed": removed is not None,
                "suggestion": None,
            }
        )

    def _read_blocks_document(path: Path) -> tuple[dict[str, Any], bool]:
        """Read `path` as a raw YAML mapping; return empty default if missing."""
        import yaml

        if not path.exists():
            return {"version": 1, "default_match_confidence": 0.6, "blocks": []}, False
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        if data is None:
            return {"version": 1, "default_match_confidence": 0.6, "blocks": []}, True
        if not isinstance(data, dict):
            raise ValueError(
                f"{path}: top-level YAML must be a mapping, got {type(data).__name__}"
            )
        data.setdefault("version", 1)
        data.setdefault("default_match_confidence", 0.6)
        data.setdefault("blocks", [])
        return data, True

    _STARTER_BLOCK_TEMPLATES: tuple[dict[str, Any], ...] = (
        {
            "id": "ai_prompt_context",
            "title": "AI prompt context",
            "description": "Append the selected project name and clear instruction context to AI-assistant prompts.",
            "sample_utterance": "help me design the settings panel",
            "requires_project": True,
            "block": {
                "id": "ai_prompt_context",
                "description": "User is dictating a prompt for an AI assistant and wants project context attached.",
                "match": {
                    "examples": [
                        "Claude help me write a function for this project",
                        "build a prompt for the settings panel",
                        "ask the assistant to debug this module",
                    ],
                    "negative_examples": ["remind me to buy milk"],
                    "threshold": 0.7,
                },
                "inject": {
                    "mode": "append",
                    "template": "\n\nProject: {project.name}\nUse the selected project's constraints and local context when answering.",
                },
            },
        },
        {
            "id": "action_item",
            "title": "Action item",
            "description": "Turn short task dictation into a consistent action-item line.",
            "sample_utterance": "follow up with Sam about the launch checklist",
            "requires_project": False,
            "block": {
                "id": "action_item",
                "description": "User is capturing a task or follow-up item.",
                "match": {
                    "examples": [
                        "follow up with Sam about the launch checklist",
                        "remember to review the pull request",
                        "make a task to update the docs",
                    ],
                    "negative_examples": ["write a paragraph about the architecture"],
                    "threshold": 0.7,
                },
                "inject": {
                    "mode": "replace",
                    "template": "Action item: {raw_text}",
                },
            },
        },
        {
            "id": "concise_note",
            "title": "Concise note",
            "description": "Format quick thoughts as a clean note that is easy to scan later.",
            "sample_utterance": "the retry worker should surface its next scheduled run",
            "requires_project": False,
            "block": {
                "id": "concise_note",
                "description": "User is dictating a concise note or implementation observation.",
                "match": {
                    "examples": [
                        "note that the retry worker needs a status line",
                        "capture this implementation idea",
                        "write down this design concern",
                    ],
                    "negative_examples": ["send an email to Alex"],
                    "threshold": 0.7,
                },
                "inject": {
                    "mode": "replace",
                    "template": "Note: {raw_text}",
                },
            },
        },
        {
            "id": "code_review_focus",
            "title": "Code review focus",
            "description": "Append a review rubric for correctness, edge cases, and tests.",
            "sample_utterance": "review the queue processing change",
            "requires_project": False,
            "block": {
                "id": "code_review_focus",
                "description": "User is dictating a code-review request.",
                "match": {
                    "examples": [
                        "review the queue processing change",
                        "look over this implementation for bugs",
                        "check this diff for edge cases",
                    ],
                    "negative_examples": ["start a meeting recording"],
                    "threshold": 0.7,
                },
                "inject": {
                    "mode": "append",
                    "template": "\n\nReview focus: correctness, edge cases, regressions, and missing tests.",
                },
            },
        },
    )
    _STARTER_PROJECT_KB: dict[str, Any] = {
        "stack": None,
        "task_focus": None,
        "constraints": None,
    }

    def _starter_template(template_id: str) -> Optional[dict[str, Any]]:
        for template in _STARTER_BLOCK_TEMPLATES:
            if template["id"] == template_id:
                return deepcopy(template)
        return None

    def _serialize_intent(intent: Any) -> Optional[dict[str, Any]]:
        if intent is None:
            return None
        return {
            "matched": bool(getattr(intent, "matched", False)),
            "block_id": getattr(intent, "block_id", None),
            "confidence": float(getattr(intent, "confidence", 0.0)),
            "raw_label": getattr(intent, "raw_label", None),
            "extras": dict(getattr(intent, "extras", {}) or {}),
        }

    def _serialize_stage_result(result: Any) -> dict[str, Any]:
        from ...dictation_telemetry import summarize_stage

        payload = {
            "stage_id": str(getattr(result, "stage_id", "")),
            "elapsed_ms": float(getattr(result, "elapsed_ms", 0.0)),
            "intent": _serialize_intent(getattr(result, "intent", None)),
            "warnings": list(getattr(result, "warnings", []) or []),
            "metadata": dict(getattr(result, "metadata", {}) or {}),
            "text": str(getattr(result, "text", "")),
        }
        payload["telemetry"] = summarize_stage(payload)
        return payload

    def _run_dictation_dry_run_text(
        text: str,
        project_root_override: Optional[str],
        target_hints: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Execute the browser dry-run path for already-validated text."""
        from ...config import Config
        from ...dictation_telemetry import summarize_dry_run
        from ...plugins.dictation.assembly import DEFAULT_GLOBAL_BLOCKS_PATH, build_pipeline
        from ...plugins.dictation.contracts import Utterance
        from ...target_profile import collect_active_target_hints, detect_target_profile_with_override

        cfg = Config.load().dictation
        try:
            project = _resolve_project_context(project_root_override)
        except ValueError:
            if project_root_override:
                raise
            project = None
        project_root = Path(project["root"]) if project else None

        if not cfg.pipeline.enabled:
            warnings = ["dictation pipeline disabled"]
            return {
                "project": dict(project) if project else None,
                "runtime_status": "disabled",
                "runtime_detail": "dictation pipeline disabled (opt-in)",
                "blocks_count": 0,
                "stages": [],
                "final_text": text,
                "total_elapsed_ms": 0.0,
                "warnings": warnings,
                "telemetry": summarize_dry_run(
                    runtime_status="disabled",
                    runtime_detail="dictation pipeline disabled (opt-in)",
                    stages=[],
                    warnings=warnings,
                    total_elapsed_ms=0.0,
                    max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
                ),
            }

        result = build_pipeline(
            cfg,
            project_root=project_root,
            global_blocks_path=DEFAULT_GLOBAL_BLOCKS_PATH,
        )
        target_profile = detect_target_profile_with_override(
            target_hints or collect_active_target_hints(),
            cfg.pipeline.target_profile_override,
        )
        run = result.pipeline.run(
            Utterance(
                raw_text=text,
                audio_duration_s=0.0,
                transcribed_at=datetime.now(),
                project=project,
                activity={"target": target_profile.to_dict()},
            )
        )
        stages = [_serialize_stage_result(sr) for sr in run.stage_results]
        _store_project_doc_suggestion(project, stages)
        warnings = list(run.warnings)
        return {
            "project": dict(project) if project else None,
            "target": target_profile.to_dict(),
            "runtime_status": result.runtime_status,
            "runtime_detail": result.runtime_detail,
            "blocks_count": len(result.blocks.blocks),
            "stages": stages,
            "final_text": run.final_text,
            "total_elapsed_ms": float(run.total_elapsed_ms),
            "warnings": warnings,
            "telemetry": summarize_dry_run(
                runtime_status=result.runtime_status,
                runtime_detail=result.runtime_detail,
                stages=stages,
                warnings=warnings,
                total_elapsed_ms=float(run.total_elapsed_ms),
                max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
            ),
        }

    def _unique_block_id(base_id: str, document: dict[str, Any]) -> str:
        existing = {
            b.get("id")
            for b in document.get("blocks", [])
            if isinstance(b, dict)
        }
        if base_id not in existing:
            return base_id
        index = 2
        while f"{base_id}_{index}" in existing:
            index += 1
        return f"{base_id}_{index}"

    def _block_summary(path: Path) -> dict[str, Any]:
        from ...plugins.dictation.blocks import BlockConfigError, load_blocks_yaml

        if not path.exists():
            return {
                "path": str(path),
                "exists": False,
                "valid": True,
                "count": 0,
                "error": None,
            }
        try:
            loaded = load_blocks_yaml(path)
        except BlockConfigError as exc:
            return {
                "path": str(path),
                "exists": True,
                "valid": False,
                "count": 0,
                "error": str(exc),
            }
        return {
            "path": str(path),
            "exists": True,
            "valid": True,
            "count": len(loaded.blocks),
            "error": None,
        }

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

    def _runtime_readiness(cfg: Any) -> dict[str, Any]:
        from ...dictation_telemetry import summarize_readiness_telemetry
        from ...plugins.dictation import runtime as runtime_module
        from ...plugins.dictation.runtime_counters import get_counters, get_session_status

        if not cfg.pipeline.enabled:
            payload = {
                "status": "disabled",
                "requested_backend": cfg.runtime.backend,
                "resolved_backend": None,
                "detail": "dictation pipeline disabled",
                "model_path": None,
                "model_exists": False,
                "counters": get_counters(),
                "session": get_session_status(),
            }
            payload["telemetry"] = summarize_readiness_telemetry(
                runtime_payload=payload,
                max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
            )
            return payload

        try:
            resolved_backend, reason = runtime_module.resolve_backend(cfg.runtime.backend)
        except runtime_module.RuntimeUnavailableError as exc:
            from ...plugins.dictation.guidance import runtime_guidance

            payload = {
                "status": "unavailable",
                "requested_backend": cfg.runtime.backend,
                "resolved_backend": None,
                "detail": str(exc),
                "model_path": None,
                "model_exists": False,
                "guidance": runtime_guidance(
                    kind="unavailable",
                    requested_backend=cfg.runtime.backend,
                ),
                "counters": get_counters(),
                "session": get_session_status(),
            }
            payload["telemetry"] = summarize_readiness_telemetry(
                runtime_payload=payload,
                max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
            )
            return payload

        if resolved_backend == "openai_compatible":
            from ...plugins.dictation.guidance import runtime_guidance

            payload = {
                "status": "available",
                "requested_backend": cfg.runtime.backend,
                "resolved_backend": resolved_backend,
                "detail": (
                    f"endpoint={cfg.runtime.openai_compatible_base_url}; "
                    f"model={cfg.runtime.openai_compatible_model}"
                ),
                "model_path": None,
                "model_exists": True,
                "guidance": runtime_guidance(
                    kind="endpoint_config",
                    requested_backend=cfg.runtime.backend,
                    resolved_backend=resolved_backend,
                ),
                "counters": get_counters(),
                "session": get_session_status(),
            }
            payload["telemetry"] = summarize_readiness_telemetry(
                runtime_payload=payload,
                max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
            )
            return payload

        model_path = Path(
            cfg.runtime.mlx_model
            if resolved_backend == "mlx"
            else cfg.runtime.llama_cpp_model_path
        ).expanduser()
        model_exists = model_path.exists()
        guidance = None
        if not model_exists:
            from ...plugins.dictation.guidance import runtime_guidance

            guidance = runtime_guidance(
                kind="missing_model",
                requested_backend=cfg.runtime.backend,
                resolved_backend=resolved_backend,
                model_path=model_path,
            )
        payload = {
            "status": "available" if model_exists else "missing_model",
            "requested_backend": cfg.runtime.backend,
            "resolved_backend": resolved_backend,
            "detail": reason if model_exists else f"model file missing at {model_path}",
            "model_path": str(model_path),
            "model_exists": model_exists,
            "guidance": guidance,
            "counters": get_counters(),
            "session": get_session_status(),
        }
        payload["telemetry"] = summarize_readiness_telemetry(
            runtime_payload=payload,
            max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
        )
        return payload

    @router.get("/api/dictation/readiness")
    async def api_dictation_readiness(project_root: Optional[str] = None) -> Any:
        """Return one browser-facing readiness snapshot for dictation setup."""
        from ...agent_context import get_recent_agent_session
        from ...config import Config
        from ...plugins.dictation.project_kb import ProjectKBError, kb_path_for, read_project_kb
        from ...target_profile import detect_active_target_profile, detect_target_profile_with_override

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

    @router.get("/api/dictation/blocks")
    async def api_dictation_blocks_list(
        scope: str = "global",
        project_root: Optional[str] = None,
    ) -> Any:
        from ...plugins.dictation.blocks import BlockConfigError, load_blocks_yaml

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
        from ...plugins.dictation.blocks import BlockConfigError, save_blocks_yaml

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
        from ...plugins.dictation.blocks import BlockConfigError, save_blocks_yaml

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
        from ...plugins.dictation.blocks import BlockConfigError, save_blocks_yaml

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
        from ...plugins.dictation.blocks import BlockConfigError, save_blocks_yaml

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

    # ── Project KB endpoints (WFS-CFG-003) ─────────────────────────────

    @router.get("/api/dictation/project-kb")
    async def api_dictation_project_kb_get(project_root: Optional[str] = None) -> Any:
        from ...plugins.dictation.project_kb import ProjectKBError, read_project_kb

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
        from ...plugins.dictation.project_kb import (
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
        from ...plugins.dictation.project_kb import (
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
        from ...plugins.dictation.project_kb import delete_project_kb

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

    # ── Dictation dry-run endpoint (WFS-CFG-005) ───────────────────────

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
            return JSONResponse(_run_dictation_dry_run_text(text, project_root_override, target_hints))
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            log.error(f"Dictation dry-run failed: {exc}")
            return JSONResponse({"error": str(exc)}, status_code=500)

    return router
