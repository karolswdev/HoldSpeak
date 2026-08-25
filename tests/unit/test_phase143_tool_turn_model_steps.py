"""HS-143-09 A3 — every model step freezes a new private route request."""
from __future__ import annotations

import hashlib
import time
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.kernel.provider_signals import ProviderKnownNoGenerationTransient
from holdspeak.inference_capabilities import process_inference_capability_registry
from holdspeak.kernel.runtime import _configure
from holdspeak.services.inference_adoption_service import RoutedInferenceCoordinator
from holdspeak.services.tool_model_adapter import (
    DeterministicToolModelAdapter,
    DeterministicToolModelTransport,
)
from holdspeak.services.tool_turn_controller import TOOL_TURN_AUTHORITY, ToolTurnRefused
from tests.unit.test_phase143_tool_turn_controller import _started


def _stage_step_material(
    db: Database, *, turn_id: str, command_id: str, reference: str,
    tool_results: list[object] | None = None,
) -> None:
    """Use the real production evidence store, not a model-plan test double."""
    material_id = hashlib.sha256(f"{turn_id}:{command_id}".encode("utf-8")).hexdigest()[:32]
    capability = process_inference_capability_registry().require("ask.answer")
    adoption = RoutedInferenceCoordinator(db, broker=_configure(db))
    adoption.evidence.stage(
        planning_reference=reference,
        capability_id=capability.id,
        operation_id=f"tool-step-{material_id}",
        contract=capability.operation_contract.name,
        contract_revision=str(capability.operation_contract.version),
        payload={"question": "Frozen MODEL_TURN material", "tool_results": tool_results or []},
        reserved_output_tokens=32,
    )


def test_each_reserved_step_freezes_new_plan_and_one_fallback_execution(tmp_path: Path) -> None:
    now = [time.time()]
    db = Database(tmp_path / "model-steps.db")
    controller, turn = _started(db, now=now, compose_model_steps=True)
    _stage_step_material(db, turn_id=turn, command_id="plan-step-one", reference="step-material-one")
    first = controller.plan_model_step(
        TOOL_TURN_AUTHORITY, command_id="plan-step-one", turn_id=turn,
        planning_reference="step-material-one",
    )
    _stage_step_material(db, turn_id=turn, command_id="plan-step-two", reference="step-material-two")
    second = controller.plan_model_step(
        TOOL_TURN_AUTHORITY, command_id="plan-step-two", turn_id=turn,
        planning_reference="step-material-two",
    )

    assert first["ordinal"] == 1 and second["ordinal"] == 2
    assert first["operation_request_plan_sha256"] != second["operation_request_plan_sha256"]
    assert first["route_execution_id"] and second["route_execution_id"]
    with db._connection() as conn:
        steps = conn.execute(
            "SELECT * FROM tool_turn_model_steps WHERE turn_id=? ORDER BY ordinal", (turn,)
        ).fetchall()
        executions = conn.execute(
            "SELECT operation_plan_id FROM inference_route_executions ORDER BY operation_plan_id"
        ).fetchall()
        attempts = conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0]
        turn_row = conn.execute("SELECT route_plan_sha256,lease_sha256 FROM tool_turns WHERE turn_id=?", (turn,)).fetchone()
    assert len(steps) == 2
    assert all(row["lease_sha256"] == turn_row["lease_sha256"] for row in steps)
    assert {row["operation_plan_id"] for row in executions} == {row["operation_request_plan_id"] for row in steps}
    # A3 starts exactly one physical-attempt authority per step, but it never
    # lets planning manufacture an InferenceRunner child before that controller
    # reserves one.
    assert attempts == 0


def test_model_step_replay_returns_same_execution_without_refreezing(tmp_path: Path) -> None:
    now = [time.time()]
    db = Database(tmp_path / "model-step-replay.db")
    controller, turn = _started(db, now=now, compose_model_steps=True)
    _stage_step_material(db, turn_id=turn, command_id="plan-replay", reference="step-material-replay")
    first = controller.plan_model_step(
        TOOL_TURN_AUTHORITY, command_id="plan-replay", turn_id=turn,
        planning_reference="step-material-replay",
    )
    replay = controller.plan_model_step(
        TOOL_TURN_AUTHORITY, command_id="plan-replay", turn_id=turn,
        planning_reference="step-material-replay",
    )
    assert replay["replayed"] is True
    assert replay["id"] == first["id"]
    assert replay["route_execution_id"] == first["route_execution_id"]
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM tool_turn_model_steps WHERE turn_id=?", (turn,)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM inference_route_executions").fetchone()[0] == 1


