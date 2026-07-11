#!/usr/bin/env python
"""Playwright drive of the real guided UAT site — a labelled harness self-test.

Boots the conductor (serving the built SPA) on an isolated runs-root, then
drives the home → start → staged → walkthrough loop with a real chromium and
saves screenshots. The verdicts it casts are harness self-tests, NOT a sitting.

    uv run python scripts/uat_site_walk.py [--out <dir>]

Requires the site to be built (uat/web/dist) and Playwright chromium installed.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PORT = int(os.environ.get("UAT_WALK_PORT", "8811"))


def _wait_health(url: str, timeout: float = 40.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.4)
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "pm/roadmap/holdspeak-uat/phase-1-the-mechanics/assets"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    dist = REPO / "uat" / "web" / "dist" / "index.html"
    if not dist.exists():
        print("site not built; run: npm --prefix uat/web install && npm --prefix uat/web run build", file=sys.stderr)
        return 2

    runs_root = Path(tempfile.mkdtemp(prefix="uat-walk-"))
    env = os.environ.copy()
    env["UAT_PORT"] = str(PORT)
    env["UAT_RUNS_ROOT"] = str(runs_root)
    env["UAT_DB_PATH"] = str(runs_root / "uat.db")
    conductor = subprocess.Popen(
        [sys.executable, "-m", "uat.conductor"], cwd=str(REPO), env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
    )
    try:
        base = f"http://127.0.0.1:{PORT}"
        if not _wait_health(f"{base}/api/health"):
            print("conductor did not come up", file=sys.stderr)
            return 1

        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            # Desktop first.
            page = browser.new_page(viewport={"width": 1100, "height": 860})
            page.goto(base, wait_until="networkidle")
            page.wait_for_selector("text=Run the functional verification", timeout=10000)
            page.screenshot(path=str(out / "site-01-home.png"))
            print("captured home")

            # Start the first owner campaign by its human title. Its opening
            # first-run/no-model world is fully local and fast.
            first_campaign = page.locator(".card").filter(
                has=page.get_by_role(
                    "heading",
                    name="1 · React Web Desk foundation — desktop",
                    exact=True,
                )
            )
            first_campaign.get_by_role("button", name="Start").click()
            # Staging then the first walkthrough step.
            page.wait_for_selector("text=Expect:", timeout=60000)
            page.screenshot(path=str(out / "site-02-walkthrough.png"))
            print("captured walkthrough")

            # Cast a harness-only pass on the explicit web_react:desktop slot.
            page.click("button.vb.pass >> nth=0")
            page.wait_for_timeout(600)
            page.screenshot(path=str(out / "site-03-verdict-cast.png"))
            print("captured verdict cast")

            # Phone-width responsive proof.
            phone = browser.new_page(viewport={"width": 390, "height": 800})
            phone.goto(base, wait_until="networkidle")
            phone.wait_for_selector("text=Run the functional verification", timeout=10000)
            phone.evaluate("window.scrollTo(0, 0)")
            phone.screenshot(path=str(out / "site-04-phone-home.png"))
            print("captured phone home")

            browser.close()
        print(f"screenshots in {out}")
        return 0
    finally:
        try:
            os.killpg(os.getpgid(conductor.pid), 15)
        except Exception:
            conductor.terminate()


if __name__ == "__main__":
    raise SystemExit(main())
