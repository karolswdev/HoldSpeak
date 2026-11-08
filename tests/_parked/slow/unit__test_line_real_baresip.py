"""The Line (2026-10-29) on the REAL baresip installed on this machine: aupipe
builds and loads, a call between two baresips on 127.0.0.1 carries audio both
ways in under 150 ms, the Line hears his words, and no GPL library is mapped
into baresip or the Line's process. Skips when baresip is not installed."""
from __future__ import annotations

import asyncio
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
import pytest

from holdspeak.line.adapter import Line
from holdspeak.line.hub import LineHub
from holdspeak.line.node import LineNode, LocalLink
from holdspeak.line.speech import gpl_loaded
from holdspeak.line.supervisor import build_aupipe, find_baresip
from tests.fixtures.fake_baresip import ToneSTT, ToneTTS, tone, words_pcm
from tests.fixtures.line_rig import Caller, free_port, short_dir

pytestmark = [pytest.mark.slow, pytest.mark.timeout(240, method="thread")]

BARESIP = find_baresip()
UTTERANCE = Path(__file__).resolve().parents[1] / "fixtures" / "line_utterance.wav"


def _maps(pid: int) -> str:
    if sys.platform == "darwin":
        return subprocess.run(["vmmap", str(pid)], capture_output=True, text=True, timeout=60).stdout
    return Path(f"/proc/{pid}/maps").read_text()


def _onset(frames, since: float, threshold: int = 3000):
    for at, frame in list(frames):
        if at < since:
            continue
        loud = np.nonzero(np.abs(frame.astype(np.int32)) > threshold)[0]
        if len(loud):
            return at + int(loud[0]) / 16000
    return None


@pytest.mark.skipif(BARESIP is None, reason="baresip is not installed")
def test_a_real_call_carries_audio_both_ways_and_the_line_hears_him() -> None:
    try:
        from holdspeak.line.speech import Parakeet

        stt = Parakeet()
        real = True
    except Exception:  # the line extra or its model is not here: the tone ear
        stt, real = ToneSTT(), False

    async def walk() -> dict:
        root = short_dir()
        aupipe = build_aupipe(root / "build", binary=BARESIP)
        hub = LineHub()
        hub.config_fn = lambda _n: {"account": {"kind": "sip", "user": "holdspeak", "codecs": ["PCMU", "PCMA"]},
                                    "owner": "Karol"}
        port = free_port()
        node = LineNode("this-mac", LocalLink(hub, "this-mac"), stt=stt, tts=ToneTTS(), binary=BARESIP,
                        home=root / "line", sip_port=port, ctrl_port=free_port(), aupipe=aupipe,
                        say_sock=root / "l.say", heard_sock=root / "l.heard")
        caller = Caller(BARESIP, aupipe, root, sip_port=free_port(), ctrl_port=free_port())
        line = Line("this-mac", hub=hub, count_path=root / "c.json")
        heard_frames: list = []
        await node.start()
        inner = node.heard_port.on_frame
        node.heard_port.on_frame = lambda at, f: (heard_frames.append((at, f)), inner(at, f))
        await caller.start()
        out: dict = {"modules": list(node.supervisor.modules)}
        try:
            await caller.control.command("dial", f"sip:holdspeak@127.0.0.1:{port}")
            incoming = await line.listen(timeout=10)
            call_id = incoming.data["call_id"]
            await asyncio.sleep(1.0)
            to_caller, to_line = [], []
            for _ in range(4):
                idx = node.say_port.queue(tone(1000.0, 80, amp=12000))
                await asyncio.sleep(0.4)
                sent = node.say_port.sent_at(idx)
                got = _onset(caller.frames, sent - 0.01)
                to_caller.append((got - sent) * 1000 if got else 9999)
                idx = caller.say.queue(tone(1000.0, 80, amp=12000))
                await asyncio.sleep(0.4)
                sent = caller.say.sent_at(idx)
                got = _onset(heard_frames, sent - 0.01)
                to_line.append((got - sent) * 1000 if got else 9999)
            out["to_caller"], out["to_line"] = to_caller, to_line
            if real:
                with wave.open(str(UTTERANCE)) as w:
                    caller.say.queue(np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16))
            else:
                caller.say.queue(words_pcm("Blue heron."))
            heard = await line.listen(call_id=call_id, timeout=20)
            out["heard"] = heard.data.get("text", "")
            out["baresip_maps"] = _maps(node.supervisor.proc.pid)
            out["gpl"] = gpl_loaded()
            await line.hangup(say="", call_id=call_id)
        finally:
            await caller.stop()
            await node.stop()
        return out

    out = asyncio.run(walk())
    assert "gzrtp" not in out["modules"] and "aupipe" in out["modules"]
    assert max(out["to_caller"]) < 150 and max(out["to_line"]) < 150, out
    if real:
        assert "Tomas" in out["heard"] and "runbook" in out["heard"].replace(" ", ""), out["heard"]
    else:
        assert out["heard"] == "Blue heron.", out["heard"]
    assert not any(name in out["baresip_maps"] for name in ("espeak", "x264", "x265"))
    assert out["gpl"] == []
