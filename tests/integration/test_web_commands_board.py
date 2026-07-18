"""HS-52-05: the Voice Commands board route + the Test endpoint.

The route serves the built board; `POST /api/commands/test` fires an action to verify
it (egress kinds run on the host through the bounded connector; `type_text` returns a
preview because it types into the focused app, with nothing to run here).
"""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
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


@pytest.fixture
def client() -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
        )
    )
    return TestClient(server.app)


def test_commands_route_serves_board(client: TestClient) -> None:
    res = client.get("/commands")
    assert res.status_code == 200
    assert '<div id="root"></div>' in res.text
    source = (Path(__file__).resolve().parents[2] / "web/src/pages/cores/CommandsCore.tsx").read_text()
    assert "Command board" in source
    # HS-95-04: the eyebrow rides the window chrome (the SURFACES table).
    surfaces = (
        Path(__file__).resolve().parents[2]
        / "web/src/desk/components/SurfaceWindows.tsx"
    ).read_text()
    assert '"Voice commands"' in surfaces
    assert "/api/commands/test" in source and "/api/settings" in source


def test_test_endpoint_type_text_returns_preview(client: TestClient, settings_path: Path) -> None:
    res = client.post("/api/commands/test", json={"kind": "type_text", "payload": "## Standup"})
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["tested"] is False
    assert data["preview"] == "types: ## Standup"


def test_test_endpoint_rejects_unknown_kind(client: TestClient, settings_path: Path) -> None:
    res = client.post("/api/commands/test", json={"kind": "telepathy", "payload": "x"})
    assert res.status_code == 400
    assert res.json()["ok"] is False


def test_test_endpoint_rejects_empty_payload(client: TestClient, settings_path: Path) -> None:
    res = client.post("/api/commands/test", json={"kind": "shell", "payload": "  "})
    assert res.status_code == 400
    assert res.json()["ok"] is False
