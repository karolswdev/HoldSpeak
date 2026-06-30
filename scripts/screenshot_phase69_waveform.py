"""HS-69-08 — reactive mic waveform proof.

Boots the cockpit and pumps a simulated speech envelope through
window.__hsWaveformLevel (the same entry the `audio_level` WS frame drives), so
the floating meter reveals and the canvas fills with reactive bars. Captures the
active state (speech) and the rest state (silence → hidden).

Run: uv run python scripts/screenshot_phase69_waveform.py
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
            pg.set_viewport_size({"width": 1100, "height": 720})
            pg.goto(f"{url}/history", wait_until="networkidle")
            pg.wait_for_timeout(400)
            has_hook = pg.evaluate("() => typeof window.__hsWaveformLevel === 'function'")
            # pump a simulated speech envelope (~1.4 s) into the meter
            pg.evaluate(
                """() => {
                    let t = 0;
                    window.__wfTimer = setInterval(() => {
                        t += 0.06;
                        const env = 0.55 + 0.4 * Math.sin(t * 5.0);
                        const lvl = Math.max(0, env * (0.6 + 0.4 * Math.abs(Math.sin(t * 17))));
                        window.__hsWaveformLevel({ level: lvl });
                    }, 55);
                }""")
            pg.wait_for_selector(".hs-waveform.is-active", timeout=3000)
            pg.wait_for_timeout(1400)  # let the bar history fill
            pg.screenshot(path=str(OUT / "waveform-active.png"))
            # crop to just the meter
            el = pg.query_selector(".hs-waveform")
            if el:
                el.screenshot(path=str(OUT / "waveform-meter.png"))
            # stop pumping → after the idle window it settles flat + hides
            pg.evaluate("() => clearInterval(window.__wfTimer)")
            pg.wait_for_timeout(1600)
            still_active = pg.evaluate(
                "() => document.querySelector('.hs-waveform').classList.contains('is-active')")
            b.close()
        print("waveform hook present:", has_hook, "| still active after silence:", still_active)
    finally:
        server.stop()
        reset_database()
    print("Saved waveform screenshots to", OUT)


if __name__ == "__main__":
    main()
