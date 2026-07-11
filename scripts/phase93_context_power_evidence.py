#!/usr/bin/env python3
"""Capture HS-93-04 Web evidence against the production HoldSpeak server.

The runner seeds a real isolated database, serves the built React client through
``MeetingWebServer``, and drives the selection/tool/inspector/authority path.
Any failed API response or visible request failure aborts the evidence run.

    .venv/bin/python scripts/phase93_context_power_evidence.py [output-directory]
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
import holdspeak.plugins.builtin.webhook_post_actuator as webhook_module  # noqa: E402
from holdspeak.config import Config  # noqa: E402
from holdspeak.db import FIRST_DICTATION_SUCCESS, get_database, reset_database  # noqa: E402
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks  # noqa: E402


DEFAULT_OUTPUT = (
    ROOT
    / "pm/roadmap/holdspeak/phase-93-effortless-holdspeak/evidence/hs-93-04"
)
VISIBLE_FAILURES = (
    "HoldSpeak could not complete that request",
    "Selected material is retained; retry the action",
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
    page.wait_for_timeout(500)
    visible = [text for text in VISIBLE_FAILURES if text in page.locator("body").inner_text()]
    if api_failures or visible:
        detail = ", ".join([*api_failures, *visible])
        raise AssertionError(f"{label} is not clean: {detail}")


def select_release_note(page: Page) -> None:
    note = page.locator('.desk-obj[aria-label^="Release checklist"]').first
    note.wait_for()
    note.click(modifiers=["Shift"])
    page.locator(".desk-obj.selected", has_text="Release checklist").wait_for()


def open_tools(page: Page) -> None:
    page.locator(".desk-tools-launch").click()
    page.locator("#desk-tool-shelf").wait_for()


def seed(database: object) -> None:
    database.notes.upsert(
        note_id="release",
        title="Release checklist",
        body_markdown="Ship after checks pass. Confirm the rollout owner.",
    )
    database.recipes.upsert(
        recipe_id="scout",
        name="Scout",
        role="Find concrete facts",
        system_prompt="Extract concrete facts and open questions.",
    )
    database.workflows.upsert(
        workflow_id="release-workflow",
        name="Release review",
        prompt="Summarize release readiness and remaining risk.",
    )
    database.projects.create_project(
        project_id="orion",
        name="Project Orion",
        description="Launch readiness and follow-through.",
    )
    database.project_relationships.upsert(
        project_id="orion",
        resource_ref="note:release",
        relationship="member",
    )
    database.milestones.mark(FIRST_DICTATION_SUCCESS)


def capture_desktop(page: Page, url: str, output: Path) -> None:
    failures = track_api_failures(page)
    page.goto(f"{url}/", wait_until="domcontentloaded")
    select_release_note(page)
    open_tools(page)

    shelf = page.locator("#desk-tool-shelf")
    for text in (
        "Ask Scout about Release checklist",
        "Run Release review on Release checklist",
        "Send Release checklist to Slack",
        "Project Orion",
        "This device",
    ):
        if text not in shelf.inner_text():
            raise AssertionError(f"selection tool shelf is missing {text!r}")
    assert_clean(page, failures, "selection tool shelf")
    page.screenshot(path=str(output / "after-web-selection-tools.png"))

    page.get_by_role(
        "button", name=re.compile(r"^Send Release checklist to Slack")
    ).click()
    inspector = page.locator(".desk-tool-inspector")
    inspector.wait_for()
    if "Configured Slack workspace" not in inspector.inner_text():
        raise AssertionError("Integration inspector omitted the destination")
    page.screenshot(path=str(output / "after-web-integration-inspector.png"))

    page.get_by_role("button", name="Send Release checklist to Slack").click()
    page.get_by_role("button", name="Approve and send to Slack").wait_for()
    page.screenshot(path=str(output / "after-web-integration-proposal.png"))
    page.get_by_role("button", name="Approve and send to Slack").click()
    page.get_by_text("Receipt · executed").wait_for()
    assert_clean(page, failures, "Integration Receipt")
    page.screenshot(path=str(output / "after-web-integration-receipt.png"))

    page.get_by_role("button", name="Return to Release checklist").click()
    page.locator(".desk-pullout", has_text="Release checklist").wait_for()
    page.locator(".desk-pullout-close").click()

    open_tools(page)
    page.get_by_role("button", name=re.compile(r"^Project Orion")).click()
    project = page.locator(".desk-tool-inspector", has_text="Project Orion")
    project.wait_for()
    project.get_by_text("Release checklist").wait_for()
    assert_clean(page, failures, "Project inspector")
    page.screenshot(path=str(output / "after-web-project-inspector.png"))


def capture_compact(page: Page, url: str, output: Path) -> None:
    failures = track_api_failures(page)
    page.goto(f"{url}/", wait_until="domcontentloaded")
    select_release_note(page)
    open_tools(page)
    page.get_by_text("For selection").wait_for()
    assert_clean(page, failures, "compact contextual tools")
    page.screenshot(path=str(output / "after-web-selection-tools-compact.png"))


def main(output_directory: str | None = None) -> int:
    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="holdspeak-phase93-context-") as temp_dir:
        scratch = Path(temp_dir)
        config_module.CONFIG_FILE = scratch / "config.json"
        config = Config()
        config.meeting.slack_webhook_url = (
            "https://hooks.slack.com/services/T0/B0/evidence-placeholder"
        )
        config.save(config_module.CONFIG_FILE)
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
        original_post = webhook_module._default_post
        webhook_module._default_post = lambda _url, _body, *, timeout: (
            webhook_module.WebhookResponse(status=200, body="ok")
        )

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                capture_desktop(
                    browser.new_page(viewport={"width": 1440, "height": 1000}),
                    url,
                    output,
                )
                capture_compact(
                    browser.new_page(viewport={"width": 560, "height": 1000}),
                    url,
                    output,
                )
                browser.close()
        finally:
            webhook_module._default_post = original_post
            server.stop()
            reset_database()

    print(f"HS-93-04 clean production Web evidence -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
