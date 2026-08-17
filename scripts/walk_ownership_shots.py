"""HS-134-10 -- web ownership screenshots.

Boots an isolated, seeded hub with a recipe and workbench wired for
ownership display, then captures both-width screenshots of:
  1. Get Info on a recipe (placement summary + Edit in Agent hand-off)
  2. WorkbenchWindow config (INHERITED skills + hand-off)

Usage:
  HOME=$(mktemp -d) uv run python scripts/walk_ownership_shots.py
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from scripts.desk_walk.assertions import (
    assert_no_silent_failure,
    track_silent_failures,
)
from scripts.desk_walk.fixtures import HubFixture
from scripts.desk_walk.pages import DeskPage, Pullout, WorkbenchWindow

ASSETS = (
    Path(__file__).resolve().parents[1]
    / "pm"
    / "roadmap"
    / "holdspeak"
    / "phase-134-one-owner"
    / "assets"
)
VIEWPORTS = ((1440, 900), (393, 852))

def _ensure_recipe_and_skills(fixture: HubFixture) -> str:
    """Create a recipe with a skill and wire it to the seed workbench."""
    db = fixture.database
    assert db is not None

    # Create a recipe (agent) for the ownership proof
    recipe = db.recipes.upsert(
        recipe_id="walk-ownership-recipe",
        name="Morning Brief",
        system_prompt="You summarize the day ahead.",
        user_template="{input}",
        profile_id=None,  # no agent-tier override -> INHERITED placement
    )

    # Attach a skill to the recipe
    db.skills.upsert(
        skill_id="walk-ownership-skill",
        title="Calendar awareness",
        body="When summarizing the day, include calendar events.",
        source="owner-authored",
        status="active",
        recipe_ids=[recipe.id],
    )

    # Wire the seed workbench to this recipe
    db.workbenches.upsert(
        workbench_id="hs-seed-workbench",
        name="Workbench",
        recipe_id=recipe.id,
        profile_id=None,  # inheriting placement
        resolver_profile_id="hs-seed-local-4b-resolver",
    )

    return recipe.id


def capture(page: Page, width: int, name: str) -> Path:
    ASSETS.mkdir(parents=True, exist_ok=True)
    path = ASSETS / f"{width}-{name}.png"
    page.screenshot(path=str(path), full_page=False)
    print(f"  saved {path}")
    return path


def walk_viewport(
    page: Page, fixture: HubFixture, width: int, height: int, recipe_id: str,
) -> list[Path]:
    assert fixture.url is not None
    track_silent_failures(page)

    shots: list[Path] = []

    # --- Get Info on the recipe (placement summary) ----------------------
    # InfoWindow renders ONLY in WorldStage (spatial view). Navigate in
    # spatial view; the recipe's object button may overlap the menubar,
    # so use keyboard access: open the pullout via ?open=, close it,
    # focus the object button via Tab, then press Shift+F10 to trigger
    # the context menu on the focused element (the list view's
    # onRowKeyDown recognises this chord; the spatial world buttons are
    # plain DOM buttons that emit the same native contextmenu event).
    page.goto(
        f"{fixture.url}/?token={fixture.owner_token}&view=spatial"
        f"&open=recipe:{recipe_id}",
        wait_until="networkidle",
    )
    desk = DeskPage(page)
    desk.wait_for_ready()
    page.wait_for_timeout(600)
    # Close the pullout so the world is clean
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # Use the GL engine's __hsWorldProbe to find the exact screen
    # position of the recipe object, then right-click at that position.
    info_opened = False
    probe = page.evaluate(
        """(title) => {
            if (typeof window.__hsWorldProbe !== 'function') return null;
            const objs = window.__hsWorldProbe();
            return objs.find(o => o.title === title) || null;
        }""",
        "Morning Brief",
    )
    if probe:
        cx, cy = probe["x"], probe["y"]
        print(f"  probe: Morning Brief at ({cx}, {cy})")
        page.mouse.click(cx, cy, button="right")
        page.wait_for_timeout(500)
        get_info = page.get_by_role("menuitem", name="Get Info")
        if get_info.count():
            get_info.click()
            page.wait_for_timeout(800)
            info_window = page.locator(".desk-info-window")
            if info_window.count():
                info_window.wait_for(state="visible", timeout=5000)
                page.wait_for_timeout(300)
                info_opened = True
                print(f"  InfoWindow opened at {width}px")
            else:
                print(f"  WARNING: InfoWindow not visible after click at {width}px")
        else:
            print(f"  WARNING: Get Info menuitem not found at {width}px")
    else:
        print(f"  WARNING: __hsWorldProbe did not find 'Morning Brief' at {width}px")
    shots.append(capture(page, width, "ownership-get-info"))

    # Close everything with Escape
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    # --- WorkbenchWindow config (INHERITED skills) -----------------------
    # Re-navigate to clear any open pullouts (on mobile the pullout
    # covers the list completely).
    page.goto(
        f"{fixture.url}/?token={fixture.owner_token}&view=list",
        wait_until="networkidle",
    )
    desk.wait_for_ready()
    page.wait_for_selector(".desk-listmode", timeout=8000)
    page.wait_for_timeout(400)
    # Open the seed workbench from the list view row.
    wb_row = page.locator(
        'button.desk-sortable-table-open:has-text("Workbench")'
    )
    if wb_row.count():
        wb_row.first.click()
        page.wait_for_timeout(500)

        # The pullout/workbench window should appear
        wb_region = page.locator(".desk-pullout").first
        if wb_region.count():
            wb_region.wait_for(state="visible", timeout=5000)
            # The config panel starts collapsed (strip). Click the strip
            # to expand the full config panel which shows SKILLS section.
            config_strip = wb_region.locator(".wb-config-strip")
            if config_strip.count() and config_strip.is_visible():
                config_strip.click()
                page.wait_for_timeout(400)
            # Scroll to the SKILLS section to make it visible
            skills_label = wb_region.locator("text=SKILLS")
            if skills_label.count():
                skills_label.first.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
            shots.append(capture(page, width, "ownership-workbench-skills"))
            # Close via Escape
            page.keyboard.press("Escape")
            page.wait_for_timeout(200)
        else:
            print(f"  WARNING: workbench pullout not visible at {width}px")
            shots.append(capture(page, width, "ownership-workbench-skills"))
    else:
        print(f"  WARNING: 'Workbench' not found in list at {width}px")
        shots.append(capture(page, width, "ownership-workbench-skills"))

    # Zero console errors -- genuinely zero, no filters.
    assert_no_silent_failure(page)
    return shots


def main() -> int:
    recipe_id: str = ""
    outputs: list[Path] = []
    with HubFixture() as fixture:
        recipe_id = _ensure_recipe_and_skills(fixture)
        print(f"recipe_id={recipe_id}")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for width, height in VIEWPORTS:
                    print(f"\n--- viewport {width}x{height} ---")
                    context = browser.new_context(
                        viewport={"width": width, "height": height},
                        device_scale_factor=2,
                        extra_http_headers={
                            "X-HoldSpeak-Token": fixture.owner_token,
                        },
                    )
                    try:
                        outputs.extend(
                            walk_viewport(
                                context.new_page(), fixture, width, height,
                                recipe_id,
                            )
                        )
                    finally:
                        context.close()
            finally:
                browser.close()

    print(f"\n{'='*60}")
    print(f"Ownership screenshots: {len(outputs)} saved")
    for p in outputs:
        print(f"  {p}")
    print(f"{'='*60}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
