"""Primitive pullout page object."""
from __future__ import annotations

from playwright.sync_api import Locator, Page, expect


class Pullout:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.window: Locator | None = None

    def open_by_ref(self, kind: str, id: str) -> "Pullout":
        """Open a primitive through its screen-reader-accessible world button."""
        object_button = self.page.locator(
            f'button[data-kind="{kind}"][data-obj-id$=":{id}"]'
        )
        expect(object_button).to_be_visible()
        label = object_button.get_attribute("aria-label")
        if not label:
            raise AssertionError(f"{kind}:{id} has no accessible object label")
        # The semantic world controls are intentionally overlaid on the canvas.
        # Exercise their keyboard contract rather than forcing a pointer through
        # desk chrome that is correctly above the spatial world.
        object_button.press("Enter")
        self.window = self.page.get_by_role("region", name=label, exact=True)
        expect(self.window).to_be_visible()
        return self

    def get_content(self) -> Locator:
        if self.window is None:
            raise RuntimeError("Open a pullout before requesting its content")
        body = self.window.locator(".desk-pullout-body")
        expect(body).to_be_visible()
        return body

    def close(self) -> None:
        if self.window is None:
            return
        name = self.window.get_attribute("aria-label")
        if not name:
            raise AssertionError("Pullout has no accessible name")
        self.window.get_by_role("button", name=f"Close {name}").click()
        expect(self.window).to_be_hidden()
        self.window = None
