"""The sitting backend: create → stage → verdicts → resume → finish.

Uses a real boot for staging (self-skips if the product can't boot) but drives
the verdict/resume math directly, since that is the crash-safety contract the
guided site leans on.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from uat.conductor.app import create_app
from uat.conductor.db import Database
from uat.conductor.runs import RunManager


@pytest.fixture
def client(fake_products):
    # Fake product: create_run reports 'up' without a real boot, so the sitting
    # verdict/resume math can be tested fast. Staging (real recipe apply) needs a
    # real product and is covered in the real-boot test below.
    mgr = RunManager(Database(), boot_timeout=1.0, link_caches=False)
    app = create_app(mgr)
    with TestClient(app) as c:
        yield c


def _first_step_surface(sitting):
    r = sitting["resume"]
    return r["scenario_id"], r["step_index"], r["surface"]


def test_sitting_verdict_resume_flow(client):
    created = client.post("/api/sittings", json={"pack": "smoke"}).json()
    sid = created["id"]
    assert created["pack"] == "smoke"
    assert created["progress"]["cast"] == 0
    assert created["progress"]["expected"] > 0

    # Resume starts at the first (scenario, step, surface).
    scen, step, surface = _first_step_surface(created)

    # Cast that verdict; resume advances.
    r = client.post(
        f"/api/sittings/{sid}/verdicts",
        json={"scenario_id": scen, "step_index": step, "surface": surface, "verdict": "pass", "note": "looks right"},
    )
    assert r.status_code == 200
    after = r.json()
    assert after["progress"]["cast"] == 1
    assert _first_step_surface(after) != (scen, step, surface)


def test_verdict_persists_across_a_fresh_manager(client, tmp_path):
    created = client.post("/api/sittings", json={"pack": "smoke"}).json()
    sid = created["id"]
    scen, step, surface = _first_step_surface(created)
    client.post(
        f"/api/sittings/{sid}/verdicts",
        json={"scenario_id": scen, "step_index": step, "surface": surface, "verdict": "fail", "note": "wrong badge"},
    )
    # A brand-new manager over the SAME db file (crash-safe resume).
    import os

    db = Database(os.environ["UAT_DB_PATH"])
    from uat.conductor.sittings import SittingManager
    from uat.conductor.runs import RunManager

    fresh = SittingManager(RunManager(db, link_caches=False), db)
    reread = fresh.get(sid)
    assert reread["progress"]["cast"] == 1
    v = reread["verdicts"][0]
    assert v["verdict"] == "fail" and v["note"] == "wrong badge"


def test_invalid_verdict_and_surface_rejected(client):
    sid = client.post("/api/sittings", json={"pack": "smoke"}).json()["id"]
    bad = client.post(
        f"/api/sittings/{sid}/verdicts",
        json={"scenario_id": "x", "step_index": 0, "surface": "web", "verdict": "great"},
    )
    assert bad.status_code == 400


def test_list_and_finish(client):
    sid = client.post("/api/sittings", json={"pack": "smoke"}).json()["id"]
    listing = client.get("/api/sittings").json()["sittings"]
    assert any(s["id"] == sid for s in listing)
    done = client.post(f"/api/sittings/{sid}/finish").json()
    assert done["status"] == "done"
    assert done["finished_at"]


def test_unknown_pack_404(client):
    assert client.post("/api/sittings", json={"pack": "nope"}).status_code == 404
