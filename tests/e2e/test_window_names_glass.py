"""A window's title is the name of the thing in it -- fenced AS RENDERED.

Owner ratified 2026-10-04; Muad'Dib's ruling the same day: at 393 the clock
leaves the screen bar while a window is in front, and the window's name takes
its width. Before, the bar had no free width (393 px of parts) and a Project
Room read ``Pay…``.

Through the real hub on an isolated HOME and the built bundle (DeskChrome.tsx,
SurfaceWindows.tsx, windowName.ts): a project made by the real producer, its
Room opened from the palette, at 393 (touch) and at 1440 (the control).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, _room_through_drawer
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the window names glass needs Playwright")

TOKEN = "window-names-glass"
SHOTS = evidence_dir("tests/e2e/shots/window-names")
SIZES = {1440: 900, 393: 852}
PROJECT = "Payments ledger cutover"

# How much of the name the screen title paints: the characters that fit its
# box in its own font (the rest is the ellipsis).
NAME_FACTS = """() => {
  const e = document.querySelector('.desk-screen-name'); if (!e) return null;
  const cs = getComputedStyle(e); const text = e.textContent.trim();
  const c = document.createElement('canvas').getContext('2d'); c.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
  const box = e.clientWidth; let shown = text.length;
  if (c.measureText(text).width > box + 0.5) { shown = 0;
    for (let n = text.length - 1; n > 0; n--) if (c.measureText(text.slice(0, n) + '…').width <= box + 0.5) { shown = n; break; } }
  const clock = document.querySelector('.desk-clock');
  const mark = document.querySelector('.desk-screen-switcher-mark');
  const bar = document.querySelector('.desk-menubar').getBoundingClientRect();
  const r = e.getBoundingClientRect(); const m = mark ? mark.getBoundingClientRect() : null;
  return { text, box, shown, one_line: r.height < parseFloat(cs.fontSize) * 1.8, ellipsis: cs.textOverflow,
    clock: !!clock && clock.getBoundingClientRect().width > 0,
    mark_whole: m ? (m.width >= 5 && m.right <= bar.right + 0.5) : null,
    bar_overflow: document.documentElement.scrollWidth > innerWidth,
    front: [...document.querySelectorAll('.desk-window-shell.is-front')].map((w) => w.getAttribute('aria-label')) };
}"""


class TestWindowNamesOnGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    @pytest.mark.parametrize("width", [393, 1440])
    def test_the_project_room_is_named_by_its_project_and_393_shows_the_name(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                      device_scale_factor=1, has_touch=width < 720)
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                _api(page, "POST", "/api/projects", {"name": PROJECT}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(2500)
                _settle(page)

                # The Room, from the palette: `Open <project>`.
                self._press(page, page.locator("button[aria-controls=desk-tool-shelf]"), width)
                page.locator("input[aria-controls=desk-palette-listbox]").fill("Payments")
                row = page.get_by_role("option", name=f"Open {PROJECT}").first
                row.wait_for()
                self._press(page, row, width)
                _room_through_drawer(page, lambda loc: self._press(page, loc, width))
                room = page.locator("[id='surface-project-memory']")
                room.wait_for()
                page.wait_for_timeout(1200)
                _settle(page)

                # One name: the frame, and the screen title.
                assert room.get_attribute("aria-label") == PROJECT, room.get_attribute("aria-label")
                facts = page.evaluate(NAME_FACTS)
                SHOTS.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(SHOTS / f"project-room-{width}.png"))
                (SHOTS / f"project-room-{width}.txt").write_text(f"{facts}\n")
                assert facts["text"] == PROJECT, facts
                assert PROJECT in facts["front"], facts
                assert facts["one_line"] and facts["ellipsis"] == "ellipsis", facts
                assert not facts["bar_overflow"], facts
                if width < 720:
                    # The ruling: the clock is gone while a window is in front,
                    # and the name shows more than `Pay…` (it showed 3 letters).
                    assert not facts["clock"], facts
                    assert facts["shown"] >= 10, facts
                    assert facts["box"] >= 100, facts
                    assert facts["mark_whole"], facts   # the ▾ never truncates
                else:
                    assert facts["clock"], facts
                    assert facts["shown"] == len(PROJECT), facts
                assert errors == [], errors
            finally:
                browser.close()
