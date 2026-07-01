#!/usr/bin/env python3
"""HS-70-05: Meetings mode made whole.

  1. meetings-empty.png  — /history retitled "Meetings" with the entry actions
     (Start a meeting / Import) promoted to the hero.
  2. meetings-import.png — the import panel opened from the hero action.

    .venv/bin/python scripts/screenshot_phase70_meetings.py <out_dir>
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
    get_database(tmp / "mtg.db")

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
    )
    url = server.start()
    time.sleep(1.0)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 950})

            page.goto(f"{url}/history", wait_until="networkidle")
            page.wait_for_selector(".hero-actions")
            page.wait_for_timeout(500)
            page.screenshot(path=str(out / "meetings-empty.png"))

            page.click(".hero-import")
            page.wait_for_selector(".import-panel", state="visible")
            page.wait_for_timeout(500)
            page.screenshot(path=str(out / "meetings-import.png"))

            browser.close()
    finally:
        server.stop()
    print(f"Wrote meetings shots to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "phase70-meetings"))
