"""PHILO-13-11 close: re-shoot the C1 Chair boards that no glass test shoots.

C1-4b (a Chair window zoomed at 1440; The week open at 393), C1-4d at 393
(Go ▸ Chair open) and C1-4e (a closed Chair window reopened in front), plus the
whole Chair desk (C1-1, C1-4a, C1-6a). It reuses the Chair glass rig whole
(``tests/e2e/test_philo13_11_chair_glass.py``: the real hub, an isolated HOME,
the canvas week through the real producers) and its fences (C2 one blue window
named by the screen bar; C3 ownership; C4 393 content and targets).

Run from the repo root (the tests conftest enforces the isolated HOME):

    HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=~/Library/Caches/ms-playwright \
      uv run pytest -p tests.conftest -q \
      pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-close/shoot_close.py

Shots go to ``.tmp/evidence-shots/<this dir>/`` unless HOLDSPEAK_EVIDENCE_WRITE=1.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from tests._evidence import evidence_dir
from tests.e2e import test_philo13_11_chair_glass as chair_glass

SIZES = chair_glass.SIZES

SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-close")


class TestCloseShots(chair_glass.TestTheChairAsWindows):
    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_chair_as_windows(self, width: int) -> None:  # the parent's walk is not repeated here
        pytest.skip("the parent test runs in tests/e2e")

    def _go_chair(self, page: Any, width: int) -> None:
        self._press(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"), width)
        page.locator(".desk-verbbar-menu").wait_for()
        sub = page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Chair')")
        sub.scroll_into_view_if_needed()
        self._press(page, sub, width)
        page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Needs you')").wait_for()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_close_shots(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        facts: dict[str, Any] = {}
        failures: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            shell = lambda name: page.locator(f".desk-window-shell[aria-label='{name}']")  # noqa: E731

            def board(name: str) -> None:
                frame, chair = self._measure(page, width, name, facts)
                failures[name] = self._fails(frame, chair, width)
                page.screenshot(path=str(SHOTS / f"close-{name}-{width}.png"))

            try:
                if width > 720:
                    board("C1-1-the-desk")  # = C1-4a
                    # C1-4b: Zoom fills the screen
                    shell("Brief").get_by_role("button", name="Zoom Brief").click()
                    page.wait_for_timeout(500)
                    board("C1-4b-chair-window-zoomed")
                    # Zoom covers the other Chair windows by design (§5, C1-4b):
                    # the tiling fence does not apply to this one board.
                    failures["C1-4b-chair-window-zoomed"].pop("C1 the four tile", None)
                    work = page.evaluate("""() => { const r = document.querySelector(
                        ".desk-window-shell[aria-label='Brief']").getBoundingClientRect();
                        return {w: Math.round(r.width), h: Math.round(r.height)}; }""")
                    facts["zoomed-brief"] = work
                    facts["zoom-geometry"] = page.evaluate("""() => {
                        const r = (e) => { const b = e.getBoundingClientRect(); return [Math.round(b.left), Math.round(b.top), Math.round(b.right), Math.round(b.bottom)]; };
                        const shells = Object.fromEntries([...document.querySelectorAll('.desk-window-shell')].map((e) => [e.getAttribute('aria-label'), r(e)]));
                        const z = document.querySelector(".desk-window-shell[aria-label='Brief']");
                        const op = z.offsetParent;
                        return {shells, work_top: getComputedStyle(z).getPropertyValue('--desk-work-top'),
                                work_bottom: getComputedStyle(z).getPropertyValue('--desk-work-bottom'),
                                root_snap_bottom: getComputedStyle(document.documentElement).getPropertyValue('--desk-snap-bottom'),
                                root_dock_h: getComputedStyle(document.documentElement).getPropertyValue('--desk-dock-h'),
                                dock: r(document.querySelector('.desk-dock')),
                                sizing_gadget_hit: (() => { const g = z.querySelector('.desk-gadget-size, [class*=sizing], [aria-label^="Size"]');
                                  if (!g) return 'no sizing gadget found'; const b = g.getBoundingClientRect();
                                  const hit = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
                                  return {gadget: r(g), owns: g.contains(hit), hit: hit ? hit.className : null}; })(),
                                offset_parent: op ? [op.className, r(op)] : null,
                                screen_bar: r(document.querySelector('[data-testid=desk-screen-title]').closest('header, nav, div'))};
                    }""")
                    if work["w"] < 1400 or not facts["zoom-geometry"]["sizing_gadget_hit"].get("owns"):
                        failures["C1-4b-chair-window-zoomed"]["zoom fills the screen"] = work
                    shell("Brief").get_by_role("button", name="Zoom Brief").click()
                    page.wait_for_timeout(400)
                    # C1-4e: close, then Window ▸ Chair ▸ Brief reopens it in front
                    shell("Brief").get_by_role("button", name="Close Brief").click()
                    shell("Brief").wait_for(state="detached")
                    page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
                    page.locator(".desk-verbbar-menu").wait_for()
                    page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Chair')").hover()
                    page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Brief')").click()
                    shell("Brief").wait_for()
                    board("C1-4e-chair-window-reopened")
                else:
                    board("C1-1-the-desk")  # = C1-6a
                    # C1-4b (393): The week open from Go ▸ Chair
                    self._go_chair(page, width)
                    self._press(page, page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('The week')"), width)
                    shell("The week").wait_for()
                    board("C1-4b-chair-week-open")
                    # C1-4d (393): Go ▸ Chair, a check on each open one
                    self._go_chair(page, width)
                    facts["go-chair"] = page.evaluate("""() => [...document.querySelectorAll(
                        '.desk-menu-list [role="menuitemcheckbox"]')].map((e) => [e.textContent.trim(), e.getAttribute('aria-checked')])""")
                    page.wait_for_timeout(300)
                    page.screenshot(path=str(SHOTS / f"close-C1-4d-window-menu-chair-{width}.png"))
                    # C1-4e (393): Brief opens in front; close; reopen from Go ▸ Chair
                    self._press(page, page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Brief')"), width)
                    shell("Brief").wait_for()
                    self._press(page, shell("Brief").get_by_role("button", name="Close Brief"), width)
                    shell("Brief").wait_for(state="detached")
                    self._go_chair(page, width)
                    self._press(page, page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Brief')"), width)
                    shell("Brief").wait_for()
                    board("C1-4e-chair-window-reopened")
                facts["errors"] = [e for e in errors if "ResizeObserver" not in e]
                failures = {k: v for k, v in failures.items() if v}
                facts["failures"] = failures
                (SHOTS / f"close-facts-{width}.json").write_text(json.dumps(facts, indent=2) + "\n")
                assert not facts["errors"], facts["errors"]
                assert not failures, json.dumps(failures, indent=2)
            finally:
                browser.close()
