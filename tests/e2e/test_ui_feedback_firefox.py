"""Loaded Settings feedback in Firefox: repeated capture, save and transport retry."""
from __future__ import annotations

import json
import time
import wave
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, clear_hub_windows
from .test_ui_feedback_glass import _browser_png_facts

SHOTS = evidence_dir("ui-feedback-firefox")
TOKEN = "feedback-firefox-settings"


def _feedback_name(width: int) -> str:
    """The title-bar Feedback verb names what the window shows: on the phone
    the title bar names the open Settings pane (#1458), here You."""
    return "Give feedback on Settings" if width >= 720 else "Give feedback on You"


# Absolute UI timing is measured as a separate locked run. Concurrent
# Chromium/Firefox startup can exceed these limits through CPU contention;
# the complete tape still runs this check, with all budgets unchanged.
@pytest.mark.slow
@pytest.mark.parametrize("width", [1440, 393])
def test_loaded_settings_repeated_feedback_and_save_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int
) -> None:
    from playwright.sync_api import sync_playwright

    monkeypatch.setenv("HOLDSPEAK_UI_FEEDBACK", "1")
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    observations: list[dict[str, Any]] = []
    try:
        with sync_playwright() as pw:
            browser = pw.firefox.launch(
                headless=True,
                firefox_user_prefs={
                    "media.navigator.streams.fake": True,
                    "media.navigator.permission.disabled": True,
                    "media.autoplay.default": 0,
                    "media.autoplay.block-webaudio": False,
                },
            )
            context = browser.new_context(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
                device_scale_factor=2,
                reduced_motion="reduce",
            )
            page = context.new_page()
            page.set_default_timeout(20_000)
            page.add_init_script("""(() => {
              window.__feedbackBeat = {last: performance.now(), max: 0};
              setInterval(() => {
                const now = performance.now(), beat = window.__feedbackBeat;
                beat.max = Math.max(beat.max, now - beat.last); beat.last = now;
              }, 25);
            })()""")
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            assert _api(page, "GET", "/api/ui-feedback/status", token=TOKEN) == {"enabled": True}
            clear_hub_windows(page, TOKEN)
            _api(page, "POST", "/api/desk/windows/surface-settings/open", {}, token=TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            window = page.locator("[id='surface-settings'][data-layer='window']")
            name = window.get_by_role("textbox", name="Your name", exact=True)
            if width < 720:
                # Settings on the phone opens on its rail (#1458, the native
                # preference window); the You pane holds the name field.
                window.get_by_test_id("settings-index-you").click()
            name.wait_for()
            # The loading placeholder is cheap. The real Settings document is
            # the reported failure and must be present before measurements.
            window.locator("[data-settings-section='this-mac']").wait_for(state="attached")
            for index in range(3):
                draft = f"Settings feedback {index + 1}"
                name.fill(draft)
                page.evaluate("window.__feedbackBeat = {last: performance.now(), max: 0}")
                started = time.monotonic()
                window.get_by_role("button", name=_feedback_name(width), exact=True).click()
                strip = page.locator("[data-ui-feedback]")
                page.wait_for_function("""() => {
                  const strip = document.querySelector('[data-ui-feedback]');
                  return strip && /Recording|Not saved/.test(strip.textContent);
                }""")
                observation = {
                    "attempt": index + 1,
                    "capture_ms": round((time.monotonic() - started) * 1000),
                    "heartbeat_gap_ms": page.evaluate("window.__feedbackBeat.max"),
                    "strip": strip.inner_text(),
                }
                observations.append(observation)
                (SHOTS / f"settings-{width}-timing.json").write_text(json.dumps(observations, indent=2))
                page.screenshot(path=str(SHOTS / f"settings-{width}-{index + 1}-recording.png"))
                assert strip.get_by_text("Recording", exact=True).is_visible(), observation
                assert observation["capture_ms"] < 3000, observation
                # Concurrent glass runs need scheduling headroom; the
                # original regression blocks this heartbeat for >7 seconds.
                assert observation["heartbeat_gap_ms"] < 1000, observation
                # Firefox's fake device must deliver actual frames, rather
                # than ending the hold immediately after its grant resolves.
                page.wait_for_timeout(1200)
                rejected: list[str] = []
                if index == 2:
                    def interrupt_once(route: Any) -> None:
                        if not rejected:
                            rejected.append(route.request.post_data or "")
                            route.abort("failed")
                        else:
                            route.continue_()
                    page.route("**/api/ui-feedback", interrupt_once)
                    strip.get_by_role("button", name="Stop and save", exact=True).click()
                    strip.get_by_text("Not saved", exact=True).wait_for()
                    stop = strip.get_by_role("button", name="Retry", exact=True)
                else:
                    stop = strip.get_by_role("button", name="Stop and save", exact=True)
                with page.expect_response(
                    lambda r: r.url.endswith("/api/ui-feedback") and r.request.method == "POST"
                ) as saved:
                    stop.click()
                response = saved.value
                assert response.status == 200, response.text()
                if rejected:
                    assert response.request.post_data == rejected[0], "Retry changed the frozen report"
                receipt = response.json()
                strip.get_by_text("Saved", exact=True).wait_for()
                directory = Path(receipt["directory"])
                report = json.loads((directory / "report.json").read_text())
                assert report["context"]["owner"]["window_id"] == "surface-settings"
                assert any(f.get("label") == "Your name" and f.get("value") == draft
                           for f in report["context"]["fields"])
                with wave.open(str(directory / "audio.wav"), "rb") as audio:
                    assert audio.getnframes() >= 1600 and audio.getframerate() == 16_000
                png = directory / "window.png"
                assert _browser_png_facts(page, png)["colors"] > 8
                (SHOTS / f"settings-{width}-{index + 1}-window.png").write_bytes(png.read_bytes())
                page.screenshot(path=str(SHOTS / f"settings-{width}-{index + 1}-saved.png"))
                assert page.locator("body > div[style*='-100000px']").count() == 0
            browser.close()
    finally:
        server.stop()
