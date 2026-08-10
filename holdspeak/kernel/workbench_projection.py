"""Receipt-gated projections for admitted Workbench attempts."""
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


def _receipt(conn: Any, operation_id: str) -> str:
    row = conn.execute("SELECT receipt_id FROM kernel_receipts WHERE operation_id=?", (operation_id,)).fetchone()
    if row is None: raise KernelRefused("projection_receipt_missing")
    return str(row["receipt_id"])


def _child(conn: Any, stage: Any, permit: Any) -> dict[str, Any]:
    _permit(conn, permit)
    p = dict(stage.projection)
    p.update({"invocation_id":stage.invocation_id, "operation_id":stage.operation_id,
              "receipt_id":_receipt(conn, stage.operation_id), "result_ref":stage.result_ref})
    controller = permit._stager._broker.parent_run_controller
    p["advanced"] = controller.finalize_child_checkpoint(
        conn, stage_id=stage.stage_id, parent_operation_id=str(p["parent_operation_id"]),
        child_invocation_id=stage.invocation_id, execution_epoch=int(p["execution_epoch"]),
        planned_node=str(p["planned_node"]), checkpoint=p)
    if not p["advanced"]: return p
    now = datetime.now().isoformat()
    if stage.kind == "workbench-item-output":
        artifact_id = str(p["artifact_id"])
        conn.execute("UPDATE workbench_items SET status='done',result=?,result_egress_json=?,completed_at=?,last_modified=?,result_artifact_id=?,mint_attempted=1 WHERE id=?", (p["output"], json.dumps(p["egress"],sort_keys=True),now,now,artifact_id,str(p["item_id"])))
        conn.execute("INSERT OR IGNORE INTO artifacts(id,meeting_id,origin,artifact_type,title,body_markdown,structured_json,confidence,status,plugin_id,plugin_version,source_run_id,source_item_id,created_at,updated_at) VALUES(?,NULL,'run','workbench_output',?,?,?,0.0,'pending-review','workbench_run','1',?,?,?,?)", (artifact_id,p["artifact_title"],p["output"],json.dumps({"parent_operation_id":p["parent_operation_id"],"operation_id":stage.operation_id,"receipt_id":p["receipt_id"]},sort_keys=True),p["run_id"],p["item_id"],now,now))
    else:
        from ..workbench_memory import append_memory
        text = str(p.get("observation") or "").strip()
        if text and text.lower() not in {"nothing", "nothing."}:
            append_memory(str(p["workbench_id"]),str(p["run_id"]),"observation",text,item_title=str(p["item_title"]),provenance={"operation_id":stage.operation_id,"receipt_id":p["receipt_id"]})
    return p


def _run(conn: Any, stage: Any, permit: Any) -> dict[str, Any]:
    _permit(conn, permit)
    p = dict(stage.projection)
    # Receipt is the winner test: a cancelled parent may retain its stage but
    # cannot publish a completed native history row.
    row = conn.execute("SELECT state FROM kernel_parent_runs WHERE operation_id=?", (p["parent_operation_id"],)).fetchone()
    receipt = conn.execute("SELECT receipt_id,outcome FROM kernel_receipts WHERE operation_id=?", (p["parent_operation_id"],)).fetchone()
    if row is None or receipt is None or str(receipt["outcome"]) != "succeeded":
        p["advanced"] = False; return p
    now = datetime.now().isoformat()
    conn.execute("UPDATE workbench_runs SET completed_at=?,items_attempted=?,items_completed=?,items_failed=?,mint_failures=?,egress_boundary=?,model=?,constitutional_context_revision=?,constitutional_context_hash=?,skills_injected_json=?,status='completed' WHERE id=?", (now,p["attempted"],p["completed"],p["failed"],p["mint_failures"],p["egress_boundary"],p["model"],p["context_revision"],p["context_hash"],json.dumps(p["skills"]),p["run_id"]))
    p.update({"receipt_id":str(receipt["receipt_id"]),"advanced":True})
    return p


def register(stager: Any) -> None:
    for kind in ("workbench-item-output", "workbench-memory-writeback"):
        try: stager.register(kind, _child)
        except ValueError: pass
    try: stager.register("workbench-run-result", _run)
    except ValueError: pass
