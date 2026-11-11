"""The Automations app, AS RENDERED: what only a real browser proves.

Betterment A5 (docs/internal/betterment/workbench/RECIPE.md): a desk object
dropped on the automation window becomes an About chip. The drop is a real
HTML drag from the Screen's note icon (the hand's drag: `hand/drag.ts`) onto
the window, through the real hub on an isolated HOME at 1440 x 900. The
phone (393) has no loose Screen icons to drag; its About is the picker
(web/src/desk/__tests__/automation.app.test.tsx).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the automation glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "automation-glass"
SHOTS = evidence_dir("automation-about")
T = 20_000
NOTE_ID, NOTE = "n-platform", "Platform sync notes"
WB = "wb-glass-about"
SIZES = {1440: 900, 393: 852}
ICON = f".desk-screen [data-object-id='note:{NOTE_ID}']"


def _automation_verb(page: Any, label: str) -> None:
    app = page.locator("#surface-workbenches")
    app.get_by_role("grid", name="Automations", exact=True).wait_for()
    new = app.get_by_role("button", name=label, exact=True)
    if new.is_visible():
        new.click()
    else:
        app.get_by_role("button", name="Actions ▾", exact=True).click()
        page.get_by_role("menuitem", name=re.compile("^" + re.escape(label))).click()


def _new_automation(page: Any) -> None:
    _automation_verb(page, "New automation")


def _object_verb(page: Any, window: Any, label: str) -> None:
    window.get_by_test_id("automation-toolbar").wait_for(state="visible")
    direct = window.get_by_role("button", name=label, exact=True)
    if direct.count() and direct.is_visible(): direct.click()
    else:
        window.get_by_role("button", name="Actions ▾", exact=True).click()
        page.get_by_role("menu").last.get_by_role("menuitem", name=label, exact=True).click()


def _object_edit(page: Any, window: Any, part: str) -> None:
    _object_verb(page, window, "Edit")
    window.get_by_test_id("automation-setup").wait_for()
    window.get_by_role("tab", name=part, exact=True).click()


class TestAboutDrop:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        from holdspeak.db import get_database
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.primitive_service import PrimitiveService

        self.db = get_database()
        owner = Principal(PrincipalKind.OWNER, "karol")
        PrimitiveService(self.db).create_note(
            owner, note_id=NOTE_ID, title=NOTE, body_markdown="The cutover moves to Thursday.", tags=[])
        self.db.workbenches.upsert(workbench_id=WB, name="Friday team update",
                                   instruction="Draft my team update.")
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int = 1440) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                  has_touch=width < 720, reduced_motion="reduce")
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        page.goto(f"{self.base}/?token={TOKEN}&open=workbench:{WB}", wait_until="load")
        _normal_chair(page)
        if width >= 720:
            page.locator(ICON).wait_for(timeout=T)
        page.get_by_test_id("automation-window").wait_for(timeout=T)
        return browser, page, errors

    def test_1440_a_floor_note_dropped_on_the_window_becomes_an_about_chip(self) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw)
            try:
                about = page.get_by_test_id("automation-summary")
                assert "Platform sync notes" not in about.inner_text()
                window = page.get_by_test_id("automation-window")
                # The window opens over the Screen's icons: move it by its
                # title strip until the note's icon is clear.
                icon_box = page.locator(ICON).bounding_box()
                frame = page.locator(f"[id='workbench:{WB}']")
                box = frame.bounding_box()
                assert icon_box and box
                # Sideways: a window stops above the dock (windowGeometry.ts
                # workBand), and since the floating dock (#1497, #1514) a
                # 680 px window at 900 px cannot drop below the icon's foot.
                grab = (box["x"] + 120, box["y"] + 12)
                shift = max(0.0, icon_box["x"] + icon_box["width"] + 24 - box["x"])
                page.mouse.move(*grab)
                page.mouse.down()
                page.mouse.move(grab[0] + shift / 2, grab[1], steps=6)
                page.mouse.move(grab[0] + shift, grab[1], steps=6)
                page.mouse.up()
                moved = frame.bounding_box()
                assert moved and moved["x"] > icon_box["x"] + icon_box["width"], (icon_box, moved)
                with page.expect_response(lambda r: r.url.endswith(f"/api/workbenches/{WB}")
                                          and r.request.method == "PUT") as kept:
                    page.locator(ICON).drag_to(window)
                assert kept.value.ok, kept.value.text()
                assert (kept.value.request.post_data_json or {}).get("sources") == [f"note:{NOTE_ID}"]
                about.get_by_text(NOTE, exact=True).wait_for(timeout=T)
                assert self.db.workbenches.get(WB).sources_json == f'["note:{NOTE_ID}"]'
                page.screenshot(path=str(SHOTS / "about-drop-1440.png"))
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", [1440, 393])
    def test_typing_plat_finds_the_note_and_one_press_adds_its_chip(self, width: int) -> None:
        """Done when (A5): adding "Platform sync notes" by typing "plat" takes
        2 presses (the About line, then the match), at 1440 and 393."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                about = page.get_by_test_id("automation-summary")
                _object_edit(page, page.get_by_test_id("automation-window"), "About")
                well = page.get_by_role("textbox", name="Find by name")
                well.fill("plat")
                with page.expect_response(lambda r: r.url.endswith(f"/api/workbenches/{WB}")
                                          and r.request.method == "PUT") as kept:
                    page.get_by_role("row",name=NOTE,exact=True).dblclick()
                assert (kept.value.request.post_data_json or {}).get("sources") == [f"note:{NOTE_ID}"]
                page.get_by_role("checkbox", name=NOTE, exact=True).wait_for(timeout=T)
                assert well.input_value() == "plat"  # typed text is never deleted
                page.screenshot(path=str(SHOTS / f"about-picker-{width}.png"))
                assert not errors, errors
            finally:
                browser.close()


