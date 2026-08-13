"""Atomic admission transaction for controller-issued child operations."""
from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from typing import Any

from ..operation_policy import POLICY_VERSION
from .admission import parse_request
from .model import KernelRefused
from .parent_run import OuterRunContext


def submit(broker: Any, raw: Any, principal: Any, context: Any, *, planned_node: str) -> dict[str, Any]:
    """Admit a child and validate its parent capability in one write transaction.

    Parsing and codec selection precede the lock. No capability, owner, epoch,
    parent-state, or warrant observation made before ``BEGIN IMMEDIATE`` is used
    as authority after the boundary.
    """
    operation_id, request = "op_" + uuid.uuid4().hex, parse_request(raw)
    spec = broker._specs.get((request.name, request.version))
    if spec is None: raise KernelRefused("operation_type_unregistered")
    if not getattr(spec.codec, "trusted_child", False): raise KernelRefused("parent_context_client_supplied")
    broker._trusted_scheduler_child = principal.name == "scheduler"
    try:
        admission, layers = broker._admit_authority(request, spec, principal, operation_id)
    finally:
        broker._trusted_scheduler_child = False
    now = broker._clock()
    with broker.store._connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        # All authority starts here. Even a genuine object is untrusted until its
        # private identity and durable owner/epoch have been re-derived.
        parent_id = getattr(context, "operation_id", "")
        row = conn.execute("""SELECT o.*,p.execution_epoch,p.state AS parent_state,p.child_budget,p.children_json,p.deadline_at,
            p.publication_claim_id,p.native_id AS parent_native_id,p.input_json FROM kernel_operations o JOIN kernel_parent_runs p
            ON p.operation_id=o.operation_id WHERE o.operation_id=?""", (parent_id,)).fetchone()
        if row is None: raise KernelRefused("parent_operation_unknown")
        controller = getattr(broker, "parent_run_controller", None)
        if not isinstance(context, OuterRunContext) or controller is None:
            raise KernelRefused("parent_context_invalid")
        controller._valid_context(context, row, principal)
        if request.parent_operation_id != str(row["operation_id"]):
            raise KernelRefused("parent_context_client_supplied")
        if str(row["state"]) != "claimed" or str(row["parent_state"]) != "OPEN":
            raise KernelRefused("parent_operation_not_running")
        if str(row["publication_claim_id"] or ""):
            raise KernelRefused("parent_publication_in_progress")
        # A parent deadline is an execution fence, not annotation. The caller
        # closes it through the controller before dispatch; this lock still
        # rejects a child that races that closure.
        if float(row["deadline_at"]) <= now:
            raise KernelRefused("parent_deadline_expired")
        warrant = json.loads(str(row["warrant_json"] or "{}"))
        secret = conn.execute("SELECT value FROM kernel_meta WHERE key='warrant_secret'").fetchone()
        unsigned = {key: value for key, value in warrant.items() if key != "signature"}
        encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        signed = bool(secret) and hmac.compare_digest(str(warrant.get("signature") or ""), hmac.new(str(secret[0]).encode(), encoded.encode(), hashlib.sha256).hexdigest())
        if not signed or bool(row["warrant_revoked"]) or float(warrant.get("execution_expires_at") or 0) <= now:
            raise KernelRefused("parent_operation_not_live")
        children = json.loads(str(row["children_json"]))
        if len(children) >= int(row["child_budget"]): raise KernelRefused("parent_child_budget_exhausted")
        existing = conn.execute("SELECT * FROM kernel_operations WHERE principal_identity=? AND idempotency_key=?", (principal.identity, request.idempotency_key)).fetchone()
        if existing is not None:
            if str(existing["envelope_sha256"]) != admission.payload_hash: raise KernelRefused("idempotency_payload_mismatch", operation_id=str(existing["operation_id"]))
            return broker._handle(broker.store._operation(existing))
        parent_input = json.loads(str(row['input_json'] or '{}'))
        if str(row["principal_kind"]) == "scheduler":
            delegation = conn.execute("SELECT * FROM kernel_schedule_delegations WHERE id=?", (str(parent_input.get("delegation_id") or ""),)).fetchone()
            if delegation is None or str(delegation["state"]) != "LIVE" or str(delegation["terms_sha256"]) != str(parent_input.get("terms_sha256") or ""):
                raise KernelRefused("delegation_revoked")
            recipe = conn.execute("SELECT last_modified FROM recipes WHERE id=? AND deleted=0", (str(delegation["recipe_id"]),)).fetchone()
            if recipe is None or str(recipe["last_modified"]) != str(delegation["recipe_revision"]):
                raise KernelRefused("delegation_stale_work")
            if str(request.arguments.get("deployment_revision") or "") != str(delegation["deployment_revision_id"]):
                raise KernelRefused("delegation_target_changed")
        basis = (f"schedule-delegation:{parent_input.get('delegation_id')}:{parent_input.get('terms_sha256')}"
                 if principal.name == 'scheduler' else "authenticated_principal+declared_capability+hard_prerequisites+interruption_policy")
        conn.execute("""INSERT INTO kernel_operations(operation_id,request_id,idempotency_key,name,version,principal_kind,principal_identity,target_ref,placement,envelope_sha256,policy_version,authority_basis,state,revision,native_id,parent_operation_id,correlation_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (operation_id, request.request_id, request.idempotency_key, request.name, request.version, principal.name, principal.identity, admission.target_ref, admission.placement, admission.payload_hash, POLICY_VERSION, basis, "admitting", 1, admission.native_id, str(row["operation_id"]), str(row["correlation_id"] or row["operation_id"]), now, now))
        if principal.name == 'scheduler':
            conn.execute("UPDATE kernel_operations SET delegator_kind=?,delegator_identity=? WHERE operation_id=?", (str(row['delegator_kind']), str(row['delegator_identity']), operation_id))
        children.append(admission.native_id)
        changed = conn.execute("UPDATE kernel_parent_runs SET planned_node=?,active_child_invocation_id=?,children_json=?,lease_process_id=?,lease_heartbeat_at=?,updated_at=? WHERE operation_id=? AND state='OPEN' AND execution_epoch=? AND publication_claim_id=''", (planned_node, admission.native_id, json.dumps(children, separators=(",", ":")), controller._process_id, now, now, str(row["operation_id"]), int(row["execution_epoch"])))
        if changed.rowcount != 1: raise KernelRefused("parent_operation_not_running")
    controller.begin_child_dispatch(str(row["operation_id"]))
    broker.last_authority_layers = tuple(layers)
    broker.store.append("operation.admitted", operation_id, refs=admission.refs, head=admission.head, causation_id=str(row["operation_id"]))
    try:
        spec.codec.admit(request, admission, principal, operation_id)
        operation = broker.store.transition(operation_id, 1, "awaiting_decision")
        broker.store.append("operation.awaiting_decision", operation_id, refs=admission.refs)
        return broker._handle(operation)
    except Exception as exc:
        operation = broker.store.transition(operation_id, 1, "refused")
        receipt = broker._terminal(operation, "refused", str(getattr(exc, "reason", "native_admission_failed")))
        return broker._handle(operation, receipt)
