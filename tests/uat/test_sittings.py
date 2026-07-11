"""Protocol-v2 sitting lifecycle, exact slots, and native attestations."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from uat.conductor.app import create_app
from uat.conductor.db import Database
from uat.conductor.runs import RunManager


@pytest.fixture
def client(fake_products):
    manager = RunManager(Database(), boot_timeout=1.0, link_caches=False)
    app = create_app(manager)
    with TestClient(app) as test_client:
        test_client.mgr = manager
        yield test_client


def _first_step_slot(sitting):
    resume = sitting["resume"]
    return resume["scenario_id"], resume["step_index"], resume["slot_id"]


def _mark_staged(client, sitting, scenario_id, *, manual_confirmed=0):
    client.mgr.db.upsert_scenario_stage(
        {
            "run_id": sitting["run"]["id"],
            "pack": sitting["pack"],
            "scenario_id": scenario_id,
            "status": "done",
            "result_json": "{}",
            "error": None,
            "manual_confirmed": manual_confirmed,
            "created_at": "2026-07-09T00:00:00+00:00",
            "updated_at": "2026-07-09T00:00:00+00:00",
        }
    )


def _register_device(
    client,
    sitting,
    *,
    target="ios_flagship_swift",
    form_factor="ipad",
    pairing_verified=True,
):
    before = {
        session["id"]
        for session in client.get(f"/api/sittings/{sitting['id']}").json()[
            "device_sessions"
        ]
    }
    response = client.post(
        f"/api/sittings/{sitting['id']}/device-sessions",
        json={
            "target": target,
            "form_factor": form_factor,
            "device_name": f"UAT {form_factor}",
            "os_version": "iOS 19.0",
            "bundle_id": f"com.example.{target}",
            "build_number": "20260709.1",
            "install_source": "TestFlight",
            "pairing_verified": pairing_verified,
        },
    )
    assert response.status_code == 200, response.text
    return next(
        session
        for session in response.json()["device_sessions"]
        if session["id"] not in before
    )


def test_sitting_verdict_resume_flow_uses_slot_id(client):
    created = client.post("/api/sittings", json={"pack": "smoke"}).json()
    assert created["progress"]["cast"] == 0
    assert created["protocol"]["schema"] == 2
    scenario_id, step_index, slot_id = _first_step_slot(created)
    assert slot_id == "web_react:desktop"
    _mark_staged(client, created, scenario_id)

    response = client.post(
        f"/api/sittings/{created['id']}/verdicts",
        json={
            "scenario_id": scenario_id,
            "step_index": step_index,
            "slot_id": slot_id,
            "verdict": "pass",
            "note": "looks right",
        },
    )
    assert response.status_code == 200, response.text
    after = response.json()
    assert after["progress"]["cast"] == 1
    assert _first_step_slot(after) != (scenario_id, step_index, slot_id)
    verdict = after["verdicts"][0]
    assert verdict["slot_id"] == "web_react:desktop"
    assert verdict["execution_target"] == "web_react"
    assert verdict["form_factor"] == "desktop"


def test_required_measurements_fail_closed_and_persist_as_structured_data(client):
    response = client.post(
        "/api/sittings", json={"pack": "owner-08-phase92-web-close"}
    )
    assert response.status_code == 201, response.text
    sitting = response.json()
    scenario_id, step_index, slot_id = _first_step_slot(sitting)
    _mark_staged(client, sitting, scenario_id, manual_confirmed=1)
    body = {
        "scenario_id": scenario_id,
        "step_index": step_index,
        "slot_id": slot_id,
        "verdict": "pass",
    }
    missing = client.post(f"/api/sittings/{sitting['id']}/verdicts", json=body)
    assert missing.status_code == 400
    assert "required measurements missing" in missing.json()["detail"]

    recorded_failure = client.post(
        f"/api/sittings/{sitting['id']}/verdicts",
        json={**body, "verdict": "fail", "note": "instrument unavailable"},
    )
    assert recorded_failure.status_code == 200, recorded_failure.text

    measurements = {
        "elapsed_seconds": "18.4", "product_steps": "2",
        "placement_decisions": "0", "technical_nouns": "1",
    }
    accepted = client.post(
        f"/api/sittings/{sitting['id']}/verdicts",
        json={**body, "measurements": measurements},
    )
    assert accepted.status_code == 200, accepted.text
    verdict = next(
        item for item in accepted.json()["verdicts"]
        if item["scenario_id"] == scenario_id and item["slot_id"] == slot_id
    )
    assert verdict["measurements"] == measurements


def test_verdict_persists_across_a_fresh_manager(client):
    created = client.post("/api/sittings", json={"pack": "smoke"}).json()
    scenario_id, step_index, slot_id = _first_step_slot(created)
    _mark_staged(client, created, scenario_id)
    response = client.post(
        f"/api/sittings/{created['id']}/verdicts",
        json={
            "scenario_id": scenario_id,
            "step_index": step_index,
            "slot_id": slot_id,
            "verdict": "fail",
            "note": "wrong badge",
        },
    )
    assert response.status_code == 200, response.text

    import os

    database = Database(os.environ["UAT_DB_PATH"])
    from uat.conductor.sittings import SittingManager

    fresh = SittingManager(RunManager(database, link_caches=False), database)
    reread = fresh.get(created["id"])
    assert reread["progress"]["cast"] == 1
    verdict = reread["verdicts"][0]
    assert verdict["verdict"] == "fail"
    assert verdict["slot_id"] == slot_id


def test_legacy_surface_payload_is_rejected(client):
    sitting = client.post("/api/sittings", json={"pack": "smoke"}).json()
    response = client.post(
        f"/api/sittings/{sitting['id']}/verdicts",
        json={
            "scenario_id": sitting["resume"]["scenario_id"],
            "step_index": sitting["resume"]["step_index"],
            "surface": "web",
            "verdict": "pass",
        },
    )
    assert response.status_code == 422
    assert "slot_id" in response.text


def test_invalid_verdict_is_rejected(client):
    sitting = client.post("/api/sittings", json={"pack": "smoke"}).json()
    scenario_id, step_index, slot_id = _first_step_slot(sitting)
    response = client.post(
        f"/api/sittings/{sitting['id']}/verdicts",
        json={
            "scenario_id": scenario_id,
            "step_index": step_index,
            "slot_id": slot_id,
            "verdict": "great",
        },
    )
    assert response.status_code == 400


def test_verdict_rejected_before_scenario_staging(client):
    sitting = client.post("/api/sittings", json={"pack": "smoke"}).json()
    scenario_id, step_index, slot_id = _first_step_slot(sitting)
    response = client.post(
        f"/api/sittings/{sitting['id']}/verdicts",
        json={
            "scenario_id": scenario_id,
            "step_index": step_index,
            "slot_id": slot_id,
            "verdict": "pass",
        },
    )
    assert response.status_code == 400
    assert "has not completed recipe staging" in response.json()["detail"]


def test_native_pack_requires_lan_device_mode(client):
    refused = client.post(
        "/api/sittings", json={"pack": "ios-flagship-smoke", "lan": False}
    )
    assert refused.status_code == 400
    assert "requires a device sitting" in refused.json()["detail"]

    created = client.post(
        "/api/sittings", json={"pack": "ios-flagship-smoke", "lan": True}
    )
    assert created.status_code == 201, created.text
    assert created.json()["run"]["lan"] is True


def test_native_verdict_requires_exact_pairing_verified_attestation(client):
    sitting_response = client.post(
        "/api/sittings", json={"pack": "ios-flagship-smoke", "lan": True}
    )
    assert sitting_response.status_code == 201, sitting_response.text
    sitting = sitting_response.json()
    scenario_id, step_index, slot_id = _first_step_slot(sitting)
    assert slot_id == "ios_flagship_swift:ipad"
    _mark_staged(client, sitting, scenario_id, manual_confirmed=1)

    body = {
        "scenario_id": scenario_id,
        "step_index": step_index,
        "slot_id": slot_id,
        "verdict": "pass",
    }
    missing = client.post(f"/api/sittings/{sitting['id']}/verdicts", json=body)
    assert missing.status_code == 400
    assert "matching device attestation" in missing.json()["detail"]

    unpaired = _register_device(client, sitting, pairing_verified=False)
    not_verified = client.post(
        f"/api/sittings/{sitting['id']}/verdicts",
        json={**body, "device_session_id": unpaired["id"]},
    )
    assert not_verified.status_code == 400
    assert "pairing has not been attested" in not_verified.json()["detail"]

    paired = _register_device(client, sitting, pairing_verified=True)
    accepted = client.post(
        f"/api/sittings/{sitting['id']}/verdicts",
        json={**body, "device_session_id": paired["id"]},
    )
    assert accepted.status_code == 200, accepted.text
    verdict = accepted.json()["verdicts"][0]
    assert verdict["slot_id"] == slot_id
    assert verdict["device_session_id"] == paired["id"]


def test_native_attestation_requires_all_device_facts(client):
    sitting = client.post(
        "/api/sittings", json={"pack": "ios-flagship-smoke", "lan": True}
    ).json()
    response = client.post(
        f"/api/sittings/{sitting['id']}/device-sessions",
        json={
            "target": "ios_flagship_swift",
            "form_factor": "ipad",
            "device_name": "",
            "os_version": "iOS 19.0",
            "bundle_id": "com.example.flagship",
            "build_number": "",
            "pairing_verified": True,
        },
    )
    assert response.status_code == 400
    assert "build_number" in response.json()["detail"]
    assert "device_name" in response.json()["detail"]


def test_native_attestation_is_bound_to_its_exact_sitting(client):
    first = client.post(
        "/api/sittings", json={"pack": "ios-flagship-smoke", "lan": True}
    ).json()
    second = client.post(
        "/api/sittings", json={"pack": "ios-flagship-smoke", "lan": True}
    ).json()
    attestation = _register_device(client, first)
    scenario_id, step_index, slot_id = _first_step_slot(second)
    _mark_staged(client, second, scenario_id, manual_confirmed=1)

    response = client.post(
        f"/api/sittings/{second['id']}/verdicts",
        json={
            "scenario_id": scenario_id,
            "step_index": step_index,
            "slot_id": slot_id,
            "device_session_id": attestation["id"],
            "verdict": "pass",
        },
    )
    assert response.status_code == 400
    assert "does not belong to this sitting" in response.json()["detail"]


def test_wrong_target_and_form_attestations_are_rejected(client):
    sitting_response = client.post(
        "/api/sittings",
        json={"pack": "owner-07-secondary-native-shells", "lan": True},
    )
    assert sitting_response.status_code == 201, sitting_response.text
    sitting = sitting_response.json()

    holdbar = next(
        scenario
        for scenario in sitting["scenarios"]
        if scenario["id"] == "f-holdbar-teleprompter"
    )
    macros = next(
        scenario
        for scenario in sitting["scenarios"]
        if scenario["id"] == "f-macros-fire"
    )
    _mark_staged(client, sitting, holdbar["id"], manual_confirmed=1)
    _mark_staged(client, sitting, macros["id"], manual_confirmed=1)

    classic_ipad = _register_device(
        client,
        sitting,
        target="ios_classic_swift",
        form_factor="ipad",
    )
    companion_ipad = _register_device(
        client,
        sitting,
        target="ios_companion_swift",
        form_factor="ipad",
    )

    wrong_form = client.post(
        f"/api/sittings/{sitting['id']}/verdicts",
        json={
            "scenario_id": holdbar["id"],
            "step_index": 0,
            "slot_id": "ios_classic_swift:iphone",
            "device_session_id": classic_ipad["id"],
            "verdict": "pass",
        },
    )
    assert wrong_form.status_code == 400
    assert "does not match the execution slot" in wrong_form.json()["detail"]

    wrong_target = client.post(
        f"/api/sittings/{sitting['id']}/verdicts",
        json={
            "scenario_id": macros["id"],
            "step_index": 0,
            "slot_id": "ios_classic_swift:ipad",
            "device_session_id": companion_ipad["id"],
            "verdict": "pass",
        },
    )
    assert wrong_target.status_code == 400
    assert "does not match the execution slot" in wrong_target.json()["detail"]


def test_list_and_incomplete_finish_is_rejected(client):
    sitting_id = client.post("/api/sittings", json={"pack": "smoke"}).json()["id"]
    listing = client.get("/api/sittings").json()["sittings"]
    assert any(item["id"] == sitting_id for item in listing)
    response = client.post(f"/api/sittings/{sitting_id}/finish")
    assert response.status_code == 400
    assert "cannot finish an incomplete sitting" in response.json()["detail"]


def test_complete_sitting_finishes_and_tears_down(client, tmp_path, monkeypatch):
    scenarios = tmp_path / "scenarios" / "tiny"
    scenarios.mkdir(parents=True)
    (scenarios / "01-one.yaml").write_text(
        """
