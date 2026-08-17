"""HS-134-01 -- recipe execution takes the precedence door.

Proves that ``RecipeService.run`` and ``RecipeService.chat`` resolve their
execution target through ``resolve_placement`` (the Phase-130 ONE placement
authority) and that the full precedence chain works at runtime:

    invocation > workbench > agent > global

Before this story, recipe execution manually chained
``inference_target_id or recipe.profile_id or "this_machine"`` through
``resolve_inference_target``, which made Workbench overrides invisible to
actual execution (Article II lie). The listing path already used
``resolve_placement`` -- now execution does too.
"""
from __future__ import annotations

import ast
import asyncio
import re
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.recipe_service import RecipeService

OWNER = Principal(PrincipalKind.OWNER, "owner")


class _FakeEngine:
    active_provider = "test"
    active_model = "test-model"

    def run_prompt(self, **kwargs):
        return "output"


@pytest.fixture
def rig(tmp_path, monkeypatch):
    db = Database(tmp_path / "precedence.db")
    # Agent-tier target (A)
    db.profiles.upsert(
        profile_id="agent_target",
        name="Agent Target",
        kind="openAICompatible",
        base_url="http://agent:8080/v1",
        model="agent-model",
    )
    # Workbench-tier target (B)
    db.profiles.upsert(
        profile_id="wb_target",
        name="Workbench Target",
        kind="openAICompatible",
        base_url="http://workbench:8080/v1",
        model="wb-model",
    )
    # Invocation-tier target (C)
    db.profiles.upsert(
        profile_id="invocation_target",
        name="Invocation Target",
        kind="openAICompatible",
        base_url="http://invocation:8080/v1",
        model="invocation-model",
    )
    # Recipe with agent-tier placement
    db.recipes.upsert(
        recipe_id="r1",
        name="Precedence Test",
        system_prompt="system",
        profile_id="agent_target",
    )
    broker = _configure(db)
    broker.inference_runner._engine_factory = lambda _revision, **_: _FakeEngine()
    return db, RecipeService(db, broker=broker)


# ---------------------------------------------------------------------------
# run() precedence
# ---------------------------------------------------------------------------


def test_run_workbench_override_changes_actual_execution(rig):
    """Agent has tier A; workbench override B -> execution actually uses B."""
    _db, service = rig
    result = asyncio.run(service.run(
        OWNER, "r1", input="hello", workbench_id="wb_target",
    ))
    assert result["profile_id"] == "wb_target"
    assert result["inference_target"]["id"] == "wb_target"


def test_run_no_override_uses_agent_tier(rig):
    """No workbench, no invocation -> agent tier wins."""
    _db, service = rig
    result = asyncio.run(service.run(
        OWNER, "r1", input="hello",
    ))
    assert result["profile_id"] == "agent_target"
    assert result["inference_target"]["id"] == "agent_target"


def test_run_invocation_beats_workbench_and_agent(rig):
    """Explicit invocation arg wins over both workbench and agent."""
    _db, service = rig
    result = asyncio.run(service.run(
        OWNER, "r1", input="hello",
        inference_target_id="invocation_target",
        workbench_id="wb_target",
    ))
    assert result["profile_id"] == "invocation_target"
    assert result["inference_target"]["id"] == "invocation_target"


# ---------------------------------------------------------------------------
# chat() precedence
# ---------------------------------------------------------------------------


def test_chat_workbench_override_changes_actual_execution(rig):
    """Chat: agent has tier A; workbench override B -> execution uses B."""
    _db, service = rig
    result = asyncio.run(service.chat(
        OWNER, "r1", question="hello", workbench_id="wb_target",
    ))
    assert result["profile_id"] == "wb_target"
    assert result["inference_target"]["id"] == "wb_target"


def test_chat_no_override_uses_agent_tier(rig):
    """Chat: no workbench, no invocation -> agent tier wins."""
    _db, service = rig
    result = asyncio.run(service.chat(
        OWNER, "r1", question="hello",
    ))
    assert result["profile_id"] == "agent_target"
    assert result["inference_target"]["id"] == "agent_target"


def test_chat_invocation_beats_workbench_and_agent(rig):
    """Chat: explicit invocation arg wins over both."""
    _db, service = rig
    result = asyncio.run(service.chat(
        OWNER, "r1", question="hello",
        inference_target_id="invocation_target",
        workbench_id="wb_target",
    ))
    assert result["profile_id"] == "invocation_target"
    assert result["inference_target"]["id"] == "invocation_target"


# ---------------------------------------------------------------------------
# Structural fences
# ---------------------------------------------------------------------------


def test_recipe_service_target_uses_resolve_placement_not_resolve_inference_target():
    """AC-1: ``_target()`` must use ``resolve_placement``, not
    ``resolve_inference_target``."""
    source = Path(__file__).resolve().parents[2] / "holdspeak/services/recipe_service.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "_target":
            body_text = ast.unparse(node)
            assert "resolve_inference_target" not in body_text, (
                "_target() still uses resolve_inference_target -- "
                "recipe execution must route through resolve_placement"
            )
            assert "resolve_placement" in body_text, (
                "_target() does not call resolve_placement"
            )
            break
    else:
        pytest.fail("_target() method not found in recipe_service.py")


_INLINE_FALLBACK = re.compile(r'or\s+["\']this_machine["\']')


def test_no_inline_this_machine_fallback_in_recipe_service():
    """The inline ``or "this_machine"`` placement fallback is gone from
    recipe_service.py -- the resolver handles the global default."""
    source = Path(__file__).resolve().parents[2] / "holdspeak/services/recipe_service.py"
    offenders = []
    for lineno, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if _INLINE_FALLBACK.search(line):
            offenders.append(f"recipe_service.py:{lineno}: {line.strip()}")
    assert not offenders, (
        "Inline `or \"this_machine\"` placement fallback still present:\n"
        + "\n".join(offenders)
    )
