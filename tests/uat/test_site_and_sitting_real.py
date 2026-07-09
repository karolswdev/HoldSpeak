"""The whole guided-site loop, driven the way the browser drives it.

Serves the built SPA, then drives a real staged run through the conductor's
sitting API — create → stage → cast a verdict per surface → resume advances.
This is a harness self-test (the verdicts are cast by the test, NOT a sitting).
Self-skips if the product cannot boot here.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from uat.conductor.app import _site_dist, create_app
from uat.conductor.db import Database
from uat.conductor.runs import RunManager


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


def test_built_site_is_served_at_root(real_client):
    if not (_site_dist() / "index.html").exists():
        pytest.skip("guided site not built (uat/web/dist absent)")
    r = real_client.get("/")
    assert r.status_code == 200
    assert 'id="root"' in r.text  # the SPA mount point


def test_full_sitting_loop_stages_and_advances(real_client):
    created = real_client.post("/api/sittings", json={"pack": "smoke"}).json()
    sid = created["id"]
    if created["run"] is None or created["run"]["status"] != "up":
        pytest.skip("product did not boot; sitting loop unexercised")

    # The first scenario in resume order is the local seeded-desk walk.
    scen_id = created["resume"]["scenario_id"]
    staged = real_client.post(f"/api/sittings/{sid}/stage", json={"scenario_id": scen_id})
    assert staged.status_code == 200, staged.text
    body = staged.json()
    if not body["ok"]:
        pytest.skip(f"staging needs the LAN or failed: {body}")

    # Cast a verdict for every applicable surface of the current step.
    sitting = real_client.get(f"/api/sittings/{sid}").json()
    resume = sitting["resume"]
    scenario = next(s for s in sitting["scenarios"] if s["id"] == resume["scenario_id"])
    step = scenario["steps"][resume["step_index"]]
    applicable = [s for s, v in step["surfaces"].items() if v["applicable"]]
    assert applicable, "step must have an applicable surface"

    last = sitting
    for surface in applicable:
        last = real_client.post(
            f"/api/sittings/{sid}/verdicts",
            json={
                "scenario_id": scenario["id"],
                "step_index": step["index"],
                "surface": surface,
                "verdict": "pass",
                "note": f"harness self-test on {surface}",
            },
        ).json()

    # The step is fully answered → resume advanced past it.
    assert last["progress"]["cast"] >= len(applicable)
    new_resume = last["resume"]
    assert new_resume != resume  # moved on (next step or next scenario)
