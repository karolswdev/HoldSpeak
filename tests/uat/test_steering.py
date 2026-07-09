"""Live steering staged through the product's own /api/coders routes.

Spawns a real tmux coder pane, proves peek shows it, the unarmed consent gate
refuses keys, arming grants + audits — all fully local (no .43). Self-skips if
tmux is absent or the product cannot boot; cleans up its tmux session.
"""

from __future__ import annotations

import shutil

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


@pytest.mark.skipif(shutil.which("tmux") is None, reason="tmux not installed")
def test_awaiting_pane_and_consent_gate(real_manager):
    run = real_manager.create_run(deck="golden-local")
    if run.status != "up":
        pytest.skip("product did not boot")
    result = real_manager.apply_recipe(run.id, "agent-pane-awaiting-input")
    assert result.probe["ok"], result.probe
    kinds = {r["kind"]: r for r in result.probe["results"]}
    assert kinds["pane_listed"]["ok"]
    assert kinds["pane_shows"]["ok"]
    # The consent gate: unarmed keys refuse.
    assert kinds["keys_refused_unarmed"]["ok"], kinds["keys_refused_unarmed"]


@pytest.mark.skipif(shutil.which("tmux") is None, reason="tmux not installed")
def test_arm_grants_and_audits(real_manager):
    run = real_manager.create_run(deck="golden-local")
    if run.status != "up":
        pytest.skip("product did not boot")
    result = real_manager.apply_recipe(run.id, "agent-pane-armed")
    assert result.probe["ok"], result.probe
    kinds = {r["kind"]: r for r in result.probe["results"]}
    assert kinds["grant_live"]["ok"], kinds["grant_live"]
    assert kinds["audit_min"]["ok"], kinds["audit_min"]
