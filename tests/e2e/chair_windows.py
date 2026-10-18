"""Reach the current Desk windows through the owner's menu and Dock doors.

Go lists every Chair window at both widths (Window ▸ Desk keeps them once a
window is open). Phone Brief opens Today with Since yesterday open
(Betterment D4: Today is one page; the Brief wing is its fold).
"""
from __future__ import annotations

from typing import Any
import re


def chair_window(page: Any, name: str) -> Any:
    if name == "Brief" and page.viewport_size["width"] <= 720:
        return page.locator('[id="pullout:intelligence:desk"]')
    return page.locator(f".desk-window-shell.chair-window[aria-label='{name}']")


def open_chair_window(page: Any, name: str) -> Any:
    """Bring the Chair window `name` to the work area (no-op when shown)."""
    win = chair_window(page, name)
    if win.count() and win.is_visible():
        if name != "Brief" or page.viewport_size["width"] > 720:
            return win
        since = win.get_by_test_id("today-since-toggle")
        if since.count() and since.get_attribute("aria-expanded") == "true":
            return win
    # Go is the Chair windows' door at both widths: S0 (#1257) left an empty
    # desk's Window menu with one line, so Go lists every Chair window (one
    # list, applications.ts GO_EXTRA_ROWS). On the phone, Go ▸ Brief is
    # Today's Brief view.
    page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
    panel = page.locator(".desk-verbbar-menu")
    panel.wait_for()
    panel.locator("[role^='menuitem']").filter(
        has=page.locator(".desk-menu-label", has_text=re.compile(rf"^{re.escape(name)}$"))).click()
    win.wait_for()
    if name == "Brief" and page.viewport_size["width"] <= 720:
        # The fold is open, or its read failed (one line and Retry).
        win.locator("[data-testid=today-since-toggle], [data-testid=today-since-failed]").first.wait_for()
        since = win.get_by_test_id("today-since-toggle")
        if since.count():
            assert since.get_attribute("aria-expanded") == "true"
    return win


def go_group(page: Any, group: str, press: Any = None) -> Any:
    """At 393 Go has one group, `New ▸` (PHILO-15 11, B21, owner ruling
    2026-10-07; was C7 Q3 `Desk ▸ Object ▸ Window ▸`). With Go open, open
    one group (the panel is replaced, a back row first) and return the menu."""
    import re

    row = page.locator(".desk-verbbar-menu [role='menuitem'][aria-haspopup='menu']").filter(
        has=page.locator(".desk-menu-label", has_text=re.compile(rf"^{re.escape(group)}$")))
    row.wait_for()
    row.scroll_into_view_if_needed()
    (press or (lambda loc: loc.click()))(row)
    page.locator(".desk-verbbar-menu .desk-menu-back", has_text=group).wait_for()
    return page.locator(".desk-verbbar-menu")
