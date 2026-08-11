"""Admitted dictation provider dispatches: classify, rewrite, punctuate (HS-131-09).

Every ACTUAL dictation-pipeline model call — the intent router's classify
attempts, the OpenAI-compatible ``response_format`` compatibility retry, the
project rewriter's passes, the model-assisted target detection, and a configured
provider-backed punctuation stage — runs as ONE trusted ``inference.invoke@1``
child of the live speech session, against ONE exact frozen deployment revision
from the session plan.

Two rules shape this module:

* **The adapter never resolves placement.** The frozen
  :class:`~holdspeak.speech_session.plan.SpeechSessionPlan` decided it when the
  session opened; a capability absent from the plan refuses BY NAME before any
  provider request exists, and a mesh dispatch reuses the envelope the runner
  built from the admitted revision + warrant (HS-131-07) instead of constructing
  a fresh target.
* **Retry is never invisible.** Each provider-reaching attempt is its own child
  with its own attempt ordinal and terminal receipt; a validation or lexical
  no-match is not a child at all.

Prompt and transcript material ride ONLY inside the dispatched payload. The
journal row carries the contract, the revision, and the payload hash.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger
from .child import SpeechProviderFailure, run_admitted_speech_child
from .plan import (
    CAPABILITY_INTENT_CLASSIFY,
    CAPABILITY_PUNCTUATE,
    CAPABILITY_REWRITE,
    CONTRACT_INTENT_CLASSIFY,
    CONTRACT_PUNCTUATE,
    CONTRACT_REWRITE,
    SpeechSessionRefused,
    text_sha,
)

log = get_logger("speech_session")

PROVIDER_DEADLINE_SECONDS = 120.0

#: The named refusal a dispatch attempt raises when the session was fenced
#: (cancelled, expired, revoked, or closed) before it could reach a provider.
PROVIDER_FENCED = "speech_provider_fenced"
#: The mesh transport was selected but the runner's admitted engine cannot carry
#: the HS-131-07 envelope. A fresh target is never built to paper over this.
MESH_ENGINE_REQUIRED = "speech_mesh_admitted_engine_required"


@dataclass
class ProviderAdmission:
    """The live authority one dictation pipeline run dispatches providers under.

    Immutable in everything that matters (broker, principal, frozen plan, parent,
    fence); the only mutable state is the attempt ordinal, which exists so two
    dispatches in one run can never share an invocation identity.
    """

    broker: Any
    principal: Any
    plan: Any
    parent: Any
    fence: Any = None
    #: (capability, contract, outcome) per child this admission has run, in order.
    children: list[tuple[str, str, str]] = field(default_factory=list)
    _ordinal: int = 0
    _lock: Any = field(default_factory=threading.Lock)
    #: revision id -> the dispatch target bound to THAT frozen revision. The hot
    #: path pays the identity comparison (and any construction) once per revision
    #: per session, never once per call.
    _targets: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------ plan

    def declares(self, capability: str) -> bool:
        return bool(self.plan is not None and self.plan.has(capability))

    def revision(self, capability: str) -> str:
        return str(self.plan.primary(capability))

    @property
    def egress_boundary(self) -> str:
        """Where this admission's model work goes, read from the frozen plan."""
        return str(self.plan.egress_boundary())

    def _next_ordinal(self) -> int:
        with self._lock:
            self._ordinal += 1
            return self._ordinal

    # ------------------------------------------------------ the bound target

    def prepared(self, runtime: Any, capability: str) -> Any:
        """The non-mesh dispatch target, resolved BEFORE the child is admitted.

        Resolving here is what makes an unbindable backend a NAMED refusal with no
        operation behind it, instead of an anonymous dispatch failure recorded
        after the kernel already admitted a child.
        """
        if str(getattr(runtime, "backend", "")) == "mesh_relay":
            return None
        return self.target(runtime, None, capability)

    def target(self, runtime: Any, engine: Any, capability: str) -> Any:
        """The object THIS child dispatches through, bound to the frozen revision.

        A mesh leg rides the runner's admitted envelope (HS-131-07). Every other
        backend is checked against — and if necessary rebound onto — the exact
        deployment revision this session froze, so a configuration change after
        admission cannot retarget the call while the receipt still names the
        frozen revision.
        """
        if str(getattr(runtime, "backend", "")) == "mesh_relay":
            return _dispatch_target(runtime, engine)
        revision_id = self.revision(capability)
        # The runtime object is part of the key AND is held by the cached entry:
        # a pipeline that rebuilt its runtime is re-checked against the frozen
        # revision, and holding the reference keeps the identity key sound.
        key = f"{revision_id}:{id(runtime)}"
        with self._lock:
            cached = self._targets.get(key)
        if cached is not None:
            return cached[1]
        from .revision_target import bound_target

        bound = bound_target(runtime, self.plan.deployment(revision_id))
        with self._lock:
            self._targets[key] = (runtime, bound)
        return bound

    # ----------------------------------------------------------- one child

    def child(
        self,
        *,
        capability: str,
        contract: str,
        material: Mapping[str, Any],
        call: Callable[[Any, Mapping[str, Any], threading.Event], Any],
        seed: Any,
        deadline_seconds: float = PROVIDER_DEADLINE_SECONDS,
    ) -> tuple[Any, Any]:
        """Run ONE admitted provider dispatch and return ``(outcome, result)``.

        Refuses by name — before any provider request exists — when the plan does
        not declare the capability or the session is already fenced.
        """
        if self.fence is not None:
            reason = self.fence.reason()
            if reason:
                log.info("speech provider dispatch fenced: %s (%s)", reason, capability)
                raise SpeechSessionRefused(PROVIDER_FENCED, capability)
        attempt = self._next_ordinal()
        outcome, result = run_admitted_speech_child(
            broker=self.broker,
            principal=self.principal,
            plan=self.plan,
            parent=self.parent,
            capability=capability,
            contract=contract,
            material=dict(material),
            call=call,
            seed=(seed, attempt),
            attempt_ordinal=attempt,
            deadline_seconds=float(deadline_seconds),
        )
        self.children.append((capability, contract, str(outcome.outcome)))
        state = str(outcome.outcome)
        if state == "succeeded":
            return outcome, result
        # The pipeline's own error contract is exception-based, so a non-succeeded
        # child surfaces as one — named by contract and a SAFE reason only, never
        # provider text. The receipt already recorded the honest outcome.
        if state == "refused":
            raise SpeechSessionRefused(PROVIDER_FENCED, capability)
        raise SpeechProviderFailure(contract, reason=state)

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
        """ONE admitted classify attempt, plus its compatibility retry as a SECOND child.

        The OpenAI-compatible ``response_format`` retry used to hide inside one
        provider method. It is a second real request to a model, so it is a second
        child with its own ordinal and receipt; only that specific
        unsupported-parameter failure advances to it.
        """
        material = {
            "prompt_sha256": text_sha(prompt),
            "prompt_chars": len(str(prompt)),
            "schema_sha256": text_sha(getattr(schema, "block_ids", "")),
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
            "backend": str(getattr(runtime, "backend", "") or ""),
        }
        first = _ClassifyLeg(self, runtime, prompt, schema, max_tokens, temperature)
        try:
            return first.run(material, response_format=True)
        except SpeechProviderFailure as failure:
            if not first.retryable:
                raise
            log.info("dictation classify retrying without response_format as a new child")
            return first.run(
                {**material, "compatibility_retry": True}, response_format=False
            )

    def rewrite(
        self, runtime: Any, prompt: str, *, max_tokens: int, temperature: float
    ) -> str:
        """ONE admitted rewrite dispatch."""
        material = {
            "prompt_sha256": text_sha(prompt),
            "prompt_chars": len(str(prompt)),
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
            "backend": str(getattr(runtime, "backend", "") or ""),
            "prompt_material": str(prompt),
        }

        prepared = self.prepared(runtime, CAPABILITY_REWRITE)

        def call(engine: Any, payload: Mapping[str, Any], cancellation: threading.Event) -> str:
            target = prepared if prepared is not None else _dispatch_target(runtime, engine)
            return str(
                target.rewrite(
                    payload["prompt_material"],
                    max_tokens=int(payload["max_tokens"]),
                    temperature=float(payload["temperature"]),
                )
            )

        _outcome, result = self.child(
            capability=CAPABILITY_REWRITE,
            contract=CONTRACT_REWRITE,
            material=material,
            call=call,
            seed=material["prompt_sha256"],
        )
        return "" if result is None else str(result)

    def punctuate(self, runtime: Any, prompt: str, *, max_tokens: int = 256) -> str:
        """ONE admitted provider-backed punctuation dispatch.

        Today's ``text_processor.process`` is lexical work and reaches no model,
        so no plan declares this capability and this seam refuses by name. It
        exists so a configured provider-backed stage can never appear as
        unreceipted work later.
        """
        material = {
            "prompt_sha256": text_sha(prompt),
            "prompt_chars": len(str(prompt)),
            "max_tokens": int(max_tokens),
            "backend": str(getattr(runtime, "backend", "") or ""),
            "prompt_material": str(prompt),
        }

        prepared = self.prepared(runtime, CAPABILITY_PUNCTUATE)

        def call(engine: Any, payload: Mapping[str, Any], cancellation: threading.Event) -> str:
            target = prepared if prepared is not None else _dispatch_target(runtime, engine)
            return str(
                target.rewrite(payload["prompt_material"], max_tokens=int(payload["max_tokens"]))
            )

        _outcome, result = self.child(
            capability=CAPABILITY_PUNCTUATE,
            contract=CONTRACT_PUNCTUATE,
            material=material,
            call=call,
            seed=material["prompt_sha256"],
        )
        return "" if result is None else str(result)


