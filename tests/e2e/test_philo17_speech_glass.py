"""PHILO-17 speech — "Speech is not set up" on every face that needs speech.

A walker on a fresh desk with no speech (Whisper) model saw Speak say
READY, Record say "Listening for speech", Runs on say TOOL INCOMPATIBLE and
Setup say PASS; his first meeting was saved with no transcript. The rig's
isolated HOME has no speech model, which is that desk. Each face now says
"Speech is not set up" and offers ONE verb, "Set up speech · <size>" (the
first-run page's speech-only download). The rig never presses it: the
download would reach huggingface.co.

Shots land in .tmp/evidence-shots/philo17/speech/<face>-<width>.png.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _api,
    _assert_clean,
    _boot,
    _ensure_build,
    _normal_chair,
    _settle,
    clear_hub_windows,
)
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="speech glass needs Playwright")

SHOTS = evidence_dir("philo17/speech")
SHOTS.mkdir(parents=True, exist_ok=True)
TOKEN = "philo17-speech"
VERB = re.compile(r"^Set up speech · \d+ MB$")

#: (staged surface key, the row's test id, the face's shot name)
FACES = (
    ("dictate", "speak-speech-setup", "speak"),
    ("record-live", "live-speech-setup", "record"),
    ("configure-runs-on", "runson-speech-setup", "runs-on"),
    ("configure-setup", "setup-speech-setup", "setup"),
)


def _stage(page: Any, key: str) -> None:
    clear_hub_windows(page, token=TOKEN)
    page.evaluate(
        """([key]) => {
          localStorage.removeItem("hs.desk.workspace.v1");
          sessionStorage.setItem("hs.desk.staged-surface-open", JSON.stringify({key}));
        }""",
        [key],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


def _shot(page: Any, row: Any, name: str, width: int) -> None:
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    window = row.locator("xpath=ancestor::*[contains(@class,'desk-surface-window')][1]")
    (window if window.count() else page).screenshot(path=str(path))
    assert path.stat().st_size > 2_000


def _walk(page: Any, url: str, width: int) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    _normal_chair(page)

    speech = _api(page, "GET", "/api/setup/local-ai", token=TOKEN)["speech"]
    assert speech["ready"] is False and speech["state"] == "will_download", speech

    for key, test_id, name in FACES:
        _stage(page, key)
        row = page.get_by_test_id(test_id)
        row.wait_for(timeout=20_000)
        verb = page.get_by_test_id(f"{test_id}-verb")
        assert VERB.match(verb.inner_text().strip()), verb.inner_text()
        if key == "configure-setup":
            # The doctor row already says it; the verb stands alone on it.
            assert page.get_by_test_id(f"{test_id}-line").count() == 0
            assert "Speech is not set up" in page.locator("body").inner_text()
        else:
            assert page.get_by_test_id(f"{test_id}-line").inner_text() == "Speech is not set up"
        # Egress where the fetch happens: the host chip beside the verb.
        assert "HUGGINGFACE.CO" in row.inner_text().upper()
        if key == "record-live":
            body = page.locator("body").inner_text()
            assert "Ready to record audio only" in body or "Start meeting" in body
        _shot(page, row, name, width)


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_every_speech_face_says_speech_is_not_set_up(tmp_path: Path, monkeypatch: Any, width: int, height: int) -> None:
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": width, "height": height})
            _walk(page, url, width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
