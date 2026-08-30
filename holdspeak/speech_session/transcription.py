"""The admission handle one local Whisper dispatch runs under (HS-131-09).

``Transcriber`` never talks to the kernel directly: it receives one of these,
and every nonempty transcription or MLX preload dispatch becomes one admitted
``inference.invoke@1`` child with a terminal receipt. Audio is DISPATCH-ONLY —
the child's journal row carries the SHA-256 and safe counts, never samples.
"""

from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Callable, Mapping, Optional

from .child import (
    SpeechProviderFailure,
    run_admitted_speech_capability,
    run_admitted_speech_child,
)
from .plan import (
    CAPABILITY_WHISPER_PRELOAD,
    CAPABILITY_WHISPER_TRANSCRIBE,
    CONTRACT_WHISPER_PRELOAD,
    CONTRACT_WHISPER_TRANSCRIBE,
    SpeechSessionPlan,
    SpeechSessionRefused,
)

TRANSCRIBE_DEADLINE_SECONDS = 300.0
PRELOAD_DEADLINE_SECONDS = 900.0


def audio_sha256(audio: Any) -> str:
    """The content address of exactly the samples this dispatch will see."""
    try:
        raw = audio.tobytes()
    except AttributeError:
        raw = bytes(audio)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class TranscriptionAdmission:
    """One live (or explicitly authorized service) authority for model dispatch.

    ``parent`` is the live session parent — a ``dictation.session``,
    ``wake.session``, or the EXISTING ``meeting.session`` — or ``None`` for the
    authorized pre-session warm, which has no session to parent it.
    """

    broker: Any
    principal: Any
    plan: SpeechSessionPlan
    parent: Any = None
    fence: Any = None
    capability: str = CAPABILITY_WHISPER_TRANSCRIBE
    preload_capability: str = CAPABILITY_WHISPER_PRELOAD
    #: Every preload child this admission has run, in order (stage, outcome).
    preloads: list[tuple[str, str]] = field(default_factory=list)
    #: Sol Amendment 8: run INSIDE the first Whisper child claim of this
    #: utterance, before the model dispatch and after the kernel validated the
    #: parent — the browser inactivity lease refresh rides here and costs zero
    #: extra round trips. Never invoked for empty audio (no child exists) and
    #: never for a preload child.
    on_claim: Any = None
    #: One entry per time ``on_claim`` actually fired.
    claims: list[str] = field(default_factory=list)
    #: The refusal an ``on_claim`` hook raised, if any. A hook that refuses (the
    #: browser lease having ALREADY lapsed at claim time) turns the child into a
    #: kernel refusal — no model runs — and the named reason is re-raised to the
    #: caller instead of being laundered into an anonymous transcription failure.
    claim_refusals: list[Any] = field(default_factory=list)
    #: Distinguishes utterances WITHIN one session. A browser interval can hear
    #: the same words twice (or the same silence), and two dispatches must never
    #: collide on one invocation identity — the second would be refused as a
    #: replay of the first.
    utterance_ref: str = ""

    def loaded_artifact_reusable(self, impl: Any) -> bool:
        """Within a legacy session, a loaded model is always reusable.

        The routed admission cross-validates the deployment revision and
        provenance; the legacy admission has no route bundles, so a model
        loaded under THIS session's preload children is reusable for all
        remaining windows.  Without this, ``ensure_loaded`` re-runs the
        preload for every transcription window and the kernel refuses the
        second attempt as ``idempotency_payload_mismatch`` (HS-151-03).
        """
        return any(outcome == "succeeded" for _, outcome in self.preloads)

    @property
    def outer_context(self) -> Any:
        return None if self.parent is None else self.parent.context

    @property
    def session_id(self) -> str:
        return self.plan.session_id

    def revision(self, capability: str = "") -> str:
        return self.plan.primary(capability or self.capability)

    def _refuse_if_fenced(self, capability: str) -> None:
        if self.fence is None:
            return
        reason = self.fence.reason()
        if reason:
            # Preserve the speech carrier's fixed, content-free durable reason.
            # Letting the child runner rediscover a dead parent would collapse an
            # exact revocation/expiry into generic ``parent_operation_not_live``.
            raise SpeechSessionRefused(reason, capability)

    # ------------------------------------------------------------ transcribe

    def transcribe_child(
        self,
        *,
        material: Mapping[str, Any],
        run: Callable[[], str],
        seed: Any,
        attempt_ordinal: int = 1,
        deadline_seconds: float = TRANSCRIBE_DEADLINE_SECONDS,
    ) -> tuple[Any, Any]:
        """ONE admitted transcription dispatch, walking the frozen entries."""

        self._refuse_if_fenced(self.capability)

        def dispatch(engine: Any, payload: Mapping[str, Any], cancellation: Any) -> str:
            # Inside the claim: the kernel has already revalidated the parent's
            # liveness, authority, epoch, and budget for THIS child.
            if self.on_claim is not None and not self.claims:
                self.claims.append(str(payload.get("audio_sha256") or ""))
                try:
                    self.on_claim()
                except SpeechSessionRefused as refusal:
                    from ..kernel.model import KernelRefused

                    self.claim_refusals.append(refusal)
                    # A refusal inside the claim is a REFUSED child, not a failed
                    # one, and `run()` is never reached: no model sees this audio.
                    raise KernelRefused(refusal.reason) from None
            return run()

        outcome = run_admitted_speech_capability(
            broker=self.broker,
            principal=self.principal,
            plan=self.plan,
            parent=self.parent,
            capability=self.capability,
            contract=CONTRACT_WHISPER_TRANSCRIBE,
            material=dict(material),
            call=dispatch,
            seed=(self.utterance_ref, seed) if self.utterance_ref else seed,
            attempt_ordinal=int(attempt_ordinal),
            deadline_seconds=float(deadline_seconds),
        )
        if self.claim_refusals:
            raise self.claim_refusals[0]
        return outcome

    # -------------------------------------------------------------- preload

    def preload_child(
        self,
        *,
        stage: str,
        material: Mapping[str, Any],
        run: Callable[[], Any],
        attempt_ordinal: int,
        deadline_seconds: float = PRELOAD_DEADLINE_SECONDS,
    ) -> tuple[Any, Any]:
        """ONE admitted preload dispatch — a SIBLING child, never a nested one.

        Sol Amendment 7: the explicit ``ModelHolder.get_model`` attempt and the
        silent-audio fallback are separate children, each completed BEFORE the
        ordinary transcription child. This never reacquires the caller's
        transcription lock: it holds no lock of its own.
        """
        self._refuse_if_fenced(self.preload_capability)
        outcome, result = run_admitted_speech_child(
            broker=self.broker,
            principal=self.principal,
            plan=self.plan,
            parent=self.parent,
            capability=self.preload_capability,
            contract=CONTRACT_WHISPER_PRELOAD,
            material={"preload_stage": str(stage), **dict(material)},
            call=lambda engine, payload, cancellation: run(),
            seed=(str(stage), material.get("model_repo", "")),
            attempt_ordinal=int(attempt_ordinal),
            deadline_seconds=float(deadline_seconds),
        )
        self.preloads.append((str(stage), str(outcome.outcome)))
        return outcome, result


