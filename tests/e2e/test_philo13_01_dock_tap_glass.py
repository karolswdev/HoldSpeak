"""PHILO-13-01 (B0) -- a tap on the 393 Dock presses the icon under the finger.

Through the real hub on an isolated HOME at 393x852 with touch. The Dock
shelf scrolls inside itself and snaps to whole icons. Its sticky More gadget
carried ``scroll-snap-align: start``; a sticky snap target moves with the
shelf, so the end of every tap gesture re-snapped the shelf one page on and
the tap pressed the icon a page further. The owner's tap on Floor pressed
Hide the menus, and Search was gone (B0 Zone, Chain and Coder at 393).

The fence pages the shelf the three ways a person does (More, a native
swipe, and the browser bringing the icon into view), then taps Floor with a
native touch. The Floor must open; the menus must stay.
"""
from __future__ import annotations

from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="the Dock tap glass needs Playwright")

TOKEN = "philo13-01-dock-tap"
FLOOR = '[data-testid="chair-floor-toggle"]'
PRESSES_JS = """() => { window.__presses = [];
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('button');
    window.__presses.push(b ? (b.getAttribute('aria-label') || b.textContent.trim()) : null);
  }, true); }"""


class TestDockTap393:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Any, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("paging", ["more", "swipe", "into-view"])
    def test_a_tap_on_a_paged_dock_presses_that_icon_393(self, paging: str) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 393, "height": 852},
                                      device_scale_factor=1, has_touch=True)
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                _settle(page)
                floor = page.locator(FLOOR)
                floor.wait_for(state="attached")
                box = floor.bounding_box()
                assert box and box["x"] + box["width"] > 393, (
                    "the fence needs Floor past the first page of the shelf", box)
                if paging == "more":
                    page.get_by_test_id("desk-dock-more").tap()
                elif paging == "swipe":
                    cdp = ctx.new_cdp_session(page)
                    cdp.send("Input.synthesizeScrollGesture", {
                        "x": 300, "y": 824, "xDistance": -341, "yDistance": 0,
                        "gestureSourceType": "touch", "speed": 800})
                    cdp.detach()
                else:
                    floor.scroll_into_view_if_needed()
                page.wait_for_timeout(1200)
                page.evaluate(PRESSES_JS)
                box = floor.bounding_box()
                assert box and 0 <= box["x"] and box["x"] + box["width"] <= 393 - 48, (
                    "Floor is not on the paged shelf", paging, box)
                page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                page.wait_for_timeout(600)
                presses = page.evaluate("() => window.__presses")
                settled = page.evaluate(
                    "() => document.querySelector('.desk-next').getAttribute('data-settled')")
                assert presses == ["Floor"], (paging, presses)
                assert settled != "true", (paging, "the tap hid the menus")
                assert page.locator(".desk-tools-launch").first.is_visible(), (
                    paging, "Search is hidden after the Floor tap")
            finally:
                browser.close()
