"""HS-143-09 A2 — durable ToolTurn transaction authority."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.services.inference_adoption_service import RoutedInferenceCoordinator
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.inference_parent_route_bundle_service import InferenceParentRouteBundleService
from holdspeak.services.tool_capability_service import (
    CanonicalApplicationOperationDescriptor,
    ModelTurnCapabilityProjection,
)
from holdspeak.services.tool_turn_controller import (
    BrokerToolCallPort,
    TOOL_TURN_AUTHORITY,
    ToolTurnController,
    ToolTurnRefused,
)
from holdspeak.services.tool_capability_service import ToolCallCandidate, ToolResultEnvelope
from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim


def _descriptor() -> CanonicalApplicationOperationDescriptor:
    return CanonicalApplicationOperationDescriptor(
        capability_id="evidence.note_lookup", revision=1,
        label="Find attached Note", description="Find an attached Note.",
        argument_schema={
            "type": "object", "additionalProperties": False,
            "properties": {"note_id": {"type": "string"}}, "required": ["note_id"],
        },
        service_operation="note.lookup", capability_class="evidence_read", effect_mode="read",
        allowed_data_classes=("note",), allowed_placements=("local",), allowed_egress=("local",),
        max_calls=2, max_result_bytes=1024, max_result_tokens=256, commutative_read=True,
    )


def _lease(descriptor: CanonicalApplicationOperationDescriptor, *, turn: str, now: float) -> dict[str, object]:
    return {
        "schema": "TurnCapabilityLease@1", "lease_id": f"lease-{turn}", "nonce": f"nonce-{turn}",
        "epoch": 1, "parent_turn_id": turn, "owner_principal_id": "owner-1",
        "deployment_revision": "deployment-1", "operation_kind": "thought.interview",
        "operation_revision": "revision-1", "owner_intent_receipt_id": None, "policy_revision": "policy-1",
        "capabilities": [{
            "capability_id": descriptor.capability_id, "capability_revision": descriptor.revision,
            "descriptor_sha256": descriptor.descriptor_sha256, "schema_sha256": descriptor.schema_sha256,
            "service_operation": descriptor.service_operation, "class": "evidence_read", "effect_mode": "read",
            "scope": {"attached": True}, "data_classes": ["note"], "placement": ["local"],
            "egress": ["local"], "max_calls": 2, "max_result_bytes": 1024,
            "max_result_tokens": 256, "commutative_read": True,
        }],
        "max_provider_steps": 2, "max_tool_calls": 2, "max_effect_proposals": 0,
        "max_parallel_reads": 2, "aggregate_result_bytes": 2048, "aggregate_result_tokens": 512,
        "wall_deadline": now + 20, "expires_at": now + 20,
    }


def _effect_descriptor() -> CanonicalApplicationOperationDescriptor:
    return CanonicalApplicationOperationDescriptor(
        capability_id="effect.note_propose", revision=1,
        label="Propose Note effect", description="Propose a closed Note effect.",
        argument_schema={
            "type": "object", "additionalProperties": False,
            "properties": {"note_id": {"type": "string"}}, "required": ["note_id"],
        },
        service_operation="note.propose", capability_class="effect_proposal", effect_mode="proposal",
        allowed_data_classes=("note",), allowed_placements=("local",), allowed_egress=("local",),
        max_calls=1, max_result_bytes=1024, max_result_tokens=256,
    )


def _effect_lease(descriptor: CanonicalApplicationOperationDescriptor, *, turn: str, now: float) -> dict[str, object]:
    lease = _lease(_descriptor(), turn=turn, now=now)
    lease["owner_intent_receipt_id"] = "owner-intent-1"
    lease["capabilities"] = [{
        "capability_id": descriptor.capability_id, "capability_revision": descriptor.revision,
        "descriptor_sha256": descriptor.descriptor_sha256, "schema_sha256": descriptor.schema_sha256,
        "service_operation": descriptor.service_operation, "class": "effect_proposal", "effect_mode": "proposal",
        "scope": {"attached": True}, "data_classes": ["note"], "placement": ["local"],
        "egress": ["local"], "max_calls": 1, "max_result_bytes": 1024,
        "max_result_tokens": 256, "commutative_read": False,
    }]
    lease["max_tool_calls"] = 1
    lease["max_effect_proposals"] = 1
    lease["max_parallel_reads"] = 0
    lease["aggregate_result_bytes"] = 1024
    lease["aggregate_result_tokens"] = 256
    return lease


def _started(
    db: Database, *, now: list[float], compose_model_steps: bool = False,
    compose_broker: bool = False, descriptor: CanonicalApplicationOperationDescriptor | None = None,
    lease_terms: dict[str, object] | None = None,
) -> tuple[ToolTurnController, str]:
    """Build real DB, kernel parent/bundle and optional production seams."""
    descriptor = descriptor or _descriptor()
    _profile(db, "tool-parent-model", claims=("language", _result_claim("ask.answer")))
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "assign-tool-parent", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "ask.answer"},
        "entries": [{"profile_id": "tool-parent-model", "profile_revision": 1}],
    })
    broker = _configure(db)
    adoption = RoutedInferenceCoordinator(db, broker=broker)
    controller = ToolTurnController(
        db, projection=ModelTurnCapabilityProjection([descriptor]), clock=lambda: now[0],
        route_plan_service=adoption.plans if compose_model_steps else None,
        fallback_controller=adoption.controller if compose_model_steps else None,
        tool_broker=BrokerToolCallPort(broker) if compose_broker else None,
    )
    bundles = InferenceParentRouteBundleService(broker, adoption)
    started = bundles.start(
        OWNER, command_id="start-tool-parent", parent_kind="tool.turn", definition_ref="tool.turn:foundation",
        definition_revision="1", input_snapshot={"schema": "ToolTurnParentInput@1"}, deadline_at=now[0] + 20,
        routes=[{"key": "model", "capability_id": "ask.answer", "invocation_id": "tool-turn-parent"}],
    )
    bundle = started["bundle"]
    route = bundle["members"][0]
    turn = "turn-1"
    created = controller.start(
        TOOL_TURN_AUTHORITY, command_id="start-tool-turn", turn_id=turn,
        parent_operation_id=started["parent"].operation_id, parent_bundle_id=bundle["id"],
        route_plan_id=route["route_plan_id"], route_plan_sha256=route["route_plan_sha256"],
        lease_terms=lease_terms or _lease(descriptor, turn=turn, now=now[0]),
    )
    assert created["state"] == "reserved"
    return controller, turn


def test_start_replay_and_private_lease_reconstruction_use_real_parent_bundle(tmp_path: Path) -> None:
    now = [time.time()]
    db = Database(tmp_path / "tool-turn.db")
    controller, turn = _started(db, now=now)
    replay = controller.reconstruct(TOOL_TURN_AUTHORITY, turn_id=turn)
    assert replay["lease_sha256"].startswith("sha256:")
    with db._connection() as conn:
        terms = conn.execute("SELECT terms_json FROM turn_capability_leases").fetchone()[0]
        projection = controller._turn_projection(conn, turn)
    assert "nonce" in terms
    assert "nonce" not in str(projection)


def test_reservations_are_exact_replay_safe_and_budget_fenced(tmp_path: Path) -> None:
    now = [time.time()]
    controller, turn = _started(Database(tmp_path / "reservations.db"), now=now)
    first = controller.reserve_tool_call(
        TOOL_TURN_AUTHORITY, command_id="reserve-call-1", turn_id=turn,
        provider_tool_call_id="call-1", capability_id="evidence.note_lookup",
        capability_revision=1, arguments={"note_id": "note-1"},
    )
    replay = controller.reserve_tool_call(
        TOOL_TURN_AUTHORITY, command_id="reserve-call-2", turn_id=turn,
        provider_tool_call_id="call-1", capability_id="evidence.note_lookup",
        capability_revision=1, arguments={"note_id": "note-1"},
    )
    assert replay["id"] == first["id"] and replay["replayed"] is True
    with pytest.raises(ToolTurnRefused) as changed:
        controller.reserve_tool_call(
            TOOL_TURN_AUTHORITY, command_id="reserve-call-changed", turn_id=turn,
            provider_tool_call_id="call-1", capability_id="evidence.note_lookup",
            capability_revision=1, arguments={"note_id": "other"},
        )
    assert changed.value.code == "provider_tool_call_replay_changed"
    controller.reserve_tool_call(
        TOOL_TURN_AUTHORITY, command_id="reserve-call-3", turn_id=turn,
        provider_tool_call_id="call-2", capability_id="evidence.note_lookup",
        capability_revision=1, arguments={"note_id": "note-2"},
    )
    with pytest.raises(ToolTurnRefused) as exhausted:
        controller.reserve_tool_call(
            TOOL_TURN_AUTHORITY, command_id="reserve-call-4", turn_id=turn,
            provider_tool_call_id="call-3", capability_id="evidence.note_lookup",
            capability_revision=1, arguments={"note_id": "note-3"},
        )
    assert exhausted.value.code == "tool_call_budget_exhausted"


def test_expiry_and_stop_terminalize_before_any_later_reservation(tmp_path: Path) -> None:
    now = [time.time()]
    controller, turn = _started(Database(tmp_path / "expiry.db"), now=now)
    now[0] += 20
    with pytest.raises(ToolTurnRefused) as expired:
        controller.reserve_model_step(
            TOOL_TURN_AUTHORITY, command_id="late-step", turn_id=turn,
            operation_request_plan_id="plan-1", operation_request_plan_sha256="sha256:" + "1" * 64,
            request_material_ref="material-1",
        )
    assert expired.value.code == "lease_expired"

    now = [time.time()]
    controller, turn = _started(Database(tmp_path / "stop.db"), now=now)
    stopped = controller.request_stop(
        TOOL_TURN_AUTHORITY, command_id="stop-1", turn_id=turn, provenance_ref="owner-stop"
    )
    assert stopped["state"] == "stopped"
    with pytest.raises(ToolTurnRefused) as fenced:
        controller.reserve_model_step(
            TOOL_TURN_AUTHORITY, command_id="after-stop", turn_id=turn,
            operation_request_plan_id="plan-1", operation_request_plan_sha256="sha256:" + "1" * 64,
            request_material_ref="material-1",
        )
    assert fenced.value.code == "tool_turn_terminal"


def test_tool_call_admission_uses_real_broker_and_refuses_schema_drift(tmp_path: Path) -> None:
    now = [time.time()]
    db = Database(tmp_path / "tool-admission.db")
    controller, turn = _started(db, now=now, compose_broker=True)
    admitted = controller.admit_tool_call(
        TOOL_TURN_AUTHORITY, command_id="admit-read", turn_id=turn,
        candidate=ToolCallCandidate("provider-read-1", "evidence.note_lookup", {"note_id": "note-1"}),
    )
    assert admitted["state"] == "admitted"
    with db._connection() as conn:
        child = conn.execute("SELECT broker_child_id FROM tool_turn_tool_calls WHERE id=?", (admitted["id"],)).fetchone()
        operation = conn.execute("SELECT principal_identity,name,version FROM kernel_operations WHERE operation_id=?", (child["broker_child_id"],)).fetchone()
    assert tuple(operation) == ("model-turn-tool-service", "tool.call", 1)
    with pytest.raises(ToolTurnRefused) as drift:
        controller.admit_tool_call(
            TOOL_TURN_AUTHORITY, command_id="admit-drift", turn_id=turn,
            candidate=ToolCallCandidate("provider-read-2", "evidence.note_lookup", {"note_id": 7}),
        )
    assert drift.value.code == "tool_call_arguments_schema_invalid"
    with pytest.raises(ToolTurnRefused) as confusable:
        controller.admit_tool_call(
            TOOL_TURN_AUTHORITY, command_id="admit-confusable", turn_id=turn,
            candidate=ToolCallCandidate("provider-read-3", "evidence-note-lookup", {"note_id": "note-1"}),
        )
    assert confusable.value.code == "capability_not_leased"


def test_typed_unavailable_result_is_not_model_failure_or_material(tmp_path: Path) -> None:
    now = [time.time()]
    controller, turn = _started(Database(tmp_path / "typed-outage.db"), now=now, compose_broker=True)
    admitted = controller.admit_tool_call(
        TOOL_TURN_AUTHORITY, command_id="admit-outage", turn_id=turn,
        candidate=ToolCallCandidate("provider-outage", "evidence.note_lookup", {"note_id": "note-1"}),
    )
    settled = controller.settle_tool_call(
        TOOL_TURN_AUTHORITY, command_id="settle-outage", turn_id=turn, tool_call_id=admitted["id"],
        receipt_id="receipt-tool-outage", envelope=ToolResultEnvelope.limitation("unavailable"),
    )
    assert settled["state"] == "unavailable"
    assert controller.reconstruct(TOOL_TURN_AUTHORITY, turn_id=turn)["state"] == "tool_receipted"


def test_replay_changed_arguments_refuses_before_second_broker_child(tmp_path: Path) -> None:
    now = [time.time()]
    db = Database(tmp_path / "changed-call.db")
    controller, turn = _started(db, now=now, compose_broker=True)
    controller.admit_tool_call(
        TOOL_TURN_AUTHORITY, command_id="admit-original", turn_id=turn,
        candidate=ToolCallCandidate("same-provider-call", "evidence.note_lookup", {"note_id": "note-1"}),
    )
    with pytest.raises(ToolTurnRefused) as changed:
        controller.admit_tool_call(
            TOOL_TURN_AUTHORITY, command_id="admit-changed", turn_id=turn,
            candidate=ToolCallCandidate("same-provider-call", "evidence.note_lookup", {"note_id": "note-2"}),
        )
    assert changed.value.code == "provider_tool_call_replay_changed"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='tool.call'").fetchone()[0] == 1


def test_effect_receipt_adopts_once_and_unknown_completion_terminalizes(tmp_path: Path) -> None:
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.tool_turn_controller import MODEL_TURN_TOOL_PRINCIPAL

    now = [time.time()]
    descriptor = _effect_descriptor()
    db = Database(tmp_path / "effect-adoption.db")
    controller, turn = _started(
        db, now=now, compose_broker=True, descriptor=descriptor,
        lease_terms=_effect_lease(descriptor, turn="turn-1", now=now[0]),
    )
    admitted = controller.admit_tool_call(
        TOOL_TURN_AUTHORITY, command_id="admit-effect", turn_id=turn,
        candidate=ToolCallCandidate("provider-effect", descriptor.capability_id, {"note_id": "note-1"}),
    )
    with db._connection() as conn:
        operation = conn.execute(
            "SELECT operation_id,revision,native_id FROM kernel_operations WHERE operation_id=(SELECT broker_child_id FROM tool_turn_tool_calls WHERE id=?)",
            (admitted["id"],),
        ).fetchone()
    broker = _configure(db)
    approved = broker.decide(operation["operation_id"], "approve", operation["revision"], MODEL_TURN_TOOL_PRINCIPAL)
    node = Principal(PrincipalKind.NODE, "model-turn")
    assert broker.claim(node, operation["native_id"])["operations"][0]["operation_id"] == operation["operation_id"]
    broker.receipt(operation["operation_id"], "succeeded", "effect:note-1", node)
    adopted = controller.reconcile_effect_child(TOOL_TURN_AUTHORITY, turn_id=turn, tool_call_id=admitted["id"])
    assert adopted["state"] == "adopted"
    assert controller.reconcile_effect_child(TOOL_TURN_AUTHORITY, turn_id=turn, tool_call_id=admitted["id"])["replayed"] is True
    with db._connection() as conn:
        effect = conn.execute("SELECT state,adopted_receipt_id FROM tool_turn_effect_children").fetchone()
    assert effect["state"] == "adopted" and effect["adopted_receipt_id"]

    unknown_db = Database(tmp_path / "effect-unknown.db")
    unknown, unknown_turn = _started(
        unknown_db, now=now, compose_broker=True, descriptor=descriptor,
        lease_terms=_effect_lease(descriptor, turn="turn-1", now=now[0]),
    )
    pending = unknown.admit_tool_call(
        TOOL_TURN_AUTHORITY, command_id="admit-unknown-effect", turn_id=unknown_turn,
        candidate=ToolCallCandidate("provider-effect-unknown", descriptor.capability_id, {"note_id": "note-2"}),
    )
    assert unknown.reconcile_effect_child(
        TOOL_TURN_AUTHORITY, turn_id=unknown_turn, tool_call_id=pending["id"]
    )["state"] == "indeterminate"
    assert unknown.reconstruct(TOOL_TURN_AUTHORITY, turn_id=unknown_turn)["state"] == "indeterminate"
