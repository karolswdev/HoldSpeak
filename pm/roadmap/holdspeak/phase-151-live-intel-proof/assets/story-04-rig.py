"""HS-151-04 vision proof rig — the snapshot adapter on real metal (8081).

The FIRST real-vision product-path proof: the truth image through the
REAL snapshot import route -> real router dispatch to Qwythos-9B at
http://192.168.1.43:8081/v1 -> anchored review -> confirm -> .ics through
the one bounded parser -> rail events under the snapshot source.

Legs:
  (a) truth image (vision-probe-week.png, 4 events)
  (b) messy image rendered by Playwright (overlapping + all-day)
  (c) refusal: non-calendar image -> zero events or named refusal
  (d) 422 rider: corrupt upload -> named refusal in-flow
  (e) frames: review window populated, rail with snapshot chips, 1440

Orchestrator-runnable; shots land in story-04-shots/.
"""
from __future__ import annotations

import base64
import json
import os
import struct
import sys
import time
import zlib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[5]
ASSETS = REPO / "pm/roadmap/holdspeak/phase-151-live-intel-proof/assets"
SHOTS = ASSETS / "story-04-shots"
TRUTH_IMAGE = ASSETS / "vision-probe-week.png"
TOKEN = "hs151-vision"

# -------------------------------------------------------------------
# Ground truth from the image: "Calendar — Week of September 1, 2026"
# -------------------------------------------------------------------
TRUTH_ANCHOR_DATE = "2026-09-01"  # the Monday visible in the header
TRUTH_EVENTS = [
    {"title": "Team planning", "weekday": "monday", "start": "11:00", "end": "12:00"},
    {"title": "1:1 w/ Ewa", "weekday": "tuesday", "start": "09:00", "end": "09:30"},
    {"title": "Architecture review", "weekday": "thursday", "start": "11:00", "end": "12:30"},
    {"title": "Sprint retro", "weekday": "friday", "start": "14:00", "end": "15:00"},
]

# Messy image ground truth (rendered by the rig)
MESSY_ANCHOR_DATE = "2026-09-08"  # next Monday
MESSY_EVENTS = [
    {"title": "Sprint Planning", "weekday": "monday", "start": "09:00", "end": "10:30"},
    {"title": "Design Review", "weekday": "monday", "start": "09:30", "end": "11:00"},  # overlaps
    {"title": "All Hands", "weekday": "wednesday", "start": "00:00", "end": "23:59"},   # all-day
    {"title": "Retro", "weekday": "friday", "start": "15:00", "end": "16:00"},
]


