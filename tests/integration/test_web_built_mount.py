"""HS-10-01 smoke tests: the /_built static-files mount serves the
Astro-built design-check page, and the five legacy routes still serve
their hand-authored HTML untouched.

These tests assume `npm run build` has already been executed in `web/`.
If `holdspeak/static/_built/` is missing, the design-check assertion
is skipped — the legacy-route assertions still run because the mount
is conditional on the directory existing.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

pytestmark = [pytest.mark.requires_meeting]


_BUILT_ROOT = (
    Path(__file__).resolve().parents[2] / "holdspeak" / "static" / "_built"
)
_BUILT_INDEX = _BUILT_ROOT / "design" / "components" / "index.html"
_GALLERY_INDEX = _BUILT_ROOT / "design" / "components" / "index.html"


@pytest.fixture
def test_client() -> TestClient:
    server = MeetingWebServer(
                 WebRuntimeCallbacks(
                     on_bookmark=MagicMock(),
                     on_stop=MagicMock(),
                     get_state=MagicMock(return_value={}),
                 )
             )
    return TestClient(server.app)


@pytest.mark.skipif(
    not _BUILT_INDEX.is_file(),
    reason="run `cd web && npm run build` to populate holdspeak/static/_built/",
)
def test_built_design_components_page_is_served(test_client: TestClient) -> None:
    response = test_client.get("/_built/design/components/")
    assert response.status_code == 200
    assert "Component gallery" in response.text
    assert "/_built/_astro/" in response.text


@pytest.mark.skipif(
    not _BUILT_INDEX.is_file(),
    reason="run `cd web && npm run build` to populate holdspeak/static/_built/",
)
def test_topnav_renders_with_aria_current(test_client: TestClient) -> None:
    """HS-10-04: a page passing `current` to AppLayout must render the
    matching nav link with aria-current=page and the selected class.
    (/dictation sets current="dictation"; the old design/check probe page
    was removed in the Phase-72 shadow sweep.)"""
    response = test_client.get("/_built/dictation/")
    body = response.text
    assert "Skip to content" in body
    assert 'aria-current="page"' in body
    # Exactly one nav link is current.
    assert body.count('aria-current="page"') == 1
    # HS-70-01/04: the two-mode primaries (Home/Dictation/Meetings) + Studio.
    # Activity folded into Dictation (HS-70-04), so it is no longer a nav item.
    for href in ('href="/"', 'href="/history"', 'href="/dictation"'):
        assert href in body, href
    assert 'href="/workbench"' in body  # a Studio-tier item is present


@pytest.mark.skipif(
    not _GALLERY_INDEX.is_file(),
    reason="run `cd web && npm run build` to populate the components gallery",
)
def test_topnav_renders_without_current_on_gallery(
    test_client: TestClient,
) -> None:
    """The gallery does not pass `current`; no nav link should be marked
    current and the local-only fallback pill should still render."""
    response = test_client.get("/_built/design/components/")
    body = response.text
    assert "Skip to content" in body
    assert 'aria-current="page"' not in body
    assert "local-only" in body


@pytest.mark.skipif(
    not _GALLERY_INDEX.is_file(),
    reason="run `cd web && npm run build` to populate the components gallery",
)
def test_components_gallery_is_served(test_client: TestClient) -> None:
    response = test_client.get("/_built/design/components/")
    assert response.status_code == 200
    # Every component family must show up at least once on the gallery.
    for marker in (
        "Component gallery",
        "Button",
        "Pill",
        "Panel",
        "ListRow",
        "EmptyState",
        "InlineMessage",
        "Toolbar alignment",
    ):
        assert marker in response.text, marker


@pytest.mark.skipif(
    not _BUILT_INDEX.is_file(),
    reason="run `cd web && npm run build` to populate holdspeak/static/_built/",
)
def test_identity_layer_assets_serve(test_client: TestClient) -> None:
    """HS-10-05 / HS-42-05: app mark SVG inlines in TopNav, favicon +
    apple-touch-icon are referenced + served, and the shell privacy signal (now
    the ambient TrustChip, HS-42-05) renders."""
    response = test_client.get("/_built/design/components/")
    body = response.text
    # Favicon refs in <head>.
    assert 'href="/_built/favicon.svg"' in body
    assert 'href="/_built/apple-touch-icon.png"' in body
    # App mark inline SVG geometry (keycap rect + 3 waveform paths).
    assert 'viewBox="0 0 24 24"' in body
    assert 'rx="3"' in body
    # The shell privacy signal — the ambient TrustChip (replaced the static
    # LocalPill default in the TopNav).
    assert "data-trust-open" in body
    assert "what can leave this machine" in body

    # Static-files mount serves the SVG itself.
    favicon = test_client.get("/_built/favicon.svg")
    assert favicon.status_code == 200
    assert favicon.headers["content-type"].startswith("image/svg")

    icon = test_client.get("/_built/apple-touch-icon.png")
    assert icon.status_code == 200
    assert icon.headers["content-type"] == "image/png"


def test_legacy_routes_still_serve(test_client: TestClient) -> None:
    # All route surfaces serve from the Astro build:
    # / (HS-10-06), /activity (HS-10-07), /history (HS-10-08),
    # /settings (its own page since HS-42-02), /dictation +
    # /docs/dictation-runtime (HS-10-09).
    for path, marker in [
        ("/", "HoldSpeak"),
        ("/activity", "Activity ledger"),
        ("/history", "Meetings"),  # HS-70-05: retitled from "HoldSpeak History"
        ("/settings", "Every global HoldSpeak setting"),
        ("/dictation", "HoldSpeak Dictation"),
        ("/docs/dictation-runtime", "Dictation runtime setup"),
    ]:
        response = test_client.get(path)
        assert response.status_code == 200, path
        assert marker in response.text, path
