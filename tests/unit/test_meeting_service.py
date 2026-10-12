"""The meeting service tests: one file for the service (merged from phase-named files, 2026-10-12)."""
from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.cadence.collector import LoopCollector
from holdspeak.db import Database
from holdspeak.db.calendar_events import CalendarEvent
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
from holdspeak.mcp import tools as mcp_tools
from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
from holdspeak.meeting_session.deferred_admission import queue_service_principal
from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.errors import ConflictError, ValidationError
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.inference_adoption_service import RoutedInferenceCoordinator
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.inference_fallback_controller import (
    INFERENCE_FALLBACK_AUTHORITY,
    InferenceFallbackController,
    RoutedAttemptRuntime,
)
from holdspeak.services.inference_parent_route_bundle_service import (
    HandoffEvidenceProvider,
    InferenceParentRouteBundleService,
)
from holdspeak.services.inference_route_plan_service import (
    ROUTE_PLANNING_AUTHORITY,
    InferenceRoutePlanService,
    RouteAdmissionEvidenceProvider,
)
from holdspeak.services.inference_semantic_adapters import (
    ClosedSemanticAdapter,
    SemanticAdapterContract,
    adapter_for,
    adapter_for_frozen_definition,
    normalize_bookmark_label,
)
from holdspeak.services.meeting_service import MeetingService
from holdspeak.services.people_service import PeopleService
from holdspeak.services.project_service import ProjectService
from holdspeak.services.projection_service import ProjectionService
from holdspeak.services.proposal_bridge_service import ProposalBridgeService
from holdspeak.services.recall_service import RecallService
from holdspeak.services.room_people_service import _read_room_commitments
from holdspeak.services.sync_service import SyncService
from holdspeak.services.watch_sources import MeetingWatchSource
from holdspeak.services.workbench_service import WorkbenchService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.meeting_import import build_meeting_import_router
from holdspeak.web.routes.meetings.crud import build_crud_router
from holdspeak.web.routes.projections import build_projections_router
from holdspeak.web.routes.proposals import _status, build_proposal_router
from tests.unit.test_phase143_inference_assignments import (
    OWNER,
    _profile,
    _result_claim,
)
from tests.unit.test_phase143_inference_fallback_controller import _broker_child

# ── from test_phase143_meeting_route_primitives.py: Story 143-08 tranche A-C closed adapters, principals, and parent bundles. ──


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


def test_service_route_policy_inherits_global_only_for_the_meeting_queue(tmp_path: Path) -> None:
    """meeting-intel-queue@2 (owner ruling 2026-10-05): the meeting queue inherits
    the owner's global "Default for AI work"; every other service policy stays
    capability-only (group/global are not ambient authority for them)."""
    from holdspeak.services.inference_service_route_policy import (
        builtin_service_route_policy_registry,
    )

    sources = {
        definition.id: definition.assignment_sources
        for definition in builtin_service_route_policy_registry()._definitions.values()
    }
    assert sources.pop("meeting-intel-queue@2") == ("capability", "group", "global")
    assert sources and set(sources.values()) == {("capability",)}

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
        inherited = plans.freeze_route_plan_for_feature_in_transaction(
            ROUTE_PLANNING_AUTHORITY,
            conn,
            command_id="service-global-inherited",
            feature_principal=queue,
            parent_kind="meeting.deferred-intel-job",
            capability_id=capability,
            invocation_id="job-zero",
        )
        conn.commit()
    assert inherited["source"]["inherited_from"] == "global"

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
    assert evidence["assignment_sources"] == ["capability", "group", "global"]

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


def test_aggregate_bundle_budget_debits_once_and_refuses_overallocation(tmp_path: Path) -> None:
    """A manifest-only group is charged inside controller reservation BEGIN IMMEDIATE."""
    db = Database(tmp_path / "aggregate-group.db")
    _profile(
        db, "ask-profile",
        claims=("language", "structured_output", _result_claim("thought.interview")),
    )
    _assign(db, "ask.answer", "ask-profile", command="aggregate-ask")
    _assign(db, "thought.interview", "ask-profile", command="aggregate-interview")
    broker = _configure(db)
    adoption = broker.inference_adoption_service
    bundles = InferenceParentRouteBundleService(broker, adoption)
    started = bundles.start(
        OWNER,
        command_id="aggregate-parent",
        parent_kind="meeting.session",
        definition_ref="meeting:aggregate:intel",
        definition_revision="1",
        input_snapshot={"meeting_id": "aggregate"},
        deadline_at=time.time() + 300,
        routes=(
            {"key": "ask", "capability_id": "ask.answer", "invocation_id": "aggregate"},
            {"key": "interview", "capability_id": "thought.interview", "invocation_id": "aggregate"},
        ),
        budget_groups=(
            {"id": "meeting-intelligence", "allocation": 1, "member_keys": ["ask", "interview"]},
        ),
    )
    bundle = started["bundle"]
    assert bundle["parent_child_budget"] == 1
    assert bundle["budget_groups"] == [
        {"id": "meeting-intelligence", "allocation": 1, "member_keys": ["ask", "interview"]}
    ]
    ask_route = next(item for item in bundle["members"] if item["key"] == "ask")
    interview_route = next(item for item in bundle["members"] if item["key"] == "interview")
    ask = adoption.admit_on_frozen_route(
        OWNER,
        command_id="aggregate-ask-operation",
        route_plan_id=ask_route["route_plan_id"],
        capability_id="ask.answer",
        operation_id="aggregate-ask-operation",
        payload={"system_prompt": "Answer.", "user_prompt": "Why?", "temperature": 0.0, "max_tokens": 16},
        reserved_output_tokens=16,
    )
    first = adoption.controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id="aggregate-first-reserve",
        execution_id=ask["execution"]["id"],
    )
    assert first["reservation"] is not None
    with db._connection() as conn:
        before_replay = conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0]
    assert adoption.controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id="aggregate-first-reserve",
        execution_id=ask["execution"]["id"],
    ) == first
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0] == before_replay
    interview = adoption.admit_on_frozen_route(
        OWNER,
        command_id="aggregate-interview-operation",
        route_plan_id=interview_route["route_plan_id"],
        capability_id="thought.interview",
        operation_id="aggregate-interview-operation",
        payload={"prompt": "private"},
        reserved_output_tokens=16,
    )
    with pytest.raises(ConflictError) as refused:
        adoption.controller.reserve_next_attempt(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id="aggregate-second-reserve",
            execution_id=interview["execution"]["id"],
        )
    assert refused.value.code == "inference_route_group_budget_exhausted"


