"""Receipt-backed checkpoint compare-and-swap for outer parent runs."""
from __future__ import annotations

import json
from typing import Any, Mapping

from .model import KernelRefused


def finalize(
    conn: Any,
    *,
    clock: Any,
    stage_id: str,
    parent_operation_id: str,
    child_invocation_id: str,
    execution_epoch: int,
    planned_node: str,
    checkpoint: Mapping[str, Any],
) -> bool:
    """Record a child checkpoint and advance only the matching active tuple."""
    row = conn.execute(
        "SELECT state,execution_epoch,planned_node,active_child_invocation_id "
        "FROM kernel_parent_runs WHERE operation_id=?", (parent_operation_id,)
    ).fetchone()
    if row is None:
        raise KernelRefused("parent_operation_unknown")
    exact = (
        str(row["state"]) == "OPEN"
        and int(row["execution_epoch"]) == int(execution_epoch)
        and str(row["planned_node"]) == planned_node
        and str(row["active_child_invocation_id"]) == child_invocation_id
    )
    now = clock()
    conn.execute(
        "INSERT OR IGNORE INTO kernel_parent_checkpoints("
        "stage_id,parent_operation_id,child_invocation_id,execution_epoch,planned_node,"
        "checkpoint_json,advanced,created_at) VALUES(?,?,?,?,?,?,?,?)",
        (stage_id, parent_operation_id, child_invocation_id, execution_epoch,
         planned_node, json.dumps(dict(checkpoint), sort_keys=True,
                                  separators=(",", ":")), int(exact), now),
    )
    if not exact:
        return False
    advanced = conn.execute(
        "UPDATE kernel_parent_runs SET planned_node='',active_child_invocation_id='',"
        "updated_at=? WHERE operation_id=? AND state='OPEN' AND execution_epoch=? "
        "AND planned_node=? AND active_child_invocation_id=?",
        (now, parent_operation_id, execution_epoch, planned_node, child_invocation_id),
    )
    return advanced.rowcount == 1
