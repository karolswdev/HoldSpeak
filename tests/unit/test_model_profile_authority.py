"""HSEGHS001HS104-143-03 — reusable model profile authority."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import holdspeak.mcp.tools as mcp_tools
from holdspeak.db import Database
from holdspeak.deployment_revisions import DeploymentRevision
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, NotFound, ServiceError, ValidationError
from holdspeak.services.model_profile_service import (
    ModelProfileService,
    adapt_v1_profile,
    resolve_v1_profile_execution,
)
from holdspeak.services.profile_service import ProfileService
from holdspeak.services.sync_service import SyncService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.primitives.model_profiles import build_model_profiles_router
from holdspeak.web.routes.primitives.profiles import build_profiles_router


OWNER = Principal(PrincipalKind.OWNER, "story-143-owner")
AGENT = Principal(PrincipalKind.AGENT, "story-143-agent")
SERVICE = Principal(PrincipalKind.SERVICE, "story-143-model-turn")


def _manifest() -> dict[str, object]:
    claims = ["language", "structured_output"]
    encoded = json.dumps(
        {"claims": claims, "revision": "capability-evidence-v1"},
        sort_keys=True, separators=(",", ":"),
    ).encode()
    import hashlib

    return {
        "revision": "capability-evidence-v1",
        "sha256": "sha256:" + hashlib.sha256(encoded).hexdigest(),
        "claims": claims,
    }


def _profile_body(
    *,
    profile_id: str = "balanced-qwen",
    expected_revision: int = 0,
    model_or_artifact_identity: str = "artifact-balanced-1",
) -> dict[str, object]:
    return {
        "profile_id": profile_id,
        "expected_revision": expected_revision,
        "label": "Balanced Qwen",
        "provider_family": "local",
        "runtime_family": "llama_cpp_prompt_v1",
        "model_or_artifact_identity": model_or_artifact_identity,
        "supported_modalities": ["language"],
        "context_support": "bounded",
        "tokenizer_template_requirements": {"chat_template": "qwen3"},
        "capability_manifest": _manifest(),
        "safe_presentation": {"summary": "General reasoning"},
    }


def _install_deployment(
    db: Database,
    *,
    revision: int = 1,
    destination_id: str = "this_machine",
    runtime_id: str = "llama_cpp_prompt_v1",
) -> tuple[str, str]:
    artifact_id = f"artifact-balanced-{revision}"
    deployment_id = f"deployment-balanced-{revision}"
    deployment = DeploymentRevision.from_artifact(
        destination_id=destination_id,
        engine="configured_local_engine",
        model="Qwen Balanced",
        runtime_id=runtime_id,
        runtime_revision="0.3.34",
        artifact_id=artifact_id,
        manifest_sha256=f"sha256:{revision:064x}",
        format="gguf",
        architecture="qwen3",
        context_ceiling=8192,
        capability_sha256=str(_manifest()["sha256"]),
    )
    db.deployment_revisions.upsert(deployment)
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO inference_model_artifacts
               (artifact_id,format,source_kind,source_repository,source_revision,
                manifest_json,manifest_sha256,installed_bytes,state,local_locator,
                created_at,verified_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                artifact_id, "gguf", "fixture", "fixture", "r1", "{}",
                deployment.manifest_sha256, 1, "verified", "/private/model.gguf",
                "2026-08-21T00:00:00Z", "2026-08-21T00:00:00Z",
            ),
        )
        conn.execute(
            """INSERT INTO inference_deployments
               (deployment_id,destination_id,runtime_id,runtime_revision,artifact_id,
                model_identity,context_ceiling,recommended_context,capability_json,
                capability_sha256,execution_revision_id,configuration_revision,active,
                created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                deployment_id, destination_id, runtime_id, "0.3.34",
                artifact_id, "Qwen Balanced", 8192, 8192, "{}",
                deployment.capability_sha256, deployment.id, revision, 1,
                "2026-08-21T00:00:00Z", "2026-08-21T00:00:00Z",
            ),
        )
    return deployment_id, deployment.id