class _ClassifyLeg:
    """One classify capability, run as one or two admitted children."""

    def __init__(
        self,
        admission: ProviderAdmission,
        runtime: Any,
        prompt: str,
        schema: Any,
        max_tokens: int,
        temperature: float,
    ) -> None:
        self._admission = admission
        self._runtime = runtime
        self._prompt = str(prompt)
        self._schema = schema
        self._max_tokens = int(max_tokens)
        self._temperature = float(temperature)
        #: True only when the failure was the endpoint rejecting
        #: ``response_format`` — the one compatibility fallback that earns a
        #: second child.
        self.retryable = False

    def run(self, material: Mapping[str, Any], *, response_format: bool) -> dict[str, Any]:
        self.retryable = False
        prepared = self._admission.prepared(self._runtime, CAPABILITY_INTENT_CLASSIFY)

        def call(engine: Any, payload: Mapping[str, Any], cancellation: threading.Event) -> Any:
            target = prepared if prepared is not None else _dispatch_target(self._runtime, engine)
            kwargs: dict[str, Any] = {
                "max_tokens": int(payload["max_tokens"]),
                "temperature": float(payload["temperature"]),
            }
            if _accepts_response_format(target):
                kwargs["response_format"] = bool(response_format)
            try:
                return target.classify(self._prompt, self._schema, **kwargs)
            except Exception as exc:
                if response_format and _response_format_unsupported(exc):
                    self.retryable = True
                raise

        _outcome, result = self._admission.child(
            capability=CAPABILITY_INTENT_CLASSIFY,
            contract=CONTRACT_INTENT_CLASSIFY,
            material=material,
            call=call,
            seed=(material["prompt_sha256"], bool(response_format)),
        )
        return dict(result or {})


