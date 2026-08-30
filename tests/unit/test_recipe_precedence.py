"""HS-143-10 Recipe placement is one canonical subject-assignment path."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ValidationError
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.recipe_service import RecipeService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim


OWNER = Principal(PrincipalKind.OWNER, "owner")


class _Engine:
    active_provider = "test"
    active_model = "test-model"

    def run_prompt(self, **_kwargs: object) -> str:
        return "output"


@pytest.fixture
def rig(tmp_path: Path) -> tuple[Database, RecipeService]:
    db = Database(tmp_path / "recipe-placement.db")
    # Both profiles are executable for the one generic recipe result schema.
    _profile(db, "recipe-primary", claims=(_result_claim("recipe.run"),))
    _profile(db, "global-other", claims=(_result_claim("recipe.run"),))
    db.recipes.upsert(recipe_id="r1", name="Recipe", system_prompt="system", profile_id="recipe-primary")
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "global-recipe-placement", "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": "global-other", "profile_revision": 1}],
    })
    broker = _configure(db)
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: _Engine()
    return db, RecipeService(db, broker=broker)


# HS-151-04: test_recipe_subject_assignment_beats_divergent_global_for_run_and_chat
# DELETED — recipe.chat retired; the law is proven by recipe.run alone below.


def test_recipe_subject_assignment_beats_divergent_global_for_run(rig: tuple[Database, RecipeService]) -> None:
    _db, service = rig
    run = asyncio.run(service.run(OWNER, "r1", input="hello"))
    assert run["profile_id"] == "recipe-primary"
    assert run["placement"]["route_plan_id"]
    assert run["route_execution_receipt"]["outcome"] == "succeeded"


def test_recipe_refuses_retired_invocation_selector(rig: tuple[Database, RecipeService]) -> None:
    _db, service = rig
    with pytest.raises(ValidationError) as refused:
        asyncio.run(service.run(OWNER, "r1", input="hello", inference_target_id="global-other"))
    assert refused.value.code == "inference_legacy_selector_retired"


def test_recipe_service_has_no_local_target_or_display_resolver() -> None:
    source = (Path(__file__).resolve().parents[2] / "holdspeak/services/recipe_service.py").read_text(encoding="utf-8")
    assert "def _target(" not in source
    assert "resolve_placement" not in source
    assert "_chat_completion_text" not in source
