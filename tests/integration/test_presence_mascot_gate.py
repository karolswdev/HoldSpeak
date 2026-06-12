"""HS-56-01 — the Qlippy mascot gate.

`presence.mascot` defaults off, round-trips `/api/settings`
config-version-safe, the settings page carries the subordinate sub-toggle,
the vendored assets ship in the bundle, and an unset flag changes nothing.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

from holdspeak.config import Config, PresenceConfig
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

_REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def temp_config(monkeypatch):
    temp_dir = Path(tempfile.mkdtemp())
    import holdspeak.config as config_module

    monkeypatch.setattr(config_module, "CONFIG_FILE", temp_dir / "config.json")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def client(temp_config):
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    return TestClient(server.app)


def test_mascot_defaults_off_and_round_trips(client):
    settings = client.get("/api/settings").json()
    assert settings["presence"]["enabled"] is False
    assert settings["presence"]["mascot"] is False

    response = client.put(
        "/api/settings", json={"presence": {"enabled": True, "mascot": True}}
    )
    assert response.status_code == 200, response.text
    settings = client.get("/api/settings").json()
    assert settings["presence"] == {"enabled": True, "mascot": True}


def test_older_config_shape_coerces_forward(temp_config):
    # A pre-mascot config (presence carries only `enabled`) loads with the
    # default, nothing dropped — the config-version posture (HS-50-04).
    import json

    import holdspeak.config as config_module

    config_module.CONFIG_FILE.write_text(
        json.dumps({"presence": {"enabled": True}})
    )
    cfg = Config.load()
    assert cfg.presence.enabled is True
    assert cfg.presence.mascot is False


def test_presence_config_dataclass_default():
    assert PresenceConfig().mascot is False


def test_settings_page_has_the_subordinate_sub_toggle():
    page = (_REPO / "web" / "src" / "pages" / "settings.astro").read_text()
    assert "Qlippy, the mascot" in page
    assert "settings.presence.mascot" in page
    # Subordinate: inert when presence itself is off; guarded click.
    assert "mascot-subfield" in page
    assert "is-inert" in page
    assert "settings.presence.enabled && (settings.presence.mascot" in page
    # Honest copy: he only offers (HS-62-02 swept the reassurance tail).
    assert "He only ever offers." in page


def test_assets_are_vendored_with_provenance():
    qlippy = _REPO / "web" / "public" / "qlippy"
    sprites = sorted(p.name for p in (qlippy / "sprites").glob("*.png"))
    assert len(sprites) == 14
    for state in ("idle", "listening", "thinking", "alert", "approve",
                  "decline", "learned", "present-note", "error", "sleeping"):
        assert f"{state}.png" in sprites
    glyphs = sorted(p.name for p in (qlippy / "glyphs").glob("*.png"))
    assert glyphs == ["bang.png", "check.png", "lightbulb.png", "x.png"]
    readme = (qlippy / "README.md").read_text()
    assert "44c0b009" in readme  # provenance: the PixelLab object id
    assert "9 frames" in readme
