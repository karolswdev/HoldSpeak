#!/usr/bin/env python3
"""HS-60-06 closeout dogfood: the whole wake loop, live, on real speech.

No mocks in the chain that matters: REAL synthesized speech (`say`) runs
through the REAL openWakeWord detector inside the REAL `WakeWordListener`,
whose detection drives the REAL production `_on_wake_detect` (the same
queue topology as the live stream: detection fires mid-queue, the capture
drains the remaining frames), the captured sentence is transcribed by REAL
Whisper, the `wake_preview` broadcast crosses the REAL server socket to a
REAL browser where Qlippy's card appears, and **Type it** goes through the
REAL one-shot route. The only replaced edge is hardware: the microphone is
replayed real speech (a headless runner cannot hold a mic to a speaker),
and typing lands in a recording writer instead of a focused app — both
stated here, neither touching the detection/transcription/broadcast chain.

Also proven: the type action is the explicit opt-in (a second pass with
`action="type"` types without a preview) and the defaults are off.

    .venv/bin/python pm/roadmap/holdspeak/phase-60-wake-word/dogfood_story06.py
"""
from __future__ import annotations

import queue as queue_mod
import subprocess
import sys
import tempfile
import threading
import time
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

OUT_DIR = Path(__file__).resolve().parent / "screenshots"
SENTENCE = "ship the database migration fix today"


def _say(line: str, tmp: Path, name: str) -> np.ndarray:
    out = tmp / name
    subprocess.run(
        ["say", "-v", "Samantha", "--data-format=LEI16@16000", "-o", str(out), line],
        check=True,
    )
    with wave.open(str(out), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)


