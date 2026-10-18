"""The finish-polish rig: a real hub on an isolated HOME with five projects
and one decision, opened at 1440x900 (mouse) or 393x852 (touch).

Shared by the app glass files that keep the finish-polish fences (the test
diet, push 2, 2026-10-12): tests/e2e/test_dock_glass.py,
test_chair_glass.py, test_processes_glass.py and test_roadmap_glass.py.
Was the rig of tests/e2e/test_finish_face_polish_glass.py (parked).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

TOKEN = "finish-polish-glass"
SHOTS = evidence_dir("tests/e2e/shots/finish-face-polish")
SIZES = {1440: 900, 393: 852}
PROJECTS = ("Payments ledger cutover", "Platform observability", "Staff hiring loop",
            "Search relevance", "Mobile release train")


class FinishRig:
    """A base class: its autouse fixture boots the hub; its helpers open a page."""

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


    def _page(self, pw: Any, width: int, *, builder_tools: bool = False) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                  has_touch=width < 720, reduced_motion="reduce")
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.set_default_navigation_timeout(120_000)
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        if builder_tools:
            # Betterment shell S1 (#1259): Processes, Refresh from hub and the
            # other builder tools are in Go and Search only with Settings ▸
            # System ▸ Builder tools on (web/src/desk/builderTools.ts).
            page.evaluate("() => localStorage.setItem('hs.desk.builderTools', 'on')")
        page.reload(wait_until="load")
        # The first /api/setup/status runs every doctor check cold (imports);
        # on a loaded machine that took 36 s. The desk waits for it.
        page.locator(".chair").wait_for(timeout=120_000)
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
