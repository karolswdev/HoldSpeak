"""Dictation provider stages through the engine door: classify, rewrite, punctuate (HS-131-09).

Every dictation-pipeline model call — the intent router's classify, the project
rewriter's passes, the model-assisted target detection, a provider-backed
punctuation stage — runs as ONE door job (``speech.intent_classify``,
``speech.rewrite``, ``speech.punctuate``), a trusted child of the live speech
session.

* **The door picks the engine at the moment of the call.** It reads the owner's
  live assignment chain (Settings › Engines); a change there is honoured on the
  next call of the same session. A stage the session does not hold refuses by
  name before any provider request exists.
* **Retry is never invisible.** The door's one retry on the next engine is its
  own child with its own receipt.

Prompt and transcript material ride ONLY inside the dispatched payload.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Mapping, Optional

from ..logging_config import get_logger
from .child import SpeechProviderFailure
from .plan import (
    CAPABILITY_INTENT_CLASSIFY,
    CAPABILITY_PUNCTUATE,
    CAPABILITY_REWRITE,
    CAPABILITY_WHISPER_TRANSCRIBE,
    CONTRACT_INTENT_CLASSIFY,
    CONTRACT_PUNCTUATE,
    CONTRACT_REWRITE,
    PROVIDER_CAPABILITIES,
    SESSION_NOT_LIVE,
    SpeechSessionRefused,
    door_egress,
    text_sha,
)

log = get_logger("speech_session")

PROVIDER_DEADLINE_SECONDS = 120.0

#: The named refusal a dispatch attempt raises when the session was fenced
#: (cancelled, expired, revoked, or closed) before it could reach a provider.
PROVIDER_FENCED = "speech_provider_fenced"


@dataclass
class ProviderAdmission:
    """The live authority one dictation pipeline run dispatches providers under."""

    broker: Any
    principal: Any
    plan: Any
    parent: Any
    fence: Any = None
    #: (capability, contract, outcome) per child this admission has run, in order.
    children: list[tuple[str, str, str]] = field(default_factory=list)

    # ------------------------------------------------------------------ plan

    def declares(self, capability: str) -> bool:
        return bool(self.plan is not None and self.plan.has(capability))

    def revision(self, capability: str) -> str:
        """The deployment revision the door's chain names for this stage now."""
        from ..services import engine_door

        try:
            return engine_door.engine_for(self.broker, self.plan.job(capability)).revision
        except engine_door.EngineDoorError:
            raise SpeechSessionRefused("no_engine", capability) from None

    def deployment(self, capability: str) -> Any:
        """The deployment revision object of this stage's engine now."""
        from ..deployment_revisions import resolve_deployment_revision

        revision = resolve_deployment_revision(self.broker.database, self.revision(capability))
        if revision is None:
            raise SpeechSessionRefused("deployment_revision_unknown", capability)
        return revision

    @property
    def egress_boundary(self) -> str:
        """Where this session's model work can go, read from the door's chains
        now: the widest of its transcription and provider stages."""
        stages = [name for name in (CAPABILITY_WHISPER_TRANSCRIBE, *PROVIDER_CAPABILITIES)
                  if self.declares(name)]
        return door_egress(self.broker.database, stages)

    # ----------------------------------------------------------- one child

    def child(
        self,
        *,
        capability: str,
        contract: str,
        material: Mapping[str, Any],
        deadline_seconds: float = PROVIDER_DEADLINE_SECONDS,
        **_kwargs: Any,
    ) -> tuple[Any, Any]:
        """Run ONE door job and return ``(outcome, result)``.

        Refuses by name — before any provider request exists — when the session
        does not hold the stage or is already fenced.
        """
        from ..kernel.model import KernelRefused
        from ..services import engine_door

        if self.fence is not None:
            reason = self.fence.reason()
            if reason:
                log.info("speech provider dispatch fenced: %s (%s)", reason, capability)
                raise SpeechSessionRefused(reason, capability)
        job = self.plan.job(capability)
        try:
            answer = engine_door.run(
                self.broker, self.principal, job, dict(material), contract=contract,
                adapter=_DoorSpeechAdapter(job),
                parent_context=self.parent.context, deadline=float(deadline_seconds),
            )
        except KernelRefused as exc:
            self.children.append((capability, contract, "refused"))
            raise SpeechSessionRefused(exc.reason or SESSION_NOT_LIVE, capability) from None
        except engine_door.EngineDoorError as exc:
            self.children.append((capability, contract, exc.outcome or exc.code))
            if exc.code == "no_engine" or exc.outcome == "refused":
                raise SpeechSessionRefused(exc.error or exc.outcome or exc.code, capability) from None
            raise SpeechProviderFailure(contract, reason=exc.outcome or "failed") from None
        self.children.append((capability, contract, "succeeded"))
        value = answer.result
        if job in {"speech.rewrite", "speech.punctuate"}:
            value = dict(value or {}).get("output", "")
        elif job == "speech.intent_classify":
            value = dict(value or {})
            value["extras"] = json.loads(str(value.pop("extras_json")))
        return SimpleNamespace(
            outcome="succeeded", receipt={"operation_id": answer.operation_id},
            operation_id=answer.operation_id,
        ), value

    # ------------------------------------------------------- the capabilities

    def classify(
        self,
        runtime: Any,
        prompt: str,
        schema: Any,
        *,
        max_tokens: int,
        temperature: float,
    ) -> dict[str, Any]:
        """ONE classify job."""
        material = {
            "prompt_sha256": text_sha(prompt),
            "prompt_chars": len(str(prompt)),
            "prompt_material": str(prompt),
            "block_ids": list(getattr(schema, "block_ids", ())),
            "extras_per_block": {
                str(key): list(value)
                for key, value in dict(getattr(schema, "extras_per_block", {}) or {}).items()
            },
            "schema_sha256": text_sha({
                "block_ids": list(getattr(schema, "block_ids", ())),
                "extras_per_block": dict(getattr(schema, "extras_per_block", {}) or {}),
            }),
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
            "backend": str(getattr(runtime, "backend", "") or ""),
        }
        _outcome, result = self.child(
            capability=CAPABILITY_INTENT_CLASSIFY, contract=CONTRACT_INTENT_CLASSIFY, material=material,
        )
        return dict(result or {})

    def rewrite(
        self, runtime: Any, prompt: str, *, max_tokens: int, temperature: float
    ) -> str:
        """ONE rewrite job."""
        material = {
            "prompt_sha256": text_sha(prompt),
            "prompt_chars": len(str(prompt)),
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
            "backend": str(getattr(runtime, "backend", "") or ""),
            "prompt_material": str(prompt),
        }
        _outcome, result = self.child(
            capability=CAPABILITY_REWRITE, contract=CONTRACT_REWRITE, material=material,
        )
        return "" if result is None else str(result)

    def punctuate(self, runtime: Any, prompt: str, *, max_tokens: int = 256) -> str:
        """ONE provider-backed punctuation job.

        Today's ``text_processor.process`` is lexical work and reaches no model,
        so no plan holds this stage and this seam refuses by name.
        """
        material = {
            "prompt_sha256": text_sha(prompt),
            "prompt_chars": len(str(prompt)),
            "max_tokens": int(max_tokens),
            "backend": str(getattr(runtime, "backend", "") or ""),
            "prompt_material": str(prompt),
        }
        _outcome, result = self.child(
            capability=CAPABILITY_PUNCTUATE, contract=CONTRACT_PUNCTUATE, material=material,
        )
        return "" if result is None else str(result)


