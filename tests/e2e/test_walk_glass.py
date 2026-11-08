"""The Walk, AS RENDERED: the highlighted part takes the pointer.

The first walk on the owner's desk (2026-11-07, "totally doesn't work"): the
ring marked New program, but a press on it went to the dim backdrop (a
clip-path cut-out Chromium's hit test did not honour). Only a real browser
proves the hit test, so this is T4: a walk made through the hub
(``POST /api/walks``) marks ``programs-new``; the part takes the pointer two
frames after its window moves (the cut-out lagged it by its 180 ms
transition: the press Playwright retried went to the dim); a plain press (no
force) on it opens the well (the project rows show); and a point far from
the part is the dim's. At 1440 x 900 and 393 x 844. Every other face of the walk is T2
(``web/src/desk/walk/__tests__/walk.app.test.tsx``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair

pytest.importorskip("playwright.sync_api", reason="the walk glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "walk-glass"
T = 20_000

# The first point (of a few far ones) outside the marked part and the card,
# and the element the browser hits there.
_FAR_HIT_JS = """
() => {
  const pad = 12;
  const part = document.querySelector('[data-testid="walk-ring"]').getBoundingClientRect();
  const card = document.querySelector('[data-testid="walk-card"]').getBoundingClientRect();
  const inside = (box, x, y) => x >= box.left - pad && x <= box.right + pad && y >= box.top - pad && y <= box.bottom + pad;
  const w = window.innerWidth, h = window.innerHeight;
  const points = [[w - 20, 20], [20, h - 20], [w - 20, h - 20], [20, 20], [w / 2, h / 2], [w / 2, 20]];
  for (const [x, y] of points) {
    if (inside(part, x, y) || inside(card, x, y)) continue;
    const hit = document.elementFromPoint(x, y);
    return { x, y, testid: hit && hit.getAttribute('data-testid'), cls: hit && hit.className };
  }
  return null;
}
"""

# Move the part's window, wait two frames (what Playwright waits for a
# stable box), and name what the browser hits at the part's centre.
_HIT_AFTER_MOVE_JS = """
async () => {
  const part = document.querySelector('[data-testid="programs-new"]');
  const win = part.closest("[data-layer='window']");
  const frames = () => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)));
  const hit = () => {
    const box = part.getBoundingClientRect();
    const element = document.elementFromPoint(box.left + box.width / 2, box.top + box.height / 2);
    return element && (element.closest('[data-testid="programs-new"]') ? "programs-new" : element.getAttribute("data-testid"));
  };
  win.style.translate = "-60px 40px";
  await frames();
  const moved = hit();
  win.style.translate = "";
  await frames();
  return { moved, back: hit() };
}
"""


@pytest.mark.parametrize("size", [(1440, 900), (393, 844)], ids=["1440", "393"])
def test_the_highlighted_part_takes_a_plain_press_and_the_dim_blocks_the_rest(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, size: tuple[int, int]) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    width, height = size
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1)
            page = ctx.new_page()
            page.set_default_timeout(45_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                # The well lists his projects: one is enough.
                _api(page, "POST", "/api/projects", {"name": "Walk glass"}, token=TOKEN)
                made: dict[str, Any] = _api(page, "POST", "/api/walks", {"title": "The press", "steps": [
                    {"open": {"app": "surface-programs"}},
                    {"highlight": {"target": "programs-new", "words": "Press New program. The well opens."}},
                ]}, token=TOKEN)
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                page.goto(f"{base}{made['url_path']}", wait_until="load")

                page.get_by_test_id("walk-ring").wait_for(timeout=T)
                target = page.locator('[data-testid="programs-new"]')
                assert page.evaluate(_HIT_AFTER_MOVE_JS) == {"moved": "programs-new", "back": "programs-new"}
                # A plain press: Playwright refuses it when another element
                # would take the pointer at the part's centre.
                target.click(timeout=10_000)
                page.locator('[data-testid="programs-make-rows"]').wait_for(state="visible", timeout=T)

                far = page.evaluate(_FAR_HIT_JS)
                assert far is not None, "no point outside the part and the card"
                assert str(far["testid"] or "").startswith("walk-backdrop"), far
                assert errors == [], errors
            finally:
                ctx.close()
                browser.close()
    finally:
        server.stop()
