"""PHILO-13-11 (C1, slice two) -- reach a Chair window the way the owner does.

The Chair is four windows (Needs you, Brief, The week, Capture; owner
ratification 2026-10-02). At 1440 all four are open. At 393 one is shown at
a time (R2): Needs you first; Brief and The week through Go ▸ Chair; Capture
on demand from the Speak AppIcon. Old Chair fences that read a section of
another window at 393 open that window first, through these product doors.
"""
from __future__ import annotations

from typing import Any


def chair_window(page: Any, name: str) -> Any:
    return page.locator(f".desk-window-shell.chair-window[aria-label='{name}']")


def open_chair_window(page: Any, name: str) -> Any:
    """Bring the Chair window `name` to the work area (no-op when shown)."""
    win = chair_window(page, name)
    if win.count() and win.first.is_visible():
        return win.first
    if name == "Capture":
        page.locator(".desk-dock [aria-label^='Speak']").first.click()
    else:
        menu = "window" if page.viewport_size["width"] > 720 else "go"
        page.locator(f".desk-verbbar-item[data-menu-id='{menu}'] button").click()
        page.locator(".desk-verbbar-menu").wait_for()
        sub = page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Chair')")
        sub.scroll_into_view_if_needed()
        sub.click()
        page.locator(f".desk-menu-list [role='menuitemcheckbox']:has-text('{name}')").click()
    win.first.wait_for()
    return win.first
