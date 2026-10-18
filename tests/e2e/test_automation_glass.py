"""The Automations app, AS RENDERED: what only a real browser proves.

Betterment A5 (docs/internal/betterment/workbench/RECIPE.md): a desk object
dropped on the automation window becomes an About chip. The drop is a real
HTML drag from the Screen's note icon (the hand's drag: `hand/drag.ts`) onto
the window, through the real hub on an isolated HOME at 1440 x 900. The
phone (393) has no loose Screen icons to drag; its About is the picker
(web/src/desk/__tests__/automation.app.test.tsx).
"""

from __future__ import annotations

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
                about = page.get_by_test_id("automation-line-about")
                assert "What is it about?" in about.inner_text()
                window = page.get_by_test_id("automation-window")
                # The window opens over the Screen's icons: move it by its
                # title strip until the note's icon is clear.
                icon_box = page.locator(ICON).bounding_box()
                frame = page.locator(f"[id='workbench:{WB}']")
                box = frame.bounding_box()
                assert icon_box and box
                grab = (box["x"] + 120, box["y"] + 12)
                shift = max(0.0, icon_box["y"] + icon_box["height"] + 24 - box["y"])
                page.mouse.move(*grab)
                page.mouse.down()
                page.mouse.move(grab[0], grab[1] + shift / 2, steps=6)
                page.mouse.move(grab[0], grab[1] + shift, steps=6)
                page.mouse.up()
                moved = frame.bounding_box()
                assert moved and moved["y"] > icon_box["y"] + icon_box["height"], (icon_box, moved)
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
                about = page.get_by_test_id("automation-line-about")
                about.get_by_role("button").first.click()
                well = page.get_by_role("textbox", name="Find by name")
                well.fill("plat")
                with page.expect_response(lambda r: r.url.endswith(f"/api/workbenches/{WB}")
                                          and r.request.method == "PUT") as kept:
                    page.get_by_role("button", name=f"Add {NOTE}").click()
                assert (kept.value.request.post_data_json or {}).get("sources") == [f"note:{NOTE_ID}"]
                page.get_by_role("button", name=f"Remove {NOTE}").wait_for(timeout=T)
                assert well.input_value() == "plat"  # typed text is never deleted
                page.screenshot(path=str(SHOTS / f"about-picker-{width}.png"))
                assert not errors, errors
            finally:
                browser.close()


class TestFridayWalk:
    """Betterment A7, DESIGN §6: New automation → Friday team update → With →
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
        monkeypatch.setenv(CLI_ENGINES_ENV, "on")
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("width", [1440, 393])
    def test_friday_team_update_reads_a_result_in_six_presses(self, width: int) -> None:
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
                page.get_by_role("menuitem", name="Automations").first.click()
                new = page.get_by_test_id("automation-new")
                new.wait_for(timeout=T)
                page.screenshot(path=str(SHOTS / f"walk-0-home-{width}.png"))

                started, presses = time.monotonic(), 0
                new.click(); presses += 1
                friday = page.get_by_test_id("automation-starter-friday-team-update").last
                friday.wait_for(timeout=T)
                page.screenshot(path=str(SHOTS / f"walk-1-new-{width}.png"))
                friday.click(); presses += 1
                with_line = page.get_by_test_id("automation-line-with")
                with_line.wait_for(timeout=T)
                page.screenshot(path=str(SHOTS / f"walk-2-sentence-{width}.png"))
                with_line.get_by_role("button").first.click(); presses += 1
                add = page.get_by_role("button", name="Add Claude Code")
                add.wait_for(timeout=T)
                add.click(); presses += 1
                with_line.get_by_text("Claude Code").first.wait_for(timeout=T)
                page.get_by_test_id("automation-run-now").click(); presses += 1
                reading = page.get_by_test_id("automation-newest").get_by_test_id("automation-reading")
                reading.get_by_role("heading", name="Team update, this week").wait_for(timeout=60_000)
                seconds = time.monotonic() - started
                reading.scroll_into_view_if_needed()
                page.screenshot(path=str(SHOTS / f"walk-3-result-{width}.png"))
                assert presses <= 6, presses
                assert "##" not in reading.inner_text()
                print(f"FRIDAY WALK {width}: {presses} presses, {seconds:.1f} s")
                (SHOTS / f"walk-{width}.txt").write_text(f"{presses} presses, {seconds:.1f} s\n")
                assert not errors, errors
            finally:
                browser.close()
