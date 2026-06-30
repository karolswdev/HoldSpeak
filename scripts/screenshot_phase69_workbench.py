"""HS-69-10 — node canvas foundation proof.

Loads /workbench and captures: the default workflow rendered as a node chain
with typed bezier cables on the dot grid; a node dragged (the cable follows);
and a preset switch. Requires the built bundle + Playwright.
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
            pg.set_viewport_size({"width": 1280, "height": 760})
            pg.goto(f"{url}/workbench", wait_until="networkidle")
            pg.wait_for_selector(".wb-node", timeout=4000)
            pg.wait_for_timeout(500)
            nodes = pg.eval_on_selector_all(".wb-node", "els => els.length")
            cables = pg.eval_on_selector_all(".wb-cable", "els => els.length")
            pg.screenshot(path=str(OUT / "workbench-default.png"))

            # drag the middle node down-right; the cables should follow
            box = pg.query_selector_all(".wb-node")[1].bounding_box()
            pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            pg.mouse.down()
            pg.mouse.move(box["x"] + 160, box["y"] + 150, steps=12)
            pg.mouse.up()
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(OUT / "workbench-dragged.png"))

            # switch to a richer preset
            pg.click('.wb-preset-btn[data-preset-id="preset-triage"]')
            pg.wait_for_timeout(400)
            pg.screenshot(path=str(OUT / "workbench-triage.png"))
            triage_nodes = pg.eval_on_selector_all(".wb-node", "els => els.length")
            b.close()
        print(f"default: {nodes} nodes / {cables} cables | triage: {triage_nodes} nodes")
    finally:
        server.stop()
        reset_database()
    print("Saved workbench screenshots to", OUT)


if __name__ == "__main__":
    main()
