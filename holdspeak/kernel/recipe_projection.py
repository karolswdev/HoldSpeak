"""Kernel materializers for receipt-gated Recipe run and chat results."""
from __future__ import annotations
import json
import time
from typing import Any
from .model import KernelRefused
from .projection_stager import _PublicationPermit

def _receipt(conn, stage):
    row=conn.execute("SELECT receipt_id FROM kernel_receipts WHERE operation_id=?",(stage.operation_id,)).fetchone()
    if row is None: raise KernelRefused("projection_receipt_missing")
    return str(row["receipt_id"])
def _permit(conn, permit):
    if not isinstance(permit,_PublicationPermit): raise KernelRefused("projection_publication_permit_invalid")
    permit.use(conn)
def materialize_run(conn: Any, stage: Any, permit: Any) -> dict[str, Any]:
    _permit(conn,permit); p=dict(stage.projection); rid=_receipt(conn,stage); aid=str(p["artifact_id"])
    conn.execute("INSERT INTO artifacts(id,meeting_id,origin,artifact_type,title,body_markdown,structured_json,confidence,status,plugin_id,plugin_version,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(aid,None,"run","plugin_output",p["name"],p["output"],json.dumps({"recipe_id":p["recipe_id"]},sort_keys=True),1.0,"draft","recipe_run","1",p["created_at"],p["created_at"]))
    for source in p["sources"]: conn.execute("INSERT INTO artifact_sources(artifact_id,source_type,source_ref) VALUES(?,?,?)",(aid,source["source_type"],source["source_ref"]))
    conn.execute("INSERT INTO recipe_results(projection_stage_id,invocation_id,operation_id,receipt_id,artifact_id) VALUES(?,?,?,?,?)",(stage.stage_id,stage.invocation_id,stage.operation_id,rid,aid))
    p.update({"invocation_id":stage.invocation_id,"operation_id":stage.operation_id,"receipt_id":rid,"result_ref":stage.result_ref})
    return p
def materialize_chat(conn: Any, stage: Any, permit: Any) -> dict[str, Any]:
    _permit(conn,permit); p=dict(stage.projection); rid=_receipt(conn,stage)
    p.update({"invocation_id":stage.invocation_id,"operation_id":stage.operation_id,"receipt_id":rid,"result_ref":stage.result_ref})
    conn.execute("INSERT INTO recipe_chat_results(projection_stage_id,invocation_id,operation_id,receipt_id,payload_json,created_at) VALUES(?,?,?,?,?,?)",(stage.stage_id,stage.invocation_id,stage.operation_id,rid,json.dumps(p,sort_keys=True),time.time()))
    return p
def register(stager: Any) -> None:
    for kind, fn in (("recipe-run",materialize_run),("recipe-chat-result",materialize_chat)):
        try: stager.register(kind,fn)
        except ValueError: pass
