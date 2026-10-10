"""PHILO-17 objverbs — the Chair has the desk's one selection, on a real hub.

Two walkers (BLOCKER): on the Chair, a selected icon drew selected but the
menu bar Object menu kept every verb disabled ("Select an object"), a
right-click opened no menu and F2 did nothing. The Chair kept its selection
in local state; the menu bar and the keymap read the store's selectedIds.

- 1440: select a loose note on the Chair → Object ▸ Rename is live → F2 opens
  its editor and a new title is kept; a right-click opens the object menu.
- 393: a right-click on the icon opens the object menu; Rename opens the editor.
- Desk ▸ New Note: the title starts empty (placeholder only); typing gives
  exactly what was typed, never "New note<typed>".
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="objverbs glass needs Playwright")

TOKEN = "philo17-objverbs"
SHOTS = evidence_dir("p17-objverbs")
SIZES = {1440: 900, 393: 852}
T = 20_000
NOTE_ID, NOTE = "n-loose", "Questions for Avery"
ICON = f".desk-screen [data-object-id='note:{NOTE_ID}']"


class TestObjectVerbsOnTheChair:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        from holdspeak.db import get_database
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.primitive_service import PrimitiveService

        self.db = get_database()
        PrimitiveService(self.db).create_note(
            Principal(PrincipalKind.OWNER, "karol"), note_id=NOTE_ID, title=NOTE, body_markdown="- cutover", tags=[])
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                  has_touch=width < 720, reduced_motion="reduce")
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        page.locator(ICON).wait_for(timeout=T)
        return browser, page, errors

    def _note_title(self) -> str:
        return str(self.db.notes.get(NOTE_ID).title)

    def _rename_in_editor(self, page: Any, title: str) -> None:
        editor = page.locator(".desk-editor-window")
        editor.wait_for(timeout=T)
        field = editor.get_by_role("textbox", name="Title", exact=True)
        with page.expect_response(lambda r: f"/api/notes/{NOTE_ID}" in r.url and r.request.method == "PUT"
                                  and (r.request.post_data_json or {}).get("title") == title) as kept:
            field.fill(title)
        assert kept.value.ok, kept.value.text()
        editor.get_by_role("button", name="Save", exact=True).click()
        editor.wait_for(state="detached", timeout=T)

    def _object_rename_disabled(self, page: Any, shot: str | None = None) -> bool:
        """Open the menu bar Object menu; True when Rename is ghosted."""
        page.locator(".desk-verbbar").get_by_role("button", name="Object", exact=True).click()
        menu = page.get_by_role("menu", name="Object menu")
        menu.wait_for(timeout=T)
        disabled = menu.get_by_role("menuitem", name=re.compile(r"^Rename")).get_attribute("aria-disabled") == "true"
        if shot:
            page.screenshot(path=str(SHOTS / shot))
        page.keyboard.press("Escape")
        menu.wait_for(state="detached", timeout=T)
        return disabled

    def test_1440_object_menu_f2_and_right_click(self) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                icon = page.locator(ICON)
                # Nothing selected: Object ▸ Rename is ghosted.
                assert self._object_rename_disabled(page) is True
                icon.click()
                assert icon.get_attribute("aria-pressed") == "true"
                # Selected on the Chair: the menu bar Object menu reads the same selection.
                assert self._object_rename_disabled(page, shot="objverbs-1440-object-menu.png") is False
                # A press on empty glass clears the selection: ghosted again.
                page.mouse.click(720, 600)
                assert icon.get_attribute("aria-pressed") == "false"
                assert self._object_rename_disabled(page) is True
                # F2 renames the selected icon.
                icon.click()
                page.keyboard.press("F2")
                self._rename_in_editor(page, "Avery 1:1 questions")
                assert self._note_title() == "Avery 1:1 questions"
                # After a reload the desk and the editor show the new title.
                page.reload(wait_until="load")
                _normal_chair(page)
                icon = page.locator(ICON)
                icon.wait_for(timeout=T)
                assert "Avery 1:1 questions" in (icon.get_attribute("aria-label") or ""), icon.get_attribute("aria-label")
                icon.click()
                page.keyboard.press("F2")
                editor = page.locator(".desk-editor-window")
                editor.wait_for(timeout=T)
                assert editor.get_by_role("textbox", name="Title", exact=True).input_value() == "Avery 1:1 questions"
                editor.get_by_role("button", name="Save", exact=True).click()
                editor.wait_for(state="detached", timeout=T)
                # A right-click opens the Floor's object menu.
                icon.click(button="right")
                ctx_menu = page.locator(".desk-world-menu")
                ctx_menu.wait_for(timeout=T)
                live = ctx_menu.get_by_role("menuitem", name=re.compile(r"^Rename"))
                assert live.get_attribute("aria-disabled") != "true"
                page.screenshot(path=str(SHOTS / "objverbs-1440-right-click.png"))
                page.keyboard.press("Escape")
                # Desk ▸ New Note: the title starts empty; typing is exactly what was typed.
                page.locator(".desk-verbbar").get_by_role("button", name="Desk", exact=True).click()
                page.get_by_role("menuitem", name=re.compile(r"^New Note")).click()
                editor = page.locator(".desk-editor-window")
                editor.wait_for(timeout=T)
                field = editor.get_by_role("textbox", name="Title", exact=True)
                field.wait_for(timeout=T)
                assert field.input_value() == ""
                assert field.get_attribute("placeholder") == "New note"
                # The new note's title well takes the focus (StringGadget autoFocus).
                field.evaluate("el => new Promise((ok) => { const t = setInterval(() => "
                               "{ if (document.activeElement === el) { clearInterval(t); ok(true); } }, 20); })")
                page.keyboard.type("Ask Avery")
                assert field.input_value() == "Ask Avery"
                page.screenshot(path=str(SHOTS / "objverbs-1440-new-note.png"))
                assert not errors, errors
            finally:
                browser.close()

    def test_393_right_click_opens_the_object_menu(self) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 393)
            try:
                icon = page.locator(ICON)
                icon.scroll_into_view_if_needed()
                icon.click(button="right")
                assert icon.get_attribute("aria-pressed") == "true"
                ctx_menu = page.locator(".desk-world-menu")
                ctx_menu.wait_for(timeout=T)
                rename = ctx_menu.get_by_role("menuitem", name=re.compile(r"^Rename"))
                assert rename.get_attribute("aria-disabled") != "true"
                page.screenshot(path=str(SHOTS / "objverbs-393-right-click.png"))
                rename.click()
                self._rename_in_editor(page, "Avery questions")
                assert self._note_title() == "Avery questions"
                assert not errors, errors
            finally:
                browser.close()
