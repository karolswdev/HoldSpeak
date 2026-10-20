"""Admitted manual Workbench execution."""
from __future__ import annotations
import asyncio, hashlib, json, time, uuid
from holdspeak.timestamps import utc_now_iso
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


class _MeteredPromptAdapter(CanonicalPromptAdapter):
    """The canonical adapter, plus the tokens the provider said it used.

    The sealed result shape stays {output, provider, model}. The count travels
    on this adapter instance, which the runner keeps for its one child."""

    def __init__(self, spend_limit_usd: float | None = None, work_folder: str | None = None, *,
                 desk_tools: bool = True, project_id: str = "") -> None:
        self.tokens = 0
        #: Betterment A4: the automation's Spend limit per run; it overrides
        #: the engine's own limit on an agent CLI that enforces one.
        self.spend_limit_usd = spend_limit_usd
        #: Betterment M2 follow-up (orchestrator ruling): the memory call
        #: after an item runs WITHOUT the desk's tools on an agent CLI.
        self.desk_tools = desk_tools
        #: Project scope for an update automation's run credential.
        self.project_id = str(project_id or "").strip()
        #: Betterment A10: the folder an agent CLI works in, read only (the
        #: automation's Folder source). An HTTP engine has no folder: ignored.
        self.work_folder = work_folder

    def _limited(self, engine: Any) -> Any:
        preset = getattr(engine, "preset", None)
        limit = (self.spend_limit_usd is not None and hasattr(engine, "spend_limit_usd")
                 and getattr(preset, "enforces_spend_limit", False))
        no_tools = not self.desk_tools and getattr(engine, "desk_tools", False)
        folder = bool(self.work_folder) and hasattr(engine, "work_folder")
        project_scope = bool(self.project_id) and hasattr(engine, "project_id")
        if not limit and not no_tools and not folder and not project_scope:
            return engine
        # A copy for this one call: the routed engine may be shared.
        import copy

        limited = copy.copy(engine)
        if limit:
            limited.spend_limit_usd = self.spend_limit_usd
        if no_tools:
            limited.desk_tools = False
        if folder:
            limited.work_folder = self.work_folder
        if project_scope:
            limited.project_id = self.project_id
        return limited

    def dispatch(self, engine: Any, payload: dict[str, Any], cancellation: Any) -> dict[str, str]:
        engine = self._limited(engine)
        from .run_trace import for_item

        # Betterment M2: an agent CLI run records the item it ran for, so the
        # result shows the run's cost and what its agent used.
        with for_item(str(payload.get("item_id") or "")):
            if self.desk_tools:
                # MCP M5: an HTTP engine whose server takes tool calls runs
                # the item through the hub's tool loop, with the desk's tools.
                from .engine_tool_loop import answer_item

                looped = answer_item(engine, payload, cancellation)
                if looped is not None:
                    result, tokens = looped
                    self.tokens += tokens
                    return result
            result = super().dispatch(engine, payload, cancellation)
        try:
            usage = dict(getattr(engine, "last_usage", None) or {})
            self.tokens += int(usage.get("total_tokens") or 0)
        except (TypeError, ValueError):
            pass  # an engine without a provider count reports none, never a guess
        return result


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

    def _record_terminal(self, run_id: str, parent: Any, receipt: dict[str, Any], *, attempted: int = 0, completed: int = 0, failed: int = 0, ran: dict[str, Any] | None = None) -> list[dict[str, str]]:
        """Make the coordination row point at the one durable terminal receipt.

        ``ran`` carries what this run really did (counts, egress, model,
        tokens). A cancelled or expired run keeps the work it finished, so its
        row says so instead of ``0/0``."""
        links = _children(self.db, self.broker, parent.operation_id)
        outcome = str(receipt.get("outcome") or "indeterminate")
        status = "completed" if outcome == "succeeded" else outcome
        with self.db._connection() as conn:
            conn.execute("UPDATE workbench_runs SET parent_receipt_id=?,child_links_json=?,status=? WHERE id=?", (str(receipt["receipt_id"]), json.dumps(links), status, run_id))
            if ran is not None:
                conn.execute(
                    "UPDATE workbench_runs SET items_attempted=?,items_completed=?,items_failed=?,egress_boundary=?,model=?,total_tokens=? WHERE id=?",
                    (int(ran["attempted"]), int(ran["completed"]), int(ran["failed"]), str(ran["boundary"]), str(ran["model"]), int(ran["tokens"]), run_id),
                )
                attempted, completed, failed = int(ran["attempted"]), int(ran["completed"]), int(ran["failed"])
        # HS-132-03: every terminal — succeeded, cancelled, expired, failed —
        # funnels through here, so this is the one honest place the desk hears
        # a run end. A terminal adopted from the loop carries the counts it
        # reached; one with no ``ran`` (no items) carries only its disposition.
        self._emit_run_complete(run_id, outcome, attempted=attempted, completed=completed, failed=failed)
        return links

    def _emit_run_complete(self, run_id: str, disposition: str, *, attempted: int, completed: int, failed: int) -> None:
        """Tell every open surface this run reached its terminal."""
        try:
            from ..workbench_conductor import emit_run_complete
            with self.db._connection() as conn:
                row = conn.execute("SELECT workbench_id FROM workbench_runs WHERE id=?", (run_id,)).fetchone()
                workbench_id = str(row["workbench_id"]) if row is not None else ""
                pending = conn.execute("SELECT COUNT(*) AS n FROM workbench_items WHERE workbench_id=? AND status='pending' AND parked=0", (workbench_id,)).fetchone()
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

    def _adopt_terminal(self, run_id: str, parent: Any, ran: dict[str, Any] | None = None) -> dict[str, Any]:
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
        links = self._record_terminal(run_id, parent, receipt, ran=ran)
        return {"run_id": run_id, "parent_operation_id": parent.operation_id, "receipt_id": receipt["receipt_id"], "terminal_disposition": receipt.get("outcome"), "children": links}

    def _run_hand(
        self, principal: Principal, wb: Any, *, item_ids: list[str] | None = None,
        parent: Any = None, scheduler_authorized: bool = False,
    ) -> dict[str, Any]:
        """AG14: hand each eligible source item once through AgentHandService."""
        from . import automation_runs as automation
        from .agent_hand_service import default_agent_hand_service

        if principal.kind is PrincipalKind.SCHEDULER and not scheduler_authorized:
            raise ServiceError(
                "schedule_delegation_required",
                "A scheduled hand needs its live owner delegation",
                context={"status": 409},
            )
        run_id = "wbrun_" + uuid.uuid4().hex[:12]
        candidates = automation.materialize_hand_items(self.db, wb)
        if item_ids is not None:
            wanted = {str(value) for value in item_ids if str(value)}
            candidates = [item for item in candidates if item.id in wanted]
        with self.db._connection() as conn:
            if parent is None:
                conn.execute(
                    "INSERT INTO workbench_runs(id,workbench_id,started_at,status) VALUES(?,?,?, 'running')",
                    (run_id, wb.id, utc_now_iso()),
                )
            else:
                conn.execute(
                    "INSERT INTO workbench_runs(id,workbench_id,started_at,parent_operation_id,parent_receipt_id,child_links_json,status) VALUES(?,?,?,?,'','[]','running')",
                    (run_id, wb.id, utc_now_iso(), parent.operation_id),
                )

        # A scheduler may use the owner identity only after the existing
        # durable schedule parent admitted this exact hand.  A direct
        # scheduler call never receives owner elevation.
        hand_principal = principal
        if scheduler_authorized:
            hand_principal = Principal(PrincipalKind.OWNER, "local-automation-conductor")
        hand_service = default_agent_hand_service(self.db)
        started: list[dict[str, Any]] = []
        queued: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        failed = 0
        profile = str(getattr(wb, "agent_profile", "") or "").strip() or None
        review_by = str(getattr(wb, "review_by", "") or "").strip() or None
        instruction = str(getattr(wb, "instruction", "") or "").strip() or None
        for item in candidates:
            context = automation._hand_context(item)
            hand = context.get("agent_hand") if isinstance(context.get("agent_hand"), dict) else {}
            prior = str(hand.get("status") or "")
            if prior in {"starting", "queued", "launched", "done", "failed"} or hand.get("launch_id") or hand.get("queue_id"):
                skipped.append({"item_id": item.id, "title": item.title, "status": prior or "handed"})
                continue
            # The source item is the existing durable idempotency seam. Claim
            # it under SQLite's write lock before the process launch so two
            # concurrent Run presses cannot hand the same source twice.
            context["occurrence"] = True
            context["agent_hand"] = {**hand, "status": "starting", "run_id": run_id}
            with self.db._connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                current = conn.execute("SELECT context_json, status FROM workbench_items WHERE id=?", (item.id,)).fetchone()
                try:
                    current_context = json.loads(current["context_json"] or "{}") if current else {}
                except (TypeError, ValueError):
                    current_context = {}
                current_hand = current_context.get("agent_hand") if isinstance(current_context, dict) and isinstance(current_context.get("agent_hand"), dict) else {}
                current_status = str(current_hand.get("status") or "")
                if current is None or current_status in {"starting", "queued", "launched", "done", "failed"} or current_hand.get("launch_id") or current_hand.get("queue_id"):
                    skipped.append({"item_id": item.id, "title": item.title, "status": current_status or "handed"})
                    continue
                claimed = conn.execute(
                    "UPDATE workbench_items SET status='claimed', context_json=?, last_modified=? WHERE id=? AND status='pending'",
                    (json.dumps(context, sort_keys=True), utc_now_iso(), item.id),
                ).rowcount
                if claimed != 1:
                    skipped.append({"item_id": item.id, "title": item.title, "status": "claimed"})
                    continue
            source_ref = str(hand.get("source_ref") or "")
            kind, _, source_id = source_ref.partition(":")
            if not kind or not source_id:
                failed += 1
                skipped.append({"item_id": item.id, "title": item.title, "status": "invalid_source"})
                continue
            try:
                answer = hand_service.hand_item(
                    hand_principal,
                    kind=kind,
                    id=source_id,
                    instruction=instruction,
                    profile=profile,
                    queue=True,
                    review_by=review_by,
                )
                state = str(answer.get("status") or "launched")
                hand = {
                    **hand,
                    "status": state,
                    "run_id": run_id,
                    "profile": str(answer.get("profile") or profile or ""),
                    "review_by": review_by or "none",
                    **({"launch_id": str(answer["launch_id"])} if answer.get("launch_id") else {}),
                    **({"queue_id": str(answer["queue_id"])} if answer.get("queue_id") else {}),
                }
                context["occurrence"] = True
                context["agent_hand"] = hand
                with self.db._connection() as conn:
                    conn.execute(
                        "UPDATE workbench_items SET status='pending', context_json=?, last_modified=? WHERE id=? AND status='claimed'",
                        (json.dumps(context, sort_keys=True), utc_now_iso(), item.id),
                    )
                entry = {"item_id": item.id, "title": item.title, "source_ref": source_ref, **answer}
                if state == "queued":
                    queued.append(entry)
                else:
                    started.append(entry)
            except Exception as exc:
                failed += 1
                context["occurrence"] = True
                context["agent_hand"] = {
                    **hand, "status": "failed", "run_id": run_id,
                    "error": str(getattr(exc, "detail", None) or exc),
                }
                with self.db._connection() as conn:
                    conn.execute(
                        "UPDATE workbench_items SET status='failed', result=?, context_json=?, completed_at=?, last_modified=? WHERE id=? AND status='claimed'",
                        (f"Error: {context['agent_hand']['error']}", json.dumps(context, sort_keys=True), utc_now_iso(), utc_now_iso(), item.id),
                    )

        with self.db._connection() as conn:
            conn.execute(
                """UPDATE workbench_runs SET completed_at=?, items_attempted=?, items_completed=0,
                   items_failed=?, status='completed' WHERE id=?""",
                (utc_now_iso(), len(candidates), failed, run_id),
            )
        answer = {
            "run_id": run_id,
            "status": "completed",
            "agents_started": started,
            "agents_queued": queued,
            "skipped": skipped,
            "items_attempted": len(candidates),
            "items_completed": 0,
            "items_failed": failed,
        }
        if parent is not None:
            receipt = self._close_or_adopt(
                parent, "failed" if failed and not started and not queued else "succeeded",
                principal=principal,
            )
            if receipt.get("outcome") != "succeeded":
                return self._adopt_terminal(run_id, parent)
            self._record_terminal(
                run_id, parent, receipt, attempted=len(candidates),
                completed=0, failed=failed,
            )
            answer.update({
                "parent_operation_id": parent.operation_id,
                "receipt_id": receipt["receipt_id"],
                "parent_receipt_id": receipt["receipt_id"],
                "terminal_disposition": receipt.get("outcome"),
            })
        return answer

    def _run_event_hand(
        self, principal: Principal, wb: Any, request_id: str,
        *, source_event: dict[str, str], item_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Use the existing owner parent admission for an event hand."""
        snapshot = {
            "workbench_id": wb.id,
            "do_kind": "hand_to_agent",
            "agent_profile": str(getattr(wb, "agent_profile", "") or ""),
            "review_by": str(getattr(wb, "review_by", "") or ""),
            "source_event": dict(source_event),
            "items": list(item_ids or []),
        }
        parent = self.broker.parent_run_controller.start(
            principal,
            kind="workbench",
            definition_ref=f"workbench:{wb.id}",
            definition_revision=str(wb.last_modified),
            input_snapshot=snapshot,
            deadline_at=time.time() + 600,
            child_budget=max(1, len(item_ids or [])),
            idempotency_key=request_id,
        )
        if parent.replayed:
            return self._replayed_result(parent.operation_id)
        return self._run_hand(principal, wb, item_ids=item_ids, parent=parent)

    def _run_scheduled_hand(
        self, principal: Principal, wb: Any, delegation: dict[str, Any],
        *, request_id: str, due_minute: int, item_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Admit a scheduled native hand through the durable parent path."""
        from . import automation_runs as automation

        candidates = automation.materialize_hand_items(self.db, wb)
        if item_ids is not None:
            wanted = {str(value) for value in item_ids if str(value)}
            candidates = [item for item in candidates if item.id in wanted]
        deadline = time.time() + 600 * max(1, len(candidates))
        snapshot = {
            "workbench_id": wb.id,
            "items": [item.id for item in candidates],
            "item_scope": "explicit" if item_ids is not None else "pending_batch",
            "do_kind": "hand_to_agent",
            "agent_profile": str(getattr(wb, "agent_profile", "") or ""),
            "review_by": str(getattr(wb, "review_by", "") or ""),
            "request_id": request_id,
            "due_minute": due_minute,
            "delegation_id": delegation["id"],
            "terms_sha256": delegation["terms_sha256"],
            "delegator_kind": delegation["delegator_kind"],
            "delegator_identity": delegation["delegator_identity"],
            "deployment_revision_id": delegation["deployment_revision_id"],
        }
        parent = self.broker.parent_run_controller.start_delegated_schedule(
            principal,
            definition_ref=f"workbench:{wb.id}",
            definition_revision=str(wb.last_modified),
            input_snapshot=snapshot,
            deadline_at=deadline,
            child_budget=max(1, len(candidates)),
            idempotency_key=request_id,
        )
        if parent.replayed:
            return self._replayed_result(parent.operation_id)
        return self._run_hand(
            principal, wb, item_ids=item_ids, parent=parent,
            scheduler_authorized=True,
        )

    async def run(self, principal: Principal, workbench_id: str, *, memory_enabled: bool=True, request_id: str|None=None, deadline_seconds: float|None=None, delegation: dict[str, Any] | None = None, due_minute: int | None = None, source_event: dict[str, str] | None = None, item_ids: list[str] | None = None) -> dict[str,Any]:
        if principal is None or principal.kind is PrincipalKind.NONE:
            from ..kernel.model import KernelRefused
            raise KernelRefused("principal_authentication_required")
        wb=self.db.workbenches.get(workbench_id)
        if wb is None: raise ServiceError("not_found","Unknown automation",context={"status":404})
        if str(getattr(wb, "do_kind", "run") or "run") == "hand_to_agent":
            if delegation is not None:
                return await asyncio.to_thread(
                    self._run_scheduled_hand, principal, wb, delegation,
                    request_id=request_id or f"schedule:{workbench_id}:{due_minute}",
                    due_minute=int(due_minute if due_minute is not None else time.time() // 60),
                    item_ids=item_ids,
                )
            if principal.kind is PrincipalKind.SCHEDULER:
                raise ServiceError(
                    "schedule_delegation_required",
                    "A scheduled hand needs its live owner delegation",
                    context={"status": 409},
                )
            # Events have already been admitted by their durable reaction
            # projection. Keep the same parent authority for this run so its
            # receipt is the operation recorded by the reaction.
            if source_event and request_id:
                return await asyncio.to_thread(
                    self._run_event_hand, principal, wb, request_id,
                    source_event=source_event, item_ids=item_ids,
                )
            return await asyncio.to_thread(self._run_hand, principal, wb, item_ids=item_ids)
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
            project_target = output_target.removeprefix("project_updates:")
            try:
                from .project_service import ProjectService
                from .memory_grounding import MemoryContext, page_excerpts, project_pages
                from .project_update_service import ProjectUpdateService

                update_service = ProjectUpdateService(
                    self.db, project_service=ProjectService(self.db),
                )
                project_update_refs = update_service.project_update_grounding_refs(
                    principal, project_target,
                )
                # P8's no-tool contract: the engine receives the existing
                # records draft and the three project standing pages as
                # material. Pages are read sentence-by-sentence with the same
                # P2 exclusions, so a stale private source cannot re-enter at
                # this second context seam.
                records = update_service.draft_update(
                    principal, project_target, generator="deterministic", persist=False,
                )
                excluded = update_service.project_update_excluded_refs(
                    principal, project_target,
                )
                project_update_excluded_refs = sorted(excluded)
                excluded_folded = {str(ref).casefold() for ref in excluded}

                def page_sentence_is_safe(sentence: Any) -> bool:
                    refs = sentence.get("refs") if isinstance(sentence, dict) else []
                    return not any(
                        str(ref.get("ref") or "").split("#", 1)[0].casefold()
                        in excluded_folded
                        for ref in refs or [] if isinstance(ref, dict)
                    )

                pages = page_excerpts(
                    self.db,
                    project_pages(
                        project_target,
                        "what-we-decided",
                        "what-is-open",
                        "what-changed-this-week",
                    ),
                    exclude_refs=excluded,
                    sentence_filter=page_sentence_is_safe,
                )
                records_body = str(records.get("body_md") or "").strip()
                page_body = MemoryContext(tuple(pages)).prompt_block("PROJECT PAGES")
                project_update_material = "\n\n".join(
                    part for part in (
                        f"[RECORDS DRAFT]\n{records_body}\n[END RECORDS DRAFT]"
                        if records_body else "",
                        page_body,
                    ) if part
                )
            except Exception:
                # An update run must never fall back to broad project
                # hydration when its P2 source list cannot be established.
                project_update_refs = []
                project_update_material = ""
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
