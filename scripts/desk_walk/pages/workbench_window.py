"""An open Workbench desk window."""
from __future__ import annotations

from playwright.sync_api import Locator, Page, expect


class WorkbenchWindow:
    def __init__(self, page: Page, window: Locator) -> None:
        self.page = page
        self.window = window

    @classmethod
    def find_by_name(cls, page: Page, name: str) -> "WorkbenchWindow":
        window = page.get_by_role("region", name=name, exact=True)
        expect(window).to_be_visible()
        return cls(page, window)

    def get_footer(self) -> Locator:
        footer = self.window.locator("footer").last
        expect(footer).to_be_visible()
        return footer

    def snap(self) -> None:
        """Snap to the maximized desk placement exposed by the window chrome."""
        maximize = self.window.get_by_role("button", name="Maximize", exact=False)
        expect(maximize).to_be_visible()
        maximize.click()

    def close(self) -> None:
        name = self.window.get_attribute("aria-label")
        if not name:
            raise AssertionError("Workbench window has no accessible name")
        self.window.get_by_role("button", name=f"Close {name}").click()
        expect(self.window).to_be_hidden()
