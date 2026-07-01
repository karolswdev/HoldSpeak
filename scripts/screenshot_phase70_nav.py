#!/usr/bin/env python3
"""Capture the HS-70-01 two-mode nav reframe (Phase 70, Legible Product).

Boots a real MeetingWebServer (serving the built bundle) and shoots the new
TopNav in four states:
  1. wide, Studio collapsed  — Home · Dictation · Meetings · Studio ▾
  2. wide, Studio expanded   — the advanced tier dropdown (7 items)
  3. wide, on /workbench     — Studio auto-opens + the active item highlighted
  4. narrow, menu open       — the column nav with Studio inline (mobile)

Run after `cd web && npm run build`:

    .venv/bin/python scripts/screenshot_phase70_nav.py <out_dir>
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
    from holdspeak.db import Database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    db = Database(tmp / "nav.db")

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        ),
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)

    nav_clip = {"x": 0, "y": 0, "width": 1280, "height": 360}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()

            # --- wide, collapsed (on /dictation, a plain mode page) ---
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"{url}/dictation", wait_until="networkidle")
            page.wait_for_selector(".topnav-studio-summary")
            page.wait_for_timeout(200)
            page.screenshot(path=str(out / "nav-01-collapsed.png"), clip=nav_clip)

            # --- wide, expanded (open the Studio disclosure) ---
            page.click(".topnav-studio-summary")
            page.wait_for_selector(".topnav-studio-panel", state="visible")
            page.wait_for_timeout(250)
            page.screenshot(path=str(out / "nav-02-studio-open.png"), clip=nav_clip)
            page.close()

            # --- wide, on /workbench: Studio auto-open + active highlight ---
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"{url}/workbench", wait_until="networkidle")
            page.wait_for_selector(".topnav-studio[open] .topnav-studio-panel")
            page.wait_for_timeout(250)
            page.screenshot(path=str(out / "nav-03-workbench-active.png"), clip=nav_clip)
            page.close()

            # --- narrow, menu open (mobile column) ---
            page = browser.new_page(viewport={"width": 720, "height": 1000})
            page.goto(f"{url}/dictation", wait_until="networkidle")
            page.wait_for_selector("[data-nav-toggle]")
            page.click("[data-nav-toggle]")
            page.wait_for_selector(".topnav[data-open] .topnav-nav", state="visible")
            # expand Studio inline so the tier is visible in the column
            page.click(".topnav-studio-summary")
            page.wait_for_timeout(300)
            page.screenshot(
                path=str(out / "nav-04-mobile-menu.png"),
                clip={"x": 0, "y": 0, "width": 720, "height": 640},
            )
            page.close()

            browser.close()
    finally:
        server.stop()

    print(f"Wrote nav shots to {out}")
    return 0


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "phase70-nav"
    raise SystemExit(main(out_dir))