def main() -> int:
    assert os.environ.get("HOLDSPEAK_PEOPLE_KEYSTORE_FILE"), "keystore seam env REQUIRED"
    sys.path.insert(0, str(REPO))
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    SHOTS.mkdir(parents=True, exist_ok=True)
    home = Path(os.environ["HOME"])
    config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
    db_core.DEFAULT_DB_PATH = home / "holdspeak.db"
    reset_database()

    # --- Wire the vision profile (legacy v1) ---
    db = get_database()
    db.profiles.upsert(
        profile_id="hs151-vision",
        name="Qwythos 9B Vision (8081)",
        kind="openAICompatible",
        base_url="http://192.168.1.43:8081/v1",
        model="Qwythos-9B",
        requires_key=False,
    )

    # Boot the real hub
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=TOKEN,
    )
    url = server.start()
    print(f"Hub at {url}")

    findings: list[str] = []
    failures: list[str] = []
    json_reliability: list[str] = []
    extraction_fidelity: list[dict[str, Any]] = []

    # NOTE: parse_extraction_json code-fence fix applied in product code
    # (calendar_snapshot_service.py:108) per orchestrator ruling — no monkeypatch.

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)

            # -------------------------------------------------------
            # Helper: API call via page context
            # -------------------------------------------------------
            def api(page, method, path, body=None):
                r = page.evaluate(
                    """async ([m, p, b, t]) => {
                      const r = await fetch(p, {method: m,
                        headers: {authorization: `Bearer ${t}`,
                                  ...(b ? {"content-type": "application/json"} : {})},
                        body: b ? JSON.stringify(b) : undefined});
                      const ct = r.headers.get("content-type") || "";
                      return {status: r.status,
                              payload: ct.includes("json") ? await r.json() : await r.text()};
                    }""",
                    [method, path, body, TOKEN],
                )
                return r

            def open_desk(width=1440, height=900, nav_timeout=180000):
                ctx = browser.new_context(viewport={"width": width, "height": height})
                page = ctx.new_page()
                page.set_default_timeout(nav_timeout)
                page.emulate_media(reduced_motion="reduce")
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                chair = page.locator(".chair")
                chair.wait_for(timeout=30000)
                if chair.evaluate("el => el.classList.contains('chair-first-value')"):
                    page.get_by_role("button", name="Continue later", exact=True).click()
                page.locator(".chair:not(.chair-first-value)").wait_for(timeout=30000)
                return ctx, page

            # -------------------------------------------------------
            # Wire the assignment via the API (the REAL adoption path)
            # -------------------------------------------------------
            ctx0, page0 = open_desk()
            try:
                assign_r = api(page0, "POST", "/api/inference/assignments/set", {
                    "command_id": "hs151-wire-snapshot-vision",
                    "expected_revision": 0,
                    "scope": {"kind": "capability", "capability_id": "calendar.snapshot_extract"},
                    "entries": [{"profile_id": "legacy-hs151-vision"}],
                })
                if assign_r["status"] >= 300:
                    findings.append(f"Assignment set failed (status {assign_r['status']}): {assign_r['payload']} -- falling through to direct dispatch")
                else:
                    print(f"Assignment set OK: capability calendar.snapshot_extract -> legacy-hs151-vision")
            finally:
                ctx0.close()

            # -------------------------------------------------------
            # LEG (a): Truth image through the REAL product path
            # -------------------------------------------------------
            print("\n=== LEG (a): Truth image (vision-probe-week.png) ===")
            assert TRUTH_IMAGE.exists(), f"Truth image not found: {TRUTH_IMAGE}"
            truth_bytes = TRUTH_IMAGE.read_bytes()
            truth_b64 = base64.b64encode(truth_bytes).decode("ascii")

            ctx1, page1 = open_desk()
            try:
                # Upload via multipart FormData (the real glass path)
                t0 = time.time()
                extract_result = page1.evaluate(
                    """async ([token, b64]) => {
                      const binary = atob(b64);
                      const bytes = new Uint8Array(binary.length);
                      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
                      const blob = new Blob([bytes], {type: "image/png"});
                      const form = new FormData();
                      form.append("files", blob, "vision-probe-week.png");
                      const r = await fetch("/api/calendar/snapshot", {
                        method: "POST",
                        headers: { authorization: `Bearer ${token}` },
                        body: form,
                      });
                      return await r.json();
                    }""",
                    [TOKEN, truth_b64],
                )
                t1 = time.time()
                elapsed_a = t1 - t0
                print(f"  Extraction took {elapsed_a:.1f}s")
                print(f"  Raw result: {json.dumps(extract_result, indent=2)}")

                # Record JSON reliability
                if extract_result.get("error"):
                    json_reliability.append(f"LEG_A: model returned error: {extract_result['error']}")
                if not extract_result.get("success"):
                    json_reliability.append(f"LEG_A: extraction unsuccessful: {extract_result}")

                extracted_events = extract_result.get("events", [])
                anchor_date = extract_result.get("anchor_date")
                anchor_conf = extract_result.get("anchor_confidence")

                # Shape assertion: did we get events?
                if not extracted_events:
                    failures.append("LEG_A: zero events extracted from truth image")
                else:
                    # Content assertion (grounded, not char-exact)
                    fidelity_a = _check_truth_fidelity(
                        extracted_events, TRUTH_EVENTS, "LEG_A"
                    )
                    extraction_fidelity.append({"leg": "a", "result": fidelity_a})
                    for note in fidelity_a.get("misses", []):
                        findings.append(f"LEG_A miss: {note}")

                # Anchor assertion
                if anchor_date:
                    if anchor_date == TRUTH_ANCHOR_DATE:
                        print(f"  Anchor date EXACT MATCH: {anchor_date}")
                    else:
                        findings.append(
                            f"LEG_A: anchor date mismatch: got {anchor_date}, "
                            f"expected {TRUTH_ANCHOR_DATE}"
                        )
                else:
                    findings.append("LEG_A: no anchor_date returned")

                if anchor_conf:
                    print(f"  Anchor confidence: {anchor_conf}")
                    if anchor_conf != "visible_header":
                        findings.append(
                            f"LEG_A: anchor confidence is '{anchor_conf}', "
                            f"expected 'visible_header' (the header IS visible)"
                        )

                # Egress truth
                egress = extract_result.get("egress")
                if egress:
                    print(f"  Egress: {egress}")
                else:
                    findings.append("LEG_A: no egress returned")

                # CONFIRM the extraction if we got events
                if extracted_events and anchor_date:
                    confirm_r = api(page1, "POST", "/api/calendar/snapshot/confirm", {
                        "anchor_date": anchor_date,
                        "events": extracted_events,
                    })
                    if confirm_r["status"] >= 300:
                        failures.append(
                            f"LEG_A confirm failed (status {confirm_r['status']}): "
                            f"{confirm_r['payload']}"
                        )
                    else:
                        confirm_body = confirm_r["payload"]
                        print(f"  Confirm OK: {confirm_body.get('events_count')} events, "
                              f"source_id={confirm_body.get('source_id')}")

                        # Trigger calendar refresh so rail shows the events
                        from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
                        CalendarIngestConductor().refresh()
                        page1.wait_for_timeout(2000)
                elif not extracted_events:
                    findings.append("LEG_A: skipping confirm (no events)")
                elif not anchor_date:
                    findings.append("LEG_A: skipping confirm (no anchor)")
            finally:
                ctx1.close()

            # -------------------------------------------------------
            # LEG (b): Messy image (overlapping + all-day)
            # -------------------------------------------------------
            print("\n=== LEG (b): Messy image (Playwright-rendered) ===")
            messy_png = _render_messy_calendar(browser)
            messy_b64 = base64.b64encode(messy_png).decode("ascii")

            ctx2, page2 = open_desk()
            try:
                t0 = time.time()
                messy_result = page2.evaluate(
                    """async ([token, b64]) => {
                      const binary = atob(b64);
                      const bytes = new Uint8Array(binary.length);
                      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
                      const blob = new Blob([bytes], {type: "image/png"});
                      const form = new FormData();
                      form.append("files", blob, "messy-calendar.png");
                      const r = await fetch("/api/calendar/snapshot", {
                        method: "POST",
                        headers: { authorization: `Bearer ${token}` },
                        body: form,
                      });
                      return await r.json();
                    }""",
                    [TOKEN, messy_b64],
                )
                t1 = time.time()
                elapsed_b = t1 - t0
                print(f"  Extraction took {elapsed_b:.1f}s")
                print(f"  Raw result: {json.dumps(messy_result, indent=2)}")

                messy_events = messy_result.get("events", [])
                if not messy_events:
                    findings.append("LEG_B: zero events extracted from messy image (model miss)")
                    json_reliability.append("LEG_B: zero events from a valid calendar image")
                else:
                    fidelity_b = _check_truth_fidelity(
                        messy_events, MESSY_EVENTS, "LEG_B"
                    )
                    extraction_fidelity.append({"leg": "b", "result": fidelity_b})
                    for note in fidelity_b.get("misses", []):
                        findings.append(f"LEG_B miss: {note}")

                if messy_result.get("error"):
                    json_reliability.append(
                        f"LEG_B: model returned error: {messy_result['error']}"
                    )
            finally:
                ctx2.close()

            # -------------------------------------------------------
            # LEG (c): COUNSEL S2 refusal — non-calendar image
            # -------------------------------------------------------
            print("\n=== LEG (c): Refusal (non-calendar image) ===")
            refusal_png = _render_non_calendar_image(browser)
            refusal_b64 = base64.b64encode(refusal_png).decode("ascii")

            ctx3, page3 = open_desk()
            try:
                t0 = time.time()
                refusal_result = page3.evaluate(
                    """async ([token, b64]) => {
                      const binary = atob(b64);
                      const bytes = new Uint8Array(binary.length);
                      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
                      const blob = new Blob([bytes], {type: "image/png"});
                      const form = new FormData();
                      form.append("files", blob, "not-a-calendar.png");
                      const r = await fetch("/api/calendar/snapshot", {
                        method: "POST",
                        headers: { authorization: `Bearer ${token}` },
                        body: form,
                      });
                      return await r.json();
                    }""",
                    [TOKEN, refusal_b64],
                )
                t1 = time.time()
                elapsed_c = t1 - t0
                print(f"  Extraction took {elapsed_c:.1f}s")
                print(f"  Raw result: {json.dumps(refusal_result, indent=2)}")

                refusal_events = refusal_result.get("events", [])
                refusal_error = refusal_result.get("error")

                if refusal_events:
                    # The model invented events from a non-calendar image
                    findings.append(
                        f"LEG_C: CRITICAL — model invented {len(refusal_events)} events "
                        f"from a non-calendar image: {refusal_events}"
                    )
                    json_reliability.append(
                        f"LEG_C: model hallucinated events from text: {refusal_events}"
                    )
                elif refusal_error:
                    print(f"  Refusal OK: named error '{refusal_error}'")
                else:
                    print("  Refusal OK: zero events, no named error")
                    findings.append(
                        "LEG_C: zero events but no named refusal error "
                        "(parse_extraction_json should have set one)"
                    )
            finally:
                ctx3.close()

            # -------------------------------------------------------
            # LEG (d): 422 rider — corrupt/invalid upload
            # -------------------------------------------------------
            print("\n=== LEG (d): 422 rider (corrupt upload) ===")
            ctx4, page4 = open_desk()
            try:
                # Send a text/plain file (unsupported type)
                corrupt_result = page4.evaluate(
                    """async ([token]) => {
                      const blob = new Blob(["not an image"], {type: "text/plain"});
                      const form = new FormData();
                      form.append("files", blob, "garbage.txt");
                      const r = await fetch("/api/calendar/snapshot", {
                        method: "POST",
                        headers: { authorization: `Bearer ${token}` },
                        body: form,
                      });
                      return {status: r.status, payload: await r.json()};
                    }""",
                    [TOKEN],
                )
                print(f"  Status: {corrupt_result['status']}")
                print(f"  Payload: {corrupt_result['payload']}")

                if corrupt_result["status"] == 422:
                    error_msg = corrupt_result["payload"].get("error", "")
                    if "unsupported type" in error_msg.lower() or "text/plain" in error_msg.lower():
                        print("  422 refusal OK: named type-refusal in-flow")
                    else:
                        findings.append(
                            f"LEG_D: 422 returned but error not descriptive: '{error_msg}'"
                        )
                else:
                    failures.append(
                        f"LEG_D: expected 422, got {corrupt_result['status']}: "
                        f"{corrupt_result['payload']}"
                    )

                # Also test: zero files
                zero_result = page4.evaluate(
                    """async ([token]) => {
                      const form = new FormData();
                      const r = await fetch("/api/calendar/snapshot", {
                        method: "POST",
                        headers: { authorization: `Bearer ${token}` },
                        body: form,
                      });
                      return {status: r.status, payload: await r.json()};
                    }""",
                    [TOKEN],
                )
                print(f"  Zero-files status: {zero_result['status']}")
                if zero_result["status"] != 422:
                    findings.append(
                        f"LEG_D: zero-files expected 422, got {zero_result['status']}"
                    )
            finally:
                ctx4.close()

            # -------------------------------------------------------
            # LEG (e): Frames — review window, rail, 1440
            # -------------------------------------------------------
            print("\n=== LEG (e): Frames ===")
            ctx5, page5 = open_desk()
            try:
                # The rail should show snapshot events if LEG_A confirm succeeded
                page5.wait_for_timeout(2000)
                page5.screenshot(
                    path=str(SHOTS / "rail-snapshot-1440.png"), full_page=True
                )
                print(f"  Frame: rail-snapshot-1440.png")

                # Check for the O365 SNAPSHOT source label on the rail
                snapshot_label = page5.locator("text=O365 SNAPSHOT")
                if snapshot_label.count() > 0:
                    print("  Rail shows 'O365 SNAPSHOT' source label")
                else:
                    findings.append("LEG_E: 'O365 SNAPSHOT' label not visible on rail")

                # Check for snapshot chips
                chips = page5.locator('[data-testid*="snapshot"], [data-testid*="calendar-chip"]')
                if chips.count() > 0:
                    print(f"  Found {chips.count()} snapshot/calendar chips")
                else:
                    # Try broader search
                    event_items = page5.locator('[data-testid*="calendar-event"], [data-testid*="rail-event"]')
                    if event_items.count() > 0:
                        print(f"  Found {event_items.count()} calendar/rail event items")
                    else:
                        findings.append("LEG_E: no snapshot chips or event items visible on rail")

                page5.screenshot(
                    path=str(SHOTS / "desk-with-snapshot-1440.png"), full_page=True
                )
            finally:
                ctx5.close()

            browser.close()
    finally:
        server.stop()
        reset_database()

    # -------------------------------------------------------------------
    # REPORT
    # -------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("HS-151-04 VISION PROOF RIG REPORT")
    print("=" * 60)

    print(f"\nShots: {SHOTS}")

    if extraction_fidelity:
        print("\n--- Extraction Fidelity ---")
        for f in extraction_fidelity:
            leg = f["leg"]
            r = f["result"]
            print(f"  Leg {leg}: {r['matched']}/{r['expected']} truth events matched, "
                  f"{r['extra']} extra, {r['total_extracted']} total extracted")

    if json_reliability:
        print("\n--- JSON Reliability (COUNSEL L2) ---")
        for note in json_reliability:
            print(f"  {note}")
    else:
        print("\n--- JSON Reliability (COUNSEL L2): clean ---")

    if findings:
        print(f"\n--- Findings ({len(findings)}) ---")
        for f in findings:
            print(f"  FINDING: {f}")
    else:
        print("\n--- Findings: none ---")

    if failures:
        print(f"\n--- Failures ({len(failures)}) ---")
        for f in failures:
            print(f"  FAILURE: {f}")
        return 1
    else:
        print("\n--- Failures: none ---")

    print(f"\nDONE (exit 0)")
    return 0


