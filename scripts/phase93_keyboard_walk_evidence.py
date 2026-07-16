#!/usr/bin/env python3
"""Capture the keyboard-only Web walk against the production HoldSpeak server.

The runner seeds a real isolated database, serves the built React client
through ``MeetingWebServer``, and proves the Phase 93 arrival is operable
without a pointer: the Create menu, the Tools shelf (Control+K search to a
Desk item's pull-out), and the Desk memory drawer all open, act, and close
by keyboard alone. No step uses the mouse. Any failed API response aborts
the evidence run.

    .venv/bin/python scripts/phase93_keyboard_walk_evidence.py [output-directory]
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
    ROOT / "pm/roadmap/holdspeak/phase-93-effortless-holdspeak/evidence/hs-93-01"
)

STEP_TIMEOUT_MS = 10_000


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


def active_matches(page: Page, selector: str) -> bool:
    return bool(
        page.evaluate(
            "sel => !!(document.activeElement && document.activeElement.matches(sel))",
            selector,
        )
    )


def active_text(page: Page) -> str:
    return str(
        page.evaluate("() => (document.activeElement?.textContent || '').trim()")
    )


def tab_to(page: Page, selector: str, label: str, max_tabs: int = 120) -> None:
    """Reach `selector` with Tab alone — a bounded walk of the focus order.

    Failing to reach it within the bound is a real accessibility defect
    (the control is not in the keyboard focus order), not a flaky wait.
    """
    for _ in range(max_tabs):
        if active_matches(page, selector):
            return
        page.keyboard.press("Tab")
    raise AssertionError(
        f"{label} ({selector}) was not reachable within {max_tabs} Tab presses: "
        "the control is missing from the keyboard focus order"
    )


def gone(page: Page, selector: str, label: str) -> None:
    page.locator(selector).wait_for(state="detached", timeout=STEP_TIMEOUT_MS)
    if page.locator(selector).count():
        raise AssertionError(f"{label} did not close")


def capture(page: Page, url: str, output: Path) -> None:
    failures = track_api_failures(page)
    page.set_default_timeout(STEP_TIMEOUT_MS)
    page.goto(f"{url}/", wait_until="domcontentloaded")
    page.locator('.desk-obj[aria-label^="Release checklist"]').first.wait_for()

    # 1. Create by keyboard: Tab to the chrome's Create entry, Enter opens
    # the menu (focus lands on the first choice), arrows move within it,
    # Enter on "Create Note" spawns the note and opens its in-world editor.
    tab_to(page, ".desk-create-button", "Create menu button")
    page.keyboard.press("Enter")
    page.locator(".desk-create-menu").wait_for()
    if not active_matches(page, ".desk-create-menu button"):
        raise AssertionError("opening the Create menu did not move focus into it")
    page.keyboard.press("ArrowDown")  # Note -> Zone
    page.keyboard.press("ArrowUp")  # back to Note
    if not active_matches(page, '[aria-label="Create Note"]'):
        raise AssertionError(
            f"arrow keys did not land on Create Note (focus: {active_text(page)!r})"
        )
    page.keyboard.press("Enter")
    page.locator(".desk-editor").wait_for()
    assert_clean(page, failures, "keyboard note creation")
    page.screenshot(path=str(output / "after-web-keyboard-create.png"))
    page.keyboard.press("Escape")
    gone(page, ".desk-editor", "the note editor")

    # 2. Tools by keyboard: Control+K opens the shelf with search focused,
    # a typed query plus ArrowDown reaches the seeded Desk note, Enter opens
    # its pull-out, Escape closes it.
    page.keyboard.press("Control+k")
    page.locator("#desk-tool-shelf").wait_for()
    if not active_matches(page, "#desk-tool-shelf input[type='search']"):
        raise AssertionError("Control+K did not focus the Tools search field")
    page.keyboard.type("Release")
    page.locator("#desk-tool-shelf .desk-tool-list button").first.wait_for()
    reached = False
    for _ in range(10):
        page.keyboard.press("ArrowDown")
        if "Release checklist" in active_text(page):
            reached = True
            break
    if not reached:
        raise AssertionError(
            "arrow keys never reached the 'Release checklist' Desk item "
            f"in the Tools shelf (focus: {active_text(page)!r})"
        )
    assert_clean(page, failures, "keyboard Tools search")
    page.screenshot(path=str(output / "after-web-keyboard-tools.png"))
    page.keyboard.press("Enter")
    pullout = page.locator(".desk-pullout", has_text="Release checklist")
    pullout.wait_for()
    gone(page, "#desk-tool-shelf", "the Tools shelf")
    page.keyboard.press("Escape")
    gone(page, ".desk-pullout", "the note pull-out")

    # 3. Desk memory by keyboard: Tab to the launcher, Enter opens the
    # drawer, Escape closes it.
    tab_to(page, ".desk-attention-launch", "Desk memory launcher")
    page.keyboard.press("Enter")
    page.locator("#desk-memory-drawer").wait_for()
    if "Desk memory" not in page.locator("#desk-memory-drawer").inner_text():
        raise AssertionError("Desk memory drawer lost its canonical name")
    assert_clean(page, failures, "keyboard Desk memory")
    page.screenshot(path=str(output / "after-web-keyboard-memory.png"))
    page.keyboard.press("Escape")
    gone(page, "#desk-memory-drawer", "the Desk memory drawer")

    assert_clean(page, failures, "the keyboard walk")


def main(output_directory: str | None = None) -> int:
    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="holdspeak-phase93-keyboard-") as temp_dir:
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

    print(f"keyboard-walk evidence written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