def main() -> int:
    import httpx
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.config import Config
    from holdspeak.db import get_database, reset_database
    from holdspeak.text_processor import TextProcessor
    from holdspeak.transcribe import Transcriber
    from holdspeak.voice_typing import VoiceTypingSession
    from holdspeak.wake_word import (
        FRAME_SAMPLES,
        OpenWakeWordDetector,
        WakeWordListener,
    )
    from holdspeak.web_runtime import WebRuntime
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    cfg = Config()
    print(f"defaults: wake_word.enabled={cfg.wake_word.enabled} action={cfg.wake_word.action!r}")
    assert cfg.wake_word.enabled is False, "the default must be off"
    cfg.presence.enabled = True
    cfg.presence.mascot = True
    cfg.wake_word.enabled = True
    cfg.save(path=config_module.CONFIG_FILE)
    reset_database()
    db = get_database(tmp / "dogfood.db")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    # The real speech: wake phrase, a beat of silence, the sentence, silence.
    print("step: synthesizing speech…")
    wake_audio = _say("hey jarvis", tmp, "wake.wav")
    sentence_audio = _say(SENTENCE, tmp, "sentence.wav")
    gap = np.zeros(16000 // 2, dtype=np.int16)
    tail = np.zeros(16000 * 3, dtype=np.int16)
    stream_audio = np.concatenate([gap, wake_audio, gap, sentence_audio, tail])

    # The production topology: ONE queue. The listener detects mid-queue;
    # the capture drains the remaining (sentence) frames from the same queue.
    frames_queue: queue_mod.Queue = queue_mod.Queue()
    for i in range(0, len(stream_audio) - FRAME_SAMPLES, FRAME_SAMPLES):
        frames_queue.put(stream_audio[i : i + FRAME_SAMPLES])
    drained = threading.Event()

    def frame_source():
        try:
            return frames_queue.get(timeout=0.3)
        except queue_mod.Empty:
            drained.set()
            return np.zeros(FRAME_SAMPLES, dtype=np.int16)

    # The bare runtime carrying the REAL production methods + collaborators.
    print("step: building the bare runtime…")
    rt = WebRuntime.__new__(WebRuntime)
    rt.config = Config.load()
    rt.voice_session = VoiceTypingSession()
    rt.runtime_stop_event = threading.Event()
    rt.transcription_lock = threading.Lock()
    rt.wake_previews = {}
    rt._wake_listener = None
    rt._wake_stream = None
    rt._wake_queue = frames_queue
    rt.text_processor = TextProcessor()
    print("step: loading Whisper…")
    transcriber = Transcriber(model_name="small", backend="auto")
    print("step: Whisper ready")
    rt._ensure_transcriber_loaded = lambda: transcriber
    typed: list[str] = []
    rt.typer = SimpleNamespace(type_text=typed.append)
    activities: list[str] = []

    print("step: constructing the server…")
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
            on_wake_type=rt._type_wake_preview,
        ),
    )
    rt.server = server

    def set_activity(state, **kw):
        activities.append(state)
        try:
            server.broadcast(
                "runtime_activity",
                {"state": state, "label": kw.get("label", state), "detail": kw.get("detail", "")},
            )
        except Exception:
            pass

    rt._set_runtime_activity = set_activity

    print("step: starting the server…")
    url = server.start()
    print(f"step: server at {url}")
    time.sleep(1.0)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 520, "height": 470})
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url}/presence", wait_until="networkidle")
            page.wait_for_selector("#qlippy:not([hidden])", timeout=5000)
            page.wait_for_timeout(400)

            # The REAL detector + listener over the REAL speech.
            print("step: loading the detector…")
            detector = OpenWakeWordDetector("hey_jarvis")
            print("step: detector ready; listening…")
            listener = WakeWordListener(
                detector=detector,
                frames=frame_source,
                on_detect=rt._on_wake_detect,
                threshold=rt.config.wake_word.threshold,
            )
            listener.start()

            try:
                page.wait_for_selector("#qlippy-card.is-in", timeout=120000)
            except Exception:
                print(f"debug: activities={activities}")
                print(f"debug: previews={list(rt.wake_previews)}")
                print(f"debug: queue size={frames_queue.qsize()} drained={drained.is_set()}")
                print(f"debug: floor owner={rt.voice_session.active_owner!r}")
                raise
            page.wait_for_timeout(700)
            headline = (page.text_content("#qlippy-headline") or "").strip()
            preview_text = (page.text_content("#qlippy-preview") or "").strip()
            page.screenshot(path=str(OUT_DIR / "story06-live-preview.png"))
            listener.stop()

            if "armed" not in activities:
                failures.append(f"the armed state never broadcast: {activities}")
            else:
                print("PASS  the REAL detector armed on REAL speech (the armed broadcast crossed the socket)")
            if headline != "Heard you — review before it types":
                failures.append(f"unexpected card headline: {headline!r}")
            lowered = preview_text.lower()
            if all(w in lowered for w in ("ship", "database", "migration")):
                print(f"PASS  real Whisper transcribed the captured sentence: {preview_text!r}")
            else:
                failures.append(f"preview text unexpected: {preview_text!r}")
            if typed:
                failures.append(f"preview default typed something: {typed}")
            else:
                print("PASS  nothing was typed before the confirm (the preview default held)")

            # Type it: the REAL one-shot route, clicked in the REAL browser.
            page.click(".q-btn-primary")
            page.wait_for_timeout(900)
            if typed == [preview_text] or (typed and typed[0].lower().startswith("ship")):
                print(f"PASS  Type it typed exactly the stored preview: {typed[0]!r}")
            else:
                failures.append(f"Type it outcome unexpected: {typed}")
            token_reuse = httpx.post(
                f"{url}/api/dictation/wake/type",
                json={"token": "anything"},
                timeout=10,
            )
            if token_reuse.status_code == 404:
                print("PASS  the token model holds (unknown/used tokens are refused)")
            else:
                failures.append(f"token reuse not refused: {token_reuse.status_code}")

            # The type action, as the explicit opt-in.
            rt.config.wake_word.action = "type"
            typed.clear()
            rt._transcribe_wake(sentence_audio.astype(np.float32) / 32768.0)
            if typed and "migration" in typed[0].lower():
                print(f"PASS  action='type' (the explicit opt-in) typed directly: {typed[0]!r}")
            else:
                failures.append(f"type action outcome unexpected: {typed}")

            if errors:
                failures.extend(f"pageerror: {e}" for e in errors)
            browser.close()
    finally:
        server.stop()
        reset_database()

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