def _probe_body(deployment_id: str, deployment_revision_id: str, *, configuration_revision: int = 1) -> dict[str, object]:
    return {
        "profile_id": "balanced-qwen",
        "profile_revision": 1,
        "deployment_head_id": deployment_id,
        "expected_deployment_configuration_revision": configuration_revision,
        "expected_deployment_revision_id": deployment_revision_id,
    }


def _mint_observation(
    service: ModelProfileService,
    deployment_id: str,
    deployment_revision_id: str,
    *,
    configuration_revision: int = 1,
) -> str:
    return str(
        service.probe_profile(
            OWNER,
            _probe_body(
                deployment_id,
                deployment_revision_id,
                configuration_revision=configuration_revision,
            ),
        )["observation_id"]
    )


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "model-profiles.db")


@pytest.fixture(autouse=True)
def _reset_kernel_runtime() -> None:
    """MCP dispatch composes kernel services; never leak its test DB globally."""
    import holdspeak.kernel.runtime as runtime

    runtime._broker = None
    yield
    runtime._broker = None


def test_profile_revision_is_immutable_locator_free_and_hash_server_generated(db: Database) -> None:
    service = ModelProfileService(db)
    first = service.create_profile(OWNER, _profile_body())
    assert first["schema_version"] == 2
    assert first["revision"] == 1
    assert first["sha256"].startswith("sha256:")
    encoded = json.dumps(first, sort_keys=True)
    assert "endpoint" not in encoded
    assert "secret" not in encoded
    assert "model_file" not in encoded
    assert "/private" not in encoded

    second_body = _profile_body(expected_revision=1)
    second_body["label"] = "Balanced Qwen v2"
    second = service.create_profile(OWNER, second_body)
    assert second["revision"] == 2
    assert service.get_profile(OWNER, "balanced-qwen", revision=1)["label"] == "Balanced Qwen"

    with pytest.raises(ValidationError, match="invalid shape"):
        service.create_profile(OWNER, {**_profile_body(profile_id="forged"), "sha256": "sha256:" + "0" * 64})
    with pytest.raises(ValidationError, match="must not contain"):
        service.create_profile(OWNER, {**_profile_body(profile_id="endpoint"), "safe_presentation": {"endpoint": "https://evil.example"}})
    with pytest.raises(ValidationError, match="must not contain"):
        service.create_profile(
            OWNER,
            {
                **_profile_body(profile_id="credential"),
                "safe_presentation": {"summary": "Bearer private-value"},
            },
        )
    forged_manifest = _profile_body(profile_id="forged-manifest")
    forged_manifest["capability_manifest"] = {**_manifest(), "sha256": "sha256:" + "0" * 64}
    with pytest.raises(ValidationError) as forged:
        service.create_profile(OWNER, forged_manifest)
    assert forged.value.code == "model_profile_manifest_hash_invalid"


def test_profile_and_deployment_rows_are_reverified_before_projection_or_binding(db: Database) -> None:
    service = ModelProfileService(db)
    service.create_profile(OWNER, _profile_body())
    with db._connection() as conn:
        conn.execute(
            "UPDATE model_profile_revisions SET label=? WHERE profile_id=? AND revision=1",
            ("https://tampered.example/v1", "balanced-qwen"),
        )
    for action in (
        lambda: service.list_profiles(OWNER),
        lambda: service.get_profile(OWNER, "balanced-qwen"),
    ):
        with pytest.raises(ConflictError) as refusal:
            action()
        assert refusal.value.code == "model_profile_integrity_invalid"

