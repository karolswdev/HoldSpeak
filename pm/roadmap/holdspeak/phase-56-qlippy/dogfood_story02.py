#!/usr/bin/env python3
"""HS-56-02 dogfood: the Qlippy dock + card shell, live.

Boots a real server, flips presence.enabled + presence.mascot via the real
settings API, and drives /presence with Playwright:

    1. flag OFF: the page renders the ring-only HUD — no Qlippy node visible;
    2. flag ON: the dock appears (idle sprite) and follows dispatched
       runtime-activity events through the state map (listening → thinking →
       the complete flourish → idle);
    3. two mock cards present FIFO: the first slides in (alert styling), the
       queue hint shows "+1", dismissing reveals the second;
    4. pause-on-hover holds an auto-dismissing card past its timer;
    5. zero uncaught page errors.

Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python pm/roadmap/holdspeak/phase-56-qlippy/dogfood_story02.py
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

OUT_DIR = Path(__file__).resolve().parent / "screenshots"


def main() -> int:
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    db = get_database(tmp / "dogfood.db")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)
    failures: list[str] = []
    page_errors: list[str] = []

    def dock_state(page):
        return page.get_attribute("#qlippy-dock-sprite", "data-state")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 520, "height": 420})
            page.on("pageerror", lambda err: page_errors.append(str(err)))

            # 1. Flag off: no Qlippy.
            page.goto(f"{url}/presence", wait_until="networkidle")
            page.wait_for_timeout(400)
            if page.is_visible("#qlippy"):
                failures.append("Qlippy visible with the mascot flag off")
            else:
                print("PASS  flag off: ring-only HUD, no Qlippy node visible")

            # Enable both flags through the real settings API.
            import httpx
            httpx.put(f"{url}/api/settings", json={"presence": {"enabled": True, "mascot": True}}, timeout=10)

            # 2. Flag on: the dock appears and follows activity.
            page.goto(f"{url}/presence", wait_until="networkidle")
            page.wait_for_selector("#qlippy:not([hidden])", timeout=5000)
            if dock_state(page) != "idle":
                failures.append(f"dock did not boot idle: {dock_state(page)}")
            page.screenshot(path=str(OUT_DIR / "story02-dock-idle.png"))

            def send_activity(state):
                page.evaluate(
                    "(s) => document.dispatchEvent(new CustomEvent('hs-activity', {detail: {state: s}}))",
                    state,
                )
                page.wait_for_timeout(150)

            send_activity("listening")
            listening = dock_state(page)
            send_activity("transcribing")
            thinking = dock_state(page)
            send_activity("complete")
            flourish = dock_state(page)
            page.screenshot(path=str(OUT_DIR / "story02-dock-listening.png"))
            page.wait_for_timeout(2300)
            after_flourish = dock_state(page)
            if [listening, thinking, flourish, after_flourish] == ["listening", "thinking", "approve", "idle"]:
                print("PASS  dock follows the state map (listening → thinking → approve flourish → idle)")
            else:
                failures.append(
                    f"dock map wrong: {[listening, thinking, flourish, after_flourish]}"
                )

            # 3. Two cards FIFO + the queue hint.
            page.evaluate(
                """() => {
                  window.qlippyCard.present({sprite: 'alert', headline: 'A decision needs you',
                    detail: 'Mock proposal: create an issue on GitHub.',
                    preview: 'title: Fix the flaky login test',
                    privacy: 'Data used: the proposal preview above. This sends to GitHub only if you approve. You decide here or in the dashboard.',
                    actions: [{label: 'Approve', kind: 'primary'}, {label: 'Decline', kind: 'danger'}],
                    sticky: true});
                  window.qlippyCard.present({sprite: 'learned', glyph: 'lightbulb',
                    headline: 'Learned from you', detail: 'Mock: matches 3 past dictations.',
                    actions: [{label: 'View digest', kind: 'ghost'}]});
                }"""
            )
            page.wait_for_selector("#qlippy-card.is-in", timeout=3000)
            hint = page.text_content("#qlippy-queue-hint")
            if (hint or "").strip() != "+1":
                failures.append(f"queue hint expected +1, got {hint!r}")
            page.wait_for_timeout(600)
            page.screenshot(path=str(OUT_DIR / "story02-card-alert.png"))
            headline1 = page.text_content("#qlippy-headline")

            page.click("#qlippy-dismiss")
            page.wait_for_timeout(500)
            headline2 = page.text_content("#qlippy-headline")
            if headline1.strip() == "A decision needs you" and headline2.strip() == "Learned from you":
                print("PASS  FIFO: dismissing the alert reveals the queued learned card (+1 hint shown)")
            else:
                failures.append(f"FIFO broke: {headline1!r} -> {headline2!r}")
            page.screenshot(path=str(OUT_DIR / "story02-card-learned.png"))

            # 4. Pause-on-hover holds an auto-dismissing card.
            page.click("#qlippy-dismiss")
            page.wait_for_timeout(500)
            page.evaluate(
                """() => window.qlippyCard.present({sprite: 'present-note', headline: 'Hover hold',
                     detail: 'Short-fuse card.', autoDismissMs: 900})"""
            )
            page.wait_for_selector("#qlippy-card.is-in", timeout=3000)
            page.hover("#qlippy-card")
            page.wait_for_timeout(1600)
            still_open = page.is_visible("#qlippy-card.is-in")
            if still_open:
                print("PASS  pause-on-hover held the card past its 900 ms fuse")
            else:
                failures.append("hover did not hold the auto-dismiss")
            page.mouse.move(10, 10)
            page.wait_for_timeout(2500)
            if page.is_visible("#qlippy-card.is-in"):
                failures.append("card never auto-dismissed after the hover ended")
            else:
                print("PASS  auto-dismiss resumed after the hover ended")

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
