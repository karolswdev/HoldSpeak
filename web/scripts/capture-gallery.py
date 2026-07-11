"""Capture HS-10-03 component-gallery screenshots in two viewports.

Spawns a tiny Python http.server against `holdspeak/static/` (which the
Vite pipeline emits into) so the `/_built` base prefix resolves
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
from urllib.parse import urlsplit

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
    ("story-08-history-meetings-desktop.png", "/_built/history/", 1440, 1800),
    ("story-08-history-meetings-narrow.png", "/_built/history/", 420, 2600),
    ("story-08-history-settings-desktop.png", "/_built/history/?_tab=settings", 1440, 2800),
    ("story-10-command-preview-desktop.png", GALLERY_PATH + "#command-preview", 1440, 1100),
    ("story-10-command-preview-narrow.png", GALLERY_PATH + "#command-preview", 768, 1400),
    ("story-09-dictation-blocks-desktop.png", "/_built/dictation/", 1440, 1500),
    ("story-09-dictation-blocks-narrow.png", "/_built/dictation/", 420, 2200),
    ("story-09-dictation-runtime-doc-desktop.png", "/_built/docs/dictation-runtime/", 1440, 1600),
]


@contextmanager
def serve(directory: Path, port: int = 0):
    class SpaHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def do_GET(self):  # noqa: N802 - stdlib handler contract
            path = urlsplit(self.path).path
            target = directory / path.lstrip("/")
            if path.startswith("/_built/") and not target.is_file():
                self.path = "/_built/index.html"
            super().do_GET()

    httpd = socketserver.TCPServer(("127.0.0.1", port), SpaHandler)
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

                target = out_dir / filename
                # story-10 captures only the CommandPreview section
                # so it stays a viewport-bound shot focused on the
                # component (the gallery itself is captured by story-03).
                full_page = filename.startswith(("story-03-", "story-06-", "story-08-", "story-09-"))
                if filename.startswith("story-10-"):
                    page.evaluate(
                        "document.getElementById('command-preview')?.scrollIntoView({ block: 'start' })",
                    )
                    page.wait_for_timeout(200)
                page.screenshot(path=str(target), full_page=full_page)
                print(f"wrote {target} {width}x{height} {route}")
            browser.close()


if __name__ == "__main__":
    main()
