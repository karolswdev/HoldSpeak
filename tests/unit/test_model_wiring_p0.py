"""P0 model-wiring regression tests.

Bug A: define-endpoint wrote context_ceiling=0 into deployment_revisions while
inference_deployments carried 16384.  The compatibility checker reads
deployment_revisions, so every defined endpoint was context_unsupported.

Bug B: legacy-profile freeze path must return a typed error on FK constraint
violations instead of a raw HTTP 500.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import replace as _replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.deployment_revisions import DeploymentRevision
from holdspeak.inference_capabilities import (
    InferenceCapabilityRegistry,
    builtin_capability_definitions,
    builtin_retry_policy_definitions,
    process_inference_capability_registry,
)
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.inference_adoption_service import RoutedInferenceCoordinator
from holdspeak.services.model_profile_service import ModelProfileService

OWNER = Principal(PrincipalKind.OWNER, "test-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "wiring.db")


def _make_library_service(db: Database) -> Any:
    """Construct a ModelLibraryApplicationService with minimal stubs."""
    from holdspeak.services.model_library_service import ModelLibraryApplicationService

    class _StubSetup:
        def get_model_library_facts(self, principal: Any) -> dict:
            return {"catalog": {}, "local": {}}

    class _StubAcquisition:
        pass

    return ModelLibraryApplicationService(
        db,
        setup_service=_StubSetup(),
        acquisition_service=_StubAcquisition(),
    )


# ── Bug A: context_ceiling write path ──────────────────────────────────


def test_define_endpoint_writes_nonzero_context_ceiling(db: Database) -> None:
    """define-endpoint must store context_ceiling > 0 in deployment_revisions."""
    svc = _make_library_service(db)
    profile_id = "p0-test-endpoint"
    svc.define_endpoint(OWNER, {
        "request_id": f"req-{uuid.uuid4().hex[:8]}",
        "profile_id": profile_id,
        "expected_profile_revision": 0,
        "label": "P0 Test Endpoint",
        "provider_family": "openai_compatible",
        "model": "qwen3.6",
        "endpoint": "http://192.168.1.43:8080/v1",
        "requires_key": False,
    })
    # Verify deployment_revisions.context_ceiling is NOT 0
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT id, context_ceiling FROM deployment_revisions"
        ).fetchall()
    assert len(rows) >= 1, "No deployment revision created"
    for row in rows:
        assert int(row["context_ceiling"]) > 0, (
            f"deployment_revisions.context_ceiling is {row['context_ceiling']} "
            f"for id={row['id']}; must be >0 after define-endpoint"
        )
    # Cross-check against inference_deployments
    with db._connection() as conn:
        dep_rows = conn.execute(
            "SELECT deployment_id, context_ceiling, execution_revision_id "
            "FROM inference_deployments"
        ).fetchall()
    assert len(dep_rows) >= 1
    for dep in dep_rows:
        rev_row = next(r for r in rows if r["id"] == dep["execution_revision_id"])
        assert int(rev_row["context_ceiling"]) == int(dep["context_ceiling"]), (
            "deployment_revisions.context_ceiling must match "
            "inference_deployments.context_ceiling"
        )


# ── Bug A: context_ceiling read path ──────────────────────────────────


def test_deployment_from_row_preserves_stored_context_ceiling(db: Database) -> None:
    """The v1 read path must preserve the stored context_ceiling, not reset to 0."""
    profiles = ModelProfileService(db)
    # Seed a v1 deployment revision with a non-zero context_ceiling
    from holdspeak.inference_targets import DeploymentIdentity
    identity = DeploymentIdentity(
        destination_id="test-dest",
        kind="private_endpoint",
        engine="openai_compatible",
        model="test-model",
        node="",
        boundary="private_network",
        endpoint="http://192.168.1.43:8080/v1",
        model_path=None,
        secret_slot="",
    )
    revision = _replace(
        DeploymentRevision.from_identity(identity),
        context_ceiling=16_384,
    )
    db.deployment_revisions.upsert(revision)
    # Verify the read path preserves context_ceiling
    with db._connection() as conn:
        row = conn.execute(
            "SELECT * FROM deployment_revisions WHERE id=?", (revision.id,)
        ).fetchone()
    rebuilt = profiles._deployment_from_row(row)
    assert rebuilt.context_ceiling == 16_384, (
        f"_deployment_from_row returned context_ceiling={rebuilt.context_ceiling}; "
        f"expected 16384 (the stored value)"
    )


# ── Bug A: backfill ───────────────────────────────────────────────────


def test_backfill_heals_poisoned_context_ceiling(tmp_path: Path) -> None:
    """The reconcile backfill must heal context_ceiling=0 in deployment_revisions.

    Seeds a pre-fix-shaped DB: deployment_revisions with context_ceiling=0 and
    a matching inference_deployments row with context_ceiling=16384.  After
    the backfill runs, the deployment_revisions row must have 16384.
    """
    db_path = tmp_path / "backfill.db"
    db = Database(db_path)
    # Seed a deployment revision with context_ceiling=0 (the pre-fix state)
    from holdspeak.inference_targets import DeploymentIdentity
    identity = DeploymentIdentity(
        destination_id="test-backfill",
        kind="private_endpoint",
        engine="openai_compatible",
        model="backfill-model",
        node="",
        boundary="private_network",
        endpoint="http://192.168.1.43:8080/v1",
        model_path=None,
        secret_slot="",
    )
    revision = DeploymentRevision.from_identity(identity)
    assert revision.context_ceiling == 0, "Sanity: from_identity produces context_ceiling=0"
    db.deployment_revisions.upsert(revision)
    # Seed a matching inference_deployments row with the correct context_ceiling.
    # This requires an inference_model_artifacts row first (FK constraint).
    artifact_id = f"artifact-backfill-{uuid.uuid4().hex[:8]}"
    manifest_sha = "sha256:" + hashlib.sha256(b"backfill").hexdigest()
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO inference_model_artifacts
               (artifact_id,format,source_kind,source_repository,source_revision,
                manifest_json,manifest_sha256,installed_bytes,state,local_locator,
                created_at,verified_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (artifact_id, "gguf", "test", "test", "r1", "{}", manifest_sha,
             1, "verified", "", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        conn.execute(
            """INSERT INTO inference_deployments
               (deployment_id,destination_id,runtime_id,runtime_revision,artifact_id,
                model_identity,context_ceiling,recommended_context,capability_json,
                capability_sha256,execution_revision_id,configuration_revision,active,
                created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("head-backfill", "test-backfill", "", "", artifact_id,
             "backfill-model", 16_384, 16_384, "{}", "", revision.id, 1, 0,
             "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
    # Run the backfill directly (the reconcile shape-changed gate
    # would not fire on an already-current schema)
    from holdspeak.db.reconcile import _backfill_deployment_revision_context_ceiling
    with db._connection() as conn:
        _backfill_deployment_revision_context_ceiling(conn)
    # Verify the backfill healed the context_ceiling
    with db._connection() as conn:
        row = conn.execute(
            "SELECT context_ceiling FROM deployment_revisions WHERE id=?",
            (revision.id,),
        ).fetchone()
    assert int(row["context_ceiling"]) == 16_384, (
        f"Backfill did not heal context_ceiling: got {row['context_ceiling']}, expected 16384"
    )


# ── Bug A: compatibility check ────────────────────────────────────────


def test_defined_endpoint_is_not_context_unsupported(db: Database) -> None:
    """A defined-endpoint profile must NOT be context_unsupported for chat.turn.

    This is the end-to-end smoke test: define an endpoint, assign it to
    chat.turn, and admit.  The admission must succeed (not fail with
    context_unsupported).
    """
    # Define endpoint
    lib = _make_library_service(db)
    profile_id = "p0-compat-test"
    lib.define_endpoint(OWNER, {
        "request_id": f"req-compat-{uuid.uuid4().hex[:8]}",
        "profile_id": profile_id,
        "expected_profile_revision": 0,
        "label": "P0 Compat Test",
        "provider_family": "openai_compatible",
        "model": "qwen3.6",
        "endpoint": "http://192.168.1.43:8080/v1",
        "requires_key": False,
    })
    # Assign to chat.turn
    assignments = InferenceAssignmentService(db)
    assignments.set_assignment(OWNER, {
        "command_id": f"assign-compat-{uuid.uuid4().hex[:8]}",
        "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "chat.turn"},
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })
    # Admit
    coordinator = RoutedInferenceCoordinator(db)
    inv = "chat_turn_" + uuid.uuid4().hex
    admitted = coordinator.admit(
        OWNER,
        command_id=f"admit-{inv}",
        capability_id="chat.turn",
        operation_id=inv,
        payload={"messages": [{"role": "user", "content": "hello"}]},
        invocation_id=inv,
        reserved_output_tokens=512,
    )
    assert "route_plan" in admitted
    assert "execution" in admitted
    entries = admitted["route_plan"].get("entries", [])
    assert len(entries) >= 1, "Route plan must have at least one entry"


# ── Bug B: FK error handling ──────────────────────────────────────────


def test_legacy_profile_admit_succeeds(db: Database) -> None:
    """Legacy profile admission through chat.turn must succeed, not FK-fail."""
    db.profiles.upsert(
        profile_id="legacy-intel",
        name="Legacy Intel Model",
        kind="openAICompatible",
        base_url="http://192.168.1.43:8080/v1",
        model="qwen3.6",
        requires_key=False,
    )
    # Set context_limit so the legacy path doesn't hit context_unsupported
    with db._connection() as conn:
        conn.execute(
            "UPDATE profiles SET context_limit=? WHERE id=?",
            (16384, "legacy-intel"),
        )
    svc = InferenceAssignmentService(db)
    svc.set_assignment(OWNER, {
        "command_id": f"assign-legacy-{uuid.uuid4().hex[:8]}",
        "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "chat.turn"},
        "entries": [{"profile_id": "legacy-legacy-intel"}],
    })
    coordinator = RoutedInferenceCoordinator(db)
    inv = "chat_turn_" + uuid.uuid4().hex
    admitted = coordinator.admit(
        OWNER,
        command_id=f"admit-{inv}",
        capability_id="chat.turn",
        operation_id=inv,
        payload={"messages": [{"role": "user", "content": "hello"}]},
        invocation_id=inv,
        reserved_output_tokens=512,
    )
    assert "route_plan" in admitted
    # Verify the stored deployment revision has the correct context_ceiling
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT id, context_ceiling FROM deployment_revisions"
        ).fetchall()
    for row in rows:
        assert int(row["context_ceiling"]) == 16384, (
            f"Legacy deployment revision context_ceiling={row['context_ceiling']}; expected 16384"
        )


def test_fk_error_returns_typed_service_error(db: Database) -> None:
    """FK IntegrityError during admit must surface as a typed ServiceError,
    not a raw sqlite3.IntegrityError / HTTP 500."""
    coordinator = RoutedInferenceCoordinator(db)
    # Monkey-patch the freeze to raise a FOREIGN KEY IntegrityError
    original = coordinator.plans._freeze_one_shot_in_transaction

    def _broken_freeze(*args: Any, **kwargs: Any) -> Any:
        raise sqlite3.IntegrityError("FOREIGN KEY constraint failed")

    coordinator.plans._freeze_one_shot_in_transaction = _broken_freeze
    # Seed a minimal assignment
    db.profiles.upsert(
        profile_id="fk-test-profile",
        name="FK Test",
        kind="openAICompatible",
        base_url="http://localhost:1234/v1",
        model="test",
        requires_key=False,
    )
    svc = InferenceAssignmentService(db)
    svc.set_assignment(OWNER, {
        "command_id": f"assign-fk-{uuid.uuid4().hex[:8]}",
        "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "chat.turn"},
        "entries": [{"profile_id": "legacy-fk-test-profile"}],
    })
    inv = "chat_turn_" + uuid.uuid4().hex
    with pytest.raises(ServiceError, match="parent record is missing"):
        coordinator.admit(
            OWNER,
            command_id=f"admit-{inv}",
            capability_id="chat.turn",
            operation_id=inv,
            payload={"messages": [{"role": "user", "content": "hello"}]},
            invocation_id=inv,
            reserved_output_tokens=512,
        )
