"""HSEGHS001HS104-143-04 — sparse assignment authority and resolver."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.deployment_revisions import DeploymentRevision
from holdspeak.inference_capabilities import process_inference_capability_registry
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, ServiceError, ValidationError
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.model_profile_service import ModelProfileService
from holdspeak.services.sync_service import SyncService


OWNER = Principal(PrincipalKind.OWNER, "assignment-owner")
AGENT = Principal(PrincipalKind.AGENT, "assignment-agent")


def _result_claim(capability_id: str) -> str:
    definition = process_inference_capability_registry().require(capability_id)
    return f"result_schema:{definition.output_schema_sha256}"


def _manifest(*claims: str) -> dict[str, object]:
    values = list(claims or ("language",))
    material = {"claims": values, "revision": "fixture-v1"}
    return {
        **material,
        "sha256": "sha256:"
        + hashlib.sha256(
            json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


def _profile(
    db: Database,
    profile_id: str,
    *,
    claims: tuple[str, ...] = ("language",),
    ready: bool = True,
    context_ceiling: int = 32768,
    modalities: tuple[str, ...] = ("language",),
) -> str:
    profiles = ModelProfileService(db)
    manifest = _manifest(*claims)
    profiles.create_profile(
        OWNER,
        {
            "profile_id": profile_id,
            "expected_revision": 0,
            "label": profile_id.replace("-", " ").title(),
            "provider_family": "local",
            "runtime_family": "llama_cpp_prompt_v1",
            "model_or_artifact_identity": f"artifact-{profile_id}",
            "supported_modalities": list(modalities),
            "context_support": "bounded",
            "tokenizer_template_requirements": {},
            "capability_manifest": manifest,
            "safe_presentation": {"summary": "Fixture"},
        },
    )
    deployment = DeploymentRevision.from_artifact(
        destination_id="this_machine",
        engine="configured_local_engine",
        model=profile_id,
        runtime_id="llama_cpp_prompt_v1",
        runtime_revision="1",
        artifact_id=f"artifact-{profile_id}",
        manifest_sha256="sha256:" + hashlib.sha256(profile_id.encode()).hexdigest(),
        format="gguf",
        architecture="qwen",
        context_ceiling=context_ceiling,
        capability_sha256=str(manifest["sha256"]),
    )
    db.deployment_revisions.upsert(deployment)
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO inference_model_artifacts
            (artifact_id,format,source_kind,source_repository,source_revision,manifest_json,manifest_sha256,
             installed_bytes,state,local_locator,created_at,verified_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                f"artifact-{profile_id}",
                "gguf",
                "fixture",
                "fixture",
                "r1",
                "{}",
                deployment.manifest_sha256,
                1,
                "verified",
                f"/private/{profile_id}.gguf",
                "2026-08-21T00:00:00Z",
                "2026-08-21T00:00:00Z",
            ),
        )
        conn.execute(
            """INSERT INTO inference_deployments
            (deployment_id,destination_id,runtime_id,runtime_revision,artifact_id,model_identity,context_ceiling,
             recommended_context,capability_json,capability_sha256,execution_revision_id,configuration_revision,
             active,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                f"head-{profile_id}",
                "this_machine",
                "llama_cpp_prompt_v1",
                "1",
                f"artifact-{profile_id}",
                profile_id,
                context_ceiling,
                context_ceiling,
                "{}",
                deployment.capability_sha256,
                deployment.id,
                1,
                1,
                "2026-08-21T00:00:00Z",
                "2026-08-21T00:00:00Z",
            ),
        )
    observation = profiles.probe_profile(
        OWNER,
        {
            "profile_id": profile_id,
            "profile_revision": 1,
            "deployment_head_id": f"head-{profile_id}",
            "expected_deployment_configuration_revision": 1,
            "expected_deployment_revision_id": deployment.id,
        },
    )
    profiles.bind_profile(
        OWNER,
        {
            "binding_id": f"binding-{profile_id}",
            "profile_id": profile_id,
            "profile_revision": 1,
            "deployment_head_id": f"head-{profile_id}",
            "expected_binding_revision": 0,
            "expected_deployment_configuration_revision": 1,
            "expected_deployment_revision_id": deployment.id,
            "enabled": True,
            "readiness_observation_id": observation["observation_id"],
        },
    )
    if not ready:
        with db._connection() as conn:
            conn.execute(
                "UPDATE model_profile_readiness_observations SET state='unavailable',reason_code='busy'"
            )
        return "unavailable"
    return str(observation["state"])


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "assignments.db")


