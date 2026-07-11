"""Multi-campaign UAT closeout is exact, commit-coherent, and fail-closed."""

from __future__ import annotations

from copy import deepcopy

from fastapi.testclient import TestClient

from uat.conductor.app import create_app
from uat.conductor.closeouts import CloseoutSpec, evaluate_packets
from uat.conductor.contract.scenarios import load_pack
from uat.conductor.db import Database
from uat.conductor.runs import RunManager


COMMIT = "a" * 40


def _good_value(policy):
    if policy.operator == "present":
        return 1
    return policy.threshold


def _packet(
    spec: CloseoutSpec, pack: str, *, generated_at: str = "2026-07-11T00:00:00+00:00"
):
    requirement = next(item for item in spec.campaigns if item.pack == pack)
    scenarios = load_pack(pack)
    verdicts = []
    for scenario in scenarios:
        for step in scenario.steps:
            for slot in step.execution_slots(scenario):
                verdicts.append(
                    {
                        "pack": pack,
                        "scenario_id": scenario.id,
                        "step_index": step.index,
                        "execution_target": slot.target,
                        "form_factor": slot.form_factor,
                        "slot_id": slot.id,
                        "verdict": "pass",
                        "measurements": {
                            prompt.key: _good_value(spec.metric_policies[prompt.key])
                            for prompt in step.measurements
                            if prompt.required
                        },
                    }
                )
    devices = []
    if requirement.require_paired_device_attestations:
        for slot_id in requirement.required_slots:
            target, form = slot_id.split(":", 1)
            devices.append(
                {
                    "execution_target": target,
                    "form_factor": form,
                    "device_name": f"Owner {form}",
                    "os_version": "26.0",
                    "bundle_id": "com.holdspeak.flagship",
                    "build_number": "92",
                    "install_source": "Xcode archive",
                    "pairing_verified": True,
                }
            )
    features = sorted(
        {feature for scenario in scenarios for feature in scenario.features}
    )
    return {
        "header": {
            "pack": pack,
            "git_commit": COMMIT,
            "generated_at": generated_at,
            "run_id": f"run-{pack}",
            "sitting_id": f"sitting-{pack}",
            "execution_slots_sat": list(requirement.required_slots),
            "protocol_schema": 2,
            "protocol_valid": True,
            "protocol_hash": f"protocol-{pack}",
        },
        "complete": True,
        "acceptance_status": "passed",
        "verdicts": verdicts,
        "coverage": {"cited_features": features},
        "findings": [],
        "device_sessions": devices,
    }


def _evaluate(spec, packets, *, clean=True):
    return evaluate_packets(
        spec,
        packets,
        repository_commit=COMMIT,
        repository_clean=clean,
        repository_requirement_results={
            item.id: {
                "id": item.id,
                "path": item.path,
                "passed": True,
                "detail": "test fixture",
            }
            for item in spec.repository_requirements
        },
    )


def test_phase92_closeout_accepts_exact_complete_same_commit_packets():
    spec = CloseoutSpec.load("phase-92")
    packets = [_packet(spec, requirement.pack) for requirement in spec.campaigns]
    report = _evaluate(spec, packets)
    assert report["ready"] is True
    assert report["status"] == "ready"
    assert len(report["selected_debriefs"]) == 2
    assert report["metrics"] and all(item["passed"] for item in report["metrics"])
    assert report["side_effects"].startswith("none")


def test_closeout_never_borrows_campaign_evidence_from_another_commit():
    spec = CloseoutSpec.load("phase-92")
    packets = [_packet(spec, requirement.pack) for requirement in spec.campaigns]
    packets[1]["header"]["git_commit"] = "b" * 40
    report = _evaluate(spec, packets)
    assert report["ready"] is False
    gap = next(
        item for item in report["gaps"] if item["code"] == "campaign-debrief-missing"
    )
    assert gap["campaign"] == "owner-09-phase92-native-close"
    assert gap["available_commits"] == ["b" * 40]


def test_closeout_uses_newest_attempt_for_campaign_not_an_older_pass():
    spec = CloseoutSpec.load("phase-92")
    old_web = _packet(
        spec, spec.campaigns[0].pack, generated_at="2026-07-10T00:00:00+00:00"
    )
    new_web = deepcopy(old_web)
    new_web["header"]["generated_at"] = "2026-07-11T00:00:00+00:00"
    new_web["header"]["run_id"] = "run-new-failed-attempt"
    new_web["verdicts"].pop()
    native = _packet(spec, spec.campaigns[1].pack)
    report = _evaluate(spec, [old_web, new_web, native])
    assert report["ready"] is False
    assert any(item["code"] == "verdict-missing" for item in report["gaps"])
    selected_web = next(
        item
        for item in report["selected_debriefs"]
        if item["campaign"] == spec.campaigns[0].pack
    )
    assert selected_web["run_id"] == "run-new-failed-attempt"


def test_closeout_blocks_dirty_tree_bad_metrics_and_missing_device_attestation():
    spec = CloseoutSpec.load("phase-92")
    web = _packet(spec, spec.campaigns[0].pack)
    native = _packet(spec, spec.campaigns[1].pack)
    measured = next(
        item for item in web["verdicts"] if "product_steps" in item["measurements"]
    )
    measured["measurements"]["product_steps"] = 4
    native["device_sessions"][0]["install_source"] = ""
    report = _evaluate(spec, [web, native], clean=False)
    codes = {item["code"] for item in report["gaps"]}
    assert {
        "repository-not-clean",
        "metric-threshold",
        "device-attestation-missing",
    }.issubset(codes)


def test_observation_requires_explicit_closeable_triage_and_disposition():
    spec = CloseoutSpec.load("phase-92")
    packets = [_packet(spec, requirement.pack) for requirement in spec.campaigns]
    web = packets[0]
    web["acceptance_status"] = "passed-with-observations"
    web["verdicts"][0]["verdict"] = "observe"
    web["findings"] = [{"id": "UAT-observe", "triage_state": "untriaged"}]
    assert any(
        item["code"] == "finding-unresolved"
        for item in _evaluate(spec, packets)["gaps"]
    )
    web["findings"][0].update(
        {"triage_state": "by-design", "disposition": "Expected platform behavior"}
    )
    assert _evaluate(spec, packets)["ready"] is True


def test_closeout_api_lists_policies_and_reports_gaps_without_writing(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("UAT_RUNS_ROOT", str(tmp_path / "runs"))
    manager = RunManager(Database(), boot_timeout=1.0, link_caches=False)
    with TestClient(create_app(manager)) as client:
        listing = client.get("/api/closeouts")
        assert listing.status_code == 200
        assert any(item["id"] == "phase-92" for item in listing.json()["closeouts"])
        report = client.get("/api/closeouts/phase-92")
        assert report.status_code == 200
        assert report.json()["ready"] is False
        assert report.json()["selected_debriefs"] == []
        assert client.get("/api/closeouts/does-not-exist").status_code == 404


def test_malformed_selected_packet_becomes_gaps_instead_of_crashing():
    spec = CloseoutSpec.load("phase-92")
    packets = [_packet(spec, requirement.pack) for requirement in spec.campaigns]
    packets[0]["verdicts"] = {"not": "a list"}
    packets[0]["findings"] = "not a list"
    packets[0]["header"]["protocol_schema"] = "nonsense"
    report = _evaluate(spec, packets)
    assert report["ready"] is False
    codes = {item["code"] for item in report["gaps"]}
    assert {"packet-schema", "invalid-protocol", "verdict-missing"}.issubset(codes)
