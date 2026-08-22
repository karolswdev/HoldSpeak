"""Story 143-08 tranche A-C closed adapters, principals, and parent bundles."""

from __future__ import annotations

import json
import threading
import time
import uuid
from datetime import datetime, timezone
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.db import Database
from holdspeak.inference_capabilities import (
    InferenceCapabilityRegistry,
    InferenceCapabilityRegistryError,
    process_inference_capability_registry,
)
from holdspeak.intel.models import ActionItem, IntelResult
from holdspeak.kernel.inference_runner import (
    InferenceRunner,
    InvocationRequest,
    ServiceContract,
)
from holdspeak.kernel.provider_signals import InferenceInvalidTypedOutput
from holdspeak.kernel.runtime import _configure
from holdspeak.meeting_session.deferred_admission import queue_service_principal
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, ValidationError
from holdspeak.services.inference_adoption_service import RoutedInferenceCoordinator
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.inference_fallback_controller import (
    INFERENCE_FALLBACK_AUTHORITY,
    InferenceFallbackController,
    RoutedAttemptRuntime,
)
from holdspeak.services.sync_service import SyncService
from holdspeak.services.inference_parent_route_bundle_service import (
    HandoffEvidenceProvider,
    InferenceParentRouteBundleService,
)
from holdspeak.services.inference_route_plan_service import (
    InferenceRoutePlanService,
    ROUTE_PLANNING_AUTHORITY,
    RouteAdmissionEvidenceProvider,
)
from holdspeak.services.inference_semantic_adapters import (
    ClosedSemanticAdapter,
    SemanticAdapterContract,
    adapter_for,
    adapter_for_frozen_definition,
    normalize_bookmark_label,
)
from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim
from tests.unit.test_phase143_inference_fallback_controller import _broker_child


def _assign(
    db: Database,
    capability_id: str,
    profile_id: str,
    *,
    command: str,
    scope: dict[str, object] | None = None,
) -> None:
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": command,
            "expected_revision": 0,
            "scope": scope or {"kind": "capability", "capability_id": capability_id},
            "entries": [{"profile_id": profile_id, "profile_revision": 1}],
        },
    )


def _meeting_profile(db: Database, profile_id: str, *capabilities: str) -> None:
    _profile(
        db,
        profile_id,
        claims=(
            "language",
            "structured_output",
            *(_result_claim(capability) for capability in capabilities),
        ),
    )


def _call(raw: object):
    return lambda _engine, _payload, _cancellation: raw


def test_corrected_results_are_semantic_only_and_unchanged_contracts_keep_revision() -> None:
    registry = process_inference_capability_registry()
    for capability_id, fields, revision in (
        ("meeting.bookmark_label", {"label"}, 2),
        ("meeting.auto_title", {"title"}, 2),
        ("background.rails_summary", {"summary"}, 2),
        ("background.cadence_draft", {"draft"}, 2),
        ("decision.promotion_draft", {"draft"}, 2),
        ("delivery.pr_review_draft", {"draft"}, 2),
    ):
        definition = registry.require(capability_id)
        assert definition.revision == revision
        assert set(definition.output_schema["properties"]) == fields
        assert "provider" not in definition.output_schema["properties"]
        assert "model" not in definition.output_schema["properties"]
    assert registry.require("meeting.live_analysis").revision == 1
    assert registry.require("meeting.deferred_analysis").revision == 1
    assert registry.require("speech.transcribe").revision == 1
    assert registry.require("speech.preload").revision == 1
    assert all(
        registry.require(capability_id).revision == 1
        for capability_id in registry.capability_ids
        if capability_id.startswith("meeting.plugin.")
    )


def test_semantic_adapters_validate_before_returning_attempt_output() -> None:
    analysis = IntelResult(
        topics=["Routing"],
        action_items=[ActionItem("Ship", owner="Ada", due=None)],
        summary="One route",
        raw_response="private provider bytes",
    )
    result = adapter_for("meeting.live_analysis", _call(analysis)).dispatch(
        object(), {}, object()
    )
    assert result == {
        "summary": "One route",
        "topics": ["Routing"],
        "action_items": [{"task": "Ship", "owner": "Ada", "due": None}],
    }
    assert adapter_for("meeting.bookmark_label", _call("Decision")).dispatch(
        object(), {}, object()
    ) == {"label": "Decision"}
    assert adapter_for("speech.transcribe", _call("hello")).dispatch(
        object(), {}, object()
    ) == {"text": "hello", "language": None}

    hostile = (
        ("meeting.live_analysis", {**result, "provider": "forged"}),
        ("meeting.bookmark_label", {"label": "x", "boundary": "cloud"}),
        ("speech.transcribe", {"text": "x", "language": None, "model": "fake"}),
        ("speech.preload", {"state": "loaded", "extra": True}),
        (
            "meeting.plugin.project_detector",
            {
                "plugin_id": "project_detector",
                "kind": "detector",
                "summary": "none",
                "matched_projects": [],
                "token_count": 0,
                "active_intents": [],
                "confidence_hint": 0.0,
                "placement": "cloud",
            },
        ),
    )
    for capability_id, raw in hostile:
        with pytest.raises(InferenceInvalidTypedOutput):
            adapter_for(capability_id, _call(raw)).dispatch(object(), {}, object())

    current = SemanticAdapterContract.current("meeting.bookmark_label")
    wrong = ClosedSemanticAdapter(
        replace(current, capability_revision=current.capability_revision + 1),
        _call("x"),
        normalize_bookmark_label,
    )
    with pytest.raises(InferenceInvalidTypedOutput):
        wrong.dispatch(object(), {}, object())


def test_historical_text_adapter_keeps_v1_shape_without_reinterpreting_as_v2() -> None:
    current = process_inference_capability_registry().require("meeting.bookmark_label")
    legacy_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "output": {"type": "string"},
            "provider": {"type": "string"},
            "model": {"type": "string"},
        },
        "required": ["output", "provider", "model"],
    }
    legacy = replace(
        current,
        revision=1,
        output_schema=legacy_schema,
        output_schema_sha256="",
        schema_sha256="",
    )
    engine = SimpleNamespace(active_provider="frozen-provider", active_model="frozen-model")
    adapter = adapter_for_frozen_definition(legacy.canonical_dict(), _call("Decision"))
    assert adapter.dispatch(engine, {}, object()) == {
        "output": "Decision",
        "provider": "frozen-provider",
        "model": "frozen-model",
    }
    assert adapter_for("meeting.bookmark_label", _call("Decision")).dispatch(
        engine, {}, object()
    ) == {"label": "Decision"}


