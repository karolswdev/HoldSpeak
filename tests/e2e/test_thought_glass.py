"""The note window (the sticky), rendered: only what needs a real browser.

Betterment Q8 "One note" (2026-10-18): every note opens in the sticky; New
Note (⌃N, and ⌃T) opens an empty one; its foot is Ask about this, Project ▾,
Send… and Done. Kept here (keys, focus and the send flow need a browser):

* ⌃T opens one new note from any window and never inside a field;
* one press opens one window at once, and every key typed lands in it;
* a note is sent to a folder from its own window.

The tests of the faces Q8 took off the sticky (the Reads well, Finish and
Resume, the thought engine band and its interview, the foot receipt beside
Add a note) are parked whole in tests/e2e/_parked/test_thought_glass.py. The
face half of Q8 is web/src/desk/pullouts/__tests__/note.app.test.tsx and
web/src/desk/thought-workspace/ThoughtWorkspaceWindow.test.tsx.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir
from tests.e2e.chair_windows import go_group
from tests.e2e.glass_infra import _normal_chair
from .glass_infra import _api as _gi_api, _boot as _gi_boot, _ensure_build, _settle

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(300, method="thread")]

K_TOKEN = "thought-glass"
THOUGHT = ".desk-window.thought-workspace-window"


class TestThoughtKeys:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _gi_boot(tmp_path, monkeypatch, token=K_TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def test_ctrl_t_opens_one_thought_and_never_inside_a_field(self) -> None:
        """replaces: tests/e2e/test_philo13_16_capture_glass.py::TestCaptureFromAnywhere::test_a_thought_from_anywhere_titled_by_its_words
        (the key and focus legs, 1440)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
            page = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1).new_page()
            page.set_default_timeout(30_000)
            errors: list[str] = []
            notes: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            page.on("request", lambda r: notes.append(r.url)
                    if r.method == "POST" and r.url.split("?")[0].endswith("/api/notes") else None)
            try:
                page.goto(f"{self.base}/?token={K_TOKEN}", wait_until="load")
                _gi_api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=K_TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1200)
                _settle(page)

                # A body window first: Today from the Dock, focus on its title bar.
                page.locator(".desk-dock-launch[aria-label^='Today']").click()
                today = page.locator(".desk-window[aria-label='Today']")
                today.wait_for()
                page.wait_for_timeout(600)
                today.locator(".desk-window-title").first.click()
                focus = page.evaluate("() => document.activeElement.matches('input,textarea,[contenteditable=true]')")
                assert not focus, "focus is in a field before the key"
                page.keyboard.press("Control+t")  # ONE key press
                page.locator(THOUGHT).wait_for()
                assert len(notes) == 1, ("one press, one note", notes)

                # Inside the note ⌃T is the editor's own key (it swaps two letters).
                field = page.locator(f"{THOUGHT} .thought-note-body .cm-content").first
                field.wait_for()
                field.click()
                page.keyboard.type("Ask Priya about the ledger ADR")
                page.locator(f"{THOUGHT} .desk-window-title", has_text="Ask Priya about the ledger ADR").wait_for(timeout=15_000)
                assert page.evaluate("() => document.activeElement.closest('.cm-content') !== null"), "focus is not in the note"
                page.keyboard.press("Control+t")
                page.wait_for_timeout(1200)
                assert len(notes) == 1 and page.locator(THOUGHT).count() == 1, ("⌃T inside the note opened a thought", notes)
                page.locator(f"{THOUGHT} .desk-gadget-close").first.click()
                page.locator(THOUGHT).wait_for(state="detached")
                _settle(page)

                # Inside the palette's search field.
                page.locator("[aria-controls=desk-tool-shelf]").first.click()
                page.locator("[aria-controls=desk-palette-listbox]").focus()
                page.keyboard.press("Control+t")
                page.wait_for_timeout(1200)
                assert len(notes) == 1 and page.locator(THOUGHT).count() == 0, (
                    "⌃T inside the palette search opened a thought", notes)
                assert not [e for e in errors if "ResizeObserver" not in e], errors
            finally:
                browser.close()


