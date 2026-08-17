"""HS-134-04 -- every answer names its decider.

Proves that every placement-resolving execution response carries
``{"placement": {"effective_target_id": ..., "source": ...}}`` from
``PlacementResolution.placement_dict()`` -- the REAL resolution used for
that run, not a recomputation that could disagree.

Surfaces covered: Ask, Recipe run, Recipe chat, Workbench run,
Sequence, Workflow, Cadence get_loop (LLM-drafted path).
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.inference_targets import PLACEMENT_SOURCES, THIS_MACHINE_ID
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "provenance-owner")


class _FakeEngine:
    active_provider = "test"
    active_model = "test-model"

    def run_prompt(self, **kwargs):
        return "output"


# ---------------------------------------------------------------------------
# Ask
# ---------------------------------------------------------------------------


@pytest.fixture
def ask_rig(tmp_path, monkeypatch):
    from holdspeak.services.ask_service import AskService

    db = Database(tmp_path / "ask_prov.db")
    monkeypatch.setattr(
        "holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", "")
    )
    db.profiles.upsert(
        profile_id="ask_profile",
        name="Ask Profile",
        kind="openAICompatible",
        base_url="http://ask:8080/v1",
        model="ask-model",
    )
    broker = _configure(db)
    broker.inference_runner._engine_factory = lambda _rev, **_: _FakeEngine()
    return db, AskService(db, broker=broker)


def test_ask_global_placement(ask_rig):
    """Ask with no overrides -> source 'global'."""
    _db, service = ask_rig
    result = asyncio.run(service.ask(OWNER, "hello"))
    assert "placement" in result, f"placement block missing from Ask result: {sorted(result)}"
    p = result["placement"]
    assert p["source"] == "global"
    assert p["effective_target_id"] == THIS_MACHINE_ID


def test_ask_invocation_placement(ask_rig):
    """Ask with explicit inference_target_id -> source 'invocation'."""
    _db, service = ask_rig
    result = asyncio.run(
        service.ask(OWNER, "hello", inference_target_id="ask_profile", model="ask-model")
    )
    assert result["placement"]["source"] == "invocation"
    assert result["placement"]["effective_target_id"] == "ask_profile"


# ---------------------------------------------------------------------------
# Recipe
# ---------------------------------------------------------------------------


@pytest.fixture
def recipe_rig(tmp_path, monkeypatch):
    from holdspeak.services.recipe_service import RecipeService

    db = Database(tmp_path / "recipe_prov.db")
    db.profiles.upsert(
        profile_id="agent_target",
        name="Agent Target",
        kind="openAICompatible",
        base_url="http://agent:8080/v1",
        model="agent-model",
    )
    db.profiles.upsert(
        profile_id="wb_target",
        name="Workbench Target",
        kind="openAICompatible",
        base_url="http://workbench:8080/v1",
        model="wb-model",
    )
    db.profiles.upsert(
        profile_id="invocation_target",
        name="Invocation Target",
        kind="openAICompatible",
        base_url="http://invocation:8080/v1",
        model="invocation-model",
    )
    db.recipes.upsert(
        recipe_id="r1",
        name="Provenance Test",
        system_prompt="system",
        profile_id="agent_target",
    )
    broker = _configure(db)
    broker.inference_runner._engine_factory = lambda _rev, **_: _FakeEngine()
    return db, RecipeService(db, broker=broker)


def test_recipe_run_agent_default(recipe_rig):
    """Recipe run with no override -> agent tier wins."""
    _db, service = recipe_rig
    result = asyncio.run(service.run(OWNER, "r1", input="hello"))
    assert "placement" in result, f"placement missing from recipe run: {sorted(result)}"
    assert result["placement"]["source"] == "agent"
    assert result["placement"]["effective_target_id"] == "agent_target"


def test_recipe_run_workbench_override(recipe_rig):
    """Recipe run with workbench override -> source 'workbench'."""
    _db, service = recipe_rig
    result = asyncio.run(
        service.run(OWNER, "r1", input="hello", workbench_id="wb_target")
    )
    assert result["placement"]["source"] == "workbench"
    assert result["placement"]["effective_target_id"] == "wb_target"


def test_recipe_run_invocation_override(recipe_rig):
    """Recipe run with invocation -> source 'invocation'."""
    _db, service = recipe_rig
    result = asyncio.run(
        service.run(
            OWNER, "r1", input="hello",
            inference_target_id="invocation_target",
            workbench_id="wb_target",
        )
    )
    assert result["placement"]["source"] == "invocation"
    assert result["placement"]["effective_target_id"] == "invocation_target"


def test_recipe_chat_agent_default(recipe_rig):
    """Chat with no override -> agent tier wins."""
    _db, service = recipe_rig
    result = asyncio.run(service.chat(OWNER, "r1", question="hello"))
    assert "placement" in result
    assert result["placement"]["source"] == "agent"
    assert result["placement"]["effective_target_id"] == "agent_target"


def test_recipe_chat_workbench_override(recipe_rig):
    """Chat with workbench override -> source 'workbench'."""
    _db, service = recipe_rig
    result = asyncio.run(
        service.chat(OWNER, "r1", question="hello", workbench_id="wb_target")
    )
    assert result["placement"]["source"] == "workbench"
    assert result["placement"]["effective_target_id"] == "wb_target"


def test_recipe_chat_invocation_override(recipe_rig):
    """Chat with invocation -> source 'invocation'."""
    _db, service = recipe_rig
    result = asyncio.run(
        service.chat(
            OWNER, "r1", question="hello",
            inference_target_id="invocation_target",
            workbench_id="wb_target",
        )
    )
    assert result["placement"]["source"] == "invocation"
    assert result["placement"]["effective_target_id"] == "invocation_target"


# ---------------------------------------------------------------------------
# Workbench
# ---------------------------------------------------------------------------


def test_workbench_run_placement(tmp_path, monkeypatch):
    """Workbench run carries placement block with workbench source."""
    from holdspeak.services.workbench_runner import WorkbenchRunner

    db = Database(tmp_path / "wb_prov.db")

    class FakeIntel:
        active_provider = "test-provider"
        active_model = "test-model"

        def run_prompt(self, **kwargs):
            return "wb-output"

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_meeting_intel_for_profile",
        lambda **_: FakeIntel(),
    )
    profile = db.profiles.upsert(
        profile_id="wb_profile",
        name="Profile",
        kind="openAICompatible",
        base_url="http://profile",
        model="model",
    )
    recipe = db.recipes.upsert(
        recipe_id="wb_recipe",
        name="Runner",
        system_prompt="SYS",
        user_template="{input}",
    )
    workbench = db.workbenches.upsert(
        workbench_id="wb_1",
        name="Runner",
        recipe_id=recipe.id,
        profile_id=profile.id,
    )
    db.workbench_items.upsert(
        item_id="item_1",
        workbench_id=workbench.id,
        title="Item 1",
        body="input 1",
    )
    broker = _configure(db)
    result = asyncio.run(
        WorkbenchRunner(db, broker).run(OWNER, workbench.id, memory_enabled=False)
    )
    assert "placement" in result, f"placement missing from workbench run: {sorted(result)}"
    # Workbench profile_id is set -> source is "workbench"
    assert result["placement"]["source"] == "workbench"
    assert result["placement"]["effective_target_id"] == profile.id


# ---------------------------------------------------------------------------
# Sequence
# ---------------------------------------------------------------------------


def test_sequence_run_placement(tmp_path, monkeypatch):
    """Sequence run carries placement block."""
    import holdspeak.db as hsdb
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from holdspeak.kernel.inference_runner import InferenceRunner
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes import build_primitives_router

    reset_database()
    db = Database(tmp_path / "seq_prov.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setattr(
        "holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", "")
    )

    class _Engine:
        active_provider = "local"

        def run_prompt(self, **_):
            return "seq-output"

    monkeypatch.setitem(
        InferenceRunner.__init__.__kwdefaults__,
        "engine_factory",
        lambda rev, **_: _Engine(),
    )
    monkeypatch.setattr(
        "holdspeak.intel.providers._configured_engine", lambda: _Engine()
    )

    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    client = TestClient(app)

    rid = client.post(
        "/api/recipes",
        json={"name": "Seq", "system_prompt": "SYS", "user_template": "{input}"},
    ).json()["recipe"]["id"]
    cid = client.post(
        "/api/chains", json={"name": "seq", "steps": [rid]}
    ).json()["chain"]["id"]
    response = client.post(f"/api/chains/{cid}/run", json={"input": "hi"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert "placement" in result, f"placement missing from sequence: {sorted(result)}"
    # No invocation/workbench/agent override -> global
    assert result["placement"]["source"] == "global"
    assert result["placement"]["effective_target_id"] == THIS_MACHINE_ID


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


def test_workflow_run_placement(tmp_path, monkeypatch):
    """Workflow run carries placement block."""
    import holdspeak.db as hsdb
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from holdspeak.kernel.inference_runner import InferenceRunner
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes import build_primitives_router

    reset_database()
    db = Database(tmp_path / "wf_prov.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setattr(
        "holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", "")
    )

    class _Engine:
        active_provider = "local"

        def run_prompt(self, **_):
            return "wf-output"

    monkeypatch.setitem(
        InferenceRunner.__init__.__kwdefaults__,
        "engine_factory",
        lambda rev, **_: _Engine(),
    )
    monkeypatch.setattr(
        "holdspeak.intel.providers._configured_engine", lambda: _Engine()
    )

    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    client = TestClient(app)

    graph = {
        "entry": "entry",
        "nodes": [
            {"id": "entry", "kind": {"entry": {}}},
            {"id": "model", "kind": {"summarize": {}}},
            {"id": "out", "kind": {"output": {}}},
        ],
        "exec_edges": [
            {"from": {"node": "entry", "name": "then"}, "to": "model"},
            {"from": {"node": "model", "name": "then"}, "to": "out"},
        ],
    }
    wid = client.post(
        "/api/workflows",
        json={"id": "wf_prov", "name": "Prov", "graph_json": graph},
    ).json()["workflow"]["id"]
    response = client.post(f"/api/workflows/{wid}/run", json={"input": "hi"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert "placement" in result, f"placement missing from workflow: {sorted(result)}"
    assert result["placement"]["source"] == "global"
    assert result["placement"]["effective_target_id"] == THIS_MACHINE_ID


# ---------------------------------------------------------------------------
# Cadence (LLM-drafted path)
# ---------------------------------------------------------------------------


def test_cadence_get_loop_llm_placement(tmp_path, monkeypatch):
    """Cadence get_loop with LLM draft carries placement block."""
    from holdspeak.cadence.models import OpenLoop
    from holdspeak.config.integrations import CadenceConfig
    from holdspeak.services.cadence_service import CadenceService

    reset_database()
    db = Database(tmp_path / "cadence_prov.db")
    monkeypatch.setattr(
        "holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", "")
    )
    loop = db.cadence.upsert_loop(
        OpenLoop(
            source_type="meeting_action",
            source_id="a1",
            title="Ship it",
            owner="Karol",
        )
    )
    broker = _configure(db)

    class FakeIntel:
        active_provider = "local"

        def run_prompt(self, **_):
            return '{"kind":"create_issue","title":"Do the thing","body_markdown":"body"}'

    broker.inference_runner._engine_factory = lambda _rev, **_: FakeIntel()
    service = CadenceService(db, CadenceConfig(use_llm=True), kernel=broker)
    detail = asyncio.run(service.get_loop(OWNER, loop.id))
    assert detail["next_action"]["generated_by"] == "llm"
    assert "placement" in detail, f"placement missing from cadence: {sorted(detail)}"
    assert detail["placement"]["source"] == "global"
    assert detail["placement"]["effective_target_id"] == THIS_MACHINE_ID


def test_cadence_get_loop_deterministic_no_placement(tmp_path, monkeypatch):
    """Cadence get_loop without LLM draft omits placement block."""
    from holdspeak.cadence.models import OpenLoop
    from holdspeak.config.integrations import CadenceConfig
    from holdspeak.services.cadence_service import CadenceService

    reset_database()
    db = Database(tmp_path / "cadence_det.db")
    loop = db.cadence.upsert_loop(
        OpenLoop(
            source_type="meeting_action",
            source_id="a2",
            title="Review draft",
            owner="Karol",
        )
    )
    service = CadenceService(db, CadenceConfig(use_llm=False))
    detail = asyncio.run(service.get_loop(OWNER, loop.id))
    assert detail["next_action"]["generated_by"] == "deterministic"
    # No model invocation -> no placement block
    assert "placement" not in detail


# ---------------------------------------------------------------------------
# Placement dict shape
# ---------------------------------------------------------------------------


def test_placement_dict_source_vocabulary():
    """placement_dict source is always one of PLACEMENT_SOURCES."""
    assert set(PLACEMENT_SOURCES) == {"invocation", "workbench", "agent", "global"}
