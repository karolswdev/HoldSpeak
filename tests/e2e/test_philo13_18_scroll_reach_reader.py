"""PHILO-13-18 (C8) -- the on-glass reader exempts only REACHABLE scrolled text.

Astra's counsel on #743: the on-glass reader exempted every vertical
overflow inside an auto/scroll box, so a word shifted above a 20 px
scroller's top (scrollHeight == clientHeight, never scrollable into view)
read as zero faults. These fixtures keep that mutation as a permanent fence:
the unreachable word must be REPORTED clipped, and ordinary scrolled text
below the fold must stay exempt. No hub: a real Chromium on static glass.
"""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api", reason="the reader fence needs Playwright")

from .glass_infra import _rendered_text_faults  # noqa: E402

FIXTURE = """<!doctype html><html><head><style>
  body { margin: 0; font: 13px sans-serif; }
  .box { width: 200px; height: 20px; overflow: auto; line-height: 20px; }
  .up { position: relative; top: -18px; display: block; }
</style></head><body>
  <div class="scope" id="unreachable"><div class="box"><span class="up">Unreachable</span></div></div>
  <div class="scope" id="scrolls"><div class="box"><div>Row one</div><div>Row two</div><div>Row three</div></div></div>
</body></html>"""


def _clipped(selector: str) -> list[str]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 393, "height": 852})
            page.set_content(FIXTURE)
            faults = _rendered_text_faults(page, selector, on_glass=True)
        finally:
            browser.close()
    return [c["text"] for c in faults["clipped"]]


def test_unreachable_text_in_a_scroller_is_reported() -> None:
    assert "Unreachable" in _clipped("#unreachable"), "a word above the scroll range passed the on-glass reader"


def test_text_below_the_fold_of_a_scroller_stays_exempt() -> None:
    assert _clipped("#scrolls") == [], "ordinary scrolled rows were reported clipped"