class _DoorSpeechAdapter:
    """Execute and validate one speech stage on the engine the door picked."""

    connector_id = "inference-provider"

    def __init__(self, capability: str) -> None:
        self._capability = capability

    def dispatch(self, engine: Any, payload: dict[str, Any], cancellation: Any) -> Any:
        from ..inference_capabilities import InferenceCapabilityRegistryError, process_inference_capability_registry
        from ..kernel.dispatch_context import dispatch_context_of
        from ..kernel.model import KernelRefused
        from ..kernel.provider_signals import InferenceInvalidTypedOutput

        dispatch_context_of(engine)  # proves Runner built the selected revision
        try:
            if self._capability == "speech.intent_classify":
                allowed = [str(value) for value in payload["block_ids"]]
                raw_text = engine.run_prompt(
                    system_prompt=(
                        "Return JSON only with matched:boolean, block_id:string|null, "
                        "confidence:number, extras:object. block_id must be one of: "
                        + ", ".join(allowed)
                    ),
                    user_prompt=str(payload["prompt_material"]),
                    max_tokens=int(payload["max_tokens"]),
                    temperature=float(payload["temperature"]),
                )
                raw = json.loads(str(raw_text))
                if bool(raw.get("matched")) and str(raw.get("block_id") or "") not in allowed:
                    raise ValueError("invalid block")
            else:
                raw = engine.run_prompt(
                    system_prompt="Rewrite the supplied dictated text. Return only the rewritten text.",
                    user_prompt=str(payload["prompt_material"]),
                    max_tokens=int(payload["max_tokens"]),
                    temperature=float(payload.get("temperature") or 0.0),
                )
        except KernelRefused:
            raise
        except (AttributeError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            raise InferenceInvalidTypedOutput() from None
        result = raw
        if self._capability == "speech.intent_classify" and isinstance(raw, Mapping):
            result = {
                "matched": bool(raw.get("matched")),
                "block_id": raw.get("block_id") if isinstance(raw.get("block_id"), str) else None,
                "confidence": float(raw.get("confidence") or 0.0),
                "extras_json": json.dumps(
                    raw.get("extras") if isinstance(raw.get("extras"), Mapping) else {},
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            }
        if self._capability in {"speech.rewrite", "speech.punctuate"}:
            result = {
                "output": str(raw),
                "provider": str(getattr(engine, "active_provider", "") or ""),
                "model": str(getattr(engine, "active_model", "") or ""),
            }
        try:
            process_inference_capability_registry().require(self._capability).validate_result(result)
        except InferenceCapabilityRegistryError:
            raise InferenceInvalidTypedOutput() from None
        return result

    def cancel(self) -> str:
        return "not_supported"


class AdmittedDictationRuntime:
    """The ``LLMRuntime`` the dictation pipeline sees: every call is admitted.

    It is a thin decorator over the runtime the pipeline already built, so the
    intent router's two classify attempts, the rewriter's passes, and the
    model-assisted target detection each become their own admitted child WITHOUT
    any stage learning about the kernel. ``load``/``info`` reach no model and are
    passed through unchanged.
    """

    def __init__(self, inner: Any, admission: ProviderAdmission) -> None:
        self._inner = inner
        self._admission = admission

    @property
    def backend(self) -> str:
        return str(getattr(self._inner, "backend", ""))

    @property
    def admission(self) -> ProviderAdmission:
        return self._admission

    def load(self) -> None:
        loader = getattr(self._inner, "load", None)
        if callable(loader):
            loader()

    def info(self) -> dict[str, Any]:
        info = getattr(self._inner, "info", None)
        return dict(info()) if callable(info) else {}

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def classify(
        self,
        prompt: str,
        schema: Any,
        *,
        max_tokens: int = 128,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        return self._admission.classify(
            self._inner, prompt, schema, max_tokens=max_tokens, temperature=temperature
        )

    def rewrite(
        self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.15
    ) -> str:
        return self._admission.rewrite(
            self._inner, prompt, max_tokens=max_tokens, temperature=temperature
        )


def admitted_runtime(inner: Any, admission: Optional[ProviderAdmission]) -> Any:
    """Wrap ``inner`` so every provider-reaching call is an admitted child.

    ``None`` admission returns the runtime unchanged: the surfaces that reach a
    provider (hold, wake, browser) always pass one, and the CLI/route dry-run
    seams that do not are recorded, not silently admitted.
    """
    if inner is None or admission is None:
        return inner
    return AdmittedDictationRuntime(inner, admission)


__all__ = [
    "AdmittedDictationRuntime",
    "PROVIDER_DEADLINE_SECONDS",
    "PROVIDER_FENCED",
    "ProviderAdmission",
    "admitted_runtime",
]
