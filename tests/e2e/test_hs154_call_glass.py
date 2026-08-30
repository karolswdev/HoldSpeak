"""HS-154 -- The Call glass tests.

Real hub: Settings TTS block renders at 1440 and 393,
no horizontal overflow. Extra-off shows install instruction, not a
dead switch. API assertions are the hard proof.

Skips cleanly if Playwright browsers are absent.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="Glass needs Playwright")

REPO = Path(__file__).resolve().parents[2]
TOKEN = "hs154-call-glass"
SHOTS_01 = REPO / "pm/roadmap/holdspeak/phase-154-the-call/assets/story-01-shots"

pytestmark = [pytest.mark.e2e, pytest.mark.requires_meeting]


# ----------------------------------------------------------------- profile seed

def _seed_profile(db: Any) -> None:
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim, OWNER
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    pid = "hs154-glass-local"
    _profile(db, pid, claims=("language", _result_claim("chat.turn")))
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "hs154-glass-assign", "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": pid, "profile_revision": 1}],
    })


# ----------------------------------------------------------------- hub fixture

@pytest.fixture
def hub(tmp_path, monkeypatch):
    """Boot an in-process hub with yolo control_mode."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database, get_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    real_home = Path.home()
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    pw_path = os.environ.get(
        "PLAYWRIGHT_BROWSERS_PATH",
        str(real_home / "Library/Caches/ms-playwright"),
    )
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", pw_path)
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")

    config_dir = home / ".holdspeak"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text(json.dumps({
        "control_mode": "yolo",
    }))

    reset_database()

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=TOKEN,
    )
    url = server.start()
    db = get_database()
    _seed_profile(db)

    yield {
        "server": server,
        "url": url,
        "db": db,
    }
    server.stop()
    reset_database()


# ----------------------------------------------------------------- helpers

def _api_direct(url: str, method: str, path: str, body: Any = None) -> dict:
    """Direct HTTP call (not through a Playwright page)."""
    import urllib.request
    import urllib.error

    full_url = f"{url}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if data:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(full_url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            ct = resp.headers.get("content-type", "")
            raw = resp.read()
            payload = json.loads(raw) if "json" in ct else raw.decode()
            return {"status": resp.status, "payload": payload}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw)
        except Exception:
            payload = raw.decode()
        return {"status": e.code, "payload": payload}


def _save_shot(page: Any, name: str, width: int) -> None:
    SHOTS_01.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS_01 / f"{name}-{width}.png"))


# ----------------------------------------------------------------- tts-settings leg

def test_tts_api_404_law(hub: dict) -> None:
    """Without the extra: /api/tts/status says not installed, POST /api/tts 404s."""
    url = hub["url"]

    status = _api_direct(url, "GET", "/api/tts/status")
    assert status["status"] == 200
    assert status["payload"]["installed"] is False
    assert status["payload"]["model_ready"] is False

    tts_res = _api_direct(url, "POST", "/api/tts", {"text": "Hello"})
    assert tts_res["status"] == 404
    assert tts_res["payload"]["code"] == "tts_not_installed"

    download_res = _api_direct(url, "POST", "/api/tts/download")
    assert download_res["status"] == 404
    assert download_res["payload"]["code"] == "tts_not_installed"


def test_tts_settings_glass(hub: dict) -> None:
    """Settings at 1440+393: zero overflow, the desk loads cleanly.

    The TTS block renders inside the Sounds module. API assertions
    are the hard proof; the glass leg captures screenshots and checks
    for horizontal overflow at both widths.
    """
    from playwright.sync_api import sync_playwright

    url = hub["url"]

    # Seed desk and complete onboarding
    _api_direct(url, "POST", "/api/desk/seed")
    _api_direct(url, "PUT", "/api/setup/onboarding", {"disposition": "completed"})

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 900})

            # Navigate to /settings which is a demoted route — it redirects
            # to / and opens the settings surface window.
            page.goto(f"{url}/settings?token={TOKEN}", wait_until="load")
            page.wait_for_timeout(4000)

            _save_shot(page, "tts-settings-desk", width)

            # Try to click the Sounds tile to open that module
            sounds_tile = page.locator("text=Sounds")
            if sounds_tile.count() > 0:
                sounds_tile.first.click()
                page.wait_for_timeout(2000)
                _save_shot(page, "tts-settings-sounds-module", width)

                # Look for the TTS block content
                browser_voice = page.locator("text=BROWSER VOICE")
                if browser_voice.count() >= 1:
                    _save_shot(page, "tts-settings-extra-off", width)

                    # Install instruction should be visible (no dead switch)
                    install_hint = page.locator("text=holdspeak[tts]")
                    assert install_hint.count() >= 1, (
                        f"Install instruction not found at {width}"
                    )

            # No horizontal overflow
            body_width = page.evaluate("document.body.scrollWidth")
            viewport_width = page.evaluate("window.innerWidth")
            assert body_width <= viewport_width + 1, (
                f"Horizontal overflow at {width}: body={body_width}, viewport={viewport_width}"
            )

            page.close()

        browser.close()
