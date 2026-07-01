#!/usr/bin/env python3
"""HS-70-04: Activity folded into Dictation.

  1. activity-ledger.png  — /activity reframed as a Dictation sub-view
     ("Activity ledger", a "← Dictation" back link, the nav shows Dictation).
  2. studio-no-activity.png — the Studio dropdown, now 6 tools (Activity gone).

    .venv/bin/python scripts/screenshot_phase70_activity.py <out_dir>
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


def main(out_dir: str) -> int:
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    get_database(tmp / "act.db")

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
    )
    url = server.start()
    time.sleep(1.0)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})

            page.goto(f"{url}/activity", wait_until="networkidle")
            page.wait_for_selector(".activity-back")
            page.wait_for_timeout(500)
            page.screenshot(path=str(out / "activity-ledger.png"))

            page.goto(f"{url}/dictation", wait_until="networkidle")
            page.wait_for_selector(".topnav-studio-summary")
            page.click(".topnav-studio-summary")
            page.wait_for_selector(".topnav-studio-panel", state="visible")
            page.wait_for_timeout(250)
            page.screenshot(
                path=str(out / "studio-no-activity.png"),
                clip={"x": 0, "y": 0, "width": 1280, "height": 360},
            )
            browser.close()
    finally:
        server.stop()
    print(f"Wrote activity-fold shots to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "phase70-activity"))
