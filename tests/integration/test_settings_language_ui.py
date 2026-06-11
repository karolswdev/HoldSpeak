"""HS-59-01 — the language knob at the settings boundary + the UI lockstep.

PUT /api/settings validates against the vendored registry (a typo fails the
write, not a dictation later) and stores the normalized code; the settings
page's option list is kept in lockstep with `holdspeak/languages.py` so the
UI can never offer a language the backend would refuse.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

import holdspeak.config as config_module
from holdspeak.config import Config
from holdspeak.languages import WHISPER_LANGUAGES
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

_REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def settings_path(tmp_path, monkeypatch):
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    Config().save(path=target)
    return target


@pytest.fixture
def client(settings_path):
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    return TestClient(server.app)


def test_language_round_trips_normalized(client):
    response = client.put("/api/settings", json={"model": {"language": "Polish"}})
    assert response.status_code == 200, response.text
    fetched = client.get("/api/settings").json()
    assert fetched["model"]["language"] == "pl"


def test_auto_round_trips(client):
    assert client.put("/api/settings", json={"model": {"language": "auto"}}).status_code == 200
    assert client.get("/api/settings").json()["model"]["language"] == "auto"


def test_unknown_language_refused_actionably(client):
    response = client.put("/api/settings", json={"model": {"language": "klingon"}})
    assert response.status_code == 400
    assert "Unknown language" in response.json()["error"]
    # The bad write changed nothing.
    assert client.get("/api/settings").json()["model"]["language"] == "auto"


def test_settings_page_language_list_matches_the_registry():
    """The UI's option list and the Python registry cannot drift apart."""
    page = (_REPO / "web" / "src" / "pages" / "settings.astro").read_text()
    assert "Spoken language" in page
    match = re.search(r"const WHISPER_LANGUAGES = \[(.*?)\];", page, re.DOTALL)
    assert match, "settings.astro lost its WHISPER_LANGUAGES list"
    ui_codes = set(re.findall(r'code: "([a-z]+)"', match.group(1)))
    assert ui_codes == set(WHISPER_LANGUAGES), (
        "settings.astro's language list drifted from holdspeak/languages.py: "
        f"ui-only={sorted(ui_codes - set(WHISPER_LANGUAGES))} "
        f"registry-only={sorted(set(WHISPER_LANGUAGES) - ui_codes)}"
    )
