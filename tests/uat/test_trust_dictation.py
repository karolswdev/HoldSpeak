"""Two fully-local harness-backlog probes: honest learning-count + key-never-syncs."""

from __future__ import annotations

import pytest

from uat.conductor.db import Database
from uat.conductor.runs import RunManager


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


def test_learned_correction_taught_has_honest_count(real_manager):
    run = real_manager.create_run(deck="golden-local")
    if run.status != "up":
        pytest.skip("product did not boot")
    result = real_manager.apply_recipe(run.id, "learned-correction-taught")
    assert result.probe["ok"], result.probe
    # The digest reads a real count, not vacuous.
    digest = real_manager.product_client(run.id).get_json("/api/dictation/learning-digest")
    assert digest["totals"]["corrections_made"] >= 1


def test_profile_key_never_syncs_is_a_real_attack(real_manager):
    run = real_manager.create_run(deck="golden-local")
    if run.status != "up":
        pytest.skip("product did not boot")
    result = real_manager.apply_recipe(run.id, "profile-key-never-syncs")
    # Non-vacuous: profile_exists forced the create; the secret is absent DESPITE it.
    assert result.probe["ok"], result.probe
    assert result.already_satisfied is False
    blob = str(real_manager.product_client(run.id).get_json("/api/profiles"))
    assert "UAT-SECRET-KEY-DO-NOT-LEAK" not in blob
    assert any(p["id"] == "uat-leaky-profile" for p in real_manager.product_client(run.id).get_json("/api/profiles")["profiles"])
