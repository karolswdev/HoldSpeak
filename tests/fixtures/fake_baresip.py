#!/usr/bin/env python3
"""A fake baresip for the Line's tests: a real separate process.

It speaks baresip 4.12.0's ``ctrl_tcp`` (netstring JSON; the answers and the
event shapes are the RECORDED ones in ``tests/fixtures/baresip_events.json``,
``scripts/line/record_baresip_events.py``) and it is the ``aupipe`` module's
side of the two sockets: it reads our voice from ``say.sock`` one 20 ms
frame at a time (real time, as aupipe does) and writes the caller's voice to
``heard.sock`` one frame every 20 ms (silence between his words).

The caller's words are TONES: word ``i`` of :data:`WORDS` is a tone at
``tone_hz(i)``, and :class:`ToneSTT` hears a tone back as its words, so the
audio really goes through the sockets, the VAD and the end-of-speech rule.
:class:`ToneTTS` is our voice: a 2 kHz tone, 40 ms per character.

    holdspeak/line's Supervisor runs: fake_baresip.py -f <config dir>
    FAKE_BARESIP_SCRIPT=<scenario.json>   FAKE_BARESIP_OUT=<folder>

The scenario::

    {"incoming": {"remote": "sip:...", "after": 0.2} | null,
     "dial": "answer" | "busy" | "none" | "decline",
     "caller": [{"say": "<words>", "wait": "voice" | "quiet" | <seconds>, "barge_ms": 300?},
                {"hangup": true, "wait": ...}],
     "exit_after": <seconds>?}

``wait: "voice"`` waits until we spoke and then were quiet for 400 ms.
``barge_ms`` starts his words that long into our voice instead.
The folder gets ``commands.jsonl`` (each command), ``voice.jsonl`` (each
span of our voice: start, end, seconds) and ``said.raw`` (our PCM).
"""
from __future__ import annotations

import json
import os
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any, Iterator, Optional

import numpy as np

RATE = 16000
FRAME = 320
FRAME_BYTES = FRAME * 2
HERE = Path(__file__).resolve().parent
RECORDED = json.loads((HERE / "baresip_events.json").read_text())

#: The caller's words a test may use; word i is a tone at tone_hz(i).
WORDS = [
    "Blue heron.", "Add a task for me: nudge Tomás about the runbook by Friday.", "That's all, thanks.", "Yes, do it.",
    "No.", "Wait, stop.", "red fox", "What is on my desk today?", "Hello?",
]
VOICE_HZ = 2000.0
AMP = 9000


def tone_hz(index: int) -> float:
    return 300.0 + 75.0 * index


def tone(hz: float, ms: int, amp: int = AMP) -> np.ndarray:
    t = np.arange(int(RATE * ms / 1000)) / RATE
    return (amp * np.sin(2 * np.pi * hz * t)).astype(np.int16)


def words_pcm(words: str) -> np.ndarray:
    """His words as a tone (900 ms; long enough to be speech, short for tests)."""
    return tone(tone_hz(WORDS.index(words)), 900)


def peak_hz(pcm: np.ndarray) -> float:
    spectrum = np.abs(np.fft.rfft(pcm.astype(np.float64)))
    return float(np.fft.rfftfreq(len(pcm), 1 / RATE)[int(np.argmax(spectrum[1:]) + 1)])


class ToneSTT:
    """Hears a tone as its words (the nearest word's tone)."""

    def __init__(self) -> None:
        self.calls = 0

    def transcribe(self, pcm: np.ndarray) -> str:
        self.calls += 1
        hz = peak_hz(pcm)
        index = int(round((hz - 300.0) / 75.0))
        return WORDS[index] if 0 <= index < len(WORDS) and abs(hz - tone_hz(index)) < 30 else ""


class ToneTTS:
    """Our voice: 2 kHz, 40 ms a character, in 100 ms chunks; a short lead
    of silence (the trim is Pocket's own; this voice has none to trim)."""

    def __init__(self) -> None:
        self.texts: list[str] = []

    def stream(self, text: str, stop: Optional[threading.Event] = None) -> Iterator[np.ndarray]:
        self.texts.append(text)
        pcm = tone(VOICE_HZ, max(200, 40 * len(text)), amp=7000)
        for i in range(0, len(pcm), 1600):
            if stop is not None and stop.is_set():
                return
            yield pcm[i:i + 1600]


def _template(kind: str, direction: str) -> dict[str, Any]:
    for step in RECORDED["steps"]:
        for event in step.get("events") or []:
            if event["type"] == kind and event.get("direction") == direction:
                return dict(event)
    raise KeyError(kind)


def _response(command: str) -> dict[str, Any]:
    for step in RECORDED["steps"]:
        if "response" in step and step["step"].split()[-1] == command:
            return dict(step["response"])
    return {"response": True, "ok": True, "data": ""}


def netstring(message: dict[str, Any]) -> bytes:
    raw = json.dumps(message).encode()
    return f"{len(raw)}:".encode() + raw + b","


