"""PHILO-13-16 (C6) -- capture from anywhere, fenced AS RENDERED.

Through the real hub on an isolated HOME, at 1440x900 (mouse, keyboard) and
393x852 (touch: every press a tap; no hardware key assumed):

* 1440: ⌃T from a body window (Intelligence, focus on its body) opens a new
  Thought window: one key press, one POST /api/notes.
* 393: the same verb from the menu (the phone's one door, Go, carries the
  Desk menu's verbs): `Write a thought`, ⌃T shown.
* The key does not fire inside a text field that owns it: with focus in the
  Thought window's note and in the palette's search field, ⌃T writes no note.
  (jsdom lies about focus, so this fence is on glass.)
* Three thoughts typed: three names, each its first words, on the Chair's
  THOUGHTS rows and in the palette. Red on main: `Thought` x3.

Every record is minted by the product's own path (the verb -> openNewThought
-> POST /api/notes -> the thought adoption -> the writer's save).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .chair_windows import go_group, open_chair_window
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _rendered_text_faults, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the capture glass needs Playwright")

TOKEN = "philo13-16-capture"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-16-shots")
SIZES = {1440: 900, 393: 852}
BODIES = [
    "Ask Priya about the ledger ADR\nShe owns the cutover.",
    "Hire a second SRE before Q1\nBudget is open.",
    "Cut the reporting scope for Nov\nTell the team on Monday.",
]
TITLES = [body.split("\n", 1)[0] for body in BODIES]
THOUGHT = ".desk-window.thought-workspace-window"


class TestCaptureFromAnywhere:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

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
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
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

    @staticmethod
    def _thoughts_open(page: Any) -> int:
        return page.locator(THOUGHT).count()

    def _open_from_menu(self, page: Any, width: int) -> Any:
        # 1440: the Desk menu; 393: the one phone door, Go ▸ New ▸ Thought
        # (PHILO-15 11, B21, owner ruling 2026-10-07).
        menu = "desk" if width >= 720 else "go"
        self._press(page, page.locator(f".desk-verbbar-item[data-menu-id='{menu}'] button"), width)
        if width < 720:
            go_group(page, "New", lambda loc: self._press(page, loc, width))
        label = "Write a thought" if width >= 720 else "Thought"
        item = page.locator(f".desk-verbbar-menu [role='menuitem']:has-text('{label}')")
        item.wait_for()
        return item

    @staticmethod
    def _shoot_menu_row(page: Any, item: Any, width: int, proof: dict[str, Any]) -> None:
        """The verb's row in the menu shows its key, ⌃T (C2's keycap wells)."""
        item.scroll_into_view_if_needed()
        row = "".join(item.inner_text().split())
        proof[f"menu_row_{width}"] = row
        # PHILO-15 11 (B21): a phone has no ⌘/⌃ key, so the 393 row is `Thought`, no keycap.
        assert row.endswith("Writeathought⌃T") if width >= 720 else row.endswith("Thought"), row
        page.screenshot(path=str(SHOTS / f"menu-write-a-thought-{width}.png"))

    def _type_and_keep(self, page: Any, width: int, body: str, title: str) -> None:
        """Type the note; the title shows the first words once the save lands."""
        field = page.locator(f"{THOUGHT} .thought-note-body .cm-content").first
        field.wait_for()
        self._press(page, field, width)
        page.keyboard.type(body)
        page.locator(f"{THOUGHT} .thought-note-title", has_text=title).wait_for(timeout=15_000)
        page.wait_for_timeout(700)

    def _close_thought(self, page: Any, width: int) -> None:
        self._press(page, page.locator(f"{THOUGHT} .desk-gadget-close").first, width)
        page.locator(THOUGHT).wait_for(state="detached")
        _settle(page)

    # ── the fence ────────────────────────────────────────────────────────

    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_thought_from_anywhere_titled_by_its_words(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors, notes = self._page(pw, width)
            try:
                proof: dict[str, Any] = {"width": width}
                if width >= 720:
                    item = self._open_from_menu(page, width)
                    self._shoot_menu_row(page, item, width, proof)
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(300)
                for i, (body, title) in enumerate(zip(BODIES, TITLES)):
                    before = len(notes)
                    if width >= 720:
                        # A body window first: Intelligence from the Dock, focus on its body.
                        self._press(page, page.locator(".desk-dock-launch[aria-label^='Intelligence']"), width)
                        intel = page.locator(".desk-window[aria-label='Intelligence']")
                        intel.wait_for()
                        page.wait_for_timeout(600)
                        intel.locator(".desk-window-title").first.click()
                        focus = page.evaluate("() => { const a = document.activeElement; return {tag: a.tagName, field: a.matches('input,textarea,[contenteditable=true]')}; }")
                        assert not focus["field"], focus
                        if i == 0:
                            page.screenshot(path=str(SHOTS / f"key-from-body-window-before-{width}.png"))
                        page.keyboard.press("Control+t")  # ONE key press
                    else:
                        item = self._open_from_menu(page, width)
                        if i == 0:
                            self._shoot_menu_row(page, item, width, proof)
                        self._press(page, item, width)
                    page.locator(THOUGHT).wait_for()
                    assert len(notes) == before + 1, ("one press, one note", notes)
                    if i == 0:
                        page.wait_for_timeout(600)
                        page.screenshot(path=str(SHOTS / f"thought-open-{width}.png"))
                    self._type_and_keep(page, width, body, title)
                    if i == 0:
                        page.screenshot(path=str(SHOTS / f"thought-titled-{width}.png"))
                        faults = _rendered_text_faults(page, THOUGHT, on_glass=True)
                        proof["thought_window_faults"] = {k: faults[k] for k in ("clipped", "overlaps")}
                        assert not faults["clipped"] and not faults["overlaps"], faults
                    if width >= 720 and i == 0:
                        # The key inside a field that owns it: the note field, then the palette's
                        # search. In the note ⌃T is the editor's own key (it swaps two letters).
                        focus = page.evaluate("() => document.activeElement.closest('.cm-content') !== null")
                        assert focus, "focus is not in the note"
                        page.keyboard.press("Control+t")
                        page.wait_for_timeout(1200)
                        assert len(notes) == before + 1 and self._thoughts_open(page) == 1, (
                            "⌃T inside the note opened a thought", notes)
                        proof["in_note_field"] = "no note written"
                    self._close_thought(page, width)

                if width >= 720:
                    self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
                    search = page.locator("[aria-controls=desk-palette-listbox]")
                    search.focus()
                    before = len(notes)
                    page.keyboard.press("Control+t")
                    page.wait_for_timeout(1200)
                    assert len(notes) == before and self._thoughts_open(page) == 0, (
                        "⌃T inside the palette search opened a thought", notes)
                    proof["in_palette_field"] = "no note written"
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(400)

                # Three names on the Chair (The week window holds THOUGHTS).
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1200)
                if width < 720:
                    open_chair_window(page, "The week")
                rows = page.locator("[data-testid=arrival-thought-row]")
                rows.first.wait_for()
                rows.first.scroll_into_view_if_needed()
                chair_text = page.locator("[data-testid=arrival-thoughts]").inner_text()
                proof["chair_thoughts"] = chair_text
                for title in TITLES:
                    assert title in chair_text, (title, chair_text)
                assert "Thought\n" not in chair_text + "\n", chair_text
                page.locator("[data-testid=arrival-thoughts]").screenshot(
                    path=str(SHOTS / f"chair-three-names-{width}.png"))
                page.screenshot(path=str(SHOTS / f"chair-three-names-screen-{width}.png"))

                # Three names in the palette: each thought is found by its own words.
                self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
                search = page.locator("[aria-controls=desk-palette-listbox]")
                found: dict[str, list[str]] = {}
                for word, title in zip(("Priya", "SRE", "reporting"), TITLES):
                    search.fill(word)
                    page.wait_for_timeout(700)
                    options = page.locator("[id^='desk-palette-option-note:']")
                    labels = [options.nth(k).inner_text() for k in range(options.count())]
                    found[word] = labels
                    assert any(title in label for label in labels), (word, title, labels)
                    assert not any(label.strip() == "Thought" for label in labels), labels
                    if word == "SRE":
                        page.screenshot(path=str(SHOTS / f"palette-titled-{width}.png"))
                proof["palette"] = found
                search.fill("thought")
                page.wait_for_timeout(700)
                options = page.locator("[id^='desk-palette-option-note:']")
                proof["palette_thought"] = [options.nth(k).inner_text() for k in range(options.count())]
                assert not any(label.strip() == "Thought" for label in proof["palette_thought"]), proof

                (SHOTS / f"capture-{width}.txt").write_text(f"{proof}\n")
                real = [e for e in errors if "ResizeObserver" not in e]
                assert not real, real
            finally:
                browser.close()
