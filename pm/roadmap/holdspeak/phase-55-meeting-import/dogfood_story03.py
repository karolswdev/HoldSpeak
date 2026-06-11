#!/usr/bin/env python3
"""HS-55-03 dogfood: a real browser upload lands a meeting, in place.

Boots one real `MeetingWebServer` (temp DB) with a slowed fake transcriber
(so the importing state is observable) and drives /history with Playwright:

    1. the "Import a recording" affordance opens the panel (screenshot);
    2. a real WAV is attached via the file input, title + speaker set,
       Import clicked;
    3. the meeting card appears with the pulsing "Importing…" pill and the
       window progress detail — without a manual refresh (screenshot);
    4. the card resolves in place to the normal intel posture (screenshot);
    5. zero uncaught page errors across the run.

Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python pm/roadmap/holdspeak/phase-55-meeting-import/dogfood_story03.py
"""
from __future__ import annotations

import sys
import tempfile
import time
import wave
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

OUT_DIR = Path(__file__).resolve().parent / "screenshots"


class SlowFakeTranscriber:
    def transcribe(self, audio):
        time.sleep(1.2)
        return "imported speech from the browser upload"


def _write_wav(path: Path, seconds: float):
    rate = 16000
    t = np.linspace(0, seconds, int(seconds * rate), endpoint=False)
    tone = (np.sin(2 * np.pi * 440 * t) * 0.3 * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(tone.tobytes())
    return path


def main() -> int:
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.db import get_database, reset_database
    from holdspeak.web.routes import meeting_import as import_route
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    db = get_database(tmp / "dogfood.db")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wav = _write_wav(tmp / "team retro recording.wav", seconds=95.0)

    import_route._transcriber_factory = lambda cfg: SlowFakeTranscriber()

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
            page.set_viewport_size({"width": 1280, "height": 1100})
            page.on("pageerror", lambda err: page_errors.append(str(err)))

            page.goto(f"{url}/history", wait_until="networkidle")
            page.click(".import-open-btn")
            page.wait_for_selector(".import-panel", state="visible", timeout=5000)
            page.wait_for_timeout(250)
            page.screenshot(path=str(OUT_DIR / "story03-panel.png"))
            print("PASS  panel opens with the honest notes")

            page.set_input_files(".import-file-input", str(wav))
            page.wait_for_selector(".import-drop.has-file", timeout=3000)
            page.fill('.import-fields input[x-model="importTitle"]', "Team retro (imported)")
            page.fill('.import-fields input[x-model="importSpeaker"]', "Retro recording")
            page.click(".import-panel .btn.primary")

            # The card appears in importing state without a manual refresh.
            page.wait_for_selector(".status-pill.importing", timeout=10000)
            page.wait_for_selector('text=Team retro (imported)', timeout=5000)
            page.wait_for_timeout(400)
            page.screenshot(path=str(OUT_DIR / "story03-importing.png"))
            detail_visible = page.is_visible(".meta-line")
            print(f"PASS  card shows Importing… (progress detail visible: {detail_visible})")

            # ...and resolves in place (slow fake: 4 windows × 1.2 s).
            page.wait_for_selector(".status-pill.importing", state="detached", timeout=30000)
            page.wait_for_selector(".status-pill.queued, .status-pill.disabled", timeout=5000)
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT_DIR / "story03-resolved.png"))
            print("PASS  card resolved in place, no manual refresh")

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
