#!/usr/bin/env python3
"""HS-53-04: capture the Activity Pre-Briefing nudges on the dictation cockpit.

Boots one real ``MeetingWebServer`` against a temp DB seeded with a handful of
local activity records (no browser, no mic, no LLM), opens ``/dictation``, and
screenshots the populated nudge card list and the empty (activity-off) state.

Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python scripts/screenshot_activity_nudges.py
"""
from __future__ import annotations

import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

OUT_DIR = (
    Path(__file__).parent.parent
    / "pm" / "roadmap" / "holdspeak" / "phase-53-activity-prebriefing" / "screenshots"
)


def _seed(db, *, enabled: bool) -> None:
    db.activity.update_activity_privacy_settings(enabled=enabled)
    if not enabled:
        return
    now = datetime.now()
    db.activity.upsert_activity_record(
        source_browser="safari",
        source_profile="default",
        url="https://github.com/karolswdev/HoldSpeak/issues/53",
        title="Activity Pre-Briefing",
        entity_type="github_issue",
        entity_id="karolswdev/HoldSpeak#53",
        visit_count=4,
        last_seen_at=now - timedelta(minutes=18),
    )
    db.activity.upsert_activity_record(
        source_browser="safari",
        source_profile="default",
        url="https://github.com/karolswdev/HoldSpeak/pull/41",
        title="Phase 53: scaffold Activity Pre-Briefing",
        entity_type="github_pull_request",
        entity_id="karolswdev/HoldSpeak#41",
        visit_count=3,
        last_seen_at=now - timedelta(hours=1),
    )
    db.activity.upsert_activity_record(
        source_browser="firefox",
        source_profile="work",
        url="https://example.atlassian.net/browse/HS-805",
        title="HS-805 shared context",
        entity_type="jira_issue",
        entity_id="HS-805",
        visit_count=2,
        last_seen_at=now - timedelta(hours=2),
    )


def _capture(suffix: str, *, enabled: bool, click_dictate: bool = False) -> None:
    from playwright.sync_api import sync_playwright

    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    reset_database()
    db = get_database(tmp / "holdspeak.db")
    _seed(db, enabled=enabled)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        ),
        host="127.0.0.1",
    )
    url = server.start()
    time.sleep(1.0)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1200, "height": 900})
            page.goto(f"{url}/dictation", wait_until="networkidle")
            page.wait_for_timeout(800)
            # Make sure the nudges have had a beat to render after the GET.
            page.wait_for_function(
                "() => {"
                "  const el = document.getElementById('activity-nudges');"
                "  if (!el) return true;"
                "  return true;"
                "}",
                timeout=3000,
            )
            page.wait_for_timeout(400)
            shell_visible = page.evaluate(
                "() => {"
                "  const el = document.getElementById('activity-nudges');"
                "  return !!el && !el.hidden;"
                "}"
            )
            print(f"[{suffix}] activity-nudges shell visible = {shell_visible}")
            target = page.locator("#activity-nudges")
            if shell_visible:
                target.scroll_into_view_if_needed()
                page.wait_for_timeout(200)
                if click_dictate:
                    # Click the first record card's "Dictate with this" so the
                    # selection-pin renders; the screenshot captures the full flow.
                    page.locator(".activity-nudge[data-kind='record'] .an-btn-primary").first.click()
                    page.wait_for_selector("#activity-nudges-pin:not([hidden])", timeout=2000)
                    page.wait_for_timeout(200)
                # Crop tight to the nudge surface for a clean record.
                target.screenshot(path=str(OUT_DIR / f"nudges-{suffix}.png"))
            else:
                # Empty / off — capture the top of the page so the absence is honest.
                page.screenshot(
                    path=str(OUT_DIR / f"nudges-{suffix}.png"),
                    clip={"x": 0, "y": 0, "width": 1200, "height": 380},
                )
            print(f"Wrote {OUT_DIR / ('nudges-' + suffix + '.png')}")
            browser.close()
    finally:
        server.stop()
        reset_database()


def main() -> int:
    _capture("populated", enabled=True)
    _capture("pinned", enabled=True, click_dictate=True)
    _capture("off", enabled=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
