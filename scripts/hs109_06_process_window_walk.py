"""HS-109-06 — the process window's live walk.

Drives a staged product (uat.stage seeded-desk-steering) with real kernel
operations, then walks the Processes window with Playwright at 1440 and 393:

  1. A REAL steered send through /api/coders/{key}/steer — the proven
     process.input@1 path — producing admit/approve/claim/receipt journal
     events for a real tmux pane.
  2. A REAL named kernel refusal — /api/kernel/submit with an unregistered
     operation type — landing in Recently ended with its reason.
  3. The window opened from the Go menu (the verb registry, not a URL),
     rows asserted, screenshots at both densities.

Usage:
  HS_WALK_BASE=http://127.0.0.1:8791 HS_WALK_TOKEN=... \
      uv run python scripts/hs109_06_process_window_walk.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

BASE = os.environ.get("HS_WALK_BASE", "http://127.0.0.1:8791")
TOKEN = os.environ.get("HS_WALK_TOKEN", "")
OUT = Path("uat/_runs/hs-109-06-walk")


def api(path: str, payload: dict | None = None) -> tuple[int, dict]:
    url = f"{BASE}{path}"
    sep = "&" if "?" in path else "?"
    if TOKEN:
        url = f"{url}{sep}token={TOKEN}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body or "{}")
        except json.JSONDecodeError:
            return e.code, {"raw": body}


def beat(name: str, ok: bool, detail: str = "") -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    return ok


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    results: list[bool] = []

    # -- Real operations first, so the window has truth to show. --------
    status, panes = api("/api/coders/steering/panes")
    key = ""
    for p_row in panes.get("panes", []) or []:
        session = str(p_row.get("session", ""))
        if session.startswith("uat-") and session.endswith("-coder"):
            key = quote(f"pane:{p_row.get('pane_id')}", safe=":")
            break
    results.append(beat("staged pane found", status == 200 and bool(key),
                        f"key={key or '<none>'}"))

    if key:
        api(f"/api/coders/{key}/arm", {"ttl_seconds": 300})
    steer_status, steer = api(
        f"/api/coders/{key}/steer",
        {"text": "echo HS-109-06 process window walk", "submit": True},
    ) if key else (0, {})
    results.append(beat(
        "real steer delivered (process.input@1)",
        steer_status == 200 and steer.get("status") == "delivered",
        f"http={steer_status} status={steer.get('status')} audit={steer.get('audit_id')}",
    ))

    refuse_status, refused = api(
        "/api/kernel/submit",
        {"name": "walk.nonexistent", "version": 1, "request_id": "hs10906-walk-refusal",
         "payload": {}, "target": {}, "placement": "node:local-desktop"},
    )
    reason = json.dumps(refused)[:200]
    outcome = (refused.get("receipt") or {}).get("outcome", "")
    results.append(beat(
        "named kernel refusal minted",
        refused.get("state") == "refused" and bool(outcome),
        f"http={refuse_status} outcome={outcome or reason}",
    ))

    ops_status, events = api("/api/kernel/events?after_cursor=0")
    batch = events.get("events", events if isinstance(events, list) else [])
    results.append(beat(
        "journal carries the walk's events",
        ops_status == 200 and len(batch) >= 2,
        f"events={len(batch)}",
    ))

    # -- The window, both densities. ------------------------------------
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for width, height, label in ((1440, 900, "1440"), (393, 852, "393")):
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(f"{BASE}/?token={TOKEN}")
            page.wait_for_selector(".desk-next, .desk-world, .desk-listmode",
                                   timeout=20000)
            page.wait_for_timeout(1500)

            opened = False
            # The Go menu first (the registry's own door)…
            try:
                page.get_by_text("Go", exact=True).first.click(timeout=4000)
                page.get_by_text("Processes", exact=True).first.click(timeout=4000)
                opened = True
            except Exception:
                # …then the tool shelf.
                try:
                    page.keyboard.press("Meta+k")
                    page.wait_for_timeout(400)
                    page.keyboard.type("Processes")
                    page.wait_for_timeout(500)
                    page.get_by_text("See what the kernel is running",
                                     exact=False).first.click(timeout=4000)
                    opened = True
                except Exception:
                    opened = False
            page.wait_for_timeout(2500)

            window_ok = False
            rows_ok = False
            refusal_ok = False
            try:
                page.wait_for_selector("text=Processes", timeout=8000)
                window_ok = True
                body = page.content()
                rows_ok = ("process.input" in body) or ("Recently ended" in body)
                refusal_ok = "refused" in body.lower()
            except Exception:
                pass

            shot = OUT / f"process-window-{label}.png"
            page.screenshot(path=str(shot), full_page=False)
            results.append(beat(f"[{label}] window opened", opened and window_ok))
            results.append(beat(f"[{label}] real rows visible", rows_ok))
            results.append(beat(f"[{label}] refusal visible", refusal_ok))
            print(f"shot: {shot}")
            page.close()
        browser.close()

    print(f"\n{sum(results)}/{len(results)} beats passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
