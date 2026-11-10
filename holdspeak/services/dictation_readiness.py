"""Dictation readiness projection used by DictationService on both transports."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from .dictation_files import (
    _block_summary,
    _resolve_blocks_target,
    _resolve_project_context,
)
from .dictation_service import _refused

#: HS-176-02 (R12/N1): the order the six target-override ids are offered in.
#: `auto` is NOT a member — it is meaningless as a correction and `_profile`
#: raises `KeyError` on it inside the live typing path.
_TARGET_OVERRIDE_ORDER = (
    "claude_code",
    "codex_cli",
    "terminal_shell",
    "browser",
    "editor",
    "chat",
)


def _target_override_options() -> list[dict[str, str]]:
    """The `target` correction's `[{id, label}]` pick list — six ids, no `auto`.

    The labels come from `_profile`'s own map (`target_profile.py:280-288`), the
    ONE source, so the face prints `Terminal shell` verbatim and no design-owned
    label table can drift from it (C12 note).
    """
    from ..target_profile import TARGET_PROFILE_OVERRIDE_OPTIONS, _profile

    offered = [
        pid for pid in _TARGET_OVERRIDE_ORDER if pid in TARGET_PROFILE_OVERRIDE_OPTIONS
    ]
    # Anything the option set grows later is still offered (never `auto`).
    offered += sorted(
        TARGET_PROFILE_OVERRIDE_OPTIONS - set(_TARGET_OVERRIDE_ORDER) - {"auto"}
    )
    options: list[dict[str, str]] = []
    for pid in offered:
        try:
            label = _profile(pid, 0.0, "readiness", {}, details={}).label
        except Exception:  # pragma: no cover - the belt N1 pays in target_profile
            label = pid
        options.append({"id": pid, "label": str(label)})
    return options


def _hotkey_custody(ctx: Any, config_snapshot: Any) -> dict[str, Any]:
    """HS-200-05: the physical hotkey's custody, for `/api/dictation/readiness`.

    Two facts, joined: whether the global listener actually installed (the
    runtime's own `global_hotkey_available` / `global_hotkey_error`, which
    until now nothing read), and the honestly-read state of the three macOS
    grants the dictation path needs. Reading a grant NEVER prompts.

    When the app has no runtime to ask — a bare test server, a dry run —
    availability is `None`, which the face must render UNKNOWN. It is never
    smoothed into "the hotkey works".
    """
    from ..desktop_permissions import hotkey_custody

    available: Optional[bool] = None
    error = ""
    getter = getattr(ctx, "on_get_status", None)
    if callable(getter):
        try:
            status = getter() or {}
        except Exception as exc:  # pragma: no cover - defensive
            status = {}
            error = f"{type(exc).__name__}: {exc}"
        raw = (
            status.get("global_hotkey_available") if isinstance(status, dict) else None
        )
        if isinstance(raw, bool):
            available = raw
        if isinstance(status, dict) and not error:
            error = str(status.get("global_hotkey_error") or "")

    hotkey_cfg = getattr(config_snapshot, "hotkey", None)
    return hotkey_custody(
        listener_available=available,
        listener_error=error,
        key=str(getattr(hotkey_cfg, "key", "") or ""),
        display=str(getattr(hotkey_cfg, "display", "") or ""),
    )


def _runtime_readiness(cfg: Any) -> dict[str, Any]:
    from ..dictation_telemetry import summarize_readiness_telemetry
    from ..plugins.dictation import runtime as runtime_module
    from ..plugins.dictation.runtime_counters import get_counters, get_session_status

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
        resolved_backend, reason = runtime_module.resolve_backend(
            cfg.runtime.backend,
            mlx_model_set=bool(str(cfg.runtime.mlx_model or "").strip()),
        )
    except runtime_module.RuntimeUnavailableError as exc:
        from ..plugins.dictation.guidance import runtime_guidance

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
        from ..intel.providers import effective_dictation_llm
        from ..plugins.dictation.guidance import runtime_guidance

        effective = effective_dictation_llm(cfg.runtime)
        payload = {
            "status": "available",
            "requested_backend": cfg.runtime.backend,
            "resolved_backend": resolved_backend,
            "detail": (
                f"endpoint={effective.base_url or 'unset'}; "
                f"model={effective.model or 'unset'}"
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

    raw_model_path = str(
        cfg.runtime.mlx_model
        if resolved_backend == "mlx"
        else cfg.runtime.llama_cpp_model_path
    ).strip()
    model_path = Path(raw_model_path).expanduser()
    # A blank path is "not set", never Path("") == "." (which exists).
    model_exists = bool(raw_model_path) and model_path.exists()
    guidance = None
    if not model_exists:
        from ..plugins.dictation.guidance import runtime_guidance

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


def readiness(ctx: Any, project_root: Optional[str] = None, *, db: Any) -> dict[str, Any]:
    from ..agent_context import get_recent_agent_session
    from ..config import Config
    from ..plugins.dictation.project_kb import (
        ProjectKBError,
        kb_path_for,
        read_project_kb,
    )
    from ..target_profile import (
        detect_active_target_profile,
        detect_target_profile_with_override,
    )

    config_snapshot = Config.load()
    cfg = config_snapshot.dictation
    warnings: list[dict[str, Any]] = []

    project: Optional[dict[str, Any]]
    project_error: Optional[str] = None
    try:
        project = _resolve_project_context(project_root)
    except ValueError as exc:
        if project_root:
            raise _refused(400, {"error": str(exc)}) from exc
        project = None
        project_error = str(exc)

    global_path, _ = _resolve_blocks_target("global")
    global_blocks = _block_summary(global_path)

    project_blocks: Optional[dict[str, Any]] = None
    project_root_path: Optional[Path] = None
    if project is not None:
        project_root_path = Path(project["root"])
        project_blocks = _block_summary(
            project_root_path / ".holdspeak" / "blocks.yaml"
        )

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

    # HS-47-04: the `.hs/` context existence, so the discovery nudge can tell
    # "this project has no knowledge yet" (no KB and no context) without a new
    # detection path.
    hs_context_payload: dict[str, Any] = {"path": None, "exists": False}
    if project_root_path is not None:
        hs_dir = project_root_path / ".hs"
        hs_context_payload["path"] = str(hs_dir)
        hs_context_payload["exists"] = hs_dir.is_dir()

    runtime_payload = _runtime_readiness(cfg)
    # HS-200-05: the physical hotkey's custody. `web_runtime` has always
    # recorded `global_hotkey_available` / `global_hotkey_error` and NOTHING
    # read them, so a refused Input Monitoring grant made Right Option do
    # nothing and the desk never said why. This is the seam that carries it
    # out, beside the three macOS grants the dictation path actually needs.
    # `on_get_status` is absent on a bare/test app: then availability is
    # honestly `None` (UNKNOWN), never a claim that the listener is up.
    hotkey_payload = _hotkey_custody(ctx, config_snapshot)
    from ..speech_session import configured_pipeline_egress_boundary

    egress_boundary = configured_pipeline_egress_boundary(
        config_snapshot, db
    )
    try:
        target_payload = detect_active_target_profile(
            cfg.pipeline.target_profile_override
        ).to_dict()
    except Exception:
        target_payload = detect_target_profile_with_override(
            {},
            cfg.pipeline.target_profile_override,
        ).to_dict()
    # HS-176-02 (R12/N1): the label source for a `target` correction. The
    # face renders labels; the wire carries ids. SIX ids —
    # `TARGET_PROFILE_OVERRIDE_OPTIONS` minus `auto`, which is meaningless
    # as a correction and raises `KeyError` inside `_profile` on the live
    # typing path. The labels are read from `_profile`'s own map, so there
    # is no second, drifting label table (C12 note).
    target_payload["overrides"] = _target_override_options()
    agent_hooks_payload: dict[str, Any] = {}
    for agent in ("claude", "codex"):
        latest = get_recent_agent_session(agent=agent, max_age_seconds=7 * 24 * 60 * 60)
        agent_hooks_payload[agent] = {
            "fresh": latest is not None,
            "latest_session": latest.to_dict() if latest else None,
        }

    if not cfg.pipeline.enabled:
        warnings.append(
            {
                "code": "pipeline_disabled",
                "message": "Dictation pipeline is disabled.",
                "action": "Enable the dictation pipeline from Runtime.",
                "section": "runtime",
                "runtime_action": "enable_pipeline",
            }
        )
    if project is None:
        warnings.append(
            {
                "code": "no_project",
                "message": project_error or "No project root detected.",
                "action": "Set a project root override or launch holdspeak from a project directory.",
                "section": "readiness",
            }
        )
    if not resolved_blocks["exists"] or int(resolved_blocks["count"]) == 0:
        warnings.append(
            {
                "code": "no_blocks",
                "message": "No dictation blocks are loaded for the selected project.",
                "action": "Create the Action item starter and run its sample.",
                "section": "blocks",
                "template_id": "action_item",
                "template_action": "create_dry_run",
                "template_scope": "project" if project is not None else "global",
            }
        )
    if not global_blocks["valid"] or (
        project_blocks is not None and not project_blocks["valid"]
    ):
        warnings.append(
            {
                "code": "invalid_blocks",
                "message": "A blocks.yaml file is invalid.",
                "action": "Open Blocks and fix the validation error.",
                "section": "blocks",
            }
        )
    if project is not None and not kb_payload["exists"]:
        warnings.append(
            {
                "code": "missing_project_kb",
                "message": "Project KB file is missing.",
                "action": "Create a starter Project KB file.",
                "section": "kb",
                "kb_action": "create_starter",
            }
        )
    if not kb_payload["valid"]:
        warnings.append(
            {
                "code": "invalid_project_kb",
                "message": "Project KB file is invalid.",
                "action": "Open Project KB and fix the validation error.",
                "section": "kb",
            }
        )
    if runtime_payload["status"] == "unavailable":
        warnings.append(
            {
                "code": "runtime_unavailable",
                "message": runtime_payload["detail"],
                "action": "Install the selected runtime extra or change backend.",
                "section": "runtime",
                "guidance": runtime_payload.get("guidance"),
            }
        )
    elif runtime_payload["status"] == "missing_model":
        warnings.append(
            {
                "code": "runtime_model_missing",
                "message": runtime_payload["detail"],
                "action": "Download the model or update the runtime model path.",
                "section": "runtime",
                "guidance": runtime_payload.get("guidance"),
            }
        )

    ready = (
        cfg.pipeline.enabled
        and project is not None
        and bool(resolved_blocks["valid"])
        and int(resolved_blocks["count"]) > 0
        and bool(kb_payload["valid"])
        and runtime_payload["status"] == "available"
    )

    # HS-39-05: depth telemetry — per-stage latency quantiles + budget
    # guidance + multi-pass timings + correction-store state.
    from ..dictation_telemetry import build_depth_readiness

    telemetry_store = getattr(ctx, "telemetry", None)
    corrections_store = getattr(ctx, "corrections", None)
    depth_payload = build_depth_readiness(
        stage_quantiles=telemetry_store.stage_quantiles()
        if telemetry_store is not None
        else {},
        rewrite_pass_ms=telemetry_store.latest_rewrite_pass_ms()
        if telemetry_store is not None
        else [],
        run_count=len(telemetry_store) if telemetry_store is not None else 0,
        budget_ms=cfg.pipeline.max_total_latency_ms,
        corrections_enabled=bool(getattr(cfg.pipeline, "corrections_enabled", False)),
        corrections_size=len(corrections_store) if corrections_store is not None else 0,
        corrections_recent=(
            [c.key for c in corrections_store.recent(limit=5)]
            if corrections_store is not None
            else []
        ),
    )

    return {
        "ready": ready,
        "project": project,
        "egress_boundary": egress_boundary,
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
        "project_context": hs_context_payload,
        "runtime": runtime_payload,
        "hotkey": hotkey_payload,
        "telemetry": runtime_payload.get("telemetry"),
        "depth": depth_payload,
        "target": target_payload,
        "agent_hooks": agent_hooks_payload,
        "warnings": warnings,
    }
