#!/usr/bin/env python3
"""HS-201-06 — the plain-words walk: one shot of every changed label in place.

One process: an isolated HOME, a real in-process hub over a scratch DB
seeded with two meetings (one with no transcript, one with three saved
segments), driven by Playwright at 1440x900.  Nothing outside the
scratch HOME is written; no microphone is opened.

Run:
    REAL=$HOME; HOME=$(mktemp -d) \
      PLAYWRIGHT_BROWSERS_PATH=$REAL/Library/Caches/ms-playwright \
      uv run python pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-06-shots/story06_walk.py
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
TOKEN = "hs-201-06-plain-words-token"
WIDTH, HEIGHT = 1440, 900

SHOTS: list[tuple[str, str]] = []
FAILS: list[str] = []
NOTES: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> bool:
    if cond:
        print(f"  PASS  {label}" + (f"  {detail}" if detail else ""), flush=True)
    else:
        FAILS.append(f"{label}  {detail}")
        print(f"  FAIL  {label}" + (f"  {detail}" if detail else ""), flush=True)
    return bool(cond)


def note(text: str) -> None:
    NOTES.append(text)
    print(f"  NOTE  {text}", flush=True)


def shot(page, name: str, proves: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}-{WIDTH}.png"
    page.screenshot(path=str(path), full_page=False)
    SHOTS.append((path.name, proves))
    print(f"  SHOT  {path.name}  ({proves})", flush=True)


def seed(db_path: Path) -> None:
    """Two meetings: no transcript, and three saved segments."""
    from holdspeak.db import get_database, reset_database
    from holdspeak.meeting_session.models import MeetingState, TranscriptSegment

    reset_database()
    db = get_database(db_path)
    start = datetime.now() - timedelta(hours=3)

    db.meetings.save_meeting(MeetingState(
        id="m-201-06-empty",
        started_at=start,
        ended_at=start + timedelta(minutes=1),
        title="",
        capture_status="finalized",
        intel_status="error",
        intel_status_detail="Meeting intelligence did not finish.",
    ))
    db.intel.enqueue_intel_job("m-201-06-empty", transcript_hash="hs-201-06-empty")
    # fail_intel_job only moves a running/claimed row, so claim it first.
    db.intel.claim_next_intel_job()
    db.intel.fail_intel_job("m-201-06-empty", "Meeting intelligence did not finish.")

    segments = [
        TranscriptSegment(text="We agreed to ship the plain words first.",
                          speaker="Karol", start_time=0.0, end_time=4.0),
        TranscriptSegment(text="The summary can wait for the model.",
                          speaker="Karol", start_time=4.0, end_time=8.0),
        TranscriptSegment(text="Record the walk at fourteen forty.",
                          speaker="Karol", start_time=8.0, end_time=12.0),
    ]
    db.meetings.save_meeting(MeetingState(
        id="m-201-06-kept",
        started_at=start + timedelta(minutes=30),
        ended_at=start + timedelta(minutes=42),
        title="Sprint review",
        capture_status="finalized",
        segments=segments,
        intel_status="error",
        intel_status_detail="Meeting intelligence did not finish.",
    ))
    db.intel.enqueue_intel_job("m-201-06-kept", transcript_hash="hs-201-06-kept")
    db.intel.claim_next_intel_job()
    db.intel.fail_intel_job("m-201-06-kept", "Meeting intelligence did not finish.")
    return db


def boot(db):
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    import urllib.request

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda _label: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        host="127.0.0.1",
        auth_token=TOKEN,
    )
    url = server.start()
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(
                f"{url}/health", headers={"X-HoldSpeak-Token": TOKEN})
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status == 200:
                    break
        except Exception:
            time.sleep(0.2)
    print(f"  hub {url}", flush=True)
    return server, url


def goto(page, url: str, route: str) -> None:
    sep = "&" if "?" in route else "?"
    page.goto(f"{url}{route}{sep}token={TOKEN}", wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(1500)


def normal_chair(page) -> None:
    """Cross the First Sentence gate (tests/e2e/glass_infra._normal_chair)."""
    chair = page.locator(".chair")
    chair.wait_for(timeout=20000)
    if chair.evaluate("el => el.classList.contains('chair-first-value')"):
        page.get_by_role("button", name="Continue later", exact=True).click()
    page.locator(".chair:not(.chair-first-value)").wait_for(timeout=20000)
    page.wait_for_timeout(800)


def open_surface(page, key: str) -> bool:
    """Stage a surface key and reload (tests/e2e/..._open_surface)."""
    page.evaluate(
        """([key]) => {
          localStorage.removeItem("hs.desk.workspace.v1");
          sessionStorage.setItem(
            "hs.desk.staged-surface-open", JSON.stringify({key}));
        }""",
        [key],
    )
    page.reload(wait_until="load")
    normal_chair(page)
    try:
        page.locator(".desk-surface-window").first.wait_for(timeout=15000)
        page.wait_for_timeout(1200)
        return True
    except Exception:
        return False


def walk() -> int:
    from playwright.sync_api import sync_playwright

    home = Path(os.environ["HOME"])
    db = seed(home / "hs-201-06-walk.db")
    server, url = boot(db)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": WIDTH, "height": HEIGHT},
                device_scale_factor=2,
            )
            page = context.new_page()

            # ---- 1. arrival: the FirstWords line ------------------------
            print("\n== arrival ==", flush=True)
            goto(page, url, "/")
            body = page.locator("body").inner_text()
            check("arrival card present", "Dictate one sentence" in body, body[:120])
            check("plain words line",
                  "Speak. Then edit and keep your text." in body)
            check("old line gone", "Tap to speak, edit here, then use" not in body)
            shot(page, "arrival-first-words", "Speak. Then edit and keep your text.")

            # ---- 2. the Desk, the menus --------------------------------
            print("\n== desk menus ==", flush=True)
            normal_chair(page)
            page.locator('[data-menu-id="desk"] button').first.click()
            page.wait_for_timeout(700)
            menu = page.locator(".desk-verbbar-menu")
            menu_text = menu.first.inner_text() if menu.count() else ""
            check("Desk menu says Hide the menus", "Hide the menus" in menu_text,
                  menu_text[:160].replace("\n", " · "))
            check("Settle in gone", "Settle in" not in menu_text)
            shot(page, "desk-menu-hide-the-menus", "Hide the menus (was: Settle in)")
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)

            # ---- 3. the Chair meeting row (ChairHome: lane A's file) ----
            chair_text = page.locator("body").inner_text()
            if "Untitled meeting" in chair_text:
                note("ChairHome still renders 'Untitled meeting' (its own fallback "
                     "at web/src/desk/chair/ChairHome.tsx:1709 — lane A owns the file)")
            shot(page, "chair-meeting-row", "the Chair's own untitled-meeting fallback")

            # ---- 4. Change places --------------------------------------
            print("\n== change places ==", flush=True)
            check("change-places surface opened", open_surface(page, "change-places"))
            cp = page.locator(".desk-surface-window").first.inner_text()
            check("Change places says Hide the menus", "Hide the menus" in cp,
                  cp[:160].replace("\n", " · "))
            check("Settle in gone from Change places", "Settle in" not in cp)
            shot(page, "change-places-hide-the-menus", "Hide the menus (was: Settle in)")

            # ---- 5. the Meetings ledger + the two records ---------------
            print("\n== meetings ==", flush=True)
            check("meetings surface opened", open_surface(page, "review-meetings"))
            led = page.locator(".desk-surface-window").first.inner_text()
            check("ledger no longer says INTELLIGENCE", "INTELLIGENCE" not in led,
                  led[:200].replace("\n", " · "))
            shot(page, "meetings-ledger", "the ledger after the words changed")

            for meeting_id, name, expect, proves in (
                ("m-201-06-kept", "record-kept-segments",
                 "KEPT 3 SEGMENTS",
                 "KEPT 3 SEGMENTS (was: RETAINED 3 SEG)"),
                ("m-201-06-empty", "record-empty-no-zero-counter",
                 "NOT DONE: SUMMARY, TOPICS, ACTION ITEMS",
                 "NOT DONE (no routed artifacts); no RETAINED 0 SEG"),
            ):
                row = page.locator(f"[data-testid='meeting-row-{meeting_id}'] .meetings-stream-row-body")
                if not row.count():
                    row = page.locator(f"[data-testid='meeting-row-{meeting_id}']")
                check(f"{meeting_id}: row present", row.count() > 0)
                if row.count():
                    row.first.click()
                    page.wait_for_timeout(2000)
                detail = page.locator(".desk-surface-window").first.inner_text()
                check(f"{meeting_id}: {expect}", expect in detail,
                      detail[:300].replace("\n", " · "))
                check(f"{meeting_id}: SUMMARY axis", "SUMMARY" in detail)
                if meeting_id == "m-201-06-empty":
                    check("no zero counter", "RETAINED 0" not in detail and "KEPT 0" not in detail)
                shot(page, name, proves)

                if meeting_id == "m-201-06-empty":
                    retry = page.get_by_role("button", name="Retry", exact=True)
                    check("Retry verb on the record", retry.count() > 0)
                    if retry.count():
                        retry.first.click()
                        page.wait_for_timeout(2500)
                        refused = page.locator(".desk-surface-window").first.inner_text()
                        check("refusal ends its sentence",
                              "This meeting has no transcript. No summary can run. "
                              "The Meeting and completed work remain saved." in refused,
                              refused[:320].replace("\n", " · "))
                        shot(page, "record-retry-refusal",
                             "two sentences, each closed (was one run-on)")

            # ---- 6. the egress window ----------------------------------
            print("\n== data boundaries ==", flush=True)
            goto(page, url, "/")
            normal_chair(page)
            chip = page.locator(".egress-badge-button")
            check("chrome egress chip present", chip.count() > 0)
            if chip.count():
                chip.first.click()
                page.wait_for_timeout(1500)
            win = page.locator(".desk-trust-window")
            check("trust window open", win.count() > 0)
            trust = win.first.inner_text() if win.count() else ""
            for head in ("Where it goes", "Allowed by", "Runs without you", "How to stop it"):
                check(f"trust head: {head}", head in trust)
            for old in ("Boundary", "Authority", "Background", "Revoke"):
                check(f"old head gone: {old}", old not in trust)
            shot(page, "trust-window-heads",
                 "Where it goes / Allowed by / Runs without you / How to stop it")

            # ---- 7. Models: the waiting token --------------------------
            print("\n== models ==", flush=True)
            check("concierge surface opened", open_surface(page, "open-concierge"))
            page.wait_for_timeout(3000)
            models = page.locator(".desk-surface-window").first.inner_text()
            check("no invented plural", "WAITINGS" not in models,
                  models[:240].replace("\n", " · "))
            check("waiting token present", "WAITING" in models,
                  models[:240].replace("\n", " · "))
            shot(page, "models-waiting", "N WAITING (was: 7 WAITINGS)")

            context.close()
            browser.close()
    finally:
        try:
            server.stop()
        except Exception:
            pass

    print("\n" + "=" * 60, flush=True)
    print(f"SHOTS: {len(SHOTS)}  FAILS: {len(FAILS)}", flush=True)
    for name, proves in SHOTS:
        print(f"  {name}  ({proves})", flush=True)
    if NOTES:
        print("\nNOTES:", flush=True)
        for n in NOTES:
            print(f"  - {n}", flush=True)
    if FAILS:
        print("\nFAILS:", flush=True)
        for f in FAILS:
            print(f"  - {f}", flush=True)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(walk())
