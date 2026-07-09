"""The scenario contract: schema validation (positive + negative) and surfaces."""

from __future__ import annotations

import pytest

from uat.conductor.contract.scenarios import (
    ScenarioError,
    load_scenario,
    validate_scenario,
)

LEDGER_KEYS = {"feat.one", "feat.two"}
RECIPES = {"seeded-desk", "fresh-desk"}
DECKS = {"golden-local", "bad-endpoint"}


def _write(tmp_path, text):
    p = tmp_path / "s.yaml"
    p.write_text(text)
    return p


def test_valid_scenario_loads_and_resolves_surfaces(tmp_path):
    p = _write(
        tmp_path,
        """
id: s1
title: A scenario
features: [feat.one]
recipes: [seeded-desk]
surfaces:
  web: yes
  ipad: yes
  iphone: {n/a: "not confirmed on iPhone"}
steps:
  - do: Do the thing
    expect: The thing happened
    where: /
""",
    )
    s = load_scenario(p, pack="smoke")
    assert s.id == "s1"
    assert s.surfaces["iphone"] == {"applicable": False, "reason": "not confirmed on iPhone"}
    step = s.steps[0]
    assert step.applicable_surfaces(s.surfaces) == ["web", "ipad"]
    # 1 step × 2 applicable surfaces = 2 expected verdicts.
    assert s.expected_verdict_count() == 2
    assert validate_scenario(s, ledger_keys=LEDGER_KEYS, recipe_names=RECIPES) == []


def test_missing_required_field_names_the_field(tmp_path):
    p = _write(tmp_path, "id: s1\ntitle: t\n")  # no steps is allowed to load; no id/title fails
    # Missing title:
    p2 = tmp_path / "s2.yaml"
    p2.write_text("id: only\nfeatures: [feat.one]\n")
    with pytest.raises(ScenarioError, match="missing required field 'title'"):
        load_scenario(p2)


def test_na_without_reason_fails_load(tmp_path):
    p = _write(
        tmp_path,
        """
id: s1
title: t
features: [feat.one]
recipes: [seeded-desk]
surfaces:
  iphone: {n/a: ""}
steps:
  - do: x
    expect: y
""",
    )
    with pytest.raises(ScenarioError, match="needs a stated reason"):
        load_scenario(p)


def test_unknown_ledger_key_and_recipe_fail_validation(tmp_path):
    p = _write(
        tmp_path,
        """
id: s1
title: t
features: [feat.one, feat.nope]
recipes: [seeded-desk, no-such-recipe]
steps:
  - do: x
    expect: y
""",
    )
    s = load_scenario(p)
    errors = validate_scenario(s, ledger_keys=LEDGER_KEYS, recipe_names=RECIPES)
    assert any("unknown ledger key: feat.nope" in e for e in errors)
    assert any("unknown recipe: no-such-recipe" in e for e in errors)


def test_scenario_with_no_features_fails(tmp_path):
    p = _write(tmp_path, "id: s\ntitle: t\nrecipes: [seeded-desk]\nsteps:\n  - do: x\n    expect: y\n")
    s = load_scenario(p)
    errors = validate_scenario(s, ledger_keys=LEDGER_KEYS, recipe_names=RECIPES)
    assert any("cites no features" in e for e in errors)


def test_step_with_every_surface_na_fails_validation(tmp_path):
    p = _write(
        tmp_path,
        """
id: s
title: t
features: [feat.one]
recipes: [seeded-desk]
surfaces:
  web: {n/a: "a"}
  ipad: {n/a: "b"}
  iphone: {n/a: "c"}
steps:
  - do: x
    expect: y
""",
    )
    s = load_scenario(p)
    errors = validate_scenario(s, ledger_keys=LEDGER_KEYS, recipe_names=RECIPES)
    assert any("no applicable surface" in e for e in errors)


def test_after_action_unknown_recipe_fails(tmp_path):
    p = _write(
        tmp_path,
        """
id: s
title: t
features: [feat.one]
recipes: [seeded-desk]
steps:
  - do: x
    expect: y
    after:
      - apply_recipe: no-such-recipe
""",
    )
    s = load_scenario(p)
    errors = validate_scenario(s, ledger_keys=LEDGER_KEYS, recipe_names=RECIPES, deck_names=DECKS)
    assert any("apply_recipe names unknown recipe: no-such-recipe" in e for e in errors)


def test_step_missing_do_or_expect_fails_load(tmp_path):
    p = _write(tmp_path, "id: s\ntitle: t\nfeatures: [feat.one]\nrecipes: [seeded-desk]\nsteps:\n  - do: only\n")
    with pytest.raises(ScenarioError, match="needs both 'do' and 'expect'"):
        load_scenario(p)
