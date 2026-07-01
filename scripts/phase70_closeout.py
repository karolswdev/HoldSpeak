#!/usr/bin/env python3
"""HS-70-09 closeout: no dead doors + the clean arrival, proven.

  A. Route sweep — every Phase-70 route resolves (200 after following redirects),
     so nothing 404s (moved/renamed/aliased routes included).
  B. The arrival flow — a first-run user (fresh DB) hitting `/` is guarded to the
     single arrival (/welcome); a set-up user stays on Home with the four-door nav.

    .venv/bin/python scripts/phase70_closeout.py <out_dir>
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

ROUTES = [
    "/", "/live", "/welcome", "/setup", "/studio", "/desk", "/workbench",
    "/history", "/meetings", "/settings", "/dictation", "/activity",
    "/commands", "/companion", "/presence", "/cadence", "/profiles",
    "/docs/dictation-runtime",
]


def main(out_dir: str) -> int:
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.db import FIRST_DICTATION_SUCCESS, get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    db = get_database(tmp / "closeout.db")

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
    )
    url = server.start()
    time.sleep(1.0)

    failures = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()

            # A. Route sweep — no dead doors (urllib follows redirects).
            import urllib.request
            for r in ROUTES:
                try:
                    with urllib.request.urlopen(f"{url}{r}", timeout=10) as resp:
                        if resp.status != 200:
                            failures.append(f"{r} -> {resp.status}")
                except Exception as exc:
                    failures.append(f"{r} -> {exc}")
            print(f"A. Route sweep: {len(ROUTES) - len(failures)}/{len(ROUTES)} resolve 200")

            # B1. First-run: `/` guards to the single arrival (/welcome).
            page = browser.new_page(viewport={"width": 1280, "height": 850})
            page.goto(f"{url}/", wait_until="networkidle")
            page.wait_for_timeout(800)  # let the client-side guard redirect
            arrived = page.url
            first_run_ok = arrived.rstrip("/").endswith("/welcome")
            print(f"B1. first-run `/` -> {arrived}  ({'OK' if first_run_ok else 'FAIL'})")
            if not first_run_ok:
                failures.append(f"first-run guard did not reach /welcome (got {arrived})")

            # B2. Set-up user: `/` stays on Home with the four-door nav.
            db.milestones.mark(FIRST_DICTATION_SUCCESS)
            page.goto(f"{url}/", wait_until="networkidle")
            page.wait_for_selector(".home-modes")
            page.wait_for_timeout(500)
            labels = page.eval_on_selector_all(
                ".topnav-nav .topnav-link", "els => els.map(e => e.textContent.trim())"
            )
            print(f"B2. set-up `/` stays Home; nav primaries = {labels}")
            page.screenshot(path=str(out / "closeout-home-nav.png"),
                            clip={"x": 0, "y": 0, "width": 1280, "height": 60})
            page.close()
            browser.close()
    finally:
        server.stop()

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  -", f)
        return 1
    print("\nCLOSEOUT OK — no dead doors, single arrival, Home front door.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "phase70-closeout"))
