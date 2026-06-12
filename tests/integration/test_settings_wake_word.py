"""HS-60-01 — the wake-word config at the settings boundary (strict 400s)."""
from __future__ import annotations

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

import holdspeak.config as config_module
from holdspeak.config import Config
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def settings_path(tmp_path, monkeypatch):
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    Config().save(path=target)
    return target


@pytest.fixture
def client(settings_path):
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    return TestClient(server.app)


def test_wake_settings_round_trip(client):
    response = client.put(
        "/api/settings",
        json={"wake_word": {"enabled": True, "threshold": 0.6, "armed_window_seconds": 10, "action": "preview"}},
    )
    assert response.status_code == 200, response.text
    stored = client.get("/api/settings").json()["wake_word"]
    assert stored["enabled"] is True
    assert stored["threshold"] == 0.6
    assert stored["armed_window_seconds"] == 10
    assert stored["action"] == "preview"


def test_defaults_are_off_and_preview(client):
    stored = client.get("/api/settings").json()["wake_word"]
    assert stored == {
        "enabled": False,
        "model": "hey_jarvis",
        "threshold": 0.5,
        "armed_window_seconds": 8.0,
        "action": "preview",
    }


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"action": "always"}, "must be 'preview' or 'type'"),
        ({"threshold": 1.5}, "between 0 and 1"),
        ({"threshold": "hot"}, "must be a number"),
        ({"armed_window_seconds": 99}, "between 2 and 30"),
        ({"model": "  "}, "must not be empty"),
    ],
)
def test_malformed_wake_settings_refused(client, payload, message):
    response = client.put("/api/settings", json={"wake_word": payload})
    assert response.status_code == 400
    assert message in response.json()["error"]
    # The bad write changed nothing.
    assert client.get("/api/settings").json()["wake_word"]["enabled"] is False
