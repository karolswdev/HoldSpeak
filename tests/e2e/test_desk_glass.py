"""The desk (the Screen) app, AS RENDERED: what only a real browser proves.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation. Through the real hub
on an isolated HOME at 1440x900 (mouse, keys) and 393x852 (touch):

* PHILO-17 objverbs (moved whole): the Chair has the desk's one selection: a
  selected loose note makes Object ▸ Rename live; F2 opens its editor and a
  new title is kept; a right click (1440, 393) opens the object menu; Desk ▸
  New Note starts with an empty title.
* PHILO-17 one desk (two of its four cases): an off-desk kind keeps Delete
  from its window menu (right click; a touch long press at 393), the receipt
  readable on the desk, the hub answering 404 after the Undo window; Undo
  stays in view (in the viewport, owning its centre) after a window Delete
  with a Chair window already open.

* PHILO-3-01 (moved whole): the ONE write receipt's Retry and OK own their
  areas (nine points; 44 x 44 at 393, the painted face at 1440) to
  `elementFromPoint` and a real pointer, in three consumers (the chrome, a
  Thread, a footer), each driven to a real failure at the browser boundary.
* PHILO-9-04 (moved whole): the selection in the note editor and the thread
  composer is readable (the computed ::selection colours at 4.5:1).

The other two one-desk cases have successors: a stored Floor loads the Screen
in web/src/desk/__tests__/deskRemembers.philo1307.test.tsx:137 (and the sweep's
bare desk), the Dock's seats in Dock.test.tsx:130, Send from a desk window in
tests/e2e/test_send_glass.py and tests/unit/test_desk_palette_send.py; a zone
window refused and closed on the hub in tests/unit/test_desk_windows_routes.py:131
and tests/unit/test_desk_window_service.py:448.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _api_allow_error, _boot, _ensure_build, _normal_chair, _settle
from .chair_windows import open_chair_window
from tests._evidence import evidence_dir
from tests.e2e.test_kit_glass import OWNERSHIP_JS, PROBES, _overlap

pytest.importorskip("playwright.sync_api", reason="the desk glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "desk-glass"
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
        if width < 720:
            # The phone has a Go index instead of loose Screen icons. Open
            # this exact note, then use its window's Object menu.
            _search(page, NOTE, f"[id='desk-palette-option-note:{NOTE_ID}']")
            page.get_by_role("region", name=NOTE, exact=True).wait_for(timeout=T)
        else:
            page.locator(ICON).wait_for(timeout=T)
        return browser, page, errors

    def _note_title(self) -> str:
        return str(self.db.notes.get(NOTE_ID).title)

    def _rename_in_editor(self, page: Any, title: str, *, inline: bool = False) -> None:
        # Betterment Q8: Rename opens the same sticky at both widths.
        editor = page.locator(f"[id='pullout:note:{NOTE_ID}']")
        editor.wait_for(timeout=T)
        editor.get_by_role("button", name="Edit Title", exact=True).click()
        field = editor.get_by_role("textbox", name="Title", exact=True)
        field.fill(title)
        with page.expect_response(lambda r: "/api/thoughts/" in r.url and r.url.endswith("/working")
                                  and r.request.method == "PATCH"
                                  and (r.request.post_data_json or {}).get("title") == title) as kept:
            field.press("Enter")
        assert kept.value.ok, kept.value.text()
        assert editor.get_attribute("aria-label") == title
        editor.get_by_role("button", name="Done", exact=True).click()
        editor.wait_for(state="detached", timeout=T)

    def _object_rename_disabled(self, page: Any, shot: str | None = None) -> bool:
        """True when the menu bar offers no live Rename for an object.

        Betterment shell S0 (#1257): the Object menu mirrors right-click and
        is titled by the target's kind ("Note"); with no target its title is
        not drawn, and a row that cannot run is withheld, not ghosted."""
        title = page.locator(".desk-verbbar").get_by_role("button", name="Note", exact=True)
        if not title.count():
            assert not page.locator(".desk-verbbar").get_by_role("button", name="Object", exact=True).count()
            return True
        title.click()
        menu = page.get_by_role("menu", name="Note menu")
        menu.wait_for(timeout=T)
        rename = menu.get_by_role("menuitem", name=re.compile(r"^Rename"))
        disabled = not rename.count() or rename.get_attribute("aria-disabled") == "true"
        if shot:
            page.screenshot(path=str(SHOTS / shot))
        page.keyboard.press("Escape")
        menu.wait_for(state="detached", timeout=T)
        return disabled

    def test_1440_object_menu_f2_and_right_click(self) -> None:
        """replaces: tests/e2e/test_philo17_objverbs_glass.py::TestObjectVerbsOnTheChair::test_1440_object_menu_f2_and_right_click (moved whole)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                icon = page.locator(ICON)
                # Nothing selected: no Object menu, so no Rename (S0 #1257).
                assert self._object_rename_disabled(page) is True
                icon.click()
                assert icon.get_attribute("aria-pressed") == "true"
                # Selected on the Chair: the menu bar Object menu reads the same selection.
                assert self._object_rename_disabled(page, shot="objverbs-1440-object-menu.png") is False
                # A press on empty glass clears the selection: the Note menu goes.
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
                editor = page.locator(f"[id='pullout:note:{NOTE_ID}']")
                editor.wait_for(timeout=T)
                assert editor.get_by_role("button", name="Edit Title", exact=True).inner_text() == "Avery 1:1 questions"
                editor.get_by_role("button", name="Done", exact=True).click()
                editor.wait_for(state="detached", timeout=T)
                # A right-click opens the Floor's object menu.
                icon.click(button="right")
                ctx_menu = page.locator(".desk-world-menu")
                ctx_menu.wait_for(timeout=T)
                live = ctx_menu.get_by_role("menuitem", name=re.compile(r"^Rename"))
                assert live.get_attribute("aria-disabled") != "true"
                page.screenshot(path=str(SHOTS / "objverbs-1440-right-click.png"))
                page.keyboard.press("Escape")
                # New Note opens an empty sticky; its body receives the keys.
                page.locator(".desk-verbbar").get_by_role("button", name="Desk", exact=True).click()
                page.get_by_role("menuitem", name=re.compile(r"^New Note")).click()
                editor = page.locator(".thought-workspace-window")
                editor.wait_for(timeout=T)
                field = editor.get_by_role("textbox", name="Note body", exact=True)
                field.wait_for(timeout=T)
                assert field.locator(".cm-placeholder").is_visible()
                field.click()
                page.keyboard.type("Ask Avery")
                assert field.inner_text() == "Ask Avery"
                page.screenshot(path=str(SHOTS / "objverbs-1440-new-note.png"))
                assert not errors, errors
            finally:
                browser.close()

    def test_393_right_click_opens_the_object_menu(self) -> None:
        """replaces: tests/e2e/test_philo17_objverbs_glass.py::TestObjectVerbsOnTheChair::test_393_right_click_opens_the_object_menu (moved whole)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 393)
            try:
                note = page.get_by_role("region", name=NOTE, exact=True)
                note.locator(":scope > .desk-pullout-head").click(button="right")
                ctx_menu = page.locator(".desk-head-menu")
                ctx_menu.wait_for(timeout=T)
                ctx_menu.get_by_role("menuitem", name="Object", exact=True).click()
                rename = ctx_menu.get_by_role("menuitem", name=re.compile(r"^Rename"))
                assert rename.get_attribute("aria-disabled") != "true"
                page.screenshot(path=str(SHOTS / "objverbs-393-right-click.png"))
                rename.click()
                self._rename_in_editor(page, "Avery questions", inline=True)
                assert self._note_title() == "Avery questions"
                assert not errors, errors
            finally:
                browser.close()

# ── PHILO-17 one desk: Delete from a window keeps its receipt and Undo ──
OD_TOKEN = "desk-glass-one-desk"
OD_SHOTS = evidence_dir("p17-one-desk")
DECISION = "Freeze the old ledger on Nov 5"
WORKSPACE = "hs.desk.workspace.v1"


class TestOneDesk:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=OD_TOKEN)
        self.server, self.base = server, base
        from holdspeak.db import get_database

        self.db = get_database()
        try:
            yield
        finally:
            server.stop()

    def _sends(self, ref: str) -> list[dict[str, Any]]:
        with self.db._connection() as conn:
            rows = conn.execute(
                "SELECT id, state FROM channel_sends WHERE document_ref = ?", (ref,)).fetchall()
        return [{"id": r[0], "state": r[1]} for r in rows]

    def _tap(self, page: Any, loc: Any, phone: bool, ms: int = 700) -> None:
        loc = loc.first
        loc.scroll_into_view_if_needed()
        if phone:
            b = loc.bounding_box()
            page.touchscreen.tap(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
        else:
            loc.click()
        page.wait_for_timeout(ms)

    def _window_menu(self, page: Any, win: str, phone: bool) -> None:
        head = page.locator(f"[id='{win}'] > .desk-pullout-head")
        t = head.locator(".desk-pullout-title").first
        b = t.bounding_box() if t.count() and t.is_visible() else head.first.bounding_box()
        x, y = b["x"] + min(b["width"] - 4, max(8, b["width"] / 2)), b["y"] + b["height"] / 2
        hit = page.evaluate("""([x, y]) => {
          const target = document.elementFromPoint(x, y);
          return {window: target?.closest('.desk-window-shell')?.id,
                  target: target?.outerHTML.slice(0, 200)};
        }""", [x, y])
        assert hit["window"] == win, (win, b, hit)
        if phone:
            cdp = page.context.new_cdp_session(page)
            cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y, "id": 1}]})
            page.wait_for_timeout(750)
            cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
            cdp.detach()
            page.wait_for_timeout(500)
        else:
            page.mouse.click(x, y, button="right")
            page.wait_for_timeout(500)
        page.locator(".desk-head-menu").wait_for(timeout=10_000)

    def _desk(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        phone = width <= 720
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                  has_touch=phone, reduced_motion="reduce")
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={OD_TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=OD_TOKEN)
        return browser, page, errors

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", list(SIZES))
    def test_an_off_desk_window_deletes_its_object(self, width: int) -> None:
        """replaces: tests/e2e/test_philo17_one_desk_glass.py::TestOneDesk::test_an_off_desk_window_deletes_its_object (moved whole: the window menu by right click or a touch long press; the receipt in view)."""
        from playwright.sync_api import sync_playwright

        phone = width <= 720
        with sync_playwright() as pw:
            browser, page, errors = self._desk(pw, width)
            try:
                made = _api(page, "POST", "/api/chains", {"name": "One desk sequence", "steps": []}, token=OD_TOKEN)
                chain_id = made["chain"]["id"]
                page.reload(wait_until="load")
                _normal_chair(page)
                page.locator("[data-testid=desk-screen]").wait_for(timeout=T)
                # Search is the Sequence's door (it is not on the desk).
                field = page.locator("[aria-controls=desk-palette-listbox]")
                if not field.is_visible():
                    page.locator("[aria-controls=desk-tool-shelf]").first.click()
                field.fill("One desk sequence")
                self._tap(page, page.locator(f"[id='desk-palette-option-chain:{chain_id}']"), phone, 900)
                win = f"pullout:sequence:{chain_id}"
                page.locator(f"[id='{win}']").wait_for(timeout=T)
                page.wait_for_timeout(900)
                self._window_menu(page, win, phone)
                menu = page.locator(".desk-head-menu")
                obj = menu.get_by_role("menuitem", name="Object", exact=True)
                obj.wait_for(timeout=T)
                if phone:
                    self._tap(page, obj, phone)
                else:
                    obj.hover()
                    page.wait_for_timeout(700)
                    assert obj.get_attribute("aria-expanded") == "true"
                object_menu = page.get_by_role("menu", name="Object submenu", exact=True)
                object_menu.wait_for(timeout=T)
                # Desktop adds a visible Delete key hint to the accessible
                # name. The exact action label identifies the one row.
                delete = object_menu.get_by_role("menuitem").filter(
                    has=page.locator(".desk-menu-label", has_text=re.compile(r"^Delete$")))
                assert delete.count() == 1, object_menu.inner_text()
                assert delete.get_attribute("aria-disabled") != "true", delete.inner_text()
                self._tap(page, delete, phone, 900)
                page.locator(f"[id='{win}']").wait_for(state="detached", timeout=T)
                receipt = page.locator(".undo-receipt").first
                receipt.wait_for(timeout=T)
                assert "Removed" in receipt.inner_text(), receipt.inner_text()
                box = receipt.bounding_box()
                assert box and box["y"] >= 0 and box["y"] + box["height"] <= SIZES[width], box
                _settle(page)
                page.screenshot(path=str(OD_SHOTS / f"one-desk-window-delete-{width}.png"))
                page.wait_for_function(
                    "() => (document.querySelector('.undo-receipt')?.innerText || '').includes('Removal committed')",
                    timeout=20_000)
                status, _ = _api_allow_error(page, "GET", f"/api/chains/{chain_id}", token=OD_TOKEN)
                assert status == 404, status
                assert not [e for e in errors if "ResizeObserver" not in e and "Failed to fetch" not in e], errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", list(SIZES))
    def test_window_delete_keeps_undo_in_view_with_a_chair_window_open(self, width: int) -> None:
        """replaces: tests/e2e/test_philo17_one_desk_glass.py::TestOneDesk::test_window_delete_keeps_undo_in_view_with_a_chair_window_open (moved whole: the window menu by right click or a touch long press; the receipt in view)."""
        from playwright.sync_api import sync_playwright

        phone = width <= 720
        with sync_playwright() as pw:
            browser, page, errors = self._desk(pw, width)
            try:
                made = _api(page, "POST", "/api/chains", {"name": "Undo sequence", "steps": []}, token=OD_TOKEN)
                chain_id = made["chain"]["id"]
                page.reload(wait_until="load")
                _normal_chair(page)
                page.locator("[data-testid=desk-screen]").wait_for(state="attached", timeout=T)
                # A Chair window first: at 393 it fills the work area over the Screen.
                open_chair_window(page, "Needs you")
                field = page.locator("[aria-controls=desk-palette-listbox]")
                if not field.is_visible():
                    page.locator("[aria-controls=desk-tool-shelf]").first.click()
                field.fill("Undo sequence")
                self._tap(page, page.locator(f"[id='desk-palette-option-chain:{chain_id}']"), phone, 900)
                win = f"pullout:sequence:{chain_id}"
                page.locator(f"[id='{win}']").wait_for(timeout=T)
                page.wait_for_timeout(900)
                self._window_menu(page, win, phone)
                menu = page.locator(".desk-head-menu")
                obj = menu.get_by_role("menuitem", name="Object", exact=True)
                obj.wait_for(timeout=T)
                if phone:
                    self._tap(page, obj, phone)
                else:
                    obj.hover()
                    page.wait_for_timeout(700)
                    assert obj.get_attribute("aria-expanded") == "true"
                object_menu = page.get_by_role("menu", name="Object submenu", exact=True)
                object_menu.wait_for(timeout=T)
                delete = object_menu.get_by_role("menuitem").filter(
                    has=page.locator(".desk-menu-label", has_text=re.compile(r"^Delete$")))
                assert delete.count() == 1, object_menu.inner_text()
                self._tap(page, delete, phone, 900)
                page.locator(f"[id='{win}']").wait_for(state="detached", timeout=T)
                # The Chair window is still open; the receipt and its Undo are on the glass.
                assert page.locator(".desk-window-shell.chair-window[aria-label='Needs you']").first.is_visible()
                page.wait_for_function(
                    "() => (document.querySelector('.undo-receipt')?.innerText || '').includes('Removed')", timeout=T)
                _settle(page)
                seen = page.evaluate("""() => { const b = document.querySelector('.undo-receipt-btn');
                    if (!b) return null; const r = b.getBoundingClientRect();
                    const hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
                    return {inView: r.width > 0 && r.top >= 0 && r.left >= 0 && r.bottom <= innerHeight && r.right <= innerWidth,
                            own: !!hit && (hit === b || b.contains(hit))}; }""")
                assert seen and seen["inView"] and seen["own"], seen
                page.screenshot(path=str(OD_SHOTS / f"one-desk-undo-over-chair-{width}.png"))
                self._tap(page, page.locator(".undo-receipt-btn"), phone, 600)
                page.wait_for_function(
                    "() => (document.querySelector('.undo-receipt')?.innerText || '').includes('Restored')", timeout=T)
                page.wait_for_timeout(10_000)  # past the 8 s window
                status, _ = _api_allow_error(page, "GET", f"/api/chains/{chain_id}", token=OD_TOKEN)
                assert status == 200, status
                assert not [e for e in errors if "ResizeObserver" not in e and "Failed to fetch" not in e], errors
            finally:
                browser.close()


# ── Betterment P9: one decision record across Project, Desk and Needs you ──
P9_TOKEN = "p9-one-decision"
P9_SHOTS = evidence_dir("p9-one-decision")
P9_PROJECT_ID = "p-p9-one-decision"
P9_PROJECT_NAME = "P9 canonical project"
P9_DECISION_TEXT = "Use one canonical decision record for every surface."
P9_ABOUT = f"About: {P9_PROJECT_NAME}"
P9_WHY = "Why: one record keeps Project and Desk reads aligned."
P9_MEETING_ID = "m-p9-decide"
P9_MEETING_DECISION = "Keep the meeting decision in the canonical ledger."
P9_PROPOSED = "Confirm the proposed architecture direction"


class TestOneDecisionRecord:
    """T4: real producers and consumers share one canonical decision record."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=P9_TOKEN)
        self.server, self.base = server, base
        from .meetings_rig import _save_meeting
        from holdspeak.db import get_database

        self.db = get_database()
        self.db.projects.create_project(
            project_id=P9_PROJECT_ID,
            name=P9_PROJECT_NAME,
            description="A project for the one decision record proof.",
            keywords=["p9", "canonical", "decision"],
        )
        _save_meeting(P9_MEETING_ID, "P9 decision review", 1, "disabled")
        self.db.projects.associate_meeting_project(
            meeting_id=P9_MEETING_ID, project_id=P9_PROJECT_ID, source="manual", confidence=1.0,
        )
        try:
            yield
        finally:
            server.stop()

    @staticmethod
    def _tap(page: Any, loc: Any, phone: bool) -> None:
        loc = loc.first
        loc.scroll_into_view_if_needed()
        if phone:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        phone = width <= 720
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(
            viewport={"width": width, "height": SIZES[width]},
            device_scale_factor=1,
            has_touch=phone,
            reduced_motion="reduce",
        )
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)[:200]))
        page.goto(f"{self.base}/?token={P9_TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=P9_TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.locator("[data-testid=desk-screen]").wait_for(timeout=45_000)
        return browser, page, errors

    def _open_project(self, page: Any, phone: bool) -> Any:
        launcher = page.locator("[aria-controls=desk-tool-shelf]").first
        if not launcher.is_visible():
            launcher = page.locator("[aria-controls=desk-tool-shelf]").first
        launcher.click()
        field = page.locator("[aria-controls=desk-palette-listbox]")
        field.wait_for(timeout=T)
        field.fill(P9_PROJECT_NAME)
        option = page.locator(f"[id='desk-palette-option-project.open.{P9_PROJECT_ID}']")
        option.wait_for(timeout=T)
        self._tap(page, option, phone)
        room = page.locator("#surface-project-memory")
        room.wait_for(timeout=T)
        room.get_by_test_id("room-head").wait_for(timeout=T)
        name = room.locator(".room-head-name-measure")
        name.wait_for(state="attached", timeout=T)
        assert name.text_content() == P9_PROJECT_NAME
        return room

    @staticmethod
    def _json(page: Any, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        result = page.evaluate(
            """async ([method, path, body, token]) => {
              const response = await fetch(path, {
                method,
                headers: { authorization: `Bearer ${token}`, ...(body ? {"content-type": "application/json"} : {}) },
                body: body ? JSON.stringify(body) : undefined,
              });
              let payload = null;
              try { payload = await response.json(); } catch (_) {}
              return { status: response.status, payload };
            }""",
            [method, path, body, P9_TOKEN],
        )
        assert result["status"] < 300, result
        return result["payload"]

    def _new_decision(self, page: Any, phone: bool) -> tuple[str, str, Any]:
        _search(page, "New Decision", "[id='desk-palette-option-desk.new-decision']")
        prompt = page.get_by_test_id("palette-name")
        prompt.wait_for(timeout=T)
        with page.expect_response(
            lambda response: response.request.method == "POST" and response.url.endswith("/api/decision-records/from-desk")
        ) as created:
            prompt.fill(P9_DECISION_TEXT)
            page.get_by_test_id("decision-about-chip").wait_for(timeout=T)
            why = page.get_by_test_id("decision-why")
            why.fill(P9_WHY.removeprefix("Why: "))
            prompt.press("Enter")
        body = created.value.json()
        decision_id = str(body["decision"]["id"])
        record_id = str(body["record"]["id"])
        decisions = page.locator(".intelligence-pullout:not(.today)")
        decisions.wait_for(timeout=T)
        detail = decisions.locator(".receipt-detail").filter(has_text=P9_DECISION_TEXT)
        detail.wait_for(timeout=T)
        assert P9_DECISION_TEXT in detail.inner_text()
        assert P9_PROJECT_NAME in detail.inner_text()
        assert P9_WHY.removeprefix("Why: ") in detail.inner_text()
        return decision_id, record_id, detail

    @staticmethod
    def _hit_and_focus(loc: Any) -> dict[str, Any]:
        return loc.evaluate(
            """(el) => {
                const describe = (node) => {
                  if (!(node instanceof HTMLElement)) return null;
                  const shell = node.closest('.desk-window-shell');
                  return {
                    tag: node.tagName,
                    className: node.className,
                    testid: node.getAttribute('data-testid'),
                    text: (node.innerText || node.textContent || '').trim().slice(0, 180),
                    html: node.outerHTML.slice(0, 500),
                    window: shell ? {
                      id: shell.id,
                      className: shell.className,
                      plane: shell.getAttribute('data-plane'),
                      zIndex: getComputedStyle(shell).zIndex,
                      rect: (() => { const sr = shell.getBoundingClientRect(); return {
                        left: sr.left, top: sr.top, right: sr.right, bottom: sr.bottom,
                        width: sr.width, height: sr.height,
                      }; })(),
                    } : null,
                  };
                };
                const r = el.getBoundingClientRect();
                const x = r.left + r.width / 2, y = r.top + r.height / 2;
                const hit = document.elementFromPoint(x, y);
                el.focus();
                return {
                  rect: {left: r.left, top: r.top, right: r.right, bottom: r.bottom,
                         width: r.width, height: r.height},
                  in_view: r.width > 0 && r.height > 0 && r.left >= 0 && r.top >= 0
                    && r.right <= innerWidth && r.bottom <= innerHeight,
                  owns_hit: hit === el || el.contains(hit),
                  focused: document.activeElement === el,
                  element: describe(el),
                  hit: describe(hit),
                  outer: [...document.querySelectorAll('.desk-window-shell')].map(describe),
                };
            }"""
        )

    def _open_room_again(self, page: Any, phone: bool) -> Any:
        return self._open_project(page, phone)

    @pytest.mark.e2e
    @pytest.mark.timeout(900)
    @pytest.mark.parametrize("width", list(SIZES))
    def test_new_decision_project_decisions_meeting_and_needs_confirm(
        self, width: int,
    ) -> None:
        from playwright.sync_api import sync_playwright

        phone = width <= 720
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # Open the real Project first, then use the Desk New Decision verb.
                room = self._open_project(page, phone)
                decision_id, record_id, detail = self._new_decision(page, phone)
                source_records = self._json(page, "GET", f"/api/decision-records/source/desk/{decision_id}")
                assert len(source_records) == 1, source_records
                assert str(source_records[0]["id"]) == record_id
                assert source_records[0]["decision_text"] == P9_DECISION_TEXT
                assert P9_ABOUT in str(source_records[0]["rationale"])
                assert P9_WHY in str(source_records[0]["rationale"])
                canonical_detail = self._json(page, "GET", f"/api/decision-records/{record_id}")
                assert any(s.get("source_type") == "project" and s.get("source_ref") == P9_PROJECT_ID
                           for s in canonical_detail.get("sources", [])), canonical_detail

                # The Project's real This week reads the canonical record and opens it.
                room = self._open_room_again(page, phone)
                this_week = room.get_by_test_id("room-this-week")
                this_week.wait_for(timeout=T)
                decided = this_week.get_by_test_id("this-week-decided").filter(has_text=P9_DECISION_TEXT)
                decided.wait_for(timeout=T)
                geometry = self._hit_and_focus(decided)
                assert geometry["in_view"] and geometry["owns_hit"] and geometry["focused"], geometry
                page.screenshot(path=str(P9_SHOTS / f"project-this-week-{width}.png"))
                decided.click()
                detail = page.locator(".receipt-detail").filter(has_text=P9_DECISION_TEXT)
                detail.wait_for(timeout=T)
                assert P9_DECISION_TEXT in detail.inner_text()
                detail_text = detail.inner_text()
                assert P9_PROJECT_NAME in detail_text
                assert P9_WHY.removeprefix("Why: ") in detail_text
                # Leave the record detail before opening another Desk surface.
                # On a phone the detail is a full sheet and otherwise owns the
                # Decisions row's hit point.
                detail_window = page.locator(
                    ".desk-window-shell.is-front[aria-label=" + json.dumps(P9_DECISION_TEXT) + "]"
                )
                detail_window.get_by_role("button", name=re.compile(r"^(Back from|Close) ")).click()
                detail_window.wait_for(state="detached", timeout=T)

                # The Decisions desk icon (Go ▸ Decisions) opens the same record.
                page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
                go = page.locator(".desk-verbbar-menu")
                go.get_by_role("menuitem", name="Decisions", exact=True).click()
                decisions_frame = page.locator("[id='surface-decisions']")
                page.locator("[id='surface-decisions'].is-front").wait_for(timeout=T)
                decisions_window = decisions_frame.get_by_test_id("decisions-window")
                decisions_window.wait_for(timeout=T)
                row = decisions_window.get_by_test_id("decisions-row").filter(has_text=P9_DECISION_TEXT)
                row.wait_for(timeout=T)
                geometry = self._hit_and_focus(row)
                assert geometry["in_view"] and geometry["owns_hit"] and geometry["focused"], json.dumps(geometry, sort_keys=True)
                row.click()
                desk_detail = decisions_window.locator(".receipt-detail").filter(has_text=P9_DECISION_TEXT)
                desk_detail.wait_for(timeout=T)
                assert P9_DECISION_TEXT in desk_detail.inner_text()
                desk_detail_text = desk_detail.inner_text()
                assert P9_PROJECT_NAME in desk_detail_text
                assert P9_WHY.removeprefix("Why: ") in desk_detail_text
                page.screenshot(path=str(P9_SHOTS / f"decisions-window-{width}.png"))
                decisions_surface = page.locator("#surface-decisions")
                decisions_surface.get_by_role("button", name=re.compile(r"^(Back from|Close) ")).click()
                decisions_surface.wait_for(state="detached", timeout=T)

                # The meeting's Decide well uses the same real desk producer.
                page.evaluate(
                    "([key, scope]) => sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify({key, scope}))",
                    ["review-meetings", f"meeting:{P9_MEETING_ID}"],
                )
                page.reload(wait_until="load")
                _normal_chair(page)
                meeting_window = page.locator("#surface-meetings")
                # The staged arrival restores the existing Meetings window;
                # use the real Go door to raise it after persisted windows
                # rehydrate at either width. Match the visible label so the
                # desktop keycap does not change the accessible name.
                page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
                page.locator(".desk-verbbar-menu").locator("[role^='menuitem']").filter(
                    has=page.locator(".desk-menu-label", has_text=re.compile(r"^Meetings$"))
                ).click()
                meeting_title = meeting_window.get_by_text("P9 decision review", exact=True)
                meeting_title.wait_for(state="attached", timeout=T)
                meeting_geometry = self._hit_and_focus(meeting_window)
                assert meeting_geometry["in_view"] and meeting_geometry["owns_hit"], json.dumps(meeting_geometry, sort_keys=True)
                meeting_window.get_by_role("button", name="More actions", exact=True).click()
                page.get_by_role("menuitem", name="Decide", exact=True).click()
                well = meeting_window.get_by_test_id("decide-naming")
                well.wait_for(timeout=T)
                with page.expect_response(
                    lambda response: response.request.method == "POST" and response.url.endswith("/api/decision-records/from-desk")
                ) as meeting_created:
                    title = well.get_by_role("textbox", name="Decision title", exact=True)
                    title.fill(P9_MEETING_DECISION)
                    title.press("Enter")
                meeting_body = meeting_created.value.json()
                meeting_decision_id = str(meeting_body["decision"]["id"])
                meeting_record = self._json(page, "GET", f"/api/decision-records/source/desk/{meeting_decision_id}")
                meeting_detail = self._json(page, "GET", f"/api/decision-records/{meeting_body['record']['id']}")
                assert len(meeting_record) == 1, meeting_record
                assert "Meeting: P9 decision review" in str(meeting_record[0]["rationale"])
                assert meeting_record[0]["decision_text"] == P9_MEETING_DECISION
                assert str(meeting_record[0]["id"]) == str(meeting_body["record"]["id"])
                assert any(s.get("source_type") == "meeting" and s.get("source_ref") == P9_MEETING_ID
                           for s in meeting_detail.get("sources", [])), meeting_detail
                page.get_by_test_id("decide-receipt").wait_for(timeout=T)
                assert page.get_by_test_id("decide-receipt").count() == 1
                page.screenshot(path=str(P9_SHOTS / f"meeting-decide-{width}.png"))

                # A proposed desk decision is offered as Confirm and reads back accepted.
                proposed = _api(page, "POST", "/api/decisions", {
                    "title": P9_PROPOSED,
                    "status": "proposed",
                    "decision_markdown": P9_PROPOSED,
                }, token=P9_TOKEN)
                proposed_id = str(proposed["decision"]["id"])
                proposed_source = self._json(page, "GET", f"/api/decision-records/source/desk/{proposed_id}")
                assert len(proposed_source) == 1, proposed_source
                proposed_record_id = str(proposed_source[0]["id"])
                assert proposed_source[0]["status"] == "proposed", proposed_source
                before_room = self._json(page, "GET", f"/api/projects/{P9_PROJECT_ID}/room")
                before_texts = [str(item.get("text", "")) for item in before_room.get("decisions", {}).get("items", [])]
                assert P9_PROPOSED not in before_texts, before_room
                assert self._json(page, "GET", f"/api/decision-records/{proposed_record_id}")["status"] == "proposed"
                needs_answer = self._json(page, "GET", "/api/desk/needs-you?fresh=1")
                needs_item = next(
                    (item for item in needs_answer.get("items", [])
                     if str(item.get("ref", "")) == f"decision:{proposed_id}"),
                    None,
                )
                assert needs_item is not None, needs_answer
                assert needs_item.get("status") == "proposed", needs_item
                # The admitted producer's desk_changed frame refreshes the
                # live Chair membership; let that real browser read settle.
                page.wait_for_timeout(700)
                needs = open_chair_window(page, "Needs you")
                proposed_row = needs.locator(
                    "[data-testid='needs-row'][data-object-id="
                    + json.dumps(f"decision:{proposed_id}") + "]"
                )
                proposed_row.wait_for(timeout=T)
                assert P9_PROPOSED in proposed_row.inner_text()
                confirm = proposed_row.get_by_role(
                    "button", name=f"Confirm: {P9_PROPOSED}", exact=True,
                )
                geometry = self._hit_and_focus(confirm)
                assert geometry["in_view"] and geometry["owns_hit"] and geometry["focused"], geometry
                with page.expect_response(
                    lambda response: response.request.method == "PUT"
                    and f"/api/decisions/{proposed_id}/status" in response.url
                ):
                    self._tap(page, confirm, phone)
                page.wait_for_timeout(500)
                assert _api(page, "GET", f"/api/decisions/{proposed_id}", token=P9_TOKEN)["decision"]["status"] == "accepted"
                after_record = self._json(page, "GET", f"/api/decision-records/{proposed_record_id}")
                assert str(after_record["id"]) == proposed_record_id
                assert after_record["status"] == "accepted", after_record
                after_room = self._json(page, "GET", f"/api/projects/{P9_PROJECT_ID}/room")
                after_texts = [str(item.get("text", "")) for item in after_room.get("decisions", {}).get("items", [])]
                # This proposal has no Project membership. The Room keeps
                # excluding it after Confirm; the canonical record/status
                # above is the durable proof of the same decision identity.
                assert P9_PROPOSED not in after_texts, after_room
                page.screenshot(path=str(P9_SHOTS / f"needs-confirm-{width}.png"))
                assert not [error for error in errors if "ResizeObserver" not in error and "Failed to fetch" not in error], errors
            finally:
                browser.close()


# ── PHILO-3-01 the write receipt's verbs own their areas ──
R_REPO = Path(__file__).resolve().parents[2]
R_SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-01-shots/receipt-hits")

_spec = importlib.util.spec_from_file_location("graph_walk_receipt_hits", R_REPO / "scripts/graph_walk.py")
gw = importlib.util.module_from_spec(_spec)
sys.modules["graph_walk_receipt_hits"] = gw
_spec.loader.exec_module(gw)

VIEWPORTS = {1440: {"width": 1440, "height": 900}, 393: {"width": 393, "height": 852}}

_GEOMETRY = """([id, hit]) => {
  const el = document.querySelector(`[data-probe="${id}"]`);
  const r = el.getBoundingClientRect();
  const halfW = Math.max(hit, r.width) / 2, halfH = Math.max(hit, r.height) / 2;
  const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
  return { painted: { w: r.width, h: r.height },
           area: { left: cx - halfW, right: cx + halfW, top: cy - halfH, bottom: cy + halfH },
           cx, cy, halfW, halfH,
           font: parseFloat(getComputedStyle(el).fontSize) };
}"""

_OWNS = """([id, x, y]) => {
""" + OWNERSHIP_JS + """
  const el = document.querySelector(`[data-probe="${id}"]`);
  const seen = hs202Classify(el, x, y);
  return { owner: seen.owner, outcome: seen.outcome };
}"""

# A window capture listener runs before React's root listener: it records
# which probed Button a real click reached and stops the product acting on it.
_TRAP = """() => {
  window.__fired = [];
  window.__trapOn = true;
  if (window.__trap) return;
  window.__trap = true;
  window.addEventListener('click', (e) => {
    if (!window.__trapOn) return;
    const b = e.target.closest && e.target.closest('[data-probe]');
    window.__fired.push(b ? b.dataset.probe : (e.target.className || e.target.tagName));
    e.stopPropagation(); e.preventDefault();
  }, true);
}"""


def _points(g: dict) -> list[tuple[float, float, str]]:
    out = []
    for fx, fy in PROBES:
        out.append((g["cx"] + fx * (g["halfW"] - 1), g["cy"] + fy * (g["halfH"] - 1),
                    {(0, 0): "center"}.get((fx, fy), f"({fx:+d},{fy:+d})")))
    return out


def _fault(page, method: str, prefix: str) -> None:
    def handler(route):
        req = route.request
        from urllib.parse import urlsplit
        if req.method == method and urlsplit(req.url).path.startswith(prefix):
            route.fulfill(status=500, content_type="application/json", body='{"error":"substituted"}')
        else:
            route.fallback()
    page.route("**/*", handler)


def _search(page, query: str, option: str) -> None:
    page.locator("[aria-controls=desk-tool-shelf]").click()
    page.locator("[aria-controls=desk-palette-listbox]").fill(query)
    page.locator(option).first.click()


def _probe(page, scope: str, name: str, width: int, failures: list[str]) -> None:
    receipt = page.locator(f"{scope} .write-receipt").first
    receipt.wait_for(state="visible", timeout=15000)
    # the receipt seats with an animation (write-receipt.css receipt-seat);
    # geometry read mid-flight is not the geometry a press meets
    receipt.evaluate("e => Promise.all(e.getAnimations({ subtree: true }).map(a => a.finished))")
    page.wait_for_timeout(100)
    label_px = receipt.locator(".write-receipt-label").evaluate("e => parseFloat(getComputedStyle(e).fontSize)")
    if label_px < 12:
        failures.append(f"{name}@{width}: label is {label_px}px, under the 12 px floor")
    ids = []
    for cls in ("write-receipt-retry", "write-receipt-dismiss"):
        pid = f"{name}-{cls}"
        receipt.locator(f".{cls}").evaluate(f"(e) => e.dataset.probe = '{pid}'")
        ids.append(pid)
    page.evaluate(_TRAP)
    hit = 44 if width <= 420 else 0
    geo = {i: page.evaluate(_GEOMETRY, [i, hit]) for i in ids}
    for i in ids:
        g = geo[i]
        if g["font"] < 12:
            failures.append(f"{i}@{width}: verb is {g['font']}px, under the 12 px floor")
        for x, y, where in _points(g):
            if not (0 <= x < VIEWPORTS[width]["width"] and 0 <= y < VIEWPORTS[width]["height"]):
                failures.append(f"{i}@{width}: {where} ({x:.1f},{y:.1f}) is off the screen")
                continue
            seen = page.evaluate(_OWNS, [i, x, y])
            if seen["outcome"] != "own":
                stack = page.evaluate(
                    "([x, y, id]) => { const el = document.querySelector(`[data-probe=\"${id}\"]`);"
                    " const r = el.getBoundingClientRect(); const a = getComputedStyle(el, '::after');"
                    " return { stack: document.elementsFromPoint(x, y).slice(0, 4).map(e => (e.className || e.tagName).toString().slice(0, 40)),"
                    " face: [r.top, r.bottom], halo: [a.content, a.height] }; }", [x, y, i])
                failures.append(f"{i}@{width}: {where} ({x:.1f},{y:.1f}) -> {seen['owner']!r} [{seen['outcome']}] {stack}")
                continue
            page.evaluate("window.__fired = []")
            page.mouse.click(x, y)
            fired = page.evaluate("window.__fired")
            if fired != [i]:
                failures.append(f"{i}@{width}: a real pointer at {where} reached {fired!r}")
    if _overlap(geo[ids[0]]["area"], geo[ids[1]]["area"]):
        failures.append(f"{name}@{width}: Retry and OK areas intersect")
    R_SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(R_SHOTS / f"{name}-{width}.png"))


def _row_law(page, failures: list[str]) -> None:
    """The row is in the flow between the bar and the work, full width, its
    label whole; the Chair starts below it; the bar holds no receipt."""
    fact = page.evaluate("""() => {
      const row = document.querySelector('.desk-receipt-row');
      const bar = document.querySelector('.desk-menubar');
      const chair = document.querySelector('.chair');
      const label = row.querySelector('.write-receipt-label');
      const rr = row.getBoundingClientRect(), br = bar.getBoundingClientRect();
      const cr = chair ? chair.getBoundingClientRect() : null;
      return { position: getComputedStyle(row).position, rowTop: rr.top, rowBottom: rr.bottom,
               rowLeft: rr.left, rowRight: rr.right, barBottom: br.bottom, vw: innerWidth,
               chairTop: cr && cr.top, labelClipped: label.scrollWidth > label.clientWidth + 1,
               labelFont: parseFloat(getComputedStyle(label).fontSize),
               barReceipt: !!document.querySelector('.desk-menubar .write-receipt') };
    }""")
    if fact["position"] not in ("static", "relative"):
        failures.append(f"row@393: position {fact['position']}, not in the flow")
    if fact["rowTop"] < fact["barBottom"]:
        failures.append(f"row@393: top {fact['rowTop']} is under the bar ({fact['barBottom']})")
    if fact["rowLeft"] > 16.5 or fact["rowRight"] < fact["vw"] - 16.5:
        failures.append(f"row@393: {fact['rowLeft']}..{fact['rowRight']} is not full width")
    if fact["chairTop"] is not None and fact["chairTop"] < fact["rowBottom"]:
        failures.append(f"row@393: the Chair starts at {fact['chairTop']}, inside the row")
    if fact["labelClipped"]:
        failures.append("row@393: the label is cut")
    if fact["barReceipt"]:
        failures.append("row@393: the bar still holds a receipt")


def _band_law(page, when: str, failures: list[str]) -> None:
    """The Chair's work band holds with or without the row (the constraints of
    tests/e2e/test_hs141_chair_geometry.py:93): the Chair ends at the band's
    bottom, the capture bar sits above the dock, and the document does not
    grow past the screen."""
    g = page.evaluate("""() => {
      const chair = document.querySelector('.chair');
      // PHILO-13-11 (slice two, R2): at 393 the Chair is one window at a time
      // (Needs you first; the capture bar is the Capture window, on demand
      // from Speak): the shown Chair window is the surface that must end
      // above the dock.
      // PHILO-14 A1: with no Chair window open, the screen of objects is
      // that surface.
      const bar = document.querySelector('[data-testid="arrival-capture-bar"]')
        || document.querySelector('.desk-window.chair-window.is-sheet')
        || document.querySelector('.desk-screen');
      const dock = document.querySelector('.desk-dock');
      const style = getComputedStyle(document.documentElement);
      return { chairBottom: chair.getBoundingClientRect().bottom,
               chairHeight: chair.getBoundingClientRect().height,
               barBottom: bar ? bar.getBoundingClientRect().bottom : null,
               dockTop: dock ? dock.getBoundingClientRect().top : null,
               vh: innerHeight,
               workBottom: parseFloat(style.getPropertyValue('--desk-work-bottom')),
               scrollHeight: document.scrollingElement.scrollHeight };
    }""")
    if g["chairBottom"] > g["vh"] - g["workBottom"] + 0.5:
        failures.append(f"band@393 ({when}): the Chair ends at {g['chairBottom']:.1f}, past the band ({g['vh'] - g['workBottom']}); {g}")
    if g["barBottom"] is None or g["dockTop"] is None:
        failures.append(f"band@393 ({when}): no capture bar or no dock to measure; {g}")
    elif g["barBottom"] > g["dockTop"]:
        failures.append(f"band@393 ({when}): the capture bar ends at {g['barBottom']:.1f}, under the dock ({g['dockTop']:.1f})")
    if g["scrollHeight"] > g["vh"]:
        failures.append(f"band@393 ({when}): the document is {g['scrollHeight']} px, taller than the screen ({g['vh']})")


@pytest.fixture(scope="module")
def receipt_hub():
    home = Path(tempfile.mkdtemp(prefix="philo3-receipt-hits-"))
    h = gw.Hub(home).start()
    try:
        yield h
    finally:
        h.stop()


@pytest.mark.timeout(600, method="thread")
@pytest.mark.parametrize("width", [1440, 393])
def test_receipt_verbs_own_their_areas(receipt_hub, width: int) -> None:
    """replaces: tests/e2e/test_philo3_01_receipt_hits.py::test_receipt_verbs_own_their_areas (moved whole: nine points to elementFromPoint and a real pointer)."""
    from playwright.sync_api import sync_playwright

    failures: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport=VIEWPORTS[width])
        page.emulate_media(reduced_motion="reduce")
        page.goto(f"{receipt_hub.url}/?token={receipt_hub.token}")
        # PHILO-16 (16b): one hub is one desk; this page starts on an empty desk.
        from .glass_infra import clear_hub_windows

        clear_hub_windows(page, receipt_hub.token)
        page.reload()
        _normal_chair(page)
        page.locator("[aria-controls=desk-tool-shelf]").wait_for(timeout=15000)

        # 1. the chrome receipt (the desk backstop)
        _fault(page, "POST", "/api/decision-records/from-desk")
        _search(page, "New Decision", "[id='desk-palette-option-desk.new-decision']")
        # PHILO-13-08 (B3): the decision is named before it is created; the
        # refused POST is the named one.
        page.get_by_test_id("palette-name").fill("Adopt the one bus")
        page.keyboard.press("Enter")
        # the owner's ruling (2026-09-23): at phone width the backstop is a
        # full-width row in the desk flow, not a seat in the bar
        seat = ".desk-receipt-row" if width <= 720 else ".desk-chrome-receipt"
        _probe(page, seat, "chrome", width, failures)
        if width <= 720:
            _row_law(page, failures)
            _band_law(page, "row standing", failures)
            # clear it for real: OK, not the trap
            page.evaluate("window.__trapOn = false")
            page.locator(".desk-receipt-row .write-receipt-dismiss").click()
            page.locator(".desk-receipt-row").wait_for(state="detached", timeout=5000)
            page.wait_for_timeout(200)
            _band_law(page, "row cleared", failures)
        page.unroute("**/*")
        page.reload()
        page.locator("[aria-controls=desk-tool-shelf]").wait_for(timeout=15000)

        # 2. (Betterment Q4: the Thread window and its Rename are parked;
        # threads open in Ask, which has no rename.)

        # 3. (parked by Betterment daily D4) the Brief wing's footer receipt:
        # Today is one page and the wing (Acknowledge, its footer) is parked;
        # the leg is in tests/e2e/_parked/test_desk_glass_brief_footer_leg.py.
        browser.close()
    assert not failures, "\n".join(failures)


