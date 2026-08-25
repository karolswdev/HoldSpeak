"""HSEGHS001HS104-143-05 — immutable route and request-plan evidence."""

from __future__ import annotations

import json
import socket
import sqlite3
import time
import hashlib
import urllib.request
from contextlib import contextmanager
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, ServiceError, ValidationError
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.inference_route_plan_service import (
    InferenceRoutePlanService,
    ROUTE_PLANNING_AUTHORITY,
    RouteAdmissionEvidenceProvider,
)
from holdspeak.inference_capabilities import process_inference_capability_registry
from holdspeak.services.sync_service import SyncService
from holdspeak.services.model_profile_service import ModelProfileService
from tests.unit.test_phase143_inference_assignments import OWNER, _profile


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "route-plans.db")


def _assign(db: Database, profiles: list[str], *, command: str = "assign-route") -> None:
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": command,
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "ask.answer"},
            "entries": [
                {"profile_id": profile_id, "profile_revision": 1}
                for profile_id in profiles
            ],
        },
    )


def _ready_route(db: Database, *, profiles: tuple[str, ...] = ("quick", "deep")) -> InferenceRoutePlanService:
    for profile_id in profiles:
        _profile(db, profile_id)
    _assign(db, list(profiles))
    return InferenceRoutePlanService(db)


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(encoded.encode()).hexdigest()


def _evidence_service(db: Database, *, entries: list[dict[str, object]], reference: str, budgets: list[dict[str, object]] | None = None) -> InferenceRoutePlanService:
    capability = process_inference_capability_registry().require("ask.answer")
    policy = f"{capability.operation_contract.name}@{capability.operation_contract.version}:{capability.schema_sha256}"
    with db._connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS test_route_admission_evidence(ref TEXT PRIMARY KEY,payload_json TEXT NOT NULL)")
        conn.execute("INSERT OR REPLACE INTO test_route_admission_evidence VALUES (?,?)", (reference, json.dumps({"evidence_ref": reference, "material_snapshot_sha256": _digest({"snapshot": reference}), "entries": entries}, sort_keys=True)))

    def freeze(conn: object, planning_reference: str, _operation_id: str) -> dict[str, object]:
        row = conn.execute("SELECT payload_json FROM test_route_admission_evidence WHERE ref=?", (planning_reference,)).fetchone()
        return json.loads(str(row["payload_json"]))

    def reconstruct(conn: object, evidence_ref: str) -> dict[str, object]:
        row = conn.execute("SELECT payload_json FROM test_route_admission_evidence WHERE ref=?", (evidence_ref,)).fetchone()
        return json.loads(str(row["payload_json"]))

    def reconstruct_budgets(_conn: object, evidence_ref: str) -> dict[str, object]:
        return {
            "schema": "RouteAttemptBudgetEvidence@1",
            "evidence_ref": evidence_ref,
            "material_snapshot_sha256": _digest({"snapshot": reference}),
            "entries": budgets or [],
        }

    provider = RouteAdmissionEvidenceProvider(
        id="test-parent-evidence",
        revision=1,
        capabilities=((capability.id, capability.revision, capability.schema_sha256),),
        operation_policy_revisions=(policy,),
        freeze=freeze,
        reconstruct=reconstruct,
        reconstruct_attempt_budgets=reconstruct_budgets if budgets is not None else None,
    )
    return InferenceRoutePlanService(db, operation_evidence_providers=(provider,))


