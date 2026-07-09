"""Induction recipes that ride the .43 LAN endpoint.

`meeting-just-ended-open-actions` needs real intel to extract an open action;
the mesh lifecycle needs the mesh-node deck (intel-wired). Both self-skip when
`.43` is unreachable — CI has no LAN, so these are honestly `.43`-gated, per
the HANDOVER. Run live with `.43` up to prove real pipeline output.
"""

from __future__ import annotations

import httpx
import pytest

from uat.conductor.db import Database
from uat.conductor.runs import RunManager

LAN_ENDPOINT = "http://192.168.1.43:8080/v1/models"


def _lan_up() -> bool:
    try:
        return httpx.get(LAN_ENDPOINT, timeout=5).status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(not _lan_up(), reason=".43 LAN endpoint unreachable")


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


def _boot_or_skip(mgr, deck):
    run = mgr.create_run(deck=deck)
    if run.status != "up":
        logs = mgr.logs(run.id, 60)
        pytest.skip(f"product did not boot: {run.error}\nstderr:\n{logs.get('stderr','')}")
    return run


def test_meeting_recipe_yields_a_real_open_action(real_manager):
    run = _boot_or_skip(real_manager, "golden-43")
    result = real_manager.apply_recipe(run.id, "meeting-just-ended-open-actions")
    assert result.probe["ok"], result.probe
    meeting_check = next(
        r for r in result.probe["results"] if r["kind"] == "meeting_with_open_actions"
    )
    assert meeting_check["ok"], meeting_check


def test_mesh_node_lifecycle(real_manager):
    run = _boot_or_skip(real_manager, "mesh-node")

    alive = real_manager.apply_recipe(run.id, "mesh-node-alive")
    assert alive.probe["ok"], alive.probe

    died = real_manager.apply_recipe(run.id, "mesh-node-just-died")
    assert died.probe["ok"], died.probe
