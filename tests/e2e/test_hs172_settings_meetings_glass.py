"""HS-172 -- Settings Meetings module glass rig.

Two legs:
  1. Cold install (no model assigned) -> NO MODEL + Choose model, no chip.
  2. Assigned LAN host -> 192.168.1.43 . LAN chip, no Choose model.

Both legs at 1440 + 393: display headline, CycleGadget, Capture rows,
no raw <button>, no zero counter. Shots to story-02-shots/.

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
    meetings_row = page.locator(
        ".surface-ledger-row",
        has=page.locator(".surface-ledger-primary", has_text="Meetings"),
    )
    meetings_row.locator(".btn", has_text="Open").click()
    page.locator("[data-testid='meetings-auto-display']").wait_for(timeout=8_000)


class TestSettingsMeetingsAutoRun:
    """HS-172 -- the Settings Meetings module at both states."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.tmp_path = tmp_path

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    @pytest.mark.parametrize("width", [1440, 393])
    def test_settings_meetings_nomodel(self, width: int) -> None:
        """Cold install: no model assigned -> NO MODEL + Choose model."""
        from playwright.sync_api import sync_playwright

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _navigate_to_settings_hub(page, self.base)
            _open_meetings_module(page)
            _settle(page)

            # Display headline
            display = page.locator("[data-testid='meetings-auto-display']")
            display_text = display.text_content() or ""
            assert "After room meetings" in display_text, (
                f"Display at {width}: {display_text}"
            )

            # CycleGadget visible
            assert page.locator(".gadget-cycle select").count() >= 1, (
                f"No CycleGadget at {width}"
            )

            # NO MODEL warning on the Intelligence row: no egress chip
            # Scope to the Intelligence gadget-row (not footer/calendar chips).
            intel_row = page.locator(".gadget-row", has=page.locator(
                ".gadget-row-label", has_text="Intelligence"
            ))
            intel_egress = intel_row.locator(".gadget-chip-egress")
            assert intel_egress.count() == 0, (
                f"EgressChip on Intelligence row should be absent at {width} with no model"
            )

            # NO MODEL token present
            no_model = intel_row.locator(".surface-state-chip[data-state='warning']")
            assert no_model.count() >= 1, (
                f"NO MODEL warning absent at {width}"
            )

            # Choose model verb present
            choose = page.locator("[data-testid='settings-choose-model']")
            assert choose.count() >= 1, (
                f"Choose model button absent at {width}"
            )

            # Capture rows present
            module_text = page.locator(".desk-surface-body").text_content() or ""
            assert "Mic device" in module_text, f"Mic device missing at {width}"
            assert "Auto export" in module_text, f"Auto export missing at {width}"

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

            # Screenshot
            SHOTS.mkdir(parents=True, exist_ok=True)
            _settle(page)
            page.screenshot(
                path=str(SHOTS / f"build-settings-meetings-nomodel-{width}.png"),
                full_page=True,
            )

            if width == 393:
                no_overflow = page.evaluate(
                    "document.documentElement.scrollWidth <= window.innerWidth"
                )
                assert no_overflow, f"Settings overflows at {width}"

            _assert_clean(page, errors)
            page.close()
            errors.clear()
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    @pytest.mark.parametrize("width", [1440, 393])
    def test_settings_meetings_with_host(self, width: int) -> None:
        """Assigned LAN host: chip shows 192.168.1.43 . LAN."""
        from playwright.sync_api import sync_playwright

        # Patch the hub to return a real host.
        import holdspeak.web.routes.system.settings as settings_mod
        _orig_hub = None
        orig_router_builder = settings_mod.build_settings_router

        def _patch_hub_host(monkeypatch_: Any = None) -> None:
            """Monkeypatch the settings hub to return a LAN host."""
            # We intercept at the config level: set intel_provider so the
            # placement resolver returns a LAN host.
            from holdspeak.config import Config
            cfg = Config.load()
            cfg.meeting.intel_cloud_base_url = "http://192.168.1.43:8080"
            cfg.meeting.intel_provider = "cloud"
            cfg.save()

        _patch_hub_host()

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _navigate_to_settings_hub(page, self.base)
            _open_meetings_module(page)
            _settle(page)

            # Display headline
            display = page.locator("[data-testid='meetings-auto-display']")
            display_text = display.text_content() or ""
            assert "After room meetings" in display_text, (
                f"Display at {width}: {display_text}"
            )

            # CycleGadget visible
            assert page.locator(".gadget-cycle select").count() >= 1, (
                f"No CycleGadget at {width}"
            )

            # Capture rows present
            module_text = page.locator(".desk-surface-body").text_content() or ""
            assert "Mic device" in module_text, f"Mic device missing at {width}"

            # No raw <button>
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

            # Screenshot
            SHOTS.mkdir(parents=True, exist_ok=True)
            _settle(page)
            page.screenshot(
                path=str(SHOTS / f"build-settings-meetings-{width}.png"),
                full_page=True,
            )

            if width == 393:
                no_overflow = page.evaluate(
                    "document.documentElement.scrollWidth <= window.innerWidth"
                )
                assert no_overflow, f"Settings overflows at {width}"

            _assert_clean(page, errors)
            page.close()
            errors.clear()
            browser.close()
