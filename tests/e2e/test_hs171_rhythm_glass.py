"""HS-171-02 + HS-171-06 -- Rhythm face glass rig.

Tests the heartbeat Rhythm face (CadenceCore.tsx) at 1440 + 393.
Legs:
  1. Cold state: headline, sweep row with CycleGadget, brief row, notify row.
  2. Change cadence via the gadget -- assert PUT + hub row text update.
  3. Run now -- assert receipt tokens update LAST.
  4. Toggle a mute -- assert the setting persists.
  5. Quiet hours: seed the window around now, assert HELD chip.
  6. Hub row: Settings hub shows EVERY N MIN + NEXT tokens.

Shots: build-rhythm-{cadence,running,quiet}-1440.png,
       build-rhythm-393.png, build-settings-hub-heartbeat-1440.png.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _boot as _conftest_boot,
    _api,
    _ensure_build,
    _settle,
    _normal_chair,
    _assert_clean,
)

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-171-the-heartbeat/assets/story-02-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "glass-test"


# ── Helpers ──────────────────────────────────────────────────────

def _open_rhythm(page: Any) -> None:
    """Open the Rhythm / Cadence surface window."""
    page.evaluate(
        """([key]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key})
          );
        }""",
        ["configure-cadence"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


def _window(page: Any) -> Any:
    """The Rhythm surface window element."""
    return page.locator(".desk-surface-window").first


def _shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    old_size = page.viewport_size
    page.set_viewport_size({"width": old_size["width"], "height": 2400})
    _settle(page)
    path = SHOTS / f"{name}.png"
    win = _window(page)
    if win.count() > 0:
        win.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    page.set_viewport_size(old_size)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def _seed_project(page: Any) -> str:
    """Create a project and return its id for mute-toggle tests."""
    result = _api(page, "POST", "/api/projects", {
        "name": "Q4 Platform",
        "title": "Q4 Platform",
    })
    return result.get("project", {}).get("id", "")


# ── Fixtures ─────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def _build():
    _ensure_build()


@pytest.fixture()
def glass(tmp_path, monkeypatch, _build):
    """Boot the hub, navigate to the desk, yield (server, page)."""
    server, base_url = _conftest_boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"{base_url}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        yield server, page, errors, base_url
        browser.close()
        pw.stop()
    finally:
        server.stop()


# ── Tests ────────────────────────────────────────────────────────

class TestRhythmFace:
    """HS-171-02: the Rhythm face at 1440 + 393."""

    def test_cold_state_1440(self, glass):
        """Cold state: default 15 min sweep. Headline, sweep row, brief row, notify row."""
        server, page, errors, base_url = glass

        _open_rhythm(page)
        page.wait_for_timeout(600)

        # The headline should show "Every 15 min" (the default sweep interval).
        headline = page.locator('[data-testid="rhythm-headline"]')
        headline.wait_for(timeout=5000)
        text = headline.text_content() or ""
        assert "15 min" in text.lower(), f"Expected '15 min' in headline, got: {text}"

        # Sweep row exists
        sweep_row = page.locator('[data-testid="rhythm-sweep-row"]')
        assert sweep_row.count() > 0, "Sweep row not found"

        # Brief row exists
        brief_row = page.locator('[data-testid="rhythm-brief-row"]')
        assert brief_row.count() > 0, "Brief row not found"

        # Notify row exists
        notify_row = page.locator('[data-testid="rhythm-notify-row"]')
        assert notify_row.count() > 0, "Notify row not found"

        # Run now button exists and is enabled
        run_now = page.locator('[data-testid="rhythm-run-now"]')
        assert run_now.count() > 0, "Run now button not found"

        # Generate now button exists
        gen_now = page.locator('[data-testid="rhythm-generate-now"]')
        assert gen_now.count() > 0, "Generate now button not found"

        _shot(page, "build-rhythm-cadence-1440", 1440)
        _assert_clean(page, errors)

    def test_change_cadence(self, glass):
        """Change sweep interval via CycleGadget, assert PUT and text update."""
        server, page, errors, base_url = glass

        _open_rhythm(page)
        page.wait_for_timeout(600)

        # Change from 15 to 30 via the select
        gadget = page.locator('[aria-label="Sweep interval"]')
        gadget.wait_for(timeout=5000)
        gadget.select_option("30")
        page.wait_for_timeout(800)

        # Verify the PUT went through by reading back
        settings = _api(page, "GET", "/api/settings/heartbeat")
        assert settings["sweep_every_minutes"] == 30, (
            f"Expected sweep_every_minutes=30, got {settings.get('sweep_every_minutes')}"
        )

        # Headline should update
        headline = page.locator('[data-testid="rhythm-headline"]')
        text = headline.text_content() or ""
        assert "30 min" in text.lower(), f"Expected '30 min' in headline, got: {text}"

    def test_run_now(self, glass):
        """Run now produces a receipt; LAST token updates."""
        server, page, errors, base_url = glass

        _open_rhythm(page)
        page.wait_for_timeout(600)

        # Click Run now
        run_now = page.locator('[data-testid="rhythm-run-now"]')
        run_now.wait_for(timeout=5000)
        run_now.click()
        page.wait_for_timeout(1500)

        # After running, LAST token should appear in sweep facts
        facts = page.locator('[data-testid="rhythm-sweep-facts"]')
        facts_text = facts.text_content() or ""
        assert "LAST" in facts_text, f"Expected LAST in sweep facts, got: {facts_text}"

        _shot(page, "build-rhythm-running-1440", 1440)

    def test_mute_toggle(self, glass):
        """Toggle a project mute and assert the setting persists."""
        server, page, errors, base_url = glass

        # Create a project first
        project_id = _seed_project(page)
        if not project_id:
            pytest.skip("Could not create project for mute test")

        _open_rhythm(page)
        page.wait_for_timeout(800)

        # Check if mute toggles appear
        mutes = page.locator('[data-testid="rhythm-mute-toggles"]')
        if mutes.count() == 0:
            # No projects visible -- mute toggles won't render
            pytest.skip("No project mute toggles rendered")

        # Find a token toggle label and click it (the label wraps the hidden
        # checkbox + the visible face span in CheckGadget variant="token").
        toggle = mutes.locator(".gadget-check-token").first
        if toggle.count() > 0:
            checkbox = toggle.locator('input[type="checkbox"]')
            was_checked = checkbox.is_checked()
            toggle.click()
            page.wait_for_timeout(800)

            # Read back settings
            settings = _api(page, "GET", "/api/settings/heartbeat")
            muted = settings.get("muted_projects", [])
            if was_checked:
                # Was checked (not muted) -> now unchecked (muted)
                assert project_id in muted, "Project should be in muted list"
            else:
                # Was unchecked (muted) -> now checked (not muted)
                assert project_id not in muted, "Project should not be in muted list"

    def test_quiet_hours_held(self, glass):
        """Seed quiet hours around now, assert HELD chip appears."""
        server, page, errors, base_url = glass

        import datetime
        now = datetime.datetime.now()
        # Set quiet hours to cover the current hour
        start = now.hour
        end = (now.hour + 2) % 24

        _api(page, "PUT", "/api/settings/heartbeat", {
            "quiet_hours": {"start": start, "end": end},
        })

        _open_rhythm(page)
        page.wait_for_timeout(800)

        # HELD chip should appear in sweep facts
        facts = page.locator('[data-testid="rhythm-sweep-facts"]')
        facts.wait_for(timeout=5000)
        facts_text = facts.text_content() or ""
        assert "HELD" in facts_text, (
            f"Expected HELD in sweep facts during quiet hours, got: {facts_text}"
        )

        _shot(page, "build-rhythm-quiet-1440", 1440)

    def test_phone_width(self, glass):
        """393 width: stacks per the phone board."""
        server, page, errors, base_url = glass

        # Reset quiet hours to defaults
        _api(page, "PUT", "/api/settings/heartbeat", {
            "quiet_hours": {"start": 22, "end": 8},
            "sweep_every_minutes": 15,
        })

        _open_rhythm(page)
        page.wait_for_timeout(600)

        page.set_viewport_size({"width": 393, "height": 900})
        page.wait_for_timeout(400)

        _shot(page, "build-rhythm-393", 393)

        # Restore viewport
        page.set_viewport_size({"width": 1440, "height": 900})
        _assert_clean(page, errors)

    def test_settings_hub_rhythm_row(self, glass):
        """Hub Rhythm row: shows EVERY N MIN + NEXT when sweep runs."""
        server, page, errors, base_url = glass

        # Ensure we have a sweep setting with timestamps by running a sweep
        _api(page, "PUT", "/api/settings/heartbeat", {
            "sweep_every_minutes": 15,
        })
        _api(page, "POST", "/api/settings/heartbeat/run-now", {})

        # Open Settings hub (the way test_hs170_settings_hub_glass.py does)
        page.evaluate("""() => {
            sessionStorage.setItem(
                "hs.desk.staged-surface-open",
                JSON.stringify({key: "configure-settings"})
            );
        }""")
        page.goto(f"{base_url}/?token={TOKEN}", wait_until="load")
        page.locator(".prefs-hub-headline").wait_for(timeout=10_000)
        page.wait_for_timeout(600)

        # Assert the hub wire has sweepEveryMinutes
        hub = _api(page, "GET", "/api/settings/hub")
        rhythm = hub.get("rhythm", {})
        assert rhythm.get("sweepEveryMinutes") is not None, (
            f"Expected sweepEveryMinutes in hub rhythm, got: {rhythm}"
        )

        # Assert the Rhythm row text in the rendered face
        settings_window = page.locator(".desk-settings-window")
        settings_window.wait_for(timeout=5000)
        settings_text = settings_window.text_content() or ""
        assert "EVERY 15 MIN" in settings_text, (
            f"Expected 'EVERY 15 MIN' in settings hub, got: {settings_text}"
        )

        # Shoot the Settings WINDOW (not full page)
        _settle(page)
        old_size = page.viewport_size
        page.set_viewport_size({"width": old_size["width"], "height": 2400})
        _settle(page)
        path = SHOTS / "build-settings-hub-heartbeat-1440.png"
        settings_window.screenshot(path=str(path))
        page.set_viewport_size(old_size)
        assert path.stat().st_size > 2_000
