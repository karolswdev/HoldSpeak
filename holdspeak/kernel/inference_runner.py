"""The admitted gateway for one actual inference provider dispatch."""
from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any, Protocol

from ..deployment_revisions import resolve_deployment_revision
from ..inference_targets import build_intel_for_revision
from ..principals import Principal, PrincipalKind
from .dispatch_context import (
    CONTEXT_MISMATCH,
    _issue_dispatch_context,
    bind_dispatch_context,
    dispatch_context_of,
    release_dispatch_context,
    require_dispatch_context,
)
from .inference import executor_identity
from .inference_cancel_signal import perform_cancel
from .invocation_sequence import SequenceRegistry
from .model import KernelRefused, valid_ref
from .projection_stager import retarget_publisher
from .provider_signals import (
    InferenceInvalidTypedOutput,
    ProviderCompatibilityRetry,
    ProviderIndeterminate,
    ProviderKnownNoGenerationTransient,
    ProviderPermanentNoGeneration,
    ProviderPermissionDenied,
    compatibility_follow_up,
)
from .runner_receipt_evidence import _install_runner_receipt_evidence_issuer

_issue_runner_receipt_evidence = _install_runner_receipt_evidence_issuer()

def _canonical_payload(payload: Any) -> str:
    try: return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError) as exc: raise KernelRefused("inference_payload_not_canonicalizable") from exc
class ClosurePersistenceError(RuntimeError): pass
class ProviderAdapter(Protocol):
    def dispatch(self, engine: Any, payload: Any, cancellation: threading.Event) -> Any: ...
    def cancel(self) -> str: ...
    def dispatch_stream(self, engine: Any, payload: Any, cancellation: threading.Event) -> Any:
        """Yield :class:`Delta` objects.  Default: wrap ``dispatch`` into one text delta + done."""
        from .inference_stream import Delta
        result = self.dispatch(engine, payload, cancellation)
        text = str(result.get("output", "") if isinstance(result, dict) else result)
        yield Delta(kind="text", text=text)
        yield Delta(kind="done")
@dataclass(frozen=True)
class SavedDefinition:
    ref: str; revision: str
    def journal_value(self): return {"kind":"saved","ref":self.ref,"revision":self.revision}
@dataclass(frozen=True)
class ServiceContract:
    contract: str; revision: str; payload_hash: str
    @classmethod
    def for_payload(cls, contract, revision, payload):
        return cls(contract, revision, "sha256:"+hashlib.sha256(_canonical_payload(payload).encode()).hexdigest())
    def journal_value(self): return {"kind":"service","contract":self.contract,"revision":self.revision,"payload_hash":self.payload_hash}
DefinitionOrigin = SavedDefinition | ServiceContract
@dataclass(frozen=True)
class InvocationRequest:
    deployment_revision: str; definition_origin: DefinitionOrigin; deadline_at: float; payload: Any; invocation_id: str=""; parent_operation_id: str=""; attempt_ordinal: int=1; before_physical_dispatch: Any=None; before_compatibility_retry: Any=None; route_attempt_reservation: Mapping[str,Any]|None=None
@dataclass(frozen=True)
class InvocationOutcome:
    operation_id: str; invocation_id: str; outcome: str; result_ref: str; receipt: Mapping[str, Any]; error: str = ""; runner_signal: str = "none"; send_phase: str = "pre_send"
@dataclass
class _Active:
    adapter: ProviderAdapter; operation_id: str; node: Principal; principal: Principal
    cancelled: threading.Event=field(default_factory=threading.Event)
    condition: threading.Condition=field(default_factory=threading.Condition)
    state: str="RUNNING"; cancel_principal: Principal|None=None; disposition: str=""; cancel_performing: bool=False; closing: bool=False; terminal_outcome: str=""; closure_error: BaseException|None=None; dispatch_intent: bool=False; routed: bool=False
