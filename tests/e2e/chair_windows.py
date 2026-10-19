"""Reach the current Desk windows through the owner's menu and Dock doors.

Go lists every Chair window at both widths (Window ▸ Desk keeps them once a
window is open). Betterment daily D5: the Brief window retired into Today, so
"Brief" is Today with Since yesterday open (its fold), at both widths, and Go
has no Brief row: the helper opens Today from Go and unfolds Since yesterday.
"""
from __future__ import annotations

from typing import Any
import re


def chair_window(page: Any, name: str) -> Any:
    if name == "Brief":
        return page.locator('[id="pullout:intelligence:desk"]')
    return page.locator(f".desk-window-shell.chair-window[aria-label='{name}']")


def _since_open(win: Any) -> bool:
    since = win.get_by_test_id("today-since-toggle")
    return bool(since.count()) and since.get_attribute("aria-expanded") == "true"


def open_chair_window(page: Any, name: str) -> Any:
    """Bring the Chair window `name` to the work area (no-op when shown)."""
    win = chair_window(page, name)
    if win.count() and win.is_visible() and (name != "Brief" or _since_open(win)):
        return win
    # Go is the Chair windows' door at both widths: S0 (#1257) left an empty
    # desk's Window menu with one line, so Go lists every Chair window (one
    # list, applications.ts GO_EXTRA_ROWS).
    label = "Today" if name == "Brief" else name
    page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
    panel = page.locator(".desk-verbbar-menu")
    panel.wait_for()
    panel.locator("[role^='menuitem']").filter(
        has=page.locator(".desk-menu-label", has_text=re.compile(rf"^{re.escape(label)}$"))).click()
    win.wait_for()
    if name == "Brief":
        # The fold opens, or its read failed (one line and Retry).
        win.locator("[data-testid=today-since-toggle], [data-testid=today-since-failed]").first.wait_for()
        since = win.get_by_test_id("today-since-toggle")
        if since.count() and since.get_attribute("aria-expanded") != "true":
            since.click()
            page.wait_for_function(
                "el => el.getAttribute('aria-expanded') === 'true'", arg=since.element_handle())
    return win
