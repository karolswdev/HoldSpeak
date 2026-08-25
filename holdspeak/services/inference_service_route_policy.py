"""Closed feature-principal policy for inference route resolution.

Kernel routing authorities are implementation identities.  This policy instead
describes the principal whose feature work will execute.  OWNER work may use
the normal assignment inheritance chain.  SERVICE work is default-deny and may
consume only an exact owner-configured capability assignment named by a sealed
composition policy; group/global rows never become ambient service authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from ..inference_capabilities import (
    InferenceCapabilityRegistry,
    process_inference_capability_registry,
)
from ..principals import Principal, PrincipalKind
from .errors import ValidationError


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class ServiceRoutePolicyDefinition:
    id: str
    revision: int
    service_identity: str
    authority_basis: str
    parent_kind: str
    allowed_operations: frozenset[tuple[str, int]]
    capability_ids: tuple[str, ...]
    allowed_boundaries: tuple[str, ...]
    assignment_sources: tuple[str, ...] = ("capability",)

    def material(self, registry: InferenceCapabilityRegistry) -> dict[str, Any]:
        capabilities = []
        for capability_id in self.capability_ids:
            capability = registry.require(capability_id)
            capabilities.append(
                {
                    "id": capability.id,
                    "revision": capability.revision,
                    "schema_sha256": capability.schema_sha256,
                }
            )
        return {
            "schema": "InferenceServiceRoutePolicy@1",
            "id": self.id,
            "revision": self.revision,
            "service_identity": self.service_identity,
            "authority_basis": self.authority_basis,
            "parent_kind": self.parent_kind,
            "allowed_operations": [
                {"name": name, "version": version}
                for name, version in sorted(self.allowed_operations)
            ],
            "capabilities": capabilities,
            "allowed_boundaries": list(self.allowed_boundaries),
            "assignment_sources": list(self.assignment_sources),
        }


class ServiceRoutePolicyRegistry:
    def __init__(
        self,
        definitions: Iterable[ServiceRoutePolicyDefinition],
        *,
        capability_registry: InferenceCapabilityRegistry | None = None,
    ) -> None:
        self._capabilities = capability_registry or process_inference_capability_registry()
        self._definitions: dict[tuple[str, str, str], ServiceRoutePolicyDefinition] = {}
        for definition in definitions:
            key = (
                definition.service_identity,
                definition.authority_basis,
                definition.parent_kind,
            )
            if key in self._definitions:
                raise ValueError("duplicate inference service route policy")
            material = definition.material(self._capabilities)
            if definition.revision < 1 or not definition.capability_ids:
                raise ValueError("invalid inference service route policy")
            if set(definition.assignment_sources) - {"capability"}:
                raise ValueError("service route policy cannot inherit ambient assignments")
            self._definitions[key] = definition
            _sha256(material)

    def authorize(
        self,
        principal: Principal,
        *,
        parent_kind: str,
        capability_id: str,
    ) -> dict[str, Any]:
        if principal.kind is not PrincipalKind.SERVICE:
            raise ValidationError(
                "Service route policy requires a service principal.",
                code="inference_service_route_policy_denied",
            )
        definition = self._definitions.get(
            (principal.identity, principal.authority_basis, str(parent_kind))
        )
        if definition is None or capability_id not in definition.capability_ids:
            raise ValidationError(
                "Service route is not authorized.",
                code="inference_service_route_policy_denied",
            )
        if principal.allowed_operations != definition.allowed_operations:
            raise ValidationError(
                "Service operation authority does not match its route policy.",
                code="inference_service_route_policy_denied",
            )
        declared_material = definition.material(self._capabilities)
        capability = next(
            item for item in declared_material["capabilities"] if item["id"] == capability_id
        )
        # Evidence names exactly the member being frozen.  A wake parent can
        # therefore carry provider stages at their own capability boundaries
        # without widening its local-only transcribe/preload members.
        capability_definition = self._capabilities.require(capability_id)
        allowed_boundaries = [
            boundary
            for boundary in declared_material["allowed_boundaries"]
            if boundary in capability_definition.allowed_boundaries
        ]
        material = {
            **declared_material,
            "capabilities": [capability],
            "allowed_boundaries": allowed_boundaries,
        }
        return {
            "schema": "InferenceFeaturePrincipalPolicyEvidence@1",
            "principal_kind": "service",
            "policy_id": definition.id,
            "policy_revision": definition.revision,
            "policy_sha256": _sha256(material),
            "policy_material": material,
            "principal_identity": definition.service_identity,
            "authority_basis": definition.authority_basis,
            "allowed_operations": material["allowed_operations"],
            "parent_kind": definition.parent_kind,
            "capability": capability,
            "allowed_boundaries": list(allowed_boundaries),
            "assignment_sources": list(definition.assignment_sources),
        }


def builtin_service_route_policy_registry(
    *, capability_registry: InferenceCapabilityRegistry | None = None,
) -> ServiceRoutePolicyRegistry:
    registry = capability_registry or process_inference_capability_registry()
    requested_meeting_capabilities = (
        "meeting.deferred_analysis",
        "meeting.bookmark_label",
        "meeting.auto_title",
        *(
            capability_id
            for capability_id in registry.capability_ids
            if capability_id.startswith("meeting.plugin.")
        ),
    )
    available = set(registry.capability_ids)
    missing = sorted(set(requested_meeting_capabilities) - available)
    if missing:
        raise ValueError(
            f"meeting service route policy capabilities are absent: {missing!r}"
        )
    meeting_capabilities = tuple(requested_meeting_capabilities)
    queue_operations = frozenset(
        {
            ("meeting.deferred-intel-job", 1),
            ("inference.invoke", 1),
            ("inference.cancel", 1),
        }
    )
    return ServiceRoutePolicyRegistry(
        (
            ServiceRoutePolicyDefinition(
                id="meeting-intel-queue@1",
                revision=1,
                service_identity="meeting-intel-queue",
                authority_basis="meeting-intel-queue:deferred",
                parent_kind="meeting.deferred-intel-job",
                allowed_operations=queue_operations,
                capability_ids=tuple(meeting_capabilities),
                allowed_boundaries=("local", "mesh", "private_network", "cloud"),
            ),
            ServiceRoutePolicyDefinition(
                id="wake-capture@1",
                revision=1,
                service_identity="wake-capture",
                authority_basis="wake-capture:configured-capture",
                parent_kind="wake.session",
                allowed_operations=frozenset(
                    {
                        ("wake.session", 1),
                        ("inference.invoke", 1),
                        ("inference.cancel", 1),
                    }
                ),
                # Wake freezes the same provider-backed stages that its normal
                # dictation tail can dispatch.  The bundle still includes only
                # the stages selected by this exact Config snapshot; this closed
                # policy is the SERVICE-side authority for those routed members.
                capability_ids=(
                    "speech.transcribe",
                    "speech.preload",
                    "speech.intent_classify",
                    "speech.rewrite",
                ),
                # The policy may carry the boundaries its provider members
                # permit.  speech.transcribe and speech.preload remain local-only
                # because their capability definitions independently refuse every
                # other boundary during the same route admission.
                allowed_boundaries=("local", "mesh", "private_network", "cloud"),
            ),
            ServiceRoutePolicyDefinition(
                id="rails-observer@1",
                revision=1,
                service_identity="rails-observer",
                authority_basis="rails-observer:journal-only",
                parent_kind="rails.observer-batch",
                allowed_operations=frozenset(
                    {
                        ("rails.observer-batch", 1),
                        ("inference.invoke", 1),
                        ("inference.cancel", 1),
                    }
                ),
                capability_ids=("background.rails_summary",),
                allowed_boundaries=("local", "mesh", "private_network", "cloud"),
            ),
            ServiceRoutePolicyDefinition(
                id="local-model-preload@1",
                revision=1,
                service_identity="local-model-preload",
                authority_basis="local-model-preload:assigned-speech-route",
                parent_kind="local-model-preload",
                allowed_operations=frozenset({("inference.invoke", 1)}),
                capability_ids=("speech.preload",),
                allowed_boundaries=("local",),
            ),
        ),
        capability_registry=registry,
    )


__all__ = [
    "ServiceRoutePolicyDefinition",
    "ServiceRoutePolicyRegistry",
    "builtin_service_route_policy_registry",
]
