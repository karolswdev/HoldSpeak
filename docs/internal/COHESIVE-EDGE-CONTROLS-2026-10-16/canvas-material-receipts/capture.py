"""Capture declared library directions, with APIs intercepted."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

shots = Path(__file__).resolve().parents[4] / ".tmp/edges/canvas-material-receipts/shots"
shots.mkdir(parents=True, exist_ok=True)
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    for width in (1440, 393):
        context = browser.new_context(viewport={"width": width, "height": 900}, reduced_motion="reduce")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/api/**", lambda route: route.fulfill(status=200, content_type="application/json", body="{}"))
        for face in ("material", "pr-result", "frame-before", "frame-after"):
            page.goto(f"http://127.0.0.1:4499/?face={face}", wait_until="networkidle")
            page.locator(".desk-surface-body").wait_for()
            if face == "pr-result":
                page.get_by_role("button", name="More for #393", exact=True).click()
                page.get_by_role("menuitem", name="Draft review", exact=True).click()
                page.get_by_text("Review ready", exact=True).wait_for()
            page.screenshot(path=str(shots / f"{face}-{width}.png"), full_page=True)
            print(json.dumps({"face": face, "width": width, "errors": errors, "shot": str(shots / f"{face}-{width}.png")}))
            if face == "pr-result":
                page.locator(".desk-pr-result summary").click()
                page.screenshot(path=str(shots / f"pr-result-open-{width}.png"), full_page=True)
        context.close()
    browser.close()