def test_pure_resolution_is_one_snapshot_zero_write_and_fast(
    db: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _ready_route(db, profiles=("tiny", "quick", "balanced", "deep"))
    writes: list[str] = []
    original_connection = db._connection

    @contextmanager
    def audited_connection():
        with original_connection() as conn:
            conn.set_trace_callback(
            lambda sql: writes.append(sql)
            if sql.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE", "REPLACE"))
            else None
            )
            yield conn

    monkeypatch.setattr(db, "_connection", audited_connection)
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("pure route resolution crossed an external/scan seam")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    monkeypatch.setattr(Path, "exists", forbidden)
    monkeypatch.setattr(Path, "glob", forbidden)
    for ordinal in range(5):
        service.resolve_route_plan(
            ROUTE_PLANNING_AUTHORITY,
            capability_id="ask.answer",
            plan_id=f"irp_warm_{ordinal}",
        )
    values, timings = [], []
    for ordinal in range(80):
        started = time.perf_counter()
        values.append(service.resolve_route_plan(
            ROUTE_PLANNING_AUTHORITY, capability_id="ask.answer", plan_id=f"irp_preview_{ordinal}"
        ))
        timings.append((time.perf_counter() - started) * 1000)
    p95 = sorted(timings)[int(len(timings) * 0.95) - 1]
    assert writes == []
    assert p95 < 10
    assert [entry["ordinal"] for entry in values[0]["entries"]] == [1, 2, 3, 4]
    encoded = json.dumps(values[0])
    assert "/private/" not in encoded
    assert "endpoint" not in encoded and "secret" not in encoded


def test_disabled_leg_is_retained_as_frozen_preflight_unavailable(db: Database) -> None:
    _profile(db, "offline", ready=False)
    _assign(db, ["offline"])
    evidence_entries = [{
        "route_leg_ordinal": 1,
        "eligibility": "known_preflight_unavailable",
        "reason_code": "binding_not_ready",
    }]
    service = _evidence_service(db, entries=evidence_entries, reference="offline-source")
    result = service.freeze_one_shot(
        ROUTE_PLANNING_AUTHORITY,
        command_id="offline-shot",
        route_request={"capability_id": "ask.answer"},
        operation_id="offline-operation",
        planning_reference="offline-source",
    )
    assert len(result["route_plan"]["entries"]) == 1
    assert result["operation_request_plan"]["entries"][0] == {
        "route_leg_ordinal": 1,
        "eligibility": "known_preflight_unavailable",
        "reason_code": "binding_not_ready",
        "admitted_request_id": None,
        "admitted_request_sha256": None,
        "context_plan_sha256": None,
        "serialized_request_sha256": None,
    }


def test_freeze_replay_and_restart_ignore_later_assignment_mutation(db: Database) -> None:
    service = _ready_route(db)
    frozen = service.freeze_route_plan(
        ROUTE_PLANNING_AUTHORITY,
        command_id="freeze-1",
        capability_id="ask.answer",
    )
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "replace-route",
            "expected_revision": 1,
            "scope": {"kind": "capability", "capability_id": "ask.answer"},
            "entries": [{"profile_id": "deep", "profile_revision": 1}],
        },
    )
    replay = service.freeze_route_plan(
        ROUTE_PLANNING_AUTHORITY,
        command_id="freeze-1",
        capability_id="ask.answer",
    )
    restarted = InferenceRoutePlanService(Database(db.db_path)).get_route_plan(
        OWNER, frozen["id"]
    )
    assert replay == frozen == restarted
    assert [entry["profile_id"] for entry in restarted["entries"]] == ["quick", "deep"]
    with pytest.raises(ConflictError):
        service.freeze_route_plan(
            ROUTE_PLANNING_AUTHORITY,
            command_id="freeze-1",
            capability_id="ask.answer",
            invocation_id="different-request",
        )


