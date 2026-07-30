"""HS-109-05 — the Project Memory window's live walk.

Against a hub spawned from this tree serving a COPY of the REAL archive
(a real project, real meetings, real decision records with moments):

  1440: open the real project from the Desk search, read the timeline,
  accept a real decision in-row, see the promote verbs appear, promote
  deterministically, search the project for BLUE LANTERN, run
  Ask-this-project on the REAL `.43` profile and see the cited answer
  with its grounded-on count. 393: the window list-first, no overflow.

Usage:
  HS_WALK_BASE=http://127.0.0.1:8797 HS_WALK_TOKEN=... \
      uv run --with playwright python scripts/hs109_05_walk.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("HS_WALK_BASE", "http://127.0.0.1:8797")
TOKEN = os.environ.get("HS_WALK_TOKEN", "hs109-walk-token")
OUT = Path("uat/_runs/hs-109-05-walk")
PROJECT = "delivery-workbench"


def beat(name: str, ok: bool, detail: str = "") -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    return ok


def open_project(page) -> bool:
    page.keyboard.press("Meta+k")
    page.wait_for_timeout(500)
    page.keyboard.type(PROJECT)
    page.wait_for_timeout(700)
    try:
        page.get_by_text(PROJECT, exact=False).nth(1).click(timeout=4000)
        return True
    except Exception:
        try:
            page.keyboard.press("Enter")
            return True
        except Exception:
            return False


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    results: list[bool] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ---------------- 1440 ----------------
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(f"{BASE}/?token={TOKEN}")
        page.wait_for_selector(".desk-next, .desk-world, .desk-listmode",
                               timeout=20000)
        page.wait_for_timeout(1500)
        opened = open_project(page)
        page.wait_for_timeout(2000)
        body = page.content()
        results.append(beat("[1440] project opened from Desk search",
                            opened and PROJECT in body))
        results.append(beat("[1440] memory window face present",
                            "Since" in body or "Timeline" in body
                            or "Decisions" in body))

        # Accept a recorded decision in-row → promote verbs appear.
        try:
            page.get_by_text("Decisions", exact=True).first.click(timeout=4000)
            page.wait_for_timeout(800)
            page.get_by_role("button", name="Accept").first.click(timeout=5000)
            page.wait_for_timeout(1200)
        except Exception:
            pass
        body = page.content()
        promote_visible = "Promote" in body
        results.append(beat("[1440] accept gesture → promote verbs appear",
                            promote_visible))
        if promote_visible:
            try:
                page.get_by_role("button", name="Promote", exact=True).first.click(
                    timeout=4000)
                page.wait_for_timeout(1500)
                body = page.content()
                results.append(beat("[1440] deterministic promote → artifact chip",
                                    "artifact:promoted-" in body))
            except Exception:
                results.append(beat("[1440] deterministic promote → artifact chip",
                                    False, "click failed"))
        else:
            results.append(False)

        # Project search.
        try:
            page.get_by_text("Search", exact=True).first.click(timeout=4000)
            page.wait_for_timeout(600)
            search = page.get_by_label("Search this project")
            search.fill("BLUE LANTERN")
            page.wait_for_timeout(1500)
            body = page.content()
            results.append(beat("[1440] project search hits the real decision",
                                "BLUE" in body and "LANTERN" in body))
        except Exception:
            results.append(beat("[1440] project search hits the real decision",
                                False, "search input not found"))

        shot = OUT / "memory-window-1440.png"
        page.screenshot(path=str(shot))
        print(f"shot: {shot}")

        # Ask this project on the real .43 profile.
        ask_ok = False
        cited = False
        try:
            page.get_by_text("Ask", exact=True).first.click(timeout=4000)
            page.wait_for_timeout(600)
            page.get_by_label("Ask this project").fill(
                "What is the launch codename for the mesh milestone?")
            sel = page.locator("select").last
            sel.select_option("profile_03617b8c9250")
            page.get_by_role("button", name="Ask", exact=True).first.click(
                timeout=4000)
            page.wait_for_timeout(30000)
            body = page.content()
            ask_ok = "BLUE LANTERN" in body
            cited = "Grounded on" in body
        except Exception as e:
            print(f"  ask leg error: {e}")
        results.append(beat("[1440] ask-this-project answers from the archive "
                            "(.43)", ask_ok))
        results.append(beat("[1440] grounded-on count visible", cited))
        shot = OUT / "memory-window-ask-1440.png"
        page.screenshot(path=str(shot))
        print(f"shot: {shot}")
        page.close()

        # ---------------- 393 ----------------
        page = browser.new_page(viewport={"width": 393, "height": 852})
        page.goto(f"{BASE}/?token={TOKEN}")
        page.wait_for_selector(".desk-next, .desk-world, .desk-listmode",
                               timeout=20000)
        page.wait_for_timeout(1500)
        opened = open_project(page)
        page.wait_for_timeout(2000)
        body = page.content()
        results.append(beat("[393] project opens", opened and PROJECT in body))
        overflow = page.evaluate(
            "document.body.scrollWidth > window.innerWidth + 1")
        results.append(beat("[393] no horizontal body overflow", not overflow))
        shot = OUT / "memory-window-393.png"
        page.screenshot(path=str(shot))
        print(f"shot: {shot}")
        page.close()
        browser.close()

    print(f"\n{sum(1 for r in results if r)}/{len(results)} beats passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
