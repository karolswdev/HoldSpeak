"""CAD-2-02/03 — the /api/cadence/* routes over the Phase-1 substrate."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.db import get_database, reset_database
from holdspeak.web.context import WebContext
from holdspeak.web.routes.cadence import build_cadence_router


@pytest.fixture
def client(tmp_path: Path):
    reset_database()
    db = get_database(tmp_path / "routes.db")
    with db._connection() as c:
        c.execute("INSERT INTO meetings (id, title, started_at, created_at) "
                  "VALUES ('m1','Platform sync','2026-06-27T14:00:00','2026-06-27T14:00:00')")
        c.execute("INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state, created_at) "
                  "VALUES ('a1','m1','File the watchdog issue','Karol','2026-06-30','pending','reviewed','2026-06-26T10:00:00')")
    db.actuators.record_proposal(
        meeting_id="m1", window_id="m1:aftercare", plugin_id="github_issue_actuator",
        plugin_version="1.0", idempotency_key="k1", target="github", action="create_issue",
        preview="Create issue: watchdog around intel queue", reversible=False,
    )
    app = FastAPI()
    app.include_router(build_cadence_router(WebContext(get_state=lambda: {})))
    yield TestClient(app), db
    reset_database()


def test_status_is_off_by_default(client):
    c, _ = client
    r = c.get("/api/cadence/status")
    assert r.status_code == 200
    body = r.json()
    assert body["enabled"] is False
    assert body["egress"] == {"scope": "local", "label": "Local only"}


def test_run_now_then_loops_carry_evidence_and_next_action(client):
    c, _ = client
    assert c.post("/api/cadence/run-now").json()["projected"] == 2
    loops = c.get("/api/cadence/loops").json()["loops"]
    assert len(loops) == 2
    top = loops[0]
    assert top["evidence"] and top["evidence"][0]["deep_link"]
    assert top["next_action"]["kind"] in ("approve_proposal", "create_issue")
    assert top["egress"]["scope"] == "local"


def test_brief_route_leads_with_top_move(client):
    c, _ = client
    c.post("/api/cadence/run-now")
    b = c.get("/api/cadence/brief").json()
    assert b["headline"] and b["items"] and b["open_count"] >= 1
    assert b["items"][0]["next_action"]["title"]
    assert b["egress"]["scope"] == "local"


def test_closeout_recommends_and_batch_applies(client):
    c, db = client
    c.post("/api/cadence/run-now")
    co = c.get("/api/cadence/closeout").json()
    assert co["open_count"] >= 1 and co["recs"]
    assert all("action" in r and "reason" in r and "severity" in r for r in co["recs"])
    # batch-apply: snooze them all
    decisions = [{"loop_id": r["loop"]["id"], "action": "snooze"} for r in co["recs"]]
    res = c.post("/api/cadence/closeout/apply", json={"decisions": decisions}).json()
    assert res["applied"] == len(decisions) and res["skipped"] == 0
    assert all(l["status"] == "snoozed" for l in c.get("/api/cadence/loops").json()["loops"])


def test_audit_route_is_local_and_complete(client):
    c, _ = client
    c.post("/api/cadence/run-now")
    audit = c.get("/api/cadence/audit").json()
    assert audit["egress"]["scope"] == "local"
    assert audit["totals"]["loops"] >= 1
    assert "loops" in audit and "nudges" in audit and "policies" in audit


def test_history_lists_nudges(client):
    c, db = client
    c.post("/api/cadence/run-now")
    from holdspeak.cadence.models import Nudge
    loop_id = c.get("/api/cadence/loops").json()["loops"][0]["id"]
    db.cadence.record_nudge(Nudge(loop_id=loop_id, surface="web", title="pushed it"))
    hist = c.get("/api/cadence/history").json()["nudges"]
    assert hist and hist[0]["title"] == "pushed it" and hist[0]["surface"] == "web"


def test_loop_detail_404_then_ok(client):
    c, _ = client
    assert c.get("/api/cadence/loops/nope").status_code == 404
    c.post("/api/cadence/run-now")
    loop_id = c.get("/api/cadence/loops").json()["loops"][0]["id"]
    assert c.get(f"/api/cadence/loops/{loop_id}").json()["id"] == loop_id


def test_snooze_kill_close_mutate(client):
    c, db = client
    c.post("/api/cadence/run-now")
    loop_id = c.get("/api/cadence/loops").json()["loops"][0]["id"]

    snoozed = c.post(f"/api/cadence/loops/{loop_id}/snooze", json={"hours": 2}).json()
    assert snoozed["status"] == "snoozed" and snoozed["snoozed_until"]

    killed = c.post(f"/api/cadence/loops/{loop_id}/kill").json()
    assert killed["status"] == "killed"
    # killed loop drops out of the default (non-terminal) listing
    open_ids = [l["id"] for l in c.get("/api/cadence/loops").json()["loops"]]
    assert loop_id not in open_ids
    assert loop_id in [l["id"] for l in c.get("/api/cadence/loops?all=true").json()["loops"]]


def test_kill_survives_reprojection_via_route(client):
    c, _ = client
    c.post("/api/cadence/run-now")
    loop_id = c.get("/api/cadence/loops").json()["loops"][0]["id"]
    c.post(f"/api/cadence/loops/{loop_id}/kill")
    c.post("/api/cadence/run-now")  # re-project
    assert c.get(f"/api/cadence/loops/{loop_id}").json()["status"] == "killed"
