"""PARKED 20261109 (lane door/rest-park-waist) from tests/integration/test_inference_placement_adoption.py: recipe run/chat, the agent façade and voice resolution left the 143 waist (engine door; voice parked).
Not collected (tests/_parked/conftest.py). Restore with git revert.
"""
from __future__ import annotations
import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Event
from pathlib import Path
from typing import Any, Callable
import pytest
from holdspeak.db import Database
from holdspeak.kernel.inference import InferenceRunCodec
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.agent_turn_service import AgentTurnService
from holdspeak.services.errors import NotFound
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.recipe_service import RecipeService
from holdspeak.services.workbench_runner import WorkbenchRunner
from holdspeak.services.workbench_service import WorkbenchService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
from tests.unit.test_engines_run_retirement import _legacy_request
from tests.unit.test_ask_tool_turn_routing import _qualified_manifest


def _assert_attempt_linkage(db: Database, broker: Any, *, capability_id: str) -> None:
    """Every physical result connects kernel child → route → controller receipt."""
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT a.execution_id,a.child_operation_id,a.child_receipt_sha256,
                      p.route_plan_id,e.id AS evidence_id
                 FROM inference_route_attempts a
                 JOIN inference_route_executions e ON e.id=a.execution_id
                 JOIN inference_operation_route_request_plans p ON p.id=e.operation_plan_id
                 JOIN inference_adoption_route_evidence evidence
                   ON evidence.evidence_ref=p.admission_evidence_ref
                WHERE evidence.capability_id=? AND a.state='terminal'""",
            (capability_id,),
        ).fetchall()
    assert rows, f"no actual attempt for {capability_id}"
    for row in rows:
        assert row["execution_id"] == row["evidence_id"]
        assert row["route_plan_id"] and row["child_operation_id"]
        receipt = broker.store.receipt(str(row["child_operation_id"]))
        assert receipt is not None and receipt["receipt_id"] and row["child_receipt_sha256"]


def _run_recipe(db: Database, broker: Any) -> Any:
    recipe = db.recipes.upsert(recipe_id="recipe-matrix", name="Matrix", system_prompt="system", user_template="{input}")
    _assign(db, _Case("recipe-run", "recipe.run", "recipe", recipe.id), "matrix-old", "entry-recipe-run")
    return asyncio.run(RecipeService(db, broker=broker).run(OWNER, recipe.id, input="run"))


def _run_recipe_chat_unqualified(db: Database, broker: Any) -> Any:
    recipe = db.recipes.upsert(recipe_id="recipe-matrix", name="Matrix", system_prompt="system")
    _assign(db, _Case("recipe-chat", "recipe.chat", "recipe", recipe.id), "matrix-old", "entry-recipe-chat")
    return asyncio.run(RecipeService(db, broker=broker).chat(OWNER, recipe.id, question="chat"))


def _run_recipe_chat_qualified(db: Database, broker: Any) -> Any:
    recipe = db.recipes.upsert(recipe_id="recipe-matrix", name="Matrix", system_prompt="system")
    _profile(
        db,
        "matrix-tool",
        claims=("language", _result_claim("agent.tool_turn"), "tool_turn"),
        capability_manifest=_qualified_manifest("language", _result_claim("agent.tool_turn"), "tool_turn"),
    )
    _assign(db, _Case("qualified", "agent.tool_turn", "recipe", recipe.id), "matrix-tool", "entry-recipe-qualified")
    return asyncio.run(RecipeService(db, broker=broker).chat(OWNER, recipe.id, question="qualified"))


def _run_workbench(db: Database, broker: Any) -> Any:
    recipe = db.recipes.upsert(recipe_id="recipe-matrix", name="Matrix", system_prompt="system")
    workbench = db.workbenches.upsert(workbench_id="workbench-matrix", name="Matrix", recipe_id=recipe.id)
    db.workbench_items.upsert(item_id="item-matrix", workbench_id=workbench.id, title="item", body="body")
    _assign(db, _Case("workbench", "workbench.item", "workbench", workbench.id), "matrix-old", "entry-workbench")
    return asyncio.run(WorkbenchRunner(db, broker).run(OWNER, workbench.id, memory_enabled=True))


def _run_agent_facade(db: Database, broker: Any) -> Any:
    recipe = db.recipes.upsert(recipe_id="recipe-matrix", name="Matrix", system_prompt="system")
    _profile(
        db,
        "matrix-tool",
        claims=("language", _result_claim("agent.tool_turn"), "tool_turn"),
        capability_manifest=_qualified_manifest("language", _result_claim("agent.tool_turn"), "tool_turn"),
    )
    _assign(db, _Case("facade", "agent.tool_turn", "recipe", recipe.id), "matrix-tool", "entry-agent-facade")
    return AgentTurnService.compose(broker).run_recipe(
        OWNER,
        command_id="entry-agent-facade",
        turn_id="entry-agent-facade-turn",
        recipe_id=recipe.id,
        messages=[{"role": "system", "content": "system"}, {"role": "user", "content": "facade"}],
        deadline_at=time.time() + 30,
        publish=lambda _route: (lambda _value, _reservation: "matrix:agent"),
    )


def _run_voice(db: Database, broker: Any) -> Any:
    recipe = db.recipes.upsert(recipe_id="recipe-matrix", name="Matrix")
    workbench = db.workbenches.upsert(workbench_id="workbench-matrix", name="Matrix", recipe_id=recipe.id)
    db.directories.upsert(directory_id="zone-matrix", name="Matrix zone")
    _assign(db, _Case("voice", "voice.reference_resolve", "workbench", workbench.id), "matrix-old", "entry-voice")
    return WorkbenchService(db).resolve_voice(OWNER, workbench.id, "matrix", "matrix-voice-request")


ENTRY_CASES: tuple[tuple[str, str, Callable[[Database, Any], Any]], ...] = (
    ("recipe-run", "recipe.run", _run_recipe),
    # HS-151-02: recipe.chat retired — both _run_recipe_chat_* helpers call
    # RecipeService.chat() which internally admits "recipe.chat", no longer in
    # the sealed registry. Removed until HS-151-04 re-wires the alias.
    # 2026-11-08: the item queue is parked (_run_workbench drove it).
    ("agent-turn-facade", "agent.tool_turn", _run_agent_facade),
    ("voice-resolution", "voice.reference_resolve", _run_voice),
)


@pytest.mark.parametrize(("name", "capability_id", "invoke"), ENTRY_CASES, ids=[row[0] for row in ENTRY_CASES])
def test_every_python_placement_family_uses_real_product_objects_and_runner_receipts(
    tmp_path: Path, name: str, capability_id: str, invoke: Callable[[Database, Any], Any]
) -> None:
    """Production entry → canonical terms → controller → runner, without local selection."""
    db, broker, engine = _matrix_db(tmp_path, _Case(name, capability_id))
    result = invoke(db, broker)
    assert result is not None and engine.calls >= 1
    _assert_attempt_linkage(db, broker, capability_id=capability_id)
    assert "InferenceRunner.invoke" not in (Path(__file__).parents[2] / "holdspeak/services/recipe_service.py").read_text()


def test_qualified_recipe_chat_and_agent_facade_freeze_toolturn_before_assignment_edit(tmp_path: Path) -> None:
    """The ruled qualified Recipe path and its façade share one frozen tool route."""
    case = _Case("qualified-tool-mutation", "agent.tool_turn", "recipe", "recipe-matrix")
    db = Database(tmp_path / "qualified-tool-mutation.db")
    broker = _configure(db)
    agent = AgentTurnService.compose(broker)
    for profile_id in ("matrix-tool-old", "matrix-tool-new"):
        claims = ("language", _result_claim("agent.tool_turn"), "tool_turn")
        _profile(db, profile_id, claims=claims, capability_manifest=_qualified_manifest(*claims))
    recipe = db.recipes.upsert(recipe_id="recipe-matrix", name="Matrix", system_prompt="system")
    _assign(db, case, "matrix-tool-old", "qualified-tool-old")

    entered, release = Event(), Event()

    class _BlockingToolEngine(_Engine):
        def run_prompt(self, **kwargs: Any) -> str:
            entered.set()
            assert release.wait(5), "test did not release the admitted tool turn"
            return super().run_prompt(**kwargs)

    blocked = _BlockingToolEngine()
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: blocked

    def run_first() -> dict[str, Any]:
        return agent.run_recipe(
            OWNER, command_id="qualified-tool-first", turn_id="qualified-tool-first-turn",
            recipe_id=recipe.id,
            messages=[{"role": "system", "content": "system"}, {"role": "user", "content": "first"}],
            deadline_at=time.time() + 30,
            publish=lambda _route: (lambda _value, _reservation: "matrix:tool-first"),
        )

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_first)
        assert entered.wait(5), "physical provider was not reached through the façade"
        # The physical attempt is now running, therefore ToolTurn.start and its
        # model-step route admission are durable. Only a later turn may see this.
        _assign(db, case, "matrix-tool-new", "qualified-tool-edit")
        release.set()
        first = future.result(timeout=10)

    assert first["outcome"] == "succeeded"
    assert first["start"]["route_plan"]["entries"][0]["profile_id"] == "matrix-tool-old"
    _assert_attempt_linkage(db, broker, capability_id="agent.tool_turn")

    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: _Engine()
    second = agent.run_recipe(
        OWNER, command_id="qualified-tool-second", turn_id="qualified-tool-second-turn",
        recipe_id=recipe.id,
        messages=[{"role": "system", "content": "system"}, {"role": "user", "content": "later"}],
        deadline_at=time.time() + 30,
        publish=lambda _route: (lambda _value, _reservation: "matrix:tool-second"),
    )
    assert second["outcome"] == "succeeded"
    assert second["start"]["route_plan"]["entries"][0]["profile_id"] == "matrix-tool-new"


VOICE_OWNER = Principal(PrincipalKind.OWNER, "owner")


class _VoiceEngine:
    def __init__(self) -> None:
        self.calls = 0

    def run_prompt(self, **_kwargs: object) -> str:
        self.calls += 1
        return '{"zone_ids":["zone-focus"]}'


def test_voice_resolution_has_one_controller_receipt_for_its_real_attempt(tmp_path: Path) -> None:
    db = Database(tmp_path / "voice-route.db")
    broker = _configure(db)
    _profile(db, "voice-model", claims=("language", _result_claim("voice.reference_resolve")))
    recipe = db.recipes.upsert(recipe_id="voice-recipe", name="Voice")
    workbench = db.workbenches.upsert(workbench_id="voice-workbench", name="Voice", recipe_id=recipe.id)
    db.directories.upsert(directory_id="zone-focus", name="Focus")
    InferenceAssignmentService(db).set_assignment(VOICE_OWNER, {
        "command_id": "voice-route", "expected_revision": 0,
        "scope": {"kind": "subject", "subject_kind": "workbench", "subject_id": workbench.id, "capability_id": "voice.reference_resolve"},
        "entries": [{"profile_id": "voice-model", "profile_revision": 1}],
    })
    engine = _VoiceEngine()
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: engine

    result = WorkbenchService(db).resolve_voice(VOICE_OWNER, workbench.id, "focus please", "voice-request")

    assert result["refs"] == [{"name": "Focus", "id": "zone-focus", "ref": "zone:zone-focus", "kind": "zone"}]
    assert result["attempts"] == 1 and engine.calls == 1
    receipt = result["route_execution_receipt"]
    assert receipt["outcome"] == "succeeded" and len(receipt["attempts"]) == 1
    with db._connection() as conn:
        parent = conn.execute("SELECT operation_id FROM kernel_parent_runs WHERE kind='voice_reference_resolve'").fetchone()
        attempt = conn.execute("SELECT child_receipt_sha256 FROM inference_route_attempts").fetchone()
    assert parent is not None and attempt["child_receipt_sha256"]


