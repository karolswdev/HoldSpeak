"""Protocol-v2 scenarios require an exact implementation target and form factor."""

from __future__ import annotations

import pytest

from uat.conductor.contract.scenarios import (
    ScenarioError,
    load_pack,
    load_scenario,
    validate_scenario,
)

LEDGER_KEYS = {"feat.one", "feat.two"}
RECIPES = {"seeded-desk", "fresh-desk"}
DECKS = {"golden-local", "bad-endpoint"}


def _write(tmp_path, text):
    path = tmp_path / "s.yaml"
    path.write_text(text)
    return path


def _errors(scenario):
    return validate_scenario(
        scenario,
        ledger_keys=LEDGER_KEYS,
        recipe_names=RECIPES,
    )


def test_valid_scenario_builds_target_qualified_slots(tmp_path):
    scenario = load_scenario(
        _write(
            tmp_path,
            """
id: s1
title: A scenario
execution_target: web_react
form_factors: [desktop, tablet_viewport]
features: [feat.one]
recipes: [seeded-desk]
steps:
  - do: Do the thing
    expect: The thing happened
    where: /
    form_factors: [desktop]
""",
        ),
        pack="smoke",
    )

    assert scenario.id == "s1"
    assert scenario.execution_target == "web_react"
    assert scenario.form_factors == ["desktop", "tablet_viewport"]
    assert [slot.id for slot in scenario.execution_slots] == [
        "web_react:desktop",
        "web_react:tablet_viewport",
    ]
    assert [slot.id for slot in scenario.steps[0].execution_slots(scenario)] == [
        "web_react:desktop"
    ]
    assert scenario.expected_verdict_count() == 1
    assert _errors(scenario) == []


@pytest.mark.parametrize("missing", ["execution_target", "form_factors"])
def test_missing_target_or_form_factors_is_rejected(tmp_path, missing):
    fields = {
        "execution_target": "execution_target: web_react\n",
        "form_factors": "form_factors: [desktop]\n",
    }
    fields[missing] = ""
    path = _write(
        tmp_path,
        f"""
id: s1
title: Missing identity
{fields['execution_target']}{fields['form_factors']}features: [feat.one]
recipes: [seeded-desk]
steps:
  - {{do: x, expect: y}}
""",
    )
    with pytest.raises(ScenarioError, match=rf"missing required field '{missing}'"):
        load_scenario(path)


def test_form_factors_must_be_explicit_nonempty_unique_list(tmp_path):
    for value in ("[]", "desktop", "[desktop, desktop]"):
        path = _write(
            tmp_path,
            f"""
id: s1
title: Bad forms
execution_target: web_react
form_factors: {value}
features: [feat.one]
recipes: [seeded-desk]
steps:
  - {{do: x, expect: y}}
""",
        )
        with pytest.raises(ScenarioError, match="form_factors"):
            load_scenario(path)


def test_legacy_scenario_and_step_surfaces_are_rejected(tmp_path):
    scenario_level = _write(
        tmp_path,
        """
id: s1
title: Legacy
execution_target: web_react
form_factors: [desktop]
features: [feat.one]
recipes: [seeded-desk]
surfaces: {web: yes}
steps:
  - {do: x, expect: y}
""",
    )
    with pytest.raises(ScenarioError, match="legacy 'surfaces' is forbidden"):
        load_scenario(scenario_level)

    step_level = _write(
        tmp_path,
        """
id: s1
title: Legacy step
execution_target: web_react
form_factors: [desktop]
features: [feat.one]
recipes: [seeded-desk]
steps:
  - do: x
    expect: y
    surfaces: {web: yes}
""",
    )
    with pytest.raises(ScenarioError, match="step 0 uses legacy 'surfaces'"):
        load_scenario(step_level)


@pytest.mark.parametrize("form_factor", ["ipad", "iphone"])
def test_web_react_cannot_use_native_device_form_factors(tmp_path, form_factor):
    scenario = load_scenario(
        _write(
            tmp_path,
            f"""
id: s1
title: React is not Swift
execution_target: web_react
form_factors: [{form_factor}]
features: [feat.one]
recipes: [seeded-desk]
steps:
  - {{do: x, expect: y}}
""",
        )
    )
    assert any(
        f"form factor '{form_factor}' is invalid for 'web_react'" in error
        for error in _errors(scenario)
    )


@pytest.mark.parametrize(
    "target,form_factor",
    [
        ("ios_flagship_swift", "desktop"),
        ("ios_flagship_swift", "tablet_viewport"),
        ("ios_companion_swift", "ipad_browser"),
        ("ios_classic_swift", "iphone_browser"),
    ],
)
def test_swift_targets_cannot_use_web_or_viewport_forms(
    tmp_path, target, form_factor
):
    scenario = load_scenario(
        _write(
            tmp_path,
            f"""
id: s1
title: Swift is not React
execution_target: {target}
form_factors: [{form_factor}]
features: [feat.one]
recipes: [seeded-desk]
steps:
  - {{do: x, expect: y}}
""",
        )
    )
    assert any(
        f"form factor '{form_factor}' is invalid for '{target}'" in error
        for error in _errors(scenario)
    )


