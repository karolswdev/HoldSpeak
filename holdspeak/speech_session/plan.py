"""Frozen, content-free speech session plans (HS-131-09).

One desktop hold, one wake capture, or one pre-session local-model warm freezes
ONE plan before any child is admitted. The plan names, per capability, the
ORDERED and immutable deployment revisions that capability may execute
(HS-131-08 Sol Amendment 1 shape, reused verbatim here). Every admitted child
repeats an entry the plan already froze; a capability absent from the plan is a
named refusal, never a late placement resolution.

The plan carries ids, hashes, revisions, and capability names only — never
audio, transcript, prompt, token, or credential material.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

PLAN_SCHEMA = 1

PLAN_DICTATION = "DictationSessionPlan"
PLAN_WAKE = "WakeSessionPlan"
PLAN_LOCAL_MODEL_PRELOAD = "LocalModelPreloadPlan"

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

# The one on-device speech-to-text destination. Whisper is a real deployment: it
# has an engine (mlx / faster-whisper), a model, and a same-device boundary, so
# it is frozen and receipted like every other place a model runs.
WHISPER_DESTINATION_ID = "local_whisper"
WHISPER_KIND = "local_speech_to_text"
WHISPER_BOUNDARY = "same_device"

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
#: A pre-session warm with no ``model.local_model_preload_authority``.
PRELOAD_AUTHORITY_REQUIRED = "local_model_preload_authority_required"
#: The knob is set but does not name THIS model configuration's revision.
PRELOAD_AUTHORITY_MISMATCHED = "local_model_preload_authority_mismatched"
#: The parent operation's warrant was revoked while the session was running.
SESSION_REVOKED = "speech_session_warrant_revoked"
#: The dispatch would have reached a target other than the frozen admitted
#: revision, and the backend cannot be rebound onto that revision.
REVISION_TARGET_UNBINDABLE = "speech_revision_target_unbindable"


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
    #: The FROZEN deployment revisions this plan admitted, by revision id. The
    #: dispatch seam binds its target from these fields, so a configuration
    #: change after admission can never retarget a live session — and no dispatch
    #: pays a database read to find out where it is allowed to run.
    deployments: Mapping[str, Any] = field(default_factory=dict)

    @property
    def subject_id(self) -> str:
        return self.session_id

    def deployment(self, revision_id: str) -> Any:
        """The frozen revision object for ``revision_id``, or ``None``."""
        return self.deployments.get(str(revision_id))

    def egress_boundary(self, capability: str = "") -> str:
        """Where this plan's model work ACTUALLY goes, from the frozen revisions.

        Sol round 2: the browser route used to state its egress from a separate
        top-level ``inference.run`` admission that neither parented nor authorized
        the real children — and that defaulted to ``local`` whenever the kernel
        errored. The honest source is the revision this session already froze, run
        through the ONE egress classifier (HS-130-04), so the label names exactly
        the destination the receipts name.

        Sol round 3: a classify-only pipeline must not report ``local`` because
        rewrite happens to be unplanned. With no explicit ``capability``, the
        label conservatively combines EVERY frozen provider capability
        (classify, rewrite, punctuate) and reports the widest boundary. A
        capability the plan never froze cannot egress at all — the dispatch
        would refuse by name — so an EMPTY provider set is honestly ``local``.
        """
        from ..intel.providers import EGRESS_BOUNDARIES, EGRESS_LOCAL, egress_boundary

        def boundary_of(name: str) -> str:
            revision = self.deployment(self.primary(name)) if self.has(name) else None
            if revision is None:
                return EGRESS_LOCAL
            endpoint = str(getattr(revision, "endpoint", "") or "")
            node = str(getattr(revision, "node", "") or "")
            return str(egress_boundary(cloud=bool(endpoint), base_url=endpoint, node=node))

        if capability:
            return boundary_of(capability)
        provider_capabilities = (
            CAPABILITY_INTENT_CLASSIFY, CAPABILITY_REWRITE, CAPABILITY_PUNCTUATE,
        )
        widest = EGRESS_LOCAL
        for name in provider_capabilities:
            candidate = boundary_of(name)
            if EGRESS_BOUNDARIES.index(candidate) > EGRESS_BOUNDARIES.index(widest):
                widest = candidate
        return widest

    def has(self, capability: str) -> bool:
        return capability in self.capabilities

    def revisions(self, capability: str) -> tuple[str, ...]:
        """The ordered permitted deployment revisions for one capability."""
        entry = self.capabilities.get(capability)
        if not entry:
            raise SpeechSessionRefused(CAPABILITY_NOT_PLANNED, capability)
        return tuple(entry)

    def primary(self, capability: str) -> str:
        return self.revisions(capability)[0]

    def assert_planned(self, capability: str, revision_id: str) -> str:
        if str(revision_id) not in self.revisions(capability):
            raise SpeechSessionRefused(REVISION_NOT_PLANNED, capability)
        return str(revision_id)

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


def whisper_deployment_identity(model_config: Any, *, backend: str = "") -> Any:
    """The ONE deployment identity a local Whisper dispatch is pinned to."""
    from ..inference_targets import DeploymentIdentity

    return DeploymentIdentity(
        destination_id=WHISPER_DESTINATION_ID,
        kind=WHISPER_KIND,
        engine=str(backend or getattr(model_config, "backend", "auto") or "auto"),
        model=str(getattr(model_config, "name", "") or ""),
        node="",
        boundary=WHISPER_BOUNDARY,
        model_path=None,
        endpoint="",
        secret_slot="",
    )


class LocalWhisperDeployment:
    """The inert engine handle an admitted Whisper revision builds.

    A Whisper child dispatches through the ``Transcriber`` implementation the
    caller already holds, so the runner's engine construction must load nothing
    and read no mutable configuration — it only carries the frozen revision.
    """

    __slots__ = ("revision",)

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
    runtime = getattr(getattr(config_snapshot, "dictation", None), "runtime", None)
    return {
        "pipeline_enabled": bool(getattr(pipeline, "enabled", False)),
        "stages": [str(stage) for stage in (getattr(pipeline, "stages", None) or [])],
        "rewrite_passes": int(getattr(pipeline, "rewrite_passes", 1) or 1),
        "target_detect_llm_enabled": bool(
            getattr(pipeline, "target_detect_llm_enabled", False)
        ),
        "runtime_backend": str(getattr(runtime, "backend", "") or ""),
        "runtime_profile_id": str(getattr(runtime, "profile_id", "") or ""),
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
    if "intent-router" in stages or bool(terms.get("target_detect_llm_enabled")):
        declared.append(CAPABILITY_INTENT_CLASSIFY)
    if "project-rewriter" in stages:
        declared.append(CAPABILITY_REWRITE)
    return tuple(declared)


class DictationSessionPlanResolver:
    """The ONE session-opening resolution seam (Sol OQ4).

    Resolution happens EXACTLY once, when the session opens: adapters later
    receive the frozen deployment revision directly and never reconstruct a
    target from mutable settings.
    """

    def resolve(
        self,
        config_snapshot: Any,
        registry_snapshot: Any,
        principal: Any,
        insertion_aim: str,
        *,
        session_id: str,
        deadline_at: float,
        child_budget: int,
        plan_kind: str = PLAN_DICTATION,
        capabilities: Sequence[str] = (),
        insertion_context: str = "",
        created_at: Optional[float] = None,
    ) -> SpeechSessionPlan:
        from ..deployment_revisions import capture_deployment_revision

        if principal is None or str(getattr(principal, "name", "none")) == "none":
            raise SpeechSessionRefused(PRINCIPAL_REQUIRED)

        model_terms = _model_terms(getattr(config_snapshot, "model", None))
        pipeline_terms = _pipeline_terms(config_snapshot)
        whisper = capture_deployment_revision(
            registry_snapshot,
            whisper_deployment_identity(getattr(config_snapshot, "model", None)),
        )

        declared = list(dict.fromkeys(str(name) for name in capabilities if str(name).strip()))
        if not declared:
            declared = [CAPABILITY_WHISPER_TRANSCRIBE, CAPABILITY_WHISPER_PRELOAD]
            declared.extend(_pipeline_capabilities(pipeline_terms))

        frozen: dict[str, tuple[str, ...]] = {}
        unresolved: list[str] = []
        deployments: dict[str, Any] = {whisper.id: whisper}
        provider_legs: tuple[Any, ...] | None = None
        for name in declared:
            if name in (CAPABILITY_WHISPER_TRANSCRIBE, CAPABILITY_WHISPER_PRELOAD):
                frozen[name] = (whisper.id,)
                continue
            if provider_legs is None:
                provider_legs = self._provider_legs(
                    registry_snapshot, pipeline_terms["runtime_profile_id"]
                )
            if provider_legs:
                frozen[name] = tuple(leg.id for leg in provider_legs)
                deployments.update({leg.id: leg for leg in provider_legs})
            else:
                # An unreachable leg is NOT a silent omission: it is recorded on
                # the plan, and any dispatch for it refuses by name.
                unresolved.append(name)

        config_revision = sha({"model": model_terms, "pipeline": pipeline_terms})
        registry_revision = sha(
            {name: list(value) for name, value in sorted(frozen.items())}
        )
        now = time.time() if created_at is None else float(created_at)
        body = {
            "schema": PLAN_SCHEMA,
            "plan_kind": str(plan_kind),
            "session_id": str(session_id),
            "actor": f"{principal.name}:{principal.identity}",
            "authority_basis": str(getattr(principal, "authority_basis", "") or ""),
            "insertion_aim": str(insertion_aim or ""),
            "insertion_context_sha256": text_sha(insertion_context),
            "config_revision": config_revision,
            "registry_revision": registry_revision,
            "deadline_at": float(deadline_at),
            "child_budget": int(child_budget),
            "capabilities": {name: list(value) for name, value in sorted(frozen.items())},
            "unresolved": sorted(unresolved),
        }
        return SpeechSessionPlan(
            schema=PLAN_SCHEMA,
            plan_kind=str(plan_kind),
            session_id=str(session_id),
            actor=str(body["actor"]),
            authority_basis=str(body["authority_basis"]),
            insertion_aim=str(insertion_aim or ""),
            insertion_context_sha256=str(body["insertion_context_sha256"]),
            config_revision=config_revision,
            registry_revision=registry_revision,
            created_at=now,
            deadline_at=float(deadline_at),
            child_budget=int(child_budget),
            capabilities=frozen,
            unresolved=tuple(sorted(unresolved)),
            sha256=sha(body),
            deployments=deployments,
        )

    @staticmethod
    def _provider_legs(registry_snapshot: Any, profile_id: str) -> tuple[Any, ...]:
        """The ordered dictation-LLM legs, resolved ONCE at session opening."""
        from ..deployment_revisions import capture_deployment_revision
        from ..inference_targets import resolve_placement

        try:
            resolution = resolve_placement(
                registry_snapshot, invocation=str(profile_id).strip() or None
            )
            target = resolution.target
            if target is None or target.deployment is None:
                return ()
            return (capture_deployment_revision(registry_snapshot, target),)
        except Exception:
            return ()


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
    "CONTRACT_INTENT_CLASSIFY",
    "CONTRACT_PUNCTUATE",
    "CONTRACT_REWRITE",
    "CONTRACT_WHISPER_PRELOAD",
    "CONTRACT_WHISPER_TRANSCRIBE",
    "DictationSessionPlanResolver",
    "LocalWhisperDeployment",
    "PARENT_DICTATION_SESSION",
    "PARENT_WAKE_SESSION",
    "PLAN_DICTATION",
    "PLAN_LOCAL_MODEL_PRELOAD",
    "PLAN_SCHEMA",
    "PLAN_WAKE",
    "PRELOAD_AUTHORITY_MISMATCHED",
    "PRELOAD_AUTHORITY_REQUIRED",
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
    "SpeechSessionRefused",
    "TRANSCRIPTION_CONTEXT_REQUIRED",
    "WHISPER_DESTINATION_ID",
    "WHISPER_KIND",
    "sha",
    "text_sha",
    "whisper_deployment_identity",
]
