"""Reach the current Desk windows through the owner's menu and Dock doors.

The desktop Window menu keeps the Chair windows. Phone Brief opens the
Brief view in Today; Capture has its own Dock door. Other phone Chair
windows open through the transient Go menu.
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
        brief = win.get_by_role("group", name="Intelligence view", exact=True).filter(visible=True).get_by_role(
            "button", name="Brief", exact=True)
        if brief.get_attribute("aria-pressed") == "true":
            return win
    if name == "Capture" and page.viewport_size["width"] <= 720:
        page.locator(".desk-dock").get_by_role("button", name="Capture", exact=True).click()
    else:
        menu = "window" if page.viewport_size["width"] > 720 else "go"
        page.locator(f".desk-verbbar-item[data-menu-id='{menu}'] button").click()
        panel = page.locator(".desk-verbbar-menu")
        panel.wait_for()
        if menu == "window":
            # PHILO-14 A1 (#939): at 393 the Chair's windows are Go's first rows.
            sub = panel.get_by_role("menuitem").filter(
                has=page.locator(".desk-menu-label", has_text=re.compile(r"^Desk$")))
            sub.scroll_into_view_if_needed()
            sub.click()
        panel.locator("[role^='menuitem']").filter(
            has=page.locator(".desk-menu-label", has_text=re.compile(rf"^{re.escape(name)}$"))).click()
    win.wait_for()
    if name == "Brief" and page.viewport_size["width"] <= 720:
        win.get_by_role("group", name="Intelligence view", exact=True).filter(visible=True).get_by_role(
            "button", name="Brief", exact=True).wait_for()
        assert win.get_by_role("group", name="Intelligence view", exact=True).filter(visible=True).get_by_role(
            "button", name="Brief", exact=True).get_attribute("aria-pressed") == "true"
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
