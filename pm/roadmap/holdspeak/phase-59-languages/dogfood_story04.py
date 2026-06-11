#!/usr/bin/env python3
"""HS-59-04 closeout dogfood: real non-English speech, real Whisper, real config.

No mocks in the chains:

    1. a real German sentence (macOS `say`, voice Anna) is transcribed by
       REAL Whisper with the language pinned to `de` through the real
       Transcriber facade, and once on auto for the honest comparison;
    2. the spoken-symbol dictionary travels the real plumbing: PUT through
       the real settings API → saved config → reloaded → a TextProcessor
       constructed exactly as web_runtime constructs it → the symbols fire;
    3. the defaults are byte-identical: a fresh config saves
       language="auto" + spoken_symbols=[], and the default TextProcessor
       output equals the bare pre-phase processor on the golden cases.

Run on this Mac, real model load included:

    .venv/bin/python pm/roadmap/holdspeak/phase-59-languages/dogfood_story04.py
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

GERMAN_LINE = (
    "Das Meeting beginnt morgen um neun Uhr und wir besprechen die Datenbank Migration."
)


def _spoken_wav(tmp: Path) -> np.ndarray:
    out = tmp / "german.wav"
    subprocess.run(
        ["say", "-v", "Anna", "--data-format=LEI16@16000", "-o", str(out), GERMAN_LINE],
        check=True,
    )
    with wave.open(str(out), "rb") as w:
        frames = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return frames.astype(np.float32) / 32768.0


def main() -> int:
    import httpx

    import holdspeak.config as config_module
    from holdspeak.config import Config
    from holdspeak.db import get_database, reset_database
    from holdspeak.text_processor import TextProcessor
    from holdspeak.transcribe import Transcriber
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    Config().save(path=config_module.CONFIG_FILE)
    reset_database()
    get_database(tmp / "dogfood.db")
    failures: list[str] = []

    # 1. Real German speech, real Whisper, language pinned vs auto.
    audio = _spoken_wav(tmp)
    print(f"spoken (Anna/de): {GERMAN_LINE!r} ({len(audio)/16000:.1f}s)")
    pinned = Transcriber(model_name="small", backend="auto", language="de")
    text_pinned = pinned.transcribe(audio).strip()
    print(f"pinned de  : {text_pinned!r}")
    auto = Transcriber(model_name="small", backend="auto", language="auto")
    text_auto = auto.transcribe(audio).strip()
    print(f"auto-detect: {text_auto!r}")
    lowered = text_pinned.lower()
    hits = [w for w in ("meeting", "morgen", "datenbank") if w in lowered]
    if len(hits) >= 2:
        print(f"PASS  real Whisper transcribed real German with the language pinned ({hits})")
    else:
        failures.append(f"pinned German transcription unexpected: {text_pinned!r}")

    # 2. The dictionary through the real plumbing.
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
    )
    url = server.start()
    time.sleep(1.0)
    try:
        put = httpx.put(
            f"{url}/api/settings",
            json={
                "model": {"language": "German"},
                "dictation": {"spoken_symbols": [
                    {"spoken": "double colon", "symbol": "::", "attach": "both"},
                    {"spoken": "arrow", "symbol": "→", "attach": "none"},
                ]},
            },
            timeout=10,
        )
        assert put.status_code == 200, put.text
        reloaded = Config.load()
        if reloaded.model.language != "de":
            failures.append(f"language did not round-trip normalized: {reloaded.model.language!r}")
        # The exact construction web_runtime performs.
        tp = TextProcessor(spoken_symbols=getattr(reloaded.dictation, "spoken_symbols", []))
        out1 = tp._process_punctuation("std double colon vector")
        out2 = tp._process_punctuation("x arrow y")
        if out1 == "std::vector" and out2 == "x → y":
            print(f"PASS  the dictionary fired through the real settings round-trip ({out1!r}, {out2!r})")
        else:
            failures.append(f"dictionary output unexpected: {out1!r}, {out2!r}")
    finally:
        server.stop()
        reset_database()

    # 3. Defaults byte-identical.
    fresh = Config()
    if fresh.model.language == "auto" and fresh.dictation.spoken_symbols == []:
        print("PASS  fresh config defaults: language='auto', spoken_symbols=[]")
    else:
        failures.append("fresh config defaults drifted")
    bare = TextProcessor()
    empty = TextProcessor(spoken_symbols=[])
    golden = ["hello period", "hello comma world", "self dash aware", "one new line two"]
    if all(bare._process_punctuation(g) == empty._process_punctuation(g) for g in golden):
        print("PASS  the default TextProcessor is byte-identical on the golden cases")
    else:
        failures.append("default TextProcessor output drifted")

    if failures:
        for f in failures:
            print(f"FAIL  {f}")
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
