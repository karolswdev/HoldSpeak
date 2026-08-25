"""Cancellation and terminal receipt elections for durable parent runs."""
from __future__ import annotations

import time
import uuid
from threading import Thread
from typing import Any, Mapping

from .model import KernelRefused

_OUTCOME_STATES = {
    "succeeded": "SUCCEEDED",
    "failed": "FAILED",
    "cancelled": "CANCELLED",
    "refused": "REFUSED",
    "indeterminate": "INDETERMINATE",
}


def cancel_parent(controller: Any, context: Any, principal: Any) -> str:
    wait_until = time.monotonic() + controller._publication_wait_seconds
    while True:
        with controller._database._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT p.*,o.principal_kind,o.principal_identity "
                "FROM kernel_parent_runs p JOIN kernel_operations o "
                "ON o.operation_id=p.operation_id WHERE p.operation_id=?",
                (getattr(context, "operation_id", ""),),
            ).fetchone()
            if row is None:
                raise KernelRefused("parent_operation_unknown")
            controller._valid_context(context, row, principal)
            if str(row["state"]) != "OPEN":
                return str(row["state"]).lower()
            if str(row["publication_claim_id"] or ""):
                if time.monotonic() >= wait_until:
                    return "pending"
                child = ""
            else:
                changed = conn.execute(
                    "UPDATE kernel_parent_runs SET state='CANCELLING',"
                    "execution_epoch=execution_epoch+1,active_child_invocation_id='',"
                    "lease_heartbeat_at=?,updated_at=? WHERE operation_id=? "
                    "AND state='OPEN' AND execution_epoch=? "
                    "AND publication_claim_id=''",
                    (
                        controller._clock(),
                        controller._clock(),
                        context.operation_id,
                        context.epoch,
                    ),
                ).rowcount
                if changed != 1:
                    continue
                child = str(row["active_child_invocation_id"] or "")
                break
        time.sleep(0.01)
    controller.end_child_dispatch(context.operation_id)
    if not child:
        return "cancelled"
    # Durable cancellation is already elected above. Do not let a provider's
    # in-flight dispatch hold the cancelling HTTP request hostage.
    Thread(
        target=controller._broker.inference_runner._cancel_internal,
        args=(child, principal),
        daemon=True,
    ).start()
    return "pending"


def close_parent(
    controller: Any,
    context: Any,
    outcome: str,
    result_ref: str = "",
    *,
    principal: Any | None = None,
    stale_before: float | None = None,
    stale_process_id: str | None = None,
    publication_claim_id: str = "",
    executor_lease: Mapping[str, Any] | None = None,
) -> tuple[Mapping[str, Any] | None, bool]:
    if outcome not in _OUTCOME_STATES:
        raise KernelRefused("receipt_outcome_unknown")
    with controller._database._connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT p.*,o.principal_kind,o.principal_identity,o.claimed_by,"
            "o.revision,o.target_ref,o.state AS operation_state "
            "FROM kernel_parent_runs p JOIN kernel_operations o "
            "ON o.operation_id=p.operation_id WHERE p.operation_id=?",
            (getattr(context, "operation_id", ""),),
        ).fetchone()
        if row is None:
            raise KernelRefused("parent_operation_unknown")
        controller._valid_context(context, row, principal)
        if executor_lease is not None:
            job_id = str(executor_lease.get("job_id") or "")
            token = str(executor_lease.get("token") or "")
            try:
                epoch = int(executor_lease.get("epoch") or 0)
            except (TypeError, ValueError):
                return None, False
            owner = conn.execute(
                """SELECT 1 FROM intel_jobs WHERE job_id=? AND parent_operation_id=?
                   AND executor_lease_token=? AND executor_lease_epoch=?
                   AND status IN ('claimed','running','succeeded','superseded','failed')
                   AND executor_lease_expires_at>?""",
                (job_id, context.operation_id, token, epoch, time.time()),
            ).fetchone()
            if owner is None:
                # This is the actual parent-receipt fence: the same IMMEDIATE
                # transaction cannot race a lease takeover between check and close.
                return None, False
        existing = conn.execute(
            "SELECT * FROM kernel_receipts WHERE operation_id=?",
            (context.operation_id,),
        ).fetchone()
        if existing is not None:
            return dict(existing), False
        durable_claim = str(row["publication_claim_id"] or "")
        if durable_claim and durable_claim != str(publication_claim_id or ""):
            claimed_at = float(row["publication_claimed_at"] or 0.0)
            if stale_before is None or not claimed_at or claimed_at >= stale_before:
                if stale_before is not None:
                    return None, False
                raise KernelRefused("parent_publication_in_progress")
            # Reconciliation alone may clear a claim whose publication owner and
            # parent lease are both stale. It still closes through the ordinary
            # stale-process predicate below.
            conn.execute(
                "UPDATE kernel_parent_runs SET publication_claim_id='',"
                "publication_claimed_at=NULL WHERE operation_id=? "
                "AND publication_claim_id=?",
                (context.operation_id, durable_claim),
            )
            durable_claim = ""
        elif publication_claim_id and durable_claim != publication_claim_id:
            raise KernelRefused("parent_publication_claim_lost")
        winner = "cancelled" if str(row["state"]) == "CANCELLING" else outcome
        predicate, parameters = "", []
        if stale_before is not None:
            predicate = (
                " AND lease_process_id IS ? AND "
                "(lease_heartbeat_at IS NULL OR lease_heartbeat_at < ?)"
            )
            parameters = [stale_process_id, stale_before]
        settle_claim = ""
        if durable_claim:
            settle_claim = ",publication_claim_id='',publication_claimed_at=NULL"
            predicate += " AND publication_claim_id=?"
            parameters.append(durable_claim)
        changed = conn.execute(
            "UPDATE kernel_parent_runs SET state=?,active_child_invocation_id='',"
            "lease_heartbeat_at=?,updated_at=?" + settle_claim +
            " WHERE operation_id=? AND state IN ('OPEN','CANCELLING')" + predicate,
            (
                _OUTCOME_STATES[winner],
                controller._clock(),
                controller._clock(),
                context.operation_id,
                *parameters,
            ),
        ).rowcount
        if changed != 1:
            if stale_before is not None:
                return None, False
            if durable_claim:
                raise KernelRefused("parent_publication_claim_lost")
            winner = next(
                (
                    key
                    for key, value in _OUTCOME_STATES.items()
                    if value == str(row["state"])
                ),
                outcome,
            )
        conn.execute(
            "UPDATE kernel_operations SET state=?,revision=revision+1,updated_at=? "
            "WHERE operation_id=? AND state='claimed'",
            (winner, controller._clock(), context.operation_id),
        )
        conn.execute(
            "INSERT OR IGNORE INTO kernel_receipts(receipt_id,operation_id,state,"
            "outcome,result_ref,created_at) VALUES(?,?,?,?,?,?)",
            (
                "rcpt_" + uuid.uuid4().hex,
                context.operation_id,
                winner,
                winner,
                result_ref if winner == outcome else "",
                controller._clock(),
            ),
        )
        receipt = conn.execute(
            "SELECT * FROM kernel_receipts WHERE operation_id=?",
            (context.operation_id,),
        ).fetchone()
    controller.end_child_dispatch(context.operation_id)
    controller._broker.store.append(
        "operation.receipt",
        context.operation_id,
        refs=tuple(
            filter(None, (str(row["target_ref"]), str(receipt["result_ref"])))
        ),
        head=str(receipt["outcome"]),
    )
    return dict(receipt), True


__all__ = ["cancel_parent", "close_parent"]