def test_aggregate_bundle_manifest_tamper_refuses_reconstruction(tmp_path: Path) -> None:
    db, _broker, adoption, bundles, started, _run_displaced, _fresh_bundles = _ask_bundle(
        tmp_path, name="aggregate-tamper"
    )
    # Group-less bundles retain their exact historical arithmetic.  Add a malformed
    # aggregate manifest only through hostile direct storage and ensure the shared
    # bundle validator, used by the controller, refuses it.
    bundle = started["bundle"]
    with db._connection() as conn:
        conn.execute("DROP TRIGGER inference_parent_route_bundles_no_update")
        material = {key: value for key, value in bundle.items() if key != "sha256"}
        material["budget_groups"] = [
            {"id": "forged", "allocation": 1, "member_keys": ["missing"]}
        ]
        conn.execute(
            "UPDATE inference_parent_route_bundles SET payload_json=? WHERE id=?",
            (json.dumps(material, sort_keys=True, separators=(",", ":")), bundle["id"]),
        )
    with pytest.raises(ConflictError) as refused:
        bundles.get(bundle["id"])
    assert refused.value.code == "inference_parent_route_bundle_integrity_invalid"


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


# ── from test_philo13_meeting_parking.py: PHILO-13-02 H-A1: meeting parking preserves the retained row and work. ──


OWNER_parking = Principal(PrincipalKind.OWNER, "philo13-test-owner")


def _meeting(meeting_id: str = "meeting-a1") -> MeetingState:
    return MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 10, 1, 10, 0, 0),
        ended_at=datetime(2026, 10, 1, 10, 1, 0),
        title="A1 retained meeting",
        tags=["phase-13"],
        segments=[
            TranscriptSegment(
                text="The retained transcript must survive parking.",
                speaker="Me",
                start_time=0.0,
                end_time=3.0,
            ),
            TranscriptSegment(
                text="Restore must return the same meeting.",
                speaker="Remote",
                start_time=4.0,
                end_time=8.0,
            ),
        ],
        intel=IntelSnapshot(
            timestamp=8.0,
            topics=["retention"],
            action_items=[{"id": "a1-action", "task": "Verify restore", "owner": "Me"}],
            summary="The meeting carries retained work.",
        ),
    )


def _client(db: Database, service: MeetingService) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def owner_principal(request: Request, call_next):
        request.state.principal = OWNER_parking
        return await call_next(request)

    ctx = WebContext(get_state=lambda: {}, meeting_service=service)
    app.include_router(build_meeting_import_router(ctx))
    app.include_router(build_crud_router(ctx))
    return TestClient(app)


def _proposal_client(db: Database) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def owner_principal(request: Request, call_next):
        request.state.principal = OWNER_parking
        return await call_next(request)

    ctx = WebContext(get_state=lambda: {})
    ctx.proposal_bridge_service = ProposalBridgeService(db)
    app.include_router(build_proposal_router(ctx))
    return TestClient(app)


class _RecordingBoundBinder:
    """A real queue binder that records the producer's claimed Meeting id."""

    def __init__(self, db: Database, *, park_in_prepare: bool = False) -> None:
        self.db = db
        self.park_in_prepare = park_in_prepare
        self.prepared: list[str] = []
        self.bound: list[tuple[str, dict[str, str]]] = []
        self.discarded: list[str] = []

    def prepare(self, job, command_ids) -> None:
        self.prepared.append(str(job.meeting_id))
        if self.park_in_prepare:
            assert self.db.meetings.delete_meeting(str(job.meeting_id)) is True

    def discard(self, job_id: str) -> None:
        self.discarded.append(str(job_id))

    def __call__(self, _conn, job, command_ids):
        self.bound.append((str(job.meeting_id), dict(command_ids)))
        return {
            "parent_operation_id": "parent:recording-fence",
            "bundle_id": "bundle:recording-fence",
            "bundle_sha256": "sha256:recording-fence",
        }


