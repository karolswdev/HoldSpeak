"""Durable private ToolTurn reservation authority (HS-143-09 A2).

The controller owns leases, terminal election and tool/model reservation only.
It never constructs a provider request, calls a provider, or invokes a tool
service; later slices compose its rows with InferenceFallbackController and the
Broker's separately admitted children.
"""
from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from ..principals import Principal, PrincipalKind
from .tool_capability_service import (
    ModelTurnCapabilityProjection,
    ToolCapabilityError,
    canonical_json,
    sha256,
)


TOOL_TURN_AUTHORITY = Principal(
    PrincipalKind.SERVICE,
    "tool-turn-controller",
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
        if normalized["max_effect_proposals"] and not any(item["capability_class"] == "effect_proposal" for item in normalized_capabilities):
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
    ) -> None:
        if not isinstance(projection, ModelTurnCapabilityProjection):
            raise ToolTurnError("MODEL_TURN projection is required")
        self._db = db
        self._projection = projection
        self._clock = clock

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
    ) -> dict[str, Any]:
        """Atomically reserve a frozen worst-case tool slot before Broker admission."""
        self._require_authority(principal)
        command, turn = _safe(command_id, field="command_id"), _safe(turn_id, field="turn_id")
        provider_id = _safe(provider_tool_call_id, field="provider_tool_call_id")
        capability = _safe(capability_id, field="capability_id")
        revision = _int(capability_revision, field="capability_revision", minimum=1, maximum=1_000_000)
        args = _json(arguments, field="arguments")
        args_hash = sha256(args)
        request = {
            "schema": "ToolTurnReserveToolCall@1", "turn_id": turn,
            "provider_tool_call_id": provider_id, "capability_id": capability,
            "capability_revision": revision, "canonical_args_sha256": args_hash,
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
                        str(existing["capability_id"]) == capability
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
                call_id = "ttc_" + uuid.uuid4().hex
                conn.execute(
                    """INSERT INTO tool_turn_tool_calls
                       (id,turn_id,tool_ordinal,provider_tool_ordinal,provider_tool_call_id,capability_id,
                        capability_revision,lease_sha256,canonical_args_sha256,reserved_result_bytes,
                        reserved_result_tokens,reserved_effects,state,created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (call_id, turn, ordinal, ordinal, provider_id, capability, revision, turn_row["lease_sha256"],
                     args_hash, term["max_result_bytes"], term["max_result_tokens"], reserved_effects,
                     "reserved", now, now),
                )
                result = self._tool_call_projection(conn.execute("SELECT * FROM tool_turn_tool_calls WHERE id=?", (call_id,)).fetchone())
                self._command(conn, command, turn, "reserve_tool_call", request_hash, result, now)
                self._transition(conn, turn, str(turn_row["state"]), "tool_requested", "tool_call_reserved", result, now)
                conn.execute("UPDATE tool_turns SET state='tool_requested',revision=revision+1,updated_at=? WHERE turn_id=?", (now, turn))
                conn.commit()
                return result
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
                result = self._turn_projection(conn, turn)
                conn.commit()
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

    def _terminalize(self, conn: Any, row: Any, state: str, code: str, provenance: str, now: float) -> None:
        current = str(row["state"])
        if current in _TERMINAL:
            return
        changed = conn.execute(
            """UPDATE tool_turns SET state=?,terminal_code=?,stop_provenance_ref=?,revision=revision+1,updated_at=?
                 WHERE turn_id=? AND state=?""",
            (state, code, provenance, now, row["turn_id"], current),
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
            "lease_sha256": str(row["lease_sha256"]), "state": str(row["state"]),
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
    "TOOL_TURN_AUTHORITY", "ToolTurnConflict", "ToolTurnController", "ToolTurnError",
    "ToolTurnRefused", "TurnCapabilityLease",
]
