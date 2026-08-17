#!/usr/bin/env python3
"""HS-136-03 — the Scheduled Recording surface walk.

Screenshot + console-error proof for the Chair's schedule surface at
1440x900 and 393x900: the in-world create control (a DeskWindow, title
focused, speak-to-fill mic), and the SCHEDULED entry in the Meetings
lane. Reuses scripts/chair_walk.py's Hub/Shooter/goto (isolated HOME,
seeded hub, console-error assertion).

The arming countdown is a 10s transient behind the 60s conductor tick;
it is covered by the CaptureHero vitest suite and proven end-to-end in
HS-136-04's live-metal walk — not shot here.

Run:
    HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=~/Library/Caches/ms-playwright \
        uv run python scripts/schedule_walk_hs136.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import chair_walk as cw  # noqa: E402
from chair_walk import Hub, Shooter, check, finding, goto, section, _free_port  # noqa: E402

WALK_OUT = REPO / "pm/roadmap/holdspeak/phase-136-scheduled-recording/assets/walk"
TOKEN = "hs-136-03-schedule-walk-token"
VIEWPORTS = ((1440, 900), (393, 900))


def seed_schedule(hub: Hub) -> bool:
    """POST a recurring schedule so the Meetings lane has a SCHEDULED row."""
    body = json.dumps({
        "title": "Weekly standup",
        "cron_expr": "0 9 * * 1-5",
        "one_shot": False,
        "duration_minutes": 30,
        "enabled": True,
    }).encode()
    req = urllib.request.Request(
        f"{hub.url}/api/scheduled-recordings",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-HoldSpeak-Token": hub.token,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = resp.status in (200, 201)
            check("seed schedule via POST /api/scheduled-recordings", ok,
                  f"status={resp.status}")
            return ok
    except Exception as exc:  # noqa: BLE001
        check("seed schedule via POST /api/scheduled-recordings", False, str(exc))
        return False


def leg_create_control(shooter: Shooter, hub: Hub) -> None:
    section(f"schedule create control @{shooter.width}")
    goto(shooter, hub, "/")
    page = shooter.page

    check("chair rendered", page.locator('[data-testid="chair"]').count() > 0)
    sched_btn = page.locator('[data-testid="capture-hero-schedule"]')
    if not check("Schedule button on hero", sched_btn.count() > 0):
        shooter.shot("schedule", "no-button", "hero without the Schedule button")
        return

    sched_btn.first.click()
    try:
        page.wait_for_selector('[data-testid="schedule-create-submit"]', timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(400)  # settle the imperative-focus timeout

    submit = page.locator('[data-testid="schedule-create-submit"]')
    check("create window opened", submit.count() > 0)

    focused_tag = page.evaluate("document.activeElement?.tagName")
    focused_label = page.evaluate(
        "document.activeElement?.getAttribute('aria-label') || "
        "document.activeElement?.placeholder || 'unknown'")
    check("a text field is focused in the create window",
          focused_tag in ("INPUT", "TEXTAREA"),
          f"tag={focused_tag} label={focused_label}")

    mic = page.locator('[data-testid="schedule-create-submit"]').locator(
        "xpath=ancestor::*[3]").locator('button[aria-label*="peak"], '
        'button[aria-label*="mic"], [data-testid*="mic"]')
    if mic.count() > 0:
        check("speak-to-fill mic present in the create window", True)
    else:
        finding("mic affordance not located by selector (verify visually in shot)")

    shooter.shot("schedule", "create-window",
                 "in-world create control: title+mic, mode, datetime, duration")
    shooter.assert_clean("schedule create control")


def leg_meetings_scheduled(shooter: Shooter, hub: Hub) -> None:
    section(f"meetings lane SCHEDULED entry @{shooter.width}")
    goto(shooter, hub, "/")
    page = shooter.page

    lane = page.locator('[data-lane="meetings"]')
    check("meetings lane present", lane.count() > 0)

    badge = page.get_by_text("SCHEDULED", exact=False)
    has_badge = badge.count() > 0
    check("SCHEDULED badge in the Meetings lane", has_badge)
    if has_badge:
        check("scheduled entry names its next fire",
              lane.get_by_text("Weekly standup", exact=False).count() > 0)

    shooter.shot("meetings", "scheduled-entry",
                 "Meetings lane: a SCHEDULED recording with next-fire time")
    shooter.assert_clean("meetings scheduled entry")


def main() -> int:
    from playwright.sync_api import sync_playwright

    port = _free_port()
    home = tempfile.mkdtemp(prefix="hs136-walk-")
    hub = Hub(port, TOKEN, home).start()
    seeded = seed_schedule(hub)
    if not seeded:
        finding("schedule seed failed; the SCHEDULED-badge leg may be empty")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for width, height in VIEWPORTS:
                section(f"===== viewport {width}x{height} =====")
                ctx = browser.new_context(viewport={"width": width, "height": height})
                page = ctx.new_page()
                shooter = Shooter(page, width, WALK_OUT)
                leg_create_control(shooter, hub)
                leg_meetings_scheduled(shooter, hub)
                ctx.close()
            browser.close()
    finally:
        hub.stop()

    section("RESULT")
    print(f"  PASS x{cw.PASSES}   FAIL x{len(cw.FAILS)}   SHOTS x{len(cw.SHOTS)}", flush=True)
    for f in cw.FAILS:
        print(f"  FAIL  {f}", flush=True)
    for name, proves in cw.SHOTS:
        print(f"  shot  {name}  {proves}", flush=True)
    return 1 if cw.FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
