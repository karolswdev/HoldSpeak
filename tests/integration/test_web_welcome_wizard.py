"""HS-43-01: the first-run wizard route + shell."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

import holdspeak.web.routes.pages as pages
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

_REPO = Path(__file__).resolve().parents[2]


def _client() -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={}))
    )
    return TestClient(server.app)


def test_welcome_route_serves_the_wizard() -> None:
    resp = _client().get("/welcome")
    assert resp.status_code == 200
    if (pages._HOLDSPEAK_DIR / "static" / "_built" / "welcome" / "index.html").exists():
        assert "welcomeApp" in resp.text
    else:
        assert "Welcome to HoldSpeak" in resp.text


def test_wizard_is_a_funnel_with_a11y_and_reduced_motion() -> None:
    """The wizard source is a real step-funnel with the a11y bones in place."""
    page = (_REPO / "web" / "src" / "pages" / "welcome.astro").read_text()
    app = (_REPO / "web" / "src" / "scripts" / "welcome-app.js").read_text()
    # one step at a time + Step N of M + Back/Skip (user freedom)
    assert "Step ${i + 1} of ${steps.length}" in app or "Step ${i + 1} of" in page
    assert "skip()" in page and "back()" in page
    # focus moves to the step heading on transition (a11y)
    assert "focusHeading" in app and "x-ref=\"heading_welcome\"" in page
    # reduced-motion is respected
    assert "prefers-reduced-motion" in page
    assert "reduceMotion" in app
    # the six steps exist
    for sid in ("welcome", "permissions", "model", "dictation", "presence", "done"):
        assert f'"{sid}"' in app


def test_wizard_reads_os_dynamically_and_mentions_meetings() -> None:
    """No hardcoded 'Mac'; HoldSpeak is also a meeting tool — say so."""
    page = (_REPO / "web" / "src" / "pages" / "welcome.astro").read_text()
    app = (_REPO / "web" / "src" / "scripts" / "welcome-app.js").read_text()
    # OS is read dynamically from the status, never hardcoded.
    assert "your Mac is ready" not in page
    assert "osLabel" in app and "presence?.os" in app
    assert 'x-text="osLabel"' in page
    # meetings are part of the pitch (welcome value prop + a "Run a meeting" card).
    assert "meeting" in page.lower()
    assert "Run a meeting" in page
