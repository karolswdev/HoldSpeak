"""Shared, ctx-free helpers for the dictation route sub-package (HS-34-01).

These are the private helpers that several dictation route groups share —
project-context resolution, blocks-document IO, the dry-run executor, the starter
templates, and the project-doc-suggestion plumbing. They were inline closures in
the original 1,607-line `dictation.py`; the split moves them here verbatim, with
two signature tweaks so the shared in-memory suggestion store is passed
explicitly (it used to be a closure variable):
`_store_project_doc_suggestion(..., suggestions)` and
`_run_dictation_dry_run_text(..., suggestions)`.

Imports gained one relative dot — these modules sit one package deeper than the
old `web/routes/dictation.py`.
"""

from __future__ import annotations

import os
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def _resolve_project_context(project_root: Optional[str] = None) -> dict[str, Any]:
    """Return detected/manual project context for dictation project APIs."""
    from ....plugins.dictation.project_root import detect_project_for_cwd

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
    from ....plugins.dictation.assembly import DEFAULT_GLOBAL_BLOCKS_PATH

    if scope == "global":
        return DEFAULT_GLOBAL_BLOCKS_PATH, None
    if scope == "project":
        project = _resolve_project_context(project_root)
        return Path(project["root"]) / ".holdspeak" / "blocks.yaml", dict(project)
    raise ValueError(f"scope must be 'global' or 'project', got {scope!r}")


# ── project-doc-suggestion helpers (operate on a caller-owned store) ──────


def _project_suggestion_key(project: dict[str, Any]) -> str:
    return str(Path(project["root"]).resolve())


def _extract_project_doc_suggestion(stages: list[dict[str, Any]]) -> dict[str, str] | None:
    from ....project_doc_suggestions import validate_project_doc_suggestion_payload

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
    suggestions: dict[str, dict[str, str]],
) -> None:
    if not project:
        return
    suggestion = _extract_project_doc_suggestion(stages)
    if suggestion is not None:
        suggestions[_project_suggestion_key(project)] = suggestion
    else:
        suggestions.pop(_project_suggestion_key(project), None)


def _validate_project_doc_suggestion_body(payload: dict[str, Any]) -> Any:
    from ....project_doc_suggestions import validate_project_doc_suggestion_payload

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


# ── .hs project-context payload helpers ──────────────────────────────────


def _project_hs_payload(project: dict[str, Any]) -> dict[str, Any]:
    from ....agent_context import (
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
    from ....agent_context import HS_CONTEXT_FILES

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


# ── blocks-document IO + starter templates ───────────────────────────────


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
    from ....plugins.dictation.blocks import BlockConfigError, load_blocks_yaml

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


# ── dry-run executor + its serialization helpers ─────────────────────────


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
    from ....dictation_telemetry import summarize_stage

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
    *,
    suggestions: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Execute the browser dry-run path for already-validated text."""
    from ....config import Config
    from ....dictation_telemetry import summarize_dry_run
    from ....plugins.dictation.assembly import DEFAULT_GLOBAL_BLOCKS_PATH, build_pipeline
    from ....plugins.dictation.contracts import Utterance
    from ....target_profile import collect_active_target_hints, detect_target_profile_with_override

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
    _store_project_doc_suggestion(project, stages, suggestions)
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


def _runtime_readiness(cfg: Any) -> dict[str, Any]:
    from ....dictation_telemetry import summarize_readiness_telemetry
    from ....plugins.dictation import runtime as runtime_module
    from ....plugins.dictation.runtime_counters import get_counters, get_session_status

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
        from ....plugins.dictation.guidance import runtime_guidance

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
        from ....plugins.dictation.guidance import runtime_guidance

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
        from ....plugins.dictation.guidance import runtime_guidance

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
