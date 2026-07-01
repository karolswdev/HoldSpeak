#!/usr/bin/env python3
"""HS-70-03: the consolidated first-run arrival.

  1. welcome-arrival.png — /welcome, the single first-run arrival (guard sends
     new users here; it ends by landing on Home and teaches both modes).
  2. setup-health.png    — /setup demoted from a second "Welcome" to the
     returning-user "Setup & health" surface (eyebrow retitled).
  3. settings-health-link.png — the Settings aside surfaces the health check.

    .venv/bin/python scripts/screenshot_phase70_firstrun.py <out_dir>
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
    get_database(tmp / "fr.db")

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
    )
    url = server.start()
    time.sleep(1.0)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})

            page.goto(f"{url}/welcome", wait_until="networkidle")
            page.wait_for_timeout(600)
            page.screenshot(path=str(out / "welcome-arrival.png"))

            page.goto(f"{url}/setup", wait_until="networkidle")
            page.wait_for_timeout(700)
            page.screenshot(path=str(out / "setup-health.png"))

            page.goto(f"{url}/settings", wait_until="networkidle")
            page.wait_for_timeout(600)
            page.screenshot(path=str(out / "settings-health-link.png"), full_page=False)

            browser.close()
    finally:
        server.stop()
    print(f"Wrote first-run shots to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "phase70-firstrun"))