def test_freeze_requests_are_closed_and_identity_collisions_are_named(db: Database) -> None:
    service = _ready_route(db, profiles=("quick",))
    with pytest.raises(Exception) as private:
        service.freeze_route_plan(
            ROUTE_PLANNING_AUTHORITY, command_id="private-extra",
            capability_id="ask.answer", prompt="PRIVATE",
        )
    assert getattr(private.value, "code", "") == "inference_route_plan_invalid"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_plans WHERE id='irp_private'").fetchone()[0] == 0
    first = service.freeze_route_plan(
        ROUTE_PLANNING_AUTHORITY, command_id="identity-one",
        capability_id="ask.answer",
    )
    second = service.freeze_route_plan(
        ROUTE_PLANNING_AUTHORITY, command_id="identity-two",
        capability_id="ask.answer",
    )
    assert first["id"] != second["id"]
    with pytest.raises(Exception) as nested:
        service.freeze_one_shot(
            ROUTE_PLANNING_AUTHORITY, command_id="nested-private",
            route_request={"capability_id": "ask.answer", "endpoint": "PRIVATE"},
            operation_id="nested-operation", planning_reference="nested-source",
        )
    assert getattr(nested.value, "code", "") == "inference_route_plan_invalid"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_plans WHERE id='irp_nested'").fetchone()[0] == 0


def test_command_pointer_tamper_and_operation_identity_collisions_refuse(db: Database) -> None:
    service = _ready_route(db, profiles=("quick",))
    first = service.freeze_route_plan(ROUTE_PLANNING_AUTHORITY, command_id="pointer-one", capability_id="ask.answer")
    second = service.freeze_route_plan(ROUTE_PLANNING_AUTHORITY, command_id="pointer-two", capability_id="ask.answer")
    with db._connection() as conn:
        with pytest.raises(sqlite3.IntegrityError, match="immutable inference route command"):
            conn.execute("UPDATE inference_route_plan_commands SET plan_id=?,plan_sha256=? WHERE command_id='pointer-one'", (second["id"], second["sha256"]))
    assert service.freeze_route_plan(ROUTE_PLANNING_AUTHORITY, command_id="pointer-one", capability_id="ask.answer") == first
    assert first["id"] != second["id"]

    evidence_entries = [{
        "route_leg_ordinal": 1,
        "eligibility": "known_preflight_unavailable",
        "reason_code": "binding_not_ready",
    }]
    with db._connection() as conn:
        conn.execute("UPDATE model_profile_readiness_observations SET state='unavailable'")
    operation_service = _evidence_service(db, entries=evidence_entries, reference="collision-source")
    first_operation = operation_service.freeze_one_shot(
        ROUTE_PLANNING_AUTHORITY, command_id="operation-one",
        route_request={"capability_id": "ask.answer"},
        operation_id="shared-operation", planning_reference="collision-source",
    )
    second_operation = operation_service.freeze_one_shot(
        ROUTE_PLANNING_AUTHORITY, command_id="operation-two",
        route_request={"capability_id": "ask.answer"},
        operation_id="second-operation", planning_reference="collision-source",
    )
    with db._connection() as conn:
        with pytest.raises(sqlite3.IntegrityError, match="immutable operation route command"):
            conn.execute(
                """UPDATE inference_operation_route_request_plan_commands
                   SET route_plan_id=?,route_plan_sha256=?,operation_plan_id=?,operation_plan_sha256=?
                   WHERE command_id='operation-one'""",
                (
                    second_operation["route_plan"]["id"],
                    second_operation["route_plan"]["sha256"],
                    second_operation["operation_request_plan"]["id"],
                    second_operation["operation_request_plan"]["sha256"],
                ),
            )
    assert operation_service.freeze_one_shot(
        ROUTE_PLANNING_AUTHORITY, command_id="operation-one",
        route_request={"capability_id": "ask.answer"},
        operation_id="shared-operation", planning_reference="collision-source",
    ) == first_operation
    with pytest.raises(ConflictError) as collision:
        operation_service.freeze_one_shot(
            ROUTE_PLANNING_AUTHORITY, command_id="collision-shared-operation",
            route_request={"capability_id": "ask.answer"},
            operation_id="shared-operation", planning_reference="collision-source",
        )
    assert collision.value.code == "inference_operation_route_plan_id_conflict"


