#!/usr/bin/env python3
"""HS-54-02 dogfood: drive every cockpit tab on a live runtime and prove the
carved behavior modules act exactly like the monolith did.

Boots one real `MeetingWebServer` over a temp DB (no mic, no LLM) and walks
`/dictation` with Playwright:

    1. every page error (uncaught exception) anywhere in the run is fatal —
       a missed export or broken import surfaces here instantly;
    2. all nine tabs activate and their loaders populate real content
       (readiness cards, block list, KB meta, .hs file list, hook cards,
       runtime form, memory digest, journal, dry-run);
    3. the write paths work end to end: a dry-run produces a final text +
       trace + the moment-of-truth ritual; "Right" acknowledges; the run is
       journaled; a correction added in Memory appears and deletes;
       runtime Save round-trips.

Screenshots land in ./screenshots/. Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python pm/roadmap/holdspeak/phase-54-dictation-frontend-decomposition/dogfood_story02.py
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

OUT_DIR = Path(__file__).resolve().parent / "screenshots"

SECTIONS = [
    ("readiness", "#ready-cards .readiness-card"),
    ("blocks", "#template-list .template-card, #block-list"),
    ("kb", "#kb-meta-banner"),
    ("hs", "#hs-file-list .block-card"),
    ("hooks", "#hooks-agent-list .hook-card"),
    ("runtime", "#rt-counters"),
    ("memory", "#learn-digest .learn-empty, #learn-digest .learn-sentence"),
    ("journal", "#journal-list .journal-empty, #journal-list .journal-card"),
    ("dry-run", "#dry-utterance"),
]


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
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 1400})
            page.on("pageerror", lambda err: page_errors.append(str(err)))

            page.goto(f"{url}/dictation", wait_until="networkidle")

            # 1+2. Every tab activates and its loader populates content.
            for name, selector in SECTIONS:
                page.click(f'.scope-row button[data-section="{name}"]')
                try:
                    page.wait_for_selector(selector, state="attached", timeout=5000)
                    page.wait_for_timeout(250)
                    visible = page.is_visible(f"#view-{name}")
                    if not visible:
                        failures.append(f"tab {name}: view not visible after activation")
                    else:
                        print(f"PASS  tab {name}: activated + populated")
                except Exception as exc:
                    failures.append(f"tab {name}: {exc}")
            page.screenshot(path=str(OUT_DIR / "story02-readiness.png"))

            # 3a. Enable the pipeline through the UI (a fresh temp config has it
            # off, and a disabled pipeline's dry-run takes the simple path that
            # neither executes stages nor journals — so no moment-of-truth).
            # This is also the real runtime-save round-trip.
            page.click('.scope-row button[data-section="runtime"]')
            page.wait_for_selector("#rt-counters", timeout=5000)
            page.check("#rt-enabled")
            page.click("#rt-btn-save")
            page.wait_for_selector("#rt-msg .ok-box", timeout=5000)
            print("PASS  runtime: pipeline enabled via UI, save round-trips")

            # 3b. Dry-run end to end: final text + stage trace + moment-of-truth.
            page.click('.scope-row button[data-section="dry-run"]')
            page.fill("#dry-utterance", "fix the flaky login test and add a regression case")
            page.click("#dry-btn-run")
            page.wait_for_selector("#dry-final .cmd-pre", timeout=8000)
            page.wait_for_selector("#dry-trace .trace-stage", timeout=5000)
            page.wait_for_selector("#dry-moment .fixit", timeout=5000)
            print("PASS  dry-run: final text + stage trace + moment-of-truth rendered")
            page.screenshot(path=str(OUT_DIR / "story02-dryrun.png"))

            # 3c. The ritual acknowledges "Right".
            page.click("#dry-moment [data-fixit-yes]")
            page.wait_for_selector("#dry-moment .fixit-done:not([hidden])", timeout=3000)
            print("PASS  ritual: 'Right' acknowledged")

            # 3d. The run was journaled.
            page.click('.scope-row button[data-section="journal"]')
            page.wait_for_selector("#journal-list .journal-card", timeout=5000)
            print("PASS  journal: the dry-run is journaled")
            page.screenshot(path=str(OUT_DIR / "story02-journal.png"))

            # 3e. Memory: add a correction, see it listed, delete it.
            page.click('.scope-row button[data-section="memory"]')
            page.select_option("#mem-add-kind", "intent")
            page.fill("#mem-add-text", "deploy the staging branch")
            page.fill("#mem-add-value", "deploy-notes")
            page.click("#mem-add-form button[type=submit]")
            page.wait_for_selector("#mem-list .mem-item", timeout=5000)
            print("PASS  memory: correction added + listed")
            page.click("#mem-list .mem-del")
            page.wait_for_selector("#mem-list .mem-empty", timeout=5000)
            print("PASS  memory: correction deleted")

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
