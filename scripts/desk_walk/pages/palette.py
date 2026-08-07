"""The command palette page object."""
from __future__ import annotations

import re

from playwright.sync_api import Locator, Page, expect


class Palette:
    def __init__(self, page: Page) -> None:
        self.page = page

    @property
    def region(self) -> Locator:
        return self.page.get_by_role("region", name="Tools and Desk search")

    @property
    def combobox(self) -> Locator:
        return self.page.get_by_role("combobox", name="Search tools and Desk items")

    def open(self) -> None:
        self.page.keyboard.press("Meta+k")
        expect(self.region).to_be_visible()

    def assert_combobox(self) -> Locator:
        expect(self.combobox).to_be_visible()
        expect(self.combobox).to_have_attribute("aria-controls", "desk-palette-listbox")
        expect(self.combobox).to_have_attribute("aria-activedescendant", re.compile(r".+"))
        return self.combobox

    def search(self, query: str) -> None:
        self.assert_combobox().fill(query)
        expect(self.page.get_by_role("listbox")).to_be_visible()

    def close(self) -> None:
        # The desk follows the native search ladder: first Escape clears a
        # non-empty query, the second dismisses the palette.
        self.combobox.press("Escape")
        if self.region.is_visible():
            self.combobox.press("Escape")
        expect(self.region).to_be_hidden()

    def choose(self, entry: str) -> None:
        """Verify the named choice is rendered, then use the keyboard to choose it."""
        expect(self.page.get_by_role("option", name=entry).first).to_be_visible()
        self.combobox.press("Enter")
        expect(self.region).to_be_hidden()
