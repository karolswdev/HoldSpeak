"""The Today app, AS RENDERED: what only a real browser proves of Today.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation.

* PHILO-15 lane 12, B24 (Astra r1): the Today window (the Intelligence
  window) opens AT its declared size, rendered, with its first Brief items in
  view and its segments on one row; a size he sets with the grip wins on the
  next open, after a reload (1440).

The rest of that after-shot walk has cheaper successors: the Dock sprites
(B19) in web/src/desk/systemSprites.test.ts; the desk labels (B30) in
web/src/desk/__tests__/philo15Ugly.test.tsx:106-146 and the desk sweep's
`clipped` fence on the bare desk; the empty Project's NEW (B25) in
philo15Ugly.test.tsx:72-90.
"""
from __future__ import annotations

import re

import pytest

from .fit_rig import BOX_JS, ITEM, T, TOKEN, FitRig
from .glass_infra import _api, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="the Today glass needs Playwright")

pytestmark = [pytest.mark.e2e]


class TestTheTodayWindowSize(FitRig):
    def test_today_opens_at_its_size_and_keeps_the_size_he_sets(self) -> None:
        """replaces: tests/e2e/test_philo15_12_ugly_glass.py::TestPhilo15Lane12Ugly::test_after_shots_dock_intelligence_project_label
        (the B24 leg, 1440)."""
        from playwright.sync_api import sync_playwright

        width = 1440
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                self._seed_meeting()
                _api(page, "POST", "/api/brief/generate", {}, token=TOKEN)   # Today opens with items
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1200)
                _settle(page)
                dock = page.locator(".desk-dock").first
                dock.locator("[data-app='intelligence:desk']").click()
                win = page.locator(".desk-pullout:has(.intelligence-pullout)").first
                win.wait_for(timeout=T)
                # PHILO-17 (concept C): the window opens on Day; its first
                # items here are the Brief's, one tab away.
                win.locator(".intelligence-segment", has_text="Brief").first.click()
                first = win.locator(ITEM).first
                first.wait_for(timeout=T)
                page.wait_for_timeout(900)
                _settle(page)
                box = win.evaluate(BOX_JS)
                item = first.evaluate(BOX_JS)
                tops = win.locator(".intelligence-segment").evaluate_all(
                    "(es) => es.map((e) => Math.round(e.getBoundingClientRect().top))")
                self.facts["B24"] = {"window": box, "first_item": item, "segment_tops": tops}
                assert box["w"] >= 600, box
                assert box["h"] >= 600, box                    # the declared 620, rendered
                assert len(set(tops)) <= 1, tops
                assert item["btm"] <= box["btm"] and item["y"] >= box["y"], (item, box)
                self._shot(page, "B24-intelligence", width)
                # He sizes it smaller; the saved size wins on the next open.
                grip = win.locator(".desk-window-grip").first
                g = grip.evaluate(BOX_JS)
                page.mouse.move(g["x"] + g["w"] / 2, g["y"] + g["h"] / 2)
                page.mouse.down()
                page.mouse.move(g["x"] + g["w"] / 2 - 120, g["y"] + g["h"] / 2 - 160, steps=8)
                page.mouse.up()
                page.wait_for_timeout(500)
                saved = win.evaluate(BOX_JS)
                assert saved["w"] < box["w"] - 60 and saved["h"] < box["h"] - 60, (saved, box)
                win.get_by_role("button", name=re.compile(r"^Close ")).first.click()
                win.wait_for(state="detached", timeout=T)
                page.reload(wait_until="load")
                _normal_chair(page)
                page.locator(".desk-dock [data-app='intelligence:desk']").click()
                again = page.locator(".desk-pullout:has(.intelligence-pullout)").first
                again.wait_for(timeout=T)
                page.wait_for_timeout(900)
                reopened = again.evaluate(BOX_JS)
                self.facts["B24"]["saved"], self.facts["B24"]["reopened"] = saved, reopened
                assert abs(reopened["w"] - saved["w"]) <= 2 and abs(reopened["h"] - saved["h"]) <= 2, (reopened, saved)
                self._shot(page, "B24-intelligence-saved-size", width)
                self._write("today", width)
                assert not errors, errors
            finally:
                browser.close()