def test_step_form_factors_must_be_scenario_subset(tmp_path):
    scenario = load_scenario(
        _write(
            tmp_path,
            """
id: s1
title: Step escapes scenario
execution_target: ios_flagship_swift
form_factors: [ipad]
features: [feat.one]
recipes: [seeded-desk]
steps:
  - do: x
    expect: y
    form_factors: [iphone]
""",
        )
    )
    assert any("step 0 form_factors must be a subset" in error for error in _errors(scenario))


def test_unknown_ledger_key_and_recipe_fail_validation(tmp_path):
    scenario = load_scenario(
        _write(
            tmp_path,
            """
id: s1
title: Unknown references
execution_target: web_react
form_factors: [desktop]
features: [feat.one, feat.nope]
recipes: [seeded-desk, no-such-recipe]
steps:
  - {do: x, expect: y}
""",
        )
    )
    errors = _errors(scenario)
    assert any("unknown ledger key: feat.nope" in error for error in errors)
    assert any("unknown recipe: no-such-recipe" in error for error in errors)


def test_scenario_with_no_features_fails(tmp_path):
    scenario = load_scenario(
        _write(
            tmp_path,
            """
id: s
title: No feature
execution_target: web_react
form_factors: [desktop]
recipes: [seeded-desk]
steps:
  - {do: x, expect: y}
""",
        )
    )
    assert any("cites no features" in error for error in _errors(scenario))


def test_after_action_unknown_recipe_fails(tmp_path):
    scenario = load_scenario(
        _write(
            tmp_path,
            """
id: s
title: Bad transition
execution_target: web_react
form_factors: [desktop]
features: [feat.one]
recipes: [seeded-desk]
steps:
  - do: x
    expect: y
    after:
      - apply_recipe: no-such-recipe
""",
        )
    )
    errors = validate_scenario(
        scenario,
        ledger_keys=LEDGER_KEYS,
        recipe_names=RECIPES,
        deck_names=DECKS,
    )
    assert any("apply_recipe names unknown recipe" in error for error in errors)


def test_step_missing_do_or_expect_fails_load(tmp_path):
    path = _write(
        tmp_path,
        """
id: s
title: Missing expectation
execution_target: web_react
form_factors: [desktop]
features: [feat.one]
recipes: [seeded-desk]
steps:
  - do: only
""",
    )
    with pytest.raises(ScenarioError, match="needs both 'do' and 'expect'"):
        load_scenario(path)


def test_initial_recipes_on_different_decks_fail_validation(tmp_path):
    scenario = load_scenario(
        _write(
            tmp_path,
            """
id: s
title: Cross-deck recipes
execution_target: web_react
form_factors: [desktop]
features: [feat.one]
recipes: [seeded-desk, fresh-desk]
steps:
  - {do: x, expect: y}
""",
        )
    )
    errors = validate_scenario(
        scenario,
        ledger_keys=LEDGER_KEYS,
        recipe_names=RECIPES,
        recipe_decks={"seeded-desk": "golden-local", "fresh-desk": "no-model"},
    )
    assert any("initial recipes span multiple decks" in error for error in errors)


def test_step_verifies_must_map_every_declared_feature(tmp_path):
    scenario = load_scenario(
        _write(
            tmp_path,
            """
id: s
title: Incomplete traceability
execution_target: web_react
form_factors: [desktop]
features: [feat.one, feat.two]
recipes: [seeded-desk]
steps:
  - do: x
    expect: y
    verifies: [feat.one]
""",
        )
    )
    assert any(
        "mapping misses scenario feature(s): feat.two" in error
        for error in _errors(scenario)
    )


def test_campaign_rejects_unknown_and_duplicate_scenario_refs(tmp_path, monkeypatch):
    scenario_root = tmp_path / "scenarios"
    source_pack = scenario_root / "source"
    source_pack.mkdir(parents=True)
    (source_pack / "01.yaml").write_text(
        """
id: source-one
title: Source one
execution_target: web_react
form_factors: [desktop]
features: [feat.one]
recipes: [seeded-desk]
steps:
  - {do: x, expect: y}
"""
    )
    campaigns = tmp_path / "campaigns"
    campaigns.mkdir()
    monkeypatch.setenv("UAT_CAMPAIGNS_DIR", str(campaigns))

    (campaigns / "unknown.yaml").write_text(
        "scenarios:\n  - source/no-such-id\n"
    )
    with pytest.raises(ScenarioError, match="unknown id 'no-such-id'"):
        load_pack("unknown", directory=scenario_root)

    (campaigns / "duplicate.yaml").write_text(
        "scenarios:\n  - source/source-one\n  - source/source-one\n"
    )
    with pytest.raises(ScenarioError, match="duplicate scenario id: source-one"):
        load_pack("duplicate", directory=scenario_root)