def _decision_commitment_chain(db: Database, meeting_id: str) -> tuple[str, str, str]:
    """Mint a decisions artifact, accepted decision, promoted record and commitment."""
    db.plugins.record_artifact(
        artifact_id=f"decisions-{meeting_id}",
        meeting_id=meeting_id,
        artifact_type="decisions",
        title="Decision extraction",
        structured_json={
            "decisions": [{
                "decision": "Parked meeting dependency must disappear",
                "rationale": "A parked source is not active work.",
                "source_timestamp": 1.0,
            }],
        },
        confidence=1.0,
        status="accepted",
        plugin_id="decision_capture",
        plugin_version="test",
    )
    decision = db.decisions.list(meeting_id=meeting_id)[0]
    db.decisions.accept(decision.id, actor=OWNER_parking.identity)
    record = DecisionRecordService(db).create_from_meeting(OWNER_parking, decision.id)
    db.decisions.promote(decision.id, "note", actor=OWNER_parking.identity)
    commitment = FollowThroughService(db).commit_decision(
        OWNER_parking, decision.id, owner="Me", due_at="2099-01-01"
    )
    return decision.id, str(record["id"]), str(commitment["id"])


def _related_rows(db: Database, meeting_id: str) -> dict[str, list[tuple]]:
    with db._connection() as conn:
        return {
            "segments": [
                tuple(row)
                for row in conn.execute(
                    "SELECT text, speaker, start_time, end_time FROM segments "
                    "WHERE meeting_id = ? ORDER BY start_time",
                    (meeting_id,),
                )
            ],
            "intel": [
                tuple(row)
                for row in conn.execute(
                    "SELECT timestamp, summary FROM intel_snapshots "
                    "WHERE meeting_id = ? ORDER BY timestamp",
                    (meeting_id,),
                )
            ],
            "actions": [
                tuple(row)
                for row in conn.execute(
                    "SELECT id, task, owner FROM action_items "
                    "WHERE meeting_id = ? ORDER BY id",
                    (meeting_id,),
                )
            ],
            "artifacts": [
                tuple(row)
                for row in conn.execute(
                    "SELECT id, title, body_markdown FROM artifacts "
                    "WHERE meeting_id = ? ORDER BY id",
                    (meeting_id,),
                )
            ],
            "project_links": [
                tuple(row)
                for row in conn.execute(
                    "SELECT meeting_id, project_id, source, confidence "
                    "FROM meeting_projects WHERE meeting_id = ? ORDER BY project_id",
                    (meeting_id,),
                )
            ],
        }


