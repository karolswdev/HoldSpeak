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
    """An incomplete smoke sitting with a target-qualified desktop failure."""
    sitting = client.post("/api/sittings", json={"pack": "smoke"}).json()
    sid = sitting["id"]
    scen = sitting["scenarios"][0]
    client.mgr.db.upsert_scenario_stage(
        {
            "run_id": sitting["run"]["id"],
            "pack": sitting["pack"],
            "scenario_id": scen["id"],
            "status": "done",
            "result_json": "{}",
            "error": None,
            "manual_confirmed": 0,
            "created_at": "2026-07-09T00:00:00+00:00",
            "updated_at": "2026-07-09T00:00:00+00:00",
        }
    )
    step0 = scen["steps"][0]
    slots = [slot["id"] for slot in step0["execution_slots"]]
    assert slots == ["web_react:desktop"]
    response = client.post(
        f"/api/sittings/{sid}/verdicts",
        json={
            "scenario_id": scen["id"],
            "step_index": 0,
            "slot_id": slots[0],
            "verdict": "fail",
            "note": f"fail note on {slots[0]}",
        },
    )
    assert response.status_code == 200, response.text
    return sid, scen["id"], slots


def _generate(client, sitting_id):
    """Exercise packet semantics below the HTTP unfinished-sitting gate."""
    return client.app.state.debrief.generate(sitting_id)


def test_debrief_generates_both_files_and_findings(client):
    sid, scen_id, slots = _sitting_with_verdicts(client)
    res = _generate(client, sid)
    assert res["md"].endswith("debrief.md")
    assert res["json"].endswith("debrief.json")
    packet = res["packet"]
    # The web fail became one finding; passes did not.
    assert len(packet["findings"]) == 1
    f = packet["findings"][0]
    assert f["verdict"] == "fail"
    assert f["id"].startswith("UAT-")
    assert "log_slice" in f
    # Score and coverage retain the exact implementation-qualified slot.
    assert set(packet["scores"]) == {"web_react:desktop"}
    assert set(packet["coverage"]["slots"]) == {"web_react:desktop"}
    assert f["slot_id"] == "web_react:desktop"
    assert f["execution_target"] == "web_react"
    assert f["form_factor"] == "desktop"
    assert packet["coverage"]["overall"]["total"] > 0
    assert packet["complete"] is False
    assert packet["acceptance_status"] == "in-progress"


def test_debrief_json_schema_stable(client):
    sid, *_ = _sitting_with_verdicts(client)
    packet = _generate(client, sid)["packet"]
    assert set(packet.keys()) >= {
        "header", "scores", "coverage", "findings", "verdicts", "verdict_totals"
    }
    assert set(packet["verdict_totals"].keys()) == {
        "pass", "fail", "partial", "observe", "skip"
    }
    assert packet["header"]["protocol_hash"]
    assert packet["header"]["protocol_schema"] == 2
    assert packet["header"]["protocol_valid"] is True


def test_finding_cross_slot_data_uses_slot_ids_and_never_infers_parity(client):
    sid, scen_id, slots = _sitting_with_verdicts(client)
    packet = _generate(client, sid)["packet"]
    f = packet["findings"][0]
    assert f["cross_slot"] == {
        "all_slots": {"web_react:desktop": "fail"},
        "passed_on": [],
        "is_split": False,
    }


def test_triage_roundtrips_and_survives_regeneration(client):
    sid, *_ = _sitting_with_verdicts(client)
    packet = _generate(client, sid)["packet"]
    fid = packet["findings"][0]["id"]

    r = client.patch(f"/api/findings/{fid}", json={"triage_state": "fix", "disposition": "real bug"})
    assert r.status_code == 200
    assert r.json()["triage_state"] == "fix"

    # Regenerate — the disposition the human set must survive.
    packet2 = _generate(client, sid)["packet"]
    f2 = next(f for f in packet2["findings"] if f["id"] == fid)
    assert f2["triage_state"] == "fix"
    assert f2["disposition"] == "real bug"


