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
from .inference_service_route_policy import (
    ServiceRoutePolicyRegistry,
    builtin_service_route_policy_registry,
)
from .model_profile_service import (
    ModelProfileService,
    adapt_v1_profile,
)
from .tool_capability_service import (
    ToolCapabilityError,
    ToolCapabilityFoundation,
    parse_capability_manifest,
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
    reconstruct_attempt_budgets: Callable[[Any, str], Mapping[str, Any]] | None = None
    freeze_resolved: Callable[
        [Any, str, str, Mapping[str, Any], Sequence[Mapping[str, Any]]],
        Mapping[str, Any],
    ] | None = None


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
        service_route_policies: ServiceRoutePolicyRegistry | None = None,
        tool_capability_foundation: ToolCapabilityFoundation | None = None,
    ) -> None:
        self._db = db
        self._registry = registry or process_inference_capability_registry()
        self._assignments = InferenceAssignmentService(
            db,
            registry=self._registry,
            tool_capability_foundation=tool_capability_foundation,
        )
        self._profiles = ModelProfileService(db)
        self._clock = clock
        self._service_route_policies = (
            service_route_policies
            or builtin_service_route_policy_registry(capability_registry=self._registry)
        )
        self._operation_evidence_providers = {
            provider.id: provider for provider in operation_evidence_providers
        }
        if len(self._operation_evidence_providers) != len(operation_evidence_providers):
            raise ValueError("duplicate route admission evidence provider")
        owned: set[tuple[tuple[str, int, str], str]] = set()
        for provider in operation_evidence_providers:
            _safe_id(provider.id, field="evidence_provider_id")
            if type(provider.revision) is not int or provider.revision < 1 or not callable(provider.freeze) or not callable(provider.reconstruct) or (provider.reconstruct_attempt_budgets is not None and not callable(provider.reconstruct_attempt_budgets)) or (provider.freeze_resolved is not None and not callable(provider.freeze_resolved)):
                raise ValueError("invalid route admission evidence provider")
            claims = {
                (capability, policy)
                for capability in provider.capabilities
                for policy in provider.operation_policy_revisions
            }
            if owned & claims:
                raise ValueError("ambiguous route admission evidence provider")
            owned.update(claims)

    def bind_tool_capability_foundation(
        self, foundation: ToolCapabilityFoundation
    ) -> None:
        """Bind the executable ToolTurn foundation through startup composition."""
        self._assignments.bind_tool_capability_foundation(foundation)

    def register_operation_evidence_provider(
        self, provider: RouteAdmissionEvidenceProvider
    ) -> None:
        """Register one internal evidence owner before any route is frozen.

        This remains a composition seam, not a feature request surface.  A
        ToolTurn parent needs its own evidence owner so no Ask/Recipe/Workbench
        adopter can accidentally become the first tool-bearing executor.
        """
        _safe_id(provider.id, field="evidence_provider_id")
        if (
            type(provider.revision) is not int
            or provider.revision < 1
            or not callable(provider.freeze)
            or not callable(provider.reconstruct)
            or (provider.reconstruct_attempt_budgets is not None and not callable(provider.reconstruct_attempt_budgets))
            or (provider.freeze_resolved is not None and not callable(provider.freeze_resolved))
        ):
            raise ValueError("invalid route admission evidence provider")
        if provider.id in self._operation_evidence_providers:
            raise ValueError("duplicate route admission evidence provider")
        claims = {
            (capability, policy)
            for capability in provider.capabilities
            for policy in provider.operation_policy_revisions
        }
        existing = {
            (capability, policy)
            for registered in self._operation_evidence_providers.values()
            for capability in registered.capabilities
            for policy in registered.operation_policy_revisions
        }
        if claims & existing:
            raise ValueError("ambiguous route admission evidence provider")
        self._operation_evidence_providers[provider.id] = provider

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

    def resolve_route_plan_for_feature(
        self,
        authority: Principal,
        *,
        feature_principal: Principal,
        parent_kind: str,
        capability_id: str,
        operation_policy_revision: str | None = None,
        invocation_id: str | None = None,
        subject_kind: str | None = None,
        subject_id: str | None = None,
        deadline_at: float | None = None,
    ) -> dict[str, Any]:
        """Pure feature-principal resolution using the freeze policy election."""
        self._require_planner(authority)
        capability = self._registry.require(capability_id)
        policy_revision = self._operation_policy(capability, operation_policy_revision)
        principal_policy = self._feature_principal_policy(
            feature_principal, parent_kind=parent_kind, capability=capability
        )
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
                    plan_id=None,
                    deadline_at=deadline_at,
                    assignment_sources=principal_policy["assignment_sources"],
                    allowed_boundaries=principal_policy["allowed_boundaries"],
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
        deadline_at: float | None = None,
        assignment_sources: Sequence[str] | None = None,
        allowed_boundaries: Sequence[str] | None = None,
    ) -> tuple[dict[str, Any], list[DeploymentRevision], list[dict[str, Any]]]:
        assignment, inherited_from = self._assignment_snapshot(
            conn,
            capability=capability,
            invocation_id=invocation_id,
            subject_kind=subject_kind,
            subject_id=subject_id,
            assignment_sources=assignment_sources,
        )
        entries, private_revisions, preflight = self._resolve_entries(
            conn, capability, assignment["entries"]
        )
        if allowed_boundaries is not None:
            denied = [
                entry["boundary"]
                for entry in entries
                if entry["boundary"] not in set(allowed_boundaries)
            ]
            if denied:
                raise ValidationError(
                    "Feature principal policy does not permit this route boundary.",
                    code="inference_service_route_policy_denied",
                )
        retry_policy = self._registry.retry_policy(
            assignment["retry_policy_id"] or capability.default_retry_policy_id
        )
        created = self._clock()
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        created_at = _timestamp(created)
        deadline = (
            datetime.fromtimestamp(float(deadline_at), tz=timezone.utc)
            if deadline_at is not None
            else created + timedelta(milliseconds=retry_policy.deadline_ms)
        )
        if deadline <= created:
            raise ValidationError("Route deadline has elapsed.", code="inference_route_plan_invalid")
        deadline_at_text = _timestamp(deadline)
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
            "deadline_at": deadline_at_text,
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
        assignment_sources: Sequence[str] | None = None,
    ) -> tuple[dict[str, Any], str]:
        keys: list[tuple[str, str]] = []
        if invocation_id:
            keys.append((f"invocation:{_safe_id(invocation_id, field='invocation_id')}:capability:{capability.id}", "invocation"))
        if subject_kind or subject_id:
            if subject_kind not in {"thought", "workbench", "agent", "recipe", "project"} or not subject_id:
                raise ValidationError("subject is invalid", code="inference_route_plan_invalid")
            keys.append((f"subject:{subject_kind}:{_safe_id(subject_id, field='subject_id')}:capability:{capability.id}", "subject"))
        keys.extend(((f"capability:{capability.id}", "capability"), (f"group:{capability.group_id}", "group"), ("global", "global")))
        permitted = None if assignment_sources is None else set(assignment_sources)
        for key, inherited in keys:
            if permitted is not None and inherited not in permitted:
                continue
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
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                resolved = self.freeze_route_plan_in_transaction(
                    authority, conn, command_id=command_id, **request
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return resolved

    def freeze_route_plan_in_transaction(
        self, authority: Principal, conn: Any, *, command_id: str, **request: Any
    ) -> dict[str, Any]:
        """Freeze one route inside an adopter-owned composite transaction."""
        return self._freeze_route_plan_in_transaction(
            authority, conn, command_id=command_id, principal_policy=None, **request
        )

    def freeze_route_plan_for_feature_in_transaction(
        self,
        authority: Principal,
        conn: Any,
        *,
        command_id: str,
        feature_principal: Principal,
        parent_kind: str,
        **request: Any,
    ) -> dict[str, Any]:
        """Freeze with the feature principal's explicit inheritance policy.

        This is the only lawful route-freeze primitive for SERVICE work.  It
        records a private policy proof and never consults ambient OWNER group
        or global assignments for a service principal.
        """
        capability = self._registry.require(str(request.get("capability_id") or ""))
        principal_policy = self._feature_principal_policy(
            feature_principal, parent_kind=parent_kind, capability=capability
        )
        return self._freeze_route_plan_in_transaction(
            authority,
            conn,
            command_id=command_id,
            principal_policy=principal_policy,
            **request,
        )

    def freeze_capability_only_owner_route_in_transaction(
        self,
        authority: Principal,
        conn: Any,
        *,
        command_id: str,
        feature_principal: Principal,
        parent_kind: str,
        **request: Any,
    ) -> dict[str, Any]:
        """Freeze the exact owner-visible capability row, never ambient fallback.

        Parentless local-model warming is deliberately narrower than ordinary
        owner work: it derives its warrant from the one selected
        ``speech.transcribe`` capability assignment.  Group/global rows are not
        an alternate source of authority for a process-wide service warm.
        """
        if feature_principal.kind is not PrincipalKind.OWNER:
            raise ValidationError(
                "Capability-only preload source requires owner authority.",
                code="inference_route_plan_invalid",
            )
        capability = self._registry.require(str(request.get("capability_id") or ""))
        policy = self._feature_principal_policy(
            feature_principal, parent_kind=parent_kind, capability=capability
        )
        material = dict(policy["policy_material"])
        material.update(
            {
                "id": "owner-capability-only-preload-source@1",
                "assignment_sources": ["capability"],
            }
        )
        policy = {
            **policy,
            "policy_id": "owner-capability-only-preload-source@1",
            "policy_material": material,
            "policy_sha256": _sha256(material),
            "assignment_sources": ["capability"],
        }
        return self._freeze_route_plan_in_transaction(
            authority, conn, command_id=command_id, principal_policy=policy, **request
        )

    def freeze_derived_preload_for_transcription_in_transaction(
        self,
        authority: Principal,
        conn: Any,
        *,
        command_id: str,
        feature_principal: Principal,
        parent_kind: str,
        transcription_route_plan_id: str,
    ) -> dict[str, Any]:
        """Derive internal preload from one frozen transcription deployment.

        This copies already-frozen assignment/deployment facts and therefore never
        performs a second assignment lookup for ``speech.preload``.  The normal
        route-row validator still reconstructs the copied transcription selection.
        """
        self._require_planner(authority)
        command = _safe_id(command_id, field="command_id")
        source_id = _safe_id(transcription_route_plan_id, field="transcription_route_plan_id")
        source_row = conn.execute(
            "SELECT * FROM inference_route_plans WHERE id=?", (source_id,)
        ).fetchone()
        if source_row is None:
            raise ValidationError(
                "Transcription route is missing.", code="inference_route_plan_invalid"
            )
        source = self._route_from_row(conn, source_row)
        if source["capability"]["id"] != "speech.transcribe":
            raise ValidationError(
                "Derived preload requires a transcription route.",
                code="inference_route_plan_invalid",
            )
        capability = self._registry.require("speech.preload")
        policy = self._registry.retry_policy(capability.default_retry_policy_id)
        principal_policy = self._feature_principal_policy(
            feature_principal, parent_kind=parent_kind, capability=capability
        )
        request_hash = _sha256(
            {
                "command_id": command,
                "transcription_route_plan_id": source["id"],
                "transcription_route_plan_sha256": source["sha256"],
                "capability": capability.canonical_dict(),
                "retry_policy": policy.canonical_dict(),
                "principal_policy_sha256": _sha256(principal_policy),
            }
        )
        expected_plan_id = self._deterministic_id("derived-preload", command, request_hash)
        replay = conn.execute(
            "SELECT * FROM inference_route_plan_commands WHERE command_id=?", (command,)
        ).fetchone()
        if replay is not None:
            if str(replay["request_sha256"]) != request_hash:
                raise ConflictError(
                    "Derived preload command changed.",
                    code="inference_route_plan_command_conflict",
                )
            result = self._route_from_row(
                conn,
                conn.execute(
                    "SELECT * FROM inference_route_plans WHERE id=?", (replay["plan_id"],)
                ).fetchone(),
            )
            if str(replay["plan_sha256"]) != result["sha256"] or result["id"] != expected_plan_id:
                raise ConflictError(
                    "Stored derived preload effect is invalid.",
                    code="inference_route_plan_command_integrity_invalid",
                )
            return result
        self._refuse_route_identity_collision(conn, expected_plan_id)
        material = {
            **{key: value for key, value in source.items() if key != "sha256"},
            "id": expected_plan_id,
            "capability": {
                "id": capability.id,
                "revision": capability.revision,
                "schema_sha256": capability.schema_sha256,
            },
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
            "operation_policy_revision": self._operation_policy(capability, None),
        }
        digest = _sha256(material)
        revisions = [
            self._profiles._deployment_from_row(
                conn.execute(
                    "SELECT * FROM deployment_revisions WHERE id=?",
                    (entry["deployment_revision_id"],),
                ).fetchone()
            )
            for entry in material["entries"]
        ]
        self._insert_route(
            conn,
            material,
            digest,
            revisions,
            capability_definition=capability.canonical_dict(),
            retry_policy_definition=policy.canonical_dict(),
            principal_policy_evidence=principal_policy,
        )
        conn.execute(
            "INSERT INTO inference_route_plan_commands (command_id, request_sha256, plan_id, plan_sha256, created_at) VALUES (?,?,?,?,?)",
            (command, request_hash, material["id"], digest, material["created_at"]),
        )
        return {**material, "sha256": digest}

    def _freeze_route_plan_in_transaction(
        self,
        authority: Principal,
        conn: Any,
        *,
        command_id: str,
        principal_policy: Mapping[str, Any] | None,
        **request: Any,
    ) -> dict[str, Any]:
        self._require_planner(authority)
        allowed = {"capability_id", "operation_policy_revision", "invocation_id", "subject_kind", "subject_id", "deadline_at"}
        if set(request) - allowed or "capability_id" not in request:
            raise ValidationError("Route freeze request has an invalid shape.", code="inference_route_plan_invalid")
        command = _safe_id(command_id, field="command_id")
        request_hash = _sha256(
            {
                "command_id": command,
                **request,
                "principal_policy_sha256": None
                if principal_policy is None
                else _sha256(principal_policy),
            }
        )
        expected_plan_id = self._deterministic_id("route", command, request_hash)
        replay = conn.execute(
            "SELECT * FROM inference_route_plan_commands WHERE command_id=?", (command,)
        ).fetchone()
        if replay is not None:
            if str(replay["request_sha256"]) != request_hash:
                raise ConflictError("Route command changed.", code="inference_route_plan_command_conflict")
            result = self._route_from_row(conn, conn.execute(
                "SELECT * FROM inference_route_plans WHERE id=?", (replay["plan_id"],)
            ).fetchone())
            if str(replay["plan_sha256"]) != result["sha256"] or result["id"] != expected_plan_id:
                raise ConflictError("Stored route command effect is invalid.", code="inference_route_plan_command_integrity_invalid")
            return result
        self._refuse_route_identity_collision(conn, expected_plan_id)
        capability = self._registry.require(str(request["capability_id"]))
        policy_revision = self._operation_policy(capability, request.get("operation_policy_revision"))
        resolved, revisions, preflight = self._resolve_in_conn(
            conn, capability=capability, operation_policy_revision=policy_revision,
            invocation_id=request.get("invocation_id"), subject_kind=request.get("subject_kind"),
            subject_id=request.get("subject_id"), plan_id=expected_plan_id,
            deadline_at=request.get("deadline_at"),
            assignment_sources=None
            if principal_policy is None
            else principal_policy["assignment_sources"],
            allowed_boundaries=None
            if principal_policy is None
            else principal_policy["allowed_boundaries"],
        )
        material = {key: value for key, value in resolved.items() if key != "sha256"}
        self._insert_route(
            conn, material, resolved["sha256"], revisions,
            capability_definition=capability.canonical_dict(),
            retry_policy_definition=self._registry.retry_policy(material["retry_policy"]["id"]).canonical_dict(),
            frozen_preflight=preflight,
            principal_policy_evidence=principal_policy,
        )
        conn.execute(
            "INSERT INTO inference_route_plan_commands (command_id, request_sha256, plan_id, plan_sha256, created_at) VALUES (?,?,?,?,?)",
            (command, request_hash, material["id"], resolved["sha256"], material["created_at"]),
        )
        return resolved

    def _feature_principal_policy(
        self, principal: Principal, *, parent_kind: str, capability: Any
    ) -> dict[str, Any]:
        if principal.kind is PrincipalKind.OWNER:
            policy_material = {
                "schema": "InferenceOwnerRoutePolicy@1",
                "id": "owner-route-inheritance@1",
                "revision": 1,
                "assignment_sources": [
                    "invocation",
                    "subject",
                    "capability",
                    "group",
                    "global",
                ],
                "allowed_boundaries": list(capability.allowed_boundaries),
            }
            return {
                "schema": "InferenceFeaturePrincipalPolicyEvidence@1",
                "principal_kind": "owner",
                "policy_id": "owner-route-inheritance@1",
                "policy_revision": 1,
                "policy_sha256": _sha256(policy_material),
                "policy_material": policy_material,
                "principal_identity": "",
                "authority_basis": "owner-authenticated",
                "allowed_operations": [],
                "parent_kind": str(parent_kind),
                "capability": {
                    "id": capability.id,
                    "revision": capability.revision,
                    "schema_sha256": capability.schema_sha256,
                },
                "allowed_boundaries": list(capability.allowed_boundaries),
                "assignment_sources": [
                    "invocation",
                    "subject",
                    "capability",
                    "group",
                    "global",
                ],
            }
        return self._service_route_policies.authorize(
            principal, parent_kind=parent_kind, capability_id=capability.id
        )

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
                self._insert_route(conn, material, route_hash, [deployment_revision], capability_definition=capability.canonical_dict(), retry_policy_definition=policy.canonical_dict(), frozen_preflight=({"route_leg_ordinal": 1, "eligibility": "executable", "reason_code": None},))
                conn.execute("INSERT INTO inference_route_plan_commands (command_id, request_sha256, plan_id, plan_sha256, created_at) VALUES (?,?,?,?,?)", (command, request_hash, material["id"], route_hash, material["created_at"]))
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
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                result = self._freeze_one_shot_in_transaction(
                    authority,
                    conn,
                    command_id=command_id,
                    route_request=route_request,
                    operation_id=operation_id,
                    planning_reference=planning_reference,
                    operation_plan_id=operation_plan_id,
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return result

    def _freeze_one_shot_in_transaction(
        self,
        authority: Principal,
        conn: Any,
        *,
        command_id: str,
        route_request: Mapping[str, Any],
        operation_id: str,
        planning_reference: str,
        operation_plan_id: str | None = None,
    ) -> dict[str, Any]:
        """Freeze route + operation evidence in a caller-owned transaction.

        Production composite owners use this seam so their logical reservation,
        private material, route/operation pair, and controller start commit or
        roll back together.  It never begins, commits, or rolls back ``conn``.
        """
        self._require_planner(authority)
        allowed_route = {"capability_id", "operation_policy_revision", "invocation_id", "subject_kind", "subject_id"}
        if operation_plan_id is not None or not isinstance(route_request, Mapping) or set(route_request) - allowed_route or "capability_id" not in route_request:
            raise ValidationError("One-shot route request has an invalid shape.", code="inference_route_plan_invalid")
        command = _safe_id(command_id, field="command_id")
        reference = _safe_id(planning_reference, field="planning_reference")
        request_hash = _sha256({"command_id": command, "route_request": dict(route_request), "operation_id": operation_id, "planning_reference": reference})
        expected_route_id = self._deterministic_id("operation-route", command, request_hash)
        expected_operation_plan_id = self._deterministic_id("operation-request", command, request_hash)
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
            return {"route_plan": route, "operation_request_plan": operation}
        self._refuse_route_identity_collision(conn, expected_route_id)
        self._refuse_operation_identity_collision(conn, operation_plan_id=expected_operation_plan_id, operation_id=operation_id)
        capability = self._registry.require(str(route_request["capability_id"]))
        resolved, revisions, preflight = self._resolve_in_conn(
            conn, capability=capability,
            operation_policy_revision=self._operation_policy(capability, route_request.get("operation_policy_revision")),
            invocation_id=route_request.get("invocation_id"), subject_kind=route_request.get("subject_kind"),
            subject_id=route_request.get("subject_id"), plan_id=expected_route_id,
        )
        route_material = {key: value for key, value in resolved.items() if key != "sha256"}
        evidence = self._operation_evidence(
            conn, provider_id=None, planning_reference=reference, operation_id=operation_id,
            capability=capability, operation_policy_revision=resolved["operation_policy_revision"],
            freeze=True, resolved_route=resolved, frozen_preflight=preflight,
        )
        operation = self._operation_material(
            route=resolved, operation_id=operation_id,
            material_snapshot_sha256=evidence["material_snapshot_sha256"], entries=evidence["entries"],
            operation_plan_id=expected_operation_plan_id, frozen_preflight=preflight,
            evidence_provider_id=evidence["provider_id"], planning_reference=reference,
            evidence_provider_revision=evidence["provider_revision"],
            admission_evidence_ref=evidence["evidence_ref"], admission_evidence_sha256=evidence["evidence_sha256"],
        )
        operation_hash = _sha256(operation)
        budget_provider = self._operation_evidence_providers.get(str(operation["evidence_provider_id"]))
        budget_material = None
        if budget_provider is not None and budget_provider.reconstruct_attempt_budgets is not None:
            budget_material = self._attempt_budget_material_in_transaction(
                ROUTE_PLANNING_AUTHORITY, conn, operation={**operation, "sha256": operation_hash}, route=resolved,
            )
        self._insert_route(conn, route_material, resolved["sha256"], revisions, capability_definition=capability.canonical_dict(), retry_policy_definition=self._registry.retry_policy(route_material["retry_policy"]["id"]).canonical_dict(), frozen_preflight=preflight)
        self._insert_operation(conn, operation, operation_hash, frozen_preflight=preflight)
        if budget_material is not None:
            conn.execute(
                """INSERT INTO inference_operation_route_attempt_budget_evidence
                   (operation_plan_id,provider_id,provider_revision,evidence_ref,
                    material_snapshot_sha256,payload_json,sha256) VALUES (?,?,?,?,?,?,?)""",
                (operation["id"], budget_material["provider_id"], budget_material["provider_revision"], operation["admission_evidence_ref"], operation["material_snapshot_sha256"], _canonical(budget_material), _sha256(budget_material)),
            )
        conn.execute("INSERT INTO inference_operation_route_request_plan_commands (command_id, request_sha256, route_plan_id, route_plan_sha256, operation_plan_id, operation_plan_sha256, created_at) VALUES (?,?,?,?,?,?,?)", (command, request_hash, route_material["id"], resolved["sha256"], operation["id"], operation_hash, operation["created_at"]))
        return {"route_plan": resolved, "operation_request_plan": {**operation, "sha256": operation_hash}}

    def freeze_operation_for_route(
        self,
        authority: Principal,
        *,
        command_id: str,
        route_plan_id: str,
        operation_id: str,
        planning_reference: str,
    ) -> dict[str, Any]:
        """Attach exact operation material to an already-frozen route.

        Speech sessions freeze assignment/deployment truth at logical admission,
        then use this seam once transcript-derived material exists. No mutable
        assignment, profile, binding, readiness, or Config selector is reread.
        """
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                result = self.freeze_operation_for_route_in_transaction(
                    authority, conn, command_id=command_id,
                    route_plan_id=route_plan_id, operation_id=operation_id,
                    planning_reference=planning_reference,
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return result

    def freeze_operation_for_route_in_transaction(
        self,
        authority: Principal,
        conn: Any,
        *,
        command_id: str,
        route_plan_id: str,
        operation_id: str,
        planning_reference: str,
    ) -> dict[str, Any]:
        self._require_planner(authority)
        command = _safe_id(command_id, field="command_id")
        route_id = _safe_id(route_plan_id, field="route_plan_id")
        operation_key = _safe_id(operation_id, field="operation_id")
        reference = _safe_id(planning_reference, field="planning_reference")
        request_hash = _sha256({
            "command_id": command, "route_plan_id": route_id,
            "operation_id": operation_key, "planning_reference": reference,
        })
        expected_operation_id = self._deterministic_id("operation-request", command, request_hash)
        replay = conn.execute(
            "SELECT * FROM inference_operation_route_request_plan_commands WHERE command_id=?",
            (command,),
        ).fetchone()
        if replay is not None:
            if str(replay["request_sha256"]) != request_hash:
                raise ConflictError("Operation route command changed.", code="inference_operation_route_plan_command_conflict")
            route = self._route_from_row(conn, conn.execute("SELECT * FROM inference_route_plans WHERE id=?", (replay["route_plan_id"],)).fetchone())
            operation = self._operation_from_row(conn, conn.execute("SELECT * FROM inference_operation_route_request_plans WHERE id=?", (replay["operation_plan_id"],)).fetchone())
            if route["id"] != route_id or operation["id"] != expected_operation_id or operation["operation_id"] != operation_key or operation["route_plan_id"] != route_id or str(replay["route_plan_sha256"]) != route["sha256"] or str(replay["operation_plan_sha256"]) != operation["sha256"]:
                raise ConflictError("Stored operation route command effect is invalid.", code="inference_operation_route_plan_command_integrity_invalid")
            return {"route_plan": route, "operation_request_plan": operation}
        route = self._route_from_row(
            conn, conn.execute("SELECT * FROM inference_route_plans WHERE id=?", (route_id,)).fetchone()
        )
        self._refuse_operation_identity_collision(
            conn, operation_plan_id=expected_operation_id, operation_id=operation_key
        )
        try:
            frozen_definition, _retry = self._frozen_authority_definitions_from_route(
                conn, route
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ConflictError(
                "Frozen capability authority is unavailable.",
                code="inference_route_plan_integrity_invalid",
            ) from exc
        capability = SimpleNamespace(
            id=frozen_definition["id"],
            revision=int(frozen_definition["revision"]),
            schema_sha256=frozen_definition["schema_sha256"],
        )
        rows = conn.execute(
            "SELECT * FROM inference_route_plan_preflight_evidence WHERE plan_id=? ORDER BY route_leg_ordinal",
            (route_id,),
        ).fetchall()
        if len(rows) != len(route["entries"]):
            raise ConflictError("Frozen route preflight evidence is missing.", code="inference_route_plan_integrity_invalid")
        preflight = [
            {"route_leg_ordinal": int(row["route_leg_ordinal"]), "eligibility": str(row["eligibility"]), "reason_code": row["reason_code"]}
            for row in rows
        ]
        evidence = self._operation_evidence(
            conn, provider_id=None, planning_reference=reference,
            operation_id=operation_key, capability=capability,
            operation_policy_revision=route["operation_policy_revision"], freeze=True,
            resolved_route=route, frozen_preflight=preflight,
        )
        operation = self._operation_material(
            route=route, operation_id=operation_key,
            material_snapshot_sha256=evidence["material_snapshot_sha256"],
            entries=evidence["entries"], operation_plan_id=expected_operation_id,
            frozen_preflight=preflight, evidence_provider_id=evidence["provider_id"],
            planning_reference=reference, evidence_provider_revision=evidence["provider_revision"],
            admission_evidence_ref=evidence["evidence_ref"], admission_evidence_sha256=evidence["evidence_sha256"],
        )
        operation_hash = _sha256(operation)
        budget_material = self._attempt_budget_material_in_transaction(
            authority, conn, operation={**operation, "sha256": operation_hash}, route=route
        )
        self._insert_operation(conn, operation, operation_hash, frozen_preflight=preflight)
        conn.execute(
            """INSERT INTO inference_operation_route_attempt_budget_evidence
               (operation_plan_id,provider_id,provider_revision,evidence_ref,
                material_snapshot_sha256,payload_json,sha256) VALUES (?,?,?,?,?,?,?)""",
            (operation["id"], budget_material["provider_id"], budget_material["provider_revision"],
             operation["admission_evidence_ref"], operation["material_snapshot_sha256"],
             _canonical(budget_material), _sha256(budget_material)),
        )
        conn.execute(
            "INSERT INTO inference_operation_route_request_plan_commands (command_id, request_sha256, route_plan_id, route_plan_sha256, operation_plan_id, operation_plan_sha256, created_at) VALUES (?,?,?,?,?,?,?)",
            (command, request_hash, route["id"], route["sha256"], operation["id"], operation_hash, operation["created_at"]),
        )
        return {"route_plan": route, "operation_request_plan": {**operation, "sha256": operation_hash}}

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

    def frozen_capability_definition_in_transaction(
        self, authority: Principal, conn: Any, *, route_plan_id: str
    ) -> dict[str, Any]:
        """Reconstruct the immutable capability definition for one frozen route."""
        self._require_planner(authority)
        route_id = _safe_id(route_plan_id, field="route_plan_id")
        route = self._route_from_row(
            conn,
            conn.execute(
                "SELECT * FROM inference_route_plans WHERE id=?", (route_id,)
            ).fetchone(),
        )
        try:
            definition, _retry = self._frozen_authority_definitions_from_route(
                conn, route
            )
            return definition
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ConflictError(
                "Frozen capability authority is unavailable.",
                code="inference_route_plan_integrity_invalid",
            ) from exc

    def reconstruct_frozen_pair_in_transaction(
        self,
        authority: Principal,
        conn: Any,
        operation_plan_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Verify one operation/route pair inside its caller-owned transaction."""
        self._require_planner(authority)
        operation = self._operation_from_row(
            conn,
            conn.execute(
                "SELECT * FROM inference_operation_route_request_plans WHERE id=?",
                (_safe_id(operation_plan_id, field="operation_plan_id"),),
            ).fetchone(),
        )
        route = self._route_from_row(
            conn,
            conn.execute(
                "SELECT * FROM inference_route_plans WHERE id=?",
                (operation["route_plan_id"],),
            ).fetchone(),
        )
        if operation["route_plan_id"] != route["id"]:
            raise ConflictError(
                "Stored operation route binding is invalid.",
                code="inference_operation_route_plan_integrity_invalid",
            )
        return operation, route

    def reconstruct_attempt_budgets_in_transaction(
        self,
        authority: Principal,
        conn: Any,
        *,
        operation: Mapping[str, Any],
        route: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Reconstruct closed, hash-bound worst-case budgets from the same owner."""
        material = self._attempt_budget_material_in_transaction(
            authority, conn, operation=operation, route=route
        )
        frozen = conn.execute(
            "SELECT * FROM inference_operation_route_attempt_budget_evidence WHERE operation_plan_id=?",
            (operation["id"],),
        ).fetchone()
        if frozen is None:
            raise ServiceError(
                "inference_attempt_budget_evidence_missing",
                "This historical operation has no frozen attempt budgets",
            )
        try:
            payload = json.loads(str(frozen["payload_json"]))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ConflictError("Frozen attempt budget evidence is invalid.", code="inference_attempt_budget_evidence_invalid") from exc
        if (
            payload != material
            or str(frozen["sha256"]) != _sha256(material)
            or str(frozen["provider_id"]) != material["provider_id"]
            or int(frozen["provider_revision"]) != material["provider_revision"]
            or str(frozen["evidence_ref"]) != operation["admission_evidence_ref"]
            or str(frozen["material_snapshot_sha256"]) != operation["material_snapshot_sha256"]
        ):
            raise ConflictError("Frozen attempt budget evidence changed.", code="inference_attempt_budget_evidence_invalid")
        return {**material, "sha256": _sha256(material)}

    def _attempt_budget_material_in_transaction(
        self,
        authority: Principal,
        conn: Any,
        *,
        operation: Mapping[str, Any],
        route: Mapping[str, Any],
    ) -> dict[str, Any]:
        self._require_planner(authority)
        provider = self._operation_evidence_providers.get(str(operation["evidence_provider_id"]))
        if (
            provider is None
            or provider.revision != int(operation["evidence_provider_revision"])
            or provider.reconstruct_attempt_budgets is None
        ):
            raise ServiceError(
                "inference_attempt_budget_evidence_missing",
                "The admitted operation owner did not freeze attempt budgets",
            )
        before = conn.total_changes
        value = provider.reconstruct_attempt_budgets(
            conn, str(operation["admission_evidence_ref"])
        )
        if conn.total_changes != before:
            raise ConflictError(
                "Attempt budget reconstruction wrote state.",
                code="inference_attempt_budget_evidence_invalid",
            )
        if not isinstance(value, Mapping) or set(value) != {"schema", "evidence_ref", "material_snapshot_sha256", "entries"} or value["schema"] != "RouteAttemptBudgetEvidence@1":
            raise ConflictError("Attempt budget evidence has an invalid shape.", code="inference_attempt_budget_evidence_invalid")
        if value["evidence_ref"] != operation["admission_evidence_ref"] or value["material_snapshot_sha256"] != operation["material_snapshot_sha256"]:
            raise ConflictError("Attempt budget evidence is not bound to the frozen material.", code="inference_attempt_budget_evidence_invalid")
        entries = value["entries"]
        if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)) or len(entries) != len(operation["entries"]):
            raise ConflictError("Attempt budget evidence has invalid cardinality.", code="inference_attempt_budget_evidence_invalid")
        normalized: list[dict[str, Any]] = []
        fields = {"route_leg_ordinal", "admitted_request_id", "admitted_request_sha256", "context_plan_sha256", "serialized_request_sha256", "input_tokens", "reserved_output_tokens", "total_tokens", "reserved_cost_units", "reserved_tool_calls"}
        for ordinal, (raw, planned) in enumerate(zip(entries, operation["entries"]), 1):
            if not isinstance(raw, Mapping) or set(raw) != fields or raw["route_leg_ordinal"] != ordinal:
                raise ConflictError("Attempt budget evidence entry is invalid.", code="inference_attempt_budget_evidence_invalid")
            for name in ("input_tokens", "reserved_output_tokens", "total_tokens", "reserved_cost_units", "reserved_tool_calls"):
                if type(raw[name]) is not int or raw[name] < 0:
                    raise ConflictError("Attempt budget evidence amount is invalid.", code="inference_attempt_budget_evidence_invalid")
            if raw["total_tokens"] != raw["input_tokens"] + raw["reserved_output_tokens"]:
                raise ConflictError("Attempt token budget does not add up.", code="inference_attempt_budget_evidence_invalid")
            if planned["eligibility"] != "executable" and any(int(raw[name]) for name in ("input_tokens", "reserved_output_tokens", "total_tokens", "reserved_cost_units", "reserved_tool_calls")):
                raise ConflictError("Unavailable legs must reserve zero budget.", code="inference_attempt_budget_evidence_invalid")
            for name in ("admitted_request_id", "admitted_request_sha256", "context_plan_sha256", "serialized_request_sha256"):
                expected = planned[name]
                if raw[name] != expected:
                    raise ConflictError("Attempt budget evidence is cross-bound incorrectly.", code="inference_attempt_budget_evidence_invalid")
            normalized.append(dict(raw))
        material = {
            "schema": "RouteAttemptBudgetEvidence@1",
            "provider_id": provider.id,
            "provider_revision": provider.revision,
            "operation_plan_id": operation["id"],
            "operation_plan_sha256": operation["sha256"],
            "material_snapshot_sha256": operation["material_snapshot_sha256"],
            "route_plan_id": route["id"],
            "route_plan_sha256": route["sha256"],
            "entries": normalized,
        }
        return material

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
        skipped_tool_reasons: list[str] = []
        for source_ordinal, value in enumerate(values, 1):
            if int(value["ordinal"]) != source_ordinal:
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
            manifest = profile["capability_manifest"]
            reason: str | None = None
            qualification = None
            if boundary not in capability.allowed_boundaries:
                reason = "boundary_unsupported"
            elif int(value.get("profile_schema_version", 2)) == 1:
                if capability.requires.structured_output or capability.requires.structured_tools:
                    reason = "structured_tools_unsupported" if capability.requires.structured_tools else "structured_output_unsupported"
                elif int(context["maximum_tokens"]) < capability.requires.minimum_context_tokens:
                    reason = "context_unsupported"
            else:
                reason = self._assignments._incompatibility(
                    profile_obj,
                    deployment,
                    set(manifest.get("claims") or []),
                    set(profile_obj.supported_modalities),
                    capability,
                )
                if capability.requires.structured_tools and reason is None:
                    # The assignment predicate proves compatibility, but route
                    # resolution carries the exact manifest qualification as
                    # frozen evidence.  It is reconstructed from the immutable
                    # profile revision, never a current deployment head.
                    try:
                        parsed_manifest, qualification = parse_capability_manifest(manifest)
                    except ToolCapabilityError:
                        reason = "tool_manifest_invalid"
                    else:
                        if (
                            parsed_manifest["sha256"] != str(deployment.capability_sha256)
                            or qualification.structured_tool_use != "qualified"
                            or qualification.qualified_palette < 1
                            or qualification.native_tool_dialect == "none"
                        ):
                            reason = "structured_tools_unqualified"
            if reason:
                if capability.requires.structured_tools:
                    # A saved chain can become invalid after its original save
                    # (or predate Foundation composition).  Tool routes select
                    # only exact qualified revisions, never retarget or dispatch
                    # an unqualified leg; its presence remains lawful for
                    # ordinary no-tool capabilities.
                    skipped_tool_reasons.append(reason)
                    continue
                if reason == "boundary_unsupported":
                    raise ValidationError("Model boundary is incompatible.", code="inference_route_boundary_unsupported")
                raise ValidationError("Model profile is no longer compatible.", code="no_compatible_assignment", context={"reason_code": reason})
            route_ordinal = len(entries) + 1
            route_entry = {
                "ordinal": route_ordinal,
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
            }
            if capability.requires.structured_tools:
                if qualification is None:  # pragma: no cover - branch is guarded above
                    raise ValidationError("Tool qualification is missing.", code="tool_required_unavailable")
                route_entry.update({
                    "source_assignment_ordinal": source_ordinal,
                    "tool_qualification": qualification.to_dict(),
                })
            entries.append(route_entry)
            revisions.append(deployment)
            # A migrated built-in Whisper runtime has no verified artifact file
            # to observe before it is first loaded. For its two speech
            # operations only, an enabled unavailable binding is capacity that
            # the derived preload observes at operation time; no other
            # unavailable profile gains executable status.
            unloaded_local_speech = (
                int(value.get("profile_schema_version", 2)) == 2
                and readiness == "unavailable"
                and deployment.kind == "this_device"
                and deployment.boundary == "same_device"
                and deployment.engine in {"mlx", "faster-whisper"}
                and getattr(capability, "id", "") in {"speech.transcribe", "speech.preload"}
            )
            # Rails' exact saved same-device deployment is likewise allowed one
            # first frozen execution without a migration-time load/probe.  Its
            # private artifact locator is already fixed; the successful physical
            # load records readiness for later freezes.
            unloaded_local_rails = (
                int(value.get("profile_schema_version", 2)) == 2
                and readiness == "unavailable"
                and deployment.kind == "this_device"
                and deployment.boundary == "same_device"
                and deployment.engine == "configured_local_engine"
                and deployment.runtime_revision == "rails-observer-this-machine-v1"
                and getattr(capability, "id", "") == "background.rails_summary"
            )
            executable = enabled and (
                readiness in {"ready", "unknown"} or unloaded_local_speech or unloaded_local_rails
            )
            preflight.append({
                "route_leg_ordinal": route_ordinal,
                "eligibility": "executable" if executable else "known_preflight_unavailable",
                "reason_code": None if executable else ("binding_disabled" if not enabled else "binding_not_ready"),
            })
        if capability.requires.structured_tools and not entries:
            raise ValidationError(
                "This operation requires an AI with tool use.",
                code="tool_required_unavailable",
                context={
                    "reason_code": skipped_tool_reasons[0] if skipped_tool_reasons else "structured_tools_unqualified",
                    "repair": "Use an AI with tool use",
                },
            )
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

    def _operation_evidence(self, conn: Any, *, provider_id: str | None, planning_reference: str, operation_id: str, capability: Any, operation_policy_revision: str, freeze: bool, evidence_ref: str | None = None, resolved_route: Mapping[str, Any] | None = None, frozen_preflight: Sequence[Mapping[str, Any]] = ()) -> dict[str, Any]:
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
        if freeze and provider.freeze_resolved is not None:
            if resolved_route is None:
                raise ConflictError(
                    "Resolved route evidence is missing.",
                    code="inference_operation_evidence_invalid",
                )
            value = provider.freeze_resolved(
                conn,
                planning_reference,
                operation_id,
                resolved_route,
                frozen_preflight,
            )
        else:
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

    def _insert_route(self, conn: Any, material: Mapping[str, Any], digest: str, revisions: Sequence[DeploymentRevision], *, capability_definition: Mapping[str, Any], retry_policy_definition: Mapping[str, Any], frozen_preflight: Sequence[Mapping[str, Any]] = (), principal_policy_evidence: Mapping[str, Any] | None = None) -> None:
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
               (id,sha256,capability_id,capability_revision,capability_schema_sha256,assignment_id,assignment_revision,assignment_sha256,inherited_from,retry_policy_id,retry_policy_revision,operation_policy_revision,principal_policy_sha256,payload_json,state,deadline_at,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (material["id"], digest, capability["id"], capability["revision"], capability["schema_sha256"], source["assignment_id"], source["assignment_revision"], source["assignment_sha256"], source["inherited_from"], policy["id"], policy["revision"], material["operation_policy_revision"], _sha256(principal_policy_evidence) if principal_policy_evidence is not None else None, _canonical(material), "frozen", material["deadline_at"], material["created_at"]),
        )
        for entry in material["entries"]:
            conn.execute(
                """INSERT INTO inference_route_plan_entries
                   (id,plan_id,route_leg_ordinal,profile_id,profile_revision,profile_schema_version,binding_id,binding_revision,deployment_head_id,deployment_configuration_revision,deployment_revision_id,capability_manifest_sha256,boundary,context_support_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (f"{material['id']}:{entry['ordinal']}", material["id"], entry["ordinal"], entry["profile_id"], entry["profile_revision"], entry["profile_schema_version"], entry["binding_id"], entry["binding_revision"], entry["deployment_head_id"], entry["deployment_configuration_revision"], entry["deployment_revision_id"], entry["capability_manifest_sha256"], entry["boundary"], _canonical(entry["context_support"])),
            )
        conn.execute(
            "INSERT INTO inference_route_plan_authority_evidence (plan_id, capability_definition_json, capability_definition_sha256, retry_policy_definition_json, retry_policy_definition_sha256) VALUES (?,?,?,?,?)",
            (material["id"], _canonical(capability_definition), capability_definition["schema_sha256"], _canonical(retry_policy_definition), retry_policy_definition["sha256"]),
        )
        if principal_policy_evidence is not None:
            conn.execute(
                "INSERT INTO inference_route_plan_principal_evidence (plan_id, payload_json, sha256) VALUES (?,?,?)",
                (
                    material["id"],
                    _canonical(principal_policy_evidence),
                    _sha256(principal_policy_evidence),
                ),
            )
        values = tuple(frozen_preflight) or tuple(
            {"route_leg_ordinal": entry["ordinal"], "eligibility": "executable", "reason_code": None}
            for entry in material["entries"]
        )
        for expected, item in enumerate(values, 1):
            if int(item["route_leg_ordinal"]) != expected:
                raise ConflictError("Route preflight order is invalid.", code="inference_route_plan_integrity_invalid")
            conn.execute(
                "INSERT INTO inference_route_plan_preflight_evidence (plan_id, route_leg_ordinal, eligibility, reason_code) VALUES (?,?,?,?)",
                (material["id"], expected, item["eligibility"], item.get("reason_code")),
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

    def _frozen_authority_definitions_from_route(
        self, conn: Any, route: Mapping[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        authority = conn.execute(
            "SELECT * FROM inference_route_plan_authority_evidence WHERE plan_id=?",
            (route["id"],),
        ).fetchone()
        if authority is None:
            raise ValueError("authority evidence")
        capability_definition = json.loads(str(authority["capability_definition_json"]))
        retry_definition = json.loads(str(authority["retry_policy_definition_json"]))
        if (
            not isinstance(capability_definition, dict)
            or not isinstance(retry_definition, dict)
            or capability_definition.get("schema_sha256")
            != str(authority["capability_definition_sha256"])
            or _sha256(
                {
                    key: value
                    for key, value in capability_definition.items()
                    if key != "schema_sha256"
                }
            )
            != capability_definition["schema_sha256"]
            or retry_definition.get("sha256")
            != str(authority["retry_policy_definition_sha256"])
            or _sha256(
                {key: value for key, value in retry_definition.items() if key != "sha256"}
            )
            != retry_definition["sha256"]
        ):
            raise ValueError("authority hash")
        expected_retry = {
            "id": retry_definition["id"],
            "revision": retry_definition["revision"],
            "sha256": retry_definition["sha256"],
            "per_entry_attempts": retry_definition["per_entry_attempts"],
            "total_physical_attempts": retry_definition["total_physical_attempts"],
            "deadline_ms": retry_definition["deadline_ms"],
            "token_budget": retry_definition["token_budget"],
            "cost_budget": retry_definition["cost_budget"],
            "tool_call_budget": retry_definition["tool_call_budget"],
            "fallback_dispositions": retry_definition["fallback_dispositions"],
            "retryable_dispositions": retry_definition["retryable_dispositions"],
        }
        if (
            route["retry_policy"] != expected_retry
            or route["capability"]
            != {
                "id": capability_definition["id"],
                "revision": capability_definition["revision"],
                "schema_sha256": capability_definition["schema_sha256"],
            }
        ):
            raise ValueError("authority cross bind")
        return capability_definition, retry_definition

    def _route_from_row(self, conn: Any, row: Any) -> dict[str, Any]:
        try:
            material = json.loads(str(row["payload_json"]))
            if set(material) != {"schema", "id", "capability", "source", "entries", "retry_policy", "operation_policy_revision", "created_at", "deadline_at"} or material["schema"] != ROUTE_PLAN_SCHEMA:
                raise ValueError("shape")
            digest = _sha256(material)
            self._validate_route_material(material)
            self._frozen_authority_definitions_from_route(conn, material)
            principal_evidence = conn.execute(
                "SELECT * FROM inference_route_plan_principal_evidence WHERE plan_id=?",
                (material["id"],),
            ).fetchone()
            required_principal_sha = str(row["principal_policy_sha256"] or "")
            if bool(required_principal_sha) != (principal_evidence is not None):
                raise ValueError("principal policy presence")
            if principal_evidence is not None:
                policy = json.loads(str(principal_evidence["payload_json"]))
                if (
                    str(principal_evidence["sha256"]) != required_principal_sha
                    or str(principal_evidence["sha256"]) != _sha256(policy)
                    or not self._valid_principal_policy_evidence(policy, material)
                ):
                    raise ValueError("principal policy evidence")
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
                if all("source_assignment_ordinal" in entry for entry in material["entries"]):
                    source_entries = source_material["entries"]
                    prior = 0
                    for entry in material["entries"]:
                        source_ordinal = int(entry["source_assignment_ordinal"])
                        if source_ordinal <= prior or source_ordinal > len(source_entries):
                            raise ValueError("tool assignment selection")
                        expected_source = source_entries[source_ordinal - 1]
                        selected = {
                            key: entry[key]
                            for key in ("profile_id", "profile_revision", "profile_schema_version")
                        }
                        if selected != {
                            key: expected_source[key]
                            for key in ("profile_id", "profile_revision", "profile_schema_version")
                        }:
                            raise ValueError("tool assignment selection")
                        prior = source_ordinal
                else:
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
                if "tool_qualification" in entry:
                    frozen_manifest, frozen_qualification = parse_capability_manifest(
                        profile.capability_manifest
                    )
                    if (
                        frozen_manifest["sha256"] != str(deployment.capability_sha256)
                        or frozen_qualification.to_dict() != entry["tool_qualification"]
                        or frozen_qualification.structured_tool_use != "qualified"
                        or frozen_qualification.qualified_palette < 1
                        or frozen_qualification.native_tool_dialect == "none"
                    ):
                        raise ValueError("tool qualification facts")
            return {**material, "sha256": digest}
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ConflictError("Stored route plan integrity could not be verified.", code="inference_route_plan_integrity_invalid") from exc

    @staticmethod
    def _valid_principal_policy_evidence(
        policy: Any, route: Mapping[str, Any]
    ) -> bool:
        fields = {
            "schema",
            "principal_kind",
            "policy_id",
            "policy_revision",
            "policy_sha256",
            "policy_material",
            "principal_identity",
            "authority_basis",
            "allowed_operations",
            "parent_kind",
            "capability",
            "allowed_boundaries",
            "assignment_sources",
        }
        if (
            not isinstance(policy, Mapping)
            or set(policy) != fields
            or policy["schema"] != "InferenceFeaturePrincipalPolicyEvidence@1"
            or policy["principal_kind"] not in {"owner", "service"}
            or type(policy["policy_revision"]) is not int
            or policy["policy_revision"] < 1
            or not isinstance(policy["policy_material"], Mapping)
            or policy["policy_sha256"] != _sha256(policy["policy_material"])
            or policy["capability"] != route["capability"]
            or not isinstance(policy["allowed_boundaries"], list)
            or len(policy["allowed_boundaries"]) != len(set(policy["allowed_boundaries"]))
            or not isinstance(policy["assignment_sources"], list)
            or len(policy["assignment_sources"]) != len(set(policy["assignment_sources"]))
            or route["source"]["inherited_from"] not in policy["assignment_sources"]
            or any(
                entry["boundary"] not in policy["allowed_boundaries"]
                for entry in route["entries"]
            )
        ):
            return False
        operations = policy["allowed_operations"]
        if not isinstance(operations, list) or any(
            not isinstance(item, Mapping)
            or set(item) != {"name", "version"}
            or not isinstance(item["name"], str)
            or type(item["version"]) is not int
            for item in operations
        ) or operations != sorted(operations, key=lambda item: (item["name"], item["version"])):
            return False
        if policy["principal_kind"] == "owner":
            expected = {
                "schema": "InferenceOwnerRoutePolicy@1",
                "id": policy["policy_id"],
                "revision": policy["policy_revision"],
                "assignment_sources": policy["assignment_sources"],
                "allowed_boundaries": policy["allowed_boundaries"],
            }
            return (
                policy["principal_identity"] == ""
                and policy["authority_basis"] == "owner-authenticated"
                and operations == []
                and policy["policy_material"] == expected
            )
        material = policy["policy_material"]
        if set(material) != {
            "schema",
            "id",
            "revision",
            "service_identity",
            "authority_basis",
            "parent_kind",
            "allowed_operations",
            "capabilities",
            "allowed_boundaries",
            "assignment_sources",
        }:
            return False
        capabilities = material["capabilities"]
        if not isinstance(capabilities, list) or any(
            not isinstance(item, Mapping)
            or set(item) != {"id", "revision", "schema_sha256"}
            for item in capabilities
        ) or len(capabilities) != len({item["id"] for item in capabilities}):
            return False
        return (
            material["schema"] == "InferenceServiceRoutePolicy@1"
            and material["id"] == policy["policy_id"]
            and material["revision"] == policy["policy_revision"]
            and material["service_identity"] == policy["principal_identity"]
            and material["authority_basis"] == policy["authority_basis"]
            and material["parent_kind"] == policy["parent_kind"]
            and material["allowed_operations"] == operations
            and material["allowed_boundaries"] == policy["allowed_boundaries"]
            and material["assignment_sources"] == policy["assignment_sources"]
            and route["capability"] in capabilities
            and policy["assignment_sources"] == ["capability"]
        )

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
        base_entry_keys = {
            "ordinal", "profile_id", "profile_revision", "profile_schema_version",
            "binding_id", "binding_revision", "deployment_head_id",
            "deployment_configuration_revision", "deployment_revision_id",
            "capability_manifest_sha256", "boundary", "context_support",
        }
        qualified_entry_keys = base_entry_keys | {
            "source_assignment_ordinal", "tool_qualification",
        }
        saw_qualified = False
        for ordinal, entry in enumerate(material["entries"], 1):
            keys = set(entry)
            if (keys != base_entry_keys and keys != qualified_entry_keys) or entry["ordinal"] != ordinal:
                raise ValueError("entry shape")
            if keys == qualified_entry_keys:
                saw_qualified = True
                if (
                    type(entry["source_assignment_ordinal"]) is not int
                    or entry["source_assignment_ordinal"] < 1
                ):
                    raise ValueError("source assignment ordinal")
                qualification = entry["tool_qualification"]
                if not isinstance(qualification, Mapping):
                    raise ValueError("tool qualification")
                # Parses the nested digest and rejects legacy/palette-zero or
                # post-hoc shape changes without consulting current config.
                _manifest, parsed = parse_capability_manifest({
                    "revision": "route-frozen-tool-qualification",
                    "claims": [],
                    "tool_qualification": qualification,
                    "sha256": _sha256({
                        "revision": "route-frozen-tool-qualification",
                        "claims": [],
                        "tool_qualification": qualification,
                    }),
                })
                if (
                    parsed.structured_tool_use != "qualified"
                    or parsed.qualified_palette < 1
                    or parsed.native_tool_dialect == "none"
                ):
                    raise ValueError("tool qualification")
            self._context_support(entry["context_support"])
            _hash(entry["capability_manifest_sha256"], field="capability_manifest_sha256")
        if saw_qualified and any(set(entry) != qualified_entry_keys for entry in material["entries"]):
            raise ValueError("mixed tool qualification route")


__all__ = [
    "InferenceRoutePlanService",
    "OPERATION_ROUTE_REQUEST_PLAN_SCHEMA",
    "ROUTE_PLAN_SCHEMA",
    "ROUTE_PLANNING_AUTHORITY",
    "RouteAdmissionEvidenceProvider",
]
