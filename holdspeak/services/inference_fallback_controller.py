"""Durable retry and fallback authority for frozen inference routes (HS-143-06)."""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone
from typing import Any

from ..principals import Principal, PrincipalKind
from .errors import ConflictError, ValidationError
from .inference_route_plan_service import (
    ROUTE_PLANNING_AUTHORITY,
    InferenceRoutePlanService,
)

ROUTE_EXECUTION_RECEIPT_SCHEMA = "RouteExecutionReceipt@1"
FALLBACK_CLASSIFIER_REVISION = "inference-fallback-dispositions@1"
INFERENCE_FALLBACK_AUTHORITY = Principal(
    PrincipalKind.SERVICE,
    "inference-fallback-controller",
    authority_basis="kernel:inference-routing@1",
)


def _canonical(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def _sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode()).hexdigest()


def _timestamp(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


class InferenceFallbackController:
    """The sole server-owned state machine above :class:`InferenceRunner`.

    Story 05 owns immutable route/request evidence.  This controller binds one
    execution to those exact hashes before it may reserve a physical child.
    """

    def __init__(
        self,
        db: Any,
        *,
        route_plan_service: InferenceRoutePlanService,
        kernel_child_reader: Any | None = None,
        kernel_receipt_reader: Any | None = None,
        clock: Any | None = None,
    ) -> None:
        self._db = db
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._plans = route_plan_service
        self._kernel_child_reader = kernel_child_reader
        self._kernel_receipt_reader = kernel_receipt_reader

    def start_execution(
        self,
        authority: Principal,
        *,
        command_id: str,
        operation_plan_id: str,
    ) -> dict[str, Any]:
        """Create/adopt one execution head bound to frozen Story-05 evidence."""
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                result = self.start_execution_in_transaction(
                    authority, conn, command_id=command_id,
                    operation_plan_id=operation_plan_id,
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return result

    def start_execution_in_transaction(
        self,
        authority: Principal,
        conn: Any,
        *,
        command_id: str,
        operation_plan_id: str,
    ) -> dict[str, Any]:
        """Create/adopt an execution inside a caller-owned transaction."""
        self._require_controller(authority)
        command = self._safe_id(command_id, "command_id")
        operation_id = self._safe_id(operation_plan_id, "operation_plan_id")
        request_hash = _sha256({"action": "start", "command_id": command, "operation_plan_id": operation_id})
        execution_id = "ire_" + hashlib.sha256(request_hash.encode()).hexdigest()[:32]
        replay = conn.execute(
            "SELECT * FROM inference_route_execution_commands WHERE command_id=?", (command,)
        ).fetchone()
        if replay is not None and str(replay["request_sha256"]) != request_hash:
            raise ConflictError("Route execution command changed.", code="inference_route_execution_command_conflict")
        operation, route = self._plans.reconstruct_frozen_pair_in_transaction(
            ROUTE_PLANNING_AUTHORITY, conn, operation_id
        )
        policy = route["retry_policy"]
        budgets = self._plans.reconstruct_attempt_budgets_in_transaction(
            ROUTE_PLANNING_AUTHORITY, conn, operation=operation, route=route
        )
        if replay is not None:
            effect = json.loads(str(replay["effect_json"]))
            if str(replay["execution_id"]) != execution_id or str(replay["effect_sha256"]) != _sha256(effect) or effect != {"execution_id": execution_id}:
                raise ConflictError("Stored route execution command is invalid.", code="inference_route_execution_command_integrity_invalid")
            return self._execution(conn, execution_id)
        parent_rows = conn.execute(
            """SELECT p.state FROM inference_parent_route_bundle_members m
                   JOIN inference_parent_route_bundles b ON b.id=m.bundle_id
                   LEFT JOIN kernel_parent_runs p ON p.operation_id=b.parent_operation_id
                  WHERE m.route_plan_id=?""",
            (route["id"],),
        ).fetchall()
        if parent_rows and any(str(row["state"] or "") != "OPEN" for row in parent_rows):
            raise ConflictError(
                "Route execution parent is sealed.",
                code="inference_route_execution_parent_sealed",
            )
        collision = conn.execute(
            "SELECT 1 FROM inference_route_executions WHERE id=? OR operation_plan_id=?",
            (execution_id, operation_id),
        ).fetchone()
        if collision is not None:
            raise ConflictError("Route execution identity is already in use.", code="inference_route_execution_identity_conflict")
        now = self._clock()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        created_at = _timestamp(now)
        conn.execute(
            """INSERT INTO inference_route_executions
               (id,route_plan_id,route_plan_sha256,operation_plan_id,
                operation_plan_sha256,budget_evidence_provider_id,
                budget_evidence_provider_revision,budget_evidence_sha256,
                state,revision,total_attempt_limit,per_leg_attempt_limit,
                token_budget,cost_budget,tool_call_budget,started_at)
               VALUES (?,?,?,?,?,?,?,?,'active',1,?,?,?,?,?,?)""",
            (execution_id, route["id"], route["sha256"], operation["id"], operation["sha256"],
             budgets["provider_id"], budgets["provider_revision"], budgets["sha256"],
             int(policy["total_physical_attempts"]), int(policy["per_entry_attempts"]),
             policy["token_budget"], policy["cost_budget"], policy["tool_call_budget"], created_at),
        )
        effect = {"execution_id": execution_id}
        conn.execute(
            "INSERT INTO inference_route_execution_commands VALUES (?,?,?,?,?,?,?)",
            (command, "start", request_hash, execution_id, _canonical(effect), _sha256(effect), created_at),
        )
        self._insert_transition(
            conn, execution_id, action="start", command_id=command,
            prior_revision=0, post_revision=1, prior_state="none", post_state="active", effect=effect,
        )
        return self._execution(conn, execution_id)

    def get_route_execution_receipt(
        self, authority: Principal, *, execution_id: str
    ) -> dict[str, Any]:
        """Reconstruct the privacy-safe receipt from immutable frozen evidence."""
        if authority != INFERENCE_FALLBACK_AUTHORITY and authority.kind is not PrincipalKind.OWNER:
            raise ValidationError(
                "Route receipt inspection requires owner or controller authority.",
                code="inference_route_receipt_authority_required",
            )
        execution = self._safe_id(execution_id, "execution_id")
        with self._db._connection() as conn:
            self._execution(conn, execution)
            return self._route_execution_receipt(conn, execution)

    def reserve_next_attempt(
        self,
        authority: Principal,
        *,
        command_id: str,
        execution_id: str,
    ) -> dict[str, Any]:
        """Reserve the only next lawful physical child from frozen evidence.

        The caller supplies no leg, deployment, ordinal, purpose, or budget.
        Those facts are selected and debited under the execution transaction.
        """
        self._require_controller(authority)
        command = self._safe_id(command_id, "command_id")
        execution = self._safe_id(execution_id, "execution_id")
        request_hash = _sha256(
            {"action": "reserve", "command_id": command, "execution_id": execution}
        )
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                replay = conn.execute(
                    "SELECT * FROM inference_route_execution_commands WHERE command_id=?",
                    (command,),
                ).fetchone()
                if replay is not None:
                    if str(replay["action"]) != "reserve" or str(replay["request_sha256"]) != request_hash:
                        raise ConflictError("Route execution command changed.", code="inference_route_execution_command_conflict")
                    effect = json.loads(str(replay["effect_json"]))
                    if str(replay["execution_id"]) != execution or str(replay["effect_sha256"]) != _sha256(effect):
                        raise ConflictError("Stored reservation effect is invalid.", code="inference_route_execution_command_integrity_invalid")
                    self._verify_reserve_effect(conn, execution, effect)
                    conn.commit()
                    return effect
                row = conn.execute(
                    "SELECT * FROM inference_route_executions WHERE id=?", (execution,)
                ).fetchone()
                if row is None:
                    raise ValidationError("Route execution is missing.", code="inference_route_execution_missing")
                projection = self._execution(conn, execution)
                operation, route = self._plans.reconstruct_frozen_pair_in_transaction(
                    ROUTE_PLANNING_AUTHORITY, conn, projection["operation_plan_id"]
                )
                now = self._clock()
                if now.tzinfo is None:
                    now = now.replace(tzinfo=timezone.utc)
                now_text = _timestamp(now)
                if bool(row["stop_requested"]) or str(row["state"]) != "active":
                    raise ConflictError("Route execution is terminal.", code="inference_route_execution_terminal")
                deadline = datetime.fromisoformat(str(route["deadline_at"]).replace("Z", "+00:00"))
                if now >= deadline:
                    conn.execute(
                        """UPDATE inference_route_executions
                           SET state='terminal',revision=revision+1,
                               terminal_disposition='deadline_exhausted',
                               terminal_outcome='cancelled',terminal_at=? WHERE id=?""",
                        (now_text, execution),
                    )
                    effect = {"schema": "RouteAttemptReservationEffect@1", "execution_id": execution, "terminal": "deadline_exhausted", "reservation": None}
                    self._insert_command(conn, command, "reserve", request_hash, execution, effect, now_text)
                    self._insert_transition(conn, execution, action="reserve", command_id=command, prior_revision=int(row["revision"]), post_revision=int(row["revision"])+1, prior_state="active", post_state="terminal", effect=effect)
                    conn.commit()
                    return effect
                outstanding = conn.execute(
                    "SELECT id FROM inference_route_attempts WHERE execution_id=? AND state<>'terminal'",
                    (execution,),
                ).fetchone()
                if outstanding is not None:
                    raise ConflictError("A physical attempt is already reserved.", code="inference_route_attempt_outstanding")
                prior_rows = conn.execute(
                    "SELECT * FROM inference_route_attempts WHERE execution_id=? ORDER BY physical_attempt_ordinal",
                    (execution,),
                ).fetchall()
                if prior_rows:
                    last = prior_rows[-1]
                    last_disposition = str(last["disposition"])
                    retryable = (
                        last_disposition in route["retry_policy"]["retryable_dispositions"]
                        and int(last["leg_attempt_ordinal"]) < int(row["per_leg_attempt_limit"])
                    )
                    fallback = (
                        not retryable
                        and last_disposition in route["retry_policy"]["fallback_dispositions"]
                        and int(last["route_leg_ordinal"]) < len(route["entries"])
                    )
                    if str(last["state"]) != "terminal" or not (retryable or fallback):
                        raise ConflictError("The prior attempt is not eligible for retry.", code="inference_route_advance_not_ready")
                    if retryable:
                        leg_ordinal = int(last["route_leg_ordinal"])
                        leg_attempt_ordinal = int(last["leg_attempt_ordinal"]) + 1
                        last_evidence = json.loads(str(last["disposition_evidence_json"] or "{}"))
                        purpose = "compatibility" if last_evidence.get("typed_signal") == "compatibility_no_generation" else "retry"
                    else:
                        leg_ordinal = int(last["route_leg_ordinal"]) + 1
                        leg_attempt_ordinal, purpose = 1, "fallback"
                else:
                    leg_ordinal, leg_attempt_ordinal, purpose = 1, 1, "primary"
                planned = operation["entries"][leg_ordinal - 1]
                if planned["eligibility"] == "known_context_overflow":
                    next_ordinal = leg_ordinal + 1
                    larger = bool(
                        "context_overflow" in route["retry_policy"]["fallback_dispositions"]
                        and next_ordinal <= len(route["entries"])
                        and operation["entries"][next_ordinal - 1]["eligibility"] == "executable"
                        and int(route["entries"][next_ordinal - 1]["context_support"]["maximum_tokens"])
                           > int(route["entries"][leg_ordinal - 1]["context_support"]["maximum_tokens"])
                    )
                    if larger:
                        conn.execute(
                            "INSERT INTO inference_route_execution_skips VALUES (?,?,?,?,?,?)",
                            (f"{execution}:{leg_ordinal}", execution, leg_ordinal,
                             "context_overflow", str(planned["reason_code"]), now_text),
                        )
                        leg_ordinal, leg_attempt_ordinal, purpose = next_ordinal, 1, "fallback"
                        planned = operation["entries"][leg_ordinal - 1]
                if planned["eligibility"] != "executable":
                    disposition = "context_overflow" if planned["eligibility"] == "known_context_overflow" else "preflight_unavailable"
                    conn.execute(
                        "INSERT INTO inference_route_execution_skips VALUES (?,?,?,?,?,?)",
                        (f"{execution}:{leg_ordinal}", execution, leg_ordinal, disposition, str(planned["reason_code"]), now_text),
                    )
                    # Current v1 policies do not authorize preflight-unavailable
                    # advancement. Context overflow advancement is implemented only
                    # when a strictly larger executable frozen leg is selected.
                    conn.execute(
                        """UPDATE inference_route_executions
                           SET state='terminal',revision=revision+1,
                               terminal_disposition=?,terminal_outcome='failed',terminal_at=?
                           WHERE id=?""",
                        (disposition, now_text, execution),
                    )
                    effect = {"schema": "RouteAttemptReservationEffect@1", "execution_id": execution, "terminal": disposition, "reservation": None}
                    self._insert_command(conn, command, "reserve", request_hash, execution, effect, now_text)
                    self._insert_transition(conn, execution, action="reserve", command_id=command, prior_revision=int(row["revision"]), post_revision=int(row["revision"])+1, prior_state="active", post_state="terminal", effect=effect)
                    conn.commit()
                    return effect
                budgets = self._plans.reconstruct_attempt_budgets_in_transaction(
                    ROUTE_PLANNING_AUTHORITY, conn, operation=operation, route=route
                )
                budget = budgets["entries"][leg_ordinal - 1]
                if route["retry_policy"]["cost_budget"] is not None:
                    raise ValidationError("Cost budget units are not versioned.", code="inference_route_cost_budget_unit_unsupported")
                if int(budget["reserved_cost_units"]) != 0:
                    raise ValidationError("Cost reservation is unsupported.", code="inference_route_cost_budget_unit_unsupported")
                if route["retry_policy"]["tool_call_budget"] is not None or int(budget["reserved_tool_calls"]) != 0:
                    raise ValidationError("Tool lease budget evidence is required.", code="inference_route_tool_budget_evidence_missing")
                tokens = int(budget["total_tokens"])
                total_limit = int(row["total_attempt_limit"])
                if int(row["attempts_reserved"]) + 1 > total_limit:
                    raise ConflictError("Physical attempt budget is exhausted.", code="inference_route_attempt_budget_exhausted")
                if row["token_budget"] is not None and int(row["tokens_reserved"]) + tokens > int(row["token_budget"]):
                    raise ConflictError("Token budget is exhausted.", code="inference_route_token_budget_exhausted")
                nonce = secrets.token_urlsafe(32)
                physical = int(row["attempts_reserved"]) + 1
                attempt_id = f"ira_{hashlib.sha256(f'{execution}:{physical}'.encode()).hexdigest()[:32]}"
                invocation_id = f"invoke_{hashlib.sha256(attempt_id.encode()).hexdigest()[:32]}"
                leg = route["entries"][leg_ordinal - 1]
                conn.execute(
                    """INSERT INTO inference_route_attempts
                       (id,execution_id,route_leg_ordinal,physical_attempt_ordinal,
                        leg_attempt_ordinal,purpose,deployment_revision_id,boundary,state,
                        child_invocation_id,admission_nonce_sha256,
                        reservation_command_id,
                        budget_evidence_provider_id,budget_evidence_provider_revision,
                        budget_evidence_sha256,reserved_token_budget,reserved_cost_budget,
                        reserved_tool_call_budget,reserved_at)
                       VALUES (?,?,?,?,?,?,?,?,'reserved',?,?,?,?,?,?,?,?,?,?)""",
                    (
                        attempt_id, execution, leg_ordinal, physical, leg_attempt_ordinal,
                        purpose, leg["deployment_revision_id"], leg["boundary"], invocation_id,
                        _sha256({"nonce": nonce}), command, budgets["provider_id"], budgets["provider_revision"],
                        budgets["sha256"], tokens, 0, 0, now_text,
                    ),
                )
                conn.execute(
                    """UPDATE inference_route_executions
                       SET revision=revision+1,attempts_reserved=attempts_reserved+1,
                           tokens_reserved=tokens_reserved+? WHERE id=?""",
                    (tokens, execution),
                )
                reservation = {
                    "schema": "InferenceRouteAttemptReservation@1",
                    "attempt_id": attempt_id,
                    "execution_id": execution,
                    "route_plan_id": route["id"],
                    "operation_plan_id": operation["id"],
                    "route_leg_ordinal": leg_ordinal,
                    "physical_attempt_ordinal": physical,
                    "leg_attempt_ordinal": leg_attempt_ordinal,
                    "purpose": purpose,
                    "deployment_revision_id": leg["deployment_revision_id"],
                    "child_invocation_id": invocation_id,
                    "nonce": nonce,
                }
                effect = {"schema": "RouteAttemptReservationEffect@1", "execution_id": execution, "terminal": None, "reservation": reservation}
                self._insert_command(conn, command, "reserve", request_hash, execution, effect, now_text)
                self._insert_transition(conn, execution, action="reserve", command_id=command, prior_revision=int(row["revision"]), post_revision=int(row["revision"])+1, prior_state="active", post_state="active", effect=effect)
                conn.commit()
                return effect
            except Exception:
                conn.rollback()
                raise

    def claim_reservation(
        self, authority: Principal, *, command_id: str, reservation: dict[str, Any]
    ) -> dict[str, Any]:
        """Consume one controller-minted reservation before broker submission."""
        self._require_controller(authority)
        command = self._safe_id(command_id, "command_id")
        ticket = self._closed_reservation(reservation)
        if command != f"claim-{ticket['attempt_id']}":
            raise ConflictError(
                "Claim command identity is not controller-derived.",
                code="inference_route_execution_command_conflict",
            )
        request_hash = _sha256({"action": "claim", "command_id": command, "reservation": ticket})
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                replay = self._replay_command(conn, command, "claim", request_hash, ticket["execution_id"])
                if replay is not None:
                    self._verify_claim_effect(conn, ticket, replay)
                    conn.commit()
                    return replay
                attempt, execution, _operation, route = self._reservation_rows(conn, ticket)
                if str(attempt["state"]) != "reserved":
                    raise ConflictError("Reservation was already consumed.", code="inference_route_reservation_consumed")
                self._fence_execution(execution, route)
                now_text = self._now_text()
                conn.execute(
                    "UPDATE inference_route_attempts SET state='admitted',admitted_at=? WHERE id=? AND state='reserved'",
                    (now_text, ticket["attempt_id"]),
                )
                if conn.total_changes < 1:
                    raise ConflictError("Reservation was already consumed.", code="inference_route_reservation_consumed")
                effect = {
                    "schema": "InferenceRouteAttemptClaim@1",
                    "attempt_id": ticket["attempt_id"],
                    "child_invocation_id": ticket["child_invocation_id"],
                    "deployment_revision_id": ticket["deployment_revision_id"],
                    "physical_attempt_ordinal": ticket["physical_attempt_ordinal"],
                }
                self._insert_command(conn, command, "claim", request_hash, ticket["execution_id"], effect, now_text)
                conn.commit()
                return effect
            except Exception:
                conn.rollback()
                raise

    def bind_admitted_child(
        self,
        authority: Principal,
        *,
        command_id: str,
        attempt_id: str,
        child_operation_id: str,
    ) -> dict[str, Any]:
        """Bind only the exact claimed kernel child created for this reservation."""
        self._require_controller(authority)
        command = self._safe_id(command_id, "command_id")
        attempt_key = self._safe_id(attempt_id, "attempt_id")
        child_key = self._safe_id(child_operation_id, "child_operation_id")
        if command != f"bind-{attempt_key}":
            raise ConflictError(
                "Bind command identity is not controller-derived.",
                code="inference_route_execution_command_conflict",
            )
        request_hash = _sha256({"action": "bind", "command_id": command, "attempt_id": attempt_key, "child_operation_id": child_key})
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                attempt = conn.execute("SELECT * FROM inference_route_attempts WHERE id=?", (attempt_key,)).fetchone()
                if attempt is None:
                    raise ValidationError("Route attempt is missing.", code="inference_route_attempt_missing")
                replay = self._replay_command(conn, command, "bind", request_hash, str(attempt["execution_id"]))
                if replay is not None:
                    if replay != self._bind_effect(attempt):
                        raise ConflictError("Stored bind effect is invalid.", code="inference_route_execution_command_integrity_invalid")
                    conn.commit()
                    return replay
                if str(attempt["state"]) != "admitted" or attempt["child_operation_id"] is not None:
                    raise ConflictError("Route attempt cannot bind another child.", code="inference_route_attempt_already_bound")
                if self._kernel_child_reader is None:
                    raise ValidationError("Kernel child reconstruction is not composed.", code="inference_route_kernel_reader_missing")
                child = self._kernel_child_reader(child_key)
                if (
                    child is None
                    or str(child["name"]) != "inference.invoke"
                    or int(child["version"]) != 1
                    or str(child["state"]) != "claimed"
                    or str(child["native_id"]) != str(attempt["child_invocation_id"])
                    or str(child["target_ref"]) != f"deployment-revision:{attempt['deployment_revision_id']}"
                ):
                    raise ConflictError("Kernel child does not match the reservation.", code="inference_route_child_binding_invalid")
                conn.execute("UPDATE inference_route_attempts SET child_operation_id=? WHERE id=? AND child_operation_id IS NULL", (child_key, attempt_key))
                attempt = conn.execute("SELECT * FROM inference_route_attempts WHERE id=?", (attempt_key,)).fetchone()
                effect = self._bind_effect(attempt)
                self._insert_command(conn, command, "bind", request_hash, str(attempt["execution_id"]), effect, self._now_text())
                conn.commit()
                return effect
            except Exception:
                conn.rollback()
                raise
    def mark_dispatch_intent(
        self, authority: Principal, *, command_id: str, attempt_id: str
    ) -> dict[str, Any]:
        """Persist the final pre-network fact; crash after this point is unknown."""
        self._require_controller(authority)
        command = self._safe_id(command_id, "command_id")
        attempt_key = self._safe_id(attempt_id, "attempt_id")
        if command != f"dispatch-{attempt_key}":
            raise ConflictError(
                "Dispatch command identity is not controller-derived.",
                code="inference_route_execution_command_conflict",
            )
        request_hash = _sha256({"action": "dispatch_intent", "command_id": command, "attempt_id": attempt_key})
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                attempt = conn.execute("SELECT * FROM inference_route_attempts WHERE id=?", (attempt_key,)).fetchone()
                if attempt is None:
                    raise ValidationError("Route attempt is missing.", code="inference_route_attempt_missing")
                replay = self._replay_command(conn, command, "dispatch_intent", request_hash, str(attempt["execution_id"]))
                if replay is not None:
                    if replay != self._dispatch_effect(attempt):
                        raise ConflictError("Stored dispatch effect is invalid.", code="inference_route_execution_command_integrity_invalid")
                    conn.commit()
                    return replay
                execution = conn.execute("SELECT * FROM inference_route_executions WHERE id=?", (attempt["execution_id"],)).fetchone()
                projection = self._execution(conn, str(attempt["execution_id"]))
                _operation, route = self._plans.reconstruct_frozen_pair_in_transaction(ROUTE_PLANNING_AUTHORITY, conn, projection["operation_plan_id"])
                self._fence_execution(execution, route)
                if str(attempt["state"]) != "admitted" or not attempt["child_operation_id"]:
                    raise ConflictError("A bound admitted child is required.", code="inference_route_child_not_bound")
                now_text = self._now_text()
                conn.execute("UPDATE inference_route_attempts SET state='dispatch_intent',dispatch_intent_at=? WHERE id=? AND state='admitted'", (now_text, attempt_key))
                attempt = conn.execute("SELECT * FROM inference_route_attempts WHERE id=?", (attempt_key,)).fetchone()
                effect = self._dispatch_effect(attempt)
                self._insert_command(conn, command, "dispatch_intent", request_hash, str(attempt["execution_id"]), effect, now_text)
                conn.commit()
                return effect
            except Exception:
                conn.rollback()
                raise

    def settle_attempt(
        self, authority: Principal, *, command_id: str, attempt_id: str
    ) -> dict[str, Any]:
        """Crash-adopt a durable child receipt without accepting classifications."""
        return self._settle_runner_evidence(
            authority, command_id=command_id, attempt_id=attempt_id,
        )

    def adopt_pre_send_receipt(
        self, authority: Principal, *, command_id: str, attempt_id: str,
        child_operation_id: str,
    ) -> dict[str, Any]:
        """Adopt an attested refusal that terminalized before child claim/bind."""
        self._require_controller(authority)
        command = self._safe_id(command_id, "command_id")
        attempt_key = self._safe_id(attempt_id, "attempt_id")
        child_key = self._safe_id(child_operation_id, "child_operation_id")
        request_hash = _sha256({"action": "settle", "command_id": command, "attempt_id": attempt_key, "child_operation_id": child_key})
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                attempt = conn.execute("SELECT * FROM inference_route_attempts WHERE id=?", (attempt_key,)).fetchone()
                if attempt is None:
                    raise ValidationError("Route attempt is missing.", code="inference_route_attempt_missing")
                execution_id = str(attempt["execution_id"])
                replay = self._replay_command(conn, command, "settle", request_hash, execution_id)
                if replay is not None:
                    if replay != self._settlement_effect(conn, execution_id, attempt_key):
                        raise ConflictError("Stored settlement effect is invalid.", code="inference_route_execution_command_integrity_invalid")
                    conn.commit(); return replay
                if str(attempt["state"]) != "admitted" or (
                    attempt["child_operation_id"] is not None
                    and str(attempt["child_operation_id"]) != child_key
                ):
                    raise ConflictError("Attempt cannot adopt a pre-send child.", code="inference_route_attempt_already_bound")
                if self._kernel_receipt_reader is None:
                    raise ValidationError("Kernel receipt reconstruction is not composed.", code="inference_route_kernel_receipt_reader_missing")
                reconstructed = self._kernel_receipt_reader(child_key)
                operation = None if reconstructed is None else reconstructed.get("operation")
                receipt = None if reconstructed is None else reconstructed.get("receipt")
                attestation = None if reconstructed is None else reconstructed.get("terminal_attestation")
                if (
                    not isinstance(operation, dict) or not isinstance(receipt, dict) or not isinstance(attestation, dict)
                    or str(operation.get("native_id") or "") != str(attempt["child_invocation_id"])
                    or str(operation.get("target_ref") or "") != f"deployment-revision:{attempt['deployment_revision_id']}"
                    or str(attestation.get("send_phase") or "") != "pre_send"
                ):
                    raise ConflictError("Pre-send child receipt is invalid.", code="inference_route_child_receipt_invalid")
                receipt_sha = _sha256(receipt)
                typed_signal = str(attestation.get("runner_signal") or "none")
                disposition, send_phase = self._classify_receipt(
                    str(receipt["state"]), typed_signal, "pre_send"
                )
                if send_phase != "pre_send":
                    raise ConflictError(
                        "Runner send phase contradicts kernel truth.",
                        code="inference_route_disposition_evidence_invalid",
                    )
                evidence = {
                    "schema": "RunnerDispositionEvidence@1", "attempt_id": attempt_key,
                    "child_operation_id": child_key, "child_receipt_id": str(receipt["receipt_id"]),
                    "child_receipt_sha256": receipt_sha,
                    "kernel_outcome": str(receipt["state"]),
                    "send_phase": send_phase, "typed_signal": typed_signal,
                    "classifier_revision": FALLBACK_CLASSIFIER_REVISION,
                }
                now_text = self._now_text()
                conn.execute(
                    """UPDATE inference_route_attempts SET state='terminal',child_operation_id=?,
                         disposition=?,outcome=?,child_receipt_sha256=?,
                         disposition_evidence_json=?,disposition_evidence_sha256=?,classifier_revision=?,
                         send_phase='pre_send',terminal_at=? WHERE id=? AND state='admitted'""",
                    (child_key, disposition, str(receipt["state"]), receipt_sha, _canonical(evidence), _sha256(evidence),
                     FALLBACK_CLASSIFIER_REVISION, now_text, attempt_key),
                )
                head = conn.execute("SELECT * FROM inference_route_executions WHERE id=?", (execution_id,)).fetchone()
                prior_state, prior_revision = str(head["state"]), int(head["revision"])
                if prior_state != "active":
                    raise ConflictError("Route terminal was already elected.", code="inference_route_execution_terminal")
                operation_plan, route_plan = self._plans.reconstruct_frozen_pair_in_transaction(
                    ROUTE_PLANNING_AUTHORITY, conn, str(head["operation_plan_id"])
                )
                next_leg = int(attempt["route_leg_ordinal"]) + 1
                may_fallback = bool(
                    disposition in route_plan["retry_policy"]["fallback_dispositions"]
                    and next_leg <= len(route_plan["entries"])
                    and operation_plan["entries"][next_leg - 1]["eligibility"] == "executable"
                    and int(head["attempts_reserved"]) < int(head["total_attempt_limit"])
                )
                if may_fallback:
                    conn.execute("UPDATE inference_route_executions SET revision=revision+1 WHERE id=?", (execution_id,))
                    post_state = "active"
                else:
                    conn.execute(
                        """UPDATE inference_route_executions SET state='terminal',revision=revision+1,
                             terminal_disposition=?,terminal_outcome=?,terminal_at=? WHERE id=?""",
                        (disposition, str(receipt["state"]), now_text, execution_id),
                    )
                    post_state = "terminal"
                effect = self._settlement_effect(conn, execution_id, attempt_key)
                self._insert_command(conn, command, "settle", request_hash, execution_id, effect, now_text)
                self._insert_transition(conn, execution_id, action="settle", command_id=command,
                    prior_revision=prior_revision, post_revision=prior_revision + 1,
                    prior_state=prior_state, post_state=post_state, effect=effect)
                self._execution(conn, execution_id)
                conn.commit(); return effect
            except Exception:
                conn.rollback(); raise

    def _settle_runner_evidence(
        self,
        authority: Principal,
        *,
        command_id: str,
        attempt_id: str,
    ) -> dict[str, Any]:
        """Adopt immutable kernel truth and elect the route's terminal result.

        Callers cannot nominate a disposition or outcome.  The only auxiliary
        input is a closed Runner control signal; kernel receipt state remains the
        outcome authority and the classifier below owns its meaning.
        """
        self._require_controller(authority)
        command = self._safe_id(command_id, "command_id")
        attempt_key = self._safe_id(attempt_id, "attempt_id")
        request_hash = _sha256({
            "action": "settle", "command_id": command,
            "attempt_id": attempt_key,
        })
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                attempt = conn.execute(
                    "SELECT * FROM inference_route_attempts WHERE id=?", (attempt_key,)
                ).fetchone()
                if attempt is None:
                    raise ValidationError("Route attempt is missing.", code="inference_route_attempt_missing")
                execution_id = str(attempt["execution_id"])
                replay = self._replay_command(conn, command, "settle", request_hash, execution_id)
                if replay is not None:
                    expected = self._settlement_effect(conn, execution_id, attempt_key)
                    if replay != expected:
                        raise ConflictError("Stored settlement effect is invalid.", code="inference_route_execution_command_integrity_invalid")
                    conn.commit()
                    return replay
                if str(attempt["state"]) != "dispatch_intent" or not attempt["child_operation_id"]:
                    raise ConflictError("Only a dispatched bound child can settle.", code="inference_route_attempt_not_dispatched")
                if self._kernel_receipt_reader is None:
                    raise ValidationError("Kernel receipt reconstruction is not composed.", code="inference_route_kernel_receipt_reader_missing")
                reconstructed = self._kernel_receipt_reader(str(attempt["child_operation_id"]))
                if reconstructed is None:
                    raise ConflictError("Kernel receipt is not durable yet.", code="inference_route_child_receipt_missing")
                operation = reconstructed.get("operation")
                receipt = reconstructed.get("receipt")
                attestation = reconstructed.get("terminal_attestation")
                if (
                    not isinstance(operation, dict) or not isinstance(receipt, dict)
                    or not isinstance(attestation, dict)
                    or str(operation.get("operation_id") or "") != str(attempt["child_operation_id"])
                    or str(operation.get("native_id") or "") != str(attempt["child_invocation_id"])
                    or str(operation.get("target_ref") or "") != f"deployment-revision:{attempt['deployment_revision_id']}"
                    or str(receipt.get("operation_id") or "") != str(attempt["child_operation_id"])
                ):
                    raise ConflictError("Kernel receipt crosses route attempts.", code="inference_route_child_receipt_invalid")
                typed_signal = str(attestation.get("runner_signal") or "")
                attested_send_phase = str(attestation.get("send_phase") or "")
                if typed_signal not in {
                    "none", "compatibility_no_generation", "physical_outcome_unknown",
                    "dispatch_outcome_unknown", "kernel_refused", "unclassified_pre_send",
                    "known_no_generation_transient",
                    "provider_permanent_no_generation", "permission_denied",
                    "local_capacity_unavailable", "invalid_typed_output",
                    "effect_indeterminate",
                }:
                    raise ConflictError("Attested Runner signal is unknown.", code="inference_route_disposition_evidence_invalid")
                outcome = str(receipt["state"])
                disposition, send_phase = self._classify_receipt(outcome, typed_signal, attested_send_phase)
                if attested_send_phase != send_phase:
                    raise ConflictError("Runner send phase contradicts kernel truth.", code="inference_route_disposition_evidence_invalid")
                receipt_sha = _sha256(receipt)
                evidence = {
                    "schema": "RunnerDispositionEvidence@1",
                    "attempt_id": attempt_key,
                    "child_operation_id": str(attempt["child_operation_id"]),
                    "child_receipt_id": str(receipt["receipt_id"]),
                    "child_receipt_sha256": receipt_sha,
                    "kernel_outcome": outcome,
                    "send_phase": send_phase,
                    "typed_signal": typed_signal,
                    "classifier_revision": FALLBACK_CLASSIFIER_REVISION,
                }
                now_text = self._now_text()
                result_ref = str(receipt.get("result_ref") or "") if outcome == "succeeded" else ""
                conn.execute(
                    """UPDATE inference_route_attempts
                         SET state='terminal',disposition=?,outcome=?,result_ref=?,
                             child_receipt_sha256=?,disposition_evidence_json=?,
                             disposition_evidence_sha256=?,classifier_revision=?,send_phase=?,terminal_at=?
                       WHERE id=? AND state='dispatch_intent'""",
                    (disposition, outcome, result_ref, receipt_sha, _canonical(evidence),
                     _sha256(evidence), FALLBACK_CLASSIFIER_REVISION, send_phase, now_text, attempt_key),
                )
                head = conn.execute("SELECT * FROM inference_route_executions WHERE id=?", (execution_id,)).fetchone()
                if str(head["state"]) not in {"active", "stopping"}:
                    raise ConflictError("Route terminal was already elected.", code="inference_route_execution_terminal")
                prior_state, prior_revision = str(head["state"]), int(head["revision"])
                _operation_plan, route_plan = self._plans.reconstruct_frozen_pair_in_transaction(
                    ROUTE_PLANNING_AUTHORITY, conn, str(head["operation_plan_id"])
                )
                policy = route_plan["retry_policy"]
                leg_attempts = conn.execute(
                    "SELECT COUNT(*) FROM inference_route_attempts WHERE execution_id=? AND route_leg_ordinal=?",
                    (execution_id, int(attempt["route_leg_ordinal"])),
                ).fetchone()[0]
                may_retry = bool(
                    prior_state == "active"
                    and outcome != "succeeded"
                    and disposition in policy["retryable_dispositions"]
                    and int(leg_attempts) < int(head["per_leg_attempt_limit"])
                    and int(head["attempts_reserved"]) < int(head["total_attempt_limit"])
                )
                current_leg = int(attempt["route_leg_ordinal"])
                next_leg = current_leg + 1
                may_fallback = bool(
                    prior_state == "active"
                    and not may_retry
                    and outcome != "succeeded"
                    and disposition in policy["fallback_dispositions"]
                    and next_leg <= len(route_plan["entries"])
                    and _operation_plan["entries"][next_leg - 1]["eligibility"] == "executable"
                    and int(head["attempts_reserved"]) < int(head["total_attempt_limit"])
                    and (
                        disposition != "context_overflow"
                        or int(route_plan["entries"][next_leg - 1]["context_support"]["maximum_tokens"])
                           > int(route_plan["entries"][current_leg - 1]["context_support"]["maximum_tokens"])
                    )
                )
                if may_retry or may_fallback:
                    conn.execute(
                        "UPDATE inference_route_executions SET revision=revision+1 WHERE id=?",
                        (execution_id,),
                    )
                    post_state = "active"
                else:
                    conn.execute(
                        """UPDATE inference_route_executions
                             SET state='terminal',revision=revision+1,terminal_disposition=?,
                                 terminal_outcome=?,result_ref=?,winning_attempt_id=?,terminal_at=?
                           WHERE id=?""",
                        (disposition, outcome, result_ref or None,
                         attempt_key if outcome == "succeeded" else None, now_text, execution_id),
                    )
                    post_state = "terminal"
                effect = self._settlement_effect(conn, execution_id, attempt_key)
                self._insert_command(conn, command, "settle", request_hash, execution_id, effect, now_text)
                self._insert_transition(
                    conn, execution_id, action="settle", command_id=command,
                    prior_revision=prior_revision, post_revision=prior_revision + 1,
                    prior_state=prior_state, post_state=post_state, effect=effect,
                )
                # Reconstruction after every write makes the transaction refuse
                # rather than commit a receipt/head mismatch.
                self._execution(conn, execution_id)
                conn.commit()
                return effect
            except Exception:
                conn.rollback()
                raise

    def reconcile_dispatch_intent(
        self, authority: Principal, *, command_id: str, attempt_id: str
    ) -> dict[str, Any]:
        """Terminalize intent-without-receipt as indeterminate; never advance."""
        self._require_controller(authority)
        command = self._safe_id(command_id, "command_id")
        attempt_key = self._safe_id(attempt_id, "attempt_id")
        request_hash = _sha256({"action": "reconcile", "command_id": command, "attempt_id": attempt_key})
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                attempt = conn.execute("SELECT * FROM inference_route_attempts WHERE id=?", (attempt_key,)).fetchone()
                if attempt is None:
                    raise ValidationError("Route attempt is missing.", code="inference_route_attempt_missing")
                execution_id = str(attempt["execution_id"])
                replay = self._replay_command(conn, command, "reconcile", request_hash, execution_id)
                if replay is not None:
                    if replay != self._settlement_effect(conn, execution_id, attempt_key):
                        raise ConflictError("Stored reconciliation effect is invalid.", code="inference_route_execution_command_integrity_invalid")
                    conn.commit(); return replay
                if str(attempt["state"]) != "dispatch_intent":
                    raise ConflictError("Attempt has no unsettled dispatch intent.", code="inference_route_attempt_not_dispatched")
                if self._kernel_receipt_reader is not None and self._kernel_receipt_reader(str(attempt["child_operation_id"])) is not None:
                    raise ConflictError("A durable child receipt must be settled.", code="inference_route_child_receipt_available")
                evidence = {
                    "schema": "RunnerDispositionEvidence@1", "attempt_id": attempt_key,
                    "child_operation_id": str(attempt["child_operation_id"]),
                    "child_receipt_id": None, "child_receipt_sha256": None,
                    "kernel_outcome": "indeterminate", "send_phase": "dispatch_intent",
                    "typed_signal": "receipt_missing_after_dispatch_intent",
                    "classifier_revision": FALLBACK_CLASSIFIER_REVISION,
                }
                now_text = self._now_text()
                conn.execute(
                    """UPDATE inference_route_attempts SET state='terminal',
                         disposition='dispatch_outcome_unknown',outcome='indeterminate',
                         disposition_evidence_json=?,disposition_evidence_sha256=?,
                         classifier_revision=?,send_phase='dispatch_intent',terminal_at=?
                       WHERE id=? AND state='dispatch_intent'""",
                    (_canonical(evidence), _sha256(evidence), FALLBACK_CLASSIFIER_REVISION, now_text, attempt_key),
                )
                head = conn.execute("SELECT * FROM inference_route_executions WHERE id=?", (execution_id,)).fetchone()
                prior_state, prior_revision = str(head["state"]), int(head["revision"])
                if prior_state not in {"active", "stopping"}:
                    raise ConflictError("Route terminal was already elected.", code="inference_route_execution_terminal")
                conn.execute(
                    """UPDATE inference_route_executions SET state='terminal',revision=revision+1,
                         terminal_disposition='dispatch_outcome_unknown',terminal_outcome='indeterminate',
                         result_ref=NULL,winning_attempt_id=NULL,terminal_at=? WHERE id=?""",
                    (now_text, execution_id),
                )
                effect = self._settlement_effect(conn, execution_id, attempt_key)
                self._insert_command(conn, command, "reconcile", request_hash, execution_id, effect, now_text)
                self._insert_transition(conn, execution_id, action="reconcile", command_id=command,
                    prior_revision=prior_revision, post_revision=prior_revision + 1,
                    prior_state=prior_state, post_state="terminal", effect=effect)
                self._execution(conn, execution_id)
                conn.commit(); return effect
            except Exception:
                conn.rollback(); raise

    @staticmethod
    def _classify_receipt(outcome: str, typed_signal: str, attested_send_phase: str) -> tuple[str, str]:
        if outcome == "succeeded":
            if typed_signal != "none":
                raise ConflictError("Success cannot carry a failure signal.", code="inference_route_disposition_evidence_invalid")
            return "owner_terminal", "provider_returned"
        if typed_signal in {"compatibility_no_generation", "known_no_generation_transient"} and outcome == "failed":
            return "known_no_generation_transient", "provider_no_generation"
        if typed_signal == "provider_permanent_no_generation" and outcome == "failed":
            return "provider_permanent", "provider_no_generation"
        if typed_signal == "permission_denied":
            return "permission_denied", "provider_no_generation"
        if typed_signal == "local_capacity_unavailable":
            return "local_capacity_unavailable", "pre_send"
        if typed_signal == "invalid_typed_output" and outcome == "failed":
            return "invalid_typed_output", "provider_returned"
        if typed_signal == "effect_indeterminate" and outcome == "failed":
            return "effect_indeterminate", "provider_returned"
        if typed_signal in {"dispatch_outcome_unknown", "physical_outcome_unknown"}:
            return "dispatch_outcome_unknown", "dispatch_intent"
        if typed_signal == "unclassified_pre_send":
            return "policy_refused", "pre_send"
        if typed_signal == "kernel_refused":
            return (
                ("dispatch_outcome_unknown", "dispatch_intent")
                if attested_send_phase == "dispatch_intent"
                else ("policy_refused", "pre_send")
            )
        if typed_signal == "none" and outcome == "failed":
            # A receipt proves kernel closure, not whether a provider generated.
            # Without Runner's typed evidence a post-intent failure is unknown.
            return "dispatch_outcome_unknown", "dispatch_intent"
        if typed_signal == "none" and outcome == "cancelled":
            return (
                "owner_cancelled",
                "pre_send" if attested_send_phase == "pre_send" else "dispatch_intent",
            )
        return {
            "refused": ("policy_refused", "pre_send"),
            "cancelled": ("owner_cancelled", "dispatch_intent"),
            "indeterminate": ("physical_outcome_unknown", "dispatch_intent"),
            "failed": ("provider_permanent", "provider_returned"),
        }.get(outcome, ("effect_indeterminate", "dispatch_intent"))

    def _settlement_effect(self, conn: Any, execution_id: str, attempt_id: str) -> dict[str, Any]:
        execution = conn.execute("SELECT * FROM inference_route_executions WHERE id=?", (execution_id,)).fetchone()
        attempt = conn.execute("SELECT * FROM inference_route_attempts WHERE id=?", (attempt_id,)).fetchone()
        evidence = json.loads(str(attempt["disposition_evidence_json"] or "{}"))
        receipt = self._route_execution_receipt(conn, execution_id)
        return {
            "schema": "InferenceRouteSettlementEffect@1",
            "execution_id": execution_id,
            "attempt_id": attempt_id,
            "disposition": str(attempt["disposition"] or ""),
            "outcome": str(attempt["outcome"] or ""),
            "evidence_sha256": _sha256(evidence),
            "terminal_state": str(execution["state"]),
            "route_execution_receipt": receipt,
        }

    def _route_execution_receipt(self, conn: Any, execution_id: str) -> dict[str, Any]:
        head = conn.execute("SELECT * FROM inference_route_executions WHERE id=?", (execution_id,)).fetchone()
        _operation, route = self._plans.reconstruct_frozen_pair_in_transaction(
            ROUTE_PLANNING_AUTHORITY, conn, str(head["operation_plan_id"])
        )
        attempts = conn.execute(
            "SELECT * FROM inference_route_attempts WHERE execution_id=? ORDER BY physical_attempt_ordinal", (execution_id,)
        ).fetchall()
        skips = conn.execute(
            "SELECT * FROM inference_route_execution_skips WHERE execution_id=? ORDER BY route_leg_ordinal",
            (execution_id,),
        ).fetchall()
        attempts_by_leg: dict[int, list[Any]] = {}
        for attempt in attempts:
            attempts_by_leg.setdefault(int(attempt["route_leg_ordinal"]), []).append(attempt)
        skips_by_leg = {int(skip["route_leg_ordinal"]): skip for skip in skips}
        considerations = []
        for leg in route["entries"]:
            ordinal = int(leg["ordinal"])
            skip = skips_by_leg.get(ordinal)
            considered = attempts_by_leg.get(ordinal, [])
            physical = [item for item in considered if item["send_phase"] in {"provider_no_generation", "provider_returned"}]
            possibly_started = any(item["dispatch_intent_at"] is not None for item in considered) and not physical
            considerations.append({
                "route_leg_ordinal": ordinal,
                "profile_id": str(leg["profile_id"]),
                "profile_revision": int(leg["profile_revision"]),
                "deployment_revision_id": str(leg["deployment_revision_id"]),
                "boundary": str(leg["boundary"]),
                "status": "attempted" if physical else ("possibly_started" if possibly_started else ("not_started" if considered else ("skipped" if skip is not None else "not_reached"))),
                "disposition": None if skip is None else str(skip["disposition"]),
                "reason_code": None if skip is None else str(skip["reason_code"]),
                "physical_attempts": len(physical),
            })
        winning = next((item for item in attempts if str(item["id"]) == str(head["winning_attempt_id"] or "")), None)
        physical_attempts = [item for item in attempts if item["send_phase"] in {"provider_no_generation", "provider_returned"}]
        attempted_ordinals = {int(item["route_leg_ordinal"]) for item in physical_attempts}
        all_failed = bool(
            physical_attempts
            and attempted_ordinals == {int(item["ordinal"]) for item in route["entries"]}
            and all(str(item["outcome"] or "") == "failed" for item in physical_attempts)
            and not skips
        )
        return {
            "schema": ROUTE_EXECUTION_RECEIPT_SCHEMA,
            "execution_id": execution_id,
            "route_plan_id": str(head["route_plan_id"]),
            "route_plan_sha256": str(head["route_plan_sha256"]),
            "operation_plan_id": str(head["operation_plan_id"]),
            "operation_plan_sha256": str(head["operation_plan_sha256"]),
            "state": str(head["state"]),
            "outcome": head["terminal_outcome"],
            "disposition": head["terminal_disposition"],
            "winning_attempt_id": head["winning_attempt_id"],
            "result_ref": head["result_ref"],
            "winning_deployment_revision_id": None if winning is None else str(winning["deployment_revision_id"]),
            "winning_boundary": None if winning is None else str(winning["boundary"]),
            "considerations": considerations,
            "all_models_physically_failed": all_failed,
            "physically_failed_attempt_count": len(physical_attempts) if all_failed else 0,
            "attempts": [{
                "attempt_id": str(item["id"]),
                "route_leg_ordinal": int(item["route_leg_ordinal"]),
                "leg_attempt_ordinal": int(item["leg_attempt_ordinal"]),
                "profile_id": str(route["entries"][int(item["route_leg_ordinal"]) - 1]["profile_id"]),
                "profile_revision": int(route["entries"][int(item["route_leg_ordinal"]) - 1]["profile_revision"]),
                "physical_attempt_ordinal": int(item["physical_attempt_ordinal"]),
                "purpose": str(item["purpose"]),
                "deployment_revision_id": str(item["deployment_revision_id"]),
                "boundary": str(item["boundary"]),
                "child_operation_id": str(item["child_operation_id"] or ""),
                "disposition": item["disposition"], "outcome": item["outcome"],
                "send_phase": item["send_phase"],
                "child_receipt_sha256": item["child_receipt_sha256"],
                "disposition_evidence_sha256": item["disposition_evidence_sha256"],
            } for item in attempts],
        }

    def request_stop(self, authority: Principal, *, command_id: str, execution_id: str) -> dict[str, Any]:
        self._require_controller(authority)
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                result = self.request_stop_in_transaction(
                    authority,
                    conn,
                    command_id=command_id,
                    execution_id=execution_id,
                )
                conn.commit()
                return result
            except Exception:
                conn.rollback(); raise

    def request_stop_in_transaction(
        self,
        authority: Principal,
        conn: Any,
        *,
        command_id: str,
        execution_id: str,
    ) -> dict[str, Any]:
        """Fence one execution inside an adopter-owned durable handoff."""
        self._require_controller(authority)
        command = self._safe_id(command_id, "command_id")
        execution = self._safe_id(execution_id, "execution_id")
        request_hash = _sha256(
            {"action": "stop", "command_id": command, "execution_id": execution}
        )
        replay = self._replay_command(conn, command, "stop", request_hash, execution)
        if replay is not None:
            current = self._execution(conn, execution)
            self._verify_stop_effect(conn, replay, execution, command, current)
            return {
                "schema": "InferenceRouteStopResult@1",
                "effect": replay,
                "execution": current,
            }
        current = self._execution(conn, execution)
        row = conn.execute(
            "SELECT * FROM inference_route_executions WHERE id=?", (execution,)
        ).fetchone()
        now_text = self._now_text()
        prior_state = str(row["state"])
        if prior_state == "active":
            dispatched = conn.execute(
                "SELECT 1 FROM inference_route_attempts WHERE execution_id=? AND state='dispatch_intent'",
                (execution,),
            ).fetchone() is not None
            if dispatched:
                conn.execute(
                    "UPDATE inference_route_executions SET stop_requested=1,stop_command_id=?,state='stopping',revision=revision+1 WHERE id=? AND state='active'",
                    (command, execution),
                )
                elected = "stopping"
            else:
                conn.execute(
                    """UPDATE inference_route_executions
                       SET stop_requested=1,stop_command_id=?,state='stopped',revision=revision+1,
                           terminal_disposition='owner_cancelled',terminal_outcome='cancelled',terminal_at=?
                       WHERE id=? AND state='active'""",
                    (command, now_text, execution),
                )
                elected = "stopped"
        else:
            elected = prior_state
        effect = {
            "schema": "InferenceRouteStopEffect@1",
            "execution_id": execution,
            "observed_state": prior_state,
            "observed_revision": int(row["revision"]),
            "elected_state": elected,
        }
        self._insert_command(
            conn, command, "stop", request_hash, execution, effect, now_text
        )
        if prior_state == "active":
            self._insert_transition(
                conn,
                execution,
                action="stop",
                command_id=command,
                prior_revision=int(row["revision"]),
                post_revision=int(row["revision"]) + 1,
                prior_state="active",
                post_state=elected,
                effect=effect,
            )
        current = self._execution(conn, execution)
        return {
            "schema": "InferenceRouteStopResult@1",
            "effect": effect,
            "execution": current,
        }

    @staticmethod
    def _verify_stop_effect(conn: Any, effect: Any, execution_id: str, command_id: str, current: dict[str, Any]) -> None:
        if (
            not isinstance(effect, dict)
            or set(effect) != {"schema", "execution_id", "observed_state", "observed_revision", "elected_state"}
            or effect.get("schema") != "InferenceRouteStopEffect@1"
            or effect.get("execution_id") != execution_id
            or effect.get("observed_state") not in {"active", "stopping", "stopped", "terminal"}
            or type(effect.get("observed_revision")) is not int
            or effect.get("observed_revision") < 1
            or effect.get("elected_state") not in {"stopping", "stopped", "terminal"}
            or (
                effect.get("observed_state") != "active"
                and effect.get("elected_state") != effect.get("observed_state")
            )
            or (
                effect.get("observed_state") == "active"
                and effect.get("elected_state") not in {"stopping", "stopped"}
            )
        ):
            raise ConflictError("Stored Stop effect is invalid.", code="inference_route_execution_command_integrity_invalid")
        observed = conn.execute(
            """SELECT 1 FROM inference_route_execution_transitions
                 WHERE execution_id=? AND post_revision=? AND post_state=?""",
            (execution_id, effect["observed_revision"], effect["observed_state"]),
        ).fetchone()
        if effect["observed_state"] == "active":
            head = conn.execute(
                "SELECT stop_command_id FROM inference_route_executions WHERE id=?",
                (execution_id,),
            ).fetchone()
            transition = conn.execute(
                "SELECT 1 FROM inference_route_execution_transitions WHERE execution_id=? AND action='stop' AND command_id=?",
                (execution_id, command_id),
            ).fetchone()
            if head is None or str(head["stop_command_id"] or "") != command_id or transition is None:
                raise ConflictError("Stored Stop provenance is invalid.", code="inference_route_execution_command_integrity_invalid")
        elif observed is None and not (
            effect["observed_revision"] == current["revision"]
            and effect["observed_state"] == current["state"]
        ):
            raise ConflictError("Stored Stop observation is invalid.", code="inference_route_execution_command_integrity_invalid")

    def _closed_reservation(self, value: Any) -> dict[str, Any]:
        fields = {
            "schema", "attempt_id", "execution_id", "route_plan_id",
            "operation_plan_id", "route_leg_ordinal", "physical_attempt_ordinal",
            "leg_attempt_ordinal", "purpose", "deployment_revision_id",
            "child_invocation_id", "nonce",
        }
        if not isinstance(value, dict) or set(value) != fields or value.get("schema") != "InferenceRouteAttemptReservation@1":
            raise ValidationError("Reservation has an invalid shape.", code="inference_route_reservation_invalid")
        ticket = dict(value)
        for name in ("attempt_id", "execution_id", "route_plan_id", "operation_plan_id", "deployment_revision_id", "child_invocation_id"):
            ticket[name] = self._safe_id(ticket[name], name)
        if ticket["purpose"] not in {"primary", "retry", "fallback", "compatibility"}:
            raise ValidationError("Reservation purpose is invalid.", code="inference_route_reservation_invalid")
        for name in ("route_leg_ordinal", "physical_attempt_ordinal", "leg_attempt_ordinal"):
            if type(ticket[name]) is not int or ticket[name] < 1:
                raise ValidationError("Reservation ordinal is invalid.", code="inference_route_reservation_invalid")
        if not isinstance(ticket["nonce"], str) or len(ticket["nonce"]) < 32:
            raise ValidationError("Reservation nonce is invalid.", code="inference_route_reservation_invalid")
        return ticket

    def _reservation_rows(self, conn: Any, ticket: dict[str, Any]) -> tuple[Any, Any, dict[str, Any], dict[str, Any]]:
        attempt = conn.execute("SELECT * FROM inference_route_attempts WHERE id=?", (ticket["attempt_id"],)).fetchone()
        execution = conn.execute("SELECT * FROM inference_route_executions WHERE id=?", (ticket["execution_id"],)).fetchone()
        if attempt is None or execution is None:
            raise ValidationError("Reservation is unknown.", code="inference_route_reservation_invalid")
        projection = self._execution(conn, ticket["execution_id"])
        operation, route = self._plans.reconstruct_frozen_pair_in_transaction(
            ROUTE_PLANNING_AUTHORITY, conn, projection["operation_plan_id"]
        )
        physical = int(attempt["physical_attempt_ordinal"])
        attempt_seed = f"{ticket['execution_id']}:{physical}"
        expected_attempt = f"ira_{hashlib.sha256(attempt_seed.encode()).hexdigest()[:32]}"
        expected_invocation = f"invoke_{hashlib.sha256(expected_attempt.encode()).hexdigest()[:32]}"
        leg = route["entries"][int(attempt["route_leg_ordinal"]) - 1]
        expected = {
            "attempt_id": str(attempt["id"]),
            "execution_id": str(attempt["execution_id"]),
            "route_plan_id": route["id"],
            "operation_plan_id": operation["id"],
            "route_leg_ordinal": int(attempt["route_leg_ordinal"]),
            "physical_attempt_ordinal": physical,
            "leg_attempt_ordinal": int(attempt["leg_attempt_ordinal"]),
            "purpose": str(attempt["purpose"]),
            "deployment_revision_id": str(attempt["deployment_revision_id"]),
            "child_invocation_id": str(attempt["child_invocation_id"]),
        }
        supplied = {key: ticket[key] for key in expected}
        if (
            supplied != expected
            or ticket["attempt_id"] != expected_attempt
            or ticket["child_invocation_id"] != expected_invocation
            or ticket["deployment_revision_id"] != leg["deployment_revision_id"]
            or _sha256({"nonce": ticket["nonce"]}) != str(attempt["admission_nonce_sha256"])
        ):
            raise ConflictError("Reservation does not match its frozen attempt.", code="inference_route_reservation_integrity_invalid")
        return attempt, execution, operation, route

    def _verify_reserve_effect(self, conn: Any, execution_id: str, effect: Any) -> None:
        if not isinstance(effect, dict) or set(effect) != {"schema", "execution_id", "terminal", "reservation"} or effect.get("schema") != "RouteAttemptReservationEffect@1" or effect.get("execution_id") != execution_id:
            raise ConflictError("Stored reservation effect is invalid.", code="inference_route_execution_command_integrity_invalid")
        self._execution(conn, execution_id)
        if effect["reservation"] is not None:
            ticket = self._closed_reservation(effect["reservation"])
            if ticket["execution_id"] != execution_id:
                raise ConflictError("Stored reservation effect crosses executions.", code="inference_route_execution_command_integrity_invalid")
            self._reservation_rows(conn, ticket)
            if effect["terminal"] is not None:
                raise ConflictError("Stored reservation effect contradicts itself.", code="inference_route_execution_command_integrity_invalid")
            return
        row = conn.execute("SELECT state,terminal_disposition FROM inference_route_executions WHERE id=?", (execution_id,)).fetchone()
        if str(row["state"]) != "terminal" or effect["terminal"] != row["terminal_disposition"]:
            raise ConflictError("Stored terminal reservation effect is invalid.", code="inference_route_execution_command_integrity_invalid")

    def _verify_claim_effect(self, conn: Any, ticket: dict[str, Any], effect: Any) -> None:
        attempt, _execution, _operation, _route = self._reservation_rows(conn, ticket)
        expected = {
            "schema": "InferenceRouteAttemptClaim@1",
            "attempt_id": ticket["attempt_id"],
            "child_invocation_id": ticket["child_invocation_id"],
            "deployment_revision_id": ticket["deployment_revision_id"],
            "physical_attempt_ordinal": ticket["physical_attempt_ordinal"],
        }
        if effect != expected or str(attempt["state"]) not in {"admitted", "dispatch_intent", "terminal"}:
            raise ConflictError("Stored claim effect is invalid.", code="inference_route_execution_command_integrity_invalid")

    @staticmethod
    def _bind_effect(attempt: Any) -> dict[str, Any]:
        return {
            "schema": "InferenceRouteChildBinding@1",
            "attempt_id": str(attempt["id"]),
            "child_invocation_id": str(attempt["child_invocation_id"]),
            "child_operation_id": str(attempt["child_operation_id"] or ""),
        }

    @staticmethod
    def _dispatch_effect(attempt: Any) -> dict[str, Any]:
        return {
            "schema": "InferenceRouteDispatchIntent@1",
            "attempt_id": str(attempt["id"]),
            "child_operation_id": str(attempt["child_operation_id"] or ""),
            "physical_attempt_ordinal": int(attempt["physical_attempt_ordinal"]),
        }

    def _fence_execution(self, execution: Any, route: dict[str, Any]) -> None:
        now = self._clock()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        deadline = datetime.fromisoformat(str(route["deadline_at"]).replace("Z", "+00:00"))
        if bool(execution["stop_requested"]) or str(execution["state"]) != "active":
            raise ConflictError("Route execution is terminal.", code="inference_route_execution_terminal")
        if now >= deadline:
            raise ConflictError("Route execution deadline is exhausted.", code="inference_route_deadline_exhausted")

    def _replay_command(self, conn: Any, command: str, action: str, request_hash: str, execution: str) -> dict[str, Any] | None:
        row = conn.execute("SELECT * FROM inference_route_execution_commands WHERE command_id=?", (command,)).fetchone()
        if row is None:
            return None
        if str(row["action"]) != action or str(row["request_sha256"]) != request_hash:
            raise ConflictError("Route execution command changed.", code="inference_route_execution_command_conflict")
        try:
            effect = json.loads(str(row["effect_json"]))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ConflictError("Stored route execution effect is invalid.", code="inference_route_execution_command_integrity_invalid") from exc
        if str(row["execution_id"]) != execution or str(row["effect_sha256"]) != _sha256(effect):
            raise ConflictError("Stored route execution effect is invalid.", code="inference_route_execution_command_integrity_invalid")
        return effect

    def _now_text(self) -> str:
        now = self._clock()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return _timestamp(now)

    @staticmethod
    def _insert_command(conn: Any, command: str, action: str, request_hash: str, execution: str, effect: dict[str, Any], created_at: str) -> None:
        conn.execute(
            "INSERT INTO inference_route_execution_commands VALUES (?,?,?,?,?,?,?)",
            (command, action, request_hash, execution, _canonical(effect), _sha256(effect), created_at),
        )

    @staticmethod
    def _insert_transition(
        conn: Any,
        execution_id: str,
        *,
        action: str,
        command_id: str,
        prior_revision: int,
        post_revision: int,
        prior_state: str,
        post_state: str,
        effect: dict[str, Any],
    ) -> None:
        previous = conn.execute(
            """SELECT sha256 FROM inference_route_execution_transitions
                 WHERE execution_id=? ORDER BY ordinal DESC LIMIT 1""",
            (execution_id,),
        ).fetchone()
        prior_sha = str(previous["sha256"]) if previous is not None else "sha256:" + "0" * 64
        ordinal = conn.execute(
            "SELECT COUNT(*) FROM inference_route_execution_transitions WHERE execution_id=?",
            (execution_id,),
        ).fetchone()[0] + 1
        material = {
            "execution_id": execution_id,
            "ordinal": int(ordinal),
            "action": action,
            "command_id": command_id,
            "prior_revision": prior_revision,
            "post_revision": post_revision,
            "prior_state": prior_state,
            "post_state": post_state,
            "effect_sha256": _sha256(effect),
            "previous_sha256": prior_sha,
        }
        digest = _sha256(material)
        conn.execute(
            "INSERT INTO inference_route_execution_transitions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                f"irt_{digest.removeprefix('sha256:')[:32]}", execution_id, ordinal,
                action, command_id, prior_revision, post_revision, prior_state,
                post_state, material["effect_sha256"], prior_sha, digest,
            ),
        )

    def _execution(self, conn: Any | None, execution_id: str) -> dict[str, Any]:
        if conn is None:
            with self._db._connection() as owned:
                return self._execution(owned, execution_id)
        row = conn.execute(
            "SELECT * FROM inference_route_executions WHERE id=?", (execution_id,)
        ).fetchone()
        if row is None:
            raise ValidationError(
                "Route execution is missing.", code="inference_route_execution_missing"
            )
        operation, route = self._plans.reconstruct_frozen_pair_in_transaction(
            ROUTE_PLANNING_AUTHORITY, conn, str(row["operation_plan_id"])
        )
        budgets = self._plans.reconstruct_attempt_budgets_in_transaction(
            ROUTE_PLANNING_AUTHORITY, conn, operation=operation, route=route
        )
        aggregate = conn.execute(
            """SELECT COUNT(*) AS attempts,COALESCE(SUM(reserved_token_budget),0) AS tokens,
                      COALESCE(SUM(reserved_cost_budget),0) AS cost,
                      COALESCE(SUM(reserved_tool_call_budget),0) AS tools
                 FROM inference_route_attempts WHERE execution_id=?""",
            (execution_id,),
        ).fetchone()
        attempt_rows = conn.execute(
            "SELECT * FROM inference_route_attempts WHERE execution_id=? ORDER BY physical_attempt_ordinal",
            (execution_id,),
        ).fetchall()
        skip_rows = conn.execute(
            "SELECT * FROM inference_route_execution_skips WHERE execution_id=? ORDER BY route_leg_ordinal",
            (execution_id,),
        ).fetchall()
        skips_valid = all(
            self._skip_evidence_valid(
                conn, item, execution_id=execution_id, operation=operation, route=route,
            )
            for item in skip_rows
        )
        skipped_ordinals = {int(item["route_leg_ordinal"]): str(item["disposition"]) for item in skip_rows}
        per_leg = conn.execute(
            """SELECT COALESCE(MAX(n),0) FROM
                 (SELECT COUNT(*) AS n FROM inference_route_attempts
                   WHERE execution_id=? GROUP BY route_leg_ordinal)""",
            (execution_id,),
        ).fetchone()[0]
        attempts_valid = True
        leg_counts: dict[int, int] = {}
        for expected_physical, item in enumerate(attempt_rows, 1):
            leg_ordinal = int(item["route_leg_ordinal"])
            leg_counts[leg_ordinal] = leg_counts.get(leg_ordinal, 0) + 1
            leg = route["entries"][leg_ordinal - 1] if 1 <= leg_ordinal <= len(route["entries"]) else None
            budget = budgets["entries"][leg_ordinal - 1] if leg is not None else None
            expected_attempt = f"ira_{hashlib.sha256(f'{execution_id}:{expected_physical}'.encode()).hexdigest()[:32]}"
            expected_invocation = f"invoke_{hashlib.sha256(expected_attempt.encode()).hexdigest()[:32]}"
            command_ticket_valid = self._attempt_reservation_command_valid(
                conn,
                item,
                execution_id=execution_id,
                route_plan_id=route["id"],
                operation_plan_id=operation["id"],
            )
            transition_valid_for_attempt = True
            if expected_physical > 1:
                previous = attempt_rows[expected_physical - 2]
                previous_leg = int(previous["route_leg_ordinal"])
                previous_disposition = str(previous["disposition"] or "")
                if leg_ordinal == previous_leg:
                    try:
                        previous_evidence = json.loads(str(previous["disposition_evidence_json"] or "{}"))
                    except (TypeError, ValueError, json.JSONDecodeError):
                        previous_evidence = {}
                    expected_purpose = "compatibility" if previous_evidence.get("typed_signal") == "compatibility_no_generation" else "retry"
                    transition_valid_for_attempt = bool(
                        str(previous["state"]) == "terminal"
                        and previous_disposition in route["retry_policy"]["retryable_dispositions"]
                        and str(item["purpose"]) == expected_purpose
                        and int(item["leg_attempt_ordinal"]) == int(previous["leg_attempt_ordinal"]) + 1
                    )
                elif leg_ordinal == previous_leg + 1:
                    transition_valid_for_attempt = bool(
                        str(previous["state"]) == "terminal"
                        and previous_disposition in route["retry_policy"]["fallback_dispositions"]
                        and (
                            previous_disposition not in route["retry_policy"]["retryable_dispositions"]
                            or int(previous["leg_attempt_ordinal"]) >= int(row["per_leg_attempt_limit"])
                        )
                        and str(item["purpose"]) == "fallback"
                        and int(item["leg_attempt_ordinal"]) == 1
                    )
                else:
                    transition_valid_for_attempt = False
            terminal_valid = self._terminal_attempt_valid(item)
            lifecycle_valid = self._attempt_lifecycle_valid(conn, item)
            attempts_valid = attempts_valid and bool(
                leg is not None
                and budget is not None
                and int(item["physical_attempt_ordinal"]) == expected_physical
                and int(item["leg_attempt_ordinal"]) == leg_counts[leg_ordinal]
                and str(item["id"]) == expected_attempt
                and str(item["child_invocation_id"]) == expected_invocation
                and str(item["deployment_revision_id"]) == leg["deployment_revision_id"]
                and str(item["boundary"]) == leg["boundary"]
                and int(item["reserved_token_budget"]) == int(budget["total_tokens"])
                and int(item["reserved_cost_budget"]) == int(budget["reserved_cost_units"])
                and int(item["reserved_tool_call_budget"]) == int(budget["reserved_tool_calls"])
                and (
                    expected_physical != 1
                    or (leg_ordinal == 1 and str(item["purpose"]) == "primary")
                    or (
                        leg_ordinal > 1 and str(item["purpose"]) == "fallback"
                        and all(skipped_ordinals.get(value) == "context_overflow" for value in range(1, leg_ordinal))
                    )
                )
                and transition_valid_for_attempt
                and (str(item["state"]) != "reserved" or item["child_operation_id"] is None)
                and (str(item["state"]) != "dispatch_intent" or item["child_operation_id"] is not None)
                and terminal_valid
                and lifecycle_valid
                and command_ticket_valid
            )
        state = str(row["state"])
        dispatched_count = sum(str(item["state"]) == "dispatch_intent" for item in attempt_rows)
        winning = None
        if row["winning_attempt_id"] is not None:
            winning = next(
                (item for item in attempt_rows if str(item["id"]) == str(row["winning_attempt_id"])),
                None,
            )
        state_valid = bool(
            (
                state == "active"
                and not bool(row["stop_requested"])
                and row["terminal_disposition"] is None
                and row["terminal_outcome"] is None
                and row["winning_attempt_id"] is None
                and row["terminal_at"] is None
            )
            or (
                state == "stopping"
                and bool(row["stop_requested"])
                and dispatched_count >= 1
                and row["terminal_disposition"] is None
                and row["terminal_outcome"] is None
                and row["winning_attempt_id"] is None
                and row["terminal_at"] is None
            )
            or (
                state == "stopped"
                and bool(row["stop_requested"])
                and dispatched_count == 0
                and row["terminal_disposition"] == "owner_cancelled"
                and row["terminal_outcome"] == "cancelled"
                and row["winning_attempt_id"] is None
                and row["terminal_at"] is not None
            )
            or (
                state == "terminal"
                and row["terminal_outcome"] is not None
                and row["terminal_at"] is not None
                and (
                    (
                        row["terminal_outcome"] == "succeeded"
                        and winning is not None
                        and str(row["result_ref"] or "")
                    )
                    or (
                        row["terminal_outcome"] != "succeeded"
                        and row["winning_attempt_id"] is None
                    )
                )
            )
        )
        minimum_revision = 1 + int(aggregate["attempts"]) + int(state != "active")
        transitions = conn.execute(
            "SELECT * FROM inference_route_execution_transitions WHERE execution_id=? ORDER BY ordinal",
            (execution_id,),
        ).fetchall()
        transition_valid = bool(transitions)
        previous_sha = "sha256:" + "0" * 64
        prior_revision = 0
        prior_state = "none"
        for ordinal, transition in enumerate(transitions, 1):
            command = conn.execute(
                "SELECT * FROM inference_route_execution_commands WHERE command_id=?",
                (transition["command_id"],),
            ).fetchone()
            material = {
                "execution_id": execution_id,
                "ordinal": ordinal,
                "action": str(transition["action"]),
                "command_id": str(transition["command_id"]),
                "prior_revision": int(transition["prior_revision"]),
                "post_revision": int(transition["post_revision"]),
                "prior_state": str(transition["prior_state"]),
                "post_state": str(transition["post_state"]),
                "effect_sha256": str(transition["effect_sha256"]),
                "previous_sha256": str(transition["previous_sha256"]),
            }
            transition_valid = transition_valid and bool(
                int(transition["ordinal"]) == ordinal
                and int(transition["prior_revision"]) == prior_revision
                and int(transition["post_revision"]) == prior_revision + 1
                and str(transition["prior_state"]) == prior_state
                and str(transition["previous_sha256"]) == previous_sha
                and str(transition["sha256"]) == _sha256(material)
                and command is not None
                and str(command["action"]) == str(transition["action"])
                and str(command["execution_id"]) == execution_id
                and str(command["effect_sha256"]) == str(transition["effect_sha256"])
                and (ordinal != 1 or (transition["action"] == "start" and transition["prior_state"] == "none" and transition["post_state"] == "active"))
            )
            previous_sha = str(transition["sha256"])
            prior_revision = int(transition["post_revision"])
            prior_state = str(transition["post_state"])
        transition_valid = transition_valid and bool(
            prior_revision == int(row["revision"])
            and prior_state == state
            and len(transitions) == int(row["revision"])
        )
        if row["stop_command_id"] is not None:
            transition_valid = transition_valid and any(
                str(item["action"]) == "stop"
                and str(item["command_id"]) == str(row["stop_command_id"])
                for item in transitions
            )
        if (
            operation["route_plan_id"] != route["id"]
            or str(row["route_plan_sha256"]) != route["sha256"]
            or str(row["operation_plan_sha256"]) != operation["sha256"]
            or str(row["budget_evidence_provider_id"]) != budgets["provider_id"]
            or int(row["budget_evidence_provider_revision"]) != budgets["provider_revision"]
            or str(row["budget_evidence_sha256"]) != budgets["sha256"]
            or int(row["total_attempt_limit"])
            != int(route["retry_policy"]["total_physical_attempts"])
            or int(row["per_leg_attempt_limit"])
            != int(route["retry_policy"]["per_entry_attempts"])
            or row["token_budget"] != route["retry_policy"]["token_budget"]
            or row["cost_budget"] != route["retry_policy"]["cost_budget"]
            or row["tool_call_budget"] != route["retry_policy"]["tool_call_budget"]
            or int(row["attempts_reserved"]) > int(row["total_attempt_limit"])
            or int(row["attempts_reserved"]) != int(aggregate["attempts"])
            or int(row["tokens_reserved"]) != int(aggregate["tokens"])
            or int(row["cost_reserved"]) != int(aggregate["cost"])
            or int(row["tool_calls_reserved"]) != int(aggregate["tools"])
            or int(per_leg) > int(row["per_leg_attempt_limit"])
            or not attempts_valid
            or not skips_valid
            or not state_valid
            or int(row["revision"]) < minimum_revision
            or not transition_valid
            or any(
                str(item["budget_evidence_provider_id"]) != budgets["provider_id"]
                or int(item["budget_evidence_provider_revision"]) != budgets["provider_revision"]
                or str(item["budget_evidence_sha256"]) != budgets["sha256"]
                for item in attempt_rows
            )
            or (
                row["token_budget"] is not None
                and int(row["tokens_reserved"]) > int(row["token_budget"])
            )
            or (
                row["cost_budget"] is not None
                and int(row["cost_reserved"]) > int(row["cost_budget"])
            )
            or (
                row["tool_call_budget"] is not None
                and int(row["tool_calls_reserved"]) > int(row["tool_call_budget"])
            )
        ):
            raise ConflictError(
                "Stored route execution binding is invalid.",
                code="inference_route_execution_integrity_invalid",
            )
        return {
            "schema": "InferenceRouteExecution@1",
            "id": str(row["id"]),
            "route_plan_id": str(row["route_plan_id"]),
            "route_plan_sha256": str(row["route_plan_sha256"]),
            "operation_plan_id": str(row["operation_plan_id"]),
            "operation_plan_sha256": str(row["operation_plan_sha256"]),
            "state": str(row["state"]),
            "revision": int(row["revision"]),
            "stop_requested": bool(row["stop_requested"]),
            "terminal_disposition": row["terminal_disposition"],
            "terminal_outcome": row["terminal_outcome"],
            "winning_attempt_id": row["winning_attempt_id"],
            "result_ref": row["result_ref"],
        }

    def _skip_evidence_valid(
        self,
        conn: Any,
        skip: Any,
        *,
        execution_id: str,
        operation: dict[str, Any],
        route: dict[str, Any],
    ) -> bool:
        """Reconstruct a zero-physical leg consideration from frozen evidence.

        The skip row is only a normalized projection.  Its authority is the
        exact reserve command and transition which either terminalized that
        frozen leg or minted the immediately following fallback reservation.
        """
        try:
            ordinal = int(skip["route_leg_ordinal"])
            planned = operation["entries"][ordinal - 1]
            route_leg = route["entries"][ordinal - 1]
        except (IndexError, KeyError, TypeError, ValueError):
            return False
        eligibility = str(planned.get("eligibility") or "")
        expected_disposition = {
            "known_context_overflow": "context_overflow",
            "known_preflight_unavailable": "preflight_unavailable",
        }.get(eligibility)
        if not expected_disposition:
            return False
        if not (
            str(skip["id"]) == f"{execution_id}:{ordinal}"
            and str(skip["execution_id"]) == execution_id
            and str(skip["disposition"]) == expected_disposition
            and str(skip["reason_code"]) == str(planned.get("reason_code") or "")
        ):
            return False
        commands = conn.execute(
            """SELECT * FROM inference_route_execution_commands
                 WHERE execution_id=? AND action='reserve' ORDER BY created_at,command_id""",
            (execution_id,),
        ).fetchall()
        matches = 0
        for command in commands:
            command_id = str(command["command_id"])
            transition = conn.execute(
                """SELECT * FROM inference_route_execution_transitions
                     WHERE execution_id=? AND command_id=? AND action='reserve'""",
                (execution_id, command_id),
            ).fetchone()
            try:
                effect = json.loads(str(command["effect_json"]))
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            if not (
                str(command["request_sha256"]) == _sha256({
                    "action": "reserve", "command_id": command_id,
                    "execution_id": execution_id,
                })
                and str(command["effect_sha256"]) == _sha256(effect)
                and isinstance(effect, dict)
                and set(effect) == {"schema", "execution_id", "terminal", "reservation"}
                and effect.get("schema") == "RouteAttemptReservationEffect@1"
                and effect.get("execution_id") == execution_id
                and transition is not None
                and str(transition["effect_sha256"]) == str(command["effect_sha256"])
            ):
                continue
            terminal_match = bool(
                effect.get("terminal") == expected_disposition
                and effect.get("reservation") is None
            )
            advancing_match = False
            reservation = effect.get("reservation")
            if expected_disposition == "context_overflow" and isinstance(reservation, dict):
                next_ordinal = ordinal + 1
                next_attempt = conn.execute(
                    """SELECT * FROM inference_route_attempts
                         WHERE execution_id=? AND route_leg_ordinal=?
                           AND reservation_command_id=?""",
                    (execution_id, next_ordinal, command_id),
                ).fetchone()
                advancing_match = bool(
                    next_ordinal <= len(route["entries"])
                    and next_ordinal <= len(operation["entries"])
                    and operation["entries"][next_ordinal - 1]["eligibility"] == "executable"
                    and "context_overflow" in route["retry_policy"]["fallback_dispositions"]
                    and int(route["entries"][next_ordinal - 1]["context_support"]["maximum_tokens"])
                        > int(route_leg["context_support"]["maximum_tokens"])
                    and next_attempt is not None
                    and reservation.get("attempt_id") == str(next_attempt["id"])
                    and reservation.get("route_leg_ordinal") == next_ordinal
                    and reservation.get("purpose") == "fallback"
                )
            if terminal_match or advancing_match:
                matches += 1
        return matches == 1

    def _attempt_reservation_command_valid(
        self,
        conn: Any,
        attempt: Any,
        *,
        execution_id: str,
        route_plan_id: str,
        operation_plan_id: str,
    ) -> bool:
        command_id = str(attempt["reservation_command_id"] or "")
        command = conn.execute(
            "SELECT * FROM inference_route_execution_commands WHERE command_id=?",
            (command_id,),
        ).fetchone()
        if command is None:
            return False
        request_hash = _sha256(
            {"action": "reserve", "command_id": command_id, "execution_id": execution_id}
        )
        try:
            effect = json.loads(str(command["effect_json"]))
            ticket = self._closed_reservation(effect["reservation"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError, ValidationError):
            return False
        expected = {
            "schema": "InferenceRouteAttemptReservation@1",
            "attempt_id": str(attempt["id"]),
            "execution_id": execution_id,
            "route_plan_id": route_plan_id,
            "operation_plan_id": operation_plan_id,
            "route_leg_ordinal": int(attempt["route_leg_ordinal"]),
            "physical_attempt_ordinal": int(attempt["physical_attempt_ordinal"]),
            "leg_attempt_ordinal": int(attempt["leg_attempt_ordinal"]),
            "purpose": str(attempt["purpose"]),
            "deployment_revision_id": str(attempt["deployment_revision_id"]),
            "child_invocation_id": str(attempt["child_invocation_id"]),
            "nonce": ticket.get("nonce"),
        }
        return bool(
            str(command["action"]) == "reserve"
            and str(command["execution_id"]) == execution_id
            and str(command["request_sha256"]) == request_hash
            and str(command["effect_sha256"]) == _sha256(effect)
            and set(effect) == {"schema", "execution_id", "terminal", "reservation"}
            and effect["schema"] == "RouteAttemptReservationEffect@1"
            and effect["execution_id"] == execution_id
            and effect["terminal"] is None
            and ticket == expected
            and _sha256({"nonce": ticket["nonce"]}) == str(attempt["admission_nonce_sha256"])
        )

    def _attempt_lifecycle_valid(self, conn: Any, attempt: Any) -> bool:
        """Rebuild claim/bind/dispatch state from immutable commands.

        This deliberately does not infer state from nullable columns alone: a
        paired edit of state, child id, and timestamp must not manufacture a
        provider-reaching attempt.
        """
        execution_id = str(attempt["execution_id"])
        reservation_command = conn.execute(
            "SELECT * FROM inference_route_execution_commands WHERE command_id=?",
            (attempt["reservation_command_id"],),
        ).fetchone()
        if reservation_command is None:
            return False
        try:
            reserve_effect = json.loads(str(reservation_command["effect_json"]))
            ticket = self._closed_reservation(reserve_effect["reservation"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError, ValidationError):
            return False
        commands = conn.execute(
            """SELECT * FROM inference_route_execution_commands
                 WHERE execution_id=? AND action IN ('claim','bind','dispatch_intent')""",
            (execution_id,),
        ).fetchall()
        claim_matches: list[Any] = []
        bind_matches: list[Any] = []
        dispatch_matches: list[Any] = []
        for command in commands:
            try:
                effect = json.loads(str(command["effect_json"]))
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            if str(command["effect_sha256"]) != _sha256(effect):
                continue
            action = str(command["action"])
            command_id = str(command["command_id"])
            if action == "claim":
                if command_id != f"claim-{attempt['id']}":
                    continue
                expected = {
                    "schema": "InferenceRouteAttemptClaim@1",
                    "attempt_id": str(attempt["id"]),
                    "child_invocation_id": str(attempt["child_invocation_id"]),
                    "deployment_revision_id": str(attempt["deployment_revision_id"]),
                    "physical_attempt_ordinal": int(attempt["physical_attempt_ordinal"]),
                }
                request = {"action": "claim", "command_id": command_id, "reservation": ticket}
                if effect == expected and str(command["request_sha256"]) == _sha256(request):
                    claim_matches.append(command)
            elif action == "bind":
                if command_id != f"bind-{attempt['id']}":
                    continue
                expected = self._bind_effect(attempt)
                request = {
                    "action": "bind", "command_id": command_id,
                    "attempt_id": str(attempt["id"]),
                    "child_operation_id": str(attempt["child_operation_id"] or ""),
                }
                if effect == expected and str(command["request_sha256"]) == _sha256(request):
                    bind_matches.append(command)
            else:
                if command_id != f"dispatch-{attempt['id']}":
                    continue
                expected = self._dispatch_effect(attempt)
                request = {
                    "action": "dispatch_intent", "command_id": command_id,
                    "attempt_id": str(attempt["id"]),
                }
                if effect == expected and str(command["request_sha256"]) == _sha256(request):
                    dispatch_matches.append(command)
        state = str(attempt["state"])
        claimed = len(claim_matches) == 1
        bound = len(bind_matches) == 1
        dispatched = len(dispatch_matches) == 1
        if state == "reserved":
            return bool(
                not claim_matches and not bind_matches and not dispatch_matches
                and attempt["admitted_at"] is None
                and attempt["child_operation_id"] is None
                and attempt["dispatch_intent_at"] is None
            )
        if not claimed or str(attempt["admitted_at"] or "") != str(claim_matches[0]["created_at"]):
            return False
        if state == "admitted":
            if dispatch_matches or attempt["dispatch_intent_at"] is not None:
                return False
            if attempt["child_operation_id"] is None:
                return not bind_matches
            if not bound or self._kernel_child_reader is None:
                return False
            child = self._kernel_child_reader(str(attempt["child_operation_id"]))
            return bool(
                child is not None
                and str(child.get("state") or "") == "claimed"
                and str(child.get("native_id") or "") == str(attempt["child_invocation_id"])
                and str(child.get("target_ref") or "")
                    == f"deployment-revision:{attempt['deployment_revision_id']}"
            )
        if state == "dispatch_intent":
            return bool(
                bound and dispatched
                and str(attempt["dispatch_intent_at"] or "") == str(dispatch_matches[0]["created_at"])
            )
        if state == "terminal":
            if attempt["dispatch_intent_at"] is None:
                return not dispatch_matches and len(bind_matches) <= 1
            return bool(
                bound and dispatched
                and str(attempt["dispatch_intent_at"] or "") == str(dispatch_matches[0]["created_at"])
            )
        return False

    def _terminal_attempt_valid(self, attempt: Any) -> bool:
        if str(attempt["state"]) != "terminal":
            return bool(
                attempt["disposition"] is None and attempt["outcome"] is None
                and attempt["disposition_evidence_sha256"] is None
                and attempt["classifier_revision"] is None and attempt["send_phase"] is None
            )
        try:
            evidence = json.loads(str(attempt["disposition_evidence_json"] or ""))
        except (TypeError, ValueError, json.JSONDecodeError):
            return False
        if (
            str(attempt["classifier_revision"] or "") != FALLBACK_CLASSIFIER_REVISION
            or _sha256(evidence) != str(attempt["disposition_evidence_sha256"] or "")
        ):
            return False
        child_id = str(attempt["child_operation_id"] or "")
        if attempt["child_receipt_sha256"] is None:
            expected = {
                "schema": "RunnerDispositionEvidence@1", "attempt_id": str(attempt["id"]),
                "child_operation_id": child_id, "child_receipt_id": None,
                "child_receipt_sha256": None, "kernel_outcome": "indeterminate",
                "send_phase": "dispatch_intent", "typed_signal": "receipt_missing_after_dispatch_intent",
                "classifier_revision": FALLBACK_CLASSIFIER_REVISION,
            }
            return bool(
                evidence == expected
                and attempt["disposition"] == "dispatch_outcome_unknown"
                and attempt["outcome"] == "indeterminate"
                and attempt["send_phase"] == "dispatch_intent"
                and attempt["dispatch_intent_at"] is not None
            )
        if not child_id or self._kernel_receipt_reader is None:
            return False
        reconstructed = self._kernel_receipt_reader(child_id)
        if reconstructed is None:
            return False
        operation = reconstructed.get("operation")
        receipt = reconstructed.get("receipt")
        attestation = reconstructed.get("terminal_attestation")
        if not isinstance(operation, dict) or not isinstance(receipt, dict) or not isinstance(attestation, dict):
            return False
        typed_signal = str(attestation.get("runner_signal") or "")
        phase = str(attestation.get("send_phase") or "")
        try:
            disposition, classified_phase = self._classify_receipt(str(receipt["state"]), typed_signal, phase)
        except (ConflictError, KeyError):
            return False
        receipt_sha = _sha256(receipt)
        expected = {
            "schema": "RunnerDispositionEvidence@1", "attempt_id": str(attempt["id"]),
            "child_operation_id": child_id, "child_receipt_id": str(receipt["receipt_id"]),
            "child_receipt_sha256": receipt_sha, "kernel_outcome": str(receipt["state"]),
            "send_phase": classified_phase, "typed_signal": typed_signal,
            "classifier_revision": FALLBACK_CLASSIFIER_REVISION,
        }
        return bool(
            evidence == expected
            and str(attempt["child_invocation_id"]) == str(operation.get("native_id") or "")
            and str(operation.get("target_ref") or "") == f"deployment-revision:{attempt['deployment_revision_id']}"
            and str(attempt["child_receipt_sha256"]) == receipt_sha
            and str(attempt["disposition"]) == disposition
            and str(attempt["outcome"]) == str(receipt["state"])
            and str(attempt["send_phase"]) == classified_phase
            and (str(receipt.get("result_ref") or "") if receipt["state"] == "succeeded" else "") == str(attempt["result_ref"] or "")
        )

    @staticmethod
    def _safe_id(value: Any, field: str) -> str:
        clean = str(value or "").strip()
        if not clean or len(clean) > 192 or not clean.replace("_", "").replace("-", "").replace(":", "").replace(".", "").isalnum():
            raise ValidationError(
                f"{field} is invalid", code="inference_route_execution_invalid"
            )
        return clean

    @staticmethod
    def _require_controller(authority: Principal) -> None:
        if authority != INFERENCE_FALLBACK_AUTHORITY:
            raise ValidationError(
                "Fallback controller authority is required.",
                code="inference_route_execution_authority_required",
            )


class RoutedAttemptRuntime:
    """Composition-owned bridge; requests carry tickets, never controllers."""

    def __init__(self, controller: InferenceFallbackController) -> None:
        self._controller = controller

    def claim(self, reservation: dict[str, Any]) -> dict[str, Any]:
        return self._controller.claim_reservation(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"claim-{reservation['attempt_id']}",
            reservation=reservation,
        )

    def bind(self, reservation: dict[str, Any], child_operation_id: str) -> dict[str, Any]:
        return self._controller.bind_admitted_child(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"bind-{reservation['attempt_id']}",
            attempt_id=str(reservation["attempt_id"]),
            child_operation_id=child_operation_id,
        )

    def mark_dispatch_intent(self, reservation: dict[str, Any]) -> dict[str, Any]:
        return self._controller.mark_dispatch_intent(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"dispatch-{reservation['attempt_id']}",
            attempt_id=str(reservation["attempt_id"]),
        )

    def settle(self, reservation: dict[str, Any], outcome: Any) -> dict[str, Any]:
        """Persist Runner-owned closed evidence; no request controls this call."""
        if str(outcome.send_phase) == "pre_send":
            return self._controller.adopt_pre_send_receipt(
                INFERENCE_FALLBACK_AUTHORITY,
                command_id=f"settle-{reservation['attempt_id']}",
                attempt_id=str(reservation["attempt_id"]),
                child_operation_id=str(outcome.operation_id),
            )
        return self._controller.settle_attempt(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"settle-{reservation['attempt_id']}",
            attempt_id=str(reservation["attempt_id"]),
        )
