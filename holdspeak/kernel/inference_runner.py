"""The admitted gateway for one actual inference provider dispatch."""
from __future__ import annotations
import hashlib, json, threading, time, uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from typing import Any, Protocol
from ..deployment_revisions import resolve_deployment_revision
from ..inference_targets import build_intel_for_revision
from ..principals import Principal, PrincipalKind
from .dispatch_context import CONTEXT_MISMATCH, _issue_dispatch_context, bind_dispatch_context, dispatch_context_of, release_dispatch_context, require_dispatch_context
from .inference import executor_identity
from .inference_cancel_signal import perform_cancel
from .invocation_sequence import SequenceRegistry
from .model import KernelRefused, valid_ref
from .projection_stager import retarget_publisher
from .provider_signals import ProviderCompatibilityRetry, ProviderIndeterminate, compatibility_follow_up

def _canonical_payload(payload: Any) -> str:
    try: return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError) as exc: raise KernelRefused("inference_payload_not_canonicalizable") from exc
class ClosurePersistenceError(RuntimeError): pass
class ProviderAdapter(Protocol):
    def dispatch(self, engine: Any, payload: Any, cancellation: threading.Event) -> Any: ...
    def cancel(self) -> str: ...
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
    deployment_revision: str; definition_origin: DefinitionOrigin; deadline_at: float; payload: Any; invocation_id: str=""; parent_operation_id: str=""; attempt_ordinal: int=1
@dataclass(frozen=True)
class InvocationOutcome:
    operation_id: str; invocation_id: str; outcome: str; result_ref: str; receipt: Mapping[str, Any]; error: str = ""
@dataclass
class _Active:
    adapter: ProviderAdapter; operation_id: str; node: Principal; principal: Principal
    cancelled: threading.Event=field(default_factory=threading.Event)
    condition: threading.Condition=field(default_factory=threading.Condition)
    state: str="RUNNING"; cancel_principal: Principal|None=None; disposition: str=""; cancel_performing: bool=False; closing: bool=False; terminal_outcome: str=""; closure_error: BaseException|None=None
