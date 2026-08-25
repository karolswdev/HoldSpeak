"""Durable private ToolTurn reservation authority (HS-143-09 A2).

The controller owns leases, terminal election and tool/model reservation.  A
selected ``ToolModelAdapter`` may render and parse one provider wire exchange,
but the controller still delegates every physical model child to the existing
``InferenceFallbackController``/``InferenceRunner`` path and every tool child to
the Broker.  It never chooses a provider, loops, retries, or invokes a tool
service directly.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Protocol, Sequence

from ..principals import Principal, PrincipalKind
from .inference_fallback_controller import (
    INFERENCE_FALLBACK_AUTHORITY,
    InferenceFallbackController,
)
from .inference_route_plan_service import (
    ROUTE_PLANNING_AUTHORITY,
    InferenceRoutePlanService,
)
from .tool_capability_service import (
    CanonicalApplicationOperationDescriptor,
    ModelTurnCapabilityProjection,
    ToolCallCandidate,
    ToolCapabilityError,
    ToolResultEnvelope,
    canonical_json,
    sha256,
    validate_closed_arguments,
)
from .tool_model_adapter import (
    ToolModelAdapter,
    ToolModelAdapterError,
    ToolModelProviderAdapter,
    ToolModelProviderTransport,
    ToolModelToolCallCandidate,
)


TOOL_TURN_AUTHORITY = Principal(
    PrincipalKind.SERVICE,
    "tool-turn-controller",
    allowed_operations=frozenset({("inference.invoke", 1)}),
    authority_basis="kernel:tool-turn@1",
)
_MAX_CAPABILITIES = 12
_MAX_PROVIDER_STEPS = 4
_MAX_TOOL_CALLS = 6
_MAX_EFFECT_PROPOSALS = 1
_MAX_PARALLEL_READS = 2
_MAX_RESULT_BYTES = 64 * 1024
_MAX_RESULT_TOKENS = 8 * 1024
_MAX_PER_RESULT_BYTES = 32 * 1024
_MAX_WALL_SECONDS = 30
_SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_TERMINAL = frozenset({"result_ready", "stopped", "failed", "indeterminate"})


class ToolTurnError(RuntimeError):
    code = "tool_turn_invalid"


class ToolTurnRefused(ToolTurnError):
    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or code)


class ToolTurnConflict(ToolTurnError):
    code = "tool_turn_conflict"


MODEL_TURN_TOOL_PRINCIPAL = Principal(
    PrincipalKind.SERVICE,
    "model-turn-tool-service",
    allowed_operations=frozenset({("tool.call", 1)}),
    authority_basis="kernel:model-turn-tool@1",
)


class ToolCallBrokerPort(Protocol):
    """The canonical Broker boundary for exactly one reserved tool child."""

    def admit(
        self,
        *,
        turn_id: str,
        tool_call_id: str,
        descriptor: CanonicalApplicationOperationDescriptor,
        candidate: ToolCallCandidate,
    ) -> Mapping[str, Any]: ...

    def receipt(self, child_operation_id: str) -> Mapping[str, Any] | None: ...


class BrokerToolCallPort:
    """Production adapter through the existing Broker ``tool.call@1`` seam.

    This is intentionally narrow: it carries only a canonical argument digest to
    the kernel proposal record.  The application capability and private argument
    body remain under the frozen lease; there is no generic model ``call_tool``
    capability or owner transport surface here.
    """

    def __init__(self, broker: Any) -> None:
        if not hasattr(broker, "submit") or not hasattr(broker, "store"):
            raise ToolTurnError("tool Broker composition is invalid")
        self._broker = broker

    def admit(
        self,
        *,
        turn_id: str,
        tool_call_id: str,
        descriptor: CanonicalApplicationOperationDescriptor,
        candidate: ToolCallCandidate,
    ) -> Mapping[str, Any]:
        raw = {
            "request_schema": 1,
            "request_id": f"model-turn-{turn_id}-{tool_call_id}",
            "idempotency_key": f"model-turn-{turn_id}-{tool_call_id}",
            "operation": {"name": "tool.call", "version": 1},
            "subject_refs": [f"tool-turn:{turn_id}"],
            "target": {"ref": f"model-turn:{tool_call_id}"},
            "arguments": {
                "proposal_id": tool_call_id,
                "tool": descriptor.service_operation,
                "args_sha256": candidate.canonical_args_sha256.removeprefix("sha256:"),
                "args_head": f"MODEL_TURN {descriptor.capability_id}",
                "cwd": "model-turn",
                "ttl_seconds": 30,
            },
            "placement": "node:model-turn",
        }
        return self._broker.submit(raw, MODEL_TURN_TOOL_PRINCIPAL)

    def receipt(self, child_operation_id: str) -> Mapping[str, Any] | None:
        return self._broker.store.receipt(child_operation_id)


def _safe(value: Any, *, field: str) -> str:
    clean = str(value or "").strip()
    if not _SAFE.fullmatch(clean):
        raise ToolTurnError(f"{field} is invalid")
    return clean


def _hash(value: Any, *, field: str) -> str:
    clean = str(value or "").strip()
    if not _SHA256.fullmatch(clean):
        raise ToolTurnError(f"{field} is invalid")
    return clean


def _int(value: Any, *, field: str, minimum: int = 0, maximum: int = 2**31 - 1) -> int:
    if type(value) is not int or value < minimum or value > maximum:
        raise ToolTurnError(f"{field} is invalid")
    return value


def _timestamp(value: Any, *, field: str) -> float:
    if type(value) not in (int, float) or isinstance(value, bool):
        raise ToolTurnError(f"{field} is invalid")
    number = float(value)
    if number != number or number in (float("inf"), float("-inf")):
        raise ToolTurnError(f"{field} is invalid")
    return number


def _json(value: Any, *, field: str) -> Any:
    try:
        return json.loads(canonical_json(value))
    except (ToolCapabilityError, json.JSONDecodeError) as exc:
        raise ToolTurnError(f"{field} is not canonical JSON") from exc


def _sorted_ids(values: Any, *, field: str) -> list[str]:
    if not isinstance(values, list) or not values:
        raise ToolTurnError(f"{field} is invalid")
    normalized = sorted({_safe(item, field=field) for item in values})
    if len(normalized) != len(values):
        raise ToolTurnError(f"{field} has duplicate values")
    return normalized


@dataclass(frozen=True)
class TurnCapabilityLease:
    """Closed canonical private body persisted in ``turn_capability_leases``."""

    terms: Mapping[str, Any]
    terms_sha256: str

    @classmethod
    def parse(cls, raw: Mapping[str, Any], *, now: float | None = None) -> "TurnCapabilityLease":
        if not isinstance(raw, Mapping):
            raise ToolTurnError("lease terms are invalid")
        required = {
            "schema", "lease_id", "nonce", "epoch", "parent_turn_id", "owner_principal_id",
            "deployment_revision", "operation_kind", "operation_revision", "owner_intent_receipt_id",
            "policy_revision", "capabilities", "max_provider_steps", "max_tool_calls",
            "max_effect_proposals", "max_parallel_reads", "aggregate_result_bytes",
            "aggregate_result_tokens", "wall_deadline", "expires_at",
        }
        if set(raw) != required or raw.get("schema") != "TurnCapabilityLease@1":
            raise ToolTurnError("lease terms have an invalid shape")
        normalized: dict[str, Any] = {
            "schema": "TurnCapabilityLease@1",
            "lease_id": _safe(raw["lease_id"], field="lease_id"),
            "nonce": _safe(raw["nonce"], field="nonce"),
            "epoch": _int(raw["epoch"], field="epoch", minimum=1, maximum=1_000_000),
            "parent_turn_id": _safe(raw["parent_turn_id"], field="parent_turn_id"),
            "owner_principal_id": _safe(raw["owner_principal_id"], field="owner_principal_id"),
            "deployment_revision": _safe(raw["deployment_revision"], field="deployment_revision"),
            "operation_kind": _safe(raw["operation_kind"], field="operation_kind"),
            "operation_revision": _safe(raw["operation_revision"], field="operation_revision"),
            "owner_intent_receipt_id": None if raw["owner_intent_receipt_id"] is None else _safe(raw["owner_intent_receipt_id"], field="owner_intent_receipt_id"),
            "policy_revision": _safe(raw["policy_revision"], field="policy_revision"),
            "max_provider_steps": _int(raw["max_provider_steps"], field="max_provider_steps", minimum=1, maximum=_MAX_PROVIDER_STEPS),
            "max_tool_calls": _int(raw["max_tool_calls"], field="max_tool_calls", minimum=0, maximum=_MAX_TOOL_CALLS),
            "max_effect_proposals": _int(raw["max_effect_proposals"], field="max_effect_proposals", minimum=0, maximum=_MAX_EFFECT_PROPOSALS),
            "max_parallel_reads": _int(raw["max_parallel_reads"], field="max_parallel_reads", minimum=0, maximum=_MAX_PARALLEL_READS),
            "aggregate_result_bytes": _int(raw["aggregate_result_bytes"], field="aggregate_result_bytes", minimum=0, maximum=_MAX_RESULT_BYTES),
            "aggregate_result_tokens": _int(raw["aggregate_result_tokens"], field="aggregate_result_tokens", minimum=0, maximum=_MAX_RESULT_TOKENS),
            "wall_deadline": _timestamp(raw["wall_deadline"], field="wall_deadline"),
            "expires_at": _timestamp(raw["expires_at"], field="expires_at"),
        }
        if normalized["expires_at"] > normalized["wall_deadline"]:
            raise ToolTurnError("lease expiry exceeds wall deadline")
        if now is not None and (normalized["wall_deadline"] < now or normalized["wall_deadline"] - now > _MAX_WALL_SECONDS):
            raise ToolTurnError("lease deadline exceeds bootstrap maximum")
        capabilities = raw["capabilities"]
        if not isinstance(capabilities, list) or not capabilities or len(capabilities) > _MAX_CAPABILITIES:
            raise ToolTurnError("lease capability palette is invalid")
        normalized_capabilities = [cls._capability(item) for item in capabilities]
        normalized_capabilities.sort(key=lambda item: item["capability_id"])
        ids = [item["capability_id"] for item in normalized_capabilities]
        if len(ids) != len(set(ids)):
            raise ToolTurnError("lease capability palette has duplicates")
        if sum(item["max_calls"] for item in normalized_capabilities) < normalized["max_tool_calls"]:
            # A whole-turn maximum cannot promise calls no leased capability allows.
            raise ToolTurnError("lease tool call maximum exceeds capability limits")
        if normalized["max_parallel_reads"] and not any(item["commutative_read"] for item in normalized_capabilities):
            raise ToolTurnError("parallel reads require commutative read capabilities")
        if normalized["max_effect_proposals"] and not any(item["class"] == "effect_proposal" for item in normalized_capabilities):
            raise ToolTurnError("effect quota requires an effect proposal capability")
        normalized["capabilities"] = normalized_capabilities
        return cls(terms=normalized, terms_sha256=sha256(normalized))

    @staticmethod
    def _capability(raw: Any) -> dict[str, Any]:
        if not isinstance(raw, Mapping):
            raise ToolTurnError("lease capability is invalid")
        required = {
            "capability_id", "capability_revision", "descriptor_sha256", "schema_sha256",
            "service_operation", "class", "effect_mode", "scope", "data_classes", "placement",
            "egress", "max_calls", "max_result_bytes", "max_result_tokens", "commutative_read",
        }
        if set(raw) != required:
            raise ToolTurnError("lease capability has an invalid shape")
        klass = raw["class"]
        mode = raw["effect_mode"]
        if klass not in {"evidence_read", "candidate_builder", "effect_proposal"} or mode not in {"read", "candidate", "proposal", "execute_if_policy_admits"}:
            raise ToolTurnError("lease capability class or effect mode is invalid")
        if klass == "evidence_read" and mode != "read":
            raise ToolTurnError("evidence read lease is invalid")
        if mode == "execute_if_policy_admits" and klass != "effect_proposal":
            raise ToolTurnError("effect execution lease is invalid")
        commutative = raw["commutative_read"]
        if type(commutative) is not bool or commutative and mode != "read":
            raise ToolTurnError("commutative_read is invalid")
        return {
            "capability_id": _safe(raw["capability_id"], field="capability_id"),
            "capability_revision": _int(raw["capability_revision"], field="capability_revision", minimum=1, maximum=1_000_000),
            "descriptor_sha256": _hash(raw["descriptor_sha256"], field="descriptor_sha256"),
            "schema_sha256": _hash(raw["schema_sha256"], field="schema_sha256"),
            "service_operation": _safe(raw["service_operation"], field="service_operation"),
            "class": klass,
            "effect_mode": mode,
            "scope": _json(raw["scope"], field="scope"),
            "data_classes": _sorted_ids(raw["data_classes"], field="data_classes"),
            "placement": _sorted_ids(raw["placement"], field="placement"),
            "egress": _sorted_ids(raw["egress"], field="egress"),
            "max_calls": _int(raw["max_calls"], field="max_calls", minimum=1, maximum=_MAX_TOOL_CALLS),
            "max_result_bytes": _int(raw["max_result_bytes"], field="max_result_bytes", minimum=1, maximum=_MAX_PER_RESULT_BYTES),
            "max_result_tokens": _int(raw["max_result_tokens"], field="max_result_tokens", minimum=1, maximum=_MAX_RESULT_TOKENS),
            "commutative_read": commutative,
        }

    def capability(self, capability_id: str) -> Mapping[str, Any]:
        clean = _safe(capability_id, field="capability_id")
        for item in self.terms["capabilities"]:
            if item["capability_id"] == clean:
                return item
        raise ToolTurnRefused("capability_not_leased")


class ToolTurnController:
    """Server-owned lease/turn transaction authority; intentionally sync-hostile."""

    is_tool_turn_controller = True
    sync_allowed = False

    def __init__(
        self,
        db: Any,
        *,
        projection: ModelTurnCapabilityProjection,
        clock: Callable[[], float],
        route_plan_service: InferenceRoutePlanService | None = None,
        fallback_controller: InferenceFallbackController | None = None,
        model_coordinator: Any | None = None,
        tool_broker: ToolCallBrokerPort | None = None,
    ) -> None:
        if not isinstance(projection, ModelTurnCapabilityProjection):
            raise ToolTurnError("MODEL_TURN projection is required")
        if (route_plan_service is None) != (fallback_controller is None):
            raise ToolTurnError("model-step route and fallback composition must arrive together")
        if model_coordinator is not None and (
            route_plan_service is None
            or fallback_controller is None
            or getattr(model_coordinator, "plans", None) is not route_plan_service
            or getattr(model_coordinator, "controller", None) is not fallback_controller
        ):
            raise ToolTurnError("model-step execution composition must share route authority")
        self._db = db
        self._projection = projection
        self._clock = clock
        self._plans = route_plan_service
        self._fallback = fallback_controller
        self._model_coordinator = model_coordinator
        self._tool_broker = tool_broker

    @staticmethod
    def _require_authority(principal: Principal | None) -> None:
        if principal is None or principal.kind is not PrincipalKind.SERVICE or principal.identity != TOOL_TURN_AUTHORITY.identity:
            raise ToolTurnRefused("tool_turn_service_required")

    def start(
        self,
        principal: Principal,
        *,
        command_id: str,
        turn_id: str,
        parent_operation_id: str,
        parent_bundle_id: str,
        route_plan_id: str,
        route_plan_sha256: str,
        lease_terms: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Atomically freeze one validated lease beside one already-admitted bundle."""
        self._require_authority(principal)
        command = _safe(command_id, field="command_id")
        turn = _safe(turn_id, field="turn_id")
        parent = _safe(parent_operation_id, field="parent_operation_id")
        bundle = _safe(parent_bundle_id, field="parent_bundle_id")
        route = _safe(route_plan_id, field="route_plan_id")
        route_hash = _hash(route_plan_sha256, field="route_plan_sha256")
        now = float(self._clock())
        lease = TurnCapabilityLease.parse(lease_terms, now=now)
        if lease.terms["parent_turn_id"] != turn:
            raise ToolTurnError("lease parent turn does not match turn")
        self._validate_projection(lease)
        request = {
            "schema": "ToolTurnStart@1", "command_id": command, "turn_id": turn,
            "parent_operation_id": parent, "parent_bundle_id": bundle, "route_plan_id": route,
            "route_plan_sha256": route_hash, "lease_sha256": lease.terms_sha256,
        }
        request_hash = sha256(request)
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                replay = conn.execute("SELECT * FROM tool_turn_commands WHERE command_id=?", (command,)).fetchone()
                if replay is not None:
                    if str(replay["kind"]) != "start" or str(replay["request_sha256"]) != request_hash:
                        raise ToolTurnConflict("tool turn start command changed")
                    result = self._turn_projection(conn, turn)
                    conn.commit()
                    return {**result, "replayed": True}
                self._verify_parent_bundle(conn, parent=parent, bundle=bundle, route=route, route_hash=route_hash)
                existing = conn.execute("SELECT command_id FROM tool_turns WHERE turn_id=?", (turn,)).fetchone()
                if existing is not None:
                    raise ToolTurnConflict("tool turn id is already bound")
                conn.execute(
                    """INSERT INTO turn_capability_leases
                       (lease_id,turn_id,terms_json,terms_sha256,nonce_sha256,epoch,created_at,expires_at,state)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (lease.terms["lease_id"], turn, canonical_json(lease.terms), lease.terms_sha256,
                     sha256({"nonce": lease.terms["nonce"]}), lease.terms["epoch"], now,
                     lease.terms["expires_at"], "active"),
                )
                budgets = self._budgets(lease)
                conn.execute(
                    """INSERT INTO tool_turns
                       (turn_id,command_id,parent_operation_id,parent_bundle_id,route_plan_id,route_plan_sha256,
                        lease_id,lease_sha256,budgets_json,budgets_sha256,state,deadline_at,created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (turn, command, parent, bundle, route, route_hash, lease.terms["lease_id"],
                     lease.terms_sha256, canonical_json(budgets), sha256(budgets), "reserved",
                     lease.terms["wall_deadline"], now, now),
                )
                result = self._turn_projection(conn, turn)
                self._command(conn, command, turn, "start", request_hash, result, now)
                self._transition(conn, turn, "", "reserved", "started", result, now)
                conn.commit()
                return result
            except Exception:
                conn.rollback()
                raise

    def reserve_model_step(
        self,
        principal: Principal,
        *,
        command_id: str,
        turn_id: str,
        operation_request_plan_id: str,
        operation_request_plan_sha256: str,
        request_material_ref: str,
    ) -> dict[str, Any]:
        """Reserve the next model-step ordinal; provider dispatch remains elsewhere."""
        self._require_authority(principal)
        command, turn = _safe(command_id, field="command_id"), _safe(turn_id, field="turn_id")
        plan, plan_hash, material_ref = (
            _safe(operation_request_plan_id, field="operation_request_plan_id"),
            _hash(operation_request_plan_sha256, field="operation_request_plan_sha256"),
            _safe(request_material_ref, field="request_material_ref"),
        )
        request = {"schema": "ToolTurnReserveModelStep@1", "turn_id": turn, "plan": plan, "plan_hash": plan_hash, "material_ref": material_ref}
        return self._reserve_model_step(command, request)

    def _reserve_model_step(self, command: str, request: Mapping[str, Any]) -> dict[str, Any]:
        turn = str(request["turn_id"])
        request_hash = sha256(request)
        now = float(self._clock())
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                replay = conn.execute("SELECT * FROM tool_turn_commands WHERE command_id=?", (command,)).fetchone()
                if replay is not None:
                    if str(replay["kind"]) != "reserve_model_step" or str(replay["request_sha256"]) != request_hash:
                        raise ToolTurnConflict("model step command changed")
                    row = conn.execute("SELECT * FROM tool_turn_model_steps WHERE turn_id=? ORDER BY ordinal DESC LIMIT 1", (turn,)).fetchone()
                    if row is None:
                        raise ToolTurnConflict("model step command has no effect")
                    conn.commit()
                    return {**self._model_step_projection(row), "replayed": True}
                row, lease = self._live_turn(conn, turn, now)
                ordinal = int(conn.execute("SELECT COALESCE(MAX(ordinal),0)+1 FROM tool_turn_model_steps WHERE turn_id=?", (turn,)).fetchone()[0])
                if ordinal > int(lease.terms["max_provider_steps"]):
                    self._terminalize(conn, row, "failed", "model_step_budget_exhausted", "", now)
                    # This is a terminal election, not a failed prospective
                    # reservation: persist it before returning the typed refusal.
                    conn.commit()
                    raise ToolTurnRefused("model_step_budget_exhausted")
                step_id = "tms_" + uuid.uuid4().hex
                conn.execute(
                    """INSERT INTO tool_turn_model_steps
                       (id,turn_id,ordinal,operation_request_plan_id,operation_request_plan_sha256,
                        lease_sha256,state,request_material_ref,created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (step_id, turn, ordinal, request["plan"], request["plan_hash"], row["lease_sha256"],
                     "reserved", request["material_ref"], now, now),
                )
                result = self._model_step_projection(conn.execute("SELECT * FROM tool_turn_model_steps WHERE id=?", (step_id,)).fetchone())
                self._command(conn, command, turn, "reserve_model_step", request_hash, result, now)
                self._transition(conn, turn, str(row["state"]), "model_running", "model_step_reserved", result, now)
                conn.execute("UPDATE tool_turns SET state='model_running',revision=revision+1,updated_at=? WHERE turn_id=?", (now, turn))
                conn.commit()
                return result
            except Exception:
                conn.rollback()
                raise

    def reserve_tool_call(
        self,
        principal: Principal,
        *,
        command_id: str,
        turn_id: str,
        provider_tool_call_id: str,
        capability_id: str,
        capability_revision: int,
        arguments: Mapping[str, Any],
        provider_call_ordinal: int | None = None,
    ) -> dict[str, Any]:
        """Atomically reserve a frozen worst-case tool slot before Broker admission.

        Native adapters always supply their provider-call ordinal.  The ``None``
        compatibility form is retained only for internal direct reservations and
        derives the next ordinal under this transaction; it cannot alter an
        adapter-supplied ordinal.
        """
        self._require_authority(principal)
        command, turn = _safe(command_id, field="command_id"), _safe(turn_id, field="turn_id")
        provider_id = _safe(provider_tool_call_id, field="provider_tool_call_id")
        provider_ordinal = None if provider_call_ordinal is None else _int(
            provider_call_ordinal, field="provider_call_ordinal", minimum=1, maximum=_MAX_TOOL_CALLS
        )
        capability = _safe(capability_id, field="capability_id")
        revision = _int(capability_revision, field="capability_revision", minimum=1, maximum=1_000_000)
        args = _json(arguments, field="arguments")
        args_hash = sha256(args)
        request = {
            "schema": "ToolTurnReserveToolCall@1", "turn_id": turn,
            "provider_tool_call_id": provider_id, "provider_call_ordinal": provider_ordinal,
            "capability_id": capability, "capability_revision": revision,
            "canonical_args_sha256": args_hash,
        }
        request_hash, now = sha256(request), float(self._clock())
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                replay = conn.execute("SELECT * FROM tool_turn_commands WHERE command_id=?", (command,)).fetchone()
                if replay is not None:
                    if str(replay["kind"]) != "reserve_tool_call" or str(replay["request_sha256"]) != request_hash:
                        raise ToolTurnConflict("tool call command changed")
                    row = conn.execute("SELECT * FROM tool_turn_tool_calls WHERE turn_id=? AND provider_tool_call_id=?", (turn, provider_id)).fetchone()
                    if row is None:
                        raise ToolTurnConflict("tool call command has no effect")
                    conn.commit()
                    return {**self._tool_call_projection(row), "replayed": True}
                turn_row, lease = self._live_turn(conn, turn, now)
                existing = conn.execute("SELECT * FROM tool_turn_tool_calls WHERE turn_id=? AND provider_tool_call_id=?", (turn, provider_id)).fetchone()
                if existing is not None:
                    same = (
                        (provider_ordinal is None or int(existing["provider_tool_ordinal"]) == provider_ordinal)
                        and str(existing["capability_id"]) == capability
                        and int(existing["capability_revision"]) == revision
                        and str(existing["canonical_args_sha256"]) == args_hash
                    )
                    if not same:
                        raise ToolTurnRefused("provider_tool_call_replay_changed")
                    result = self._tool_call_projection(existing)
                    self._command(conn, command, turn, "reserve_tool_call", request_hash, result, now)
                    conn.commit()
                    return {**result, "replayed": True}
                term = lease.capability(capability)
                try:
                    descriptor = self._projection.require(capability)
                    normalized_arguments = validate_closed_arguments(descriptor.argument_schema, args)
                except ToolCapabilityError as exc:
                    raise ToolTurnRefused("tool_call_arguments_schema_invalid") from exc
                if sha256(normalized_arguments) != args_hash:
                    raise ToolTurnRefused("tool_call_argument_hash_invalid")
                if (
                    descriptor.revision != int(term["capability_revision"])
                    or descriptor.descriptor_sha256 != str(term["descriptor_sha256"])
                    or descriptor.schema_sha256 != str(term["schema_sha256"])
                    or descriptor.service_operation != str(term["service_operation"])
                ):
                    raise ToolTurnRefused("capability_schema_or_descriptor_drift")
                if int(term["capability_revision"]) != revision:
                    raise ToolTurnRefused("capability_revision_mismatch")
                usage = conn.execute(
                    """SELECT COUNT(*) AS calls,COALESCE(SUM(reserved_result_bytes),0) AS bytes,
                              COALESCE(SUM(reserved_result_tokens),0) AS tokens,
                              COALESCE(SUM(reserved_effects),0) AS effects
                         FROM tool_turn_tool_calls WHERE turn_id=?""", (turn,)
                ).fetchone()
                cap_calls = conn.execute(
                    "SELECT COUNT(*) FROM tool_turn_tool_calls WHERE turn_id=? AND capability_id=?", (turn, capability)
                ).fetchone()[0]
                if int(usage["calls"]) >= int(lease.terms["max_tool_calls"]) or int(cap_calls) >= int(term["max_calls"]):
                    raise ToolTurnRefused("tool_call_budget_exhausted")
                reserved_effects = 1 if term["class"] == "effect_proposal" else 0
                if int(usage["bytes"]) + int(term["max_result_bytes"]) > int(lease.terms["aggregate_result_bytes"]):
                    raise ToolTurnRefused("aggregate_result_bytes_exhausted")
                if int(usage["tokens"]) + int(term["max_result_tokens"]) > int(lease.terms["aggregate_result_tokens"]):
                    raise ToolTurnRefused("aggregate_result_tokens_exhausted")
                if int(usage["effects"]) + reserved_effects > int(lease.terms["max_effect_proposals"]):
                    raise ToolTurnRefused("effect_budget_exhausted")
                ordinal = int(conn.execute("SELECT COALESCE(MAX(tool_ordinal),0)+1 FROM tool_turn_tool_calls WHERE turn_id=?", (turn,)).fetchone()[0])
                effective_provider_ordinal = ordinal if provider_ordinal is None else provider_ordinal
                call_id = "ttc_" + uuid.uuid4().hex
                conn.execute(
                    """INSERT INTO tool_turn_tool_calls
                       (id,turn_id,tool_ordinal,provider_tool_ordinal,provider_tool_call_id,capability_id,
                        capability_revision,lease_sha256,canonical_args_sha256,reserved_result_bytes,
                        reserved_result_tokens,reserved_effects,state,created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (call_id, turn, ordinal, effective_provider_ordinal, provider_id, capability, revision, turn_row["lease_sha256"],
                     args_hash, term["max_result_bytes"], term["max_result_tokens"], reserved_effects,
                     "reserved", now, now),
                )
                result = self._tool_call_projection(conn.execute("SELECT * FROM tool_turn_tool_calls WHERE id=?", (call_id,)).fetchone())
                self._command(conn, command, turn, "reserve_tool_call", request_hash, result, now)
                if str(turn_row["state"]) != "tool_requested":
                    self._transition(conn, turn, str(turn_row["state"]), "tool_requested", "tool_call_reserved", result, now)
                    conn.execute("UPDATE tool_turns SET state='tool_requested',revision=revision+1,updated_at=? WHERE turn_id=?", (now, turn))
                conn.commit()
                return result
            except Exception:
                conn.rollback()
                raise

    def plan_model_step(
        self,
        principal: Principal,
        *,
        command_id: str,
        turn_id: str,
        planning_reference: str,
    ) -> dict[str, Any]:
        """Freeze one new private request plan and start one route execution.

        The caller can name neither deployment nor physical attempt.  The frozen
        parent route remains the sole source of those facts; the existing fallback
        controller remains the only authority that can later reserve a Runner
        child.
        """
        self._require_authority(principal)
        if self._plans is None or self._fallback is None:
            raise ToolTurnRefused("tool_turn_model_step_composition_missing")
        command, turn, reference = (
            _safe(command_id, field="command_id"), _safe(turn_id, field="turn_id"),
            _safe(planning_reference, field="planning_reference"),
        )
        now = float(self._clock())
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row, _lease = self._live_turn(conn, turn, now)
                request_hash = sha256({"schema": "ToolTurnPlanModelStep@1", "turn_id": turn, "planning_reference": reference})
                replay = conn.execute("SELECT * FROM tool_turn_commands WHERE command_id=?", (command,)).fetchone()
                if replay is not None:
                    if str(replay["kind"]) != "reserve_model_step" or str(replay["request_sha256"]) != request_hash:
                        raise ToolTurnConflict("model step command changed")
                    step = conn.execute(
                        "SELECT * FROM tool_turn_model_steps WHERE turn_id=? AND request_material_ref=?",
                        (turn, reference),
                    ).fetchone()
                    if step is None:
                        raise ToolTurnConflict("model step command has no effect")
                    conn.commit()
                    return {**self._model_step_projection(step), "replayed": True}
                material_id = hashlib.sha256(f"{turn}:{command}".encode("utf-8")).hexdigest()[:32]
                frozen = self._plans.freeze_operation_for_route_in_transaction(
                    ROUTE_PLANNING_AUTHORITY, conn,
                    command_id=f"tool-step-freeze-{material_id}", route_plan_id=str(row["route_plan_id"]),
                    operation_id=f"tool-step-{material_id}", planning_reference=reference,
                )
                route = frozen["route_plan"]
                operation = frozen["operation_request_plan"]
                if str(route["sha256"]) != str(row["route_plan_sha256"]) or str(operation["route_plan_id"]) != str(row["route_plan_id"]):
                    raise ToolTurnRefused("tool_turn_step_route_integrity_invalid")
                ordinal = int(conn.execute(
                    "SELECT COALESCE(MAX(ordinal),0)+1 FROM tool_turn_model_steps WHERE turn_id=?", (turn,)
                ).fetchone()[0])
                lease = self._load_lease(conn, row)
                if ordinal > int(lease.terms["max_provider_steps"]):
                    self._terminalize(conn, row, "failed", "model_step_budget_exhausted", "", now)
                    # This is a terminal election, not a failed prospective
                    # reservation: persist it before returning the typed refusal.
                    conn.commit()
                    raise ToolTurnRefused("model_step_budget_exhausted")
                step_id = "tms_" + uuid.uuid4().hex
                conn.execute(
                    """INSERT INTO tool_turn_model_steps
                       (id,turn_id,ordinal,operation_request_plan_id,operation_request_plan_sha256,
                        lease_sha256,state,request_material_ref,created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (step_id, turn, ordinal, operation["id"], operation["sha256"], row["lease_sha256"],
                     "reserved", reference, now, now),
                )
                execution = self._fallback.start_execution_in_transaction(
                    INFERENCE_FALLBACK_AUTHORITY, conn,
                    command_id=f"tool-step-execution-{material_id}", operation_plan_id=str(operation["id"]),
                )
                conn.execute(
                    """UPDATE tool_turn_model_steps SET route_execution_id=?,state='running',updated_at=?
                       WHERE id=? AND state='reserved'""",
                    (execution["id"], now, step_id),
                )
                step = conn.execute("SELECT * FROM tool_turn_model_steps WHERE id=?", (step_id,)).fetchone()
                result = self._model_step_projection(step)
                self._command(conn, command, turn, "reserve_model_step", request_hash, result, now)
                self._transition(conn, turn, str(row["state"]), "model_running", "model_step_execution_started", result, now)
                conn.execute("UPDATE tool_turns SET state='model_running',revision=revision+1,updated_at=? WHERE turn_id=?", (now, turn))
                conn.commit()
                return result
            except Exception:
                conn.rollback()
                raise

    def execute_model_step(
        self,
        principal: Principal,
        *,
        command_id: str,
        turn_id: str,
        model_step_id: str,
        model_adapter: ToolModelAdapter,
        provider_transport: ToolModelProviderTransport,
    ) -> dict[str, Any]:
        """Run one planned step through one selected native-tool adapter bridge.

        The bridge is constrained to one render/request/parse exchange for every
        physical Runner child.  Route retries remain outside it in the existing
        fallback controller; the model-step receipt settles before any parsed tool
        candidate is admitted through the canonical Broker path.
        """
        self._require_authority(principal)
        if self._model_coordinator is None:
            raise ToolTurnRefused("tool_turn_model_execution_composition_missing")
        if not isinstance(model_adapter, ToolModelAdapter):
            raise ToolTurnRefused("tool_model_adapter_required")
        if not isinstance(provider_transport, ToolModelProviderTransport):
            raise ToolTurnRefused("tool_model_transport_required")
        command, turn, step_id = (
            _safe(command_id, field="command_id"), _safe(turn_id, field="turn_id"),
            _safe(model_step_id, field="model_step_id"),
        )
        now = float(self._clock())
        with self._db._connection() as conn:
            row, lease = self._live_turn(conn, turn, now)
            step = conn.execute(
                "SELECT * FROM tool_turn_model_steps WHERE id=? AND turn_id=?", (step_id, turn)
            ).fetchone()
            if step is None or str(step["state"]) != "running" or not str(step["route_execution_id"]):
                raise ToolTurnRefused("model_step_not_running")
            if str(step["lease_sha256"]) != str(row["lease_sha256"]):
                raise ToolTurnRefused("tool_turn_step_lease_integrity_invalid")
            provider_tools = self._projection.provider_tools([
                str(item["capability_id"]) for item in lease.terms["capabilities"]
            ])
        bridge = ToolModelProviderAdapter(model_adapter, provider_transport, provider_tools)
        outcome = self._model_coordinator.execute(
            TOOL_TURN_AUTHORITY,
            execution_id=str(step["route_execution_id"]),
            adapter=bridge,
        )
        if outcome.get("outcome") != "succeeded" or not isinstance(outcome.get("result"), Mapping):
            return {
                "schema": "ToolTurnModelStepOutcome@1", "model_step": self._model_step_projection(step),
                "outcome": str(outcome.get("outcome") or "failed"), "candidate": None,
            }
        try:
            candidate = bridge.candidate_for_result(outcome["result"])
        except ToolModelAdapterError as exc:
            raise ToolTurnRefused("tool_model_candidate_receipt_integrity_invalid") from exc
        # Candidate parsing is local, deterministic interpretation of the already
        # elected child result.  Settle the child into the *actual next turn
        # state*, rather than briefly lying that a tool-call continuation is
        # merely ``reserved`` (the A5 audit ledger note).
        next_state = "tool_requested" if isinstance(candidate, ToolModelToolCallCandidate) else "result_ready"
        settled = self.settle_model_step(
            principal, command_id=f"settle-{hashlib.sha256(command.encode()).hexdigest()[:24]}",
            turn_id=turn, model_step_id=step_id, next_state=next_state,
        )
        admitted = None
        if isinstance(candidate, ToolModelToolCallCandidate):
            admitted = self.admit_tool_call(
                principal,
                command_id=f"tool-{hashlib.sha256(command.encode()).hexdigest()[:24]}",
                turn_id=turn,
                candidate=candidate.tool_call,
            )
        return {
            "schema": "ToolTurnModelStepOutcome@1", "model_step": settled,
            "outcome": "succeeded", "candidate": candidate.to_dict(), "tool_call": admitted,
        }

    def settle_model_step(
        self,
        principal: Principal,
        *,
        command_id: str,
        turn_id: str,
        model_step_id: str,
        next_state: str,
    ) -> dict[str, Any]:
        """Adopt a model child into its lawful model-answer or tool-call state."""
        self._require_authority(principal)
        command, turn, step_id = (
            _safe(command_id, field="command_id"), _safe(turn_id, field="turn_id"),
            _safe(model_step_id, field="model_step_id"),
        )
        if next_state not in {"tool_requested", "result_ready"}:
            raise ToolTurnRefused("model_step_next_state_invalid")
        now = float(self._clock())
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                step = conn.execute("SELECT * FROM tool_turn_model_steps WHERE id=? AND turn_id=?", (step_id, turn)).fetchone()
                if step is None:
                    raise ToolTurnRefused("model_step_not_found")
                request_hash = sha256({
                    "schema": "ToolTurnSettleModelStep@1", "turn_id": turn,
                    "model_step_id": step_id, "next_state": next_state,
                })
                replay = conn.execute("SELECT * FROM tool_turn_commands WHERE command_id=?", (command,)).fetchone()
                if replay is not None:
                    if str(replay["kind"]) != "reconcile" or str(replay["request_sha256"]) != request_hash:
                        raise ToolTurnConflict("model step settlement command changed")
                    conn.commit()
                    return {**self._model_step_projection(step), "replayed": True}
                if str(step["state"]) != "running" or not str(step["route_execution_id"]):
                    raise ToolTurnRefused("model_step_not_running")
                execution = conn.execute(
                    "SELECT * FROM inference_route_executions WHERE id=?", (step["route_execution_id"],)
                ).fetchone()
                attempt = None if execution is None or not execution["winning_attempt_id"] else conn.execute(
                    "SELECT * FROM inference_route_attempts WHERE id=?", (execution["winning_attempt_id"],)
                ).fetchone()
                if (
                    execution is None or str(execution["state"]) != "terminal" or attempt is None
                    or not str(attempt["child_receipt_sha256"])
                ):
                    raise ToolTurnRefused("model_step_receipt_missing")
                try:
                    evidence = json.loads(str(attempt["disposition_evidence_json"] or "{}"))
                    receipt_id = _safe(evidence["child_receipt_id"], field="child_receipt_id")
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                    raise ToolTurnRefused("model_step_receipt_integrity_invalid") from exc
                result_hash = sha256({
                    "route_execution_id": str(step["route_execution_id"]), "receipt_id": receipt_id,
                    "result_ref": str(attempt["result_ref"] or ""),
                })
                row = self._live_turn(conn, turn, now)[0]
                conn.execute(
                    """UPDATE tool_turn_model_steps SET state='receipted',child_receipt_id=?,result_sha256=?,updated_at=?
                       WHERE id=? AND state='running'""",
                    (receipt_id, result_hash, now, step_id),
                )
                step = conn.execute("SELECT * FROM tool_turn_model_steps WHERE id=?", (step_id,)).fetchone()
                result = self._model_step_projection(step)
                if next_state == "result_ready":
                    # A final answer is terminal only after its physical child
                    # receipt is durable.  It cannot later be mistaken for an
                    # idle/reserved tool turn and resumed with new egress.
                    self._terminalize(
                        conn, row, "result_ready", "model_answer_ready", "",
                        now, final_result_ref=step_id,
                    )
                else:
                    conn.execute(
                        "UPDATE tool_turns SET state='tool_requested',revision=revision+1,updated_at=? WHERE turn_id=?",
                        (now, turn),
                    )
                    self._transition(
                        conn, turn, str(row["state"]), "tool_requested",
                        "model_step_tool_requested", result, now,
                    )
                self._command(conn, command, turn, "reconcile", request_hash, result, now)
                conn.commit()
                return result
            except Exception:
                conn.rollback()
                raise

    def admit_tool_call(
        self,
        principal: Principal,
        *,
        command_id: str,
        turn_id: str,
        candidate: ToolCallCandidate,
    ) -> dict[str, Any]:
        """Validate a single native candidate, reserve it, then admit one Broker child."""
        self._require_authority(principal)
        if self._tool_broker is None:
            raise ToolTurnRefused("tool_turn_broker_composition_missing")
        if not isinstance(candidate, ToolCallCandidate):
            raise ToolTurnRefused("tool_call_candidate_invalid")
        turn = _safe(turn_id, field="turn_id")
        with self._db._connection() as conn:
            now = float(self._clock())
            conn.execute("BEGIN IMMEDIATE")
            try:
                row, lease = self._live_turn(conn, turn, now)
                descriptor, term = self._validate_tool_candidate(lease, candidate)
                if str(row["lease_sha256"]) != sha256(lease.terms):
                    raise ToolTurnRefused("tool_turn_lease_integrity_invalid")
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        reservation = self.reserve_tool_call(
            principal, command_id=command_id, turn_id=turn,
            provider_tool_call_id=candidate.provider_tool_call_id, capability_id=candidate.capability_id,
            capability_revision=descriptor.revision, arguments=candidate.arguments,
            provider_call_ordinal=candidate.provider_call_ordinal,
        )
        admitted = self._tool_broker.admit(
            turn_id=turn, tool_call_id=str(reservation["id"]), descriptor=descriptor, candidate=candidate,
        )
        child_id = _safe(admitted.get("operation_id"), field="broker_child_id")
        now = float(self._clock())
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row, lease = self._live_turn(conn, turn, now)
                call = conn.execute("SELECT * FROM tool_turn_tool_calls WHERE id=? AND turn_id=?", (reservation["id"], turn)).fetchone()
                if call is None:
                    raise ToolTurnRefused("tool_call_reservation_missing")
                if str(call["state"]) == "reserved":
                    conn.execute("UPDATE tool_turn_tool_calls SET state='admitted',broker_child_id=?,updated_at=? WHERE id=?", (child_id, now, call["id"]))
                    if term["class"] == "effect_proposal":
                        conn.execute(
                            """INSERT INTO tool_turn_effect_children
                               (id,turn_id,tool_call_id,broker_child_id,owner_intent_receipt_ref,
                                policy_receipt_ref,disposition,state,created_at)
                               VALUES (?,?,?,?,?,?,?,?,?)""",
                            ("tte_" + uuid.uuid4().hex, turn, call["id"], child_id,
                             str(lease.terms["owner_intent_receipt_id"] or ""),
                             str(lease.terms["policy_revision"]), "effect_pending", "reserved", now),
                        )
                    conn.execute("UPDATE tool_turns SET state='tool_admitted',revision=revision+1,updated_at=? WHERE turn_id=?", (now, turn))
                elif str(call["broker_child_id"]) != child_id:
                    raise ToolTurnConflict("tool call child changed")
                call = conn.execute("SELECT * FROM tool_turn_tool_calls WHERE id=?", (reservation["id"],)).fetchone()
                conn.commit()
                return self._tool_call_projection(call)
            except Exception:
                conn.rollback()
                raise

    def settle_tool_call(
        self,
        principal: Principal,
        *,
        command_id: str,
        turn_id: str,
        tool_call_id: str,
        receipt_id: str,
        envelope: ToolResultEnvelope,
        result_material: Any | None = None,
    ) -> dict[str, Any]:
        """Adopt one immutable child receipt into the closed result envelope only."""
        self._require_authority(principal)
        if not isinstance(envelope, ToolResultEnvelope):
            raise ToolTurnRefused("tool_result_envelope_required")
        command, turn, call_id, receipt = (
            _safe(command_id, field="command_id"), _safe(turn_id, field="turn_id"),
            _safe(tool_call_id, field="tool_call_id"), _safe(receipt_id, field="receipt_id"),
        )
        request_hash, now = sha256({"schema": "ToolTurnSettleToolCall@1", "turn_id": turn, "tool_call_id": call_id, "receipt_id": receipt, "envelope": envelope.__dict__}), float(self._clock())
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                replay = conn.execute("SELECT * FROM tool_turn_commands WHERE command_id=?", (command,)).fetchone()
                if replay is not None:
                    if str(replay["kind"]) != "reconcile" or str(replay["request_sha256"]) != request_hash:
                        raise ToolTurnConflict("tool settlement command changed")
                    call = conn.execute("SELECT * FROM tool_turn_tool_calls WHERE id=?", (call_id,)).fetchone()
                    if call is None:
                        raise ToolTurnConflict("tool settlement command has no effect")
                    conn.commit()
                    return {**self._tool_call_projection(call), "replayed": True}
                row, _lease = self._live_turn(conn, turn, now)
                call = conn.execute("SELECT * FROM tool_turn_tool_calls WHERE id=? AND turn_id=?", (call_id, turn)).fetchone()
                if call is None or str(call["state"]) != "admitted" or not str(call["broker_child_id"]):
                    raise ToolTurnRefused("tool_call_not_admitted")
                if self._tool_broker is not None:
                    durable = self._tool_broker.receipt(str(call["broker_child_id"]))
                    if durable is not None and str(durable.get("receipt_id") or "") != receipt:
                        raise ToolTurnRefused("tool_call_receipt_binding_invalid")
                if envelope.status == "available":
                    material = _json(result_material, field="result_material")
                    if sha256(material) != envelope.result_sha256 or envelope.result_bytes > int(call["reserved_result_bytes"]) or envelope.result_tokens > int(call["reserved_result_tokens"]):
                        raise ToolTurnRefused("tool_result_budget_or_hash_invalid")
                    result_hash = str(envelope.result_sha256)
                    material_json = canonical_json(material)
                    state, disposition = "receipted", "available"
                else:
                    if result_material is not None:
                        raise ToolTurnRefused("tool_result_limitation_carries_material")
                    result_hash, material_json = "", ""
                    state, disposition = envelope.status, envelope.status
                conn.execute(
                    """UPDATE tool_turn_tool_calls SET state=?,receipt_id=?,result_sha256=?,disposition=?,updated_at=?
                       WHERE id=? AND state='admitted'""",
                    (state, receipt, result_hash, disposition, now, call_id),
                )
                conn.execute(
                    """INSERT INTO tool_turn_tool_call_results
                       (tool_call_id,turn_id,provider_tool_ordinal,envelope_json,result_material_json,
                        result_material_sha256,created_at)
                       VALUES (?,?,?,?,?,?,?)""",
                    (call_id, turn, int(call["provider_tool_ordinal"]), canonical_json({
                        "status": envelope.status, "result_sha256": envelope.result_sha256,
                        "result_bytes": envelope.result_bytes, "result_tokens": envelope.result_tokens,
                        "final_answer_may_name_limitation": envelope.final_answer_may_name_limitation,
                    }), material_json, result_hash, now),
                )
                effect = conn.execute("SELECT * FROM tool_turn_effect_children WHERE tool_call_id=?", (call_id,)).fetchone()
                if effect is not None:
                    effect_state = "adopted" if envelope.status == "available" else "refused"
                    conn.execute(
                        """UPDATE tool_turn_effect_children SET state=?,adopted_receipt_id=?,result_sha256=?,disposition=?
                           WHERE id=? AND state='reserved'""",
                        (effect_state, receipt if effect_state == "adopted" else "", result_hash, disposition, effect["id"]),
                    )
                terminal = envelope.status == "indeterminate"
                if terminal:
                    self._terminalize(conn, row, "indeterminate", "effect_indeterminate" if effect is not None else "tool_indeterminate", "", now)
                else:
                    conn.execute("UPDATE tool_turns SET state='tool_receipted',revision=revision+1,updated_at=? WHERE turn_id=?", (now, turn))
                    self._transition(conn, turn, str(row["state"]), "tool_receipted", disposition, {"tool_call_id": call_id, "receipt_id": receipt, "envelope": envelope.__dict__}, now)
                call = conn.execute("SELECT * FROM tool_turn_tool_calls WHERE id=?", (call_id,)).fetchone()
                result = self._tool_call_projection(call)
                self._command(conn, command, turn, "reconcile", request_hash, result, now)
                conn.commit()
                return result
            except Exception:
                conn.rollback()
                raise

    def ordered_tool_results(self, principal: Principal, *, turn_id: str) -> dict[str, Any]:
        """Return durable continuation material in provider-call ordinal order.

        Completion/receipt timing is intentionally absent from this projection.
        A caller stages these exact rows into the next frozen model-step request;
        a fallback deployment therefore sees the same bytes in the same order.
        """
        self._require_authority(principal)
        turn = _safe(turn_id, field="turn_id")
        with self._db._connection() as conn:
            self._turn_row(conn, turn)
            rows = conn.execute(
                """SELECT c.provider_tool_ordinal,c.provider_tool_call_id,c.capability_id,
                          c.capability_revision,c.state,c.disposition,
                          r.envelope_json,r.result_material_json,r.result_material_sha256
                     FROM tool_turn_tool_calls c
                     JOIN tool_turn_tool_call_results r ON r.tool_call_id=c.id
                    WHERE c.turn_id=?
                    ORDER BY c.provider_tool_ordinal""",
                (turn,),
            ).fetchall()
        results: list[dict[str, Any]] = []
        for row in rows:
            try:
                envelope = json.loads(str(row["envelope_json"]))
                material_json = str(row["result_material_json"])
                material = None if not material_json else json.loads(material_json)
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ToolTurnRefused("tool_result_continuation_integrity_invalid") from exc
            if str(envelope.get("status") or "") != str(row["disposition"]):
                raise ToolTurnRefused("tool_result_continuation_integrity_invalid")
            if material is not None and sha256(material) != str(row["result_material_sha256"]):
                raise ToolTurnRefused("tool_result_continuation_integrity_invalid")
            results.append({
                "provider_call_ordinal": int(row["provider_tool_ordinal"]),
                "provider_tool_call_id": str(row["provider_tool_call_id"]),
                "capability_id": str(row["capability_id"]),
                "capability_revision": int(row["capability_revision"]),
                # Receipt identity remains private ledger evidence.  It cannot
                # enter provider material, or identical read results completed in
                # another order would receive different random child IDs.
                "status": str(row["state"]),
                "envelope": envelope,
                "result": material,
            })
        return {"schema": "ToolTurnOrderedToolResults@1", "turn_id": turn, "tool_results": results}

    def reconcile_effect_child(self, principal: Principal, *, turn_id: str, tool_call_id: str) -> dict[str, Any]:
        """Restart truth: adopt a known effect receipt once, otherwise terminalize."""
        self._require_authority(principal)
        if self._tool_broker is None:
            raise ToolTurnRefused("tool_turn_broker_composition_missing")
        turn, call_id = _safe(turn_id, field="turn_id"), _safe(tool_call_id, field="tool_call_id")
        with self._db._connection() as conn:
            effect = conn.execute(
                "SELECT e.*,c.broker_child_id FROM tool_turn_effect_children e JOIN tool_turn_tool_calls c ON c.id=e.tool_call_id WHERE e.turn_id=? AND e.tool_call_id=?",
                (turn, call_id),
            ).fetchone()
            if effect is None:
                raise ToolTurnRefused("effect_child_not_found")
            if str(effect["state"]) == "adopted":
                return {"schema": "ToolTurnEffectReconciliation@1", "turn_id": turn, "tool_call_id": call_id, "state": "adopted", "replayed": True}
            child_id = str(effect["broker_child_id"])
        receipt = self._tool_broker.receipt(child_id)
        if receipt is not None:
            receipt_id = _safe(receipt.get("receipt_id"), field="receipt_id")
            result = {"receipt_ref": receipt_id}
            settled = self.settle_tool_call(
                principal, command_id=f"reconcile-effect-{call_id}", turn_id=turn, tool_call_id=call_id,
                receipt_id=receipt_id, envelope=ToolResultEnvelope.available(result), result_material=result,
            )
            return {"schema": "ToolTurnEffectReconciliation@1", "turn_id": turn, "tool_call_id": call_id, "state": "adopted", "tool_call": settled}
        now = float(self._clock())
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = self._turn_row(conn, turn)
                conn.execute("UPDATE tool_turn_effect_children SET state='indeterminate',disposition='effect_indeterminate' WHERE tool_call_id=? AND state='reserved'", (call_id,))
                self._terminalize(conn, row, "indeterminate", "effect_indeterminate", "", now)
                conn.commit()
                return {"schema": "ToolTurnEffectReconciliation@1", "turn_id": turn, "tool_call_id": call_id, "state": "indeterminate"}
            except Exception:
                conn.rollback()
                raise

    def request_stop(self, principal: Principal, *, command_id: str, turn_id: str, provenance_ref: str) -> dict[str, Any]:
        self._require_authority(principal)
        command, turn, provenance = _safe(command_id, field="command_id"), _safe(turn_id, field="turn_id"), _safe(provenance_ref, field="provenance_ref")
        request = {"schema": "ToolTurnStop@1", "turn_id": turn, "provenance_ref": provenance}
        request_hash, now = sha256(request), float(self._clock())
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                replay = conn.execute("SELECT * FROM tool_turn_commands WHERE command_id=?", (command,)).fetchone()
                if replay is not None:
                    if str(replay["kind"]) != "stop" or str(replay["request_sha256"]) != request_hash:
                        raise ToolTurnConflict("stop command changed")
                    result = self._turn_projection(conn, turn)
                    conn.commit()
                    return {**result, "replayed": True}
                row = self._turn_row(conn, turn)
                if str(row["state"]) not in _TERMINAL:
                    self._terminalize(conn, row, "stopped", "owner_cancelled", provenance, now)
                result = self._turn_projection(conn, turn)
                self._command(conn, command, turn, "stop", request_hash, result, now)
                conn.commit()
                return result
            except Exception:
                conn.rollback()
                raise

    def revoke_lease(self, principal: Principal, *, command_id: str, turn_id: str, epoch: int, code: str = "lease_revoked") -> dict[str, Any]:
        self._require_authority(principal)
        command, turn, revocation = _safe(command_id, field="command_id"), _safe(turn_id, field="turn_id"), _safe(code, field="revocation_code")
        expected_epoch = _int(epoch, field="epoch", minimum=1, maximum=1_000_000)
        request = {"schema": "ToolTurnRevoke@1", "turn_id": turn, "epoch": expected_epoch, "code": revocation}
        request_hash, now = sha256(request), float(self._clock())
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                replay = conn.execute("SELECT * FROM tool_turn_commands WHERE command_id=?", (command,)).fetchone()
                if replay is not None:
                    if str(replay["kind"]) != "revoke" or str(replay["request_sha256"]) != request_hash:
                        raise ToolTurnConflict("revoke command changed")
                    result = self._turn_projection(conn, turn)
                    conn.commit()
                    return {**result, "replayed": True}
                row = self._turn_row(conn, turn)
                lease_row = conn.execute("SELECT * FROM turn_capability_leases WHERE lease_id=?", (row["lease_id"],)).fetchone()
                if lease_row is None or int(lease_row["epoch"]) != expected_epoch:
                    raise ToolTurnRefused("lease_epoch_mismatch")
                conn.execute("UPDATE turn_capability_leases SET state='revoked',revoked_at=?,revocation_code=? WHERE lease_id=? AND state='active'", (now, revocation, row["lease_id"]))
                if str(row["state"]) not in _TERMINAL:
                    self._terminalize(conn, row, "failed", revocation, "", now)
                result = self._turn_projection(conn, turn)
                self._command(conn, command, turn, "revoke", request_hash, result, now)
                conn.commit()
                return result
            except Exception:
                conn.rollback()
                raise

    def receipt(self, principal: Principal, *, turn_id: str) -> dict[str, Any]:
        """Return the owner-safe private receipt graph without lease authority.

        This is intentionally an internal service result: it names separately
        admitted model/tool/effect children and their receipts, but never exposes
        nonce, lease terms, provider dialect payloads, MCP fields, or owner
        transport credentials.
        """
        self._require_authority(principal)
        turn = _safe(turn_id, field="turn_id")
        with self._db._connection() as conn:
            row = self._turn_row(conn, turn)
            steps = conn.execute(
                """SELECT ordinal,id,route_execution_id,state,child_receipt_id,result_sha256
                     FROM tool_turn_model_steps WHERE turn_id=? ORDER BY ordinal""",
                (turn,),
            ).fetchall()
            calls = conn.execute(
                """SELECT c.tool_ordinal,c.provider_tool_ordinal,c.capability_id,c.state,
                          c.broker_child_id,c.receipt_id,c.disposition,e.state AS effect_state,
                          e.adopted_receipt_id AS effect_receipt_id,e.disposition AS effect_disposition
                     FROM tool_turn_tool_calls c
                     LEFT JOIN tool_turn_effect_children e ON e.tool_call_id=c.id
                    WHERE c.turn_id=? ORDER BY c.tool_ordinal""",
                (turn,),
            ).fetchall()
        return {
            "schema": "ToolTurnReceipt@1",
            "turn_id": turn,
            "state": str(row["state"]),
            "terminal_code": str(row["terminal_code"]),
            "final_result_ref": str(row["final_result_ref"]),
            "route_plan_id": str(row["route_plan_id"]),
            "route_plan_sha256": str(row["route_plan_sha256"]),
            "model_steps": [{
                "ordinal": int(item["ordinal"]), "model_step_id": str(item["id"]),
                "route_execution_id": str(item["route_execution_id"]),
                "state": str(item["state"]), "receipt_id": str(item["child_receipt_id"]),
                "result_sha256": str(item["result_sha256"]),
            } for item in steps],
            "tool_calls": [{
                "tool_ordinal": int(item["tool_ordinal"]),
                "provider_tool_ordinal": int(item["provider_tool_ordinal"]),
                "capability_id": str(item["capability_id"]), "state": str(item["state"]),
                "broker_child_id": str(item["broker_child_id"]),
                "receipt_id": str(item["receipt_id"]), "disposition": str(item["disposition"]),
                "effect": None if item["effect_state"] is None else {
                    "state": str(item["effect_state"]),
                    "receipt_id": str(item["effect_receipt_id"]),
                    "disposition": str(item["effect_disposition"]),
                },
            } for item in calls],
        }

    def reconstruct(self, principal: Principal, *, turn_id: str) -> dict[str, Any]:
        """Verify persisted terms only; never rebuild authority from mutable state."""
        self._require_authority(principal)
        turn = _safe(turn_id, field="turn_id")
        now = float(self._clock())
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = self._turn_row(conn, turn)
                try:
                    lease = self._load_lease(conn, row)
                except (ToolTurnError, ToolCapabilityError, TypeError, ValueError, json.JSONDecodeError):
                    if str(row["state"]) not in _TERMINAL:
                        self._terminalize(conn, row, "indeterminate", "lease_terms_integrity_invalid", "", now)
                    conn.commit()
                    raise ToolTurnRefused("lease_terms_integrity_invalid")
                if now >= float(lease.terms["expires_at"]) or now >= float(lease.terms["wall_deadline"]):
                    if str(row["state"]) not in _TERMINAL:
                        self._expire(conn, row, now)
                    conn.commit()
                    raise ToolTurnRefused("lease_expired")
                pending_effect = None
                if self._tool_broker is not None and str(row["state"]) not in _TERMINAL:
                    pending_effect = conn.execute(
                        "SELECT tool_call_id FROM tool_turn_effect_children WHERE turn_id=? AND state='reserved' ORDER BY created_at LIMIT 1",
                        (turn,),
                    ).fetchone()
                result = self._turn_projection(conn, turn)
                conn.commit()
                if pending_effect is not None:
                    # Restart never guesses whether a dispatched effect ran: known
                    # kernel receipt adopts exactly once; absence elects the turn's
                    # terminal indeterminate winner before any later model step.
                    self.reconcile_effect_child(
                        principal, turn_id=turn, tool_call_id=str(pending_effect["tool_call_id"])
                    )
                    return self.reconstruct(principal, turn_id=turn)
                return result
            except Exception:
                if conn.in_transaction:
                    conn.rollback()
                raise

    def sync_projection(self, *_args: Any, **_kwargs: Any) -> None:
        raise ToolTurnRefused("tool_turn_sync_forbidden")

    def _validate_projection(self, lease: TurnCapabilityLease) -> None:
        for item in lease.terms["capabilities"]:
            try:
                descriptor = self._projection.require(item["capability_id"])
            except ToolCapabilityError as exc:
                raise ToolTurnRefused("capability_not_eligible_for_model_turn") from exc
            exact = (
                descriptor.revision == item["capability_revision"]
                and descriptor.descriptor_sha256 == item["descriptor_sha256"]
                and descriptor.schema_sha256 == item["schema_sha256"]
                and descriptor.service_operation == item["service_operation"]
                and descriptor.capability_class == item["class"]
                and descriptor.effect_mode == item["effect_mode"]
            )
            if not exact:
                raise ToolTurnRefused("capability_descriptor_mismatch")
            if not set(item["data_classes"]).issubset(descriptor.allowed_data_classes) or not set(item["placement"]).issubset(descriptor.allowed_placements) or not set(item["egress"]).issubset(descriptor.allowed_egress):
                raise ToolTurnRefused("capability_scope_expansion")
            if item["max_calls"] > descriptor.max_calls or item["max_result_bytes"] > descriptor.max_result_bytes or item["max_result_tokens"] > descriptor.max_result_tokens or item["commutative_read"] and not descriptor.commutative_read:
                raise ToolTurnRefused("capability_budget_expansion")
            if item["effect_mode"] == "execute_if_policy_admits" and lease.terms["owner_intent_receipt_id"] is None:
                raise ToolTurnRefused("owner_intent_receipt_required")

    def _validate_tool_candidate(
        self, lease: TurnCapabilityLease, candidate: ToolCallCandidate
    ) -> tuple[CanonicalApplicationOperationDescriptor, Mapping[str, Any]]:
        """Fail closed on confusables, descriptor drift, and non-closed arguments."""
        try:
            descriptor = self._projection.require(candidate.capability_id)
        except ToolCapabilityError as exc:
            raise ToolTurnRefused("capability_not_leased") from exc
        term = lease.capability(candidate.capability_id)
        if (
            descriptor.revision != int(term["capability_revision"])
            or descriptor.descriptor_sha256 != str(term["descriptor_sha256"])
            or descriptor.schema_sha256 != str(term["schema_sha256"])
            or descriptor.service_operation != str(term["service_operation"])
        ):
            raise ToolTurnRefused("capability_schema_or_descriptor_drift")
        try:
            normalized = validate_closed_arguments(descriptor.argument_schema, candidate.arguments)
        except ToolCapabilityError as exc:
            raise ToolTurnRefused("tool_call_arguments_schema_invalid") from exc
        if sha256(normalized) != candidate.canonical_args_sha256:
            raise ToolTurnRefused("tool_call_argument_hash_invalid")
        return descriptor, term

    @staticmethod
    def _budgets(lease: TurnCapabilityLease) -> dict[str, Any]:
        fields = (
            "max_provider_steps", "max_tool_calls", "max_effect_proposals", "max_parallel_reads",
            "aggregate_result_bytes", "aggregate_result_tokens", "wall_deadline", "expires_at",
        )
        return {"schema": "ToolTurnBudgets@1", **{field: lease.terms[field] for field in fields}}

    def _verify_parent_bundle(self, conn: Any, *, parent: str, bundle: str, route: str, route_hash: str) -> None:
        row = conn.execute(
            """SELECT p.kind,b.parent_operation_id,m.route_plan_id,m.route_plan_sha256,r.sha256 AS actual_route_sha256
                 FROM inference_parent_route_bundles b
                 JOIN kernel_parent_runs p ON p.operation_id=b.parent_operation_id
                 JOIN inference_parent_route_bundle_members m ON m.bundle_id=b.id
                 JOIN inference_route_plans r ON r.id=m.route_plan_id
                WHERE b.id=? AND b.parent_operation_id=? AND m.route_plan_id=?""",
            (bundle, parent, route),
        ).fetchone()
        if row is None or str(row["kind"]) != "tool.turn":
            raise ToolTurnRefused("tool_turn_parent_bundle_invalid")
        if str(row["route_plan_sha256"]) != route_hash or str(row["actual_route_sha256"]) != route_hash:
            raise ToolTurnRefused("tool_turn_route_integrity_invalid")

    def _turn_row(self, conn: Any, turn: str) -> Any:
        row = conn.execute("SELECT * FROM tool_turns WHERE turn_id=?", (turn,)).fetchone()
        if row is None:
            raise ToolTurnRefused("tool_turn_not_found")
        return row

    def _load_lease(self, conn: Any, turn: Any) -> TurnCapabilityLease:
        lease_row = conn.execute("SELECT * FROM turn_capability_leases WHERE lease_id=?", (turn["lease_id"],)).fetchone()
        if lease_row is None:
            raise ToolTurnError("lease row is missing")
        parsed = TurnCapabilityLease.parse(json.loads(str(lease_row["terms_json"])))
        if (
            parsed.terms_sha256 != str(lease_row["terms_sha256"])
            or parsed.terms_sha256 != str(turn["lease_sha256"])
            or parsed.terms["lease_id"] != str(turn["lease_id"])
            or parsed.terms["parent_turn_id"] != str(turn["turn_id"])
            or sha256({"nonce": parsed.terms["nonce"]}) != str(lease_row["nonce_sha256"])
            or parsed.terms["epoch"] != int(lease_row["epoch"])
        ):
            raise ToolTurnError("lease row hash binding is invalid")
        return parsed

    def _live_turn(self, conn: Any, turn: str, now: float) -> tuple[Any, TurnCapabilityLease]:
        row = self._turn_row(conn, turn)
        if str(row["state"]) in _TERMINAL:
            raise ToolTurnRefused("tool_turn_terminal")
        try:
            lease = self._load_lease(conn, row)
        except (ToolTurnError, ToolCapabilityError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._terminalize(conn, row, "indeterminate", "lease_terms_integrity_invalid", "", now)
            raise ToolTurnRefused("lease_terms_integrity_invalid") from exc
        lease_row = conn.execute("SELECT state FROM turn_capability_leases WHERE lease_id=?", (row["lease_id"],)).fetchone()
        if lease_row is None or str(lease_row["state"]) == "revoked":
            self._terminalize(conn, row, "failed", "lease_revoked", "", now)
            raise ToolTurnRefused("lease_revoked")
        if now >= float(lease.terms["expires_at"]) or now >= float(lease.terms["wall_deadline"]):
            self._expire(conn, row, now)
            raise ToolTurnRefused("lease_expired")
        return row, lease

    def _expire(self, conn: Any, row: Any, now: float) -> None:
        conn.execute("UPDATE turn_capability_leases SET state='expired' WHERE lease_id=? AND state='active'", (row["lease_id"],))
        self._terminalize(conn, row, "failed", "lease_expired", "", now)

    def _terminalize(
        self, conn: Any, row: Any, state: str, code: str, provenance: str,
        now: float, *, final_result_ref: str = "",
    ) -> None:
        current = str(row["state"])
        if current in _TERMINAL:
            return
        changed = conn.execute(
            """UPDATE tool_turns SET state=?,terminal_code=?,final_result_ref=?,stop_provenance_ref=?,revision=revision+1,updated_at=?
                 WHERE turn_id=? AND state=?""",
            (state, code, final_result_ref, provenance, now, row["turn_id"], current),
        ).rowcount
        if changed == 1:
            self._transition(conn, str(row["turn_id"]), current, state, code, {"provenance": provenance}, now)
            conn.execute("UPDATE turn_capability_leases SET state='terminal' WHERE lease_id=? AND state='active'", (row["lease_id"],))

    @staticmethod
    def _command(conn: Any, command: str, turn: str, kind: str, request_hash: str, result: Mapping[str, Any], now: float) -> None:
        conn.execute(
            "INSERT INTO tool_turn_commands (command_id,turn_id,kind,request_sha256,result_sha256,created_at) VALUES (?,?,?,?,?,?)",
            (command, turn, kind, request_hash, sha256(result), now),
        )

    @staticmethod
    def _transition(conn: Any, turn: str, from_state: str, to_state: str, code: str, evidence: Any, now: float) -> None:
        ordinal = int(conn.execute("SELECT COALESCE(MAX(ordinal),0)+1 FROM tool_turn_transitions WHERE turn_id=?", (turn,)).fetchone()[0])
        conn.execute(
            "INSERT INTO tool_turn_transitions (id,turn_id,ordinal,from_state,to_state,code,evidence_sha256,created_at) VALUES (?,?,?,?,?,?,?,?)",
            ("ttt_" + uuid.uuid4().hex, turn, ordinal, from_state, to_state, code, sha256(evidence), now),
        )

    def _turn_projection(self, conn: Any, turn: str) -> dict[str, Any]:
        row = self._turn_row(conn, turn)
        return {
            "schema": "ToolTurnProjection@1", "turn_id": str(row["turn_id"]),
            "parent_operation_id": str(row["parent_operation_id"]), "route_plan_id": str(row["route_plan_id"]),
            "route_plan_sha256": str(row["route_plan_sha256"]), "lease_sha256": str(row["lease_sha256"]),
            "state": str(row["state"]), "terminal_code": str(row["terminal_code"]),
            "deadline_at": float(row["deadline_at"]),
        }

    @staticmethod
    def _model_step_projection(row: Any) -> dict[str, Any]:
        return {
            "schema": "ToolTurnModelStepReservation@1", "id": str(row["id"]), "turn_id": str(row["turn_id"]),
            "ordinal": int(row["ordinal"]), "operation_request_plan_id": str(row["operation_request_plan_id"]),
            "operation_request_plan_sha256": str(row["operation_request_plan_sha256"]),
            "route_execution_id": str(row["route_execution_id"]),
            "lease_sha256": str(row["lease_sha256"]), "state": str(row["state"]),
            "child_receipt_id": str(row["child_receipt_id"]),
            "result_sha256": str(row["result_sha256"]),
        }

    @staticmethod
    def _tool_call_projection(row: Any) -> dict[str, Any]:
        return {
            "schema": "ToolTurnToolCallReservation@1", "id": str(row["id"]), "turn_id": str(row["turn_id"]),
            "tool_ordinal": int(row["tool_ordinal"]), "provider_tool_ordinal": int(row["provider_tool_ordinal"]),
            "provider_tool_call_id": str(row["provider_tool_call_id"]), "capability_id": str(row["capability_id"]),
            "capability_revision": int(row["capability_revision"]), "lease_sha256": str(row["lease_sha256"]),
            "canonical_args_sha256": str(row["canonical_args_sha256"]), "state": str(row["state"]),
        }


__all__ = [
    "BrokerToolCallPort", "MODEL_TURN_TOOL_PRINCIPAL", "TOOL_TURN_AUTHORITY",
    "ToolCallBrokerPort", "ToolTurnConflict", "ToolTurnController", "ToolTurnError",
    "ToolTurnRefused", "TurnCapabilityLease",
]
