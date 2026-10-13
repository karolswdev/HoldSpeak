"""The Desk-remembers rig: the canvas week (open_rig._seed) on a real hub,
a page at 1440 (mouse) or 393 (touch), and the press, palette and window
readers the reload fences use.

Was the rig of tests/e2e/test_philo13_07_remembers_glass.py (moved here by
the test diet, push 2, 2026-10-12): tests/e2e/test_windows_glass.py and
test_philo17_phonepass_glass.py share it.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _ensure_build, _normal_chair, _settle
from .open_rig import _seed
from tests._evidence import evidence_dir

TOKEN = "philo13-06-open"  # _seed's own _http speaks this token
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-07-shots")
SIZES = {1440: 900, 393: 852}
ROOM_WORDS = "Dry run passed Tuesday; EU shard backup plan due Friday; Priya owns the rollback runbook."
AGENDA = "Ask Priya about the EU shard backup plan"
DECISION = "Freeze the old ledger on Nov 5"

# PHILO-17 (2b): a person opens in their own window, named by the person.
PERSON = ".desk-window[aria-label='Priya Nair'], .desk-window-shell[aria-label='Priya Nair']"
WINDOWS_JS = r"""() => [...document.querySelectorAll('.desk-window-shell, .desk-window, .desk-pullout')]
  .filter((w) => { const r = w.getBoundingClientRect(); const cs = getComputedStyle(w);
    return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0.05; })
  .map((w) => { const r = w.getBoundingClientRect();
    return {id: w.id, title: (w.getAttribute('aria-label') || '').trim(), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]}; })"""


class _Rig:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        self.ids = _seed(tmp_path / "home", base)
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        page.locator(".desk-window-shell[aria-label='Needs you']").wait_for(timeout=15_000)
        page.wait_for_timeout(1500)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        loc.scroll_into_view_if_needed()
        if width < 720:
            # A touch tap does not wait for the control to be enabled, as a
            # click does. The Room's Draft update stays disabled until the
            # engine read lands (UpdatePosture.tsx, "CHECKING ENGINE"); a tap
            # before that did nothing and the editor never opened (2 of 3 runs).
            from playwright.sync_api import expect
            expect(loc).to_be_enabled(timeout=15_000)
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click(timeout=8_000)

    def _palette(self, page: Any, query: str, option: str, width: int) -> None:
        self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
        page.locator("[aria-controls=desk-palette-listbox]").fill(query)
        opt = page.locator(f"[id='desk-palette-option-{option}']")
        try:
            opt.wait_for(timeout=8_000)
        except Exception:
            ids = page.evaluate("() => [...document.querySelectorAll('[id^=desk-palette-option-]')].map(o => o.id)")
            raise AssertionError(f"no palette option {option!r}; options: {ids}")
        # The shelf's MEMORY rows arrive after the local rows and move them;
        # a touch tap aimed before they land hits a neighbour (at 393 a
        # meeting row sat under the Project's: its window opened over the Room).
        page.wait_for_timeout(900)
        _settle(page)
        self._press(page, opt, width)

    def _chair_window(self, page: Any, width: int, name: str) -> None:
        """At 393, Go > <name>; at 1440 the window stands."""
        shell = page.locator(f".desk-window-shell[aria-label='{name}']")
        if width > 720 or (shell.count() and shell.first.is_visible() and
                           shell.first.evaluate("e => e.classList.contains('is-front')")):
            return
        # PHILO-14 A1 (#939): the Chair's windows are Go's first rows at 393.
        for loc in (
            page.locator(".desk-verbbar-item[data-menu-id='go'] button"),
            page.locator(f".desk-menu-list [role='menuitemcheckbox']:has-text('{name}')"),
        ):
            loc.first.wait_for()
            self._press(page, loc.first, width)
            page.wait_for_timeout(250)
        shell.wait_for()
        _settle(page)

    def _windows(self, page: Any) -> list[dict[str, Any]]:
        return page.evaluate(WINDOWS_JS)

    def _workspace(self, page: Any) -> dict[str, Any]:
        return json.loads(page.evaluate("() => localStorage.getItem('hs.desk.workspace.v1') || '{}'"))