def test_preupgrade_frozen_route_binds_after_registry_upgrade(tmp_path: Path) -> None:
    db = Database(tmp_path / "historical-route.db")
    current_registry = process_inference_capability_registry()
    current = current_registry.require("meeting.bookmark_label")
    legacy_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "output": {"type": "string"},
            "provider": {"type": "string"},
            "model": {"type": "string"},
        },
        "required": ["output", "provider", "model"],
    }
    legacy = replace(
        current,
        revision=1,
        output_schema=legacy_schema,
        output_schema_sha256="",
        schema_sha256="",
    )
    legacy_registry = InferenceCapabilityRegistry.compose(
        capabilities=(
            legacy if capability.id == legacy.id else capability
            for capability in current_registry._capabilities.values()
        ),
        retry_policies=current_registry._retry_policies.values(),
    )
    _profile(
        db,
        "historical-bookmark",
        claims=("language", f"result_schema:{legacy.output_schema_sha256}"),
    )
    InferenceAssignmentService(db, registry=legacy_registry).set_assignment(
        OWNER,
        {
            "command_id": "legacy-bookmark-assignment",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": legacy.id},
            "entries": [{"profile_id": "historical-bookmark", "profile_revision": 1}],
        },
    )
    old_plans = InferenceRoutePlanService(db, registry=legacy_registry)
    route = old_plans.freeze_route_plan(
        ROUTE_PLANNING_AUTHORITY,
        command_id="legacy-bookmark-route",
        capability_id=legacy.id,
    )
    assert route["capability"]["revision"] == 1

    evidence_by_ref: dict[str, dict[str, object]] = {}
    budgets_by_ref: dict[str, dict[str, object]] = {}

    def freeze_resolved(conn, reference, operation_id, resolved, preflight):
        ref = f"legacy-evidence:{reference}"
        entry = {
            "route_leg_ordinal": 1,
            "eligibility": "executable",
            "reason_code": None,
            "admitted_request_id": "legacy-request",
            "admitted_request_sha256": "sha256:" + "1" * 64,
            "context_plan_sha256": "sha256:" + "2" * 64,
            "serialized_request_sha256": "sha256:" + "3" * 64,
        }
        value = {
            "evidence_ref": ref,
            "material_snapshot_sha256": "sha256:" + "4" * 64,
            "entries": [entry],
        }
        evidence_by_ref[ref] = value
        budgets_by_ref[ref] = {
            "schema": "RouteAttemptBudgetEvidence@1",
            "evidence_ref": ref,
            "material_snapshot_sha256": value["material_snapshot_sha256"],
            "entries": [
                {
                    "route_leg_ordinal": 1,
                    "admitted_request_id": entry["admitted_request_id"],
                    "admitted_request_sha256": entry["admitted_request_sha256"],
                    "context_plan_sha256": entry["context_plan_sha256"],
                    "serialized_request_sha256": entry["serialized_request_sha256"],
                    "input_tokens": 4,
                    "reserved_output_tokens": 8,
                    "total_tokens": 12,
                    "reserved_cost_units": 0,
                    "reserved_tool_calls": 0,
                }
            ],
        }
        conn.execute(
            "CREATE TABLE IF NOT EXISTS test_historical_evidence(ref TEXT PRIMARY KEY)"
        )
        conn.execute("INSERT INTO test_historical_evidence VALUES (?)", (ref,))
        return value

    policy = (
        f"{legacy.operation_contract.name}@{legacy.operation_contract.version}:"
        f"{legacy.schema_sha256}"
    )
    provider = RouteAdmissionEvidenceProvider(
        id="historical-bookmark-evidence",
        revision=1,
        capabilities=((legacy.id, legacy.revision, legacy.schema_sha256),),
        operation_policy_revisions=(policy,),
        freeze=lambda _conn, reference, _operation: evidence_by_ref[reference],
        reconstruct=lambda _conn, ref: evidence_by_ref[ref],
        reconstruct_attempt_budgets=lambda _conn, ref: budgets_by_ref[ref],
        freeze_resolved=freeze_resolved,
    )
    upgraded = InferenceRoutePlanService(
        db,
        registry=current_registry,
        operation_evidence_providers=(provider,),
    )
    frozen = upgraded.freeze_operation_for_route(
        ROUTE_PLANNING_AUTHORITY,
        command_id="bind-legacy-bookmark",
        route_plan_id=route["id"],
        operation_id="legacy-bookmark-operation",
        planning_reference="legacy-bookmark-material",
    )
    assert frozen["operation_request_plan"]["route_plan_id"] == route["id"]
    assert upgraded.get_operation_request_plan(
        ROUTE_PLANNING_AUTHORITY, frozen["operation_request_plan"]["id"]
    )["sha256"] == frozen["operation_request_plan"]["sha256"]

    broker = _configure(db)
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: SimpleNamespace(
        active_provider="frozen-provider", active_model="frozen-model"
    )
    coordinator = RoutedInferenceCoordinator(db, broker=broker, registry=current_registry)
    coordinator.plans = upgraded
    coordinator.controller = InferenceFallbackController(
        db,
        route_plan_service=upgraded,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    coordinator.evidence.serialized_request = lambda _ref, _ordinal: {
        "contract": legacy.operation_contract.name,
        "contract_revision": str(legacy.operation_contract.version),
        "payload": {},
    }
    broker.inference_runner._routed_attempt_runtime = RoutedAttemptRuntime(
        coordinator.controller
    )
    execution = coordinator.controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id="execute-legacy-bookmark",
        operation_plan_id=frozen["operation_request_plan"]["id"],
    )
    result = coordinator.execute(
        OWNER,
        execution_id=execution["id"],
        adapter=adapter_for_frozen_definition(legacy.canonical_dict(), _call("Decision")),
    )
    assert result["outcome"] == "succeeded"
    assert result["result"] == {
        "output": "Decision",
        "provider": "frozen-provider",
        "model": "frozen-model",
    }
    with pytest.raises(InferenceCapabilityRegistryError):
        coordinator._validate_frozen_result(
            legacy.canonical_dict(), {"label": "current-only"}
        )


def test_current_route_projection_uses_its_identical_frozen_definition(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "current-frozen-definition.db")
    registry = process_inference_capability_registry()
    capability = registry.require("meeting.bookmark_label")
    _profile(
        db,
        "current-bookmark",
        claims=("language", f"result_schema:{capability.output_schema_sha256}"),
    )
    InferenceAssignmentService(db, registry=registry).set_assignment(
        OWNER,
        {
            "command_id": "current-bookmark-assignment",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": capability.id},
            "entries": [{"profile_id": "current-bookmark", "profile_revision": 1}],
        },
    )
    plans = InferenceRoutePlanService(db, registry=registry)
    route = plans.freeze_route_plan(
        ROUTE_PLANNING_AUTHORITY,
        command_id="current-bookmark-route",
        capability_id=capability.id,
    )
    coordinator = RoutedInferenceCoordinator(db, registry=registry)
    definition = coordinator._frozen_capability_definition(route["id"])
    assert definition == capability.canonical_dict()
    coordinator._validate_frozen_result(definition, {"label": "Decision"})
    with pytest.raises(InferenceCapabilityRegistryError):
        coordinator._validate_frozen_result(
            definition,
            {"output": "Decision", "provider": "old", "model": "old"},
        )


