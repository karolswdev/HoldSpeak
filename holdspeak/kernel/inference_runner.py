"""The admitted gateway for one actual inference provider dispatch."""
from __future__ import annotations
import hashlib, json, threading, time, uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol
from ..deployment_revisions import resolve_deployment_revision
from ..inference_targets import build_intel_for_revision
from ..principals import Principal, PrincipalKind
from .inference import executor_identity
from .model import KernelRefused, valid_ref

def _canonical_payload(payload: Any) -> str:
    try: return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError) as exc: raise KernelRefused("inference_payload_not_canonicalizable") from exc
class ProviderIndeterminate(RuntimeError): pass
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
    operation_id: str; invocation_id: str; outcome: str; result_ref: str; receipt: Mapping[str, Any]
@dataclass
class _Active:
    adapter: ProviderAdapter; operation_id: str; node: Principal; principal: Principal
    cancelled: threading.Event=field(default_factory=threading.Event)
    condition: threading.Condition=field(default_factory=threading.Condition)
    state: str="RUNNING"; cancel_principal: Principal|None=None; disposition: str=""; cancel_performing: bool=False; closing: bool=False; terminal_outcome: str=""; closure_error: BaseException|None=None
class InferenceRunner:
    def __init__(self, broker, database, *, engine_factory=build_intel_for_revision, principal_provider=None, clock=time.time, cancel_timeout=3.0, receipt_attempts=3):
        self._broker,self._database,self._engine_factory=broker,database,engine_factory; self._principal_provider=principal_provider or self._runtime_principal; self._clock=clock; self._cancel_timeout=cancel_timeout; self._receipt_attempts=receipt_attempts; self._active={}; self._pending={}; self._pending_cancellations=self._pending; self._active_lock=threading.Lock()
    def cancel(self, invocation_id: str) -> str: return self._request_cancel(invocation_id,self._principal_provider())
    def _cancel_internal(self, invocation_id: str, principal: Principal) -> str: return self._request_cancel(invocation_id,principal)
    def _request_cancel(self, iid, principal):
        with self._active_lock:
            active=self._active.get(iid)
            if active is None:
                completed=self._broker.store.operation_for_native(iid)
                receipt=self._broker.store.receipt(completed["operation_id"]) if completed else None
                if receipt:
                    return {"succeeded":"completed", "indeterminate":"unknown"}.get(receipt["outcome"], receipt["outcome"])
                self._pending[iid]=principal; return "pending"
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
    def _perform_cancel(self,iid,active,principal):
        with active.condition:
            # This is the election point.  A request is deliberately separate
            # from performing it: either the public caller or invoke() may get
            # here first, but only the winner may touch the adapter.
            dispatching=active.state=="DISPATCHING"
            if active.state=="CANCEL_REQUESTED":
                active.state="CANCELLING"
            elif active.state=="CANCELLING":
                while active.state=="CANCELLING": active.condition.wait()
                return self._terminal_disposition(active)
            elif not dispatching:
                return self._terminal_disposition(active)
        sid="cancel_"+uuid.uuid4().hex; raw={"request_schema":1,"request_id":sid,"idempotency_key":sid,"operation":{"name":"inference.cancel","version":1},"target":{},"parent_operation_id":active.operation_id,"arguments":{"invocation_id":iid,"signal_id":sid,"reason":"cancelled"}}
        acknowledged=False; disposition_known=False; cancel_operation_id=""
        try:
            signal=self._broker.submit(raw,principal)
            if signal["state"]=="refused": return self._cancel_refused(active,"refused")
            approved=self._broker.decide(signal["operation_id"],"approve",signal["revision"],principal)
            cancel_operation_id=approved["operation_id"]
            if not self._broker.claim(active.node,sid).get("operations"): return self._cancel_refused(active,"refused")
            cancel_result: list[object] = []
            cancel_error: list[BaseException] = []
            def run_cancel():
                try: cancel_result.append(active.adapter.cancel())
                except BaseException as exc: cancel_error.append(exc)
            cancel_thread=threading.Thread(target=run_cancel, daemon=True)
            cancel_thread.start()
            cancel_thread.join(self._cancel_timeout)
            if cancel_thread.is_alive():
                disposition="unknown"; acknowledged=True; disposition_known=True
                with active.condition: active.closing=True
                self._persist_receipt(active,cancel_operation_id,"indeterminate","cancel-disposition:unknown")
                with active.condition:
                    active.closing=False; active.disposition=disposition; active.cancelled.set(); active.condition.notify_all()
                self._finish(active,iid,"indeterminate", cancellation_owner=True)
                return "unknown"
            if cancel_error: raise cancel_error[0]
            disposition=str(cancel_result[0]); acknowledged=disposition!="completed"; disposition_known=True
            child_outcome={"cancelled":"succeeded","completed":"refused","unknown":"indeterminate"}.get(disposition,"indeterminate")
            child_ref=f"invocation:{iid}" if disposition=="cancelled" else f"cancel-disposition:{disposition}"
            with active.condition: active.closing=True
            self._persist_receipt(active,cancel_operation_id,child_outcome,child_ref)
            with active.condition: active.closing=False; active.condition.notify_all()
            if dispatching:
                # DISPATCHING is cooperative: except for unknown, the dispatcher
                # elects invocation closure only after adapter.dispatch returns.
                if acknowledged: active.cancelled.set()
                with active.condition: active.disposition=disposition; active.condition.notify_all()
                if disposition=="unknown":
                    self._finish(active,iid,"indeterminate",cancellation_owner=True)
                    return "unknown"
                with active.condition:
                    while active.state=="DISPATCHING": active.condition.wait()
                return self._terminal_disposition(active)
            if acknowledged:
                active.cancelled.set()
                with active.condition: active.closing=True
                self._persist_receipt(active,active.operation_id,"indeterminate" if disposition=="unknown" else "cancelled","")
            with active.condition: active.disposition=disposition; active.state="RUNNING" if disposition=="completed" else "CANCELLED"; active.closing=False; active.condition.notify_all()
            return disposition
        except BaseException as exc:
            if disposition_known:
                with active.condition:
                    if active.state=="CLOSURE_FAILED": raise active.closure_error
                raise
            if cancel_operation_id:
                with active.condition: active.closing=True
                self._persist_receipt(active,cancel_operation_id,"failed","cancel-disposition:failed")
                with active.condition: active.closing=False; active.condition.notify_all()
            self._cancel_refused(active,"refused")
            if not isinstance(exc, Exception): raise
            return "refused"
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
    def invoke(self, request, adapter, *, publish=None):
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
        submitted=self._broker.submit(raw,principal)
        if submitted["state"]=="refused": return InvocationOutcome(submitted["operation_id"],iid,"refused","",submitted["receipt"])
        approved=self._broker.decide(submitted["operation_id"],"approve",submitted["revision"],principal); op=self._broker.store.operation(approved["operation_id"]); node=Principal(PrincipalKind.NODE,executor_identity(self._revision(request.deployment_revision).destination_id))
        claimed=self._broker.claim(node,iid)
        if not claimed["operations"]: return InvocationOutcome(op["operation_id"],iid,"refused","",claimed.get("refusal") or {})
        active=_Active(adapter,op["operation_id"],node,principal)
        with self._active_lock: self._active[iid]=active; pending=self._pending.pop(iid,None)
        if pending is not None: self._request_cancel(iid,pending)
        watchdog=threading.Timer(max(0,request.deadline_at-self._clock()),lambda:self._cancel_internal(iid,principal)); watchdog.daemon=True; watchdog.start()
        try:
            engine=self._engine_factory(self._revision(request.deployment_revision))
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
            result=self._dispatch(adapter,engine,json.loads(material),active,op["operation_id"],principal)
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
        except KernelRefused: return self._finish(active,iid,"refused")
        except Exception: return self._finish(active,iid,"failed")
        finally:
            watchdog.cancel()
            with self._active_lock:
                if active.state != "CLOSURE_FAILED": self._active.pop(iid,None)
    def _dispatch(self,adapter,engine,payload,active,operation_id,principal):
        destination=str(getattr(adapter,"egress_destination","") or "")
        if not destination: return adapter.dispatch(engine,payload,active.cancelled)
        from .external_egress import run_external_egress
        return run_external_egress(connector_id=str(getattr(adapter,"connector_id","inference-provider")),destination=destination,data_classes=tuple(getattr(adapter,"egress_data_classes",("instruction",))),payload_material={"payload_hash":""},sender=lambda:adapter.dispatch(engine,payload,active.cancelled),allowed_destinations=(destination,),parent_operation_id=operation_id,principal=principal,broker=self._broker)
    def _finish(self,active,iid,outcome, *, cancellation_owner=False):
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
        return InvocationOutcome(active.operation_id,iid,outcome,"",receipt)
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
