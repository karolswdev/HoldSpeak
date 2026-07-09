"""The seeder creates every desk primitive type through public routes."""

from __future__ import annotations

import pytest

from uat.conductor.induction.seeds import PRIMITIVE_ROUTES, SeedManifest, SeedRegistry
from uat.conductor.db import Database
from uat.conductor.runs import RunManager


def test_manifest_parses_all_primitive_types_and_aliases():
    m = SeedManifest.from_doc(
        "t",
        {
            "zones": [{"id": "z", "name": "Z"}],          # alias -> directories
            "knowledge_blocks": [{"id": "k", "name": "K"}],  # alias -> kbs
            "recipes": [{"id": "r", "name": "R"}],
            "profiles": [{"id": "p", "name": "P", "kind": "onDevice"}],
        },
    )
    assert m.primitives["directories"][0]["id"] == "z"
    assert m.primitives["kbs"][0]["id"] == "k"
    assert "recipes" in m.primitives and "profiles" in m.primitives


def test_demo_seed_declares_zones_and_members():
    m = SeedRegistry().load("desk-zones-demo")
    zone = m.primitives["directories"][0]
    assert zone["member_ids"] == ["uat-seed-note-z1", "uat-seed-note-z2"]


@pytest.fixture
def real_manager(tmp_path, monkeypatch):
    monkeypatch.setenv("UAT_RUNS_ROOT", str(tmp_path / "_runs"))
    monkeypatch.setenv("UAT_DB_PATH", str(tmp_path / "_runs" / "uat.db"))
    monkeypatch.delenv("UAT_REAL_HOME", raising=False)
    mgr = RunManager(Database(), boot_timeout=60.0, link_caches=True)
    try:
        yield mgr
    finally:
        mgr.teardown_all()


def test_seed_all_primitive_types_against_real_product(real_manager):
    run = real_manager.create_run(deck="golden-local")
    if run.status != "up":
        pytest.skip("product did not boot")
    outcome = real_manager.apply_seed(run.id, "desk-zones-demo")
    assert outcome["errors"] == [], outcome["errors"]
    assert outcome["applied"].get("directories") == 1
    assert outcome["applied"].get("kbs") == 1
    assert outcome["applied"].get("notes") == 2
    assert outcome["applied"].get("recipes") == 1
    assert outcome["applied"].get("profiles") == 1

    client = real_manager.product_client(run.id)
    # The zone exists with both notes filed into it (read back through the route).
    dirs = client.get_json("/api/directories")["directories"]
    zone = next(d for d in dirs if d["id"] == "uat-seed-zone-demo")
    assert set(zone.get("member_ids", [])) == {"uat-seed-note-z1", "uat-seed-note-z2"}
    # And the primitives are all there, indistinguishable from user-made.
    assert any(n["id"] == "uat-seed-note-z1" for n in client.get_json("/api/notes")["notes"])
    assert any(k["id"] == "uat-seed-kb-demo" for k in client.get_json("/api/kbs")["kbs"])


def test_seed_is_idempotent(real_manager):
    run = real_manager.create_run(deck="golden-local")
    if run.status != "up":
        pytest.skip("product did not boot")
    real_manager.apply_seed(run.id, "desk-zones-demo")
    client = real_manager.product_client(run.id)
    before = len(client.get_json("/api/notes")["notes"])
    real_manager.apply_seed(run.id, "desk-zones-demo")  # again
    after = len(client.get_json("/api/notes")["notes"])
    assert before == after  # deterministic ids upsert — no duplicate desk