def test_service_route_policy_never_inherits_owner_global_or_group(tmp_path: Path) -> None:
    db = Database(tmp_path / "service-route-policy.db")
    capability = "meeting.deferred_analysis"
    _meeting_profile(db, "meeting-model", capability)
    _assign(
        db,
        capability,
        "meeting-model",
        command="owner-global",
        scope={"kind": "global"},
    )
    plans = InferenceRoutePlanService(db)
    queue = queue_service_principal()
    with db._connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        with pytest.raises(ValidationError) as denied:
            plans.freeze_route_plan_for_feature_in_transaction(
                ROUTE_PLANNING_AUTHORITY,
                conn,
                command_id="service-global-denied",
                feature_principal=queue,
                parent_kind="meeting.deferred-intel-job",
                capability_id=capability,
                invocation_id="job-one",
            )
        assert denied.value.code == "no_assignment"
        conn.rollback()

    _assign(db, capability, "meeting-model", command="service-exact-capability")
    with db._connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        route = plans.freeze_route_plan_for_feature_in_transaction(
            ROUTE_PLANNING_AUTHORITY,
            conn,
            command_id="service-capability-allowed",
            feature_principal=queue,
            parent_kind="meeting.deferred-intel-job",
            capability_id=capability,
            invocation_id="job-one",
        )
        conn.commit()
    assert route["source"]["inherited_from"] == "capability"
    with db._connection() as conn:
        evidence = json.loads(
            str(
                conn.execute(
                    "SELECT payload_json FROM inference_route_plan_principal_evidence WHERE plan_id=?",
                    (route["id"],),
                ).fetchone()[0]
            )
        )
    assert evidence["principal_kind"] == "service"
    assert evidence["principal_identity"] == "meeting-intel-queue"
    assert evidence["assignment_sources"] == ["capability"]

    forged = (
        Principal(PrincipalKind.SERVICE, queue.identity, queue.allowed_operations, "wrong"),
        Principal(PrincipalKind.SERVICE, queue.identity, frozenset(), queue.authority_basis),
        Principal(PrincipalKind.SERVICE, "rails-observer", queue.allowed_operations, queue.authority_basis),
    )
    for ordinal, principal in enumerate(forged, 1):
        with db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            with pytest.raises(ValidationError) as refused:
                plans.freeze_route_plan_for_feature_in_transaction(
                    ROUTE_PLANNING_AUTHORITY,
                    conn,
                    command_id=f"forged-service-{ordinal}",
                    feature_principal=principal,
                    parent_kind="meeting.deferred-intel-job",
                    capability_id=capability,
                    invocation_id="job-one",
                )
            assert refused.value.code == "inference_service_route_policy_denied"
            conn.rollback()


def _ask_bundle(tmp_path: Path, *, name: str = "bundle"):
    db = Database(tmp_path / f"{name}.db")
    _profile(db, "quick")
    _assign(db, "ask.answer", "quick", command=f"{name}-assignment")
    broker = _configure(db)
    adoption = broker.inference_adoption_service
    with db._connection() as conn:
        conn.executescript(
            """
            CREATE TABLE test_displaced_jobs (
                evidence_ref TEXT PRIMARY KEY,
                planning_reference TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                evidence_sha256 TEXT NOT NULL
            );
            CREATE TABLE test_displaced_job_activations (
                evidence_ref TEXT PRIMARY KEY REFERENCES test_displaced_jobs(evidence_ref)
            );
            CREATE TABLE test_displaced_job_runs (
                evidence_ref TEXT PRIMARY KEY REFERENCES test_displaced_jobs(evidence_ref),
                simulated_egress TEXT NOT NULL
            );
            CREATE TABLE test_old_provider_egress (
                child_operation_id TEXT PRIMARY KEY
            );
            CREATE TRIGGER test_displaced_jobs_no_update
            BEFORE UPDATE ON test_displaced_jobs BEGIN
                SELECT RAISE(ABORT, 'immutable test displaced job');
            END;
            CREATE TRIGGER test_displaced_jobs_no_delete
            BEFORE DELETE ON test_displaced_jobs BEGIN
                SELECT RAISE(ABORT, 'immutable test displaced job');
            END;
            CREATE TRIGGER test_displaced_job_activations_no_update
            BEFORE UPDATE ON test_displaced_job_activations BEGIN
                SELECT RAISE(ABORT, 'immutable test displaced activation');
            END;
            CREATE TRIGGER test_displaced_job_activations_no_delete
            BEFORE DELETE ON test_displaced_job_activations BEGIN
                SELECT RAISE(ABORT, 'immutable test displaced activation');
            END;
            CREATE TRIGGER test_displaced_job_runs_no_update
            BEFORE UPDATE ON test_displaced_job_runs BEGIN
                SELECT RAISE(ABORT, 'immutable test displaced run');
            END;
            CREATE TRIGGER test_displaced_job_runs_no_delete
            BEFORE DELETE ON test_displaced_job_runs BEGIN
                SELECT RAISE(ABORT, 'immutable test displaced run');
            END;
            """
        )

    def evidence(conn, evidence_ref):
        row = conn.execute(
            "SELECT * FROM test_displaced_jobs WHERE evidence_ref=?", (evidence_ref,)
        ).fetchone()
        if row is None:
            raise RuntimeError("displaced job is missing")
        active = conn.execute(
            "SELECT 1 FROM test_displaced_job_activations WHERE evidence_ref=?",
            (evidence_ref,),
        ).fetchone() is not None
        return {
            "schema": "InferenceParentHandoffEvidence@1",
            "planning_reference": str(row["planning_reference"]),
            "evidence_ref": str(row["evidence_ref"]),
            "evidence_sha256": str(row["evidence_sha256"]),
            "state": "active" if active else "reserved",
        }

    def freeze(conn, planning_reference, context):
        ref = f"handoff:{planning_reference}"
        payload = json.dumps(context, sort_keys=True, separators=(",", ":"))
        digest = "sha256:" + __import__("hashlib").sha256(payload.encode()).hexdigest()
        conn.execute(
            "INSERT INTO test_displaced_jobs VALUES (?,?,?,?)",
            (ref, planning_reference, payload, digest),
        )
        return evidence(conn, ref)

    def reconstruct(conn, evidence_ref):
        return evidence(conn, evidence_ref)

    def activate(conn, evidence_ref):
        conn.execute(
            "INSERT INTO test_displaced_job_activations VALUES (?)", (evidence_ref,)
        )

    def run_displaced(conn, evidence_ref):
        inserted = conn.execute(
            """INSERT INTO test_displaced_job_runs(evidence_ref,simulated_egress)
                 SELECT evidence_ref,'simulated'
                   FROM test_displaced_job_activations
                  WHERE evidence_ref=?
                    AND NOT EXISTS (
                        SELECT 1 FROM test_displaced_job_runs WHERE evidence_ref=?
                    )""",
            (evidence_ref, evidence_ref),
        )
        return inserted.rowcount == 1

    bundles = InferenceParentRouteBundleService(
        broker,
        adoption,
        handoff_evidence_providers=(
            HandoffEvidenceProvider(
                "test-meeting-handoff", 1, freeze, reconstruct, activate
            ),
        ),
    )
    started = bundles.start(
        OWNER,
        command_id=f"{name}-parent",
        parent_kind="meeting.session",
        definition_ref="meeting:test",
        definition_revision="1",
        input_snapshot={"meeting_id": "meeting-test"},
        deadline_at=time.time() + 300,
        routes=(
            {"key": "ask", "capability_id": "ask.answer", "invocation_id": "meeting-test"},
        ),
        lifecycle_child_budget=2,
    )
    def fresh_bundles():
        return InferenceParentRouteBundleService(
            broker,
            adoption,
            handoff_evidence_providers=(
                HandoffEvidenceProvider(
                    "test-meeting-handoff", 1, freeze, reconstruct, activate
                ),
            ),
        )

    return db, broker, adoption, bundles, started, run_displaced, fresh_bundles



