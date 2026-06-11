#!/usr/bin/env python3
"""HS-56-04 dogfood: the learning + aftercare cards, end to end on a live server.

No mocks in the chain: the presence page connects to the real `/ws`; a real
correction POSTed to the real journal-correct route fires the real
`learning_event` broadcast (taught AND reach > 0) and the "Learned from you"
card slides out with the honest match count; then a real `MeetingSession`
wrapping a finished meeting with open work emits the real `aftercare_ready`
broadcast through the same server socket and the present-note card appears
with the open count and top items. A quiet path is proven too: a secret-shaped
transcript teaches nothing and presents nothing.

Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python pm/roadmap/holdspeak/phase-56-qlippy/dogfood_story04.py
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

    # Two similar real journal rows: the taught gist will reach both.
    entry = db.dictation_journal.record(
        source="dictation",
        transcript="follow up with sam about the launch",
        final_text="follow up with sam about the launch",
    )
    db.dictation_journal.record(
        source="dictation",
        transcript="follow up with sam about launch timing",
        final_text="follow up with sam about launch timing",
    )
    secret_entry = db.dictation_journal.record(
        source="dictation",
        transcript="set the api_key to sk-abcdefghijklmnop1234",
        final_text="x",
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
    try:
        httpx.put(f"{url}/api/settings", json={"presence": {"enabled": True, "mascot": True}}, timeout=10)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 520, "height": 460})
            page.on("pageerror", lambda err: page_errors.append(str(err)))
            page.goto(f"{url}/presence", wait_until="networkidle")
            page.wait_for_selector("#qlippy:not([hidden])", timeout=5000)
            page.wait_for_timeout(400)  # let the websocket attach

            # 1. A REAL correction → the real learning_event broadcast → the
            #    "Learned from you" card with the honest reach.
            corrected = httpx.post(
                f"{url}/api/dictation/journal/{entry.id}/correct",
                json={"kind": "intent", "value": "action_item"},
                timeout=10,
            ).json()
            if not (corrected.get("taught") and corrected.get("similar", 0) > 0):
                failures.append(f"the teach did not land: {corrected}")
            page.wait_for_selector("#qlippy-card.is-in", timeout=5000)
            headline = (page.text_content("#qlippy-headline") or "").strip()
            detail = (page.text_content("#qlippy-detail") or "").strip()
            privacy = (page.text_content("#qlippy-privacy") or "").strip()
            if headline != "Learned from you":
                failures.append(f"unexpected headline: {headline!r}")
            if f"matches {corrected.get('similar')} past" not in detail:
                failures.append(f"the card's reach is not the route's reach: {detail!r}")
            if "Local only" not in privacy:
                failures.append(f"local-only privacy line missing: {privacy!r}")
            page.wait_for_timeout(600)
            page.screenshot(path=str(OUT_DIR / "story04-learned-card.png"))
            print(
                f"PASS  the real correction's real broadcast presented the learned card "
                f"(matches {corrected.get('similar')}, same number the route returned)"
            )
            page.click("#qlippy-dismiss")
            page.wait_for_timeout(600)

            # 2. The quiet path: a secret-shaped transcript teaches nothing —
            #    no card may appear.
            quiet = httpx.post(
                f"{url}/api/dictation/journal/{secret_entry.id}/correct",
                json={"kind": "intent", "value": "action_item"},
                timeout=10,
            ).json()
            page.wait_for_timeout(1200)
            card_in = page.eval_on_selector("#qlippy-card", "el => el.classList.contains('is-in')")
            if quiet.get("taught") is not False:
                failures.append(f"the secret-shaped teach was not refused: {quiet}")
            if card_in:
                failures.append("a card appeared for a teach that did not happen")
            else:
                print("PASS  a refused teach stayed silent — no learned card for no learning")

            # 3. A REAL meeting wrap: MeetingSession.save() with the server's
            #    own broadcast emits the real aftercare_ready → present-note card.
            started = datetime(2026, 6, 10, 10, 0, 0)
            session = MeetingSession(transcriber=MagicMock(), on_broadcast=server.broadcast)
            session._state = MeetingState(
                id="m-wrap-dogfood",
                started_at=started,
                ended_at=datetime(2026, 6, 10, 11, 0, 0),
                title="Roadmap sync",
                segments=[TranscriptSegment(text="let's split the follow-ups", speaker="Me", start_time=0.0, end_time=5.0)],
                intel=IntelSnapshot(
                    timestamp=60.0,
                    action_items=[
                        {"id": "a1", "task": "Fix the login bug", "owner": "Me", "due": None,
                         "status": "pending", "review_state": "pending", "source_timestamp": None,
                         "created_at": started.isoformat()},
                        {"id": "a2", "task": "Draft the rollout note", "owner": "Sam", "due": None,
                         "status": "pending", "review_state": "pending", "source_timestamp": None,
                         "created_at": started.isoformat()},
                    ],
                ),
            )
            session.save(directory=tmp / "meetings")
            page.wait_for_selector("#qlippy-card.is-in", timeout=5000)
            headline = (page.text_content("#qlippy-headline") or "").strip()
            detail = (page.text_content("#qlippy-detail") or "").strip()
            if headline != "Your meeting left 2 open items":
                failures.append(f"unexpected aftercare headline: {headline!r}")
            if "Roadmap sync" not in detail or "Fix the login bug" not in detail:
                failures.append(f"aftercare detail missing title/top items: {detail!r}")
            page.wait_for_timeout(600)
            page.screenshot(path=str(OUT_DIR / "story04-aftercare-card.png"))
            print("PASS  the real meeting wrap's real broadcast presented the aftercare card (2 open, top items named)")

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
