"""The scheduler-only delegated Workbench parent admission path (HS-131-06).

One typed concern carved from the parent controller: re-deriving bounded
schedule-delegation authority under the write lock, durably receipting
refused ticks, and the atomic delegated parent start (term recheck + due
minute claim + parent persistence + provenance in one transaction).
"""
from __future__ import annotations

import uuid
from typing import Any, Mapping

from ..principals import PrincipalKind
from .model import KernelRefused


def delegated_refusal(controller: Any, conn: Any, input_snapshot: Mapping[str, Any], *, authoritative: bool = False) -> tuple[str, Any | None]:
    """Re-derive all mutable schedule authority while the write lock is held."""
    delegation_id = str(input_snapshot.get("delegation_id") or "")
    row = conn.execute("SELECT * FROM kernel_schedule_delegations WHERE id=?", (delegation_id,)).fetchone()
    if row is None: return "delegation_missing", None
    if str(row["state"]) != "LIVE" or str(row["terms_sha256"]) != str(input_snapshot.get("terms_sha256") or ""):
        return "delegation_revoked", row
    if row["expires_at"] is not None and float(row["expires_at"]) <= controller._clock():
        if authoritative:
            conn.execute("UPDATE kernel_schedule_delegations SET state='EXPIRED',updated_at=? WHERE id=? AND state='LIVE'", (controller._clock(), delegation_id))
        return "delegation_expired", row
    # The durable LIVE delegation and its terms hash are the owner's authority.
    # A fire must not re-read mutable cadence, Workbench, Recipe, or deployment
    # selectors: supported owner edits revoke/reapprove this row first.
    return "", row


def record_delegated_refusal(controller: Any, principal: Any, *, definition_ref: str, definition_revision: str, input_snapshot: Mapping[str, Any], deadline_at: float, child_budget: int, idempotency_key: str, reason: str) -> Mapping[str, Any]:
    """Durably receipt a rejected scheduled tick before any dispatch exists."""
    native_id = "workbench_run_refused_" + uuid.uuid4().hex
    raw = {"request_schema": 1, "request_id": idempotency_key,
           "idempotency_key": idempotency_key,
           "operation": {"name": "workbench.run", "version": 1}, "target": {},
           "arguments": {"native_id": native_id, "definition_ref": definition_ref,
           "definition_revision": definition_revision, "input": dict(input_snapshot),
           "deadline_at": deadline_at, "child_budget": child_budget}}
    # A repeated due minute intentionally has the same idempotency key as
    # its successful predecessor; refusal attempts need their own journal key.
    delegation_id = str(input_snapshot.get("delegation_id") or "")
    with controller._database._connection() as conn:
        row = conn.execute("SELECT * FROM kernel_schedule_delegations WHERE id=?", (delegation_id,)).fetchone()
        if row is None and input_snapshot.get("workbench_id"):
            row = conn.execute("SELECT * FROM kernel_schedule_delegations WHERE workbench_id=? ORDER BY updated_at DESC LIMIT 1", (str(input_snapshot["workbench_id"]),)).fetchone()
    provenance = None if row is None else {"delegator_kind": str(row["delegator_kind"]), "delegator_identity": str(row["delegator_identity"]), "authority_basis": f"schedule-delegation:{row['id']}:{row['terms_sha256']}", "target_ref": f"deployment:{row['deployment_revision_id']}"}
    return controller._broker._refuse_attempt(raw, principal, "op_" + uuid.uuid4().hex, reason, unique=True, provenance=provenance)


