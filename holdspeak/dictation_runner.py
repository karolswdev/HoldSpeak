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

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from .logging_config import get_logger

log = get_logger("dictation_runtime")


@dataclass
class VoiceCommandResult:
    """Outcome of a fired voice command (HS-52-04).

    ``handled`` means the utterance was a configured command and was therefore NOT
    typed; ``ok`` is whether the action succeeded. The caller (the transcription path)
    returns early without typing whenever a result is returned.
    """

    handled: bool
    keyword: str = ""
    kind: str = ""
    preview: str = ""
    ok: bool = True
    error: str = ""
    result: Optional[dict] = None


def dispatch_voice_command(
    text: str,
    *,
    config: Any,
    runner: Any = None,
    type_writer: Optional[Callable[[str], None]] = None,
    platform: Optional[str] = None,
    on_activity: Optional[Callable[[str], None]] = None,
) -> Optional[VoiceCommandResult]:
    """If ``text`` is a configured, enabled voice command, fire it and return the
    outcome (handled); otherwise return ``None`` so the caller dictates as normal.

    This is the dispatch decision at the top of the dictation seam. It is off by
    default (macros disabled -> ``None``, byte-identical to no feature), matches the
    whole utterance deterministically (``VoiceMacro.matches`` selects WHICH macro, never
    composes one), and fires through the bounded connector (HS-52-03), which reuses the
    guarded execution (permission gate + per-macro manifest). A configured macro is
    auto-fired: the config is the consent, so there is no per-fire prompt.

    The actuator *persistence* table is meeting-scoped (``actuator_proposals.meeting_id``
    references ``meetings(id)``) and a voice fire has no meeting, so the fire is audited
    via ``on_activity`` + the log rather than that table. The guarded execution (the
    security-relevant part) is fully reused.
    """
    macros_cfg = getattr(getattr(config, "dictation", None), "macros", None)
    if macros_cfg is None or not bool(getattr(macros_cfg, "enabled", False)):
        return None
    macro = next((m for m in getattr(macros_cfg, "items", []) if m.matches(text)), None)
    if macro is None:
        return None

    from .plugins.actuators import ActuatorProposal
    from .plugins.voice_macro_connector import build_voice_macro_connector

    action = macro.action
    preview = action.preview()
    if on_activity is not None:
        try:
            on_activity(f"command: {macro.keyword}")
        except Exception:  # an activity-broadcast hiccup must never block the command
            pass

    proposal_view = ActuatorProposal(
        target="voice_macro",
        action=action.kind,
        preview=preview,
        payload={"kind": action.kind, "payload": action.payload},
        reversible=False,
        required_capabilities=(),
    )
    try:
        connector = build_voice_macro_connector(
            action, runner=runner, type_writer=type_writer, platform=platform
        )
        result = connector(proposal_view)
        log.info("voice command fired: %r -> %s", macro.keyword, preview)
        return VoiceCommandResult(
            handled=True,
            keyword=macro.keyword,
            kind=action.kind,
            preview=preview,
            ok=True,
            result=result if isinstance(result, dict) else {"result": result},
        )
    except Exception as exc:
        log.warning("voice command %r failed: %s", macro.keyword, exc)
        return VoiceCommandResult(
            handled=True,
            keyword=macro.keyword,
            kind=action.kind,
            preview=preview,
            ok=False,
            error=f"{type(exc).__name__}: {exc}",
        )


def run_dictation_pipeline(
    text: str,
    *,
    config: Any,
    server: Any,
    audio_duration_s: float,
    transcribed_at: datetime,
    agent_reply_session: Any | None = None,
    journal_source: str = "dictation",
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
        # HS-53-07: the pre-briefing loop closes here. A "Dictate with this"
        # click parked a record id; consume it (one-shot, recency-bounded) so the
        # selected ActivityRecord is pinned at records[0] and named to the model.
        # No pending pin -> selected_record_id is None -> byte-identical default.
        from holdspeak.dictation_selection import consume_selected_record

        selected_record_id = consume_selected_record()
        activity = build_activity_context(
            limit=20, refresh=False, selected_record_id=selected_record_id
        ).to_dict()
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
                source=journal_source,
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
