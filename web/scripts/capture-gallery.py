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

SHOTS = [
    ("story-03-components-desktop.png", 1440, 1600),
    ("story-03-components-narrow.png", 420, 2400),
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
        url = base_url.rstrip("/") + GALLERY_PATH
        print(f"serving {STATIC_DIR} at {base_url}")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            for filename, width, height in SHOTS:
                page.set_viewport_size({"width": width, "height": height})
                page.goto(url, wait_until="networkidle")
                page.wait_for_timeout(400)
                target = out_dir / filename
                page.screenshot(path=str(target), full_page=True)
                print(f"wrote {target} {width}x{height}")
            browser.close()


if __name__ == "__main__":
    main()