def _set(
    service: InferenceAssignmentService,
    command: str,
    scope: dict[str, str],
    profile: str,
    expected: int = 0,
) -> dict:
    return service.set_assignment(
        OWNER,
        {
            "command_id": command,
            "expected_revision": expected,
            "scope": scope,
            "entries": [{"profile_id": profile, "profile_revision": 1}],
        },
    )


def test_owner_first_and_sparse_precedence_first_whole_chain(db: Database) -> None:
    _profile(db, "group-model", claims=("language", _result_claim("thought.interview")))
    _profile(db, "subject-model")
    service = InferenceAssignmentService(db)
    with pytest.raises(ServiceError) as denied:
        service.list_assignments(AGENT)
    assert denied.value.code == "inference_assignment_owner_required"
    _set(
        service,
        "set-group",
        {"kind": "group", "group_id": "thoughts_notes"},
        "group-model",
    )
    _set(
        service,
        "set-subject",
        {
            "kind": "subject",
            "subject_kind": "thought",
            "subject_id": "t1",
            "capability_id": "ask.answer",
        },
        "subject-model",
    )
    inherited = service.resolve_effective(OWNER, capability_id="ask.answer")
    subject = service.resolve_effective(
        OWNER, capability_id="ask.answer", subject_kind="thought", subject_id="t1"
    )
    assert inherited["inherited_from"] == "group"
    assert [entry["profile_id"] for entry in inherited["assignment"]["entries"]] == [
        "group-model"
    ]
    assert subject["inherited_from"] == "subject"
    assert [entry["profile_id"] for entry in subject["assignment"]["entries"]] == [
        "subject-model"
    ]


def test_clear_is_monotonic_aba_safe_and_preview_names_effective_chain(
    db: Database,
) -> None:
    _profile(
        db, "default-model", claims=("language", _result_claim("thought.interview"))
    )
    _profile(db, "custom-model")
    service = InferenceAssignmentService(db)
    _set(
        service,
        "set-group",
        {"kind": "group", "group_id": "thoughts_notes"},
        "default-model",
    )
    custom = _set(
        service,
        "set-cap",
        {"kind": "capability", "capability_id": "ask.answer"},
        "custom-model",
    )
    preview = service.preview_use_default(
        OWNER,
        scope={"kind": "capability", "capability_id": "ask.answer"},
        capability_id="ask.answer",
    )
    assert (
        preview["effective"]["assignment"]["entries"][0]["profile_id"]
        == "default-model"
    )
    cleared = service.clear_assignment(
        OWNER,
        {
            "command_id": "clear-cap",
            "expected_revision": custom["revision"],
            "scope": {"kind": "capability", "capability_id": "ask.answer"},
            "capability_id": "ask.answer",
        },
    )
    assert cleared["revision"] == 2
    assert cleared["effective"]["inherited_from"] == "group"
    with pytest.raises(ConflictError):
        _set(
            service,
            "aba",
            {"kind": "capability", "capability_id": "ask.answer"},
            "custom-model",
            expected=0,
        )
    restored = _set(
        service,
        "restore",
        {"kind": "capability", "capability_id": "ask.answer"},
        "custom-model",
        expected=2,
    )
    assert restored["revision"] == 3