def _check_truth_fidelity(
    extracted: list[dict[str, Any]],
    truth: list[dict[str, Any]],
    tag: str,
) -> dict[str, Any]:
    """Grounded fidelity check: substring match on title, exact weekday, approximate times.

    Returns a summary dict with matched/expected/extra/misses.
    """
    matched = 0
    misses: list[str] = []
    matched_indices: set[int] = set()

    for truth_event in truth:
        found = False
        for i, ext in enumerate(extracted):
            if i in matched_indices:
                continue
            # Title: case-insensitive substring
            ext_title = str(ext.get("title", "")).lower()
            truth_title = truth_event["title"].lower()
            if truth_title not in ext_title and ext_title not in truth_title:
                # Also try key words
                truth_words = set(truth_title.split())
                ext_words = set(ext_title.split())
                if not truth_words.intersection(ext_words):
                    continue
            # Weekday: exact (the schema enforces lowercase English)
            ext_weekday = str(ext.get("weekday", "")).lower()
            if ext_weekday != truth_event["weekday"]:
                continue
            # Times: allow +/- 30 min tolerance for model nondeterminism
            ext_start = str(ext.get("start_time", ""))
            ext_end = str(ext.get("end_time", ""))
            if ext_start and ext_end:
                start_ok = _time_close(ext_start, truth_event["start"], 30)
                end_ok = _time_close(ext_end, truth_event["end"], 30)
                if not (start_ok and end_ok):
                    continue
            found = True
            matched_indices.add(i)
            matched += 1
            break
        if not found:
            misses.append(
                f"{truth_event['title']} ({truth_event['weekday']} "
                f"{truth_event['start']}-{truth_event['end']})"
            )

    extra = len(extracted) - matched
    return {
        "matched": matched,
        "expected": len(truth),
        "total_extracted": len(extracted),
        "extra": extra,
        "misses": misses,
    }


