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
from pathlib import Path
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

# The one on-device DICTATION-LLM destination. When `dictation.runtime.profile_id`
# points nowhere, a provider-backed dictation stage runs HERE: on the artifact
# `dictation.runtime` names. It is a real deployment (engine + model + same-device
# boundary), so it is frozen and receipted like every other place a model runs.
#
# Its `kind` is deliberately the EXISTING same-device kind rather than a new one:
# the runner's engine factory already builds `this_device` from a revision's own
# frozen fields, so this destination needs no new construction branch.
DICTATION_DESTINATION_ID = "local_dictation"
DICTATION_KIND = "this_device"
DICTATION_BOUNDARY = "same_device"

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

    # ``_dispatch_context`` is a slot so the admitted child's HS-131-10 context can
    # ride the Whisper handle too: a slotted engine that cannot hold it would make
    # the dispatch leg fall back to the runner's own copy instead of proving it.
    __slots__ = ("revision", "_dispatch_context")

    def __init__(self, revision: Any) -> None:
        self.revision = revision


def _local_dictation_engine(backend: str) -> str:
    """The on-device engine one configured dictation backend selects, at PLAN time.

    ``auto`` uses the runtime resolver's real importability semantics at plan
    time. A discoverable ``mlx_lm`` package can still fail import because of a
    missing transitive dependency or ABI mismatch; freezing MLX from a module spec
    would then remove the existing valid fallback to ``llama_cpp``. The import is
    the availability probe only — admitted construction still forces
    ``warm_on_start=False``, so no model is loaded before a child exists.

    ``openai_compatible`` (and any unknown value) names NO on-device artifact and
    resolves to ``""``: with no profile pointer there is nothing to freeze, and
    the capability is recorded UNRESOLVED rather than aimed at another
    subsystem's model.
    """
    requested = str(backend or "auto").strip().lower()
    if requested in ("mlx", "llama_cpp"):
        return requested
    if requested != "auto":
        return ""

    import importlib
    import platform

    def importable(name: str) -> bool:
        try:
            importlib.import_module(name)
        except Exception:  # pragma: no cover - environment-dependent probe
            return False
        return True

    if platform.system() == "Darwin" and platform.machine() == "arm64":
        if importable("mlx_lm"):
            return "mlx"
    # Preserve the historical no-runtime plan shape when neither optional package
    # exists; construction will report unavailable. When llama.cpp IS importable,
    # this is the same concrete fallback runtime.resolve_backend would choose.
    return "llama_cpp"