def _pending_handoff(
    broker: object,
    adoption: object,
    bundles: InferenceParentRouteBundleService,
    started: dict[str, object],
    *,
    prefix: str,
) -> tuple[dict[str, object], dict[str, object]]:
    route = started["bundle"]["members"][0]
    admitted = adoption.admit_on_frozen_route(
        OWNER,
        command_id=f"{prefix}-child",
        route_plan_id=route["route_plan_id"],
        capability_id="ask.answer",
        operation_id=f"{prefix}-child-operation",
        payload={
            "system_prompt": "Answer.", "user_prompt": "Why?",
            "temperature": 0.0, "max_tokens": 16,
        },
        reserved_output_tokens=16,
    )
    controller = adoption.controller
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"{prefix}-reserve",
        execution_id=admitted["execution"]["id"],
    )["reservation"]
    controller.claim_reservation(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"claim-{reservation['attempt_id']}",
        reservation=reservation,
    )
    child_id = _broker_child(broker, reservation, suffix=f"{prefix}-handoff")
    controller.bind_admitted_child(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"bind-{reservation['attempt_id']}",
        attempt_id=reservation["attempt_id"],
        child_operation_id=child_id,
    )
    controller.mark_dispatch_intent(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"dispatch-{reservation['attempt_id']}",
        attempt_id=reservation["attempt_id"],
    )
    effect = bundles.request_stop_handoff(
        OWNER,
        command_id=f"{prefix}-handoff",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id="test-meeting-handoff",
        planning_reference=f"{prefix}-work",
    )
    assert effect["state"] == "pending_physical_settlement"
    return effect, reservation


def test_parent_route_bundle_is_atomic_replay_safe_and_budget_exact(tmp_path: Path) -> None:
    db, _broker, _adoption, bundles, started, _run_displaced, _fresh_bundles = _ask_bundle(tmp_path)
    bundle = started["bundle"]
    assert bundle["parent_child_budget"] == 6
    assert bundle["lifecycle_child_budget"] == 2
    assert bundle["members"][0]["maximum_physical_attempts"] == 4
    assert bundles.get(bundle["id"]) == bundle
    replay = bundles.start(
        OWNER,
        command_id="bundle-parent",
        parent_kind="meeting.session",
        definition_ref="meeting:test",
        definition_revision="1",
        input_snapshot={"meeting_id": "meeting-test"},
        deadline_at=bundle["parent_deadline_at"],
        routes=(
            {"key": "ask", "capability_id": "ask.answer", "invocation_id": "meeting-test"},
        ),
        lifecycle_child_budget=2,
    )
    assert replay["bundle"] == bundle
    with db._connection() as conn:
        parent = conn.execute(
            "SELECT child_budget,deadline_at FROM kernel_parent_runs WHERE operation_id=?",
            (bundle["parent_operation_id"],),
        ).fetchone()
        operation = conn.execute(
            "SELECT envelope_sha256,native_id FROM kernel_operations WHERE operation_id=?",
            (bundle["parent_operation_id"],),
        ).fetchone()
    assert int(parent["child_budget"]) == 6
    expected_arguments = {
        "native_id": str(operation["native_id"]),
        "definition_ref": "meeting:test",
        "definition_revision": "1",
        "input": {"meeting_id": "meeting-test"},
        "deadline_at": bundle["parent_deadline_at"],
        "child_budget": 6,
    }
    assert operation["envelope_sha256"] == "sha256:" + uuid.uuid5(
        uuid.NAMESPACE_URL,
        json.dumps(expected_arguments, sort_keys=True, separators=(",", ":")),
    ).hex


def test_bundle_rollback_terminalizes_shell_and_leaves_no_partial_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = Database(tmp_path / "bundle-rollback.db")
    _profile(db, "quick")
    _assign(db, "ask.answer", "quick", command="rollback-assignment")
    broker = _configure(db)
    bundles = InferenceParentRouteBundleService(
        broker, broker.inference_adoption_service
    )
    monkeypatch.setattr(
        bundles._plans,
        "freeze_route_plan_for_feature_in_transaction",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("fault")),
    )
    with pytest.raises(RuntimeError):
        bundles.start(
            OWNER,
            command_id="rollback-parent",
            parent_kind="meeting.session",
            definition_ref="meeting:rollback",
            definition_revision="1",
            input_snapshot={"meeting_id": "rollback"},
            deadline_at=time.time() + 300,
            routes=(
                {"key": "ask", "capability_id": "ask.answer", "invocation_id": "rollback"},
            ),
        )
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_parent_route_bundles").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_route_plans").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM kernel_parent_runs").fetchone()[0] == 0
        operation = conn.execute(
            "SELECT state FROM kernel_operations WHERE idempotency_key='rollback-parent'"
        ).fetchone()
    assert operation["state"] == "refused"


def test_bundle_reconstruction_rejects_principal_evidence_tamper(tmp_path: Path) -> None:
    db, _broker, _adoption, bundles, started, _run_displaced, _fresh_bundles = _ask_bundle(tmp_path, name="tamper")
    bundle = started["bundle"]
    with db._connection() as conn:
        conn.execute("DROP TRIGGER inference_parent_route_bundle_members_no_update")
        conn.execute(
            "UPDATE inference_parent_route_bundle_members SET principal_policy_sha256=? WHERE bundle_id=?",
            ("sha256:" + "f" * 64, bundle["id"]),
        )
    with pytest.raises(ConflictError) as refused:
        bundles.get(bundle["id"])
    assert refused.value.code == "inference_parent_route_bundle_integrity_invalid"


def test_stop_handoff_derives_complete_route_set_and_replays_durable_effect(tmp_path: Path) -> None:
    db, _broker, adoption, bundles, started, run_displaced, fresh_bundles = _ask_bundle(tmp_path, name="stop")
    route = started["bundle"]["members"][0]
    admitted = adoption.admit_on_frozen_route(
        OWNER,
        command_id="stop-child",
        route_plan_id=route["route_plan_id"],
        capability_id="ask.answer",
        operation_id="stop-child-operation",
        payload={
            "system_prompt": "Answer.",
            "user_prompt": "Why?",
            "temperature": 0.0,
            "max_tokens": 16,
        },
        reserved_output_tokens=16,
    )
    execution_id = admitted["execution"]["id"]
    second = adoption.admit_on_frozen_route(
        OWNER,
        command_id="stop-child-two",
        route_plan_id=route["route_plan_id"],
        capability_id="ask.answer",
        operation_id="stop-child-operation-two",
        payload={
            "system_prompt": "Answer.",
            "user_prompt": "And then?",
            "temperature": 0.0,
            "max_tokens": 16,
        },
        reserved_output_tokens=16,
    )
    second_execution_id = second["execution"]["id"]
    effect = bundles.request_stop_handoff(
        OWNER,
        command_id="stop-handoff",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id="test-meeting-handoff",
        planning_reference="stop-displaced-work",
    )
    assert effect["state"] == "committed"
    assert {item["execution_id"] for item in effect["route_stops"]} == {
        execution_id,
        second_execution_id,
    }
    assert effect == bundles.request_stop_handoff(
        OWNER,
        command_id="stop-handoff",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id="test-meeting-handoff",
        planning_reference="stop-displaced-work",
    )
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM test_displaced_jobs").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM inference_parent_stop_handoff_settlements").fetchone()[0] == 1
        assert conn.execute("SELECT state FROM kernel_parent_runs").fetchone()[0] == "CANCELLING"
    with pytest.raises(ValidationError):
        bundles.request_stop_handoff(
            Principal(PrincipalKind.OWNER, "other-owner"),
            command_id="forged-stop",
            bundle_id=started["bundle"]["id"],
            evidence_provider_id="test-meeting-handoff",
            planning_reference="forged",
        )


