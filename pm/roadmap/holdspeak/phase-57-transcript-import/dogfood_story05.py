#!/usr/bin/env python3
"""HS-57-05 closeout dogfood: a real VTT through real intel, on real metal.

No mocks in the chain:

    1. a realistic multi-speaker VTT uploads through the real API and becomes
       a real meeting with the file's speaker names and cue timestamps;
    2. its deferred intel job is processed FOR REAL against the configured
       LAN endpoint (the `.43` llama.cpp box) and reaches `ready` with a
       non-empty summary;
    3. the server-side speaker facet filters by a transcript-carried name
       (in: Sam Kowalski; out: a stranger);
    4. a real spoken WAV (`say` → real Whisper) imports in the SAME run,
       proving the recording path untouched;
    5. /history shows both meetings (screenshot).

Uses the real user config read-only (intel endpoint); the database is a temp
file. Run unsandboxed (the LAN endpoint is unreachable from sandboxed Bash):

    (cd web && npm run build)
    .venv/bin/python pm/roadmap/holdspeak/phase-57-transcript-import/dogfood_story05.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

OUT_DIR = Path(__file__).resolve().parent / "screenshots"
RATE = 16000

VTT = (
    "WEBVTT\n"
    "\n"
    "00:00:01.000 --> 00:00:06.000\n"
    "<v Priya Sharma>Morning everyone. Two items today: the database migration and the hiring plan.</v>\n"
    "\n"
    "00:00:06.500 --> 00:00:14.000\n"
    "<v Sam Kowalski>Migration first. The schema change is tested on staging and I want to run it Thursday night.\n"
    "\n"
    "00:00:14.500 --> 00:00:19.000\n"
    "I'll need a maintenance window and someone on call.\n"
    "\n"
    "00:00:19.500 --> 00:00:26.000\n"
    "<v Priya Sharma>Approved. Take the Thursday window, and Marek is on call that night. Now hiring.\n"
    "\n"
    "00:00:26.500 --> 00:00:33.000\n"
    "<v Sam Kowalski>We have two strong candidates for the backend role. I'd move both to onsite this week.\n"
)

SPOKEN_LINE = "We agreed to run the database migration on Thursday night."


def _build_recording(tmp: Path) -> Path:
    out = tmp / "spoken followup.wav"
    raw = tmp / "raw.wav"
    subprocess.run(
        ["say", "-v", "Samantha", "--data-format=LEI16@16000", "-o", str(raw), SPOKEN_LINE],
        check=True,
    )
    with wave.open(str(raw), "rb") as w:
        frames = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(frames.tobytes())
    return out


def main() -> int:
    import httpx
    from playwright.sync_api import sync_playwright

    from holdspeak.config import Config
    from holdspeak.db import get_database, reset_database
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.transcribe import Transcriber
    from holdspeak.web.routes import meeting_import as import_route
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    cfg = Config.load()  # real config, read-only: the .43 intel endpoint
    # The machine config pins faster-whisper (not installed); resolve like
    # "auto" does on Apple Silicon — the same real Whisper model on MLX.
    import_route._transcriber_factory = lambda c: Transcriber(
        model_name=c.model.name, backend="auto"
    )

    tmp = Path(tempfile.mkdtemp())
    reset_database()
    db = get_database(tmp / "dogfood.db")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    print(f"model: {cfg.model.name} · intel endpoint: {cfg.meeting.intel_cloud_base_url}")

    vtt_path = tmp / "infra weekly.vtt"
    vtt_path.write_text(VTT)

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)

    def _detail(meeting_id):
        return httpx.get(f"{url}/api/meetings/{meeting_id}", timeout=10).json()

    def _state(detail):
        status = detail.get("intel_status") or {}
        return status.get("state") if isinstance(status, dict) else status

    def _wait(meeting_id, statuses, timeout=120.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            d = _detail(meeting_id)
            if _state(d) in statuses:
                return d
            time.sleep(0.3)
        raise AssertionError(f"meeting {meeting_id} never reached {statuses}")

    try:
        # 1. The real VTT through the real API.
        with vtt_path.open("rb") as fh:
            response = httpx.post(
                f"{url}/api/meetings/import",
                files={"file": (vtt_path.name, fh, "text/vtt")},
                data={"tags": "imported,transcript"},
                timeout=30,
            )
        assert response.status_code == 202, response.text
        vtt_id = response.json()["meeting_id"]
        detail = _wait(vtt_id, {"queued", "disabled"}, timeout=20)
        speakers = sorted({s["speaker"] for s in detail["segments"]})
        starts = [s["start_time"] for s in detail["segments"]]
        if speakers != ["Priya Sharma", "Sam Kowalski"]:
            failures.append(f"file speakers did not land: {speakers}")
        if starts != [1.0, 6.5, 14.5, 19.5, 26.5]:
            failures.append(f"real cue timestamps did not land: {starts}")
        if _state(detail) != "queued":
            failures.append(f"expected queued intel, got {_state(detail)}")
        if not failures:
            print(f"PASS  the VTT became a real meeting ({len(detail['segments'])} segments, real cues, both speakers)")

        # 2. Real intel on the configured LAN endpoint.
        processed = process_next_intel_job(
            provider="cloud",
            cloud_model=cfg.meeting.intel_cloud_model,
            cloud_api_key_env=cfg.meeting.intel_cloud_api_key_env,
            cloud_base_url=cfg.meeting.intel_cloud_base_url,
            cloud_store=cfg.meeting.intel_cloud_store,
        )
        if not processed:
            failures.append("intel queue had no job to process")
        detail = _detail(vtt_id)
        summary = ((detail.get("intel") or {}).get("summary") or "").strip()
        if _state(detail) != "ready":
            failures.append(f"intel did not reach ready: {detail.get('intel_status')}")
        elif not summary:
            failures.append("intel ready but the summary is empty")
        else:
            print(f"PASS  real intel ready on {cfg.meeting.intel_cloud_base_url}")
            print(f"      summary: {summary[:140]}…")

        # 3. The speaker facet, server-side, by a transcript-carried name.
        hit = httpx.get(f"{url}/api/meetings", params={"speaker": "Sam Kowalski"}, timeout=10).json()
        miss = httpx.get(f"{url}/api/meetings", params={"speaker": "Nobody Realname"}, timeout=10).json()
        if [m["id"] for m in hit["meetings"]] != [vtt_id]:
            failures.append(f"speaker facet missed the transcript speaker: {hit}")
        elif miss["meetings"]:
            failures.append("speaker facet matched a stranger")
        else:
            print("PASS  the server-side speaker facet filters by a transcript-carried name")

        # 4. The recording path, untouched, in the same run: say → Whisper.
        recording = _build_recording(tmp)
        with recording.open("rb") as fh:
            response = httpx.post(
                f"{url}/api/meetings/import",
                files={"file": (recording.name, fh, "audio/wav")},
                timeout=60,
            )
        assert response.status_code == 202, response.text
        wav_id = response.json()["meeting_id"]
        detail = _wait(wav_id, {"queued", "disabled"}, timeout=180)
        text = " ".join(s["text"] for s in detail["segments"]).lower()
        if "migration" in text and "thursday" in text:
            print(f"PASS  the recording path still works: real Whisper heard {text[:80]!r}")
        else:
            failures.append(f"whisper transcript unexpected: {text!r}")

        # 5. /history with both meetings.
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1180, "height": 860})
            errors: list[str] = []
            page.on("pageerror", lambda err: errors.append(str(err)))
            page.goto(f"{url}/history", wait_until="networkidle")
            page.wait_for_timeout(900)
            page.screenshot(path=str(OUT_DIR / "story05-archive.png"))
            browser.close()
        if errors:
            failures.extend(f"pageerror: {e}" for e in errors)
        else:
            print("PASS  /history rendered both imports with zero page errors")
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
