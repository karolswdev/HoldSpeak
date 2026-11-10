# PARKED 20261109 (door/park-waist): the cases of tests/unit/test_recipe_runner_migration.py that drove the parked routed-inference waist.
# Not collected (tests/_parked/conftest.py). Restore with `git revert` of the parking commit.
"""HS-143-10 Recipe execution only traverses route/controller/Runner evidence."""
from __future__ import annotations

import asyncio
import ast
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.kernel.recipe_projection import materialize_run
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.recipe_service import RecipeService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim


def test_recipe_assignment_mutation_after_admission_cannot_retarget_frozen_execution(
    rig: tuple[Database, object],
) -> None:
    """The admitted route and operation hashes survive a later subject edit."""
    from holdspeak.services.recipe_service import _RecipeResultAdapter

    db, broker = rig
    _profile(db, "recipe-later", claims=(_result_claim("recipe.run"),))
    coordinator = broker.inference_adoption_service
    coordinator.migrate_recipe_workbench_subject_assignments(OWNER)
    payload = {
        "system_prompt": "system", "user_prompt": "first", "variables": {},
        "recipe_id": "r1", "recipe_revision": "1", "temperature": None,
        "max_tokens": None, "workbench_id": "",
    }
    admitted = coordinator.admit(
        OWNER, command_id="admit-frozen-recipe", capability_id="recipe.run",
        operation_id="frozen-recipe", payload=payload, subject_kind="recipe", subject_id="r1",
        reserved_output_tokens=512,
    )
    frozen_route = dict(admitted["route_plan"])
    frozen_operation = dict(admitted["operation_request_plan"])
    assignments = InferenceAssignmentService(db)
    current = assignments.get_assignment(OWNER, {
        "kind": "subject", "subject_kind": "recipe", "subject_id": "r1",
        "capability_id": "recipe.run",
    })
    assignments.set_assignment(OWNER, {
        "command_id": "replace-after-admission", "expected_revision": current["revision"],
        "scope": current["scope"],
        "entries": [{"profile_id": "recipe-later", "profile_revision": 1}],
    })

    executed = coordinator.execute(
        OWNER, execution_id=admitted["execution"]["id"], adapter=_RecipeResultAdapter(),
        publish=lambda _output, reservation: f"result:{reservation['child_invocation_id']}",
    )
    later = coordinator.admit(
        OWNER, command_id="admit-later-recipe", capability_id="recipe.run",
        operation_id="later-recipe", payload={**payload, "user_prompt": "second"},
        subject_kind="recipe", subject_id="r1", reserved_output_tokens=512,
    )

    assert executed["outcome"] == "succeeded"
    assert [entry["profile_id"] for entry in frozen_route["entries"]] == ["recipe-primary"]
    assert frozen_operation["route_plan_id"] == frozen_route["id"]
    assert frozen_route["sha256"].startswith("sha256:")
    assert frozen_operation["sha256"] == admitted["operation_request_plan"]["sha256"]
    assert [entry["profile_id"] for entry in later["route_plan"]["entries"]] == ["recipe-later"]
