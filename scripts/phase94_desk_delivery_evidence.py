#!/usr/bin/env python3
"""Capture the Delivery-on-the-Desk experience (HS-94-08) against production.

The runner seeds a real, isolated delivery read model — it registers THIS
repository as a Delivery Source through the vendored ``dw`` and binds one Work
attempt — serves the built React client through ``MeetingWebServer``, and drives
the Phase 94 acceptance surface end to end:

  1. the Delivery board opens and a Source renders its honest freshness;
  2. a Story opens its evidence dossier IN a desk window (no route change);
  3. a Work attempt shows its provenance and freshness;
  4. the immutable-target terminal window subscribes to a node-issued target.

Any failed API response or visible request failure aborts the run. A live tmux
session is created so the terminal target is real (the subscription must answer
a 200 snapshot, never a typed absence).

    .venv/bin/python scripts/phase94_desk_delivery_evidence.py [output-directory]
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DEFAULT_OUTPUT = (
    ROOT / "pm/roadmap/holdspeak/phase-94-delivery-runtime/evidence/hs-94-08"
)
TMUX_SESSION = "hs94evidence"


def track_api_failures(page) -> list[str]:
    failures: list[str] = []

    def observe(response) -> None:
        if "/api/" in response.url and response.status >= 400:
            failures.append(f"{response.status} {response.url}")

    page.on("response", observe)
    return failures


def assert_clean(page, api_failures: list[str], label: str) -> None:
    page.wait_for_timeout(400)
    if api_failures:
        raise AssertionError(f"{label} is not clean: {', '.join(api_failures)}")


def seed_desk(database: object) -> None:
    from holdspeak.db import FIRST_DICTATION_SUCCESS

    database.notes.upsert(
        note_id="release",
        title="Release checklist",
        body_markdown="Ship after checks pass.",
    )
    database.milestones.mark(FIRST_DICTATION_SUCCESS)


def seed_delivery(database: object) -> None:
    """Register this repo as a live Delivery Source and bind one attempt —
    the same read model the hub routes serve, populated deterministically."""
    from holdspeak.delivery import DeliveryCollector, DeliveryRegistry
    from holdspeak.delivery.attempts import (
        WorkAttemptService,
        resolver_from_registry,
    )

    registry = DeliveryRegistry()  # DEFAULT path, now under the temp HOME
    collector = DeliveryCollector(registry)
    result = collector.register_source(str(ROOT), label="holdspeak")
    source_id = result["source"]["source_id"]
    worktree_id = result["worktree_id"]

    attempts = WorkAttemptService(
        database.work_attempts, resolver=resolver_from_registry(registry)
    )
    attempts.manual_attach(
        source_id=source_id,
        worktree_id=worktree_id,
        project="holdspeak",
        story_id="HS-94-08",
        actor="desk-owner",
    )
    return source_id


def open_board(page) -> None:
    page.locator(".desk-dlv-tab").first.click()
    page.locator(".desk-dlv-board").wait_for(timeout=15000)
    # The registered source lands live (dw runs behind the snapshot).
    page.locator(".desk-dlv-fresh.is-live").first.wait_for(timeout=20000)


def capture(page, url: str, output: Path) -> None:
    failures = track_api_failures(page)
    page.goto(f"{url}/", wait_until="domcontentloaded")
    page.locator(".desk-dlv-tab").first.wait_for(timeout=15000)

    # 1. The Delivery board opens; a Source renders its honest freshness.
    open_board(page)
    assert_clean(page, failures, "delivery board")
    page.screenshot(path=str(output / "after-web-delivery-board.png"))

    # 2. A Work attempt shows its provenance and freshness.
    attempt = page.locator(".desk-dlv-attempt").first
    attempt.wait_for(timeout=15000)
    text = attempt.inner_text()
    if "HS-94-08" not in text:
        raise AssertionError(f"attempt row missing its Story: {text!r}")
    page.screenshot(path=str(output / "after-web-delivery-attempt.png"))

    # 3. A Story opens its evidence dossier IN a desk window.
    story = page.locator(
        ".desk-mc-story:has(.desk-dlv-evidence) .desk-mc-story-pick"
    ).first
    story.wait_for(timeout=15000)
    story.click()
    dossier = page.locator(".desk-dlv-dossier")
    dossier.wait_for(timeout=15000)
    # The dossier fetch resolves the manifest — wait for the captured-runs
    # section (not just the window shell) before proving it.
    dossier.get_by_text("Captured runs", exact=True).wait_for(timeout=15000)
    assert_clean(page, failures, "story dossier window")
    page.screenshot(path=str(output / "after-web-delivery-dossier.png"))

    # 4. The immutable-target terminal window subscribes to a node target.
    session = page.locator(".desk-dlv-session-open").first
    session.wait_for(timeout=15000)
    session.click()
    terminal = page.locator(".desk-dlv-terminal")
    terminal.wait_for(timeout=15000)
    # A live subscription paints the pane; a typed absence would fail-clean.
    page.locator(".desk-dlv-terminal .desk-session-pane").wait_for(timeout=15000)
    target_line = page.locator(".desk-dlv-target-line").inner_text()
    if "Target" not in target_line:
        raise AssertionError(f"terminal window lost its target identity: {target_line!r}")
    assert_clean(page, failures, "immutable-target terminal window")
    page.screenshot(path=str(output / "after-web-delivery-terminal.png"))


def main(output_directory: str | None = None) -> int:
    from playwright.sync_api import sync_playwright

    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="holdspeak-phase94-delivery-") as temp_dir:
        scratch = Path(temp_dir)
        # Isolate the delivery source registry into the scratch dir so the run
        # starts empty and only sees what we register — without touching $HOME
        # (Playwright resolves its browser cache from $HOME).
        import holdspeak.delivery.registry as registry_module

        registry_module.DEFAULT_REGISTRY_PATH = scratch / "delivery_sources.json"

        import holdspeak.config as config_module
        from holdspeak.config import Config
        from holdspeak.db import get_database, reset_database
        from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

        config_module.CONFIG_FILE = scratch / "config.json"
        Config().save(config_module.CONFIG_FILE)
        reset_database()
        database = get_database(scratch / "holdspeak.db")
        seed_desk(database)
        seed_delivery(database)

        subprocess.run(["tmux", "kill-session", "-t", TMUX_SESSION], check=False)
        subprocess.run(["tmux", "new-session", "-d", "-s", TMUX_SESSION], check=True)

        callbacks = WebRuntimeCallbacks(
            on_bookmark=MagicMock(return_value={"timestamp": 0.0, "label": "evidence"}),
            on_stop=MagicMock(return_value={"status": "stopped"}),
            get_state=MagicMock(
                return_value={"id": None, "started_at": None, "duration": 0, "bookmarks": []}
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
                # iPad-width pass: no horizontal overflow, board still reachable.
                narrow = browser.new_page(viewport={"width": 834, "height": 1112})
                narrow_failures = track_api_failures(narrow)
                narrow.goto(f"{url}/", wait_until="domcontentloaded")
                open_board(narrow)
                scroll_w = narrow.evaluate("document.documentElement.scrollWidth")
                if scroll_w > 834 + 2:
                    raise AssertionError(f"horizontal overflow at iPad width: {scroll_w}px")
                assert_clean(narrow, narrow_failures, "iPad-width board")
                narrow.screenshot(path=str(output / "after-web-delivery-ipad.png"))
                browser.close()
        finally:
            server.stop()
            subprocess.run(["tmux", "kill-session", "-t", TMUX_SESSION], check=False)

    print(f"delivery desk evidence written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
