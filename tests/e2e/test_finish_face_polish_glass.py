"""The finish-polish face fixes (pm/STATUS.md open rows), fenced AS RENDERED.

Through the real hub on an isolated HOME and the built bundle, at 1440x900
(mouse) and 393x852 (touch), on a desk with five projects, a saved folder in
the HOME and a decision:

* Dock (393): every page of the shelf starts and ends on a whole AppIcon. No
  strip of the icon before a page shows in the left gutter, and no strip of
  the next AppIcon shows beside More (it was 4 px + 1 px: "a 5 px strip").
* Chair (1440, C1-4e): a Chair window zoomed, unzoomed, closed and opened
  again from Window > Chair comes back at its tile place (it came back 12 px
  low, clamped into the shell band).
* Roadmap: the palette's Roadmap row opens the roadmap by its name with its
  phases (it opened `roadmap:<slug>` and "Roadmap not found").
* Calendar: a snapshot with no vision model reads CAN'T READ and a plain
  reason, never `no_vision_model_assigned`.
* Palette: "send" finds no row by letters spread over its words ("Close
  window"), and the built-in folder is a DESTINATION, not NOT CONFIGURED.
* Paths: the SEND well and Connections show a saved folder in the HOME as
  ~/..., and Setup shows the config file as ~/...; no face prints the HOME.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the finish-polish glass needs Playwright")

TOKEN = "finish-polish-glass"
SHOTS = evidence_dir("tests/e2e/shots/finish-face-polish")
SIZES = {1440: 900, 393: 852}
PROJECTS = ("Payments ledger cutover", "Platform observability", "Staff hiring loop",
            "Search relevance", "Mobile release train")
PNG_1PX = Path(__file__).with_name("finish_polish_1px.png")

# Every launcher and strip item that crosses the shelf's left gutter or the
# More gadget's left edge on the page in view.
SHELF_PAGE = """() => {
  const d = document.querySelector('.desk-dock');
  const more = d.querySelector('.desk-dock-more').getBoundingClientRect();
  const gutter = d.getBoundingClientRect().left + 4;
  const atEnd = d.scrollLeft >= d.scrollWidth - d.clientWidth - 1;
  const out = {scrollLeft: d.scrollLeft, atEnd, left: [], right: []};
  for (const k of d.children) {
    if (k.classList.contains('desk-dock-more') || getComputedStyle(k).display === 'none') continue;
    const b = k.getBoundingClientRect();
    const name = k.getAttribute('aria-label') || k.className;
    if (b.left < gutter - 0.5 && b.right > gutter + 0.5) out.left.push([name, Math.round(b.right - gutter)]);
    if (k.classList.contains('desk-dock-launch') && b.left < more.left - 0.5 && b.right > more.left + 0.5)
      out.right.push([name, Math.round(more.left - b.left)]);
  }
  return out;
}"""


class TestFinishFacePolish:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        root = tmp_path.resolve()
        server, base = _boot(root, monkeypatch, token=TOKEN)
        self.server, self.base, self.home = server, base, root / "home"
        from holdspeak.db import get_database
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.primitive_service import PrimitiveService

        self.db = get_database()
        for n, name in enumerate(PROJECTS):
            self.db.projects.create_project(project_id=f"p-{n}", name=name, description=name,
                                            keywords=name.lower().split()[:2])
        PrimitiveService(self.db).create_decision(
            Principal(PrincipalKind.OWNER, "karol"), decision_id="d-freeze",
            title="Freeze the old ledger on Nov 5", status="accepted",
            decision_markdown="Freeze writes to the old ledger on Nov 5.")
        try:
            yield
        finally:
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                  has_touch=width < 720, reduced_motion="reduce")
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.locator(".desk-dock").wait_for()
        page.wait_for_timeout(1200)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    def _palette(self, page: Any, text: str) -> list[tuple[str, str]]:
        page.locator(".desk-tools-launch").first.click()
        field = page.locator("input[placeholder='Search tools and Desk items']")
        field.wait_for()
        field.fill(text)
        page.wait_for_timeout(600)
        return [tuple(r) for r in page.evaluate("""() => [...document.querySelectorAll('[id^="desk-palette-option-"]')]
            .map((e) => [e.id.replace('desk-palette-option-', ''), e.innerText.replace(/\\s+/g, ' ').trim()])""")]

    def _home_forms(self) -> set[str]:
        return {str(self.home), os.path.realpath(self.home)}

    # ── the fences ───────────────────────────────────────────────────────

    @pytest.mark.e2e
    def test_the_phone_dock_pages_on_whole_icons(self) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 393)
            try:
                pages = [page.evaluate(SHELF_PAGE)]
                page.screenshot(path=str(SHOTS / "dock-home-393.png"))
                more = page.get_by_role("button", name="More AppIcons")
                for n in range(1, 8):
                    self._press(page, more, 393)
                    page.wait_for_timeout(900)
                    state = page.evaluate(SHELF_PAGE)
                    page.screenshot(path=str(SHOTS / f"dock-page{n}-393.png"))
                    if state["scrollLeft"] == 0:
                        break
                    pages.append(state)
                assert len(pages) >= 3, pages  # five projects: the shelf has pages
                for state in pages:
                    assert not state["right"], f"a strip of the next AppIcon beside More: {state}"
                    if not state["atEnd"]:
                        assert not state["left"], f"a strip of the icon before this page: {state}"
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    def test_a_chair_window_reopens_at_its_tile_place_after_a_zoom(self) -> None:
        from playwright.sync_api import sync_playwright

        rect = """() => { const b = document.querySelector(".desk-window-shell.chair-window[aria-label='Brief']").getBoundingClientRect();
                          return [Math.round(b.left), Math.round(b.top), Math.round(b.width), Math.round(b.height)]; }"""
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                shell = page.locator(".desk-window-shell.chair-window[aria-label='Brief']")
                home = page.evaluate(rect)
                shell.get_by_role("button", name="Zoom Brief").click()
                page.wait_for_timeout(500)
                shell.get_by_role("button", name="Zoom Brief").click()
                page.wait_for_timeout(500)
                assert page.evaluate(rect) == home
                shell.get_by_role("button", name="Close Brief").click()
                shell.wait_for(state="detached")
                page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
                page.locator(".desk-verbbar-menu").wait_for()
                page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Chair')").hover()
                page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Brief')").click()
                shell.wait_for()
                page.wait_for_timeout(600)
                _settle(page)
                page.screenshot(path=str(SHOTS / "chair-reopened-1440.png"))
                assert page.evaluate(rect) == home, (page.evaluate(rect), home)
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_named_faces_say_names_and_plain_reasons(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        folder = self.home / "Documents" / "HoldSpeak" / "Team updates"
        folder.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                _api(page, "POST", "/api/channels/destinations",
                     {"name": "Team updates", "channel": "file", "folder": str(folder)}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1500)

                # Palette: "send" finds no scattered-letter rows; the built-in folder is set up.
                rows = self._palette(page, "send")
                page.screenshot(path=str(SHOTS / f"palette-send-{width}.png"))
                labels = [label for _id, label in rows]
                assert not any(re.search(r"Close window|Overview|Speak PROGRAM|Rhythm", label) for label in labels), labels
                folder_row = [label for rid, label in rows if rid == "integration:channel:holdspeak-folder"]
                assert folder_row and "NOT CONFIGURED" not in folder_row[0], rows

                # Roadmap: opened by its name, with its phases.
                field = page.locator("input[placeholder='Search tools and Desk items']")
                field.fill("HoldSpeak Roadmap")
                page.wait_for_timeout(600)
                roadmap = page.locator("[id^='desk-palette-option-roadmap:']").first
                roadmap.wait_for()
                self._press(page, roadmap, width)
                window = page.locator(".desk-roadmap-window")
                window.wait_for()
                window.locator(".desk-roadmap-phases").wait_for(timeout=20_000)
                _settle(page)
                page.screenshot(path=str(SHOTS / f"roadmap-{width}.png"))
                text = window.inner_text()
                assert "Roadmap not found" not in text and "roadmap:" not in text, text[:300]
                assert page.locator(".desk-screen-name").inner_text().strip().startswith("HoldSpeak"), \
                    page.locator(".desk-screen-name").inner_text()
                self._press(page, window.locator("button[aria-label^='Close ']").first, width)
                window.wait_for(state="detached")

                # The SEND well of a decision: the saved folder reads ~/...
                self._palette(page, "freeze")
                row = page.locator("[id^='desk-palette-option-']", has_text="Freeze the old ledger").first
                self._press(page, row, width)
                well = page.get_by_text("~/Documents/HoldSpeak/Team updates").first
                well.wait_for(timeout=20_000)
                _settle(page)
                page.screenshot(path=str(SHOTS / f"send-well-{width}.png"))
                body = page.inner_text("body")
                for home in self._home_forms():
                    assert home not in body, f"the HOME on a face: {home}"

                # Calendar: Settings, Meetings, Snapshot with no vision model.
                self._palette(page, "meetings")
                self._press(page, page.locator("[id='desk-palette-option-settings:meetings']"), width)
                snap = page.get_by_role("button", name="Snapshot", exact=True)
                snap.wait_for(timeout=20_000)
                snap.scroll_into_view_if_needed()
                with page.expect_file_chooser() as chooser:
                    snap.click()
                chooser.value.set_files(str(PNG_1PX))
                refusal = page.get_by_test_id("calendar-snapshot-refusal")
                refusal.wait_for(timeout=20_000)
                _settle(page)
                page.screenshot(path=str(SHOTS / f"calendar-refusal-{width}.png"))
                said = refusal.inner_text().replace("\n", " ")
                assert "CAN'T READ" in said and "_" not in said, said

                # Setup: the config file reads ~/...; no HOME on the face.
                self._palette(page, "setup")
                self._press(page, page.locator("[id^='desk-palette-option-']", has_text="Setup").first, width)
                page.get_by_text("READINESS CHECKS", exact=False).first.wait_for(timeout=20_000)
                # The Config row is drawn (its path is ~/... when it is under the HOME;
                # tests/unit/test_face_paths_short.py proves the ~ itself).
                page.get_by_text("config version", exact=False).first.wait_for(timeout=20_000)
                _settle(page)
                page.screenshot(path=str(SHOTS / f"setup-{width}.png"))
                body = page.inner_text("body")
                for home in self._home_forms():
                    assert home not in body, f"the HOME on Setup: {home}"
                assert "same_device" not in body
                assert not errors, errors
            finally:
                browser.close()
