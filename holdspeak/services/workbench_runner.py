"""Admitted manual Workbench execution."""
from __future__ import annotations
import asyncio, hashlib, json, time, uuid
from datetime import datetime
from typing import Any
from ..deployment_revisions import capture_deployment_revision
from ..kernel.inference_runner import InvocationRequest, SavedDefinition, ServiceContract
from ..kernel.prompt_adapter import CanonicalPromptAdapter
from ..principals import Principal
from .errors import ServiceError


def _sha(value: Any) -> str:
    return "sha256:"+hashlib.sha256(json.dumps(value,sort_keys=True,default=str,separators=(",",":")).encode()).hexdigest()


def _children(db: Any, broker: Any, parent_id: str) -> list[dict[str,str]]:
    with db._connection() as conn:
        rows=conn.execute("SELECT operation_id,native_id FROM kernel_operations WHERE parent_operation_id=? ORDER BY created_at",(parent_id,)).fetchall()
    return [{"operation_id":str(r["operation_id"]),"invocation_id":str(r["native_id"]),"receipt_id":str((broker.store.receipt(str(r["operation_id"])) or {}).get("receipt_id") or "")} for r in rows]


class WorkbenchRunner:
    def __init__(self, db: Any, broker: Any) -> None:
        self.db,self.broker,self.runner=db,broker,broker.inference_runner
        from ..kernel.workbench_projection import register
        register(broker.projection_stager)

    def _target(self, wb: Any, recipe: Any):
        from ..inference_targets import resolve_placement
        target=resolve_placement(self.db,invocation=None,workbench=wb.profile_id,agent=recipe.profile_id).target
        if not target.ready: raise ServiceError("target_unavailable",target.readiness_reason,context={"status":409})
        return target,capture_deployment_revision(self.db,target)

    def _invoke(self, principal: Principal, request: InvocationRequest, context: Any, planned: str, publish: Any):
        from ..kernel.model import KernelRefused
        from ..kernel.runtime import _as_principal
        try:
            with _as_principal(principal):
                return self.runner.invoke(request,CanonicalPromptAdapter(),parent_context=context,planned_node=planned,publish=publish)
        except KernelRefused as exc:
            raise ServiceError("inference_failed",exc.reason,context={"status":502}) from exc

    def _winner(self, parent: Any) -> dict[str, Any] | None:
        """Return the durable receipt elected by a concurrent terminal path."""
        receipt = self.broker.store.receipt(parent.operation_id)
        return dict(receipt) if receipt is not None else None

    def _close_or_adopt(self, parent: Any, outcome: str, *, principal: Principal, result_ref: str = "") -> dict[str, Any]:
        """Close this parent, or adopt a cancellation that invalidated its context."""
        from ..kernel.model import KernelRefused
        try:
            return dict(self.broker.parent_run_controller.close(parent.context, outcome, result_ref, principal=principal))
        except KernelRefused as exc:
            winner = self._winner(parent)
            if exc.reason == "parent_context_invalid":
                for _ in range(100):
                    if winner is not None:
                        return winner
                    time.sleep(.01)
                    winner = self._winner(parent)
            raise

    def _record_terminal(self, run_id: str, parent: Any, receipt: dict[str, Any]) -> list[dict[str, str]]:
        """Make the coordination row point at the one durable terminal receipt."""
        links = _children(self.db, self.broker, parent.operation_id)
        outcome = str(receipt.get("outcome") or "indeterminate")
        status = "completed" if outcome == "succeeded" else outcome
        with self.db._connection() as conn:
            conn.execute("UPDATE workbench_runs SET parent_receipt_id=?,child_links_json=?,status=? WHERE id=?", (str(receipt["receipt_id"]), json.dumps(links), status, run_id))
        return links

    def _replayed_result(self, parent_operation_id: str) -> dict[str, Any]:
        """Return the durable native attempt behind an idempotent parent."""
        with self.db._connection() as conn:
            row=conn.execute("SELECT id,parent_receipt_id,child_links_json,status FROM workbench_runs WHERE parent_operation_id=?",(parent_operation_id,)).fetchone()
        receipt=self.broker.store.receipt(parent_operation_id)
        if row is not None:
            receipt_id=str(row["parent_receipt_id"] or (receipt or {}).get("receipt_id") or "")
            return {"run_id":str(row["id"]),"parent_operation_id":parent_operation_id,"receipt_id":receipt_id,"parent_receipt_id":receipt_id,"terminal_disposition":str(row["status"]),"replayed":True,"children":json.loads(row["child_links_json"] or "[]")}
        if receipt is None:
            raise ServiceError("parent_terminal_unresolved", "The replayed Workbench parent did not retain a terminal receipt.", context={"status": 409, "parent_operation_id": parent_operation_id})
        return {"parent_operation_id":parent_operation_id,"receipt_id":str(receipt["receipt_id"]),"parent_receipt_id":str(receipt["receipt_id"]),"terminal_disposition":str(receipt.get("outcome") or "indeterminate"),"replayed":True,"children":_children(self.db,self.broker,parent_operation_id)}

    def _adopt_terminal(self, run_id: str, parent: Any) -> dict[str, Any]:
        # cancel_by_operation_id makes CANCELLING durable before its in-flight
        # child returns; let that closer publish its elected receipt.
        receipt = self._winner(parent)
        if receipt is None:
            for _ in range(100):
                time.sleep(.01)
                receipt = self._winner(parent)
                if receipt is not None:
                    break
        if receipt is None:
            raise ServiceError("parent_terminal_unresolved", "The Workbench parent did not retain a terminal receipt.", context={"status": 409, "parent_operation_id": parent.operation_id})
        links = self._record_terminal(run_id, parent, receipt)
        return {"run_id": run_id, "parent_operation_id": parent.operation_id, "receipt_id": receipt["receipt_id"], "terminal_disposition": receipt.get("outcome"), "children": links}

    async def run(self, principal: Principal, workbench_id: str, *, memory_enabled: bool=True, request_id: str|None=None, deadline_seconds: float=60) -> dict[str,Any]:
        wb=self.db.workbenches.get(workbench_id)
        if wb is None: raise ServiceError("not_found","Unknown Workbench",context={"status":404})
        recipe=self.db.recipes.get(wb.recipe_id) if wb.recipe_id else None
        if recipe is None: return {"error":f"workbench {wb.name}: no recipe assigned"}
        if request_id:
            with self.db._connection() as conn:
                existing=conn.execute("SELECT p.operation_id FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id WHERE o.principal_kind=? AND o.principal_identity=? AND o.idempotency_key=? AND p.kind='workbench' AND p.definition_ref=?",(principal.name,principal.identity,request_id,f"workbench:{workbench_id}")).fetchone()
            if existing is not None and self.broker.store.receipt(str(existing["operation_id"])) is not None:
                return self._replayed_result(str(existing["operation_id"]))
        items=self.db.workbench_items.list_for_workbench(workbench_id,status="pending")
        run_id="wbrun_"+uuid.uuid4().hex[:12]; deadline=time.time()+deadline_seconds
        snapshot={"workbench_id":workbench_id,"items":[x.id for x in items],"recipe_id":recipe.id,"recipe_revision":str(recipe.last_modified),"memory_enabled":memory_enabled,"request_id":request_id or ""}
        parent=self.broker.parent_run_controller.start(principal,kind="workbench",definition_ref=f"workbench:{workbench_id}",definition_revision=str(wb.last_modified),input_snapshot=snapshot,deadline_at=deadline,child_budget=len(items)*(2 if memory_enabled else 1),idempotency_key=request_id)
        if parent.replayed:
            return self._replayed_result(parent.operation_id)
        # This is coordination metadata only; its receipt links are always retained.
        with self.db._connection() as conn:
            conn.execute("INSERT INTO workbench_runs(id,workbench_id,started_at,parent_operation_id,parent_receipt_id,child_links_json,status) VALUES(?,?,?,?,'','[]','running')",(run_id,workbench_id,datetime.now().isoformat(),parent.operation_id))
        if not items:
            receipt=self._close_or_adopt(parent,"succeeded",principal=principal)
            if receipt.get("outcome") != "succeeded":
                return self._adopt_terminal(run_id,parent)
            self._record_terminal(run_id,parent,receipt)
            return {"skipped":True,"reason":"no pending items","run_id":run_id,"parent_operation_id":parent.operation_id,"receipt_id":receipt["receipt_id"]}
        from ..workbench_conductor import _assemble_recipe_context,_hydrate_item_grounding,inject_skills,constitutional_receipt
        system=inject_skills(self.db,recipe.system_prompt or f"You are {recipe.name}, a helpful assistant.",recipe.id)
        context=_assemble_recipe_context(self.db,recipe); memory=""
        if memory_enabled:
            from ..workbench_memory import recall_for_prompt
            memory=recall_for_prompt(workbench_id)
        skills=[s.id for s in self.db.skills.list_for_recipe(recipe.id,active_only=True)]
        complete=failed=mints=0
        try:
            for ordinal,item in enumerate(items,1):
                if self.broker.parent_run_controller.expire_if_due(parent.context,principal):
                    return self._adopt_terminal(run_id,parent)
                now=datetime.now().isoformat(); self.db.workbench_items.upsert(item_id=item.id,workbench_id=workbench_id,title=item.title,body=item.body,priority=item.priority,status="claimed",claimed_at=now)
                parts=[x for x in (context,memory,_hydrate_item_grounding(self.db,item.grounding_json),f"[TASK]\n{item.title}",item.body) if x]
                prompt="\n\n".join(parts); target,deployment=self._target(wb,recipe); iid="workbench_item_"+uuid.uuid4().hex
                payload={"workbench_id":workbench_id,"workbench_revision":str(wb.last_modified),"item_id":item.id,"item_revision":str(item.last_modified),"recipe_id":recipe.id,"recipe_revision":str(recipe.last_modified),"system_prompt":system,"user_prompt":prompt,"rendered_input_sha256":_sha(prompt),"skills":skills,"context_hash":_sha(context),"attempt_ordinal":ordinal,"deployment_revision":deployment.id}
                projection=lambda r,iid=iid,item=item,target=target,epoch=parent.context.epoch: {"parent_operation_id":parent.operation_id,"execution_epoch":epoch,"planned_node":f"item:{item.id}","run_id":run_id,"workbench_id":workbench_id,"item_id":item.id,"output":str(r.get("output") if isinstance(r,dict) else r),"egress":{"boundary":target.boundary,"model":target.model},"artifact_id":"artifact_"+iid[-12:],"artifact_title":f"{recipe.name or recipe.id}: {item.title}"}
                outcome=await asyncio.to_thread(self._invoke,principal,InvocationRequest(deployment.id,SavedDefinition(f"recipe:{recipe.id}",str(recipe.last_modified)),min(deadline,time.time()+60),payload,iid,parent.operation_id),parent.context,f"item:{item.id}",self.broker.projection_stager.publisher(iid,"workbench-item-output",projection))
                # The deadline is an execution fence: a dispatch that returns
                # past it must not advance. Expiry bumps the epoch, so the
                # child's staged output stays receipt-linked but stale.
                if self.broker.parent_run_controller.expire_if_due(parent.context,principal):
                    return self._adopt_terminal(run_id,parent)
                if outcome.outcome!="succeeded":
                    # Cancellation can arrive while the provider is in flight.
                    # Do not turn that elected parent outcome into an item failure.
                    if outcome.outcome in {"cancelled", "indeterminate"} or self._winner(parent) is not None:
                        return self._adopt_terminal(run_id,parent)
                    failed+=1; self.db.workbench_items.upsert(item_id=item.id,workbench_id=workbench_id,title=item.title,body=item.body,priority=item.priority,status="failed",result=f"Error: {outcome.error or outcome.outcome}",completed_at=datetime.now().isoformat()); continue
                check=self.broker.projection_stager.finalize(iid)
                if not check or not check.get("advanced"):
                    # A checkpoint that cannot advance lost the parent election.
                    # Its child receipt remains durable; never mint a success aggregate.
                    return self._adopt_terminal(run_id,parent)
                complete+=1
                if not memory_enabled or self.broker.parent_run_controller.expire_if_due(parent.context,principal): continue
                target,deployment=self._target(wb,recipe)
                mid="workbench_memory_"+uuid.uuid4().hex; out=str(check["output"]); mp={"workbench_id":workbench_id,"item_id":item.id,"parent_operation_id":parent.operation_id,"source_item_invocation_id":iid,"source_item_operation_id":check["operation_id"],"source_item_receipt_id":check["receipt_id"],"source_output_sha256":_sha(out),"source_output":out[:500],"prompt_contract_revision":"1","deployment_revision":deployment.id}
                mprompt="Based on the task and your output, what ONE thing should future runs on this workbench remember? Reply with a single sentence. If nothing is worth remembering, reply exactly 'nothing'."
                publish=lambda r,epoch=parent.context.epoch,item=item: {"parent_operation_id":parent.operation_id,"execution_epoch":epoch,"planned_node":f"memory:{item.id}","run_id":run_id,"workbench_id":workbench_id,"item_title":item.title,"observation":str(r.get("output") if isinstance(r,dict) else r),"source_item_receipt_id":check["receipt_id"]}
                mpayload={**mp,"system_prompt":"You are a concise assistant. Reply in one sentence only.","user_prompt":f"Task: {item.title}\n\nYour output:\n{out[:500]}\n\n{mprompt}"}
                mo=await asyncio.to_thread(self._invoke,principal,InvocationRequest(deployment.id,ServiceContract.for_payload("holdspeak.workbench-memory@1","1",mpayload),min(deadline,time.time()+60),mpayload,mid,parent.operation_id),parent.context,f"memory:{item.id}",self.broker.projection_stager.publisher(mid,"workbench-memory-writeback",publish))
                if mo.outcome=="succeeded": self.broker.projection_stager.finalize(mid)
            ctx=constitutional_receipt(); stage=self.broker.projection_stager.stage(parent.native_id,"workbench-run-result",{"parent_operation_id":parent.operation_id,"run_id":run_id,"attempted":len(items),"completed":complete,"failed":failed,"mint_failures":mints,"egress_boundary":"","model":"","context_revision":ctx["revision"],"context_hash":ctx["content_hash"],"skills":skills})
            receipt=self._close_or_adopt(parent,"succeeded",principal=principal,result_ref=stage.result_ref)
            if receipt.get("outcome") != "succeeded":
                return self._adopt_terminal(run_id,parent)
            self.broker.projection_stager.finalize(parent.native_id)
            links=self._record_terminal(run_id,parent,receipt)
            return {"run_id":run_id,"parent_operation_id":parent.operation_id,"receipt_id":receipt["receipt_id"],"children":links}
        except Exception:
            receipt=self._close_or_adopt(parent,"failed",principal=principal)
            self._record_terminal(run_id,parent,receipt)
            raise
