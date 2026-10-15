"""HS-200-04 — the readiness wire on a cold installation.

The repair list and the task probe are served by the existing Concierge routes.
On a machine with nothing configured they must both answer honestly rather than
fail: an empty repair list, and a probe that refuses by name instead of claiming
a model.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.db import get_database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def cold(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    database = get_database(temp_dir / "readiness.db")
    yield database
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


def _client() -> TestClient:
    return TestClient(
        MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=MagicMock(),
                on_stop=MagicMock(),
                get_state=MagicMock(return_value={}),
            )
        ).app
    )


def test_detect_carries_a_repair_list_and_a_cold_machine_needs_nothing(cold) -> None:
    response = _client().get("/api/concierge/detect")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert "repairs" in payload, payload.keys()
    # Nothing is assigned yet, so nothing can be broken yet.
    assert payload["repairs"] == []


def test_find_on_lan_returns_transient_found_rows_without_writing(cold, monkeypatch) -> None:
    monkeypatch.setattr(
        "holdspeak.services.lan_engine_discovery.scan_lan_engines",
        lambda: {
            "engines": [{
                "id": "lan:192.168.1.43:8080:qwen3.8-27b",
                "kind": "lan",
                "name": "qwen3.8-27b",
                "legacyLabel": "qwen3.8-27b",
                "host": "192.168.1.43",
                "state": "READY",
                "baseUrl": "http://192.168.1.43:8080/v1",
                "found": True,
            }],
            "partial": False,
            "unavailable": False,
            "hostsChecked": 254,
            "portsChecked": 4,
        },
    )
    before = cold.profiles.list()
    denied = _client().post("/api/concierge/discover-lan", headers={"X-HoldSpeak-Token": "not-the-owner"})
    assert denied.status_code in {401, 403}
    response = _client().post("/api/concierge/discover-lan")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["engines"][0]["name"] == "qwen3.8-27b"
    assert payload["engines"][0]["found"] is True
    assert payload["engines"][0]["host"] == "192.168.1.43"
    assert payload["partial"] is False
    assert cold.profiles.list() == before


def test_a_detected_endpoint_carries_the_address_its_probe_needs(cold) -> None:
    """The probe reaches an endpoint only if detect told it where the endpoint is."""
    cold.profiles.upsert(
        profile_id="lan-box",
        name="LAN box",
        kind="openAICompatible",
        base_url="http://192.168.1.43:8080/v1",
        model="qwen",
    )
    payload = _client().get("/api/concierge/detect").json()
    endpoints = [e for e in payload["engines"] if e.get("profileId") == "lan-box"]
    assert endpoints, payload["engines"]
    assert endpoints[0]["baseUrl"] == "http://192.168.1.43:8080/v1"


def test_the_task_probe_refuses_by_name_when_no_route_is_assigned(cold) -> None:
    response = _client().post("/api/concierge/probe", json={"task": True})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is False
    assert payload["state"] in {"UNREACHABLE", "REFUSED"}
    # It names why, and never claims a model it did not reach.
    assert payload["reasonCode"]
    assert not payload.get("model")


def test_the_task_probe_refuses_an_unprobeable_capability(cold) -> None:
    response = _client().post(
        "/api/concierge/probe", json={"task": True, "capabilityId": "meeting.auto_title"}
    )
    assert response.status_code == 400, response.text
    assert response.json()["code"] == "concierge_probe_invalid"


@pytest.mark.parametrize("capability_id", [
    "speech.rewrite", "ask.answer", "meeting.deferred_analysis", "recipe.run", "background.rails_summary",
])
def test_each_bounded_job_sample_is_accepted_on_the_existing_wire(cold, capability_id: str) -> None:
    response = _client().post("/api/concierge/probe", json={
        "task": True, "capabilityId": capability_id, "expectedProfileIds": ["shown-profile"],
    })
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["capabilityId"] == capability_id
    assert payload["ok"] is False and payload["reasonCode"]
    assert payload["testedTask"] and payload["sampleInput"]


@pytest.mark.parametrize("expected_profiles", ["quick", [1], [""], None])
def test_the_task_probe_rejects_malformed_displayed_profile_chains(cold, expected_profiles) -> None:
    response = _client().post("/api/concierge/probe", json={
        "task": True, "expectedProfileIds": expected_profiles,
    })
    assert response.status_code == 400, response.text
    assert response.json()["code"] == "concierge_probe_invalid"
