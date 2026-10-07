"""PHILO-14 A1 (#939, Astra's P2) -- the FRESH arrival, as rendered.

The Chair is the screen of objects (board A-1): a fresh desk opens with the
four Chair windows closed. The window-content fences pre-open them
(``pytest.mark.chair_windows_open``); this file does NOT. It starts from the
default desk and reaches each window by the owner's real gestures:

  1440  Needs you: Enter on its drawer (or a double press). Brief, The week,
        Capture: Window > Chair > <name>. TALK: one press, on the screen.
  393   Needs you: Enter on its drawer. Brief, The week: Go > <name> (two
        taps, Astra's P3 ruling). Capture: the Dock's Speak (one tap).

And the engines-missing arrival: the Needs you window, reached that way,
names its SETUP row (the cold HOME assigns no summary engine).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _ensure_build, _normal_chair, _settle
from .test_philo13_11_chair_glass import _seed
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the fresh arrival needs Playwright")

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(600, method="thread")]

TOKEN = "philo14-a1-fresh"
SHOTS = evidence_dir("docs/internal/philo/phase-14/a1-shots/fresh")
SIZES = {1440: 900, 393: 852}


def _shell(page: Any, name: str) -> Any:
    return page.locator(f".desk-window-shell.chair-window[aria-label='{name}']")


class TestFreshArrival:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        _seed(tmp_path / "home")
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _press(self, page: Any, loc: Any, width: int) -> None:
        loc.first.wait_for()
        if width < 720:
            loc.first.tap()
        else:
            loc.first.click()
        page.wait_for_timeout(300)

    def _menu_pick(self, page: Any, width: int, name: str) -> int:
        """Open the Chair window `name` from the menu; returns the presses."""
        if width < 720:
            self._press(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"), width)
            self._press(page, page.locator(f".desk-menu-list [role='menuitemcheckbox']:has-text('{name}')"), width)
            return 2
        self._press(page, page.locator(".desk-verbbar-item[data-menu-id='window'] button"), width)
        page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Chair')").hover()
        self._press(page, page.locator(f".desk-menu-list [role='menuitemcheckbox']:has-text('{name}')"), width)
        return 2

    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_fresh_desk_reaches_every_chair_window(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                      device_scale_factor=1, has_touch=width < 720)
            page = ctx.new_page()
            page.set_default_timeout(20_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                page.locator("[data-testid=desk-screen]").wait_for()
                _settle(page)
                # the default desk: no Chair window open
                assert page.locator(".desk-window-shell.chair-window").count() == 0
                page.screenshot(path=str(SHOTS / f"fresh-0-screen-{width}.png"))

                # Needs you: Enter on its drawer; the engines-missing SETUP row is named
                drawer = page.locator(".desk-screen [data-object-id='drawer:needs']")
                drawer.focus()
                page.keyboard.press("Enter")
                _shell(page, "Needs you").wait_for()
                setup = page.get_by_test_id("arrival-blocker")
                setup.wait_for()
                assert "No engine" in setup.inner_text(), setup.inner_text()
                assert "Choose an engine" in setup.inner_text()
                page.screenshot(path=str(SHOTS / f"fresh-1-needs-{width}.png"))

                # Brief and The week by the menu (two presses each)
                for name, testid in (("Brief", "arrival-brief"), ("The week", None)):
                    presses = self._menu_pick(page, width, name)
                    assert presses <= 2
                    _shell(page, name).wait_for()
                    if testid:
                        _shell(page, name).get_by_test_id(testid).wait_for()
                    page.screenshot(path=str(SHOTS / f"fresh-2-{name.replace(' ', '-').lower()}-{width}.png"))

                # Capture / TALK
                if width < 720:
                    self._press(page, page.locator(".desk-dock [aria-label^='Speak']"), width)
                    _shell(page, "Capture").wait_for()
                    _shell(page, "Capture").get_by_test_id("arrival-capture-bar").wait_for()
                else:
                    talk = page.get_by_test_id("desk-screen-talk").get_by_role("button")
                    assert talk.count() == 1 and talk.first.is_visible()
                    self._menu_pick(page, width, "Capture")
                    _shell(page, "Capture").get_by_test_id("arrival-capture-bar").wait_for()
                page.screenshot(path=str(SHOTS / f"fresh-3-capture-{width}.png"))
                assert not errors, errors
            finally:
                browser.close()
