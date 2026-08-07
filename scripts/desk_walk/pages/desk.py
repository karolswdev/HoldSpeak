"""The desk shell page object."""
from __future__ import annotations

from playwright.sync_api import Locator, Page, expect


class DeskPage:
    def __init__(self, page: Page) -> None:
        self.page = page

    @property
    def palette_button(self) -> Locator:
        return self.page.get_by_role("button", name="Search", exact=False)

    def wait_for_ready(self) -> None:
        """Wait for the accessible desk shell, not an arbitrary sleep."""
        expect(self.palette_button).to_be_visible()
        self.page.wait_for_load_state("networkidle")

    def open_palette(self) -> None:
        self.page.keyboard.press("Meta+k")
        expect(
            self.page.get_by_role("region", name="Tools and Desk search")
        ).to_be_visible()

    def get_open_windows(self) -> list[str]:
        """Return accessible names for currently visible desk windows."""
        windows = self.page.get_by_role("region").filter(
            has=self.page.get_by_role("button", name="Close", exact=False)
        )
        return [
            name
            for name in windows.evaluate_all(
                "elements => elements.filter(element => !!(element.offsetWidth || element.offsetHeight || element.getClientRects().length)).map(element => element.getAttribute('aria-label') || '')"
            )
            if name
        ]

    def keyboard_shortcut(self, keys: str) -> None:
        self.page.keyboard.press(keys)
