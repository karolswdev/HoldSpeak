#!/usr/bin/env python3
"""HS-56-07 closeout dogfood: the whole phase, live, on one runtime.

No mocks in any chain — every card is driven by a real broadcast over the
real `/ws` socket of a live server:

1. The dock follows runtime states sent over the REAL socket
   (`runtime_activity` broadcasts, not synthetic DOM events).
2. A real proposal slides the alert card out (three privacy answers); while
   it is up a second event arrives and the QUEUE holds (one card + "+1").
3. Approve on the card vs. the dashboard's approve on a twin proposal:
   the audited transitions are IDENTICAL (status + decided_by, side by side).
4. The queued learned card presents next (real correction, honest reach).
5. A real meeting wrap presents the aftercare card.
6. The off-proof: mascot off → the served page is byte-identical and no
   card ever appears; presence off entirely → same silence.

Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python pm/roadmap/holdspeak/phase-56-qlippy/dogfood_story07.py
"""
from __future__ import annotations

import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

OUT_DIR = Path(__file__).resolve().parent / "screenshots"


def _seed_meeting(db, meeting_id):
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    started = datetime(2026, 6, 10, 10, 0, 0)
    state = MeetingState(
        id=meeting_id,
        started_at=started,
        ended_at=datetime(2026, 6, 10, 11, 0, 0),
        title="Closeout dogfood",
        segments=[TranscriptSegment(text="fix the flaky login test", speaker="Me", start_time=0.0, end_time=10.0)],
    )
    state.intel = IntelSnapshot(
        timestamp=60.0,
        topics=[],
        action_items=[{
            # Unique per meeting: a shared id would let a later save steal the row.
            "id": f"a1-{meeting_id}", "task": "Fix the flaky login test", "owner": "Me",
            "due": None, "status": "pending", "review_state": "accepted",
            "source_timestamp": None, "created_at": started.isoformat(),
        }],
        summary="",
    )
    db.meetings.save_meeting(state)


