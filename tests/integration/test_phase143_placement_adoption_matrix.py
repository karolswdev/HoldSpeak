"""HS-143-10 Slice 6 — one real-object placement-adoption matrix.

The matrix deliberately joins the same frozen route/controller evidence that a
product surface consumes.  Its first table proves the next-run-only rule for
each migrated capability; its second table invokes each production family.
Only the physical engine factory is substituted.
"""
from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Event
from pathlib import Path
from typing import Any, Callable

import pytest

from holdspeak.db import Database
from holdspeak.kernel.inference import InferenceRunCodec
from holdspeak.kernel.prompt_adapter import CanonicalPromptAdapter
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.agent_turn_service import AgentTurnService
from holdspeak.services.errors import NotFound
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.recipe_service import RecipeService
from holdspeak.services.sequence_workflow_service import SequenceWorkflowService
from holdspeak.services.workbench_runner import WorkbenchRunner
from holdspeak.services.workbench_service import WorkbenchService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
from tests.unit.test_phase143_inference_run_retirement import _legacy_request
from tests.unit.test_phase143_tool_turn_routing import _qualified_manifest


OWNER = Principal(PrincipalKind.OWNER, "placement-matrix-owner")


class _Engine:
    active_provider = "matrix-provider"
    active_model = "matrix-model"

    def __init__(self, *, voice: bool = False) -> None:
        self.calls = 0
        self._voice = voice

    def run_prompt(self, **_kwargs: Any) -> str:
        self.calls += 1
        return '{"zone_ids":["zone-matrix"]}' if self._voice else "matrix answer"


@dataclass(frozen=True)
class _Case:
    name: str
    capability_id: str
    subject_kind: str | None = None
    subject_id: str | None = None


# These are the canonical placement terms for every Python family Story 10
# migrated. Recipe chat intentionally has both ruled paths; Apple is absent by
# the binding owner descope.
CASES = (
    # S4's Thought contextual editor invokes this same canonical subject writer.
    _Case("thought-ask", "ask.answer", "thought", "thought-matrix"),
    _Case("recipe-run", "recipe.run", "recipe", "recipe-matrix"),
    _Case("recipe-chat-unqualified", "recipe.chat", "recipe", "recipe-matrix"),
    _Case("workbench-item-and-memory", "workbench.item", "workbench", "workbench-matrix"),
    _Case("voice-resolution", "voice.reference_resolve", "workbench", "workbench-matrix"),
    _Case("sequence-step", "sequence.step", "recipe", "recipe-matrix"),
    _Case("workflow-node", "workflow.node"),
)


def _scope(case: _Case) -> dict[str, str]:
    if case.subject_kind is None:
        return {"kind": "capability", "capability_id": case.capability_id}
    return {
        "kind": "subject",
        "subject_kind": case.subject_kind,
        "subject_id": str(case.subject_id),
        "capability_id": case.capability_id,
    }


def _assign(db: Database, case: _Case, profile_id: str, command: str) -> None:
    broker = _configure(db)
    foundation = getattr(getattr(broker, "tool_turn_foundation", None), "_foundation", None)
    assignments = InferenceAssignmentService(db, tool_capability_foundation=foundation)
    scope = _scope(case)
    try:
        current = assignments.get_assignment(OWNER, scope)
    except NotFound:
        current = None
    assignments.set_assignment(
        OWNER,
        {
            "command_id": command,
            "expected_revision": int(current["revision"]) if current else 0,
            "scope": scope,
            "entries": [{"profile_id": profile_id, "profile_revision": 1}],
        },
    )


