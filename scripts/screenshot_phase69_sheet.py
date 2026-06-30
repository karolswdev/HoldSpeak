"""HS-69-05 — premium sheet uplift proof.

Triggers window.holdspeakConfirm on a real page and screenshots the dialog in
both the danger (destructive) and the affirmative (non-danger) states, so the
grab handle, glyph-chip header, top-lit hairline, tinted-glow backdrop, and the
accent "Done" pill are all visible. Requires the built bundle + Playwright.

Run: uv run python scripts/screenshot_phase69_sheet.py
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


def shoot(pg, opts, name):
    # NB: do not return the promise — holdspeakConfirm stays pending until the
    # user acts, and Playwright would await a returned promise forever.
    pg.evaluate("(o) => { window.holdspeakConfirm(o); }", opts)
    pg.wait_for_selector("#holdspeak-confirm-dialog[open]", timeout=3000)
    pg.wait_for_timeout(350)  # let the open animation settle
    pg.screenshot(path=str(OUT / name))
    # resolve + close so the next prompt opens clean
    pg.evaluate("() => document.querySelector('[data-confirm-cancel]').click()")
    pg.wait_for_timeout(250)


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
            pg.set_viewport_size({"width": 900, "height": 620})
            pg.goto(f"{url}/settings", wait_until="networkidle")
            pg.wait_for_timeout(400)
            shoot(pg, {
                "title": "Delete this meeting?",
                "body": "This permanently removes the meeting and its derived artifacts.",
                "scopeNote": "This removes local annotations. Source data on GitHub is untouched.",
                "confirmLabel": "Delete", "cancelLabel": "Keep", "danger": True,
            }, "sheet-danger.png")
            shoot(pg, {
                "title": "Apply these settings?",
                "body": "Voice typing will use the new language and symbol dictionary.",
                "confirmLabel": "Apply", "cancelLabel": "Cancel", "danger": False,
            }, "sheet-confirm.png")
            b.close()
    finally:
        server.stop()
        reset_database()
    print("Saved sheet screenshots to", OUT)


if __name__ == "__main__":
    main()