@pytest.mark.parametrize("field,value", [
    ("boundary", "external_service"),
    ("endpoint", "https://tampered.example/v1"),
    ("secret_slot", "tampered-secret-slot"),
])
def test_deployment_content_id_rejects_tampered_private_or_boundary_fields(
    db: Database, monkeypatch, field: str, value: str
) -> None:
    service = ModelProfileService(db)
    service.create_profile(OWNER, _profile_body())
    deployment_id, deployment_revision_id = _install_deployment(db)
    with db._connection() as conn:
        conn.execute(f"UPDATE deployment_revisions SET {field}=? WHERE id=?", (value, deployment_revision_id))
    monkeypatch.setattr(service, "_observe_destination_readiness", lambda *_args, **_kwargs: ("ready", "ready"))
    with pytest.raises(ConflictError) as refusal:
        service.probe_profile(OWNER, _probe_body(deployment_id, deployment_revision_id))
    assert refusal.value.code == "deployment_revision_integrity_invalid"


def test_binding_is_cas_protected_and_freezes_exact_existing_deployment_revision(db: Database) -> None:
    service = ModelProfileService(db)
    service.create_profile(OWNER, _profile_body())
    deployment_id, first_revision = _install_deployment(db)
    observation_id = _mint_observation(service, deployment_id, first_revision)
    bound = service.bind_profile(
        OWNER,
        {
            "binding_id": "binding-balanced",
            "profile_id": "balanced-qwen",
            "profile_revision": 1,
            "deployment_head_id": deployment_id,
            "expected_binding_revision": 0,
            "expected_deployment_configuration_revision": 1,
            "expected_deployment_revision_id": first_revision,
            "enabled": True,
            "readiness_observation_id": observation_id,
        },
    )
    assert bound["deployment_revision_id"] == first_revision
    assert bound["deployment_configuration_revision"] == 1
    assert "secret_slot" not in bound
    assert "readiness_observation_id" not in bound

    with pytest.raises(ConflictError) as forged_observation:
        service.bind_profile(
            OWNER,
            {
                "binding_id": "binding-balanced",
                "profile_id": "balanced-qwen",
                "profile_revision": 1,
                "deployment_head_id": deployment_id,
                "expected_binding_revision": 1,
                "expected_deployment_configuration_revision": 1,
                "expected_deployment_revision_id": first_revision,
                "enabled": True,
                "readiness_observation_id": "ready_client_forged",
            },
        )
    assert forged_observation.value.code == "model_profile_readiness_stale"

    with db._connection() as conn:
        conn.execute(
            "UPDATE inference_deployments SET configuration_revision=2 WHERE deployment_id=?",
            (deployment_id,),
        )
    with pytest.raises(ConflictError) as conflict:
        service.bind_profile(
            OWNER,
            {
                "binding_id": "binding-balanced",
                "profile_id": "balanced-qwen",
                "profile_revision": 1,
                "deployment_head_id": deployment_id,
                "expected_binding_revision": 1,
                "expected_deployment_configuration_revision": 1,
                "expected_deployment_revision_id": first_revision,
                "enabled": True,
                "readiness_observation_id": observation_id,
            },
        )
    assert conflict.value.code == "deployment_head_conflict"
    # A later head change cannot retarget the already-frozen binding.
    assert service.get_binding(OWNER, "binding-balanced")["deployment_revision_id"] == first_revision

    with pytest.raises(ConflictError) as forged_head:
        service.bind_profile(
            OWNER,
            {
                "binding_id": "binding-balanced",
                "profile_id": "balanced-qwen",
                "profile_revision": 1,
                "deployment_head_id": deployment_id,
                "expected_binding_revision": 1,
                "expected_deployment_configuration_revision": 2,
                "expected_deployment_revision_id": "dep2_forged",
                "enabled": True,
                "readiness_observation_id": observation_id,
            },
        )
    assert forged_head.value.code == "deployment_head_conflict"

    with pytest.raises(ValidationError, match="invalid shape"):
        service.bind_profile(
            OWNER,
            {
                "binding_id": "binding-forged",
                "profile_id": "balanced-qwen",
                "profile_revision": 1,
                "deployment_head_id": deployment_id,
                "expected_binding_revision": 1,
                "expected_deployment_configuration_revision": 2,
                "expected_deployment_revision_id": first_revision,
                "enabled": True,
                "readiness_observation_id": observation_id,
                "deployment_revision_id": "forged",
            },
        )


