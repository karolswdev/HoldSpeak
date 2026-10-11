"""PHILO-17 (phonepass) -- two phone-width defects, fenced AS RENDERED.

Through the real hub on an isolated HOME (the canvas week of
test_philo13_06_open_glass._seed: Priya's 1:1 is linked, so the People
drawer wears its `1:1 HH:MM` caption).

1. Rows hold still under the finger (393, touch). The fence records every
   drawn row's box on each animation frame from the moment it is drawn,
   while the reads land: the ⌘K list after `Payments` is typed, and the
   Room on `Payments ledger cutover` after its row is tapped. A row above
   the fold never moves more than 2 px once drawn. CSS animations are off
   in the fence (the 4 px rise-in is motion, not layout).
2. The People caption touches nothing (1440 and 393): the People icon's
   box (with its caption) intersects no other icon and no count notch.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from .glass_infra import _room_opened, _settle
from .test_philo13_07_remembers_glass import SIZES, _Rig
from tests._evidence import evidence_dir

pytestmark = pytest.mark.chair_windows_open

SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-17/assets/phonepass-shots")
STILL = "*, *::before, *::after { animation: none !important; transition: none !important; }"
TOLERANCE = 2

# Each drawn row (visible, on screen) keyed by element identity; its first
# drawn y and the largest move after that.
RECORD_JS = r"""([sel, ms]) => { window.__rec = new Promise((resolve) => {
  const ids = new WeakMap(); let n = 0; const rows = {}; const t0 = performance.now();
  const H = window.innerHeight;
  const tick = () => {
    for (const el of document.querySelectorAll(sel)) {
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height || r.top >= H || r.bottom <= 0) continue;
      if (getComputedStyle(el).visibility !== 'visible') continue;
      if (!ids.has(el)) ids.set(el, ++n);
      const k = ids.get(el);
      const name = (el.getAttribute('data-testid') || el.id || (el.textContent || '').trim()).slice(0, 48);
      const y = Math.round(r.top);
      if (!rows[k]) rows[k] = {name, first: y, at: Math.round(performance.now() - t0), worst: 0, last: y};
      else { rows[k].last = y; rows[k].worst = Math.max(rows[k].worst, Math.abs(y - rows[k].first)); }
    }
    if (performance.now() - t0 < ms) requestAnimationFrame(tick); else resolve(Object.values(rows));
  };
  requestAnimationFrame(tick);
}); }"""
RESULT_JS = "() => window.__rec"

PALETTE_ROWS = "[id^=desk-palette-option-]"
ROOM_ROWS = ("#surface-project-memory .room-body button, #surface-project-memory .room-body li, "
             "#surface-project-memory .room-body [data-testid]")


class TestRowsHoldStill(_Rig):
    def test_palette_and_room_rows_do_not_move_under_the_finger_393(self) -> None:
        from playwright.sync_api import sync_playwright

        width = 393
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                page.add_style_tag(content=STILL)
                self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
                page.locator("[aria-controls=desk-palette-listbox]").wait_for()
                # His typing re-ranks the list (that is his own move); the
                # fence starts once the query is drawn, while its reads
                # (memory search, debounced 250 ms) are still in flight.
                page.locator("[aria-controls=desk-palette-listbox]").fill("Payments")
                page.evaluate(RECORD_JS, [PALETTE_ROWS, 2500])
                palette = page.evaluate(RESULT_JS)
                page.screenshot(path=str(SHOTS / "palette-393.png"))

                opt = page.locator("[id='desk-palette-option-project.open.p-ledger']")
                page.evaluate(RECORD_JS, [ROOM_ROWS, 3500])
                self._press(page, opt, width)
                _room_opened(page)
                room = page.evaluate(RESULT_JS)
                _settle(page)
                page.screenshot(path=str(SHOTS / "room-393.png"))

                proof = {"palette": palette, "room": room}
                (SHOTS / "rows-393.json").write_text(json.dumps(proof, indent=1) + "\n")
                moved = {where: [r for r in rows if r["worst"] > TOLERANCE] for where, rows in proof.items()}
                assert palette and room, proof
                assert any(r["name"] == "updates-verb" for r in room), "the Room drew no Draft update"
                assert not moved["palette"] and not moved["room"], moved
                assert not errors, errors
            finally:
                browser.close()


CAPTION_JS = r"""() => {
  const box = (el) => { const r = el.getBoundingClientRect(); return {x: r.left, y: r.top, w: r.width, h: r.height,
    name: el.getAttribute('data-object-id') || el.className}; };
  const people = document.querySelector(".desk-screen .desk-icon[data-object-id='drawer:people']");
  const others = [...document.querySelectorAll('.desk-screen .desk-icon')].filter((e) => e !== people);
  return {people: people && box(people),
          caption: box(document.querySelector("[data-testid='desk-icon-caption-drawer:people']")),
          others: others.map(box),
          notches: [...document.querySelectorAll('.desk-screen .desk-icon-count, .desk-screen .desk-icon-lamp')]
            .filter((e) => !people.contains(e)).map(box)};
}"""


def _meets(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"] and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"]


class TestCaptionTouchesNothing(_Rig):
    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_people_caption_overlaps_no_icon_or_notch(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                page.locator("[data-testid='desk-icon-caption-drawer:people']").wait_for(state="attached", timeout=20_000)
                page.wait_for_timeout(600)
                _settle(page)
                found = page.evaluate(CAPTION_JS)
                (SHOTS / f"caption-{width}.json").write_text(json.dumps(found, indent=1) + "\n")
                people = found["people"]
                # The shot only: the windows stand over the screen, so they are
                # hidden for it (the boxes above were read with them drawn).
                page.add_style_tag(content=".desk-window-shell, .desk-window, .desk-pullout, .desk-screen "
                                   "{ visibility: visible; } .desk-window-shell, .desk-window, .desk-pullout "
                                   "{ visibility: hidden !important; } .desk-screen { visibility: visible !important; }")
                if people:
                    x, y = max(0, people["x"] - 40), max(0, people["y"] - 130)
                    page.screenshot(path=str(SHOTS / f"caption-{width}.png"),
                                    clip={"x": x, "y": y, "width": min(320, width - x), "height": 400})
                assert people and found["caption"]["h"] > 0, found
                # the caption is inside the People icon's own box
                cap = found["caption"]
                assert cap["y"] + cap["h"] <= people["y"] + people["h"] + 0.5, found
                hits = [o for o in found["others"] + found["notches"] if _meets(people, o)]
                assert not hits, {"people": people, "touches": hits}
                assert not errors, errors
            finally:
                browser.close()
