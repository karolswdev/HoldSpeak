"""The debrief packet, findings lifecycle, and the BACKLOG-block generator."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from uat.conductor.app import create_app
from uat.conductor.db import Database
from uat.conductor.debrief import _log_slice
from uat.conductor.runs import RunManager


@pytest.fixture
def client(fake_products):
    mgr = RunManager(Database(), boot_timeout=1.0, link_caches=False)
    app = create_app(mgr)
    with TestClient(app) as c:
        c.mgr = mgr
        yield c


def _sitting_with_verdicts(client):
    """A smoke sitting with a fail (web), a pass (ipad), and a partial elsewhere."""
    sitting = client.post("/api/sittings", json={"pack": "smoke"}).json()
    sid = sitting["id"]
    scen = sitting["scenarios"][0]
    step0 = scen["steps"][0]
    applicable = [s for s, v in step0["surfaces"].items() if v["applicable"]]
    verdicts = {applicable[0]: "fail", **{s: "pass" for s in applicable[1:]}}
    for surface, verdict in verdicts.items():
        client.post(
            f"/api/sittings/{sid}/verdicts",
            json={"scenario_id": scen["id"], "step_index": 0, "surface": surface,
                  "verdict": verdict, "note": f"{verdict} note on {surface}"},
        )
    return sid, scen["id"], applicable


def test_debrief_generates_both_files_and_findings(client):
    sid, scen_id, applicable = _sitting_with_verdicts(client)
    res = client.post(f"/api/sittings/{sid}/debrief").json()
    assert res["md"].endswith("debrief.md")
    assert res["json"].endswith("debrief.json")
    packet = res["packet"]
    # The web fail became one finding; passes did not.
    assert len(packet["findings"]) == 1
    f = packet["findings"][0]
    assert f["verdict"] == "fail"
    assert f["id"].startswith("UAT-")
    assert "log_slice" in f
    # Score per surface present, overall coverage carried.
    assert "web" in packet["scores"]
    assert packet["coverage"]["overall"]["total"] > 0


def test_debrief_json_schema_stable(client):
    sid, *_ = _sitting_with_verdicts(client)
    packet = client.post(f"/api/sittings/{sid}/debrief").json()["packet"]
    assert set(packet.keys()) >= {"header", "scores", "coverage", "findings", "verdict_totals"}
    assert set(packet["verdict_totals"].keys()) == {"pass", "fail", "partial", "skip"}


def test_cross_surface_split_is_one_finding_with_both(client):
    sid, scen_id, applicable = _sitting_with_verdicts(client)
    packet = client.post(f"/api/sittings/{sid}/debrief").json()["packet"]
    f = packet["findings"][0]
    if len(applicable) > 1:
        assert f["cross_surface"]["is_split"] is True
        assert applicable[1] in f["cross_surface"]["passed_on"]


def test_triage_roundtrips_and_survives_regeneration(client):
    sid, *_ = _sitting_with_verdicts(client)
    packet = client.post(f"/api/sittings/{sid}/debrief").json()["packet"]
    fid = packet["findings"][0]["id"]

    r = client.patch(f"/api/findings/{fid}", json={"triage_state": "fix", "disposition": "real bug"})
    assert r.status_code == 200
    assert r.json()["triage_state"] == "fix"

    # Regenerate — the disposition the human set must survive.
    packet2 = client.post(f"/api/sittings/{sid}/debrief").json()["packet"]
    f2 = next(f for f in packet2["findings"] if f["id"] == fid)
    assert f2["triage_state"] == "fix"
    assert f2["disposition"] == "real bug"


def test_backlog_block_renders_fix_findings(client):
    sid, *_ = _sitting_with_verdicts(client)
    packet = client.post(f"/api/sittings/{sid}/debrief").json()["packet"]
    fid = packet["findings"][0]["id"]
    client.patch(f"/api/findings/{fid}", json={"triage_state": "fix", "disposition": "real bug"})

    block = client.get(f"/api/sittings/{sid}/findings/backlog-block").json()["block"]
    assert "| # | Candidate | Type | Source | Signal |" in block
    assert fid in block
    assert "debrief.md" in block


def test_backlog_block_empty_without_fix(client):
    sid, *_ = _sitting_with_verdicts(client)
    client.post(f"/api/sittings/{sid}/debrief")
    block = client.get(f"/api/sittings/{sid}/findings/backlog-block").json()["block"]
    assert "No `fix` findings" in block


def test_invalid_triage_state_rejected(client):
    sid, *_ = _sitting_with_verdicts(client)
    packet = client.post(f"/api/sittings/{sid}/debrief").json()["packet"]
    fid = packet["findings"][0]["id"]
    assert client.patch(f"/api/findings/{fid}", json={"triage_state": "maybe"}).status_code == 400


def test_log_slice_windows_on_timestamps():
    lines = [
        "2026-07-09 10:00:00 INFO booting",
        "2026-07-09 10:04:59 INFO right before",
        "2026-07-09 10:05:10 ERROR the failure",
        "2026-07-09 10:30:00 INFO much later",
    ]
    out = _log_slice(lines, "2026-07-09T10:05:00", before=120, after=30)
    assert "right before" in out
    assert "the failure" in out
    assert "much later" not in out


def test_log_slice_falls_back_to_tail_without_timestamps():
    lines = [f"line {i}" for i in range(100)]
    out = _log_slice(lines, None)
    assert "line 99" in out
    assert "line 0" not in out
