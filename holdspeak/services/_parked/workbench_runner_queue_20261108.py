"""PARKED 20261108 (Lane S2, subtraction day): the item-queue path.

Owner ruling 2026-11-08: "sequences and workflows are programs". An
automation's run is a Program of one prompt step
(automation_runs.run_as_program, program_prompt); an old queue is set
up as a program (the face's "Set this up as a program"). What only the queue
used is kept here, as text, in the order it stood:

- workbench_runner: _sha, _failure_words, _route_target,
  _scheduled_route, _run_frozen_child and the queue body of
  WorkbenchRunner.run (instruction occurrences and recipe items, the
  memory write-back);
- WorkbenchService.run_item (its callers: the watch's event start, now
  run_as_program, and Resourceful, now run_as_program too);
- workbench_conductor.run_workbench;
- automation_runs: HTTP_ITEM_SECONDS, plain_agent,
  is_occurrence, automation_result_title, mint_occurrence,
  occurrence_id, _seconds_for, item_seconds,
  assigned_item_seconds.

Not imported. Restore with git revert of the parking commit.
"""
# ruff: noqa
# fmt: off
PARKED = True

'''
def _sha(value: Any) -> str:
    return "sha256:"+hashlib.sha256(json.dumps(value,sort_keys=True,default=str,separators=(",",":")).encode()).hexdigest()



def _failure_words(routed: dict[str, Any]) -> str:
    """Say why a child failed: the adapter's error, else the route's reason."""
    error = str(routed.get("error") or "").strip()
    if error:
        return error
    receipt = routed.get("receipt") or {}
    reasons = [str(c.get("reason_code")) for c in receipt.get("considerations") or [] if c.get("reason_code")]
    disposition = str(receipt.get("disposition") or "").strip()
    words = ", ".join(dict.fromkeys([d for d in [disposition, *reasons] if d]))
    return (words or str(routed.get("outcome") or "failed")).replace("_", " ")



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

# ---- next block ----

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
        adapter: Any = None,
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
            adapter=adapter if adapter is not None else CanonicalPromptAdapter(),
            publish=publish,
            parent_context=parent.context,
            planned_node=planned_node,
        )
        return routed, admitted["route_plan"]

# ---- next block ----

        recipe=self.db.recipes.get(wb.recipe_id) if wb.recipe_id else None
        # Betterment A2: an automation with an instruction needs no agent.
        from . import automation_runs as automation
        instructed=bool(str(wb.instruction or "").strip())
        if recipe is None and not instructed: return {"error":f"The automation {wb.name} has nothing to do yet: write what it should do."}
        recipe=recipe or automation.plain_agent(wb)
        if request_id and delegation is None:
            with self.db._connection() as conn:
                existing=conn.execute("SELECT p.operation_id FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id WHERE o.principal_kind=? AND o.principal_identity=? AND o.idempotency_key=? AND p.kind='workbench' AND p.definition_ref=?",(principal.name,principal.identity,request_id,f"workbench:{workbench_id}")).fetchone()
            if existing is not None and self.broker.store.receipt(str(existing["operation_id"])) is not None:
                return self._replayed_result(str(existing["operation_id"]))
        if instructed and item_ids is None:
            # One run = one result: mint the occurrence item and run only it.
            # A scheduled minute or a request id names it, so a replay finds it.
            key=f"schedule:{due_minute}" if delegation is not None else (f"request:{request_id}" if request_id else None)
            occurrence=automation.mint_occurrence(self.db,wb,item_id=automation.occurrence_id(workbench_id,key) if key else None)
            # A finished occurrence is a replay: the parent's idempotency
            # key returns its receipt below; nothing runs twice.
            item_ids=[occurrence.id] if occurrence.status=="pending" else []
        items=self.db.workbench_items.list_for_workbench(workbench_id,status="pending")
        if item_ids is not None:
            requested=list(dict.fromkeys(str(item_id) for item_id in item_ids if item_id))
            by_id={item.id:item for item in items}
            missing=[item_id for item_id in requested if item_id not in by_id]
            if missing:
                raise ServiceError("item_not_pending","An automation item is missing or no longer pending",context={"status":409,"item_ids":missing})
            items=[by_id[item_id] for item_id in requested]
        if principal.kind is PrincipalKind.OWNER:
            self.broker.inference_adoption_service.migrate_recipe_workbench_subject_assignments(principal)
        # The time limit is per item: a run of four 20 s items must not expire
        # on the fourth one (recon 2026-10-17, step 14: the 60 s whole-run
        # limit cancelled the run, skipped item 4 and recorded 0/0).
        # Betterment A2: the limit is per item and comes from the engine (60 s
        # HTTP, the CLI preset's timeout); a caller's own limit is kept.
        per_item=deadline_seconds if deadline_seconds is not None else automation.assigned_item_seconds(self.db, workbench_id)
        run_id="wbrun_"+uuid.uuid4().hex[:12]; deadline=time.time()+per_item*max(1,len(items))
        snapshot={"workbench_id":workbench_id,"items":[x.id for x in items],"item_scope":"explicit" if item_ids is not None else "pending_batch","recipe_id":recipe.id,"recipe_revision":str(recipe.last_modified),"memory_enabled":memory_enabled,"request_id":request_id or "","source_event":dict(source_event or {})}
        if delegation is not None:
            route = self._scheduled_route(delegation)
            if deadline_seconds is None:  # the frozen route names the engine
                deadline=time.time()+automation.item_seconds(self.db, route)*max(1,len(items))
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
            conn.execute("INSERT INTO workbench_runs(id,workbench_id,started_at,parent_operation_id,parent_receipt_id,child_links_json,status) VALUES(?,?,?,?,'','[]','running')",(run_id,workbench_id,utc_now_iso(),parent.operation_id))
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
        # Orchestrator ruling (A9 follow-up): an automation with its own
        # instruction (a made-one automation included) sends that instruction
        # once, as the task; its agent's old system prompt is not sent again.
        # Its skills still apply.
        base_system=automation.PLAIN_SYSTEM_PROMPT if instructed else (recipe.system_prompt or f"You are {recipe.name}, a helpful assistant.")
        system=inject_skills(self.db,base_system,recipe.id)
        context=_assemble_recipe_context(self.db,recipe); memory=""
        output_target = str(wb.output_target or "")
        if memory_enabled and not output_target.startswith("project_updates:"):
            from ..workbench_memory import recall_for_prompt
            memory=recall_for_prompt(workbench_id)
        skills=[s.id for s in self.db.skills.list_for_recipe(recipe.id,active_only=True)]
        attempted=complete=failed=mints=0
        ran: dict[str, Any] = {"attempted": 0, "completed": 0, "failed": 0, "boundary": "", "model": "", "tokens": 0}

        def tally() -> dict[str, Any]:
            ran.update(attempted=attempted, completed=complete, failed=failed)
            return ran
        project_update_refs: list[str] | None = None
        project_update_material = ""
        project_update_excluded_refs: list[str] | None = None
        if output_target.startswith("project_updates:"):
            project_update_refs, project_update_material, project_update_excluded_refs = (
                automation.project_update_material(self.db, principal, output_target.removeprefix("project_updates:")))
        try:
            for ordinal,item in enumerate(items,1):
                if self.broker.parent_run_controller.expire_if_due(parent.context,principal):
                    return self._adopt_terminal(run_id,parent,tally())
                # Claim and epoch validation share one transaction. A cancellation
                # that wins cannot leave this item claimed without a runnable child.
                now = utc_now_iso()
                with self.db._connection() as conn:
                    conn.execute("BEGIN IMMEDIATE")
                    claimed = conn.execute(
                        """UPDATE workbench_items SET status='claimed', claimed_at=?
                           WHERE id=? AND status='pending' AND parked=0 AND EXISTS (
                             SELECT 1 FROM kernel_parent_runs
                             WHERE operation_id=? AND state='OPEN' AND execution_epoch=?
                           )""",
                        (now, item.id, parent.operation_id, parent.context.epoch),
                    ).rowcount
                    parked_skip = False
                    if claimed != 1:
                        item_state = conn.execute(
                            "SELECT parked FROM workbench_items WHERE id=?",
                            (item.id,),
                        ).fetchone()
                        parent_state = conn.execute(
                            "SELECT state, execution_epoch FROM kernel_parent_runs WHERE operation_id=?",
                            (parent.operation_id,),
                        ).fetchone()
                        parked_skip = bool(
                            item_state is not None
                            and item_state["parked"]
                            and parent_state is not None
                            and parent_state["state"] == "OPEN"
                            and int(parent_state["execution_epoch"]) == parent.context.epoch
                        )
                if claimed != 1:
                    if parked_skip:
                        continue
                    return self._adopt_terminal(run_id, parent, tally())
                attempted += 1
                emit_item_claimed(workbench_id=workbench_id,run_id=run_id,item_id=item.id,title=item.title,index=ordinal,total=len(items))
                try:
                    grounding = _hydrate_item_grounding(
                        self.db, item.grounding_json, query=f"{item.title}\n{item.body}",
                        # The item never recalls itself: its body goes once, as the task.
                        exclude_refs=[f"workbench_item:{item.id}"],
                        project_update_refs=project_update_refs,
                    )
                except ServiceError as exc:
                    # A missing attachment fails this item before any provider
                    # call. Cancellation/expiry still own the parent election.
                    if self.broker.parent_run_controller.expire_if_due(parent.context, principal):
                        self._release_unpublished_claim(item.id)
                        return self._adopt_terminal(run_id, parent, tally())
                    now = utc_now_iso()
                    with self.db._connection() as conn:
                        conn.execute("BEGIN IMMEDIATE")
                        advanced = conn.execute(
                            """UPDATE workbench_items SET status='failed', result=?,
                               result_egress_json=NULL, result_artifact_id=NULL, mint_attempted=0,
                               tokens_consumed=0, completed_at=?, last_modified=?
                               WHERE id=? AND status='claimed' AND parked=0 AND EXISTS (
                                 SELECT 1 FROM kernel_parent_runs
                                 WHERE operation_id=? AND state='OPEN' AND execution_epoch=?
                               )""",
                            (exc.detail, now, now, item.id, parent.operation_id, parent.context.epoch),
                        ).rowcount
                    if advanced != 1:
                        self._release_unpublished_claim(item.id)
                        return self._adopt_terminal(run_id, parent, tally())
                    failed += 1
                    emit_item_failed(workbench_id=workbench_id, run_id=run_id, item_id=item.id,
                                     title=item.title, index=ordinal, total=len(items), error=exc.detail)
                    continue
                parts=[x for x in (context,memory,grounding,project_update_material,f"[TASK]\n{item.title}",item.body) if x]
                prompt="\n\n".join(parts)
                item_operation="workbench_item_"+uuid.uuid4().hex
                payload={"workbench_id":workbench_id,"workbench_revision":str(wb.last_modified),"item_id":item.id,"item_revision":str(item.last_modified),"recipe_id":recipe.id,"recipe_revision":str(recipe.last_modified),"system_prompt":system,"user_prompt":prompt,"rendered_input_sha256":_sha(prompt),"skills":skills,"context_hash":_sha(context),"attempt_ordinal":ordinal,
                         # Project updates are the one automation that lets a
                         # tool-capable engine read the project and save its
                         # plain text through the CONDUCTOR set.
                         "tool_palette": "CONDUCTOR" if str(wb.output_target or "").startswith("project_updates:") else "ASK",
                         "output_target": str(wb.output_target or ""),
                         "project_update_excluded_refs": project_update_excluded_refs}

                output_target = str(wb.output_target or "")
                project_target = output_target.removeprefix("project_updates:")
                adapter = _MeteredPromptAdapter(
                    wb.spend_limit_usd, automation.work_folder_of(wb) if instructed else None,
                    project_id=project_target if output_target.startswith("project_updates:") else "")

                def publish_item(value: Any, reservation: dict[str, Any], *, item: Any = item, adapter: Any = adapter) -> str:
                    target = self._route_target(route, int(reservation["route_leg_ordinal"]))
                    reported = str(value.get("model") or "") if isinstance(value, dict) else ""
                    ran.update(boundary=target["boundary"], model=reported or target["model"])
                    occurrence = automation.is_occurrence(item)
                    projection = {"artifact_status":"new" if occurrence else "pending-review","tokens":adapter.tokens,"parent_operation_id":parent.operation_id,"execution_epoch":parent.context.epoch,"planned_node":f"item:{item.id}","run_id":run_id,"workbench_id":workbench_id,"item_id":item.id,"output":str(value.get("output") if isinstance(value,dict) else value),"egress":{"boundary":target["boundary"],"model":target["model"]},"artifact_id":"artifact_"+str(reservation["child_invocation_id"])[-12:],"artifact_title":automation.automation_result_title(wb) if occurrence else f"{recipe.name or recipe.id}: {item.title}","deployment_revision":target["deployment_revision_id"]}
                    digest = _sha(value)
                    return self.broker.projection_stager.stage(str(reservation["child_invocation_id"]), "workbench-item-output", projection, result_sha256=digest, receipt_result_ref=f"inference-result:{reservation['child_invocation_id']}/{digest}").result_ref

                routed, _ = await self._run_frozen_child(
                    principal, parent=parent, route_plan_id=str(route["id"]), capability_id="workbench.item",
                    command_id=f"{item_operation}:admit", operation_id=item_operation, payload=payload,
                    reserved_output_tokens=512, publish=publish_item, planned_node=f"item:{item.id}",
                    adapter=adapter,
                )
                ran["tokens"] += adapter.tokens
                outcome = type("FrozenOutcome", (), {"outcome": routed["outcome"], "error": _failure_words(routed)})()
                iid = str(routed.get("winning_reservation", {}).get("child_invocation_id") or "")
                # The deadline is an execution fence: a dispatch that returns
                # past it must not advance. Expiry bumps the epoch, so the
                # child's staged output stays receipt-linked but stale.
                if self.broker.parent_run_controller.expire_if_due(parent.context,principal):
                    self._release_unpublished_claim(item.id)
                    return self._adopt_terminal(run_id,parent,tally())
                if outcome.outcome!="succeeded":
                    # Cancellation can arrive while the provider is in flight.
                    # Do not turn that elected parent outcome into an item failure.
                    if outcome.outcome in {"cancelled", "indeterminate"} or self._winner(parent) is not None:
                        self._release_unpublished_claim(item.id)
                        return self._adopt_terminal(run_id,parent,tally())
                    failed+=1; self.db.workbench_items.upsert(item_id=item.id,workbench_id=workbench_id,title=item.title,body=item.body,priority=item.priority,status="failed",result=f"Error: {outcome.error}",completed_at=utc_now_iso(),grounding=json.loads(item.grounding_json or "{}"),context=json.loads(item.context_json or "{}"))  # a failure keeps its sources and its occurrence mark (A2)
                    emit_item_failed(workbench_id=workbench_id,run_id=run_id,item_id=item.id,title=item.title,index=ordinal,total=len(items),error=str(outcome.error))
                    continue
                check=self.broker.projection_stager.finalize(iid)
                if not check or not check.get("advanced"):
                    # A checkpoint that cannot advance lost the parent election.
                    # Its child receipt remains durable; never mint a success aggregate.
                    self._release_unpublished_claim(item.id)
                    return self._adopt_terminal(run_id,parent,tally())
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

                memory_adapter = _MeteredPromptAdapter(wb.spend_limit_usd, desk_tools=False)
                memory_routed, _ = await self._run_frozen_child(
                    principal, parent=parent, route_plan_id=str(route["id"]), capability_id="workbench.item",
                    command_id=f"{memory_operation}:admit", operation_id=memory_operation, payload=mpayload,
                    reserved_output_tokens=128, publish=publish_memory, planned_node=f"memory:{item.id}",
                    adapter=memory_adapter,
                )
                ran["tokens"] += memory_adapter.tokens
                if memory_routed["outcome"] == "succeeded":
                    self.broker.projection_stager.finalize(str(memory_routed["winning_reservation"]["child_invocation_id"]))
            ctx=constitutional_receipt(); stage=self.broker.projection_stager.stage(parent.native_id,"workbench-run-result",{"parent_operation_id":parent.operation_id,"run_id":run_id,"attempted":attempted,"completed":complete,"failed":failed,"mint_failures":mints,"egress_boundary":ran["boundary"],"model":ran["model"],"total_tokens":ran["tokens"],"context_revision":ctx["revision"],"context_hash":ctx["content_hash"],"skills":skills})
            receipt=self._close_or_adopt(parent,"succeeded",principal=principal,result_ref=stage.result_ref)
            if receipt.get("outcome") != "succeeded":
                return self._adopt_terminal(run_id,parent,tally())
            self.broker.projection_stager.finalize(parent.native_id)
            links=self._record_terminal(run_id,parent,receipt,ran=tally())
            return {"run_id":run_id,"parent_operation_id":parent.operation_id,"receipt_id":receipt["receipt_id"],"children":links,"placement":self._route_target(route)}
        except Exception:
            receipt=self._close_or_adopt(parent,"failed",principal=principal)
            self._record_terminal(run_id,parent,receipt,ran=tally())
            raise

# ---- next block ----

    async def run_item(
        self,
        principal: Principal,
        workbench_id: str,
        item_id: str,
        *,
        memory_enabled: bool = True,
        request_id: str | None = None,
        source_event: dict[str, str] | None = None,
        deadline_seconds: float = 600,
    ) -> dict[str, Any]:
        """Admit exactly one causal Workbench item, never the pending batch."""
        self._require_item(workbench_id, item_id)
        from holdspeak.kernel.runtime import _service
        from holdspeak.services.workbench_runner import WorkbenchRunner

        result = await WorkbenchRunner(self._db, _service()).run(
            principal,
            workbench_id,
            memory_enabled=memory_enabled,
            request_id=request_id,
            source_event=source_event,
            deadline_seconds=deadline_seconds,
            item_ids=[item_id],
        )
        return self._deliver(principal, result)

# ---- next block ----

async def run_workbench(workbench_id: str, principal: Any | None = None, *, memory_enabled: bool = True) -> dict:
    """Compatibility seam for authenticated manual Workbench execution."""
    if principal is None:
        from .services.errors import ServiceError
        raise ServiceError("scheduler_principal_required", "An explicit principal is required", context={"status": 403})
    from .kernel.runtime import _service
    from .services.workbench_runner import WorkbenchRunner
    from .db import get_database
    return await WorkbenchRunner(get_database(), _service()).run(
        principal, workbench_id, memory_enabled=memory_enabled
    )

# ---- next block ----

#: The per-item time limit for an HTTP engine (seconds).
HTTP_ITEM_SECONDS = 60.0


def plain_agent(wb: Any) -> Any:
    """The agent of an automation that has an instruction and no recipe."""
    from types import SimpleNamespace

    return SimpleNamespace(
        id="", name=str(wb.name or "Automation"), system_prompt=PLAIN_SYSTEM_PROMPT,
        last_modified="", manual_context="", kb_id=None,
    )


def is_occurrence(item: Any) -> bool:
    try:
        context = json.loads(getattr(item, "context_json", "") or "{}")
    except (TypeError, ValueError):
        return False
    return isinstance(context, dict) and bool(context.get(OCCURRENCE))


def automation_result_title(wb: Any, now: Optional[datetime] = None) -> str:
    """Name one automation result by the automation and the run date."""
    when = (now or local_now()).astimezone()
    return f"{wb.name or 'Automation'} · {when.day} {when:%b}"


def mint_occurrence(
    db: Any,
    wb: Any,
    *,
    item_id: Optional[str] = None,
    title: Optional[str] = None,
    event: Optional[dict[str, Any]] = None,
    context: Optional[dict[str, Any]] = None,
) -> Any:
    """Add the one item a run of an instruction automation runs.

    A known ``item_id`` (a scheduled minute, a request id, an event) is
    made once: a replayed start finds the item it made and adds none.
    """
    clean_id = str(item_id or ("wbocc_" + uuid.uuid4().hex[:16]))
    existing = db.workbench_items.get(clean_id, include_parked=True)
    if existing is not None:
        return existing
    body = str(wb.instruction or "").strip()
    refs, about = expand_sources(db, sources_of(wb))
    if about:
        body = f"{body}\n\n[ABOUT]\n" + "\n".join(about)
    if event is not None:
        body = f"{body}\n\n{_event_block(event)}"
    return db.workbench_items.upsert(
        item_id=clean_id,
        workbench_id=wb.id,
        title=str(title or occurrence_title(wb)),
        body=body,
        grounding={"refs": refs} if refs else {},
        context={**(context or {}), OCCURRENCE: True},
    )


def occurrence_id(workbench_id: str, key: str) -> str:
    return "wbocc_" + hashlib.sha256(f"{workbench_id}:{key}".encode()).hexdigest()[:20]


def _seconds_for(endpoints: list[Any]) -> float:
    from ..intel.cli_engine import parse_cli_endpoint

    seconds = HTTP_ITEM_SECONDS
    for endpoint in endpoints:
        parsed = parse_cli_endpoint(endpoint)
        if parsed is not None:
            seconds = max(seconds, float(parsed[0].timeout_seconds))
    return seconds


def item_seconds(db: Any, route: dict[str, Any]) -> float:
    """The time limit for one item on a frozen route (a scheduled run): 60 s
    for an HTTP engine, the preset's timeout for a CLI engine; the longest
    leg of the chain."""
    ids = [str(entry.get("deployment_revision_id") or "") for entry in route.get("entries") or []]
    endpoints: list[Any] = []
    with db._connection() as conn:
        for revision_id in ids:
            row = conn.execute(
                "SELECT kind, endpoint FROM deployment_revisions WHERE id=?", (revision_id,)
            ).fetchone()
            if row is not None and str(row["kind"]) == "cli_engine":
                endpoints.append(row["endpoint"])
    return _seconds_for(endpoints)


def assigned_item_seconds(db: Any, workbench_id: str) -> float:
    """The same limit for a press or an event: read from the engine assigned
    to this automation's ``workbench.item`` job before the run is admitted
    (the admitted deadline is bound into the route bundle and cannot move)."""
    from .inference_assignment_service import InferenceAssignmentService

    service = InferenceAssignmentService(db)
    try:
        capability = service._require_assignable("workbench.item")
        with db._connection() as conn:
            resolved = service._resolve(
                conn, capability, subject_kind="workbench", subject_id=workbench_id,
            )
            entries = list((resolved.get("assignment") or {}).get("entries") or [])
            endpoints: list[Any] = []
            for entry in entries:
                endpoint = cli_endpoint_of(conn, str(entry.get("profile_id") or ""))
                if endpoint:
                    endpoints.append(endpoint)
    except Exception as exc:  # no readable assignment: the run's own admission says why
        log.debug("automation %s: engine limit read failed: %s", workbench_id, exc)
        return HTTP_ITEM_SECONDS
    return _seconds_for(endpoints)
'''
