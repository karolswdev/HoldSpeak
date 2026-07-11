"""The smoke pack loads clean, cites real keys/recipes, and covers the vocabulary."""

from __future__ import annotations

from uat.conductor.contract.coverage import execution_coverage, pack_coverage
from uat.conductor.contract.ledger import FeatureLedger
from uat.conductor.contract.scenarios import load_pack, validate_scenario
from uat.conductor.induction.decks import DeckRegistry
from uat.conductor.induction.recipes import RecipeRegistry


def _load():
    ledger = FeatureLedger.load()
    scenarios = load_pack("smoke")
    return ledger, scenarios


def test_smoke_pack_validates_clean():
    ledger, scenarios = _load()
    recipe_names = set(RecipeRegistry().names())
    registry = RecipeRegistry()
    recipe_decks = {name: registry.load(name).deck for name in recipe_names}
    deck_names = set(DeckRegistry().names())
    errors = []
    for s in scenarios:
        errors += validate_scenario(
            s,
            ledger_keys=ledger.keys(),
            recipe_names=recipe_names,
            deck_names=deck_names,
            recipe_decks=recipe_decks,
        )
    assert errors == [], errors
    assert 6 <= len(scenarios) <= 9


def test_smoke_pack_exercises_the_whole_vocabulary():
    _, scenarios = _load()
    recipes_used = {r for s in scenarios for r in s.recipes}
    # Both golden postures (local seeding + .43 meeting/mesh) and both bad decks.
    assert {"seeded-desk", "fresh-desk"} & recipes_used  # golden-local postures
    assert "meeting-just-ended-open-actions" in recipes_used  # golden-43 intel
    assert "mesh-node-alive" in recipes_used  # mesh
    assert "intel-endpoint-dead" in recipes_used  # bad-endpoint
    assert "first-run-no-model" in recipes_used  # no-model

    # Smoke is a React desktop plumbing pack. It must never earn native evidence.
    assert {
        slot.id
        for scenario in scenarios
        for step in scenario.steps
        for slot in step.execution_slots(scenario)
    } == {"web_react:desktop"}

    # A mid-run conductor action exists (the mesh kill between steps).
    assert any(st.after for s in scenarios for st in s.steps), "no mid-run action"


def test_smoke_pack_coverage_is_target_qualified():
    ledger, scenarios = _load()
    cov = pack_coverage(scenarios, ledger)
    assert cov["overall"]["covered"] >= 1
    assert set(cov["slots"]) == {"web_react:desktop"}
    desktop = cov["slots"]["web_react:desktop"]
    assert desktop["target"] == "web_react"
    assert desktop["form_factor"] == "desktop"
    assert desktop["total"] >= desktop["covered"] >= 0
    assert 0.0 <= desktop["pct"] <= 100.0
    assert cov["expected_verdicts"] > 0


def test_execution_coverage_requires_a_fully_walked_non_skip_exact_slot():
    ledger, scenarios = _load()
    scenario = scenarios[0]
    assert execution_coverage(scenarios, ledger, [])["overall"]["covered"] == 0

    verdicts = [
        {
            "scenario_id": scenario.id,
            "step_index": step.index,
            "execution_target": "web_react",
            "form_factor": "desktop",
            "slot_id": "web_react:desktop",
            "verdict": "pass",
        }
        for step in scenario.steps
    ]
    executed = execution_coverage(scenarios, ledger, verdicts)
    assert set(scenario.features) <= set(executed["cited_features"])

    verdicts[0]["verdict"] = "skip"
    skipped = execution_coverage(scenarios, ledger, verdicts)
    assert set(scenario.steps[0].verifies).isdisjoint(skipped["cited_features"])
    assert set(scenario.steps[-1].verifies) <= set(skipped["cited_features"])


def test_wrong_or_legacy_slot_identity_earns_no_execution_coverage():
    ledger, scenarios = _load()
    scenario = scenarios[0]
    wrong = [
        {
            "scenario_id": scenario.id,
            "step_index": step.index,
            "slot_id": "ios_flagship_swift:ipad",
            "verdict": "pass",
        }
        for step in scenario.steps
    ]
    legacy = [
        {
            "scenario_id": scenario.id,
            "step_index": step.index,
            "surface": "web",
            "verdict": "pass",
        }
        for step in scenario.steps
    ]
    assert execution_coverage(scenarios, ledger, wrong)["cited_features"] == []
    assert execution_coverage(scenarios, ledger, legacy)["cited_features"] == []