def test_stop_handoff_unknown_dispatch_keeps_displaced_work_reserved_after_delayed_egress(
    tmp_path: Path,
) -> None:
    # Counsel v2: indeterminate dispatch never activates a replacement.
    db, broker, adoption, bundles, started, run_displaced, fresh_bundles = _ask_bundle(
        tmp_path, name="pending"
    )
    route = started["bundle"]["members"][0]
    admitted = adoption.admit_on_frozen_route(
        OWNER,
        command_id="pending-child",
        route_plan_id=route["route_plan_id"],
        capability_id="ask.answer",
        operation_id="pending-child-operation",
        payload={
            "system_prompt": "Answer.", "user_prompt": "Why?",
            "temperature": 0.0, "max_tokens": 16,
        },
        reserved_output_tokens=16,
    )
    controller = adoption.controller
    execution_id = admitted["execution"]["id"]
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id="pending-reserve",
        execution_id=execution_id,
    )["reservation"]
    controller.claim_reservation(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"claim-{reservation['attempt_id']}",
        reservation=reservation,
    )
    child_id = _broker_child(broker, reservation, suffix="pending-handoff")
    controller.bind_admitted_child(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"bind-{reservation['attempt_id']}",
        attempt_id=reservation["attempt_id"],
        child_operation_id=child_id,
    )
    controller.mark_dispatch_intent(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"dispatch-{reservation['attempt_id']}",
        attempt_id=reservation["attempt_id"],
    )
    pending = bundles.request_stop_handoff(
        OWNER,
        command_id="pending-handoff",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id="test-meeting-handoff",
        planning_reference="pending-work",
    )
    assert pending["state"] == "pending_physical_settlement"
    with db._connection() as conn:
        assert run_displaced(conn, pending["evidence_ref"]) is False
    controller.reconcile_dispatch_intent(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id="pending-reconcile-unknown",
        attempt_id=reservation["attempt_id"],
    )
    with db._connection() as conn:
        conn.execute("INSERT INTO test_old_provider_egress VALUES (?)", (child_id,))
    restarted = fresh_bundles()
    assert restarted.reconcile_stop_handoff(command_id="pending-handoff")["state"] == "pending_physical_settlement"
    with db._connection() as conn:
        assert run_displaced(conn, pending["evidence_ref"]) is False
        assert conn.execute("SELECT COUNT(*) FROM test_displaced_job_runs").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM test_old_provider_egress").fetchone()[0] == 1
        assert conn.execute("SELECT state FROM inference_route_executions WHERE id=?", (execution_id,)).fetchone()[0] == "terminal"


def test_stop_handoff_known_terminal_settles_activates_and_runs_once(tmp_path: Path) -> None:
    db, _broker, adoption, bundles, started, run_displaced, _fresh_bundles = _ask_bundle(
        tmp_path, name="known"
    )
    route = started["bundle"]["members"][0]
    admitted = adoption.admit_on_frozen_route(
        OWNER,
        command_id="known-child",
        route_plan_id=route["route_plan_id"],
        capability_id="ask.answer",
        operation_id="known-child-operation",
        payload={
            "system_prompt": "Answer.", "user_prompt": "Why?",
            "temperature": 0.0, "max_tokens": 16,
        },
        reserved_output_tokens=16,
    )
    effect = bundles.request_stop_handoff(
        OWNER,
        command_id="known-handoff",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id="test-meeting-handoff",
        planning_reference="known-work",
    )
    assert effect["state"] == "committed"
    with db._connection() as conn:
        assert conn.execute("SELECT state FROM inference_route_executions WHERE id=?", (admitted["execution"]["id"],)).fetchone()[0] == "stopped"
        assert run_displaced(conn, effect["evidence_ref"]) is True
        assert run_displaced(conn, effect["evidence_ref"]) is False
        assert conn.execute("SELECT COUNT(*) FROM test_displaced_job_runs").fetchone()[0] == 1
    assert bundles.reconcile_stop_handoff(command_id="known-handoff") == effect



def test_handoff_freeze_active_unwritten_or_exception_rolls_back(
    tmp_path: Path,
) -> None:
    for name, mode in (
        ("active", "active"),
        ("unwritten", "unwritten"),
        ("raises", "raises"),
    ):
        db, broker, adoption, bundles, started, _run, _fresh = _ask_bundle(
            tmp_path, name=f"freeze-{name}"
        )
        base = bundles._handoff_evidence_providers["test-meeting-handoff"]

        def freeze(conn, reference, context, *, mode=mode):
            if mode == "unwritten":
                return {
                    "schema": "InferenceParentHandoffEvidence@1",
                    "planning_reference": reference,
                    "evidence_ref": "unwritten",
                    "evidence_sha256": "sha256:" + "0" * 64,
                    "state": "reserved",
                }
            frozen = base.freeze(conn, reference, context)
            if mode == "raises":
                raise RuntimeError("freeze fault")
            return {**frozen, "state": "active"}

        hostile = InferenceParentRouteBundleService(
            broker, adoption,
            handoff_evidence_providers=(replace(base, freeze=freeze),),
        )
        with pytest.raises((ConflictError, RuntimeError)) as refused:
            hostile.request_stop_handoff(
                OWNER,
                command_id=f"freeze-{name}-handoff",
                bundle_id=started["bundle"]["id"],
                evidence_provider_id="test-meeting-handoff",
                planning_reference=f"freeze-{name}-work",
            )
        if isinstance(refused.value, ConflictError):
            assert refused.value.code == "inference_parent_stop_handoff_integrity_invalid"
        with db._connection() as conn:
            assert conn.execute("SELECT COUNT(*) FROM inference_parent_stop_handoffs").fetchone()[0] == 0
            assert conn.execute("SELECT COUNT(*) FROM test_displaced_jobs").fetchone()[0] == 0


def test_handoff_settlement_activation_faults_roll_back_together(tmp_path: Path) -> None:
    for name, mode in (
        ("pre-insert", "pre-insert"),
        ("unwritten", "unwritten"),
        ("raises", "raises"),
    ):
        db, broker, adoption, bundles, started, _run, _fresh = _ask_bundle(
            tmp_path, name=f"activate-{name}"
        )
        effect, reservation = _pending_handoff(
            broker, adoption, bundles, started, prefix=f"activate-{name}"
        )
        with db._connection() as conn:
            conn.execute(
                """UPDATE inference_route_executions
                     SET state='terminal',terminal_disposition='owner_cancelled',
                         terminal_outcome='cancelled',terminal_at='2026-08-22T00:00:00Z'
                   WHERE id=?""",
                (reservation["execution_id"],),
            )
        base = bundles._handoff_evidence_providers["test-meeting-handoff"]

        reconstructs = 0

        def reconstruct(conn, evidence_ref, *, mode=mode):
            nonlocal reconstructs
            reconstructs += 1
            if mode == "pre-insert" and reconstructs == 2:
                raise RuntimeError("before settlement insert")
            return base.reconstruct(conn, evidence_ref)

        def activate(conn, evidence_ref, *, mode=mode):
            if mode == "raises":
                base.activate(conn, evidence_ref)
                raise RuntimeError("activate fault")

        hostile = InferenceParentRouteBundleService(
            broker,
            adoption,
            handoff_evidence_providers=(
                replace(base, reconstruct=reconstruct, activate=activate),
            ),
        )
        with pytest.raises((ConflictError, RuntimeError)):
            hostile.reconcile_stop_handoff(command_id=effect["command_id"])
        with db._connection() as conn:
            assert conn.execute("SELECT COUNT(*) FROM inference_parent_stop_handoff_settlements").fetchone()[0] == 0
            assert conn.execute("SELECT COUNT(*) FROM test_displaced_job_activations").fetchone()[0] == 0
            assert conn.execute("SELECT COUNT(*) FROM test_displaced_job_runs").fetchone()[0] == 0


