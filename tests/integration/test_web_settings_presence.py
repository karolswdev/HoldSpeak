"""HS-43-04: the presence toggle round-trips through /api/settings (no env var)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    return target


def _client() -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={}))
    )
    return TestClient(server.app)


def test_presence_toggle_persists_via_settings(settings_path) -> None:
    client = _client()
    assert client.get("/api/settings").json()["presence"]["enabled"] is False

    resp = client.put("/api/settings", json={"presence": {"enabled": True}})
    assert resp.status_code == 200
    assert resp.json()["settings"]["presence"]["enabled"] is True

    # persisted to disk + reflected on a fresh GET + in the setup status.
    from holdspeak.config import Config

    assert Config.load(settings_path).presence.enabled is True
    assert client.get("/api/settings").json()["presence"]["enabled"] is True
    assert client.get("/api/setup/status").json()["presence"]["enabled"] is True


def test_wizard_presence_step_has_a_real_toggle_not_an_env_var() -> None:
    repo = Path(__file__).resolve().parents[2]
    page = (repo / "web" / "src" / "pages" / "WelcomePage.tsx").read_text()
    assert "<Switch" in page and "setPresence" in page
    assert 'json: { presence: { enabled } }' in page
