"""HS-92-02 — settings are editable without round-tripping credentials."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.config import Config
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", path)
    return path


@pytest.fixture
def client() -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        )
    )
    return TestClient(server.app)


def _seed_every_secret(path: Path) -> Config:
    config = Config()
    config.meeting.web_auth_token = "web-secret"
    config.device.psk = "device-secret"
    config.cadence_telegram.bot_token = "telegram-secret"
    config.cadence_telegram.pairing_code = "pair-secret"
    config.meeting.intel_retry_failure_webhook_url = "https://alerts.example.test/credential"
    config.meeting.intel_retry_failure_webhook_header_name = "Authorization"
    config.meeting.intel_retry_failure_webhook_header_value = "Bearer failure-secret"
    config.meeting.slack_webhook_url = "https://hooks.slack.com/services/secret/path"
    config.meeting.companion_webhook_url = "https://hooks.example.test/secret/path"
    config.save(path)
    return config


def test_get_and_generic_put_never_echo_or_mutate_secrets(
    client: TestClient, settings_path: Path
) -> None:
    seeded = _seed_every_secret(settings_path)
    raw_secrets = [
        "web-secret",
        "device-secret",
        "telegram-secret",
        "pair-secret",
        "https://alerts.example.test/credential",
        "Bearer failure-secret",
        "https://hooks.slack.com/services/secret/path",
        "https://hooks.example.test/secret/path",
    ]

    response = client.get("/api/settings")
    assert response.status_code == 200
    body = response.json()
    serialized = response.text
    assert all(secret not in serialized for secret in raw_secrets)
    assert all(state["configured"] for state in body["_secrets"].values())
    assert body["_secrets"]["slack_webhook_url"]["destination"] == "hooks.slack.com"

    # A naive full-form echo and an explicit generic secret mutation are both
    # ignored; credentials move only through the dedicated routes.
    body["meeting"]["web_auth_token"] = "attacker-replacement"
    body["device"]["psk"] = ""
    update = client.put("/api/settings", json=body)
    assert update.status_code == 200, update.text
    assert "attacker-replacement" not in update.text

    persisted = Config.load(settings_path)
    assert persisted.meeting.web_auth_token == seeded.meeting.web_auth_token
    assert persisted.device.psk == seeded.device.psk
    assert persisted.cadence_telegram.bot_token == seeded.cadence_telegram.bot_token
    assert persisted.meeting.slack_webhook_url == seeded.meeting.slack_webhook_url


def test_dedicated_replace_rotate_delete_routes_never_echo_values(
    client: TestClient, settings_path: Path
) -> None:
    replaced = client.put(
        "/api/settings/secrets/telegram_bot_token",
        json={"value": "new-telegram-secret"},
    )
    assert replaced.status_code == 200, replaced.text
    assert "new-telegram-secret" not in replaced.text
    assert replaced.json()["secrets"]["telegram_bot_token"] == {"configured": True}
    assert Config.load(settings_path).cadence_telegram.bot_token == "new-telegram-secret"

    rotated = client.post("/api/settings/secrets/web_token/rotate")
    assert rotated.status_code == 200, rotated.text
    assert Config.load(settings_path).meeting.web_auth_token
    assert Config.load(settings_path).meeting.web_auth_token not in rotated.text

    deleted = client.delete("/api/settings/secrets/telegram_bot_token")
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["secrets"]["telegram_bot_token"] == {"configured": False}
    assert Config.load(settings_path).cadence_telegram.bot_token == ""


def test_partial_update_preserves_every_unrelated_top_level_section(
    client: TestClient, settings_path: Path
) -> None:
    config = Config(config_version=7)
    config.mesh.device_name = "Studio Mac"
    config.cadence.enabled = True
    config.cadence.pressure = "aggressive"
    config.cadence_telegram.enabled = True
    config.cadence_telegram.allowed_chat_ids = ["42"]
    config.rails_observer.enabled = True
    config.rails_observer.profile_id = "private-node"
    config.presence.mascot = True
    config.save(settings_path)
    before = config.to_dict()

    response = client.put("/api/settings", json={"ui": {"theme": "light"}})
    assert response.status_code == 200, response.text
    after = Config.load(settings_path).to_dict()

    assert after["ui"]["theme"] == "light"
    for section in (
        "config_version",
        "mesh",
        "cadence",
        "cadence_telegram",
        "rails_observer",
        "presence",
        "wake_word",
        "device",
    ):
        assert after[section] == before[section], section


def test_web_settings_uses_only_dedicated_secret_operations() -> None:
    source = (
        Path(__file__).resolve().parents[2] / "web/src/pages/cores/SettingsCore.tsx"
    ).read_text()
    assert "Values stay on this hub" in source
    assert "/api/settings/secrets/${secretId}" in source
    assert "/api/settings/secrets/${secretId}/rotate" in source
    assert 'type="password"' in source
