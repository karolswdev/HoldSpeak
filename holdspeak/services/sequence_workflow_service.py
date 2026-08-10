"""Admitted execution services for Sequence and Workflow definitions."""
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
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _node_revision(node: Any) -> str:
    """One canonical frozen definition for both workflow payload and projection."""
    return _sha({"id": node.id, "kind": node.kind, "payload": node.payload,
                 "failure_policy": node.failure_policy, "runs_on": node.runs_on})


class SequenceWorkflowService:
    """Domain-owned linear execution using only trusted, admitted children."""
    def __init__(self, db: Any, broker: Any) -> None:
        self.db, self.broker, self.runner = db, broker, broker.inference_runner
        from ..kernel.sequence_workflow_projection import register
        register(broker.projection_stager)

    def _target(self, requested: Any, *, capability_default: Any = None):
        from ..inference_targets import resolve_placement
        # Phase-130 precedence is resolved independently at each eligible child.
        target = resolve_placement(self.db, invocation=str(requested or "") or None, agent=str(capability_default or "") or None).target
        if not target.ready:
            raise ServiceError("target_unavailable", target.readiness_reason, context={"status": 409, "inference_target": target.to_dict()})
        return target, capture_deployment_revision(self.db, target)

    def _invoke(self, principal: Principal, request: InvocationRequest, context: Any, planned: str, publish: Any):
        from ..kernel.model import KernelRefused
        from ..kernel.runtime import _as_principal
        try:
            with _as_principal(principal):
                return self.runner.invoke(request, CanonicalPromptAdapter(), parent_context=context, planned_node=planned, publish=publish)
        except KernelRefused as exc:
            raise ServiceError("inference_failed", exc.reason, context={"status": 502}) from exc

    def _children(self, parent_id: str) -> list[dict[str, Any]]:
        with self.db._connection() as conn:
            rows = conn.execute("SELECT operation_id,native_id FROM kernel_operations WHERE parent_operation_id=? ORDER BY created_at", (parent_id,)).fetchall()
        return [{"operation_id": str(r["operation_id"]), "invocation_id": str(r["native_id"]),
                 "outcome": str((self.broker.store.receipt(str(r["operation_id"])) or {}).get("outcome") or "")} for r in rows]

    def _close_or_adopt(self, parent: Any, outcome: str, *, principal: Principal, result_ref: str = "") -> dict[str, Any]:
        """Use this runner's close if live, otherwise report the elected receipt."""
        from ..kernel.model import KernelRefused
        try:
            return dict(self.broker.parent_run_controller.close(parent.context, outcome, result_ref, principal=principal))
        except KernelRefused as exc:
            receipt = self.broker.store.receipt(parent.operation_id)
            if exc.reason == "parent_context_invalid":
                # The canceler installs CANCELLING before its in-flight child
                # returns; wait briefly for that elected terminal receipt.
                for _ in range(100):
                    if receipt is not None:
                        return dict(receipt)
                    time.sleep(.01)
                    receipt = self.broker.store.receipt(parent.operation_id)
            raise

    def _terminal_result(self, parent: Any, kind: str, definition_id: str, receipt: dict[str, Any]) -> dict[str, Any]:
        return {"parent_operation_id": parent.operation_id, "parent_native_id": parent.native_id,
                "operation": f"{kind}.run", f"{kind}_id": definition_id,
                "receipt_id": receipt["receipt_id"], "terminal_disposition": receipt.get("outcome"),
                "children": self._children(parent.operation_id)}

    def _finish(self, parent: Any, principal: Principal, kind: str, definition_id: str, revision: str, output: str, sources: list[dict[str, str]], steps: list[dict[str, Any]], target: Any | None) -> dict[str, Any]:
        aid = "artifact_" + uuid.uuid4().hex[:12]
        stage = self.broker.projection_stager.stage(parent.native_id, f"{kind}-run-result", {
            "kind": kind, "parent_operation_id": parent.operation_id, "definition_revision": revision,
            "artifact_id": aid, "name": definition_id, "output": output, "sources": sources, "steps": steps,
            "created_at": datetime.now().isoformat(), "inference_target": target.to_dict() if target else None})
        receipt = self._close_or_adopt(parent, "succeeded", result_ref=stage.result_ref, principal=principal)
        if receipt.get("outcome") != "succeeded":
            return self._terminal_result(parent, kind, definition_id, receipt)
        result = self.broker.projection_stager.finalize(parent.native_id)
        if result is None:
            raise ServiceError("projection_not_published", "result is awaiting receipt reconciliation", context={"status": 409})
        result.update({"parent_operation_id": parent.operation_id, "parent_native_id": parent.native_id,
                       "operation": f"{kind}.run", "children": self._children(parent.operation_id),
                       "artifact_id": aid, "result_ref": f"artifact:{aid}"})
        return result

    def _fail(self, parent: Any, principal: Principal, exc: Exception) -> None:
        # A cross-request cancel invalidates this context, but its receipt is the
        # durable winner and must not turn the original service error into a kernel error.
        try:
            self._close_or_adopt(parent, "failed", principal=principal)
        except Exception:
            pass

    def _replay(self, parent: Any, kind: str, definition_id: str) -> dict[str, Any]:
        result = self.broker.projection_stager.finalize(parent.native_id)
        if result is None:
            raise ServiceError("parent_replay_unavailable", "This prior run has no published result.", context={"status": 409, "parent_operation_id": parent.operation_id})
        result.update({"parent_operation_id": parent.operation_id, "parent_native_id": parent.native_id,
                       "operation": f"{kind}.run", "children": self._children(parent.operation_id)})
        result[f"{kind}_id"] = definition_id
        return result

    async def run_sequence(self, principal: Principal, chain_id: str, body: dict[str, Any]) -> dict[str, Any]:
        chain = self.db.chains.get(chain_id)
        if chain is None: raise ServiceError("not_found", f"Unknown Sequence: {chain_id}", context={"status": 404})
        steps = list(chain.steps or [])
        parent = self.broker.parent_run_controller.start(principal, kind="sequence", definition_ref=f"sequence:{chain_id}", definition_revision=str(chain.last_modified), input_snapshot=dict(body), deadline_at=time.time()+60, child_budget=len(steps), idempotency_key=str(body.get("request_id") or "") or None)
        if parent.replayed:
            return self._replay(parent, "sequence", chain_id)
        if not steps:
            self.broker.parent_run_controller.close(parent.context, "refused", principal=principal)
            raise ServiceError("empty_sequence", "This Sequence has no Agents. Add one before running.", context={"status": 409, "parent_operation_id": parent.operation_id})
        from .support import _render_user_prompt
        current, records, sources, target = str(body.get("input") or ""), [], [{"source_type":"chain", "source_ref":chain_id}], None
        try:
            for ordinal, recipe_id in enumerate(steps, 1):
                recipe = self.db.recipes.get(str(recipe_id))
                if recipe is None: raise ServiceError("recipe_unavailable", f"Agent {recipe_id} is unavailable; the Sequence was not run. Repair the Sequence and run it again.", context={"status":409})
                prompt = _render_user_prompt(recipe.user_template, body.get("variables") if isinstance(body.get("variables"),dict) else {}, current)
                if not prompt.strip(): raise ServiceError("empty_input", f"Nothing to run for {recipe.name or recipe.id}; input is retained for Retry.", context={"status":400,"recipe_id":recipe.id})
                target, deployment = self._target(body.get("inference_target_id") or body.get("requested_placement"), capability_default=recipe.profile_id)
                payload={"sequence_ref":chain_id,"sequence_revision":str(chain.last_modified),"step_ordinal":ordinal,"recipe_id":recipe.id,"recipe_revision":str(recipe.last_modified),"system_prompt":recipe.system_prompt,"user_prompt":prompt,"deployment_revision":deployment.id,"temperature":float(body["temperature"]) if body.get("temperature") is not None else None,"max_tokens":int(body["max_tokens"]) if body.get("max_tokens") is not None else None,"attempt_ordinal":1}
                iid="sequence_child_"+uuid.uuid4().hex
                projection=lambda result, iid=iid, recipe=recipe, ordinal=ordinal, prompt=prompt, deployment=deployment, epoch=parent.context.epoch: {"parent_operation_id":parent.operation_id,"execution_epoch":epoch,"planned_node":f"step:{ordinal}","step_ordinal":ordinal,"recipe_id":recipe.id,"recipe_revision":str(recipe.last_modified),"output":str(result.get("output") if isinstance(result,dict) else result),"deployment_revision":deployment.id,"rendered_input_sha256":_sha(prompt),"provider":str(result.get("provider") if isinstance(result,dict) else "")}
                outcome=await asyncio.to_thread(self._invoke, principal, InvocationRequest(deployment.id,SavedDefinition(f"recipe:{recipe.id}",str(recipe.last_modified)),time.time()+60,payload,iid,parent.operation_id), parent.context, f"step:{ordinal}", self.broker.projection_stager.publisher(iid,"sequence-step-output",projection))
                if outcome.outcome!="succeeded": raise ServiceError("inference_failed",outcome.error or outcome.outcome,context={"status":502,"recipe_id":recipe.id})
                checkpoint=self.broker.projection_stager.finalize(iid)
                if checkpoint is None: raise ServiceError("projection_not_published","step is awaiting receipt reconciliation",context={"status":409})
                if not checkpoint.get("advanced"):
                    raise ServiceError("parent_child_stale", "The child receipt was retained but cannot advance this Sequence.", context={"status":409})
                current=str(checkpoint["output"]); records.append({"recipe_id":recipe.id,"output":current,"provider":str((checkpoint.get("provider") or target.engine))}); sources.append({"source_type":"recipe","source_ref":recipe.id})
            result=self._finish(parent,principal,"sequence",chain_id,str(chain.last_modified),current,sources,records,target)
            if result.get("terminal_disposition"):
                return result
            result.update({"chain_id":chain_id,"output":current,"provider":records[-1]["provider"],"steps":records,"sources":sources,"inference_target":target.to_dict(),"actual_placement":target.placement_receipt(provider=records[-1]["provider"])})
            return result
        except Exception as exc: self._fail(parent,principal,exc); raise

    async def run_workflow(self, principal: Principal, workflow_id: str, body: dict[str, Any]) -> dict[str, Any]:
        workflow=self.db.workflows.get(workflow_id)
        if workflow is None: raise ServiceError("not_found",f"Unknown workflow: {workflow_id}",context={"status":404})
        from .support import linearize, _MODEL_KINDS, _PURE_TRANSFORM_KINDS, _PASSTHROUGH_KINDS, apply_pure_transform, build_node_prompt, _render_user_prompt, resolved_failure_policy, on_node_error
        plan=linearize(workflow.graph_json) if workflow.graph_json else None
        executable=[] if plan is None else list(plan.ordered)
        unsupported_reason = (plan.reason if plan is not None and not plan.linearizable else "")
        unknown=[n for n in executable if n.kind not in _MODEL_KINDS and n.kind not in _PURE_TRANSFORM_KINDS and n.kind not in _PASSTHROUGH_KINDS]
        model_budget=sum(1 for n in executable if n.kind in _MODEL_KINDS)
        if plan is None and str(workflow.prompt or "").strip(): model_budget=1
        parent=self.broker.parent_run_controller.start(principal,kind="workflow",definition_ref=f"workflow:{workflow_id}",definition_revision=str(workflow.last_modified),input_snapshot=dict(body),deadline_at=time.time()+60,child_budget=model_budget,idempotency_key=str(body.get("request_id") or "") or None)
        if parent.replayed:
            return self._replay(parent, "workflow", workflow_id)
        if unsupported_reason or unknown:
            self.broker.parent_run_controller.close(parent.context,"refused",principal=principal)
            message = "This Workflow is unavailable on this host: "+unsupported_reason+". Open it in a compatible Workbench; it was not lowered to a prompt." if unsupported_reason else "This Workflow contains unsupported nodes."
            raise ServiceError("unsupported_graph",message,context={"status":409,"support":"unsupported_graph","parent_operation_id":parent.operation_id})
        current, records, sources, target=str(body.get("input") or ""), [], [{"source_type":"workflow","source_ref":workflow_id}], None
        # Replacements (retry/fallback) issue a fresh, higher-epoch capability.
        # Ordinary completed steps consume their tuple but remain in this epoch.
        context = parent.context
        try:
            if plan is None:
                prompt=_render_user_prompt(str(workflow.prompt or ""),body.get("variables") if isinstance(body.get("variables"),dict) else {},current)
                if not prompt.strip(): raise ServiceError("empty_workflow","This Workflow has no runnable graph or prompt; its input is retained.",context={"status":409})
                executable=[type("Prompt",(),{"id":"prompt","kind":"prompt","payload":{},"runs_on":"auto","failure_policy":None})()]
            for ordinal,node in enumerate(executable,1):
                if node.kind in _PURE_TRANSFORM_KINDS:
                    current=apply_pure_transform(node,current); records.append({"node_id":node.id,"kind":node.kind,"output":current,"provider":None,"status":"ok","runs_on":node.runs_on,"failure_policy":resolved_failure_policy(node)}); continue
                if node.kind in _PASSTHROUGH_KINDS:
                    continue
                prompt=_render_user_prompt(str(workflow.prompt),body.get("variables") if isinstance(body.get("variables"),dict) else {},current) if node.kind=="prompt" else build_node_prompt(node,current)
                if not prompt.strip(): continue
                target,deployment=self._target(body.get("inference_target_id") or body.get("requested_placement"))
                revision = _node_revision(node)
                payload={"workflow_ref":workflow_id,"workflow_revision":str(workflow.last_modified),"node_id":node.id,"node_revision":revision,"rendered_input":current,"system_prompt":"","user_prompt":prompt,"deployment_revision":deployment.id,"temperature":float(body["temperature"]) if body.get("temperature") is not None else None,"max_tokens":int(body["max_tokens"]) if body.get("max_tokens") is not None else None,"attempt_ordinal":1}
                iid="workflow_child_"+uuid.uuid4().hex; contract="holdspeak.workflow-prompt@1" if node.kind=="prompt" else "holdspeak.workflow-node@1"
                projection=lambda result, iid=iid, node=node, deployment=deployment, prompt=prompt, epoch=context.epoch, revision=revision: {"parent_operation_id":parent.operation_id,"execution_epoch":epoch,"planned_node":f"node:{node.id}","node_id":node.id,"node_revision":revision,"output":str(result.get("output") if isinstance(result,dict) else result),"deployment_revision":deployment.id,"rendered_input_sha256":_sha(prompt),"provider":str(result.get("provider") if isinstance(result,dict) else "")}
                origin=ServiceContract.for_payload(contract,"1",payload)
                outcome=await asyncio.to_thread(self._invoke,principal,InvocationRequest(deployment.id,origin,time.time()+60,payload,iid,parent.operation_id),context,f"node:{node.id}",self.broker.projection_stager.publisher(iid,"workflow-node-output",projection))
                if outcome.outcome!="succeeded":
                    handled=on_node_error(node,current)
                    if handled is None:
                        raise ServiceError("inference_failed",outcome.error or outcome.outcome,context={"status":502,"node_id":node.id})
                    # The legacy hub semantics treat skip and fallbackOnDevice as
                    # a pure carry-through.  They still supersede the failed
                    # active tuple before any later model child is admitted.
                    context=self.broker.parent_run_controller.supersede(context,principal)
                    parent=type(parent)(parent.operation_id,parent.native_id,context)
                    current=handled
                    records.append({"node_id":node.id,"kind":node.kind,"output":current,"provider":None,"status":"skipped" if resolved_failure_policy(node)=="skip" else "fell_back","runs_on":node.runs_on,"failure_policy":resolved_failure_policy(node),"error":outcome.error or outcome.outcome})
                    continue
                checkpoint=self.broker.projection_stager.finalize(iid)
                if checkpoint is None: raise ServiceError("projection_not_published","node is awaiting receipt reconciliation",context={"status":409})
                if not checkpoint.get("advanced"):
                    raise ServiceError("parent_child_stale", "The child receipt was retained but cannot advance this Workflow.", context={"status":409})
                current=str(checkpoint["output"]); records.append({"node_id":node.id,"kind":node.kind,"output":current,"provider":str(checkpoint.get("provider") or target.engine),"status":"ok","runs_on":node.runs_on,"failure_policy":resolved_failure_policy(node)})
            if not records: raise ServiceError("empty_workflow","Nothing executable ran; the Workflow input is retained for Retry.",context={"status":400})
            result=self._finish(parent,principal,"workflow",workflow_id,str(workflow.last_modified),current,sources,records,target)
            if result.get("terminal_disposition"):
                return result
            result.update({"workflow_id":workflow_id,"output":current,"provider":next((x["provider"] for x in reversed(records) if x["provider"]),None),"steps":records,"sources":sources,"inference_target":target.to_dict() if target else None,"actual_placement":target.placement_receipt(provider=next((x["provider"] for x in reversed(records) if x["provider"]),None)) if target else None})
            return result
        except Exception as exc: self._fail(parent,principal,exc); raise
