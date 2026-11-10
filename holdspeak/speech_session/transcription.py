"""One Whisper transcription or MLX warm through the engine door (HS-131-09).

``Transcriber`` never talks to the kernel directly: it receives a
:class:`TranscriptionAdmission`, and every nonempty transcription or MLX warm
runs as ONE door job (``speech.transcribe`` / ``speech.preload``): a child of the
live session, or, for the boot warm, a job of the preload service. Audio is
DISPATCH-ONLY: the receipt carries the SHA-256 and safe counts, never samples.

Which engine: the admission asks the door's ``speech.transcribe`` chain once, at
its first need, and keeps that answer for the one utterance it serves. A session
makes a new admission for each utterance (``SpeechSession.transcription``), so a
chain change in Settings › Engines is honoured on the session's next call. The
door's retry on the next engine is off here: the model that runs is the one the
``Transcriber`` holds, and a retry on another revision would name a model that
did not run.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import uuid
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Callable, ClassVar, Mapping, Optional

from .child import SpeechProviderFailure
from .plan import (
    CONTRACT_WHISPER_PRELOAD,
    CONTRACT_WHISPER_TRANSCRIBE,
    SESSION_NOT_LIVE,
    SpeechSessionRefused,
)

TRANSCRIBE_DEADLINE_SECONDS = 300.0
PRELOAD_DEADLINE_SECONDS = 900.0
#: The transcription job and the warm job (its receipt name).
TRANSCRIBE_JOB = "speech.transcribe"
PRELOAD_JOB = "speech.preload"
#: When a warm stops walking its candidates.
_STOP_RULES = ("success", "cancellation", "refusal", "deadline", "indeterminate", "exhaustion")


def audio_sha256(audio: Any) -> str:
    """The content address of exactly the samples this dispatch will see."""
    try:
        raw = audio.tobytes()
    except AttributeError:
        raw = bytes(audio)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class SpeechEngine:
    """The first engine of the ``speech.transcribe`` chain and what a
    ``Transcriber`` needs to build and warm it."""

    engine: Any
    backend: str
    model: str
    language: str
    candidate_ids: tuple[str, ...]
    strategy_sequence: tuple[str, ...]

    @property
    def deployment_revision_id(self) -> str:
        return str(self.engine.revision)

    def transcriber_arguments(self) -> dict[str, str]:
        return {
            "model_name": self.model,
            "backend": self.backend,
            "language": self.language,
            "deployment_revision_id": self.deployment_revision_id,
        }

    def preload_material(self) -> dict[str, Any]:
        return {
            "engine": self.backend,
            "model": self.model,
            "language": self.language,
            "candidate_ids": list(self.candidate_ids),
            "strategy_sequence": list(self.strategy_sequence),
            "stop_rules": list(_STOP_RULES),
        }


def speech_engine(broker: Any) -> SpeechEngine:
    """Ask the door's ``speech.transcribe`` chain now. Raises
    ``SpeechSessionRefused('no_engine')`` when no engine is assigned."""
    from dataclasses import replace

    from ..services import engine_door

    try:
        engine = engine_door.engine_for(broker, TRANSCRIBE_JOB)
    except engine_door.EngineDoorError:
        raise SpeechSessionRefused("no_engine", TRANSCRIBE_JOB) from None
    engine = replace(engine, fallback=None)
    with broker.database._connection() as conn:
        deployment = conn.execute(
            "SELECT engine,model FROM deployment_revisions WHERE id=?", (engine.revision,)
        ).fetchone()
        manifest = conn.execute(
            """SELECT p.capability_manifest_json FROM model_profile_binding_heads h
                 JOIN model_profile_binding_revisions b
                   ON b.binding_id=h.binding_id AND b.revision=h.revision
                 JOIN model_profile_revisions p
                   ON p.profile_id=b.profile_id AND p.revision=b.profile_revision
                WHERE h.profile_id=?""",
            (engine.profile,),
        ).fetchone()
    if deployment is None:
        raise SpeechSessionRefused("no_engine", TRANSCRIBE_JOB)
    backend = str(deployment["engine"] or "")
    if backend not in {"mlx", "faster-whisper"}:
        # The Transcriber runs local Whisper only: an assignment that names a
        # mesh or network engine (a saved selection from before the
        # local-only rule) refuses before any parent or construction.
        raise SpeechSessionRefused("inference_route_boundary_unsupported", TRANSCRIBE_JOB)
    identity = str(deployment["model"] or "")
    model = identity.removeprefix(f"builtin-whisper-{backend}-")
    language = "auto"
    try:
        claims = json.loads(str(manifest["capability_manifest_json"]))["claims"] if manifest else []
        language = next(
            (str(item).removeprefix("speech_language:") for item in claims
             if str(item).startswith("speech_language:")),
            "auto",
        )
    except (KeyError, TypeError, ValueError):
        pass
    if backend == "mlx":
        from ..transcribe import _model_repo_candidates

        candidates, strategies = tuple(_model_repo_candidates(model)), ("model-holder", "silent-audio")
    else:
        # Faster-whisper loads in its constructor: there is no separate warm.
        candidates, strategies = (identity,), ("constructor",)
    return SpeechEngine(engine, backend, model, language, candidates, strategies)


class _WhisperAdapter:
    """The door adapter for one local Whisper call: the loaded ``Transcriber``
    does the work; the runner's engine for the revision is an inert handle."""

    connector_id = "inference-provider"

    def __init__(self, contract: str, call: Callable[[Any], Any]) -> None:
        self._contract = contract
        self._call = call

    def dispatch(self, engine: Any, payload: Mapping[str, Any], cancellation: Any) -> Any:
        from ..kernel.model import KernelRefused
        from ..kernel.provider_signals import CONTROL_SIGNALS

        try:
            return self._call(cancellation)
        except CONTROL_SIGNALS:
            raise
        except KernelRefused:
            raise
        except SpeechSessionRefused as exc:
            raise KernelRefused(exc.reason) from None
        except BaseException as exc:  # sanitized: no backend text crosses this line
            raise SpeechProviderFailure(self._contract, exc) from None

    def cancel(self) -> str:
        return "cancelled"


