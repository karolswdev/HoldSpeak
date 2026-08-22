"""Kernel-owned materializer for the receipt-gated Ask result projection."""
from __future__ import annotations

import json
import time
from typing import Any

from .model import KernelRefused
from .projection_stager import _PublicationPermit


def materialize(conn: Any, stage: Any, permit: Any) -> dict[str, Any]:
    if not isinstance(permit, _PublicationPermit):
        raise KernelRefused("projection_publication_permit_invalid")
    permit.use(conn)
    receipt = conn.execute(
        "SELECT receipt_id FROM kernel_receipts WHERE operation_id=?", (stage.operation_id,)
    ).fetchone()
    if receipt is None:
        raise KernelRefused("projection_receipt_missing")
    routed = conn.execute(
        """SELECT a.id AS attempt_id,e.state,e.terminal_outcome,e.winning_attempt_id
             FROM inference_route_attempts a
             JOIN inference_route_executions e ON e.id=a.execution_id
            WHERE a.child_operation_id=?""",
        (stage.operation_id,),
    ).fetchone()
    if routed is not None and (
        str(routed["state"]) != "terminal"
        or str(routed["terminal_outcome"]) != "succeeded"
        or str(routed["winning_attempt_id"]) != str(routed["attempt_id"])
    ):
        # A succeeded physical child is only a candidate.  Generic startup
        # recovery must never publish it before the controller settles the
        # logical route or when another attempt won.
        raise KernelRefused("projection_route_winner_missing")
    payload = dict(stage.projection)
    payload.update({
        "invocation_id": stage.invocation_id,
        "operation_id": stage.operation_id,
        "receipt_id": str(receipt["receipt_id"]),
        "result_ref": stage.result_ref,
    })
    conn.execute(
        "INSERT INTO ask_results(projection_stage_id,invocation_id,operation_id,receipt_id,payload_json,created_at) VALUES(?,?,?,?,?,?)",
        (stage.stage_id, stage.invocation_id, stage.operation_id, receipt["receipt_id"],
         json.dumps(payload, sort_keys=True, separators=(",", ":")), time.time()),
    )
    return payload


def register(stager: Any) -> None:
    try:
        stager.register("ask-result", materialize)
    except ValueError:
        # Router instances are short lived; one kernel registry is not.
        pass
