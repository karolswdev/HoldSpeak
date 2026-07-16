#!/usr/bin/env python3
"""Capture the HS-93-08 1,000-item scale contract against the production server.

The runner seeds a real isolated database with 1,000 mixed primitives
(notes, knowledge, personas, workflows, a few filed into a zone), serves the
built React client through ``MeetingWebServer``, and proves the scale story:

- the spatial Desk renders a bounded floater set with an honest count chip
  (never silent truncation);
- the semantic list mode lists everything, paged by 100 with a visible count;
- Tools search finds a needle item by title (it reads the store's records,
  not the rendered nodes) and opens its pull-out.

Any failed API response aborts the evidence run. Build the web bundle first
(``npm --prefix web run build``).

    .venv/bin/python scripts/phase93_scale_evidence.py [output-directory]
"""

from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from playwright.sync_api import Page, Response, sync_playwright  # noqa: E402

import holdspeak.config as config_module  # noqa: E402
from holdspeak.config import Config  # noqa: E402
from holdspeak.db import FIRST_DICTATION_SUCCESS, get_database, reset_database  # noqa: E402
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks  # noqa: E402


DEFAULT_OUTPUT = (
    ROOT / "pm/roadmap/holdspeak/phase-93-effortless-holdspeak/evidence/hs-93-08"
)

# Spread within the hub's per-lane list bound (500 per kind by default) so
# the seed is a mixed 1,000 the server actually serves in full.
NOTE_COUNT = 450  # plus the needle note = 451 notes
KB_COUNT = 200
RECIPE_COUNT = 200
WORKFLOW_COUNT = 149
FILED_COUNT = 5  # notes shelved into the zone (hidden from the spatial root)
NEEDLE_TITLE = "Meridian launch brief"

TOTAL = NOTE_COUNT + 1 + KB_COUNT + RECIPE_COUNT + WORKFLOW_COUNT
SPATIAL_TOTAL = TOTAL - FILED_COUNT
MAX_FLOATERS = 200
LIST_PAGE = 100


def track_api_failures(page: Page) -> list[str]:
    failures: list[str] = []

    def observe(response: Response) -> None:
        if "/api/" in response.url and response.status >= 400:
            failures.append(f"{response.status} {response.url}")

    page.on("response", observe)
    return failures


def assert_clean(page: Page, api_failures: list[str], label: str) -> None:
    page.wait_for_timeout(400)
    if api_failures:
        raise AssertionError(f"{label} is not clean: {', '.join(api_failures)}")


def seed(database: object) -> None:
    for i in range(NOTE_COUNT):
        database.notes.upsert(
            note_id=f"scale-note-{i:04d}",
            title=f"Field note {i:04d}",
            body_markdown=f"Observation {i:04d} from the scale sweep.",
        )
    database.notes.upsert(
        note_id="scale-needle",
        title=NEEDLE_TITLE,
        body_markdown="The one record the search must always reach.",
    )
    for i in range(KB_COUNT):
        database.kbs.upsert(kb_id=f"scale-kb-{i:03d}", name=f"Corpus {i:03d}")
    for i in range(RECIPE_COUNT):
        database.recipes.upsert(
            recipe_id=f"scale-recipe-{i:03d}",
            name=f"Reviewer {i:03d}",
            avatar="🤖",
        )
    for i in range(WORKFLOW_COUNT):
        database.workflows.upsert(
            workflow_id=f"scale-wf-{i:03d}", name=f"Sweep {i:03d}"
        )
    database.directories.upsert(directory_id="scale-zone", name="Archive")
    for i in range(FILED_COUNT):
        database.directory_memberships.upsert(
            primitive_id=f"note:scale-note-{i:04d}", directory_id="scale-zone"
        )
    database.milestones.mark(FIRST_DICTATION_SUCCESS)


