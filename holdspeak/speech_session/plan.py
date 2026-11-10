"""Content-free speech session plans (HS-131-09; the engine door 2026-11-09).

One desktop hold, one wake capture, or one text entry opens ONE plan with its
parent. The plan names, per stage, the engine-door JOB that stage asks
(``speech.transcribe``, ``speech.rewrite``...). It names no engine: each call
asks the door's chain (``engine_door.engine_for``) at the moment of the call, so
a change in Settings › Engines is honoured on the next call.

The plan carries ids, hashes and job names only — never audio, transcript,
prompt, token, or credential material.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

PLAN_SCHEMA = 1

PLAN_DICTATION = "DictationSessionPlan"
PLAN_WAKE = "WakeSessionPlan"

PARENT_DICTATION_SESSION = "dictation.session"
PARENT_WAKE_SESSION = "wake.session"

CAPABILITY_WHISPER_TRANSCRIBE = "whisper-transcribe"
CAPABILITY_WHISPER_PRELOAD = "whisper-preload"
CAPABILITY_INTENT_CLASSIFY = "intent-classify"
CAPABILITY_REWRITE = "rewrite"
CAPABILITY_PUNCTUATE = "punctuate"

CONTRACT_WHISPER_TRANSCRIBE = "holdspeak.whisper-transcribe"
CONTRACT_WHISPER_PRELOAD = "holdspeak.whisper-preload"
CONTRACT_INTENT_CLASSIFY = "holdspeak.dictation-intent-classify"
CONTRACT_REWRITE = "holdspeak.dictation-rewrite"
CONTRACT_PUNCTUATE = "holdspeak.dictation-punctuate"

#: The two preload stages Sol Amendment 7 keeps SEPARATE: the explicit
#: ``ModelHolder.get_model`` attempt, and the silent-audio fallback dispatch.
PRELOAD_STAGE_MODEL_HOLDER = "model-holder"
PRELOAD_STAGE_SILENT_AUDIO = "silent-audio"

# The kind of an on-device speech-to-text deployment revision (the runner
# builds an inert :class:`LocalWhisperDeployment` for it).
WHISPER_KIND = "local_speech_to_text"

# Named refusals. These are the only honest outcomes when the frozen plan, the
# live parent, or the owner's configured authority does not permit the dispatch.
CAPABILITY_NOT_PLANNED = "speech_capability_not_planned"
REVISION_NOT_PLANNED = "speech_revision_not_planned"
SESSION_NOT_ADMITTED = "speech_session_not_admitted"
SESSION_NOT_LIVE = "speech_session_not_live"
SESSION_CLOSED = "speech_session_closed"
SESSION_EXPIRED = "speech_session_expired"
#: A client asked an utterance to run under a parent id it supplied itself.
BROWSER_HANDLE_REFUSED = "browser_mic_handle_refused"
#: The browser interval's inactivity lease lapsed (Sol Amendment 8).
BROWSER_INACTIVITY_LAPSED = "browser_mic_inactivity_lapsed"
#: The browser interval reached its 30-minute authority ceiling.
BROWSER_CEILING_REACHED = "browser_mic_ceiling_reached"
#: A stop/close retired the acquisition generation while ``open()`` was still
#: admitting the interval's parent (Sol Amendment 1, applied to the browser).
BROWSER_STOPPED_DURING_OPEN = "browser_mic_stopped_during_open"
PRINCIPAL_REQUIRED = "speech_session_principal_required"
#: A nonempty ``Transcriber.transcribe`` with no live admitted session.
TRANSCRIPTION_CONTEXT_REQUIRED = "whisper_transcription_context_required"
#: The parent operation's warrant was revoked while the session was running.
SESSION_REVOKED = "speech_session_warrant_revoked"
#: The dispatch would have reached a target other than the frozen admitted
#: revision, and the backend cannot be rebound onto that revision.
REVISION_TARGET_UNBINDABLE = "speech_revision_target_unbindable"
#: A synthetic-text entry (browser rehearse / replay / template preview / remote
#: processing, or the CLI dry-run) was handed something other than its OWN fresh,
#: live text-entry admission: a missing or duck-typed value, a fence belonging to
#: another session, an ended session, or an open-mic/hold parent it tried to
#: borrow (HS-131-15).
ENTRY_SESSION_REQUIRED = "speech_entry_session_required"
#: `holdspeak dictation dry-run` would reach a provider, but this process holds no
#: hub-issued owner credential. It refuses BEFORE provider construction; it never
#: mints an owner for itself (HS-131-15, Sol Amendment 1).
CLI_CREDENTIAL_REQUIRED = "speech_cli_owner_credential_required"

#: The capabilities that reach a PROVIDER rather than Whisper, in the order the
#: pipeline would use them — so "which frozen revision does this pipeline
#: construct against?" has one deterministic answer.
PROVIDER_CAPABILITIES: tuple[str, ...] = (
    CAPABILITY_INTENT_CLASSIFY,
    CAPABILITY_REWRITE,
    CAPABILITY_PUNCTUATE,
)


class SpeechSessionRefused(RuntimeError):
    """A named, content-free speech-session refusal.

    ``detail`` carries owner-actionable, content-free remediation material (a
    configuration revision hash, a backend name) — never transcript, prompt, or
    credential text.
    """

    def __init__(self, reason: str, capability: str = "", *, detail: str = "") -> None:
        parts = [str(reason)]
        if capability:
            parts.append(str(capability))
        if detail:
            parts.append(str(detail))
        super().__init__(":".join(parts))
        self.reason = reason
        self.capability = capability
        self.detail = str(detail)


def sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def text_sha(text: Any) -> str:
    return "sha256:" + hashlib.sha256(str(text).encode("utf-8", "replace")).hexdigest()


@dataclass(frozen=True)
class SpeechSessionPlan:
    """One immutable speech routing/deployment plan. See the module docstring."""

    schema: int
    plan_kind: str
    session_id: str
    actor: str
    authority_basis: str
    insertion_aim: str
    insertion_context_sha256: str
    config_revision: str
    registry_revision: str
    created_at: float
    deadline_at: float
    child_budget: int
    capabilities: Mapping[str, tuple[str, ...]]
    unresolved: tuple[str, ...]
    sha256: str

    @property
    def subject_id(self) -> str:
        return self.session_id

    def has(self, capability: str) -> bool:
        return capability in self.capabilities

    def job(self, capability: str) -> str:
        """The engine-door job this stage asks; a stage the plan does not
        hold refuses by name."""
        entry = self.capabilities.get(capability)
        if not entry:
            raise SpeechSessionRefused(CAPABILITY_NOT_PLANNED, capability)
        return str(entry[0])

    def summary(self) -> dict[str, Any]:
        """The content-free snapshot a parent ``input_snapshot`` may carry."""
        return {
            "plan_schema": self.schema,
            "plan_kind": self.plan_kind,
            "session_id": self.session_id,
            "actor": self.actor,
            "authority_basis": self.authority_basis,
            "insertion_aim": self.insertion_aim,
            "insertion_context_sha256": self.insertion_context_sha256,
            "plan_sha256": self.sha256,
            "config_revision": self.config_revision,
            "registry_revision": self.registry_revision,
            "deadline_at": self.deadline_at,
            "child_budget": self.child_budget,
            "capabilities": {
                name: list(value) for name, value in sorted(self.capabilities.items())
            },
            "unresolved_capabilities": list(self.unresolved),
        }


class LocalWhisperDeployment:
    """The inert engine handle an admitted Whisper revision builds.

    A Whisper child dispatches through the ``Transcriber`` implementation the
    caller already holds, so the runner's engine construction must load nothing
    and read no mutable configuration — it only carries the frozen revision.
    """

    # ``_dispatch_context`` is a slot so the admitted child's HS-131-10 context can
    # ride the Whisper handle too: a slotted engine that cannot hold it would make
    # the dispatch leg fall back to the runner's own copy instead of proving it.
    __slots__ = ("revision", "_dispatch_context")

    def __init__(self, revision: Any) -> None:
        self.revision = revision


def _model_terms(model_config: Any) -> dict[str, Any]:
    return {
        "name": str(getattr(model_config, "name", "") or ""),
        "backend": str(getattr(model_config, "backend", "") or ""),
        "language": str(getattr(model_config, "language", "") or ""),
        "transcribe_timeout_seconds": float(
            getattr(model_config, "transcribe_timeout_seconds", 0.0) or 0.0
        ),
    }


def _pipeline_terms(config_snapshot: Any) -> dict[str, Any]:
    pipeline = getattr(getattr(config_snapshot, "dictation", None), "pipeline", None)
    return {
        "pipeline_enabled": bool(getattr(pipeline, "enabled", False)),
        "stages": [str(stage) for stage in (getattr(pipeline, "stages", None) or [])],
        "rewrite_passes": int(getattr(pipeline, "rewrite_passes", 1) or 1),
        "target_detect_llm_enabled": bool(
            getattr(pipeline, "target_detect_llm_enabled", False)
        ),
    }


def _pipeline_capabilities(terms: Mapping[str, Any]) -> tuple[str, ...]:
    """The provider-backed dictation stages this configuration actually selects.

    Nothing is planned "just in case": a stage absent here refuses by name if a
    seam ever tries to reach a provider for it. ``punctuate`` is deliberately
    absent — today's ``text_processor.process`` is lexical work, not a model
    dispatch, so no provider-backed punctuation stage is selected.
    """
    if not bool(terms.get("pipeline_enabled")):
        return ()
    stages = [str(stage) for stage in (terms.get("stages") or [])]
    declared: list[str] = []
    if "intent-router" in stages:
        declared.append(CAPABILITY_INTENT_CLASSIFY)
    # Sol Amendment 2: model-assisted target detection calls
    # ``runtime.rewrite`` (see ``target_profile.apply_model_assisted_target``),
    # NOT ``classify``. A target-detection-only configuration therefore plans
    # REWRITE; planning classify for it left the detector's real dispatch
    # unplanned, so it refused by name — or, worse, was swallowed by the
    # detector's broad catch and degraded silently to the heuristic.
    if "project-rewriter" in stages or bool(terms.get("target_detect_llm_enabled")):
        declared.append(CAPABILITY_REWRITE)
    return tuple(dict.fromkeys(declared))


def pipeline_provider_capabilities(config_snapshot: Any) -> tuple[str, ...]:
    """The provider-backed capabilities ONE config snapshot actually selects.

    The single derivation shared by every synthetic-text entry (HS-131-15), so a
    route, the CLI, and the plan resolver can never disagree about whether this
    configuration reaches a model at all. An empty tuple means intentionally
    lexical: no runtime is constructed and no inference child is minted.
    """
    return _pipeline_capabilities(_pipeline_terms(config_snapshot))


#: The engine-door job each speech stage asks. The preload warms the engine of
#: the ``speech.transcribe`` chain; its receipt names ``speech.preload``.
STAGE_JOBS: Mapping[str, str] = {
    CAPABILITY_WHISPER_TRANSCRIBE: "speech.transcribe",
    CAPABILITY_WHISPER_PRELOAD: "speech.preload",
    CAPABILITY_INTENT_CLASSIFY: "speech.intent_classify",
    CAPABILITY_REWRITE: "speech.rewrite",
    CAPABILITY_PUNCTUATE: "speech.punctuate",
}
#: The chain a stage's engine comes from (the preload has no chain of its own).
_CHAIN_JOB = {**STAGE_JOBS, CAPABILITY_WHISPER_PRELOAD: "speech.transcribe"}


def door_egress(db: Any, capabilities: Sequence[str]) -> str:
    """Where these stages' bytes can go, read from the door's chains now: the
    widest lamp (``local`` < ``private_network`` < ``mesh`` < ``cloud``) of each
    stage's first engine and its one retry. A stage with no engine sends
    nothing anywhere. A read; nothing is written."""
    from ..inference_locality import deployment_lamp
    from ..intel.providers import EGRESS_BOUNDARIES, EGRESS_LOCAL
    from ..services.engine_door import _next_in_chain, chain

    widest = EGRESS_LOCAL
    for job in dict.fromkeys(_CHAIN_JOB[name] for name in capabilities if name in _CHAIN_JOB):
        _assignment, engines = chain(db, job)
        if not engines:
            continue
        for engine in (engines[0], _next_in_chain(engines, engines[0])):
            revision = None if engine is None else db.deployment_revisions.get(engine.revision)
            if revision is None:
                continue
            lamp = deployment_lamp(getattr(revision, "boundary", ""), getattr(revision, "endpoint", ""))
            if lamp in EGRESS_BOUNDARIES and EGRESS_BOUNDARIES.index(lamp) > EGRESS_BOUNDARIES.index(widest):
                widest = lamp
    return widest


def configured_pipeline_egress_boundary(config_snapshot: Any, registry_snapshot: Any) -> str:
    """The before-action egress disclosure for one configuration snapshot: the
    stages it turns on, read through the door's chains (:func:`door_egress`).
    ``""`` when the chains cannot be read."""
    from ..intel.providers import EGRESS_LOCAL

    capabilities = pipeline_provider_capabilities(config_snapshot)
    if not capabilities:
        return EGRESS_LOCAL
    try:
        return door_egress(registry_snapshot, capabilities)
    except Exception:
        return ""


__all__ = [
    "BROWSER_CEILING_REACHED",
    "BROWSER_HANDLE_REFUSED",
    "BROWSER_INACTIVITY_LAPSED",
    "BROWSER_STOPPED_DURING_OPEN",
    "CAPABILITY_INTENT_CLASSIFY",
    "CAPABILITY_NOT_PLANNED",
    "CAPABILITY_PUNCTUATE",
    "CAPABILITY_REWRITE",
    "CAPABILITY_WHISPER_PRELOAD",
    "CAPABILITY_WHISPER_TRANSCRIBE",
    "CLI_CREDENTIAL_REQUIRED",
    "CONTRACT_INTENT_CLASSIFY",
    "CONTRACT_PUNCTUATE",
    "CONTRACT_REWRITE",
    "CONTRACT_WHISPER_PRELOAD",
    "CONTRACT_WHISPER_TRANSCRIBE",
    "LocalWhisperDeployment",
    "configured_pipeline_egress_boundary",
    "door_egress",
    "PARENT_DICTATION_SESSION",
    "PARENT_WAKE_SESSION",
    "PLAN_DICTATION",
    "PLAN_SCHEMA",
    "PLAN_WAKE",
    "PRELOAD_STAGE_MODEL_HOLDER",
    "PRELOAD_STAGE_SILENT_AUDIO",
    "PRINCIPAL_REQUIRED",
    "REVISION_NOT_PLANNED",
    "REVISION_TARGET_UNBINDABLE",
    "SESSION_CLOSED",
    "SESSION_EXPIRED",
    "SESSION_NOT_ADMITTED",
    "SESSION_NOT_LIVE",
    "SESSION_REVOKED",
    "SpeechSessionPlan",
    "STAGE_JOBS",
    "SpeechSessionRefused",
    "TRANSCRIPTION_CONTEXT_REQUIRED",
    "WHISPER_KIND",
    "pipeline_provider_capabilities",
    "sha",
    "text_sha",
]
