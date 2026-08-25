"""HS-143-09 B2 — real durable ToolTurn boundaries survive reconstruction."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.kernel.provider_signals import ProviderPermanentNoGeneration
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


def _qualified_tool_manifest(*, palette: int = 1) -> dict[str, object]:
    qualification = ToolQualification("qualified", palette, "hs143-tool-eval-r1", "openai")
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


class _FailFirstModelWire:
    """Reference wire-format transport; only the first provider result fails."""

    def __init__(self, response: dict[str, object]) -> None:
        self._response = response
        self.requests: list[dict[str, object]] = []
        self.dispatch_count = 0

    def dispatch(self, _engine: object, request: dict[str, object], _cancellation: object) -> dict[str, object]:
        self.dispatch_count += 1
        self.requests.append(dict(request))
        if self.dispatch_count == 1:
            raise ProviderPermanentNoGeneration()
        return dict(self._response)

    def cancel(self) -> str:
        return "cancelled"


def _b4_full_turn(db: Database, *, now: list[float]) -> tuple[ToolTurnFoundationService, dict[str, object]]:
    """Build a real broker/service turn with two frozen qualified model legs."""
    broker = _configure(db)
    read, effect = _descriptor(), _effect_descriptor()
    service = ToolTurnFoundationService(
        broker, projection=ModelTurnCapabilityProjection([read, effect]), clock=lambda: now[0],
    )
    for profile_id in ("b4-tool-model-primary", "b4-tool-model-fallback"):
        _profile(
            db, profile_id,
            claims=("language", _result_claim("agent.tool_turn"), "tool_turn"),
            capability_manifest=_qualified_tool_manifest(palette=4),
        )
    InferenceAssignmentService(db, tool_capability_foundation=service._foundation).set_assignment(OWNER, {
        "command_id": "b4-qualified-chain", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "agent.tool_turn"},
        "entries": [
            {"profile_id": "b4-tool-model-primary", "profile_revision": 1},
            {"profile_id": "b4-tool-model-fallback", "profile_revision": 1},
        ],
    })
    read_lease = _lease(read, turn="b4-turn", now=now[0])
    effect_lease = _effect_lease(effect, turn="b4-turn", now=now[0])
    lease = dict(read_lease)
    lease["owner_intent_receipt_id"] = "b4-owner-intent"
    lease["capabilities"] = [*read_lease["capabilities"], *effect_lease["capabilities"]]
    lease["max_provider_steps"] = 4
    lease["max_tool_calls"] = 2
    lease["max_effect_proposals"] = 1
    lease["max_parallel_reads"] = 2
    lease["aggregate_result_bytes"] = 2048
    lease["aggregate_result_tokens"] = 512
    started = service.start(
        OWNER, command_id="b4-start", turn_id="b4-turn", lease_terms=lease,
        input_snapshot={"schema": "ToolTurnFoundationInput@1"}, deadline_at=now[0] + 20,
    )
    assert started["status"] == "started"
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: object()
    return service, started


def _b4_step(
    service: ToolTurnFoundationService,
    *,
    command: str,
    payload: dict[str, object],
    response: dict[str, object],
    transport: object | None = None,
) -> dict[str, object]:
    step = service.stage_and_plan_model_step(
        command_id=command, turn_id="b4-turn", planning_reference=f"{command}-material", payload=payload,
    )
    return service.execute_model_step(
        command_id=command, turn_id="b4-turn", model_step_id=step["id"],
        model_adapter=DeterministicToolModelAdapter(),
        provider_transport=DeterministicToolModelTransport(response) if transport is None else transport,
    )


def _b4_close_child(db: Database, service: ToolTurnFoundationService, *, call: dict[str, object], command: str, envelope: ToolResultEnvelope, result: dict[str, object] | None = None) -> None:
    broker = _configure(db)
    with db._connection() as conn:
        operation = conn.execute(
            "SELECT operation_id,revision,native_id FROM kernel_operations WHERE operation_id=(SELECT broker_child_id FROM tool_turn_tool_calls WHERE id=?)",
            (call["id"],),
        ).fetchone()
    broker.decide(operation["operation_id"], "approve", operation["revision"], MODEL_TURN_TOOL_PRINCIPAL)
    node = Principal(PrincipalKind.NODE, "model-turn")
    broker.claim(node, operation["native_id"])
    receipt = broker.receipt(operation["operation_id"], "succeeded", f"b4:{call['id']}", node)
    service.controller.settle_tool_call(
        TOOL_TURN_AUTHORITY, command_id=command, turn_id="b4-turn", tool_call_id=str(call["id"]),
        receipt_id=str(receipt["receipt_id"]), envelope=envelope, result_material=result,
    )


def _b4_step_for_internal_turn(service: ToolTurnFoundationService, *, command: str) -> dict[str, object]:
    step = service.stage_and_plan_model_step(
        command_id=command, turn_id="internal-turn", planning_reference=f"{command}-material",
        payload={"question": "call attached Note", "tool_results": []},
    )
    outcome = service.execute_model_step(
        command_id=command, turn_id="internal-turn", model_step_id=step["id"],
        model_adapter=DeterministicToolModelAdapter(),
        provider_transport=DeterministicToolModelTransport({
            "schema": "DeterministicToolModelResponse@1",
            "candidate": {"kind": "tool_call", "provider_tool_call_id": f"{command}-call",
                          "provider_call_ordinal": 1, "capability_id": "evidence.note_lookup",
                          "arguments": {"note_id": "note-1"}},
        }),
    )
    assert outcome["tool_call"] is not None
    return outcome["tool_call"]


def test_b4_ac1_ac2_ac3_ac5_full_turn_discloses_correction_effect_outage_and_qualified_fallback(tmp_path: Path) -> None:
    """B4 AC1/2/3/5: the real broker path stays leased and receipt-complete."""
    now = [time.time()]
    db = Database(tmp_path / "b4-complete-turn.db")
    service, _started = _b4_full_turn(db, now=now)

    # B3 correction: the first, malformed native candidate creates no tool child.
    malformed = _b4_step(
        service, command="b4-malformed", payload={"question": "correct", "tool_results": []},
        response={"schema": "DeterministicToolModelResponse@1", "candidate": {
            "kind": "tool_call", "provider_tool_call_id": "b4-invalid", "provider_call_ordinal": 1,
            "capability_id": "evidence.unknown_lookup", "arguments": {"note_id": "note-1"},
        }},
    )
    assert malformed["tool_call"] is None
    assert malformed["tool_disposition"]["disposition"] == "invalid_tool_call"

    # A proposed effect reaches the real Broker exactly once and its known
    # receipt is adopted before a later model step can see it.
    proposed = _b4_step(
        service, command="b4-effect", payload={"question": "propose", "tool_results": []},
        response={"schema": "DeterministicToolModelResponse@1", "candidate": {
            "kind": "tool_call", "provider_tool_call_id": "b4-effect-call", "provider_call_ordinal": 1,
            "capability_id": "effect.note_propose", "arguments": {"note_id": "note-1"},
        }},
    )
    _b4_close_child(
        db, service, call=proposed["tool_call"], command="b4-settle-effect",
        envelope=ToolResultEnvelope.available({"proposal": "note-1"}), result={"proposal": "note-1"},
    )
    adopted_replay = service.controller.admit_tool_call(
        TOOL_TURN_AUTHORITY, command_id="b4-adopted-effect-replay", turn_id="b4-turn",
        candidate=ToolCallCandidate("b4-effect-call", "effect.note_propose", {"note_id": "note-1"}, 1),
    )
    assert adopted_replay["id"] == proposed["tool_call"]["id"] and adopted_replay["replayed"] is True
    with pytest.raises(ToolTurnRefused, match="receipted_effect_adopted"):
        service.controller.admit_tool_call(
            TOOL_TURN_AUTHORITY, command_id="b4-repeat-effect", turn_id="b4-turn",
            candidate=ToolCallCandidate("b4-repeat-effect", "effect.note_propose", {"note_id": "note-1"}, 3),
        )

    # A read outage remains typed tool evidence. The frozen envelope expressly
    # permits a limited answer, so it can be continuation material but never
    # creates an automatic model/provider retry.
    unavailable = _b4_step(
        service, command="b4-unavailable", payload={"question": "read", "tool_results": []},
        response={"schema": "DeterministicToolModelResponse@1", "candidate": {
            "kind": "tool_call", "provider_tool_call_id": "b4-read-call", "provider_call_ordinal": 2,
            "capability_id": "evidence.note_lookup", "arguments": {"note_id": "note-1"},
        }},
    )
    _b4_close_child(
        db, service, call=unavailable["tool_call"], command="b4-settle-unavailable",
        envelope=ToolResultEnvelope.limitation("unavailable", final_answer_may_name_limitation=True),
    )
    ordered = service.controller.ordered_tool_results(TOOL_TURN_AUTHORITY, turn_id="b4-turn")
    assert [row["provider_call_ordinal"] for row in ordered["tool_results"]] == [1, 2]

    # The final model step has one closed provider failure, then advances through
    # the frozen second *tool-qualified* leg. The only fake is its wire envelope.
    final_wire = _FailFirstModelWire({
        "schema": "DeterministicToolModelResponse@1",
        "candidate": {"kind": "answer", "answer": {"summary": "One proposed effect; Note unavailable.", "tool_calls": []}},
    })
    answered = _b4_step(
        service, command="b4-final", payload={"question": "answer", "tool_results": ordered["tool_results"]},
        response={}, transport=final_wire,
    )
    assert answered["outcome"] == "succeeded" and final_wire.dispatch_count == 2

    receipt = service.controller.receipt(TOOL_TURN_AUTHORITY, turn_id="b4-turn")
    assert receipt["state"] == "result_ready"
    assert [item["exact_tool_used"] for item in receipt["tools_used"]] == [
        "effect.note_propose", "evidence.note_lookup",
    ]
    effect_receipt, outage_receipt = receipt["tool_calls"]
    assert effect_receipt["effect"] == {
        "proposed": True, "executed": True, "state": "adopted",
        "receipt_id": effect_receipt["effect"]["receipt_id"], "disposition": "available",
    }
    assert outage_receipt["disposition"] == "unavailable"
    final_attempts = receipt["model_steps"][-1]["model_attempts"]
    assert [(item["profile_id"], item["purpose"]) for item in final_attempts] == [
        ("b4-tool-model-primary", "primary"), ("b4-tool-model-fallback", "fallback"),
    ]
    assert final_attempts[-1]["fallback_reason"] == "provider_permanent"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == 5
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='tool.call'").fetchone()[0] == 2


def test_b4_ac4_required_tool_without_qualified_profile_refuses_before_any_child(tmp_path: Path) -> None:
    """B4 AC4: construction never turns a missing qualification into egress."""
    now = [time.time()]
    db = Database(tmp_path / "b4-no-qualified-profile.db")
    broker = _configure(db)
    service = ToolTurnFoundationService(
        broker, projection=ModelTurnCapabilityProjection([_descriptor()]), clock=lambda: now[0],
    )
    _profile(db, "b4-plain-model", claims=("language", _result_claim("ask.answer")))
    InferenceAssignmentService(db, tool_capability_foundation=service._foundation).set_assignment(OWNER, {
        "command_id": "b4-plain-chain", "expected_revision": 0,
        "scope": {"kind": "global"}, "entries": [{"profile_id": "b4-plain-model", "profile_revision": 1}],
    })
    refused = service.start(
        OWNER, command_id="b4-no-qualified-start", turn_id="b4-no-qualified-turn",
        lease_terms=_lease(_descriptor(), turn="b4-no-qualified-turn", now=now[0]),
        input_snapshot={"schema": "ToolTurnFoundationInput@1"}, deadline_at=now[0] + 20,
    )
    assert refused["status"] == "refused" and refused["reason_code"] == "tool_required_unavailable"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name IN ('inference.invoke','tool.call')").fetchone()[0] == 0


def test_b4_restart_boundaries_and_stop_races_leave_no_new_egress(tmp_path: Path) -> None:
    """B4: model/tool/effect boundary restarts and both Stop races are truthful."""
    now = [time.time()]
    # Model boundary: simulate process death after the actual Runner child has
    # durably receipted but before ToolTurn adopts its result. Restart preserves
    # the pending boundary truth and never replays/sends a second model request.
    db_model = Database(tmp_path / "b4-model-boundary.db")
    service_model, started_model = _internal_turn(db_model, now=now)
    broker_model = _configure(db_model)
    broker_model.inference_runner._engine_factory = lambda _revision, **_kwargs: object()
    planned = service_model.stage_and_plan_model_step(
        command_id="b4-crash-model", turn_id="internal-turn", planning_reference="b4-crash-model-material",
        payload={"question": "crash after model wire", "tool_results": []},
    )
    real_settle = service_model.controller.settle_model_step

    def crash_after_model_receipt(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise RuntimeError("simulated process crash after model receipt")

    service_model.controller.settle_model_step = crash_after_model_receipt  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="simulated process crash"):
        service_model.execute_model_step(
            command_id="b4-crash-model", turn_id="internal-turn", model_step_id=planned["id"],
            model_adapter=DeterministicToolModelAdapter(),
            provider_transport=DeterministicToolModelTransport({
                "schema": "DeterministicToolModelResponse@1",
                "candidate": {"kind": "answer", "answer": {"summary": "durable but unadopted", "tool_calls": []}},
            }),
        )
    service_model.controller.settle_model_step = real_settle  # type: ignore[method-assign]
    restarted_model = _restart(db_model, descriptor=_descriptor(), now=now)
    assert restarted_model.reconstruct(TOOL_TURN_AUTHORITY, turn_id="internal-turn")["state"] == "model_running"
    with db_model._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == 1
    service_model.request_stop(OWNER, command_id="b4-stop-model", turn_id="internal-turn", bundle_id=started_model["bundle"]["id"], provenance_ref="b4-model-stop")
    model_wire = DeterministicToolModelTransport({"schema": "DeterministicToolModelResponse@1", "candidate": {"kind": "answer", "answer": {"output": "never"}}})
    with pytest.raises(ToolTurnRefused, match="tool_turn_terminal"):
        service_model.execute_model_step(command_id="b4-late-model", turn_id="internal-turn", model_step_id=planned["id"], model_adapter=DeterministicToolModelAdapter(), provider_transport=model_wire)
    assert model_wire.dispatch_count == 0

    # Tool boundary: one actual Broker child is durable, restart neither repeats
    # it nor plans another model step; Stop fences its late settlement.
    db_tool = Database(tmp_path / "b4-tool-boundary.db")
    service_tool, started_tool = _internal_turn(db_tool, now=now)
    broker_tool = _configure(db_tool)
    broker_tool.inference_runner._engine_factory = lambda _revision, **_kwargs: object()
    requested = _b4_step_for_internal_turn(service_tool, command="b4-tool-call")
    restarted_tool = _restart(db_tool, descriptor=_descriptor(), now=now)
    assert restarted_tool.reconstruct(TOOL_TURN_AUTHORITY, turn_id="internal-turn")["state"] == "tool_admitted"
    service_tool.request_stop(OWNER, command_id="b4-stop-tool", turn_id="internal-turn", bundle_id=started_tool["bundle"]["id"], provenance_ref="b4-tool-stop")
    with pytest.raises(ToolTurnRefused, match="tool_turn_terminal"):
        service_tool.controller.settle_tool_call(TOOL_TURN_AUTHORITY, command_id="b4-late-tool", turn_id="internal-turn", tool_call_id=requested["id"], receipt_id="b4-late-receipt", envelope=ToolResultEnvelope.limitation("unavailable"))
    with db_tool._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='tool.call'").fetchone()[0] == 1

    # Effect boundary: an admitted effect with no immutable completion receipt is
    # reconstructed as indeterminate, never re-executed or routed to a model.
    db_effect = Database(tmp_path / "b4-effect-boundary.db")
    effect_descriptor = _effect_descriptor()
    effect_controller, effect_turn = _started(
        db_effect, now=now, compose_broker=True, descriptor=effect_descriptor,
        lease_terms=_effect_lease(effect_descriptor, turn="turn-1", now=now[0]),
    )
    effect_call = effect_controller.admit_tool_call(
        TOOL_TURN_AUTHORITY, command_id="b4-effect-boundary-admit", turn_id=effect_turn,
        candidate=ToolCallCandidate("b4-effect-boundary-call", effect_descriptor.capability_id, {"note_id": "note-1"}),
    )
    restarted_effect = _restart(db_effect, descriptor=effect_descriptor, now=now)
    assert restarted_effect.reconstruct(TOOL_TURN_AUTHORITY, turn_id=effect_turn)["state"] == "indeterminate"
    assert restarted_effect.receipt(TOOL_TURN_AUTHORITY, turn_id=effect_turn)["terminal_code"] == "effect_indeterminate"
    with db_effect._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='tool.call'").fetchone()[0] == 1
        assert conn.execute("SELECT state FROM tool_turn_effect_children WHERE tool_call_id=?", (effect_call["id"],)).fetchone()[0] == "indeterminate"