def test_probe_mints_server_readiness_and_refuses_head_drift(db: Database, monkeypatch) -> None:
    service = ModelProfileService(db)
    service.create_profile(OWNER, _profile_body())
    deployment_id, deployment_revision_id = _install_deployment(db)
    monkeypatch.setattr(
        service, "_observe_destination_readiness", lambda *_args, **_kwargs: ("ready", "ready")
    )
    observation = service.probe_profile(OWNER, _probe_body(deployment_id, deployment_revision_id))
    assert observation["observation_id"].startswith("ready_")
    assert observation["state"] == "ready"
    assert "endpoint" not in json.dumps(observation, sort_keys=True)

    with db._connection() as conn:
        conn.execute(
            "UPDATE inference_deployments SET configuration_revision=2 WHERE deployment_id=?",
            (deployment_id,),
        )
    with pytest.raises(ConflictError) as drift:
        service.bind_profile(
            OWNER,
            {
                "binding_id": "binding-balanced",
                "profile_id": "balanced-qwen",
                "profile_revision": 1,
                "deployment_head_id": deployment_id,
                "expected_binding_revision": 0,
                "expected_deployment_configuration_revision": 2,
                "expected_deployment_revision_id": deployment_revision_id,
                "enabled": True,
                "readiness_observation_id": observation["observation_id"],
            },
        )
    assert drift.value.code == "model_profile_readiness_stale"


def test_binding_refuses_a_deployment_that_does_not_substantiate_profile_identity(
    db: Database, monkeypatch
) -> None:
    service = ModelProfileService(db)
    service.create_profile(OWNER, _profile_body())
    deployment_id, deployment_revision_id = _install_deployment(db, revision=2)
    monkeypatch.setattr(
        service, "_observe_destination_readiness", lambda *_args, **_kwargs: ("ready", "ready")
    )
    observation_id = _mint_observation(
        service, deployment_id, deployment_revision_id, configuration_revision=2
    )
    with pytest.raises(ConflictError) as mismatch:
        service.bind_profile(
            OWNER,
            {
                "binding_id": "binding-balanced",
                "profile_id": "balanced-qwen",
                "profile_revision": 1,
                "deployment_head_id": deployment_id,
                "expected_binding_revision": 0,
                "expected_deployment_configuration_revision": 2,
                "expected_deployment_revision_id": deployment_revision_id,
                "enabled": True,
                "readiness_observation_id": observation_id,
            },
        )
    assert mismatch.value.code == "model_profile_deployment_mismatch"


def test_probe_uses_destination_authority_for_local_runtime_and_hosted_endpoint(
    db: Database, monkeypatch
) -> None:
    from types import SimpleNamespace

    service = ModelProfileService(db)
    service.create_profile(OWNER, _profile_body())
    local_id, local_revision = _install_deployment(db, runtime_id="missing_runtime")
    monkeypatch.setattr(
        "holdspeak.inference_targets.resolve_inference_target",
        lambda *_args, **_kwargs: SimpleNamespace(ready=True, readiness_state="ready"),
    )
    local = service.probe_profile(OWNER, _probe_body(local_id, local_revision))
    assert local["state"] == "unavailable"
    assert local["reason_code"] == "runtime_unavailable"

    db.profiles.upsert(
        profile_id="hosted", name="Hosted", kind="openAICompatible",
        base_url="https://private.example/v1", model="qwen", requires_key=False,
    )
    hosted_id, hosted_revision = _install_deployment(
        db, revision=2, destination_id="hosted", runtime_id="openai_compatible_v1"
    )
    monkeypatch.setattr(
        "holdspeak.services.profile_service.ProfileService.probe_inference_target",
        lambda *_args, **_kwargs: {"reachable": False, "latency_ms": 1, "models": [], "error": "private"},
    )
    hosted = service.probe_profile(
        OWNER, _probe_body(hosted_id, hosted_revision, configuration_revision=2)
    )
    assert hosted["state"] == "unavailable"
    assert hosted["reason_code"] == "endpoint_unreachable"
    assert "private.example" not in json.dumps(hosted, sort_keys=True)


