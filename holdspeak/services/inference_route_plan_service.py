"""Immutable content-free inference route planning authority (HS-143-05).

The resolver reads one local SQLite snapshot and performs no writes, probes,
loads, scans, or network work.  Persistence is a separate atomic step.  Once a
plan is frozen, execution evidence is reconstructed exclusively from its
content-addressed payload and normalized legs—not mutable configuration heads.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any, Callable, Mapping, Sequence

from ..deployment_revisions import DeploymentRevision
from ..inference_targets import DeploymentIdentity, _private_endpoint
from ..principals import Principal, PrincipalKind
from ..inference_capabilities import (
    InferenceCapabilityRegistry,
    process_inference_capability_registry,
)
from .errors import ConflictError, NotFound, ServiceError, ValidationError
from .inference_assignment_service import InferenceAssignmentService
from .model_profile_service import (
    ModelProfileService,
    adapt_v1_profile,
)


ROUTE_PLAN_SCHEMA = "InferenceRoutePlan@1"
OPERATION_ROUTE_REQUEST_PLAN_SCHEMA = "OperationAdmittedRouteRequestPlan@1"
_HASH = re.compile(r"^sha256:[0-9a-f]{64}$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$")
_BOUNDARIES = {
    "same_device": "local",
    "local": "local",
    "private_network": "private_network",
    "private_mesh": "mesh",
    "mesh": "mesh",
    "paired": "mesh",
    "cloud": "cloud",
    "external_service": "cloud",
}
_ELIGIBILITY = frozenset(
    {"executable", "known_preflight_unavailable", "known_context_overflow"}
)
_UNAVAILABLE_REASONS = frozenset({
    "preflight_unavailable", "binding_disabled", "binding_not_ready",
    "credential_missing", "artifact_unavailable", "runtime_unavailable",
    "resource_unavailable", "policy_unavailable", "context_overflow",
})
ROUTE_PLANNING_AUTHORITY = Principal(
    PrincipalKind.SERVICE,
    "inference-route-planner",
    authority_basis="kernel:inference-routing@1",
)


@dataclass(frozen=True)
class RouteAdmissionEvidenceProvider:
    """Composition-registered owner of durable private planning evidence."""

    id: str
    revision: int
    capabilities: tuple[tuple[str, int, str], ...]
    operation_policy_revisions: tuple[str, ...]
    freeze: Callable[[Any, str, str], Mapping[str, Any]]
    reconstruct: Callable[[Any, str], Mapping[str, Any]]


def _canonical(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def _sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _safe_id(value: Any, *, field: str) -> str:
    clean = str(value or "").strip()
    if not _SAFE_ID.fullmatch(clean):
        raise ValidationError(f"{field} is invalid", code="inference_route_plan_invalid")
    return clean


def _hash(value: Any, *, field: str) -> str:
    clean = str(value or "").strip()
    if not _HASH.fullmatch(clean):
        raise ValidationError(f"{field} is invalid", code="inference_route_plan_invalid")
    return clean


class InferenceRoutePlanService:
    """Resolve, freeze, and reconstruct the sole canonical route-plan types."""

    def __init__(
        self,
        db: Any,
        *,
        registry: InferenceCapabilityRegistry | None = None,
        clock: Any = _now,
        operation_evidence_providers: Sequence[RouteAdmissionEvidenceProvider] = (),
    ) -> None:
        self._db = db
        self._registry = registry or process_inference_capability_registry()
        self._assignments = InferenceAssignmentService(db, registry=self._registry)
        self._profiles = ModelProfileService(db)
        self._clock = clock
        self._operation_evidence_providers = {
            provider.id: provider for provider in operation_evidence_providers
        }
        if len(self._operation_evidence_providers) != len(operation_evidence_providers):
            raise ValueError("duplicate route admission evidence provider")
        owned: set[tuple[tuple[str, int, str], str]] = set()
        for provider in operation_evidence_providers:
            _safe_id(provider.id, field="evidence_provider_id")
            if type(provider.revision) is not int or provider.revision < 1 or not callable(provider.freeze) or not callable(provider.reconstruct):
                raise ValueError("invalid route admission evidence provider")
            claims = {
                (capability, policy)
                for capability in provider.capabilities
                for policy in provider.operation_policy_revisions
            }
            if owned & claims:
                raise ValueError("ambiguous route admission evidence provider")
            owned.update(claims)

    def resolve_route_plan(
        self,
        authority: Principal,
        *,
        capability_id: str,
        operation_policy_revision: str | None = None,
        invocation_id: str | None = None,
        subject_kind: str | None = None,
        subject_id: str | None = None,
        plan_id: str | None = None,
    ) -> dict[str, Any]:
        """Pure resolution: one read snapshot and no durable or external effects."""
        self._require_planner(authority)
        capability = self._registry.require(capability_id)
        policy_revision = self._operation_policy(capability, operation_policy_revision)
        with self._db._connection() as conn:
            conn.execute("BEGIN")
            try:
                result, _revisions, _preflight = self._resolve_in_conn(
                    conn,
                    capability=capability,
                    operation_policy_revision=policy_revision,
                    invocation_id=invocation_id,
                    subject_kind=subject_kind,
                    subject_id=subject_id,
                    plan_id=plan_id,
                )
                conn.rollback()
                return result
            except Exception:
                conn.rollback()
                raise

    def _resolve_in_conn(
        self,
        conn: Any,
        *,
        capability: Any,
        operation_policy_revision: str,
        invocation_id: str | None,
        subject_kind: str | None,
        subject_id: str | None,
        plan_id: str | None,
    ) -> tuple[dict[str, Any], list[DeploymentRevision], list[dict[str, Any]]]:
        assignment, inherited_from = self._assignment_snapshot(
            conn,
            capability=capability,
            invocation_id=invocation_id,
            subject_kind=subject_kind,
            subject_id=subject_id,
        )
        entries, private_revisions, preflight = self._resolve_entries(
            conn, capability, assignment["entries"]
        )
        retry_policy = self._registry.retry_policy(
            assignment["retry_policy_id"] or capability.default_retry_policy_id
        )
        created = self._clock()
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        created_at = _timestamp(created)
        deadline_at = _timestamp(created + timedelta(milliseconds=retry_policy.deadline_ms))
        identity = plan_id or "irp_" + uuid.uuid4().hex
        material = {
            "schema": ROUTE_PLAN_SCHEMA,
            "id": _safe_id(identity, field="plan_id"),
            "capability": {
                "id": capability.id,
                "revision": capability.revision,
                "schema_sha256": capability.schema_sha256,
            },
            "source": {
                "assignment_id": assignment["id"],
                "assignment_revision": assignment["revision"],
                "assignment_sha256": assignment["sha256"],
                "inherited_from": inherited_from,
            },
            "entries": entries,
            "retry_policy": {
                "id": retry_policy.id,
                "revision": retry_policy.revision,
                "sha256": retry_policy.sha256,
                "per_entry_attempts": retry_policy.per_entry_attempts,
                "total_physical_attempts": retry_policy.total_physical_attempts,
                "deadline_ms": retry_policy.deadline_ms,
                "token_budget": retry_policy.token_budget,
                "cost_budget": retry_policy.cost_budget,
                "tool_call_budget": retry_policy.tool_call_budget,
                "fallback_dispositions": list(retry_policy.fallback_dispositions),
                "retryable_dispositions": list(retry_policy.retryable_dispositions),
            },
            "operation_policy_revision": operation_policy_revision,
            "created_at": created_at,
            "deadline_at": deadline_at,
        }
        return {**material, "sha256": _sha256(material)}, private_revisions, preflight

    def _assignment_snapshot(
        self,
        conn: Any,
        *,
        capability: Any,
        invocation_id: str | None,
        subject_kind: str | None,
        subject_id: str | None,
    ) -> tuple[dict[str, Any], str]:
        keys: list[tuple[str, str]] = []
        if invocation_id:
            keys.append((f"invocation:{_safe_id(invocation_id, field='invocation_id')}:capability:{capability.id}", "invocation"))
        if subject_kind or subject_id:
            if subject_kind not in {"thought", "workbench", "agent", "recipe", "project"} or not subject_id:
                raise ValidationError("subject is invalid", code="inference_route_plan_invalid")
            keys.append((f"subject:{subject_kind}:{_safe_id(subject_id, field='subject_id')}:capability:{capability.id}", "subject"))
        keys.extend(((f"capability:{capability.id}", "capability"), (f"group:{capability.group_id}", "group"), ("global", "global")))
        for key, inherited in keys:
            row = self._assignments._head(conn, key)
            if row is None:
                continue
            material = self._assignments._assignment_material(conn, row, require_active_head=True)
            policy_id = material["retry_policy_id"] or capability.default_retry_policy_id
            if policy_id not in capability.permitted_retry_policy_ids:
                raise ValidationError("Assignment policy is no longer compatible.", code="no_compatible_assignment")
            return {**material, "sha256": str(row["sha256"])}, inherited
        raise ValidationError(
            "No model assignment can be frozen.",
            code="no_assignment",
            context={"capability_id": capability.id},
        )

    def freeze_route_plan(self, authority: Principal, *, command_id: str, **request: Any) -> dict[str, Any]:
        """Resolve and persist in one transaction; replay never re-resolves heads."""
        self._require_planner(authority)
        allowed = {"capability_id", "operation_policy_revision", "invocation_id", "subject_kind", "subject_id"}
        if set(request) - allowed or "capability_id" not in request:
            raise ValidationError("Route freeze request has an invalid shape.", code="inference_route_plan_invalid")
        command = _safe_id(command_id, field="command_id")
        request_hash = _sha256({"command_id": command, **request})
        expected_plan_id = self._deterministic_id("route", command, request_hash)
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                replay = conn.execute(
                    "SELECT * FROM inference_route_plan_commands WHERE command_id=?",
                    (command,),
                ).fetchone()
                if replay is not None:
                    if str(replay["request_sha256"]) != request_hash:
                        raise ConflictError("Route command changed.", code="inference_route_plan_command_conflict")
                    result = self._route_from_row(
                        conn,
                        conn.execute("SELECT * FROM inference_route_plans WHERE id=?", (replay["plan_id"],)).fetchone(),
                    )
                    if str(replay["plan_sha256"]) != result["sha256"] or result["id"] != expected_plan_id:
                        raise ConflictError("Stored route command effect is invalid.", code="inference_route_plan_command_integrity_invalid")
                    conn.commit()
                    return result
                self._refuse_route_identity_collision(conn, expected_plan_id)
                capability = self._registry.require(str(request["capability_id"]))
                policy_revision = self._operation_policy(
                    capability, request.get("operation_policy_revision")
                )
                resolved, revisions, _preflight = self._resolve_in_conn(
                    conn,
                    capability=capability,
                    operation_policy_revision=policy_revision,
                    invocation_id=request.get("invocation_id"),
                    subject_kind=request.get("subject_kind"),
                    subject_id=request.get("subject_id"),
                    plan_id=expected_plan_id,
                )
                material = {key: value for key, value in resolved.items() if key != "sha256"}
                self._insert_route(
                    conn, material, resolved["sha256"], revisions,
                    capability_definition=capability.canonical_dict(),
                    retry_policy_definition=self._registry.retry_policy(material["retry_policy"]["id"]).canonical_dict(),
                )
                conn.execute(
                    "INSERT INTO inference_route_plan_commands VALUES (?,?,?,?,?)",
                    (command, request_hash, material["id"], resolved["sha256"], material["created_at"]),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return resolved

    def freeze_legacy_one_leg_plan(
        self,
        authority: Principal,
        *,
        command_id: str,
        capability_id: str,
        legacy_profile_id: str,
        operation_policy_revision: str | None = None,
        **extras: Any,
    ) -> dict[str, Any]:
        """Adapt exact stored v1 bytes to one explicit, replay-safe route plan."""
        self._require_planner(authority)
        if extras:
            raise ValidationError("Legacy route request has an invalid shape.", code="inference_route_plan_invalid")
        capability = self._registry.require(capability_id)
        policy = self._registry.retry_policy(capability.default_retry_policy_id)
        command = _safe_id(command_id, field="command_id")
        source_id = _safe_id(legacy_profile_id, field="legacy_profile_id")
        request_hash = _sha256({"command_id": command, "capability_id": capability.id, "legacy_profile_id": source_id, "operation_policy_revision": operation_policy_revision})
        expected_plan_id = self._deterministic_id("legacy-route", command, request_hash)
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                replay = conn.execute("SELECT * FROM inference_route_plan_commands WHERE command_id=?", (command,)).fetchone()
                if replay is not None:
                    if str(replay["request_sha256"]) != request_hash:
                        raise ConflictError("Route command changed.", code="inference_route_plan_command_conflict")
                    result = self._route_from_row(conn, conn.execute("SELECT * FROM inference_route_plans WHERE id=?", (replay["plan_id"],)).fetchone())
                    if str(replay["plan_sha256"]) != result["sha256"] or result["id"] != expected_plan_id:
                        raise ConflictError("Stored route command effect is invalid.", code="inference_route_plan_command_integrity_invalid")
                    conn.commit()
                    return result
                row = conn.execute("SELECT * FROM profiles WHERE id=? AND deleted=0", (source_id,)).fetchone()
                if row is None:
                    raise NotFound("legacy profile", source_id)
                self._refuse_route_identity_collision(conn, expected_plan_id)
                source = SimpleNamespace(**dict(row))
                adapted = adapt_v1_profile(source)
                deployment_revision = self._legacy_deployment(source)
                boundary = _BOUNDARIES.get(deployment_revision.boundary)
                if boundary not in capability.allowed_boundaries:
                    raise ValidationError("Legacy target boundary is not permitted.", code="inference_route_boundary_unsupported")
                context = self._context_support({"mode": "bounded", "maximum_tokens": int(row["context_limit"] or 0)})
                self._validate_legacy_compatibility(capability, context, boundary)
                created = self._clock()
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                digest = hashlib.sha256(deployment_revision.id.encode()).hexdigest()[:24]
                material = self._legacy_material(
                    capability=capability, policy=policy, adapted=adapted,
                    deployment_revision=deployment_revision, boundary=boundary,
                    context=context, digest=digest, created=created,
                    operation_policy_revision=operation_policy_revision, plan_id=expected_plan_id,
                )
                route_hash = _sha256(material)
                self._insert_route(conn, material, route_hash, [deployment_revision], capability_definition=capability.canonical_dict(), retry_policy_definition=policy.canonical_dict())
                conn.execute("INSERT INTO inference_route_plan_commands VALUES (?,?,?,?,?)", (command, request_hash, material["id"], route_hash, material["created_at"]))
                conn.commit()
                return {**material, "sha256": route_hash}
            except Exception:
                conn.rollback()
                raise

    def _legacy_material(self, *, capability: Any, policy: Any, adapted: Mapping[str, Any], deployment_revision: DeploymentRevision, boundary: str, context: Mapping[str, Any], digest: str, created: datetime, operation_policy_revision: Any, plan_id: str | None) -> dict[str, Any]:
        return {
            "schema": ROUTE_PLAN_SCHEMA,
            "id": _safe_id(plan_id or "irp_" + uuid.uuid4().hex, field="plan_id"),
            "capability": {
                "id": capability.id,
                "revision": capability.revision,
                "schema_sha256": capability.schema_sha256,
            },
            "source": {
                "assignment_id": f"legacy-target-{digest}",
                "assignment_revision": 1,
                "assignment_sha256": _sha256({"legacy_deployment_revision_id": deployment_revision.id}),
                "inherited_from": "legacy_override",
            },
            "entries": [{
                "ordinal": 1,
                "profile_id": f"legacy-target-{digest}",
                "profile_revision": 1,
                "profile_schema_version": 1,
                "binding_id": f"legacy-binding-{digest}",
                "binding_revision": 1,
                "deployment_head_id": f"legacy-target-{digest}",
                "deployment_configuration_revision": 1,
                "deployment_revision_id": deployment_revision.id,
                "capability_manifest_sha256": adapted["profile"]["capability_manifest"]["sha256"],
                "boundary": boundary,
                "context_support": context,
            }],
            "retry_policy": {
                "id": policy.id,
                "revision": policy.revision,
                "sha256": policy.sha256,
                "per_entry_attempts": policy.per_entry_attempts,
                "total_physical_attempts": policy.total_physical_attempts,
                "deadline_ms": policy.deadline_ms,
                "token_budget": policy.token_budget,
                "cost_budget": policy.cost_budget,
                "tool_call_budget": policy.tool_call_budget,
                "fallback_dispositions": list(policy.fallback_dispositions),
                "retryable_dispositions": list(policy.retryable_dispositions),
            },
            "operation_policy_revision": self._operation_policy(capability, operation_policy_revision),
            "created_at": _timestamp(created),
            "deadline_at": _timestamp(created + timedelta(milliseconds=policy.deadline_ms)),
        }

    @staticmethod
    def _validate_legacy_compatibility(capability: Any, context: Mapping[str, Any], boundary: str) -> None:
        requires = capability.requires
        language_input = set(capability.input_modalities).issubset({"text"})
        if (
            not language_input
            or requires.structured_output
            or requires.structured_tools
            or requires.audio
            or requires.vision
            or requires.capability_classes
            or int(context["maximum_tokens"]) < requires.minimum_context_tokens
            or boundary not in capability.allowed_boundaries
        ):
            raise ValidationError(
                "Legacy model lacks exact capability evidence.",
                code="no_compatible_assignment",
                context={"capability_id": capability.id},
            )

    def freeze_one_shot(
        self,
        authority: Principal,
        *,
        command_id: str,
        route_request: Mapping[str, Any],
        operation_id: str,
        planning_reference: str,
        operation_plan_id: str | None = None,
    ) -> dict[str, Any]:
        """Atomically freeze route evidence and its private admitted request plan."""
        self._require_planner(authority)
        allowed_route = {"capability_id", "operation_policy_revision", "invocation_id", "subject_kind", "subject_id"}
        if operation_plan_id is not None or not isinstance(route_request, Mapping) or set(route_request) - allowed_route or "capability_id" not in route_request:
            raise ValidationError("One-shot route request has an invalid shape.", code="inference_route_plan_invalid")
        command = _safe_id(command_id, field="command_id")
        reference = _safe_id(planning_reference, field="planning_reference")
        request_hash = _sha256({"command_id": command, "route_request": dict(route_request), "operation_id": operation_id, "planning_reference": reference})
        expected_route_id = self._deterministic_id("operation-route", command, request_hash)
        expected_operation_plan_id = self._deterministic_id("operation-request", command, request_hash)
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                replay = conn.execute("SELECT * FROM inference_operation_route_request_plan_commands WHERE command_id=?", (command,)).fetchone()
                if replay is not None:
                    if str(replay["request_sha256"]) != request_hash:
                        raise ConflictError("Operation route command changed.", code="inference_operation_route_plan_command_conflict")
                    route = self._route_from_row(conn, conn.execute("SELECT * FROM inference_route_plans WHERE id=?", (replay["route_plan_id"],)).fetchone())
                    operation = self._operation_from_row(conn, conn.execute("SELECT * FROM inference_operation_route_request_plans WHERE id=?", (replay["operation_plan_id"],)).fetchone())
                    if (
                        str(replay["route_plan_sha256"]) != route["sha256"]
                        or str(replay["operation_plan_sha256"]) != operation["sha256"]
                        or operation["route_plan_id"] != route["id"]
                        or route["id"] != expected_route_id
                        or operation["id"] != expected_operation_plan_id
                        or str(operation_id) != operation["operation_id"]
                    ):
                        raise ConflictError("Stored operation route command effect is invalid.", code="inference_operation_route_plan_command_integrity_invalid")
                    conn.commit()
                    return {"route_plan": route, "operation_request_plan": operation}
                self._refuse_route_identity_collision(conn, expected_route_id)
                self._refuse_operation_identity_collision(
                    conn, operation_plan_id=expected_operation_plan_id, operation_id=operation_id
                )
                capability = self._registry.require(str(route_request["capability_id"]))
                resolved, revisions, preflight = self._resolve_in_conn(
                    conn,
                    capability=capability,
                    operation_policy_revision=self._operation_policy(
                        capability, route_request.get("operation_policy_revision")
                    ),
                    invocation_id=route_request.get("invocation_id"),
                    subject_kind=route_request.get("subject_kind"),
                    subject_id=route_request.get("subject_id"),
                    plan_id=expected_route_id,
                )
                route_material = {key: value for key, value in resolved.items() if key != "sha256"}
                evidence = self._operation_evidence(
                    conn,
                    provider_id=None,
                    planning_reference=reference,
                    operation_id=operation_id,
                    capability=capability,
                    operation_policy_revision=resolved["operation_policy_revision"],
                    freeze=True,
                )
                operation = self._operation_material(
                    route=resolved,
                    operation_id=operation_id,
                    material_snapshot_sha256=evidence["material_snapshot_sha256"],
                    entries=evidence["entries"],
                    operation_plan_id=expected_operation_plan_id,
                    frozen_preflight=preflight,
                    evidence_provider_id=evidence["provider_id"],
                    planning_reference=reference,
                    evidence_provider_revision=evidence["provider_revision"],
                    admission_evidence_ref=evidence["evidence_ref"],
                    admission_evidence_sha256=evidence["evidence_sha256"],
                )
                operation_hash = _sha256(operation)
                self._insert_route(conn, route_material, resolved["sha256"], revisions, capability_definition=capability.canonical_dict(), retry_policy_definition=self._registry.retry_policy(route_material["retry_policy"]["id"]).canonical_dict())
                self._insert_operation(
                    conn, operation, operation_hash, frozen_preflight=preflight
                )
                conn.execute("INSERT INTO inference_operation_route_request_plan_commands VALUES (?,?,?,?,?,?,?)", (command, request_hash, route_material["id"], resolved["sha256"], operation["id"], operation_hash, operation["created_at"]))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return {
            "route_plan": resolved,
            "operation_request_plan": {**operation, "sha256": operation_hash},
        }

    def get_route_plan(self, principal: Principal, plan_id: str) -> dict[str, Any]:
        self._require_inspector(principal)
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM inference_route_plans WHERE id=?",
                (_safe_id(plan_id, field="plan_id"),),
            ).fetchone()
            if row is None:
                raise NotFound("inference route plan", plan_id)
            return self._route_from_row(conn, row)

    def get_operation_request_plan(self, authority: Principal, plan_id: str) -> dict[str, Any]:
        self._require_planner(authority)
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM inference_operation_route_request_plans WHERE id=?",
                (_safe_id(plan_id, field="operation_plan_id"),),
            ).fetchone()
            if row is None:
                raise NotFound("operation route request plan", plan_id)
            return self._operation_from_row(conn, row)

    def route_leg_evidence(
        self,
        authority: Principal,
        *,
        operation_plan_id: str,
        route_leg_ordinal: int,
    ) -> dict[str, Any]:
        """Return a non-authorizing leg template; Story 06 owns attempts."""
        self._require_planner(authority)
        if type(route_leg_ordinal) is not int or route_leg_ordinal < 1:
            raise ValidationError("route leg ordinal is invalid", code="inference_route_plan_invalid")
        operation = self.get_operation_request_plan(authority, operation_plan_id)
        leg = next(
            (item for item in operation["entries"] if item["route_leg_ordinal"] == route_leg_ordinal),
            None,
        )
        if leg is None or leg["eligibility"] != "executable":
            raise ValidationError("route leg is not executable", code="inference_route_leg_unavailable")
        route = self.get_route_plan(authority, operation["route_plan_id"])
        route_leg = route["entries"][route_leg_ordinal - 1]
        return {
            "schema": "InferenceRouteLegEvidence@1",
            "route_plan_id": route["id"],
            "route_plan_sha256": route["sha256"],
            "operation_request_plan_id": operation["id"],
            "operation_request_plan_sha256": operation["sha256"],
            "route_leg_ordinal": route_leg_ordinal,
            "deployment_revision_id": route_leg["deployment_revision_id"],
            "admitted_request_id": leg["admitted_request_id"],
            "admitted_request_sha256": leg["admitted_request_sha256"],
            "context_plan_sha256": leg["context_plan_sha256"],
            "serialized_request_sha256": leg["serialized_request_sha256"],
        }

    def _resolve_entries(self, conn: Any, capability: Any, values: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[DeploymentRevision], list[dict[str, Any]]]:
        entries: list[dict[str, Any]] = []
        revisions: list[DeploymentRevision] = []
        preflight: list[dict[str, Any]] = []
        for expected, value in enumerate(values, 1):
            if int(value["ordinal"]) != expected:
                raise ConflictError("Assignment leg order is invalid.", code="inference_route_plan_integrity_invalid")
            if int(value.get("profile_schema_version", 2)) == 1:
                source_id = str(value["profile_id"]).removeprefix("legacy-")
                row = conn.execute("SELECT * FROM profiles WHERE id=? AND deleted=0", (source_id,)).fetchone()
                if row is None:
                    raise ValidationError("Legacy model is missing.", code="inference_route_profile_unavailable")
                source = SimpleNamespace(**dict(row))
                adapted = adapt_v1_profile(source)
                profile = adapted["profile"]
                binding = adapted["binding"]
                deployment = self._legacy_deployment(source)
                context = {"mode": profile["context_support"], "maximum_tokens": int(row["context_limit"] or 0)}
                readiness = "unknown"
                enabled = True
            else:
                profile_row = conn.execute(
                    "SELECT * FROM model_profile_revisions WHERE profile_id=? AND revision=?",
                    (value["profile_id"], value["profile_revision"]),
                ).fetchone()
                if profile_row is None:
                    raise ValidationError("Model profile revision is missing.", code="inference_route_profile_unavailable")
                profile_obj = self._profiles._revision_from_row(profile_row)
                profile = profile_obj.to_dict()
                binding_row = conn.execute(
                    """SELECT b.*,h.profile_id AS head_profile_id,h.revision AS head_revision,
                              h.updated_at AS updated_at
                         FROM model_profile_binding_heads h
                         JOIN model_profile_binding_revisions b
                           ON b.binding_id=h.binding_id AND b.revision=h.revision
                        WHERE h.profile_id=?""",
                    (value["profile_id"],),
                ).fetchone()
                if binding_row is None:
                    raise ValidationError("Model binding is missing.", code="inference_route_binding_unavailable")
                if (
                    str(binding_row["head_profile_id"]) != str(value["profile_id"])
                    or int(binding_row["head_revision"]) != int(binding_row["revision"])
                    or int(binding_row["profile_revision"]) != int(value["profile_revision"])
                ):
                    raise ConflictError("Model binding integrity failed.", code="inference_route_plan_integrity_invalid")
                binding = self._profiles._binding_from_row(binding_row).to_dict()
                enabled = bool(binding_row["enabled"])
                readiness = "unknown"
                observation_id = str(binding_row["readiness_observation_id"] or "")
                if observation_id:
                    observed = conn.execute("SELECT * FROM model_profile_readiness_observations WHERE observation_id=?", (observation_id,)).fetchone()
                    if observed is None or (str(observed["deployment_head_id"]), int(observed["deployment_configuration_revision"]), str(observed["deployment_revision_id"])) != (str(binding_row["deployment_head_id"]), int(binding_row["deployment_configuration_revision"]), str(binding_row["deployment_revision_id"])):
                        raise ConflictError("Binding readiness evidence is incoherent.", code="inference_route_plan_integrity_invalid")
                    readiness = str(observed["state"])
                deployment_row = conn.execute(
                    "SELECT * FROM deployment_revisions WHERE id=?",
                    (binding["deployment_revision_id"],),
                ).fetchone()
                if deployment_row is None:
                    raise ValidationError("Deployment revision is missing.", code="inference_route_deployment_unavailable")
                deployment = self._profiles._deployment_from_row(deployment_row)
                context = {"mode": profile["context_support"], "maximum_tokens": int(deployment.context_ceiling or 0)}
            boundary = _BOUNDARIES.get(str(deployment.boundary))
            if boundary not in capability.allowed_boundaries:
                raise ValidationError("Model boundary is incompatible.", code="inference_route_boundary_unsupported")
            manifest = profile["capability_manifest"]
            if int(value.get("profile_schema_version", 2)) == 1:
                if capability.requires.structured_output or capability.requires.structured_tools:
                    raise ValidationError("Legacy model lacks governed structured capability evidence.", code="no_compatible_assignment")
                if int(context["maximum_tokens"]) < capability.requires.minimum_context_tokens:
                    raise ValidationError("Legacy model context is incompatible.", code="no_compatible_assignment")
            else:
                reason = self._assignments._incompatibility(
                    profile_obj,
                    deployment,
                    set(manifest.get("claims") or []),
                    set(profile_obj.supported_modalities),
                    capability,
                )
                if reason:
                    raise ValidationError("Model profile is no longer compatible.", code="no_compatible_assignment", context={"reason_code": reason})
            entries.append({
                "ordinal": expected,
                "profile_id": str(value["profile_id"]),
                "profile_revision": int(value["profile_revision"]),
                "profile_schema_version": int(value.get("profile_schema_version", 2)),
                "binding_id": str(binding["binding_id"]),
                "binding_revision": int(binding["revision"]),
                "deployment_head_id": str(binding["deployment_head_id"]),
                "deployment_configuration_revision": int(binding.get("deployment_configuration_revision", 1)),
                "deployment_revision_id": deployment.id,
                "capability_manifest_sha256": _hash(manifest["sha256"], field="capability_manifest_sha256"),
                "boundary": boundary,
                "context_support": self._context_support(context),
            })
            revisions.append(deployment)
            preflight.append({
                "route_leg_ordinal": expected,
                "eligibility": "executable" if enabled and readiness in {"ready", "unknown"} else "known_preflight_unavailable",
                "reason_code": None if enabled and readiness in {"ready", "unknown"} else ("binding_disabled" if not enabled else "binding_not_ready"),
            })
        return entries, revisions, preflight

    @staticmethod
    def _refuse_route_identity_collision(conn: Any, plan_id: Any) -> None:
        if plan_id is None:
            return
        clean = _safe_id(plan_id, field="plan_id")
        if conn.execute("SELECT 1 FROM inference_route_plans WHERE id=?", (clean,)).fetchone() is not None:
            raise ConflictError("Route plan ID is already in use.", code="inference_route_plan_id_conflict")

    @staticmethod
    def _refuse_operation_identity_collision(conn: Any, *, operation_plan_id: Any, operation_id: Any) -> None:
        operation = _safe_id(operation_id, field="operation_id")
        plan = None if operation_plan_id is None else _safe_id(operation_plan_id, field="operation_plan_id")
        row = conn.execute("SELECT id,operation_id FROM inference_operation_route_request_plans WHERE operation_id=? OR id=?", (operation, plan or "")).fetchone()
        if row is not None:
            raise ConflictError("Operation route identity is already in use.", code="inference_operation_route_plan_id_conflict")

    @staticmethod
    def _deterministic_id(namespace: str, command_id: str, request_sha256: str) -> str:
        digest = hashlib.sha256(f"{namespace}:{command_id}:{request_sha256}".encode()).hexdigest()
        prefix = "iorp_" if namespace == "operation-request" else "irp_"
        return prefix + digest

    @staticmethod
    def _require_planner(principal: Principal | None) -> None:
        if principal != ROUTE_PLANNING_AUTHORITY:
            raise ServiceError(
                "inference_route_planner_required",
                "Inference route planning authority is required",
                context={"status": 403},
            )

    @staticmethod
    def _require_inspector(principal: Principal | None) -> None:
        if principal != ROUTE_PLANNING_AUTHORITY and (
            principal is None or principal.kind is not PrincipalKind.OWNER
        ):
            raise ServiceError(
                "inference_route_inspection_denied",
                "Route plan inspection is not permitted",
                context={"status": 403},
            )

    @staticmethod
    def _context_support(value: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(value, Mapping) or set(value) != {"mode", "maximum_tokens"}:
            raise ValidationError("context_support is invalid", code="inference_route_plan_invalid")
        mode = str(value["mode"])
        maximum = value["maximum_tokens"]
        if mode not in {"exact", "bounded", "unavailable"} or type(maximum) is not int or maximum < 0:
            raise ValidationError("context_support is invalid", code="inference_route_plan_invalid")
        return {"mode": mode, "maximum_tokens": maximum}

    @staticmethod
    def _operation_policy(capability: Any, supplied: Any) -> str:
        contract = capability.operation_contract
        expected = f"{contract.name}@{contract.version}:{capability.schema_sha256}"
        if supplied is not None and str(supplied) != expected:
            raise ValidationError(
                "operation_policy_revision does not match the capability contract",
                code="inference_operation_policy_revision_invalid",
            )
        return expected

    @staticmethod
    def _legacy_deployment(profile: Any) -> DeploymentRevision:
        """Pure v1 identity adapter: no path/key/liveness/readiness observation."""
        from ..intel.providers import profile_key_env

        profile_id = str(profile.id)
        kind = str(profile.kind or "")
        base_url = str(profile.base_url or "").strip()
        model_file = str(profile.model_file or "").strip()
        model = str(profile.model or "").strip()
        node = str(profile.node or "").strip()
        if kind == "onDevice":
            values = ("this_device", "local", "same_device", model_file or None)
            if not model and model_file:
                model = model_file.replace("\\", "/").rsplit("/", 1)[-1].rsplit(".", 1)[0]
        elif kind == "desktop":
            values = ("paired_device", "paired_runtime", "paired_device", None)
        elif kind == "meshNode":
            values = ("mesh_node", "node_runtime", "private_mesh", None)
        elif kind == "openAICompatible":
            private = _private_endpoint(base_url)
            values = (
                "private_endpoint" if private else "external_service",
                "openai_compatible",
                "private_network" if private else "external_service",
                None,
            )
        else:
            values = ("unsupported", "unknown", "unknown", None)
        deployment = DeploymentIdentity(
            destination_id=profile_id,
            kind=values[0],
            engine=values[1],
            model=model,
            node=node,
            boundary=values[2],
            model_path=values[3],
            endpoint=base_url,
            secret_slot=profile_key_env(profile_id) if bool(profile.requires_key) else "",
        )
        return DeploymentRevision.from_identity(deployment)

    def _operation_material(self, *, route: Mapping[str, Any], operation_id: str, material_snapshot_sha256: str, entries: Sequence[Mapping[str, Any]], operation_plan_id: str | None, frozen_preflight: Sequence[Mapping[str, Any]], evidence_provider_id: str, planning_reference: str, evidence_provider_revision: int, admission_evidence_ref: str, admission_evidence_sha256: str) -> dict[str, Any]:
        route_entries = route["entries"]
        if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)) or len(entries) != len(route_entries):
            raise ValidationError("Operation legs must exactly match the route.", code="inference_operation_route_plan_invalid")
        frozen: list[dict[str, Any]] = []
        for ordinal, raw in enumerate(entries, 1):
            allowed = {"route_leg_ordinal", "eligibility", "reason_code", "admitted_request_id", "admitted_request_sha256", "context_plan_sha256", "serialized_request_sha256"}
            if not isinstance(raw, Mapping) or set(raw) - allowed or set(raw) < {"route_leg_ordinal", "eligibility"}:
                raise ValidationError("Operation leg has an invalid shape.", code="inference_operation_route_plan_invalid")
            if raw["route_leg_ordinal"] != ordinal or raw["eligibility"] not in _ELIGIBILITY:
                raise ValidationError("Operation leg is invalid.", code="inference_operation_route_plan_invalid")
            executable = raw["eligibility"] == "executable"
            preflight = frozen_preflight[ordinal - 1]
            if preflight["eligibility"] != "executable" and (raw["eligibility"], raw.get("reason_code")) != (preflight["eligibility"], preflight["reason_code"]):
                raise ValidationError("Operation leg contradicts frozen preflight.", code="inference_operation_route_plan_invalid")
            if executable:
                if not raw.get("admitted_request_id") or any(not raw.get(key) for key in ("admitted_request_sha256", "context_plan_sha256", "serialized_request_sha256")):
                    raise ValidationError("Executable leg lacks admitted request evidence.", code="inference_operation_route_plan_invalid")
            elif raw.get("admitted_request_id") or any(raw.get(key) for key in ("admitted_request_sha256", "context_plan_sha256", "serialized_request_sha256")):
                raise ValidationError("Unavailable leg cannot carry admitted request evidence.", code="inference_operation_route_plan_invalid")
            frozen.append({
                "route_leg_ordinal": ordinal,
                "eligibility": str(raw["eligibility"]),
                "reason_code": None if executable else self._unavailable_reason(raw.get("reason_code"), raw["eligibility"]),
                "admitted_request_id": _safe_id(raw["admitted_request_id"], field="admitted_request_id") if executable else None,
                "admitted_request_sha256": _hash(raw["admitted_request_sha256"], field="admitted_request_sha256") if executable else None,
                "context_plan_sha256": _hash(raw["context_plan_sha256"], field="context_plan_sha256") if executable else None,
                "serialized_request_sha256": _hash(raw["serialized_request_sha256"], field="serialized_request_sha256") if executable else None,
            })
        return {
            "schema": OPERATION_ROUTE_REQUEST_PLAN_SCHEMA,
            "id": _safe_id(operation_plan_id or "iorp_" + uuid.uuid4().hex, field="operation_plan_id"),
            "route_plan_id": route["id"],
            "operation_id": _safe_id(operation_id, field="operation_id"),
            "evidence_provider_id": evidence_provider_id,
            "evidence_provider_revision": evidence_provider_revision,
            "planning_reference": planning_reference,
            "admission_evidence_ref": admission_evidence_ref,
            "admission_evidence_sha256": admission_evidence_sha256,
            "material_snapshot_sha256": _hash(material_snapshot_sha256, field="material_snapshot_sha256"),
            "entries": frozen,
            "created_at": route["created_at"],
            "deadline_at": route["deadline_at"],
        }

    def _operation_evidence(self, conn: Any, *, provider_id: str | None, planning_reference: str, operation_id: str, capability: Any, operation_policy_revision: str, freeze: bool, evidence_ref: str | None = None) -> dict[str, Any]:
        exact_capability = (capability.id, capability.revision, capability.schema_sha256)
        candidates = [provider for provider in self._operation_evidence_providers.values() if exact_capability in provider.capabilities and operation_policy_revision in provider.operation_policy_revisions]
        if provider_id is None:
            if len(candidates) != 1:
                raise ServiceError("inference_operation_evidence_provider_missing", "Exactly one admitted operation evidence provider must own this contract", context={"candidate_count": len(candidates)})
            provider = candidates[0]
        else:
            provider = self._operation_evidence_providers.get(provider_id)
        if provider is None:
            raise ServiceError(
                "inference_operation_evidence_provider_missing",
                "No admitted operation evidence provider is registered",
                context={"provider_id": provider_id},
            )
        if exact_capability not in provider.capabilities or operation_policy_revision not in provider.operation_policy_revisions:
            raise ServiceError("inference_operation_evidence_provider_incompatible", "The evidence provider cannot attest this operation contract")
        before = conn.total_changes
        value = provider.freeze(conn, planning_reference, operation_id) if freeze else provider.reconstruct(conn, str(evidence_ref))
        if not freeze and conn.total_changes != before:
            raise ConflictError("Operation evidence provider wrote during reconstruction.", code="inference_operation_evidence_invalid")
        required = {"evidence_ref", "material_snapshot_sha256", "entries"}
        if not isinstance(value, Mapping) or set(value) != required:
            raise ConflictError("Operation evidence provider returned an invalid shape.", code="inference_operation_evidence_invalid")
        material = {
            "provider_id": provider.id,
            "provider_revision": provider.revision,
            "capability": {"id": capability.id, "revision": capability.revision, "schema_sha256": capability.schema_sha256},
            "operation_policy_revision": operation_policy_revision,
            "operation_id": operation_id,
            "evidence_ref": _safe_id(value["evidence_ref"], field="evidence_ref"),
            "material_snapshot_sha256": _hash(value["material_snapshot_sha256"], field="material_snapshot_sha256"),
            "entries": list(value["entries"]),
        }
        return {**material, "evidence_sha256": _sha256(material)}

    @staticmethod
    def _unavailable_reason(value: Any, eligibility: Any) -> str:
        reason = str(value or "").strip()
        if reason not in _UNAVAILABLE_REASONS:
            raise ValidationError("Unavailable reason is invalid.", code="inference_operation_route_plan_invalid")
        if eligibility == "known_context_overflow" and reason != "context_overflow":
            raise ValidationError("Context overflow needs its exact reason.", code="inference_operation_route_plan_invalid")
        if eligibility == "known_preflight_unavailable" and reason == "context_overflow":
            raise ValidationError("Preflight reason is invalid.", code="inference_operation_route_plan_invalid")
        return reason

    def _insert_route(self, conn: Any, material: Mapping[str, Any], digest: str, revisions: Sequence[DeploymentRevision], *, capability_definition: Mapping[str, Any], retry_policy_definition: Mapping[str, Any]) -> None:
        for revision in revisions:
            conn.execute(
                """INSERT OR IGNORE INTO deployment_revisions
                   (id,schema_version,destination_id,kind,engine,model,node,boundary,endpoint,model_path,secret_slot,runtime_id,runtime_revision,artifact_id,manifest_sha256,format,architecture,context_ceiling,capability_sha256)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (revision.id, revision.schema_version, revision.destination_id, revision.kind, revision.engine, revision.model, revision.node, revision.boundary, revision.endpoint, revision.model_path if revision.schema_version == 1 else None, revision.secret_slot, revision.runtime_id, revision.runtime_revision, revision.artifact_id, revision.manifest_sha256, revision.format, revision.architecture, revision.context_ceiling, revision.capability_sha256),
            )
            stored = conn.execute("SELECT * FROM deployment_revisions WHERE id=?", (revision.id,)).fetchone()
            if stored is None or self._profiles._deployment_from_row(stored).to_dict() != revision.to_dict():
                raise ConflictError("Deployment revision integrity failed.", code="inference_route_plan_integrity_invalid")
        source, capability, policy = material["source"], material["capability"], material["retry_policy"]
        conn.execute(
            """INSERT INTO inference_route_plans
               (id,sha256,capability_id,capability_revision,capability_schema_sha256,assignment_id,assignment_revision,assignment_sha256,inherited_from,retry_policy_id,retry_policy_revision,operation_policy_revision,payload_json,state,deadline_at,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (material["id"], digest, capability["id"], capability["revision"], capability["schema_sha256"], source["assignment_id"], source["assignment_revision"], source["assignment_sha256"], source["inherited_from"], policy["id"], policy["revision"], material["operation_policy_revision"], _canonical(material), "frozen", material["deadline_at"], material["created_at"]),
        )
        for entry in material["entries"]:
            conn.execute(
                """INSERT INTO inference_route_plan_entries
                   (id,plan_id,route_leg_ordinal,profile_id,profile_revision,profile_schema_version,binding_id,binding_revision,deployment_head_id,deployment_configuration_revision,deployment_revision_id,capability_manifest_sha256,boundary,context_support_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (f"{material['id']}:{entry['ordinal']}", material["id"], entry["ordinal"], entry["profile_id"], entry["profile_revision"], entry["profile_schema_version"], entry["binding_id"], entry["binding_revision"], entry["deployment_head_id"], entry["deployment_configuration_revision"], entry["deployment_revision_id"], entry["capability_manifest_sha256"], entry["boundary"], _canonical(entry["context_support"])),
            )
        conn.execute(
            "INSERT INTO inference_route_plan_authority_evidence VALUES (?,?,?,?,?)",
            (material["id"], _canonical(capability_definition), capability_definition["schema_sha256"], _canonical(retry_policy_definition), retry_policy_definition["sha256"]),
        )

    @staticmethod
    def _insert_operation(conn: Any, material: Mapping[str, Any], digest: str, *, frozen_preflight: Sequence[Mapping[str, Any]]) -> None:
        conn.execute(
            """INSERT INTO inference_operation_route_request_plans
               (id,sha256,route_plan_id,operation_id,evidence_provider_id,evidence_provider_revision,planning_reference,admission_evidence_ref,admission_evidence_sha256,material_snapshot_sha256,payload_json,created_at,deadline_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (material["id"], digest, material["route_plan_id"], material["operation_id"], material["evidence_provider_id"], material["evidence_provider_revision"], material["planning_reference"], material["admission_evidence_ref"], material["admission_evidence_sha256"], material["material_snapshot_sha256"], _canonical(material), material["created_at"], material["deadline_at"]),
        )
        for entry in material["entries"]:
            conn.execute(
                """INSERT INTO inference_operation_route_request_plan_entries
                   (id,operation_plan_id,route_leg_ordinal,eligibility,reason_code,admitted_request_id,admitted_request_sha256,context_plan_sha256,serialized_request_sha256)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (f"{material['id']}:{entry['route_leg_ordinal']}", material["id"], entry["route_leg_ordinal"], entry["eligibility"], entry["reason_code"], entry["admitted_request_id"], entry["admitted_request_sha256"], entry["context_plan_sha256"], entry["serialized_request_sha256"]),
            )

    def _route_from_row(self, conn: Any, row: Any) -> dict[str, Any]:
        try:
            material = json.loads(str(row["payload_json"]))
            if set(material) != {"schema", "id", "capability", "source", "entries", "retry_policy", "operation_policy_revision", "created_at", "deadline_at"} or material["schema"] != ROUTE_PLAN_SCHEMA:
                raise ValueError("shape")
            digest = _sha256(material)
            self._validate_route_material(material)
            authority = conn.execute("SELECT * FROM inference_route_plan_authority_evidence WHERE plan_id=?", (material["id"],)).fetchone()
            if authority is None:
                raise ValueError("authority evidence")
            capability_definition = json.loads(str(authority["capability_definition_json"]))
            retry_definition = json.loads(str(authority["retry_policy_definition_json"]))
            if (
                set(capability_definition) == set()
                or capability_definition.get("schema_sha256") != str(authority["capability_definition_sha256"])
                or _sha256({key: value for key, value in capability_definition.items() if key != "schema_sha256"}) != capability_definition["schema_sha256"]
                or retry_definition.get("sha256") != str(authority["retry_policy_definition_sha256"])
                or _sha256({key: value for key, value in retry_definition.items() if key != "sha256"}) != retry_definition["sha256"]
            ):
                raise ValueError("authority hash")
            expected_retry = {
                "id": retry_definition["id"], "revision": retry_definition["revision"], "sha256": retry_definition["sha256"],
                "per_entry_attempts": retry_definition["per_entry_attempts"], "total_physical_attempts": retry_definition["total_physical_attempts"],
                "deadline_ms": retry_definition["deadline_ms"], "token_budget": retry_definition["token_budget"], "cost_budget": retry_definition["cost_budget"],
                "tool_call_budget": retry_definition["tool_call_budget"], "fallback_dispositions": retry_definition["fallback_dispositions"],
                "retryable_dispositions": retry_definition["retryable_dispositions"],
            }
            if material["retry_policy"] != expected_retry or material["capability"] != {"id": capability_definition["id"], "revision": capability_definition["revision"], "schema_sha256": capability_definition["schema_sha256"]}:
                raise ValueError("authority cross bind")
            normalized = [dict(item) for item in conn.execute("SELECT route_leg_ordinal,profile_id,profile_revision,profile_schema_version,binding_id,binding_revision,deployment_head_id,deployment_configuration_revision,deployment_revision_id,capability_manifest_sha256,boundary,context_support_json FROM inference_route_plan_entries WHERE plan_id=? ORDER BY route_leg_ordinal", (material["id"],)).fetchall()]
            expected = [{"route_leg_ordinal": e["ordinal"], "profile_id": e["profile_id"], "profile_revision": e["profile_revision"], "profile_schema_version": e["profile_schema_version"], "binding_id": e["binding_id"], "binding_revision": e["binding_revision"], "deployment_head_id": e["deployment_head_id"], "deployment_configuration_revision": e["deployment_configuration_revision"], "deployment_revision_id": e["deployment_revision_id"], "capability_manifest_sha256": e["capability_manifest_sha256"], "boundary": e["boundary"], "context_support_json": _canonical(e["context_support"])} for e in material["entries"]]
            if digest != str(row["sha256"]) or normalized != expected or material["id"] != str(row["id"]) or str(row["state"]) != "frozen":
                raise ValueError("cross bind")
            if (material["capability"]["id"], material["capability"]["revision"], material["capability"]["schema_sha256"], material["source"]["assignment_id"], material["source"]["assignment_revision"], material["source"]["assignment_sha256"], material["source"]["inherited_from"], material["retry_policy"]["id"], material["retry_policy"]["revision"], material["operation_policy_revision"], material["deadline_at"], material["created_at"]) != (str(row["capability_id"]), int(row["capability_revision"]), str(row["capability_schema_sha256"]), str(row["assignment_id"]), int(row["assignment_revision"]), str(row["assignment_sha256"]), str(row["inherited_from"]), str(row["retry_policy_id"]), int(row["retry_policy_revision"]), str(row["operation_policy_revision"]), str(row["deadline_at"]), str(row["created_at"])):
                raise ValueError("columns")
            for entry in material["entries"]:
                deployment_row = conn.execute("SELECT * FROM deployment_revisions WHERE id=?", (entry["deployment_revision_id"],)).fetchone()
                if deployment_row is None or self._profiles._deployment_from_row(deployment_row).id != entry["deployment_revision_id"]:
                    raise ValueError("deployment")
            if material["source"]["inherited_from"] != "legacy_override":
                source_row = conn.execute("SELECT * FROM inference_assignment_revisions WHERE assignment_id=? AND revision=?", (material["source"]["assignment_id"], material["source"]["assignment_revision"])).fetchone()
                if source_row is None or str(source_row["sha256"]) != material["source"]["assignment_sha256"]:
                    raise ValueError("assignment")
                source_material = self._assignments._assignment_material(conn, source_row)
                assignment_entries = [{key: entry[key] for key in ("ordinal", "profile_id", "profile_revision", "profile_schema_version")} for entry in material["entries"]]
                if source_material["entries"] != assignment_entries:
                    raise ValueError("assignment chain")
            for entry in material["entries"]:
                if entry["profile_schema_version"] == 1:
                    continue
                profile_row = conn.execute("SELECT * FROM model_profile_revisions WHERE profile_id=? AND revision=?", (entry["profile_id"], entry["profile_revision"])).fetchone()
                binding_row = conn.execute("SELECT * FROM model_profile_binding_revisions WHERE binding_id=? AND revision=?", (entry["binding_id"], entry["binding_revision"])).fetchone()
                if profile_row is None or binding_row is None:
                    raise ValueError("profile binding")
                profile = self._profiles._revision_from_row(profile_row)
                if profile.capability_manifest["sha256"] != entry["capability_manifest_sha256"]:
                    raise ValueError("profile manifest")
                if (str(binding_row["profile_id"]), int(binding_row["profile_revision"]), str(binding_row["deployment_head_id"]), int(binding_row["deployment_configuration_revision"]), str(binding_row["deployment_revision_id"])) != (entry["profile_id"], entry["profile_revision"], entry["deployment_head_id"], entry["deployment_configuration_revision"], entry["deployment_revision_id"]):
                    raise ValueError("binding cross bind")
                deployment_row = conn.execute("SELECT * FROM deployment_revisions WHERE id=?", (entry["deployment_revision_id"],)).fetchone()
                deployment = self._profiles._deployment_from_row(deployment_row)
                if _BOUNDARIES.get(deployment.boundary) != entry["boundary"] or entry["context_support"] != {"mode": profile.context_support, "maximum_tokens": int(deployment.context_ceiling or 0)}:
                    raise ValueError("deployment facts")
            return {**material, "sha256": digest}
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ConflictError("Stored route plan integrity could not be verified.", code="inference_route_plan_integrity_invalid") from exc

    def _operation_from_row(self, conn: Any, row: Any) -> dict[str, Any]:
        try:
            material = json.loads(str(row["payload_json"]))
            if set(material) != {"schema", "id", "route_plan_id", "operation_id", "evidence_provider_id", "evidence_provider_revision", "planning_reference", "admission_evidence_ref", "admission_evidence_sha256", "material_snapshot_sha256", "entries", "created_at", "deadline_at"} or material["schema"] != OPERATION_ROUTE_REQUEST_PLAN_SCHEMA:
                raise ValueError("shape")
            digest = _sha256(material)
            self._route_from_row(conn, conn.execute("SELECT * FROM inference_route_plans WHERE id=?", (material["route_plan_id"],)).fetchone())
            normalized = [dict(item) for item in conn.execute("SELECT route_leg_ordinal,eligibility,reason_code,admitted_request_id,admitted_request_sha256,context_plan_sha256,serialized_request_sha256 FROM inference_operation_route_request_plan_entries WHERE operation_plan_id=? ORDER BY route_leg_ordinal", (material["id"],)).fetchall()]
            route = self._route_from_row(conn, conn.execute("SELECT * FROM inference_route_plans WHERE id=?", (material["route_plan_id"],)).fetchone())
            capability = SimpleNamespace(id=route["capability"]["id"], revision=route["capability"]["revision"], schema_sha256=route["capability"]["schema_sha256"])
            evidence = self._operation_evidence(conn, provider_id=material["evidence_provider_id"], planning_reference=material["planning_reference"], operation_id=material["operation_id"], capability=capability, operation_policy_revision=route["operation_policy_revision"], freeze=False, evidence_ref=material["admission_evidence_ref"])
            if evidence["evidence_sha256"] != material["admission_evidence_sha256"] or evidence["provider_revision"] != material["evidence_provider_revision"]:
                raise ValueError("provider evidence")
            authoritative = self._operation_material(route=route, operation_id=material["operation_id"], material_snapshot_sha256=evidence["material_snapshot_sha256"], entries=evidence["entries"], operation_plan_id=material["id"], frozen_preflight=evidence["entries"], evidence_provider_id=material["evidence_provider_id"], planning_reference=material["planning_reference"], evidence_provider_revision=evidence["provider_revision"], admission_evidence_ref=evidence["evidence_ref"], admission_evidence_sha256=evidence["evidence_sha256"])
            if authoritative != material:
                raise ValueError("admission authority")
            if digest != str(row["sha256"]) or normalized != material["entries"] or (material["id"], material["route_plan_id"], material["operation_id"], material["evidence_provider_id"], material["evidence_provider_revision"], material["planning_reference"], material["admission_evidence_ref"], material["admission_evidence_sha256"], material["material_snapshot_sha256"], material["created_at"], material["deadline_at"]) != (str(row["id"]), str(row["route_plan_id"]), str(row["operation_id"]), str(row["evidence_provider_id"]), int(row["evidence_provider_revision"]), str(row["planning_reference"]), str(row["admission_evidence_ref"]), str(row["admission_evidence_sha256"]), str(row["material_snapshot_sha256"]), str(row["created_at"]), str(row["deadline_at"])):
                raise ValueError("cross bind")
            return {**material, "sha256": digest}
        except (KeyError, TypeError, ValueError, json.JSONDecodeError, AttributeError) as exc:
            raise ConflictError("Stored operation route plan integrity could not be verified.", code="inference_operation_route_plan_integrity_invalid") from exc

    def _validate_route_material(self, material: Mapping[str, Any]) -> None:
        if set(material["capability"]) != {"id", "revision", "schema_sha256"} or set(material["source"]) != {"assignment_id", "assignment_revision", "assignment_sha256", "inherited_from"}:
            raise ValueError("nested shape")
        retry_keys = {"id", "revision", "sha256", "per_entry_attempts", "total_physical_attempts", "deadline_ms", "token_budget", "cost_budget", "tool_call_budget", "fallback_dispositions", "retryable_dispositions"}
        if set(material["retry_policy"]) != retry_keys or not 1 <= len(material["entries"]) <= 4:
            raise ValueError("retry shape")
        for ordinal, entry in enumerate(material["entries"], 1):
            if set(entry) != {"ordinal", "profile_id", "profile_revision", "profile_schema_version", "binding_id", "binding_revision", "deployment_head_id", "deployment_configuration_revision", "deployment_revision_id", "capability_manifest_sha256", "boundary", "context_support"} or entry["ordinal"] != ordinal:
                raise ValueError("entry shape")
            self._context_support(entry["context_support"])
            _hash(entry["capability_manifest_sha256"], field="capability_manifest_sha256")


__all__ = [
    "InferenceRoutePlanService",
    "OPERATION_ROUTE_REQUEST_PLAN_SCHEMA",
    "ROUTE_PLAN_SCHEMA",
    "ROUTE_PLANNING_AUTHORITY",
    "RouteAdmissionEvidenceProvider",
]
