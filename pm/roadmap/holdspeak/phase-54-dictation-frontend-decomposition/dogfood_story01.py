#!/usr/bin/env python3
"""HS-54-01 dogfood: prove the carved discovery-nudge module behaves
identically on a live runtime, through the new ES-module seam.

Boots one real `MeetingWebServer` over a temp DB (no mic, no LLM) from the
repo cwd (no `.holdspeak/project.yaml`, no `.hs/`, so the nudge renders
naturally) and drives `/dictation` with Playwright through the module's
whole behavior surface:

    1. the nudge shows (maybeShowKnNudge -> injected api/projectRootParam);
    2. per-project dismiss hides it AND persists across a reload
       (knNudgeDismiss -> localStorage `holdspeak.knNudgeDismissed`);
    3. with storage cleared the nudge returns (the dismissal was the only
       reason it hid);
    4. the global "stop suggesting" switch hides it across a reload
       (knNudgeDisableGlobally -> localStorage `holdspeak.knNudgeDisabled`).

Screenshots land in ./screenshots/. Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python pm/roadmap/holdspeak/phase-54-dictation-frontend-decomposition/dogfood_story01.py
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
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 1200})

            # 1. The nudge shows through the carved module.
            page.goto(f"{url}/dictation", wait_until="networkidle")
            page.wait_for_selector("#kn-nudge", state="visible", timeout=5000)
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT_DIR / "story01-nudge-visible.png"))
            print("PASS  1. nudge visible via the carved module")

            # 2. Per-project dismiss hides + persists across reload.
            page.click("#kn-nudge-dismiss")
            page.wait_for_selector("#kn-nudge", state="hidden", timeout=5000)
            dismissed = page.evaluate("localStorage.getItem('holdspeak.knNudgeDismissed')")
            if not dismissed or "{" not in dismissed:
                failures.append(f"dismissal not persisted (got {dismissed!r})")
            page.reload(wait_until="networkidle")
            page.wait_for_timeout(800)
            if page.is_visible("#kn-nudge"):
                failures.append("nudge returned after per-project dismiss + reload")
            else:
                print("PASS  2. per-project dismiss persists across reload")
            page.screenshot(path=str(OUT_DIR / "story01-nudge-dismissed.png"))

            # 3. Clearing storage brings it back (dismissal was the cause).
            page.evaluate("localStorage.clear()")
            page.reload(wait_until="networkidle")
            page.wait_for_selector("#kn-nudge", state="visible", timeout=5000)
            print("PASS  3. nudge returns once dismissal is cleared")

            # 4. The global off switch persists across reload.
            page.click("#kn-nudge-off")
            page.wait_for_selector("#kn-nudge", state="hidden", timeout=5000)
            disabled = page.evaluate("localStorage.getItem('holdspeak.knNudgeDisabled')")
            if disabled != "1":
                failures.append(f"global off not persisted (got {disabled!r})")
            page.reload(wait_until="networkidle")
            page.wait_for_timeout(800)
            if page.is_visible("#kn-nudge"):
                failures.append("nudge returned after global off + reload")
            else:
                print("PASS  4. global 'stop suggesting' persists across reload")

            browser.close()
    finally:
        server.stop()
        reset_database()

    if failures:
        for f in failures:
            print(f"FAIL  {f}")
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