def test_probe_marks_acquired_unassigned_local_deployment_ready_only_with_artifact_and_runtime(
    db: Database, monkeypatch
) -> None:
    service = ModelProfileService(db)
    service.create_profile(OWNER, _profile_body())
    deployment_id, deployment_revision_id = _install_deployment(db)
    monkeypatch.setattr(
        "holdspeak.services.inference_setup_service.inspect_runtimes",
        lambda **_kwargs: [{
            "id": "llama_cpp_prompt_v1",
            "availability": {"state": "available"},
            "thought_support": {"state": "supported"},
        }],
    )
    # No Config route is written by acquisition.  The exact deployment can
    # still be ready: its verified artifact + captured runtime are the local
    # destination's readiness authority, not a global assignment pointer.
    observation = service.probe_profile(OWNER, _probe_body(deployment_id, deployment_revision_id))
    assert observation["state"] == "ready"

    with db._connection() as conn:
        conn.execute(
            "UPDATE inference_model_artifacts SET state='quarantined' WHERE artifact_id='artifact-balanced-1'"
        )
    corrupt = service.probe_profile(OWNER, _probe_body(deployment_id, deployment_revision_id))
    assert corrupt["state"] == "unavailable"
    assert corrupt["reason_code"] == "artifact_unavailable"


def test_profile_binding_survives_database_restart(db: Database, monkeypatch) -> None:
    service = ModelProfileService(db)
    service.create_profile(OWNER, _profile_body())
    deployment_id, deployment_revision_id = _install_deployment(db)
    monkeypatch.setattr(
        service, "_observe_destination_readiness", lambda *_args, **_kwargs: ("ready", "ready")
    )
    observation_id = _mint_observation(service, deployment_id, deployment_revision_id)
    service.bind_profile(
        OWNER,
        {
            "binding_id": "binding-balanced",
            "profile_id": "balanced-qwen",
            "profile_revision": 1,
            "deployment_head_id": deployment_id,
            "expected_binding_revision": 0,
            "expected_deployment_configuration_revision": 1,
            "expected_deployment_revision_id": deployment_revision_id,
            "enabled": True,
            "readiness_observation_id": observation_id,
        },
    )
    db.close()
    restarted = ModelProfileService(Database(db.db_path))
    profile = restarted.get_profile(OWNER, "balanced-qwen")
    assert profile["revision"] == 1
    assert profile["current_binding"]["binding_id"] == "binding-balanced"
    assert profile["current_binding"]["revision"] == 1
    assert profile["latest_readiness"]["observation_id"] == observation_id
    listed = restarted.list_profiles(OWNER)["profiles"]
    assert listed == [profile]
    assert restarted.get_binding(OWNER, "binding-balanced")["deployment_revision_id"] == deployment_revision_id


def test_deletion_names_exact_assignment_dependency_and_keeps_revision_history(db: Database) -> None:
    service = ModelProfileService(db)
    service.create_profile(OWNER, _profile_body())
    with db._connection() as conn:
        conn.execute("CREATE TABLE inference_assignments (id TEXT PRIMARY KEY, profile_id TEXT NOT NULL)")
        conn.execute(
            "INSERT INTO inference_assignments(id,profile_id) VALUES (?,?)",
            ("assignment-thoughts", "balanced-qwen"),
        )
    with pytest.raises(ConflictError) as refusal:
        service.delete_profile(OWNER, "balanced-qwen", expected_revision=1)
    assert refusal.value.code == "model_profile_referenced"
    assert refusal.value.context["dependent_assignments"] == ["assignment-thoughts"]

    with db._connection() as conn:
        conn.execute("DELETE FROM inference_assignments")
    service.create_profile(OWNER, _profile_body(expected_revision=1))
    with pytest.raises(ConflictError) as stale_delete:
        service.delete_profile(OWNER, "balanced-qwen", expected_revision=1)
    assert stale_delete.value.code == "model_profile_revision_conflict"
    assert service.delete_profile(OWNER, "balanced-qwen", expected_revision=2) == {"profile_id": "balanced-qwen", "deleted": True}
    with pytest.raises(NotFound):
        service.get_profile(OWNER, "balanced-qwen")
    with db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM model_profile_revisions WHERE profile_id='balanced-qwen'").fetchone()[0] == 2


