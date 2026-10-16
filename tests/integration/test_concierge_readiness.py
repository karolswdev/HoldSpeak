"""HS-200-04 — the readiness wire on a cold installation.

The repair list and the task probe are served by the existing Concierge routes.
On a machine with nothing configured they must both answer honestly rather than
fail: an empty repair list, and a probe that refuses by name instead of claiming
a model.
"""

from __future__ import annotations

import shutil
import tempfile
import ipaddress
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
    from holdspeak.kernel.external_egress import run_external_egress
    from holdspeak.principals import PrincipalKind
    from holdspeak.services import lan_engine_discovery as discovery

    monkeypatch.setattr(discovery, "_interface_snapshot", lambda: ((
        discovery.LanInterface(ipaddress.IPv4Address("192.168.1.42"), ipaddress.IPv4Network("192.168.1.42/31")),
    ), "ip-json"))
    admitted = []

    def admit(**kwargs):
        admitted.append(kwargs)
        return run_external_egress(**kwargs)

    monkeypatch.setattr(discovery, "run_external_egress", admit)

    def connect(address, **_kwargs):
        if address[1] != 8080:
            raise ConnectionRefusedError("closed port")
        return MagicMock()

    tcp = MagicMock(side_effect=connect)
    response = MagicMock()
    response.__enter__.return_value = response
    response.status = 200
    response.read.return_value = b'{"data":[{"id":"qwen3.8-27b"}]}'
    response.read1.side_effect = [response.read.return_value, b""]
    http = MagicMock(return_value=response)
    monkeypatch.setattr(discovery.socket, "create_connection", tcp)
    monkeypatch.setattr(discovery._LAN_OPENER, "open", http)
    client = _client()
    before = cold.profiles.list()
    settings_path = config_module.CONFIG_FILE
    settings_before = settings_path.read_bytes() if settings_path.exists() else None
    denied = client.post("/api/concierge/discover-lan", headers={"X-HoldSpeak-Token": "not-the-owner"})
    assert denied.status_code in {401, 403}
    assert admitted == []
    tcp.assert_not_called()
    http.assert_not_called()
    response = client.post("/api/concierge/discover-lan")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["engines"][0]["name"] == "qwen3.8-27b"
    assert payload["engines"][0]["found"] is True
    assert payload["engines"][0]["host"] == "192.168.1.43"
    assert payload["partial"] is False
    assert len(admitted) == 1
    assert admitted[0]["principal"].kind is PrincipalKind.OWNER
    assert admitted[0]["principal"].identity == "owner-session"
    assert admitted[0]["connector_id"] == "lan-engine-discovery"
    http.assert_called_once()
    assert cold.profiles.list() == before
    assert (settings_path.read_bytes() if settings_path.exists() else None) == settings_before


def test_find_on_lan_returns_a_named_egress_refusal(cold, monkeypatch) -> None:
    from holdspeak.kernel.external_egress import EgressOperationRefused
    from holdspeak.principals import PrincipalKind

    def refused(*, principal):
        assert principal.kind is PrincipalKind.OWNER
        raise EgressOperationRefused("lan-scan:manifest", "external_egress_warrant_refused")

    monkeypatch.setattr(
        "holdspeak.services.lan_engine_discovery.scan_lan_engines",
        refused,
    )
    response = _client().post("/api/concierge/discover-lan")
    assert response.status_code == 403, response.text
    assert response.json() == {
        "code": "concierge_lan_refused", "message": "external_egress_warrant_refused",
    }


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