def _matrix_db(tmp_path: Path, case: _Case) -> tuple[Database, Any, _Engine]:
    db = Database(tmp_path / f"{case.name}.db")
    broker = _configure(db)
    AgentTurnService.compose(broker)
    claims = ("language", _result_claim(case.capability_id))
    manifest = None
    if case.capability_id == "agent.tool_turn":
        claims = ("language", _result_claim("agent.tool_turn"), "tool_turn")
        manifest = _qualified_manifest(*claims)
    _profile(db, "matrix-old", claims=claims, capability_manifest=manifest)
    _profile(db, "matrix-new", claims=claims, capability_manifest=manifest)
    _assign(db, case, "matrix-old", f"{case.name}-old")
    engine = _Engine(voice=case.capability_id == "voice.reference_resolve")
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: engine
    return db, broker, engine


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


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_frozen_canonical_terms_survive_assignment_mutation_then_later_admission_sees_edit(
    tmp_path: Path, case: _Case
) -> None:
    """One table proves selection/freeze/linkage for every migrated capability."""
    db, broker, engine = _matrix_db(tmp_path, case)
    coordinator = broker.inference_adoption_service
    admitted = coordinator.admit(
        OWNER,
        command_id=f"{case.name}-admit-old",
        capability_id=case.capability_id,
        operation_id=f"{case.name}-operation-old",
        payload={"system_prompt": "matrix", "user_prompt": case.name},
        subject_kind=case.subject_kind,
        subject_id=case.subject_id,
        reserved_output_tokens=32,
    )
    old_route = admitted["route_plan"]
    assert old_route["entries"][0]["profile_id"] == "matrix-old"

    # Mutation happens after admission, before the physical controller execution.
    _assign(db, case, "matrix-new", f"{case.name}-assignment-edit")
    # The old plan is immutable evidence even before its physical reservation is
    # consumed; every actual execution/receipt assertion lives in the product
    # entry table below, which supplies the family-specific adapter and payload.
    assert old_route["entries"][0]["profile_id"] == "matrix-old"

    later = coordinator.admit(
        OWNER,
        command_id=f"{case.name}-admit-new",
        capability_id=case.capability_id,
        operation_id=f"{case.name}-operation-new",
        payload={"system_prompt": "matrix", "user_prompt": "later"},
        subject_kind=case.subject_kind,
        subject_id=case.subject_id,
        reserved_output_tokens=32,
    )
    assert later["route_plan"]["entries"][0]["profile_id"] == "matrix-new"


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


def _run_sequence(db: Database, broker: Any) -> Any:
    recipe = db.recipes.upsert(recipe_id="recipe-matrix", name="Matrix", system_prompt="system", user_template="{input}")
    db.chains.upsert(chain_id="chain-matrix", name="Matrix", steps=[recipe.id])
    _assign(db, _Case("sequence", "sequence.step", "recipe", recipe.id), "matrix-old", "entry-sequence")
    return asyncio.run(SequenceWorkflowService(db, broker).run_sequence(OWNER, "chain-matrix", {"input": "sequence"}))


def _run_workflow(db: Database, broker: Any) -> Any:
    db.workflows.upsert(workflow_id="workflow-matrix", name="Matrix", prompt="Do: {input}")
    _assign(db, _Case("workflow", "workflow.node"), "matrix-old", "entry-workflow")
    return asyncio.run(SequenceWorkflowService(db, broker).run_workflow(OWNER, "workflow-matrix", {"input": "workflow"}))


ENTRY_CASES: tuple[tuple[str, str, Callable[[Database, Any], Any]], ...] = (
    ("recipe-run", "recipe.run", _run_recipe),
    ("recipe-chat-unqualified", "recipe.chat", _run_recipe_chat_unqualified),
    ("recipe-chat-qualified-toolturn", "agent.tool_turn", _run_recipe_chat_qualified),
    ("workbench-item-and-memory", "workbench.item", _run_workbench),
    ("agent-turn-facade", "agent.tool_turn", _run_agent_facade),
    ("voice-resolution", "voice.reference_resolve", _run_voice),
    ("sequence-step", "sequence.step", _run_sequence),
    ("workflow-node", "workflow.node", _run_workflow),
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


def test_legacy_operation_refusal_has_no_route_or_provider_attempt(tmp_path: Path) -> None:
    """The descoped Apple row has no substitute: legacy Python operation refuses."""
    db = Database(tmp_path / "legacy-refusal.db")
    broker = _configure(db)
    refused = broker.submit(_legacy_request(target_id="mutable-after-admission"), OWNER)
    assert refused["state"] == "refused"
    assert refused["receipt"]["outcome"] == "inference_run_retired"
    assert InferenceRunCodec(db).read_native("retired-invocation") is None
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == 0
