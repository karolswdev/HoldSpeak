#!/usr/bin/env python3
"""HS-57-03 dogfood: a real browser uploads a real VTT on a live server.

No mocks in the chain: Playwright opens the extended "Import a recording or
transcript" panel on /history, drops a realistic multi-speaker VTT through
the real file input, clicks Import, and the meeting card resolves in place —
with the file's own speaker names and real cue timestamps verified through
the real detail API. No transcriber exists in this process (the factory is
poisoned), proving the no-model path live.

Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python pm/roadmap/holdspeak/phase-57-transcript-import/dogfood_story03.py
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

OUT_DIR = Path(__file__).resolve().parent / "screenshots"

VTT = (
    "WEBVTT\n"
    "\n"
    "00:00:01.000 --> 00:00:05.000\n"
    "<v Priya Sharma>Morning everyone. Two items today: the rollout and hiring.</v>\n"
    "\n"
    "00:00:05.500 --> 00:00:11.000\n"
    "<v Sam Kowalski>Rollout first — the fix is merged, tests are green, I'd ship Friday.\n"
    "\n"
    "00:00:11.500 --> 00:00:15.000\n"
    "And I'll write the changelog tonight.\n"
    "\n"
    "00:00:15.500 --> 00:00:19.000\n"
    "<v Priya Sharma>Agreed, Friday it is. Sam owns the changelog.\n"
)


def main() -> int:
    import httpx
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.db import get_database, reset_database
    from holdspeak.web.routes import meeting_import as import_route
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    # Poison the transcriber factory: if the transcript path ever builds a
    # model, the import fails loudly and so does this dogfood.
    def _boom(_cfg):
        raise AssertionError("transcript import built a transcriber")

    import_route._transcriber_factory = _boom

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    db = get_database(tmp / "dogfood.db")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    vtt_path = tmp / "weekly product sync.vtt"
    vtt_path.write_text(VTT)

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
            page.set_viewport_size({"width": 1180, "height": 860})
            page.on("pageerror", lambda err: page_errors.append(str(err)))
            page.goto(f"{url}/history", wait_until="networkidle")

            opener = page.text_content(".import-open-btn") or ""
            if "transcript" not in opener:
                failures.append(f"opener copy missing transcripts: {opener!r}")
            page.click(".import-open-btn")
            page.wait_for_selector(".import-panel", timeout=5000)
            notes = page.text_content(".import-notes") or ""
            for needle in ("Transcripts:", "Speaker names are read from the file", "real for vtt / srt"):
                if needle not in notes:
                    failures.append(f"honest note missing: {needle!r}")
            page.wait_for_timeout(400)
            page.screenshot(path=str(OUT_DIR / "story03-panel.png"))
            print("PASS  the panel reads 'recording or transcript' with the per-kind honest notes")

            page.set_input_files(".import-file-input", str(vtt_path))
            page.fill(".import-fields .field:nth-child(3) .input", "imported, dogfood")
            page.click(".import-panel .btn.primary")

            # The transcript path resolves near-instantly; watch the card land,
            # catch the honest lifecycle pill, then wait for it to clear.
            page.wait_for_selector(".meeting-card-wrap", timeout=10000)
            page.screenshot(path=str(OUT_DIR / "story03-importing.png"))
            page.wait_for_selector(".status-pill.importing", state="detached", timeout=15000)
            page.wait_for_timeout(400)
            page.screenshot(path=str(OUT_DIR / "story03-resolved.png"))

            meetings = httpx.get(f"{url}/api/meetings", timeout=10).json()["meetings"]
            if len(meetings) != 1:
                failures.append(f"expected one meeting, got {len(meetings)}")
            detail = httpx.get(f"{url}/api/meetings/{meetings[0]['id']}", timeout=10).json()
            speakers = [s["speaker"] for s in detail["segments"]]
            starts = [s["start_time"] for s in detail["segments"]]
            if speakers != ["Priya Sharma", "Sam Kowalski", "Sam Kowalski", "Priya Sharma"]:
                failures.append(f"file speakers did not land: {speakers}")
            if starts != [1.0, 5.5, 11.5, 15.5]:
                failures.append(f"real cue timestamps did not land: {starts}")
            if detail["title"] != "weekly product sync":
                failures.append(f"title fell back wrong: {detail['title']!r}")
            state = (detail.get("intel_status") or {}).get("state")
            if state not in ("queued", "disabled"):
                failures.append(f"unexpected intel posture: {state!r}")
            if not failures:
                print(
                    "PASS  the browser-uploaded VTT became a real meeting: "
                    f"speakers {speakers[:2]}…, real cue starts {starts}, intel {state!r}, "
                    "no transcriber ever built"
                )
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
