#!/usr/bin/env python3
"""HS-70-06: the Studio index — the advanced tier framed.

  1. studio-index.png — /studio: the six power tools as framed cards.
  2. studio-dropdown.png — the nav dropdown with the "ADVANCED ->" index link.

    .venv/bin/python scripts/screenshot_phase70_studio.py <out_dir>
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
    get_database(tmp / "studio.db")

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
    )
    url = server.start()
    time.sleep(1.0)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})

            page.goto(f"{url}/studio", wait_until="networkidle")
            page.wait_for_selector(".studio-grid")
            page.wait_for_timeout(400)
            page.screenshot(path=str(out / "studio-index.png"), full_page=True)

            page.goto(f"{url}/dictation", wait_until="networkidle")
            page.wait_for_selector(".topnav-studio-summary")
            page.click(".topnav-studio-summary")
            page.wait_for_selector(".topnav-studio-index", state="visible")
            page.wait_for_timeout(250)
            page.screenshot(
                path=str(out / "studio-dropdown.png"),
                clip={"x": 0, "y": 0, "width": 1280, "height": 400},
            )
            browser.close()
    finally:
        server.stop()
    print(f"Wrote studio shots to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "phase70-studio"))
