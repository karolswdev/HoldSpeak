"""Durable native controllers for admitted outer runs."""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Mapping

from ..principals import Principal, PrincipalKind
from .parent_lease import ParentLeaseHeartbeats
from .model import Admission, KernelRefused, OperationRequest, valid_ref

_PARENT_FIELDS = frozenset({"native_id", "definition_ref", "definition_revision", "input", "deadline_at", "child_budget"})
_OUTCOME_STATES = {"succeeded": "SUCCEEDED", "failed": "FAILED", "cancelled": "CANCELLED", "refused": "REFUSED", "indeterminate": "INDETERMINATE"}


@dataclass(frozen=True)
class _ParentAdmission(Admission):
    kind: str; definition_ref: str; definition_revision: str
    input_snapshot: Mapping[str, Any]; deadline_at: float; child_budget: int


class ParentRunCodec:
    version = 1
    def __init__(self, kind: str, *, clock: Any = time.time) -> None:
        self.kind, self.name, self._clock = kind, f"{kind}.run", clock
    def validate(self, request: OperationRequest) -> Admission:
        if request.target_ref or request.placement or set(request.arguments) != _PARENT_FIELDS:
            raise KernelRefused("parent_run_prerequisite_failed")
        args = request.arguments
        try: deadline, budget = float(args.get("deadline_at")), int(args.get("child_budget"))
        except (TypeError, ValueError) as exc: raise KernelRefused("parent_run_prerequisite_failed") from exc
        native_id, definition_ref, revision, snapshot = (str(args.get("native_id") or "").strip(), str(args.get("definition_ref") or "").strip(), str(args.get("definition_revision") or "").strip(), args.get("input"))
        if not native_id or not valid_ref(definition_ref) or not revision or not isinstance(snapshot, Mapping) or deadline <= self._clock() or budget < 0:
            raise KernelRefused("parent_run_prerequisite_failed")
        return _ParentAdmission(f"{self.kind}-run:{native_id}", "node:parent-controller", "sha256:" + uuid.uuid5(uuid.NAMESPACE_URL, json.dumps(dict(args), sort_keys=True, separators=(",", ":"))).hex, (definition_ref, f"revision:{revision}"), f"{self.kind} run", max(.1, deadline-self._clock()), native_id, self.kind, definition_ref, revision, dict(snapshot), deadline, budget)
    def authorize(self, request: OperationRequest, admission: _ParentAdmission, principal: Any, operation_id: str) -> _ParentAdmission: return admission
    def admit(self, request: OperationRequest, admission: _ParentAdmission, principal: Any, operation_id: str) -> None: return None
    def decide(self, native_id: str, decision: str, principal: Any, reason: str = "") -> None: return None
    def read_native(self, native_id: str) -> dict[str, Any]: return {"native_id": native_id, "kind": self.kind}
    def project_process(self, native_id: str, operation: Mapping[str, Any]) -> dict[str, Any]: return {"process_id": f"process:{operation['operation_id']}", "kind": self.name, "principal": operation["principal_identity"], "generic_state": operation["state"], "domain_state": operation["state"], "target_ref": operation["target_ref"], "current_operation_id": operation["operation_id"]}
    def project_receipts(self, native_id: str) -> list[dict[str, Any]]: return []


class OuterRunContext:
    """Opaque controller-local capability; no constructor, codec, or stable value."""
    __slots__ = ("_capability", "_controller", "operation_id", "native_id", "owner_kind", "owner_identity", "epoch")
    def __init__(self, *args: Any, **kwargs: Any) -> None: raise TypeError("OuterRunContext is kernel-issued and cannot be constructed")
    def __reduce__(self) -> Any: raise TypeError("OuterRunContext is not serializable")
    def __repr__(self) -> str: return "<OuterRunContext>"


@dataclass(frozen=True)
class ParentRun:
    operation_id: str; native_id: str; context: OuterRunContext; replayed: bool = False