id: tiny-one
title: One real check
execution_target: web_react
form_factors: [desktop]
features: [desk.web.front_door]
recipes: []
manual_setup: [Confirm the tiny world]
steps:
  - do: Look
    expect: It is present
"""
    )
    monkeypatch.setenv("UAT_SCENARIOS_DIR", str(tmp_path / "scenarios"))
    created_response = client.post("/api/sittings", json={"pack": "tiny"})
    assert created_response.status_code == 201, created_response.text
    created = created_response.json()
    client.post(
        f"/api/sittings/{created['id']}/manual-confirm",
        json={"scenario_id": "tiny-one"},
    )
    verdict = client.post(
        f"/api/sittings/{created['id']}/verdicts",
        json={
            "scenario_id": "tiny-one",
            "step_index": 0,
            "slot_id": "web_react:desktop",
            "verdict": "pass",
        },
    )
    assert verdict.status_code == 200, verdict.text
    done = client.post(f"/api/sittings/{created['id']}/finish").json()
    assert done["status"] == "done"
    assert done["finished_at"]
    assert done["run"]["status"] == "down"


def test_legacy_schema_one_sitting_is_review_only(client):
    sitting = client.post("/api/sittings", json={"pack": "smoke"}).json()
    snapshot_path = Path(sitting["protocol"]["snapshot"])
    snapshot = json.loads(snapshot_path.read_text())
    snapshot["schema"] = 1
    snapshot["scenarios"] = [
        {
            "id": "legacy-one",
            "title": "Legacy unqualified check",
            "pack": "smoke",
            "features": ["desk.front-door.spatial-objects"],
            "recipes": [],
            "surfaces": {
                "web": {"applicable": True, "reason": None},
                "ipad": {"applicable": False, "reason": "old n/a"},
                "iphone": {"applicable": False, "reason": "old n/a"},
            },
            "steps": [
                {
                    "index": 0,
                    "do": "Look",
                    "expect": "Old result",
                    "surfaces": {
                        "web": {"applicable": True, "reason": None},
                        "ipad": {"applicable": False, "reason": "old n/a"},
                        "iphone": {"applicable": False, "reason": "old n/a"},
                    },
                }
            ],
        }
    ]
    snapshot_path.write_text(json.dumps(snapshot))

    review = client.get(f"/api/sittings/{sitting['id']}").json()
    assert review["legacy_invalid"] is True
    assert review["protocol"]["schema"] == 1
    assert review["scenarios"][0]["execution_target"] == "legacy_unqualified"

    verdict = client.post(
        f"/api/sittings/{sitting['id']}/verdicts",
        json={
            "scenario_id": "legacy-one",
            "step_index": 0,
            "slot_id": "legacy_unqualified:web",
            "verdict": "pass",
        },
    )
    assert verdict.status_code == 400
    assert "review-only" in verdict.json()["detail"]

    finish = client.post(f"/api/sittings/{sitting['id']}/finish")
    assert finish.status_code == 400
    assert "preserved for review" in finish.json()["detail"]

    public_debrief = client.post(f"/api/sittings/{sitting['id']}/debrief")
    assert public_debrief.status_code == 409
    debrief = client.app.state.debrief.generate(sitting["id"])["packet"]
    assert debrief["acceptance_status"] == "invalid-protocol"
    assert debrief["header"]["protocol_valid"] is False


def test_unknown_pack_404(client):
    assert client.post("/api/sittings", json={"pack": "nope"}).status_code == 404


def test_sitting_uses_immutable_protocol_snapshot(client, tmp_path, monkeypatch):
    created = client.post("/api/sittings", json={"pack": "smoke"}).json()
    assert created["protocol"]["hash"]
    original_ids = [scenario["id"] for scenario in created["scenarios"]]

    empty = tmp_path / "empty-scenarios"
    empty.mkdir()
    monkeypatch.setenv("UAT_SCENARIOS_DIR", str(empty))
    reread = client.get(f"/api/sittings/{created['id']}").json()
    assert [scenario["id"] for scenario in reread["scenarios"]] == original_ids
    assert reread["protocol"]["hash"] == created["protocol"]["hash"]


def test_supersede_preserves_feedback_and_starts_current_protocol(client):
    created = client.post(
        "/api/sittings", json={"pack": "owner-01-local-foundation"}
    ).json()
    scenario_id, step_index, slot_id = _first_step_slot(created)
    _mark_staged(client, created, scenario_id)
    verdict = client.post(
        f"/api/sittings/{created['id']}/verdicts",
        json={
            "scenario_id": scenario_id,
            "step_index": step_index,
            "slot_id": slot_id,
            "verdict": "fail",
            "note": "important feedback",
        },
    )
    assert verdict.status_code == 200, verdict.text

    response = client.post(f"/api/sittings/{created['id']}/supersede")
    assert response.status_code == 201, response.text
    replacement = response.json()
    assert replacement["id"] != created["id"]
    assert replacement["superseded_sitting_id"] == created["id"]
    assert replacement["protocol"]["schema"] == 2
    assert replacement["progress"]["cast"] == 0

    old = client.get(f"/api/sittings/{created['id']}").json()
    assert old["status"] == "aborted"
    assert old["verdicts"][0]["note"] == "important feedback"
    rejected = client.post(
        f"/api/sittings/{created['id']}/verdicts",
        json={
            "scenario_id": scenario_id,
            "step_index": step_index,
            "slot_id": slot_id,
            "verdict": "pass",
        },
    )
    assert rejected.status_code == 400
    assert "closed sitting" in rejected.json()["detail"]


def test_campaign_snapshot_hashes_manifest_and_source_scenarios(client):
    created = client.post(
        "/api/sittings", json={"pack": "owner-01-local-foundation"}
    ).json()
    snapshot = json.loads(Path(created["protocol"]["snapshot"]).read_text())
    assets = set(snapshot["asset_hashes"])
    assert "uat/campaigns/owner-01-local-foundation.yaml" in assets
    assert any(
        path.endswith("scenarios/smoke/05-first-run-no-model.yaml")
        for path in assets
    )


def test_last_slot_verdict_executes_after_transition_once(client, monkeypatch):
    sitting = client.post("/api/sittings", json={"pack": "smoke"}).json()
    scenario = next(
        item
        for item in sitting["scenarios"]
        if item["id"] == "smoke-mesh-node-lifecycle"
    )
    step = scenario["steps"][0]
    _mark_staged(client, sitting, scenario["id"])
    calls = []

    def apply_recipe(run_id, name):
        calls.append((run_id, name))
        return SimpleNamespace(
            probe={"ok": True},
            to_dict=lambda: {"recipe": name, "probe": {"ok": True}},
        )

    monkeypatch.setattr(client.mgr, "apply_recipe", apply_recipe)
    result = sitting
    for slot in step["execution_slots"]:
        response = client.post(
            f"/api/sittings/{sitting['id']}/verdicts",
            json={
                "scenario_id": scenario["id"],
                "step_index": step["index"],
                "slot_id": slot["id"],
                "verdict": "pass",
            },
        )
        assert response.status_code == 200, response.text
        result = response.json()

    assert [name for _, name in calls] == ["mesh-node-just-died"]
    transition = next(
        row
        for row in result["transitions"]
        if row["scenario_id"] == scenario["id"] and row["step_index"] == 0
    )
    assert transition["status"] == "done"
    assert result["blocked_transition"] is None

    client.post(
        f"/api/sittings/{sitting['id']}/after",
        json={"scenario_id": scenario["id"], "step_index": 0},
    )
    assert len(calls) == 1, "a completed transition must be idempotent"
