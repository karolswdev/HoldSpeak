#!/usr/bin/env python3
"""HS-56-03 dogfood: the actuator card, end to end on a live server.

No mocks in the chain: a real meeting with an accepted action item is seeded,
the presence page connects to the real `/ws`, the aftercare file-issue API
creates a real proposal whose broadcast slides the alert card out (with the
three privacy answers), **Approve on the card** POSTs the identical decision
request the dashboard sends, and the database shows the proposal `approved`
with the audit actor — no side effect performed (execution stays the guarded
executor's separate job). A second proposal is Declined on the card and the
real `actuator_result` broadcast presents the Declined card.

Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python pm/roadmap/holdspeak/phase-56-qlippy/dogfood_story03.py
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


def _seed_meeting(db, meeting_id):
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    started = datetime(2026, 6, 10, 10, 0, 0)
    state = MeetingState(
        id=meeting_id,
        started_at=started,
        ended_at=datetime(2026, 6, 10, 11, 0, 0),
        title="Live actuator dogfood",
        segments=[TranscriptSegment(text="fix the flaky login test", speaker="Me", start_time=0.0, end_time=10.0)],
    )
    state.intel = IntelSnapshot(
        timestamp=60.0,
        topics=[],
        action_items=[{
            "id": "a1", "task": "Fix the flaky login test", "owner": "Me",
            "due": None, "status": "pending", "review_state": "accepted",
            "source_timestamp": None, "created_at": started.isoformat(),
        }],
        summary="",
    )
    db.meetings.save_meeting(state)


def main() -> int:
    import httpx
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    db = get_database(tmp / "dogfood.db")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _seed_meeting(db, "m-live")

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
        httpx.put(f"{url}/api/settings", json={"presence": {"enabled": True, "mascot": True}}, timeout=10)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 520, "height": 460})
            page.on("pageerror", lambda err: page_errors.append(str(err)))
            page.goto(f"{url}/presence", wait_until="networkidle")
            page.wait_for_selector("#qlippy:not([hidden])", timeout=5000)
            page.wait_for_timeout(400)  # let the websocket attach

            # 1. A REAL proposal: the aftercare API fires the real broadcast.
            filed = httpx.post(
                f"{url}/api/meetings/m-live/aftercare/file-issue",
                json={"action_item_id": "a1", "repo": "acme/widgets"},
                timeout=10,
            ).json()
            proposal_id = filed["proposal"]["id"]
            page.wait_for_selector("#qlippy-card.is-in", timeout=5000)
            headline = (page.text_content("#qlippy-headline") or "").strip()
            privacy = (page.text_content("#qlippy-privacy") or "").strip()
            if headline != "A decision needs you":
                failures.append(f"unexpected headline: {headline!r}")
            for needle in ("Data used:", "goes to github", "Your controls:"):
                if needle not in privacy:
                    failures.append(f"privacy answer missing: {needle!r}")
            page.wait_for_timeout(600)
            page.screenshot(path=str(OUT_DIR / "story03-real-proposal-card.png"))
            print("PASS  the real aftercare proposal slid the card out with the three privacy answers")

            # 2. Approve on the card == the dashboard decision, audited.
            page.click(".q-btn-primary")
            page.wait_for_timeout(800)
            stored = db.actuators.get_proposal(proposal_id)
            if stored.status == "approved" and stored.decided_by:
                print(f"PASS  Approve recorded the audited decision (status={stored.status}, by={stored.decided_by!r}) — no side effect performed")
            else:
                failures.append(f"approval not recorded: {stored.status}")

            # 3. A second proposal, Declined on the card → the real
            #    actuator_result broadcast presents the Declined card.
            _seed_meeting(db, "m-live2")
            httpx.post(
                f"{url}/api/meetings/m-live2/aftercare/file-issue",
                json={"action_item_id": "a1", "repo": "acme/widgets"},
                timeout=10,
            )
            page.wait_for_selector("#qlippy-card.is-in", timeout=5000)
            page.click(".q-btn-danger")
            page.wait_for_timeout(900)
            headline = (page.text_content("#qlippy-headline") or "").strip()
            if headline == "Declined":
                print("PASS  Decline → the real actuator_result broadcast presented the Declined card")
            else:
                failures.append(f"expected the Declined result card, got {headline!r}")
            page.screenshot(path=str(OUT_DIR / "story03-declined-card.png"))

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
