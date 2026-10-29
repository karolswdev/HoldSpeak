#!/usr/bin/env python3
"""One real call to a Line node on another machine, through a rig hub (LINE-3).

This Mac runs a rig hub (a real HoldSpeak hub app, its own HOME, its own
token, bound to this Mac's tailnet address) and a caller (a plain baresip with
aupipe). The Line node on the other machine is enrolled against the rig hub
with a code this script mints through the real route and writes to
``--code-file``. When the node's hello arrives, the caller dials the Line,
the hub's ``Line`` adapter (the Calls runner's own surface) hears the fixture
utterance and says a reply, and the script measures, on this Mac's one clock:

- end of speech (the caller's last loud sample) → the text at the hub
  (the call audio over the tailnet, the 300 ms rule, Parakeet on the node,
  the ``heard`` event back), and the node's own speech-in time;
- the hub's ``say`` → the first sound at the caller (the long poll, Pocket on
  the node, the call audio back);
- hang-up.

Mouth to ear is measured with ``--echo``: the node machine runs a plain
baresip that sends each heard frame back (``measure_remote.py echo`` there);
one way is half the round trip.

    HOME=$(mktemp -d) HOLDSPEAK_LINE=on HOLDSPEAK_CALLS=off \\
      python scripts/line/measure_remote.py hub --bind 100.66.207.100 --node karol \\
      --line sip:holdspeak@100.118.33.80:5060 --code-file /tmp/code
    python scripts/line/measure_remote.py echo --bind 100.118.33.80 --port 5070     (on the node machine)
    python scripts/line/measure_remote.py tones --bind 100.66.207.100 --to sip:echo@100.118.33.80:5070
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import statistics
import sys
import tempfile
import time
import urllib.request
import wave
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

UTTERANCE = ROOT / "tests" / "fixtures" / "line_utterance.wav"
REPLY = "Done. I added a task: nudge Tomás about the runbook by Friday."
RATE = 16000


def _stats(values: list[float]) -> dict[str, Any]:
    return {"median": round(statistics.median(values), 1), "min": round(min(values), 1),
            "max": round(max(values), 1), "n": len(values)} if values else {}


def _tone(ms: int = 80, freq: float = 1000.0, amp: int = 12000) -> np.ndarray:
    t = np.arange(int(RATE * ms / 1000)) / RATE
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.int16)


def _onset(frames: list[tuple[float, np.ndarray]], since: float, threshold: int = 1500) -> Any:
    for at, frame in list(frames):
        if at < since:
            continue
        loud = np.nonzero(np.abs(frame.astype(np.int32)) > threshold)[0]
        if len(loud):
            return at + int(loud[0]) / RATE
    return None


class Endpoint:
    """A plain baresip with aupipe on one address (the caller, or the echo)."""

    def __init__(self, root: Path, *, bind: str, sip_port: int, user: str, echo: bool = False) -> None:
        from holdspeak.line.audio import HeardPort, SayPort
        from holdspeak.line.supervisor import Account, LineConfig, Supervisor, build_aupipe, find_baresip

        binary = find_baresip()
        if not binary:
            raise SystemExit("baresip is not installed")
        aupipe = build_aupipe(root / "build", binary=binary)
        self.cfg = LineConfig(home=root / user, bind=bind, sip_port=sip_port, ctrl_port=_free_port(),
                              say_sock=root / f"{user[:1]}.say", heard_sock=root / f"{user[:1]}.heard",
                              account=Account(kind="sip", user=user, codecs=("PCMU", "PCMA")))
        self.frames: list[tuple[float, np.ndarray]] = []
        self.say = SayPort(self.cfg.say_sock)

        def on_frame(at: float, frame: np.ndarray) -> None:
            self.frames.append((at, frame))
            if echo:
                self.say.queue(frame)

        self.heard = HeardPort(self.cfg.heard_sock, on_frame)
        self.supervisor = Supervisor(self.cfg, binary=binary)
        self.supervisor.prepare(aupipe=aupipe)
        self.control: Any = None

    async def start(self) -> None:
        from holdspeak.line.control import Control

        await self.supervisor.start()
        self.control = Control(port=self.cfg.ctrl_port)
        await self.control.connect(wait=10)

    async def wait_event(self, kind: str, timeout: float = 15.0) -> Any:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while True:
            event = await asyncio.wait_for(self.control.events.get(), max(0.01, deadline - loop.time()))
            if event.type == kind:
                return event

    async def stop(self) -> None:
        if self.control is not None:
            await self.control.close()
        await self.supervisor.stop()
        self.say.close()
        self.heard.close()


def _free_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _short_dir() -> Path:
    """A unix socket path is at most 104 bytes on macOS: a short folder
    (``HOLDSPEAK_LINE_RIG_DIR`` names another, for a machine where /tmp is not ours)."""
    base = os.environ.get("HOLDSPEAK_LINE_RIG_DIR") or "/tmp"
    Path(base).mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="hsl", dir=base))


def _post(url: str, token: str, body: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(url, method="POST", data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json", "X-HoldSpeak-Token": token})
    with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310 (the rig hub)
        return json.loads(response.read().decode("utf-8") or "{}")


def _get(url: str, token: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"X-HoldSpeak-Token": token})
    with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310 (the rig hub)
        return json.loads(response.read().decode("utf-8") or "{}")


async def _hub(args: argparse.Namespace) -> dict[str, Any]:
    from holdspeak.line.adapter import Line
    from holdspeak.line.hub import LINE_HUB
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    token = secrets.token_urlsafe(24)
    server = MeetingWebServer(WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None,
                                                  get_state=lambda: {}),
                              host=args.bind, port=args.port, auth_token=token)
    url = server.start()
    out: dict[str, Any] = {"hub": url}
    minted = _post(url + "/api/calls/line/codes", token, {"node": args.node})
    Path(args.code_file).write_text(json.dumps({"hub": url, "code": minted["code"], "node": minted["node"]}))
    print(f"code written: {minted['code']} for {minted['node']} on {url}", flush=True)
    deadline = time.monotonic() + args.wait
    while LINE_HUB.node_state(args.node) != "live":
        if time.monotonic() > deadline:
            raise SystemExit("the node never said hello")
        await asyncio.sleep(0.5)
    await asyncio.sleep(2.0)
    out["status_ready"] = _get(url + "/api/calls/line/status", token)
    out["nodes"] = _get(url + "/api/calls/line/nodes", token)
    line = Line(args.node)
    root = _short_dir()
    caller = Endpoint(root, bind=args.bind, sip_port=_free_port(), user="caller")
    await caller.start()
    try:
        t_dial = time.monotonic()
        await caller.control.command("dial", args.line)
        incoming = await line.listen(timeout=15)
        out["dial_to_incoming_at_hub_ms"] = round((time.monotonic() - t_dial) * 1000, 1)
        call_id = incoming.data.get("call_id", "")
        out["incoming"] = incoming.data
        await asyncio.sleep(1.0)
        with wave.open(str(args.utterance)) as w:
            speech = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).copy()
        last_loud = int(np.nonzero(np.abs(speech.astype(np.int32)) > 1500)[0][-1])
        runs = []
        for _ in range(args.runs):
            start = caller.say.queue(speech)
            heard = await line.listen(call_id=call_id, timeout=20)
            got = time.monotonic()
            spoken_end = caller.say.sent_at(start + last_loud)
            runs.append({"end_of_speech_to_text_at_hub_ms": round((got - spoken_end) * 1000, 1) if spoken_end else None,
                         "node_stt_ms": heard.data.get("stt_ms"), "text": heard.data.get("text", "")})
            # The reply: the hub's say → the first sound at the caller.
            t0 = time.monotonic()
            task = asyncio.ensure_future(line.say(REPLY, call_id=call_id))
            first = None
            until = time.monotonic() + 10
            while first is None and time.monotonic() < until:
                await asyncio.sleep(0.005)
                first = _onset(caller.frames, t0)
            said = await task
            runs[-1]["say_to_first_sound_at_caller_ms"] = round((first - t0) * 1000, 1) if first else None
            runs[-1]["say_result"] = said.data.get("result")
            await asyncio.sleep(1.0)
        out["runs"] = runs
        hung = time.monotonic()
        reply = await line.hangup(call_id=call_id)
        out["hangup_ms"] = round((time.monotonic() - hung) * 1000, 1)
        out["hangup"] = reply.data
    finally:
        await caller.stop()
    eos = [r["end_of_speech_to_text_at_hub_ms"] for r in out.get("runs", []) if r["end_of_speech_to_text_at_hub_ms"]]
    stt = [r["node_stt_ms"] for r in out.get("runs", []) if isinstance(r["node_stt_ms"], (int, float))]
    say = [r["say_to_first_sound_at_caller_ms"] for r in out.get("runs", []) if r["say_to_first_sound_at_caller_ms"]]
    out["summary"] = {"end_of_speech_to_text_at_hub_ms": _stats(eos), "node_stt_ms": _stats(stt),
                      "say_to_first_sound_at_caller_ms": _stats(say)}
    if args.revoke:
        request = urllib.request.Request(f"{url}/api/calls/line/nodes/{args.node}", method="DELETE",
                                         headers={"X-HoldSpeak-Token": token})
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310 (the rig hub)
            out["revoked"] = json.loads(response.read().decode("utf-8"))
        await asyncio.sleep(1.0)
    server.stop()
    return out


async def _echo(args: argparse.Namespace) -> None:
    root = _short_dir()
    echo = Endpoint(root, bind=args.bind, sip_port=args.port, user="echo", echo=True)
    await echo.start()
    print(f"echo on sip:echo@{args.bind}:{args.port}", flush=True)
    try:
        while True:
            event = await echo.control.events.get()
            if event.type == "CALL_INCOMING":
                await echo.control.command("accept", event.call_id)
            if event.type == "CALL_CLOSED" and args.once:
                return
    finally:
        await echo.stop()


async def _tones(args: argparse.Namespace) -> dict[str, Any]:
    root = _short_dir()
    caller = Endpoint(root, bind=args.bind, sip_port=_free_port(), user="caller")
    await caller.start()
    try:
        t0 = time.monotonic()
        await caller.control.command("dial", args.to)
        await caller.wait_event("CALL_ESTABLISHED")
        established = round((time.monotonic() - t0) * 1000, 1)
        await asyncio.sleep(1.5)
        trips = []
        for _ in range(8):
            idx = caller.say.queue(_tone())
            await asyncio.sleep(0.6)
            sent = caller.say.sent_at(idx)
            heard = _onset(caller.frames, sent + 0.01, threshold=3000) if sent else None
            if heard:
                trips.append((heard - sent) * 1000)
            await asyncio.sleep(0.3)
        await caller.control.command("hangup", "")
        await asyncio.sleep(0.5)
    finally:
        await caller.stop()
    return {"dial_to_established_ms": established, "echo_round_trip_ms": _stats(trips),
            "mouth_to_ear_one_way_ms": _stats([t / 2 for t in trips])}


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    hub = sub.add_parser("hub")
    hub.add_argument("--bind", required=True)
    hub.add_argument("--port", type=int, default=18765)
    hub.add_argument("--node", default="karol")
    hub.add_argument("--line", required=True, help="the Line's SIP address")
    hub.add_argument("--code-file", required=True)
    hub.add_argument("--wait", type=float, default=600.0)
    hub.add_argument("--runs", type=int, default=3)
    hub.add_argument("--utterance", default=str(UTTERANCE), help="16 kHz mono s16le speech (the caller's words)")
    hub.add_argument("--revoke", action="store_true", help="revoke the node's credential at the end")
    echo = sub.add_parser("echo")
    echo.add_argument("--bind", required=True)
    echo.add_argument("--port", type=int, default=5070)
    echo.add_argument("--once", action="store_true")
    tones = sub.add_parser("tones")
    tones.add_argument("--bind", required=True)
    tones.add_argument("--to", required=True)
    args = parser.parse_args()
    if args.mode == "hub":
        os.environ.setdefault("HOLDSPEAK_CALLS", "off")  # no listener takes the call from this script
        print(json.dumps(asyncio.run(_hub(args)), indent=1, ensure_ascii=False))
    elif args.mode == "echo":
        asyncio.run(_echo(args))
    else:
        print(json.dumps(asyncio.run(_tones(args)), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
