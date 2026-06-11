#!/usr/bin/env python3
"""HS-55-06 closeout dogfood: a real recording, end to end, on real metal.

No fakes anywhere in the pipeline:

    1. real speech is synthesized with macOS `say` (two utterances spaced
       into separate ~30 s transcription windows);
    2. the WAV is uploaded through the real `POST /api/meetings/import`
       against a live server — the real Whisper transcriber (the user's
       configured model) transcribes it on the background thread;
    3. the meeting resolves at /history with windowed segments whose text
       contains the expected phrases, and a deferred intel job is enqueued;
    4. the intel job is processed for real against the configured
       OpenAI-compatible endpoint (the LAN llama.cpp box) and the meeting
       reaches intel_status=ready with a non-empty snapshot;
    5. the facets find it (speaker include) and exclude it (wrong speaker);
    6. a /history screenshot shows the imported meeting.

Uses the real user config read-only (for the Whisper model + intel
endpoint); the database is a temp file. Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python pm/roadmap/holdspeak/phase-55-meeting-import/dogfood_story06.py
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

UTTERANCE_ONE = "The quarterly budget needs a final review before Friday."
UTTERANCE_TWO = "We decided to ship the import feature next week."


def _say(line: str, out: Path) -> np.ndarray:
    subprocess.run(
        ["say", "-v", "Samantha", "--data-format=LEI16@16000", "-o", str(out), line],
        check=True,
    )
    with wave.open(str(out), "rb") as w:
        frames = w.readframes(w.getnframes())
    return np.frombuffer(frames, dtype=np.int16)


def _build_recording(tmp: Path) -> Path:
    a = _say(UTTERANCE_ONE, tmp / "a.wav")
    b = _say(UTTERANCE_TWO, tmp / "b.wav")
    # Pad utterance one out to a full 30 s window so utterance two lands in
    # window 2 — proving multi-window segmentation on real audio.
    pad = np.zeros(max(0, 30 * RATE - len(a)), dtype=np.int16)
    combined = np.concatenate([a, pad, b])
    out = tmp / "imported board sync.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(combined.tobytes())
    return out


def main() -> int:
    import httpx
    from playwright.sync_api import sync_playwright

    from holdspeak.config import Config
    from holdspeak.db import get_database, reset_database
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    cfg = Config.load()  # the real config, read-only (Whisper model + .43 endpoint)
    # This machine's config pins model.backend="faster-whisper", which is not
    # installed here (an honest config quirk the first dogfood run surfaced by
    # marking the row import_failed with the actionable install hint — the
    # failure path proven live). For the happy path, resolve the backend the
    # way "auto" does on Apple Silicon: the same real Whisper model on MLX.
    from holdspeak.transcribe import Transcriber

    from holdspeak.web.routes import meeting_import as import_route

    import_route._transcriber_factory = lambda c: Transcriber(
        model_name=c.model.name, backend="auto"
    )
    tmp = Path(tempfile.mkdtemp())
    reset_database()
    db = get_database(tmp / "dogfood.db")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    print(f"model: {cfg.model.name} · intel endpoint: {cfg.meeting.intel_cloud_base_url}")
    recording = _build_recording(tmp)
    print(f"recording: {recording.name} ({recording.stat().st_size // 1024} KiB)")

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)
    try:
        # 2. Real upload through the real route.
        with recording.open("rb") as fh:
            response = httpx.post(
                f"{url}/api/meetings/import",
                files={"file": (recording.name, fh, "audio/wav")},
                data={"title": "Imported board sync", "speaker": "Board call", "tags": "imported,dogfood"},
                timeout=30,
            )
        assert response.status_code == 202, response.text
        meeting_id = response.json()["meeting_id"]
        print(f"PASS  202 with meeting id {meeting_id}; transcribing with real Whisper…")

        # 3. Wait for real transcription to resolve the row.
        deadline = time.time() + 600
        detail = None
        while time.time() < deadline:
            detail = httpx.get(f"{url}/api/meetings/{meeting_id}", timeout=10).json()
            state = (detail.get("intel_status") or {}).get("state")
            if state in {"queued", "disabled", "import_failed"}:
                break
            time.sleep(2)
        state = (detail.get("intel_status") or {}).get("state")
        if state != "queued":
            failures.append(f"expected intel queued after import, got {state}: {detail.get('intel_status')}")
        segments = detail.get("segments") or []
        texts = " ".join(s["text"].lower() for s in segments)
        print(f"      {len(segments)} segment(s): {[s['text'] for s in segments]}")
        if len(segments) < 2:
            failures.append(f"expected 2 windowed segments, got {len(segments)}")
        for needle in ("budget", "import feature"):
            if needle not in texts:
                failures.append(f"expected phrase missing from real transcript: {needle!r}")
        if segments and segments[0].get("speaker") != "Board call":
            failures.append(f"speaker label lost: {segments[0].get('speaker')!r}")
        if not failures:
            print("PASS  real Whisper transcript carries both expected phrases across 2 windows")

        # 4. Real intel on the configured endpoint.
        processed = process_next_intel_job(
            provider="cloud",
            cloud_model=cfg.meeting.intel_cloud_model,
            cloud_api_key_env=cfg.meeting.intel_cloud_api_key_env,
            cloud_base_url=cfg.meeting.intel_cloud_base_url,
            cloud_store=cfg.meeting.intel_cloud_store,
        )
        if not processed:
            failures.append("intel queue had no job to process")
        detail = httpx.get(f"{url}/api/meetings/{meeting_id}", timeout=10).json()
        state = (detail.get("intel_status") or {}).get("state")
        intel = detail.get("intel") or {}
        summary = (intel.get("summary") or "").strip()
        if state != "ready":
            failures.append(f"intel did not reach ready: {detail.get('intel_status')}")
        elif not summary:
            failures.append("intel ready but the snapshot summary is empty")
        else:
            print(f"PASS  real intel ready on {cfg.meeting.intel_cloud_base_url}")
            print(f"      summary: {summary[:160]}")

        # 5. Facets include + exclude it.
        hit = httpx.get(f"{url}/api/meetings", params={"speaker": "Board call", "tag": "dogfood"}, timeout=10).json()
        miss = httpx.get(f"{url}/api/meetings", params={"speaker": "Nobody"}, timeout=10).json()
        if not any(m["id"] == meeting_id for m in hit["meetings"]):
            failures.append("speaker+tag facet did not find the imported meeting")
        elif any(m["id"] == meeting_id for m in miss["meetings"]):
            failures.append("a wrong speaker facet still returned the meeting")
        else:
            print("PASS  facets include (speaker+tag) and exclude (wrong speaker) correctly")

        # 6. Screenshot the archive with the imported, intel-ready meeting.
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 950})
            page.goto(f"{url}/history", wait_until="networkidle")
            page.wait_for_timeout(600)
            page.screenshot(path=str(OUT_DIR / "story06-imported-ready.png"))
            browser.close()
        print("PASS  /history screenshot captured")
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
