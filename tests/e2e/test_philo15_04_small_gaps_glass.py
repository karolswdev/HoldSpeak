"""PHILO-15 04 -- the Parked drawer and the denied calendar, as rendered.

Gap 14: the screen's Parked icon opens the Parked drawer, every parked
object across kinds in one list. The rig parks a meeting and a Project on
the real hub, opens the drawer by the owner's gesture (Enter at 1440, a
double tap at 393), sees both, and restores the Project with the receipt.

Gap 12: with macOS Calendar access denied, the first-run Calendar card
shows Open System Settings and Check again. EventKit and the macOS ``open``
are doubles in the hub process; no real permission is read and no System
Settings window opens.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _images_loaded, _normal_chair, _settle
from .test_philo13_11_chair_glass import _seed
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the lane-04 glass needs Playwright")

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(600, method="thread")]

TOKEN = "philo15-04"
SHOTS = evidence_dir("docs/internal/philo/phase-15/04-shots")
SIZES = {1440: 900, 393: 852}


class _Mac:
    """EventKit says denied until Check again finds it allowed; the open is counted."""

    def __init__(self) -> None:
        self.state = "denied"
        self.opens = 0

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import holdspeak.macos_calendar as macos

        monkeypatch.setattr(macos, "access_state", lambda: self.state)
        monkeypatch.setattr(macos, "list_calendars", lambda: [])
        monkeypatch.setattr(macos, "open_privacy_settings", self.open)

    def open(self) -> bool:
        self.opens += 1
        return True


def _context(pw: Any, width: int) -> Any:
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                              device_scale_factor=1, has_touch=width < 720)
    page = ctx.new_page()
    page.set_default_timeout(20_000)
    return browser, page


class TestParkedDrawer:
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

    @pytest.mark.parametrize("width", [1440, 393])
    def test_park_a_meeting_and_a_project_see_both_restore_one(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page = _context(pw, width)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                page.locator("[data-testid=desk-screen]").wait_for()
                # Park one meeting and one Project on the real hub.
                _api(page, "DELETE", "/api/meetings/m-arch", token=TOKEN)
                _api(page, "DELETE", "/api/projects/p-hiring", token=TOKEN)

                parked = page.locator(".desk-screen [data-object-id='drawer:parked']")
                parked.first.wait_for()
                if width < 720:
                    parked.first.dblclick()
                else:
                    parked.first.focus()
                    page.keyboard.press("Enter")
                window = page.locator(".desk-window-shell[aria-label='Parked']")
                window.wait_for()
                rows = window.locator(".object-list-row")
                meeting = window.get_by_role("button", name="Architecture review: tracing, MEETING", exact=False)
                project = window.get_by_role("button", name="Staff hiring loop, PROJECT", exact=False)
                meeting.first.wait_for()
                project.first.wait_for()
                assert rows.count() == 2, rows.all_inner_texts()
                # The Meetings window is not what opened.
                assert page.locator(".desk-window-shell[aria-label='Meetings']").count() == 0
                _images_loaded(page)
                _settle(page)
                page.screenshot(path=str(SHOTS / f"04-parked-drawer-{width}.png"))

                # Restore the Project: the receipt, and the row leaves the drawer.
                project.first.click()
                window.get_by_test_id("parked-restore").click()
                receipt = window.get_by_test_id("parked-receipt")
                receipt.wait_for()
                assert receipt.inner_text().startswith("RESTORED"), receipt.inner_text()
                project.first.wait_for(state="detached")
                assert rows.count() == 1
                projects = _api(page, "GET", "/api/projects", token=TOKEN)["projects"]
                assert any(p["id"] == "p-hiring" for p in projects)
                page.screenshot(path=str(SHOTS / f"04-parked-restored-{width}.png"))
                assert not errors, errors
            finally:
                browser.close()


class TestCalendarDenied:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        self.mac = _Mac()
        self.mac.install(monkeypatch)
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("width", [1440, 393])
    def test_denied_has_a_way_forward(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page = _context(pw, width)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                denied = page.get_by_test_id("firstrun-calendar-denied")
                denied.wait_for()
                assert "CALENDAR · NOT ALLOWED" in denied.inner_text()
                settings = denied.get_by_role("button", name="Open System Settings")
                check = denied.get_by_role("button", name="Check again")
                assert settings.is_visible() and check.is_visible()
                denied.scroll_into_view_if_needed()
                _settle(page)
                page.screenshot(path=str(SHOTS / f"04-calendar-denied-{width}.png"))

                settings.click()
                for _ in range(40):
                    if self.mac.opens:
                        break
                    page.wait_for_timeout(100)
                assert self.mac.opens == 1
                assert denied.get_by_text("SETTINGS · NOT OPENED").count() == 0

                # He allows it in System Settings; Check again moves the card on.
                self.mac.state = "full_access"
                check.click()
                denied.wait_for(state="detached")
                assert not errors, errors
            finally:
                browser.close()