def main() -> int:
    import httpx
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.db import get_database, reset_database
    from holdspeak.meeting_session import (
        IntelSnapshot,
        MeetingSession,
        MeetingState,
        TranscriptSegment,
    )
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    db = get_database(tmp / "dogfood.db")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _seed_meeting(db, "m-card")
    _seed_meeting(db, "m-dash")
    entry = db.dictation_journal.record(
        source="dictation", transcript="follow up with sam about the launch", final_text="x"
    )
    db.dictation_journal.record(
        source="dictation", transcript="follow up with sam about launch timing", final_text="y"
    )

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)
    failures: list[str] = []
    page_errors: list[str] = []

    def shot(page, name):
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT_DIR / name))

    try:
        httpx.put(f"{url}/api/settings", json={"presence": {"enabled": True, "mascot": True}}, timeout=10)
        html_mascot_on = httpx.get(f"{url}/presence", timeout=10).text

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 520, "height": 470})
            page.on("pageerror", lambda err: page_errors.append(str(err)))
            page.goto(f"{url}/presence", wait_until="networkidle")
            page.wait_for_selector("#qlippy:not([hidden])", timeout=5000)
            page.wait_for_timeout(400)

            # 1. The dock follows REAL socket broadcasts.
            def dock_state():
                return page.get_attribute("#qlippy-dock-sprite", "data-state")

            seen = []
            for state, expected in (("listening", "listening"), ("processing", "thinking"), ("complete", "approve")):
                server.broadcast("runtime_activity", {"state": state, "label": state, "detail": "dogfood"})
                page.wait_for_timeout(450)
                seen.append((state, dock_state()))
                if dock_state() != expected:
                    failures.append(f"dock at {state!r}: expected {expected!r}, got {dock_state()!r}")
            shot(page, "story07-dock-flourish.png")
            page.wait_for_timeout(2200)  # the flourish ends → idle
            if dock_state() != "idle":
                failures.append(f"dock did not settle idle after the flourish: {dock_state()!r}")
            if not failures:
                print(f"PASS  the dock followed real socket broadcasts {seen} and settled idle")

            # 2. The real proposal card + the queue holding under a race.
            filed = httpx.post(
                f"{url}/api/meetings/m-card/aftercare/file-issue",
                json={"action_item_id": "a1-m-card", "repo": "acme/widgets"},
                timeout=10,
            ).json()
            if "proposal" not in filed:
                raise RuntimeError(f"file-issue refused: {filed}")
            p_card = filed["proposal"]["id"]
            page.wait_for_selector("#qlippy-card.is-in", timeout=5000)
            privacy = (page.text_content("#qlippy-privacy") or "").strip()
            for needle in ("Data used:", "goes to github", "Your controls:"):
                if needle not in privacy:
                    failures.append(f"privacy answer missing: {needle!r}")
            shot(page, "story07-actuator-card.png")

            # The race: a second moment arrives while the sticky card is up.
            corrected = httpx.post(
                f"{url}/api/dictation/journal/{entry.id}/correct",
                json={"kind": "intent", "value": "action_item"},
                timeout=10,
            ).json()
            page.wait_for_timeout(600)
            hint = (page.text_content("#qlippy-queue-hint") or "").strip()
            headline = (page.text_content("#qlippy-headline") or "").strip()
            if headline != "A decision needs you":
                failures.append(f"the sticky card was displaced by the race: {headline!r}")
            if "+1" not in hint:
                failures.append(f"queue hint missing under the race: {hint!r}")
            else:
                print("PASS  the queue held a race: the sticky decision card stayed, '+1' queued")
            shot(page, "story07-queue-race.png")

            # 3. Approve on the card == the dashboard approval (audit parity).
            page.click(".q-btn-primary")
            page.wait_for_timeout(900)
            httpx.post(
                f"{url}/api/meetings/m-dash/aftercare/file-issue",
                json={"action_item_id": "a1-m-dash", "repo": "acme/widgets"},
                timeout=10,
            )
            # The dashboard's identical request, via HTTP like dashboard-app.js.
            dash_props = httpx.get(f"{url}/api/meetings/m-dash/proposals", timeout=10).json()["proposals"]
            p_dash = dash_props[0]["id"]
            httpx.post(
                f"{url}/api/meetings/m-dash/proposals/{p_dash}/decision",
                json={"decision": "approved"},
                timeout=10,
            )
            a = db.actuators.get_proposal(p_card)
            b = db.actuators.get_proposal(p_dash)
            if (a.status, a.decided_by) == (b.status, b.decided_by) == ("approved", "web-user"):
                print(
                    f"PASS  audit parity: card approval ({a.status}, {a.decided_by!r}) == "
                    f"dashboard approval ({b.status}, {b.decided_by!r}); no side effect on either"
                )
            else:
                failures.append(
                    f"audit mismatch: card=({a.status},{a.decided_by!r}) dashboard=({b.status},{b.decided_by!r})"
                )

            # 4. The queued learned card presents next.
            for _ in range(20):
                if (page.text_content("#qlippy-headline") or "").strip() == "Learned from you":
                    break
                # the m-dash proposal card may be queued ahead; dismiss it
                if page.eval_on_selector("#qlippy-card", "el => el.classList.contains('is-in')"):
                    page.click("#qlippy-dismiss")
                page.wait_for_timeout(500)
            headline = (page.text_content("#qlippy-headline") or "").strip()
            if headline == "Learned from you":
                detail = (page.text_content("#qlippy-detail") or "").strip()
                if f"matches {corrected.get('similar')} past" not in detail:
                    failures.append(f"learned card reach mismatch: {detail!r}")
                else:
                    print(f"PASS  the queued learned card presented (matches {corrected.get('similar')})")
                shot(page, "story07-learned-card.png")
                page.click("#qlippy-dismiss")
                page.wait_for_timeout(600)
            else:
                failures.append(f"learned card never presented: {headline!r}")

            # Drain whatever is still queued (the m-dash proposal card) so the
            # aftercare card presents cleanly.
            for _ in range(6):
                if not page.eval_on_selector("#qlippy-card", "el => el.classList.contains('is-in')"):
                    break
                page.click("#qlippy-dismiss")
                page.wait_for_timeout(700)

            # 5. The aftercare card from a real meeting wrap.
            started = datetime(2026, 6, 10, 12, 0, 0)
            session = MeetingSession(transcriber=MagicMock(), on_broadcast=server.broadcast)
            session._state = MeetingState(
                id="m-wrap-07",
                started_at=started,
                ended_at=datetime(2026, 6, 10, 13, 0, 0),
                title="Closeout sync",
                segments=[TranscriptSegment(text="split the follow-ups", speaker="Me", start_time=0.0, end_time=5.0)],
                intel=IntelSnapshot(
                    timestamp=60.0,
                    action_items=[
                        {"id": "a1", "task": "Ship the fix", "owner": "Me", "due": None,
                         "status": "pending", "review_state": "pending", "source_timestamp": None,
                         "created_at": started.isoformat()},
                    ],
                ),
            )
            session.save(directory=tmp / "meetings")
            page.wait_for_selector("#qlippy-card.is-in", timeout=5000)
            headline = (page.text_content("#qlippy-headline") or "").strip()
            if "open item" in headline:
                print(f"PASS  the aftercare card presented from a real wrap ({headline!r})")
            else:
                failures.append(f"unexpected aftercare headline: {headline!r}")
            shot(page, "story07-aftercare-card.png")

            # 6. The off-proof.
            httpx.put(f"{url}/api/settings", json={"presence": {"enabled": True, "mascot": False}}, timeout=10)
            html_mascot_off = httpx.get(f"{url}/presence", timeout=10).text
            if html_mascot_on == html_mascot_off:
                print("PASS  the served /presence page is byte-identical with the mascot on vs. off")
            else:
                failures.append("/presence HTML differs across the mascot flag")

            off_page = browser.new_page()
            off_page.on("pageerror", lambda err: page_errors.append(str(err)))
            off_page.goto(f"{url}/presence", wait_until="networkidle")
            off_page.wait_for_timeout(600)
            _seed_meeting(db, "m-off")
            httpx.post(
                f"{url}/api/meetings/m-off/aftercare/file-issue",
                json={"action_item_id": "a1-m-off", "repo": "acme/widgets"},
                timeout=10,
            )
            server.broadcast("runtime_activity", {"state": "listening", "label": "x", "detail": ""})
            off_page.wait_for_timeout(1500)
            hidden = off_page.get_attribute("#qlippy", "hidden")
            card_in = off_page.eval_on_selector("#qlippy-card", "el => el.classList.contains('is-in')")
            if hidden is not None and not card_in:
                print("PASS  mascot off: Qlippy stayed hidden through a proposal AND activity")
            else:
                failures.append(f"mascot-off leak: hidden={hidden!r} card_in={card_in}")

            httpx.put(f"{url}/api/settings", json={"presence": {"enabled": False, "mascot": True}}, timeout=10)
            off2 = browser.new_page()
            off2.on("pageerror", lambda err: page_errors.append(str(err)))
            off2.goto(f"{url}/presence", wait_until="networkidle")
            off2.wait_for_timeout(800)
            if off2.get_attribute("#qlippy", "hidden") is not None:
                print("PASS  presence off entirely: Qlippy never appears (the double gate)")
            else:
                failures.append("presence-off leak: the mascot booted without presence")

            browser.close()
    finally:
        server.stop()
        reset_database()

    if page_errors:
        for err in page_errors:
            failures.append(f"pageerror: {err}")
    if failures:
        for f in failures:
            print(f"FAIL  {f}")
        print("RESULT: FAIL")
        return 1
    print("PASS  zero page errors across the whole run")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
