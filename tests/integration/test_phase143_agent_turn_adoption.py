"""HS-143-10 — Recipe.chat is the first real production ToolTurn adopter."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.agent_turn_service import AgentTurnService
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.recipe_service import RecipeService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
from tests.unit.test_phase143_tool_turn_routing import _qualified_manifest

OWNER = Principal(PrincipalKind.OWNER, "owner")


class _Engine:
    def __init__(self) -> None:
        self.calls = 0

    def run_prompt(self, *, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> str:
        self.calls += 1
        assert system_prompt and user_prompt
        return "one admitted answer"


def _qualified_recipe(db: Database, *, tools: list[str] | None = None) -> tuple[RecipeService, _Engine, str]:
    broker = _configure(db)
    AgentTurnService.compose(broker)
    _profile(
        db, "tool-model",
        claims=("language", _result_claim("agent.tool_turn"), "tool_turn"),
        capability_manifest=_qualified_manifest("language", _result_claim("agent.tool_turn"), "tool_turn"),
    )
    recipe = db.recipes.upsert(recipe_id="recipe-tool", name="Tool Agent", system_prompt="Be exact.", tools=tools or [])
    InferenceAssignmentService(db, tool_capability_foundation=broker.tool_turn_foundation._foundation).set_assignment(OWNER, {
        "command_id": "qualified-recipe-turn", "expected_revision": 0,
        "scope": {"kind": "subject", "subject_kind": "recipe", "subject_id": recipe.id, "capability_id": "agent.tool_turn"},
        "entries": [{"profile_id": "tool-model", "profile_revision": 1}],
    })
    engine = _Engine()
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: engine
    return RecipeService(db, broker=broker), engine, recipe.id


# HS-150-04: three tests DELETED. They tested RecipeService.chat() which is
# permanently retired (recipe.chat replaced by chat.turn in HS-150-02):
# - test_recipe_chat_qualified_route_drives_foundation_controller_and_runner
# - test_recipe_chat_unqualified_uses_ruled_plain_fallback_and_no_toolturn_rows
# - test_recipe_tools_remain_inert_on_the_qualified_production_turn