@dataclass
class RoutedSpeechTranscriptionAdmission:
    """One Phase-D speech child on its parent's immutable bundle member.

    This is deliberately the same controller-owned waist as Phase-B Meeting
    transcription.  It carries no v1 plan and does not resolve a route after the
    parent exists: the bundle's transcription member is its complete authority.
    """

    broker: Any
    principal: Any
    parent: Any
    bundle: Mapping[str, Any]
    fence: Any = None
    utterance_ref: str = ""
    on_claim: Any = None
    single_preload_sequence: bool = True

    def _member(self, capability_id: str) -> Mapping[str, Any] | None:
        return next(
            (
                item for item in self.bundle.get("members", ())
                if item.get("capability_id") == capability_id
            ),
            None,
        )

    def _operation_id(self, capability_id: str, material: Mapping[str, Any]) -> str:
        identity = {
            "parent_operation_id": str(self.parent.operation_id),
            "utterance_ref": self.utterance_ref,
            "capability": capability_id,
            "audio_sha256": str(material.get("audio_sha256") or ""),
            "lifecycle_material_sha256": hashlib.sha256(
                json.dumps(dict(material), sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        }
        digest = hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return f"speech-route:{self.parent.operation_id}:{capability_id}:{digest}"

    def _refuse_if_fenced(self) -> None:
        if self.fence is not None and (reason := self.fence.reason()):
            raise SpeechSessionRefused(reason)

    def _execute(
        self,
        *,
        capability_id: str,
        material: Mapping[str, Any],
        call: Callable[[Any, Mapping[str, Any], Any], Any],
        reserved_output_tokens: int,
    ) -> Mapping[str, Any]:
        self._refuse_if_fenced()
        member = self._member(capability_id)
        if member is None:
            raise SpeechSessionRefused("speech_route_member_missing", capability_id)
        operation_id = self._operation_id(capability_id, material)
        coordinator = self.broker.inference_adoption_service
        admitted = coordinator.admit_on_frozen_route(
            self.principal,
            command_id="speech-route-operation:" + operation_id,
            route_plan_id=str(member["route_plan_id"]),
            capability_id=capability_id,
            operation_id=operation_id,
            payload=dict(material),
            reserved_output_tokens=int(reserved_output_tokens),
            parent_operation_id=(
                str(self.parent.operation_id)
                if str(getattr(getattr(self.principal, "kind", ""), "value", self.principal.kind))
                == "service"
                else None
            ),
        )
        from ..services.inference_semantic_adapters import adapter_for

        return coordinator.execute(
            self.principal,
            execution_id=str(admitted["execution"]["id"]),
            adapter=adapter_for(capability_id, call),
            parent_context=self.parent.context,
        )

    def transcribe_child(
        self,
        *,
        material: Mapping[str, Any],
        run: Callable[[], str],
        seed: Any,
        **_kwargs: Any,
    ) -> tuple[Any, Any]:
        """Run one actual-byte transcription with controller-owned outcomes."""
        del seed
        from ..kernel.model import KernelRefused
        from ..kernel.provider_signals import ProviderIndeterminate
        from ..transcribe import TranscriberTimeoutError

        def call(_engine: Any, _payload: Mapping[str, Any], cancellation: Any) -> str:
            if cancellation.is_set():
                raise KernelRefused("speech_transcription_not_admitted")
            if self.on_claim is not None:
                try:
                    self.on_claim()
                except SpeechSessionRefused as refusal:
                    raise KernelRefused(refusal.reason) from None
            try:
                return run()
            except TranscriberTimeoutError as exc:
                # A timed native worker can survive the caller.  Its physical
                # disposition is unknown, so the controller must terminalize and
                # never advance to another route leg.
                raise ProviderIndeterminate() from exc

        routed = self._execute(
            capability_id="speech.transcribe",
            material=material,
            call=call,
            reserved_output_tokens=64,
        )
        state = str(routed["outcome"])
        if state == "refused":
            raise SpeechSessionRefused(
                str(routed["receipt"].get("terminal_disposition") or state),
                "speech.transcribe",
            )
        result = routed.get("result")
        return SimpleNamespace(outcome=state, receipt=routed.get("receipt")), (
            None if not isinstance(result, Mapping) else result.get("text")
        )

    def preload_child(self, **_kwargs: Any) -> tuple[Any, Any]:
        """Refuse an unbound legacy preload leg before it can dispatch."""
        raise SpeechSessionRefused("speech_preload_not_admitted", "speech.preload")

    def _preload_evidence(self) -> Mapping[str, Any]:
        transcription = self._member("speech.transcribe")
        preload = self._member("speech.preload")
        evidence = next(
            (
                item for item in self.bundle.get("derived_preloads", ())
                if transcription is not None
                and preload is not None
                and item.get("transcription_route_plan_id") == transcription.get("route_plan_id")
                and item.get("preload_route_plan_id") == preload.get("route_plan_id")
            ),
            None,
        )
        if not isinstance(evidence, Mapping):
            raise SpeechSessionRefused("speech_preload_evidence_missing", "speech.preload")
        return evidence

    def frozen_preload_material(self) -> Mapping[str, Any]:
        evidence = self._preload_evidence()
        return {
            "engine": str(evidence["engine"]),
            "model": str(evidence["model"]),
            "language": str(evidence["language"]),
            "candidate_ids": [str(item["id"]) for item in evidence["candidate_material"]],
            "strategy_sequence": [str(item) for item in evidence["strategy_sequence"]],
            "stop_rules": [str(item) for item in evidence["stop_rules"]],
        }

    def loaded_artifact_reusable(self, impl: Any) -> bool:
        evidence = self._preload_evidence()
        material = self.frozen_preload_material()
        return _durable_preload_provenance_matches(
            self.broker,
            getattr(impl, "_holdspeak_preload_provenance", {}),
            deployment_revision_id=str(evidence["deployment_revision_id"]),
            engine=material["engine"],
            model=material["model"],
            language=material["language"],
        )

    def record_loaded_artifact(self, impl: Any, receipt: Mapping[str, Any]) -> None:
        if str(receipt.get("outcome") or "") != "succeeded":
            return
        evidence = self._preload_evidence()
        preload = self._member("speech.preload")
        if preload is None:
            return
        impl._holdspeak_preload_provenance = {
            "deployment_revision_id": str(evidence["deployment_revision_id"]),
            "engine": str(evidence["engine"]),
            "model": str(evidence["model"]),
            "language": str(evidence["language"]),
            "execution_id": str(receipt.get("execution_id") or ""),
            "route_plan_id": str(preload["route_plan_id"]),
        }

    def preload_sequence(
        self, *, material: Mapping[str, Any], run: Callable[..., Any]
    ) -> tuple[Any, Any]:
        """Execute the one P=1 frozen MLX lifecycle sequence.

        Candidate/stage discovery is prohibited after admission.  The physical
        walker receives cancellation and may advance only within the immutable
        evidence sequence it was constructed from.
        """
        evidence = self._preload_evidence()
        expected = self.frozen_preload_material()
        if dict(material) != expected:
            raise SpeechSessionRefused("speech_preload_sequence_mismatched", "speech.preload")

        def call(_engine: Any, _payload: Mapping[str, Any], cancellation: Any) -> Mapping[str, str]:
            if cancellation.is_set():
                from ..kernel.model import KernelRefused

                raise KernelRefused("speech_preload_cancelled")
            value = run(cancellation) if inspect.signature(run).parameters else run()
            return {"state": str(value or "loaded")}

        routed = self._execute(
            capability_id="speech.preload",
            material={"stage": "frozen-sequence", **dict(material)},
            call=call,
            reserved_output_tokens=16,
        )
        state = str(routed["outcome"])
        principal_name = str(
            getattr(getattr(self.principal, "name", ""), "value", getattr(self.principal, "name", ""))
        )
        if state == "succeeded" and principal_name == "owner":
            self.broker.inference_adoption_service.record_local_speech_readiness_after_load(
                self.principal,
                deployment_revision_id=str(evidence["deployment_revision_id"]),
            )
        self.last_preload_receipt = routed.get("receipt")
        return SimpleNamespace(outcome=state, receipt=routed.get("receipt")), routed.get("result")


@dataclass
class ParentlessPreloadAdmission:
    """One derived, parentless MLX lifecycle route.

    A pre-session warm has no capture parent, but it is not ambient process
    authority: ``source_route`` is the exact frozen owner-visible transcription
    assignment and ``preload_route`` is the closed SERVICE-derived member.
    """

    broker: Any
    principal: Any
    source_route: Mapping[str, Any]
    preload_route: Mapping[str, Any]
    evidence: Mapping[str, Any]
    single_preload_sequence: bool = True

    def frozen_preload_material(self) -> Mapping[str, Any]:
        return {
            "engine": str(self.evidence["engine"]),
            "model": str(self.evidence["model"]),
            "language": str(self.evidence["language"]),
            "candidate_ids": [str(item["id"]) for item in self.evidence["candidate_material"]],
            "strategy_sequence": [str(item) for item in self.evidence["strategy_sequence"]],
            "stop_rules": [str(item) for item in self.evidence["stop_rules"]],
        }

    def loaded_artifact_reusable(self, impl: Any) -> bool:
        provenance = getattr(impl, "_holdspeak_preload_provenance", None)
        if not isinstance(provenance, Mapping):
            return False
        expected = self.frozen_preload_material()
        return _durable_preload_provenance_matches(
            self.broker,
            provenance,
            deployment_revision_id=str(self.evidence["deployment_revision_id"]),
            engine=expected["engine"],
            model=expected["model"],
            language=expected["language"],
        )

    def record_loaded_artifact(self, impl: Any, receipt: Mapping[str, Any]) -> None:
        if str(receipt.get("outcome") or "") != "succeeded":
            return
        impl._holdspeak_preload_provenance = {
            "deployment_revision_id": str(self.evidence["deployment_revision_id"]),
            "engine": str(self.evidence["engine"]),
            "model": str(self.evidence["model"]),
            "language": str(self.evidence["language"]),
            "execution_id": str(receipt.get("execution_id") or ""),
            "route_plan_id": str(self.preload_route["id"]),
        }

    def preload_sequence(
        self, *, material: Mapping[str, Any], run: Callable[..., Any]
    ) -> tuple[Any, Any]:
        expected = self.frozen_preload_material()
        if dict(material) != expected:
            raise SpeechSessionRefused("speech_preload_sequence_mismatched", "speech.preload")

        def call(_engine: Any, _payload: Mapping[str, Any], cancellation: Any) -> Mapping[str, str]:
            if cancellation.is_set():
                from ..kernel.model import KernelRefused

                raise KernelRefused("speech_preload_cancelled")
            value = run(cancellation) if inspect.signature(run).parameters else run()
            return {"state": str(value or "loaded")}

        operation_id = "speech-preload:" + hashlib.sha256(
            json.dumps(
                {
                    "source_route_plan_id": self.source_route["id"],
                    "source_route_plan_sha256": self.source_route["sha256"],
                    "preload_route_plan_id": self.preload_route["id"],
                    "material": dict(material),
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        coordinator = self.broker.inference_adoption_service
        admitted = coordinator.admit_on_frozen_route(
            self.principal,
            command_id="speech-preload-operation:" + operation_id,
            route_plan_id=str(self.preload_route["id"]),
            capability_id="speech.preload",
            operation_id=operation_id,
            payload={"stage": "frozen-sequence", **dict(material)},
            reserved_output_tokens=16,
            parentless_source_route_plan_id=str(self.source_route["id"]),
        )
        from ..services.inference_semantic_adapters import adapter_for

        routed = coordinator.execute(
            self.principal,
            execution_id=str(admitted["execution"]["id"]),
            adapter=adapter_for("speech.preload", call),
        )
        receipt = routed.get("receipt")
        if not isinstance(receipt, Mapping):
            receipt = {}
        self.last_preload_receipt = receipt
        return SimpleNamespace(outcome=str(routed["outcome"]), receipt=receipt), routed.get("result")


def _durable_preload_provenance_matches(
    broker: Any,
    provenance: Mapping[str, Any],
    *,
    deployment_revision_id: str,
    engine: str,
    model: str,
    language: str,
) -> bool:
    """Require both exact construction identity and a durable successful receipt."""
    if (
        str(provenance.get("deployment_revision_id") or "") != deployment_revision_id
        or str(provenance.get("engine") or "") != engine
        or str(provenance.get("model") or "") != model
        or str(provenance.get("language") or "auto") != str(language or "auto")
    ):
        return False
    execution_id = str(provenance.get("execution_id") or "")
    route_plan_id = str(provenance.get("route_plan_id") or "")
    if not execution_id or not route_plan_id:
        return False
    with broker.database._connection() as conn:
        row = conn.execute(
            """SELECT e.terminal_outcome,e.winning_attempt_id,p.capability_id,
                      r.deployment_revision_id
                   FROM inference_route_executions e
                   JOIN inference_operation_route_request_plans o ON o.id=e.operation_plan_id
                   JOIN inference_route_plans p ON p.id=o.route_plan_id
                   JOIN inference_route_plan_entries r ON r.plan_id=p.id
                  WHERE e.id=? AND p.id=? AND r.route_leg_ordinal=1""",
            (execution_id, route_plan_id),
        ).fetchone()
    return bool(
        row is not None
        and str(row["terminal_outcome"] or "") == "succeeded"
        and str(row["winning_attempt_id"] or "")
        and str(row["capability_id"] or "") == "speech.preload"
        and str(row["deployment_revision_id"] or "") == deployment_revision_id
    )


__all__ = [
    "PRELOAD_DEADLINE_SECONDS",
    "ParentlessPreloadAdmission",
    "RoutedSpeechTranscriptionAdmission",
    "SpeechProviderFailure",
    "TRANSCRIBE_DEADLINE_SECONDS",
    "TranscriptionAdmission",
    "audio_sha256",
]
