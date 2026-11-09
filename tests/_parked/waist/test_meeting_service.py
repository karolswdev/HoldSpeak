# PARKED 2026-11-09 (door/own-choice-park-waist): their methods are parked: no product caller once the engine door chose on its own.
# Moved from tests/unit/test_meeting_service.py; its helpers are still there.

from tests.unit.test_meeting_service import *  # noqa: F401,F403
from holdspeak.services.inference_fallback_controller import InferenceFallbackController  # noqa: F401
from holdspeak.services.inference_route_plan_service import RouteAdmissionEvidenceProvider  # noqa: F401


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