def test_command_replay_is_exact_and_unrelated_heads_do_not_conflict(
    db: Database,
) -> None:
    _profile(db, "one-model")
    service = InferenceAssignmentService(db)
    body = {
        "command_id": "same-command",
        "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "ask.answer"},
        "entries": [{"profile_id": "one-model"}],
    }
    first = service.set_assignment(OWNER, body)
    assert service.set_assignment(OWNER, body) == first
    with pytest.raises(ConflictError) as changed:
        service.set_assignment(
            OWNER,
            {
                **body,
                "entries": [{"profile_id": "one-model", "profile_revision": 1}],
                "retry_policy_id": "text-conservative",
            },
        )
    assert changed.value.code == "inference_assignment_command_conflict"
    later = service.set_assignment(
        OWNER,
        {
            "command_id": "later-same-key",
            "expected_revision": 1,
            "scope": {"kind": "capability", "capability_id": "ask.answer"},
            "entries": [{"profile_id": "one-model"}],
        },
    )
    replayed = service.set_assignment(OWNER, body)
    assert replayed["committed_effect"]["revision"] == 1
    assert replayed["current"]["revision"] == later["revision"] == 2
    other = _set(
        service,
        "other",
        {"kind": "capability", "capability_id": "speech.rewrite"},
        "one-model",
    )
    assert other["revision"] == 1


def test_readiness_and_capacity_are_not_structural_save_blockers(db: Database) -> None:
    _profile(db, "busy-model", ready=False)
    service = InferenceAssignmentService(db)
    saved = _set(
        service,
        "save-busy",
        {"kind": "capability", "capability_id": "ask.answer"},
        "busy-model",
    )
    assert saved["revision"] == 1
    assert any(
        issue["code"] == "binding_not_ready" and issue["severity"] == "repair"
        for issue in saved["issues"]
    )
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO inference_runtime_leases VALUES (?,?,?,?,?,?,?,?)",
            ("lease", "op", "dep", "active", "p", 9999999999, 1, 1),
        )
    assert (
        service.resolve_effective(OWNER, capability_id="ask.answer")["status"]
        == "assigned"
    )


def test_assignment_mirror_tamper_fails_closed(
    db: Database,
) -> None:
    _profile(db, "text-model")
    service = InferenceAssignmentService(db)
    saved = _set(
        service,
        "set",
        {"kind": "capability", "capability_id": "ask.answer"},
        "text-model",
    )
    with db._connection() as conn:
        conn.execute(
            "UPDATE inference_assignments SET ordinal=4 WHERE assignment_id=?",
            (saved["id"],),
        )
    with pytest.raises(ConflictError) as tampered:
        service.get_assignment(
            OWNER, {"kind": "capability", "capability_id": "ask.answer"}
        )
    assert tampered.value.code == "inference_assignment_integrity_invalid"


def test_adding_a_profile_leaves_assignment_bytes_identical(db: Database) -> None:
    _profile(db, "first-model")
    service = InferenceAssignmentService(db)
    _set(
        service,
        "set",
        {"kind": "capability", "capability_id": "ask.answer"},
        "first-model",
    )
    with db._connection() as conn:
        before = [
            tuple(row)
            for row in conn.execute(
                "SELECT * FROM inference_assignment_revisions ORDER BY assignment_id,revision"
            )
        ]
    _profile(db, "second-model")
    with db._connection() as conn:
        after = [
            tuple(row)
            for row in conn.execute(
                "SELECT * FROM inference_assignment_revisions ORDER BY assignment_id,revision"
            )
        ]
    assert after == before


def test_chain_shape_duplicate_bound_and_structured_claims(db: Database) -> None:
    _profile(db, "plain-model")
    service = InferenceAssignmentService(db)
    with pytest.raises(ValidationError):
        service.set_assignment(
            OWNER,
            {
                "command_id": "empty",
                "expected_revision": 0,
                "scope": {"kind": "global"},
                "entries": [],
            },
        )
    with pytest.raises(ValidationError):
        service.set_assignment(
            OWNER,
            {
                "command_id": "dupe",
                "expected_revision": 0,
                "scope": {"kind": "global"},
                "entries": [
                    {"profile_id": "plain-model"},
                    {"profile_id": "plain-model"},
                ],
            },
        )
    with pytest.raises(ValidationError) as typed:
        _set(
            service,
            "structured",
            {"kind": "capability", "capability_id": "thought.interview"},
            "plain-model",
        )
    assert typed.value.code == "inference_assignment_incompatible"