class InferenceRunner:
    def __init__(self, broker, database, *, engine_factory=build_intel_for_revision, principal_provider=None, clock=time.time, cancel_timeout=3.0, receipt_attempts=3):
        self._broker,self._database,self._engine_factory=broker,database,engine_factory; self._principal_provider=principal_provider or self._runtime_principal; self._clock=clock; self._cancel_timeout=cancel_timeout; self._receipt_attempts=receipt_attempts; self._active={}; self._pending={}; self._pending_cancellations=self._pending; self._active_lock=threading.Lock(); self._sequences=SequenceRegistry()
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
    def _persist_receipt(self,active,operation_id,outcome,result_ref):
        last=None
        for _ in range(self._receipt_attempts):
            try: return self._broker.receipt(operation_id,outcome,result_ref,active.node)
            except Exception as exc: last=exc
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
            if not signal or outcome.outcome!="failed" or sequence.cancelled: return outcome
            follow=compatibility_follow_up(first,outcome.invocation_id)
            # LAST check before the follow-up becomes real. Building the request is
            # not free, and a cancellation that lands while we build it must stop a
            # retry that has not been admitted yet — no submit, no claim, no child.
            if sequence.cancelled: return self._cancelled_before_retry(outcome)
            return self._attempt(follow,adapter,publish=retarget_publisher(publish,follow.invocation_id),parent_context=parent_context,planned_node=planned_node,signal=None,sequence=sequence)
        finally:
            self._sequences.close(sequence)
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
        submitted=(self._broker.submit_trusted_child(raw, principal, parent_context, planned_node=planned_node) if parent_context is not None else self._broker.submit(raw,principal))
        if submitted["state"]=="refused": return InvocationOutcome(submitted["operation_id"],iid,"refused","",submitted["receipt"])
        approved=self._broker.decide(submitted["operation_id"],"approve",submitted["revision"],principal); op=self._broker.store.operation(approved["operation_id"]); node=Principal(PrincipalKind.NODE,executor_identity(self._revision(request.deployment_revision).destination_id))
        claimed=self._broker.claim(node,iid)
        if not claimed["operations"]: return InvocationOutcome(op["operation_id"],iid,"refused","",claimed.get("refusal") or {})
        active=_Active(adapter,op["operation_id"],node,principal)
        with self._active_lock:
            self._active[iid]=active; pending=self._pending.pop(iid,None)
            # Atomic with becoming reachable: a cancellation that landed during the
            # handoff is returned here and performed below as an ordinary
            # pre-dispatch cancellation — no provider is ever reached.
            if sequence is not None: pending=sequence.enter(iid) or pending
        if pending is not None: self._request_cancel(iid,pending)
        watchdog=threading.Timer(max(0,request.deadline_at-self._clock()),lambda:self._cancel_internal(iid,principal)); watchdog.daemon=True; watchdog.start()
        context=None; bound_engine=None
        try:
            revision = self._revision(request.deployment_revision)
            # HS-131-10: the ONE mint, for the child THIS call just claimed, out of
            # that claim's single-use witness — a caller cannot invent one.
            child=claimed["operations"][0]
            if str(child.get("operation_id") or "")!=op["operation_id"]: raise KernelRefused(CONTEXT_MISMATCH)
            warrant=child["warrant"]
            context=_issue_dispatch_context(witness=child.get("claim_witness"), revision=revision, attempt_ordinal=request.attempt_ordinal, warrant=warrant)
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
            result=self._dispatch(adapter,engine,json.loads(material),active,op["operation_id"],principal,context=context)
            with active.condition:
                while active.state=="CANCELLING" or active.closing or (active.state=="DISPATCHING" and active.cancel_performing and not active.disposition): active.condition.wait()
                pending_principal=None; terminal_after_dispatch=False
                if active.state=="DISPATCHING" and active.disposition and active.disposition!="completed":
                    publishing=False; terminal_after_dispatch=True
                elif active.state=="DISPATCHING":
                    active.state="PUBLISHING"; active.condition.notify_all(); publishing=True
                elif active.state=="RUNNING": active.state="PUBLISHING"; publishing=True
                elif active.state=="CANCEL_REQUESTED": publishing=False; pending_principal=active.cancel_principal
                elif active.state=="CANCELLED": publishing=False
                else: publishing=False
            if not publishing:
                if pending_principal: self._perform_cancel(iid,active,pending_principal)
                return self._finish(active,iid,"indeterminate" if active.disposition=="unknown" else "cancelled")
            result_ref=publish(result) if publish else f"inference-result:{iid}"; outcome="succeeded" if result_ref and valid_ref(result_ref) else "failed"
            with active.condition: active.closing=True
            receipt=self._persist_receipt(active,active.operation_id,outcome,result_ref if outcome=="succeeded" else "")
            with active.condition: active.state="PUBLISHED" if outcome=="succeeded" else "FAILED"; active.closing=False; active.condition.notify_all()
            return InvocationOutcome(active.operation_id,iid,outcome,result_ref if outcome=="succeeded" else "",receipt)
        except ProviderIndeterminate: return self._finish(active,iid,"indeterminate")
        except ProviderCompatibilityRetry as exc:
            # One physical attempt happened and failed on dialect; `invoke` admits the follow-up.
            if signal is not None: signal.append(exc)
            return self._finish(active,iid,"failed", error=str(exc))
        except KernelRefused as exc:
            # KernelRefused.reason is a fixed, content-free control class. Carry it
            # to the domain adapter without persisting provider exception text, so
            # a post-claim context/revision refusal stays named at the speech edge.
            return self._finish(active,iid,"refused",error=str(exc.reason))
        except Exception as exc: return self._finish(active,iid,"failed", error=str(exc))
        finally:
            watchdog.cancel()
            release_dispatch_context(bound_engine, context)
            if sequence is not None: sequence.leave(iid)
            with self._active_lock:
                if active.state != "CLOSURE_FAILED": self._active.pop(iid,None)
    def _dispatch(self,adapter,engine,payload,active,operation_id,principal,*,context):
        # HS-131-10: the last gate before a physical dispatch. The engine's own
        # context wins when it could carry one (a slotted backend cannot), and it
        # must be THIS claimed child's — another operation/attempt refuses by name.
        require_dispatch_context(dispatch_context_of(engine) or context, operation_id=operation_id, attempt_ordinal=getattr(context,"attempt_ordinal",0))
        destination=str(getattr(adapter,"egress_destination","") or "")
        if not destination: return adapter.dispatch(engine,payload,active.cancelled)
        from .external_egress import run_external_egress
        return run_external_egress(connector_id=str(getattr(adapter,"connector_id","inference-provider")),destination=destination,data_classes=tuple(getattr(adapter,"egress_data_classes",("instruction",))),payload_material={"payload_hash":""},sender=lambda:adapter.dispatch(engine,payload,active.cancelled),allowed_destinations=(destination,),parent_operation_id=operation_id,principal=principal,broker=self._broker)
    def _finish(self,active,iid,outcome, *, cancellation_owner=False, error=""):
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
                receipt=self._persist_receipt(active,active.operation_id,outcome,"")
                return InvocationOutcome(active.operation_id,iid,outcome,"",receipt)
            # Claim closure but do not expose a terminal state until receipt()
            # has committed.  All cancellation callers wait on `closing`.
            active.closing=True
        receipt=self._persist_receipt(active,active.operation_id,outcome,"")
        with active.condition:
            active.state=outcome.upper(); active.terminal_outcome=outcome; active.closing=False; active.condition.notify_all()
        return InvocationOutcome(active.operation_id,iid,outcome,"",receipt,error)
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
