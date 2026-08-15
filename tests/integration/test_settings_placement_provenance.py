"""HS-132-10 — the settings document states which dial decided meetings placement.

Issue #450 defect 4's UI half: the backend has ONE placement authority with real
precedence (an adopted destination beats the local/cloud provider intent), but no
client could see it. A person set Provider = LOCAL and nothing happened, silently,
because a destination adopted in another module had already decided.

These lock the wire half of the fix: `/api/settings` carries `_placement.meeting`
with `placement_source` / `placement_reason`, the effective target identity, and
`provider_honored` — and the write's own echo carries the NEW placement, so the
surface that turns the dial sees where meetings now run without a reload. The
round-trip is proven against `resolve_meeting_placement` itself: the payload never
describes a placement the resolver would not perform.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.config import Config
from holdspeak.db.models import ProfileRecord
from holdspeak.intel import providers
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    return target


@pytest.fixture
def client() -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
            on_settings_applied=MagicMock(),
        )
    )
    return TestClient(server.app)


def _lan_profile(**overrides) -> ProfileRecord:
    fields = dict(
        id="p-43",
        name="LAN llama",
        kind="openAICompatible",
        base_url="http://192.168.1.43:8080/v1",
        model="Qwen3.5-9B-Q6_K",
    )
    fields.update(overrides)
    return ProfileRecord(**fields)


def _placement(body: dict) -> dict:
    assert "_placement" in body, "settings payload carries no placement provenance"
    return body["_placement"]["meeting"]


def _put(client: TestClient, patch: dict) -> dict:
    response = client.put("/api/settings", json=patch)
    assert response.status_code == 200, response.text
    return response.json()["settings"]


# ── 1. every placement state is named, never silent ──────────────────────────


def test_local_provider_with_no_destination_names_the_provider(
    client: TestClient, settings_path: Path
) -> None:
    body = client.get("/api/settings").json()
    placement = _placement(body)
    assert placement["placement_source"] == "provider"
    assert placement["provider_intent"] == "local"
    assert placement["provider_honored"] is True
    assert placement["boundary"] == "local"
    assert placement["target_id"] == ""
    # The effective target identity rides along (what would actually load).
    assert placement["engine"] in {"local", "cloud"}
    assert isinstance(placement["model"], str)


def test_cloud_provider_with_no_destination_names_the_provider(
    client: TestClient, settings_path: Path
) -> None:
    settings = _put(client, {"meeting": {"intel_provider": "cloud"}})
    placement = _placement(settings)
    assert placement["placement_source"] == "provider"
    assert placement["provider_intent"] == "cloud"
    assert placement["provider_honored"] is True
    assert placement["boundary"] in {"cloud", "private_network"}


def test_adopted_destination_reports_the_provider_selection_as_ignored(
    client: TestClient, settings_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(providers, "_lookup_profile_record", lambda pid: _lan_profile())
    settings = _put(
        client,
        {"meeting": {"intel_provider": "local", "intel_profile_id": "p-43"}},
    )
    placement = _placement(settings)
    # THE defect, now stated on the wire: the LOCAL provider intent is not what
    # decided; the adopted destination did.
    assert placement["placement_source"] == "destination"
    assert placement["provider_intent"] == "local"
    assert placement["provider_honored"] is False
    assert placement["target_id"] == "p-43"
    assert placement["target_name"] == "LAN llama"
    assert placement["boundary"] == "private_network"
    assert placement["model"] == "Qwen3.5-9B-Q6_K"
    assert placement["engine"] == "cloud"


def test_mesh_destination_is_named_as_mesh(
    client: TestClient, settings_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        providers,
        "_lookup_profile_record",
        lambda pid: _lan_profile(
            id="p-phone",
            name="Walk edge",
            kind="meshNode",
            base_url=None,
            node="walk-edge",
            model="qwen3.5-4b",
        ),
    )
    settings = _put(client, {"meeting": {"intel_profile_id": "p-phone"}})
    placement = _placement(settings)
    assert placement["placement_source"] == "destination"
    assert placement["provider_honored"] is False
    assert placement["boundary"] == "mesh"
    assert placement["node"] == "walk-edge"
    assert placement["engine"] == "mesh"


def test_dangling_destination_surfaces_the_overridden_selection_with_its_reason(
    client: TestClient, settings_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(providers, "_lookup_profile_record", lambda pid: None)
    settings = _put(
        client,
        {"meeting": {"intel_provider": "local", "intel_profile_id": "gone"}},
    )
    placement = _placement(settings)
    assert placement["placement_source"] == "provider-selection-ignored"
    # The pointer was dropped, so the provider intent DID decide — and the
    # reason is on the wire instead of nowhere.
    assert placement["provider_honored"] is True
    assert "gone" in placement["placement_reason"]
    assert placement["boundary"] == "local"


# ── 2. the round trip: the payload never lies about where meetings run ───────


def test_changing_the_control_changes_where_meetings_run(
    client: TestClient, settings_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(providers, "_lookup_profile_record", lambda pid: _lan_profile())

    before = _placement(client.get("/api/settings").json())
    assert before["placement_source"] == "provider"
    assert providers.resolve_meeting_placement(Config.load().meeting).base_url is None

    after = _placement(_put(client, {"meeting": {"intel_profile_id": "p-43"}}))

    # The persisted config now resolves to the destination — the control moved
    # the run, and the payload's story matches the resolver's decision.
    resolved = providers.resolve_meeting_placement(Config.load().meeting)
    assert resolved.base_url == "http://192.168.1.43:8080/v1"
    assert resolved.provider == "cloud"
    assert after["placement_source"] == resolved.source == "destination"
    assert after["target_id"] == resolved.profile_id == "p-43"
    assert after["boundary"] == resolved.boundary

    # ...and clearing it hands the decision back to the provider intent.
    cleared = _placement(_put(client, {"meeting": {"intel_profile_id": None}}))
    assert cleared["placement_source"] == "provider"
    assert cleared["provider_honored"] is True
    assert providers.resolve_meeting_placement(Config.load().meeting).base_url is None


def test_the_provenance_block_is_never_persisted(
    client: TestClient, settings_path: Path
) -> None:
    """A client echoing the whole document back must not write the describer."""
    body = client.get("/api/settings").json()
    body["ui"]["theme"] = "light"
    response = client.put("/api/settings", json=body)
    assert response.status_code == 200, response.text
    assert "_placement" not in Config.load().to_dict()
    assert settings_path.exists()
    assert "_placement" not in settings_path.read_text()
