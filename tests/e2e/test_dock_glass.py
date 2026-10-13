"""The Dock app, AS RENDERED: what only a real browser proves of the Dock.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation. Through the real hub
on an isolated HOME:

* 393 (touch): the daily seats come first, whole, left of More AppIcons; a
  touch tap on More AppIcons moves the shelf one page.
* The hub stops and his "Refresh from hub" runs (the palette, at both widths):
  the outage receipt's Retry and OK each own the point at their centre, and
  the screen bar stays one line with the receipt in it.

The Dock's words have cheaper successors: READY, SENT, REC and OFFLINE in
web/src/desk/components/window/Dock.test.tsx, the outage receipt's words in
web/src/desk/__tests__/dock.app.test.tsx, the producers in
tests/unit/test_philo13_c3_dock.py and tests/unit/test_philo13_c3_ready.py.
Clip, overlap and fit of the Dock at 1440 and 393 are the desk sweep's
(tests/e2e/test_desk_sweep.py, the bare desk case and the pager waiver).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the Dock glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "dock-glass"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-13-shots")
SIZES = {1440: 900, 393: 852}
T = 20_000
DOCK = ".desk-dock"

OWNS_ITS_CENTRE = """(el) => { const r = el.getBoundingClientRect();
    const x = r.left + r.width / 2, y = r.top + r.height / 2;
    const hit = document.elementFromPoint(x, y);
    return { owned: !!hit && (hit === el || el.contains(hit)),
             hit: hit ? (hit.className || hit.tagName) + '' : null,
             in_viewport: x >= 0 && y >= 0 && x <= innerWidth && y <= innerHeight }; }"""

BAR_SPILL = """() => {
    const bar = document.querySelector('.desk-menubar').getBoundingClientRect();
    return [...document.querySelectorAll('.desk-menubar .desk-chrome-tr > *')]
      .map((e) => ({el: (e.getAttribute('aria-label') || e.textContent || e.className).trim().slice(0, 40),
                    r: e.getBoundingClientRect()}))
      .filter((x) => x.r.width > 0 && x.r.height > 0 && (x.r.top < bar.top - 0.5 || x.r.bottom > bar.bottom + 0.5))
      .map((x) => ({el: x.el, top: Math.round(x.r.top), bottom: Math.round(x.r.bottom), bar: Math.round(bar.bottom)}));
}"""


class TestDockGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        self.stopped = False
        try:
            yield
        finally:
            if not self.stopped:
                server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720,
                                  reduced_motion="reduce")
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.locator(DOCK).wait_for()
        page.wait_for_timeout(1200)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    def test_the_phone_shelf_seats_and_pages_by_touch(self) -> None:
        """replaces: tests/e2e/test_philo13_13_dock_glass.py::TestLiveDock::test_the_dock_shows_his_day_live_and_stays_through_an_outage
        (the 393 leg: the daily seats on the first page, More AppIcons pages the shelf)."""
        from playwright.sync_api import sync_playwright

        width = 393
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                seats = page.evaluate("""() => {
                    const d = document.querySelector('.desk-dock');
                    const more = d.querySelector('.desk-dock-more').getBoundingClientRect();
                    return [...d.querySelectorAll('.desk-dock-launch')]
                      .map((b) => ({ app: b.dataset.app || b.getAttribute('aria-label'), r: b.getBoundingClientRect() }))
                      .filter((x) => x.r.right <= more.left + 0.5 && x.r.left >= 0)
                      .sort((a, b) => a.r.left - b.r.left).map((x) => x.app);
                }""")
                # PHILO-17 (doors): People is a desk drawer now; Missed fits the first page.
                assert seats == ["intelligence:desk", "surface-meetings", "surface-dictation", "Missed"], seats
                before = page.evaluate("() => document.querySelector('.desk-dock').scrollLeft")
                self._press(page, page.get_by_role("button", name="More AppIcons"), width)
                page.wait_for_timeout(700)
                after = page.evaluate("() => document.querySelector('.desk-dock').scrollLeft")
                assert after > before, (before, after)
                page.screenshot(path=str(SHOTS / f"dock-02-more-{width}.png"))
                assert not [e for e in errors if "ResizeObserver" not in e], errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_outage_receipt_owns_its_verbs_and_the_bar_stays_one_line(self, width: int) -> None:
        """replaces: tests/e2e/test_philo13_13_dock_glass.py::TestLiveDock::test_the_dock_shows_his_day_live_and_stays_through_an_outage
        (the outage legs that are geometry: Retry and OK own their centres;
        PHILO-13-11 close, design §4: the screen bar does not wrap under the receipt)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                self.server.stop()
                self.stopped = True
                page.get_by_test_id("desk-dock-offline").wait_for(timeout=T)
                # An actual failed Desk refresh: his "Refresh from hub", from the palette.
                field = page.locator("[aria-controls=desk-palette-listbox]")
                if not field.is_visible():
                    self._press(page, page.locator("[aria-controls=desk-tool-shelf]"), width)
                field.fill("Refresh from hub")
                self._press(page, page.locator("[id='desk-palette-option-desk.refresh']"), width)
                receipt = page.locator(".write-receipt", has_text="READ MEETINGS FAILED · HUB UNREACHABLE").first
                receipt.wait_for(timeout=T)
                _settle(page)  # the phone window yields to the receipt row in a layout pass; measure after it
                for name in ("Retry", "OK"):
                    button = receipt.get_by_role("button", name=name, exact=True)
                    assert button.count() == 1, f"{name} is missing from the outage receipt"
                    owned = page.evaluate(OWNS_ITS_CENTRE, button.element_handle())
                    assert owned["in_viewport"] and owned["owned"], f"{name}: {owned}"
                spill = page.evaluate(BAR_SPILL)
                assert not spill, f"the screen bar wraps under the outage receipt: {spill}"
                page.screenshot(path=str(SHOTS / f"dock-08b-outage-receipt-{width}.png"))
                assert not [e for e in errors if "ResizeObserver" not in e], errors
            finally:
                browser.close()
