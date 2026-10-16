"""Capture this direction canvas only; no production desk or hub is opened."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[4]
out = root / ".tmp/evidence-shots/navigation-context-canvas"
out.mkdir(parents=True, exist_ok=True)
observations = []

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(args=["--use-angle=metal"])
    for width, height in [(1440, 1000), (393, 900)]:
        for face in ["context-empty", "context-saved", "needs"]:
            page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion="reduce")
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"http://127.0.0.1:4493/?face={face}")
            page.get_by_role("textbox", name="Constitutional context").wait_for() if face != "needs" else page.get_by_text("3 need you").wait_for()
            page.evaluate("document.fonts.ready")
            page.screenshot(path=str(out / f"{face}-{width}.png"), full_page=True)
            observations.append({"face": face, "width": width, "page_errors": errors})
            page.close()
    browser.close()

(out / "preview.json").write_text(json.dumps(observations, indent=2) + "\n")
print(json.dumps({"output": str(out), "observations": observations}, indent=2))
