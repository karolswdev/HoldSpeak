"""Admitted manual Workbench execution."""
from __future__ import annotations
import asyncio, hashlib, json, time, uuid
from datetime import datetime
from typing import Any
from ..kernel.prompt_adapter import CanonicalPromptAdapter
from ..principals import Principal, PrincipalKind
from .errors import ServiceError
from .inference_parent_route_bundle_service import InferenceParentRouteBundleService
from .inference_route_plan_service import ROUTE_PLANNING_AUTHORITY


def _sha(value: Any) -> str:
    return "sha256:"+hashlib.sha256(json.dumps(value,sort_keys=True,default=str,separators=(",",":")).encode()).hexdigest()


def _children(db: Any, broker: Any, parent_id: str) -> list[dict[str,str]]:
    with db._connection() as conn:
        rows=conn.execute("SELECT operation_id,native_id FROM kernel_operations WHERE parent_operation_id=? ORDER BY created_at",(parent_id,)).fetchall()
    return [{"operation_id":str(r["operation_id"]),"invocation_id":str(r["native_id"]),"receipt_id":str((broker.store.receipt(str(r["operation_id"])) or {}).get("receipt_id") or "")} for r in rows]


class WorkbenchRunner:
    def __init__(self, db: Any, broker: Any) -> None:
        self.db,self.broker=db,broker
        from ..kernel.workbench_projection import register
        register(broker.projection_stager)

    @staticmethod
    def _route_target(route: dict[str, Any], ordinal: int = 1) -> dict[str, str]:
        """Project egress only from a frozen route entry, never a live target."""
        entry = dict(route["entries"][ordinal - 1])
        return {
            "boundary": str(entry["boundary"]),
            "model": str(entry["profile_id"]).removeprefix("legacy-"),
            "deployment_revision_id": str(entry["deployment_revision_id"]),
        }

    def _scheduled_route(self, delegation: dict[str, Any]) -> dict[str, Any]:
        """Read the owner-enabled route by its immutable delegation identity."""
        command_id = f"schedule-delegation-route-{delegation['id']}"
        with self.db._connection() as conn:
            row = conn.execute(
                "SELECT plan_id FROM inference_route_plan_commands WHERE command_id=?",
                (command_id,),
            ).fetchone()
        if row is None:
            raise ServiceError(
                "delegation_route_missing", "The schedule has no frozen route terms.",
                context={"status": 409},
            )
        return self.broker.inference_adoption_service.plans.get_route_plan(
            ROUTE_PLANNING_AUTHORITY, str(row["plan_id"])
        )

    async def _run_frozen_child(
        self,
        principal: Principal,
        *,
        parent: Any,
        route_plan_id: str,
        capability_id: str,
        command_id: str,
        operation_id: str,
        payload: dict[str, Any],
        reserved_output_tokens: int,
        publish: Any,
        planned_node: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Attach one child payload to the parent's frozen route and execute it."""
        admitted = await asyncio.to_thread(
            self.broker.inference_adoption_service.admit_on_frozen_route,
            principal,
            command_id=command_id,
            route_plan_id=route_plan_id,
            capability_id=capability_id,
            operation_id=operation_id,
            payload=payload,
            reserved_output_tokens=reserved_output_tokens,
            parent_operation_id=parent.operation_id,
        )
        routed = await asyncio.to_thread(
            self.broker.inference_adoption_service.execute,
            principal,
            execution_id=admitted["execution"]["id"],
            adapter=CanonicalPromptAdapter(),
            publish=publish,
            parent_context=parent.context,
            planned_node=planned_node,
        )
        return routed, admitted["route_plan"]

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

    def _record_terminal(self, run_id: str, parent: Any, receipt: dict[str, Any], *, attempted: int = 0, completed: int = 0, failed: int = 0) -> list[dict[str, str]]:
        """Make the coordination row point at the one durable terminal receipt."""
        links = _children(self.db, self.broker, parent.operation_id)
        outcome = str(receipt.get("outcome") or "indeterminate")
        status = "completed" if outcome == "succeeded" else outcome
        with self.db._connection() as conn:
            conn.execute("UPDATE workbench_runs SET parent_receipt_id=?,child_links_json=?,status=? WHERE id=?", (str(receipt["receipt_id"]), json.dumps(links), status, run_id))
        # HS-132-03: every terminal — succeeded, cancelled, expired, failed —
        # funnels through here, so this is the one honest place the desk hears
        # a run end. Adopted terminals carry no counts; the disposition is the
        # truth they do carry.
        self._emit_run_complete(run_id, outcome, attempted=attempted, completed=completed, failed=failed)
        return links

    def _emit_run_complete(self, run_id: str, disposition: str, *, attempted: int, completed: int, failed: int) -> None:
        """Tell every open surface this run reached its terminal."""
        try:
            from ..workbench_conductor import emit_run_complete
            with self.db._connection() as conn:
                row = conn.execute("SELECT workbench_id FROM workbench_runs WHERE id=?", (run_id,)).fetchone()
                workbench_id = str(row["workbench_id"]) if row is not None else ""
                pending = conn.execute("SELECT COUNT(*) AS n FROM workbench_items WHERE workbench_id=? AND status='pending'", (workbench_id,)).fetchone()
            emit_run_complete(
                workbench_id=workbench_id, run_id=run_id, disposition=disposition,
                attempted=attempted, completed=completed, failed=failed,
                pending_count=int(pending["n"]) if pending is not None else 0,
            )
        except Exception:
            pass  # a deaf desk never fails a run

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

    def _release_unpublished_claim(self, item_id: str) -> None:
        """Return a claim that lost its parent election to the pending queue."""
        with self.db._connection() as conn:
            conn.execute(
                """UPDATE workbench_items SET status='pending', claimed_at=NULL
                   WHERE id=? AND status='claimed' AND (result IS NULL OR result='')""",
                (item_id,),
            )

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

    async def run(self, principal: Principal, workbench_id: str, *, memory_enabled: bool=True, request_id: str|None=None, deadline_seconds: float=60, delegation: dict[str, Any] | None = None, due_minute: int | None = None, source_event: dict[str, str] | None = None, item_ids: list[str] | None = None) -> dict[str,Any]:
        if principal is None or principal.kind is PrincipalKind.NONE:
            from ..kernel.model import KernelRefused
            raise KernelRefused("principal_authentication_required")
        wb=self.db.workbenches.get(workbench_id)
        if wb is None: raise ServiceError("not_found","Unknown Workbench",context={"status":404})
        recipe=self.db.recipes.get(wb.recipe_id) if wb.recipe_id else None
        if recipe is None: return {"error":f"workbench {wb.name}: no recipe assigned"}
        if request_id and delegation is None:
            with self.db._connection() as conn:
                existing=conn.execute("SELECT p.operation_id FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id WHERE o.principal_kind=? AND o.principal_identity=? AND o.idempotency_key=? AND p.kind='workbench' AND p.definition_ref=?",(principal.name,principal.identity,request_id,f"workbench:{workbench_id}")).fetchone()
            if existing is not None and self.broker.store.receipt(str(existing["operation_id"])) is not None:
                return self._replayed_result(str(existing["operation_id"]))
        items=self.db.workbench_items.list_for_workbench(workbench_id,status="pending")
        if item_ids is not None:
            requested=list(dict.fromkeys(str(item_id) for item_id in item_ids if item_id))
            by_id={item.id:item for item in items}
            missing=[item_id for item_id in requested if item_id not in by_id]
            if missing:
                raise ServiceError("item_not_pending","A scoped Workbench item is missing or no longer pending",context={"status":409,"item_ids":missing})
            items=[by_id[item_id] for item_id in requested]
        if principal.kind is PrincipalKind.OWNER:
            self.broker.inference_adoption_service.migrate_recipe_workbench_subject_assignments(principal)
        run_id="wbrun_"+uuid.uuid4().hex[:12]; deadline=time.time()+deadline_seconds
        snapshot={"workbench_id":workbench_id,"items":[x.id for x in items],"item_scope":"explicit" if item_ids is not None else "pending_batch","recipe_id":recipe.id,"recipe_revision":str(recipe.last_modified),"memory_enabled":memory_enabled,"request_id":request_id or "","source_event":dict(source_event or {})}
        if delegation is not None:
            route = self._scheduled_route(delegation)
            snapshot.update({"delegation_id": delegation["id"], "terms_sha256": delegation["terms_sha256"],
                             "delegator_kind": delegation["delegator_kind"], "delegator_identity": delegation["delegator_identity"],
                             "deployment_revision_id": delegation["deployment_revision_id"],
                             "route_plan_id": route["id"], "route_plan_sha256": route["sha256"],
                             "due_minute": due_minute})
            parent=self.broker.parent_run_controller.start_delegated_schedule(principal,definition_ref=f"workbench:{workbench_id}",definition_revision=str(wb.last_modified),input_snapshot=snapshot,deadline_at=deadline,child_budget=len(items)*(2 if memory_enabled else 1),idempotency_key=request_id or f"schedule:{workbench_id}:{due_minute}")
        else:
            bundle = InferenceParentRouteBundleService(self.broker, self.broker.inference_adoption_service).start(
                principal, command_id=f"workbench-route-{run_id}", parent_kind="workbench",
                definition_ref=f"workbench:{workbench_id}", definition_revision=str(wb.last_modified),
                input_snapshot=snapshot, deadline_at=deadline,
                lifecycle_child_budget=len(items)*(2 if memory_enabled else 1),
                parent_command_id=request_id,
                routes=[{"key": "item", "capability_id": "workbench.item", "invocation_id": f"workbench:{run_id}", "subject_kind": "workbench", "subject_id": workbench_id}],
            )
            parent, member = bundle["parent"], bundle["bundle"]["members"][0]
            route = self.broker.inference_adoption_service.plans.get_route_plan(
                ROUTE_PLANNING_AUTHORITY, str(member["route_plan_id"])
            )
        if parent.replayed:
            return self._replayed_result(parent.operation_id)
        # This is coordination metadata only; its receipt links are always retained.
        with self.db._connection() as conn:
            conn.execute("INSERT INTO workbench_runs(id,workbench_id,started_at,parent_operation_id,parent_receipt_id,child_links_json,status) VALUES(?,?,?,?,'','[]','running')",(run_id,workbench_id,datetime.now().isoformat(),parent.operation_id))
        # HS-132-03: the run is real from here — say so on the one bus.
        from ..workbench_conductor import emit_item_claimed, emit_item_done, emit_item_failed, emit_run_start
        emit_run_start(workbench_id=workbench_id, run_id=run_id, item_count=len(items))
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
                # Claim and epoch validation share one transaction. A cancellation
                # that wins cannot leave this item claimed without a runnable child.
                now = datetime.now().isoformat()
                with self.db._connection() as conn:
                    conn.execute("BEGIN IMMEDIATE")
                    claimed = conn.execute(
                        """UPDATE workbench_items SET status='claimed', claimed_at=?
                           WHERE id=? AND status='pending' AND EXISTS (
                             SELECT 1 FROM kernel_parent_runs
                             WHERE operation_id=? AND state='OPEN' AND execution_epoch=?
                           )""",
                        (now, item.id, parent.operation_id, parent.context.epoch),
                    ).rowcount
                if claimed != 1:
                    return self._adopt_terminal(run_id, parent)
                emit_item_claimed(workbench_id=workbench_id,run_id=run_id,item_id=item.id,title=item.title,index=ordinal,total=len(items))
                parts=[x for x in (context,memory,_hydrate_item_grounding(
                    self.db,
                    item.grounding_json,
                    query=f"{item.title}\n{item.body}",
                ),f"[TASK]\n{item.title}",item.body) if x]
                prompt="\n\n".join(parts)
                item_operation="workbench_item_"+uuid.uuid4().hex
                payload={"workbench_id":workbench_id,"workbench_revision":str(wb.last_modified),"item_id":item.id,"item_revision":str(item.last_modified),"recipe_id":recipe.id,"recipe_revision":str(recipe.last_modified),"system_prompt":system,"user_prompt":prompt,"rendered_input_sha256":_sha(prompt),"skills":skills,"context_hash":_sha(context),"attempt_ordinal":ordinal}

                def publish_item(value: Any, reservation: dict[str, Any], *, item: Any = item) -> str:
                    target = self._route_target(route, int(reservation["route_leg_ordinal"]))
                    projection = {"parent_operation_id":parent.operation_id,"execution_epoch":parent.context.epoch,"planned_node":f"item:{item.id}","run_id":run_id,"workbench_id":workbench_id,"item_id":item.id,"output":str(value.get("output") if isinstance(value,dict) else value),"egress":{"boundary":target["boundary"],"model":target["model"]},"artifact_id":"artifact_"+str(reservation["child_invocation_id"])[-12:],"artifact_title":f"{recipe.name or recipe.id}: {item.title}","deployment_revision":target["deployment_revision_id"]}
                    digest = _sha(value)
                    return self.broker.projection_stager.stage(str(reservation["child_invocation_id"]), "workbench-item-output", projection, result_sha256=digest, receipt_result_ref=f"inference-result:{reservation['child_invocation_id']}/{digest}").result_ref

                routed, _ = await self._run_frozen_child(
                    principal, parent=parent, route_plan_id=str(route["id"]), capability_id="workbench.item",
                    command_id=f"{item_operation}:admit", operation_id=item_operation, payload=payload,
                    reserved_output_tokens=512, publish=publish_item, planned_node=f"item:{item.id}",
                )
                outcome = type("FrozenOutcome", (), {"outcome": routed["outcome"], "error": routed["outcome"]})()
                iid = str(routed.get("winning_reservation", {}).get("child_invocation_id") or "")
                # The deadline is an execution fence: a dispatch that returns
                # past it must not advance. Expiry bumps the epoch, so the
                # child's staged output stays receipt-linked but stale.
                if self.broker.parent_run_controller.expire_if_due(parent.context,principal):
                    self._release_unpublished_claim(item.id)
                    return self._adopt_terminal(run_id,parent)
                if outcome.outcome!="succeeded":
                    # Cancellation can arrive while the provider is in flight.
                    # Do not turn that elected parent outcome into an item failure.
                    if outcome.outcome in {"cancelled", "indeterminate"} or self._winner(parent) is not None:
                        self._release_unpublished_claim(item.id)
                        return self._adopt_terminal(run_id,parent)
                    failed+=1; self.db.workbench_items.upsert(item_id=item.id,workbench_id=workbench_id,title=item.title,body=item.body,priority=item.priority,status="failed",result=f"Error: {outcome.error or outcome.outcome}",completed_at=datetime.now().isoformat())
                    emit_item_failed(workbench_id=workbench_id,run_id=run_id,item_id=item.id,title=item.title,index=ordinal,total=len(items),error=str(outcome.error or outcome.outcome))
                    continue
                check=self.broker.projection_stager.finalize(iid)
                if not check or not check.get("advanced"):
                    # A checkpoint that cannot advance lost the parent election.
                    # Its child receipt remains durable; never mint a success aggregate.
                    self._release_unpublished_claim(item.id)
                    return self._adopt_terminal(run_id,parent)
                complete+=1
                emit_item_done(workbench_id=workbench_id,run_id=run_id,item_id=item.id,title=item.title,index=ordinal,total=len(items))
                if not memory_enabled or self.broker.parent_run_controller.expire_if_due(parent.context,principal): continue
                memory_operation="workbench_memory_"+uuid.uuid4().hex; out=str(check["output"]); mp={"workbench_id":workbench_id,"item_id":item.id,"parent_operation_id":parent.operation_id,"source_item_invocation_id":iid,"source_item_operation_id":check["operation_id"],"source_item_receipt_id":check["receipt_id"],"source_output_sha256":_sha(out),"source_output":out[:500],"prompt_contract_revision":"1"}
                mprompt="Based on the task and your output, what ONE thing should future runs on this workbench remember? Reply with a single sentence. If nothing is worth remembering, reply exactly 'nothing'."
                mpayload={**mp,"system_prompt":"You are a concise assistant. Reply in one sentence only.","user_prompt":f"Task: {item.title}\n\nYour output:\n{out[:500]}\n\n{mprompt}"}

                def publish_memory(value: Any, reservation: dict[str, Any], *, item: Any = item) -> str:
                    target = self._route_target(route, int(reservation["route_leg_ordinal"]))
                    projection = {"parent_operation_id":parent.operation_id,"execution_epoch":parent.context.epoch,"planned_node":f"memory:{item.id}","run_id":run_id,"workbench_id":workbench_id,"item_title":item.title,"observation":str(value.get("output") if isinstance(value,dict) else value),"source_item_receipt_id":check["receipt_id"],"deployment_revision":target["deployment_revision_id"]}
                    digest = _sha(value)
                    return self.broker.projection_stager.stage(str(reservation["child_invocation_id"]), "workbench-memory-writeback", projection, result_sha256=digest, receipt_result_ref=f"inference-result:{reservation['child_invocation_id']}/{digest}").result_ref

                memory_routed, _ = await self._run_frozen_child(
                    principal, parent=parent, route_plan_id=str(route["id"]), capability_id="workbench.item",
                    command_id=f"{memory_operation}:admit", operation_id=memory_operation, payload=mpayload,
                    reserved_output_tokens=128, publish=publish_memory, planned_node=f"memory:{item.id}",
                )
                if memory_routed["outcome"] == "succeeded":
                    self.broker.projection_stager.finalize(str(memory_routed["winning_reservation"]["child_invocation_id"]))
            ctx=constitutional_receipt(); stage=self.broker.projection_stager.stage(parent.native_id,"workbench-run-result",{"parent_operation_id":parent.operation_id,"run_id":run_id,"attempted":len(items),"completed":complete,"failed":failed,"mint_failures":mints,"egress_boundary":"","model":"","context_revision":ctx["revision"],"context_hash":ctx["content_hash"],"skills":skills})
            receipt=self._close_or_adopt(parent,"succeeded",principal=principal,result_ref=stage.result_ref)
            if receipt.get("outcome") != "succeeded":
                return self._adopt_terminal(run_id,parent)
            self.broker.projection_stager.finalize(parent.native_id)
            links=self._record_terminal(run_id,parent,receipt,attempted=len(items),completed=complete,failed=failed)
            return {"run_id":run_id,"parent_operation_id":parent.operation_id,"receipt_id":receipt["receipt_id"],"children":links,"placement":self._route_target(route)}
        except Exception:
            receipt=self._close_or_adopt(parent,"failed",principal=principal)
            self._record_terminal(run_id,parent,receipt)
            raise

    async def run_scheduled(self, scheduler_principal: Principal, workbench_id: str, *, due_minute: int | None = None) -> dict[str, Any]:
        """Revalidate local delegated terms, then use the ordinary admitted loop."""
        from .schedule_delegation import ScheduleDelegationService
        if scheduler_principal.kind.name != "SCHEDULER":
            raise ServiceError("scheduler_principal_required", "Scheduler principal required", context={"status": 403})
        minute = int(time.time() // 60 if due_minute is None else due_minute)
        try:
            delegation = ScheduleDelegationService(self.db).validate(workbench_id)
        except ServiceError as exc:
            wb = self.db.workbenches.get(workbench_id)
            if wb is not None:
                self.broker.parent_run_controller.record_delegated_refusal(
                    scheduler_principal, definition_ref=f"workbench:{workbench_id}",
                    definition_revision=str(wb.last_modified),
                    input_snapshot={"workbench_id": workbench_id, "due_minute": minute},
                    deadline_at=time.time() + 60, child_budget=0,
                    idempotency_key=f"schedule:{workbench_id}:{minute}", reason=exc.code,
                )
            raise
        return await self.run(scheduler_principal, workbench_id, request_id=f"schedule:{workbench_id}:{minute}", delegation=delegation, due_minute=minute)
