"""The smoke pack loads clean, cites real keys/recipes, and covers the vocabulary."""

from __future__ import annotations

from uat.conductor.contract.coverage import pack_coverage
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
    deck_names = set(DeckRegistry().names())
    errors = []
    for s in scenarios:
        errors += validate_scenario(
            s, ledger_keys=ledger.keys(), recipe_names=recipe_names, deck_names=deck_names
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

    # A three-surface scenario exists (all three applicable on ≥1 step).
    def all_three(scn):
        return all(scn.surfaces[s]["applicable"] for s in ("web", "ipad", "iphone"))

    assert any(all_three(s) for s in scenarios), "no fully three-surface scenario"

    # An honest per-surface n/a with a reason exists somewhere.
    na = [
        v
        for s in scenarios
        for st in s.steps
        for v in st.resolved_surfaces(s.surfaces).values()
        if not v["applicable"]
    ]
    assert na and all(v["reason"] for v in na), "n/a must carry a reason"

    # A mid-run conductor action exists (the mesh kill between steps).
    assert any(st.after for s in scenarios for st in s.steps), "no mid-run action"


def test_smoke_pack_coverage_is_per_surface():
    ledger, scenarios = _load()
    cov = pack_coverage(scenarios, ledger)
    assert cov["overall"]["covered"] >= 1
    for s in ("web", "ipad", "iphone"):
        assert cov[s]["total"] >= cov[s]["covered"] >= 0
        assert 0.0 <= cov[s]["pct"] <= 100.0
    assert cov["expected_verdicts"] > 0
