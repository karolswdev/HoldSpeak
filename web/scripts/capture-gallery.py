"""Capture HS-10-03 component-gallery screenshots in two viewports.

Spawns a tiny Python http.server against `holdspeak/static/` (which the
Astro pipeline emits into) so the `/_built` base prefix resolves
without the FastAPI runtime running. Hits `/_built/design/components/`
at 1440 and 420 wide and writes PNGs into the phase folder.

Run via:

    uv run --extra dev python web/scripts/capture-gallery.py
"""

from __future__ import annotations

import argparse
import http.server
import socketserver
import threading
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]
STATIC_DIR = REPO / "holdspeak" / "static"
DEFAULT_OUT = REPO / "pm" / "roadmap" / "holdspeak" / "phase-10-web-design-system" / "screenshots"

GALLERY_PATH = "/_built/design/components/"
DESIGN_CHECK_PATH = "/_built/design/check/"
RUNTIME_PATH = "/_built/"

SHOTS = [
    ("story-03-components-desktop.png", GALLERY_PATH, 1440, 1600),
    ("story-03-components-narrow.png", GALLERY_PATH, 420, 2400),
    ("story-04-topnav-1440.png", GALLERY_PATH, 1440, 200),
    ("story-04-topnav-768.png", GALLERY_PATH, 768, 240),
    ("story-04-topnav-360.png", GALLERY_PATH, 360, 280),
    ("story-04-topnav-current-runtime.png", DESIGN_CHECK_PATH, 1440, 200),
    ("story-05-identity-desktop.png", GALLERY_PATH, 1440, 1900),
    ("story-05-identity-narrow.png", GALLERY_PATH, 420, 2900),
    ("story-06-runtime-idle-desktop.png", RUNTIME_PATH, 1440, 1400),
    ("story-06-runtime-idle-narrow.png", RUNTIME_PATH, 420, 2200),
    ("story-06-runtime-active-desktop.png", RUNTIME_PATH + "?_state=active", 1440, 1400),
    ("story-06-runtime-stopping-desktop.png", RUNTIME_PATH + "?_state=stopping", 1440, 1400),
    ("story-07-activity-desktop.png", "/_built/activity/", 1440, 2200),
    ("story-07-activity-narrow.png", "/_built/activity/", 420, 3000),
]


@contextmanager
def serve(directory: Path, port: int = 0):
    handler = lambda *args, **kw: http.server.SimpleHTTPRequestHandler(
        *args, directory=str(directory), **kw
    )
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    actual_port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{actual_port}"
    finally:
        httpd.shutdown()
        httpd.server_close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    with serve(STATIC_DIR) as base_url:
        print(f"serving {STATIC_DIR} at {base_url}")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            for filename, route, width, height in SHOTS:
                page.set_viewport_size({"width": width, "height": height})
                shot_url = base_url.rstrip("/") + route
                page.goto(shot_url, wait_until="networkidle")
                page.wait_for_timeout(400)

                # Story-06: synthesize meeting states by mutating
                # Alpine's x-data on the runtime page directly. The
                # backend is not running for capture, so this is the
                # only way to render non-idle hero hierarchy.
                if "_state=" in route:
                    state = route.split("_state=")[-1]
                    page.evaluate(
                        """(state) => {
                          const root = document.querySelector('[x-data]');
                          if (!root || !window.Alpine) return;
                          const data = window.Alpine.$data(root);
                          data.meetingTitle = 'Architecture sync';
                          data.meetingTags = ['planning', 'pluggable-pipeline'];
                          if (state === 'active') {
                            data.meetingActive = true;
                            data.duration = '00:24:18';
                            data.segments = new Array(31);
                            data.entries = [
                              { id: 'b1', kind: 'bookmark', label: 'Decision: defer light-mode tokens to phase 12.', timestamp: '00:09:42' },
                              { id: 's1', kind: 'segment', speaker: 'A', text: 'OK so the connector ecosystem moves to phase 11, design phase becomes phase 10.', start: '00:23:51', end: '00:23:58' },
                              { id: 's2', kind: 'segment', speaker: 'B', text: 'And we keep Alpine for now — the JS data layer is fine, we are rebuilding the visuals.', start: '00:24:01', end: '00:24:09' },
                            ];
                          }
                          if (state === 'stopping') {
                            data.meetingActive = true;
                            data.stopInProgress = true;
                            data.duration = '00:38:02';
                            data.segments = new Array(58);
                          }
                        }""",
                        state,
                    )
                    page.wait_for_timeout(400)

                target = out_dir / filename
                full_page = filename.startswith(("story-03-", "story-06-"))
                page.screenshot(path=str(target), full_page=full_page)
                print(f"wrote {target} {width}x{height} {route}")
            browser.close()


if __name__ == "__main__":
    main()
