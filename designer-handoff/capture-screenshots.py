"""Capture designer-handoff screenshots from a running HoldSpeak web runtime."""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


SHOTS = [
    ("dashboard-desktop.png", "/", 1440, 1000),
    ("activity-desktop.png", "/activity", 1440, 1100),
    ("activity-mobile.png", "/activity", 390, 1200),
    ("history-desktop.png", "/history", 1440, 1100),
    ("dictation-desktop.png", "/dictation", 1440, 1100),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:64524")
    parser.add_argument("--out", default="designer-handoff/screenshots")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        for filename, route, width, height in SHOTS:
            page.set_viewport_size({"width": width, "height": height})
            page.goto(args.base_url.rstrip("/") + route, wait_until="domcontentloaded")
            page.wait_for_timeout(1800)
            path = out_dir / filename
            page.screenshot(path=str(path), full_page=True)
            print(f"wrote {path} {width}x{height} {route}")
        browser.close()


if __name__ == "__main__":
    main()
