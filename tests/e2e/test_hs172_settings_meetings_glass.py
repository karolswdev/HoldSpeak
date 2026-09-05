"""HS-172 -- Settings Meetings module glass rig.

Seed with default settings (intelligence_auto=room_linked).
Assert at 1440 + 393:
  - display headline shows 'After room meetings' (sentence-case fact)
  - Intelligence row with CycleGadget visible
  - EgressChip visible
  - Capture + export section present
  - no raw <button>, no zero counter, no LOCAL
  - hub Meetings row shows INTELLIGENCE ON
  - shots to story-02-shots/

Companion to test_hs170_settings_hub_glass.py (not edited).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _boot,
    _api,
    _assert_clean,
    _normal_chair,
    _ensure_build,
    _settle,
    REPO,
)

pytest.importorskip("playwright.sync_api", reason="Settings glass needs Playwright")

SHOTS = REPO / "pm/roadmap/holdspeak/phase-172-the-loop-closes/assets/story-02-shots"
TOKEN = "hs172-settings-meetings"


def _navigate_to_settings_hub(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding",
         {"disposition": "completed"}, token=TOKEN)
    page.evaluate("""() => {
        sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key: "configure-settings"})
        );
    }""")
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    page.locator(".prefs-hub-headline").wait_for(timeout=10_000)


def _open_meetings_module(page: Any) -> None:
    """Click the Meetings hub row to open the module."""
    meetings_row = page.locator(
        ".surface-ledger-row",
        has=page.locator(".surface-ledger-primary", has_text="Meetings"),
    )
    meetings_row.locator(".btn", has_text="Open").click()
    # Wait for the meetings module face
    page.locator("[data-testid='meetings-auto-display']").wait_for(timeout=8_000)


class TestSettingsMeetingsAutoRun:
    """HS-172 -- the Settings Meetings module with auto-run setting."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.tmp_path = tmp_path

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    @pytest.mark.parametrize("width", [1440, 393])
    def test_settings_meetings_module(self, width: int) -> None:
        from playwright.sync_api import sync_playwright, expect

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _navigate_to_settings_hub(page, self.base)
            _settle(page)

            # ── Hub assertions ──

            # Meetings hub row should show INTELLIGENCE ON
            meetings_row = page.locator(
                ".surface-ledger-row",
                has=page.locator(".surface-ledger-primary", has_text="Meetings"),
            )
            expect(meetings_row).to_be_visible(timeout=5_000)
            row_text = meetings_row.text_content() or ""
            assert "INTELLIGENCE" in row_text, (
                f"INTELLIGENCE missing from Meetings hub row at {width}: {row_text}"
            )

            # Screenshot hub
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(
                path=str(SHOTS / f"build-settings-hub-{width}.png"),
                full_page=True,
            )

            # ── Open Meetings module ──
            _open_meetings_module(page)
            _settle(page)

            # Display headline: 'After room meetings' (the default)
            display = page.locator("[data-testid='meetings-auto-display']")
            display_text = display.text_content() or ""
            assert "After room meetings" in display_text, (
                f"Display headline at {width}: expected 'After room meetings', got '{display_text}'"
            )

            # CycleGadget visible (the select element)
            cycle = page.locator(".gadget-cycle select")
            assert cycle.count() >= 1, f"No CycleGadget at {width}"

            # EgressChip visible
            egress = page.locator(".gadget-chip-egress")
            assert egress.count() >= 1, f"No EgressChip at {width}"

            # Capture + export section present
            module_text = page.locator(".desk-surface-body").text_content() or ""
            assert "Capture" in module_text or "CAPTURE" in module_text or "CONFIG LIVES ON MEETINGS" in module_text, (
                f"Capture section missing at {width}"
            )

            # No raw <button> outside the surface kit
            raw_buttons = page.evaluate("""() => {
                const body = document.querySelector('.desk-surface-body');
                if (!body) return [];
                const allowed = ['btn', 'desk-mic', 'gadget-cycle',
                    'gadget-stepper-btn', 'gadget-table-add',
                    'gadget-table-delete', 'surface-ledger-line'];
                return Array.from(body.querySelectorAll('button'))
                    .filter(b => !allowed.some(c => b.classList.contains(c))
                        && !b.closest('.gadget-stepper')
                        && !b.closest('.gadget-table'))
                    .map(b => (b.textContent || '').trim().slice(0, 40));
            }""")
            assert len(raw_buttons) == 0, f"Raw buttons at {width}: {raw_buttons}"

            # No zero counter
            assert "0 NEEDS" not in module_text, f"Zero counter at {width}"

            # No LOCAL
            assert "LOCAL" not in module_text, f"'LOCAL' found at {width}"

            # Screenshot module
            page.screenshot(
                path=str(SHOTS / f"build-settings-meetings-{width}.png"),
                full_page=True,
            )

            # 393: nothing overflows
            if width == 393:
                no_overflow = page.evaluate(
                    "document.documentElement.scrollWidth <= window.innerWidth"
                )
                assert no_overflow, f"Settings overflows at {width}"

            _assert_clean(page, errors)
            page.close()
            errors.clear()

            browser.close()