# ── moved whole from tests/e2e/test_thought_opens_at_once_glass.py and the PHILO-17 thought-send glass ──
SIZES = {1440: 900, 393: 852}
T = 20_000
OPENS_TOKEN = "thought-glass-opens"
OPENS_SHOTS = evidence_dir("tests/e2e/shots/thought-opens-at-once")
READ_DELAY_MS = 4000
OPENS_WITHIN_MS = 1500
OPENS_WORDS = "Ask Priya about the ledger ADR"
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
        server, base = _gi_boot(tmp_path, monkeypatch, token=OPENS_TOKEN)
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
        page.goto(f"{self.base}/?token={OPENS_TOKEN}", wait_until="load")
        _gi_api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=OPENS_TOKEN)
        self.seeded = {n["id"] for n in _gi_api(page, "GET", "/api/notes", token=OPENS_TOKEN)["notes"]}
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
        if width < 720:  # PHILO-15 11 (B21): Go ▸ New ▸ Thought at 393
            go_group(page, "New", lambda loc: self._press(page, loc, width))
        label = "New Note" if width >= 720 else "Note"
        item = page.locator(f".desk-verbbar-menu [role='menuitem']:has-text('{label}')").first
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
        return [n for n in _gi_api(page, "GET", "/api/notes", token=OPENS_TOKEN)["notes"]
                if not n.get("deleted") and n["id"] not in self.seeded]

    @pytest.mark.parametrize("width", list(SIZES))
    def test_one_press_one_window_every_key(self, width: int) -> None:
        """replaces: tests/e2e/test_thought_opens_at_once_glass.py::TestTheThoughtOpensAtOnce::test_one_press_one_window_every_key (moved whole)."""
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
                page.screenshot(path=str(OPENS_SHOTS / f"six-presses-{width}.png"))
                self._press(page, page.locator(f"{THOUGHT} .desk-gadget-close").first, width)
                page.locator(THOUGHT).wait_for(state="detached")
                page.wait_for_timeout(READ_DELAY_MS + 1500)  # the desk reads land

                if width >= 720:
                    # ⌃T from a body window, then the words with no wait: every key lands.
                    self._press(page, page.locator(".desk-dock-launch[aria-label^='Today']"), width)
                    intel = page.locator(".desk-window[aria-label='Today']")
                    intel.wait_for()
                    page.wait_for_timeout(600)
                    intel.locator(".desk-window-title").first.click()
                    page.keyboard.press("Control+t")
                    page.keyboard.type(OPENS_WORDS)  # no wait: the window is not there yet
                    self._opens(page, "⌃T at 1440")
                else:
                    self._menu_thought(page, width)
                    self._opens(page, "the menu verb at 393")
                    field = page.locator(f"{THOUGHT} .thought-note-body .cm-content").first
                    field.wait_for()
                    self._press(page, field, width)
                    page.keyboard.type(OPENS_WORDS)
                field = page.locator(f"{THOUGHT} .thought-note-body .cm-content").first
                field.wait_for()
                page.wait_for_function(
                    "(sel) => document.activeElement && document.activeElement.matches(sel)",
                    arg=f"{THOUGHT} .thought-note-body .cm-content", timeout=5_000)
                page.wait_for_timeout(300)
                assert field.inner_text().strip() == OPENS_WORDS, ("keys were lost", field.inner_text())
                assert len(notes) == 1, ("the empty thought was not used again", notes)
                page.keyboard.type(" today")  # the next key continues the same line
                page.locator(f"{THOUGHT} .desk-window-title", has_text=OPENS_WORDS).wait_for(timeout=15_000)
                assert field.inner_text().strip() == f"{OPENS_WORDS} today", field.inner_text()
                proof["typed"] = field.inner_text().strip()
                page.wait_for_timeout(1500)
                page.screenshot(path=str(OPENS_SHOTS / f"every-key-{width}.png"))

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
                page.locator(f"{THOUGHT} .desk-window-title", has_text=SECOND).wait_for(timeout=15_000)
                page.wait_for_timeout(1500)

                titles = sorted(n["title"] for n in self._thought_notes(page))
                proof["titles_on_hub"] = titles
                assert titles == sorted([f"{OPENS_WORDS} today", SECOND]), titles
                assert "Thought" not in titles, titles
                page.screenshot(path=str(OPENS_SHOTS / f"second-thought-{width}.png"))

                (OPENS_SHOTS / f"proof-{width}.txt").write_text(f"{proof}\n")
                real = [e for e in errors if "ResizeObserver" not in e]
                assert not real, real
            finally:
                browser.close()

    # Astra's condition on #790: the second thought started before the first was saved.
    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_second_thought_before_the_save_is_its_own_note(self, width: int) -> None:
        """replaces: tests/e2e/test_thought_opens_at_once_glass.py::TestTheThoughtOpensAtOnce::test_a_second_thought_before_the_save_is_its_own_note (moved whole)."""
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
                page.locator(f"{THOUGHT} .desk-window-title", has_text="Second thought").wait_for(timeout=15_000)
                page.wait_for_timeout(2500)  # both saves land
                page.screenshot(path=str(OPENS_SHOTS / f"second-before-save-{width}.png"))
                assert len(notes) == 2, ("the second thought did not get its own note", notes)
                kept = sorted((n["title"], n["body_markdown"].strip()) for n in self._thought_notes(page))
                assert kept == [("First thought", "First thought"), ("Second thought", "Second thought")], kept
                real = [e for e in errors if "ResizeObserver" not in e]
                assert not real, real
            finally:
                browser.close()


