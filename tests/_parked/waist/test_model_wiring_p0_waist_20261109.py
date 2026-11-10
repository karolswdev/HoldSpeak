# PARKED 20261109 (door/park-waist): the cases of tests/unit/test_model_wiring_p0.py that drove the parked routed-inference waist.
# Not collected (tests/_parked/conftest.py). Restore with `git revert` of the parking commit.
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
from holdspeak.services.assignment_migration import AssignmentMigration
from holdspeak.services.model_profile_service import ModelProfileService


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
    coordinator = AssignmentMigration(db)
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
    coordinator = AssignmentMigration(db)
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
    coordinator = AssignmentMigration(db)
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
