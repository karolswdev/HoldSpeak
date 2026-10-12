"""HS-42-02: the global /settings route + the interim-drawer retirement guard."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

import holdspeak.web.routes.pages as pages
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

_REPO = Path(__file__).resolve().parents[2]


def _client() -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        )
    )
    return TestClient(server.app)


def test_settings_route_serves_the_settings_page() -> None:
    resp = _client().get("/settings")
    assert resp.status_code == 200
    built = (pages._HOLDSPEAK_DIR / "static" / "_built" / "index.html").exists()
    if built:
        assert '<div id="root"></div>' in resp.text
    else:
        assert "npm run build" in resp.text