def test_recomputed_payload_hash_cannot_forge_retry_or_leg_evidence(db: Database) -> None:
    service = _ready_route(db)
    route = service.freeze_route_plan(
        ROUTE_PLANNING_AUTHORITY,
        command_id="freeze-tamper",
        capability_id="ask.answer",
    )
    with db._connection() as conn:
        row = conn.execute("SELECT payload_json FROM inference_route_plans WHERE id=?", (route["id"],)).fetchone()
        value = json.loads(str(row["payload_json"]))
        value["retry_policy"]["total_physical_attempts"] += 20
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        digest = "sha256:" + hashlib.sha256(encoded.encode()).hexdigest()
        conn.execute("UPDATE inference_route_plans SET payload_json=?,sha256=? WHERE id=?", (encoded, digest, route["id"]))
    with pytest.raises(ConflictError) as invalid:
        service.get_route_plan(OWNER, route["id"])
    assert invalid.value.code == "inference_route_plan_integrity_invalid"


def test_cross_bound_assignment_profile_and_binding_tamper_refuses(db: Database) -> None:
    service = _ready_route(db)
    route = service.freeze_route_plan(
        ROUTE_PLANNING_AUTHORITY,
        command_id="freeze-cross-bind",
        capability_id="ask.answer",
    )
    with db._connection() as conn:
        source = route["source"]
        row = conn.execute(
            "SELECT payload_json FROM inference_assignment_revisions WHERE assignment_id=? AND revision=?",
            (source["assignment_id"], source["assignment_revision"]),
        ).fetchone()
        material = json.loads(str(row["payload_json"]))
        material["entries"].reverse()
        encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        digest = "sha256:" + hashlib.sha256(encoded.encode()).hexdigest()
        conn.execute(
            "UPDATE inference_assignment_revisions SET payload_json=?,sha256=? WHERE assignment_id=? AND revision=?",
            (encoded, digest, source["assignment_id"], source["assignment_revision"]),
        )
    with pytest.raises(ConflictError):
        service.get_route_plan(OWNER, route["id"])