class Fake:
    def __init__(self, home: Path) -> None:
        self.home = home
        conf: dict[str, str] = {}
        for line in (home / "config").read_text().splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2:
                conf.setdefault(parts[0], parts[1])
        self.ctrl_port = int(conf["ctrl_tcp_listen"].strip().rsplit(":", 1)[1])
        self.say_path = conf["audio_source"].strip().split(",", 1)[1]
        self.heard_path = conf["audio_player"].strip().split(",", 1)[1]
        account = (home / "accounts").read_text().strip()
        self.account = account
        self.aor = account.split(">", 1)[0].lstrip("<")
        script = os.environ.get("FAKE_BARESIP_SCRIPT")
        self.scenario = json.loads(Path(script).read_text()) if script else {}
        self.out = Path(os.environ.get("FAKE_BARESIP_OUT") or home)
        self.out.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.client: Optional[socket.socket] = None
        self.call: Optional[dict[str, Any]] = None
        self.seq = 0
        self.caller_pcm = np.zeros(0, dtype=np.int16)
        self.voice_on = False
        self.voice_start = 0.0
        self.voice_last = 0.0
        self.voice_spans: list[tuple[float, float]] = []
        self.said = open(self.out / "said.raw", "ab")

    # ── ctrl_tcp ─────────────────────────────────────────────────────

    def send(self, message: dict[str, Any]) -> None:
        with self.lock:
            if self.client is not None:
                try:
                    self.client.sendall(netstring(message))
                except OSError:
                    pass

    def event(self, kind: str, *, param: str = "") -> None:
        call = self.call
        if call is None:
            return
        message = _template(kind, call["direction"])
        message.update({"id": call["id"], "peeruri": call["peer"], "contacturi": call["peer"],
                        "accountaor": self.aor, "localuri": self.aor})
        message["param"] = param if param else (call["peer"] if kind == "CALL_INCOMING" else message.get("param", ""))
        self.send(message)

    def log(self, entry: dict[str, Any]) -> None:
        with open(self.out / "commands.jsonl", "a") as handle:
            handle.write(json.dumps({**entry, "at": time.time()}) + "\n")

    def serve_ctrl(self) -> None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", self.ctrl_port))
        server.listen(1)
        while True:
            conn, _ = server.accept()
            with self.lock:
                self.client = conn
            threading.Thread(target=self.read_ctrl, args=(conn,), daemon=True).start()
            threading.Timer(0.05, self.register).start()
            incoming = self.scenario.get("incoming")
            if incoming and not self.scenario.get("_incoming_done"):
                self.scenario["_incoming_done"] = True
                threading.Timer(float(incoming.get("after", 0.2)), self.ring_in, args=(incoming,)).start()

    def read_ctrl(self, conn: socket.socket) -> None:
        buf = b""
        while True:
            try:
                chunk = conn.recv(65536)
            except OSError:
                return
            if not chunk:
                return
            buf += chunk
            while b":" in buf:
                head, rest = buf.split(b":", 1)
                size = int(head)
                if len(rest) < size + 1:
                    break
                message, buf = json.loads(rest[:size]), rest[size + 1:]
                self.command(message)

    def command(self, message: dict[str, Any]) -> None:
        name, params, token = message.get("command"), str(message.get("params") or ""), message.get("token")
        self.log({"command": name, "params": params})
        reply = {"response": True, "ok": True, "data": "", "token": token}
        if name == "dial":
            self.seq += 1
            call_id = f"fa4e{self.seq:012x}"
            reply["data"] = f"call uri: {params}\ncall id: {call_id}\n"
            self.call = {"id": call_id, "direction": "outgoing", "peer": params, "up": False}
            self.send(reply)
            self.event("CALL_OUTGOING")
            self.event("CALL_RINGING")
            mode = self.scenario.get("dial", "answer")
            if mode == "answer":
                threading.Timer(0.2, self.answer_out).start()
            elif mode == "busy":
                threading.Timer(0.2, self.close, kwargs={"param": "486 Busy Here"}).start()
            elif mode == "decline":
                threading.Timer(0.2, self.close, kwargs={"param": "603 Decline"}).start()
            return
        if name == "accept":
            if self.call is None:
                reply.update(ok=False, data="no active call\n")
            else:
                self.send(reply)
                self.call["up"] = True
                self.event("CALL_ESTABLISHED")
                self.start_caller()
                return
        elif name == "hangup":
            if self.call is None:
                reply.update(ok=False, data="no active call\n")
            else:
                self.send(reply)
                self.close(param="Rejected by user")
                return
        elif name == "listcalls":
            reply["data"] = _response("listcalls").get("data", "")
        self.send(reply)

    def register(self) -> None:
        """A carrier account (``regint`` > 0) registers: the fake registrar
        answers REGISTER 200 when the account has ``auth_pass``, else 401.
        The event shape is baresip 4.12.0's ``ua_event`` for the ``register``
        class (``src/event.c``), written from the source, NOT recorded: the
        recorded steps have no registrar."""
        if "regint=0" in self.account or "regint=" not in self.account:
            return
        ok = ";auth_pass=" in self.account
        self.log({"register": self.aor, "answer": 200 if ok else 401})
        self.send({"event": True, "class": "register", "type": "REGISTERING", "accountaor": self.aor, "param": ""})
        self.send({"event": True, "class": "register", "type": "REGISTER_OK" if ok else "REGISTER_FAIL",
                   "accountaor": self.aor, "param": "200 OK" if ok else "401 Unauthorized"})

    def ring_in(self, incoming: dict[str, Any]) -> None:
        self.seq += 1
        self.call = {"id": f"fa4e{self.seq:012x}", "direction": "incoming",
                     "peer": str(incoming.get("remote") or "sip:+12125550142@sip.telnyx.com"), "up": False}
        self.event("CALL_INCOMING")

    def answer_out(self) -> None:
        if self.call is None:
            return
        self.call["up"] = True
        self.event("CALL_ANSWERED")
        self.event("CALL_ESTABLISHED")
        self.start_caller()

    def close(self, *, param: str) -> None:
        call = self.call
        if call is None:
            return
        self.event("CALL_CLOSED", param=param)
        self.call = None

    # ── the audio (aupipe's side) ────────────────────────────────────

    def connect(self, path: str) -> Optional[socket.socket]:
        for _ in range(200):
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(path)
                return sock
            except OSError:
                time.sleep(0.02)
        return None

    def audio(self) -> None:
        say = self.connect(self.say_path)
        heard = self.connect(self.heard_path)
        if say is None or heard is None:
            return
        say.settimeout(0.005)
        tick = time.monotonic()
        partial = b""
        while True:
            # aupipe's source: read what is there for one frame (never block long)
            frame = np.zeros(FRAME, dtype=np.int16)
            try:
                data = partial + say.recv(FRAME_BYTES - len(partial))
                if len(data) == FRAME_BYTES:
                    frame, partial = np.frombuffer(data, dtype=np.int16).copy(), b""
                else:
                    partial = data
            except (socket.timeout, BlockingIOError):
                pass
            except OSError:
                return
            if self.call is not None and self.call.get("up"):
                self.said.write(frame.tobytes())
                self.track_voice(frame)
            with self.lock:
                out, self.caller_pcm = self.caller_pcm[:FRAME], self.caller_pcm[FRAME:]
            if len(out) < FRAME:
                out = np.concatenate([out, np.zeros(FRAME - len(out), dtype=np.int16)])
            try:
                heard.sendall(out.tobytes())
            except OSError:
                return
            tick += 0.02
            delay = tick - time.monotonic()
            if delay > 0:
                time.sleep(delay)

    def track_voice(self, frame: np.ndarray) -> None:
        loud = float(np.sqrt(np.mean(frame.astype(np.float64) ** 2))) > 600
        now = time.monotonic()
        if loud:
            if not self.voice_on:
                self.voice_on, self.voice_start = True, now
            self.voice_last = now
        elif self.voice_on and now - self.voice_last > 0.1:
            self.voice_on = False
            self.voice_spans.append((self.voice_start, self.voice_last))
            with open(self.out / "voice.jsonl", "a") as handle:
                handle.write(json.dumps({"start": self.voice_start, "end": self.voice_last,
                                         "seconds": round(self.voice_last - self.voice_start, 2),
                                         "wall": time.time()}) + "\n")

    def start_caller(self) -> None:
        threading.Thread(target=self.caller, daemon=True).start()

    def caller(self) -> None:
        for step in self.scenario.get("caller") or []:
            wait = step.get("wait", "voice")
            spans_before = len(self.voice_spans)
            if wait == "voice":
                deadline = time.monotonic() + 40
                while time.monotonic() < deadline:
                    if len(self.voice_spans) > spans_before and not self.voice_on and time.monotonic() - self.voice_last > 0.4:
                        break
                    if step.get("barge_ms") and self.voice_on and time.monotonic() - self.voice_start > step["barge_ms"] / 1000:
                        break
                    time.sleep(0.01)
            elif isinstance(wait, (int, float)):
                time.sleep(float(wait))
            if self.call is None:
                return
            if step.get("hangup"):
                self.log({"caller": "hangup"})
                self.close(param="Connection reset by peer [54]")
                return
            words = step["say"]
            self.log({"caller": "say", "words": words})
            with self.lock:
                self.caller_pcm = np.concatenate([self.caller_pcm, words_pcm(words)])


def main() -> int:
    args = sys.argv[1:]
    home = Path(args[args.index("-f") + 1])
    fake = Fake(home)
    exit_after = fake.scenario.get("exit_after")
    if exit_after and not (fake.out / "exited").exists():
        def leave() -> None:
            (fake.out / "exited").write_text("1")
            os._exit(3)
        threading.Timer(float(exit_after), leave).start()
    threading.Thread(target=fake.audio, daemon=True).start()
    fake.serve_ctrl()
    return 0


if __name__ == "__main__":
    sys.exit(main())