def test_repository_parks_and_restores_without_deleting_retained_work(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking.db")
    state = _meeting()
    db.meetings.save_meeting(state)
    db.plugins.record_artifact(
        artifact_id="a1-artifact",
        meeting_id=state.id,
        artifact_type="handoff",
        title="Retained handoff",
        body_markdown="The body remains while parked.",
    )
    db.projects.create_project(project_id="a1-project", name="A1 project")
    db.projects.associate_meeting_project(
        meeting_id=state.id, project_id="a1-project", source="test", confidence=0.9
    )
    before = _related_rows(db, state.id)
    assert len(before["segments"]) == 2
    assert len(before["intel"]) == 1
    assert len(before["actions"]) == 1
    assert len(before["artifacts"]) == 1
    assert len(before["project_links"]) == 1

    assert db.meetings.delete_meeting(state.id) is True
    with db._connection() as conn:
        retained_row = conn.execute(
            "SELECT parked FROM meetings WHERE id = ?", (state.id,)
        ).fetchone()
    assert retained_row is not None
    assert retained_row[0] == 1
    assert db.meetings.get_meeting(state.id) is None
    assert db.meetings.get_meeting(state.id, include_parked=True).id == state.id
    assert _related_rows(db, state.id) == before
    assert db.meetings.list_meetings() == []
    assert [item.id for item in db.meetings.list_meetings(parked=True)] == [state.id]

    db.close()
    reopened = Database(tmp_path / "meeting-parking.db")
    assert reopened.meetings.get_meeting(state.id) is None
    assert reopened.meetings.get_meeting(state.id, include_parked=True).parked is True
    assert _related_rows(reopened, state.id) == before

    assert reopened.meetings.restore_meeting(state.id) is True
    assert reopened.meetings.get_meeting(state.id).to_dict()["id"] == state.id
    assert _related_rows(reopened, state.id) == before
    with reopened._connection() as conn:
        assert conn.execute("SELECT parked FROM meetings WHERE id = ?", (state.id,)).fetchone()[0] == 0


def test_repository_park_and_restore_are_idempotent_and_unknown_stays_missing(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking-idempotent.db")
    db.meetings.save_meeting(_meeting("idempotent"))
    assert db.meetings.delete_meeting("idempotent") is True
    assert db.meetings.delete_meeting("idempotent") is True
    assert db.meetings.restore_meeting("idempotent") is True
    assert db.meetings.restore_meeting("idempotent") is True
    assert db.meetings.delete_meeting("unknown") is False
    assert db.meetings.restore_meeting("unknown") is False


def test_save_does_not_accidentally_unpark_a_retained_meeting(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking-save.db")
    db.meetings.save_meeting(_meeting("save-retained"))
    assert db.meetings.delete_meeting("save-retained") is True
    db.meetings.save_meeting(MeetingState(id="save-retained", started_at=datetime.now()))
    assert db.meetings.get_meeting("save-retained") is None
    assert db.meetings.get_meeting("save-retained", include_parked=True).parked is True


def test_service_parked_search_reads_only_the_retained_meeting(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking-search.db")
    service = MeetingService(db)
    db.meetings.save_meeting(_meeting("search-retained"))
    service.delete_meeting(OWNER_parking, "search-retained")

    assert service.list_meetings(OWNER_parking, query="retained", parked=False)["meetings"] == []
    parked = service.list_meetings(OWNER_parking, query="retained", parked=True)
    assert [row["id"] for row in parked["meetings"]] == ["search-retained"]


def test_parked_meeting_proposal_refusal_tells_owner_to_restore(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking-proposal.db")
    db.meetings.save_meeting(_meeting("proposal-retained"))
    proposal = db.proposals.create_proposal(
        meeting_id="proposal-retained",
        project_id=None,
        kind="decision",
        text="Keep the retained record",
        source_plugin="test",
    )
    assert proposal is not None
    db.meetings.delete_meeting("proposal-retained")

    result = ProposalBridgeService(db).confirm_proposal(OWNER_parking, proposal.id)
    assert result["code"] == "meeting_parked"
    assert "restore" in result["error"].lower()
    assert _status(result) == 409

    response = _proposal_client(db).post(f"/api/proposals/{proposal.id}/confirm", json={})
    assert response.status_code == 409
    assert response.json()["success"] is False
    assert response.json()["code"] == "meeting_parked"
    assert "restore" in response.json()["error"].lower()


def test_mcp_delete_verbs_return_parked_receipts_and_retain_rows(
    tmp_path: Path, monkeypatch
) -> None:
    db = Database(tmp_path / "meeting-parking-mcp.db")
    db.meetings.save_meeting(_meeting("mcp-meeting"))
    workbench = db.workbenches.upsert(workbench_id="mcp-workbench", name="MCP parking")
    item = WorkbenchService(db).add_item(OWNER_parking, workbench.id, title="Retained item")

    # Dispatch through the same operation composition used by MCP, with this
    # isolated producer database as the root.  No fabricated parked field is
    # supplied to either operation.
    monkeypatch.setattr(composition, "_installed", composition.bare(db=db, label="a1-mcp"))
    meeting_receipt = mcp_tools.dispatch(
        "meeting.delete", {"meeting_id": "mcp-meeting"}, OWNER_parking
    )
    item_receipt = mcp_tools.dispatch(
        "workbench.delete_item",
        {"workbench_id": workbench.id, "item_id": item["id"]},
        OWNER_parking,
    )

    assert meeting_receipt == {"parked": True, "id": "mcp-meeting"}
    assert item_receipt == {"parked": True, "id": item["id"]}
    assert db.meetings.get_meeting("mcp-meeting") is None
    assert db.meetings.get_meeting("mcp-meeting", include_parked=True).parked is True
    assert db.workbench_items.get(item["id"]) is None
    assert db.workbench_items.get(item["id"], include_parked=True).parked is True


def test_real_import_route_parks_reads_retained_detail_and_restores(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking-route.db")
    service = MeetingService(db)
    client = _client(db, service)

    response = client.post(
        "/api/meetings/import",
        files={"file": ("a1.txt", b"Me: first imported line\nRemote: second imported line\n", "text/plain")},
        data={"title": "Imported A1"},
    )
    assert response.status_code == 202, response.text
    meeting_id = response.json()["meeting_id"]

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        imported = db.meetings.get_meeting(meeting_id, include_parked=True)
        if imported is not None and imported.intel_status != "importing":
            break
        time.sleep(0.02)
    imported = db.meetings.get_meeting(meeting_id, include_parked=True)
    assert imported is not None
    assert len(imported.segments) == 2
    before = _related_rows(db, meeting_id)

    parked = client.delete(f"/api/meetings/{meeting_id}")
    assert parked.status_code == 200
    assert parked.json() == {"parked": meeting_id}
    assert client.get(f"/api/meetings/{meeting_id}").status_code == 404
    assert client.get("/api/meetings").json()["meetings"] == []
    parked_list = client.get("/api/meetings?parked=true")
    assert parked_list.status_code == 200
    assert [row["id"] for row in parked_list.json()["meetings"]] == [meeting_id]
    retained = client.get(f"/api/meetings/{meeting_id}?include_parked=true")
    assert retained.status_code == 200
    assert retained.json()["parked"] is True
    assert [segment["text"] for segment in retained.json()["segments"]] == [
        "first imported line",
        "second imported line",
    ]
    assert _related_rows(db, meeting_id) == before

    restored = client.post(f"/api/meetings/{meeting_id}/restore")
    assert restored.status_code == 200
    assert restored.json()["meeting"]["id"] == meeting_id
    assert restored.json()["meeting"]["parked"] is False
    assert client.get(f"/api/meetings/{meeting_id}").status_code == 200
    assert client.get("/api/meetings?parked=true").json()["meetings"] == []
    assert _related_rows(db, meeting_id) == before


def test_schema_reconciles_parked_columns_additively(tmp_path: Path) -> None:
    path = tmp_path / "old-shape.db"
    db = Database(path)
    with db._connection() as conn:
        conn.execute("ALTER TABLE meetings RENAME TO meetings_old")
        conn.execute(
            "CREATE TABLE meetings (id TEXT PRIMARY KEY, started_at TEXT NOT NULL, "
            "ended_at TEXT, title TEXT)"
        )
        conn.execute(
            "INSERT INTO meetings(id, started_at, ended_at, title) "
            "SELECT id, started_at, ended_at, title FROM meetings_old"
        )
        conn.execute("DROP TABLE meetings_old")
        conn.commit()
    db.close()
    reopened = Database(path)
    with reopened._connection() as conn:
        meeting_columns = {row[1] for row in conn.execute("PRAGMA table_info(meetings)")}
        workbench_columns = {row[1] for row in conn.execute("PRAGMA table_info(workbench_items)")}
    assert "parked" in meeting_columns
    assert "parked" in workbench_columns


@pytest.mark.parametrize(
    "read_family",
    ["brief", "calendar", "recall", "proposal", "intel_claim"],
)
def test_parked_meeting_is_absent_from_its_real_read_family(
    tmp_path: Path, read_family: str,
) -> None:
    db = Database(tmp_path / f"meeting-parking-{read_family}.db")
    state = _meeting(f"read-family-{read_family}")
    if read_family in {"brief", "calendar"}:
        state.calendar_event_id = f"calendar-{read_family}"
    db.meetings.save_meeting(state)

    if read_family in {"brief", "calendar"}:
        from holdspeak.services.monday_brief_service import MondayBriefService

        brief = MondayBriefService(db)
        window_start = "2026-10-01T00:00:00"
        window_end = "2026-10-02T00:00:00"
        read = (
            (lambda: brief._collect_meetings(window_start, window_end))
            if read_family == "brief"
            else (lambda: brief._recorded_calendar_event_ids(window_start, window_end))
        )
        expected_after_park = [] if read_family == "brief" else set()
        expected_after_restore = (
            {f"calendar-{read_family}"} if read_family == "calendar" else None
        )
    elif read_family == "recall":
        read = lambda: db.memory.search("retained transcript", kinds=["meeting"]).hits
        expected_after_park = []
        expected_after_restore = f"meeting:{state.id}"
    elif read_family == "proposal":
        proposal = db.proposals.create_proposal(
            meeting_id=state.id,
            project_id=None,
            kind="action",
            text="Keep the producer fence",
            source_plugin="test",
        )
        assert proposal is not None
        read = lambda: db.proposals.list_proposals(meeting_id=state.id)
        expected_after_park = []
        expected_after_restore = proposal.id
    else:
        job_id = db.intel.enqueue_intel_job(
            state.id,
            transcript_hash=state.transcript_hash(),
            reason="producer fence",
        )
        assert job_id
        binder = _RecordingBoundBinder(db)
        read = lambda: db.intel.claim_next_intel_job_bound(binder)
        expected_after_park = None

    assert db.meetings.delete_meeting(state.id) is True
    parked_value = read()
    assert parked_value == expected_after_park

    assert db.meetings.restore_meeting(state.id) is True
    restored_value = read()
    if read_family == "brief":
        assert restored_value
    elif read_family == "recall":
        assert [hit.source_ref for hit in restored_value] == [expected_after_restore]
    elif read_family == "proposal":
        assert [row.id for row in restored_value] == [expected_after_restore]
    elif read_family == "intel_claim":
        assert restored_value is not None and restored_value.meeting_id == state.id
        assert binder.bound and binder.bound[-1][0] == state.id
    else:
        assert restored_value == expected_after_restore


def test_projection_route_hides_meeting_actuator_job_and_conflict_rows(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking-projections.db")
    state = _meeting("projection-fences")
    db.meetings.save_meeting(state)
    db.actuators.record_proposal(
        meeting_id=state.id,
        window_id="projection-window",
        plugin_id="projection-test",
        plugin_version="1",
        idempotency_key="projection-fence-actuator",
        target="webhook",
        action="post",
        preview="projection fence",
    )
    db.plugins.record_artifact(
        artifact_id="projection-fence-artifact",
        meeting_id=state.id,
        artifact_type="handoff",
        title="Projection fence artifact",
        body_markdown="Hidden with its parked Meeting",
    )
    db.intel.enqueue_intel_job(
        state.id,
        transcript_hash=state.transcript_hash(),
        reason="projection fence",
        legacy_displaced_work=True,
    )
    conflict_id = db.meetings.record_sync_conflict(
        state.id,
        local_value=state.to_dict(),
        incoming_value={**state.to_dict(), "title": "incoming"},
    )
    assert conflict_id

    app = FastAPI()
    app.include_router(build_projections_router(WebContext(
        get_state=lambda: {},
        projection_service=ProjectionService(db),
    )))
    client = TestClient(app)

    before_response = client.get("/api/desk/projections", params={"limit": 200}).json()
    before = before_response["projections"]
    meeting_ref = f"meeting:{state.id}"
    related_rows = [
        row for row in before
        if row["subject_ref"] == meeting_ref or row["correlation_id"] == meeting_ref
    ]
    assert {row["source_kind"] for row in related_rows} >= {
        "actuator_proposal", "artifact", "intel_job", "meeting_sync_conflict"
    }

    db.meetings.delete_meeting(state.id)
    parked_response = client.get("/api/desk/projections", params={"limit": 200}).json()
    parked = parked_response["projections"]
    assert all(
        row["subject_ref"] != meeting_ref and row["correlation_id"] != meeting_ref
        for row in parked
    )
    assert parked_response["page"]["total"] == before_response["page"]["total"] - len(related_rows)

    db.meetings.restore_meeting(state.id)
    restored_response = client.get("/api/desk/projections", params={"limit": 200}).json()
    restored = restored_response["projections"]
    restored_related = [
        row for row in restored
        if row["subject_ref"] == meeting_ref or row["correlation_id"] == meeting_ref
    ]
    assert {row["source_kind"] for row in restored_related} >= {
        "actuator_proposal", "artifact", "intel_job", "meeting_sync_conflict"
    }
    assert restored_response["page"]["total"] == before_response["page"]["total"]


def test_sync_conflict_tombstone_parks_and_restores_retained_children(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking-conflict.db")
    state = _meeting("conflict-tombstone")
    db.meetings.save_meeting(state)
    db.plugins.record_artifact(
        artifact_id="conflict-artifact",
        meeting_id=state.id,
        artifact_type="handoff",
        title="Conflict artifact",
        body_markdown="Retained while parked",
    )
    before = _related_rows(db, state.id)
    conflict_id = db.meetings.record_sync_conflict(
        state.id,
        local_value=state.to_dict(),
        incoming_value={"id": state.id, "deleted": True},
    )

    assert db.meetings.resolve_sync_conflict(
        state.id, conflict_id, resolution="use_incoming"
    ) == "deleted"
    assert db.meetings.get_meeting(state.id) is None
    retained = db.meetings.get_meeting(state.id, include_parked=True)
    assert retained is not None and retained.parked is True
    assert _related_rows(db, state.id) == before
    assert db.meetings.list_sync_conflicts(state.id) == []

    assert db.meetings.restore_meeting(state.id) is True
    assert db.meetings.get_meeting(state.id) is not None
    assert _related_rows(db, state.id) == before


def test_parked_meeting_actions_and_speakers_disappear_from_all_owner_reads(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-parking-owner-reads.db")
    state = _meeting("owner-read-fences")
    state.segments[0].speaker_id = "speaker-fence"
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO speakers (id, name, embedding) VALUES (?, ?, ?)",
            ("speaker-fence", "Fence speaker", b"speaker-embedding"),
        )
        conn.commit()
    db.meetings.save_meeting(state)
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, status) "
            "VALUES (?, NULL, ?, ?, 'pending')",
            ("standalone-owner-read", "Standalone action", "Me"),
        )
        conn.commit()
    db.projects.create_project(project_id="owner-read-project", name="Owner read project")
    db.projects.associate_meeting_project(
        meeting_id=state.id, project_id="owner-read-project", source="test", confidence=1.0
    )

    assert {item.id for item in db.meetings.list_action_items()} == {
        "standalone-owner-read", "a1-action"
    }
    project_service = ProjectService(db)
    assert [item["id"] for item in project_service.list_action_items(OWNER_parking, "owner-read-project")] == [
        "a1-action"
    ]

    before_segments = db.meetings.get_speaker_segments("speaker-fence")
    assert len(before_segments) == 1 and len(before_segments[0]["segments"]) == 1
    assert db.meetings.get_speaker_stats("speaker-fence")["total_segments"] == 1

    people_store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    people_store.initialize()
    people = PeopleService(people_store)
    relationship = people.create_relationship(OWNER_parking, {"display_name": "Owner read person"})
    people.link_calendar_series(
        OWNER_parking, relationship["id"], "uid-owner-read", "source-owner-read", "Owner read"
    )
    db.calendar_events.replace_projection(
        "owner-read-revision",
        [CalendarEvent(
            id="event-owner-read", uid="uid-owner-read", title="Owner read",
            starts_at="2026-10-01T10:00:00", ends_at="2026-10-01T11:00:00",
            location=None, meeting_url=None, last_seen_at=1.0,
            subscription_revision="owner-read-revision", source_id="source-owner-read",
        )],
        seen_at=1.0,
        source_id="source-owner-read",
    )
    with db._connection() as conn:
        conn.execute(
            "UPDATE meetings SET calendar_event_id=? WHERE id=?",
            ("event-owner-read", state.id),
        )
        conn.commit()
    assert people.one_on_one_brief(OWNER_parking, relationship["id"], db=db)["linked_meetings"]

    db.meetings.delete_meeting(state.id)
    after_park = {
        "global_actions": [item.id for item in db.meetings.list_action_items()],
        "project_actions": [
            item["id"] for item in project_service.list_action_items(OWNER_parking, "owner-read-project")
        ],
        "speaker_meetings": [
            group["meeting_id"] for group in db.meetings.get_speaker_segments("speaker-fence")
        ],
        "speaker_total_segments": db.meetings.get_speaker_stats("speaker-fence")["total_segments"],
        "people_meetings": [
            row["meeting_id"]
            for row in people.one_on_one_brief(OWNER_parking, relationship["id"], db=db)["linked_meetings"]
        ],
    }
    assert after_park == {
        "global_actions": ["standalone-owner-read"],
        "project_actions": [],
        "speaker_meetings": [],
        "speaker_total_segments": 0,
        "people_meetings": [],
    }

    db.meetings.restore_meeting(state.id)
    assert {item.id for item in db.meetings.list_action_items()} == {
        "standalone-owner-read", "a1-action"
    }
    assert [item["id"] for item in project_service.list_action_items(OWNER_parking, "owner-read-project")] == [
        "a1-action"
    ]
    assert db.meetings.get_speaker_segments("speaker-fence")
    assert db.meetings.get_speaker_stats("speaker-fence")["total_segments"] == 1
    assert people.one_on_one_brief(OWNER_parking, relationship["id"], db=db)["linked_meetings"]


def test_bound_intel_claim_initial_fence_reads_real_parked_meeting(tmp_path: Path) -> None:
    db = Database(tmp_path / "bound-intel-initial.db")
    state = _meeting("bound-intel-initial")
    db.meetings.save_meeting(state)
    job_id = db.intel.enqueue_intel_job(
        state.id, transcript_hash=state.transcript_hash(), reason="bound fence"
    )
    assert db.meetings.delete_meeting(state.id) is True

    binder = _RecordingBoundBinder(db)
    assert db.intel.claim_next_intel_job_bound(binder) is None
    assert binder.bound == []
    with db._connection() as conn:
        row = conn.execute(
            "SELECT status FROM intel_jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
    assert row["status"] == "queued"

    assert db.meetings.restore_meeting(state.id) is True
    claimed = db.intel.claim_next_intel_job_bound(binder)
    assert claimed is not None
    assert binder.bound and binder.bound[-1][0] == state.id


def test_bound_intel_claim_recheck_fence_rejects_meeting_parked_during_prepare(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "bound-intel-recheck.db")
    state = _meeting("bound-intel-recheck")
    db.meetings.save_meeting(state)
    db.intel.enqueue_intel_job(
        state.id, transcript_hash=state.transcript_hash(), reason="bound recheck fence"
    )

    binder = _RecordingBoundBinder(db, park_in_prepare=True)
    assert db.intel.claim_next_intel_job_bound(binder) is None
    assert binder.prepared == [state.id]
    assert binder.bound == []
    # The bound path may replace the legacy queue leaf before prepare freezes
    # it; the binder must discard that exact prepared leaf after the recheck.
    assert len(binder.discarded) == 1
    with db._connection() as conn:
        row = conn.execute(
            "SELECT status FROM intel_jobs WHERE job_id = ?", (binder.discarded[0],)
        ).fetchone()
    assert row["status"] == "queued"


def test_follow_through_action_read_hides_parked_meeting_and_restores_it(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "follow-through-parked.db")
    state = _meeting("follow-through-parked")
    db.meetings.save_meeting(state)
    service = FollowThroughService(db)

    def card_ids() -> set[str]:
        board = service.board(OWNER_parking)
        return {card.id for lane in (board.now, board.waiting, board.unassigned, board.overdue) for card in lane}

    assert "a1-action" in card_ids()
    assert db.meetings.delete_meeting(state.id) is True
    assert "a1-action" not in card_ids()
    assert db.meetings.restore_meeting(state.id) is True
    assert "a1-action" in card_ids()


def test_follow_through_decision_commitment_hides_parked_source_and_restores_it(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "follow-through-decision-parked.db")
    state = _meeting("follow-through-decision-parked")
    db.meetings.save_meeting(state)
    decision_id, _, _ = _decision_commitment_chain(db, state.id)
    with db._connection() as conn:
        action_item_id = str(conn.execute(
            "SELECT action_item_id FROM decision_commitments WHERE decision_id = ?",
            (decision_id,),
        ).fetchone()[0])
    # The real collector produces the meeting-decision and source-meeting
    # action cadence cards. The board must hide both loops and the open
    # commitment when the source meeting is parked, without a refresh.
    loops = LoopCollector(db).collect()
    decision_loop = next(
        loop for loop in loops
        if loop.source_type == "meeting_decision" and loop.source_id == decision_id
    )
    decision_loop_id = str(decision_loop.id)
    with db._connection() as conn:
        action_rows = conn.execute(
            "SELECT id FROM action_items WHERE meeting_id = ?", (state.id,)
        ).fetchall()
        action_item_ids = {str(row["id"]) for row in action_rows}
        action_loop_rows = conn.execute(
            """SELECT c.id, c.source_id
               FROM cadence_loops c
               JOIN action_items a ON a.id = c.source_id
               WHERE c.source_type = 'meeting_action' AND a.meeting_id = ?""",
            (state.id,),
        ).fetchall()
    action_loop_ids = {str(row["id"]) for row in action_loop_rows}
    assert action_loop_ids
    assert action_item_id in action_item_ids
    assert {str(row["source_id"]) for row in action_loop_rows} <= action_item_ids
    service = FollowThroughService(db)

    def decision_cards() -> list[object]:
        board = service.board(OWNER_parking)
        return [
            card
            for lane in (board.now, board.waiting, board.unassigned, board.overdue)
            for card in lane
            if card.decision_id == decision_id
            or card.id in action_item_ids | action_loop_ids | {decision_loop_id}
        ]

    before = decision_cards()
    before_ids = {card.id for card in before}
    assert action_item_ids <= before_ids
    assert decision_loop_id in before_ids
    assert db.meetings.delete_meeting(state.id) is True
    parked_ids = {card.id for card in decision_cards()}
    assert parked_ids.isdisjoint(action_item_ids | action_loop_ids | {decision_loop_id})
    assert db.meetings.restore_meeting(state.id) is True
    restored_ids = {card.id for card in decision_cards()}
    assert action_item_ids | {decision_loop_id} <= restored_ids
    with db._connection() as conn:
        restored_loop_ids = {
            str(row["id"])
            for row in conn.execute(
                "SELECT id FROM cadence_loops WHERE id IN ({})".format(
                    ",".join("?" for _ in action_loop_ids)
                ),
                tuple(action_loop_ids),
            ).fetchall()
        }
    assert restored_loop_ids == action_loop_ids


def test_project_stats_hide_parked_meeting_actions_and_artifacts(tmp_path: Path) -> None:
    db = Database(tmp_path / "project-stats-parked.db")
    state = _meeting("project-stats-parked")
    db.meetings.save_meeting(state)
    db.projects.create_project(project_id="project-stats", name="Project stats")
    db.projects.associate_meeting_project(
        meeting_id=state.id, project_id="project-stats", source="test", confidence=1.0
    )
    db.plugins.record_artifact(
        artifact_id="project-stats-artifact", meeting_id=state.id,
        artifact_type="handoff", title="Stats artifact", body_markdown="retained",
    )
    service = ProjectService(db)
    assert service.summary(OWNER_parking, "project-stats") == {
        "meeting_count": 1,
        # Stored as the aware UTC instant of 10:00 local (the aware-time census).
        "first_meeting": datetime(2026, 10, 1, 10, 0, 0).astimezone(timezone.utc).isoformat(),
        "last_meeting": datetime(2026, 10, 1, 10, 0, 0).astimezone(timezone.utc).isoformat(),
        "action_items_by_status": {"pending": 1},
        "artifact_count": 1,
    }

    assert db.meetings.delete_meeting(state.id) is True
    assert service.summary(OWNER_parking, "project-stats") == {
        "meeting_count": 0,
        "first_meeting": None,
        "last_meeting": None,
        "action_items_by_status": {},
        "artifact_count": 0,
    }
    assert db.meetings.restore_meeting(state.id) is True
    assert service.summary(OWNER_parking, "project-stats")["artifact_count"] == 1
    assert service.summary(OWNER_parking, "project-stats")["action_items_by_status"] == {"pending": 1}


def test_meeting_watch_source_hides_parked_meeting_and_restores_it(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-watch-parked.db")
    state = _meeting("meeting-watch-parked")
    db.meetings.save_meeting(state)
    db.projects.create_project(project_id="watch-project", name="Watch project")
    db.projects.associate_meeting_project(
        meeting_id=state.id, project_id="watch-project", source="test", confidence=1.0
    )
    source = MeetingWatchSource(db=db)
    query = {"project_id": "watch-project"}
    assert [row["id"] for row in source.snapshot(OWNER_parking, query_kind="meetings", query=query)] == [state.id]

    assert db.meetings.delete_meeting(state.id) is True
    assert source.snapshot(OWNER_parking, query_kind="meetings", query=query) == []
    assert db.meetings.restore_meeting(state.id) is True
    assert [row["id"] for row in source.snapshot(OWNER_parking, query_kind="meetings", query=query)] == [state.id]


def test_intel_job_list_hides_parked_meeting_and_restores_it(tmp_path: Path) -> None:
    db = Database(tmp_path / "intel-list-parked.db")
    state = _meeting("intel-list-parked")
    db.meetings.save_meeting(state)
    job_id = db.intel.enqueue_intel_job(
        state.id, transcript_hash=state.transcript_hash(), reason="list fence"
    )
    assert [job.job_id for job in db.intel.list_intel_jobs()] == [job_id]

    assert db.meetings.delete_meeting(state.id) is True
    assert db.intel.list_intel_jobs() == []
    assert db.meetings.restore_meeting(state.id) is True
    assert [job.job_id for job in db.intel.list_intel_jobs()] == [job_id]


def test_loop_collector_hides_parked_meeting_decision_and_restores_it(tmp_path: Path) -> None:
    db = Database(tmp_path / "collector-parked.db")
    state = _meeting("collector-parked")
    db.meetings.save_meeting(state)
    decision_id, _, _ = _decision_commitment_chain(db, state.id)
    collector = LoopCollector(db)

    assert any(loop.source_id == decision_id for loop in collector.collect())
    assert db.meetings.delete_meeting(state.id) is True
    assert collector._collect_meeting_decisions(datetime.now()) == []
    parked_loop = db.cadence.get_loop_by_source("meeting_decision", decision_id)
    assert parked_loop is not None and parked_loop.status == "closed"
    assert db.meetings.restore_meeting(state.id) is True
    assert any(loop.source_id == decision_id for loop in collector.collect())


def test_room_commitment_read_hides_parked_source_and_restores_it(tmp_path: Path) -> None:
    db = Database(tmp_path / "room-commitment-parked.db")
    state = _meeting("room-commitment-parked")
    db.meetings.save_meeting(state)
    db.projects.create_project(project_id="room-project", name="Room project")
    db.projects.associate_meeting_project(
        meeting_id=state.id, project_id="room-project", source="test", confidence=1.0
    )
    _, _, commitment_id = _decision_commitment_chain(db, state.id)
    project_service = ProjectService(db)
    assert [row["id"] for row in _read_room_commitments(project_service, "room-project")] == [commitment_id]

    assert db.meetings.delete_meeting(state.id) is True
    assert _read_room_commitments(project_service, "room-project") == []
    assert db.meetings.restore_meeting(state.id) is True
    assert [row["id"] for row in _read_room_commitments(project_service, "room-project")] == [commitment_id]


def test_recall_hides_parked_commitment_but_keeps_promoted_decision_record(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "recall-parked.db")
    state = _meeting("recall-parked")
    db.meetings.save_meeting(state)
    _, record_id, commitment_id = _decision_commitment_chain(db, state.id)
    service = RecallService(db)

    before_decisions = service.recall(OWNER_parking, "Parked meeting dependency", filter="decisions")
    before_commitments = service.recall(OWNER_parking, "Parked meeting dependency", filter="commitments")
    assert [card["id"] for card in before_decisions["current"]] == [record_id]
    assert [row["id"] for row in before_commitments["owed"]] == [commitment_id]
    assert before_decisions["current"][0]["source"]["meeting_id"] == state.id

    assert db.meetings.delete_meeting(state.id) is True
    parked_decisions = service.recall(OWNER_parking, "Parked meeting dependency", filter="decisions")
    parked_commitments = service.recall(OWNER_parking, "Parked meeting dependency", filter="commitments")
    assert [card["id"] for card in parked_decisions["current"]] == [record_id]
    assert parked_decisions["current"][0]["source"] is None
    assert parked_commitments["owed"] == []

    assert db.meetings.restore_meeting(state.id) is True
    restored = service.recall(OWNER_parking, "Parked meeting dependency", filter="commitments")
    assert [row["id"] for row in restored["owed"]] == [commitment_id]
