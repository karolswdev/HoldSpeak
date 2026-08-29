"""HS-150-06 — the phase walk: the manager's Monday, cold, on real glass.

Graduates story-0203-rig with the exit assertions: person_sections in
the RESPONSE but ABSENT from the monday_brief tables (the persisted
boundary walked, not assumed), the Add-to-1:1-agenda round-trip
through the real 138 authority, and the DELEGATION/MONDAY probes
flipped from the audit's PAINFUL/PERSON-BLIND verdicts.

Through the 149 seam: three reports, the REAL map gesture on a board
card, chips/filter/staleness, the brief's person sections + verbs,
the BriefLane act state — zero keychain interaction by construction.
Orchestrator-run; shots land in story-0203-shots/.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-150-delegation-monday/assets/walk-shots"
TOKEN = "hs150-suite"


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

            from datetime import datetime as _dt, timedelta as _td, timezone as _tz

            ctx, page = open_desk()
            try:
                # BriefLane act state BEFORE any brief exists (D4 fold).
                lane_act = page.locator('[data-testid="brief-lane-act"]')
                lane_act.wait_for(timeout=15000)
                page.screenshot(path=str(SHOTS / "brieflane-act-1440.png"), full_page=True)

                # Seed: People + three reports; Ewa gets a linked 1:1 series.
                api(page, "POST", "/api/people/setup")
                rels = {}
                for name in ("Ewa", "Marek", "Ola"):
                    r = api(page, "POST", "/api/people/relationships",
                            {"display_name": name, "relationship_kind": "direct_report"})
                    rels[name] = r.get("relationship", r).get("id")
                # A commitment + agenda for Ewa (YOU-OWE + backlog signals).
                req = api(page, "POST", f"/api/people/relationships/{rels['Ewa']}/requests",
                          {"body": "Review the auth design doc", "due": None})
                api(page, "POST", f"/api/people/requests/{req.get('request', req).get('id')}/accept", {})
                oo = api(page, "POST", f"/api/people/relationships/{rels['Ewa']}/one-on-ones",
                         {"visibility": "shared_intent"})
                api(page, "POST", f"/api/people/one-on-ones/{oo.get('one_on_one', oo).get('id')}/agenda",
                    {"body": "Growth: conference talk?"})
                # The 1:1 series on the calendar, linked to Ewa.
                starts = _dt.now(_tz.utc).replace(second=0, microsecond=0) + _td(hours=26)
                fixture = home / "week.ics"
                fixture.write_text("\r\n".join([
                    "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//HS150//EN", "BEGIN:VEVENT",
                    "UID:hs150-ewa-11", f"DTSTART:{starts.strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTEND:{(starts + _td(minutes=30)).strftime('%Y%m%dT%H%M%SZ')}",
                    "SUMMARY:1:1 w/ Ewa", "END:VEVENT", "END:VCALENDAR", "",
                ]), encoding="utf-8")
                api(page, "PUT", "/api/settings",
                    {"calendar": {"sources": [{"id": "work", "label": "Work", "url": str(fixture), "enabled": True}]}})
                from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
                assert CalendarIngestConductor().refresh() is True
                api(page, "POST", f"/api/people/relationships/{rels['Ewa']}/calendar-links",
                    {"uid": "hs150-ewa-11", "source_id": "work", "label": "1:1 w/ Ewa"})

                # Owned + unowned board cards via the sync authority.
                _now = _dt.now(_tz.utc)
                items = [
                    {"id": "hs150-ai-1", "task": "Send the RFC to the team", "owner": "Ewa"},
                    {"id": "hs150-ai-2", "task": "Schedule design review", "owner": "Ewa"},
                    {"id": "hs150-ai-3", "task": "Update the deployment runbook", "owner": "Marek"},
                    {"id": "hs150-ai-4", "task": "File the security audit findings", "owner": None},
                ]
                api(page, "POST", "/api/sync/push", {"meetings": [{
                    "meta": {"id": "hs150-m1", "kind": "meeting",
                             "last_modified": _now.isoformat(), "deleted": False},
                    "value": {"id": "hs150-m1",
                              "started_at": (_now - _td(days=4)).isoformat(),
                              "ended_at": (_now - _td(days=4) + _td(minutes=30)).isoformat(),
                              "title": "Team planning", "tags": [], "segments": [], "bookmarks": [],
                              "capture_status": "finalized", "transcription_status": "active",
                              "provenance": "native",
                              "intel": {"timestamp": _now.timestamp(), "topics": [],
                                        "summary": "planning",
                                        "action_items": [{**i, "due": None, "status": "pending",
                                                          "review_state": "accepted",
                                                          "created_at": (_now - _td(days=4)).isoformat()}
                                                         for i in items]}},
                }]})

                # THE MAP GESTURE on a real card: reload, find an Ewa card, map it.
                page.reload(wait_until="load")
                page.locator(".chair:not(.chair-first-value)").wait_for()
                map_btn = page.locator('[data-testid="door-card-map-btn"]').first
                map_btn.wait_for(timeout=15000)
                page.screenshot(path=str(SHOTS / "board-unmapped-1440.png"), full_page=True)
                map_btn.click()
                picker = page.locator('[data-testid="door-card-map-picker"]')
                picker.wait_for(timeout=15000)
                page.screenshot(path=str(SHOTS / "map-picker-1440.png"), full_page=True)
                picker.locator('[data-testid="door-card-map-option"]', has_text="Ewa").first.click()
                page.wait_for_timeout(1000)
            finally:
                ctx.close()

            # Chips + staleness + filter — FRESH CONTEXT (the occlusion law).
            c2, p2 = open_desk()
            try:
                chip = p2.locator('[data-testid="door-card-person-chip"]')
                chip.first.wait_for(timeout=15000)
                if p2.locator(".surface-window", has_text="People").count():
                    failures.append("People window occludes the board shot")
                stale = p2.locator('[data-testid="door-card-staleness"]')
                if not stale.first.is_visible():
                    failures.append("staleness label missing on mapped card")
                p2.screenshot(path=str(SHOTS / "board-mapped-chips-1440.png"), full_page=True)
                p2.locator('[data-testid="door-filter-person"]', has_text="Ewa").first.click()
                p2.wait_for_timeout(500)
                p2.screenshot(path=str(SHOTS / "board-filtered-ewa-1440.png"), full_page=True)
                p2.locator('[data-testid="door-filter-everyone"]').click()

                # Generate via the D1 lane act, then read the sections in BriefView.
                act_btn = p2.locator('[data-testid="brief-lane-act"] button')
                act_btn.wait_for(timeout=15000)
                p2.screenshot(path=str(SHOTS / "brieflane-act-populated-1440.png"), full_page=True)
                act_btn.click()
                p2.locator('[data-testid="brief-lane-act"]').wait_for(state="detached", timeout=20000)
                # Open Intelligence (Brief is its default view) via the Desk menu.
                p2.get_by_role("button", name="Desk", exact=True).first.click()
                dmenu = p2.locator('nav[role="menu"]').last
                dmenu.wait_for(timeout=15000)
                dmenu.get_by_text("Open Intelligence", exact=True).click()
                sections = p2.locator('[data-testid="person-sections"]')
                sections.wait_for(timeout=15000)
                text = sections.inner_text()
                if "Ewa" not in text:
                    failures.append("person sections missing Ewa")
                # The no-inference law on glass: Marek's cards carry an owner
                # STRING but no gesture mapped them — he must NOT appear.
                if "Marek" in text:
                    failures.append("person sections INFERRED Marek from an owner string")
                p2.screenshot(path=str(SHOTS / "brief-person-sections-1440.png"), full_page=True)
                # Select the person row; the manager's verbs live in the footer.
                p2.locator('[data-testid^="person-row-"]').first.click()
                p2.locator('[data-testid="verb-add-agenda"]').wait_for(timeout=15000)
                if p2.locator('[data-testid="verb-open-person"]').count() == 0:
                    failures.append("Open-person verb missing on selection")
                p2.screenshot(path=str(SHOTS / "brief-person-verbs-1440.png"), full_page=True)

                # EXIT S1 — the persisted boundary, walked: person_sections in
                # the RESPONSE, and the Ewa relationship id in NO brief table.
                latest = api(p2, "GET", "/api/brief/latest") or {}
                secs = latest.get("person_sections") or []
                if not any(s.get("display_name") == "Ewa" for s in secs):
                    failures.append("GET /api/brief/latest lacks the Ewa person_section")
                if any(s.get("display_name") == "Marek" for s in secs):
                    failures.append("response INFERRED Marek from an owner string")
                rel_id = rels["Ewa"]
                import sqlite3 as _sq
                con = _sq.connect(db_core.DEFAULT_DB_PATH)
                dump: list[str] = []
                for tbl in ("monday_briefs", "monday_brief_items", "monday_brief_item_shelf"):
                    for row in con.execute(f"SELECT * FROM {tbl}"):  # noqa: S608
                        dump.append(repr(row))
                con.close()
                blob = "\n".join(dump)
                if rel_id in blob or "person_sections" in blob:
                    failures.append("PERSISTED-BOUNDARY BREACH: person material in monday_brief tables")
                if not dump:
                    failures.append("monday_brief tables empty — the persistence probe proved nothing")
                print("MONDAY PROBE: person-blind -> People section in the response,"
                      f" {len(dump)} persisted rows scanned clean")

                # EXIT S2 — Add-to-1:1-agenda round-trips through the real authority.
                p2.locator('[data-testid="verb-add-agenda"]').click()
                deadline = _dt.now(_tz.utc) + _td(seconds=15)
                landed = False
                while _dt.now(_tz.utc) < deadline:
                    oos = api(p2, "GET", f"/api/people/relationships/{rel_id}/one-on-ones") or {}
                    items = [a for s in (oos.get("one_on_ones") or []) for a in (s.get("agenda") or [])]
                    if any("Follow up from brief" in str(a.get("body", "")) for a in items):
                        landed = True
                        break
                    p2.wait_for_timeout(500)
                if not landed:
                    failures.append("Add-to-1:1-agenda round-trip: the agenda item never landed")
                p2.screenshot(path=str(SHOTS / "brief-agenda-added-1440.png"), full_page=True)
                print("DELEGATION PROBE: scan-every-card -> chip + filter + staleness on glass")
            finally:
                c2.close()

            # Story 02's OwnerAliasSection on the Context lens (reworked room).
            c3, p3 = open_desk()
            try:
                p3.get_by_role("button", name="Desk", exact=True).first.click()
                pmenu = p3.locator('nav[role="menu"]').last
                pmenu.wait_for(timeout=15000)
                pmenu.get_by_text("Open People", exact=True).click()
                # Scope to the window layer: story 02's chips put "Ewa" on the
                # board BEHIND the People window (the interception scar).
                pwin = p3.locator(".desk-surface-windows")
                pwin.get_by_text("Ewa", exact=True).first.click()
                pwin.get_by_text("Context", exact=True).first.click()
                aliases = p3.locator('[data-testid="people-owner-aliases"]')
                aliases.wait_for(timeout=15000)
                p3.locator('[data-testid="people-alias-add"]').wait_for(timeout=15000)
                p3.screenshot(path=str(SHOTS / "people-owner-aliases-1440.png"), full_page=True)
            finally:
                c3.close()

            # 393: chips on the narrow board.
            n1, np1 = open_desk(width=393, height=852)
            try:
                np1.locator('[data-testid="door-card-person-chip"]').first.wait_for(timeout=15000)
                np1.screenshot(path=str(SHOTS / "board-mapped-393.png"), full_page=True)
            finally:
                n1.close()
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