def test_reference_adapter_uses_one_real_model_child_and_receipt(tmp_path: Path) -> None:
    """A5: the reference wire fake cannot bypass Runner/admission/receipt truth."""
    now = [time.time()]
    db = Database(tmp_path / "reference-tool-model.db")
    controller, turn = _started(db, now=now, compose_model_execution=True)
    _stage_step_material(db, turn_id=turn, command_id="execute-reference", reference="reference-material")
    step = controller.plan_model_step(
        TOOL_TURN_AUTHORITY, command_id="execute-reference", turn_id=turn,
        planning_reference="reference-material",
    )
    broker = _configure(db)
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: object()
    transport = DeterministicToolModelTransport({
        "schema": "DeterministicToolModelResponse@1",
        "candidate": {"kind": "answer", "answer": {"output": "one admitted answer"}},
    })

    outcome = controller.execute_model_step(
        TOOL_TURN_AUTHORITY, command_id="execute-reference", turn_id=turn,
        model_step_id=step["id"], model_adapter=DeterministicToolModelAdapter(),
        provider_transport=transport,
    )

    assert outcome["candidate"]["kind"] == "answer"
    assert transport.dispatch_count == 1
    assert transport.requests[0]["request"] == {
        "question": "Frozen MODEL_TURN material", "tool_results": []
    }
    with db._connection() as conn:
        children = conn.execute(
            "SELECT operation_id FROM kernel_operations WHERE name='inference.invoke'"
        ).fetchall()
        receipts = conn.execute(
            "SELECT receipt_id FROM kernel_receipts WHERE operation_id=?", (children[0]["operation_id"],)
        ).fetchall()
        settled = conn.execute(
            "SELECT state,child_receipt_id FROM tool_turn_model_steps WHERE id=?", (step["id"],)
        ).fetchone()
    assert len(children) == len(receipts) == 1
    assert settled["state"] == "receipted" and settled["child_receipt_id"]


def test_stopped_planned_step_refuses_pre_dispatch_with_zero_runner_children(tmp_path: Path) -> None:
    """A5: stop wins before the adapter can render or mint a Runner child."""
    now = [time.time()]
    db = Database(tmp_path / "stopped-tool-model.db")
    controller, turn = _started(db, now=now, compose_model_execution=True)
    _stage_step_material(db, turn_id=turn, command_id="stopped-step", reference="stopped-material")
    step = controller.plan_model_step(
        TOOL_TURN_AUTHORITY, command_id="stopped-step", turn_id=turn,
        planning_reference="stopped-material",
    )
    controller.request_stop(
        TOOL_TURN_AUTHORITY, command_id="stop-before-adapter", turn_id=turn,
        provenance_ref="owner-stop",
    )
    transport = DeterministicToolModelTransport({
        "schema": "DeterministicToolModelResponse@1",
        "candidate": {"kind": "answer", "answer": {"output": "must not run"}},
    })

    with pytest.raises(ToolTurnRefused) as refused:
        controller.execute_model_step(
            TOOL_TURN_AUTHORITY, command_id="stopped-execute", turn_id=turn,
            model_step_id=step["id"], model_adapter=DeterministicToolModelAdapter(),
            provider_transport=transport,
        )
    assert getattr(refused.value, "code", "") == "tool_turn_terminal"
    with db._connection() as conn:
        children = conn.execute(
            "SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'"
        ).fetchone()[0]
    assert children == transport.dispatch_count == 0


class _RetryThenAnswerTransport:
    """Reference wire transport: one known-no-generation retry, then one answer."""

    def __init__(self) -> None:
        self.requests: list[dict[str, object]] = []
        self.dispatch_count = 0

    def dispatch(self, _engine: object, request: dict[str, object], _cancelled: object) -> dict[str, object]:
        self.dispatch_count += 1
        self.requests.append(request)
        if self.dispatch_count == 1:
            raise ProviderKnownNoGenerationTransient()
        return {
            "schema": "DeterministicToolModelResponse@1",
            "candidate": {"kind": "answer", "answer": {"output": "retry winner"}},
        }

    def cancel(self) -> str:
        return "cancelled"


def test_frozen_retry_policy_has_n_distinct_admitted_children_one_winner(tmp_path: Path) -> None:
    """A5: N is physical receipts, never an adapter-internal loop or replacement."""
    now = [time.time()]
    db = Database(tmp_path / "retry-tool-model.db")
    controller, turn = _started(db, now=now, compose_model_execution=True)
    _stage_step_material(db, turn_id=turn, command_id="retry-step", reference="retry-material")
    step = controller.plan_model_step(
        TOOL_TURN_AUTHORITY, command_id="retry-step", turn_id=turn,
        planning_reference="retry-material",
    )
    broker = _configure(db)
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: object()
    transport = _RetryThenAnswerTransport()

    outcome = controller.execute_model_step(
        TOOL_TURN_AUTHORITY, command_id="retry-step", turn_id=turn,
        model_step_id=step["id"], model_adapter=DeterministicToolModelAdapter(),
        provider_transport=transport,
    )

    assert outcome["outcome"] == "succeeded"
    with db._connection() as conn:
        attempts = conn.execute(
            """SELECT child_operation_id,child_receipt_sha256,outcome
                 FROM inference_route_attempts
                WHERE execution_id=? ORDER BY physical_attempt_ordinal""",
            (step["route_execution_id"],),
        ).fetchall()
        winner = conn.execute(
            "SELECT winning_attempt_id FROM inference_route_executions WHERE id=?",
            (step["route_execution_id"],),
        ).fetchone()["winning_attempt_id"]
        winner_child = conn.execute(
            "SELECT child_operation_id FROM inference_route_attempts WHERE id=?", (winner,)
        ).fetchone()["child_operation_id"]
    assert transport.dispatch_count == len(attempts) == 2
    assert len({row["child_operation_id"] for row in attempts}) == 2
    assert all(row["child_receipt_sha256"] for row in attempts)
    assert attempts[-1]["outcome"] == "succeeded" and winner_child == attempts[-1]["child_operation_id"]
