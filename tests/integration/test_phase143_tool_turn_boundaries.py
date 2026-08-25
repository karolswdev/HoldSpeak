"""HS-143-09 B2 — real durable ToolTurn boundaries survive reconstruction."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.tool_capability_service import (
    ModelTurnCapabilityProjection,
    ToolCallCandidate,
    ToolQualification,
    ToolResultEnvelope,
    sha256,
)
from holdspeak.services.tool_model_adapter import (
    DeterministicToolModelAdapter,
    DeterministicToolModelTransport,
)
from holdspeak.services.tool_turn_controller import (
    BrokerToolCallPort,
    MODEL_TURN_TOOL_PRINCIPAL,
    TOOL_TURN_AUTHORITY,
    ToolTurnController,
    ToolTurnRefused,
)
from holdspeak.services.tool_turn_service import ToolTurnFoundationService
from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim
from tests.unit.test_phase143_tool_turn_controller import (
    _descriptor,
    _effect_descriptor,
    _effect_lease,
    _lease,
    _started,
)


def _restart(db: Database, *, descriptor, now: list[float]) -> ToolTurnController:
    """A new production controller object reads no mutable owner route state."""
    return ToolTurnController(
        db, projection=ModelTurnCapabilityProjection([descriptor]), clock=lambda: now[0],
        tool_broker=BrokerToolCallPort(_configure(db)),
    )


def test_restart_adopts_known_effect_receipt_never_reexecutes_it(tmp_path: Path) -> None:
    now = [time.time()]
    descriptor = _effect_descriptor()
    db = Database(tmp_path / "known-effect-restart.db")
    controller, turn = _started(
        db, now=now, compose_broker=True, descriptor=descriptor,
        lease_terms=_effect_lease(descriptor, turn="turn-1", now=now[0]),
    )
    call = controller.admit_tool_call(
        TOOL_TURN_AUTHORITY, command_id="boundary-effect", turn_id=turn,
        candidate=ToolCallCandidate("boundary-effect-call", descriptor.capability_id, {"note_id": "note-1"}),
    )
    broker = _configure(db)
    with db._connection() as conn:
        operation = conn.execute(
            "SELECT operation_id,revision,native_id FROM kernel_operations WHERE operation_id=(SELECT broker_child_id FROM tool_turn_tool_calls WHERE id=?)",
            (call["id"],),
        ).fetchone()
    broker.decide(operation["operation_id"], "approve", operation["revision"], MODEL_TURN_TOOL_PRINCIPAL)
    node = Principal(PrincipalKind.NODE, "model-turn")
    broker.claim(node, operation["native_id"])
    broker.receipt(operation["operation_id"], "succeeded", "effect:note-1", node)

    restarted = _restart(db, descriptor=descriptor, now=now)
    assert restarted.reconstruct(TOOL_TURN_AUTHORITY, turn_id=turn)["state"] == "tool_receipted"
    adopted = restarted.reconcile_effect_child(TOOL_TURN_AUTHORITY, turn_id=turn, tool_call_id=call["id"])
    assert adopted["state"] == "adopted"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='tool.call'").fetchone()[0] == 1


def test_restart_unknown_effect_completion_elects_terminal_without_model_egress(tmp_path: Path) -> None:
    now = [time.time()]
    descriptor = _effect_descriptor()
    db = Database(tmp_path / "unknown-effect-restart.db")
    controller, turn = _started(
        db, now=now, compose_broker=True, descriptor=descriptor,
        lease_terms=_effect_lease(descriptor, turn="turn-1", now=now[0]),
    )
    call = controller.admit_tool_call(
        TOOL_TURN_AUTHORITY, command_id="boundary-unknown", turn_id=turn,
        candidate=ToolCallCandidate("boundary-unknown-call", descriptor.capability_id, {"note_id": "note-2"}),
    )
    restarted = _restart(db, descriptor=descriptor, now=now)
    terminal = restarted.reconcile_effect_child(TOOL_TURN_AUTHORITY, turn_id=turn, tool_call_id=call["id"])
    assert terminal["state"] == "indeterminate"
    assert restarted.reconstruct(TOOL_TURN_AUTHORITY, turn_id=turn)["terminal_code"] == "effect_indeterminate"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0] == 0
        assert conn.execute("SELECT state FROM tool_turn_effect_children").fetchone()[0] == "indeterminate"


def _qualified_tool_manifest() -> dict[str, object]:
    qualification = ToolQualification("qualified", 1, "hs143-tool-eval-r1", "openai")
    material: dict[str, object] = {
        "revision": "integration-tool-v2",
        "claims": ["language", _result_claim("agent.tool_turn"), "tool_turn"],
        "tool_qualification": qualification.to_dict(),
    }
    return {**material, "sha256": sha256(material)}


def _internal_turn(db: Database, *, now: list[float], max_provider_steps: int = 2) -> tuple[ToolTurnFoundationService, dict[str, object]]:
    broker = _configure(db)
    service = ToolTurnFoundationService(
        broker, projection=ModelTurnCapabilityProjection([_descriptor()]), clock=lambda: now[0],
    )
    _profile(
        db, "tool-model",
        claims=("language", _result_claim("agent.tool_turn"), "tool_turn"),
        capability_manifest=_qualified_tool_manifest(),
    )
    InferenceAssignmentService(db, tool_capability_foundation=service._foundation).set_assignment(OWNER, {
        "command_id": "assign-internal-tool-turn", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "agent.tool_turn"},
        "entries": [{"profile_id": "tool-model", "profile_revision": 1}],
    })
    lease = _lease(_descriptor(), turn="internal-turn", now=now[0])
    lease["max_provider_steps"] = max_provider_steps
    started = service.start(
        OWNER,
        command_id="start-internal-tool-turn",
        turn_id="internal-turn",
        lease_terms=lease,
        input_snapshot={"schema": "ToolTurnFoundationInput@1"},
        deadline_at=now[0] + 20,
    )
    assert started["status"] == "started"
    return service, started


def _settle_read(db: Database, service: ToolTurnFoundationService, *, call: dict[str, object], result: dict[str, object], command: str) -> None:
    broker = _configure(db)
    with db._connection() as conn:
        operation = conn.execute(
            "SELECT operation_id,revision,native_id FROM kernel_operations WHERE operation_id=(SELECT broker_child_id FROM tool_turn_tool_calls WHERE id=?)",
            (call["id"],),
        ).fetchone()
    broker.decide(operation["operation_id"], "approve", operation["revision"], MODEL_TURN_TOOL_PRINCIPAL)
    node = Principal(PrincipalKind.NODE, "model-turn")
    broker.claim(node, operation["native_id"])
    receipt = broker.receipt(operation["operation_id"], "succeeded", f"read:{call['id']}", node)
    service.controller.settle_tool_call(
        TOOL_TURN_AUTHORITY,
        command_id=command,
        turn_id="internal-turn",
        tool_call_id=str(call["id"]),
        receipt_id=str(receipt["receipt_id"]),
        envelope=ToolResultEnvelope.available(result),
        result_material=result,
    )


def test_internal_foundation_composes_real_model_tool_model_turn_with_every_receipt(tmp_path: Path) -> None:
    """B2/AC5: two Runner children and one Broker child form one truthful turn."""
    now = [time.time()]
    db = Database(tmp_path / "complete-real-turn.db")
    service, started = _internal_turn(db, now=now)
    broker = _configure(db)
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: object()

    first = service.stage_and_plan_model_step(
        command_id="first-model", turn_id="internal-turn", planning_reference="first-material",
        payload={"question": "Find the attached Note", "tool_results": []},
    )
    requested = service.execute_model_step(
        command_id="first-model", turn_id="internal-turn", model_step_id=first["id"],
        model_adapter=DeterministicToolModelAdapter(),
        provider_transport=DeterministicToolModelTransport({
            "schema": "DeterministicToolModelResponse@1",
            "candidate": {"kind": "tool_call", "provider_tool_call_id": "lookup-1",
                          "provider_call_ordinal": 1, "capability_id": "evidence.note_lookup",
                          "arguments": {"note_id": "note-1"}},
        }),
    )
    assert requested["model_step"]["state"] == "receipted"
    assert requested["tool_call"]["state"] == "admitted"
    assert service.controller.reconstruct(TOOL_TURN_AUTHORITY, turn_id="internal-turn")["state"] == "tool_admitted"

    _settle_read(
        db, service, call=requested["tool_call"], result={"note_id": "note-1", "body": "Truth"},
        command="settle-lookup-1",
    )
    ordered = service.controller.ordered_tool_results(TOOL_TURN_AUTHORITY, turn_id="internal-turn")
    second = service.stage_and_plan_model_step(
        command_id="second-model", turn_id="internal-turn", planning_reference="second-material",
        payload={"question": "Answer from the receipt", "tool_results": ordered["tool_results"]},
    )
    answered = service.execute_model_step(
        command_id="second-model", turn_id="internal-turn", model_step_id=second["id"],
        model_adapter=DeterministicToolModelAdapter(),
        provider_transport=DeterministicToolModelTransport({
            "schema": "DeterministicToolModelResponse@1",
            "candidate": {"kind": "answer", "answer": {"summary": "The Note says Truth.", "tool_calls": []}},
        }),
    )

    assert answered["model_step"]["state"] == "receipted"
    receipt = service.controller.receipt(TOOL_TURN_AUTHORITY, turn_id="internal-turn")
    assert receipt["state"] == "result_ready"
    assert [step["receipt_id"] for step in receipt["model_steps"]] and len(receipt["model_steps"]) == 2
    assert len(receipt["tool_calls"]) == 1 and receipt["tool_calls"][0]["receipt_id"]
    assert "nonce" not in str(receipt) and "terms_json" not in str(receipt)
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='tool.call'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM kernel_receipts").fetchone()[0] >= 3
        transitions = conn.execute("SELECT from_state,to_state FROM tool_turn_transitions WHERE turn_id=? ORDER BY ordinal", ("internal-turn",)).fetchall()
    assert ("model_running", "tool_requested") in [tuple(item) for item in transitions]
    assert ("model_running", "result_ready") in [tuple(item) for item in transitions]


def test_model_step_budget_exhaustion_terminalizes_without_second_egress(tmp_path: Path) -> None:
    """B2: the model/tool loop cannot turn a two-step plan into a third child."""
    now = [time.time()]
    db = Database(tmp_path / "model-budget-exhaustion.db")
    service, _started = _internal_turn(db, now=now, max_provider_steps=1)
    broker = _configure(db)
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: object()
    first = service.stage_and_plan_model_step(
        command_id="budget-first", turn_id="internal-turn", planning_reference="budget-first-material",
        payload={"question": "No tool answer", "tool_results": []},
    )
    service.execute_model_step(
        command_id="budget-first", turn_id="internal-turn", model_step_id=first["id"],
        model_adapter=DeterministicToolModelAdapter(),
        provider_transport=DeterministicToolModelTransport({
            "schema": "DeterministicToolModelResponse@1",
            "candidate": {"kind": "tool_call", "provider_tool_call_id": "budget-lookup",
                          "provider_call_ordinal": 1, "capability_id": "evidence.note_lookup",
                          "arguments": {"note_id": "note-1"}},
        }),
    )
    # The configured one model step has been durably receipted; a continuation
    # cannot reserve a new exact request or create a second Runner child.
    with pytest.raises(ToolTurnRefused) as exhausted:
        service.stage_and_plan_model_step(
            command_id="budget-second", turn_id="internal-turn", planning_reference="budget-second-material",
            payload={"question": "Must not dispatch", "tool_results": []},
        )
    assert exhausted.value.code == "model_step_budget_exhausted"
    terminal = service.controller.reconstruct(TOOL_TURN_AUTHORITY, turn_id="internal-turn")
    assert terminal["state"] == "failed" and terminal["terminal_code"] == "model_step_budget_exhausted"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == 1


def test_stop_fences_model_and_tool_boundaries_before_later_egress(tmp_path: Path) -> None:
    """B2: parent/turn Stop wins at both the planned-model and tool boundaries."""
    now = [time.time()]
    db = Database(tmp_path / "stop-every-boundary.db")
    service, started = _internal_turn(db, now=now)
    broker = _configure(db)
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: object()
    planned = service.stage_and_plan_model_step(
        command_id="stop-model", turn_id="internal-turn", planning_reference="stop-model-material",
        payload={"question": "Must not run", "tool_results": []},
    )
    service.request_stop(
        OWNER, command_id="stop-model", turn_id="internal-turn",
        bundle_id=started["bundle"]["id"], provenance_ref="owner-stop-model",
    )
    model_wire = DeterministicToolModelTransport({
        "schema": "DeterministicToolModelResponse@1",
        "candidate": {"kind": "answer", "answer": {"output": "must not run"}},
    })
    with pytest.raises(ToolTurnRefused) as model_fenced:
        service.execute_model_step(
            command_id="stop-model-execute", turn_id="internal-turn", model_step_id=planned["id"],
            model_adapter=DeterministicToolModelAdapter(), provider_transport=model_wire,
        )
    assert model_fenced.value.code == "tool_turn_terminal"
    assert model_wire.dispatch_count == 0

    # A distinct turn reaches the separately admitted tool boundary; Stop then
    # refuses continuation and no second model child can be created.
    db_tool = Database(tmp_path / "stop-tool-boundary.db")
    service_tool, started_tool = _internal_turn(db_tool, now=now)
    broker_tool = _configure(db_tool)
    broker_tool.inference_runner._engine_factory = lambda _revision, **_kwargs: object()
    first = service_tool.stage_and_plan_model_step(
        command_id="stop-tool-first", turn_id="internal-turn", planning_reference="stop-tool-first-material",
        payload={"question": "Call read", "tool_results": []},
    )
    requested = service_tool.execute_model_step(
        command_id="stop-tool-first", turn_id="internal-turn", model_step_id=first["id"],
        model_adapter=DeterministicToolModelAdapter(),
        provider_transport=DeterministicToolModelTransport({
            "schema": "DeterministicToolModelResponse@1",
            "candidate": {"kind": "tool_call", "provider_tool_call_id": "stop-tool-call",
                          "provider_call_ordinal": 1, "capability_id": "evidence.note_lookup",
                          "arguments": {"note_id": "note-1"}},
        }),
    )
    assert requested["tool_call"]["state"] == "admitted"
    service_tool.request_stop(
        OWNER, command_id="stop-tool", turn_id="internal-turn",
        bundle_id=started_tool["bundle"]["id"], provenance_ref="owner-stop-tool",
    )
    with pytest.raises(ToolTurnRefused) as tool_fenced:
        service_tool.controller.settle_tool_call(
            TOOL_TURN_AUTHORITY, command_id="late-tool-settlement", turn_id="internal-turn",
            tool_call_id=requested["tool_call"]["id"], receipt_id="late-receipt",
            envelope=ToolResultEnvelope.limitation("unavailable"),
        )
    assert tool_fenced.value.code == "tool_turn_terminal"
    with db_tool._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == 1
