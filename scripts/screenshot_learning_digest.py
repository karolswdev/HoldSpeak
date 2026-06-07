#!/usr/bin/env python3
"""HS-48-01: capture the "What HoldSpeak learned" digest, reproducibly.

Boots one real `MeetingWebServer` over a temp DB seeded with a handful of
journal rows + corrections (no mic, no LLM), opens `/dictation`, switches to the
Memory tab, and screenshots the digest hero in both window states + the empty
state. Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python scripts/screenshot_learning_digest.py
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

OUT_DIR = Path(__file__).parent.parent / "docs" / "assets" / "screenshots"

# Two near-duplicate utterances (the matcher links them) + unrelated lines.
JOURNAL = [
    "send the launch checklist to the team",
    "send the launch checklist to everyone",
    "follow up with Priya about the rollout",
    "remember to book the conference room",
]
CORRECTIONS = [
    ("intent", "send the launch checklist to the team", "action_item"),
    ("intent", "follow up with Priya about the rollout", "action_item"),
    ("target", "open the terminal", "iterm"),
]


def _seed_empty(db) -> None:
    pass


def _seed_populated(db) -> None:
    for kind, gist, value in CORRECTIONS:
        db.dictation_corrections.record_correction(kind=kind, gist=gist, value=value)
    first = None
    for transcript in JOURNAL:
        rec = db.dictation_journal.record(source="dictation", transcript=transcript, final_text=transcript)
        if first is None:
            first = rec
    if first is not None:
        db.dictation_journal.mark_corrected(first.id)


def _capture(seed, suffix: str) -> None:
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.config import Config
    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    # Corrections on, so the inline "learned from N similar" chips render on the
    # journal entries (the matcher only nudges when enabled).
    cfg = Config()
    cfg.dictation.pipeline.corrections_enabled = True
    cfg.save(path=config_module.CONFIG_FILE)
    reset_database()
    db = get_database(tmp / "shot.db")
    seed(db)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1100, "height": 1000})
            page.goto(f"{url}/dictation", wait_until="networkidle")
            page.click('#section-memory')
            page.wait_for_selector("#learn-digest", state="visible", timeout=5000)
            # Let the digest fetch + render settle.
            page.wait_for_timeout(600)
            page.screenshot(path=str(OUT_DIR / f"learning-digest-{suffix}.png"))
            print(f"Wrote {OUT_DIR / ('learning-digest-' + suffix + '.png')}")
            if suffix == "week":
                page.click("#learn-window-all")
                page.wait_for_timeout(600)
                page.screenshot(path=str(OUT_DIR / "learning-digest-all.png"))
                print(f"Wrote {OUT_DIR / 'learning-digest-all.png'}")
                # HS-48-02: the inline reach chips on the Memory list (full page),
                # then the Journal tab where each matched entry carries one.
                page.screenshot(path=str(OUT_DIR / "trust-signals-memory.png"), full_page=True)
                print(f"Wrote {OUT_DIR / 'trust-signals-memory.png'}")
                page.click('#section-journal')
                page.wait_for_selector("#journal-list", state="visible", timeout=5000)
                page.wait_for_timeout(600)
                page.screenshot(path=str(OUT_DIR / "trust-signals-journal.png"), full_page=True)
                print(f"Wrote {OUT_DIR / 'trust-signals-journal.png'}")
                # HS-48-03: the one-tap ritual mid-flow — "Fix it" opens the
                # pre-scoped correct path inline on the first entry.
                page.click(".journal-card [data-fixit-no]")
                page.wait_for_timeout(400)
                page.screenshot(path=str(OUT_DIR / "correction-ritual.png"), full_page=True)
                print(f"Wrote {OUT_DIR / 'correction-ritual.png'}")
            browser.close()
    finally:
        server.stop()
        reset_database()


def main() -> int:
    # Populated (this-week window + all-time) then the empty teaching state.
    _capture(_seed_populated, "week")
    _capture(_seed_empty, "empty")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
