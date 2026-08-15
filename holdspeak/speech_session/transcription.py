"""The admission handle one local Whisper dispatch runs under (HS-131-09).

``Transcriber`` never talks to the kernel directly: it receives one of these,
and every nonempty transcription or MLX preload dispatch becomes one admitted
``inference.invoke@1`` child with a terminal receipt. Audio is DISPATCH-ONLY —
the child's journal row carries the SHA-256 and safe counts, never samples.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
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


__all__ = [
    "PRELOAD_DEADLINE_SECONDS",
    "SpeechProviderFailure",
    "TRANSCRIBE_DEADLINE_SECONDS",
    "TranscriptionAdmission",
    "audio_sha256",
]