@dataclass
class TranscriptionAdmission:
    """One utterance's speech work, a child of its live session through the door.

    ``parent`` is the live session parent (a ``dictation.session`` or
    ``wake.session``), or ``None`` for the boot warm, which runs as the preload
    service.
    """

    broker: Any
    principal: Any
    parent: Any = None
    fence: Any = None
    #: Distinguishes utterances WITHIN one session (a browser interval can hear
    #: the same words twice).
    utterance_ref: str = ""
    #: Sol Amendment 8: runs inside the first transcription child, before the
    #: model runs (the browser interval's lease refresh). A refusal here is a
    #: refused child: no model sees the audio, and the named reason is raised.
    on_claim: Any = None
    claims: list[str] = field(default_factory=list)
    claim_refusals: list[Any] = field(default_factory=list)
    last_preload_receipt: Any = None
    _speech: Optional[SpeechEngine] = None
    _nonce: str = field(default_factory=lambda: uuid.uuid4().hex)
    #: One warm walks the engine's candidate sequence as one job.
    single_preload_sequence: ClassVar[bool] = True

    @property
    def outer_context(self) -> Any:
        return None if self.parent is None else self.parent.context

    def speech(self) -> SpeechEngine:
        """The ``speech.transcribe`` engine, asked once for this utterance."""
        if self._speech is None:
            self._speech = speech_engine(self.broker)
        return self._speech

    def _refuse_if_fenced(self, job: str) -> None:
        if self.fence is not None and (reason := self.fence.reason()):
            raise SpeechSessionRefused(reason, job)

    def _run(
        self, job: str, contract: str, material: Mapping[str, Any], call: Callable[[Any], Any],
        seed: Any, deadline: float,
    ) -> tuple[Any, Any]:
        from ..kernel.model import KernelRefused
        from ..services import engine_door

        self._refuse_if_fenced(job)
        speech = self.speech()
        payload = {"payload_schema": 1, "capability": job,
                   "deployment_revision": speech.deployment_revision_id, **dict(material)}
        run_id = "speech_" + hashlib.sha256(
            json.dumps([self._nonce, self.utterance_ref, job, str(seed)]).encode()
        ).hexdigest()[:32]
        try:
            answer = engine_door.run(
                self.broker, self.principal, job, payload, engine=speech.engine, contract=contract,
                adapter=_WhisperAdapter(contract, call), invocation_id=run_id,
                parent_context=self.outer_context, deadline=float(deadline),
            )
        except KernelRefused as exc:
            raise SpeechSessionRefused(exc.reason or SESSION_NOT_LIVE, job) from None
        except engine_door.EngineDoorError as exc:
            if self.claim_refusals:
                raise self.claim_refusals[0] from None
            if exc.outcome == "refused":
                raise SpeechSessionRefused(exc.error or exc.outcome, job) from None
            receipt = {"operation_id": exc.operation_id, "outcome": exc.outcome or "failed"}
            return SimpleNamespace(outcome=receipt["outcome"], receipt=receipt,
                                   operation_id=exc.operation_id), None
        receipt = {"operation_id": answer.operation_id, "outcome": "succeeded"}
        try:
            engine_door.record_ready(self.broker.database, speech.deployment_revision_id,
                                     "loaded_under_speech_preload")
        except Exception:  # no binding: nothing to record
            pass
        return SimpleNamespace(outcome="succeeded", receipt=receipt,
                               operation_id=answer.operation_id), answer.result

    # ------------------------------------------------------------ transcribe

    def transcribe_child(
        self, *, material: Mapping[str, Any], run: Callable[[], str], seed: Any, **_kwargs: Any,
    ) -> tuple[Any, Any]:
        """ONE transcription job; returns ``(outcome, text)``."""
        from ..kernel.model import KernelRefused
        from ..kernel.provider_signals import ProviderIndeterminate
        from ..transcribe import TranscriberTimeoutError

        def call(cancellation: Any) -> dict[str, Any]:
            if cancellation is not None and cancellation.is_set():
                raise KernelRefused("speech_transcription_not_admitted")
            if self.on_claim is not None and not self.claims:
                self.claims.append(str(material.get("audio_sha256") or ""))
                try:
                    self.on_claim()
                except SpeechSessionRefused as refusal:
                    self.claim_refusals.append(refusal)
                    raise KernelRefused(refusal.reason) from None
            try:
                return {"text": run()}
            except TranscriberTimeoutError as exc:
                # A timed native worker can outlive the caller: its end is unknown.
                raise ProviderIndeterminate() from exc

        outcome, result = self._run(TRANSCRIBE_JOB, CONTRACT_WHISPER_TRANSCRIBE, material, call,
                                    seed, TRANSCRIBE_DEADLINE_SECONDS)
        return outcome, (result.get("text") if isinstance(result, Mapping) else None)

    # -------------------------------------------------------------- the warm

    def frozen_preload_material(self) -> Mapping[str, Any]:
        """What the warm walks: the engine's model, language and candidates."""
        return self.speech().preload_material()

    def loaded_artifact_reusable(self, impl: Any) -> bool:
        """A loaded model serves this call when it was warmed for the same
        engine (revision, backend, model, language) and its warm succeeded."""
        provenance = getattr(impl, "_holdspeak_preload_provenance", None)
        if not isinstance(provenance, Mapping):
            return False
        speech = self.speech()
        if (
            str(provenance.get("deployment_revision_id") or "") != speech.deployment_revision_id
            or str(provenance.get("engine") or "") != speech.backend
            or str(provenance.get("model") or "") != speech.model
            or str(provenance.get("language") or "auto") != str(speech.language or "auto")
        ):
            return False
        operation_id = str(provenance.get("operation_id") or "")
        if not operation_id:
            return False
        receipt = self.broker.store.receipt(operation_id)
        return receipt is not None and str(receipt["outcome"]) == "succeeded"

    def record_loaded_artifact(self, impl: Any, receipt: Mapping[str, Any]) -> None:
        if str(receipt.get("outcome") or "") != "succeeded":
            return
        speech = self.speech()
        impl._holdspeak_preload_provenance = {
            "deployment_revision_id": speech.deployment_revision_id,
            "engine": speech.backend,
            "model": speech.model,
            "language": speech.language,
            "operation_id": str(receipt.get("operation_id") or ""),
        }

    def preload_sequence(self, *, material: Mapping[str, Any], run: Callable[..., Any]) -> tuple[Any, Any]:
        """ONE warm job: the loader walks the engine's candidates in order."""
        if dict(material) != dict(self.frozen_preload_material()):
            raise SpeechSessionRefused("speech_preload_sequence_mismatched", PRELOAD_JOB)

        def call(cancellation: Any) -> dict[str, str]:
            from ..kernel.model import KernelRefused

            if cancellation is not None and cancellation.is_set():
                raise KernelRefused("speech_preload_cancelled")
            value = run(cancellation) if inspect.signature(run).parameters else run()
            return {"state": str(value or "loaded")}

        outcome, result = self._run(PRELOAD_JOB, CONTRACT_WHISPER_PRELOAD,
                                    {"stage": "sequence", **dict(material)}, call,
                                    "preload", PRELOAD_DEADLINE_SECONDS)
        self.last_preload_receipt = outcome.receipt
        return outcome, result

    def preload_child(self, **_kwargs: Any) -> tuple[Any, Any]:
        """One warm is one job (``preload_sequence``); a per-candidate child is refused."""
        raise SpeechSessionRefused("speech_preload_not_admitted", PRELOAD_JOB)


__all__ = [
    "PRELOAD_DEADLINE_SECONDS",
    "SpeechEngine",
    "SpeechProviderFailure",
    "TRANSCRIBE_DEADLINE_SECONDS",
    "TranscriptionAdmission",
    "audio_sha256",
    "speech_engine",
]
