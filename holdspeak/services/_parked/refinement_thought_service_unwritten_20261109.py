# PARKED: routed-only readers retired with the unwritten routing tables on 2026-11-09.
from __future__ import annotations

class _Parked__reconcile_invocation_in_transaction:
    def _reconcile_invocation_in_transaction(self, conn: Any, inv: dict[str, Any], thought: dict[str, Any]) -> None:
        # Stop, Good enough, owner edit, Answer/Accept/Reject and an earlier
        # terminal reconciliation are durable suppression fences.  Late kernel
        # proof may remain auditable in native tables, but can never resurrect
        # a review invitation after one of those owner decisions.
        if str(inv["state"]) not in {"reserved", "in_flight", "awaiting_projection", "review_ready"}:
            return
        if (int(thought["aggregate_revision"]),int(thought["working_revision"]),int(thought["attachment_revision"])) != (int(inv["frozen_aggregate_revision"]),int(inv["frozen_working_revision"]),int(inv["frozen_attachment_revision"])):
            conn.execute("UPDATE refinement_invocations SET state='stale',terminal_code='refinement_result_stale',updated_at=?,terminal_at=? WHERE id=?", (_now(),_now(),inv["id"])); return
        attempts = conn.execute("SELECT * FROM refinement_invocation_attempts WHERE invocation_id=? ORDER BY attempt_ordinal", (inv["id"],)).fetchall()
        # A crash can land after the runner durably plans the one compatibility
        # child but before that child's pre-dispatch hook has created its attempt
        # row. Reconcile names this exact plan; it never reconstructs/rebinds it.
        plans = conn.execute("SELECT * FROM refinement_retry_plans WHERE invocation_id=?", (inv["id"],)).fetchall()
        ordinals = {int(item["attempt_ordinal"]) for item in attempts}
        for plan in plans:
            child_ordinal = int(plan["child_attempt_ordinal"])
            if child_ordinal in ordinals:
                continue
            base = next((item for item in attempts if int(item["attempt_ordinal"]) == int(plan["parent_attempt_ordinal"])), None)
            from ..kernel.provider_signals import retry_invocation_id
            expected = retry_invocation_id(str(base["ask_invocation_id"]) if base else "", child_ordinal)
            if base is None or str(plan["child_ask_invocation_id"]) != expected:
                conn.execute("UPDATE refinement_invocations SET state='unknown',terminal_code='retry_plan_invalid',updated_at=?,terminal_at=? WHERE id=?", (_now(),_now(),inv["id"])); return
            native = conn.execute("SELECT operation_id FROM kernel_operations WHERE native_id=?", (str(plan["child_ask_invocation_id"]),)).fetchone()
            if native is not None:
                conn.execute("INSERT INTO refinement_invocation_attempts(invocation_id,attempt_ordinal,ask_invocation_id,state,terminal_code,created_at,terminal_at) VALUES(?,?,?,'orphaned_before_dispatch_binding','orphaned_before_dispatch_binding',?,?)", (inv["id"],child_ordinal,str(plan["child_ask_invocation_id"]),_now(),_now()))
                conn.execute("UPDATE refinement_invocations SET state='unknown',terminal_code='orphaned_before_dispatch_binding',updated_at=?,terminal_at=? WHERE id=?", (_now(),_now(),inv["id"])); return
            conn.execute("UPDATE refinement_invocations SET state='failed',terminal_code='retry_child_missing_after_plan',updated_at=?,terminal_at=? WHERE id=?", (_now(),_now(),inv["id"])); return
        winners: list[tuple[Any, Any, str]] = []; known_success = False
        for attempt in attempts:
            op = str(attempt["kernel_operation_id"] or "")
            if not op:
                native = conn.execute("SELECT operation_id FROM kernel_operations WHERE native_id=?", (attempt["ask_invocation_id"],)).fetchone()
                if native:
                    conn.execute("UPDATE refinement_invocation_attempts SET state='orphaned_before_dispatch_binding',terminal_code='orphaned_before_dispatch_binding',terminal_at=? WHERE invocation_id=? AND attempt_ordinal=?", (_now(),inv["id"],attempt["attempt_ordinal"]))
                    conn.execute("UPDATE refinement_invocations SET state='unknown',terminal_code='orphaned_before_dispatch_binding',updated_at=?,terminal_at=? WHERE id=?", (_now(),_now(),inv["id"])); return
                continue
            row = conn.execute("SELECT r.receipt_id,r.outcome,r.result_ref,s.stage_id,s.kind,s.state stage_state,s.invocation_id stage_invocation,s.operation_id stage_operation,s.result_ref stage_result_ref,a.projection_stage_id,a.invocation_id ask_invocation,a.operation_id ask_operation,a.receipt_id ask_receipt,a.payload_json,ra.id route_attempt_id,ra.child_invocation_id route_child_invocation,ra.execution_id route_execution_id,re.state route_execution_state,re.terminal_outcome route_execution_outcome,re.terminal_disposition route_execution_disposition,re.winning_attempt_id FROM kernel_receipts r LEFT JOIN kernel_projection_stages s ON s.operation_id=r.operation_id LEFT JOIN ask_results a ON a.operation_id=r.operation_id LEFT JOIN inference_route_attempts ra ON ra.child_operation_id=r.operation_id LEFT JOIN inference_route_executions re ON re.id=ra.execution_id WHERE r.operation_id=?", (op,)).fetchone()
            if row is None: continue
            if str(row["outcome"]) == "succeeded": known_success = True
            controller_winner = (
                row["route_attempt_id"] is None
                or (
                    str(row["route_execution_state"] or "") == "terminal"
                    and str(row["route_execution_outcome"] or "") == "succeeded"
                    and str(row["winning_attempt_id"] or "") == str(row["route_attempt_id"])
                )
            )
            expected_invocation = str(row["route_child_invocation"] or attempt["ask_invocation_id"])
            if str(row["outcome"]) == "succeeded" and controller_winner and row["projection_stage_id"] and str(row["result_ref"]) and str(row["stage_id"] or "") == str(row["projection_stage_id"]) and str(row["kind"] or "") == "ask-result" and str(row["stage_state"] or "") == "PUBLISHED" and str(row["stage_invocation"] or "") == expected_invocation and str(row["ask_invocation"] or "") == expected_invocation and str(row["stage_operation"] or "") == op and str(row["ask_operation"] or "") == op and str(row["ask_receipt"] or "") == str(row["receipt_id"]) and str(row["stage_result_ref"] or "") == str(row["result_ref"]):
                winners.append((attempt,row,hashlib.sha256(str(row["payload_json"]).encode()).hexdigest()))
            conn.execute("UPDATE refinement_invocation_attempts SET state=?,receipt_id=?,result_ref=?,terminal_at=? WHERE invocation_id=? AND attempt_ordinal=?", (str(row["outcome"]),row["receipt_id"],row["result_ref"],_now(),inv["id"],attempt["attempt_ordinal"]))
            # PHILO-15 10 (Astra r2, finding 1): a result the engine RETURNED
            # that failed the Thought schema is named, not a bare "failed".
            if str(row["outcome"]) == "failed" and self._structured_result_unusable(conn, op, row):
                conn.execute("UPDATE refinement_invocation_attempts SET terminal_code='structured_result_unusable' WHERE invocation_id=? AND attempt_ordinal=?", (inv["id"],attempt["attempt_ordinal"]))
        if len(winners) > 1:
            raise ConflictError("multiple refinement result attempts matched", code="refinement_correlation_mismatch")
        if winners:
            attempt,row,digest=winners[0]; existing=conn.execute("SELECT * FROM refinement_review_results WHERE invocation_id=?",(inv["id"],)).fetchone(); rid=str(existing["id"]) if existing else _id("rresult")
            # Never persist a review-ready invitation whose native payload is
            # not the narrow card grammar.  A malformed model result is a
            # named terminal outcome, not an actionable owner decision.
            try:
                self._review_card(str(row["payload_json"]))
            except ValidationError:
                conn.execute("UPDATE refinement_invocation_attempts SET state='failed',terminal_code='refinement_result_invalid',terminal_at=? WHERE invocation_id=? AND attempt_ordinal=?", (_now(), inv["id"], attempt["attempt_ordinal"]))
                conn.execute("UPDATE refinement_invocations SET state='failed',terminal_code='refinement_result_invalid',updated_at=?,terminal_at=? WHERE id=?", (_now(), _now(), inv["id"]))
                return
            if not existing:
                conn.execute("INSERT INTO refinement_review_results(id,invocation_id,attempt_ordinal,ask_result_stage_id,ask_invocation_id,kernel_operation_id,receipt_id,result_ref,frozen_aggregate_revision,frozen_working_revision,frozen_attachment_revision,result_sha256,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(rid,inv["id"],attempt["attempt_ordinal"],row["projection_stage_id"],attempt["ask_invocation_id"],attempt["kernel_operation_id"],row["receipt_id"],row["result_ref"],inv["frozen_aggregate_revision"],inv["frozen_working_revision"],inv["frozen_attachment_revision"],digest,_now()))
            elif (str(existing["ask_result_stage_id"]),str(existing["ask_invocation_id"]),str(existing["kernel_operation_id"]),str(existing["receipt_id"]),str(existing["result_ref"]),str(existing["result_sha256"])) != (str(row["projection_stage_id"]),str(attempt["ask_invocation_id"]),str(attempt["kernel_operation_id"]),str(row["receipt_id"]),str(row["result_ref"]),digest):
                raise ConflictError("stored review result does not match native proof", code="refinement_correlation_mismatch")
            conn.execute("UPDATE refinement_invocation_attempts SET state='succeeded',receipt_id=?,projection_stage_id=?,ask_result_stage_id=?,result_ref=?,terminal_at=? WHERE invocation_id=? AND attempt_ordinal=?",(row["receipt_id"],row["stage_id"],row["projection_stage_id"],row["result_ref"],_now(),inv["id"],attempt["attempt_ordinal"]))
            conn.execute("UPDATE refinement_invocations SET state='review_ready',review_result_id=?,updated_at=? WHERE id=?",(rid,_now(),inv["id"]))
        elif attempts and all(not str(item["kernel_operation_id"] or "") for item in attempts):
            conn.execute("UPDATE refinement_invocations SET state='unknown',terminal_code='kernel_operation_missing',updated_at=?,terminal_at=? WHERE id=?", (_now(),_now(),inv["id"]))
        elif known_success:
            conn.execute("UPDATE refinement_invocations SET state='awaiting_projection',terminal_code='ask_result_unpublished',updated_at=? WHERE id=?", (_now(),inv["id"]))
        else:
            fresh_attempts = conn.execute("SELECT state,terminal_code FROM refinement_invocation_attempts WHERE invocation_id=? ORDER BY attempt_ordinal", (inv["id"],)).fetchall()
            plans = conn.execute("SELECT child_attempt_ordinal FROM refinement_retry_plans WHERE invocation_id=?", (inv["id"],)).fetchall()
            planned_children = {int(row["child_attempt_ordinal"]) for row in plans}
            present = set(range(1, len(fresh_attempts) + 1))
            terminal = {"failed", "refused", "cancelled", "indeterminate", "orphaned_before_dispatch_binding"}
            if fresh_attempts and all(str(row["state"]) in terminal for row in fresh_attempts) and planned_children <= present:
                last = fresh_attempts[-1]
                state = "unknown" if str(last["state"]) == "orphaned_before_dispatch_binding" else str(last["state"])
                conn.execute("UPDATE refinement_invocations SET state=?,terminal_code=?,updated_at=?,terminal_at=? WHERE id=?", (state,_closed_terminal_code(str(last["terminal_code"] or state)),_now(),_now(),inv["id"]))


