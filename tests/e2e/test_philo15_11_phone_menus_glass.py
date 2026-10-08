"""PHILO-15 11 (B21) -- the phone menus fit a phone, on glass.

Owner ruling 2026-10-07, through the brief: at 393 Go is Needs you / Brief /
The week / Capture, then the Dock's places (Meetings, People, Conductor,
Settings), then the projects; no ⌘ hint on a phone; New is Thought / Meeting
/ Project / Person. 1440 stays as it is.

Rehearsal 1A (bounce B21, `2.2-go-menu-393.png`) counted 22 Go entries with
⌘ keycaps at 393 and nine New kinds. Through the real hub on an isolated
HOME, the built bundle, 393x852 with touch. Shots go to
.tmp/evidence-shots/philo-15-11/ (tests/_evidence.py).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the phone menus glass needs Playwright")

TOKEN = "philo15-11-menus"
SHOTS = evidence_dir("philo-15-11")
PROJECT = "Payments ledger cutover"

GO_ROWS = ["Needs you", "Brief", "The week", "Capture", "Meetings", "People", "Conductor", "Settings", PROJECT, "New"]
NEW_ROWS = ["Thought", "Meeting", "Project", "Person"]

ROWS = """() => [...document.querySelectorAll('.desk-verbbar-menu [role^=menuitem]')]
  .filter((e) => e.getBoundingClientRect().width > 0)
  .map((e) => ({ label: (e.querySelector('.desk-menu-label')?.textContent || '').trim(),
                 keycap: !!e.querySelector('.desk-menu-keycaps, kbd') }))"""


class TestThePhoneMenus:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        from holdspeak.db import get_database

        get_database().projects.create_project(
            project_id="p-ledger", name=PROJECT, description="Move settlement to the new ledger.", keywords=["ledger"]
        )
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": 393, "height": 852}, device_scale_factor=1, has_touch=True)
        page = ctx.new_page()
        page.set_default_timeout(20_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _tap(page: Any, loc: Any, wait: int = 500) -> None:
        loc.first.wait_for()
        box = loc.first.bounding_box()
        assert box, "nothing to tap"
        page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.wait_for_timeout(wait)

    def test_go_and_new_fit_a_phone_393(self) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw)
            try:
                self._tap(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"), 700)
                go = page.evaluate(ROWS)
                page.screenshot(path=str(SHOTS / "11-go-menu-393.png"))
                # The whole Go is on one phone screen: no scroll to its end.
                fits = page.evaluate("""() => { const m = document.querySelector('.desk-verbbar-menu');
                  return !!m && m.scrollHeight <= m.clientHeight + 1; }""")

                self._tap(page, page.locator(".desk-verbbar-menu [role=menuitem][aria-haspopup=menu]", has_text="New"))
                new = page.evaluate(ROWS)
                page.screenshot(path=str(SHOTS / "11-new-menu-393.png"))
            finally:
                browser.close()

        assert [r["label"] for r in go] == GO_ROWS, go
        assert not [r for r in go if r["keycap"]], "a ⌘ hint on a phone"
        assert fits, "Go does not fit the phone screen"
        # The open submenu leads with its back row (◂ New), then the four kinds.
        assert [r["label"] for r in new if r["label"] != "New"] == NEW_ROWS, new
        assert not [r for r in new if r["keycap"]], "a ⌘ hint on a phone"
        assert errors == []
