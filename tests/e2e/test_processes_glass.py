"""Processes in a real browser: the name column at 393.

Kept by the test diet (push 2, 2026-10-12), one file for the Processes app:

* Astra, #869 iteration 2: at 393 the row's name column measured 3 px, so
  two decisions made in the same second looked the same. The RENDERED name
  (its box cut by every ancestor that hides overflow) shows at least its
  first word (an exact geometry relation; was the Processes leg of
  tests/e2e/test_finish_face_polish_glass.py).
"""
from __future__ import annotations

import pytest

from .finish_rig import SHOTS, TOKEN, FinishRig
from .glass_infra import _api, _settle

pytest.importorskip("playwright.sync_api", reason="the Processes glass needs Playwright")


class TestProcessNames(FinishRig):
    @pytest.mark.e2e
    def test_processes_names_two_same_second_decisions_visibly_at_393(self) -> None:
        """Astra, #869 iteration 2: at 393 the Processes row's name column
        measured 3 px, so two decisions made in the same second looked the
        same. The RENDERED name (its box cut by every ancestor that hides
        overflow) must show at least its first word."""
        from playwright.sync_api import sync_playwright

        visible = """() => [...document.querySelectorAll('[data-testid=process-target]')].map((el) => {
            let r = el.getBoundingClientRect(); let left = r.left, right = r.right;
            for (let a = el.parentElement; a; a = a.parentElement) {
              const cs = getComputedStyle(a);
              if (cs.overflowX !== 'visible' || cs.overflow !== 'visible') {
                const b = a.getBoundingClientRect(); left = Math.max(left, b.left); right = Math.min(right, b.right); }
            }
            const text = el.textContent.replace(/^\\s*·\\s*/, '');
            const cs = getComputedStyle(el);
            const c = document.createElement('canvas').getContext('2d');
            c.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
            return {text, shown: Math.round(Math.max(0, right - left)), firstWord: Math.ceil(c.measureText('· ' + text.split(' ')[0]).width)};
          })"""
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 393, builder_tools=True)
            try:
                for title in ("Freeze the old ledger on Nov 5", "Adopt OpenTelemetry"):
                    _api(page, "POST", "/api/decisions", {"title": title, "status": "proposed"}, token=TOKEN)
                page.wait_for_timeout(1500)
                self._palette(page, "processes")
                self._press(page, page.locator("[id^='desk-palette-option-']", has_text="Processes").first, 393)
                page.locator("[data-testid=process-target]").nth(1).wait_for(timeout=30_000)
                _settle(page)
                page.screenshot(path=str(SHOTS / "processes-two-decisions-393.png"))
                names = page.evaluate(visible)
                assert sorted(n["text"] for n in names) == ["Adopt OpenTelemetry", "Freeze the old ledger on Nov 5"], names
                for n in names:
                    assert n["shown"] >= n["firstWord"], f"the name is not readable on the glass: {n}"
                assert not errors, errors
            finally:
                browser.close()
