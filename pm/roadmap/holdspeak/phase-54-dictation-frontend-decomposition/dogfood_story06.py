#!/usr/bin/env python3
"""HS-54-06 closeout dogfood: the nudge surfaces on the carved frontend.

Complements `dogfood_story02.py` (all nine tabs + dry-run → moment-of-truth →
journal → corrections) by exercising the two nudge systems against a live
runtime with *seeded activity*:

    1. activity pre-briefing cards render from seeded ActivityRecords
       (source-cited, JS-rendered by the carved activity-nudges module);
    2. "Dictate with this" sets the visible pin;
    3. Clear removes the pin (and the shell hides when no cards remain);
    4. Dismiss removes a card;
    5. the discovery nudge still shows and dismisses (the HS-54-01 module);
    6. zero uncaught page errors across the run.

Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python pm/roadmap/holdspeak/phase-54-dictation-frontend-decomposition/dogfood_story06.py
"""
from __future__ import annotations

import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

OUT_DIR = Path(__file__).resolve().parent / "screenshots"


def _seed(db) -> None:
    db.activity.update_activity_privacy_settings(enabled=True)
    now = datetime.now()
    db.activity.upsert_activity_record(
        source_browser="safari",
        source_profile="default",
        url="https://github.com/karolswdev/HoldSpeak/issues/54",
        title="Dictation Frontend Decomposition",
        entity_type="github_issue",
        entity_id="karolswdev/HoldSpeak#54",
        visit_count=4,
        last_seen_at=now - timedelta(minutes=18),
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


def main() -> int:
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    db = get_database(tmp / "dogfood.db")
    _seed(db)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)
    failures: list[str] = []
    page_errors: list[str] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 1400})
            page.on("pageerror", lambda err: page_errors.append(str(err)))

            # 1. Seeded activity → source-cited cards render.
            page.goto(f"{url}/dictation", wait_until="networkidle")
            page.wait_for_selector("#activity-nudges:not([hidden])", timeout=5000)
            page.wait_for_selector(".activity-nudge", timeout=5000)
            print("PASS  activity nudges: seeded records render as cards")
            page.screenshot(path=str(OUT_DIR / "story06-nudges.png"))

            # 2. "Dictate with this" → the pin appears with the entity label.
            page.click(".activity-nudge .an-btn-primary")
            page.wait_for_selector("#activity-nudges-pin:not([hidden])", timeout=5000)
            entity = page.text_content("#activity-nudges-pin-entity") or ""
            if "github_issue" not in entity and "#54" not in entity:
                failures.append(f"pin entity label unexpected: {entity!r}")
            else:
                print(f"PASS  pin set: next dictation will include {entity!r}")
            page.screenshot(path=str(OUT_DIR / "story06-pinned.png"))

            # 3. Clear → pin hides again.
            page.click("#activity-nudges-pin-clear")
            page.wait_for_selector("#activity-nudges-pin", state="hidden", timeout=5000)
            print("PASS  pin cleared")

            # 4. Dismiss removes a card.
            before = len(page.query_selector_all(".activity-nudge"))
            page.click(".activity-nudge .an-btn-ghost")
            page.wait_for_timeout(400)
            after = len(page.query_selector_all(".activity-nudge"))
            if after >= before:
                failures.append(f"dismiss did not remove a card ({before} -> {after})")
            else:
                print(f"PASS  dismiss removed a card ({before} -> {after})")

            # 5. The discovery nudge still shows + dismisses.
            page.wait_for_selector("#kn-nudge", state="visible", timeout=5000)
            page.click("#kn-nudge-dismiss")
            page.wait_for_selector("#kn-nudge", state="hidden", timeout=5000)
            print("PASS  discovery nudge shows + dismisses")

            browser.close()
    finally:
        server.stop()
        reset_database()

    if page_errors:
        for err in page_errors:
            failures.append(f"pageerror: {err}")
    if failures:
        for f in failures:
            print(f"FAIL  {f}")
        print("RESULT: FAIL")
        return 1
    print("PASS  zero page errors across the whole run")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
