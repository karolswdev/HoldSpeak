"""HS-143-10 — a Sequence node survives the admission/execution restart seam."""
from __future__ import annotations

import time
from pathlib import Path

from holdspeak.db import Database
from holdspeak.kernel.prompt_adapter import CanonicalPromptAdapter
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim


OWNER = Principal(PrincipalKind.OWNER, "sequence-restart-owner")


class _Engine:
    active_provider = "restart-provider"
    active_model = "restart-model"

    def run_prompt(self, **_kwargs):
        return "reconstructed"


def test_restart_reconstructs_the_same_frozen_sequence_node_attempt(
    tmp_path: Path, monkeypatch
) -> None:
    db = Database(tmp_path / "sequence-restart.db")
    _profile(db, "sequence-restart", claims=(_result_claim("sequence.step"),))
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "sequence-restart-assignment",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "sequence.step"},
            "entries": [{"profile_id": "sequence-restart", "profile_revision": 1}],
        },
    )
    from holdspeak.kernel.inference_runner import InferenceRunner

    monkeypatch.setitem(
        InferenceRunner.__init__.__kwdefaults__, "engine_factory", lambda *_args, **_kwargs: _Engine()
    )
    deadline = time.time() + 30
    broker = _configure(db)
    parent = broker.parent_run_controller.start(
        OWNER,
        kind="sequence",
        definition_ref="sequence:restart",
        definition_revision="rev-1",
        input_snapshot={"input": "restart"},
        deadline_at=deadline,
        child_budget=4,
        idempotency_key="sequence-restart-request",
    )
    route = broker.inference_adoption_service.freeze_routes(
        OWNER,
        command_id=f"sequence-routes-{parent.operation_id}",
        deadline_at=deadline,
        routes=[
            {
                "key": "step:1",
                "capability_id": "sequence.step",
                "invocation_id": f"{parent.native_id}:step:1",
            }
        ],
    )["step:1"]
    payload = {
        "sequence_ref": "restart",
        "sequence_revision": "rev-1",
        "step_ordinal": 1,
        "recipe_id": "recipe-restart",
        "recipe_revision": "rev-1",
        "system_prompt": "system",
        "user_prompt": "restart",
    }
    operation_id = f"sequence:{parent.operation_id}:step:1"
    admitted_before_crash = broker.inference_adoption_service.admit_on_frozen_route(
        OWNER,
        command_id=f"{operation_id}:admit",
        route_plan_id=route["id"],
        capability_id="sequence.step",
        operation_id=operation_id,
        payload=payload,
        reserved_output_tokens=32,
        parent_operation_id=parent.operation_id,
    )

    # Simulate process loss precisely after durable admission and before a
    # physical transport call. Restart reconstructs the parent capability and
    # replays both immutable command records, not a fresh route or node attempt.
    restarted = _configure(db)
    resumed_parent = restarted.parent_run_controller.start(
        OWNER,
        kind="sequence",
        definition_ref="sequence:restart",
        definition_revision="rev-1",
        input_snapshot={"input": "restart"},
        deadline_at=time.time() + 30,
        child_budget=4,
        idempotency_key="sequence-restart-request",
    )
    assert resumed_parent.replayed
    replayed_route = restarted.inference_adoption_service.freeze_routes(
        OWNER,
        command_id=f"sequence-routes-{parent.operation_id}",
        deadline_at=deadline,
        routes=[
            {
                "key": "step:1",
                "capability_id": "sequence.step",
                "invocation_id": f"{parent.native_id}:step:1",
            }
        ],
    )["step:1"]
    admitted_after_restart = restarted.inference_adoption_service.admit_on_frozen_route(
        OWNER,
        command_id=f"{operation_id}:admit",
        route_plan_id=replayed_route["id"],
        capability_id="sequence.step",
        operation_id=operation_id,
        payload=payload,
        reserved_output_tokens=32,
        parent_operation_id=resumed_parent.operation_id,
    )

    assert replayed_route["id"] == route["id"]
    assert admitted_after_restart["operation_request_plan"]["id"] == admitted_before_crash["operation_request_plan"]["id"]
    assert admitted_after_restart["execution"]["id"] == admitted_before_crash["execution"]["id"]
    routed = restarted.inference_adoption_service.execute(
        OWNER,
        execution_id=admitted_after_restart["execution"]["id"],
        adapter=CanonicalPromptAdapter(),
        parent_context=resumed_parent.context,
        planned_node="step:1",
    )
    assert routed["outcome"] == "succeeded"
    assert routed["winning_reservation"]["child_invocation_id"].startswith("invoke_")