# ── PHILO-9-04 selection contrast in the note editor and the thread composer ──
S_TOKEN = "philo9-04-desk-debts"
S_SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-shots")
WIDTHS = list(SIZES)
NOTES = ["Ledger cutover plan", "Priya 1:1 notes", "Tomas growth plan", "Vendor risk list",
         "Q4 capacity", "Incident review 42",
         "A very long note title that names the whole architecture decision record for the card ledger"]

# The canvas harness's colour helpers (shoot.py COLOR_JS).
COLOR_JS = r"""
window.__c = (() => {
  const parse = (css) => {
    const m = css.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);
    return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1};
  };
  const over = (top, under) => ({
    r: top.a * top.r + (1 - top.a) * under.r, g: top.a * top.g + (1 - top.a) * under.g,
    b: top.a * top.b + (1 - top.a) * under.b, a: 1});
  const ground = (el) => {
    const layers = [];
    for (let e = el; e; e = e.parentElement) {
      const c = parse(getComputedStyle(e).backgroundColor);
      if (c && c.a > 0) { layers.push(c); if (c.a >= 1) break; }
    }
    let base = {r: 14, g: 15, b: 19, a: 1};
    for (let i = layers.length - 1; i >= 0; i--) base = over(layers[i], base);
    return base;
  };
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return +((x + 0.05) / (y + 0.05)).toFixed(2); };
  const hex = (c) => `rgb(${Math.round(c.r)},${Math.round(c.g)},${Math.round(c.b)})`;
  return {parse, over, ground, ratio, hex};
})();
"""

