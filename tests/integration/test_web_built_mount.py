"""Phase-91 integration locks for the one Vite/React Web shell."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from holdspeak.web.routes.pages import SPA_ROUTES
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

pytestmark = [pytest.mark.requires_meeting]

_BUILT_ROOT = Path(__file__).resolve().parents[2] / "holdspeak" / "static" / "_built"
_BUILT_INDEX = _BUILT_ROOT / "index.html"


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


@pytest.mark.skipif(not _BUILT_INDEX.is_file(), reason="run `cd web && npm run build`")
def test_vite_index_and_assets_are_served(test_client: TestClient) -> None:
    response = test_client.get("/_built/index.html")
    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text
    assert "/_built/assets/" in response.text
    assert "_astro" not in response.text
    assert "favicon.svg" in response.text
    assert test_client.get("/_built/favicon.svg").status_code == 200


@pytest.mark.skipif(not _BUILT_INDEX.is_file(), reason="run `cd web && npm run build`")
def test_every_canonical_deep_link_returns_the_same_react_shell(
    test_client: TestClient,
) -> None:
    expected = _BUILT_INDEX.read_text(encoding="utf-8")
    for path in SPA_ROUTES:
        response = test_client.get(path, follow_redirects=False)
        assert response.status_code == 200, path
        assert response.text == expected, path


@pytest.mark.skipif(not _BUILT_INDEX.is_file(), reason="run `cd web && npm run build`")
def test_query_token_deep_link_keeps_the_shell_available(
    test_client: TestClient,
) -> None:
    response = test_client.get("/dictation?token=browser-arrival-token")
    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text


def test_missing_build_has_one_honest_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.web.routes import pages

    monkeypatch.setattr(pages, "_SHELL_PATH", Path("/definitely/missing/index.html"))
    response = pages._react_shell()
    assert response.status_code == 200
    assert b"npm run build" in response.body
