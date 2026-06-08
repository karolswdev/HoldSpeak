"""HS-52-01: the dictation-execution seam, carved out of ``web_runtime``.

The dictation pipeline orchestration used to be an inline method
(``_maybe_run_dictation_pipeline``) on the 2,341-line ``WebRuntime`` god-object.
This module holds that orchestration as a standalone, unit-testable function so the
dictation path has a clean home of its own. ``web_runtime`` now delegates to it.
Named ``dictation_runner`` (not ``dictation_runtime``) to stay distinct from the
DIR-01 LLM backend layer in ``holdspeak.plugins.dictation.runtime``.

Behaviour is byte-identical to the old inline method: the body is verbatim, with the
two ``self`` collaborators it touched (``self.config`` and ``self.server``) lifted to
explicit parameters. Off (pipeline disabled) or on any error it returns the input
text unchanged (the byte-identical default), and journaling stays a best-effort
side-channel that never alters the returned text.

Phase 52's voice-command dispatch will sit at the top of this seam in a later story;
this story only carves it out, adding no new behaviour.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .logging_config import get_logger

log = get_logger("dictation_runtime")


def run_dictation_pipeline(
    text: str,
    *,
    config: Any,
    server: Any,
    audio_duration_s: float,
    transcribed_at: datetime,
    agent_reply_session: Any | None = None,
) -> str:
    """Run the dictation pipeline over ``text`` and return the text to type.

    ``config`` is the runtime config (``config.dictation.pipeline`` gates the run);
    ``server`` supplies the optional dictation collaborators (correction store,
    telemetry, journal). Returns ``text`` unchanged when the pipeline is disabled or
    anything raises.
    """
    dictation_cfg = getattr(config, "dictation", None)
    pipeline_cfg = getattr(dictation_cfg, "pipeline", None)
    if dictation_cfg is None or pipeline_cfg is None or not bool(getattr(pipeline_cfg, "enabled", False)):
        return text

    try:
        from holdspeak.activity_context import build_activity_context
        from holdspeak.agent_context import get_recent_agent_session
        from holdspeak.agent_device import target_profile_override_for_agent
        from holdspeak.plugins.dictation.assembly import build_pipeline
        from holdspeak.plugins.dictation.contracts import Utterance
        from holdspeak.plugins.dictation.project_root import detect_project_for_cwd
        from holdspeak.target_profile import (
            apply_model_assisted_target,
            apply_target_correction,
            collect_active_target_hints,
            detect_target_profile_with_override,
        )

        if agent_reply_session is not None and getattr(agent_reply_session, "cwd", None):
            project = detect_project_for_cwd(
                Path(str(agent_reply_session.cwd)),
                prefer_agent_session=False,
            )
        else:
            project = detect_project_for_cwd()
        project_root = Path(project["root"]) if project else None

        # HS-39-02: consult the session correction store (shared with the
        # dictation routes via the server) when corrections are enabled.
        corrections_store = getattr(server, "dictation_corrections", None)
        correction_snapshot = (
            corrections_store.snapshot()
            if corrections_store is not None and bool(getattr(pipeline_cfg, "corrections_enabled", False))
            else None
        )

        telemetry_store = getattr(server, "dictation_telemetry", None)
        result = build_pipeline(
            dictation_cfg,
            project_root=project_root,
            corrections=correction_snapshot,
            on_run=(telemetry_store.record_run if telemetry_store is not None else None),
        )
        if result.runtime_status != "loaded":
            return text

        target_override = (
            target_profile_override_for_agent(agent_reply_session)
            or getattr(pipeline_cfg, "target_profile_override", "auto")
        )
        activity = build_activity_context(limit=20, refresh=False).to_dict()
        target_hints = collect_active_target_hints()
        target_profile = detect_target_profile_with_override(target_hints, target_override)
        target_profile = apply_target_correction(
            target_profile, text=text, corrections=correction_snapshot
        )
        target_profile = apply_model_assisted_target(
            target_profile,
            runtime=getattr(result, "runtime", None),
            hints=target_hints,
            text=text,
            enabled=bool(getattr(pipeline_cfg, "target_detect_llm_enabled", False)),
            below_confidence=float(getattr(pipeline_cfg, "target_detect_llm_below", 0.8)),
        )
        activity["target"] = target_profile.to_dict()
        recent_agent = agent_reply_session or get_recent_agent_session(max_age_seconds=120)
        if recent_agent is not None and bool(getattr(recent_agent, "awaiting_response", False)):
            agent_project_root = getattr(recent_agent, "repo_root", None)
            if not project_root or not agent_project_root or str(project_root) == str(agent_project_root):
                activity["agent"] = recent_agent.to_dict()

        run = result.pipeline.run(
            Utterance(
                raw_text=text,
                audio_duration_s=audio_duration_s,
                transcribed_at=transcribed_at,
                project=project,
                activity=activity,
            )
        )
        # HS-45-01: journal this run as a side-channel (best-effort, never
        # alters the typed result). Same post-run seam telemetry uses.
        journal = getattr(server, "dictation_journal", None)
        if journal is not None:
            journal.record(
                run,
                source="dictation",
                transcript=text,
                target_profile=target_profile,
                project_root=project_root,
                enabled=bool(getattr(pipeline_cfg, "journal_enabled", True)),
                retention=int(getattr(pipeline_cfg, "journal_retention", 500)),
            )
        return run.final_text
    except Exception as exc:
        log.warning(f"Web dictation pipeline raised; falling back to processed text: {exc}")
        return text