def capture(page: Page, url: str, output: Path) -> dict[str, float]:
    failures = track_api_failures(page)
    timings: dict[str, float] = {}

    # 1. The spatial Desk: bounded floaters + the honest count chip.
    t0 = time.monotonic()
    page.goto(f"{url}/", wait_until="domcontentloaded")
    chip = page.locator(".desk-scale-chip")
    chip.wait_for()
    timings["spatial_first_paint_s"] = time.monotonic() - t0
    chip_text = chip.inner_text()
    expected = f"Showing {MAX_FLOATERS} of {SPATIAL_TOTAL}"
    if expected not in chip_text:
        raise AssertionError(f"count chip says {chip_text!r}, wanted {expected!r}")
    floaters = page.locator(".desk-obj").count()
    if floaters != MAX_FLOATERS:
        raise AssertionError(f"{floaters} floaters rendered, wanted {MAX_FLOATERS}")
    assert_clean(page, failures, "spatial desk at scale")
    page.screenshot(path=str(output / "after-web-scale-desk.png"))

    # 2. The semantic list mode: everything, paged by 100.
    t0 = time.monotonic()
    page.get_by_role("button", name="List", exact=True).click()
    page.locator(".desk-listmode").wait_for()
    timings["list_mode_s"] = time.monotonic() - t0
    rows = page.locator(".desk-list-table tbody tr")
    if rows.count() != LIST_PAGE:
        raise AssertionError(f"list shows {rows.count()} rows, wanted {LIST_PAGE}")
    status = page.locator(".desk-list-status").inner_text()
    if f"Showing {LIST_PAGE} of {TOTAL}" not in status:
        raise AssertionError(f"list status says {status!r}")
    page.get_by_role("button", name=f"Show {LIST_PAGE} more").click()
    page.wait_for_timeout(150)
    if rows.count() != 2 * LIST_PAGE:
        raise AssertionError(
            f"after show-more the list has {rows.count()} rows, wanted {2 * LIST_PAGE}"
        )
    assert_clean(page, failures, "list mode at scale")
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(150)
    page.screenshot(path=str(output / "after-web-scale-list.png"))

    # 3. Tools search reaches the needle no page has rendered.
    t0 = time.monotonic()
    page.get_by_role("button", name="Tools ⌘K").click()
    page.get_by_placeholder("Search tools and Desk items").fill("Meridian")
    hit = page.locator(".desk-tool-shelf").get_by_role("button", name=NEEDLE_TITLE)
    hit.wait_for()
    hit.click()
    pullout = page.locator(".desk-pullout")
    pullout.wait_for()
    timings["search_to_open_s"] = time.monotonic() - t0
    if NEEDLE_TITLE not in pullout.inner_text():
        raise AssertionError("the opened pull-out is not the needle record")
    assert_clean(page, failures, "search and open at scale")
    page.screenshot(path=str(output / "after-web-scale-search.png"))
    return timings


def main(output_directory: str | None = None) -> int:
    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="holdspeak-phase93-scale-") as temp_dir:
        scratch = Path(temp_dir)
        config_module.CONFIG_FILE = scratch / "config.json"
        Config().save(config_module.CONFIG_FILE)
        reset_database()
        database = get_database(scratch / "holdspeak.db")
        seed(database)

        callbacks = WebRuntimeCallbacks(
            on_bookmark=MagicMock(return_value={"timestamp": 0.0, "label": "evidence"}),
            on_stop=MagicMock(return_value={"status": "stopped"}),
            get_state=MagicMock(
                return_value={
                    "id": None,
                    "started_at": None,
                    "duration": 0,
                    "bookmarks": [],
                }
            ),
        )
        server = MeetingWebServer(callbacks, host="127.0.0.1")
        url = server.start()
        time.sleep(0.8)

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                timings = capture(page, url, output)
                browser.close()
        finally:
            server.stop()

    print(
        f"scale evidence written to {output}\n"
        f"  seeded={TOTAL} spatial_rendered={MAX_FLOATERS}/{SPATIAL_TOTAL} "
        f"list_page={LIST_PAGE}\n"
        f"  timings={ {k: round(v, 2) for k, v in timings.items()} }"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
