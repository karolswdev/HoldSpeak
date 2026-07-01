#!/usr/bin/env python3
"""Capture the HS-70-02 Home (the orientation front door).

Two states:
  1. home-empty.png  — fresh DB: the next-action band + guiding empty
     subtitles ("Nothing yet. Hold your key and speak." / "...import your
     first meeting.") — the "won't scare a new user" proof.
  2. home-seeded.png — a seeded meeting + a seeded journal entry: the mode
     cards' subtitles fill with the latest activity.

Run after `cd web && npm run build`:

    .venv/bin/python scripts/screenshot_phase70_home.py <out_dir>
"""
from __future__ import annotations

import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


def _shot(url: str, out: Path, name: str) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 1000})
        page.goto(f"{url}/", wait_until="networkidle")
        page.wait_for_selector(".home-modes")
        # let the dynamic subtitles + next-action settle
        page.wait_for_timeout(700)
        page.screenshot(path=str(out / name), full_page=True)
        browser.close()


def main(out_dir: str) -> int:
    import holdspeak.config as config_module
    from holdspeak.db import FIRST_DICTATION_SUCCESS, Database, get_database, reset_database
    from holdspeak.db.journal import DictationJournalRepository
    from holdspeak.meeting_session import MeetingState
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"

    # --- empty --- (mark the milestone so the first-run guard shows Home,
    # not the /welcome wizard; a truly-fresh user correctly gets /welcome.)
    reset_database()
    edb = get_database(tmp / "empty.db")
    edb.milestones.mark(FIRST_DICTATION_SUCCESS)
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
    )
    url = server.start()
    time.sleep(1.0)
    try:
        _shot(url, out, "home-empty.png")
    finally:
        server.stop()

    # --- seeded ---
    reset_database()
    db = get_database(tmp / "seeded.db")
    db.milestones.mark(FIRST_DICTATION_SUCCESS)
    db.meetings.save_meeting(
        MeetingState(
            id="m-seed-1",
            started_at=datetime.now(),
            ended_at=datetime.now(),
            title="Q3 planning sync",
            tags=["delivery"],
        )
    )
    journal = DictationJournalRepository(db._connection, db)
    journal.record(
        source="dictation",
        transcript="add a retry with backoff to the upload path",
        final_text="Add a retry with backoff to the upload path.",
        total_ms=820.0,
    )
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        dictation_journal_repository=journal,
    )
    url = server.start()
    time.sleep(1.0)
    try:
        _shot(url, out, "home-seeded.png")
    finally:
        server.stop()

    print(f"Wrote Home shots to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "phase70-home"))
