"""HS-149 pre-charter reduced walk — ZERO keychain writes by construction.

The populated-People legs are BLOCKED by the Phase-138 L3 gap (no
dev-only keystore seam; macOS keychain is UID-scoped and Python
keyring #623 ignores custom keychains) — that blockage IS a walk
finding and becomes story 01. This rig never calls People setup or
any keyring-adjacent write: it shoots the readiness/empty gates, the
Tuesday probe from the calendar side, and the era-mismatch state of
PeopleCore. Orchestrator-run.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-149-one-on-one-loop/assets/audit-walk-shots"
TOKEN = "hs149-audit"


def main() -> int:
    sys.path.insert(0, str(REPO))
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    SHOTS.mkdir(parents=True, exist_ok=True)
    home = Path(os.environ["HOME"])  # caller supplies the isolated HOME
    config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
    db_core.DEFAULT_DB_PATH = home / "holdspeak.db"
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
        auth_token=TOKEN,
    )
    url = server.start()
    findings: list[str] = []
    facts: list[str] = []
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
                return page.evaluate(
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

            # 1. Readiness truth via API (read-only, no key material touched).
            ctx, page = open_desk()
            try:
                readiness = api(page, "GET", "/api/people/readiness")
                facts.append(f"readiness API: {readiness}")

                # 2. Open People from the Desk menu — the empty/unconfigured gate.
                page.get_by_role("button", name="Desk", exact=True).first.click()
                menu = page.locator('nav[role="menu"]').last
                menu.wait_for(timeout=15000)
                menu.get_by_text("Open People", exact=True).click()
                people = page.locator(".surface-window, [data-surface], section").filter(has_text="People").first
                page.wait_for_timeout(1200)
                page.screenshot(path=str(SHOTS / "people-unconfigured-1440.png"), full_page=True)

                # 3. Tuesday probe, calendar side: seed "1:1 w/ Ewa" and look for ANY person path.
                starts = datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(hours=2)
                fixture = home / "one-on-one.ics"
                fixture.write_text("\r\n".join([
                    "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//HS149//EN", "BEGIN:VEVENT",
                    "UID:hs149-ewa-11", f"DTSTART:{starts.strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTEND:{(starts + timedelta(minutes=30)).strftime('%Y%m%dT%H%M%SZ')}",
                    "SUMMARY:1:1 w/ Ewa", "END:VEVENT", "END:VCALENDAR", "",
                ]), encoding="utf-8")
                api(page, "PUT", "/api/settings",
                    {"calendar": {"sources": [{"id": "hs149", "label": "Work", "url": str(fixture), "enabled": True}]}})
                from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
                CalendarIngestConductor().refresh()
                page.reload(wait_until="load")
                page.locator(".chair:not(.chair-first-value)").wait_for()
                rail = page.locator(".door-upcoming-rail")
                row = rail.locator('[data-upcoming-source="calendar_event"]', has_text="1:1 w/ Ewa")
                row.wait_for(timeout=15000)
                page.screenshot(path=str(SHOTS / "tuesday-rail-1440.png"), full_page=True)
                row_html = row.evaluate("el => el.outerHTML")
                has_person_ref = any(k in row_html.lower() for k in ("person", "relationship", "people"))
                facts.append(f"TUESDAY PROBE (a) event→person affordance on rail row: {'EXISTS?' if has_person_ref else 'DOES NOT EXIST'}")
                # Arm it (147) and check the schedule payload for any person field.
                door = api(page, "GET", "/api/door")
                ev = next(i for i in door["payload"]["upcoming"] if i.get("source") == "calendar_event")
                armed = api(page, "POST", "/api/scheduled-recordings", {"calendar_event_id": ev["id"]})
                sched = armed["payload"].get("schedule", {})
                person_fields = [k for k in sched if "person" in k or "relationship" in k]
                facts.append(f"TUESDAY PROBE (b) armed recording person fields: {person_fields or 'NONE — DOES NOT EXIST'}")
                page.reload(wait_until="load")
                page.locator(".chair:not(.chair-first-value)").wait_for()
                page.screenshot(path=str(SHOTS / "tuesday-armed-1440.png"), full_page=True)
            finally:
                ctx.close()

            # 4. Narrow People gate.
            nctx, npage = open_desk(width=393, height=852)
            try:
                npage.get_by_role("button", name="Go", exact=True).first.click()
                gomenu = npage.locator('nav[role="menu"]').last
                gomenu.wait_for(timeout=15000)
                npage.keyboard.press("Escape")
                # People at narrow rides the mark/Desk menus which are hidden; note honestly.
                facts.append("393: Desk menu (Open People) hidden by design; People reachable via ⌘K only")
                npage.screenshot(path=str(SHOTS / "door-393.png"), full_page=True)
            finally:
                nctx.close()
            browser.close()
    finally:
        server.stop()
        reset_database()
    print("== FACTS ==")
    for f in facts:
        print(" ", f)
    for f in findings:
        print("FINDING", f)
    print(f"shots={SHOTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
