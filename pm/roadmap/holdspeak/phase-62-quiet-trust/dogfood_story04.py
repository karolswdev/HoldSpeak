#!/usr/bin/env python3
"""HS-62-04 closeout dogfood: the badge on REAL broadcast-driven cards.

Story 01 proved the shell renders the badge; this proves the production
event path end to end with no injected cards: a REAL file-issue route call
fires the real `actuator_proposed` broadcast and the card arrives with
"☁ github"; a REAL journal correction (taught, reach > 0) fires the real
`learning_event` broadcast and the card arrives with "⌂ Local". Zero
privacy prose anywhere on either card; zero page errors.

Run after building the web bundle.
"""
from __future__ import annotations

import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

OUT_DIR = Path(__file__).resolve().parent / "screenshots"

RETIRED = ("Data used", "nothing is sent", "stays on this machine",
           "Your controls", "leaves your machine", "Local only:")


def main() -> int:
    import httpx
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.config import Config
    from holdspeak.db import get_database, reset_database
    from holdspeak.meeting_session import IntelSnapshot, MeetingState
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    config = Config()
    config.presence.enabled = True
    config.presence.mascot = True
    config.save(path=config_module.CONFIG_FILE)
    reset_database()
    db = get_database(tmp / "dogfood.db")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    started = datetime(2026, 6, 12, 10, 0, 0)
    state = MeetingState(
        id="m-close",
        started_at=started,
        ended_at=datetime(2026, 6, 12, 11, 0, 0),
        title="Quiet trust closeout",
    )
    state.intel = IntelSnapshot(
        timestamp=60.0,
        action_items=[{
            "id": "a1", "task": "Fix the flaky login test", "owner": "Me",
            "due": None, "status": "pending", "review_state": "accepted",
            "source_timestamp": None, "created_at": started.isoformat(),
        }],
    )
    db.meetings.save_meeting(state)

    # Two similar journal rows so a taught correction has real reach.
    entry = db.dictation_journal.record(
        source="dictation",
        transcript="follow up with sam about the launch",
        final_text="follow up with sam about the launch",
    )
    db.dictation_journal.record(
        source="dictation",
        transcript="follow up with sam about launch timing",
        final_text="follow up with sam about launch timing",
    )

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)
    failures: list[str] = []
    page_errors: list[str] = []

    def check(ok, label):
        print(("PASS  " if ok else "FAIL  ") + label)
        if not ok:
            failures.append(label)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 520, "height": 460})
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            page.goto(f"{url}/presence", wait_until="networkidle")
            page.wait_for_selector("#qlippy:not([hidden])", timeout=5000)
            page.wait_for_timeout(500)

            # 1. The REAL proposal broadcast → the cloud badge.
            filed = httpx.post(
                f"{url}/api/meetings/m-close/aftercare/file-issue",
                json={"action_item_id": "a1", "repo": "acme/widgets"},
                timeout=10,
            ).json()
            check(bool(filed.get("proposal")), "the real file-issue route filed a proposal")
            page.wait_for_selector("#qlippy-card.is-in", timeout=8000)
            page.wait_for_timeout(500)
            badge = page.text_content("#qlippy-egress") or ""
            check(badge == "☁ github", f"the broadcast-driven card carries '☁ github' (got {badge!r})")
            card_text = page.text_content("#qlippy-card") or ""
            for phrase in RETIRED:
                check(phrase not in card_text, f"no retired prose on the decision card: {phrase!r}")
            page.screenshot(path=str(OUT_DIR / "story04-broadcast-cloud.png"))
            page.evaluate("window.qlippyCard.resolve()")
            page.wait_for_timeout(700)

            # 2. A REAL taught correction → the local badge.
            corrected = httpx.post(
                f"{url}/api/dictation/journal/{entry.id}/correct",
                json={"kind": "intent", "value": "action_item"},
                timeout=10,
            ).json()
            check(
                bool(corrected.get("taught")) and corrected.get("similar", 0) > 0,
                f"the real teach landed with reach (taught={corrected.get('taught')}, similar={corrected.get('similar')})",
            )
            page.wait_for_selector("#qlippy-card.is-in", timeout=8000)
            page.wait_for_timeout(500)
            badge = page.text_content("#qlippy-egress") or ""
            check(badge == "⌂ Local", f"the broadcast-driven learned card carries '⌂ Local' (got {badge!r})")
            card_text = page.text_content("#qlippy-card") or ""
            for phrase in RETIRED:
                check(phrase not in card_text, f"no retired prose on the learned card: {phrase!r}")
            page.screenshot(path=str(OUT_DIR / "story04-broadcast-local.png"))

            browser.close()
    finally:
        server.stop()
        reset_database()

    check(not page_errors, f"zero uncaught page errors (saw {page_errors!r})")
    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} failure(s))")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
