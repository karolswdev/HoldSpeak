"""PHILO-11-02 — desk free-text Slack is a named capability deferral."""
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
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    config_path = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_path)
    config = Config()
    config.meeting.slack_webhook_url = URL
    config.save(path=config_path)
    reset_database()
    _ = get_database(tmp_path / "desk-slack.db")
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


def test_free_text_slack_proposal_is_refused_by_name(client: TestClient) -> None:
    response = client.post(
        "/api/desk/actuators/slack/propose", json={"text": "free text"}
    )
    assert response.status_code == 400
    assert response.json()["error"] == "slack_moved_to_channel"


def test_desk_status_has_no_legacy_slack_config_reader(client: TestClient) -> None:
    response = client.get("/api/desk/actuators/status")
    assert response.status_code == 200
    assert "slack_configured" not in response.json()