def test_migration_marker_is_one_way_hash_bound_and_requires_durable_assignments(
    db: Database,
) -> None:
    _profile(db, "migrated-primary")
    service = InferenceAssignmentService(db)
    migrated = _set(
        service,
        "migrated-set",
        {"kind": "capability", "capability_id": "ask.answer"},
        "migrated-primary",
    )
    body = {
        "family": "thoughts-v1",
        "marker_revision": 1,
        "source_sha256": "sha256:" + "a" * 64,
        "assignments": [
            {
                "assignment_key": "capability:ask.answer",
                "assignment_id": migrated["id"],
                "revision": migrated["revision"],
                "sha256": migrated["sha256"],
            }
        ],
    }
    first = service.commit_migration_marker(OWNER, body)
    assert service.commit_migration_marker(OWNER, body) == first
    with pytest.raises(ConflictError) as drift:
        service.commit_migration_marker(
            OWNER, {**body, "source_sha256": "sha256:" + "b" * 64}
        )
    assert drift.value.code == "inference_assignment_migration_conflict"
    with pytest.raises(ConflictError) as missing:
        service.commit_migration_marker(
            OWNER,
            {
                **body,
                "family": "meeting-v1",
                "assignments": [
                    {
                        "assignment_key": "group:meetings",
                        "assignment_id": "ia_missing",
                        "revision": 1,
                        "sha256": "sha256:" + "c" * 64,
                    }
                ],
            },
        )
    assert missing.value.code == "inference_assignment_migration_incomplete"


def test_assignment_authority_is_hub_local_and_hostile_sync_refuses(
    db: Database,
) -> None:
    with pytest.raises(ValidationError) as refused:
        SyncService(db).push(
            OWNER,
            {
                "notes": [],
                "inference_assignment_revisions": [{"profile_id": "remote"}],
                "inference_assignment_heads": [{"assignment_key": "global"}],
                "inference_assignment_commands": [{"command_id": "forged"}],
            },
        )
    assert refused.value.code == "sync_hub_local_bucket_forbidden"
    pulled = SyncService(db).pull(OWNER)
    assert not (
        {
            "inference_assignments",
            "inference_assignment_revisions",
            "inference_assignment_heads",
        }
        & set(pulled)
    )


def test_legacy_v1_and_v2_entries_share_one_chain_without_rewriting_v1(
    db: Database,
) -> None:
    legacy = db.profiles.upsert(
        profile_id="old-local",
        name="https://private.example/model",
        kind="onDevice",
        model_file="/private/old.gguf",
        model="Old Qwen",
        context_limit=32768,
    )
    before = legacy.to_dict()
    _profile(db, "new-local")
    service = InferenceAssignmentService(db)
    saved = service.set_assignment(
        OWNER,
        {
            "command_id": "mixed-chain",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "ask.answer"},
            "entries": [
                {"profile_id": "legacy-old-local"},
                {"profile_id": "new-local"},
            ],
        },
    )
    assert [
        (entry["profile_id"], entry["profile_schema_version"], entry["label"])
        for entry in saved["entries"]
    ] == [("legacy-old-local", 1, "Old Qwen"), ("new-local", 2, "New Local")]
    assert "private.example" not in json.dumps(saved)
    assert db.profiles.get("old-local").to_dict() == before


