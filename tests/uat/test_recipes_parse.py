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
    recipe = RecipeRegistry().load("first-run-no-model")
    assert recipe.link_caches is False
    assert recipe.probe == [{"first_run_pending": True}]


def test_first_run_probe_does_not_treat_optional_llm_as_a_readiness_gate():
    from uat.conductor.induction.probes import ProbeEvaluator

    class Client:
        def get_json(self, path):
            assert path == "/api/setup/status"
            return {"first_run": True, "overall": "ready"}

    report = ProbeEvaluator(Client()).evaluate([{"first_run_pending": True}])
    assert report.ok is True
    assert "overall='ready'" in report.results[0].detail


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


def test_mesh_dispatch_recipe_present_and_composes():
    reg = RecipeRegistry()
    assert "mesh-run-on-worker" in reg.names()
    # It rides the live-worker + authored-run stage, so mesh-run-ready folds in.
    assert reg.resolve_order("mesh-run-on-worker")[:2] == ["mesh-node-alive", "mesh-run-ready"]
    assert reg.load("mesh-run-on-worker").requires_intel is True


def test_cloud_egress_recipe_is_local_and_composes_seeded_control():
    reg = RecipeRegistry()
    assert "egress-cloud-card" in reg.names()
    assert reg.resolve_order("egress-cloud-card") == [
        "seeded-desk",
        "egress-cloud-card",
    ]
    assert reg.load("egress-cloud-card").deck == "cloud-egress"
    assert reg.load("egress-cloud-card").requires_intel is False


def test_every_recipe_probe_kind_resolves():
    """A recipe naming a probe kind with no `_check_` method would fail only at
    apply-time on real metal; catch the typo here, no LAN needed."""
    from uat.conductor.induction.probes import ProbeEvaluator
    from uat.conductor.induction.recipes import _split_action  # reuse: same single-key shape

    reg = RecipeRegistry()
    for name in reg.names():
        for assertion in reg.load(name).probe:
            kind, _ = _split_action(assertion)
            assert hasattr(ProbeEvaluator, f"_check_{kind}"), f"{name}: unknown probe {kind!r}"