def _accepts_response_format(target: Any) -> bool:
    """True when the innermost backend takes an explicit ``response_format`` leg.

    Only the OpenAI-compatible backend does: constrained decoding (GBNF) and the
    mesh relay have no such parameter, so they get exactly one child per attempt.
    """
    inner = target
    for _ in range(4):
        if getattr(getattr(inner, "classify", None), "accepts_response_format", False):
            return True
        nested = getattr(inner, "_inner", None)
        if nested is None or nested is inner:
            return False
        inner = nested
    return False


def _response_format_unsupported(exc: BaseException) -> bool:
    from ..plugins.dictation.runtime_openai_compatible import (
        _response_format_unsupported as detector,
    )

    try:
        return bool(detector(exc))  # type: ignore[arg-type]
    except Exception:
        return False


def _dispatch_target(runtime: Any, engine: Any) -> Any:
    """The object this admitted child actually dispatches through.

    A mesh leg MUST ride the envelope the runner built from the admitted revision
    and warrant (HS-131-07), so the backend is rebound onto that admitted engine
    rather than constructing a relay of its own. Every other backend dispatches
    through the runtime the session's frozen configuration already selected.
    """
    if str(getattr(runtime, "backend", "")) != "mesh_relay":
        return runtime
    if engine is None or not callable(getattr(engine, "run_prompt", None)):
        raise SpeechSessionRefused(MESH_ENGINE_REQUIRED, CAPABILITY_INTENT_CLASSIFY)
    return _mesh_bound(runtime, engine)


def _mesh_bound(runtime: Any, engine: Any) -> Any:
    """Bind the mesh backend to the admitted engine, reusing its envelope."""
    from ..plugins.dictation.runtime_mesh_relay import MeshRelayRuntime

    inner = getattr(runtime, "_inner", runtime)
    return MeshRelayRuntime(
        node=str(getattr(inner, "node", "") or ""),
        model_hint=str(getattr(inner, "model_hint", "") or ""),
        intel=engine,
    )


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
    "MESH_ENGINE_REQUIRED",
    "PROVIDER_DEADLINE_SECONDS",
    "PROVIDER_FENCED",
    "ProviderAdmission",
    "admitted_runtime",
]
