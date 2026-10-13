"""The menus and doors of the desk, AS RENDERED: what only a real browser proves.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation. Through ONE real hub
on an isolated HOME and the built bundle, with three projects:

* 393 (touch): the whole Go menu is on one phone screen (no scroll to its
  end) (PHILO-15 11, B21).
* D6: a Room opens from Go, falls to its own Dock tile (Iconify at 1440; a
  Chair window taking the work area at 393), the tile names it, and a press
  on the tile brings it back. (T2 owed: it needs the whole desk rendered over
  recorded answers; until then it stays here.)
* D7 (393, Astra r2): Go ▸ Ask AI, Go ▸ Capture, Go ▸ Ask AI shows Ask again.
  (T2 owed, as D6.)

The rest of PHILO-17 doors and PHILO-15 11 have cheaper successors: the Go,
Tools and HoldSpeak menu rows in web/src/desk/components/DeskMenuBar.test.tsx
and web/src/desk/__tests__/menus.app.test.tsx; the phone Go and New in
web/src/desk/components/window/phoneRing.test.tsx:191-206; no keycap on a
phone in web/src/desk/__tests__/phoneKeycaps.philo1511.test.tsx; the Dock's
seats in web/src/desk/components/window/Dock.test.tsx:130; the next 1:1 on the
People drawer in web/src/desk/screen/__tests__/nextOneOnOne.test.tsx; every
application drawn loaded, and fit, in the desk sweep.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the menus glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "menus-glass"
SHOTS = evidence_dir("docs/internal/philo/phase-17/doors-shots")
SIZES = {1440: 900, 393: 852}
T = 30_000
PROJECTS = ["Ledger cutover", "Platform observability", "Hiring loop"]

# Is this Dock control fully on the shelf's visible page (left of More)?
ON_SHELF_JS = r"""(el) => {
  const d = el.closest('.desk-dock'); const more = d.querySelector('.desk-dock-more');
  const r = el.getBoundingClientRect(), b = d.getBoundingClientRect();
  const edge = more && getComputedStyle(more).display !== 'none' ? more.getBoundingClientRect().left : b.right;
  return r.width > 0 && r.left >= b.left - 0.5 && r.right <= edge + 0.5;
}"""


def _press(page: Any, target: Any) -> None:
    """A real gesture: a finger tap on a phone page, a mouse click on a desk."""
    if (page.viewport_size or {}).get("width", 1440) < 720:
        target.tap()
    else:
        target.click()


def _press_dock(page: Any, selector: str) -> None:
    """Press a Dock control as the phone does: page the shelf with More
    (a real tap) until the control is on the visible page, then tap it."""
    target = page.locator(selector).first
    for _ in range(6):
        if target.evaluate(ON_SHELF_JS):
            _press(page, target)
            return
        _press(page, page.locator(".desk-dock .desk-dock-more"))
        page.wait_for_timeout(450)
    raise AssertionError(f"{selector} never came onto the Dock's visible page")


def _row(page: Any, label: str) -> Any:
    """The menu row whose label is `label` (its name also carries a keycap)."""
    return page.locator("[role^=menuitem]").filter(
        has=page.locator(".desk-menu-label", has_text=re.compile(f"^{re.escape(label)}$"))).last


class _MenusRig:
    names: list[str] = PROJECTS

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        from holdspeak.db import get_database

        for i, name in enumerate(self.names):
            get_database().projects.create_project(project_id=f"p-door-{i}", name=name, description="", keywords=[])
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                  has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(T)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        self._fresh(page)
        return browser, page, errors

    @staticmethod
    def _fresh(page: Any) -> None:
        clear_hub_windows(page, TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        _settle(page)

    def _go_row(self, page: Any, *path: str) -> Callable[[], None]:
        def run() -> None:
            _press(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"))
            page.locator(".desk-menu-list").first.wait_for()
            for label in path:
                _press(page, _row(page, label))
        return run

class TestGoFitsAPhone(_MenusRig):
    # PHILO-15 11 measured Go with one project.
    names = PROJECTS[:1]

    def test_go_fits_a_phone_393(self) -> None:
        """replaces: tests/e2e/test_philo15_11_phone_menus_glass.py::TestThePhoneMenus::test_go_and_new_fit_a_phone_393
        (the fit leg; the rows are vitest's)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 393)
            try:
                _press(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"))
                page.locator(".desk-verbbar-menu").first.wait_for()
                page.wait_for_timeout(500)
                fits = page.evaluate("""() => { const m = document.querySelector('.desk-verbbar-menu');
                  return !!m && m.scrollHeight <= m.clientHeight + 1; }""")
                page.screenshot(path=str(SHOTS / "393-go-fits.png"))
                assert fits, "Go does not fit the phone screen"
                assert errors == [], errors
            finally:
                browser.close()


class TestDoors(_MenusRig):
    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_room_falls_to_its_dock_tile_and_comes_back(self, width: int) -> None:
        """replaces: tests/e2e/test_philo17_doors_glass.py::TestDoors::test_one_door_per_application (D6)."""
        from playwright.sync_api import sync_playwright

        room = PROJECTS[0]
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                phone = width < 720
                (self._go_row(page, room) if phone else self._go_row(page, "Projects", room))()
                page.locator(f".desk-window-shell[aria-label='{room}']").wait_for(timeout=T)
                if phone:
                    # The phone's own way: a Chair window takes the work area and
                    # the window in front falls to its Dock tile (393 has no
                    # Iconify gadget).
                    self._go_row(page, "Needs you")()
                    page.locator(".desk-window-shell[aria-label='Needs you']").wait_for(timeout=T)
                else:
                    _press(page, page.locator(f"[aria-label='Iconify {room}']").first)
                seat = page.locator(".desk-dock [data-seat='surface-project-memory']")
                seat.wait_for(timeout=T)
                assert (seat.get_attribute("aria-label") or "").startswith(room), seat.get_attribute("aria-label")
                page.screenshot(path=str(SHOTS / f"{width}-room-seated.png"))
                _press_dock(page, ".desk-dock [data-seat='surface-project-memory']")
                page.locator("#surface-project-memory").wait_for(state="visible", timeout=T)
                page.locator(".desk-dock [data-seat='surface-project-memory']").wait_for(state="detached", timeout=T)
                assert errors == [], errors
            finally:
                browser.close()

    def test_ask_ai_comes_back_after_capture_393(self) -> None:
        """replaces: tests/e2e/test_philo17_doors_glass.py::TestDoors::test_one_door_per_application (D7, Astra r2)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 393)
            try:
                ask = page.locator(".desk-ask")
                self._go_row(page, "Ask AI")()
                ask.wait_for(state="visible", timeout=T)
                self._go_row(page, "Capture")()
                page.locator(".desk-window-shell[aria-label='Capture']").wait_for(state="visible", timeout=T)
                ask.wait_for(state="hidden", timeout=T)
                self._go_row(page, "Ask AI")()
                ask.wait_for(state="visible", timeout=T)
                page.locator(".desk-ask textarea, .desk-ask [role=textbox]").first.wait_for(state="visible", timeout=T)
                page.screenshot(path=str(SHOTS / "393-ask-back.png"))
                assert errors == [], errors
            finally:
                browser.close()
