"""Small assertions shared by desk walk scripts."""
from __future__ import annotations

from playwright.sync_api import Locator, Page, expect


def track_silent_failures(page: Page) -> None:
    """Record browser faults before navigation so the final assertion is useful."""
    failures: list[str] = []
    setattr(page, "_desk_walk_failures", failures)

    def record_console(message: object) -> None:
        if getattr(message, "type", None) == "error":
            failures.append(f"console: {getattr(message, 'text', message)}")

    def record_request(request: object) -> None:
        failures.append(f"request failed: {getattr(request, 'url', request)}")

    def record_response(response: object) -> None:
        status = getattr(response, "status", 0)
        if status >= 400:
            failures.append(f"HTTP {status}: {getattr(response, 'url', response)}")

    page.on("console", record_console)
    page.on("requestfailed", record_request)
    page.on("response", record_response)


def assert_surface_footer(page: Page, surface: Locator) -> Locator:
    """Assert that a surface exposes its standard egress, receipt, and verb slots."""
    footer = surface.locator("footer.surface-footer")
    expect(footer).to_be_visible()
    for slot in ("egress", "receipt", "verbs"):
        expect(footer.locator(f".surface-footer-{slot}")).to_have_count(1)
    return footer


def assert_no_silent_failure(page: Page) -> None:
    """Fail a walk on any console error, failed request, or HTTP error response."""
    failures = getattr(page, "_desk_walk_failures", None)
    if failures is None:
        raise RuntimeError("Call track_silent_failures(page) before navigation")
    assert not failures, "\n".join(failures)
