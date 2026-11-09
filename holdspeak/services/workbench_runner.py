"""Admitted manual Workbench execution."""
from __future__ import annotations

from holdspeak.db.models import _json_list
import asyncio, json, time, uuid  # noqa: E401
from holdspeak.timestamps import utc_now_iso
from typing import Any
from ..principals import Principal, PrincipalKind
from .errors import ServiceError


def _children(db: Any, broker: Any, parent_id: str) -> list[dict[str,str]]:
    with db._connection() as conn:
        rows=conn.execute("SELECT operation_id,native_id FROM kernel_operations WHERE parent_operation_id=? ORDER BY created_at",(parent_id,)).fetchall()
    return [{"operation_id":str(r["operation_id"]),"invocation_id":str(r["native_id"]),"receipt_id":str((broker.store.receipt(str(r["operation_id"])) or {}).get("receipt_id") or "")} for r in rows]


class WorkbenchRunner:
    def __init__(self, db: Any, broker: Any) -> None:
        self.db,self.broker=db,broker
        from ..kernel.workbench_projection import register
        register(broker.projection_stager)

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

    def _run_program(
        self, principal: Principal, wb: Any, *, parent: Any = None,
        scheduler_authorized: bool = False,
    ) -> dict[str, Any]:
        """PG14: make and start one Program from the template; one result
        links it. While the last Program still runs, start nothing."""
        from .automation_program import result_words, run_program

        if principal.kind is PrincipalKind.SCHEDULER and not scheduler_authorized:
            raise ServiceError(
                "schedule_delegation_required",
                "A scheduled program needs its live owner delegation",
                context={"status": 409},
            )
        run_id = "wbrun_" + uuid.uuid4().hex[:12]
        with self.db._connection() as conn:
            conn.execute(
                "INSERT INTO workbench_runs(id,workbench_id,started_at,parent_operation_id,parent_receipt_id,child_links_json,status) VALUES(?,?,?,?,'','[]','running')",
                (run_id, wb.id, utc_now_iso(), parent.operation_id if parent is not None else ""),
            )
        program_principal = principal
        if scheduler_authorized:
            program_principal = Principal(PrincipalKind.OWNER, "local-automation-conductor")
        started_at = utc_now_iso()
        failed = 0
        try:
            ran = run_program(self.db, program_principal, wb)
        except ServiceError as exc:
            failed = 1
            ran = {"started": False, "error": str(getattr(exc, "detail", None) or exc)}
        recorded = bool(ran.get("started")) or failed
        if recorded:
            # The run's one result: the occurrence item names the Program.
            now = utc_now_iso()
            program = ({"program_id": ran["program_id"], "title": ran["title"], "steps": ran.get("steps", 0)}
                       if ran.get("started") else {})
            context = {"occurrence": True, "run_id": run_id, "program": program}
            text = result_words(ran) if ran.get("started") else f"Error: {ran['error']}"
            with self.db._connection() as conn:
                conn.execute(
                    """INSERT INTO workbench_items
                       (id, workbench_id, title, body, priority, status, result, grounding_json, context_json,
                        created_at, claimed_at, completed_at, last_modified)
                       VALUES (?, ?, ?, ?, 3, ?, ?, '{}', ?, ?, ?, ?, ?)""",
                    ("wbprog_" + run_id.removeprefix("wbrun_"), wb.id,
                     str(ran.get("title") or getattr(wb, "name", "") or "Program"),
                     str(getattr(wb, "instruction", "") or ""), "failed" if failed else "done", text,
                     json.dumps(context, sort_keys=True), started_at, started_at, now, now),
                )
        with self.db._connection() as conn:
            conn.execute(
                """UPDATE workbench_runs SET completed_at=?, items_attempted=?, items_completed=?,
                   items_failed=?, status=? WHERE id=?""",
                (utc_now_iso(), 1 if recorded else 0, 1 if ran.get("started") else 0, failed,
                 "failed" if failed else "completed", run_id),
            )
        answer = {
            "run_id": run_id, "status": "failed" if failed else "completed",
            "program_started": bool(ran.get("started")),
            "program_id": ran.get("program_id"), "program_window": ran.get("window"),
            "items_attempted": 1 if recorded else 0, "items_completed": 1 if ran.get("started") else 0,
            "items_failed": failed,
        }
        if ran.get("reason"):
            answer.update({"skipped": True, "reason": ran["reason"]})
        if failed:
            answer["error"] = ran["error"]
        if parent is not None:
            receipt = self._close_or_adopt(parent, "failed" if failed else "succeeded", principal=principal)
            if receipt.get("outcome") != ("failed" if failed else "succeeded"):
                return self._adopt_terminal(run_id, parent)
            self._record_terminal(run_id, parent, receipt, attempted=answer["items_attempted"],
                                  completed=answer["items_completed"], failed=failed)
            answer.update({
                "parent_operation_id": parent.operation_id,
                "receipt_id": receipt["receipt_id"],
                "parent_receipt_id": receipt["receipt_id"],
                "terminal_disposition": receipt.get("outcome"),
            })
        return answer

    @staticmethod
    def _native_terms(wb: Any) -> dict[str, Any]:
        """The Do kind's own terms in a parent snapshot (hand or program)."""
        kind = str(getattr(wb, "do_kind", "run") or "run")
        if kind == "run_program":
            return {
                "do_kind": "run_program",
                "program_template": str(getattr(wb, "program_template", "") or ""),
                "program_control": str(getattr(wb, "program_control", "") or ""),
                "program_runs_on": _json_list(wb.program_runs_on_json),
            }
        return {
            "do_kind": "hand_to_agent",
            "agent_profile": str(getattr(wb, "agent_profile", "") or ""),
            "review_by": str(getattr(wb, "review_by", "") or ""),
        }

    def _run_native(self, principal: Principal, wb: Any, *, item_ids: list[str] | None = None,
                    parent: Any = None, scheduler_authorized: bool = False) -> dict[str, Any]:
        if str(getattr(wb, "do_kind", "run") or "run") == "run_program":
            return self._run_program(principal, wb, parent=parent, scheduler_authorized=scheduler_authorized)
        return self._run_hand(principal, wb, item_ids=item_ids, parent=parent,
                              scheduler_authorized=scheduler_authorized)

    def _run_event_hand(
        self, principal: Principal, wb: Any, request_id: str,
        *, source_event: dict[str, str], item_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Use the existing owner parent admission for an event hand."""
        snapshot = {
            "workbench_id": wb.id,
            **self._native_terms(wb),
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
        return self._run_native(principal, wb, item_ids=item_ids, parent=parent)

    def _run_scheduled_hand(
        self, principal: Principal, wb: Any, delegation: dict[str, Any],
        *, request_id: str, due_minute: int, item_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Admit a scheduled native hand through the durable parent path."""
        from . import automation_runs as automation

        program = str(getattr(wb, "do_kind", "run") or "run") == "run_program"
        candidates = [] if program else automation.materialize_hand_items(self.db, wb)
        if item_ids is not None:
            wanted = {str(value) for value in item_ids if str(value)}
            candidates = [item for item in candidates if item.id in wanted]
        deadline = time.time() + 600 * max(1, len(candidates))
        snapshot = {
            "workbench_id": wb.id,
            "items": [item.id for item in candidates],
            "item_scope": "explicit" if item_ids is not None else "pending_batch",
            **self._native_terms(wb),
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
        return self._run_native(
            principal, wb, item_ids=item_ids, parent=parent,
            scheduler_authorized=True,
        )

    async def run(self, principal: Principal, workbench_id: str, *, memory_enabled: bool=True, request_id: str|None=None, deadline_seconds: float|None=None, delegation: dict[str, Any] | None = None, due_minute: int | None = None, source_event: dict[str, str] | None = None, item_ids: list[str] | None = None) -> dict[str,Any]:
        if principal is None or principal.kind is PrincipalKind.NONE:
            from ..kernel.model import KernelRefused
            raise KernelRefused("principal_authentication_required")
        wb=self.db.workbenches.get(workbench_id)
        if wb is None: raise ServiceError("not_found","Unknown automation",context={"status":404})
        if str(getattr(wb, "do_kind", "run") or "run") in ("hand_to_agent", "run_program"):
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
            return await asyncio.to_thread(self._run_native, principal, wb, item_ids=item_ids)
        # 2026-11-08: the item queue is parked (holdspeak/services/_parked/
        # workbench_runner_queue_20261108.py). An automation with an
        # instruction runs as a Program of one prompt step
        # (automation_runs.run_as_program); an old queue is set up as a program.
        raise ServiceError(
            "set_up_as_program", "Programs run this queue now: set it up as a program.",
            context={"status": 409},
        )

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
        from . import automation_runs as automation

        wb = self.db.workbenches.get(workbench_id)
        if wb is not None and automation.runs_as_program(wb):
            # 2026-11-08: the run is a Program of one prompt step; the
            # schedule stays here, the work runs on the Programs engine.
            # The conductor's tick waits on it, as it waited on the item run.
            return await asyncio.to_thread(
                automation.run_as_program, self.db, scheduler_principal, wb, wait=True, key=f"schedule:{minute}")
        return await self.run(scheduler_principal, workbench_id, request_id=f"schedule:{workbench_id}:{minute}", delegation=delegation, due_minute=minute)
