"""PHILO-13-18 (C8) -- Escape on an open strip menu closes the menu, not the window.

Seen in the type-floor rig at 393 (2026-10-02): Meetings' wings fold into one
strip menu Button (stripMenu.tsx); a tap opens it and leaves focus on the
Button, so Escape reached the window's own Escape-closes handler
(DeskWindow.tsx) and the whole Meetings window closed. Through the real hub on
an isolated HOME at 393 touch: tap the strip menu, press Escape; the menu is
gone and Meetings is still the front window. A second Escape still closes the
window (the window's rule is unchanged).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="the strip Escape glass needs Playwright")

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(300, method="thread")]

TOKEN = "philo13-18-escape"


def test_escape_closes_the_strip_menu_not_the_window(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_context(viewport={"width": 393, "height": 852}, has_touch=True).new_page()
            page.set_default_timeout(20_000)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            page.evaluate("sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify({key: 'review-meetings'}))")
            page.reload(wait_until="load")
            _normal_chair(page)
            window = page.locator(".desk-window-shell[aria-label='Meetings']")
            window.wait_for()
            _settle(page)
            strip = window.locator(".desk-wings-menu")
            assert strip.count() == 1, "at 393 the Meetings wings fold into one strip menu"
            box = strip.bounding_box()
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.locator(".desk-menu-list").first.wait_for()
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            menu_open = page.locator(".desk-menu-list").count()
            still_open = window.count() and window.is_visible()
            front = page.evaluate(
                "() => { const f = [...document.querySelectorAll('.desk-window-shell.is-front')].pop();"
                " return f ? f.getAttribute('aria-label') : null; }")
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            closed_after_second = window.count() == 0 or not window.is_visible()
            browser.close()
    finally:
        server.stop()

    assert menu_open == 0, "the first Escape left the strip menu open"
    assert still_open and front == "Meetings", f"the first Escape closed the window (front now {front!r})"
    assert closed_after_second, "a second Escape no longer closes the window"