SEND_TOKEN = "thought-glass-send"
SEND_SHOTS = evidence_dir("tests/e2e/shots/philo17-thought-send")
SEND_WORDS = "Pilot plan: we start on Monday and Avery owns the rollout"


class TestTheThoughtSends:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _gi_boot(tmp_path, monkeypatch, token=SEND_TOKEN)
        self.base = base
        self.home = tmp_path / "home"
        from holdspeak.db import get_database

        self.db = get_database()
        try:
            yield
        finally:
            server.stop()

    def _menu_thought(self, page: Any, width: int) -> None:
        menu = "desk" if width >= 720 else "go"
        page.locator(f".desk-verbbar-item[data-menu-id='{menu}'] button").click()
        if width < 720:
            go_group(page, "New", lambda loc: loc.click())
        label = "New Note" if width >= 720 else "Note"
        item = page.locator(f".desk-verbbar-menu [role='menuitem']:has-text('{label}')").first
        item.wait_for()
        item.click()

    @staticmethod
    def _tap(page: Any, loc: Any) -> None:
        """A real pointer press at the verb's place (an inert well takes no press)."""
        loc.scroll_into_view_if_needed()
        box = loc.bounding_box()
        assert box, "the well's Send is not on the glass"
        if box:
            page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

    def _db_sends(self, note_ref: str) -> list[dict[str, Any]]:
        """The real isolated hub's rows, including its frozen transport bytes."""
        import json

        with self.db._connection() as conn:
            rows = conn.execute(
                "SELECT id, state, payload, proof_json FROM channel_sends WHERE document_ref=? ORDER BY rowid",
                (note_ref,),
            ).fetchall()
        return [{"id": r[0], "state": r[1], "payload": r[2], "proof": json.loads(r[3] or "{}")} for r in rows]

    def _saved_note(self, note_ref: str) -> tuple[int, str]:
        with self.db._connection() as conn:
            row = conn.execute(
                "SELECT t.working_revision, n.body_markdown FROM refinement_thoughts t "
                "JOIN notes n ON n.id=t.working_note_id WHERE t.working_note_id=?",
                (note_ref.removeprefix("note:"),),
            ).fetchone()
        assert row, note_ref
        return row[0], row[1]

    def _note_action(self, page: Any, win: Any, width: int, name: str) -> Any:
        foot = win.locator(".thought-note-foot")
        if width < 720:
            self._tap(page, foot.get_by_role("button", name="More actions", exact=True))
            action = page.get_by_role("menu", name="More actions", exact=True).get_by_role("menuitem", name=name, exact=True)
        else:
            action = foot.get_by_role("button", name=name, exact=True)
        action.wait_for(timeout=T)
        return action

    def _back(self, page: Any, win: Any, width: int, *, keyboard: bool = False) -> None:
        """Use the phone's actual frame Back, or the desktop host's Back."""
        back = (win.locator(".desk-gadget-close") if width < 720
                else win.locator(".thought-send-foot").get_by_role("button", name="Back", exact=True))
        if keyboard:
            back.focus()
            page.keyboard.press("Enter")
        else:
            self._tap(page, back)
        win.locator(".thought-note-body .cm-content").wait_for(timeout=T)
        assert win.locator("[data-testid=thought-send]").count() == 0
        name = "More actions" if width < 720 else "Send…"
        door = win.locator(".thought-note-foot").get_by_role("button", name=name, exact=True)
        page.wait_for_function("(el) => el.isConnected && el === document.activeElement", arg=door.element_handle(), timeout=T)
        assert door.is_visible()
        assert not page.get_by_role("menu", name="More actions", exact=True).count()

    @staticmethod
    def _send_geometry(page: Any, win: Any, width: int) -> None:
        from tests.e2e.test_send_glass import TARGETS44

        geo = win.evaluate("""(win) => {
          const well = win.querySelector('[data-testid=thought-send]');
          const outer = well.getBoundingClientRect();
          const box = (sel) => { const r = well.querySelector(sel).getBoundingClientRect();
            return {top:r.top, bottom:r.bottom, left:r.left, right:r.right, width:r.width, height:r.height}; };
          const payload = well.querySelector('[data-testid=send-preview-body]');
          return {outer:{top:outer.top, bottom:outer.bottom, left:outer.left, right:outer.right},
            preview:box('[data-testid=send-preview-body]'), verb:box('[data-testid=send-verb]'),
            overflow:getComputedStyle(well).overflowY,
            payloadOverflow:getComputedStyle(payload).overflowY, payloadMax:getComputedStyle(payload).maxHeight,
            nested:[...well.querySelectorAll('*')].filter((el) =>
              ['auto','scroll'].includes(getComputedStyle(el).overflowY) && el.scrollHeight > el.clientHeight + 1)
              .map((el) => el.className)};
        }""")
        assert geo["overflow"] in ("auto", "scroll"), geo
        assert not geo["nested"], geo
        assert geo["payloadOverflow"] not in ("auto", "scroll") and geo["payloadMax"] == "none", geo
        for name in ("preview", "verb"):
            box, outer = geo[name], geo["outer"]
            assert box["height"] > 0 and box["width"] > 0, geo
            assert outer["top"] - 1 <= box["top"] < box["bottom"] <= outer["bottom"] + 1, geo
            assert outer["left"] - 1 <= box["left"] < box["right"] <= outer["right"] + 1, geo
        if width < 720:
            # The existing nine-point probe also covers the host's Back control.
            targets = TARGETS44.replace(
                "[data-testid=send-well] button,",
                ".thought-send-foot button, .thought-workspace-window .desk-gadget-close, [data-testid=send-well] button,",
            )
            assert not page.evaluate(targets), "Send or Back loses part of its 44px target"
        assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth"), "page scrolls sideways"

    @pytest.mark.parametrize("width", list(SIZES))
    def test_write_a_thought_then_send_it_to_a_folder(self, width: int) -> None:
        """Clipboard, Back focus, exact saved revision, target geometry and real folder dispatch."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1)
            ctx.grant_permissions(["clipboard-read", "clipboard-write"])
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={SEND_TOKEN}", wait_until="load")
                _gi_api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=SEND_TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1200)
                _settle(page)

                # The frame opens before its authoritative workbench read.
                # Hold that read to exercise the real early-typing gap.
                opening_reads: list[Any] = []
                def hold_opening_read(route: Any) -> None:
                    opening_reads.append(route)
                    page.evaluate("window.__thoughtOpeningReadHeld = true")

                page.route("**/api/thoughts/*/workbench", hold_opening_read)
                with page.expect_request("**/api/thoughts/*/workbench") as opening_request:
                    self._menu_thought(page, width)
                assert opening_request.value.method == "GET"
                win = page.locator(THOUGHT)
                win.wait_for()
                win.locator(".thought-workspace-opening[aria-busy=true]").wait_for()
                page.wait_for_function("window.__thoughtOpeningReadHeld === true", timeout=T)
                assert opening_reads, "the initial workbench read was not held"
                page.keyboard.type(SEND_WORDS)  # the opening key buffer owns these words

                foot = win.locator(".thought-note-foot")
                door = foot.get_by_role("button", name="More actions" if width < 720 else "Send…", exact=True)
                opening = win.evaluate("""win => ({
                    loading: Boolean(win.querySelector('.thought-workspace-opening[aria-busy=true]')),
                    editor: Boolean(win.querySelector('.thought-note-body .cm-content')),
                    footer: Boolean(win.querySelector('.thought-note-foot')),
                    focused: document.activeElement?.getAttribute('aria-label')
                })""")
                (SEND_SHOTS / f"thought-send-opening-{width}.json").write_text(json.dumps(opening, indent=2) + "\n")
                page.screenshot(path=str(SEND_SHOTS / f"thought-send-opening-{width}.png"))
                assert opening["loading"] and not opening["editor"] and not opening["footer"], opening
                for route in opening_reads:
                    route.continue_()
                page.unroute("**/api/thoughts/*/workbench")
                # A frame is not an editable document. Let the authoritative
                # read mount Note and hand the buffered keys to its own field.
                note = win.locator(".thought-note-body .cm-content").first
                note.wait_for(timeout=T)
                page.wait_for_function("""([el, words]) => el.isConnected
                    && el.getAttribute('contenteditable') === 'true'
                    && el.innerText === words && document.activeElement === el""",
                    arg=[note.element_handle(), SEND_WORDS], timeout=T)
                door.wait_for(timeout=T)
                assert door.is_visible()
                opening["ready"] = note.evaluate("""el => ({body: el.innerText,
                    editable: el.getAttribute('contenteditable'), focused: document.activeElement === el})""")
                (SEND_SHOTS / f"thought-send-opening-{width}.json").write_text(json.dumps(opening, indent=2) + "\n")
                _settle(page)
                page.screenshot(path=str(SEND_SHOTS / f"thought-send-ready-{width}.png"))

                # Keyboard Send saves first, then owns the body. No dispatch yet.
                send = self._note_action(page, win, width, "Send…")
                send.focus()
                page.keyboard.press("Enter")
                well = win.locator("[data-testid=send-well][data-doc^='note:']")
                well.wait_for(timeout=T)
                note_ref = well.get_attribute("data-doc")
                assert note_ref
                win_id = win.get_attribute("id")
                opened = well.locator("[data-testid=send-open][data-destination='HoldSpeak folder']")
                opened.locator("[data-testid=send-preview]").wait_for(timeout=T)
                assert win.get_by_role("region", name="Send note", exact=True).evaluate(
                    "el => el === document.activeElement || el.contains(document.activeElement)"
                ), "keyboard Send left focus outside its body"
                preview = " ".join(opened.locator("[data-testid=send-preview]").inner_text().split())
                assert "Monday" in preview, preview
                assert not self._db_sends(note_ref)
                assert win.locator(".thought-note-body, .thought-note-ask, .thought-note-foot, .thought-reads-well, .thought-action-well").count() == 0
                assert win.get_by_role("button", name=re.compile(r"^(Finish|Resume|Copy|Task|Project ▾|Done)$")).count() == 0
                self._send_geometry(page, win, width)
                page.screenshot(path=str(SEND_SHOTS / f"thought-send-picked-{width}.png"))

                # Pointer Back returns to this note and restores its visible Send door.
                self._back(page, win, width)
                assert win.get_attribute("id") == win_id
                revision, saved_body = self._saved_note(note_ref)
                assert saved_body.strip() == SEND_WORDS, saved_body

                # Back -> edit -> Send: a held save cannot reopen an old preview.
                held: list[Any] = []
                mode = {"saves": "hold"}

                def saves(route: Any) -> None:
                    if mode["saves"] == "hold":
                        held.append(route)
                    elif mode["saves"] == "fail":
                        route.abort()
                    else:
                        route.continue_()

                page.route("**/api/thoughts/*/working", saves)
                note = win.locator(".thought-note-body .cm-content").first
                note.click()
                page.keyboard.press("End")
                page.keyboard.type(" REVISED")
                self._tap(page, self._note_action(page, win, width, "Send…"))
                for _ in range(100):  # the writer's held save reaches the route
                    if held:
                        break
                    page.wait_for_timeout(50)
                assert held, "the edit was never saved"
                assert not self._db_sends(note_ref), "Send dispatched while the edit was not saved"
                assert win.locator("[data-testid=thought-send], [data-testid=send-preview], [data-testid=send-verb]").count() == 0
                if width >= 720:
                    assert foot.get_by_role("button", name="Send…", exact=True).is_disabled()
                else:
                    assert foot.get_by_role("button", name="More actions", exact=True).get_attribute("aria-expanded") == "false"
                assert self._saved_note(note_ref) == (revision, saved_body)
                page.screenshot(path=str(SEND_SHOTS / f"thought-send-waits-{width}.png"))
                mode["saves"] = "pass"
                for route in held:
                    route.continue_()
                # Only the successfully saved revision opens a fresh preview.
                well.wait_for(timeout=T)
                page.wait_for_function(
                    "(sel) => (document.querySelector(sel)?.innerText || '').includes('REVISED')",
                    arg=f"{THOUGHT} [data-testid=send-open][data-destination='HoldSpeak folder'] [data-testid=send-preview]",
                    timeout=T)
                revised_body = f"{SEND_WORDS} REVISED"
                assert self._saved_note(note_ref) == (revision + 1, revised_body)
                self._send_geometry(page, win, width)

                # His press: the file is saved, the receipt names the path.
                verb = opened.locator("[data-testid=send-verb]")
                page.wait_for_function("(e) => e && !e.disabled", arg=verb.element_handle(), timeout=T)
                self._tap(page, verb)
                receipt = opened.locator("[data-receipt=latest][data-state=sent]")
                receipt.wait_for(timeout=T)
                sends = self._db_sends(note_ref)
                sent = [s for s in sends if s["state"] == "sent"]
                assert len(sent) == len(sends) == 1, sends
                path = Path(sent[0]["proof"]["path"])
                assert path.is_relative_to(self.home) and path.is_file(), path
                assert path.read_bytes() == sent[0]["payload"] and revised_body in path.read_text(), path
                text = " ".join(receipt.inner_text().split())
                # The built-in folder names its path from HOME (~).
                assert text == f"✓ SAVED ~/Documents/HoldSpeak/Sent/{path.name}", text
                receipt.scroll_into_view_if_needed()
                page.screenshot(path=str(SEND_SHOTS / f"thought-send-saved-{width}.png"))

                # Keyboard Back returns too. A failed revision cannot reopen Send.
                self._back(page, win, width, keyboard=True)
                assert win.get_attribute("id") == win_id
                mode["saves"] = "fail"
                note.click()
                page.keyboard.press("End")
                page.keyboard.type(" LOST")
                foot.locator("[data-tone=danger]").first.wait_for(timeout=T)
                self._tap(page, self._note_action(page, win, width, "Send…"))
                page.wait_for_timeout(600)
                after = self._db_sends(note_ref)
                assert len(after) == 1 and after[0]["id"] == sent[0]["id"], after
                assert win.locator("[data-testid=thought-send], [data-testid=send-preview], [data-testid=send-verb]").count() == 0
                assert self._saved_note(note_ref) == (revision + 1, revised_body)
                page.screenshot(path=str(SEND_SHOTS / f"thought-send-save-failed-{width}.png"))
                mode["saves"] = "pass"

                assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth"), "page scrolls sideways"
                assert not errors, errors
            finally:
                browser.close()