class InferenceRunner:
    def __init__(self, broker, database, *, engine_factory=build_intel_for_revision, principal_provider=None, clock=time.time, cancel_timeout=3.0, receipt_attempts=3, routed_attempt_runtime=None):
        self._broker,self._database,self._engine_factory=broker,database,engine_factory; self._principal_provider=principal_provider or self._runtime_principal; self._clock=clock; self._cancel_timeout=cancel_timeout; self._receipt_attempts=receipt_attempts; self._routed_attempt_runtime=routed_attempt_runtime; self._active={}; self._pending={}; self._pending_cancellations=self._pending; self._active_lock=threading.Lock(); self._sequences=SequenceRegistry()
    def cancel(self, invocation_id: str) -> str: return self._request_cancel(invocation_id,self._principal_provider())
    def _cancel_internal(self, invocation_id: str, principal: Principal) -> str: return self._request_cancel(invocation_id,principal)
    def _request_cancel(self, iid, principal):
        forward=""
        with self._active_lock:
            active=self._active.get(iid)
            # The caller names the LOGICAL invocation. Fence it first, so a retry
            # that has not started yet never will, then reach whichever physical
            # attempt is live through the ordinary machinery below.
            sequence=self._sequences.get(iid)
            if sequence is not None:
                target=sequence.mark_cancelled(principal)
                if active is None:
                    if target and target!=iid and target in self._active: forward=target
                    elif sequence.attempts>=1: return "cancelled"
            if active is None and not forward:
                completed=self._broker.store.operation_for_native(iid)
                receipt=self._broker.store.receipt(completed["operation_id"]) if completed else None
                if receipt:
                    return {"succeeded":"completed", "indeterminate":"unknown"}.get(receipt["outcome"], receipt["outcome"])
                self._pending[iid]=principal; return "pending"
        if forward: return self._request_cancel(forward,principal)
        with active.condition:
            if active.closing:
                while active.closing: active.condition.wait()
                return self._terminal_disposition(active)
            if active.state in {"PUBLISHING","PUBLISHED"}: return "completed"
            if active.state=="RUNNING":
                active.state="CANCEL_REQUESTED"; active.cancel_principal=principal; active.cancel_performing=True; active.condition.notify_all(); perform=True
            elif active.state=="DISPATCHING" and active.cancel_principal is None:
                active.cancel_principal=principal; active.cancel_performing=True; active.condition.notify_all(); perform=True
            else: perform=False
            while not perform and active.state in {"CANCEL_REQUESTED","CANCELLING","DISPATCHING"}: active.condition.wait()
            if not perform: return self._terminal_disposition(active)
        return self._perform_cancel(iid,active,principal)
    def _perform_cancel(self,iid,active,principal): return perform_cancel(self,iid,active,principal)
    @staticmethod
    def _terminal_disposition(active):
        if active.state=="CLOSURE_FAILED": raise active.closure_error or ClosurePersistenceError("terminal receipt persistence failed")
        if active.disposition: return active.disposition
        if active.state=="PUBLISHED": return "completed"
        if active.state=="INDETERMINATE": return "unknown"
        if active.state in {"FAILED","REFUSED","CANCELLED"}: return active.state.lower()
        return "refused"
    @staticmethod
    def _cancel_refused(active,disposition):
        with active.condition: active.disposition=disposition; active.state="RUNNING"; active.condition.notify_all()
        return disposition
    def _persist_receipt(self,active,operation_id,outcome,result_ref, *, runner_signal="none", send_phase="pre_send"):
        last=None
        for _ in range(self._receipt_attempts):
            try:
                operation=self._broker.store.operation(operation_id)
                if not operation or (operation.get("name"),int(operation.get("version") or 0)) != ("inference.invoke",1):
                    return self._broker.receipt(operation_id,outcome,result_ref,active.node)
                evidence=_issue_runner_receipt_evidence(
                    operation_id=operation_id,outcome=outcome,result_ref=result_ref,
                    runner_signal=runner_signal,send_phase=send_phase,
                )
                return self._broker.receipt(
                    operation_id,outcome,result_ref,active.node,
                    runner_evidence=evidence,
                )
            except Exception as exc:  # noqa: BLE001 - bounded durable-write retry
                last=exc
        error=ClosurePersistenceError(f"terminal receipt persistence failed for {outcome}")
        with active.condition:
            active.closing=False; active.state="CLOSURE_FAILED"; active.closure_error=error; active.condition.notify_all()
        raise error from last
    def invoke(self, request, adapter, *, publish=None, parent_context=None, planned_node: str = ""):
        """The one admission path; a dialect retry is a SECOND admitted child.

        Sol Amendment 3 / `provider_signals.compatibility_follow_up`: one physical
        attempt, one child, one receipt — exactly one follow-up is admitted.

        Round 2 fences the follow-up three ways: an HONEST first `failed` (a
        cancelled/indeterminate first attempt is terminal even if it left a
        signal); the logical cancellation fence (`.invocation_sequence`), which
        `_attempt` re-checks atomically as it registers; and a publisher rebound
        to the retry's OWN id, so the attempt that succeeded is the one that
        stages (`.projection_publisher`).
        """
        iid=request.invocation_id or "invoke_"+uuid.uuid4().hex
        first=request if request.invocation_id else replace(request,invocation_id=iid)
        sequence=self._sequences.open(iid); signal: list[BaseException]=[]
        try:
            outcome=self._attempt(first,adapter,publish=publish,parent_context=parent_context,planned_node=planned_node,signal=signal,sequence=sequence)
            if first.route_attempt_reservation is not None:
                self._routed_attempt_runtime.settle(dict(first.route_attempt_reservation), outcome)
            if not signal or outcome.outcome!="failed" or sequence.cancelled: return outcome
            # Canonical route executions never let Runner mint a dialect child.
            # The controller must classify this receipt and reserve a distinct
            # compatibility attempt under the frozen budgets first.
            if first.route_attempt_reservation is not None: return outcome
            follow=compatibility_follow_up(first,outcome.invocation_id)
            if first.before_compatibility_retry is not None:
                # The retry plan is durable before the derived child becomes
                # admissible. A callback refusal preserves the base receipt and
                # prevents the second provider attempt.
                first.before_compatibility_retry(outcome.operation_id, outcome.invocation_id, follow.invocation_id, follow.attempt_ordinal, str(signal[0].mode))
            # LAST check before the follow-up becomes real. Building the request is
            # not free, and a cancellation that lands while we build it must stop a
            # retry that has not been admitted yet — no submit, no claim, no child.
            if sequence.cancelled: return self._cancelled_before_retry(outcome)
            return self._attempt(follow,adapter,publish=retarget_publisher(publish,follow.invocation_id),parent_context=parent_context,planned_node=planned_node,signal=None,sequence=sequence)
        finally:
            self._sequences.close(sequence)
    def invoke_stream(self, request, adapter, *, on_delta, publish=None, parent_context=None, planned_node: str = ""):
        """Streaming twin of ``invoke``: same admission/plan/receipt envelope.

        The adapter's ``dispatch_stream`` yields ``Delta`` objects; the runner
        calls ``on_delta(delta)`` for each.  Disposition rules (D3):
        - Receipt ``succeeded`` at done.
        - Receipt ``indeterminate`` on cancel or error AFTER the first delta.
        - Fallback (existing retry path) ONLY on error BEFORE the first delta.
        - On cancel, ``on_delta`` stops being called within 250 ms.
        """
        from .inference_stream import Delta

        iid = request.invocation_id or "invoke_" + uuid.uuid4().hex
        first = request if request.invocation_id else replace(request, invocation_id=iid)
        sequence = self._sequences.open(iid)
        signal: list[BaseException] = []
        try:
            outcome = self._attempt_stream(
                first, adapter, on_delta=on_delta, publish=publish,
                parent_context=parent_context, planned_node=planned_node,
                signal=signal, sequence=sequence,
            )
            if first.route_attempt_reservation is not None:
                self._routed_attempt_runtime.settle(dict(first.route_attempt_reservation), outcome)
            if not signal or outcome.outcome != "failed" or sequence.cancelled:
                return outcome
            if first.route_attempt_reservation is not None:
                return outcome
            follow = compatibility_follow_up(first, outcome.invocation_id)
            if first.before_compatibility_retry is not None:
                first.before_compatibility_retry(
                    outcome.operation_id, outcome.invocation_id,
                    follow.invocation_id, follow.attempt_ordinal, str(signal[0].mode),
                )
            if sequence.cancelled:
                return self._cancelled_before_retry(outcome)
            return self._attempt_stream(
                follow, adapter, on_delta=on_delta,
                publish=retarget_publisher(publish, follow.invocation_id),
                parent_context=parent_context, planned_node=planned_node,
                signal=None, sequence=sequence,
            )
        finally:
            self._sequences.close(sequence)

    def _attempt_stream(self, request, adapter, *, on_delta, publish=None, parent_context=None, planned_node: str = "", signal=None, sequence=None):
        """Like ``_attempt`` but dispatches via ``adapter.dispatch_stream``."""
        from .inference_stream import Delta

        principal = self._principal_provider()
        material = _canonical_payload(request.payload)
        if isinstance(request.definition_origin, ServiceContract):
            digest = "sha256:" + hashlib.sha256(material.encode()).hexdigest()
            if request.definition_origin.payload_hash and request.definition_origin.payload_hash != digest:
                raise KernelRefused("inference_payload_hash_mismatch")
            origin = ServiceContract(request.definition_origin.contract, request.definition_origin.revision, digest)
        else:
            origin = request.definition_origin
            if not self._saved_definition_live(origin):
                raise KernelRefused("inference_saved_definition_revision_unknown")
        iid = request.invocation_id or "invoke_" + uuid.uuid4().hex
        if not iid.replace("_", "").isalnum():
            raise KernelRefused("inference_invocation_id_invalid")
        raw = {
            "request_schema": 1, "request_id": "request_" + uuid.uuid4().hex,
            "idempotency_key": iid,
            "operation": {"name": "inference.invoke", "version": 1},
            "target": {}, "parent_operation_id": request.parent_operation_id,
            "arguments": {
                "invocation_id": iid, "deployment_revision": request.deployment_revision,
                "definition_origin": origin.journal_value(),
                "deadline_at": request.deadline_at, "attempt_ordinal": request.attempt_ordinal,
            },
        }
        routed = request.route_attempt_reservation
        if routed is not None:
            runtime = self._routed_attempt_runtime
            if runtime is None:
                raise KernelRefused("inference_routed_attempt_runtime_missing")
            if (
                str(routed.get("child_invocation_id") or "") != iid
                or str(routed.get("deployment_revision_id") or "") != request.deployment_revision
                or int(routed.get("physical_attempt_ordinal") or 0) != request.attempt_ordinal
            ):
                raise KernelRefused("inference_route_reservation_mismatch")
            runtime.claim(dict(routed))
        submitted = (
            self._broker.submit_trusted_child(raw, principal, parent_context, planned_node=planned_node)
            if parent_context is not None
            else self._broker.submit(raw, principal)
        )
        if submitted["state"] == "refused":
            return InvocationOutcome(submitted["operation_id"], iid, "refused", "", submitted["receipt"])
        try:
            approved = self._broker.decide(submitted["operation_id"], "approve", submitted["revision"], principal)
        except Exception:
            node = Principal(PrincipalKind.NODE, executor_identity(self._revision(request.deployment_revision).destination_id))
            return self._close_pre_child_failure(
                submitted["operation_id"], iid, routed, node,
                expected_state="awaiting_decision", principal=principal,
                deployment_revision_id=request.deployment_revision,
            )
        op = self._broker.store.operation(approved["operation_id"])
        node = Principal(PrincipalKind.NODE, executor_identity(self._revision(request.deployment_revision).destination_id))
        claimed = self._broker.claim(node, iid)
        if not claimed["operations"]:
            if claimed.get("refusal"):
                return InvocationOutcome(
                    op["operation_id"], iid, "refused", "", claimed["refusal"],
                    runner_signal="kernel_refused", send_phase="pre_send",
                )
            return self._close_pre_child_failure(
                op["operation_id"], iid, routed, node,
                expected_state="awaiting_execution", principal=principal,
                deployment_revision_id=request.deployment_revision,
            )
        if routed is not None:
            runtime.bind(dict(routed), op["operation_id"])
        active = _Active(adapter, op["operation_id"], node, principal, routed=routed is not None)
        with self._active_lock:
            self._active[iid] = active
            pending = self._pending.pop(iid, None)
            if sequence is not None:
                pending = sequence.enter(iid) or pending
        if pending is not None:
            self._request_cancel(iid, pending)
        watchdog = threading.Timer(max(0, request.deadline_at - self._clock()), lambda: self._cancel_internal(iid, principal))
        watchdog.daemon = True
        watchdog.start()
        context = None
        bound_engine = None
        local_runtime_lease = None
        local_lease_indeterminate = False
        try:
            revision = self._revision(request.deployment_revision)
            child = claimed["operations"][0]
            if str(child.get("operation_id") or "") != op["operation_id"]:
                raise KernelRefused(CONTEXT_MISMATCH)
            warrant = child["warrant"]
            context = _issue_dispatch_context(witness=child.get("claim_witness"), revision=revision, attempt_ordinal=request.attempt_ordinal, warrant=warrant)
            if revision.schema_version >= 2 and revision.boundary == "same_device":
                from .local_runtime_lease import acquire_local_runtime_lease
                local_runtime_lease = acquire_local_runtime_lease(
                    self._database, operation_id=op["operation_id"],
                    deployment_revision_id=revision.id, clock=self._clock,
                )
            engine = self._engine_factory(revision, warrant=warrant, context=context)
            carried = dispatch_context_of(engine)
            if carried is not None and carried is not context:
                raise KernelRefused(CONTEXT_MISMATCH)
            bind_dispatch_context(engine, context)
            bound_engine = engine
            with active.condition:
                while active.state == "CANCELLING" or active.closing:
                    active.condition.wait()
                pending_principal = active.cancel_principal if active.state == "CANCEL_REQUESTED" else None
            if pending_principal:
                self._perform_cancel(iid, active, pending_principal)
            with active.condition:
                while active.state == "CANCELLING" or active.closing:
                    active.condition.wait()
                if active.state != "RUNNING":
                    if active.state == "CLOSURE_FAILED":
                        self._terminal_disposition(active)
                    return self._finish(active, iid, "indeterminate" if active.disposition == "unknown" else "cancelled")
                active.state = "DISPATCHING"
                active.condition.notify_all()
            if self._clock() >= request.deadline_at:
                raise KernelRefused("inference_deadline_exceeded")
            if request.before_physical_dispatch is not None:
                request.before_physical_dispatch(op["operation_id"], iid, request.attempt_ordinal)

            def mark_dispatch_intent():
                if routed is not None:
                    runtime.mark_dispatch_intent(dict(routed))
                active.dispatch_intent = True

            # --- streaming dispatch ---
            require_dispatch_context(dispatch_context_of(engine) or context, operation_id=op["operation_id"], attempt_ordinal=getattr(context, "attempt_ordinal", 0))
            mark_dispatch_intent()
            first_delta_seen = False
            collected_text: list[str] = []
            usage_meta: dict[str, Any] = {}
            error_text = ""
            try:
                for delta in adapter.dispatch_stream(engine, json.loads(material), active.cancelled):
                    if active.cancelled.is_set():
                        break
                    if delta.kind == "text":
                        first_delta_seen = True
                        collected_text.append(delta.text)
                        on_delta(delta)
                    elif delta.kind == "reasoning":
                        first_delta_seen = True
                        on_delta(delta)
                    elif delta.kind == "usage":
                        usage_meta = dict(delta.meta)
                        on_delta(delta)
                    elif delta.kind == "done":
                        on_delta(delta)
                    elif delta.kind == "error":
                        error_text = delta.text
                        if not first_delta_seen:
                            raise ProviderIndeterminate()
                        on_delta(delta)
            except ProviderIndeterminate:
                raise
            except ProviderCompatibilityRetry:
                raise
            except ProviderKnownNoGenerationTransient:
                raise
            except ProviderPermanentNoGeneration:
                raise
            except ProviderPermissionDenied:
                raise
            except InferenceInvalidTypedOutput:
                raise
            except KernelRefused:
                raise
            except Exception as exc:
                if not first_delta_seen:
                    raise
                # After the first delta: indeterminate, no fallback.
                local_lease_indeterminate = True
                return self._finish(active, iid, "indeterminate", runner_signal="physical_outcome_unknown", send_phase="dispatch_intent")

            # Check for cancellation after the loop.
            if active.cancelled.is_set():
                local_lease_indeterminate = True
                return self._finish(active, iid, "indeterminate", runner_signal="physical_outcome_unknown", send_phase="dispatch_intent")

            # If an error delta arrived after the first delta, it's indeterminate.
            if error_text and first_delta_seen:
                local_lease_indeterminate = True
                return self._finish(active, iid, "indeterminate", runner_signal="physical_outcome_unknown", send_phase="dispatch_intent")

            # --- publishing ---
            with active.condition:
                while active.state == "CANCELLING" or active.closing or (active.state == "DISPATCHING" and active.cancel_performing and not active.disposition):
                    active.condition.wait()
                pending_principal = None
                if active.state == "DISPATCHING" and active.disposition and active.disposition != "completed":
                    publishing = False
                elif active.state == "DISPATCHING":
                    active.state = "PUBLISHING"
                    active.condition.notify_all()
                    publishing = True
                elif active.state == "RUNNING":
                    active.state = "PUBLISHING"
                    publishing = True
                elif active.state == "CANCEL_REQUESTED":
                    publishing = False
                    pending_principal = active.cancel_principal
                elif active.state == "CANCELLED":
                    publishing = False
                else:
                    publishing = False
            if not publishing:
                if pending_principal:
                    self._perform_cancel(iid, active, pending_principal)
                return self._finish(active, iid, "indeterminate" if active.disposition == "unknown" else "cancelled")
            result = {"output": "".join(collected_text)}
            if usage_meta:
                result["usage"] = usage_meta
            try:
                result_ref = publish(result) if publish else f"inference-result:{iid}"
            except Exception as exc:
                return self._finish(
                    active, iid, "failed", error=str(exc),
                    runner_signal="effect_indeterminate", send_phase="provider_returned",
                )
            outcome_str = "succeeded" if result_ref and valid_ref(result_ref) else "failed"
            with active.condition:
                active.closing = True
            receipt = self._persist_receipt(
                active, active.operation_id, outcome_str,
                result_ref if outcome_str == "succeeded" else "",
                runner_signal="none" if outcome_str == "succeeded" else "effect_indeterminate",
                send_phase="provider_returned",
            )
            with active.condition:
                active.state = "PUBLISHED" if outcome_str == "succeeded" else "FAILED"
                active.closing = False
                active.condition.notify_all()
            return InvocationOutcome(
                active.operation_id, iid, outcome_str,
                result_ref if outcome_str == "succeeded" else "", receipt,
                runner_signal="none" if outcome_str == "succeeded" else "effect_indeterminate",
                send_phase="provider_returned",
            )
        except ProviderIndeterminate:
            if not active.dispatch_intent:
                return self._finish(active, iid, "failed", runner_signal="unclassified_pre_send", send_phase="pre_send")
            local_lease_indeterminate = True
            return self._finish(active, iid, "indeterminate", runner_signal="physical_outcome_unknown", send_phase="dispatch_intent")
        except ProviderCompatibilityRetry as exc:
            if not active.dispatch_intent:
                return self._finish(active, iid, "failed", runner_signal="unclassified_pre_send", send_phase="pre_send")
            if signal is not None:
                signal.append(exc)
            return self._finish(active, iid, "failed", error=str(exc), runner_signal="compatibility_no_generation", send_phase="provider_no_generation")
        except ProviderKnownNoGenerationTransient:
            if not active.dispatch_intent:
                return self._finish(active, iid, "failed", runner_signal="unclassified_pre_send", send_phase="pre_send")
            return self._finish(active, iid, "failed", runner_signal="known_no_generation_transient", send_phase="provider_no_generation")
        except ProviderPermanentNoGeneration:
            if not active.dispatch_intent:
                return self._finish(active, iid, "failed", runner_signal="unclassified_pre_send", send_phase="pre_send")
            return self._finish(active, iid, "failed", runner_signal="provider_permanent_no_generation", send_phase="provider_no_generation")
        except ProviderPermissionDenied:
            if not active.dispatch_intent:
                return self._finish(active, iid, "failed", runner_signal="unclassified_pre_send", send_phase="pre_send")
            return self._finish(active, iid, "refused", runner_signal="permission_denied", send_phase="provider_no_generation")
        except InferenceInvalidTypedOutput:
            if not active.dispatch_intent:
                return self._finish(active, iid, "failed", runner_signal="unclassified_pre_send", send_phase="pre_send")
            return self._finish(active, iid, "failed", runner_signal="invalid_typed_output", send_phase="provider_returned")
        except KernelRefused as exc:
            local_capacity = str(exc.reason) == "inference_local_runtime_busy" and not active.dispatch_intent
            return self._finish(active, iid, "refused", error=str(exc.reason), runner_signal="local_capacity_unavailable" if local_capacity else "kernel_refused", send_phase="dispatch_intent" if active.dispatch_intent else "pre_send")
        except Exception as exc:
            return self._finish(
                active, iid, "failed", error=str(exc),
                runner_signal="dispatch_outcome_unknown" if active.dispatch_intent else "unclassified_pre_send",
                send_phase="dispatch_intent" if active.dispatch_intent else "pre_send",
            )
        finally:
            watchdog.cancel()
            release_dispatch_context(bound_engine, context)
            if local_runtime_lease is not None:
                from .local_runtime_lease import release_local_runtime_lease
                release_local_runtime_lease(
                    self._database, local_runtime_lease,
                    indeterminate=local_lease_indeterminate, clock=self._clock,
                )
            if sequence is not None:
                sequence.leave(iid)
            with self._active_lock:
                if active.state != "CLOSURE_FAILED":
                    self._active.pop(iid, None)

    @staticmethod
    def _cancelled_before_retry(first):
        """The LOGICAL invocation was cancelled before its follow-up was admitted.

        The caller was told `cancelled` and that is what actually happened, so the
        outcome must say so rather than report the dialect `failed` of the only
        attempt that ran. The child's own receipt is untouched and still says
        `failed` — it is the honest, immutable record of that one physical attempt,
        and it rides along here so a caller can read both facts.
        """
        return InvocationOutcome(
            first.operation_id, first.invocation_id, "cancelled", "", first.receipt, first.error,
        )
    def _attempt(self, request, adapter, *, publish=None, parent_context=None, planned_node: str = "", signal=None, sequence=None):
        principal=self._principal_provider(); material=_canonical_payload(request.payload)
        if isinstance(request.definition_origin,ServiceContract):
            digest="sha256:"+hashlib.sha256(material.encode()).hexdigest()
            if request.definition_origin.payload_hash and request.definition_origin.payload_hash!=digest: raise KernelRefused("inference_payload_hash_mismatch")
            origin=ServiceContract(request.definition_origin.contract,request.definition_origin.revision,digest)
        else:
            origin=request.definition_origin
            if not self._saved_definition_live(origin): raise KernelRefused("inference_saved_definition_revision_unknown")
        iid=request.invocation_id or "invoke_"+uuid.uuid4().hex
        if not iid.replace("_","").isalnum(): raise KernelRefused("inference_invocation_id_invalid")
        raw={"request_schema":1,"request_id":"request_"+uuid.uuid4().hex,"idempotency_key":iid,"operation":{"name":"inference.invoke","version":1},"target":{},"parent_operation_id":request.parent_operation_id,"arguments":{"invocation_id":iid,"deployment_revision":request.deployment_revision,"definition_origin":origin.journal_value(),"deadline_at":request.deadline_at,"attempt_ordinal":request.attempt_ordinal}}
        routed = request.route_attempt_reservation
        if routed is not None:
            runtime = self._routed_attempt_runtime
            if runtime is None: raise KernelRefused("inference_routed_attempt_runtime_missing")
            if (
                str(routed.get("child_invocation_id") or "") != iid
                or str(routed.get("deployment_revision_id") or "") != request.deployment_revision
                or int(routed.get("physical_attempt_ordinal") or 0) != request.attempt_ordinal
            ): raise KernelRefused("inference_route_reservation_mismatch")
            runtime.claim(dict(routed))
        submitted=(self._broker.submit_trusted_child(raw, principal, parent_context, planned_node=planned_node) if parent_context is not None else self._broker.submit(raw,principal))
        if submitted["state"]=="refused": return InvocationOutcome(submitted["operation_id"],iid,"refused","",submitted["receipt"])
        try:
            approved=self._broker.decide(submitted["operation_id"],"approve",submitted["revision"],principal)
        except Exception:  # noqa: BLE001 - decision failure is content-free closure input
            node=Principal(PrincipalKind.NODE,executor_identity(self._revision(request.deployment_revision).destination_id))
            return self._close_pre_child_failure(
                submitted["operation_id"],iid,routed,node,
                expected_state="awaiting_decision",principal=principal,
                deployment_revision_id=request.deployment_revision,
            )
        op=self._broker.store.operation(approved["operation_id"]); node=Principal(PrincipalKind.NODE,executor_identity(self._revision(request.deployment_revision).destination_id))
        claimed=self._broker.claim(node,iid)
        if not claimed["operations"]:
            if claimed.get("refusal"):
                return InvocationOutcome(
                    op["operation_id"],iid,"refused","",claimed["refusal"],
                    runner_signal="kernel_refused",send_phase="pre_send",
                )
            return self._close_pre_child_failure(
                op["operation_id"],iid,routed,node,
                expected_state="awaiting_execution",principal=principal,
                deployment_revision_id=request.deployment_revision,
            )
        if routed is not None:
            runtime.bind(dict(routed), op["operation_id"])
        active=_Active(adapter,op["operation_id"],node,principal,routed=routed is not None)
        with self._active_lock:
            self._active[iid]=active; pending=self._pending.pop(iid,None)
            # Atomic with becoming reachable: a cancellation that landed during the
            # handoff is returned here and performed below as an ordinary
            # pre-dispatch cancellation — no provider is ever reached.
            if sequence is not None: pending=sequence.enter(iid) or pending
        if pending is not None: self._request_cancel(iid,pending)
        watchdog=threading.Timer(max(0,request.deadline_at-self._clock()),lambda:self._cancel_internal(iid,principal)); watchdog.daemon=True; watchdog.start()
        context=None; bound_engine=None; local_runtime_lease=None; local_lease_indeterminate=False
        try:
            revision = self._revision(request.deployment_revision)
            # HS-131-10: the ONE mint, for the child THIS call just claimed, out of
            # that claim's single-use witness — a caller cannot invent one.
            child=claimed["operations"][0]
            if str(child.get("operation_id") or "")!=op["operation_id"]: raise KernelRefused(CONTEXT_MISMATCH)
            warrant=child["warrant"]
            context=_issue_dispatch_context(witness=child.get("claim_witness"), revision=revision, attempt_ordinal=request.attempt_ordinal, warrant=warrant)
            if revision.schema_version >= 2 and revision.boundary == "same_device":
                from .local_runtime_lease import acquire_local_runtime_lease

                local_runtime_lease = acquire_local_runtime_lease(
                    self._database,
                    operation_id=op["operation_id"],
                    deployment_revision_id=revision.id,
                    clock=self._clock,
                )
            # ONE calling convention for every engine factory, injected or not.
            engine=self._engine_factory(revision, warrant=warrant, context=context)
            # Round 2: an engine already bound to ANOTHER child's context is
            # REFUSED, not rebound. Matching revision/destination was not enough —
            # two concurrent children sharing a cached engine overwrote each
            # other's context (and a reused MeshRelayIntel kept its constructor
            # warrant under someone else's). The binding is released as this
            # attempt ends, so sequential reuse is unaffected.
            carried=dispatch_context_of(engine)
            if carried is not None and carried is not context: raise KernelRefused(CONTEXT_MISMATCH)
            bind_dispatch_context(engine, context); bound_engine=engine
            with active.condition:
                while active.state=="CANCELLING" or active.closing: active.condition.wait()
                pending_principal=active.cancel_principal if active.state=="CANCEL_REQUESTED" else None
            if pending_principal: self._perform_cancel(iid,active,pending_principal)
            with active.condition:
                while active.state=="CANCELLING" or active.closing: active.condition.wait()
                if active.state != "RUNNING":
                    if active.state=="CLOSURE_FAILED": self._terminal_disposition(active)
                    return self._finish(active,iid,"indeterminate" if active.disposition=="unknown" else "cancelled")
                # A domain may bind its own durable attempt ledger here.  This is
                # deliberately after one kernel child exists and before any
                # provider call; retry attempts traverse the same _attempt path.
                # Atomic dispatch admission: a durable pre-dispatch cancellation
                # can no longer race this right after the condition is released.
                active.state="DISPATCHING"; active.condition.notify_all()
            # HS-131-16 repair R2.4: the IMMEDIATE pre-dispatch deadline fence.
            # The watchdog above is a timer — it fires asynchronously, and a
            # deadline that has already passed when the timer is armed leaves a
            # window in which admission, claim, and engine construction have
            # eaten the whole budget and this call still reaches the provider.
            # A deadline is a fact about NOW, so it is read here, at the last
            # instant before the physical act, and refuses by name.
            if self._clock()>=request.deadline_at: raise KernelRefused("inference_deadline_exceeded")
            if request.before_physical_dispatch is not None:
                request.before_physical_dispatch(op["operation_id"], iid, request.attempt_ordinal)
            def mark_dispatch_intent():
                if routed is not None:
                    runtime.mark_dispatch_intent(dict(routed))
                active.dispatch_intent = True
            result=self._dispatch(adapter,engine,json.loads(material),active,op["operation_id"],principal,context=context,before_send=mark_dispatch_intent)
            with active.condition:
                while active.state=="CANCELLING" or active.closing or (active.state=="DISPATCHING" and active.cancel_performing and not active.disposition): active.condition.wait()
                pending_principal=None
                if active.state=="DISPATCHING" and active.disposition and active.disposition!="completed":
                    publishing=False
                elif active.state=="DISPATCHING":
                    active.state="PUBLISHING"; active.condition.notify_all(); publishing=True
                elif active.state=="RUNNING": active.state="PUBLISHING"; publishing=True
                elif active.state=="CANCEL_REQUESTED": publishing=False; pending_principal=active.cancel_principal
                elif active.state=="CANCELLED": publishing=False
                else: publishing=False
            if not publishing:
                if pending_principal: self._perform_cancel(iid,active,pending_principal)
                return self._finish(active,iid,"indeterminate" if active.disposition=="unknown" else "cancelled")
            try:
                result_ref=publish(result) if publish else f"inference-result:{iid}"
            except Exception as exc:  # noqa: BLE001 - projection effect may be indeterminate
                return self._finish(
                    active,iid,"failed",error=str(exc),
                    runner_signal="effect_indeterminate",send_phase="provider_returned",
                )
            outcome="succeeded" if result_ref and valid_ref(result_ref) else "failed"
            with active.condition: active.closing=True
            receipt=self._persist_receipt(
                active,active.operation_id,outcome,result_ref if outcome=="succeeded" else "",
                runner_signal="none" if outcome=="succeeded" else "effect_indeterminate",
                send_phase="provider_returned",
            )
            with active.condition: active.state="PUBLISHED" if outcome=="succeeded" else "FAILED"; active.closing=False; active.condition.notify_all()
            return InvocationOutcome(
                active.operation_id,iid,outcome,result_ref if outcome=="succeeded" else "",receipt,
                runner_signal="none" if outcome=="succeeded" else "effect_indeterminate",
                send_phase="provider_returned",
            )
        except ProviderIndeterminate:
            if not active.dispatch_intent:
                return self._finish(
                    active,iid,"failed",runner_signal="unclassified_pre_send",
                    send_phase="pre_send",
                )
            local_lease_indeterminate=True
            return self._finish(active,iid,"indeterminate", runner_signal="physical_outcome_unknown", send_phase="dispatch_intent")
        except ProviderCompatibilityRetry as exc:
            if not active.dispatch_intent:
                return self._finish(
                    active,iid,"failed",runner_signal="unclassified_pre_send",
                    send_phase="pre_send",
                )
            # One physical attempt happened and failed on dialect; `invoke` admits the follow-up.
            if signal is not None: signal.append(exc)
            return self._finish(active,iid,"failed", error=str(exc), runner_signal="compatibility_no_generation", send_phase="provider_no_generation")
        except ProviderKnownNoGenerationTransient:
            if not active.dispatch_intent:
                return self._finish(active,iid,"failed",runner_signal="unclassified_pre_send",send_phase="pre_send")
            return self._finish(active,iid,"failed", runner_signal="known_no_generation_transient", send_phase="provider_no_generation")
        except ProviderPermanentNoGeneration:
            if not active.dispatch_intent:
                return self._finish(active,iid,"failed",runner_signal="unclassified_pre_send",send_phase="pre_send")
            return self._finish(active,iid,"failed", runner_signal="provider_permanent_no_generation", send_phase="provider_no_generation")
        except ProviderPermissionDenied:
            if not active.dispatch_intent:
                return self._finish(active,iid,"failed",runner_signal="unclassified_pre_send",send_phase="pre_send")
            return self._finish(active,iid,"refused", runner_signal="permission_denied", send_phase="provider_no_generation")
        except InferenceInvalidTypedOutput:
            if not active.dispatch_intent:
                return self._finish(active,iid,"failed",runner_signal="unclassified_pre_send",send_phase="pre_send")
            return self._finish(active,iid,"failed", runner_signal="invalid_typed_output", send_phase="provider_returned")
        except KernelRefused as exc:
            # KernelRefused.reason is a fixed, content-free control class. Carry it
            # to the domain adapter without persisting provider exception text, so
            # a post-claim context/revision refusal stays named at the speech edge.
            local_capacity = str(exc.reason) == "inference_local_runtime_busy" and not active.dispatch_intent
            return self._finish(active,iid,"refused",error=str(exc.reason), runner_signal="local_capacity_unavailable" if local_capacity else "kernel_refused", send_phase="dispatch_intent" if active.dispatch_intent else "pre_send")
        except Exception as exc:  # noqa: BLE001 - provider errors default unsafe/unknown
            return self._finish(
                active, iid, "failed", error=str(exc),
                runner_signal="dispatch_outcome_unknown" if active.dispatch_intent else "unclassified_pre_send",
                send_phase="dispatch_intent" if active.dispatch_intent else "pre_send",
            )
        finally:
            watchdog.cancel()
            release_dispatch_context(bound_engine, context)
            if local_runtime_lease is not None:
                from .local_runtime_lease import release_local_runtime_lease

                release_local_runtime_lease(
                    self._database, local_runtime_lease,
                    indeterminate=local_lease_indeterminate, clock=self._clock,
                )
            if sequence is not None: sequence.leave(iid)
            with self._active_lock:
                if active.state != "CLOSURE_FAILED": self._active.pop(iid,None)
    def _close_pre_child_failure(self, operation_id, iid, routed, planned_node, *, expected_state, principal, deployment_revision_id):
        """CAS-close pre-child failure without downgrading a claim race."""
        try:
            closed=self._broker.refuse_unstarted_inference_child(
                operation_id,expected_state=expected_state,principal=principal,
                native_id=iid,deployment_revision_id=deployment_revision_id,
            )
            return InvocationOutcome(
                closed["operation_id"],iid,"refused","",closed["receipt"],
                runner_signal="kernel_refused",send_phase="pre_send",
            )
        except KernelRefused:
            operation=self._broker.store.operation(operation_id)
            if expected_state=="awaiting_decision" and operation and operation.get("state")=="awaiting_execution":
                closed=self._broker.refuse_unstarted_inference_child(
                    operation_id,expected_state="awaiting_execution",principal=principal,
                    native_id=iid,deployment_revision_id=deployment_revision_id,
                )
                return InvocationOutcome(
                    closed["operation_id"],iid,"refused","",closed["receipt"],
                    runner_signal="kernel_refused",send_phase="pre_send",
                )
            if not operation or operation.get("state")!="claimed":
                raise
            if routed is not None:
                self._routed_attempt_runtime.bind(dict(routed),operation_id)
                self._routed_attempt_runtime.mark_dispatch_intent(dict(routed))
            claimant=Principal(
                PrincipalKind.NODE,str(operation.get("claimed_by") or planned_node.identity),
            )
            evidence=_issue_runner_receipt_evidence(
                operation_id=operation_id,outcome="indeterminate",result_ref="",
                runner_signal="physical_outcome_unknown",send_phase="dispatch_intent",
            )
            receipt=self._broker.receipt(
                operation_id,"indeterminate","",claimant,runner_evidence=evidence,
            )
            return InvocationOutcome(
                operation_id,iid,"indeterminate","",receipt,
                runner_signal="physical_outcome_unknown",send_phase="dispatch_intent",
            )
    def _dispatch(self,adapter,engine,payload,active,operation_id,principal,*,context,before_send=lambda:None):
        # HS-131-10: the last gate before a physical dispatch. The engine's own
        # context wins when it could carry one (a slotted backend cannot), and it
        # must be THIS claimed child's — another operation/attempt refuses by name.
        require_dispatch_context(dispatch_context_of(engine) or context, operation_id=operation_id, attempt_ordinal=getattr(context,"attempt_ordinal",0))
        destination=str(getattr(adapter,"egress_destination","") or "")
        if not destination:
            before_send()
            return adapter.dispatch(engine,payload,active.cancelled)
        from .external_egress import run_external_egress
        def send():
            before_send()
            return adapter.dispatch(engine,payload,active.cancelled)
        return run_external_egress(connector_id=str(getattr(adapter,"connector_id","inference-provider")),destination=destination,data_classes=tuple(getattr(adapter,"egress_data_classes",("instruction",))),payload_material={"payload_hash":""},sender=send,allowed_destinations=(destination,),parent_operation_id=operation_id,principal=principal,broker=self._broker)
    def _finish(self,active,iid,outcome, *, cancellation_owner=False, error="", runner_signal="none", send_phase="pre_send"):
        with active.condition:
            # Cancellation owns CANCELLING.  A dispatch-side failure cannot
            # overwrite an acknowledged (or unknown) cancellation while its
            # receipts are still being made durable.
            while active.state=="CANCELLING" and not cancellation_owner: active.condition.wait()
            while active.state=="DISPATCHING" and active.cancel_performing and not active.disposition: active.condition.wait()
            while active.closing: active.condition.wait()
            if active.state=="CLOSURE_FAILED": self._terminal_disposition(active)
            if active.state=="DISPATCHING" and active.disposition and active.disposition!="completed":
                outcome="indeterminate" if active.disposition=="unknown" else "cancelled"
            if active.state in {"CANCELLED","INDETERMINATE","PUBLISHED","FAILED","REFUSED"}:
                disposition=self._terminal_disposition(active)
                outcome={"cancelled":"cancelled","unknown":"indeterminate","completed":"succeeded"}.get(disposition, active.state.lower())
                if outcome=="cancelled": runner_signal,send_phase="none","dispatch_intent" if active.dispatch_intent else "pre_send"
                elif outcome=="indeterminate": runner_signal,send_phase="physical_outcome_unknown","dispatch_intent"
                receipt=self._persist_receipt(active,active.operation_id,outcome,"",runner_signal=runner_signal,send_phase=send_phase)
                return InvocationOutcome(active.operation_id,iid,outcome,"",receipt,runner_signal=runner_signal,send_phase=send_phase)
            # Claim closure but do not expose a terminal state until receipt()
            # has committed.  All cancellation callers wait on `closing`.
            active.closing=True
        if outcome=="cancelled": runner_signal,send_phase="none","dispatch_intent" if active.dispatch_intent else "pre_send"
        elif outcome=="indeterminate": runner_signal,send_phase="physical_outcome_unknown","dispatch_intent"
        receipt=self._persist_receipt(active,active.operation_id,outcome,"",runner_signal=runner_signal,send_phase=send_phase)
        with active.condition:
            active.state=outcome.upper(); active.terminal_outcome=outcome; active.closing=False; active.condition.notify_all()
        return InvocationOutcome(active.operation_id,iid,outcome,"",receipt,error,runner_signal,send_phase)
    @staticmethod
    def _runtime_principal():
        from .runtime import _principal
        return _principal.get()
    def _revision(self,rid):
        value=resolve_deployment_revision(self._database,rid)
        if value is None: raise KernelRefused("inference_deployment_revision_unknown")
        return value
    def _saved_definition_live(self,origin):
        return origin.ref.startswith("recipe:") and (recipe:=self._database.recipes.get(origin.ref.removeprefix("recipe:"))) is not None and str(recipe.last_modified)==origin.revision
