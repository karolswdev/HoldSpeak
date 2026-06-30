"""HS-69-06 — Qlippy in the cockpit proof.

Enables presence + mascot in config, boots the real server, navigates to a
cockpit page (NOT /presence), waits for the Qlippy dock to un-hide, then drives
window.qlippyCard.present(...) to show an actionable decision card with the
egress badge — proving the dock + cards now ride the main browser cockpit.

Run: uv run python scripts/screenshot_phase69_qlippy.py
"""
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

from playwright.sync_api import sync_playwright

import holdspeak.config as config_module
from holdspeak.db import get_database, reset_database
from holdspeak.meeting_session import IntelSnapshot, MeetingState
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
from datetime import datetime

OUT = Path("pm/roadmap/holdspeak/phase-69-web-recrafted/screenshots")
OUT.mkdir(parents=True, exist_ok=True)

CARD = {
    "key": "decision-demo",
    "sprite": "alert",
    "headline": "Decision needed",
    "detail": "Turn the accepted action “Wire the rate limiter behind a flag” into a GitHub issue?",
    "egress": {"scope": "local", "label": "Local"},
    "actions": [
        {"label": "Approve", "kind": "primary"},
        {"label": "Decline", "kind": "danger"},
        {"label": "Later", "kind": "ghost"},
    ],
}


def main():
    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    (tmp / "config.json").write_text(json.dumps({"presence": {"enabled": True, "mascot": True}}))
    reset_database()
    db = get_database(tmp / "holdspeak.db")
    db.meetings.save_meeting(MeetingState(
        id="m1", started_at=datetime(2026, 6, 5, 10, 0, 0),
        ended_at=datetime(2026, 6, 5, 10, 30, 0), title="API design follow-up",
        intel=IntelSnapshot(timestamp=0.0, action_items=[]),
    ))

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        host="127.0.0.1")
    url = server.start()
    time.sleep(1.0)
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.set_viewport_size({"width": 1180, "height": 760})
            pg.goto(f"{url}/history", wait_until="networkidle")
            # qlippy.js boots off /api/settings; wait for the dock to un-hide.
            pg.wait_for_selector("#qlippy:not([hidden])", timeout=4000)
            pg.wait_for_timeout(400)
            present = pg.evaluate("() => !!window.qlippyCard")
            pg.evaluate("(c) => window.qlippyCard.present(c)", CARD)
            pg.wait_for_selector("#qlippy-card.is-in", timeout=3000)
            pg.wait_for_timeout(700)  # let the slide-in + settle finish
            pg.screenshot(path=str(OUT / "qlippy-cockpit.png"))
            b.close()
        print("qlippyCard present:", present)
    finally:
        server.stop()
        reset_database()
    print("Saved Qlippy cockpit screenshot to", OUT)


if __name__ == "__main__":
    main()
