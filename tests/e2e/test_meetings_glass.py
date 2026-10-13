"""The Meetings app, AS RENDERED: what only a real browser proves of a meeting.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation.

* PHILO-15 lane 12, B22: the meeting record uses the window body's whole
  width (no rail column beside it), at 1440 (also zoomed) and 393.
"""
from __future__ import annotations

from typing import Any

import pytest

from .fit_rig import BOX_JS, T, WIDTHS, FitRig, TITLE
from .glass_infra import _settle

pytest.importorskip("playwright.sync_api", reason="the Meetings glass needs Playwright")

pytestmark = [pytest.mark.e2e]


class TestTheMeetingRecord(FitRig):
    """replaces: tests/e2e/test_philo15_12_ugly_glass.py::TestPhilo15Lane12Ugly::test_the_record_uses_the_window_width (moved whole)."""

    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_record_uses_the_window_width(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                self._seed_meeting()
                # PHILO-17 ("A meeting opens in one window"): the record is the
                # meeting's own window; it takes the window body's whole width.
                self._stage(page, "review-meetings", "meeting:p15-12-m")
                win = page.locator("[id='pullout:meeting:p15-12-m']")
                detail = win.locator(".desk-surface-body > .surface-section").first
                detail.locator(".surface-display").first.wait_for(timeout=T)
                page.wait_for_timeout(800)
                _settle(page)

                def measure(tag: str) -> dict[str, Any]:
                    body = win.locator(".desk-surface-body").first.evaluate(
                        "(e) => { const st = getComputedStyle(e); const b = e.getBoundingClientRect();"
                        " return {x: b.left, w: e.clientWidth - parseFloat(st.paddingLeft) - parseFloat(st.paddingRight)}; }")
                    d = detail.evaluate(BOX_JS)
                    facts = {"body": body, "detail": d}
                    self.facts[f"B22_{tag}"] = facts
                    # The record takes the window body's whole width; no rail
                    # column beside it (the list is its own window now).
                    assert d["w"] >= body["w"] - 2, facts
                    assert win.locator(".surface-split-main").count() == 0, facts
                    return facts

                measure("normal")
                self._shot(page, "B22-record", width, win)
                if width > 720:
                    win.get_by_role("button", name=f"Zoom {TITLE}").click()
                    page.wait_for_timeout(700)
                    _settle(page)
                    page.mouse.wheel(0, 600)
                    page.wait_for_timeout(400)
                    measure("zoomed")
                    self._shot(page, "B22-record-zoomed", width)
                self._write("record", width)
                assert not errors, errors
            finally:
                browser.close()
