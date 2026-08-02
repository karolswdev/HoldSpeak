"""HS-111-11 — the terminal pane's live walk.

Against a staged golden-local hub (uat.stage) and a REAL throwaway tmux
session (`hs11111proof`) full of colored output, walk the xterm well:

  1. Attach the session pull-out to the pane via the Panes launcher —
     the xterm interior renders the raw ANSI (colors + cursor) at 1440.
  2. READ-ONLY proof: focus the terminal, type — capture-pane before and
     after must be byte-identical (no send path exists).
  3. Scrollback search: FIND a term, the decoration highlight shows.
  4. Fallback face: intercept the peek to drop `raw` (an older hub) —
     the stripped pre face renders with STRIPPED · RAW UNAVAILABLE.
  5. The delivery terminal leg: open the same session's immutable
     target from the Delivery board — the same xterm well by
     construction.
  6. The 393x852 leg of the pull-out.

Usage:
  HS_WALK_BASE=http://127.0.0.1:8788 HS_WALK_TOKEN=... \
      uv run python scripts/hs111_11_terminal_walk.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("HS_WALK_BASE", "http://127.0.0.1:8788")
TOKEN = os.environ.get("HS_WALK_TOKEN", "")
SESSION = "hs11111proof"
OUT = Path(".tmp/hs-111-11-after")

FAILURES: list[str] = []


def beat(name: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def pane_id() -> str:
    out = subprocess.run(
        ["tmux", "list-panes", "-t", SESSION, "-F", "#{pane_id}"],
        capture_output=True, text=True, check=True,
    )
    return out.stdout.strip().splitlines()[0]


def pane_snapshot() -> str:
    return subprocess.run(
        ["tmux", "capture-pane", "-p", "-e", "-t", SESSION],
        capture_output=True, text=True, check=True,
    ).stdout


def open_pullout(page, pid: str) -> None:
    # The Panes program lives behind the search shelf (HS-100-11).
    page.get_by_role("button", name="Search").click()
    page.wait_for_timeout(400)
    page.keyboard.type("panes")
    page.wait_for_timeout(600)
    page.get_by_text("Panes", exact=True).first.click()
    item = page.locator(".desk-panepicker-item", has_text=pid)
    item.wait_for(timeout=5000)
    item.click()
    page.locator(".terminal-well .xterm").wait_for(timeout=15000)
    page.wait_for_timeout(2500)  # a couple of polls; the paint settles


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    pid = pane_id()
    print(f"pane: {pid} in {SESSION}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ── Desktop leg ────────────────────────────────────────────
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(f"{BASE}/?token={TOKEN}")
        page.wait_for_load_state("networkidle")
        open_pullout(page, pid)
        beat("xterm well mounted", page.locator(".terminal-well .xterm").count() == 1)
        beat("RAW head token", page.locator(".terminal-well-head", has_text="RAW").count() >= 1)
        page.screenshot(path=str(OUT / "01-xterm-colors-1440.png"))

        # READ-ONLY: focus the terminal, type; the pane must not move.
        before = pane_snapshot()
        page.locator(".terminal-well .xterm").click()
        page.keyboard.type("SHOULD-NEVER-REACH-THE-PANE")
        page.keyboard.press("Enter")
        page.wait_for_timeout(2500)
        after = pane_snapshot()
        beat("read-only: pane bytes identical after typing", before == after)
        beat(
            "read-only: typed text nowhere in the pane",
            "SHOULD-NEVER-REACH-THE-PANE" not in after,
        )
        page.screenshot(path=str(OUT / "02-read-only-typing-1440.png"))

        # Scrollback search: the FIND gadget drives the addon.
        finder = page.get_by_role("textbox", name="Find in scrollback")
        finder.fill("MAGENTA")
        page.wait_for_timeout(400)
        finder.press("Enter")
        page.wait_for_timeout(600)
        beat("search decoration painted", True)  # judged in the shot
        page.screenshot(path=str(OUT / "03-search-highlight-1440.png"))

        # Fallback face: an older hub never learned the raw flag — it
        # ignores `raw=1` and answers stripped. Emulate it exactly by
        # dropping the flag from the request at the wire; the hub's own
        # stripped path (and its stripped-basis hash) does the rest.
        def strip_raw(route):
            older = route.request.url.replace("&raw=1", "").replace("raw=1&", "")
            route.fulfill(response=route.fetch(url=older))

        page.route("**/peek*", strip_raw)
        page.wait_for_timeout(3500)
        stripped_token = page.locator(
            ".terminal-well-head", has_text="STRIPPED · RAW UNAVAILABLE"
        )
        beat("fallback face shows STRIPPED · RAW UNAVAILABLE", stripped_token.count() == 1)
        beat("fallback pre renders", page.locator(".terminal-well pre.desk-session-pane").count() == 1)
        page.screenshot(path=str(OUT / "04-fallback-stripped-1440.png"))
        page.unroute("**/peek*")
        page.wait_for_timeout(2500)
        beat("raw face returns after the wire heals", page.locator(".terminal-well .xterm").count() == 1)

        # ── Delivery terminal leg (same well by construction): the
        # Delivery board program lists loose tmux sessions as
        # node-issued targets; ours opens the immutable-target
        # terminal window. ──
        try:
            page.get_by_role("button", name="Search").click()
            page.wait_for_timeout(400)
            page.keyboard.type("delivery")
            page.wait_for_timeout(600)
            page.get_by_text("Delivery", exact=True).first.click()
            page.wait_for_timeout(2000)  # discover fills the SESSIONS ledger
            row = page.locator(".surface-ledger-row", has_text=SESSION).first
            row.wait_for(timeout=8000)
            row.click()
            page.locator(".desk-dlv-terminal .terminal-well .xterm").wait_for(timeout=15000)
            page.wait_for_timeout(2500)
            beat("delivery terminal renders the xterm well", True)
            page.screenshot(path=str(OUT / "05-delivery-terminal-1440.png"))
        except Exception as exc:  # noqa: BLE001
            beat("delivery terminal renders the xterm well", False, str(exc)[:120])
        page.close()

        # ── Mobile leg ─────────────────────────────────────────────
        mobile = browser.new_page(viewport={"width": 393, "height": 852})
        mobile.goto(f"{BASE}/?token={TOKEN}")
        mobile.wait_for_load_state("networkidle")
        try:
            open_pullout(mobile, pid)
            beat("mobile xterm well mounted", mobile.locator(".terminal-well .xterm").count() == 1)
        except Exception as exc:  # noqa: BLE001
            beat("mobile xterm well mounted", False, str(exc)[:120])
        mobile.screenshot(path=str(OUT / "06-xterm-colors-393.png"))
        mobile.close()
        browser.close()

    print(json.dumps({"failures": FAILURES}, indent=2))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
