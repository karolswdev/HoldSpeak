"""HS-69-09 — generation theater proof (simulated frames).

Boots the cockpit and drives the theater through its lifecycle via
window.__hsTheater (the same entry the intel WS frames drive): reveal →
streaming (the orb pulses) → complete (the constellation lights). Captures the
streaming state and the lit-constellation state.

The real-metal (live intel) proof is a separate run; see the evidence file.

Run: uv run python scripts/screenshot_phase69_theater.py
"""
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

from playwright.sync_api import sync_playwright

from holdspeak.db import get_database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

OUT = Path("pm/roadmap/holdspeak/phase-69-web-recrafted/screenshots")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    tmp = Path(tempfile.mkdtemp())
    reset_database()
    get_database(tmp / "holdspeak.db")
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
            pg.set_viewport_size({"width": 1100, "height": 760})
            pg.goto(f"{url}/history", wait_until="networkidle")
            pg.wait_for_timeout(400)
            has_hook = pg.evaluate("() => typeof window.__hsTheater === 'object'")

            # 1) reveal + stream (the orb pulses faster on tokens)
            pg.evaluate("() => window.__hsTheater.onStatus({ state: 'live' })")
            pg.evaluate(
                """() => { for (let i=0;i<6;i++) setTimeout(()=>window.__hsTheater.onToken('chunk '), i*120); }""")
            pg.wait_for_selector(".hs-theater.is-on.is-streaming", timeout=3000)
            pg.wait_for_timeout(600)
            pg.screenshot(path=str(OUT / "theater-streaming.png"))

            # 2) complete → the constellation lights for the produced types
            pg.evaluate(
                """() => window.__hsTheater.onComplete({
                    summary: 'The team agreed to ship the rate limiter behind a flag.',
                    action_items: [{ task: 'Wire the flag' }, { task: 'Pick a name' }],
                    topics: ['rate limiting', 'naming'],
                    decisions: [{ decision: 'Use Postgres' }]
                })""")
            pg.wait_for_timeout(900)  # let the staggered lighting settle
            pg.screenshot(path=str(OUT / "theater-complete.png"))
            el = pg.query_selector(".hs-theater-card")
            if el:
                el.screenshot(path=str(OUT / "theater-card.png"))
            lit = pg.evaluate("() => document.querySelectorAll('.ht-node.is-lit').length")
            b.close()
        print("theater hook:", has_hook, "| lit nodes:", lit)
    finally:
        server.stop()
        reset_database()
    print("Saved theater screenshots to", OUT)


if __name__ == "__main__":
    main()
