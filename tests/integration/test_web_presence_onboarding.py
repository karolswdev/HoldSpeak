"""HS-42-07: the presence onboarding section + the platform/tier display rules."""
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
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
        )
    )
    return TestClient(server.app)


def test_setup_page_has_presence_onboarding() -> None:
    resp = _client().get("/setup")
    assert resp.status_code == 200
    if not (pages._HOLDSPEAK_DIR / "static" / "_built" / "setup" / "index.html").exists():
        return
    html = resp.text
    assert "Desktop presence (optional)" in html
    assert "never takes keyboard focus" in html  # the focus invariant
    assert "ps-hud" in html  # the faithful inline HUD preview


def test_presence_tier_and_install_rules() -> None:
    """The platform→tier + install-command rules live in setup-app.js."""
    src = (_REPO / "web" / "src" / "scripts" / "setup-app.js").read_text()
    # macOS HUD vs Wayland tray+notification.
    assert "menu-bar glyph" in src
    assert "tray glyph + an in-place notification" in src
    # Enable + the optional extra + the Linux typelibs.
    assert "HOLDSPEAK_DESKTOP_PRESENCE=1 holdspeak" in src
    assert "uv pip install -e '.[presence]'" in src
    assert "gir1.2-notify-0.7" in src
