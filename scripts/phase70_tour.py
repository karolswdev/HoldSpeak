#!/usr/bin/env python3
"""Comprehensive Phase-70 tour screenshots on one seeded instance.

    .venv/bin/python scripts/phase70_tour.py <out_dir>
"""
from __future__ import annotations

import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


def main(out_dir: str) -> int:
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.db import FIRST_DICTATION_SUCCESS, get_database, reset_database
    from holdspeak.db.journal import DictationJournalRepository
    from holdspeak.meeting_session import MeetingState
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    db = get_database(tmp / "tour.db")
    db.milestones.mark(FIRST_DICTATION_SUCCESS)  # set-up user (Home renders, no guard)

    now = datetime.now()
    for i, title in enumerate(["Q3 planning sync", "Incident retro: checkout 500s", "Design review: onboarding"]):
        db.meetings.save_meeting(MeetingState(
            id=f"m-{i}", started_at=now - timedelta(days=i, hours=2),
            ended_at=now - timedelta(days=i, hours=1), title=title, tags=["delivery"],
        ))
    journal = DictationJournalRepository(db._connection, db)
    for t, f in [
        ("add a retry with backoff to the upload path", "Add a retry with backoff to the upload path."),
        ("draft a reply to the vendor about the SLA", "Draft a reply to the vendor about the SLA."),
    ]:
        journal.record(source="dictation", transcript=t, final_text=f, total_ms=780.0)

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        dictation_journal_repository=journal,
    )
    url = server.start()
    time.sleep(1.0)

    shots = [
        ("01-home", "/", ".home-modes", None),
        ("02-dictation", "/dictation", ".cockpit-tabs", None),
        ("03-meetings", "/history", ".hero-actions", None),
        ("04-activity-ledger", "/activity", ".activity-back", None),
        ("05-studio", "/studio", ".studio-grid", None),
        ("06-welcome", "/welcome", None, None),
        ("07-setup-health", "/setup", None, None),
        ("08-settings", "/settings", ".set-health-link", None),
    ]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            for name, route, sel, _ in shots:
                page.goto(f"{url}{route}", wait_until="networkidle")
                if sel:
                    try:
                        page.wait_for_selector(sel, timeout=6000)
                    except Exception:
                        pass
                page.wait_for_timeout(700)
                page.screenshot(path=str(out / f"tour-{name}.png"), full_page=True)
                print(f"  shot tour-{name}.png")

            # nav dropdown open (on a fresh page)
            page.goto(f"{url}/dictation", wait_until="networkidle")
            page.wait_for_selector(".topnav-studio-summary")
            page.click(".topnav-studio-summary")
            page.wait_for_selector(".topnav-studio-panel", state="visible")
            page.wait_for_timeout(300)
            page.screenshot(path=str(out / "tour-09-nav-studio-open.png"),
                            clip={"x": 0, "y": 0, "width": 1280, "height": 380})
            print("  shot tour-09-nav-studio-open.png")

            # mobile menu
            page2 = browser.new_page(viewport={"width": 720, "height": 1000})
            page2.goto(f"{url}/", wait_until="networkidle")
            page2.wait_for_selector("[data-nav-toggle]")
            page2.click("[data-nav-toggle]")
            page2.wait_for_selector(".topnav[data-open] .topnav-nav", state="visible")
            page2.click(".topnav-studio-summary")
            page2.wait_for_timeout(400)
            page2.screenshot(path=str(out / "tour-10-mobile-nav.png"),
                             clip={"x": 0, "y": 0, "width": 720, "height": 660})
            print("  shot tour-10-mobile-nav.png")
            browser.close()
    finally:
        server.stop()
    print(f"Wrote tour to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "phase70-tour"))
