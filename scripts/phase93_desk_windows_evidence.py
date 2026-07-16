#!/usr/bin/env python3
"""Capture the desk-window contract against the production HoldSpeak server.

The runner seeds a real isolated database, serves the built React client
through ``MeetingWebServer``, and proves the Phase 93 UI remediation: desk
panels are windows (coexist, drag, resize, persist, restore, raise) instead
of fixtures glued to one corner. Any failed API response or visible request
failure aborts the evidence run.

    .venv/bin/python scripts/phase93_desk_windows_evidence.py [output-directory]
"""

from __future__ import annotations

import json
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
    ROOT / "pm/roadmap/holdspeak/phase-93-effortless-holdspeak/evidence/ui-remediation"
)


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
    database.notes.upsert(
        note_id="release",
        title="Release checklist",
        body_markdown="Ship after checks pass. Confirm the rollout owner.",
    )
    database.notes.upsert(
        note_id="risks",
        title="Open risks",
        body_markdown="Rollback path unverified.",
    )
    database.milestones.mark(FIRST_DICTATION_SUCCESS)


def box(page: Page, selector: str) -> dict:
    b = page.locator(selector).bounding_box()
    if not b:
        raise AssertionError(f"{selector} has no bounding box")
    return b


def z_index(page: Page, selector: str) -> int:
    return int(
        page.eval_on_selector(
            selector, "el => Number(getComputedStyle(el).zIndex) || 0"
        )
    )


def drag(page: Page, selector: str, dx: float, dy: float) -> None:
    b = box(page, selector)
    cx, cy = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
    page.mouse.move(cx, cy)
    page.mouse.down()
    for i in range(1, 9):
        page.mouse.move(cx + dx * i / 8, cy + dy * i / 8)
    page.mouse.up()
    page.wait_for_timeout(200)


def capture(page: Page, url: str, output: Path) -> None:
    failures = track_api_failures(page)
    page.goto(f"{url}/", wait_until="domcontentloaded")

    # 1. Two windows coexist: the note's pull-out AND the Ask composer.
    note = page.locator('.desk-obj[aria-label^="Release checklist"]').first
    note.wait_for()
    note.click(modifiers=["Shift"])
    page.get_by_role("button", name="✦ Ask AI").click()
    page.locator(".desk-ask").wait_for()
    note.click()
    page.locator(".desk-pullout:not(.desk-ask)", has_text="Release checklist").wait_for()
    if not page.locator(".desk-ask").is_visible():
        raise AssertionError("opening the pull-out destroyed the Ask window")
    assert_clean(page, failures, "coexisting windows")
    page.screenshot(path=str(output / "after-web-windows-coexist.png"))

    # 2. Drag the Ask window by its head (fully clear of the pull-out so
    # its corner grip is exposed); the rect persists on drop.
    before = box(page, ".desk-ask")
    drag(page, ".desk-ask .desk-pullout-head .desk-pullout-title", -560, 40)
    after = box(page, ".desk-ask")
    if abs(after["x"] - before["x"]) < 150:
        raise AssertionError(
            f"Ask window did not move (x {before['x']} -> {after['x']})"
        )
    stored = json.loads(
        page.evaluate("localStorage.getItem('hs.desk.panels') || '{}'")
    )
    if "ask" not in stored:
        raise AssertionError("dragged Ask rect was not persisted")

    # 3. Resize by the corner grip.
    size_before = box(page, ".desk-ask")
    drag(page, ".desk-ask .desk-window-grip", 90, -60)
    size_after = box(page, ".desk-ask")
    if size_after["width"] - size_before["width"] < 40:
        raise AssertionError(
            f"Ask window did not resize (w {size_before['width']} -> {size_after['width']})"
        )
    page.screenshot(path=str(output / "after-web-windows-arranged.png"))

    # 4. Focus raises: pointer-down on the pull-out puts it above Ask.
    page.locator(".desk-pullout:not(.desk-ask) .desk-pullout-head").click()
    page.wait_for_timeout(150)
    if not z_index(page, ".desk-pullout:not(.desk-ask)") > z_index(page, ".desk-ask"):
        raise AssertionError("clicking the pull-out did not raise it above Ask")

    # 5. The arranged rect survives a full reload.
    arranged = box(page, ".desk-ask")
    page.reload(wait_until="domcontentloaded")
    note = page.locator('.desk-obj[aria-label^="Release checklist"]').first
    note.wait_for()
    note.click(modifiers=["Shift"])
    page.get_by_role("button", name="✦ Ask AI").click()
    page.locator(".desk-ask").wait_for()
    page.wait_for_timeout(900)  # let the entrance spring settle
    restored = box(page, ".desk-ask")
    if abs(restored["x"] - arranged["x"]) > 4 or abs(restored["y"] - arranged["y"]) > 4:
        raise AssertionError(
            f"arranged rect not restored ({arranged} -> {restored})"
        )
    assert_clean(page, failures, "window restore")
    page.screenshot(path=str(output / "after-web-windows-restored.png"))

    # 6. Desk memory opens as one named window.
    page.get_by_role("button", name="Desk memory").click()
    drawer = page.locator("#desk-memory-drawer")
    drawer.wait_for()
    if "Desk memory" not in drawer.inner_text():
        raise AssertionError("Desk memory drawer lost its canonical name")
    assert_clean(page, failures, "Desk memory window")
    page.screenshot(path=str(output / "after-web-desk-memory-window.png"))


def main(output_directory: str | None = None) -> int:
    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="holdspeak-phase93-windows-") as temp_dir:
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
                capture(page, url, output)
                browser.close()
        finally:
            server.stop()

    print(f"desk-window evidence written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
