"""HS-174 -- Settings System Remote Access glass rig.

Five legs:
  1. OFF state (nothing beneath the toggle).
  2. Turn ON, issue a credential (the token row visible once; Copy;
     reload -> no token; the ledger row shows NEVER USED).
  3. Revoke -> row gone.
  4. Both widths (1440 + 393).

Shots to assets/story-02-shots/.
Companion to test_hs172_settings_meetings_glass.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _boot,
    _api,
    _assert_clean,
    _ensure_build,
    _settle,
    REPO,
)

pytest.importorskip("playwright.sync_api", reason="Settings glass needs Playwright")

SHOTS = REPO / "pm/roadmap/holdspeak/phase-174-reach/assets/story-02-shots"
TOKEN = "hs174-remote-settings"


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


def _open_system_module(page: Any) -> None:
    system_row = page.locator(
        ".surface-ledger-row",
        has=page.locator(".surface-ledger-primary", has_text="System"),
    )
    system_row.locator(".btn", has_text="Open").click()
    # Wait for the module to load -- the Remote access group label
    page.locator(".gadget-group-label", has_text="Remote access").wait_for(timeout=8_000)


class TestSettingsRemoteAccess:
    """HS-174 -- the Settings System Remote Access face."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.tmp_path = tmp_path

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_remote_off_state(self, width: int) -> None:
        """OFF state: only the toggle row, nothing beneath."""
        from playwright.sync_api import sync_playwright

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _navigate_to_settings_hub(page, self.base)
            _open_system_module(page)
            _settle(page)

            # Remote access group label present
            assert page.locator(
                ".gadget-group-label", has_text="Remote access"
            ).count() >= 1, f"Remote access section absent at {width}"

            # Streamable HTTP row present
            module_text = page.locator(".desk-surface-body").text_content() or ""
            assert "Streamable HTTP" in module_text, (
                f"Streamable HTTP label missing at {width}"
            )

            # CycleGadget present with OFF
            remote_select = page.locator(
                "select[aria-label='Remote transport']"
            )
            assert remote_select.count() >= 1, f"No transport toggle at {width}"
            assert remote_select.input_value() == "OFF", (
                f"Toggle not OFF by default at {width}"
            )

            # No credentials section, no Issue credential
            assert "CREDENTIALS" not in module_text, (
                f"CREDENTIALS visible when OFF at {width}"
            )
            assert page.locator(".btn", has_text="Issue credential").count() == 0, (
                f"Issue credential visible when OFF at {width}"
            )

            # No raw <button>
            raw_buttons = page.evaluate("""() => {
                const body = document.querySelector('.desk-surface-body');
                if (!body) return [];
                const allowed = ['btn', 'desk-mic', 'gadget-cycle',
                    'gadget-stepper-btn', 'gadget-table-add',
                    'gadget-table-delete', 'surface-ledger-line',
                    'gadget-fold-toggle'];
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
                path=str(SHOTS / f"build-remote-off-{width}.png"),
                full_page=True,
            )

            _assert_clean(page, errors)
            page.close()
            errors.clear()
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_remote_on_issue_revoke(self, width: int) -> None:
        """Turn ON, issue a credential, verify token visible once,
        reload -> no token, NEVER USED; then revoke -> row gone."""
        from playwright.sync_api import sync_playwright

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _navigate_to_settings_hub(page, self.base)
            _open_system_module(page)
            _settle(page)

            # Turn remote ON via the wire (the CycleGadget triggers a PUT)
            toggle = page.locator("select[aria-label='Remote transport']")
            toggle.select_option("ON")
            # Wait for the Issue credential button to appear (remote is ON)
            page.locator(".btn", has_text="Issue credential").wait_for(timeout=8_000)

            # Screenshot: remote ON, no credentials
            SHOTS.mkdir(parents=True, exist_ok=True)
            _settle(page)
            page.screenshot(
                path=str(SHOTS / f"build-remote-on-{width}.png"),
                full_page=True,
            )

            # Click Issue credential
            page.locator(".btn", has_text="Issue credential").click()
            # Wait for the issue well
            page.locator("input[aria-label='Credential name']").wait_for(timeout=5_000)

            # Fill in credential name
            name_input = page.locator("input[aria-label='Credential name']")
            name_input.fill("test-glass-runner")

            # Screenshot: issue well open
            _settle(page)
            page.screenshot(
                path=str(SHOTS / f"build-remote-issue-{width}.png"),
                full_page=True,
            )

            # Click Issue button
            page.locator("[data-testid='issue-submit']").click()

            # Wait for the one-time token to appear
            page.locator("[data-testid='token-value']").wait_for(timeout=8_000)

            # The token is visible
            token_el = page.locator("[data-testid='token-value']")
            token_text = token_el.text_content() or ""
            assert len(token_text) > 10, f"Token too short: {token_text}"

            # Copy button present
            assert page.locator("[data-testid='token-copy']").count() >= 1, (
                f"Copy button absent at {width}"
            )

            # TOKEN SHOWN ONCE caption
            module_text = page.locator(".desk-surface-body").text_content() or ""
            assert "TOKEN SHOWN ONCE" in module_text, (
                f"Token caption missing at {width}"
            )

            # Screenshot: token visible
            _settle(page)
            if width == 1440:
                page.screenshot(
                    path=str(SHOTS / "build-remote-token-1440.png"),
                    full_page=True,
                )

            # The credential row should also be visible (with NEVER USED)
            assert "test-glass-runner" in module_text or page.locator(
                ".surface-ledger-primary", has_text="test-glass-runner"
            ).count() >= 1, f"Credential row absent at {width}"

            # Reload the page -> no token shown again
            _navigate_to_settings_hub(page, self.base)
            _open_system_module(page)
            _settle(page)

            # Re-enable: the remote was turned ON via the API earlier but
            # the app reloads fresh state; turn ON again if needed.
            toggle2 = page.locator("select[aria-label='Remote transport']")
            if toggle2.input_value() == "OFF":
                toggle2.select_option("ON")
                page.locator(".btn", has_text="Issue credential").wait_for(timeout=8_000)

            # Wait for the credential row to load
            page.locator(
                ".surface-ledger-primary", has_text="test-glass-runner"
            ).wait_for(timeout=8_000)

            # Token should NOT be visible after reload
            assert page.locator("[data-testid='token-value']").count() == 0, (
                f"Token visible after reload at {width}"
            )

            # NEVER USED should be visible
            reload_text = page.locator(".desk-surface-body").text_content() or ""
            assert "NEVER USED" in reload_text, (
                f"NEVER USED absent after reload at {width}"
            )

            # Revoke the credential
            revoke_btn = page.locator(".btn", has_text="Revoke").first
            revoke_btn.click()

            # Wait for the row to disappear
            page.locator(
                ".surface-ledger-primary", has_text="test-glass-runner"
            ).wait_for(state="detached", timeout=8_000)

            # Credential row gone
            final_text = page.locator(".desk-surface-body").text_content() or ""
            assert "test-glass-runner" not in final_text, (
                f"Credential row still present after revoke at {width}"
            )

            _assert_clean(page, errors)
            page.close()
            errors.clear()
            browser.close()
