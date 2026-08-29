"""HS-149-03 shot rig — the first headless populated-People glass ever.

Runs entirely through the story-01 seam (HOLDSPEAK_PEOPLE_KEYSTORE_FILE
must be set by the caller alongside the isolated HOME): People setup,
the relationship, the REAL link gesture through the picker, the rail
person chip, NEXT 1:1, and the joy states — zero keychain interaction
by construction. Orchestrator-run; shots land in story-03-shots/.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-149-one-on-one-loop/assets/story-04-shots"
TOKEN = "hs149-brief"


def main() -> int:
    assert os.environ.get("HOLDSPEAK_PEOPLE_KEYSTORE_FILE"), "the story-01 seam env is REQUIRED"
    sys.path.insert(0, str(REPO))
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    SHOTS.mkdir(parents=True, exist_ok=True)
    home = Path(os.environ["HOME"])
    config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
    db_core.DEFAULT_DB_PATH = home / "holdspeak.db"
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
        auth_token=TOKEN,
    )
    url = server.start()
    failures: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)

            def open_desk(width=1440, height=900):
                ctx = browser.new_context(viewport={"width": width, "height": height})
                page = ctx.new_page()
                page.emulate_media(reduced_motion="reduce")
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                chair = page.locator(".chair")
                chair.wait_for()
                if chair.evaluate("el => el.classList.contains('chair-first-value')"):
                    page.get_by_role("button", name="Continue later", exact=True).click()
                page.locator(".chair:not(.chair-first-value)").wait_for()
                return ctx, page

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
                if r["status"] >= 300:
                    raise RuntimeError(f"{method} {path}: {r}")
                return r["payload"]

            def open_people(page):
                page.get_by_role("button", name="Desk", exact=True).first.click()
                menu = page.locator('nav[role="menu"]').last
                menu.wait_for(timeout=15000)
                menu.get_by_text("Open People", exact=True).click()
                page.wait_for_timeout(800)

            ctx, page = open_desk()
            try:
                # 1. The joy state, before setup.
                open_people(page)
                page.locator('[data-testid="people-joy-state"]').wait_for(timeout=15000)
                page.screenshot(path=str(SHOTS / "joy-unconfigured-1440.png"), full_page=True)

                # 2. Headless setup through the seam + the relationship.
                api(page, "POST", "/api/people/setup")
                rel = api(page, "POST", "/api/people/relationships",
                          {"display_name": "Ewa", "relationship_kind": "direct_report"})
                rel_id = rel.get("relationship", rel).get("id")

                # 3. Seed the recurring 1:1 and refresh the calendar.
                starts = datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(hours=2)
                fixture = home / "one-on-one.ics"
                fixture.write_text("\r\n".join([
                    "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//HS149//EN", "BEGIN:VEVENT",
                    "UID:hs149-ewa-11", f"DTSTART:{starts.strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTEND:{(starts + timedelta(minutes=30)).strftime('%Y%m%dT%H%M%SZ')}",
                    "SUMMARY:1:1 w/ Ewa", "END:VEVENT", "END:VCALENDAR", "",
                ]), encoding="utf-8")
                api(page, "PUT", "/api/settings",
                    {"calendar": {"sources": [{"id": "work", "label": "Work", "url": str(fixture), "enabled": True}]}})
                from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
                assert CalendarIngestConductor().refresh() is True

                # 3b. Populate the brief's inputs: a commitment (via request→accept),
                # an agenda item, and a LINKED past meeting via the sync authority
                # (the 147 walk pattern — a peer-delivered meeting carrying the
                # calendar_event_id of an occurrence of the linked series).
                req = api(page, "POST", f"/api/people/relationships/{rel_id}/requests",
                          {"body": "Review the auth design doc", "due": None})
                req_id = req.get("request", req).get("id")
                api(page, "POST", f"/api/people/requests/{req_id}/accept", {})
                oo = api(page, "POST", f"/api/people/relationships/{rel_id}/one-on-ones",
                         {"visibility": "shared_intent"})
                oo_id = oo.get("one_on_one", oo).get("id")
                api(page, "POST", f"/api/people/one-on-ones/{oo_id}/agenda",
                    {"body": "Growth: conference talk?"})
                door_now = api(page, "GET", "/api/door")
                ev_id = next(i["id"] for i in door_now["upcoming"] if i.get("source") == "calendar_event")
                from datetime import datetime as _dt, timedelta as _td, timezone as _tz
                _now = _dt.now(_tz.utc)
                api(page, "POST", "/api/sync/push", {"meetings": [{
                    "meta": {"id": "hs149-last-11", "kind": "meeting",
                             "last_modified": _now.isoformat(), "deleted": False},
                    "value": {"id": "hs149-last-11",
                              "started_at": (_now - _td(days=7)).isoformat(),
                              "ended_at": (_now - _td(days=7) + _td(minutes=30)).isoformat(),
                              "title": "1:1 w/ Ewa", "tags": [], "segments": [], "bookmarks": [],
                              "capture_status": "finalized", "transcription_status": "active",
                              "provenance": "native", "calendar_event_id": ev_id,
                              "intel": {"timestamp": _now.timestamp(), "topics": [],
                                        "summary": "last 1:1",
                                        "action_items": [{"id": "hs149-ai-1",
                                                          "task": "Send the RFC to Ewa",
                                                          "owner": "Karol", "due": None,
                                                          "status": "pending",
                                                          "review_state": "accepted",
                                                          "created_at": _now.isoformat()}]}},
                }]})

                # 4. The REAL gesture: reload, open People, open the picker, click the suggested row.
                page.reload(wait_until="load")
                page.locator(".chair:not(.chair-first-value)").wait_for()
                open_people(page)
                page.get_by_text("Ewa", exact=True).first.click()
                page.get_by_text("Context", exact=True).first.click()
                page.locator('[data-testid="people-link-event"]').click()
                picker = page.locator('[data-testid="people-event-picker"]')
                picker.wait_for(timeout=15000)
                try:
                    picker.get_by_text("SUGGESTED", exact=True).first.wait_for(timeout=8000)
                except Exception:
                    failures.append("picker: no SUGGESTED tag on the name-matching row")
                page.screenshot(path=str(SHOTS / "picker-suggested-1440.png"), full_page=True)
                picker.get_by_text("1:1 w/ Ewa", exact=False).first.click()
                page.wait_for_timeout(800)
                # NEXT 1:1 header appears once linked.
                page.locator('[data-testid="people-next-1on1"]').wait_for(timeout=15000)

                # 4b. THE PREP LENS — the brief on glass.
                page.get_by_role("tab", name="Prep", exact=True).click()
                lens = page.locator('[data-testid="people-prep-lens"]')
                lens.wait_for(timeout=15000)
                text = lens.inner_text()
                for needle in ("Review the auth design doc", "Growth: conference talk?", "Send the RFC to Ewa"):
                    if needle not in text:
                        failures.append(f"prep lens missing {needle!r}")
                page.screenshot(path=str(SHOTS / "prep-lens-1440.png"), full_page=True)

            finally:
                ctx.close()

            # 5. PREP on the rail — FRESH CONTEXT (the occlusion law).
            # the persisted People window would sit OVER the rail while the
            # assertion passed against the element BEHIND it).
            cctx, cpage = open_desk()
            try:
                prep = cpage.locator('[data-testid="door-prep"]')
                prep.first.wait_for(timeout=15000)
                if cpage.locator(".surface-window", has_text="People").count():
                    failures.append("People window occludes the rail shot — trap not dodged")
                cpage.screenshot(path=str(SHOTS / "rail-prep-1440.png"), full_page=True)
                prep.first.click()
                cpage.locator('[data-testid="people-prep-lens"]').wait_for(timeout=15000)
                cpage.screenshot(path=str(SHOTS / "rail-prep-opens-lens-1440.png"), full_page=True)
            finally:
                cctx.close()

            # 6. 393: PREP + chip + Record this on one narrow row.
            nctx, npage = open_desk(width=393, height=852)
            try:
                npage.locator('[data-testid="door-prep"]').first.wait_for(timeout=15000)
                npage.screenshot(path=str(SHOTS / "rail-prep-393.png"), full_page=True)
            finally:
                nctx.close()
            browser.close()
    finally:
        server.stop()
        reset_database()
    for f in failures:
        print("FINDING", f)
    print(f"shots={SHOTS}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