def start_delegated_schedule(controller: Any, principal: Any, *, definition_ref: str, definition_revision: str, input_snapshot: Mapping[str, Any], deadline_at: float, child_budget: int, idempotency_key: str) -> Any:
    """Open the one scheduler-only parent path after local delegation validation.

    The broker guard is process-local and scoped to this call; public broker
    submission with a scheduler principal remains refused.
    """
    if principal.kind is not PrincipalKind.SCHEDULER:
        raise KernelRefused("scheduler_principal_required")
    # This is deliberately only a cheap read pre-check. It consumes neither
    # the due minute nor a delegation state; both are re-derived below.
    with controller._database._connection() as conn:
        refusal, _ = controller._delegated_refusal(conn, input_snapshot)
    if refusal:
        controller.record_delegated_refusal(principal, definition_ref=definition_ref, definition_revision=definition_revision, input_snapshot=input_snapshot, deadline_at=deadline_at, child_budget=child_budget, idempotency_key=idempotency_key, reason=refusal)
        raise KernelRefused(refusal)
    controller._broker._delegated_schedule_admission = True
    controller._delegated_parent_start = True
    try:
        # A rejected unconsumed minute must be retryable. Tick identity, not
        # broker idempotency, is the durable scheduler dedupe boundary.
        pending = controller.start(principal, kind="workbench", definition_ref=definition_ref, definition_revision=definition_revision, input_snapshot=input_snapshot, deadline_at=deadline_at, child_budget=child_budget, idempotency_key=idempotency_key + ":admission:" + uuid.uuid4().hex, _defer_persist=True)
    finally:
        controller._delegated_parent_start = False
        controller._broker._delegated_schedule_admission = False
    refusal = ""
    row = None
    with controller._database._connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        refusal, delegation = controller._delegated_refusal(conn, input_snapshot, authoritative=True)
        if not refusal:
            if conn.execute("INSERT OR IGNORE INTO kernel_schedule_ticks(workbench_id,due_minute,delegation_id,created_at) VALUES(?,?,?,?)", (str(delegation["workbench_id"]), int(input_snapshot.get("due_minute", -1)), str(delegation["id"]), controller._clock())).rowcount != 1:
                refusal = "duplicate_tick"
        if refusal:
            provenance = None if delegation is None else (str(delegation["delegator_kind"]), str(delegation["delegator_identity"]), f"schedule-delegation:{delegation['id']}:{delegation['terms_sha256']}", f"deployment:{delegation['deployment_revision_id']}")
            if provenance is None:
                conn.execute("UPDATE kernel_operations SET state='refused',revision=revision+1,updated_at=? WHERE operation_id=? AND state='claimed'", (controller._clock(), pending.operation_id))
            else:
                conn.execute("UPDATE kernel_operations SET state='refused',revision=revision+1,updated_at=?,delegator_kind=?,delegator_identity=?,authority_basis=?,target_ref=? WHERE operation_id=? AND state='claimed'", (controller._clock(), *provenance, pending.operation_id))
            conn.execute("INSERT OR IGNORE INTO kernel_receipts(receipt_id,operation_id,state,outcome,result_ref,created_at) VALUES(?,?,?,?,?,?)", ("rcpt_" + uuid.uuid4().hex, pending.operation_id, "refused", refusal, "", controller._clock()))
        else:
            row = controller._persist_parent(conn, operation_id=pending.operation_id, native_id=pending.native_id, kind="workbench", definition_ref=definition_ref, definition_revision=definition_revision, input_snapshot=input_snapshot, deadline_at=deadline_at, child_budget=child_budget, now=controller._clock())
            conn.execute("UPDATE kernel_operations SET authority_basis=?,delegator_kind=?,delegator_identity=?,target_ref=? WHERE operation_id=?", (f"schedule-delegation:{delegation['id']}:{delegation['terms_sha256']}", str(delegation["delegator_kind"]), str(delegation["delegator_identity"]), f"deployment:{delegation['deployment_revision_id']}", pending.operation_id))
    if refusal:
        controller._broker.store.append("operation.refused", pending.operation_id, head=refusal)
        controller._broker.store.append("operation.receipt", pending.operation_id, head=refusal)
        raise KernelRefused(refusal)
    if row is None: raise KernelRefused("parent_run_persistence_failed")
    from .parent_run import ParentRun
    return ParentRun(pending.operation_id, str(row["native_id"]), controller._context(row))
