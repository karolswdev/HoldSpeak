"""HS-122-09 headless screenshot walk for the programmable desk.

Run with:
    uv run python -m scripts.desk_walk.walk_phase_122
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from scripts.desk_walk.assertions import (
    assert_no_silent_failure,
    assert_surface_footer,
    track_silent_failures,
)
from scripts.desk_walk.fixtures import HubFixture
from scripts.desk_walk.pages import DeskPage, Palette, Pullout, WorkbenchWindow

SCREENSHOTS = Path(__file__).resolve().parent / "screenshots"
VIEWPORTS = ((1440, 900), (393, 852))


def capture(page: Page, width: int, name: str) -> Path:
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOTS / f"{width}-{name}.png"
    page.screenshot(path=str(path), full_page=False)
    return path


def walk_viewport(page: Page, fixture: HubFixture, width: int, height: int) -> list[Path]:
    assert fixture.url is not None
    track_silent_failures(page)
    page.goto(f"{fixture.url}/?token={fixture.owner_token}", wait_until="networkidle")

    desk = DeskPage(page)
    palette = Palette(page)
    pullout = Pullout(page)
    desk.wait_for_ready()
    shots = [capture(page, width, "00-desk-ready")]

    palette.open()
    palette.assert_combobox()
    shots.append(capture(page, width, "01-palette-open"))

    # The fixture's manifest includes hs-seed-workbench. Use its public
    # screen-reader button rather than an internal store or API response.
    palette.search("Workbench")
    palette.close()

    seeded_workbench = page.locator(
        '[data-kind="workbench"][data-obj-id$=":hs-seed-workbench"]'
    )
    if seeded_workbench.count():
        pullout.open_by_ref("workbench", "hs-seed-workbench")
        assert pullout.window is not None
        name = pullout.window.get_attribute("aria-label")
        assert name is not None
        workbench = WorkbenchWindow.find_by_name(page, name)
        assert_surface_footer(page, workbench.window)
        shots.append(capture(page, width, "02-workbench-with-items"))
        shots.append(capture(page, width, "03-pullout-open"))
        pullout.close()
    else:
        # A caller may reuse the harness with an intentionally empty fixture.
        # Keep the manifest stable while making the absence explicit in the shot.
        shots.append(capture(page, width, "02-workbench-with-items"))
        shots.append(capture(page, width, "03-pullout-open"))

    assert_no_silent_failure(page)
    return shots


def main() -> None:
    outputs: list[Path] = []
    with HubFixture() as fixture, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for width, height in VIEWPORTS:
                context = browser.new_context(
                    viewport={"width": width, "height": height},
                    device_scale_factor=2,
                    extra_http_headers={"X-HoldSpeak-Token": fixture.owner_token},
                )
                try:
                    outputs.extend(walk_viewport(context.new_page(), fixture, width, height))
                finally:
                    context.close()
        finally:
            browser.close()
    print("Saved desk walk screenshots:")
    for path in outputs:
        print(path)


if __name__ == "__main__":
    main()
