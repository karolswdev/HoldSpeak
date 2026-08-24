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

    def preload_sequence(
        self, *, material: Mapping[str, Any], run: Callable[..., Any]
    ) -> tuple[Any, Any]:
        """Execute the one P=1 frozen MLX lifecycle sequence.

        Candidate/stage discovery is prohibited after admission.  The physical
        walker receives cancellation and may advance only within the immutable
        evidence sequence it was constructed from.
        """
        evidence = self._preload_evidence()
        candidates = [str(item["id"]) for item in evidence["candidate_material"]]
        strategies = [str(item) for item in evidence["strategy_sequence"]]
        if (
            list(material.get("candidate_ids") or ()) != candidates
            or list(material.get("strategy_sequence") or ()) != strategies
            or str(material.get("engine") or "") != str(evidence["engine"])
            or str(material.get("model") or "") != str(evidence["model"])
            or str(material.get("language") or "") != str(evidence["language"])
        ):
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
        return SimpleNamespace(outcome=state, receipt=routed.get("receipt")), routed.get("result")


__all__ = [
    "PRELOAD_DEADLINE_SECONDS",
    "RoutedSpeechTranscriptionAdmission",
    "SpeechProviderFailure",
    "TRANSCRIBE_DEADLINE_SECONDS",
    "TranscriptionAdmission",
    "audio_sha256",
]
