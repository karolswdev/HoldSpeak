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


def test_no_interim_settings_drawer_in_live_source() -> None:
    """The interim 'consolidating / History → Settings' drawer is fully gone.

    Scans live web/src markup + scripts for the drawer's signature markers. The
    completed-move references in code comments are fine; these markers are the
    debt itself.
    """
    markers = ("consolidating", "settings-interim", "data-settings-open", "data-settings-overlay")
    offenders: list[str] = []
    web_src = _REPO / "web" / "src"
    for path in [*web_src.rglob("*.tsx"), *web_src.rglob("*.ts"), *web_src.rglob("*.css")]:
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            if any(m in line for m in markers):
                offenders.append(f"{path.relative_to(_REPO)}:{lineno}: {line.strip()}")
    assert not offenders, (
        "The interim Settings drawer markers are back in live source:\n  "
        + "\n  ".join(offenders)
    )


def test_desk_menu_opens_settings_in_world() -> None:
    """HS-95-08: the flat top-nav is gone; the desk menu dispatches the
    Settings window and the deep link demotes to the same surface.
    HS-111-07: the mark menu derives the verb from the ONE registry
    (go.configure-settings) instead of a hardcoded room list."""
    chrome = (_REPO / "web" / "src" / "desk" / "components" / "DeskChrome.tsx").read_text()
    assert '"go.configure-settings"' in chrome
    registry = (_REPO / "web" / "src" / "desk" / "verbRegistry.ts").read_text()
    assert '"configure-settings"' in registry
    routes = (_REPO / "web" / "src" / "routes.tsx").read_text()
    assert '"configure-settings"' in routes


def test_settings_is_sectioned_searchable_and_progressive() -> None:
    """HS-111-01: 'sectioned + searchable' became 'modular + filtered' —
    the same guarantee. An authored module registry owns every top-level
    settings key (unmapped keys fall through to System, so every key stays
    reachable) and the drawer filter finds deep settings by label."""
    prefs = (_REPO / "web" / "src" / "pages" / "cores" / "settingsPrefs.tsx").read_text()
    assert "export const PREF_MODULES" in prefs
    for key in ("ui", "hotkey", "model", "dictation", "presence", "meeting"):
        assert f'"{key}"' in prefs, key
    assert 'return "system"' in prefs  # every unmapped key stays reachable
    # The filter replaces "Find a setting": module hits + deep-setting hits.
    assert 'label="Filter settings"' in prefs
    assert "hit.label.toLowerCase().includes(query)" in prefs
    page = (_REPO / "web" / "src" / "pages" / "cores" / "SettingsCore.tsx").read_text()
    assert "deepIndex" in page and "moduleForKey" in page
    assert "highlight" in page  # the filter lands on the exact row
    assert '>("/api/settings"' in page