def _time_close(a: str, b: str, tolerance_min: int) -> bool:
    """Check if two HH:MM times are within tolerance_min of each other."""
    try:
        ah, am = int(a[:2]), int(a[3:5])
        bh, bm = int(b[:2]), int(b[3:5])
        diff = abs((ah * 60 + am) - (bh * 60 + bm))
        return diff <= tolerance_min
    except (ValueError, IndexError):
        return False


def _render_messy_calendar(browser) -> bytes:
    """Render a messy calendar image via Playwright (overlapping events + all-day row).

    Returns PNG bytes. The rig knows what it drew.
    """
    html = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body { font-family: Segoe UI, Arial, sans-serif; margin: 20px; background: white; }
  h2 { font-size: 18px; margin-bottom: 10px; }
  .grid { display: grid; grid-template-columns: 60px repeat(5, 1fr); border: 1px solid #ccc; }
  .header { background: #f0f0f0; padding: 6px 8px; font-weight: bold; font-size: 13px;
            border-bottom: 2px solid #4285f4; text-align: center; }
  .time-label { padding: 4px 6px; font-size: 11px; color: #666; border-right: 1px solid #eee;
                height: 50px; }
  .cell { border: 1px solid #eee; height: 50px; position: relative; }
  .event { position: absolute; left: 2px; right: 2px; padding: 2px 4px; font-size: 11px;
           border-radius: 3px; overflow: hidden; z-index: 1; }
  .event-blue { background: #d0e4ff; border-left: 3px solid #4285f4; }
  .event-green { background: #d4edda; border-left: 3px solid #28a745; }
  .event-red { background: #fdd; border-left: 3px solid #dc3545; }
  .allday-row { grid-column: 1 / -1; background: #e8f0fe; padding: 4px 8px; font-size: 12px;
                border-bottom: 1px solid #ccc; }
</style></head><body>
<h2>Calendar &mdash; Week of September 8, 2026</h2>
<div class="grid">
  <div class="header"></div>
  <div class="header">Mon Sep 8</div>
  <div class="header">Tue Sep 9</div>
  <div class="header">Wed Sep 10</div>
  <div class="header">Thu Sep 11</div>
  <div class="header">Fri Sep 12</div>
</div>
<div style="background:#e8f0fe;padding:4px 8px;font-size:12px;border:1px solid #ccc;border-top:0;">
  <strong>All day:</strong> Wed &mdash; <span style="color:#4285f4;">All Hands</span>
</div>
<div class="grid">
  <div class="time-label">09:00</div>
  <div class="cell">
    <div class="event event-blue" style="top:0;height:75px;">
      <strong>Sprint Planning</strong><br>09:00&ndash;10:30
    </div>
    <div class="event event-green" style="top:25px;height:75px;opacity:0.9;">
      <strong>Design Review</strong><br>09:30&ndash;11:00
    </div>
  </div>
  <div class="cell"></div><div class="cell"></div><div class="cell"></div><div class="cell"></div>
  <div class="time-label">10:00</div>
  <div class="cell"></div><div class="cell"></div><div class="cell"></div><div class="cell"></div><div class="cell"></div>
  <div class="time-label">11:00</div>
  <div class="cell"></div><div class="cell"></div><div class="cell"></div><div class="cell"></div><div class="cell"></div>
  <div class="time-label">15:00</div>
  <div class="cell"></div><div class="cell"></div><div class="cell"></div><div class="cell"></div>
  <div class="cell">
    <div class="event event-red" style="top:0;height:50px;">
      <strong>Retro</strong><br>15:00&ndash;16:00
    </div>
  </div>
</div>
</body></html>"""
    ctx = browser.new_context(viewport={"width": 900, "height": 500})
    page = ctx.new_page()
    page.set_content(html)
    page.wait_for_timeout(500)
    png_bytes = page.screenshot(type="png")
    # Save a copy for the evidence trail
    (SHOTS / "messy-calendar-rendered.png").write_bytes(png_bytes)
    ctx.close()
    return png_bytes


def _render_non_calendar_image(browser) -> bytes:
    """Render a non-calendar image (paragraph of text) via Playwright.

    Returns PNG bytes. Must yield zero events or a named refusal.
    """
    html = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body { font-family: Georgia, serif; margin: 40px; background: #f9f9f9; max-width: 600px; }
  h1 { font-size: 24px; }
  p { font-size: 16px; line-height: 1.6; }
</style></head><body>
<h1>The History of Bread Making</h1>
<p>Bread is one of the oldest prepared foods, dating back to the Neolithic era.
The earliest breads were flatbreads made from ground grains and water. Ancient
Egyptians discovered that allowing dough to ferment produced lighter, softer
bread. This discovery led to the development of leavened bread around 4000 BCE.</p>
<p>Medieval European bakers formed guilds to regulate bread production. The
price and weight of bread was often controlled by law. White bread, made from
finely sifted flour, was a luxury reserved for the wealthy. Common people ate
darker breads made from rye, barley, or mixed grains.</p>
<p>Modern bread production was revolutionized by the Chorleywood process in
1961, which uses intensive mechanical working of dough to dramatically reduce
fermentation time. Today, artisanal bakers are returning to traditional
long-fermentation methods.</p>
</body></html>"""
    ctx = browser.new_context(viewport={"width": 700, "height": 500})
    page = ctx.new_page()
    page.set_content(html)
    page.wait_for_timeout(500)
    png_bytes = page.screenshot(type="png")
    (SHOTS / "non-calendar-rendered.png").write_bytes(png_bytes)
    ctx.close()
    return png_bytes


if __name__ == "__main__":
    raise SystemExit(main())