S_ICON = ".desk-screen .desk-icon[aria-label^='Ledger cutover plan']"

HOSTS = r"""(scope) => {
  const C = window.__c;
  const root = document.querySelector(scope);
  if (!root) return null;
  return [...root.querySelectorAll('input:not([type=hidden]):not([type=checkbox]):not([type=radio]), textarea, .cm-line')]
    .filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .map(e => {
      const s = getComputedStyle(e, '::selection');
      const g = C.ground(e);
      const p = C.over(C.parse(s.backgroundColor) || {r: 0, g: 0, b: 0, a: 0}, g);
      const ink = C.over(C.parse(s.color), p);
      return {host: e.classList.contains('cm-line') ? 'codemirror' : e.tagName.toLowerCase(),
        cls: String(e.className).slice(0, 50), selection_bg: s.backgroundColor, selection_ink: s.color,
        ground: C.hex(g), selection_vs_ground: C.ratio(p, g), selected_text_vs_selection: C.ratio(ink, p)};
    });
}"""


def _record(name: str, width: int, data: Any) -> None:
    (S_SHOTS / f"{name}-{width}.json").write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


class TestDeskDebtsGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=S_TOKEN)
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _open(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1)
        ctx.add_init_script(COLOR_JS)
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={S_TOKEN}", wait_until="load")
        self._seed(page)
        page.reload(wait_until="load")
        _normal_chair(page)
        # The probe note is filed in Payments, so it is not a loose Screen
        # icon. Search opens the exact filed note at both widths.
        _search(page, NOTES[0], f"[id='desk-palette-option-note:{self.note_id}']")
        page.get_by_role("region", name=NOTES[0], exact=True).wait_for(timeout=T)
        page.wait_for_timeout(1200)
        return browser, page, errors

    def _seed(self, page: Any) -> None:
        """The grounding probe's objects (d2_probe.py.txt), and a real Attention:
        a GitHub proposal under the NEUTRAL mode waits `proposed` and is never
        executed; the projection counts it as needs_attention on the note."""
        zones = [_api(page, "POST", "/api/directories", {"name": n}, token=S_TOKEN)
                 for n in ("Payments", "Hiring", "Architecture reviews")]
        notes = [_api(page, "POST", "/api/notes", {"title": t, "body": t}, token=S_TOKEN) for t in NOTES]
        zid = (zones[0].get("directory") or zones[0])["id"]
        nid = (notes[0].get("note") or notes[0])["id"]
        self.note_id = nid
        _api(page, "PUT", f"/api/directories/{zid}/members/note:{nid}", {}, token=S_TOKEN)
        _api(page, "PUT", "/api/authority/control-mode", {"control_mode": "neutral"}, token=S_TOKEN)
        _api(page, "POST", "/api/desk/actuators/github/propose",
             {"text": "Check the ledger cutover plan", "repo": "example/payments", "source_ref": f"note:{nid}"},
             token=S_TOKEN)
        counts = _api(page, "GET", "/api/desk/projections?limit=50", token=S_TOKEN).get("subject_counts", {})
        assert counts.get(f"note:{nid}", {}).get("needs_attention") == 1, counts

    def _open_note_editor(self, page: Any) -> Any:
        self._note_object_menu(page).get_by_role("menuitem", name="Edit", exact=True).click()
        editor = page.locator(".cm-content").first
        editor.wait_for(timeout=T)
        return editor

    @staticmethod
    def _note_object_menu(page: Any) -> Any:
        note = page.get_by_role("region", name=NOTES[0], exact=True)
        note.locator(":scope > .desk-pullout-head").click(button="right")
        menu = page.locator(".desk-head-menu")
        menu.wait_for(timeout=T)
        menu.get_by_role("menuitem", name="Object", exact=True).click()
        return menu

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_editor_selection_is_readable(self, width: int) -> None:
        """replaces: tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_editor_selection_is_readable (moved whole: the ::selection colours, computed)."""
        """Finding 1: selected note text in the CodeMirror editor reads 4.5:1
        or more on a selection that reads 3:1 against the editor (red at
        f58cb5b0: 1.33:1, the tint ground under the page ink). The census
        covers every selection host in the open editor window: the title
        field, the body lines, the tags field."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                editor = self._open_note_editor(page)
                editor.fill("Review the ledger cutover plan with Priya.")
                editor.click()
                page.keyboard.press("ControlOrMeta+a")
                # The shot before the editor's AI bar opens over a selection
                # (EditorAIBar; at 393 it covers the body: BACKLOG
                # "PHILO-9-04 follow-ups"), and one after it.
                page.wait_for_timeout(60)
                page.screenshot(path=str(S_SHOTS / f"editor-selected-{width}.png"))
                page.wait_for_timeout(300)
                page.screenshot(path=str(S_SHOTS / f"editor-selected-aibar-{width}.png"))
                selected = page.evaluate("window.getSelection().toString()")
                window = page.evaluate(HOSTS, ".desk-window:has(.cm-content)") or []
                _record("editor-selection", width, {"selected": selected, "hosts": window})
                assert "ledger cutover" in selected, selected
                cm = [h for h in window if h["host"] == "codemirror"]
                assert cm, window
                for h in window:
                    assert h["selected_text_vs_selection"] >= 4.5, h
                    assert h["selection_vs_ground"] >= 3.0, h
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_thread_composer_selection_is_readable(self, width: int) -> None:
        """replaces: tests/e2e/test_philo9_04_desk_debts_glass.py::TestDeskDebtsGlass::test_the_thread_composer_selection_is_readable (moved whole: the ::selection colours, computed)."""
        """Finding 1's census: the thread composer's textarea (the draft
        field; row menu > Ask about this, Betterment Q5) takes the same pair."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                self._note_object_menu(page).get_by_role(
                    "menuitem", name="Ask about this", exact=True).click()
                area = page.locator("textarea").first
                area.wait_for(timeout=T)
                area.fill("Ask Priya about the cutover date")
                area.evaluate("e => { e.focus(); e.select(); }")
                page.wait_for_timeout(300)
                hosts = [h for h in page.evaluate(HOSTS, "body") if h["host"] == "textarea"]
                page.screenshot(path=str(S_SHOTS / f"composer-selected-{width}.png"))
                _record("composer-selection", width, {"hosts": hosts})
                assert hosts, "no textarea measured"
                for h in hosts:
                    assert h["selected_text_vs_selection"] >= 4.5, h
                    assert h["selection_vs_ground"] >= 3.0, h
                assert not errors, errors
            finally:
                browser.close()
