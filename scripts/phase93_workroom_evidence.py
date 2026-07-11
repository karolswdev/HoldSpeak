#!/usr/bin/env python3
"""Capture HS-93-02 Web evidence against the real production server.

Unlike the generic Vite layout-shot harness, this boots ``MeetingWebServer``
against an isolated database and config. Any failed API request or visible
request-error copy aborts the run, so disconnected frames cannot become roadmap
evidence.

    .venv/bin/python scripts/phase93_workroom_evidence.py [output-directory]
"""

from __future__ import annotations

import re
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


DEFAULT_OUTPUT = ROOT / "web" / ".shots" / "phase-93-story-02-live"
VISIBLE_FAILURES = (
    "HoldSpeak could not complete that request",
    "HTTP 404",
)


def track_api_failures(page: Page) -> list[str]:
    failures: list[str] = []

    def observe(response: Response) -> None:
        if "/api/" in response.url and response.status >= 400:
            failures.append(f"{response.status} {response.url}")

    page.on("response", observe)
    return failures


def assert_clean(page: Page, api_failures: list[str], label: str) -> None:
    page.wait_for_timeout(700)
    body = page.locator("body").inner_text()
    visible = [text for text in VISIBLE_FAILURES if text in body]
    if api_failures or visible:
        detail = ", ".join([*api_failures, *visible])
        raise AssertionError(f"{label} is not clean: {detail}")


def open_integration_workroom(page: Page, url: str) -> None:
    page.goto(f"{url}/", wait_until="domcontentloaded")
    page.locator(".desk-tools-launch").click()
    page.get_by_role("link", name=re.compile("Integrations")).click()
    page.wait_for_url(re.compile(r"/settings\?room="))
    page.wait_for_selector(".workroom-bar")
    context = page.locator(".workroom-bar").inner_text()
    assert "FROM DESK" in context.upper()
    assert "Integration destinations" in context
    assert "Back to subject on Desk" in context


def main(output_directory: str | None = None) -> int:
    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="holdspeak-phase93-") as temp_dir:
        scratch = Path(temp_dir)
        config_module.CONFIG_FILE = scratch / "config.json"
        Config().save(config_module.CONFIG_FILE)
        reset_database()
        database = get_database(scratch / "holdspeak.db")
        database.milestones.mark(FIRST_DICTATION_SUCCESS)

        callbacks = WebRuntimeCallbacks(
            on_bookmark=MagicMock(
                return_value={"timestamp": 0.0, "label": "evidence"}
            ),
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

                desktop = browser.new_page(
                    viewport={"width": 1440, "height": 1000}
                )
                desktop_failures = track_api_failures(desktop)
                open_integration_workroom(desktop, url)
                assert_clean(desktop, desktop_failures, "desktop workroom")
                desktop.screenshot(
                    path=str(output / "after-web-context-desktop.png"),
                    full_page=False,
                )

                compact = browser.new_page(
                    viewport={"width": 560, "height": 1000}
                )
                compact_failures = track_api_failures(compact)
                open_integration_workroom(compact, url)
                assert_clean(compact, compact_failures, "compact workroom")
                compact.screenshot(
                    path=str(output / "after-web-context-compact.png"),
                    full_page=False,
                )

                direct = browser.new_page(
                    viewport={"width": 1440, "height": 420}
                )
                direct_failures = track_api_failures(direct)
                direct.goto(f"{url}/dictation", wait_until="domcontentloaded")
                direct.wait_for_selector(".workroom-bar")
                orientation = direct.locator(".workroom-bar").inner_text()
                assert "OPENED DIRECTLY" in orientation.upper()
                assert "Back to Desk" in orientation
                assert_clean(direct, direct_failures, "direct Dictation")
                direct.screenshot(
                    path=str(output / "after-web-direct-fallback.png"),
                    full_page=False,
                )

                browser.close()
        finally:
            server.stop()
            reset_database()

    print(f"HS-93-02 clean production Web evidence -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
