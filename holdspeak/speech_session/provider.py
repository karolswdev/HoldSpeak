"""Admitted dictation provider dispatches: classify, rewrite, punctuate (HS-131-09).

Every ACTUAL dictation-pipeline model call — the intent router's classify
attempt, the project rewriter's passes, the model-assisted target detection, and a configured
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

import json
import threading
from dataclasses import dataclass, field
from types import SimpleNamespace
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
#: A Phase-D bundle is corrupted or incomplete.  Egress must not quietly call
#: an absent frozen transcription route "local".
ROUTED_EGRESS_ROUTE_MISSING = "speech_routed_egress_route_missing"
#: A Phase-D parent that has frozen a speech route may not quietly drop back to
#: the v1 provider-child path. Every configured provider member must exist in
#: its same parent bundle.
ROUTED_PROVIDER_ROUTE_MISSING = "speech_routed_provider_route_missing"


def _safe_refusal_reason(outcome: Any) -> str:
    """The kernel's own fixed refusal reason class for a refused child.

    Both refusal paths — admission (`_refuse_attempt`) and claim — record the
    reason as the terminal receipt's ``outcome`` field, so the receipt and the
    exception name the same thing. ``error`` is the runner's own secondary
    carrier. Everything here is a fixed reason CLASS, never provider text; if
    neither is present we fall back to the fence reason rather than invent one.
    """
    receipt = getattr(outcome, "receipt", None)
    if isinstance(receipt, Mapping):
        reason = str(receipt.get("outcome") or "").strip()
        # A receipt whose outcome is literally the state carries no reason.
        if reason and reason not in {"refused", "succeeded", "failed"}:
            return reason
    error = str(getattr(outcome, "error", "") or "").strip()
    return error or PROVIDER_FENCED


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
    routed_routes: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: Phase-D's frozen transcription member.  It is separate from the
    #: dictation LLM stages because transcription can be the widest egress.
    transcription_route: dict[str, Any] | None = None
    _active_routed_revision_id: str = ""

    # ------------------------------------------------------------------ plan

    def declares(self, capability: str) -> bool:
        return bool(self.plan is not None and self.plan.has(capability))

    def revision(self, capability: str) -> str:
        """Return the deployment revision frozen for this provider capability.

        Phase-D bundle members are the authority for routed provider work.  Their
        route plans deliberately replace the historical session-plan sentinel, so
        provider construction must read the member's frozen deployment rather than
        attempting to resolve ``routed:<capability>`` as though it were a legacy
        deployment ID.
        """
        routed = self.routed_routes.get(capability)
        if routed is None:
            return str(self.plan.primary(capability))
        with self.broker.database._connection() as conn:
            row = conn.execute(
                "SELECT deployment_revision_id FROM inference_route_plan_entries "
                "WHERE plan_id=? ORDER BY route_leg_ordinal LIMIT 1",
                (str(routed["id"]),),
            ).fetchone()
        if row is None:
            raise SpeechSessionRefused(ROUTED_PROVIDER_ROUTE_MISSING, capability)
        return str(row["deployment_revision_id"])

    def deployment(self, capability: str) -> Any:
        """Resolve the immutable deployment object for one frozen provider leg."""
        routed = self.routed_routes.get(capability)
        if routed is None:
            return self.plan.deployment(self.revision(capability))
        from ..deployment_revisions import resolve_deployment_revision

        revision = resolve_deployment_revision(self.broker.database, self.revision(capability))
        if revision is None:
            raise SpeechSessionRefused("deployment_revision_unknown", capability)
        return revision

    @property
    def egress_boundary(self) -> str:
        """Report the widest boundary across this frozen speech session.

        New Phase-D capture parents derive the badge from their bundled
        transcription member as well as any bundled provider stages.  A mesh or
        private-network transcription route can therefore never disappear behind
        the legacy plan's empty-provider ``local`` default.
        """
        if self.transcription_route is None:
            return str(self.plan.egress_boundary())
        from ..intel.providers import EGRESS_BOUNDARIES, EGRESS_LOCAL

        route_ids = [str(self.transcription_route.get("id") or "")]
        route_ids.extend(str(route.get("id") or "") for route in self.routed_routes.values())
        widest = EGRESS_LOCAL
        with self.broker.database._connection() as conn:
            for route_id in route_ids:
                rows = conn.execute(
                    "SELECT boundary FROM inference_route_plan_entries "
                    "WHERE plan_id=? ORDER BY route_leg_ordinal",
                    (route_id,),
                ).fetchall()
                if not rows:
                    raise SpeechSessionRefused(ROUTED_EGRESS_ROUTE_MISSING, route_id)
                for row in rows:
                    boundary = str(row["boundary"])
                    if EGRESS_BOUNDARIES.index(boundary) > EGRESS_BOUNDARIES.index(widest):
                        widest = boundary
        return widest

    def _next_ordinal(self) -> int:
        with self._lock:
            self._ordinal += 1
            return self._ordinal

    # ------------------------------------------------------ the bound target

    def prepared(self, runtime: Any, capability: str) -> Any:
        """The non-mesh dispatch target when nothing has to be CONSTRUCTED.

        Checking here is what makes an unbindable backend a NAMED refusal with no
        operation behind it, instead of an anonymous dispatch failure recorded
        after the kernel already admitted a child. A runtime that already IS the
        frozen target is returned as-is; a disagreement is only verified rebindable
        here and is rebuilt later under the admitted child's dispatch context
        (HS-131-10), because construction is an adapter factory.
        """
        if str(getattr(runtime, "backend", "")) == "mesh_relay":
            return None
        revision = self.deployment(capability)
        if revision is None:
            return runtime
        from .revision_target import agrees, ensure_rebindable

        if agrees(runtime, revision):
            return runtime
        ensure_rebindable(revision)
        return None

    def dispatch_through(self, runtime: Any, engine: Any, capability: str) -> Any:
        """The object THIS admitted child dispatches through, given its engine."""
        if self._active_routed_revision_id:
            from ..deployment_revisions import resolve_deployment_revision
            from ..kernel.dispatch_context import dispatch_context_of
            from .revision_target import bound_target

            revision = resolve_deployment_revision(
                self.broker.database, self._active_routed_revision_id
            )
            if revision is None:
                raise SpeechSessionRefused("deployment_revision_unknown", capability)
            if str(getattr(revision, "engine", "")) in {"mesh", "node_runtime", "mesh_relay"}:
                return _dispatch_target(runtime, engine)
            return bound_target(runtime, revision, context=dispatch_context_of(engine))
        if str(getattr(runtime, "backend", "")) == "mesh_relay":
            return _dispatch_target(runtime, engine)
        return self.target(runtime, engine, capability)

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
        from ..kernel.dispatch_context import dispatch_context_of, require_dispatch_context
        from .revision_target import bound_target

        revision = self.deployment(capability)
        with self._lock:
            cached = self._targets.get(key)
        if cached is not None:
            # A CONSTRUCTED target is not a free ride for the next caller: the
            # cache is per session, so the child collecting it proves its own
            # admission for this frozen revision before it may dispatch through
            # something an earlier child built.
            if cached[1] is not runtime:
                require_dispatch_context(dispatch_context_of(engine), revision)
            return cached[1]

        # The context rides on the engine the RUNNER built for this claimed child;
        # a rebind therefore proves admission instead of trusting its caller.
        bound = bound_target(
            runtime,
            revision,
            context=dispatch_context_of(engine),
        )
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
                # ``reason`` is one of SessionFence's fixed, content-free control
                # classes. Preserve the fact it already proved — expired, revoked,
                # closed, or cancelled — instead of overwriting every fence with
                # the generic fallback and telling the owner the wrong refusal.
                raise SpeechSessionRefused(reason, capability)
        attempt = self._next_ordinal()
        routed = self.routed_routes.get(capability)
        if routed is not None:
            canonical = {
                CAPABILITY_INTENT_CLASSIFY: "speech.intent_classify",
                CAPABILITY_REWRITE: "speech.rewrite",
                CAPABILITY_PUNCTUATE: "speech.punctuate",
            }[capability]
            logical = f"speech_{self.parent.operation_id}_{attempt}"
            admitted = self.broker.inference_adoption_service.admit_on_frozen_route(
                self.principal,
                command_id=f"speechop-{self.parent.operation_id}-{attempt}",
                route_plan_id=str(routed["id"]),
                capability_id=canonical,
                operation_id=logical,
                payload=dict(material),
                reserved_output_tokens=int(material.get("max_tokens") or 256),
            )
            result = self.broker.inference_adoption_service.execute(
                self.principal,
                execution_id=admitted["execution"]["id"],
                adapter=_RoutedSpeechAdapter(self, canonical, call),
                parent_context=self.parent.context,
            )
            state = str(result["outcome"])
            self.children.append((capability, contract, state))
            if state == "succeeded":
                value = result["result"]
                if canonical in {"speech.rewrite", "speech.punctuate"}:
                    value = dict(value or {}).get("output", "")
                elif canonical == "speech.intent_classify":
                    value = dict(value or {})
                    value["extras"] = json.loads(str(value.pop("extras_json")))
                return SimpleNamespace(
                    outcome=state,
                    receipt=result["receipt"],
                    operation_id=logical,
                ), value
            if state == "refused":
                raise SpeechSessionRefused(
                    str(result["receipt"].get("terminal_disposition") or state), capability
                )
            raise SpeechProviderFailure(contract, reason=state)
        if self.transcription_route is not None:
            # Bundle authority is all-or-nothing.  Falling through here would
            # create a plain legacy provider child under a parent that already
            # froze speech authority, which is neither budgeted nor receipted as
            # a member of that bundle.
            raise SpeechSessionRefused(ROUTED_PROVIDER_ROUTE_MISSING, capability)
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
            # Sol Amendment 3: do NOT rewrite every refusal to
            # `speech_provider_fenced`. That reason means one specific thing —
            # "this session may no longer publish" — and stamping it on a budget
            # refusal, a payload-hash mismatch, an unknown revision, or a claim
            # refusal told the owner the wrong story about their own desk and
            # made the receipt and the exception disagree. The kernel already
            # chose a fixed, safe, content-free reason class; carry THAT.
            raise SpeechSessionRefused(_safe_refusal_reason(outcome), capability)
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
        """Run one admitted classify attempt; the controller owns any advance."""
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
        # HS-143-07: dialect retries are not application-owned. A future
        # response-format variant must be a separately frozen controller leg;
        # until then this capability performs exactly one admitted request.
        return _ClassifyLeg(
            self, runtime, prompt, schema, max_tokens, temperature
        ).run(material, response_format=True)

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

        prepared = (
            None
            if CAPABILITY_REWRITE in self.routed_routes
            else self.prepared(runtime, CAPABILITY_REWRITE)
        )

        def call(engine: Any, payload: Mapping[str, Any], cancellation: threading.Event) -> str:
            target = (
                prepared
                if prepared is not None
                else self.dispatch_through(runtime, engine, CAPABILITY_REWRITE)
            )
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
            target = (
                prepared
                if prepared is not None
                else self.dispatch_through(runtime, engine, CAPABILITY_PUNCTUATE)
            )
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
    def run(self, material: Mapping[str, Any], *, response_format: bool) -> dict[str, Any]:
        prepared = (
            None
            if CAPABILITY_INTENT_CLASSIFY in self._admission.routed_routes
            else self._admission.prepared(self._runtime, CAPABILITY_INTENT_CLASSIFY)
        )

        def call(engine: Any, payload: Mapping[str, Any], cancellation: threading.Event) -> Any:
            target = (
                prepared
                if prepared is not None
                else self._admission.dispatch_through(
                    self._runtime, engine, CAPABILITY_INTENT_CLASSIFY
                )
            )
            kwargs: dict[str, Any] = {
                "max_tokens": int(payload["max_tokens"]),
                "temperature": float(payload["temperature"]),
            }
            if _accepts_response_format(target):
                kwargs["response_format"] = bool(response_format)
            return target.classify(self._prompt, self._schema, **kwargs)

        _outcome, result = self._admission.child(
            capability=CAPABILITY_INTENT_CLASSIFY,
            contract=CONTRACT_INTENT_CLASSIFY,
            material=material,
            call=call,
            seed=(material["prompt_sha256"], bool(response_format)),
        )
        return dict(result or {})


class _RoutedSpeechAdapter:
    """Execute and validate one speech stage on the controller-selected leg."""

    connector_id = "inference-provider"

    def __init__(self, admission: ProviderAdmission, capability: str, call: Any) -> None:
        self._admission, self._capability, self._call = admission, capability, call

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
