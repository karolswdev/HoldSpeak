#!/usr/bin/env python3
"""Measure the Line on this machine with the real baresip (LINE design §3).

Two baresips on 127.0.0.1: the Line (``LineNode``, the product path: aupipe,
the sockets, the end-of-speech rule, the speech, the manners, the adapter) and
a caller (a plain baresip with aupipe). It measures mouth to ear both ways
(80 ms tones), end of speech → text at the Line (the fixture utterance, 3
times), and text → first sound at the caller (a reply, 3 times).

    python scripts/line/measure_line.py            # Parakeet + Pocket (the line extra)
    python scripts/line/measure_line.py --tone     # the tone speech of the tests
"""
from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from holdspeak.line.adapter import Line  # noqa: E402
from holdspeak.line.hub import LineHub  # noqa: E402
from holdspeak.line.node import LineNode, LocalLink  # noqa: E402
from holdspeak.line.supervisor import build_aupipe, find_baresip  # noqa: E402
from tests.fixtures.fake_baresip import ToneSTT, ToneTTS, tone  # noqa: E402
from tests.fixtures.line_rig import Caller, free_port, short_dir  # noqa: E402

UTTERANCE = ROOT / "tests" / "fixtures" / "line_utterance.wav"
REPLY = "Done. I added a task: nudge Tomás about the runbook by Friday."


def _stats(values: list[float]) -> dict:
    return {"median": round(statistics.median(values), 1), "min": round(min(values), 1),
            "max": round(max(values), 1), "n": len(values)} if values else {}


async def measure(*, real_speech: bool) -> dict:
    binary = find_baresip()
    if not binary:
        raise SystemExit("baresip is not installed")
    root = short_dir()
    aupipe = build_aupipe(root / "build", binary=binary)
    if real_speech:
        from holdspeak.line.speech import Parakeet, Pocket

        t0 = time.monotonic()
        stt, tts = Parakeet(), Pocket()
        load = round(time.monotonic() - t0, 1)
    else:
        stt, tts, load = ToneSTT(), ToneTTS(), 0.0
    hub = LineHub()
    hub.config_fn = lambda _n: {"account": {"kind": "sip", "user": "holdspeak", "codecs": ["PCMU", "PCMA"]},
                                "daily_limit": 20, "owner": "Karol"}
    line_port = free_port()
    node = LineNode("this-mac", LocalLink(hub, "this-mac"), stt=stt, tts=tts, binary=binary, home=root / "line",
                    sip_port=line_port, ctrl_port=free_port(), aupipe=aupipe,
                    say_sock=root / "l.say", heard_sock=root / "l.heard")
    caller = Caller(binary, aupipe, root, sip_port=free_port(), ctrl_port=free_port())
    line = Line("this-mac", hub=hub, count_path=root / "c.json")
    result: dict = {"real_speech": real_speech, "models_load_s": load}
    line_frames: list[tuple[float, np.ndarray]] = []
    await node.start()
    original = node.heard_port.on_frame

    def tap(at: float, frame: np.ndarray) -> None:
        line_frames.append((at, frame))
        original(at, frame)

    node.heard_port.on_frame = tap
    await caller.start()
    try:
        t_dial = time.monotonic()
        await caller.control.command("dial", f"sip:holdspeak@127.0.0.1:{line_port}")
        incoming = await line.listen(timeout=10)
        result["dial_to_incoming_ms"] = round((time.monotonic() - t_dial) * 1000, 1)
        call_id = incoming.data["call_id"]
        await asyncio.sleep(1.0)

        # M1: mouth to ear, both ways.
        def onset(frames, since, threshold=3000):
            for at, frame in list(frames):
                if at < since:
                    continue
                loud = np.nonzero(np.abs(frame.astype(np.int32)) > threshold)[0]
                if len(loud):
                    return at + int(loud[0]) / 16000
            return None

        out, back = [], []
        for _ in range(6):
            idx = node.say_port.queue(tone(1000.0, 80, amp=12000))
            await asyncio.sleep(0.4)
            sent = node.say_port.sent_at(idx)
            heard = onset(caller.frames, sent - 0.01) if sent else None
            if heard:
                out.append((heard - sent) * 1000)
            idx = caller.say.queue(tone(1000.0, 80, amp=12000))
            await asyncio.sleep(0.4)
            sent = caller.say.sent_at(idx)
            heard = onset(line_frames, sent - 0.01) if sent else None
            if heard:
                back.append((heard - sent) * 1000)
            await asyncio.sleep(0.3)
        result["mouth_to_ear_line_to_caller_ms"] = _stats(out)
        result["mouth_to_ear_caller_to_line_ms"] = _stats(back)
        await asyncio.sleep(1.0)
        while True:  # the tones were heard as words or as nothing; start clean
            if line.hub.take("this-mac", f"call:{call_id}") is None:
                break

        # M2: he speaks; end of speech → the text at the Line.
        with wave.open(str(UTTERANCE)) as w:
            speech = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).copy()
        last_loud = int(np.nonzero(np.abs(speech.astype(np.int32)) > 1500)[0][-1])
        runs = []
        for _ in range(3):
            before = len(node.heard_times)
            start = caller.say.queue(speech)
            heard = await line.listen(call_id=call_id, timeout=15)
            await asyncio.sleep(0.05)
            spoken_end = caller.say.sent_at(start + last_loud)
            row = node.heard_times[before] if len(node.heard_times) > before else {}
            runs.append({"end_of_speech_to_detect_ms": round((row["end_of_speech"] - spoken_end) * 1000, 1),
                         "end_of_speech_to_text_ms": round((row["text_at"] - spoken_end) * 1000, 1),
                         "text": heard.data.get("text", "")})
            await asyncio.sleep(1.5)
        result["stt_runs"] = runs
        # Each heard turn started the manners' clock; a say stops it.

        # M3: the Line says a reply: text → first sound at the caller.
        says = []
        for _ in range(3):
            t0 = time.monotonic()
            task = asyncio.ensure_future(line.say(REPLY, call_id=call_id))
            first = None
            deadline = time.monotonic() + 8
            while first is None and time.monotonic() < deadline:
                await asyncio.sleep(0.01)
                first = onset(caller.frames, t0, threshold=1500)
            reply = await task
            says.append({"text_to_first_sound_ms": round((first - t0) * 1000, 1) if first else None,
                         "result": reply.data.get("result")})
            await asyncio.sleep(0.8)
        result["tts_runs"] = says
        hung = time.monotonic()
        await line.hangup(call_id=call_id)
        result["hangup_ms"] = round((time.monotonic() - hung) * 1000, 1)
        from holdspeak.line.speech import gpl_loaded

        result["gpl_loaded"] = gpl_loaded()
    finally:
        await caller.stop()
        await node.stop()
    eos = [r["end_of_speech_to_text_ms"] for r in result.get("stt_runs", [])]
    tts = [r["text_to_first_sound_ms"] for r in result.get("tts_runs", []) if r["text_to_first_sound_ms"]]
    result["summary"] = {"end_of_speech_to_text_ms": _stats(eos), "text_to_first_sound_ms": _stats(tts)}
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tone", action="store_true", help="the tests' tone speech, not the models")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(measure(real_speech=not args.tone)), indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
