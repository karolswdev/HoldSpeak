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
    TOOL_TURN_AUTHORITY,
    ToolTurnController,
    ToolTurnRefused,
)
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


def _started(db: Database, *, now: list[float]) -> tuple[ToolTurnController, str]:
    """Build a real kernel parent + bundle, then freeze the private turn beside it."""
    descriptor = _descriptor()
    controller = ToolTurnController(
        db, projection=ModelTurnCapabilityProjection([descriptor]), clock=lambda: now[0]
    )
    _profile(db, "tool-parent-model", claims=("language", _result_claim("ask.answer")))
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "assign-tool-parent", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "ask.answer"},
        "entries": [{"profile_id": "tool-parent-model", "profile_revision": 1}],
    })
    broker = _configure(db)
    adoption = RoutedInferenceCoordinator(db, broker=broker)
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
        lease_terms=_lease(descriptor, turn=turn, now=now[0]),
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