class ParentRunController:
    """Durable parent state, scoped contexts, lease recovery, and terminal CAS."""
    _node = Principal(PrincipalKind.NODE, "parent-controller")
    # Three beats fit within the stale window, so one missed refresh is harmless.
    _lease_seconds = 90.0
    _heartbeat_seconds = 10.0
    def __init__(self, broker: Any, database: Any, *, clock: Any = time.time) -> None:
        self._broker, self._database, self._clock = broker, database, clock
        self._process_id, self._issued = "parent-process_" + uuid.uuid4().hex, {}
        self._heartbeats = ParentLeaseHeartbeats(self._refresh_lease, interval=lambda: self._heartbeat_seconds)

    def shutdown(self) -> None:
        """Stop process-local refreshers before this controller is discarded."""
        self._heartbeats.stop_all()
        self._issued.clear()

    def _refresh_lease(self, operation_id: str) -> None:
        """Refresh only a still-active dispatch owned by this live process."""
        now = self._clock()
        with self._database._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("UPDATE kernel_parent_runs SET lease_process_id=?,lease_heartbeat_at=?,updated_at=? WHERE operation_id=? AND state IN ('OPEN','CANCELLING') AND active_child_invocation_id != ''", (self._process_id, now, now, operation_id))

    def begin_child_dispatch(self, operation_id: str) -> None:
        self._heartbeats.start(operation_id)

    def end_child_dispatch(self, operation_id: str) -> None:
        self._heartbeats.stop(operation_id)

    def _context(self, row: Mapping[str, Any]) -> OuterRunContext:
        key = (str(row["operation_id"]), int(row["execution_epoch"]))
        cap = self._issued.setdefault(key, object())
        value = object.__new__(OuterRunContext)
        value._capability, value._controller = cap, self
        value.operation_id, value.native_id = key[0], str(row["native_id"])
        value.owner_kind, value.owner_identity, value.epoch = str(row["principal_kind"]), str(row["principal_identity"]), key[1]
        return value

    def _valid_context(self, context: Any, row: Mapping[str, Any], principal: Any | None = None) -> None:
        if not isinstance(context, OuterRunContext) or context._controller is not self or context._capability is not self._issued.get((context.operation_id, context.epoch)):
            raise KernelRefused("parent_context_invalid")
        if (context.native_id != str(row["native_id"]) or context.owner_kind != str(row["principal_kind"]) or context.owner_identity != str(row["principal_identity"]) or context.epoch != int(row["execution_epoch"])):
            raise KernelRefused("parent_context_invalid")
        if principal is not None and (principal.name != str(row["principal_kind"]) or principal.identity != str(row["principal_identity"])):
            raise KernelRefused("parent_operation_scope_required")

    def start(self, principal: Any, *, kind: str, definition_ref: str, definition_revision: str, input_snapshot: Mapping[str, Any], deadline_at: float, child_budget: int, idempotency_key: str | None = None) -> ParentRun:
        if principal is None or principal.kind is PrincipalKind.NONE: raise KernelRefused("principal_authentication_required")
        if kind not in {"sequence", "workflow", "workbench"}: raise KernelRefused("parent_run_kind_unknown")
        request_id = idempotency_key or "request_" + uuid.uuid4().hex
        if idempotency_key:
            with self._database._connection() as conn:
                row = conn.execute("SELECT p.*,o.principal_kind,o.principal_identity FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id WHERE o.principal_kind=? AND o.principal_identity=? AND o.idempotency_key=?", (principal.name, principal.identity, request_id)).fetchone()
            if row is not None:
                same = (str(row["kind"]) == kind and str(row["definition_ref"]) == definition_ref and str(row["definition_revision"]) == definition_revision and json.loads(str(row["input_json"])) == dict(input_snapshot))
                if not same: raise KernelRefused("idempotency_payload_mismatch")
                return ParentRun(str(row["operation_id"]), str(row["native_id"]), self._context(row), replayed=True)
        native_id = f"{kind}_run_" + (uuid.uuid5(uuid.NAMESPACE_URL, f"{principal.name}:{principal.identity}:{kind}:{definition_ref}:{definition_revision}:{request_id}").hex if idempotency_key else uuid.uuid4().hex)
        raw = {"request_schema": 1, "request_id": request_id, "idempotency_key": request_id, "operation": {"name": f"{kind}.run", "version": 1}, "target": {}, "arguments": {"native_id": native_id, "definition_ref": definition_ref, "definition_revision": definition_revision, "input": dict(input_snapshot), "deadline_at": deadline_at, "child_budget": child_budget}}
        submitted = self._broker.submit(raw, principal)
        if submitted["state"] == "refused": raise KernelRefused(str(submitted.get("receipt", {}).get("outcome") or "parent_admission_refused"))
        operation_id = str(submitted["operation_id"])
        if submitted["state"] == "awaiting_decision": self._broker.decide(operation_id, "approve", submitted["revision"], principal)
        if (self._broker.store.operation(operation_id) or {}).get("state") == "awaiting_execution": self._broker.claim(self._node, native_id)
        now = self._clock()
        with self._database._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("""INSERT OR IGNORE INTO kernel_parent_runs(operation_id,native_id,kind,definition_ref,definition_revision,input_json,deadline_at,execution_epoch,planned_node,active_child_invocation_id,child_budget,children_json,state,lease_process_id,lease_heartbeat_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (operation_id, native_id, kind, definition_ref, definition_revision, json.dumps(dict(input_snapshot), sort_keys=True, separators=(",", ":")), deadline_at, 1, "", "", child_budget, "[]", "OPEN", self._process_id, now, now, now))
            row = conn.execute("SELECT p.*,o.principal_kind,o.principal_identity FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id WHERE p.operation_id=?", (operation_id,)).fetchone()
        if row is None: raise KernelRefused("parent_run_persistence_failed")
        return ParentRun(operation_id, str(row["native_id"]), self._context(row))

    def reserve_child(self, context: OuterRunContext, principal: Any, *, planned_node: str, invocation_id: str) -> int:
        """Test/pure-controller reservation; production admission uses trusted_child."""
        if not isinstance(context, OuterRunContext): raise KernelRefused("parent_context_invalid")
        with self._database._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT p.*,o.principal_kind,o.principal_identity,o.state AS operation_state,o.warrant_json,o.warrant_revoked FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id WHERE p.operation_id=?", (getattr(context, "operation_id", ""),)).fetchone()
            if row is None: raise KernelRefused("parent_operation_unknown")
            self._valid_context(context, row, principal)
            if str(row["state"]) != "OPEN" or str(row["operation_state"]) != "claimed": raise KernelRefused("parent_operation_not_running")
            warrant = json.loads(str(row["warrant_json"] or "{}"))
            if bool(row["warrant_revoked"]) or float(warrant.get("execution_expires_at") or 0) <= self._clock() or not self._broker.store.valid_warrant(warrant): raise KernelRefused("parent_operation_not_live")
            children = json.loads(str(row["children_json"]))
            if len(children) >= int(row["child_budget"]): raise KernelRefused("parent_child_budget_exhausted")
            children.append(invocation_id)
            if conn.execute("UPDATE kernel_parent_runs SET planned_node=?,active_child_invocation_id=?,children_json=?,lease_process_id=?,lease_heartbeat_at=?,updated_at=? WHERE operation_id=? AND state='OPEN' AND execution_epoch=?", (planned_node, invocation_id, json.dumps(children, separators=(",", ":")), self._process_id, self._clock(), self._clock(), context.operation_id, context.epoch)).rowcount != 1: raise KernelRefused("parent_operation_not_running")
        self.begin_child_dispatch(context.operation_id)
        return context.epoch

    def finalize_child_checkpoint(self, conn: Any, **kwargs: Any) -> bool:
        from .parent_checkpoint import finalize
        result = finalize(conn, clock=self._clock, **kwargs)
        self.end_child_dispatch(str(kwargs["parent_operation_id"]))
        return result

    def supersede(self, context: OuterRunContext, principal: Any) -> OuterRunContext:
        with self._database._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT p.*,o.principal_kind,o.principal_identity FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id WHERE p.operation_id=?", (getattr(context, "operation_id", ""),)).fetchone()
            if row is None: raise KernelRefused("parent_operation_unknown")
            self._valid_context(context, row, principal)
            if conn.execute("UPDATE kernel_parent_runs SET execution_epoch=execution_epoch+1,planned_node='',active_child_invocation_id='',lease_heartbeat_at=?,updated_at=? WHERE operation_id=? AND state='OPEN' AND execution_epoch=?", (self._clock(), self._clock(), context.operation_id, context.epoch)).rowcount != 1: raise KernelRefused("parent_operation_not_running")
            row = conn.execute("SELECT p.*,o.principal_kind,o.principal_identity FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id WHERE p.operation_id=?", (context.operation_id,)).fetchone()
        self.end_child_dispatch(context.operation_id)
        return self._context(row)

    def cancel(self, context: OuterRunContext, principal: Any) -> str:
        return self._cancel(context, principal)

    def expire_if_due(self, context: OuterRunContext, principal: Any) -> bool:
        """Fence an expired parent through its normal epoch-changing cancel path."""
        with self._database._connection() as conn:
            row = conn.execute("SELECT deadline_at,state FROM kernel_parent_runs WHERE operation_id=?", (context.operation_id,)).fetchone()
        if row is None or str(row["state"]) != "OPEN" or float(row["deadline_at"]) > self._clock():
            return False
        self._cancel(context, principal)
        with self._database._connection() as conn:
            row = conn.execute("SELECT p.*,o.principal_kind,o.principal_identity FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id WHERE p.operation_id=?", (context.operation_id,)).fetchone()
        if row is not None and str(row["state"]) == "CANCELLING":
            self.close(self._context(row), "cancelled", principal=principal)
        return True

    def cancel_by_operation_id(self, principal: Any, operation_id: str) -> str:
        """Route-only cancellation authority: exact durable owner, checked under lock."""
        with self._database._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT p.*,o.principal_kind,o.principal_identity FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id WHERE p.operation_id=?", (operation_id,)).fetchone()
            if row is None: raise KernelRefused("parent_operation_unknown")
            if principal.name != str(row["principal_kind"]) or principal.identity != str(row["principal_identity"]): raise KernelRefused("parent_operation_scope_required")
            context = self._context(row)
        disposition = self._cancel(context, principal)
        with self._database._connection() as conn:
            row = conn.execute("SELECT p.*,o.principal_kind,o.principal_identity FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id WHERE p.operation_id=?", (operation_id,)).fetchone()
        if row is not None and str(row["state"]) == "CANCELLING":
            receipt = self.close(self._context(row), "cancelled", principal=principal)
            return str(receipt.get("outcome") or disposition)
        # The provider signal may still be in flight ("pending"), but the
        # durable terminal receipt is the disposition the caller acts on.
        receipt = self._broker.store.receipt(operation_id)
        return str(receipt["outcome"]) if receipt else disposition

    def _cancel(self, context: OuterRunContext, principal: Any) -> str:
        with self._database._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT p.*,o.principal_kind,o.principal_identity FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id WHERE p.operation_id=?", (getattr(context, "operation_id", ""),)).fetchone()
            if row is None: raise KernelRefused("parent_operation_unknown")
            self._valid_context(context, row, principal)
            if str(row["state"]) != "OPEN": return str(row["state"]).lower()
            conn.execute("UPDATE kernel_parent_runs SET state='CANCELLING',execution_epoch=execution_epoch+1,active_child_invocation_id='',lease_heartbeat_at=?,updated_at=? WHERE operation_id=? AND state='OPEN' AND execution_epoch=?", (self._clock(), self._clock(), context.operation_id, context.epoch))
            child = str(row["active_child_invocation_id"] or "")
        self.end_child_dispatch(context.operation_id)
        if not child:
            return "cancelled"
        # Durable cancellation is already elected above. Do not let a provider's
        # in-flight dispatch hold the cancelling HTTP request hostage.
        from threading import Thread
        Thread(target=self._broker.inference_runner._cancel_internal, args=(child, principal), daemon=True).start()
        return "pending"

    def close(self, context: OuterRunContext, outcome: str, result_ref: str = "", *, principal: Any | None = None) -> Mapping[str, Any]:
        receipt, _ = self._close(context, outcome, result_ref, principal=principal)
        if receipt is None: raise KernelRefused("parent_operation_not_running")
        return receipt

    def _close(self, context: OuterRunContext, outcome: str, result_ref: str = "", *, principal: Any | None = None, stale_before: float | None = None, stale_process_id: str | None = None) -> tuple[Mapping[str, Any] | None, bool]:
        if outcome not in _OUTCOME_STATES: raise KernelRefused("receipt_outcome_unknown")
        with self._database._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT p.*,o.principal_kind,o.principal_identity,o.claimed_by,o.revision,o.target_ref,o.state AS operation_state FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id WHERE p.operation_id=?", (getattr(context, "operation_id", ""),)).fetchone()
            if row is None: raise KernelRefused("parent_operation_unknown")
            self._valid_context(context, row, principal)
            existing = conn.execute("SELECT * FROM kernel_receipts WHERE operation_id=?", (context.operation_id,)).fetchone()
            if existing is not None: return dict(existing), False
            winner = "cancelled" if str(row["state"]) == "CANCELLING" else outcome
            predicate, parameters = "", []
            if stale_before is not None:
                predicate, parameters = " AND lease_process_id IS ? AND (lease_heartbeat_at IS NULL OR lease_heartbeat_at < ?)", [stale_process_id, stale_before]
            changed = conn.execute("UPDATE kernel_parent_runs SET state=?,active_child_invocation_id='',lease_heartbeat_at=?,updated_at=? WHERE operation_id=? AND state IN ('OPEN','CANCELLING')" + predicate, (_OUTCOME_STATES[winner], self._clock(), self._clock(), context.operation_id, *parameters)).rowcount
            if changed != 1:
                if stale_before is not None: return None, False
                winner = next((key for key, value in _OUTCOME_STATES.items() if value == str(row["state"])), outcome)
            conn.execute("UPDATE kernel_operations SET state=?,revision=revision+1,updated_at=? WHERE operation_id=? AND state='claimed'", (winner, self._clock(), context.operation_id))
            conn.execute("INSERT OR IGNORE INTO kernel_receipts(receipt_id,operation_id,state,outcome,result_ref,created_at) VALUES(?,?,?,?,?,?)", ("rcpt_" + uuid.uuid4().hex, context.operation_id, winner, winner, result_ref if winner == outcome else "", self._clock()))
            receipt = conn.execute("SELECT * FROM kernel_receipts WHERE operation_id=?", (context.operation_id,)).fetchone()
        self.end_child_dispatch(context.operation_id)
        self._broker.store.append("operation.receipt", context.operation_id, refs=tuple(filter(None, (str(row["target_ref"]), str(receipt["result_ref"])))), head=str(receipt["outcome"]))
        return dict(receipt), True

    def reconcile_abandoned(self) -> int:
        now, closed = self._clock(), 0
        with self._database._connection() as conn:
            rows = conn.execute("SELECT p.*,o.principal_kind,o.principal_identity FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id WHERE p.state IN ('OPEN','CANCELLING') AND (p.lease_heartbeat_at IS NULL OR p.lease_heartbeat_at < ?)", (now-self._lease_seconds,)).fetchall()
        for row in rows:
            child = str(row["active_child_invocation_id"] or "")
            if child:
                try: self._broker.projection_stager.finalize(child)
                except KernelRefused: pass
            # Re-read under close transaction, using a controller-issued recovery context.
            try:
                context = self._context(row)
                _, changed = self._close(context, "indeterminate", stale_before=now-self._lease_seconds, stale_process_id=str(row["lease_process_id"] or "") or None)
                closed += int(changed)
            except KernelRefused: pass
        return closed


__all__ = ["OuterRunContext", "ParentRun", "ParentRunCodec", "ParentRunController"]