def test_dependency_provider_is_registered_exact_and_fails_closed_when_malformed(db: Database) -> None:
    service = ModelProfileService(
        db,
        dependency_providers={"malformed": lambda _conn, _profile_id: [{"id": "missing-kind"}]},
    )
    service.create_profile(OWNER, _profile_body())
    with pytest.raises(ConflictError) as refusal:
        service.delete_profile(OWNER, "balanced-qwen", expected_revision=1)
    assert refusal.value.code == "model_profile_referenced"
    assert {"kind": "dependency_provider_error", "id": "malformed"} in refusal.value.context["dependencies"]


def test_v1_adapter_is_deterministic_read_only_and_never_projects_path_endpoint_or_their_hash(db: Database) -> None:
    db.profiles.upsert(
        profile_id="legacy-one", name="Legacy endpoint", kind="openAICompatible",
        base_url="https://private.example/v1", model="qwen", node="private-node",
        model_file="/secret/models/never-project.gguf", requires_key=True,
    )
    stored_before = db.profiles.get("legacy-one").to_dict()
    service = ModelProfileService(db)
    adapted = service.get_profile(OWNER, "legacy-legacy-one")
    assert adapted == service.get_profile(OWNER, "legacy-legacy-one")
    assert db.profiles.get("legacy-one").to_dict() == stored_before
    encoded = json.dumps(adapted, sort_keys=True)
    for private in ("/secret/models", "private.example", "private-node", "model_file", "base_url", "secret_slot"):
        assert private not in encoded
    with db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM model_profile_revisions").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM model_profile_binding_revisions").fetchone()[0] == 0

    # Two different v1 locators/endpoints cannot perturb public identity proof.
    alternate = db.profiles.upsert(
        profile_id="legacy-two", name="Legacy endpoint", kind="openAICompatible",
        base_url="https://different.example/v1", model="qwen", node="other-node",
        model_file="/somewhere/else.gguf", requires_key=True,
    )
    first = adapt_v1_profile(db.profiles.get("legacy-one"))["profile"]
    second = adapt_v1_profile(alternate)["profile"]
    assert first["sha256"] != second["sha256"]  # stable IDs differ by design
    first_without_id = {key: value for key, value in first.items() if key not in {"profile_id", "sha256"}}
    second_without_id = {key: value for key, value in second.items() if key not in {"profile_id", "sha256"}}
    assert first_without_id == second_without_id

    db.profiles.upsert(
        profile_id="legacy-private-text", name="https://private-name.example/v1",
        kind="openAICompatible", base_url="https://private-endpoint.example/v1",
        model="/secret/model-name.gguf", model_file="/secret/model-file.gguf",
    )
    private_projection = service.get_profile(OWNER, "legacy-legacy-private-text")
    private_encoded = json.dumps(private_projection, sort_keys=True)
    assert "private-name.example" not in private_encoded
    assert "/secret/model" not in private_encoded

    db.profiles.upsert(
        profile_id="legacy-secret-text", name="Bearer private-value",
        kind="openAICompatible", model="sk-private-secret-12345678",
    )
    secret_projection = service.get_profile(OWNER, "legacy-legacy-secret-text")
    secret_encoded = json.dumps(secret_projection, sort_keys=True)
    assert "private-value" not in secret_encoded
    assert "sk-private" not in secret_encoded


