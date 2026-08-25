"""HS-143-09 A3 — every model step freezes a new private route request."""
from __future__ import annotations

import hashlib
import time
from pathlib import Path

from holdspeak.db import Database
from holdspeak.inference_capabilities import process_inference_capability_registry
from holdspeak.kernel.runtime import _configure
from holdspeak.services.inference_adoption_service import RoutedInferenceCoordinator
from holdspeak.services.tool_turn_controller import TOOL_TURN_AUTHORITY
from tests.unit.test_phase143_tool_turn_controller import _started


def _stage_step_material(db: Database, *, turn_id: str, command_id: str, reference: str) -> None:
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
        payload={"question": "Frozen MODEL_TURN material", "tool_results": []},
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
