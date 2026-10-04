"""Palette: Enter on the first row opens THAT object -- fenced AS RENDERED.

The inventory of 2026-10-03 (A-apps row 41) reported: "Enter on the first row
opened a Thought window, not the note (cause unknown)". The cause is not in
the palette. The first row for `ledger` was the note `Ledger cutover risks`,
and Enter opened that note. An earlier job of the same walk had pressed
`Develop this thought` on it, so the note was a thought, and a thought's
window is the Thought window (its frame is named `Thought`; the note's own
title is the first line inside it; shot A-shots/J48-palette-1440.jpg).

This fence holds both halves on the real hub (isolated HOME, 1440 and 393):

* an ordinary note titled with `ledger`: ⌘K, `ledger`, Enter (393: a tap on
  the first row) opens the window of that note, and no thought is made;
* the same note after `Develop this thought`: the same keys open the Thought
  window OF THAT NOTE (its title line is the note's title), and no new note
  is made.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the palette glass needs Playwright")

TOKEN = "palette-enter"
SHOTS = evidence_dir("tests/e2e/shots/palette-enter-opens-the-note")
SIZES = {1440: 900, 393: 852}
TITLE = "Ledger cutover risks"
THOUGHT = ".desk-window[aria-label='Thought']"


class TestEnterOpensTheFirstRow:
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

    def _find(self, page: Any, width: int, note_id: str) -> None:
        """Open the palette, type `ledger`, run the first row."""
        self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
        search = page.locator("[aria-controls=desk-palette-listbox]")
        search.fill("ledger")
        first = page.locator("#desk-palette-listbox [role=option]").first
        first.wait_for()
        assert first.get_attribute("id") == f"desk-palette-option-note:{note_id}", first.get_attribute("id")
        assert first.get_attribute("aria-selected") == "true", "the first row is not the selected row"
        assert TITLE in first.inner_text(), first.inner_text()
        if width >= 720:
            page.keyboard.press("Enter")
        else:
            self._press(page, first, width)

    @pytest.mark.parametrize("width", list(SIZES))
    def test_enter_opens_the_note_the_first_row_names(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
            try:
                ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                          device_scale_factor=1, has_touch=width < 720)
                page = ctx.new_page()
                page.set_default_timeout(30_000)
                errors: list[str] = []
                writes: list[str] = []
                page.on("pageerror", lambda e: errors.append(str(e)[:200]))
                page.on("request", lambda r: writes.append(r.url.split("?")[0].replace(self.base, ""))
                        if r.method == "POST" else None)
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                note = _api(page, "POST", "/api/notes", {
                    "title": TITLE, "body_markdown": "- reconciliation job slow\n- rollback plan owner: Jordan",
                    "tags": []}, token=TOKEN)["note"]
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1500)
                _settle(page)
                del writes[:]

                # 1. An ordinary note: Enter opens the note's own window. No thought is made.
                self._find(page, width, note["id"])
                win = page.locator(f"[id='pullout:note:{note['id']}']")
                win.wait_for()
                page.locator("text=Develop this thought").first.wait_for()
                assert win.get_attribute("aria-label") == TITLE, win.get_attribute("aria-label")
                assert page.locator(THOUGHT).count() == 0, "an ordinary note opened as a Thought"
                assert writes == [], ("opening a note wrote to the hub", writes)
                page.screenshot(path=str(SHOTS / f"ordinary-note-{width}.png"))

                # 2. The owner develops it (the product's verb). It is a thought now.
                self._press(page, page.get_by_role("button", name="Develop this thought").first, width)
                page.locator(THOUGHT).wait_for()
                self._press(page, page.locator(f"{THOUGHT} [aria-label='Close Thought']").first, width)
                page.locator(THOUGHT).wait_for(state="detached")
                _settle(page)
                del writes[:]

                # 3. The same keys open the Thought window OF THAT NOTE. No new note is made.
                self._find(page, width, note["id"])
                thought = page.locator(f"[id='pullout:note:{note['id']}']")
                thought.wait_for()
                assert thought.get_attribute("aria-label") == "Thought", thought.get_attribute("aria-label")
                thought.locator(".thought-note-title", has_text=TITLE).wait_for()
                assert page.locator(THOUGHT).count() == 1
                page.wait_for_timeout(800)
                assert "/api/notes" not in writes, ("the palette made a note", writes)
                page.screenshot(path=str(SHOTS / f"developed-note-{width}.png"))

                real = [e for e in errors if "ResizeObserver" not in e]
                assert not real, real
            finally:
                browser.close()