def dictation_local_deployment_identity(terms: Mapping[str, Any]) -> Any:
    """The same-device deployment a provider-backed dictation stage would load.

    Built from the SAME frozen pipeline terms the plan hashes, so the artifact the
    plan FREEZES and the artifact ``config_revision`` COVERS can never be two
    different things. ``None`` means this configuration names no on-device
    dictation artifact at all.
    """
    from ..inference_targets import DeploymentIdentity

    engine = _local_dictation_engine(str(terms.get("runtime_backend", "") or ""))
    if engine == "mlx":
        artifact = str(terms.get("runtime_mlx_model", "") or "").strip()
    elif engine == "llama_cpp":
        artifact = str(terms.get("runtime_llama_cpp_model_path", "") or "").strip()
    else:
        artifact = ""
    if not artifact:
        return None
    # The receipt name. A GGUF file drops its extension; an MLX model is a
    # DIRECTORY or repo id whose leaf carries dots ("Qwen3.5-8B-MLX-4bit"), so
    # `.stem` would truncate it to "Qwen3" and name a model that does not exist.
    leaf = Path(artifact)
    return DeploymentIdentity(
        destination_id=DICTATION_DESTINATION_ID,
        kind=DICTATION_KIND,
        engine=engine,
        model=leaf.stem if engine == "llama_cpp" else leaf.name,
        node="",
        boundary=DICTATION_BOUNDARY,
        model_path=artifact,
        endpoint="",
        secret_slot="",
    )


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
        # HS-131-15: the LOCAL artifacts a provider-backed run would actually
        # load. They were missing from the hash, so swapping the configured
        # dictation model between admission and construction changed WHICH model
        # ran while `config_revision` — the thing the receipt names — stayed
        # identical. A local retarget must be visible in the plan.
        "runtime_mlx_model": str(getattr(runtime, "mlx_model", "") or ""),
        "runtime_llama_cpp_model_path": str(
            getattr(runtime, "llama_cpp_model_path", "") or ""
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


def configured_pipeline_egress_boundary(
    config_snapshot: Any, registry_snapshot: Any
) -> str:
    """The prospective decision-point egress for one configuration snapshot.

    This is the browser's BEFORE-ACTION disclosure, not execution proof. It uses
    the same capability derivation and placement resolver as admission but does
    not capture a deployment revision or mint a parent. The dry-run response later
    carries the boundary from the actual frozen plan, which is authoritative.
    ``""`` means the configured provider leg cannot currently resolve.
    """
    from ..inference_targets import resolve_placement
    from ..intel.providers import EGRESS_LOCAL, egress_boundary

    terms = _pipeline_terms(config_snapshot)
    if not _pipeline_capabilities(terms):
        return EGRESS_LOCAL
    profile_id = str(terms.get("runtime_profile_id", "") or "").strip()
    try:
        if profile_id:
            target = resolve_placement(
                registry_snapshot, invocation=profile_id
            ).target
            deployment = None if target is None else target.deployment
        else:
            deployment = dictation_local_deployment_identity(terms)
        if deployment is None:
            return ""
        endpoint = str(getattr(deployment, "endpoint", "") or "")
        node = str(getattr(deployment, "node", "") or "")
        return str(
            egress_boundary(cloud=bool(endpoint), base_url=endpoint, node=node)
        )
    except Exception:
        return ""


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
        plan_defaults: bool = True,
        insertion_context: str = "",
        created_at: Optional[float] = None,
    ) -> SpeechSessionPlan:
        from ..deployment_revisions import capture_deployment_revision

        if principal is None or str(getattr(principal, "name", "none")) == "none":
            raise SpeechSessionRefused(PRINCIPAL_REQUIRED)

        model_terms = _model_terms(getattr(config_snapshot, "model", None))
        pipeline_terms = _pipeline_terms(config_snapshot)

        declared = list(dict.fromkeys(str(name) for name in capabilities if str(name).strip()))
        # ``plan_defaults=False`` (HS-131-15) is how a SYNTHETIC-TEXT entry says
        # "these capabilities and no others". Without it an empty request fell
        # through to the capture defaults, and a browser rehearsal or a CLI
        # dry-run would have planned Whisper transcription and preload it can
        # never legitimately use.
        if not declared and plan_defaults:
            declared = [CAPABILITY_WHISPER_TRANSCRIBE, CAPABILITY_WHISPER_PRELOAD]
            declared.extend(_pipeline_capabilities(pipeline_terms))

        frozen: dict[str, tuple[str, ...]] = {}
        unresolved: list[str] = []
        deployments: dict[str, Any] = {}
        whisper = None
        if any(
            name in (CAPABILITY_WHISPER_TRANSCRIBE, CAPABILITY_WHISPER_PRELOAD)
            for name in declared
        ):
            # Synthetic-text entries declare no Whisper capability, so they do not
            # upsert an unused deployment revision on every preview/replay/CLI run.
            whisper = capture_deployment_revision(
                registry_snapshot,
                whisper_deployment_identity(getattr(config_snapshot, "model", None)),
            )
            deployments[whisper.id] = whisper
        provider_legs: tuple[Any, ...] | None = None
        for name in declared:
            if name in (CAPABILITY_WHISPER_TRANSCRIBE, CAPABILITY_WHISPER_PRELOAD):
                assert whisper is not None
                frozen[name] = (whisper.id,)
                continue
            if provider_legs is None:
                provider_legs = self._provider_legs(registry_snapshot, pipeline_terms)
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
    def _provider_legs(
        registry_snapshot: Any, terms: Mapping[str, Any]
    ) -> tuple[Any, ...]:
        """The ordered dictation-LLM legs, resolved ONCE at session opening.

        A runtime profile pointer means the profiles table decides. WITHOUT one,
        the dictation leg runs on THIS device's configured DICTATION artifact, so
        that is what the plan freezes.

        HS-131-15: a blank pointer used to fall through to ``resolve_placement``'s
        global default, which resolves the MEETING-intel ``this_machine``
        destination. The session therefore froze ``meeting.intel_realtime_model``
        for a dictation stage — a model dictation never loads — and, because that
        revision carries the generic ``configured_local_engine``,
        ``_try_build_runtime`` found no frozen artifact to bind to and kept
        reading mutable config. Editing ``dictation.runtime`` after admission
        silently retargeted construction and warm-on-start while the plan hash and
        the receipt still named the meeting dial.
        """
        from ..deployment_revisions import capture_deployment_revision
        from ..inference_targets import resolve_placement

        profile_id = str(terms.get("runtime_profile_id", "") or "").strip()
        try:
            if not profile_id:
                identity = dictation_local_deployment_identity(terms)
                if identity is None:
                    return ()
                return (capture_deployment_revision(registry_snapshot, identity),)
            resolution = resolve_placement(registry_snapshot, invocation=profile_id)
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
    "CLI_CREDENTIAL_REQUIRED",
    "CONTRACT_INTENT_CLASSIFY",
    "CONTRACT_PUNCTUATE",
    "CONTRACT_REWRITE",
    "CONTRACT_WHISPER_PRELOAD",
    "CONTRACT_WHISPER_TRANSCRIBE",
    "DICTATION_BOUNDARY",
    "DICTATION_DESTINATION_ID",
    "DICTATION_KIND",
    "DictationSessionPlanResolver",
    "LocalWhisperDeployment",
    "configured_pipeline_egress_boundary",
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
    "dictation_local_deployment_identity",
    "pipeline_provider_capabilities",
    "sha",
    "text_sha",
    "whisper_deployment_identity",
]
