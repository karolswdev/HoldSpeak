"""Receipt-gated projections for admitted Sequence and Workflow runs."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from .model import KernelRefused
from .projection_stager import _PublicationPermit


def _permit(conn: Any, permit: Any) -> None:
    if not isinstance(permit, _PublicationPermit):
        raise KernelRefused("projection_publication_permit_invalid")
    permit.use(conn)


def _receipt(conn: Any, stage: Any) -> str:
    row = conn.execute("SELECT receipt_id FROM kernel_receipts WHERE operation_id=?", (stage.operation_id,)).fetchone()
    if row is None:
        raise KernelRefused("projection_receipt_missing")
    return str(row["receipt_id"])


def materialize_child(conn: Any, stage: Any, permit: Any) -> dict[str, Any]:
    """Publish one receipt-backed checkpoint, conditional on the parent tuple.

    A stale child remains published as a receipt-linked fact, but its
    ``advanced`` marker is false and it cannot become Sequence/Workflow input.
    """
    _permit(conn, permit)
    result = dict(stage.projection)
    result.update({"invocation_id": stage.invocation_id, "operation_id": stage.operation_id,
                   "receipt_id": _receipt(conn, stage), "result_ref": stage.result_ref})
    try:
        parent_id = str(result["parent_operation_id"])
        epoch = int(result["execution_epoch"])
        planned = str(result["planned_node"])
    except (KeyError, TypeError, ValueError) as exc:
        raise KernelRefused("parent_checkpoint_tuple_missing") from exc
    # The permit is kernel-private and bound to this transaction; its stager is
    # broker-owned, so this cannot be redirected by a service payload.
    controller = permit._stager._broker.parent_run_controller
    result["advanced"] = controller.finalize_child_checkpoint(
        conn, stage_id=stage.stage_id, parent_operation_id=parent_id,
        child_invocation_id=stage.invocation_id, execution_epoch=epoch,
        planned_node=planned, checkpoint=result,
    )
    return result


def materialize_result(conn: Any, stage: Any, permit: Any) -> dict[str, Any]:
    """Create the one run Artifact inside the parent receipt publication txn."""
    _permit(conn, permit)
    p = dict(stage.projection)
    aid = str(p["artifact_id"])
    now = str(p.get("created_at") or datetime.now().isoformat())
    conn.execute(
        "INSERT INTO artifacts(id,meeting_id,origin,artifact_type,title,body_markdown,structured_json,confidence,status,plugin_id,plugin_version,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (aid, None, "run", "plugin_output", str(p["name"]), str(p["output"]),
         json.dumps({"parent_operation_id": p["parent_operation_id"], "kind": p["kind"]}, sort_keys=True),
         1.0, "draft", f"{p['kind']}_run", "1", now, now),
    )
    for source in p["sources"]:
        conn.execute("INSERT INTO artifact_sources(artifact_id,source_type,source_ref) VALUES(?,?,?)",
                     (aid, source["source_type"], source["source_ref"]))
    p.update({"invocation_id": stage.invocation_id, "operation_id": stage.operation_id,
              "receipt_id": _receipt(conn, stage), "result_ref": f"artifact:{aid}"})
    return p


def register(stager: Any) -> None:
    for kind in ("sequence-step-output", "workflow-node-output"):
        try:
            stager.register(kind, materialize_child)
        except ValueError:
            pass
    for kind in ("sequence-run-result", "workflow-run-result"):
        try:
            stager.register(kind, materialize_result)
        except ValueError:
            pass
