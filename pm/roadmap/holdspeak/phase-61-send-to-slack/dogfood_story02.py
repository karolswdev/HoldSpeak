#!/usr/bin/env python3
"""HS-61-02 dogfood: the Send-to-Slack surfaces on a live server, in a real browser.

The off-proof first: with no webhook URL configured, /history's aftercare card
renders ZERO Slack affordances (no button, no mention). Then the URL is
configured and the same card grows the buttons; clicking one creates a real
proposal that lands in the existing approval section with the honest flash.
Nothing is approved here — no egress in this dogfood (HS-61-04 owns the real
POST against a local receiver).

Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python pm/roadmap/holdspeak/phase-61-send-to-slack/dogfood_story02.py
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
URL_VALUE = "https://hooks.slack.com/services/T0/B0/dogfood-secret"


def main() -> int:
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.config import Config
    from holdspeak.db import get_database, reset_database
    from holdspeak.meeting_session import IntelSnapshot, MeetingState
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    Config().save(path=config_module.CONFIG_FILE)
    reset_database()
    db = get_database(tmp / "dogfood.db")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    db.meetings.save_meeting(
        MeetingState(
            id="m-dogfood",
            started_at=datetime(2026, 6, 11, 10, 0, 0),
            title="Weekly product sync",
            intel=IntelSnapshot(
                timestamp=0.0,
                action_items=[
                    {
                        "id": "a1",
                        "task": "Wire the rate limiter into the gateway",
                        "owner": "Priya",
                        "due": "Friday",
                        "status": "pending",
                        "review_state": "accepted",
                        "source_timestamp": None,
                        "created_at": datetime(2026, 6, 11, 10, 0, 0).isoformat(),
                    },
                    {
                        "id": "a2",
                        "task": "Write the changelog for the rollout",
                        "owner": "Sam",
                        "due": None,
                        "status": "pending",
                        "review_state": "pending",
                        "source_timestamp": None,
                        "created_at": datetime(2026, 6, 11, 10, 0, 0).isoformat(),
                    },
                ],
            ),
        )
    )

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
        ),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)
    failures: list[str] = []
    page_errors: list[str] = []

    def check(ok: bool, label: str) -> None:
        print(("PASS  " if ok else "FAIL  ") + label)
        if not ok:
            failures.append(label)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 920})
            page.on("pageerror", lambda err: page_errors.append(str(err)))

            def open_meeting():
                page.goto(f"{url}/history", wait_until="networkidle")
                page.click("text=Weekly product sync")
                page.wait_for_selector(".aftercare-card", timeout=5000)
                page.wait_for_timeout(400)

            # 1. The off-proof: unconfigured renders no VISIBLE Slack
            #    affordance (x-show gating is how every optional surface in
            #    this product hides; hidden markup in the DOM is the Alpine
            #    norm — what matters is nothing is visible or clickable).
            open_meeting()
            check(
                page.locator(".slack-btn:visible").count() == 0,
                "unconfigured: zero visible Slack buttons",
            )
            page.click("text=Draft follow-up")
            page.wait_for_selector(".followup-pre", timeout=5000)
            note_off = page.locator(".followup-draft .loop-note").text_content() or ""
            check(
                "Preview and copy only; nothing is sent." in note_off,
                "unconfigured: the draft note keeps the local-only truth",
            )
            page.screenshot(path=str(OUT_DIR / "story02-off.png"))

            # 2. Configure the URL (the consent moment) and reload.
            config = Config.load()
            config.meeting.slack_webhook_url = URL_VALUE
            config.save(path=config_module.CONFIG_FILE)
            open_meeting()
            buttons = page.locator(".aftercare-card .slack-btn")
            check(buttons.count() >= 1, "configured: the digest Send to Slack button renders")
            page.screenshot(path=str(OUT_DIR / "story02-configured-card.png"))

            # 3. The draft view gains its own button + the honest note flips.
            page.click("text=Draft follow-up")
            page.wait_for_selector(".followup-pre", timeout=5000)
            page.wait_for_timeout(300)
            draft_card = page.text_content(".aftercare-card") or ""
            check(
                "nothing is sent until you approve it below" in draft_card,
                "configured: the draft note states the approval truth",
            )
            check(
                page.locator(".followup-draft .slack-btn").count() == 1,
                "configured: the draft has its own Send to Slack button",
            )
            page.screenshot(path=str(OUT_DIR / "story02-draft.png"))

            # 4. Clicking creates a PROPOSAL (no egress): it lands in the
            #    approval section with the honest flash.
            page.click(".aftercare-head-actions .slack-btn")
            page.wait_for_timeout(600)
            flash = page.text_content("body") or ""
            check("Nothing is sent yet" in flash, "the flash states nothing was sent")
            proposals = db.actuators.list_proposals("m-dogfood")
            check(
                len(proposals) == 1 and proposals[0].status == "proposed",
                "exactly one proposal recorded, status proposed (no egress)",
            )
            check(
                URL_VALUE not in (proposals[0].preview or "")
                and "dogfood-secret" not in str(proposals[0].payload),
                "the credential is nowhere on the proposal",
            )
            page.wait_for_timeout(400)
            page.screenshot(path=str(OUT_DIR / "story02-proposal.png"), full_page=True)

            # 5. The settings field with the honest copy.
            page.goto(f"{url}/settings", wait_until="networkidle")
            page.fill(".set-search input, input[placeholder*='Search']", "slack")
            page.wait_for_timeout(500)
            settings_text = page.text_content("body") or ""
            check(
                "Send to Slack webhook URL" in settings_text,
                "settings: the field surfaces under search 'slack'",
            )
            check(
                "only after you approve" in settings_text
                and "stored in your local config and shown nowhere else" in settings_text,
                "settings: the honest copy ships",
            )
            page.screenshot(path=str(OUT_DIR / "story02-settings.png"))

            browser.close()
    finally:
        server.stop()

    check(not page_errors, f"zero uncaught page errors (saw {page_errors!r})")
    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} failure(s))")
        return 1
    print("RESULT: PASS (all checks + zero page errors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
