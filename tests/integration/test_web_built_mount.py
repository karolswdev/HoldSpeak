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

from holdspeak.web_server import MeetingWebServer

pytestmark = [pytest.mark.requires_meeting]


_BUILT_ROOT = (
    Path(__file__).resolve().parents[2] / "holdspeak" / "static" / "_built"
)
_BUILT_INDEX = _BUILT_ROOT / "design" / "check" / "index.html"
_GALLERY_INDEX = _BUILT_ROOT / "design" / "components" / "index.html"


@pytest.fixture
def test_client() -> TestClient:
    server = MeetingWebServer(
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        get_state=MagicMock(return_value={}),
    )
    return TestClient(server.app)


@pytest.mark.skipif(
    not _BUILT_INDEX.is_file(),
    reason="run `cd web && npm run build` to populate holdspeak/static/_built/",
)
def test_built_design_check_page_is_served(test_client: TestClient) -> None:
    response = test_client.get("/_built/design/check/")
    assert response.status_code == 200
    assert "Design system online" in response.text
    assert "/_built/_astro/" in response.text


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


def test_legacy_routes_still_serve(test_client: TestClient) -> None:
    for path, marker in [
        ("/", "HoldSpeak"),
        ("/activity", "Local Activity"),
        ("/history", "HoldSpeak"),
        ("/dictation", "HoldSpeak"),
        ("/docs/dictation-runtime", "Dictation Runtime"),
    ]:
        response = test_client.get(path)
        assert response.status_code == 200, path
        assert marker in response.text, path
