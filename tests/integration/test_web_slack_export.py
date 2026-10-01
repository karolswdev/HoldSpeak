"""PHILO-11-02 — the retired meeting Slack route is parked by name."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.config import Config
from holdspeak.db import get_database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

pytestmark = [pytest.mark.requires_meeting]

URL = "https://hooks.slack.com/services/T0/B0/legacy"


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    config = Config()
    config.control_mode = "yolo"
    config.meeting.slack_webhook_url = URL
    config.save(path=target)
    return target


@pytest.fixture
def client(settings_path: Path, tmp_path: Path) -> TestClient:
    reset_database()
    _ = get_database(tmp_path / "slack-rewrite.db")
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    yield TestClient(server.app)
    reset_database()


def test_old_meeting_export_route_is_parked(client: TestClient) -> None:
    response = client.post(
        "/api/meetings/any-meeting/export/slack", json={"what": "digest"}
    )
    assert response.status_code == 400
    assert response.json() == {"success": False, "error": "slack_moved_to_channel"}
    assert URL not in response.text


def test_old_secret_operation_is_absent(client: TestClient) -> None:
    response = client.put(
        "/api/settings/secrets/slack_webhook_url", json={"value": URL}
    )
    assert response.status_code == 404
    assert URL not in response.text


def test_retained_config_value_loads_but_settings_drops_it(
    client: TestClient, settings_path: Path
) -> None:
    response = client.get("/api/settings")
    assert response.status_code == 200
    assert "slack_webhook_url" not in response.json().get("meeting", {})
    assert URL not in response.text
    assert Config.load(settings_path).meeting.slack_webhook_url == URL
