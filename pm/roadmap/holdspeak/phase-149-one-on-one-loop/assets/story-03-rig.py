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
SHOTS = REPO / "pm/roadmap/holdspeak/phase-149-one-on-one-loop/assets/story-03-shots"
TOKEN = "hs149-gesture"


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

                # 4. The REAL gesture: reload, open People, open the picker, click the suggested row.
                page.reload(wait_until="load")
                page.locator(".chair:not(.chair-first-value)").wait_for()
                open_people(page)
                page.get_by_text("Ewa", exact=True).first.click()
                page.get_by_text("Context", exact=True).first.click()
                page.locator('[data-testid="people-link-event"]').click()
                picker = page.locator('[data-testid="people-event-picker"]')
                picker.wait_for(timeout=15000)
                if "SUGGESTED" not in picker.inner_text():
                    failures.append("picker: no SUGGESTED tag on the name-matching row")
                page.screenshot(path=str(SHOTS / "picker-suggested-1440.png"), full_page=True)
                picker.get_by_text("1:1 w/ Ewa", exact=False).first.click()
                page.wait_for_timeout(800)
                # NEXT 1:1 header appears once linked.
                page.locator('[data-testid="people-next-1on1"]').wait_for(timeout=15000)
                page.screenshot(path=str(SHOTS / "linked-next-1on1-1440.png"), full_page=True)

            finally:
                ctx.close()

            # 5. The rail person chip — FRESH CONTEXT (the walk-law trap:
            # the persisted People window would sit OVER the rail while the
            # assertion passed against the element BEHIND it).
            cctx, cpage = open_desk()
            try:
                chip = cpage.locator('[data-testid="door-person-chip"]')
                chip.first.wait_for(timeout=15000)
                if "EWA" not in chip.first.inner_text().upper():
                    failures.append(f"person chip text: {chip.first.inner_text()!r}")
                if cpage.locator(".surface-window", has_text="People").count():
                    failures.append("People window occludes the chip shot — trap not dodged")
                cpage.screenshot(path=str(SHOTS / "rail-person-chip-1440.png"), full_page=True)
            finally:
                cctx.close()

            # 6. 393: the chip coexisting with the row grammar.
            nctx, npage = open_desk(width=393, height=852)
            try:
                npage.locator('[data-testid="door-person-chip"]').first.wait_for(timeout=15000)
                npage.screenshot(path=str(SHOTS / "rail-person-chip-393.png"), full_page=True)
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
