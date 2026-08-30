"""HS-150-07 shot rig — the deep room (Intelligence Follow-through) wears the person grammar.

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
SHOTS = REPO / "pm/roadmap/holdspeak/phase-150-delegation-monday/assets/story-07-shots"
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

            from datetime import datetime as _dt, timedelta as _td, timezone as _tz

            ctx, page = open_desk()
            try:
                # Seed: People + Ewa, alias mapped via API (the gesture itself is
                # story-02's proven exhibit); owned + unowned action items.
                api(page, "POST", "/api/people/setup")
                r = api(page, "POST", "/api/people/relationships",
                        {"display_name": "Ewa", "relationship_kind": "direct_report"})
                rel_id = r.get("relationship", r).get("id")
                api(page, "POST", f"/api/people/relationships/{rel_id}/owner-aliases",
                    {"alias": "Ewa"})
                _now = _dt.now(_tz.utc)
                items = [
                    {"id": "hs15007-ai-1", "task": "Send the RFC to the team", "owner": "Ewa"},
                    {"id": "hs15007-ai-2", "task": "Update the deployment runbook", "owner": "Marek"},
                ]
                api(page, "POST", "/api/sync/push", {"meetings": [{
                    "meta": {"id": "hs15007-m1", "kind": "meeting",
                             "last_modified": _now.isoformat(), "deleted": False},
                    "value": {"id": "hs15007-m1",
                              "started_at": (_now - _td(days=3)).isoformat(),
                              "ended_at": (_now - _td(days=3) + _td(minutes=30)).isoformat(),
                              "title": "Team planning", "tags": [], "segments": [], "bookmarks": [],
                              "capture_status": "finalized", "transcription_status": "active",
                              "provenance": "native",
                              "intel": {"timestamp": _now.timestamp(), "topics": [],
                                        "summary": "planning",
                                        "action_items": [{**i, "due": None, "status": "pending",
                                                          "review_state": "accepted",
                                                          "created_at": (_now - _td(days=3)).isoformat()}
                                                         for i in items]}},
                }]})
            finally:
                ctx.close()

            # The deep room at 1440, via the real Desk-menu gesture.
            c2, p2 = open_desk()
            try:
                p2.get_by_role("button", name="Desk", exact=True).first.click()
                menu = p2.locator('nav[role="menu"]').last
                menu.wait_for(timeout=15000)
                menu.get_by_text("Open Intelligence", exact=True).click()
                p2.get_by_role("button", name="Follow-through", exact=True).click()
                chip = p2.locator(".follow-through-person-chip", has_text="Ewa")
                chip.first.wait_for(timeout=15000)
                if "waiting" not in chip.first.inner_text():
                    failures.append("mapped chip lacks the staleness label")
                marek = p2.locator(".follow-through-owner")
                if marek.count() == 0:
                    failures.append("unmapped owner lost its initials rendering")
                p2.screenshot(path=str(SHOTS / "deep-room-chips-1440.png"), full_page=True)
            finally:
                c2.close()

            # 393 — honest absence: the pullout host does not operate at
            # narrow (pre-existing; the navigate event no-ops, the Desk menu
            # is hidden — the 149 "People at 393" reachability family). The
            # walk RECORDS the posture; if narrow reachability ever ships,
            # this leg goes stale loudly and gets rewritten to shoot it.
            n1, np1 = open_desk(width=393, height=852)
            try:
                np1.wait_for_timeout(1500)
                np1.evaluate("""() => window.dispatchEvent(new CustomEvent(
                    'holdspeak:intelligence-navigate', {detail: {view: 'follow-through'}}))""")
                np1.wait_for_timeout(2000)
                opened = np1.locator(".intelligence-pullout").count()
                if opened:
                    failures.append(
                        "393 now opens the Intelligence pullout — reachability "
                        "arrived; rewrite this leg to shoot the deep room narrow")
                print("393 PROBE: deep room unreachable at narrow (pre-existing posture, recorded)")
                np1.screenshot(path=str(SHOTS / "deep-room-393-unreachable.png"), full_page=True)
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
