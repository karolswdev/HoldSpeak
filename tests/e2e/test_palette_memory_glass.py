"""Inventory gap 9 (2026-10-03) -- the palette finds a word inside a meeting, AS RENDERED.

Through the real hub on an isolated HOME, at 1440x900 (mouse) and 393x852
(touch). A meeting is saved by the real producer (``db.meetings.save_meeting``)
with one word, ``quokka``, that exists only inside its transcript: not in a
title, a speaker or a note. He types the word in the palette: the MEMORY band
shows the meeting (real ``/api/memory/search``), the row is on screen and
inside the shelf, and the press opens the meeting.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the palette glass needs Playwright")

TOKEN = "palette-memory"
SHOTS = evidence_dir("palette-memory-shots")
SIZES = {1440: 900, 393: 852}
WORD = "quokka"
TITLE = "Ledger cutover sync"
ROW = "[id='desk-palette-option-memory:meeting:m-sync']"


class TestPaletteFindsAWordInsideAMeeting:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        from holdspeak.db import get_database
        from holdspeak.meeting_session.models import MeetingState, TranscriptSegment

        start = datetime.now().replace(microsecond=0) - timedelta(hours=3)
        db = get_database()
        db.meetings.save_meeting(MeetingState(
            id="m-sync", started_at=start, ended_at=start + timedelta(minutes=45), title=TITLE,
            segments=[
                TranscriptSegment(text="Two write paths still hit the old ledger.", speaker="Me",
                                  start_time=4.0, end_time=9.0),
                TranscriptSegment(text=f"The {WORD} invoice batch is late again.", speaker="Priya",
                                  start_time=10.0, end_time=16.0),
            ]))
        db.meetings.save_meeting(MeetingState(
            id="m-other", started_at=start - timedelta(days=1), ended_at=start - timedelta(days=1, minutes=-30),
            title="Hiring review",
            segments=[TranscriptSegment(text="We open one more role.", speaker="Me", start_time=1.0, end_time=3.0)]))
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
            loc.click(timeout=8_000)

    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_transcript_word_finds_its_meeting_and_the_row_opens_it(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                      device_scale_factor=1, has_touch=width < 720)
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            searches: list[str] = []
            page.on("request", lambda r: searches.append(r.url) if "/api/memory/search" in r.url else None)
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1500)
                _settle(page)

                self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
                box = page.locator("[aria-controls=desk-palette-listbox]")

                # A short query reads nothing and shows no MEMORY band.
                box.fill(WORD[:2])
                page.wait_for_timeout(700)
                assert searches == [], searches
                assert page.locator(".desk-deck-band", has_text="MEMORY").count() == 0

                box.fill(WORD)
                row = page.locator(ROW)
                row.wait_for(timeout=8_000)
                assert len(searches) == 1, searches   # one debounced read
                bands = page.locator(".desk-deck-band").all_inner_texts()
                assert bands[-1] == "MEMORY", bands
                # The word is in no title: no local row names the meeting.
                options = page.locator("#desk-palette-listbox [role=option]").all_inner_texts()
                assert sum(TITLE in o for o in options) == 1, options
                text = row.inner_text()
                assert TITLE in text and WORD in text and "MEETING" in text and "<mark>" not in text, text

                # The row is on screen, inside the shelf, and on top where it is drawn.
                facts = page.evaluate("""(sel) => { const r = document.querySelector(sel).getBoundingClientRect();
                  const s = document.getElementById('desk-tool-shelf').getBoundingClientRect();
                  const top = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
                  return { inView: r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth,
                           inShelf: r.left >= s.left - 1 && r.right <= s.right + 1,
                           onTop: !!top && !!top.closest(sel), noScrollX: document.documentElement.scrollWidth <= innerWidth,
                           height: Math.round(r.height) }; }""", ROW)
                assert facts["inView"] and facts["inShelf"] and facts["onTop"] and facts["noScrollX"], facts
                assert facts["height"] == 26, facts   # the deck row species, unchanged
                page.screenshot(path=str(SHOTS / f"palette-memory-{width}.png"))

                self._press(page, row, width)
                page.wait_for_function(
                    """(t) => !document.getElementById('desk-tool-shelf') &&
                      [...document.querySelectorAll('.desk-window-shell, .desk-window, .desk-pullout')]
                        .some((w) => w.getBoundingClientRect().width > 0 && (w.innerText || '').includes(t))""",
                    arg=TITLE, timeout=15_000)
                page.wait_for_timeout(600)
                page.screenshot(path=str(SHOTS / f"palette-memory-opened-{width}.png"))
                assert not errors, errors
            finally:
                browser.close()
