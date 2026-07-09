"""Every authored pack validates clean; Pack D stages fully locally (no .43)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from uat.conductor.app import create_app
from uat.conductor.contract.coverage import pack_coverage
from uat.conductor.contract.ledger import FeatureLedger
from uat.conductor.contract.scenarios import list_packs, load_pack, validate_scenario
from uat.conductor.db import Database
from uat.conductor.induction.decks import DeckRegistry
from uat.conductor.induction.recipes import RecipeRegistry
from uat.conductor.runs import RunManager

EXPECTED_PACKS = {"smoke", "pack-d-honest-failure", "pack-a-aftercare", "pack-c-dictation-grounding"}


def test_expected_packs_present():
    assert EXPECTED_PACKS <= set(list_packs())


def test_every_pack_validates_clean():
    ledger = FeatureLedger.load()
    rn = set(RecipeRegistry().names())
    dn = set(DeckRegistry().names())
    for pack in list_packs():
        scenarios = load_pack(pack)
        assert scenarios, f"{pack} has no scenarios"
        errors = []
        for s in scenarios:
            errors += validate_scenario(s, ledger_keys=ledger.keys(), recipe_names=rn, deck_names=dn)
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


def test_pack_d_and_c_carry_per_surface_na():
    for pack in ("pack-d-honest-failure", "pack-c-dictation-grounding"):
        scenarios = load_pack(pack)
        na = [
            v for s in scenarios for st in s.steps
            for v in st.resolved_surfaces(s.surfaces).values() if not v["applicable"]
        ]
        assert na and all(v["reason"] for v in na), f"{pack} n/a must carry reasons"


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
