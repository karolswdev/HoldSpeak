"""HS-143-09 A1 — private lease and MODEL_TURN projection contracts."""
from __future__ import annotations

import hashlib
import json

import pytest

from holdspeak.services.tool_capability_service import (
    CanonicalApplicationOperationDescriptor,
    ModelTurnCapabilityProjection,
    ToolCapabilityError,
    ToolQualification,
    ToolResultEnvelope,
    parse_capability_manifest,
)
from holdspeak.services.tool_turn_controller import TurnCapabilityLease


def _hash(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _descriptor() -> CanonicalApplicationOperationDescriptor:
    return CanonicalApplicationOperationDescriptor(
        capability_id="evidence.note_lookup",
        revision=1,
        label="Find attached Note",
        description="Find an explicitly attached Note.",
        argument_schema={
            "type": "object", "additionalProperties": False,
            "properties": {"note_id": {"type": "string"}},
            "required": ["note_id"],
        },
        service_operation="note.lookup",
        capability_class="evidence_read",
        effect_mode="read",
        allowed_data_classes=("note",),
        allowed_placements=("local",),
        allowed_egress=("local",),
        max_calls=2,
        max_result_bytes=1024,
        max_result_tokens=256,
        commutative_read=True,
    )


def _terms(descriptor: CanonicalApplicationOperationDescriptor, *, now: float = 100.0) -> dict[str, object]:
    return {
        "schema": "TurnCapabilityLease@1",
        "lease_id": "lease-1",
        "nonce": "nonce-1",
        "epoch": 1,
        "parent_turn_id": "turn-1",
        "owner_principal_id": "owner-1",
        "deployment_revision": "deployment-1",
        "operation_kind": "thought.interview",
        "operation_revision": "revision-1",
        "owner_intent_receipt_id": None,
        "policy_revision": "policy-1",
        "capabilities": [{
            "capability_id": descriptor.capability_id,
            "capability_revision": descriptor.revision,
            "descriptor_sha256": descriptor.descriptor_sha256,
            "schema_sha256": descriptor.schema_sha256,
            "service_operation": descriptor.service_operation,
            "class": descriptor.capability_class,
            "effect_mode": descriptor.effect_mode,
            "scope": {"attached": True},
            "data_classes": ["note"],
            "placement": ["local"],
            "egress": ["local"],
            "max_calls": 2,
            "max_result_bytes": 1024,
            "max_result_tokens": 256,
            "commutative_read": True,
        }],
        "max_provider_steps": 4,
        "max_tool_calls": 2,
        "max_effect_proposals": 0,
        "max_parallel_reads": 2,
        "aggregate_result_bytes": 2048,
        "aggregate_result_tokens": 512,
        "wall_deadline": now + 30,
        "expires_at": now + 30,
    }


def test_model_turn_projection_is_closed_deterministic_and_provider_private() -> None:
    descriptor = _descriptor()
    projection = ModelTurnCapabilityProjection([descriptor])
    tool = projection.provider_tools([descriptor.capability_id])[0]

    assert tool == {
        "schema": "ModelTurnProviderTool@1",
        "name": "evidence.note_lookup",
        "description": "Find an explicitly attached Note.",
        "parameters": descriptor.argument_schema,
    }
    rendered = json.dumps(tool, sort_keys=True)
    for forbidden in ("lease", "nonce", "owner", "policy", "mcp", "transport", "credential"):
        assert forbidden not in rendered.lower()
    with pytest.raises(ToolCapabilityError):
        projection.provider_tools(["settings.update"])
    with pytest.raises(ToolCapabilityError):
        ModelTurnCapabilityProjection([descriptor, descriptor])


def test_lease_normalizes_hashes_and_refuses_palette_expansion_or_expiry_extension() -> None:
    descriptor = _descriptor()
    terms = _terms(descriptor)
    first = TurnCapabilityLease.parse(terms, now=100.0)
    reordered = _terms(descriptor)
    reordered["capabilities"] = list(reversed(reordered["capabilities"]))
    assert TurnCapabilityLease.parse(reordered, now=100.0).terms_sha256 == first.terms_sha256

    escalated = _terms(descriptor)
    escalated["max_tool_calls"] = 3
    with pytest.raises(Exception, match="exceeds capability limits"):
        TurnCapabilityLease.parse(escalated, now=100.0)
    expired_extension = _terms(descriptor)
    expired_extension["expires_at"] = 131.0
    with pytest.raises(Exception, match="expiry exceeds"):
        TurnCapabilityLease.parse(expired_extension, now=100.0)


def test_qualification_hash_binds_full_manifest_and_legacy_stays_unavailable() -> None:
    qualification = ToolQualification("qualified", 4, "eval-1", "openai")
    material = {
        "revision": "manifest-v2", "claims": ["language"],
        "tool_qualification": qualification.to_dict(),
    }
    manifest = {**material, "sha256": _hash(material)}
    parsed, parsed_qualification = parse_capability_manifest(manifest)
    assert parsed == manifest
    assert parsed_qualification.qualified_palette == 4

    legacy_material = {"revision": "manifest-v1", "claims": ["language"]}
    legacy, legacy_qualification = parse_capability_manifest({**legacy_material, "sha256": _hash(legacy_material)})
    assert legacy_qualification.structured_tool_use == "unavailable"
    assert legacy_qualification.qualified_palette == 0
    assert "tool_qualification" not in legacy

    forged = {**manifest, "tool_qualification": {**qualification.to_dict(), "qualified_palette": 8}}
    with pytest.raises(ToolCapabilityError, match="hash"):
        parse_capability_manifest(forged)


def test_result_limitation_default_is_false() -> None:
    result = ToolResultEnvelope("unavailable", None, 0, 0)
    assert result.final_answer_may_name_limitation is False


def test_real_profile_persists_full_qualified_manifest_without_upgrading_legacy(tmp_path) -> None:
    from holdspeak.db import Database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.model_profile_service import ModelProfileService

    qualification = ToolQualification("qualified", 4, "eval-1", "openai")
    evidence = {
        "revision": "manifest-v2", "claims": ["language"],
        "tool_qualification": qualification.to_dict(),
    }
    manifest = {**evidence, "sha256": _hash(evidence)}
    db = Database(tmp_path / "qualified-manifest.db")
    profile = ModelProfileService(db).create_profile(
        Principal(PrincipalKind.OWNER, "owner"),
        {
            "profile_id": "tool-capable", "expected_revision": 0, "label": "Tool capable",
            "provider_family": "local", "runtime_family": "llama_cpp_prompt_v1",
            "model_or_artifact_identity": "artifact-tool", "supported_modalities": ["language"],
            "context_support": "bounded", "tokenizer_template_requirements": {},
            "capability_manifest": manifest, "safe_presentation": {"summary": "Fixture"},
        },
    )
    assert profile["capability_manifest"] == manifest