def test_handoff_concurrent_reconcile_and_dispatch_claim_are_exactly_once(
    tmp_path: Path,
) -> None:
    db, broker, adoption, bundles, started, run_displaced, fresh_bundles = _ask_bundle(
        tmp_path, name="concurrent"
    )
    effect, _reservation = _pending_handoff(
        broker, adoption, bundles, started, prefix="concurrent"
    )
    first = fresh_bundles()
    second = fresh_bundles()
    assert first.reconcile_stop_handoff(command_id=effect["command_id"])["state"] == "pending_physical_settlement"
    assert second.reconcile_stop_handoff(command_id=effect["command_id"])["state"] == "pending_physical_settlement"
    with db._connection() as conn:
        assert run_displaced(conn, effect["evidence_ref"]) is False

    db2, _broker2, adoption2, bundles2, started2, run2, fresh2 = _ask_bundle(
        tmp_path, name="competing-dispatchers"
    )
    committed = bundles2.request_stop_handoff(
        OWNER,
        command_id="competing-dispatchers-handoff",
        bundle_id=started2["bundle"]["id"],
        evidence_provider_id="test-meeting-handoff",
        planning_reference="competing-dispatchers-work",
    )
    with db2._connection() as first_conn:
        assert run2(first_conn, committed["evidence_ref"]) is True
    with db2._connection() as second_conn:
        assert run2(second_conn, committed["evidence_ref"]) is False
        assert second_conn.execute("SELECT COUNT(*) FROM test_displaced_job_runs").fetchone()[0] == 1
    assert fresh2().reconcile_stop_handoff(command_id=committed["command_id"]) == committed


def test_handoff_independent_lifecycle_witness_refuses_both_mismatch_directions(
    tmp_path: Path,
) -> None:
    db, broker, adoption, bundles, started, _run, _fresh = _ask_bundle(
        tmp_path, name="forced-active"
    )
    effect, _reservation = _pending_handoff(
        broker, adoption, bundles, started, prefix="forced-active"
    )
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO test_displaced_job_activations VALUES (?)",
            (effect["evidence_ref"],),
        )
    with pytest.raises(ConflictError) as early:
        bundles.reconcile_stop_handoff(command_id=effect["command_id"])
    assert early.value.code == "inference_parent_stop_handoff_integrity_invalid"

    db2, broker2, adoption2, bundles2, started2, _run2, _fresh2 = _ask_bundle(
        tmp_path, name="missing-active"
    )
    pending, _reservation2 = _pending_handoff(
        broker2, adoption2, bundles2, started2, prefix="missing-active"
    )
    settled = {**pending, "state": "committed"}
    encoded = json.dumps(settled, sort_keys=True, separators=(",", ":"))
    digest = "sha256:" + __import__("hashlib").sha256(encoded.encode()).hexdigest()
    with db2._connection() as conn:
        conn.execute(
            "INSERT INTO inference_parent_stop_handoff_settlements VALUES (?,?,?,?)",
            (pending["command_id"], encoded, digest, 0.0),
        )
    with pytest.raises(ConflictError) as absent:
        bundles2.reconcile_stop_handoff(command_id=pending["command_id"])
    assert absent.value.code == "inference_parent_stop_handoff_integrity_invalid"


def _ask_payload(question: str = "Why?") -> dict[str, object]:
    return {
        "system_prompt": "Answer.",
        "user_prompt": question,
        "temperature": 0.0,
        "max_tokens": 16,
    }


def test_bundle_execution_seal_refuses_late_admission_without_partial_rows(
    tmp_path: Path,
) -> None:
    db, _broker, adoption, bundles, started, run_displaced, _fresh = _ask_bundle(
        tmp_path, name="sealed-late"
    )
    route = started["bundle"]["members"][0]
    effect = bundles.request_stop_handoff(
        OWNER,
        command_id="sealed-late-handoff",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id="test-meeting-handoff",
        planning_reference="sealed-late-work",
    )
    assert effect["state"] == "committed"
    with db._connection() as conn:
        assert run_displaced(conn, effect["evidence_ref"]) is True
    provider_calls: list[str] = []
    with db._connection() as conn:
        executions_before = conn.execute(
            "SELECT COUNT(*) FROM inference_route_executions"
        ).fetchone()[0]
        attempts_before = conn.execute(
            "SELECT COUNT(*) FROM inference_route_attempts"
        ).fetchone()[0]
    with pytest.raises(ConflictError) as refused:
        adoption.admit_on_frozen_route(
            OWNER,
            command_id="sealed-late-child",
            route_plan_id=route["route_plan_id"],
            capability_id="ask.answer",
            operation_id="sealed-late-operation",
            payload=_ask_payload("Late work?"),
            reserved_output_tokens=16,
        )
    assert refused.value.code == "inference_route_execution_parent_sealed"
    assert provider_calls == []
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_executions").fetchone()[0] == executions_before
        assert conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0] == attempts_before


def test_bundle_execution_seal_refuses_after_terminal_parent(tmp_path: Path) -> None:
    db, broker, adoption, _bundles, started, _run, _fresh = _ask_bundle(
        tmp_path, name="sealed-terminal"
    )
    route = started["bundle"]["members"][0]
    broker.parent_run_controller.close(
        started["parent"].context, "cancelled", principal=OWNER
    )
    with pytest.raises(ConflictError) as refused:
        adoption.admit_on_frozen_route(
            OWNER,
            command_id="sealed-terminal-child",
            route_plan_id=route["route_plan_id"],
            capability_id="ask.answer",
            operation_id="sealed-terminal-operation",
            payload=_ask_payload(),
            reserved_output_tokens=16,
        )
    assert refused.value.code == "inference_route_execution_parent_sealed"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_executions").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0] == 0


def test_bundle_execution_seal_preserves_open_and_nonbundled_admission(
    tmp_path: Path,
) -> None:
    db, _broker, adoption, _bundles, started, _run, _fresh = _ask_bundle(
        tmp_path, name="sealed-open"
    )
    bundled = adoption.admit_on_frozen_route(
        OWNER,
        command_id="sealed-open-child",
        route_plan_id=started["bundle"]["members"][0]["route_plan_id"],
        capability_id="ask.answer",
        operation_id="sealed-open-operation",
        payload=_ask_payload(),
        reserved_output_tokens=16,
    )
    nonbundled = adoption.plans.freeze_route_plan(
        ROUTE_PLANNING_AUTHORITY,
        command_id="sealed-nonbundle-route",
        capability_id="ask.answer",
    )
    admitted = adoption.admit_on_frozen_route(
        OWNER,
        command_id="sealed-nonbundle-child",
        route_plan_id=nonbundled["id"],
        capability_id="ask.answer",
        operation_id="sealed-nonbundle-operation",
        payload=_ask_payload("Unbundled work?"),
        reserved_output_tokens=16,
    )
    assert bundled["execution"]["state"] == "active"
    assert admitted["execution"]["state"] == "active"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_executions").fetchone()[0] == 2


