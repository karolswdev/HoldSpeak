"""HS-122-12 keyboard-first headless walk for the programmable desk.

Run with:
    uv run python -m scripts.desk_walk.walk_keyboard_122
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

from scripts.desk_walk.assertions import assert_no_silent_failure, track_silent_failures
from scripts.desk_walk.fixtures import HubFixture
from scripts.desk_walk.pages import DeskPage, Palette

SCREENSHOTS = Path(__file__).resolve().parent / "screenshots"
VIEWPORT = {"width": 1440, "height": 900}


def capture(page: Page, step: str) -> Path:
    """Capture the visible desk at a named keyboard workflow step."""
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOTS / f"1440-keyboard-122-{step}.png"
    page.screenshot(path=str(path), full_page=False)
    return path


def selected_option(page: Page, label: str) -> None:
    """Assert that the palette's keyboard selection names the expected row."""
    # The row's accessible name includes its visible kind token (for example,
    # ``Workbench WORKBENCH``), so match its public label rather than its
    # implementation-specific composite accessible name.
    option = page.get_by_role("option").filter(has_text=label).first
    expect(option).to_be_visible()
    expect(option).to_have_attribute("aria-selected", "true")
    expect(option).to_contain_text(label)


def close_region_with_keyboard(page: Page, name: str) -> None:
    """Close a desk region by focusing its native Close button and pressing Enter."""
    region = page.get_by_role("region", name=name, exact=True)
    expect(region).to_be_visible()
    close = region.get_by_role("button", name=f"Close {name}", exact=True)
    expect(close).to_be_visible()
    close.focus()
    expect(close).to_be_focused()
    close.press("Enter")
    expect(region).to_be_hidden()


def walk(page: Page, fixture: HubFixture) -> list[Path]:
    assert fixture.url is not None
    track_silent_failures(page)
    page.goto(f"{fixture.url}/?token={fixture.owner_token}", wait_until="networkidle")

    desk = DeskPage(page)
    palette = Palette(page)
    desk.wait_for_ready()
    workbenches = page.locator('button[data-kind="workbench"]')
    initial_workbench_count = workbenches.count()
    assert initial_workbench_count >= 1, "fixture must expose its seeded workbench"
    shots = [capture(page, "00-desk-ready")]

    # Cmd+K opens the palette without using the pointer. Palette.open uses the
    # macOS chord; Chrome maps the same behavior to Control+K on other hosts.
    desk.open_palette()
    combobox = palette.assert_combobox()
    expect(combobox).to_be_focused()
    expect(page.get_by_role("listbox")).to_be_visible()
    shots.append(capture(page, "01-palette-open"))

    # Native Tab reaches the first option, then Shift+Tab returns focus to the
    # combobox. Arrow navigation keeps focus there and announces the selected
    # option through aria-activedescendant.
    page.keyboard.press("Tab")
    mic = page.get_by_role("button", name="Speak Search tools and Desk items")
    expect(mic).to_be_focused()
    page.keyboard.press("Tab")
    focused = page.locator(":focus")
    expect(focused).to_have_attribute("role", "option")
    page.keyboard.press("Shift+Tab")
    page.keyboard.press("Shift+Tab")
    expect(combobox).to_be_focused()
    before = combobox.get_attribute("aria-activedescendant")
    assert before, "palette combobox must announce its active option"
    page.keyboard.press("ArrowDown")
    after = combobox.get_attribute("aria-activedescendant")
    assert after and after != before, "ArrowDown did not advance palette selection"
    page.keyboard.press("ArrowUp")
    expect(combobox).to_have_attribute("aria-activedescendant", before)

    # Search and open the seeded object exclusively with the palette keyboard
    # contract: input, Enter, then a focused native Close button.
    palette.search("Workbench")
    selected_option(page, "Workbench")
    shots.append(capture(page, "02-object-search"))
    combobox.press("Enter")
    expect(palette.region).to_be_hidden()
    expect(page.get_by_role("region", name="Workbench", exact=True)).to_be_visible()
    shots.append(capture(page, "03-object-open"))
    close_region_with_keyboard(page, "Workbench")
    shots.append(capture(page, "04-object-closed"))

    # Creation uses the exact same keyboard-only palette path. The new object
    # opens in its own labelled region, which proves both mint and visibility.
    desk.open_palette()
    palette.search("New Workbench")
    selected_option(page, "New Workbench")
    shots.append(capture(page, "05-create-search"))
    combobox.press("Enter")
    expect(palette.region).to_be_hidden()
    created = page.get_by_role("region", name="New Workbench", exact=True)
    expect(created).to_be_visible()
    expect(created.get_by_role("button", name="Close New Workbench", exact=True)).to_be_visible()
    shots.append(capture(page, "06-created-workbench"))
    close_region_with_keyboard(page, "New Workbench")

    # Closing the window does not discard the created primitive: its semantic
    # world control remains on the desk, alongside the seeded workbench.
    expect(workbenches).to_have_count(initial_workbench_count + 1)
    shots.append(capture(page, "07-created-object-found"))

    assert_no_silent_failure(page)
    return shots


def main() -> None:
    with HubFixture() as fixture, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            context = browser.new_context(
                viewport=VIEWPORT,
                device_scale_factor=2,
                extra_http_headers={"X-HoldSpeak-Token": fixture.owner_token},
            )
            try:
                outputs = walk(context.new_page(), fixture)
            finally:
                context.close()
        finally:
            browser.close()
    print("Saved keyboard desk walk screenshots:")
    for path in outputs:
        print(path)


if __name__ == "__main__":
    main()
