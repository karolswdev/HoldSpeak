"""The Roadmap window in a real browser: its story rows never draw one part
over another.

Kept by the test diet (push 2, 2026-10-12), one file for the Roadmap app:

* the palette's Roadmap row opens the roadmap by its name with its phases,
  and no story row draws one of its parts over another (the IN PROGRESS
  chip sat over its title when the row had no evidence mark): an exact
  geometry relation, at 1440 and 393. Was the Roadmap leg of
  tests/e2e/test_finish_face_polish_glass.py; the ref it opens by is
  web/src/desk/__tests__/roadmapRef.test.ts.
"""
from __future__ import annotations

import pytest

from .finish_rig import SHOTS, SIZES, FinishRig
from .glass_infra import _settle

pytest.importorskip("playwright.sync_api", reason="the Roadmap glass needs Playwright")

# Every story row whose visible parts cross one another.
OVERLAPS_JS = """() => [...document.querySelectorAll('.desk-roadmap-stories li')].filter((li) => {
    const parts = [...li.children].filter((k) => getComputedStyle(k).display !== 'none').map((k) => k.getBoundingClientRect());
    return parts.some((a, i) => parts.some((b, j) => j > i && a.left < b.right - 0.5 && b.left < a.right - 0.5));
  }).map((li) => li.textContent.slice(0, 48))"""


class TestRoadmapRows(FinishRig):
    @pytest.mark.e2e
    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_roadmap_opens_by_name_and_no_row_part_overlaps(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                self._palette(page, "HoldSpeak Roadmap")
                roadmap = page.locator("[id^='desk-palette-option-roadmap:']").first
                roadmap.wait_for()
                self._press(page, roadmap, width)
                window = page.locator(".desk-roadmap-window")
                window.wait_for()
                window.locator(".desk-roadmap-phases").wait_for(timeout=20_000)
                _settle(page)
                page.screenshot(path=str(SHOTS / f"roadmap-{width}.png"))
                text = window.inner_text()
                assert "Roadmap not found" not in text and "roadmap:" not in text, text[:300]
                assert not page.evaluate(OVERLAPS_JS), page.evaluate(OVERLAPS_JS)
                assert page.locator(".desk-screen-name").inner_text().strip().startswith("HoldSpeak"), \
                    page.locator(".desk-screen-name").inner_text()
                assert not errors, errors
            finally:
                browser.close()
