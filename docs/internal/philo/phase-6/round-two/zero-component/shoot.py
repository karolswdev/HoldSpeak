"""Real AmbientLayer + publishAftercare fixture; no hub or placement claim."""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
facts = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width, height in ((1440, 900), (393, 852)):
        page = browser.new_page(viewport={"width": width, "height": height})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/api/**", lambda route: route.fulfill(
            status=200, content_type="application/json", body="{}"))
        page.goto("http://127.0.0.1:4432/")
        card = page.get_by_label("Meeting aftercare")
        card.wait_for()
        page.evaluate("document.fonts.ready")
        assert card.get_by_role("button", name="Open proposals").count() == 0
        assert card.get_by_role("button", name="Dismiss").count() == 1
        assert card.locator("p").count() == 0
        box = card.bounding_box()
        assert box and box["x"] >= 0 and box["x"] + box["width"] <= width
        assert box["y"] >= 0 and box["y"] + box["height"] <= height
        page.screenshot(path=str(out / f"zero-{width}.png"))
        card.get_by_role("button", name="Dismiss").click()
        assert card.count() == 0
        assert errors == [], errors
        facts.append({"width": width, "height": height, "card": box,
                      "openProposals": False, "dismissed": True,
                      "pageErrors": errors,
                      "kind": "actual AmbientLayer + real publishAftercare component fixture, no hub/walk"})
        page.close()
    browser.close()
(out / "facts.json").write_text(json.dumps(facts, indent=2) + "\n")
print(json.dumps(facts, indent=2))
