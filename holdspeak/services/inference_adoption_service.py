"""Production adopters for Phase 143 routed inference (HS-143-07).

This module is the application side of the Story-05/06 waist.  Owners submit
one canonical, typed material snapshot; the route planner calls the registered
provider *inside the route-freeze transaction* with the exact resolved legs.
The provider serializes and budgets those legs, and the fallback controller is
the only component subsequently allowed to select a physical attempt.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

from ..deployment_revisions import DeploymentRevision
from ..inference_capabilities import (
    InferenceCapabilityRegistry,
    _validate_result_value,
    process_inference_capability_registry,
)
from ..kernel.inference_runner import InvocationRequest, ServiceContract
from ..principals import Principal, PrincipalKind
from .errors import ConflictError, ServiceError, ValidationError
from .inference_assignment_service import InferenceAssignmentService
from .model_profile_service import ModelProfileService
from .inference_fallback_controller import (
    INFERENCE_FALLBACK_AUTHORITY,
    InferenceFallbackController,
)
from .inference_route_plan_service import (
    ROUTE_PLANNING_AUTHORITY,
    InferenceRoutePlanService,
    RouteAdmissionEvidenceProvider,
)


ADOPTED_CAPABILITIES = (
    "thought.interview",
    "ask.answer",
    "speech.intent_classify",
    "speech.rewrite",
    "speech.punctuate",
    # Phase B uses the same private material/evidence provider for the frozen
    # Meeting bundle.  `speech.preload` is internally derived, but it still
    # needs exact reconstructed operation and attempt-budget evidence.
    "meeting.live_analysis",
    "meeting.deferred_analysis",
    "meeting.bookmark_label",
    "meeting.auto_title",
    "speech.transcribe",
    "speech.preload",
    "background.rails_summary",
    # Phase E OWNER request-time drafts share the frozen route/controller waist.
    # They are deliberately not SERVICE policies or scheduler work.
    "background.cadence_draft",
    "decision.promotion_draft",
    "delivery.pr_review_draft",
    # C2 plugin membership comes only from the composed registry.  The closed
    # evidence provider must nevertheless list every installed exact capability
    # before a frozen bundle child may stage its private material.
    *tuple(
        capability_id
        for capability_id in process_inference_capability_registry().capability_ids
        if capability_id.startswith("meeting.plugin.")
    ),
)
EXECUTING_CAPABILITIES = tuple(
    value for value in ADOPTED_CAPABILITIES if value != "speech.punctuate"
)
EVIDENCE_PROVIDER_ID = "phase143-production-adopters"
EVIDENCE_PROVIDER_REVISION = 1
TOKEN_ACCOUNTING_REVISION = "utf8-byte-upper-bound@1"
MIGRATION_FAMILY = "thoughts-writing-route-assignments"
MEETING_MIGRATION_FAMILY = "meeting-route-assignments"
MEETING_DEFERRED_MIGRATION_FAMILY = "meeting-deferred-route-assignments"
SPEECH_RECOGNITION_MIGRATION_FAMILY = "speech-recognition-route-assignments"
RAILS_OBSERVER_MIGRATION_FAMILY = "rails-observer-route-assignments"
MEETING_ASSIGNMENT_CAPABILITIES = (
    "meeting.live_analysis",
    "meeting.bookmark_label",
    "meeting.auto_title",
)

# The legacy selector has no general repository/path authority.  This closed
# map is the complete set of historically shipped local Whisper selectors that
# can become v2 Model Library authority without guessing or egress.
_LOCAL_WHISPER_ARTIFACTS = {
    (backend, model): f"builtin-whisper-{backend}-{model}"
    for backend in ("mlx", "faster-whisper")
    for model in ("tiny", "base", "small", "medium", "large")
}


def _canonical(value: Any) -> str:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            "Inference material must be canonical JSON.",
            code="inference_adoption_material_invalid",
        ) from exc


def _sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode()).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _safe(value: Any, *, field: str) -> str:
    clean = str(value or "").strip()
    if (
        not clean
        or len(clean) > 192
        or not clean[0].isalnum()
        or any(not (character.isalnum() or character in "._:-") for character in clean)
    ):
        raise ValidationError(
            f"{field} is invalid", code="inference_adoption_material_invalid"
        )
    return clean


def _input_token_upper_bound(serialized: str) -> int:
    """Deterministic reservation, never a claim about provider token usage.

    Every token in supported text tokenizers is backed by at least one UTF-8
    byte.  Reserving ceil(bytes/3) would not be conservative for arbitrary
    Unicode, so the v1 law reserves one token per byte plus a fixed envelope.
    The deliberately explicit revision lets a future tokenizer-aware law coexist
    with historical evidence without reinterpretation.
    """
    return len(serialized.encode("utf-8")) + 16


class ProductionRouteEvidence:
    """Durable private evidence owner for production adopted capabilities."""

    def __init__(
        self,
        db: Any,
        *,
        registry: InferenceCapabilityRegistry | None = None,
    ) -> None:
        self._db = db
        self._registry = registry or process_inference_capability_registry()
        self._plans: InferenceRoutePlanService | None = None

    def bind_route_plan_service(self, plans: InferenceRoutePlanService) -> None:
        self._plans = plans

    def provider(self) -> RouteAdmissionEvidenceProvider:
        definitions = tuple(self._registry.require(value) for value in EXECUTING_CAPABILITIES)
        return RouteAdmissionEvidenceProvider(
            id=EVIDENCE_PROVIDER_ID,
            revision=EVIDENCE_PROVIDER_REVISION,
            capabilities=tuple(
                (item.id, item.revision, item.schema_sha256) for item in definitions
            ),
            operation_policy_revisions=tuple(
                f"{item.operation_contract.name}@{item.operation_contract.version}:{item.schema_sha256}"
                for item in definitions
            ),
            freeze=self._unresolved_freeze,
            freeze_resolved=self.freeze_resolved,
            reconstruct=self.reconstruct,
            reconstruct_attempt_budgets=self.reconstruct_attempt_budgets,
        )

    @staticmethod
    def _unresolved_freeze(
        _conn: Any, _planning_reference: str, _operation_id: str
    ) -> Mapping[str, Any]:
        raise ServiceError(
            "inference_adoption_resolved_route_required",
            "Production evidence requires the exact resolved route snapshot",
        )

    def stage(
        self,
        *,
        planning_reference: str,
        capability_id: str,
        operation_id: str,
        contract: str,
        contract_revision: str,
        payload: Mapping[str, Any],
        reserved_output_tokens: int,
        reserved_tool_calls: int = 0,
        _connection: Any | None = None,
    ) -> dict[str, Any]:
        reference = _safe(planning_reference, field="planning_reference")
        operation = _safe(operation_id, field="operation_id")
        capability = self._registry.require(capability_id)
        if capability.id not in EXECUTING_CAPABILITIES:
            raise ValidationError(
                "Capability has no selected provider-backed execution stage.",
                code="inference_adoption_capability_non_executing",
            )
        expected_contract = capability.operation_contract.name
        if contract != expected_contract or str(contract_revision) != str(
            capability.operation_contract.version
        ):
            raise ValidationError(
                "Operation contract does not match the capability.",
                code="inference_adoption_contract_mismatch",
            )
        if (
            type(reserved_output_tokens) is not int
            or reserved_output_tokens < 0
            or type(reserved_tool_calls) is not int
            or reserved_tool_calls < 0
        ):
            raise ValidationError(
                "Attempt budgets are invalid.",
                code="inference_adoption_budget_invalid",
            )
        if reserved_tool_calls:
            raise ValidationError(
                "Story 07 operations cannot reserve tools.",
                code="inference_adoption_tool_budget_forbidden",
            )
        payload_value = dict(payload)
        payload_json = _canonical(payload_value)
        payload_sha = _sha256(payload_value)
        material = {
            "schema": "AdoptedInferenceMaterial@1",
            "planning_reference": reference,
            "capability_id": capability.id,
            "capability_revision": capability.revision,
            "capability_schema_sha256": capability.schema_sha256,
            "operation_id": operation,
            "contract": contract,
            "contract_revision": str(contract_revision),
            "payload_sha256": payload_sha,
            "reserved_output_tokens": reserved_output_tokens,
            "reserved_tool_calls": reserved_tool_calls,
            "token_accounting_revision": TOKEN_ACCOUNTING_REVISION,
        }
        material_sha = _sha256(material)
        if _connection is not None:
            return self._stage_in_conn(
                _connection, reference=reference, capability_id=capability.id,
                operation=operation, contract=contract,
                contract_revision=str(contract_revision), payload_json=payload_json,
                payload_sha=payload_sha, material=material, material_sha=material_sha,
                reserved_output_tokens=reserved_output_tokens,
                reserved_tool_calls=reserved_tool_calls,
            )
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                result = self._stage_in_conn(
                    conn, reference=reference, capability_id=capability.id,
                    operation=operation, contract=contract,
                    contract_revision=str(contract_revision), payload_json=payload_json,
                    payload_sha=payload_sha, material=material, material_sha=material_sha,
                    reserved_output_tokens=reserved_output_tokens,
                    reserved_tool_calls=reserved_tool_calls,
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return result

    @staticmethod
    def _stage_in_conn(
        conn: Any,
        *,
        reference: str,
        capability_id: str,
        operation: str,
        contract: str,
        contract_revision: str,
        payload_json: str,
        payload_sha: str,
        material: Mapping[str, Any],
        material_sha: str,
        reserved_output_tokens: int,
        reserved_tool_calls: int,
    ) -> dict[str, Any]:
        existing = conn.execute(
            "SELECT * FROM inference_adoption_material_snapshots WHERE planning_reference=?",
            (reference,),
        ).fetchone()
        if existing is not None:
            if (
                str(existing["capability_id"]) != capability_id
                or str(existing["operation_id"]) != operation
                or str(existing["contract"]) != contract
                or str(existing["contract_revision"]) != contract_revision
                or str(existing["payload_json"]) != payload_json
                or str(existing["payload_sha256"]) != payload_sha
                or str(existing["material_snapshot_sha256"]) != material_sha
                or int(existing["reserved_output_tokens"]) != reserved_output_tokens
                or int(existing["reserved_tool_calls"]) != reserved_tool_calls
            ):
                raise ConflictError(
                    "Planning reference was reused with different material.",
                    code="inference_adoption_material_conflict",
                )
            return {**material, "material_snapshot_sha256": material_sha}
        conn.execute(
            "INSERT INTO inference_adoption_material_snapshots VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (reference, capability_id, operation, contract, contract_revision,
             payload_json, payload_sha, material_sha, reserved_output_tokens,
             reserved_tool_calls, _now()),
        )
        return {**material, "material_snapshot_sha256": material_sha}

    def freeze_resolved(
        self,
        conn: Any,
        planning_reference: str,
        operation_id: str,
        route: Mapping[str, Any],
        preflight: Sequence[Mapping[str, Any]],
    ) -> Mapping[str, Any]:
        row = conn.execute(
            "SELECT * FROM inference_adoption_material_snapshots WHERE planning_reference=?",
            (planning_reference,),
        ).fetchone()
        if row is None or str(row["operation_id"]) != operation_id:
            raise ConflictError(
                "Adoption material is missing or cross-bound.",
                code="inference_adoption_material_invalid",
            )
        capability_id = str(row["capability_id"])
        if capability_id != str(route["capability"]["id"]):
            raise ConflictError(
                "Adoption material names another capability.",
                code="inference_adoption_material_invalid",
            )
        try:
            payload = json.loads(str(row["payload_json"]))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ConflictError(
                "Adoption material cannot be reconstructed.",
                code="inference_adoption_material_invalid",
            ) from exc
        if _sha256(payload) != str(row["payload_sha256"]):
            raise ConflictError(
                "Adoption material changed.", code="inference_adoption_material_invalid"
            )
        evidence_ref = "iae_" + hashlib.sha256(
            f"{planning_reference}:{route['sha256']}".encode()
        ).hexdigest()[:32]
        entries: list[dict[str, Any]] = []
        budgets: list[dict[str, Any]] = []
        serialized_requests: list[dict[str, Any]] = []
        output_tokens = int(row["reserved_output_tokens"])
        for ordinal, (leg, availability) in enumerate(
            zip(route["entries"], preflight), 1
        ):
            serialized = {
                "schema": "AdoptedSerializedRequest@1",
                "capability_id": capability_id,
                "operation_id": operation_id,
                "contract": str(row["contract"]),
                "contract_revision": str(row["contract_revision"]),
                "deployment_revision": str(leg["deployment_revision_id"]),
                "payload": payload,
            }
            serialized_json = _canonical(serialized)
            input_tokens = _input_token_upper_bound(serialized_json)
            maximum = int(leg["context_support"]["maximum_tokens"])
            eligibility = str(availability["eligibility"])
            reason = availability.get("reason_code")
            if eligibility == "executable" and input_tokens + output_tokens > maximum:
                eligibility, reason = "known_context_overflow", "context_overflow"
            executable = eligibility == "executable"
            request_id = f"request:{evidence_ref}:{ordinal}" if executable else None
            context_plan = {
                "schema": "AdoptedContextPlan@1",
                "token_accounting_revision": TOKEN_ACCOUNTING_REVISION,
                "input_tokens": input_tokens,
                "reserved_output_tokens": output_tokens,
                "context_ceiling": maximum,
                "payload_sha256": str(row["payload_sha256"]),
                "deployment_revision_id": str(leg["deployment_revision_id"]),
            }
            request_sha = _sha256(
                {"id": request_id, "serialized_request": serialized}
            ) if executable else None
            context_sha = _sha256(context_plan) if executable else None
            serialized_sha = _sha256(serialized) if executable else None
            entries.append(
                {
                    "route_leg_ordinal": ordinal,
                    "eligibility": eligibility,
                    "reason_code": None if executable else str(reason),
                    "admitted_request_id": request_id,
                    "admitted_request_sha256": request_sha,
                    "context_plan_sha256": context_sha,
                    "serialized_request_sha256": serialized_sha,
                }
            )
            budgets.append(
                {
                    "route_leg_ordinal": ordinal,
                    "admitted_request_id": request_id,
                    "admitted_request_sha256": request_sha,
                    "context_plan_sha256": context_sha,
                    "serialized_request_sha256": serialized_sha,
                    "input_tokens": input_tokens if executable else 0,
                    "reserved_output_tokens": output_tokens if executable else 0,
                    "total_tokens": input_tokens + output_tokens if executable else 0,
                    "reserved_cost_units": 0,
                    "reserved_tool_calls": int(row["reserved_tool_calls"]) if executable else 0,
                }
            )
            serialized_requests.append(
                {
                    "route_leg_ordinal": ordinal,
                    "serialized_request": serialized if executable else None,
                    "context_plan": context_plan,
                }
            )
        evidence = {
            "schema": "ProductionRouteAdmissionEvidence@1",
            "evidence_ref": evidence_ref,
            "planning_reference": planning_reference,
            "operation_id": operation_id,
            "capability_id": capability_id,
            "material_snapshot_sha256": str(row["material_snapshot_sha256"]),
            "route_plan_id": str(route["id"]),
            "route_plan_sha256": str(route["sha256"]),
            "entries": entries,
            "budgets": budgets,
            "serialized_requests": serialized_requests,
        }
        evidence_json = _canonical(evidence)
        evidence_sha = _sha256(evidence)
        existing = conn.execute(
            "SELECT * FROM inference_adoption_route_evidence WHERE evidence_ref=?",
            (evidence_ref,),
        ).fetchone()
        if existing is not None:
            if (
                str(existing["planning_reference"]) != planning_reference
                or str(existing["operation_id"]) != operation_id
                or str(existing["evidence_json"]) != evidence_json
                or str(existing["evidence_sha256"]) != evidence_sha
            ):
                raise ConflictError(
                    "Stored adoption evidence changed.",
                    code="inference_adoption_evidence_invalid",
                )
        else:
            conn.execute(
                "INSERT INTO inference_adoption_route_evidence VALUES (?,?,?,?,?,?,?,?)",
                (
                    evidence_ref, planning_reference, operation_id, capability_id,
                    row["material_snapshot_sha256"], evidence_json, evidence_sha, _now(),
                ),
            )
        return {
            "evidence_ref": evidence_ref,
            "material_snapshot_sha256": str(row["material_snapshot_sha256"]),
            "entries": entries,
        }

    def _evidence(self, conn: Any, evidence_ref: str) -> dict[str, Any]:
        row = conn.execute(
            "SELECT * FROM inference_adoption_route_evidence WHERE evidence_ref=?",
            (evidence_ref,),
        ).fetchone()
        if row is None:
            raise ConflictError(
                "Adoption evidence is missing.", code="inference_adoption_evidence_invalid"
            )
        try:
            evidence = json.loads(str(row["evidence_json"]))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ConflictError(
                "Adoption evidence cannot be reconstructed.",
                code="inference_adoption_evidence_invalid",
            ) from exc
        expected_keys = {
            "schema", "evidence_ref", "planning_reference", "operation_id",
            "capability_id", "material_snapshot_sha256", "route_plan_id",
            "route_plan_sha256", "entries", "budgets", "serialized_requests",
        }
        if (
            str(row["evidence_sha256"]) != _sha256(evidence)
            or set(evidence) != expected_keys
            or evidence.get("evidence_ref") != evidence_ref
            or evidence.get("schema") != "ProductionRouteAdmissionEvidence@1"
            or evidence.get("planning_reference") != str(row["planning_reference"])
            or evidence.get("operation_id") != str(row["operation_id"])
            or evidence.get("capability_id") != str(row["capability_id"])
            or evidence.get("material_snapshot_sha256")
            != str(row["material_snapshot_sha256"])
        ):
            raise ConflictError(
                "Adoption evidence changed.", code="inference_adoption_evidence_invalid"
            )
        material = conn.execute(
            "SELECT * FROM inference_adoption_material_snapshots WHERE planning_reference=?",
            (evidence["planning_reference"],),
        ).fetchone()
        route = conn.execute(
            "SELECT id,sha256,capability_id FROM inference_route_plans WHERE id=?",
            (evidence["route_plan_id"],),
        ).fetchone()
        if material is None:
            raise ConflictError(
                "Adoption evidence is cross-bound.", code="inference_adoption_evidence_invalid"
            )
        try:
            payload = json.loads(str(material["payload_json"]))
            route_entries = [dict(value) for value in conn.execute(
                """SELECT e.route_leg_ordinal,e.deployment_revision_id,
                          e.profile_schema_version,
                          e.context_support_json,d.context_ceiling,
                          p.eligibility AS frozen_eligibility,
                          p.reason_code AS frozen_reason_code
                     FROM inference_route_plan_entries e
                     JOIN deployment_revisions d ON d.id=e.deployment_revision_id
                     JOIN inference_route_plan_preflight_evidence p
                       ON p.plan_id=e.plan_id
                      AND p.route_leg_ordinal=e.route_leg_ordinal
                    WHERE e.plan_id=? ORDER BY e.route_leg_ordinal""",
                (evidence["route_plan_id"],),
            ).fetchall()]
            if route is None:
                # One-shot freeze asks the provider to reconstruct budgets
                # before inserting its route rows, under the same write lock.
                # Dispatch reconstruction after commit always takes the strict
                # persisted-route branch above.
                route_entries = [
                    {
                        "route_leg_ordinal": request["route_leg_ordinal"],
                        "deployment_revision_id": request["context_plan"]["deployment_revision_id"],
                        "profile_schema_version": 2,
                        "context_support_json": _canonical(
                            {
                                "mode": "bounded",
                                "maximum_tokens": request["context_plan"]["context_ceiling"],
                            }
                        ),
                        "context_ceiling": request["context_plan"]["context_ceiling"],
                        "frozen_eligibility": entry["eligibility"],
                        "frozen_reason_code": entry["reason_code"],
                    }
                    for entry, request in zip(
                        evidence["entries"], evidence["serialized_requests"]
                    )
                ]
        except (TypeError, ValueError, json.JSONDecodeError):
            raise ConflictError(
                "Adoption evidence cannot be reconstructed.",
                code="inference_adoption_evidence_invalid",
            ) from None
        if route is None:
            capability = self._registry.require(str(material["capability_id"]))
            capability_id = capability.id
            capability_revision = capability.revision
            capability_schema_sha256 = capability.schema_sha256
        elif self._plans is None:
            raise ConflictError(
                "Frozen route authority is unavailable.",
                code="inference_adoption_evidence_invalid",
            )
        else:
            definition = self._plans.frozen_capability_definition_in_transaction(
                ROUTE_PLANNING_AUTHORITY, conn, route_plan_id=str(route["id"])
            )
            capability_id = str(definition["id"])
            capability_revision = int(definition["revision"])
            capability_schema_sha256 = str(definition["schema_sha256"])
        material_snapshot = {
            "schema": "AdoptedInferenceMaterial@1",
            "planning_reference": str(material["planning_reference"]),
            "capability_id": capability_id,
            "capability_revision": capability_revision,
            "capability_schema_sha256": capability_schema_sha256,
            "operation_id": str(material["operation_id"]),
            "contract": str(material["contract"]),
            "contract_revision": str(material["contract_revision"]),
            "payload_sha256": str(material["payload_sha256"]),
            "reserved_output_tokens": int(material["reserved_output_tokens"]),
            "reserved_tool_calls": int(material["reserved_tool_calls"]),
            "token_accounting_revision": TOKEN_ACCOUNTING_REVISION,
        }
        if (
            str(material["operation_id"]) != evidence["operation_id"]
            or str(material["capability_id"]) != evidence["capability_id"]
            or str(material["material_snapshot_sha256"]) != evidence["material_snapshot_sha256"]
            or _sha256(payload) != str(material["payload_sha256"])
            or _sha256(material_snapshot) != str(material["material_snapshot_sha256"])
            or (route is not None and str(route["sha256"]) != evidence["route_plan_sha256"])
            or (route is not None and str(route["capability_id"]) != evidence["capability_id"])
            or not isinstance(route_entries, list)
        ):
            raise ConflictError(
                "Adoption evidence is cross-bound.", code="inference_adoption_evidence_invalid"
            )
        entries = evidence["entries"]
        budgets = evidence["budgets"]
        requests = evidence["serialized_requests"]
        if not all(isinstance(value, list) for value in (entries, budgets, requests)) or not (
            len(entries) == len(budgets) == len(requests) == len(route_entries)
        ):
            raise ConflictError(
                "Adoption evidence cardinality changed.", code="inference_adoption_evidence_invalid"
            )
        for ordinal, (entry, budget, request, leg) in enumerate(
            zip(entries, budgets, requests, route_entries), 1
        ):
            if (
                not isinstance(entry, dict)
                or set(entry) != {"route_leg_ordinal", "eligibility", "reason_code", "admitted_request_id", "admitted_request_sha256", "context_plan_sha256", "serialized_request_sha256"}
                or not isinstance(budget, dict)
                or set(budget) != {"route_leg_ordinal", "admitted_request_id", "admitted_request_sha256", "context_plan_sha256", "serialized_request_sha256", "input_tokens", "reserved_output_tokens", "total_tokens", "reserved_cost_units", "reserved_tool_calls"}
                or not isinstance(request, dict)
                or set(request) != {"route_leg_ordinal", "serialized_request", "context_plan"}
                or not isinstance(request.get("context_plan"), dict)
                or set(request["context_plan"]) != {"schema", "token_accounting_revision", "input_tokens", "reserved_output_tokens", "context_ceiling", "payload_sha256", "deployment_revision_id"}
                or any(type(budget[name]) is not int or budget[name] < 0 for name in ("input_tokens", "reserved_output_tokens", "total_tokens", "reserved_cost_units", "reserved_tool_calls"))
            ):
                raise ConflictError("Adoption evidence shape changed.", code="inference_adoption_evidence_invalid")
            if any(int(value.get("route_leg_ordinal", 0)) != ordinal for value in (entry, budget, request)):
                raise ConflictError(
                    "Adoption evidence ordinals changed.", code="inference_adoption_evidence_invalid"
                )
            serialized = request.get("serialized_request")
            context = request.get("context_plan")
            expected_serialized = {
                "schema": "AdoptedSerializedRequest@1",
                "capability_id": evidence["capability_id"],
                "operation_id": evidence["operation_id"],
                "contract": str(material["contract"]),
                "contract_revision": str(material["contract_revision"]),
                "deployment_revision": str(leg["deployment_revision_id"]),
                "payload": payload,
            }
            input_tokens = _input_token_upper_bound(_canonical(expected_serialized))
            context_support = json.loads(str(leg["context_support_json"]))
            maximum = int(context_support["maximum_tokens"])
            if (
                int(leg["profile_schema_version"]) == 2
                and maximum != int(leg["context_ceiling"] or 0)
            ):
                raise ConflictError(
                    "Route context evidence changed.", code="inference_adoption_evidence_invalid"
                )
            eligibility = str(leg["frozen_eligibility"])
            reason = leg["frozen_reason_code"]
            output_tokens = int(material["reserved_output_tokens"])
            if eligibility == "executable" and input_tokens + output_tokens > maximum:
                eligibility, reason = "known_context_overflow", "context_overflow"
            executable = eligibility == "executable"
            request_id = f"request:{evidence_ref}:{ordinal}" if executable else None
            expected_context = {
                "schema": "AdoptedContextPlan@1",
                "token_accounting_revision": TOKEN_ACCOUNTING_REVISION,
                "input_tokens": input_tokens,
                "reserved_output_tokens": output_tokens,
                "context_ceiling": maximum,
                "payload_sha256": str(material["payload_sha256"]),
                "deployment_revision_id": str(leg["deployment_revision_id"]),
            }
            expected_request_sha = (
                _sha256({"id": request_id, "serialized_request": expected_serialized})
                if executable else None
            )
            expected_context_sha = _sha256(expected_context) if executable else None
            expected_serialized_sha = _sha256(expected_serialized) if executable else None
            expected_entry = {
                "route_leg_ordinal": ordinal,
                "eligibility": eligibility,
                "reason_code": None if executable else str(reason),
                "admitted_request_id": request_id,
                "admitted_request_sha256": expected_request_sha,
                "context_plan_sha256": expected_context_sha,
                "serialized_request_sha256": expected_serialized_sha,
            }
            expected_budget = {
                "route_leg_ordinal": ordinal,
                "admitted_request_id": request_id,
                "admitted_request_sha256": expected_request_sha,
                "context_plan_sha256": expected_context_sha,
                "serialized_request_sha256": expected_serialized_sha,
                "input_tokens": input_tokens if executable else 0,
                "reserved_output_tokens": output_tokens if executable else 0,
                "total_tokens": input_tokens + output_tokens if executable else 0,
                "reserved_cost_units": 0,
                "reserved_tool_calls": int(material["reserved_tool_calls"]) if executable else 0,
            }
            if entry != expected_entry or budget != expected_budget or context != expected_context:
                raise ConflictError(
                    "Adoption context or budget changed.",
                    code="inference_adoption_evidence_invalid",
                )
            if executable:
                if (
                    serialized != expected_serialized
                ):
                    raise ConflictError(
                        "Adoption request bytes changed.", code="inference_adoption_evidence_invalid"
                    )
            elif serialized is not None:
                raise ConflictError(
                    "An unavailable route gained request bytes.", code="inference_adoption_evidence_invalid"
                )
            elif (
                any(entry[name] is not None for name in ("admitted_request_id", "admitted_request_sha256", "context_plan_sha256", "serialized_request_sha256"))
                or any(budget[name] is not None for name in ("admitted_request_id", "admitted_request_sha256", "context_plan_sha256", "serialized_request_sha256"))
                or any(budget[name] != 0 for name in ("input_tokens", "reserved_output_tokens", "total_tokens", "reserved_cost_units", "reserved_tool_calls"))
            ):
                raise ConflictError("Unavailable evidence changed.", code="inference_adoption_evidence_invalid")
        return evidence

    def reconstruct(self, conn: Any, evidence_ref: str) -> Mapping[str, Any]:
        evidence = self._evidence(conn, evidence_ref)
        return {
            "evidence_ref": evidence_ref,
            "material_snapshot_sha256": evidence["material_snapshot_sha256"],
            "entries": evidence["entries"],
        }

    def reconstruct_attempt_budgets(
        self, conn: Any, evidence_ref: str
    ) -> Mapping[str, Any]:
        evidence = self._evidence(conn, evidence_ref)
        return {
            "schema": "RouteAttemptBudgetEvidence@1",
            "evidence_ref": evidence_ref,
            "material_snapshot_sha256": evidence["material_snapshot_sha256"],
            "entries": evidence["budgets"],
        }

    def serialized_request(self, evidence_ref: str, ordinal: int) -> dict[str, Any]:
        with self._db._connection() as conn:
            evidence = self._evidence(conn, evidence_ref)
        if type(ordinal) is not int or not 1 <= ordinal <= len(
            evidence["serialized_requests"]
        ):
            raise ValidationError(
                "Route leg is invalid.", code="inference_adoption_route_leg_invalid"
            )
        entry = evidence["serialized_requests"][ordinal - 1]
        serialized = entry["serialized_request"]
        if serialized is None:
            raise ValidationError(
                "Route leg is unavailable.", code="inference_adoption_route_leg_unavailable"
            )
        return dict(serialized)


class RoutedInferenceCoordinator:
    """Compose production evidence, frozen plans, controller, and Runner."""

    def __init__(
        self,
        db: Any,
        *,
        broker: Any | None = None,
        registry: InferenceCapabilityRegistry | None = None,
    ) -> None:
        self._db = db
        self._registry = registry or process_inference_capability_registry()
        self.evidence = ProductionRouteEvidence(db, registry=self._registry)
        self.plans = InferenceRoutePlanService(
            db,
            registry=self._registry,
            operation_evidence_providers=(self.evidence.provider(),),
        )
        self.evidence.bind_route_plan_service(self.plans)
        self._broker = broker
        self.controller = InferenceFallbackController(
            db,
            route_plan_service=self.plans,
            kernel_child_reader=None if broker is None else broker.reconstruct_claimed_inference_child,
            kernel_receipt_reader=None if broker is None else broker.reconstruct_inference_child_receipt,
        )

    def admit(
        self,
        principal: Principal,
        *,
        command_id: str,
        capability_id: str,
        operation_id: str,
        payload: Mapping[str, Any],
        invocation_id: str | None = None,
        subject_kind: str | None = None,
        subject_id: str | None = None,
        reserved_output_tokens: int = 512,
    ) -> dict[str, Any]:
        if principal.kind is not PrincipalKind.OWNER:
            raise ValidationError(
                "Owner authority is required.", code="inference_adoption_owner_required"
            )
        capability = self._registry.require(capability_id)
        operation = _safe(operation_id, field="operation_id")
        reference = "iam_" + hashlib.sha256(
            f"{command_id}:{operation}:{_sha256(dict(payload))}".encode()
        ).hexdigest()[:32]
        route_request: dict[str, Any] = {"capability_id": capability.id}
        if invocation_id:
            route_request["invocation_id"] = _safe(invocation_id, field="invocation_id")
        if subject_kind or subject_id:
            route_request.update(subject_kind=subject_kind, subject_id=subject_id)
        command = _safe(command_id, field="command_id")
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                result = self._admit_in_conn(
                    conn, command=command, capability=capability,
                    operation=operation, payload=payload,
                    reserved_output_tokens=reserved_output_tokens,
                    reference=reference, route_request=route_request,
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return result

    def _admit_in_conn(
        self,
        conn: Any,
        *,
        command: str,
        capability: Any,
        operation: str,
        payload: Mapping[str, Any],
        reserved_output_tokens: int,
        reference: str,
        route_request: Mapping[str, Any],
    ) -> dict[str, Any]:
        self.evidence.stage(
            planning_reference=reference, capability_id=capability.id,
            operation_id=operation, contract=capability.operation_contract.name,
            contract_revision=str(capability.operation_contract.version),
            payload=payload, reserved_output_tokens=reserved_output_tokens,
            _connection=conn,
        )
        frozen = self.plans._freeze_one_shot_in_transaction(
            ROUTE_PLANNING_AUTHORITY, conn, command_id=command,
            route_request=route_request, operation_id=operation,
            planning_reference=reference,
        )
        execution = self.controller.start_execution_in_transaction(
            INFERENCE_FALLBACK_AUTHORITY, conn, command_id=f"start-{command}",
            operation_plan_id=frozen["operation_request_plan"]["id"],
        )
        return {**frozen, "execution": execution}

    def admit_in_transaction(
        self,
        principal: Principal,
        conn: Any,
        *,
        command_id: str,
        capability_id: str,
        operation_id: str,
        payload: Mapping[str, Any],
        invocation_id: str | None = None,
        reserved_output_tokens: int = 512,
    ) -> dict[str, Any]:
        """Bind an adopter's logical reservation to route+controller atomically."""
        if principal.kind is not PrincipalKind.OWNER:
            raise ValidationError("Owner authority is required.", code="inference_adoption_owner_required")
        capability = self._registry.require(capability_id)
        command, operation = _safe(command_id, field="command_id"), _safe(operation_id, field="operation_id")
        reference = "iam_" + hashlib.sha256(
            f"{command}:{operation}:{_sha256(dict(payload))}".encode()
        ).hexdigest()[:32]
        route_request: dict[str, Any] = {"capability_id": capability.id}
        if invocation_id:
            route_request["invocation_id"] = _safe(invocation_id, field="invocation_id")
        return self._admit_in_conn(
            conn, command=command, capability=capability, operation=operation,
            payload=payload, reserved_output_tokens=reserved_output_tokens,
            reference=reference, route_request=route_request,
        )

    def admit_composite(
        self,
        principal: Principal,
        *,
        command_id: str,
        operations: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Atomically reserve every constituent route/execution or none."""
        if principal.kind is not PrincipalKind.OWNER:
            raise ValidationError(
                "Owner authority is required.", code="inference_adoption_owner_required"
            )
        command = _safe(command_id, field="command_id")
        if not operations or len(operations) > 5:
            raise ValidationError(
                "Composite operations are invalid.",
                code="inference_adoption_composite_invalid",
            )
        request = [dict(value) for value in operations]
        request_sha = _sha256(request)
        for item in request:
            required = {"capability_id", "operation_id", "payload"}
            if set(item) - (required | {"reserved_output_tokens", "invocation_id", "subject_kind", "subject_id"}) or not required.issubset(item):
                raise ValidationError(
                    "Composite operation has an invalid shape.",
                    code="inference_adoption_composite_invalid",
                )
        composite_id = "iac_" + hashlib.sha256(
            f"{command}:{request_sha}".encode()
        ).hexdigest()[:32]
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                existing = conn.execute(
                    "SELECT * FROM inference_adoption_composites WHERE command_id=?",
                    (command,),
                ).fetchone()
                if existing is not None:
                    if str(existing["request_sha256"]) != request_sha:
                        raise ConflictError("Composite command changed.", code="inference_adoption_composite_conflict")
                    operation_plan_ids = json.loads(str(existing["operation_plan_ids_json"]))
                    result = {"schema": "InferenceAdoptionComposite@1", "id": str(existing["composite_id"]), "operation_plan_ids": operation_plan_ids}
                    if str(existing["result_sha256"]) != _sha256(result):
                        raise ConflictError("Composite evidence changed.", code="inference_adoption_composite_integrity_invalid")
                    conn.commit()
                    return result
                admitted = []
                for ordinal, item in enumerate(request, 1):
                    capability = self._registry.require(str(item["capability_id"]))
                    operation = _safe(item["operation_id"], field="operation_id")
                    subcommand = f"{command}-{ordinal}"
                    reference = "iam_" + hashlib.sha256(
                        f"{subcommand}:{operation}:{_sha256(dict(item['payload']))}".encode()
                    ).hexdigest()[:32]
                    route_request: dict[str, Any] = {"capability_id": capability.id}
                    for name in ("invocation_id", "subject_kind", "subject_id"):
                        if item.get(name):
                            route_request[name] = item[name]
                    admitted.append(self._admit_in_conn(
                        conn, command=subcommand, capability=capability,
                        operation=operation, payload=dict(item["payload"]),
                        reserved_output_tokens=int(item.get("reserved_output_tokens", 512)),
                        reference=reference, route_request=route_request,
                    ))
                operation_plan_ids = [value["operation_request_plan"]["id"] for value in admitted]
                result = {"schema": "InferenceAdoptionComposite@1", "id": composite_id, "operation_plan_ids": operation_plan_ids}
                conn.execute(
                    "INSERT INTO inference_adoption_composites VALUES (?,?,?,?,?,?)",
                    (
                        composite_id, command, request_sha,
                        _canonical(operation_plan_ids), _sha256(result), _now(),
                    ),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return result

    def admit_on_frozen_route(
        self,
        principal: Principal,
        *,
        command_id: str,
        route_plan_id: str,
        capability_id: str,
        operation_id: str,
        payload: Mapping[str, Any],
        reserved_output_tokens: int,
        parent_operation_id: str | None = None,
        parentless_source_route_plan_id: str | None = None,
        executor_lease: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Atomically attach late operation material to a session-frozen route.

        OWNER callers retain the historical adoption surface.  A SERVICE caller is
        admitted only for the exact route member of its already-persisted parent
        bundle; it cannot borrow general OWNER route authority or invent a parent.
        """
        capability = self._registry.require(capability_id)
        command = _safe(command_id, field="command_id")
        operation = _safe(operation_id, field="operation_id")
        route_id = _safe(route_plan_id, field="route_plan_id")
        bound_parent = _safe(parent_operation_id, field="parent_operation_id") if parent_operation_id else ""
        source_route = (
            _safe(parentless_source_route_plan_id, field="parentless_source_route_plan_id")
            if parentless_source_route_plan_id
            else ""
        )
        if principal.kind is not PrincipalKind.OWNER and (
            principal.kind is not PrincipalKind.SERVICE or (not bound_parent and not source_route)
        ):
            raise ValidationError(
                "Frozen-route admission requires owner, bound service, or derived parentless preload authority.",
                code="inference_adoption_owner_required",
            )
        reference = "iam_" + hashlib.sha256(
            f"{command}:{operation}:{_sha256(dict(payload))}".encode()
        ).hexdigest()[:32]
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                if principal.kind is PrincipalKind.SERVICE:
                    if source_route:
                        self._validate_parentless_local_preload_route(
                            conn,
                            principal=principal,
                            route_plan_id=route_id,
                            source_route_plan_id=source_route,
                            capability_id=capability.id,
                        )
                    else:
                        member = conn.execute(
                            """SELECT p.state
                               FROM inference_parent_route_bundle_members m
                               JOIN inference_parent_route_bundles b ON b.id=m.bundle_id
                               JOIN kernel_parent_runs p ON p.operation_id=b.parent_operation_id
                               JOIN kernel_operations o ON o.operation_id=p.operation_id
                              WHERE m.route_plan_id=? AND m.capability_id=?
                                AND b.parent_operation_id=?
                                AND o.principal_kind=? AND o.principal_identity=?""",
                            (route_id, capability.id, bound_parent, principal.name, principal.identity),
                        ).fetchone()
                        # A closed parent may only replay the exact previously
                        # frozen operation.  It can never admit new material or
                        # use terminal membership as ambient SERVICE authority.
                        replay = None if member is None else conn.execute(
                            """SELECT 1 FROM inference_operation_route_request_plan_commands
                               WHERE command_id=? AND route_plan_id=?""",
                            (command, route_id),
                        ).fetchone()
                        if member is None or (str(member["state"]) != "OPEN" and replay is None):
                            raise ValidationError(
                                "Service route membership is required.",
                                code="inference_adoption_service_membership_required",
                            )
                if executor_lease is not None:
                    job_id = str(executor_lease.get("job_id") or "")
                    token = str(executor_lease.get("token") or "")
                    try:
                        epoch = int(executor_lease.get("epoch") or 0)
                    except (TypeError, ValueError):
                        epoch = 0
                    owner = conn.execute(
                        """SELECT 1 FROM intel_jobs WHERE job_id=? AND parent_operation_id=?
                           AND executor_lease_token=? AND executor_lease_epoch=?
                           AND status IN ('claimed','running')
                           AND executor_lease_expires_at>?""",
                        (job_id, bound_parent, token, epoch, time.time()),
                    ).fetchone()
                    if owner is None:
                        raise ValidationError(
                            "Bound queue executor lease is no longer current.",
                            code="inference_adoption_executor_lease_lost",
                        )
                self.evidence.stage(
                    planning_reference=reference,
                    capability_id=capability.id,
                    operation_id=operation,
                    contract=capability.operation_contract.name,
                    contract_revision=str(capability.operation_contract.version),
                    payload=payload,
                    reserved_output_tokens=int(reserved_output_tokens),
                    _connection=conn,
                )
                operation_plan = self.plans.freeze_operation_for_route_in_transaction(
                    ROUTE_PLANNING_AUTHORITY,
                    conn,
                    command_id=command,
                    route_plan_id=route_id,
                    operation_id=operation,
                    planning_reference=reference,
                )
                execution = self.controller.start_execution_in_transaction(
                    INFERENCE_FALLBACK_AUTHORITY,
                    conn,
                    command_id=f"start-{command}",
                    operation_plan_id=operation_plan["operation_request_plan"]["id"],
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return {**operation_plan, "execution": execution}

    @staticmethod
    def _validate_parentless_local_preload_route(
        conn: Any,
        *,
        principal: Principal,
        route_plan_id: str,
        source_route_plan_id: str,
        capability_id: str,
    ) -> None:
        """Validate the one closed SERVICE exception to parent membership.

        Parentless execution is deliberately unavailable to every other service.
        The derived preload route must copy exactly one capability-only owner
        transcription selection and preserve its deployment revision.
        """
        if (
            principal.identity != "local-model-preload"
            or principal.authority_basis != "local-model-preload:assigned-speech-route"
            or capability_id != "speech.preload"
        ):
            raise ValidationError(
                "Parentless local preload authority is invalid.",
                code="inference_adoption_service_membership_required",
            )
        route = conn.execute(
            """SELECT p.capability_id,p.assignment_id,p.assignment_revision,p.inherited_from,
                      e.deployment_revision_id,pe.payload_json
                   FROM inference_route_plans p
                   JOIN inference_route_plan_entries e ON e.plan_id=p.id
                   JOIN inference_route_plan_principal_evidence pe ON pe.plan_id=p.id
                  WHERE p.id=? AND e.route_leg_ordinal=1""",
            (route_plan_id,),
        ).fetchone()
        source = conn.execute(
            """SELECT p.capability_id,p.assignment_id,p.assignment_revision,p.inherited_from,
                      p.sha256,e.deployment_revision_id,pe.payload_json
                   FROM inference_route_plans p
                   JOIN inference_route_plan_entries e ON e.plan_id=p.id
                   JOIN inference_route_plan_principal_evidence pe ON pe.plan_id=p.id
                  WHERE p.id=? AND e.route_leg_ordinal=1""",
            (source_route_plan_id,),
        ).fetchone()
        if route is None or source is None:
            raise ValidationError(
                "Parentless preload evidence is invalid.",
                code="inference_adoption_service_membership_required",
            )
        try:
            preload_policy = json.loads(str(route["payload_json"]))
            source_policy = json.loads(str(source["payload_json"]))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValidationError(
                "Parentless preload evidence is invalid.",
                code="inference_adoption_service_membership_required",
            ) from exc
        if (
            str(route["capability_id"]) != "speech.preload"
            or str(source["capability_id"]) != "speech.transcribe"
            or str(route["assignment_id"]) != str(source["assignment_id"])
            or int(route["assignment_revision"]) != int(source["assignment_revision"])
            or str(source["inherited_from"]) != "capability"
            or str(route["deployment_revision_id"]) != str(source["deployment_revision_id"])
            or preload_policy.get("policy_id") != "local-model-preload@1"
            or preload_policy.get("principal_identity") != "local-model-preload"
            or preload_policy.get("authority_basis") != "local-model-preload:assigned-speech-route"
            or preload_policy.get("parent_kind") != "local-model-preload"
            or preload_policy.get("allowed_boundaries") != ["local"]
            or preload_policy.get("assignment_sources") != ["capability"]
            or source_policy.get("principal_kind") != "owner"
            or source_policy.get("assignment_sources") != ["capability"]
        ):
            raise ValidationError(
                "Parentless preload route is not derived from its speech assignment.",
                code="inference_adoption_service_membership_required",
            )

    def freeze_route_set(
        self,
        principal: Principal,
        *,
        command_id: str,
        routes: Sequence[Mapping[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Freeze a speech session's complete provider route set or none."""
        if principal.kind is not PrincipalKind.OWNER or not routes:
            raise ValidationError("Route set is invalid.", code="inference_adoption_composite_invalid")
        command = _safe(command_id, field="command_id")
        frozen: dict[str, dict[str, Any]] = {}
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                for ordinal, raw in enumerate(routes, 1):
                    item = dict(raw)
                    if set(item) != {"key", "capability_id", "invocation_id"}:
                        raise ValidationError("Route set is invalid.", code="inference_adoption_composite_invalid")
                    key = _safe(item["key"], field="route_key")
                    frozen[key] = self.plans.freeze_route_plan_in_transaction(
                        ROUTE_PLANNING_AUTHORITY, conn,
                        command_id=f"{command}-{ordinal}",
                        capability_id=str(item["capability_id"]),
                        invocation_id=str(item["invocation_id"]),
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return frozen

    def _frozen_capability_definition(self, route_plan_id: str) -> dict[str, Any]:
        with self._db._connection() as conn:
            conn.execute("BEGIN")
            try:
                definition = self.plans.frozen_capability_definition_in_transaction(
                    ROUTE_PLANNING_AUTHORITY, conn, route_plan_id=route_plan_id
                )
            finally:
                conn.rollback()
        return definition

    @staticmethod
    def _validate_frozen_result(definition: Mapping[str, Any], value: Any) -> None:
        _validate_result_value(
            value,
            definition["output_schema"],
            field_name=f"result for {definition['id']}",
        )

    def _publish_winner_if_unstaged(
        self,
        publish: Callable[[Any, Mapping[str, Any]], str] | None,
        value: Any,
        winning: Mapping[str, Any],
    ) -> None:
        """Publish a durably elected winner once, including terminal replays."""
        if publish is None:
            return
        stager = getattr(self._broker, "projection_stager", None)
        stage_for = getattr(stager, "get", None)
        child_invocation_id = str(winning["child_invocation_id"])
        existing = stage_for(child_invocation_id) if callable(stage_for) else None
        # A stale C1 lease creates a deliberate DISCARDED stage. The successor
        # bearer may restage the already-earned child result; every other stage
        # remains immutable/idempotent as before.
        if existing is not None and str(getattr(existing, "state", "")) != "DISCARDED":
            return
        publish(value, winning)

    def execute(
        self,
        principal: Principal,
        *,
        execution_id: str,
        adapter: Any,
        publish: Callable[[Any, Mapping[str, Any]], str] | None = None,
        before_physical_dispatch: Callable[[str, str, int], None] | None = None,
        parent_context: Any = None,
    ) -> dict[str, Any]:
        if self._broker is None:
            raise ServiceError(
                "inference_adoption_runner_missing",
                "Production execution requires a composed broker",
            )
        runner = self._broker.inference_runner
        runtime = getattr(runner, "_routed_attempt_runtime", None)
        if runtime is None or getattr(runtime, "_controller", None) is not self.controller:
            raise ServiceError(
                "inference_adoption_runtime_misconfigured",
                "The process-owned routed runtime is not composed",
            )
        execution = self.controller._execution(None, execution_id)
        # Execution receipt reconstruction is controller-owned read authority.
        # A bound SERVICE parent may execute only its member (validated above),
        # but must not be asked to impersonate OWNER merely to inspect settlement.
        receipt_authority = INFERENCE_FALLBACK_AUTHORITY
        operation = self.plans.get_operation_request_plan(
            ROUTE_PLANNING_AUTHORITY, execution["operation_plan_id"]
        )
        route = self.plans.get_route_plan(
            ROUTE_PLANNING_AUTHORITY, operation["route_plan_id"]
        )
        frozen_definition = self._frozen_capability_definition(str(route["id"]))
        if execution["state"] in {"terminal", "stopped"}:
            receipt = self.controller.get_route_execution_receipt(
                receipt_authority, execution_id=execution_id
            )
            replay: dict[str, Any] = {
                "outcome": receipt["outcome"],
                "result": self._durable_winner_result(receipt),
                "receipt": receipt,
            }
            if receipt["outcome"] == "succeeded":
                winning = self._winning_reservation(
                    execution_id, str(receipt.get("winning_attempt_id") or "")
                )
                replay["winning_reservation"] = winning
                self._publish_winner_if_unstaged(publish, replay["result"], winning)
            return replay
        frozen_deadline = datetime.fromisoformat(
            str(route["deadline_at"]).replace("Z", "+00:00")
        ).timestamp()
        next_attempt = int(execution.get("attempts_reserved") or 0) + 1
        while True:
            effect = self.controller.reserve_next_attempt(
                INFERENCE_FALLBACK_AUTHORITY,
                command_id=f"reserve-{execution_id}-{next_attempt}",
                execution_id=execution_id,
            )
            next_attempt += 1
            reservation = effect["reservation"]
            if reservation is None:
                receipt = self.controller.get_route_execution_receipt(
                    receipt_authority, execution_id=execution_id
                )
                replay = {
                    "outcome": receipt["outcome"],
                    "result": self._durable_winner_result(receipt),
                    "receipt": receipt,
                }
                if receipt["outcome"] == "succeeded":
                    winning = self._winning_reservation(
                        execution_id, str(receipt.get("winning_attempt_id") or "")
                    )
                    replay["winning_reservation"] = winning
                    self._publish_winner_if_unstaged(publish, replay["result"], winning)
                return replay
            serialized = self.evidence.serialized_request(
                operation["admission_evidence_ref"],
                int(reservation["route_leg_ordinal"]),
            )
            payload = dict(serialized["payload"])
            captured: dict[str, Any] = {}

            def project(value: Any) -> str:
                try:
                    self._validate_frozen_result(frozen_definition, value)
                except Exception as exc:
                    from ..kernel.provider_signals import InferenceInvalidTypedOutput
                    raise InferenceInvalidTypedOutput() from exc
                captured["value"] = value
                result_json, result_sha = _canonical(value), _sha256(value)
                # Attempt output remains private until the controller has elected
                # this physical reservation.  The kernel receipt therefore names a
                # content-free private result reference; feature publication occurs
                # only after durable settlement below.
                producer_result_ref = (
                    f"inference-result:{reservation['child_invocation_id']}/{result_sha}"
                )
                with self._db._connection() as conn:
                    conn.execute("BEGIN IMMEDIATE")
                    prior = conn.execute(
                        "SELECT * FROM inference_adoption_attempt_results WHERE attempt_id=?",
                        (str(reservation["attempt_id"]),),
                    ).fetchone()
                    if prior is None:
                        conn.execute(
                            "INSERT INTO inference_adoption_attempt_results VALUES (?,?,?,?,?,?)",
                            (
                                str(reservation["attempt_id"]),
                                str(reservation["child_invocation_id"]),
                                producer_result_ref,
                                result_json,
                                result_sha,
                                _now(),
                            ),
                        )
                    elif (
                        str(prior["child_invocation_id"]) != str(reservation["child_invocation_id"])
                        or str(prior["producer_result_ref"]) != producer_result_ref
                        or str(prior["result_json"]) != result_json
                        or str(prior["result_sha256"]) != result_sha
                    ):
                        raise ConflictError("Attempt result changed.", code="inference_adoption_result_integrity_invalid")
                return producer_result_ref

            request = InvocationRequest(
                str(reservation["deployment_revision_id"]),
                ServiceContract.for_payload(
                    str(serialized["contract"]),
                    str(serialized["contract_revision"]),
                    payload,
                ),
                frozen_deadline,
                payload,
                str(reservation["child_invocation_id"]),
                parent_operation_id=str(
                    getattr(parent_context, "operation_id", "") or ""
                ),
                attempt_ordinal=int(reservation["physical_attempt_ordinal"]),
                route_attempt_reservation=reservation,
                before_physical_dispatch=before_physical_dispatch,
            )
            from ..kernel.runtime import _as_principal

            with _as_principal(principal):
                runner.invoke(
                    request, adapter, publish=project, parent_context=parent_context
                )
            receipt = self.controller.get_route_execution_receipt(
                receipt_authority, execution_id=execution_id
            )
            if receipt["outcome"] == "succeeded":
                winning = self._winning_reservation(
                    execution_id, str(receipt.get("winning_attempt_id") or "")
                )
                value = self._durable_winner_result(receipt)
                if value is None:
                    raise ConflictError(
                        "Winner result is missing.",
                        code="inference_adoption_result_integrity_invalid",
                    )
                # Publication is deliberately post-election.  A UI/materializer
                # failure cannot rewrite the already elected physical receipt, and
                # the terminal replay above recovers a stage that never committed.
                self._publish_winner_if_unstaged(publish, value, winning)
                return {
                    "outcome": "succeeded",
                    "result": value,
                    "receipt": receipt,
                    "winning_reservation": winning,
                }
            if receipt["state"] == "terminal":
                return {"outcome": receipt["outcome"], "result": None, "receipt": receipt}
            execution = self.controller._execution(None, execution_id)

    def recover_route_executions(
        self, *, execution_id: str | None = None, parent_operation_id: str | None = None,
    ) -> dict[str, int]:
        """Settle durable child receipts before projection-stage recovery.

        Startup reconciliation deliberately scans globally. A live C1 lease
        adopter instead supplies its one deterministic execution and parent, so
        recovering a stale Meeting can never terminalize another live Meeting's
        provider dispatch.
        """
        if self._broker is None:
            return {"settled": 0, "indeterminate": 0}
        if (execution_id is None) != (parent_operation_id is None):
            raise ValueError("scoped route recovery requires execution and parent identity")
        with self._db._connection() as conn:
            rows = conn.execute(
                """SELECT attempt.id,attempt.child_operation_id
                   FROM inference_route_attempts attempt
                   JOIN inference_route_executions execution ON execution.id=attempt.execution_id
                   JOIN kernel_operations child ON child.operation_id=attempt.child_operation_id
                   WHERE attempt.state='dispatch_intent'
                     AND (? IS NULL OR attempt.execution_id=?)
                     AND (? IS NULL OR child.parent_operation_id=?)
                   ORDER BY attempt.reserved_at,attempt.id""",
                (execution_id, execution_id, parent_operation_id, parent_operation_id),
            ).fetchall()
        settled = indeterminate = 0
        for row in rows:
            attempt_id = str(row["id"])
            operation_id = str(row["child_operation_id"] or "")
            receipt = self._broker.reconstruct_inference_child_receipt(operation_id) if operation_id else None
            if receipt is not None:
                self.controller._settle_runner_evidence(
                    INFERENCE_FALLBACK_AUTHORITY,
                    command_id=f"recover-settle-{attempt_id}", attempt_id=attempt_id,
                )
                settled += 1
            else:
                self.controller.reconcile_dispatch_intent(
                    INFERENCE_FALLBACK_AUTHORITY,
                    command_id=f"recover-indeterminate-{attempt_id}", attempt_id=attempt_id,
                )
                indeterminate += 1
        return {"settled": settled, "indeterminate": indeterminate}

    def _durable_winner_result(self, receipt: Mapping[str, Any]) -> Any:
        winner = str(receipt.get("winning_attempt_id") or "")
        if not winner:
            return None
        with self._db._connection() as conn:
            row = conn.execute(
                """SELECT ar.result_json,ar.result_sha256,ar.child_invocation_id,
                          ar.producer_result_ref,
                          ra.child_invocation_id expected_child,ra.result_ref,
                          kr.result_ref kernel_result_ref,rp.capability_id,
                          app.payload_json application_projection_json,
                          ks.projection_json staged_projection_json,
                          ks.projection_sha256 staged_projection_sha256,
                          ks.result_ref staged_result_ref,
                          rp.id route_plan_id
                     FROM inference_adoption_attempt_results ar
                     JOIN inference_route_attempts ra ON ra.id=ar.attempt_id
                     JOIN inference_route_executions re ON re.id=ra.execution_id
                     JOIN inference_route_plans rp ON rp.id=re.route_plan_id
                     JOIN kernel_receipts kr ON kr.operation_id=ra.child_operation_id
                     LEFT JOIN ask_results app ON app.operation_id=ra.child_operation_id
                     LEFT JOIN kernel_projection_stages ks
                       ON ks.operation_id=ra.child_operation_id AND ks.kind='ask-result'
                    WHERE ar.attempt_id=? AND re.winning_attempt_id=ar.attempt_id
                      AND re.state='terminal' AND re.terminal_outcome='succeeded'""",
                (winner,),
            ).fetchone()
        if row is None:
            return None
        try:
            value = json.loads(str(row["result_json"]))
        except (TypeError, ValueError, json.JSONDecodeError):
            raise ConflictError("Attempt result is invalid.", code="inference_adoption_result_integrity_invalid") from None
        if (
            _sha256(value) != str(row["result_sha256"])
            or str(row["child_invocation_id"]) != str(row["expected_child"])
            or str(row["producer_result_ref"]) != str(row["kernel_result_ref"])
            or str(row["result_ref"]) != str(row["kernel_result_ref"])
            or not str(row["kernel_result_ref"]).endswith(
                "/" + str(row["result_sha256"])
            )
        ):
            raise ConflictError("Attempt result changed.", code="inference_adoption_result_integrity_invalid")
        try:
            self._validate_frozen_result(
                self._frozen_capability_definition(str(row["route_plan_id"])), value
            )
        except Exception as exc:
            raise ConflictError("Attempt result contract changed.", code="inference_adoption_result_integrity_invalid") from exc
        projection: dict[str, Any] | None = None
        if str(row["kernel_result_ref"]).startswith("projection-stage:"):
            try:
                projection = json.loads(str(row["staged_projection_json"]))
                projected = json.loads(str(projection["output"])) if str(row["capability_id"]) == "thought.interview" else {"output": str(projection["output"])}
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                raise ConflictError("Attempt candidate is invalid.", code="inference_adoption_result_integrity_invalid") from None
            if (
                projected != value
                or _sha256(projection) != str(row["staged_projection_sha256"])
                or str(row["staged_result_ref"]) != str(row["kernel_result_ref"])
            ):
                raise ConflictError("Attempt result is cross-bound.", code="inference_adoption_result_integrity_invalid")
        if row["application_projection_json"] and projection is not None:
            published = json.loads(str(row["application_projection_json"]))
            if published.get("output") != projection.get("output"):
                raise ConflictError("Published result is cross-bound.", code="inference_adoption_result_integrity_invalid")
        return value

    def _winning_reservation(self, execution_id: str, attempt_id: str) -> dict[str, Any]:
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM inference_route_attempts WHERE id=? AND execution_id=?",
                (attempt_id, execution_id),
            ).fetchone()
        if row is None:
            raise ConflictError("Winning attempt is missing.", code="inference_adoption_result_integrity_invalid")
        reservation = dict(row)
        # Reservation effects expose this field as ``attempt_id``; preserve that
        # stable shape when a terminal receipt is replayed from durable storage.
        reservation["attempt_id"] = str(row["id"])
        return reservation

    def stop(
        self,
        principal: Principal,
        *,
        command_id: str,
        execution_id: str,
    ) -> dict[str, Any]:
        """Fence route advancement before signalling the exact physical child."""
        if principal.kind is not PrincipalKind.OWNER:
            raise ValidationError(
                "Owner authority is required.", code="inference_adoption_owner_required"
            )
        stopped = self.controller.request_stop(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=_safe(command_id, field="command_id"),
            execution_id=_safe(execution_id, field="execution_id"),
        )
        signalled = "not_dispatched"
        if self._broker is not None and stopped["execution"]["state"] == "stopping":
            with self._db._connection() as conn:
                row = conn.execute(
                    """SELECT child_invocation_id FROM inference_route_attempts
                       WHERE execution_id=? AND state='dispatch_intent'
                       ORDER BY physical_attempt_ordinal DESC LIMIT 1""",
                    (execution_id,),
                ).fetchone()
            if row is not None:
                from ..kernel.runtime import _as_principal

                with _as_principal(principal):
                    signalled = self._broker.inference_runner.cancel(
                        str(row["child_invocation_id"])
                    )
        return {**stopped, "child_signal": signalled}

    def stop_operation(
        self, principal: Principal, *, command_id: str, operation_id: str
    ) -> dict[str, Any]:
        """Stop the controller owning one logical adopted operation."""
        with self._db._connection() as conn:
            row = conn.execute(
                """SELECT e.id FROM inference_route_executions e
                   JOIN inference_operation_request_plans o ON o.id=e.operation_plan_id
                   WHERE o.operation_id=? ORDER BY e.created_at DESC LIMIT 1""",
                (_safe(operation_id, field="operation_id"),),
            ).fetchone()
        if row is None:
            return {"execution": {"state": "not_started"}, "child_signal": "not_dispatched"}
        return self.stop(
            principal, command_id=command_id, execution_id=str(row["id"])
        )

    def next_run_summary(
        self,
        principal: Principal,
        *,
        capability_id: str,
        invocation_id: str | None = None,
        subject_kind: str | None = None,
        subject_id: str | None = None,
    ) -> dict[str, Any]:
        if principal.kind is not PrincipalKind.OWNER:
            raise ValidationError(
                "Owner authority is required.", code="inference_adoption_owner_required"
            )
        try:
            capability = self._registry.require(capability_id)
            operation_policy = self.plans._operation_policy(capability, None)
            with self._db._connection() as conn:
                conn.execute("BEGIN")
                route, _revisions, preflight = self.plans._resolve_in_conn(
                    conn,
                    capability=capability,
                    operation_policy_revision=operation_policy,
                    invocation_id=invocation_id,
                    subject_kind=subject_kind,
                    subject_id=subject_id,
                    plan_id=None,
                )
                active_row = None
                if invocation_id:
                    active_row = conn.execute(
                        """SELECT e.id,e.state,e.terminal_outcome,e.winning_attempt_id,
                                  e.route_plan_id,e.operation_plan_id
                             FROM inference_route_executions e
                             JOIN inference_operation_route_request_plans o
                               ON o.id=e.operation_plan_id
                            WHERE o.operation_id=?
                            ORDER BY e.rowid DESC LIMIT 1""",
                        (invocation_id,),
                    ).fetchone()
                conn.rollback()
        except ServiceError as exc:
            repair = {
                "no_assignment": "choose_model",
                "no_compatible_assignment": "choose_compatible_model",
                "inference_route_profile_unavailable": "repair_model",
            }.get(exc.code, "review_model_setup")
            return {
                "schema": "InferenceNextRunSummary@1",
                "capability_id": capability_id,
                "status": "needs_attention",
                "repair": repair,
                "reason_code": exc.code,
                "chain": [],
                "active_execution": None,
            }
        executable = [item for item in preflight if item["eligibility"] == "executable"]
        reason = next(
            (str(item.get("reason_code") or "model_not_ready") for item in preflight
             if item["eligibility"] != "executable"),
            None,
        )
        repair = {
            "binding_disabled": "enable_model_binding",
            "binding_not_ready": "repair_model_readiness",
            "context_overflow": "choose_larger_context_model",
        }.get(reason or "", "review_model_setup") if not executable else None
        return {
            "schema": "InferenceNextRunSummary@1",
            "capability_id": capability_id,
            "status": "ready" if executable else "needs_attention",
            "repair": repair,
            "reason_code": None if executable else reason,
            "source": route["source"]["inherited_from"],
            "chain": [
                {
                    "ordinal": leg["ordinal"],
                    "profile_id": leg["profile_id"],
                    "profile_revision": leg["profile_revision"],
                    "boundary": leg["boundary"],
                    "context_tokens": leg["context_support"]["maximum_tokens"],
                    "eligibility": preflight[index]["eligibility"],
                    "reason_code": preflight[index].get("reason_code"),
                }
                for index, leg in enumerate(route["entries"])
            ],
            "active_execution": None if active_row is None else {
                "execution_id": str(active_row["id"]),
                "route_plan_id": str(active_row["route_plan_id"]),
                "operation_plan_id": str(active_row["operation_plan_id"]),
                "state": str(active_row["state"]),
                "terminal_outcome": active_row["terminal_outcome"],
                "winning_attempt_id": active_row["winning_attempt_id"],
                "frozen": True,
            },
        }

    def apply_next_run_override(
        self,
        principal: Principal,
        *,
        command_id: str,
        invocation_id: str,
        capability_id: str,
        entries: Sequence[Mapping[str, Any]],
        expected_revision: int = 0,
    ) -> dict[str, Any]:
        return InferenceAssignmentService(self._db, registry=self._registry).set_assignment(
            principal,
            {
                "command_id": command_id,
                "expected_revision": expected_revision,
                "scope": {
                    "kind": "invocation",
                    "invocation_id": invocation_id,
                    "capability_id": capability_id,
                },
                "entries": [dict(value) for value in entries],
            },
        )

    def migrate_meeting_route_assignments(
        self, principal: Principal, config: Any
    ) -> dict[str, Any]:
        """Copy the one saved Meeting profile pointer or return a repair issue.

        The legacy Meeting configuration has one persisted profile pointer, not a
        model artifact or endpoint.  A blank pointer therefore cannot lawfully be
        expanded into a local default or an auto/cloud chain.
        """
        assignments = InferenceAssignmentService(self._db, registry=self._registry)
        existing = assignments.migration_marker(
            principal, family=MEETING_MIGRATION_FAMILY
        )
        if existing is not None:
            return {**existing, "status": "migrated", "legacy_config_read": False}
        meeting = getattr(config, "meeting", None)
        profile_id = str(getattr(meeting, "intel_profile_id", "") or "").strip()
        provider = str(getattr(meeting, "intel_provider", "") or "").strip()
        source = {"intel_profile_id": profile_id, "intel_provider": provider}
        source_sha256 = _sha256(source)
        if not profile_id:
            return self._migration_issue(
                MEETING_MIGRATION_FAMILY,
                "builtin_profile_required",
                "choose_meeting_model_profile",
                source_sha256,
            )
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT MAX(revision) AS revision FROM model_profile_revisions WHERE profile_id=?",
                (profile_id,),
            ).fetchone()
        revision = int(row["revision"] or 0) if row is not None else 0
        if revision < 1:
            return self._migration_issue(
                MEETING_MIGRATION_FAMILY,
                "legacy_profile_requires_upgrade",
                "upgrade_model_profile",
                source_sha256,
            )
        try:
            marker = assignments.migrate_capability_assignments_atomically(
                principal,
                family=MEETING_MIGRATION_FAMILY,
                source_sha256=source_sha256,
                capability_entries={
                    capability_id: {
                        "profile_id": profile_id,
                        "profile_revision": revision,
                    }
                    for capability_id in MEETING_ASSIGNMENT_CAPABILITIES
                },
            )
        except ValidationError as exc:
            if exc.code != "inference_assignment_incompatible":
                raise
            return self._migration_issue(
                MEETING_MIGRATION_FAMILY,
                "legacy_profile_incompatible",
                "choose_compatible_meeting_model_profile",
                source_sha256,
            )
        return {**marker, "status": "migrated", "legacy_config_read": True}

    def migrate_meeting_deferred_route_assignments(
        self, principal: Principal, config: Any
    ) -> dict[str, Any]:
        """Copy the saved Meeting profile into the deferred queue's exact scope.

        This intentionally remains a separate marker family: databases that
        already completed the live Meeting migration must acquire this newly
        adopted deferred capability without re-reading or rewriting that family.
        It follows the same no-guess/refusal law as the live family.
        """
        assignments = InferenceAssignmentService(self._db, registry=self._registry)
        existing = assignments.migration_marker(
            principal, family=MEETING_DEFERRED_MIGRATION_FAMILY
        )
        if existing is not None:
            return {**existing, "status": "migrated", "legacy_config_read": False}
        meeting = getattr(config, "meeting", None)
        profile_id = str(getattr(meeting, "intel_profile_id", "") or "").strip()
        provider = str(getattr(meeting, "intel_provider", "") or "").strip()
        source = {"intel_profile_id": profile_id, "intel_provider": provider}
        source_sha256 = _sha256(source)
        if not profile_id:
            return self._migration_issue(
                MEETING_DEFERRED_MIGRATION_FAMILY,
                "builtin_profile_required",
                "choose_meeting_model_profile",
                source_sha256,
            )
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT MAX(revision) AS revision FROM model_profile_revisions WHERE profile_id=?",
                (profile_id,),
            ).fetchone()
        revision = int(row["revision"] or 0) if row is not None else 0
        if revision < 1:
            return self._migration_issue(
                MEETING_DEFERRED_MIGRATION_FAMILY,
                "legacy_profile_requires_upgrade",
                "upgrade_model_profile",
                source_sha256,
            )
        try:
            marker = assignments.migrate_capability_assignments_atomically(
                principal,
                family=MEETING_DEFERRED_MIGRATION_FAMILY,
                source_sha256=source_sha256,
                capability_entries={
                    "meeting.deferred_analysis": {
                        "profile_id": profile_id,
                        "profile_revision": revision,
                    }
                },
            )
        except ValidationError as exc:
            if exc.code != "inference_assignment_incompatible":
                raise
            return self._migration_issue(
                MEETING_DEFERRED_MIGRATION_FAMILY,
                "legacy_profile_incompatible",
                "choose_compatible_meeting_model_profile",
                source_sha256,
            )
        return {**marker, "status": "migrated", "legacy_config_read": True}

    def migrate_speech_recognition_route_assignments(
        self, principal: Principal, config: Any
    ) -> dict[str, Any]:
        """Convert one exact, built-in local Whisper selector or refuse it.

        This is intentionally a tiny closed migration: it resolves ``auto`` by
        the runtime's importability-only rule, never loads/downloads a model, and
        refuses repositories, paths, and every remote-shaped selector. The profile,
        unavailable local deployment,
        binding, assignment, and family marker share the assignment service's one
        transaction.
        """
        assignments = InferenceAssignmentService(self._db, registry=self._registry)
        existing = assignments.migration_marker(
            principal, family=SPEECH_RECOGNITION_MIGRATION_FAMILY
        )
        if existing is not None:
            return {**existing, "status": "migrated", "legacy_config_read": False}
        model = getattr(config, "model", None)
        name = str(getattr(model, "name", "") or "").strip().lower()
        saved_backend = str(getattr(model, "backend", "") or "").strip().lower()
        language = str(getattr(model, "language", "") or "").strip().lower()
        backend = saved_backend
        if backend == "auto":
            # Design note §Orchestrator amendment (2026-08-22): `auto` is the
            # owner's historically effective primary. Reuse Transcriber's
            # importability-only resolution; it loads no model and touches no network.
            try:
                from ..transcribe import _resolve_backend

                backend = _resolve_backend("auto")
            except Exception:
                backend = ""
        source_sha256 = _sha256(
            {
                "model_name": name,
                "backend": saved_backend,
                "resolved_backend": backend,
                "language": language,
            }
        )
        artifact_identity = _LOCAL_WHISPER_ARTIFACTS.get((backend, name))
        if not name or artifact_identity is None:
            return self._migration_issue(
                SPEECH_RECOGNITION_MIGRATION_FAMILY,
                "builtin_profile_required",
                "choose_audio_model_profile",
                source_sha256,
            )
        # The existing language vocabulary treats ``auto`` as the one valid
        # unpinned value.  It is authority about the owned local operation, not
        # an endpoint, secret, or any cloud consent.
        if language and not (language == "auto" or language.isalpha() and len(language) <= 12):
            return self._migration_issue(
                SPEECH_RECOGNITION_MIGRATION_FAMILY,
                "builtin_profile_required",
                "choose_audio_model_profile",
                source_sha256,
            )
        profile_id = "speech-migrated-" + source_sha256.removeprefix("sha256:")[:24]
        artifact_id = "artifact-" + profile_id
        deployment_id = "deployment-" + profile_id
        binding_id = "binding-" + profile_id
        manifest_evidence = {
            "revision": "legacy-whisper-v1",
            "claims": [
                "audio",
                "speech_language:" + (language or "auto"),
                "result_schema:" + self._registry.require("speech.transcribe").output_schema_sha256,
            ],
        }
        manifest = {**manifest_evidence, "sha256": _sha256(manifest_evidence)}
        profile_payload = ModelProfileService(self._db)._profile_payload({
            "profile_id": profile_id,
            "expected_revision": 0,
            "label": f"Whisper {backend} {name}",
            "provider_family": "local",
            "runtime_family": backend,
            "model_or_artifact_identity": artifact_id,
            "supported_modalities": ["audio"],
            "context_support": "bounded",
            "tokenizer_template_requirements": {},
            "capability_manifest": manifest,
            "safe_presentation": {
                "summary": "Migrated local Whisper selection",
                "badge": "legacy-model-config",
            },
        })
        capability_sha = str(manifest["sha256"])
        artifact_manifest = {"schema": "LegacyWhisperArtifact@1", "identity": artifact_identity}
        artifact_manifest_sha = _sha256(artifact_manifest)
        revision = DeploymentRevision.from_artifact(
            destination_id="local_whisper",
            engine=backend,
            model=artifact_identity,
            runtime_id=backend,
            runtime_revision="legacy-model-config-v1",
            artifact_id=artifact_id,
            manifest_sha256=artifact_manifest_sha,
            format="mlx_safetensors",
            architecture="whisper",
            # Speech emits no prompt tokens, but its frozen lifecycle and
            # transcription children reserve bounded controller output capacity.
            context_ceiling=1024,
            capability_sha256=capability_sha,
        )

        def prelude(conn: Any) -> None:
            now = _now()
            profile_material = {
                "schema_version": 2,
                "profile_id": profile_id,
                "revision": 1,
                **{key: value for key, value in profile_payload.items() if key != "expected_revision"},
            }
            conn.execute(
                """INSERT INTO model_profile_revisions
                   (profile_id,revision,sha256,label,provider_family,runtime_family,
                    model_or_artifact_identity,supported_modalities_json,context_support,
                    tokenizer_template_requirements_json,capability_manifest_json,
                    safe_presentation_json,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    profile_id, 1, _sha256(profile_material), profile_payload["label"],
                    profile_payload["provider_family"], profile_payload["runtime_family"], artifact_id,
                    _canonical(profile_payload["supported_modalities"]), profile_payload["context_support"],
                    _canonical(profile_payload["tokenizer_template_requirements"]),
                    _canonical(manifest), _canonical(profile_payload["safe_presentation"]), now,
                ),
            )
            conn.execute(
                """INSERT INTO inference_model_artifacts
                   (artifact_id,format,source_kind,source_repository,source_revision,
                    manifest_json,manifest_sha256,installed_bytes,state,local_locator,created_at,verified_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    artifact_id, "mlx_safetensors", "legacy-model-config", artifact_identity,
                    "legacy-model-config-v1", _canonical(artifact_manifest), artifact_manifest_sha,
                    1, "removed", "", now, now,
                ),
            )
            conn.execute(
                """INSERT INTO deployment_revisions
                   (id,schema_version,destination_id,kind,engine,model,node,boundary,
                    endpoint,model_path,secret_slot,runtime_id,runtime_revision,artifact_id,
                    manifest_sha256,format,architecture,context_ceiling,capability_sha256)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    revision.id, revision.schema_version, revision.destination_id, revision.kind,
                    revision.engine, revision.model, revision.node, revision.boundary,
                    revision.endpoint, None, revision.secret_slot, revision.runtime_id,
                    revision.runtime_revision, revision.artifact_id, revision.manifest_sha256,
                    revision.format, revision.architecture, revision.context_ceiling,
                    revision.capability_sha256,
                ),
            )
            conn.execute(
                """INSERT INTO inference_deployments
                   (deployment_id,destination_id,runtime_id,runtime_revision,artifact_id,
                    model_identity,context_ceiling,recommended_context,capability_json,
                    capability_sha256,execution_revision_id,configuration_revision,active,
                    created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    deployment_id, "local_whisper", backend, revision.runtime_revision, artifact_id,
                    artifact_identity, 1024, 1024, _canonical(manifest), capability_sha, revision.id,
                    1, 0, now, now,
                ),
            )
            observation_id = "ready-" + profile_id
            conn.execute(
                """INSERT INTO model_profile_readiness_observations
                   (observation_id,deployment_head_id,deployment_configuration_revision,
                    deployment_revision_id,state,reason_code,observed_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (observation_id, deployment_id, 1, revision.id, "unavailable", "artifact_unobserved", now),
            )
            conn.execute(
                """INSERT INTO model_profile_binding_revisions
                   (binding_id,revision,profile_id,profile_revision,deployment_head_id,
                    deployment_configuration_revision,deployment_revision_id,secret_slot,
                    enabled,readiness_observation_id,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (binding_id, 1, profile_id, 1, deployment_id, 1, revision.id, "", 1, observation_id, now),
            )
            conn.execute(
                "INSERT INTO model_profile_binding_heads(binding_id,profile_id,revision,updated_at) VALUES (?,?,?,?)",
                (binding_id, profile_id, 1, now),
            )

        try:
            marker = assignments.migrate_capability_assignments_atomically(
                principal,
                family=SPEECH_RECOGNITION_MIGRATION_FAMILY,
                source_sha256=source_sha256,
                capability_entries={
                    "speech.transcribe": {"profile_id": profile_id, "profile_revision": 1}
                },
                _prelude=prelude,
            )
        except ValidationError as exc:
            if exc.code != "inference_assignment_incompatible":
                raise
            return self._migration_issue(
                SPEECH_RECOGNITION_MIGRATION_FAMILY,
                "builtin_profile_required",
                "choose_audio_model_profile",
                source_sha256,
            )
        return {**marker, "status": "migrated", "legacy_config_read": True}

    def record_local_speech_readiness_after_load(
        self, principal: Principal, *, deployment_revision_id: str
    ) -> dict[str, Any]:
        """Record the first successful same-device speech load without probing."""
        if principal.kind is not PrincipalKind.OWNER:
            raise ValidationError(
                "Owner authority is required.", code="inference_adoption_owner_required"
            )
        return self._record_local_readiness_after_load(
            deployment_revision_id=deployment_revision_id,
            reason_code="loaded_under_speech_preload",
        )

    def record_local_rails_readiness_after_load(
        self, principal: Principal, *, deployment_revision_id: str
    ) -> dict[str, Any]:
        """Record Rails' first successful frozen local load, never a probe."""
        if not (
            principal.kind is PrincipalKind.SERVICE
            and principal.identity == "rails-observer"
            and principal.authority_basis == "rails-observer:journal-only"
        ):
            raise ValidationError(
                "Rails observer authority is required.",
                code="inference_adoption_rails_service_required",
            )
        return self._record_local_readiness_after_load(
            deployment_revision_id=deployment_revision_id,
            reason_code="loaded_under_rails_observer",
        )

    def _record_local_readiness_after_load(
        self, *, deployment_revision_id: str, reason_code: str
    ) -> dict[str, Any]:
        """Advance only after a successful physical leaf proved the frozen locator."""
        revision_id = _safe(deployment_revision_id, field="deployment_revision_id")
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = conn.execute(
                    """SELECT b.*,h.profile_id AS head_profile_id,h.revision AS head_revision
                         FROM model_profile_binding_heads h
                         JOIN model_profile_binding_revisions b
                           ON b.binding_id=h.binding_id AND b.revision=h.revision
                        WHERE b.deployment_revision_id=?
                        ORDER BY h.updated_at DESC LIMIT 1""",
                    (revision_id,),
                ).fetchone()
                if row is None:
                    raise ValidationError(
                        "Speech deployment binding is missing.",
                        code="inference_route_binding_unavailable",
                    )
                current_observation = conn.execute(
                    "SELECT state FROM model_profile_readiness_observations WHERE observation_id=?",
                    (str(row["readiness_observation_id"] or ""),),
                ).fetchone()
                if current_observation is not None and str(current_observation["state"]) == "ready":
                    conn.commit()
                    return {"state": "ready", "replayed": True}
                now = _now()
                observation_id = "ready_" + uuid.uuid4().hex
                conn.execute(
                    """INSERT INTO model_profile_readiness_observations
                       (observation_id,deployment_head_id,deployment_configuration_revision,
                        deployment_revision_id,state,reason_code,observed_at)
                       VALUES (?,?,?,?,?,?,?)""",
                    (
                        observation_id,
                        str(row["deployment_head_id"]),
                        int(row["deployment_configuration_revision"]),
                        revision_id,
                        "ready",
                        reason_code,
                        now,
                    ),
                )
                next_revision = int(row["head_revision"]) + 1
                conn.execute(
                    """INSERT INTO model_profile_binding_revisions
                       (binding_id,revision,profile_id,profile_revision,deployment_head_id,
                        deployment_configuration_revision,deployment_revision_id,secret_slot,
                        enabled,readiness_observation_id,created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        str(row["binding_id"]),
                        next_revision,
                        str(row["profile_id"]),
                        int(row["profile_revision"]),
                        str(row["deployment_head_id"]),
                        int(row["deployment_configuration_revision"]),
                        revision_id,
                        str(row["secret_slot"] or ""),
                        int(row["enabled"]),
                        observation_id,
                        now,
                    ),
                )
                conn.execute(
                    """UPDATE model_profile_binding_heads
                          SET revision=?,updated_at=? WHERE binding_id=?""",
                    (next_revision, now, str(row["binding_id"])),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return {"state": "ready", "observation_id": observation_id, "replayed": False}

    @staticmethod
    def _migration_issue(
        family: str, reason_code: str, repair: str, source_sha256: str
    ) -> dict[str, Any]:
        return {
            "schema": "InferenceAssignmentMigrationIssue@1",
            "family": family,
            "status": "needs_attention",
            "reason_code": reason_code,
            "repair": repair,
            "source_sha256": source_sha256,
        }

    def migrate_rails_observer_route_assignments(
        self, principal: Principal, config: Any
    ) -> dict[str, Any]:
        """Convert Rails' one historical local selector without guessing.

        A blank selector is the documented ``this_machine`` deployment.  The
        migration records a minimum local v2 profile/binding from that exact
        saved deployment identity in the same assignment/marker transaction;
        it never tests the path, loads a model, or discovers another target.
        """
        assignments = InferenceAssignmentService(self._db, registry=self._registry)
        existing = assignments.migration_marker(principal, family=RAILS_OBSERVER_MIGRATION_FAMILY)
        if existing is not None:
            # A pre-fix marker may have materialized this Rails-only artifact as
            # active. Repair that older footprint without re-reading Config or
            # re-running migration selection: Rails execution is assignment-led,
            # so it must never participate in the generic local-artifact lookup.
            with self._db._connection() as conn:
                try:
                    conn.execute(
                        """UPDATE inference_deployments SET active=0
                           WHERE active=1 AND artifact_id IN (
                               SELECT artifact_id FROM inference_model_artifacts
                               WHERE source_kind='legacy-rails-observer'
                           )"""
                    )
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise
            return {**existing, "status": "migrated", "legacy_config_read": False}
        rails = getattr(config, "rails_observer", None)
        # Rails is off by default.  A default-constructed blank selector is not
        # saved observer intent, so it must not mint an otherwise generic local
        # deployment merely because the meeting default happens to name a path.
        # The historic ``this_machine`` sentinel is meaningful only for an
        # enabled observer: that is the installed feature which would have read
        # the saved selector.
        if not bool(getattr(rails, "enabled", False)):
            return {
                "family": RAILS_OBSERVER_MIGRATION_FAMILY,
                "status": "not_applicable",
                "reason_code": "rails_observer_disabled",
                "legacy_config_read": True,
            }
        configured = str(getattr(rails, "profile_id", "") or "").strip()
        source_selector = configured or "this_machine"
        source: dict[str, Any] = {"profile_id": source_selector}
        profile_id = configured
        profile_revision = 0
        local_path = ""
        if configured:
            with self._db._connection() as conn:
                row = conn.execute(
                    "SELECT MAX(revision) AS revision FROM model_profile_revisions WHERE profile_id=?",
                    (configured,),
                ).fetchone()
            profile_revision = int(row["revision"] or 0) if row is not None else 0
            if profile_revision < 1:
                legacy = self._db.profiles.get(configured)
                if legacy is None or str(getattr(legacy, "kind", "")) != "onDevice":
                    return self._migration_issue(
                        RAILS_OBSERVER_MIGRATION_FAMILY,
                        "legacy_profile_requires_upgrade",
                        "choose_rails_observer_model_profile",
                        _sha256(source),
                    )
                local_path = str(getattr(legacy, "model_file", "") or "").strip()
        else:
            # This function reads the loaded configuration object rather than
            # Config again.  It does no filesystem readiness probe.
            meeting = getattr(config, "meeting", None)
            local_path = str(getattr(meeting, "intel_realtime_model", "") or "").strip()
            if not local_path:
                from ..intel.providers import DEFAULT_INTEL_MODEL_PATH
                local_path = str(DEFAULT_INTEL_MODEL_PATH or "").strip()
        source["same_device_deployment_sha256"] = _sha256({"model_path": local_path})
        source_sha256 = _sha256(source)
        if profile_revision >= 1:
            try:
                marker = assignments.migrate_capability_assignments_atomically(
                    principal,
                    family=RAILS_OBSERVER_MIGRATION_FAMILY,
                    source_sha256=source_sha256,
                    capability_entries={
                        "background.rails_summary": {
                            "profile_id": profile_id,
                            "profile_revision": profile_revision,
                        }
                    },
                )
            except ValidationError as exc:
                if exc.code != "inference_assignment_incompatible":
                    raise
                return self._migration_issue(
                    RAILS_OBSERVER_MIGRATION_FAMILY,
                    "legacy_profile_incompatible",
                    "choose_rails_observer_model_profile",
                    source_sha256,
                )
            return {**marker, "status": "migrated", "legacy_config_read": True}
        if not local_path:
            return self._migration_issue(
                RAILS_OBSERVER_MIGRATION_FAMILY,
                "same_device_deployment_unnamed",
                "choose_rails_observer_model_profile",
                source_sha256,
            )

        # The stored id is a stable public handle; the exact local locator stays
        # only in the private deployment revision, as it did for the legacy path.
        suffix = source_sha256.removeprefix("sha256:")[:24]
        profile_id = "rails-observer-local-" + suffix
        artifact_id = "artifact-" + profile_id
        deployment_id = "deployment-" + profile_id
        binding_id = "binding-" + profile_id
        model = Path(local_path).expanduser().stem
        if not model:
            return self._migration_issue(
                RAILS_OBSERVER_MIGRATION_FAMILY,
                "same_device_deployment_unnamed",
                "choose_rails_observer_model_profile",
                source_sha256,
            )
        capability = self._registry.require("background.rails_summary")
        manifest_evidence = {"revision": "rails-observer-this-machine-v1", "claims": ["language"]}
        manifest = {**manifest_evidence, "sha256": _sha256(manifest_evidence)}
        profile_payload = ModelProfileService(self._db)._profile_payload({
            "profile_id": profile_id,
            "expected_revision": 0,
            "label": f"Rails observer local {model}",
            "provider_family": "local",
            "runtime_family": "configured_local_engine",
            "model_or_artifact_identity": artifact_id,
            "supported_modalities": ["language"],
            "context_support": "bounded",
            "tokenizer_template_requirements": {},
            "capability_manifest": manifest,
            "safe_presentation": {"summary": "Migrated Rails observer local deployment", "badge": "rails-observer"},
        })
        deployment = DeploymentRevision.from_artifact(
            destination_id="this_machine",
            engine="configured_local_engine",
            model=model,
            runtime_id="configured_local_engine",
            runtime_revision="rails-observer-this-machine-v1",
            artifact_id=artifact_id,
            manifest_sha256=_sha256({"same_device_deployment_sha256": source["same_device_deployment_sha256"]}),
            format="gguf",
            architecture="unknown",
            context_ceiling=16384,
            capability_sha256=str(manifest["sha256"]),
            resolved_model_path=local_path,
        )

        def prelude(conn: Any) -> None:
            now = _now()
            profile_material = {"schema_version": 2, "profile_id": profile_id, "revision": 1,
                                **{key: value for key, value in profile_payload.items() if key != "expected_revision"}}
            conn.execute(
                """INSERT INTO model_profile_revisions
                   (profile_id,revision,sha256,label,provider_family,runtime_family,model_or_artifact_identity,
                    supported_modalities_json,context_support,tokenizer_template_requirements_json,
                    capability_manifest_json,safe_presentation_json,created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (profile_id, 1, _sha256(profile_material), profile_payload["label"],
                 profile_payload["provider_family"], profile_payload["runtime_family"], artifact_id,
                 _canonical(profile_payload["supported_modalities"]), profile_payload["context_support"],
                 _canonical(profile_payload["tokenizer_template_requirements"]), _canonical(manifest),
                 _canonical(profile_payload["safe_presentation"]), now),
            )
            conn.execute(
                """INSERT INTO inference_model_artifacts
                   (artifact_id,format,source_kind,source_repository,source_revision,manifest_json,
                    manifest_sha256,installed_bytes,state,local_locator,created_at,verified_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                # The saved selector is the exact historical local locator.  It
                # is a truthful private artifact declaration, not a migration
                # probe: readiness remains unavailable until first execution
                # successfully loads this frozen deployment.
                (artifact_id, "gguf", "legacy-rails-observer", "this_machine",
                 "rails-observer-this-machine-v1", _canonical({"same_device_deployment_sha256": source["same_device_deployment_sha256"]}),
                 deployment.manifest_sha256, 1, "verified", local_path, now, now),
            )
            conn.execute(
                """INSERT INTO deployment_revisions
                   (id,schema_version,destination_id,kind,engine,model,node,boundary,endpoint,model_path,
                    secret_slot,runtime_id,runtime_revision,artifact_id,manifest_sha256,format,architecture,
                    context_ceiling,capability_sha256) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (deployment.id, deployment.schema_version, deployment.destination_id, deployment.kind,
                 deployment.engine, deployment.model, deployment.node, deployment.boundary, deployment.endpoint,
                 None, deployment.secret_slot, deployment.runtime_id, deployment.runtime_revision,
                 deployment.artifact_id, deployment.manifest_sha256, deployment.format, deployment.architecture,
                 deployment.context_ceiling, deployment.capability_sha256),
            )
            conn.execute(
                """INSERT INTO inference_deployments
                   (deployment_id,destination_id,runtime_id,runtime_revision,artifact_id,model_identity,
                    context_ceiling,recommended_context,capability_json,capability_sha256,execution_revision_id,
                    configuration_revision,active,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                # This is capability-owned route material, not the owner's
                # generic current Thought deployment.  Keep it inactive so
                # locator-based Thought resolution cannot adopt the Rails
                # artifact; the explicit background.rails_summary assignment
                # below is its only execution authority.
                (deployment_id, "this_machine", deployment.runtime_id, deployment.runtime_revision, artifact_id,
                 model, 16384, 16384, _canonical(manifest), str(manifest["sha256"]), deployment.id, 1, 0, now, now),
            )
            observation_id = "ready-" + profile_id
            # No probe occurred.  This is deliberately unavailable until the
            # actual frozen execution observes readiness.
            conn.execute(
                """INSERT INTO model_profile_readiness_observations
                   (observation_id,deployment_head_id,deployment_configuration_revision,deployment_revision_id,
                    state,reason_code,observed_at) VALUES (?,?,?,?,?,?,?)""",
                (observation_id, deployment_id, 1, deployment.id, "unavailable", "unobserved_legacy_local", now),
            )
            conn.execute(
                """INSERT INTO model_profile_binding_revisions
                   (binding_id,revision,profile_id,profile_revision,deployment_head_id,
                    deployment_configuration_revision,deployment_revision_id,secret_slot,enabled,
                    readiness_observation_id,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (binding_id, 1, profile_id, 1, deployment_id, 1, deployment.id, "", 1, observation_id, now),
            )
            conn.execute(
                "INSERT INTO model_profile_binding_heads(binding_id,profile_id,revision,updated_at) VALUES (?,?,?,?)",
                (binding_id, profile_id, 1, now),
            )

        try:
            marker = assignments.migrate_capability_assignments_atomically(
                principal,
                family=RAILS_OBSERVER_MIGRATION_FAMILY,
                source_sha256=source_sha256,
                capability_entries={"background.rails_summary": {"profile_id": profile_id, "profile_revision": 1}},
                _prelude=prelude,
            )
        except ValidationError as exc:
            if exc.code != "inference_assignment_incompatible":
                raise
            return self._migration_issue(
                RAILS_OBSERVER_MIGRATION_FAMILY,
                "same_device_deployment_incompatible",
                "choose_rails_observer_model_profile",
                source_sha256,
            )
        return {**marker, "status": "migrated", "legacy_config_read": True}

    def migrate_startup_legacy_assignments(
        self, principal: Principal, config_loader: Callable[[], Any]
    ) -> dict[str, dict[str, Any]]:
        """Run each startup-owned family once without reading Config after markers."""
        assignments = InferenceAssignmentService(self._db, registry=self._registry)
        markers = {
            family: assignments.migration_marker(principal, family=family)
            for family in (
                MIGRATION_FAMILY,
                MEETING_MIGRATION_FAMILY,
                MEETING_DEFERRED_MIGRATION_FAMILY,
                SPEECH_RECOGNITION_MIGRATION_FAMILY,
                RAILS_OBSERVER_MIGRATION_FAMILY,
            )
        }
        if all(markers.values()):
            return {
                family: {**marker, "status": "migrated", "legacy_config_read": False}
                for family, marker in markers.items()
                if marker is not None
            }
        config = config_loader()
        return {
            MIGRATION_FAMILY: self.migrate_legacy_config(principal, config),
            MEETING_MIGRATION_FAMILY: self.migrate_meeting_route_assignments(
                principal, config
            ),
            MEETING_DEFERRED_MIGRATION_FAMILY: self.migrate_meeting_deferred_route_assignments(
                principal, config
            ),
            SPEECH_RECOGNITION_MIGRATION_FAMILY: self.migrate_speech_recognition_route_assignments(
                principal, config
            ),
            RAILS_OBSERVER_MIGRATION_FAMILY: self.migrate_rails_observer_route_assignments(
                principal, config
            ),
        }

    def migrate_legacy_config(
        self, principal: Principal, config: Any
    ) -> dict[str, Any]:
        """One-way Config-pointer adapter; never a post-marker selector.

        A configured v2 profile is copied into capability assignments exactly
        once.  The implicit ``this_machine`` sentinel cannot truthfully name a
        reusable v2 profile, so it returns one explicit repair instead of
        inventing a model identity from mutable Config.
        """
        assignments = InferenceAssignmentService(self._db, registry=self._registry)
        existing = assignments.migration_marker(principal, family=MIGRATION_FAMILY)
        if existing is not None:
            return {**existing, "status": "migrated", "legacy_config_read": False}
        thoughts = str(
            getattr(getattr(config, "thoughts", None), "inference_target_id", "") or ""
        ).strip()
        writing = str(
            getattr(
                getattr(getattr(config, "dictation", None), "runtime", None),
                "profile_id",
                "",
            )
            or ""
        ).strip()
        source = {"thoughts": thoughts or "this_machine", "writing": writing or "this_machine"}
        source_sha = _sha256(source)
        if not thoughts or not writing or thoughts == "this_machine" or writing == "this_machine":
            return {
                "schema": "InferenceAssignmentMigrationIssue@1",
                "family": MIGRATION_FAMILY,
                "status": "needs_attention",
                "reason_code": "builtin_profile_required",
                "repair": "choose_model_profile",
                "source_sha256": source_sha,
            }

        def exact_profile(profile_id: str) -> dict[str, Any] | None:
            with self._db._connection() as conn:
                row = conn.execute(
                    "SELECT MAX(revision) AS revision FROM model_profile_revisions WHERE profile_id=?",
                    (profile_id,),
                ).fetchone()
            revision = int(row["revision"] or 0) if row is not None else 0
            return None if revision < 1 else {"profile_id": profile_id, "profile_revision": revision}

        thought_profile, writing_profile = exact_profile(thoughts), exact_profile(writing)
        if thought_profile is None or writing_profile is None:
            return {
                "schema": "InferenceAssignmentMigrationIssue@1",
                "family": MIGRATION_FAMILY,
                "status": "needs_attention",
                "reason_code": "legacy_profile_requires_upgrade",
                "repair": "upgrade_model_profile",
                "source_sha256": source_sha,
            }
        profiles = {
            "thought.interview": thought_profile,
            "ask.answer": thought_profile,
            "speech.intent_classify": writing_profile,
            "speech.rewrite": writing_profile,
        }
        marker = assignments.migrate_capability_assignments_atomically(
            principal,
            family=MIGRATION_FAMILY,
            source_sha256=source_sha,
            capability_entries=profiles,
        )
        return {**marker, "status": "migrated", "legacy_config_read": True}


ProductionInferenceAdoptionService = RoutedInferenceCoordinator

__all__ = [
    "ADOPTED_CAPABILITIES",
    "MEETING_MIGRATION_FAMILY",
    "MEETING_DEFERRED_MIGRATION_FAMILY",
    "SPEECH_RECOGNITION_MIGRATION_FAMILY",
    "RAILS_OBSERVER_MIGRATION_FAMILY",
    "ProductionInferenceAdoptionService",
    "ProductionRouteEvidence",
    "RoutedInferenceCoordinator",
]