def test_v1_execution_adapter_is_read_only_and_matches_legacy_deployment_and_receipt(db: Database) -> None:
    from holdspeak.inference_targets import target_from_profile

    profile = db.profiles.upsert(
        profile_id="legacy-execution", name="Legacy execution", kind="openAICompatible",
        base_url="https://private.example/v1", model="qwen/legacy", requires_key=False,
    )
    before = profile.to_dict()
    legacy_target = target_from_profile(profile, db=db)
    adapted = resolve_v1_profile_execution(profile, db=db)
    assert adapted.deployment_revision == DeploymentRevision.from_identity(legacy_target.deployment)
    assert adapted.receipt == legacy_target.placement_receipt()
    assert adapted.source_profile_id == "legacy-execution"
    assert db.profiles.get("legacy-execution").to_dict() == before
    with db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM model_profile_revisions").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM model_profile_binding_revisions").fetchone()[0] == 0


def test_owner_matrix_covers_v2_service_legacy_service_http_and_mcp(db: Database, monkeypatch) -> None:
    profiles = ModelProfileService(db)
    legacy = ProfileService(db)
    for principal in (AGENT, SERVICE, None):
        with pytest.raises(ServiceError, match="Owner access"):
            profiles.list_profiles(principal)  # type: ignore[arg-type]
        with pytest.raises(ServiceError, match="Owner access"):
            profiles.get_profile(principal, "not-visible")  # type: ignore[arg-type]
        with pytest.raises(ServiceError, match="Owner access"):
            profiles.create_profile(principal, _profile_body(profile_id="denied"))  # type: ignore[arg-type]
        with pytest.raises(ServiceError, match="Owner access"):
            profiles.bind_profile(principal, {})  # type: ignore[arg-type]
        with pytest.raises(ServiceError, match="Owner access"):
            profiles.probe_profile(principal, {})  # type: ignore[arg-type]
        with pytest.raises(ServiceError, match="Owner access"):
            profiles.unbind_profile(principal, "not-visible", expected_binding_revision=1)  # type: ignore[arg-type]
        with pytest.raises(ServiceError, match="Owner access"):
            profiles.delete_profile(principal, "not-visible", expected_revision=1)  # type: ignore[arg-type]
        with pytest.raises(ServiceError, match="Owner access"):
            legacy.list_profiles(principal)  # type: ignore[arg-type]
        with pytest.raises(ServiceError, match="Owner access"):
            legacy.get_profile(principal, "anything")  # type: ignore[arg-type]
        with pytest.raises(ServiceError, match="Owner access"):
            legacy.create_profile(principal, {})  # type: ignore[arg-type]
        with pytest.raises(ServiceError, match="Owner access"):
            legacy.update_profile(principal, "anything", {})  # type: ignore[arg-type]
        with pytest.raises(ServiceError, match="Owner access"):
            legacy.delete_profile(principal, "anything")  # type: ignore[arg-type]
        with pytest.raises(ServiceError, match="Owner access"):
            legacy.probe_inference_target(principal, "anything")  # type: ignore[arg-type]

    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    monkeypatch.setattr("holdspeak.db.get_observer", lambda: None)
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next):
        request.state.principal = OWNER if request.headers.get("x-test-principal") == "owner" else AGENT
        return await call_next(request)

    app.include_router(build_profiles_router(WebContext(get_state=lambda: {})))
    app.include_router(build_model_profiles_router())
    client = TestClient(app)
    assert client.get("/api/inference-targets").status_code == 403
    assert client.get("/api/model-profiles").status_code == 403
    assert client.get("/api/model-profiles/not-visible").status_code == 403
    assert client.post("/api/model-profiles", json={}).status_code == 403
    assert client.post("/api/model-profiles/not-visible/probe", json={}).status_code == 403
    assert client.post("/api/model-profiles/not-visible/binding", json={}).status_code == 403
    assert client.delete("/api/model-profiles/not-visible/binding").status_code == 403
    assert client.delete("/api/model-profiles/not-visible").status_code == 403

    monkeypatch.setattr(mcp_tools, "get_database", lambda: db)
    with pytest.raises(ServiceError, match="Owner access"):
        mcp_tools.dispatch("destination.list", {}, AGENT)
    with pytest.raises(ServiceError, match="Owner access"):
        mcp_tools.dispatch("model_profile.list", {}, AGENT)
    with pytest.raises(ServiceError, match="Owner access"):
        mcp_tools.dispatch("model_profile.get", {"profile_id": "not-visible"}, AGENT)
    with pytest.raises(ServiceError, match="Owner access"):
        mcp_tools.dispatch("model_profile.create", {"profile": {}}, AGENT)
    with pytest.raises(ServiceError, match="Owner access"):
        mcp_tools.dispatch("model_profile.probe", {}, AGENT)
    with pytest.raises(ServiceError, match="Owner access"):
        mcp_tools.dispatch("model_profile.bind", {"binding": {}}, AGENT)
    with pytest.raises(ServiceError, match="Owner access"):
        mcp_tools.dispatch(
            "model_profile.unbind",
            {"profile_id": "not-visible", "expected_binding_revision": 1},
            AGENT,
        )
    with pytest.raises(ServiceError, match="Owner access"):
        mcp_tools.dispatch(
            "model_profile.delete",
            {"profile_id": "not-visible", "expected_revision": 1},
            AGENT,
        )

    profiles.create_profile(OWNER, _profile_body())
    http = client.get("/api/model-profiles/balanced-qwen", headers={"x-test-principal": "owner"})
    assert http.status_code == 200
    assert http.json()["profile"] == mcp_tools.dispatch(
        "model_profile.get", {"profile_id": "balanced-qwen"}, OWNER
    )

    deployment_id, deployment_revision_id = _install_deployment(db)
    monkeypatch.setattr(
        ModelProfileService, "_observe_destination_readiness",
        lambda *_args, **_kwargs: ("ready", "ready"),
    )
    probe = _probe_body(deployment_id, deployment_revision_id)
    http_probe = client.post(
        "/api/model-profiles/balanced-qwen/probe",
        json=probe,
        headers={"x-test-principal": "owner"},
    )
    assert http_probe.status_code == 201
    mcp_probe = mcp_tools.dispatch("model_profile.probe", {"probe": probe}, OWNER)
    assert set(http_probe.json()["observation"]) == set(mcp_probe)
    assert http_probe.json()["observation"]["state"] == mcp_probe["state"] == "ready"


