"""`Write a thought` opens at once and keeps every key -- fenced AS RENDERED.

The faults (inventory 2026-10-03, A-apps row 31 and defect 6): the Thought
window opened 2 to 5 s after the press; the keys typed in that gap were lost;
every press made another note named `Thought` (six after one walk).

Through the real hub on an isolated HOME, at 1440x900 (keyboard) and 393x852
(touch; no hardware key assumed). The one thing this rig adds is the slow desk
read: the page delays its own `GET /api/roadmaps` by 4 s (the real hub still
answers it). Every record is made by the product's own verb.

* 1440: ⌃T from a body window, then the words typed with no wait. The window
  is on the glass, in front, inside 1.5 s; every key is in the note, in
  order; the note field has the cursor; the title becomes the first words.
* Both widths: the verb pressed six times with no words typed makes ONE note
  and ONE window. With words in it, the next press makes a new thought.
* An untitled thought with words is not named `Thought` on the hub.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .chair_windows import go_group
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the thought glass needs Playwright")

TOKEN = "thought-opens-at-once"
SHOTS = evidence_dir("tests/e2e/shots/thought-opens-at-once")
SIZES = {1440: 900, 393: 852}
READ_DELAY_MS = 4000
OPENS_WITHIN_MS = 1500
THOUGHT = ".desk-window.thought-workspace-window"
WORDS = "Ask Priya about the ledger ADR"
SECOND = "Hire a second SRE before Q1"

SLOW_READ = """(() => {
  const real = window.fetch.bind(window);
  window.fetch = (input, init) => {
    const url = typeof input === 'string' ? input : (input && input.url) || '';
    const method = ((init && init.method) || 'GET').toUpperCase();
    if (method === 'GET' && /\\/api\\/roadmaps(\\?|$)/.test(url))
      return new Promise((r) => setTimeout(r, %d)).then(() => real(input, init));
    return real(input, init);
  };
})()""" % READ_DELAY_MS

IN_FRONT = """(sel) => {
  const w = document.querySelector(sel); if (!w) return false;
  const r = w.getBoundingClientRect();
  const hit = (x, y) => { const e = document.elementFromPoint(x, y); return !!e && w.contains(e); };
  return hit(r.left + 40, r.top + 12) && hit(r.left + r.width / 2, r.top + 12) && hit(r.left + r.width / 2, r.top + r.height / 2);
}"""


class TestTheThoughtOpensAtOnce:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str], list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        notes: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.on("request", lambda r: notes.append(r.url)
                if r.method == "POST" and r.url.split("?")[0].endswith("/api/notes") else None)
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        self.seeded = {n["id"] for n in _api(page, "GET", "/api/notes", token=TOKEN)["notes"]}
        page.add_init_script(SLOW_READ)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(READ_DELAY_MS + 1500)  # the first desk read lands
        _settle(page)
        return browser, page, errors, notes

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    def _menu_thought(self, page: Any, width: int) -> None:
        menu = "desk" if width >= 720 else "go"
        self._press(page, page.locator(f".desk-verbbar-item[data-menu-id='{menu}'] button"), width)
        if width < 720:
            go_group(page, "Desk", lambda loc: self._press(page, loc, width))
        item = page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Write a thought')").first
        item.wait_for()
        self._press(page, item, width)

    @staticmethod
    def _opens(page: Any, what: str) -> None:
        try:
            page.locator(THOUGHT).wait_for(timeout=OPENS_WITHIN_MS)
        except Exception as exc:
            raise AssertionError(f"{what}: no Thought window inside {OPENS_WITHIN_MS} ms") from exc
        assert page.evaluate(IN_FRONT, THOUGHT), (what, "the Thought window is not in front")

    def _thought_notes(self, page: Any) -> list[dict[str, Any]]:
        """The notes this walk made (the hub seeds its own notes on a new HOME)."""
        return [n for n in _api(page, "GET", "/api/notes", token=TOKEN)["notes"]
                if not n.get("deleted") and n["id"] not in self.seeded]

    @pytest.mark.parametrize("width", list(SIZES))
    def test_one_press_one_window_every_key(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors, notes = self._page(pw, width)
            try:
                proof: dict[str, Any] = {"width": width}

                # Six presses, no words: one note, one window.
                for press in range(6):
                    self._menu_thought(page, width)
                    self._opens(page, f"press {press + 1} at {width}")
                    page.wait_for_timeout(400)
                assert len(notes) == 1, ("six presses made more than one note", notes)
                assert page.locator(THOUGHT).count() == 1, "six presses, more than one Thought window"
                kept = self._thought_notes(page)
                assert len(kept) == 1, kept
                proof["six_presses"] = {"notes_posted": len(notes), "notes_on_hub": len(kept)}
                page.screenshot(path=str(SHOTS / f"six-presses-{width}.png"))
                self._press(page, page.locator(f"{THOUGHT} .desk-gadget-close").first, width)
                page.locator(THOUGHT).wait_for(state="detached")
                page.wait_for_timeout(READ_DELAY_MS + 1500)  # the desk reads land

                if width >= 720:
                    # ⌃T from a body window, then the words with no wait: every key lands.
                    self._press(page, page.locator(".desk-dock-launch[aria-label^='Intelligence']"), width)
                    intel = page.locator(".desk-window[aria-label='Intelligence']")
                    intel.wait_for()
                    page.wait_for_timeout(600)
                    intel.locator(".desk-window-title").first.click()
                    page.keyboard.press("Control+t")
                    page.keyboard.type(WORDS)  # no wait: the window is not there yet
                    self._opens(page, "⌃T at 1440")
                else:
                    self._menu_thought(page, width)
                    self._opens(page, "the menu verb at 393")
                    field = page.locator(f"{THOUGHT} .thought-note-body .cm-content").first
                    field.wait_for()
                    self._press(page, field, width)
                    page.keyboard.type(WORDS)
                field = page.locator(f"{THOUGHT} .thought-note-body .cm-content").first
                field.wait_for()
                page.wait_for_function(
                    "(sel) => document.activeElement && document.activeElement.matches(sel)",
                    arg=f"{THOUGHT} .thought-note-body .cm-content", timeout=5_000)
                page.wait_for_timeout(300)
                assert field.inner_text().strip() == WORDS, ("keys were lost", field.inner_text())
                assert len(notes) == 1, ("the empty thought was not used again", notes)
                page.keyboard.type(" today")  # the next key continues the same line
                page.locator(f"{THOUGHT} .thought-note-title", has_text=WORDS).wait_for(timeout=15_000)
                assert field.inner_text().strip() == f"{WORDS} today", field.inner_text()
                proof["typed"] = field.inner_text().strip()
                page.wait_for_timeout(1500)
                page.screenshot(path=str(SHOTS / f"every-key-{width}.png"))

                # With words in it, the next press makes a new thought.
                self._press(page, page.locator(f"{THOUGHT} .desk-gadget-close").first, width)
                page.locator(THOUGHT).wait_for(state="detached")
                self._menu_thought(page, width)
                self._opens(page, f"the second thought at {width}")
                assert len(notes) == 2, ("a thought with words was used again", notes)
                field = page.locator(f"{THOUGHT} .thought-note-body .cm-content").first
                field.wait_for()
                if width < 720:
                    self._press(page, field, width)
                page.keyboard.type(SECOND)
                page.locator(f"{THOUGHT} .thought-note-title", has_text=SECOND).wait_for(timeout=15_000)
                page.wait_for_timeout(1500)

                titles = sorted(n["title"] for n in self._thought_notes(page))
                proof["titles_on_hub"] = titles
                assert titles == sorted([f"{WORDS} today", SECOND]), titles
                assert "Thought" not in titles, titles
                page.screenshot(path=str(SHOTS / f"second-thought-{width}.png"))

                (SHOTS / f"proof-{width}.txt").write_text(f"{proof}\n")
                real = [e for e in errors if "ResizeObserver" not in e]
                assert not real, real
            finally:
                browser.close()

    # Astra's condition on #790: the second thought started before the first was saved.
    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_second_thought_before_the_save_is_its_own_note(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors, notes = self._page(pw, width)
            try:
                self._menu_thought(page, width)
                self._opens(page, f"the first thought at {width}")
                field = page.locator(f"{THOUGHT} .thought-note-body .cm-content").first
                field.wait_for()
                if width < 720:
                    self._press(page, field, width)
                page.keyboard.type("First thought")
                # At once: no wait for the save, no close.
                self._menu_thought(page, width)
                page.keyboard.type("Second thought")
                page.wait_for_function(
                    "(sel) => document.querySelectorAll(sel).length === 2", arg=THOUGHT, timeout=OPENS_WITHIN_MS + 1000)
                page.locator(f"{THOUGHT} .thought-note-title", has_text="Second thought").wait_for(timeout=15_000)
                page.wait_for_timeout(2500)  # both saves land
                page.screenshot(path=str(SHOTS / f"second-before-save-{width}.png"))
                assert len(notes) == 2, ("the second thought did not get its own note", notes)
                kept = sorted((n["title"], n["body_markdown"].strip()) for n in self._thought_notes(page))
                assert kept == [("First thought", "First thought"), ("Second thought", "Second thought")], kept
                real = [e for e in errors if "ResizeObserver" not in e]
                assert not real, real
            finally:
                browser.close()