def test_handoff_settlement_and_stop_provenance_tamper_refuse(tmp_path: Path) -> None:
    db, _broker, adoption, bundles, started, _run, _fresh = _ask_bundle(
        tmp_path, name="provenance"
    )
    route = started["bundle"]["members"][0]
    adoption.admit_on_frozen_route(
        OWNER,
        command_id="provenance-child",
        route_plan_id=route["route_plan_id"],
        capability_id="ask.answer",
        operation_id="provenance-child-operation",
        payload={
            "system_prompt": "Answer.", "user_prompt": "Why?",
            "temperature": 0.0, "max_tokens": 16,
        },
        reserved_output_tokens=16,
    )
    first = bundles.request_stop_handoff(
        OWNER,
        command_id="provenance-handoff",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id="test-meeting-handoff",
        planning_reference="provenance-work",
    )
    second_started = bundles.start(
        OWNER,
        command_id="provenance-parent-two",
        parent_kind="meeting.session",
        definition_ref="meeting:test",
        definition_revision="1",
        input_snapshot={"meeting_id": "meeting-two"},
        deadline_at=time.time() + 300,
        routes=({"key": "ask", "capability_id": "ask.answer", "invocation_id": "meeting-two"},),
    )
    second = bundles.request_stop_handoff(
        OWNER,
        command_id="provenance-handoff-two",
        bundle_id=second_started["bundle"]["id"],
        evidence_provider_id="test-meeting-handoff",
        planning_reference="provenance-work-two",
    )
    with db._connection() as conn:
        conn.execute("DROP TRIGGER inference_parent_stop_handoff_settlements_no_update")
        copied = conn.execute(
            "SELECT effect_json,effect_sha256 FROM inference_parent_stop_handoff_settlements WHERE command_id=?",
            (first["command_id"],),
        ).fetchone()
        conn.execute(
            "UPDATE inference_parent_stop_handoff_settlements SET effect_json=?,effect_sha256=? WHERE command_id=?",
            (copied["effect_json"], copied["effect_sha256"], second["command_id"]),
        )
    with pytest.raises(ConflictError) as substitution:
        bundles.reconcile_stop_handoff(command_id=second["command_id"])
    assert substitution.value.code == "inference_parent_stop_handoff_integrity_invalid"
    with db._connection() as conn:
        conn.execute("DROP TRIGGER inference_route_execution_commands_no_update")
        command_id = conn.execute(
            "SELECT stop_command_id FROM inference_parent_stop_handoff_executions WHERE command_id=?",
            (first["command_id"],),
        ).fetchone()[0]
        conn.execute(
            "UPDATE inference_route_execution_commands SET effect_sha256=? WHERE command_id=?",
            ("sha256:" + "f" * 64, command_id),
        )
    with pytest.raises(ConflictError) as stop_tamper:
        bundles.request_stop_handoff(
            OWNER,
            command_id=first["command_id"],
            bundle_id=started["bundle"]["id"],
            evidence_provider_id="test-meeting-handoff",
            planning_reference="provenance-work",
        )
    assert stop_tamper.value.code == "inference_parent_stop_handoff_integrity_invalid"


@pytest.mark.parametrize(
    "bucket",
    (
        "inference_route_plan_principal_evidence",
        "inference_parent_route_bundles",
        "inference_parent_route_bundle_members",
        "inference_parent_stop_handoffs",
        "inference_parent_stop_handoff_executions",
        "inference_parent_stop_handoff_settlements",
    ),
)
def test_new_route_and_handoff_tables_are_hostile_sync_refused(
    tmp_path: Path, bucket: str,
) -> None:
    db = Database(tmp_path / f"hostile-{bucket}.db")
    with pytest.raises(ValidationError) as refused:
        SyncService(db).push(OWNER, {"notes": [], bucket: [{"forged": True}]})
    assert refused.value.code == "sync_hub_local_bucket_forbidden"



def _registry_with_alternate_ask_policy() -> tuple[InferenceCapabilityRegistry, str]:
    current = process_inference_capability_registry()
    original = current.require("ask.answer")
    default = current.retry_policy(original.default_retry_policy_id)
    alternate = replace(
        default,
        id="retry.ask.alternate",
        permitted_capability_ids=("ask.answer",),
        per_entry_attempts=1,
        total_physical_attempts=2,
        sha256="",
    )
    capability = replace(
        original,
        permitted_retry_policy_ids=(original.default_retry_policy_id, alternate.id),
        schema_sha256="",
    )
    return (
        InferenceCapabilityRegistry.compose(
            capabilities=tuple(
                capability if item.id == capability.id else item
                for item in current._capabilities.values()
            ),
            retry_policies=(*current._retry_policies.values(), alternate),
        ),
        alternate.id,
    )


def test_bundle_uses_exact_nondefault_assignment_budget_before_shell_admission(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "alternate-policy.db")
    registry, alternate_id = _registry_with_alternate_ask_policy()
    _profile(db, "quick")
    InferenceAssignmentService(db, registry=registry).set_assignment(
        OWNER,
        {
            "command_id": "alternate-assignment",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "ask.answer"},
            "entries": [{"profile_id": "quick", "profile_revision": 1}],
            "retry_policy_id": alternate_id,
        },
    )
    broker = _configure(db)
    bundles = InferenceParentRouteBundleService(broker, broker.inference_adoption_service)
    bundles._plans = InferenceRoutePlanService(db, registry=registry)
    started = bundles.start(
        OWNER,
        command_id="alternate-parent",
        parent_kind="meeting.session",
        definition_ref="meeting:test",
        definition_revision="1",
        input_snapshot={"meeting_id": "alternate"},
        deadline_at=time.time() + 300,
        routes=({"key": "ask", "capability_id": "ask.answer", "invocation_id": "alternate"},),
        lifecycle_child_budget=1,
    )
    assert started["bundle"]["parent_child_budget"] == 3
    assert started["bundle"]["members"][0]["maximum_physical_attempts"] == 2


def test_bundle_refuses_assignment_policy_race_after_honest_shell_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = Database(tmp_path / "alternate-policy-race.db")
    registry, alternate_id = _registry_with_alternate_ask_policy()
    _profile(db, "quick")
    assignments = InferenceAssignmentService(db, registry=registry)
    body = {
        "scope": {"kind": "capability", "capability_id": "ask.answer"},
        "entries": [{"profile_id": "quick", "profile_revision": 1}],
    }
    assignments.set_assignment(
        OWNER,
        {"command_id": "race-assignment", "expected_revision": 0, **body, "retry_policy_id": alternate_id},
    )
    broker = _configure(db)
    bundles = InferenceParentRouteBundleService(broker, broker.inference_adoption_service)
    plans = InferenceRoutePlanService(db, registry=registry)
    bundles._plans = plans
    original = plans.resolve_route_plan_for_feature

    def resolve_then_change(*args: object, **kwargs: object) -> dict[str, object]:
        resolved = original(*args, **kwargs)
        assignments.set_assignment(
            OWNER,
            {"command_id": "race-assignment-change", "expected_revision": 1, **body, "retry_policy_id": None},
        )
        return resolved

    monkeypatch.setattr(plans, "resolve_route_plan_for_feature", resolve_then_change)
    with pytest.raises(ConflictError) as refused:
        bundles.start(
            OWNER,
            command_id="race-parent",
            parent_kind="meeting.session",
            definition_ref="meeting:test",
            definition_revision="1",
            input_snapshot={"meeting_id": "race"},
            deadline_at=time.time() + 300,
            routes=({"key": "ask", "capability_id": "ask.answer", "invocation_id": "race"},),
        )
    assert refused.value.code == "inference_parent_route_bundle_integrity_invalid"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_parent_route_bundles").fetchone()[0] == 0
        assert conn.execute("SELECT state FROM kernel_operations WHERE idempotency_key='race-parent'").fetchone()[0] == "refused"


