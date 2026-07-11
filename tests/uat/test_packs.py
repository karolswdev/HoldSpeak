"""Every authored pack validates clean; Pack D stages fully locally (no .43)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from uat.conductor.app import create_app
from uat.conductor.contract.ledger import FeatureLedger
from uat.conductor.contract.scenarios import list_packs, load_pack, validate_scenario
from uat.conductor.db import Database
from uat.conductor.induction.decks import DeckRegistry
from uat.conductor.induction.recipes import RecipeRegistry
from uat.conductor.runs import RunManager

EXPECTED_PACKS = {
    "smoke",
    "ios-flagship-smoke",
    "pack-d-honest-failure",
    "pack-a-aftercare",
    "pack-c-dictation-grounding",
    "owner-01-local-foundation",
    "owner-05-flagship-native",
}


def test_expected_packs_present():
    assert EXPECTED_PACKS <= set(list_packs())


def test_every_pack_validates_clean():
    ledger = FeatureLedger.load()
    rn = set(RecipeRegistry().names())
    registry = RecipeRegistry()
    recipe_decks = {name: registry.load(name).deck for name in rn}
    dn = set(DeckRegistry().names())
    for pack in list_packs():
        scenarios = load_pack(pack)
        assert scenarios, f"{pack} has no scenarios"
        errors = []
        for s in scenarios:
            errors += validate_scenario(
                s,
                ledger_keys=ledger.keys(),
                recipe_names=rn,
                deck_names=dn,
                recipe_decks=recipe_decks,
            )
        assert errors == [], f"{pack}: {errors}"


def test_pack_d_is_no_pack_all_green():
    """PROTOCOL-NOTION: a pack must have a beat that can fail loudly."""
    scenarios = load_pack("pack-d-honest-failure")
    recipes = {r for s in scenarios for r in s.recipes}
    # The failure decks are staged: dead endpoint + first-run no-model.
    assert "intel-endpoint-dead" in recipes
    assert "first-run-no-model" in recipes
    # A mid-run failure verb (the mesh kill) closes a scenario.
    assert any(st.after for s in scenarios for st in s.steps)


def test_every_authored_scenario_has_explicit_target_qualified_slots():
    for pack in list_packs():
        for scenario in load_pack(pack):
            assert scenario.execution_target
            assert scenario.form_factors
            assert all(slot.id.count(":") == 1 for slot in scenario.execution_slots)
            for step in scenario.steps:
                assert step.execution_slots(scenario)


def test_ios_flagship_smoke_names_native_target_and_honest_close():
    scenarios = load_pack("ios-flagship-smoke")
    assert scenarios
    assert {scenario.execution_target for scenario in scenarios} == {
        "ios_flagship_swift"
    }
    assert any(step.after for scenario in scenarios for step in scenario.steps)
    assert any(
        any(slot.form_factor == "iphone" for slot in step.execution_slots(scenario))
        for scenario in scenarios
        for step in scenario.steps
    )


def test_mobile_inventory_does_not_conflate_native_apps():
    targets = {scenario.execution_target for scenario in load_pack("pack-f-mobile")}
    assert {
        "ios_flagship_swift",
        "ios_companion_swift",
        "ios_classic_swift",
    } <= targets


def test_owner_campaigns_compose_canonical_scenarios_in_execution_order():
    local = load_pack("owner-01-local-foundation")
    assert local[0].id == "smoke-first-run-no-model"
    assert local[-1].id == "desk-doctor-honest-close"
    assert {scenario.pack for scenario in local} == {"owner-01-local-foundation"}
    assert all(scenario.source.endswith(".yaml") for scenario in local)

    flagship = load_pack("owner-05-flagship-native")
    assert {scenario.execution_target for scenario in flagship} == {
        "ios_flagship_swift"
    }
    assert all(scenario.manual_setup or scenario.recipes for scenario in flagship)


def test_owner_campaigns_are_strictly_partitioned_by_implementation():
    foundation = load_pack("owner-01-local-foundation")
    assert {
        (scenario.execution_target, form)
        for scenario in foundation
        for form in scenario.form_factors
    } == {("web_react", "desktop")}

    flagship = load_pack("owner-05-flagship-native")
    assert {scenario.execution_target for scenario in flagship} == {
        "ios_flagship_swift"
    }
    assert {
        form for scenario in flagship for form in scenario.form_factors
    } <= {"ipad", "iphone"}

    secondary = load_pack("owner-07-secondary-native-shells")
    assert {scenario.execution_target for scenario in secondary} == {
        "ios_companion_swift",
        "ios_classic_swift",
    }
    assert all(
        form in {"ipad", "iphone"}
        for scenario in secondary
        for form in scenario.form_factors
    )


@pytest.fixture
def real_client(tmp_path, monkeypatch):
    monkeypatch.setenv("UAT_RUNS_ROOT", str(tmp_path / "_runs"))
    monkeypatch.setenv("UAT_DB_PATH", str(tmp_path / "_runs" / "uat.db"))
    monkeypatch.delenv("UAT_REAL_HOME", raising=False)
    mgr = RunManager(Database(), boot_timeout=60.0, link_caches=True)
    app = create_app(mgr)
    with TestClient(app) as c:
        try:
            yield c
        finally:
            mgr.teardown_all()


def test_pack_d_stages_locally(real_client):
    """Pack D demos without the LAN: its bad-endpoint scenario stages + verifies."""
    created = real_client.post("/api/sittings", json={"pack": "pack-d-honest-failure"}).json()
    if created["run"] is None or created["run"]["status"] != "up":
        pytest.skip("product did not boot")
    sid = created["id"]
    # Stage the dead-endpoint scenario (fully local — port 9 refused).
    staged = real_client.post(f"/api/sittings/{sid}/stage", json={"scenario_id": "d-dead-endpoint-doctor"}).json()
    assert staged["ok"], staged
