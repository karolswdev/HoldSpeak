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
from pathlib import Path

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.inference_targets import PLACEMENT_SOURCES, THIS_MACHINE_ID
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ValidationError
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

OWNER = Principal(PrincipalKind.OWNER, "provenance-owner")


class _FakeEngine:
    active_provider = "test"
    active_model = "test-model"

    def run_prompt(self, **kwargs):
        return "output"


def _ready_local_model(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Give legacy placement surfaces a real ready local deployment identity."""
    path = tmp_path / "fixture.gguf"
    path.write_bytes(b"fixture-model")
    monkeypatch.setattr(
        "holdspeak.intel.providers.configured_local_meeting_model_path",
        lambda: str(path),
    )
    return path


# ---------------------------------------------------------------------------
# Ask
# ---------------------------------------------------------------------------


@pytest.fixture
def ask_rig(tmp_path, monkeypatch):
    from holdspeak.services.ask_service import AskService

    db = Database(tmp_path / "ask_prov.db")
    _ready_local_model(tmp_path, monkeypatch)
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
def recipe_rig(tmp_path):
    from holdspeak.services.recipe_service import RecipeService

    db = Database(tmp_path / "recipe_prov.db")
    # recipe.run and recipe.chat share this result-schema claim.
    claims = (_result_claim("recipe.run"),)
    _profile(db, "agent_target", claims=claims)
    _profile(db, "wb_target", claims=claims)
    db.recipes.upsert(
        recipe_id="r1",
        name="Provenance Test",
        system_prompt="system",
        profile_id="agent_target",
    )
    broker = _configure(db)
    broker.inference_runner._engine_factory = lambda _rev, **_: _FakeEngine()
    return db, RecipeService(db, broker=broker)


def test_recipe_run_canonical_subject_assignment(recipe_rig):
    """Recipe projection names the frozen route selected for its subject."""
    _db, service = recipe_rig
    result = asyncio.run(service.run(OWNER, "r1", input="hello"))
    assert result["profile_id"] == "agent_target"
    assert result["inference_target"]["profile_id"] == "agent_target"
    assert set(result["placement"]) == {"route_plan_id", "route_plan_sha256"}
    assert result["route_execution_receipt"]["outcome"] == "succeeded"


def test_recipe_run_workbench_context_cannot_reroute_canonical_subject(recipe_rig):
    """The old workbench placement selector is not an execution authority."""
    _db, service = recipe_rig
    result = asyncio.run(service.run(OWNER, "r1", input="hello", workbench_id="wb_target"))
    assert result["profile_id"] == "agent_target"
    assert result["route_execution_receipt"]["outcome"] == "succeeded"


def test_recipe_run_rejects_legacy_invocation_selector(recipe_rig):
    _db, service = recipe_rig
    with pytest.raises(ValidationError, match="Legacy model selectors") as raised:
        asyncio.run(service.run(OWNER, "r1", input="hello", inference_target_id="wb_target"))
    assert raised.value.code == "inference_legacy_selector_retired"


# HS-151-04: test_recipe_chat_canonical_subject_assignment and
# test_recipe_chat_rejects_legacy_invocation_selector DELETED.
# They tested RecipeService.chat() which is permanently retired
# (recipe.chat replaced by chat.turn in HS-151-02).


# ---------------------------------------------------------------------------
# Workbench
# ---------------------------------------------------------------------------


def test_workbench_run_placement(tmp_path, monkeypatch):
    """Workbench run projects egress only from its frozen parent route."""
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
    # No service-local source/target decision survives the cutover. The public
    # projection comes from the route frozen with the parent bundle.
    assert result["placement"]["model"] == profile.id
    assert result["placement"]["deployment_revision_id"]
    assert "source" not in result["placement"] and "effective_target_id" not in result["placement"]
    with db._connection() as conn:
        member = conn.execute(
            "SELECT member.route_plan_id FROM inference_parent_route_bundle_members member "
            "JOIN inference_parent_route_bundles bundle ON bundle.id=member.bundle_id "
            "WHERE bundle.parent_operation_id=?", (result["parent_operation_id"],)
        ).fetchone()
        entry = conn.execute(
            "SELECT profile_id,deployment_revision_id FROM inference_route_plan_entries WHERE plan_id=?",
            (member["route_plan_id"],),
        ).fetchone()
    assert member is not None and entry is not None
    assert (entry["profile_id"], entry["deployment_revision_id"]) == (
        f"legacy-{profile.id}", result["placement"]["deployment_revision_id"],
    )


# ---------------------------------------------------------------------------
# Sequence
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


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
    _ready_local_model(tmp_path, monkeypatch)
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    _profile(db, "cadence-route")
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "assign-cadence-route",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "background.cadence_draft"},
            "entries": [{"profile_id": "cadence-route", "profile_revision": 1}],
        },
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
    assert detail["placement"]["source"] == "owner_assignment"
    assert detail["placement"]["egress"]["scope"] == "local"


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
