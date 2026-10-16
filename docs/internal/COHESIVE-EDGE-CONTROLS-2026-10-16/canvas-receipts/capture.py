"""Capture declared library canvas samples through the machine lock."""
from pathlib import Path
import argparse
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument("--ask-only", action="store_true")
parser.add_argument("--faces", nargs="+")
parser.add_argument("--out", type=Path)
args = parser.parse_args()
shots = args.out or Path(__file__).resolve().parents[4] / ".tmp" / "edges" / "canvas-receipts-shots"
shots.mkdir(parents=True, exist_ok=True)
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    for width in (1440, 393):
        context = browser.new_context(viewport={"width": width, "height": 1050}, reduced_motion="reduce")
        page = context.new_page()
        page.route("**/api/**", lambda route: route.fulfill(status=200, content_type="application/json", body="{}"))
        for face in (args.faces or (("ask-zero", "ask-positive") if args.ask_only else ("ask-zero", "ask-positive", "resourceful-enabled", "resourceful-paused"))):
            page.goto(f"http://127.0.0.1:4498/?face={face}")
            page.locator(".desk-surface-body").wait_for()
            page.screenshot(path=str(shots / f"{face}-{width}.png"), full_page=True)
            print(f"{face}-{width}.png")
            if face.startswith("resourceful"):
                page.locator(".receipt-direction-body").evaluate("element => element.scrollTop = element.scrollHeight")
                page.screenshot(path=str(shots / f"{face}-{width}-controls.png"), full_page=True)
                print(f"{face}-{width}-controls.png")
        context.close()
    browser.close()
