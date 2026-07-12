#!/usr/bin/env python3
"""Capture HS-93-06 partial-intelligence recovery on production Web.

This is implementation evidence only: an isolated real Hub/database serves the
built React client with a deterministically seeded partial Meeting. It does not
replace a real model fault, owner observation, or physical iPhone/iPad evidence.

    .venv/bin/python scripts/phase93_meeting_recovery_evidence.py [output-directory]
"""

from __future__ import annotations

import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from playwright.sync_api import Page, Response, sync_playwright  # noqa: E402

import holdspeak.config as config_module  # noqa: E402
from holdspeak.config import Config  # noqa: E402
from holdspeak.db import FIRST_DICTATION_SUCCESS, get_database, reset_database  # noqa: E402
from holdspeak.meeting_session import (  # noqa: E402
    IntelSnapshot,
    MeetingState,
    TranscriptSegment,
)
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks  # noqa: E402


DEFAULT_OUTPUT = (
    ROOT / "pm/roadmap/holdspeak/phase-93-effortless-holdspeak/evidence/hs-93-06"
)
MEETING_ID = "phase93-partial-meeting"
MEETING_TITLE = "Delivery resilience review"


def track_api_failures(page: Page) -> list[str]:
    failures: list[str] = []

    def observe(response: Response) -> None:
        if "/api/" in response.url and response.status >= 400:
            failures.append(f"{response.status} {response.url}")

    page.on("response", observe)
    return failures


def seed(database: object) -> None:
    started = datetime(2026, 7, 11, 14, 0, 0)
    meeting = MeetingState(
        id=MEETING_ID,
        started_at=started,
        ended_at=started + timedelta(minutes=24),
        title=MEETING_TITLE,
        tags=["delivery", "recovery"],
        segments=[
            TranscriptSegment(
                text="The transcript and decisions must survive a routing timeout.",
                speaker="Karol",
                start_time=4.0,
                end_time=10.0,
            ),
            TranscriptSegment(
                text="Retry only the remaining intelligence from the Meeting.",
                speaker="Alex",
                start_time=13.0,
                end_time=19.0,
            ),
        ],
        intel=IntelSnapshot(
            timestamp=24 * 60,
            topics=["Recovery", "Delivery"],
            action_items=[],
            summary="Base analysis completed before routed intelligence timed out.",
        ),
        capture_status="finalized",
        provenance="desktop",
    )
    database.meetings.save_meeting(meeting)
    database.plugins.record_artifact(
        artifact_id="phase93-retained-decision",
        meeting_id=meeting.id,
        artifact_type="decision",
        title="Retained recovery decision",
        body_markdown="Keep completed Meeting work through a partial failure.",
        structured_json={},
        confidence=0.94,
        status="draft",
        plugin_id="decision_extractor",
        plugin_version="1.0.0",
        sources=[],
    )
    database.intel.enqueue_intel_job(
        meeting.id,
        transcript_hash=meeting.transcript_hash(),
        reason="Routed intelligence queued.",
    )
    assert database.intel.claim_next_intel_job() is not None
    database.intel.mark_intel_job_partial(
        meeting.id,
        "Remaining routed intelligence did not finish: risk_heatmap (timeout).",
    )
    database.milestones.mark(FIRST_DICTATION_SUCCESS)


def assert_recovery(page: Page, headline: str) -> None:
    card = page.locator(".meeting-intel-recovery-card")
    card.wait_for()
    card.get_by_role("heading", name=headline).wait_for()
    for expected in (
        "Saved",
        "2 saved segments",
        "Summary, topics, and action items saved",
        "1 saved artifact",
    ):
        card.get_by_text(expected, exact=True).wait_for()


def capture(page: Page, url: str, output: Path) -> None:
    failures = track_api_failures(page)
    page.emulate_media(reduced_motion="reduce")
    page.goto(
        f"{url}/history?meeting={MEETING_ID}",
        wait_until="domcontentloaded",
    )
    assert_recovery(page, "Meeting saved · intelligence incomplete")
    page.get_by_role("button", name="Retry remaining").wait_for()
    page.get_by_role("button", name="Skip remaining").wait_for()
    page.screenshot(
        path=str(output / "after-web-history-partial-intelligence.png"),
        full_page=True,
    )

    page.goto(f"{url}/?open={MEETING_ID}", wait_until="domcontentloaded")
    page.locator(f'.desk-obj[aria-label^="{MEETING_TITLE}"]').wait_for()
    assert_recovery(page, "Meeting saved · intelligence incomplete")
    page.wait_for_timeout(500)
    page.screenshot(path=str(output / "after-web-desk-partial-intelligence.png"))

    page.get_by_role("button", name="Skip remaining").click()
    assert_recovery(page, "Meeting saved · intelligence skipped")
    page.reload(wait_until="domcontentloaded")
    assert_recovery(page, "Meeting saved · intelligence skipped")
    page.get_by_role("button", name="Retry remaining").wait_for()
    page.wait_for_timeout(500)
    page.screenshot(path=str(output / "after-web-desk-intelligence-skipped.png"))

    page.get_by_role("button", name="Retry remaining").click()
    assert_recovery(page, "Meeting saved · intelligence queued")
    page.reload(wait_until="domcontentloaded")
    assert_recovery(page, "Meeting saved · intelligence queued")
    page.get_by_role("button", name="Skip remaining").wait_for()
    # The queued job briefly rides the existing Mission Control conveyor. Let
    # that animation return to its resting chip before capturing the pull-out.
    page.wait_for_timeout(2000)
    page.screenshot(path=str(output / "after-web-desk-intelligence-retry.png"))

    if failures:
        raise AssertionError(f"production recovery walk had API failures: {failures}")


def main(output_directory: str | None = None) -> int:
    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="holdspeak-phase93-meeting-") as temp_dir:
        scratch = Path(temp_dir)
        config_module.CONFIG_FILE = scratch / "config.json"
        Config().save(config_module.CONFIG_FILE)
        reset_database()
        database = get_database(scratch / "holdspeak.db")
        seed(database)

        callbacks = WebRuntimeCallbacks(
            on_bookmark=MagicMock(return_value={"timestamp": 0.0, "label": "evidence"}),
            on_stop=MagicMock(return_value={"status": "stopped"}),
            get_state=MagicMock(return_value={}),
        )
        server = MeetingWebServer(callbacks, host="127.0.0.1")
        url = server.start()
        time.sleep(0.8)

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                capture(
                    browser.new_page(viewport={"width": 1440, "height": 1000}),
                    url,
                    output,
                )
                browser.close()
        finally:
            server.stop()
            reset_database()

    print(f"HS-93-06 production Web recovery evidence -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