def test_backlog_block_renders_fix_findings(client):
    sid, *_ = _sitting_with_verdicts(client)
    packet = _generate(client, sid)["packet"]
    fid = packet["findings"][0]["id"]
    client.patch(f"/api/findings/{fid}", json={"triage_state": "fix", "disposition": "real bug"})

    block = client.get(f"/api/sittings/{sid}/findings/backlog-block").json()["block"]
    assert "| # | Candidate | Type | Source | Signal |" in block
    assert fid in block
    assert "debrief.md" in block


def test_backlog_block_empty_without_fix(client):
    sid, *_ = _sitting_with_verdicts(client)
    _generate(client, sid)
    block = client.get(f"/api/sittings/{sid}/findings/backlog-block").json()["block"]
    assert "No `fix` findings" in block


def test_corrected_verdict_removes_stale_triaged_finding(client):
    sid, scen_id, slots = _sitting_with_verdicts(client)
    packet = _generate(client, sid)["packet"]
    fid = packet["findings"][0]["id"]
    client.patch(
        f"/api/findings/{fid}",
        json={"triage_state": "fix", "disposition": "was a bug"},
    )
    client.post(
        f"/api/sittings/{sid}/verdicts",
        json={
            "scenario_id": scen_id,
            "step_index": 0,
            "slot_id": slots[0],
            "verdict": "pass",
            "note": "rechecked",
        },
    )
    packet = _generate(client, sid)["packet"]
    assert packet["findings"] == []
    block = client.get(f"/api/sittings/{sid}/findings/backlog-block").json()["block"]
    assert "No `fix` findings" in block


def test_invalid_triage_state_rejected(client):
    sid, *_ = _sitting_with_verdicts(client)
    packet = _generate(client, sid)["packet"]
    fid = packet["findings"][0]["id"]
    assert client.patch(f"/api/findings/{fid}", json={"triage_state": "maybe"}).status_code == 400


def test_triage_requires_a_disposition(client):
    sid, *_ = _sitting_with_verdicts(client)
    packet = _generate(client, sid)["packet"]
    fid = packet["findings"][0]["id"]
    response = client.patch(
        f"/api/findings/{fid}", json={"triage_state": "fix"}
    )
    assert response.status_code == 400
    assert "disposition is required" in response.json()["detail"]


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


def test_zero_verdict_debrief_is_in_progress_not_passed(client):
    sitting = client.post("/api/sittings", json={"pack": "smoke"}).json()
    public = client.post(f"/api/sittings/{sitting['id']}/debrief")
    assert public.status_code == 409
    assert "unfinished sitting" in public.json()["detail"]
    packet = _generate(client, sitting["id"])["packet"]
    assert packet["verdict_totals"] == {
        "pass": 0,
        "fail": 0,
        "partial": 0,
        "observe": 0,
        "skip": 0,
    }
    assert packet["scores"] == {}
    assert packet["complete"] is False
    assert packet["acceptance_status"] == "in-progress"


def test_incomplete_all_passes_cannot_report_passed(client):
    sitting = client.post("/api/sittings", json={"pack": "smoke"}).json()
    scenario = sitting["scenarios"][0]
    client.mgr.db.upsert_scenario_stage(
        {
            "run_id": sitting["run"]["id"],
            "pack": sitting["pack"],
            "scenario_id": scenario["id"],
            "status": "done",
            "result_json": "{}",
            "error": None,
            "manual_confirmed": 0,
            "created_at": "2026-07-09T00:00:00+00:00",
            "updated_at": "2026-07-09T00:00:00+00:00",
        }
    )
    slot_id = scenario["steps"][0]["execution_slots"][0]["id"]
    response = client.post(
        f"/api/sittings/{sitting['id']}/verdicts",
        json={
            "scenario_id": scenario["id"],
            "step_index": 0,
            "slot_id": slot_id,
            "verdict": "pass",
        },
    )
    assert response.status_code == 200, response.text
    public = client.post(f"/api/sittings/{sitting['id']}/debrief")
    assert public.status_code == 409
    packet = _generate(client, sitting["id"])["packet"]
    assert packet["scores"]["web_react:desktop"]["pass"] == 1
    assert packet["complete"] is False
    assert packet["acceptance_status"] == "in-progress"


def test_log_slice_falls_back_to_tail_without_timestamps():
    lines = [f"line {i}" for i in range(100)]
    out = _log_slice(lines, None)
    assert "line 99" in out
    assert "line 0" not in out