def test_payload_identity_and_command_receipt_tamper_fail_closed(db: Database) -> None:
    _profile(db, "integrity-model")
    service = InferenceAssignmentService(db)
    first = _set(
        service,
        "integrity-first",
        {"kind": "capability", "capability_id": "ask.answer"},
        "integrity-model",
    )
    second = _set(
        service,
        "integrity-second",
        {"kind": "capability", "capability_id": "speech.rewrite"},
        "integrity-model",
    )
    with db._connection() as conn:
        other = conn.execute(
            "SELECT payload_json,sha256 FROM inference_assignment_revisions WHERE assignment_id=? AND revision=1",
            (second["id"],),
        ).fetchone()
        conn.execute(
            "UPDATE inference_assignment_revisions SET payload_json=?,sha256=? WHERE assignment_id=? AND revision=1",
            (other["payload_json"], other["sha256"], first["id"]),
        )
    with pytest.raises(ConflictError) as cross_bound:
        service.get_assignment(
            OWNER, {"kind": "capability", "capability_id": "ask.answer"}
        )
    assert cross_bound.value.code == "inference_assignment_integrity_invalid"

    forged = {
        "committed_effect": {
            "schema": "InferenceAssignment@1",
            "id": second["id"],
            "revision": 999,
        }
    }
    forged_hash = "sha256:" + hashlib.sha256(
        json.dumps(forged, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    with db._connection() as conn:
        conn.execute(
            """UPDATE inference_assignment_commands
                  SET response_json=?,response_sha256=?
                WHERE command_id='integrity-second'""",
            (json.dumps(forged, sort_keys=True, separators=(",", ":")), forged_hash),
        )
    with pytest.raises(ConflictError) as forged_receipt:
        service.set_assignment(
            OWNER,
            {
                "command_id": "integrity-second",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": "speech.rewrite"},
                "entries": [{"profile_id": "integrity-model", "profile_revision": 1}],
            },
        )
    assert forged_receipt.value.code == "inference_assignment_command_integrity_invalid"


def test_selected_group_starter_is_hash_bound_atomic_and_replay_safe(
    db: Database,
) -> None:
    _profile(
        db, "starter-model", claims=("language", _result_claim("thought.interview"))
    )
    service = InferenceAssignmentService(db)
    groups = [
        {
            "group_id": "thoughts_notes",
            "expected_revision": 0,
            "entries": [{"profile_id": "starter-model"}],
            "retry_policy_id": None,
        }
    ]
    preview = service.starter_bundle_preview(OWNER, {"groups": groups})
    assert [group["group_id"] for group in preview["groups"]] == ["thoughts_notes"]
    with pytest.raises(ConflictError) as stale:
        service.apply_starter_bundle(
            OWNER,
            {
                "command_id": "starter-stale",
                "preview_sha256": "sha256:" + "0" * 64,
                "groups": groups,
            },
        )
    assert stale.value.code == "starter_bundle_preview_conflict"
    assert service.list_assignments(OWNER)["assignments"] == []
    body = {
        "command_id": "starter-apply",
        "preview_sha256": preview["preview_sha256"],
        "groups": groups,
    }
    applied = service.apply_starter_bundle(OWNER, body)
    assert len(applied["committed_effect"]["assignments"]) == 1
    assert service.apply_starter_bundle(OWNER, body) == applied
    later = service.set_assignment(
        OWNER,
        {
            "command_id": "starter-later",
            "expected_revision": 1,
            "scope": {"kind": "group", "group_id": "thoughts_notes"},
            "entries": [{"profile_id": "starter-model"}],
        },
    )
    replayed = service.apply_starter_bundle(OWNER, body)
    assert replayed["committed_effect"]["assignments"][0]["revision"] == 1
    assert replayed["current"]["assignments"][0]["revision"] == later["revision"] == 2


def test_assignment_material_is_closed_even_with_a_recomputed_hash(db: Database) -> None:
    _profile(db, "closed-model")
    service = InferenceAssignmentService(db)
    saved = _set(
        service,
        "closed-set",
        {"kind": "capability", "capability_id": "ask.answer"},
        "closed-model",
    )
    with db._connection() as conn:
        row = conn.execute(
            """SELECT payload_json FROM inference_assignment_revisions
                WHERE assignment_id=? AND revision=1""",
            (saved["id"],),
        ).fetchone()
        material = json.loads(str(row["payload_json"]))
        material["unexpected"] = "must fail closed"
        encoded = json.dumps(material, sort_keys=True, separators=(",", ":"))
        digest = "sha256:" + hashlib.sha256(encoded.encode()).hexdigest()
        conn.execute(
            """UPDATE inference_assignment_revisions SET payload_json=?,sha256=?
                WHERE assignment_id=? AND revision=1""",
            (encoded, digest, saved["id"]),
        )
    with pytest.raises(ConflictError) as invalid:
        service.get_assignment(
            OWNER, {"kind": "capability", "capability_id": "ask.answer"}
        )
    assert invalid.value.code == "inference_assignment_integrity_invalid"


def test_default_summary_is_exactly_seven_rows_and_projects_safe_runtime_truth(
    db: Database,
) -> None:
    service = InferenceAssignmentService(db)
    empty = service.assignment_summary(OWNER)
    assert len(empty["rows"]) == 7
    assert empty["rows"][0]["label"] == "Default for AI work"
    assert empty["rows"][0]["repair"] == "Choose default"
    assert empty["issue_count"] == 1

    observed_readiness = _profile(db, "summary-model")
    _set(
        service,
        "summary-set",
        {"kind": "capability", "capability_id": "ask.answer"},
        "summary-model",
    )
    projected = service.get_assignment(
        OWNER, {"kind": "capability", "capability_id": "ask.answer"}
    )
    assert projected["entries"][0]["boundary"] == "local"
    assert projected["entries"][0]["readiness"] == observed_readiness
    with db._connection() as conn:
        conn.execute(
            "UPDATE model_profile_binding_revisions SET enabled=0 WHERE profile_id='summary-model'"
        )
    drifted = service.get_assignment(
        OWNER, {"kind": "capability", "capability_id": "ask.answer"}
    )
    assert drifted["entries"][0]["readiness"] == "disabled"
    assert any(issue["code"] == "binding_disabled" for issue in drifted["issues"])


def test_use_default_preview_and_clear_require_exact_scope_capability(
    db: Database,
) -> None:
    _profile(db, "scope-model")
    service = InferenceAssignmentService(db)
    saved = _set(
        service,
        "scope-set",
        {"kind": "capability", "capability_id": "ask.answer"},
        "scope-model",
    )
    with pytest.raises(ValidationError) as preview:
        service.preview_use_default(
            OWNER,
            scope={"kind": "capability", "capability_id": "ask.answer"},
            capability_id="speech.rewrite",
        )
    assert preview.value.code == "inference_assignment_capability_mismatch"
    with pytest.raises(ValidationError) as clear:
        service.clear_assignment(
            OWNER,
            {
                "command_id": "scope-clear",
                "expected_revision": saved["revision"],
                "scope": {"kind": "capability", "capability_id": "ask.answer"},
                "capability_id": "speech.rewrite",
            },
        )
    assert clear.value.code == "inference_assignment_capability_mismatch"


def test_future_lexical_punctuation_is_not_owner_assignable(db: Database) -> None:
    _profile(db, "punctuation-model")
    capability = process_inference_capability_registry().require("speech.punctuate")
    assert capability.owner_visibility == "future"
    service = InferenceAssignmentService(db)
    with pytest.raises(ValidationError) as refused:
        _set(
            service,
            "assign-future-punctuation",
            {"kind": "capability", "capability_id": "speech.punctuate"},
            "punctuation-model",
        )
    assert refused.value.code == "inference_capability_not_assignable"
    assert "future" not in {
        row["id"] for row in service.assignment_summary(OWNER)["rows"]
    }


def test_heterogeneous_global_chain_is_never_filtered_or_substituted(
    db: Database,
) -> None:
    _profile(db, "text-only")
    service = InferenceAssignmentService(db)
    saved = _set(service, "global-text", {"kind": "global"}, "text-only")
    assert [entry["profile_id"] for entry in saved["entries"]] == ["text-only"]
    ask = service.resolve_effective(OWNER, capability_id="ask.answer")
    speech = service.resolve_effective(OWNER, capability_id="speech.transcribe")
    assert ask["status"] == "assigned"
    assert speech["status"] == "no_compatible_assignment"
    assert [entry["profile_id"] for entry in speech["assignment"]["entries"]] == [
        "text-only"
    ]


def test_legacy_boundary_uses_actual_adapter_and_paired_unknown_fails_closed(
    db: Database,
) -> None:
    db.profiles.upsert(
        profile_id="private-endpoint",
        name="Private",
        kind="openAICompatible",
        base_url="http://192.168.1.20:8080/v1",
        model="qwen",
        context_limit=8192,
    )
    db.profiles.upsert(
        profile_id="paired-old",
        name="Paired",
        kind="desktop",
        model="qwen",
        context_limit=8192,
    )
    service = InferenceAssignmentService(db)
    private = service.set_assignment(
        OWNER,
        {
            "command_id": "legacy-private",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "ask.answer"},
            "entries": [{"profile_id": "legacy-private-endpoint"}],
        },
    )
    assert private["entries"][0]["boundary"] == "private_network"
    assert "192.168.1.20" not in json.dumps(private)
    with pytest.raises(ValidationError) as paired:
        service.set_assignment(
            OWNER,
            {
                "command_id": "legacy-paired",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": "speech.rewrite"},
                "entries": [{"profile_id": "legacy-paired-old"}],
            },
        )
    assert paired.value.code == "inference_assignment_incompatible"


def test_group_retry_policy_is_exact_member_intersection(db: Database) -> None:
    _profile(
        db, "policy-model", claims=("language", _result_claim("thought.interview"))
    )
    service = InferenceAssignmentService(db)
    valid = service.set_assignment(
        OWNER,
        {
            "command_id": "policy-valid",
            "expected_revision": 0,
            "scope": {"kind": "group", "group_id": "thoughts_notes"},
            "entries": [{"profile_id": "policy-model"}],
            "retry_policy_id": "retry.text.standard",
        },
    )
    assert valid["retry_policy_id"] == "retry.text.standard"
    with pytest.raises(ValidationError) as invalid:
        service.set_assignment(
            OWNER,
            {
                "command_id": "policy-invalid",
                "expected_revision": 0,
                "scope": {"kind": "group", "group_id": "writing_dictation"},
                "entries": [{"profile_id": "policy-model"}],
                "retry_policy_id": "retry.text.standard",
            },
        )
    assert invalid.value.code == "inference_assignment_policy_incompatible"


def test_clear_replay_preserves_original_invocation_and_subject_context(
    db: Database,
) -> None:
    for profile_id in ("context-default", "context-subject", "context-invocation"):
        _profile(db, profile_id)
    service = InferenceAssignmentService(db)
    _set(service, "context-global", {"kind": "global"}, "context-default")
    subject_scope = {
        "kind": "subject",
        "subject_kind": "thought",
        "subject_id": "thought-1",
        "capability_id": "ask.answer",
    }
    _set(service, "context-subject-set", subject_scope, "context-subject")
    invocation_scope = {
        "kind": "invocation",
        "invocation_id": "invoke-1",
        "capability_id": "ask.answer",
    }
    _set(service, "context-invocation-set", invocation_scope, "context-invocation")
    clear_body = {
        "command_id": "context-clear",
        "expected_revision": 1,
        "scope": subject_scope,
        "capability_id": "ask.answer",
        "invocation_id": "invoke-1",
        "subject_kind": "thought",
        "subject_id": "thought-1",
    }
    cleared = service.clear_assignment(OWNER, clear_body)
    assert cleared["current"]["inherited_from"] == "invocation"
    later = _set(
        service,
        "context-invocation-later",
        invocation_scope,
        "context-default",
        expected=1,
    )
    replayed = service.clear_assignment(OWNER, clear_body)
    assert replayed["committed_effect"]["revision"] == 2
    assert replayed["current"]["inherited_from"] == "invocation"
    assert replayed["current"]["assignment"]["revision"] == later["revision"] == 2


def test_fourth_fallback_is_an_exact_profile_deletion_dependency(db: Database) -> None:
    profile_ids = [f"fallback-{ordinal}" for ordinal in range(1, 5)]
    for profile_id in profile_ids:
        _profile(db, profile_id)
    service = InferenceAssignmentService(db)
    saved = service.set_assignment(
        OWNER,
        {
            "command_id": "four-leg",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "ask.answer"},
            "entries": [{"profile_id": profile_id} for profile_id in profile_ids],
        },
    )
    with pytest.raises(ConflictError) as referenced:
        ModelProfileService(db).delete_profile(OWNER, "fallback-4", expected_revision=1)
    assert saved["id"] in referenced.value.context["dependent_assignments"]