def test_mcp_model_profile_request_schemas_are_recursively_closed() -> None:
    tools = {tool["name"]: tool["inputSchema"] for tool in mcp_tools.TOOLS}
    profile = tools["model_profile.create"]["properties"]["profile"]
    binding = tools["model_profile.bind"]["properties"]["binding"]
    probe = tools["model_profile.probe"]["properties"]["probe"]
    assert profile["additionalProperties"] is False
    assert binding["additionalProperties"] is False
    assert probe["additionalProperties"] is False
    assert profile["properties"]["tokenizer_template_requirements"]["additionalProperties"] is False
    assert profile["properties"]["capability_manifest"]["additionalProperties"] is False
    assert profile["properties"]["safe_presentation"]["additionalProperties"] is False


def test_v2_profile_and_binding_are_hub_local_and_hostile_sync_refuses(db: Database) -> None:
    service = ModelProfileService(db)
    service.create_profile(OWNER, _profile_body())
    with pytest.raises(ValidationError) as refusal:
        SyncService(db).push(
            OWNER,
            {
                "notes": [],
                "model_profile_revisions": [{"profile_id": "remote", "model_file": "/leak"}],
                "model_profile_bindings": [{"profile_id": "remote", "endpoint": "https://leak"}],
                "model_profile_readiness_observations": [{"observation_id": "forged"}],
            },
        )
    assert refusal.value.code == "sync_hub_local_bucket_forbidden"
    with db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM model_profile_revisions").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM model_profile_binding_revisions").fetchone()[0] == 0
    pulled = SyncService(db).pull(OWNER)
    assert "model_profile_revisions" not in pulled
    assert "model_profile_bindings" not in pulled