def test_legacy_adapter_is_pure_and_never_projects_locator_or_endpoint(
    db: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO profiles
               (id,name,kind,model_file,base_url,model,node,context_limit,requires_key,created_at,last_modified,deleted)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,0)""",
            ("legacy-cloud", "Legacy", "openAICompatible", "/private/model.gguf", "https://secret.example/v1", "legacy-model", "", 16384, 1, "2026-08-21T00:00:00Z", "2026-08-21T00:00:00Z"),
        )
    original_exists = Path.exists
    monkeypatch.setattr(Path, "exists", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("scan")))
    service = InferenceRoutePlanService(db)
    try:
        route = service.freeze_legacy_one_leg_plan(
            ROUTE_PLANNING_AUTHORITY,
            command_id="legacy-freeze",
            capability_id="ask.answer",
            legacy_profile_id="legacy-cloud",
        )
    finally:
        monkeypatch.setattr(Path, "exists", original_exists)
    encoded = json.dumps(route)
    assert "secret.example" not in encoded
    assert "/private/" not in encoded
    assert "secret_slot" not in encoded
    assert service.get_route_plan(OWNER, route["id"]) == route


def test_legacy_adapter_refuses_unproved_structured_capability_before_writes(db: Database) -> None:
    with db._connection() as conn:
        conn.execute("INSERT INTO profiles(id,name,kind,model_file,model,context_limit,created_at,last_modified) VALUES (?,?,?,?,?,?,?,?)", ("legacy-local", "Old", "onDevice", "/missing/private.gguf", "old", 32768, "2026-08-21T00:00:00Z", "2026-08-21T00:00:00Z"))
    service = InferenceRoutePlanService(db)
    with pytest.raises(Exception) as refused:
        service.freeze_legacy_one_leg_plan(
            ROUTE_PLANNING_AUTHORITY,
            command_id="legacy-illegal",
            capability_id="thought.interview",
            legacy_profile_id="legacy-local",
        )
    assert getattr(refused.value, "code", "") == "no_compatible_assignment"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_plans").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_route_plan_commands").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM deployment_revisions").fetchone()[0] == 0


def test_one_shot_hashes_private_material_and_attempt_ordinal_is_not_minted(db: Database) -> None:
    _ready_route(db)
    with db._connection() as conn:
        conn.execute("UPDATE model_profile_readiness_observations SET state='ready'")
    evidence_entries = [
        {
            "route_leg_ordinal": ordinal,
            "eligibility": "executable",
            "reason_code": None,
            "admitted_request_id": f"admitted-{ordinal}",
            "admitted_request_sha256": _digest({"prompt": f"private prompt {ordinal}"}),
            "context_plan_sha256": _digest({"tokens": ordinal * 10}),
            "serialized_request_sha256": _digest(f"private serialization {ordinal}"),
        }
        for ordinal in (1, 2)
    ]
    service = _evidence_service(db, entries=evidence_entries, reference="one-shot-source")
    result = service.freeze_one_shot(
        ROUTE_PLANNING_AUTHORITY,
        command_id="oneshot-1",
        route_request={"capability_id": "ask.answer"},
        operation_id="operation-1",
        planning_reference="one-shot-source",
    )
    encoded = json.dumps(result)
    assert "owner note body" not in encoded
    assert "private prompt" not in encoded
    assert "private serialization" not in encoded
    evidence = service.route_leg_evidence(
        ROUTE_PLANNING_AUTHORITY,
        operation_plan_id=result["operation_request_plan"]["id"],
        route_leg_ordinal=2,
    )
    assert evidence["route_leg_ordinal"] == 2
    assert "physical_attempt_ordinal" not in evidence
    replay = service.freeze_one_shot(
        ROUTE_PLANNING_AUTHORITY,
        command_id="oneshot-1",
        route_request={"capability_id": "ask.answer"},
        operation_id="operation-1",
        planning_reference="one-shot-source",
    )
    assert replay == result
    without_provider = InferenceRoutePlanService(Database(db.db_path))
    with pytest.raises(ServiceError) as unavailable:
        without_provider.get_operation_request_plan(
            ROUTE_PLANNING_AUTHORITY, result["operation_request_plan"]["id"]
        )
    assert unavailable.value.code == "inference_operation_evidence_provider_missing"
    restarted = _evidence_service(
        Database(db.db_path), entries=evidence_entries, reference="one-shot-source"
    )
    assert restarted.get_operation_request_plan(
        ROUTE_PLANNING_AUTHORITY, result["operation_request_plan"]["id"]
    ) == result["operation_request_plan"]


def test_executable_operation_refuses_without_registered_evidence_owner(db: Database) -> None:
    service = _ready_route(db, profiles=("quick",))
    with pytest.raises(ServiceError) as missing:
        service.freeze_one_shot(
            ROUTE_PLANNING_AUTHORITY,
            command_id="missing-provider",
            route_request={"capability_id": "ask.answer"},
            operation_id="missing-provider-operation",
            planning_reference="missing-source",
        )
    assert missing.value.code == "inference_operation_evidence_provider_missing"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_plans WHERE id='irp_missing_provider'").fetchone()[0] == 0


def test_malformed_or_capability_mismatched_provider_rolls_back_every_write(db: Database) -> None:
    _ready_route(db, profiles=("quick",))
    capability = process_inference_capability_registry().require("ask.answer")
    policy = f"{capability.operation_contract.name}@{capability.operation_contract.version}:{capability.schema_sha256}"
    with db._connection() as conn:
        conn.execute("CREATE TABLE test_provider_writes(id TEXT PRIMARY KEY)")

    def malformed(conn: object, _reference: str, _operation: str) -> dict[str, object]:
        conn.execute("INSERT INTO test_provider_writes VALUES ('must-rollback')")
        return {"wrong": True}

    provider = RouteAdmissionEvidenceProvider(
        id="malformed-provider", revision=1,
        capabilities=((capability.id, capability.revision, capability.schema_sha256),),
        operation_policy_revisions=(policy,), freeze=malformed,
        reconstruct=lambda _conn, _ref: {"wrong": True},
    )
    service = InferenceRoutePlanService(db, operation_evidence_providers=(provider,))
    with pytest.raises(ConflictError):
        service.freeze_one_shot(
            ROUTE_PLANNING_AUTHORITY, command_id="malformed-shot",
            route_request={"capability_id": "ask.answer"},
            operation_id="malformed-operation", planning_reference="malformed-ref",
        )
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM test_provider_writes").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_route_plans WHERE id='irp_malformed'").fetchone()[0] == 0

    mismatched = RouteAdmissionEvidenceProvider(
        id="wrong-capability", revision=1,
        capabilities=(("thought.interview", capability.revision, capability.schema_sha256),),
        operation_policy_revisions=(policy,), freeze=malformed,
        reconstruct=lambda _conn, _ref: {"wrong": True},
    )
    with pytest.raises(ServiceError) as missing:
        InferenceRoutePlanService(db, operation_evidence_providers=(mismatched,)).freeze_one_shot(
            ROUTE_PLANNING_AUTHORITY, command_id="mismatched-shot",
            route_request={"capability_id": "ask.answer"},
            operation_id="mismatch-operation", planning_reference="mismatch-ref",
        )
    assert missing.value.code == "inference_operation_evidence_provider_missing"


def test_operation_reconstruction_refuses_missing_or_tampered_provider_source(db: Database) -> None:
    _ready_route(db, profiles=("quick",))
    with db._connection() as conn:
        conn.execute("UPDATE model_profile_readiness_observations SET state='ready'")
    entries = [{
        "route_leg_ordinal": 1, "eligibility": "executable", "reason_code": None,
        "admitted_request_id": "admitted-1", "admitted_request_sha256": _digest("request"),
        "context_plan_sha256": _digest("context"), "serialized_request_sha256": _digest("wire"),
    }]
    service = _evidence_service(db, entries=entries, reference="durable-source")
    result = service.freeze_one_shot(
        ROUTE_PLANNING_AUTHORITY,
        command_id="durable-shot",
        route_request={"capability_id": "ask.answer"},
        operation_id="durable-operation",
        planning_reference="durable-source",
    )
    with db._connection() as conn:
        conn.execute("UPDATE test_route_admission_evidence SET payload_json=? WHERE ref='durable-source'", (json.dumps({"evidence_ref": "durable-source", "material_snapshot_sha256": _digest("changed"), "entries": entries}),))
    with pytest.raises(ConflictError) as invalid:
        service.get_operation_request_plan(
            ROUTE_PLANNING_AUTHORITY, result["operation_request_plan"]["id"]
        )
    assert invalid.value.code == "inference_operation_route_plan_integrity_invalid"


def test_recomputed_operation_and_normalized_leg_forgery_refuses(db: Database) -> None:
    _ready_route(db, profiles=("quick",))
    entries = [{
        "route_leg_ordinal": 1, "eligibility": "known_preflight_unavailable",
        "reason_code": "binding_not_ready",
    }]
    service = _evidence_service(db, entries=entries, reference="forgery-source")
    # Make the real binding observation unavailable so the original plan is lawful.
    with db._connection() as conn:
        conn.execute("UPDATE model_profile_readiness_observations SET state='unavailable'")
    result = service.freeze_one_shot(
        ROUTE_PLANNING_AUTHORITY,
        command_id="forgery-shot",
        route_request={"capability_id": "ask.answer"},
        operation_id="forgery-operation",
        planning_reference="forgery-source",
    )
    with db._connection() as conn:
        operation_plan_id = result["operation_request_plan"]["id"]
        row = conn.execute("SELECT payload_json FROM inference_operation_route_request_plans WHERE id=?", (operation_plan_id,)).fetchone()
        material = json.loads(str(row["payload_json"]))
        material["entries"][0] = {
            "route_leg_ordinal": 1, "eligibility": "executable", "reason_code": None,
            "admitted_request_id": "forged", "admitted_request_sha256": _digest("a"),
            "context_plan_sha256": _digest("b"), "serialized_request_sha256": _digest("c"),
        }
        encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        conn.execute("UPDATE inference_operation_route_request_plans SET payload_json=?,sha256=? WHERE id=?", (encoded, _digest(material), operation_plan_id))
        forged = material["entries"][0]
        conn.execute("""UPDATE inference_operation_route_request_plan_entries SET eligibility='executable',reason_code=NULL,admitted_request_id=?,admitted_request_sha256=?,context_plan_sha256=?,serialized_request_sha256=? WHERE operation_plan_id=?""", (forged["admitted_request_id"], forged["admitted_request_sha256"], forged["context_plan_sha256"], forged["serialized_request_sha256"], operation_plan_id))
    with pytest.raises(ConflictError):
        service.route_leg_evidence(ROUTE_PLANNING_AUTHORITY, operation_plan_id=operation_plan_id, route_leg_ordinal=1)


def test_fourth_leg_is_an_exact_profile_deletion_dependency(db: Database) -> None:
    service = _ready_route(db, profiles=("one", "two", "three", "four"))
    route = service.freeze_route_plan(
        ROUTE_PLANNING_AUTHORITY,
        command_id="four-leg-freeze",
        capability_id="ask.answer",
    )
    with pytest.raises(ConflictError) as referenced:
        ModelProfileService(db).delete_profile(OWNER, "four", expected_revision=1)
    assert {tuple(item.values()) for item in referenced.value.context["dependencies"]} >= {
        ("route_plan", route["id"])
    }


def test_authority_and_hub_local_sync_are_fail_closed(db: Database) -> None:
    service = _ready_route(db, profiles=("quick",))
    agent = Principal(PrincipalKind.AGENT, "untrusted")
    with pytest.raises(ServiceError):
        service.resolve_route_plan(agent, capability_id="ask.answer")
    service.freeze_route_plan(
        ROUTE_PLANNING_AUTHORITY,
        command_id="freeze-sync",
        capability_id="ask.answer",
    )
    pulled = SyncService(db).pull(OWNER)
    assert "inference_route_plans" not in pulled
    with pytest.raises(Exception):
        SyncService(db).push(
            OWNER,
            {"inference_route_plans": [{"id": "forged"}]},
        )


def test_rails_service_policy_is_sealed_and_capability_only() -> None:
    """Rails SERVICE has no group/global inheritance escape hatch."""
    from holdspeak.services.inference_service_route_policy import (
        builtin_service_route_policy_registry,
    )

    registry = builtin_service_route_policy_registry()
    principal = Principal(
        PrincipalKind.SERVICE,
        "rails-observer",
        frozenset(
            {
                ("rails.observer-batch", 1),
                ("inference.invoke", 1),
                ("inference.cancel", 1),
            }
        ),
        "rails-observer:journal-only",
    )
    evidence = registry.authorize(
        principal,
        parent_kind="rails.observer-batch",
        capability_id="background.rails_summary",
    )
    assert evidence["assignment_sources"] == ["capability"]
    assert evidence["allowed_boundaries"]
    with pytest.raises(ValidationError) as denied_global_shape:
        registry.authorize(
            Principal(
                PrincipalKind.SERVICE,
                "rails-observer",
                frozenset({("inference.invoke", 1)}),
                "rails-observer:journal-only",
            ),
            parent_kind="rails.observer-batch",
            capability_id="background.rails_summary",
        )
    assert denied_global_shape.value.code == "inference_service_route_policy_denied"
    with pytest.raises(ValidationError):
        registry.authorize(
            principal,
            parent_kind="rails.observer-batch",
            capability_id="ask.answer",
        )