class TestFridayWalk:
    """Betterment A7, DESIGN §6: New automation → starter → Create → Open → With →
    Claude Code → Run now → a readable result, in at most 6 presses, in one
    window, at 1440 and 393. Claude Code is the fake CLI of
    tests/fixtures/fake_agent_cli.py (never the owner's own)."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        from holdspeak.intel.cli_engine import CLI_ENGINES_ENV
        from tests.fixtures.fake_agent_cli import install_fake_agent_clis, path_with, set_claude_answer

        bin_dir = install_fake_agent_clis(tmp_path / "bin")
        set_claude_answer(bin_dir, "## Team update, this week\n\n- Shipped: the rollback runbook.\n"
                                   "- Slipped: the ledger cutover moves to Thursday.\n- From Mira: the review.")
        monkeypatch.setenv("PATH", path_with(bin_dir))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        # The rig turns agent CLIs off; this walk turns them on, with the fake.
        monkeypatch.setenv(CLI_ENGINES_ENV, "on")
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("width", [1440, 393])
    def test_friday_team_update_keeps_setup_and_opens_its_result(self, width: int) -> None:
        import time

        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                      has_touch=width < 720, reduced_motion="reduce")
            page = ctx.new_page()
            page.set_default_timeout(45_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                # Find it (A1, one press; not counted): Go ▸ Automations.
                page.get_by_role("button", name="Go", exact=True).first.click()
                go = page.locator("nav[aria-label='Go menu']")
                go.wait_for(timeout=T)
                go.get_by_role("menuitem", name="Automations").first.evaluate("el => el.click()")
                page.locator("#surface-workbenches").get_by_role("grid", name="Automations", exact=True).wait_for(timeout=T)
                page.screenshot(path=str(SHOTS / f"walk-0-home-{width}.png"))

                started = time.monotonic()
                _new_automation(page)
                app = page.locator("#surface-workbenches")
                app.get_by_role("combobox", name="Automation starter").select_option("friday-team-update")
                page.screenshot(path=str(SHOTS / f"walk-1-new-{width}.png"))
                with page.expect_response(lambda r: r.url.endswith("/api/workbench-templates/friday-team-update/instantiate") and r.request.method == "POST") as made:
                    app.get_by_role("button", name="Create", exact=True).click()
                workbench_id = made.value.json()["workbench"]["id"]
                app.get_by_test_id("automation-setup").wait_for(timeout=T)
                app.get_by_role("button", name="Cancel", exact=True).click()
                app.get_by_role("row", name=re.compile("^Friday team update")).dblclick()
                window = page.locator(f'[id="workbench:{workbench_id}"]')
                window.get_by_test_id("automation-summary").wait_for(timeout=T)
                _object_edit(page, window, "With")
                engine = window.get_by_role("combobox",name="With",exact=True)
                engine.select_option(label="Add Claude Code")
                window.get_by_role("button",name="Save",exact=True).click()
                window.get_by_test_id("automation-summary").wait_for(timeout=T)
                _object_verb(page, window, "Run now")
                reading = window.get_by_test_id("automation-reading")
                reading.get_by_role("heading", name="Team update, this week").wait_for(timeout=60_000)
                seconds = time.monotonic() - started
                reading.scroll_into_view_if_needed()
                page.screenshot(path=str(SHOTS / f"walk-3-result-{width}.png"))
                # The native face at rest: With folded, the mast, the plate
                # and the ledger of runs from the top.
                assert "##" not in reading.inner_text()
                window.get_by_role("tab",name="About",exact=True).click()
                page.screenshot(path=str(SHOTS / f"walk-4-native-{width}.png"))
                print(f"FRIDAY WALK {width}: {seconds:.1f} s")
                (SHOTS / f"walk-{width}.txt").write_text(f"{seconds:.1f} s\n")
                assert not errors, errors
            finally:
                browser.close()
