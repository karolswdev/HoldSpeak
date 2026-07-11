"""HS-59-02 — the spoken-symbol dictionary at the settings boundary."""
from __future__ import annotations

from pathlib import Path

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

_REPO = Path(__file__).resolve().parents[2]


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


def test_symbols_round_trip_normalized(client):
    response = client.put(
        "/api/settings",
        json={"dictation": {"spoken_symbols": [
            {"spoken": "  tilde ", "symbol": "~", "attach": "right"},
            {"spoken": "arrow", "symbol": "→"},
        ]}},
    )
    assert response.status_code == 200, response.text
    stored = client.get("/api/settings").json()["dictation"]["spoken_symbols"]
    assert stored == [
        {"spoken": "tilde", "symbol": "~", "attach": "right"},
        {"spoken": "arrow", "symbol": "→", "attach": "none"},
    ]


def test_malformed_symbol_refused_with_400(client):
    response = client.put(
        "/api/settings",
        json={"dictation": {"spoken_symbols": [{"spoken": "", "symbol": "~"}]}},
    )
    assert response.status_code == 400
    assert "spoken phrase must not be empty" in response.json()["error"]
    assert client.get("/api/settings").json()["dictation"]["spoken_symbols"] == []


def test_default_is_empty_and_editor_ships():
    assert Config().dictation.spoken_symbols == []
    page = (_REPO / "web/src/pages/SettingsPage.tsx").read_text()
    assert "Spoken-symbol dictionary" in page
    for marker in ("symbol-row", "Add spoken symbol", "Remove", "Attachment"):
        assert marker in page, marker
