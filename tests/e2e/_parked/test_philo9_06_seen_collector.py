"""PHILO-9-06 (Codex Astra r1 on #687): the closing run's face collector
counts a row only when it is SEEN in the unobscured viewport.

The first collector accepted any element with a positive height, so the
393 ITEMS shot "showed" a risk row that was below the fold. Red with a
height-only collector, green with ``seen``: a row off-screen and a row under
a floating overlay (the Ask well's place) are not seen; a row in view is.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("philo9_room_job", REPO / "scripts/philo9_room_job.py")
assert SPEC and SPEC.loader
driver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(driver)

PAGE = """<div class="desk-window" style="position:absolute;top:0;left:0;width:393px;height:852px;overflow:auto">
  <div data-testid="room-body">
    <div data-testid="item-row" style="position:absolute;top:100px;height:40px;width:300px">Cutover rehearsal</div>
    <div data-testid="item-row" style="position:absolute;top:700px;height:40px;width:300px">Covered risk</div>
    <div data-testid="item-row" style="position:absolute;top:2000px;height:40px;width:300px">Old ledger freeze slips</div>
  </div>
</div>
<div style="position:fixed;top:680px;left:0;width:393px;height:120px;background:#000">the Ask well</div>"""


@pytest.mark.e2e
def test_only_rows_seen_in_the_unobscured_viewport_count() -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as play:
        browser = play.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 393, "height": 852})
            page.set_content(PAGE)
            facts = page.evaluate(driver.ROOM_FACTS)
        finally:
            browser.close()
    assert facts["item_rows"] == ["Cutover rehearsal"], facts["item_rows"]
    assert [row[2] for row in facts["item_all"]] == [True, False, False], facts["item_all"]
