"""HS-69-11 — node canvas wiring + inspector proof.

On /workbench: open the inspector on a step node (type chips + editable prompt);
draw a NEW type-compatible cable by dragging an output port onto an input port;
and add a node from the palette. Requires the built bundle + Playwright.
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


def center(box):
    return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2


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
            pg.set_viewport_size({"width": 1320, "height": 780})
            pg.goto(f"{url}/workbench", wait_until="networkidle")
            pg.wait_for_selector(".wb-node", timeout=4000)
            pg.wait_for_timeout(400)
            nodes = pg.query_selector_all(".wb-node")

            # 1) inspector: click the Summarize step
            nodes[1].click()
            pg.wait_for_selector(".wb-inspector.is-open", timeout=2000)
            pg.fill("[data-wb-insp-prompt]", "in three crisp bullets")
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(OUT / "workbench-inspector.png"))

            cables_before = pg.eval_on_selector_all(".wb-cable", "e => e.length")

            # 2) wiring: drag the SOURCE output port onto the EXTRACT input port
            #    (text → text, compatible → a new cable commits)
            src_out = nodes[0].query_selector(".wb-port-out")
            ext_in = nodes[2].query_selector(".wb-port-in")
            ax, ay = center(src_out.bounding_box())
            bx, by = center(ext_in.bounding_box())
            pg.mouse.move(ax, ay)
            pg.mouse.down()
            pg.mouse.move((ax + bx) / 2, ay - 120, steps=8)
            pg.mouse.move(bx, by, steps=10)  # hover the input → compat highlight
            pg.wait_for_timeout(200)
            pg.screenshot(path=str(OUT / "workbench-wiring-live.png"))
            pg.mouse.up()
            pg.wait_for_timeout(300)
            cables_after = pg.eval_on_selector_all(".wb-cable", "e => e.length")
            pg.screenshot(path=str(OUT / "workbench-wired.png"))

            # 3) palette: add a Rewrite node
            pg.click('.wb-palette-chip:has-text("Rewrite")')
            pg.wait_for_timeout(300)
            added = pg.eval_on_selector_all(".wb-node", "e => e.length")
            pg.screenshot(path=str(OUT / "workbench-added-node.png"))
            b.close()
        print(f"cables: {cables_before} -> {cables_after} (a new compatible wire) | nodes after add: {added}")
    finally:
        server.stop()
        reset_database()
    print("Saved wiring screenshots to", OUT)


if __name__ == "__main__":
    main()