def test_bundle_refuses_equal_total_per_route_policy_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = Database(tmp_path / "equal-policy-swap.db")
    current = process_inference_capability_registry()
    standard = current.retry_policy("retry.text.standard")
    alternate = replace(
        standard,
        id="retry.text.equal-swap",
        permitted_capability_ids=("ask.answer", "speech.rewrite"),
        per_entry_attempts=1,
        total_physical_attempts=2,
        sha256="",
    )
    capabilities = {
        capability_id: replace(
            current.require(capability_id),
            permitted_retry_policy_ids=(
                *current.require(capability_id).permitted_retry_policy_ids,
                alternate.id,
            ),
            schema_sha256="",
        )
        for capability_id in ("ask.answer", "speech.rewrite")
    }
    registry = InferenceCapabilityRegistry.compose(
        capabilities=tuple(
            capabilities.get(item.id, item) for item in current._capabilities.values()
        ),
        retry_policies=(*current._retry_policies.values(), alternate),
    )
    _profile(
        db,
        "quick",
        claims=(
            "language",
            _result_claim("ask.answer"),
            _result_claim("speech.rewrite"),
        ),
    )
    assignments = InferenceAssignmentService(db, registry=registry)
    for capability_id, policy_id in (("ask.answer", alternate.id), ("speech.rewrite", None)):
        assignments.set_assignment(
            OWNER,
            {
                "command_id": f"equal-swap-initial-{capability_id}",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": capability_id},
                "entries": [{"profile_id": "quick", "profile_revision": 1}],
                "retry_policy_id": policy_id,
            },
        )
    broker = _configure(db)
    bundles = InferenceParentRouteBundleService(
        broker, broker.inference_adoption_service
    )
    bundles._plans = InferenceRoutePlanService(db, registry=registry)
    original_start = bundles._parents.start

    def start_then_swap(*args: object, **kwargs: object) -> object:
        parent = original_start(*args, **kwargs)
        for capability_id, policy_id in (("ask.answer", None), ("speech.rewrite", alternate.id)):
            assignments.set_assignment(
                OWNER,
                {
                    "command_id": f"equal-swap-flip-{capability_id}",
                    "expected_revision": 1,
                    "scope": {"kind": "capability", "capability_id": capability_id},
                    "entries": [{"profile_id": "quick", "profile_revision": 1}],
                    "retry_policy_id": policy_id,
                },
            )
        return parent

    monkeypatch.setattr(bundles._parents, "start", start_then_swap)
    with pytest.raises(ConflictError) as refused:
        bundles.start(
            OWNER,
            command_id="equal-swap-parent",
            parent_kind="meeting.session",
            definition_ref="meeting:equal-swap",
            definition_revision="1",
            input_snapshot={"meeting_id": "equal-swap"},
            deadline_at=time.time() + 300,
            routes=(
                {"key": "ask", "capability_id": "ask.answer", "invocation_id": "equal-swap"},
                {"key": "rewrite", "capability_id": "speech.rewrite", "invocation_id": "equal-swap"},
            ),
        )
    assert refused.value.code == "inference_parent_route_bundle_integrity_invalid"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_parent_route_bundles").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_route_plans").fetchone()[0] == 0
        assert conn.execute("SELECT state FROM kernel_operations WHERE idempotency_key='equal-swap-parent'").fetchone()[0] == "refused"



def test_stop_handoff_known_inflight_receipt_settles_then_activates_once(
    tmp_path: Path,
) -> None:
    db, broker, adoption, bundles, started, run_displaced, fresh_bundles = _ask_bundle(
        tmp_path, name="known-inflight"
    )
    route = started["bundle"]["members"][0]
    admitted = adoption.admit_on_frozen_route(
        OWNER,
        command_id="known-inflight-child",
        route_plan_id=route["route_plan_id"],
        capability_id="ask.answer",
        operation_id="known-inflight-child-operation",
        payload={
            "system_prompt": "Answer.", "user_prompt": "Why?",
            "temperature": 0.0, "max_tokens": 16,
        },
        reserved_output_tokens=16,
    )
    controller = adoption.controller
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id="known-inflight-reserve",
        execution_id=admitted["execution"]["id"],
    )["reservation"]
    entered, release = threading.Event(), threading.Event()
    outcomes: list[object] = []
    failures: list[BaseException] = []

    class BlockingAdapter:
        def dispatch(self, _engine: object, _payload: object, _cancelled: object) -> str:
            entered.set()
            assert release.wait(timeout=10)
            return "routed-result"

        def cancel(self) -> str:
            return "cancelled"

    payload = {"question": "private"}
    request = InvocationRequest(
        deployment_revision=reservation["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30,
        payload=payload,
        invocation_id=reservation["child_invocation_id"],
        attempt_ordinal=reservation["physical_attempt_ordinal"],
        route_attempt_reservation=reservation,
    )
    runner = InferenceRunner(
        broker,
        db,
        engine_factory=lambda _revision, **_kwargs: object(),
        principal_provider=lambda: OWNER,
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    )

    def invoke() -> None:
        try:
            outcomes.append(runner.invoke(request, BlockingAdapter()))
        except BaseException as exc:  # surface worker failure in the test thread
            failures.append(exc)

    worker = threading.Thread(target=invoke)
    worker.start()
    assert entered.wait(timeout=10)
    pending = bundles.request_stop_handoff(
        OWNER,
        command_id="known-inflight-handoff",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id="test-meeting-handoff",
        planning_reference="known-inflight-work",
    )
    assert pending["state"] == "pending_physical_settlement"
    with db._connection() as conn:
        assert run_displaced(conn, pending["evidence_ref"]) is False
    release.set()
    worker.join(timeout=10)
    assert not worker.is_alive()
    assert not failures
    assert outcomes
    with db._connection() as conn:
        assert conn.execute(
            "SELECT state FROM inference_route_executions WHERE id=?",
            (admitted["execution"]["id"],),
        ).fetchone()[0] == "terminal"
    settled = fresh_bundles().reconcile_stop_handoff(command_id=pending["command_id"])
    assert settled["state"] == "committed"
    with db._connection() as conn:
        assert run_displaced(conn, pending["evidence_ref"]) is True
        assert run_displaced(conn, pending["evidence_ref"]) is False
        assert conn.execute("SELECT COUNT(*) FROM test_displaced_job_runs").fetchone()[0] == 1
    assert bundles.reconcile_stop_handoff(command_id=pending["command_id"]) == settled



@pytest.mark.parametrize(
    "column",
    ("effect_sha256", "evidence_ref", "evidence_sha256", "evidence_provider_revision"),
)
def test_handoff_effect_reference_hash_and_provider_revision_tamper_refuse(
    tmp_path: Path, column: str,
) -> None:
    db, _broker, _adoption, bundles, started, _run, _fresh = _ask_bundle(
        tmp_path, name=f"handoff-tamper-{column}"
    )
    effect = bundles.request_stop_handoff(
        OWNER,
        command_id=f"handoff-tamper-{column}",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id="test-meeting-handoff",
        planning_reference=f"handoff-tamper-{column}-work",
    )
    forged = 999 if column == "evidence_provider_revision" else "sha256:" + "f" * 64
    if column == "evidence_ref":
        forged = "handoff:forged"
    with db._connection() as conn:
        conn.execute("DROP TRIGGER inference_parent_stop_handoffs_no_update")
        conn.execute(
            f"UPDATE inference_parent_stop_handoffs SET {column}=? WHERE command_id=?",
            (forged, effect["command_id"]),
        )
    with pytest.raises(ConflictError) as refused:
        bundles.reconcile_stop_handoff(command_id=effect["command_id"])
    assert refused.value.code == "inference_parent_stop_handoff_integrity_invalid"
