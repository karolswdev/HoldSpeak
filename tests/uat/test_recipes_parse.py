"""Recipe parsing, include composition, and cycle refusal."""

from __future__ import annotations

import pytest

from uat.conductor.induction.recipes import RecipeError, RecipeRegistry

SMOKE_RECIPES = {
    "fresh-desk",
    "seeded-desk",
    "intel-endpoint-dead",
    "first-run-no-model",
    "meeting-just-ended-open-actions",
    "mesh-node-alive",
    "mesh-node-just-died",
}


def test_smoke_recipes_present():
    names = set(RecipeRegistry().names())
    assert SMOKE_RECIPES <= names, f"missing recipes: {SMOKE_RECIPES - names}"


def test_recipes_parse_and_declare_a_deck():
    reg = RecipeRegistry()
    for name in reg.names():
        r = reg.load(name)
        assert r.deck, f"{name} declares no deck"


def test_intel_recipes_flagged_requires_intel():
    reg = RecipeRegistry()
    assert reg.load("meeting-just-ended-open-actions").requires_intel is True
    assert reg.load("mesh-node-alive").requires_intel is True
    assert reg.load("fresh-desk").requires_intel is False


def test_first_run_recipe_unlinks_caches():
    assert RecipeRegistry().load("first-run-no-model").link_caches is False


def test_include_cycle_refuses_at_load(tmp_path):
    (tmp_path / "a.yaml").write_text("title: A\ndeck: golden-local\nincludes: [b]\n")
    (tmp_path / "b.yaml").write_text("title: B\ndeck: golden-local\nincludes: [a]\n")
    reg = RecipeRegistry(tmp_path)
    with pytest.raises(RecipeError, match="cycle"):
        reg.resolve_order("a")


def test_include_order_is_deps_first(tmp_path):
    (tmp_path / "base.yaml").write_text("title: base\ndeck: golden-local\n")
    (tmp_path / "mid.yaml").write_text("title: mid\ndeck: golden-local\nincludes: [base]\n")
    (tmp_path / "top.yaml").write_text("title: top\ndeck: golden-local\nincludes: [mid]\n")
    order = RecipeRegistry(tmp_path).resolve_order("top")
    assert order == ["base", "mid", "top"]


def test_unknown_recipe_raises():
    with pytest.raises(RecipeError):
        RecipeRegistry().load("no-such-recipe")
