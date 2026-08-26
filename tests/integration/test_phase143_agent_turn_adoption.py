"""HS-143-10 — Recipe.chat is the first real production ToolTurn adopter."""
from __future__ import annotations

import asyncio
from pathlib import Path

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


def test_recipe_chat_qualified_route_drives_foundation_controller_and_runner(tmp_path: Path) -> None:
    db = Database(tmp_path / "recipe-tool.db")
    recipes, engine, recipe_id = _qualified_recipe(db)

    result = asyncio.run(recipes.chat(OWNER, recipe_id, question="What is frozen?"))

    assert result["output"] == "one admitted answer"
    assert engine.calls == 1
    receipt = result["route_execution_receipt"]
    assert receipt["outcome"] == "succeeded"
    with db._connection() as conn:
        parent = conn.execute("SELECT operation_id FROM kernel_parent_runs WHERE kind='tool.turn'").fetchone()
        lease = conn.execute("SELECT turn_id,terms_sha256 FROM turn_capability_leases").fetchone()
        step = conn.execute("SELECT route_execution_id,child_receipt_id FROM tool_turn_model_steps").fetchone()
        attempt = conn.execute("SELECT child_operation_id,child_receipt_sha256 FROM inference_route_attempts").fetchone()
    assert parent is not None and lease is not None and step is not None
    assert step["route_execution_id"] == receipt["execution_id"]
    assert attempt["child_operation_id"] and attempt["child_receipt_sha256"]


def test_recipe_chat_unqualified_uses_ruled_plain_fallback_and_no_toolturn_rows(tmp_path: Path) -> None:
    db = Database(tmp_path / "recipe-plain.db")
    broker = _configure(db)
    _profile(db, "plain-model", claims=("language", _result_claim("recipe.chat")))
    recipe = db.recipes.upsert(recipe_id="recipe-plain", name="Plain", system_prompt="Answer.")
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "plain-recipe-chat", "expected_revision": 0,
        "scope": {"kind": "subject", "subject_kind": "recipe", "subject_id": recipe.id, "capability_id": "recipe.chat"},
        "entries": [{"profile_id": "plain-model", "profile_revision": 1}],
    })
    engine = _Engine()
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: engine

    result = asyncio.run(RecipeService(db, broker=broker).chat(OWNER, recipe.id, question="Plain route?"))

    assert result["output"] == "one admitted answer"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM tool_turns").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM turn_capability_leases").fetchone()[0] == 0


def test_recipe_tools_remain_inert_on_the_qualified_production_turn(tmp_path: Path) -> None:
    db = Database(tmp_path / "recipe-tools-inert.db")
    recipes, engine, recipe_id = _qualified_recipe(db, tools=["delete_everything", "ambient_tool"])

    result = asyncio.run(recipes.chat(OWNER, recipe_id, question="Does the stored list matter?"))

    assert result["output"] == "one admitted answer"
    assert engine.calls == 1
    with db._connection() as conn:
        terms = str(conn.execute("SELECT terms_json FROM turn_capability_leases").fetchone()[0])
    assert "delete_everything" not in terms and "ambient_tool" not in terms
