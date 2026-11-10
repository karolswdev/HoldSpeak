# PARKED: routed-only readers retired with the unwritten routing tables on 2026-11-09.
from __future__ import annotations

class _Parked_find_ask_result:
    def find_ask_result(self, invocation_id: str) -> Optional[dict[str, Any]]:
        """The durable answer for one invocation identity, or None.

        Three lookups, because an ask reaches ``ask_results`` under different
        identities depending on the path it took:

        1. The classic path stages under the caller's own ``invocation_id``,
           so the direct read finds it.
        2. The routed path (an active ``…-route-assignments`` migration) stages
           under the WINNING CHILD's invocation, whose kernel operation carries
           the caller's operation as ``parent_operation_id``.  The join below
           follows that link so the same claim law holds on both paths.

        Nothing is dispatched, published or mutated here — this is a read of
        proof the kernel already settled.
        """
        with self._connection() as conn:
            row = conn.execute(
                "SELECT payload_json FROM ask_results WHERE invocation_id = ?",
                (str(invocation_id),),
            ).fetchone()
            if row is None:
                row = conn.execute(
                    """SELECT ar.payload_json
                         FROM ask_results ar
                         JOIN kernel_operations child
                           ON child.operation_id = ar.operation_id
                        WHERE child.parent_operation_id = ?
                        ORDER BY child.created_at DESC
                        LIMIT 1""",
                    (str(invocation_id),),
                ).fetchone()
            if row is None:
                # 3. Betterment Q1: the routed path today journals the winning
                #    child with no parent link, so follow the route execution
                #    of the operation this identity admitted to its winning
                #    attempt.  Without this read, the Room's settle after a
                #    routed answer found nothing and ran the question again.
                row = conn.execute(
                    """SELECT ar.payload_json
                         FROM inference_operation_route_request_plans plan
                         JOIN inference_route_executions run
                           ON run.operation_plan_id = plan.id
                         JOIN inference_route_attempts attempt
                           ON attempt.id = run.winning_attempt_id
                         JOIN ask_results ar
                           ON ar.invocation_id = attempt.child_invocation_id
                        WHERE plan.operation_id = ?
                          AND run.terminal_outcome = 'succeeded'
                        LIMIT 1""",
                    (str(invocation_id),),
                ).fetchone()
        if row is None:
            return None
        try:
            payload = json.loads(str(row["payload_json"]))
        except (TypeError, ValueError):
            return None
        return payload if isinstance(payload, dict) else None


class _Parked_invocation_run_state:
    def invocation_run_state(self, invocation_id: str) -> str:
        """Has a run used this identity: ``unused``, ``running`` or ``ended``.

        Read from the kernel's own rows.  The routed path stages its material
        and route execution under ``operation_id = invocation_id``; the
        classic path journals ``inference.invoke`` with the invocation id as
        its idempotency key.  Nothing is written here.
        """
        ident = str(invocation_id)
        with self._connection() as conn:
            routed = conn.execute(
                """SELECT e.state
                     FROM inference_operation_route_request_plans p
                     JOIN inference_route_executions e ON e.operation_plan_id = p.id
                    WHERE p.operation_id = ?""",
                (ident,),
            ).fetchall()
            if any(str(row["state"]) in {"active", "stopping"} for row in routed):
                return "running"
            classic = conn.execute(
                # An answer through the engine door runs under door_<…>_<this id>_<nonce>.
                "SELECT state FROM kernel_operations WHERE idempotency_key = ? OR operation_id = ? "
                "OR (native_id LIKE 'door\\_%' ESCAPE '\\' AND instr(native_id, ?) > 0)",
                (ident, ident, f"_{ident}_"),
            ).fetchall()
            if any(
                str(row["state"]) in {"admitting", "awaiting_decision", "awaiting_execution", "claimed"}
                for row in classic
            ):
                return "running"
            staged = conn.execute(
                "SELECT 1 FROM inference_adoption_material_snapshots WHERE operation_id = ?",
                (ident,),
            ).fetchone()
        return "ended" if (routed or classic or staged is not None) else "unused"
