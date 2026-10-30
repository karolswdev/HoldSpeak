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


def test_terminals_deep_link_keeps_the_react_shell_available(
    test_client: TestClient,
) -> None:
    response = test_client.get("/terminals", follow_redirects=False)
    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text or "npm run build" in response.text


def test_missing_build_has_one_honest_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.web.routes import pages

    monkeypatch.setattr(pages, "_SHELL_PATH", Path("/definitely/missing/index.html"))
    response = pages._react_shell()
    assert response.status_code == 200
    assert b"npm run build" in response.body


@pytest.mark.skipif(not _BUILT_INDEX.is_file(), reason="run `cd web && npm run build`")
def test_the_six_desk_sounds_answer_under_the_bundle_base(test_client: TestClient) -> None:
    """replaces: tests/e2e/test_hs201_one_thing_glass.py::TestQuietDesk::test_cold_arrival_is_quiet
    (the six desk sounds leg: the URL the BUILT bundle asks for answers 200;
    the rehearsal's eight 404s were a root-relative `/desk/sfx/`)."""
    import re

    bases: set[str] = set()
    for path in (_BUILT_ROOT / "assets").glob("*.js"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        bases.update(re.findall(r"""["'`]([^"'`]*)desk/sfx/["'`]""", text))
    assert bases == {"/_built/"}, bases
    for name in ("key-down", "key-up", "latch", "land", "file", "error"):
        for extension in ("ogg", "wav"):
            url = f"/_built/desk/sfx/{name}.{extension}"
            response = test_client.get(url)
            assert response.status_code == 200, (response.status_code, url)
            assert response.content, url
