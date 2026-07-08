"""HS-86-04 — the conveyor's station lights + evidence in place, proven
live (Playwright, real app, the operator's real project map).

No seeding: both lanes are the real rails repos (holdspeak +
delivery-workbench), the receipts are real `gh` answers, the events are
the repos' real rail logs. The evidence panel opens a real evidence
file in place. The refusal chip, when staged, is a REAL dw gate
refusal (an honestly unchecked contract) — never a mocked frame.
"""
from pathlib import Path
from unittest.mock import MagicMock

from playwright.sync_api import sync_playwright

from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

OUT = Path("pm/roadmap/holdspeak/phase-86-delivery-belt/screenshots")
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        )
    )
    url = server.start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            pg = browser.new_page(viewport={"width": 1440, "height": 1000})
            pg.goto(f"{url}/", wait_until="networkidle")
            pg.wait_for_selector(".desk-mc", timeout=30_000)
            pg.wait_for_selector(".desk-mc-repo-head", timeout=30_000)
            pg.wait_for_timeout(1_200)
            conveyor = pg.locator(".desk-mc")
            conveyor.screenshot(path=str(OUT / "hs-86-04-conveyor-lanes-and-lights.png"))
            print("shot: lanes + lights")

            # The filed object opens in place: HS-86-01's evidence.
            opener = pg.locator(
                ".desk-mc-story", has_text="HS-86-01"
            ).locator(".desk-mc-evidence-open")
            opener.first.click()
            pg.wait_for_selector(".desk-mc-evidence-body", timeout=15_000)
            conveyor.screenshot(path=str(OUT / "hs-86-04-evidence-in-place.png"))
            print("shot: evidence in place")

            body = pg.locator(".desk-mc-evidence-body").inner_text()
            assert "dw check" in body, "the real evidence text is on the desk"
            pg.locator(".desk-mc-evidence .desk-mc-btn").click()

            # If the newest gate event is a refusal, the light wears it.
            refusal = pg.locator(".desk-mc-light.gate-refusal")
            if refusal.count() > 0:
                conveyor.screenshot(path=str(OUT / "hs-86-04-gate-refusal-chip.png"))
                print("shot: gate refusal chip (real refusal)")
            else:
                print("no refusal in the newest gate events (honest state)")
            browser.close()
    finally:
        server.stop()


if __name__ == "__main__":
    main()
