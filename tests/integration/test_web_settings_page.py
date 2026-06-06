"""HS-42-02: the global /settings route + the interim-drawer retirement guard."""
from __future__ import annotations

import re
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
    # Build-agnostic: when the bundle is built the route serves the real
    # settings page; the Unit Tests CI job runs without the gitignored bundle
    # and gets the 200 "not built" fallback. Assert the right one for the state.
    built = (
        pages._HOLDSPEAK_DIR / "static" / "_built" / "settings" / "index.html"
    ).exists()
    if built:
        assert "settingsApp" in resp.text  # the page's Alpine factory
    else:
        assert "HoldSpeak Settings" in resp.text


def test_no_interim_settings_drawer_in_live_source() -> None:
    """The interim 'consolidating / History → Settings' drawer is fully gone.

    Scans live web/src markup + scripts for the drawer's signature markers. The
    completed-move references in code comments are fine; these markers are the
    debt itself.
    """
    markers = ("consolidating", "settings-interim", "data-settings-open", "data-settings-overlay")
    offenders: list[str] = []
    web_src = _REPO / "web" / "src"
    for path in [*web_src.rglob("*.astro"), *web_src.rglob("*.js"), *web_src.rglob("*.css")]:
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            if any(m in line for m in markers):
                offenders.append(f"{path.relative_to(_REPO)}:{lineno}: {line.strip()}")
    assert not offenders, (
        "The interim Settings drawer markers are back in live source:\n  "
        + "\n  ".join(offenders)
    )


def test_topnav_gear_links_to_settings_route() -> None:
    topnav = (_REPO / "web" / "src" / "components" / "TopNav.astro").read_text()
    # The gear is a real link to /settings (not the old drawer button).
    assert re.search(r'href="/settings"', topnav)
