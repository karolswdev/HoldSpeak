"""The Today app, AS RENDERED: what only a real browser proves of Today.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation.

* PHILO-15 lane 12, B24 (Astra r1): the Today window opens AT its declared
  size, rendered, with its Since-yesterday line in view (Betterment D4: one
  page, no wings); a size he sets with the grip wins on the next open, after
  a reload (1440).

The rest of that after-shot walk has cheaper successors: the Dock sprites
(B19) in web/src/desk/systemSprites.test.ts; the desk labels (B30) in
web/src/desk/__tests__/philo15Ugly.test.tsx:106-146 and the desk sweep's
`clipped` fence on the bare desk; the empty Project's NEW (B25) in
philo15Ugly.test.tsx:72-90.
"""
from __future__ import annotations

import re

import pytest

from .fit_rig import BOX_JS, T, TOKEN, FitRig
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
                # Betterment D4: one page, no wings. Since yesterday (the
                # brief, made on open) is its folded line.
                first = win.get_by_test_id("today-since-toggle")
                first.wait_for(timeout=T)
                page.wait_for_timeout(900)
                _settle(page)
                box = win.evaluate(BOX_JS)
                item = first.evaluate(BOX_JS)
                assert win.get_by_role("group", name="Intelligence view", exact=True).count() == 0, "no wings"
                self.facts["B24"] = {"window": box, "first_item": item}
                assert box["w"] >= 600, box
                assert box["h"] >= 600, box                    # the declared 620, rendered
                first.scroll_into_view_if_needed()
                item = first.evaluate(BOX_JS)
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


# ── PHILO-17 Today on the sweep's seeded desk (its own hub): Today opens from
#    the Dock between the desk's icon columns and covers no icon of either.
#    Moved from test_philo17_today_glass.py (push 2 of the test diet, lane
#    e2e-low-2); its presses are TodayView.test.tsx. ──

from typing import Any  # noqa: E402

from tests._evidence import evidence_dir  # noqa: E402

from .glass_infra import clear_hub_windows_http  # noqa: E402
from .test_desk_sweep import SETTLED_JS, T as SWEEP_T, TOKEN as SWEEP_TOKEN, _page, desk, pw_browser  # noqa: E402,F401

TODAY = '[id="pullout:intelligence:desk"]'


def _open_today(pw_browser: Any, base: str, width: int) -> tuple[Any, Any]:
    clear_hub_windows_http(base, SWEEP_TOKEN)
    ctx, page, _errors, _requests = _page(pw_browser, width, base)
    page.goto(f"{base}/?token={SWEEP_TOKEN}", wait_until="load")
    _normal_chair(page)
    page.wait_for_function(SETTLED_JS, arg=None, timeout=SWEEP_T)
    page.locator(".desk-dock-launch[aria-label^='Today']").first.click()
    page.locator(f"{TODAY} [data-testid=today-day]").wait_for(timeout=SWEEP_T)
    return ctx, page


@pytest.mark.timeout(240)
def test_today_opens_between_the_icon_columns(desk: dict[str, Any], pw_browser: Any) -> None:
    ctx, page = _open_today(pw_browser, desk["base"], 1440)
    try:
        page.wait_for_function(SETTLED_JS, arg="pullout:intelligence:desk", timeout=SWEEP_T)
        box = page.locator(TODAY).bounding_box()
        assert box, "Today is not drawn"
        icons = page.evaluate("""() => [...document.querySelectorAll('.desk-icon')]
          .filter((e) => !e.closest('.desk-window, .desk-dock'))
          .map((e) => { const r = e.getBoundingClientRect();
            return {name: (e.textContent || '').trim().slice(0, 30), left: r.left, right: r.right, top: r.top, bottom: r.bottom,
                    placed: Boolean(e.closest('.desk-screen-placed'))}; })
          .filter((r) => r.right > r.left)""")
        columns = [i for i in icons if i["right"] <= 160 or (i["placed"] and i["left"] >= 1440 * 0.75)]
        assert any(i["left"] >= 1440 * 0.75 for i in columns), icons
        covered = [i["name"] for i in columns
                   if i["left"] < box["x"] + box["width"] and i["right"] > box["x"]
                   and i["top"] < box["y"] + box["height"] and i["bottom"] > box["y"]]
        assert not covered, (box, covered)
        page.screenshot(path=str(evidence_dir("today") / "today-seat-1440.png"))
    finally:
        ctx.close()
