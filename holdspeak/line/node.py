"""``holdspeak line``: the Line node (LINE design §4).

One process per machine that owns a phone line: baresip as its supervised
child, the two audio sockets, the speech, the call's manners, and the link to
the hub. Text crosses the link, never audio: the hub sends ``say``,
``hangup`` and ``call``; the node sends ``incoming``, ``heard``, ``ended``,
``dtmf`` and each command's ``result``.

For now the node runs on this Mac against this hub with the hub token
(``HOLDSPEAK_HUB_TOKEN``, else the local config's). The node credential and
the home-box enrolment are LINE-3; everything the node says to the hub goes
through :class:`HubClient`, so that is the one class LINE-3 changes.

    holdspeak line [run] [--node this-mac] [--hub URL] [--bind 127.0.0.1] [--sip-port 5060]
    holdspeak line check      what is installed and what is missing
    holdspeak line build      compile aupipe against this machine's baresip
    holdspeak line models     fetch the two speech models (and say their licences)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Protocol

import numpy as np

from ..logging_config import get_logger
from . import control as ctl
from .audio import HeardPort, SayPort
from .guards import DEFAULT_DAILY_LIMIT, DailyCount, disclosure, is_emergency
from .speech import STT, TTS, EndOfSpeech
from .supervisor import Account, LineConfig, Supervisor, find_baresip, state_dir
from .turns import GIVE_UP, ONE_MOMENT, STILL_WITH_YOU, CallTurns, Timing, Voice

log = get_logger("line.node")

VERSION = "line-2"
HEARTBEAT_SECONDS = 5.0
NODE_TOKEN_HEADER = "X-HoldSpeak-Token"


# ── the link to the hub ───────────────────────────────────────────────


class HubLink(Protocol):
    async def hello(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    async def events(self, events: list[dict[str, Any]]) -> int: ...

    async def next(self, after: int, wait: float) -> list[dict[str, Any]]: ...


class HubClient:
    """Everything the node says to the hub: three POSTs (design §4 "the wire")."""

    def __init__(self, hub: str, token: str, node: str, *, timeout: float = 35.0) -> None:
        self.hub = hub.rstrip("/")
        self.node = node
        self._token = token
        self._timeout = timeout

    def _post(self, path: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
        request = urllib.request.Request(
            self.hub + path, data=json.dumps({"node": self.node, **body}).encode("utf-8"), method="POST",
            headers={"Content-Type": "application/json", NODE_TOKEN_HEADER: self._token},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 (the hub's own URL)
            return json.loads(response.read().decode("utf-8") or "{}")

    async def hello(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(self._post, "/api/calls/line/hello", payload, 10.0)

    async def events(self, events: list[dict[str, Any]]) -> int:
        answer = await asyncio.to_thread(self._post, "/api/calls/line/events", {"events": events}, 10.0)
        return int(answer.get("acked") or 0)

    async def next(self, after: int, wait: float) -> list[dict[str, Any]]:
        answer = await asyncio.to_thread(self._post, "/api/calls/line/next", {"after": after, "wait_s": wait},
                                         wait + 10.0)
        return list(answer.get("commands") or [])


class LocalLink:
    """The same three calls against a hub in this process (tests, measurement)."""

    def __init__(self, hub: Any, node: str) -> None:
        self._hub = hub
        self.node = node

    async def hello(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._hub.hello(self.node, lines=payload.get("lines") or [], version=payload.get("version") or "",
                               active_call=payload.get("active_call"))

    async def events(self, events: list[dict[str, Any]]) -> int:
        return self._hub.post_events(self.node, events)

    async def next(self, after: int, wait: float) -> list[dict[str, Any]]:
        return await self._hub.next(self.node, after=after, wait=wait)


# ── a call on the node ────────────────────────────────────────────────


@dataclass
class Call:
    id: str
    direction: str  # in | out
    remote: str
    turns: CallTurns
    established: bool = False
    by_us: bool = False
    #: the ``call`` command that placed it, until its result is sent.
    pending_cmd: Optional[int] = None
    rang_out: bool = False
    closed: asyncio.Event = field(default_factory=asyncio.Event)
    answered: asyncio.Event = field(default_factory=asyncio.Event)


def close_outcome(param: str, *, rang_out: bool = False) -> str:
    """A placed call that closed before it was answered, as an outcome.
    (baresip's ``CALL_CLOSED`` param, recorded: ``486 Busy Here``.)"""
    found = re.match(r"\s*(\d{3})\b", str(param or ""))
    if rang_out:
        return "no_answer"
    if not found:
        return "failed"
    code = int(found.group(1))
    if code in {486, 600}:
        return "busy"
    if code in {408, 480, 487}:
        return "no_answer"
    return "rejected" if 400 <= code < 700 else "failed"


def dial_id(data: str) -> str:
    """The call id from ``dial``'s answer (``call id: 39c5fc8289003b75``)."""
    found = re.search(r"call id:\s*(\S+)", str(data or ""))
    return found.group(1) if found else ""


class LineNode:
    """The node: baresip, the sockets, the speech, the manners, the link."""

    def __init__(self, name: str, link: HubLink, *, stt: STT, tts: TTS, binary: str = "",
                 argv: Optional[list[str]] = None, home: Optional[Path] = None, bind: str = "127.0.0.1",
                 sip_port: int = 5060, ctrl_port: int = 4444, timing: Optional[Timing] = None,
                 heartbeat: float = HEARTBEAT_SECONDS, aupipe: Optional[Path] = None,
                 say_sock: Optional[Path] = None, heard_sock: Optional[Path] = None) -> None:
        self.name = name
        self.link = link
        self.stt, self.tts = stt, tts
        self.binary = binary
        self._argv = argv
        self.home = Path(home or state_dir())
        self.bind, self.sip_port, self.ctrl_port = bind, int(sip_port), int(ctrl_port)
        self.timing = timing or Timing()
        self.heartbeat = heartbeat
        self._aupipe = aupipe
        self._say_sock, self._heard_sock = say_sock, heard_sock
        self.config: dict[str, Any] = {}
        self.account = Account()
        self.call: Optional[Call] = None
        self.control: Optional[ctl.Control] = None
        self.supervisor: Optional[Supervisor] = None
        self.say_port: Optional[SayPort] = None
        self.heard_port: Optional[HeardPort] = None
        self.voice: Optional[Voice] = None
        self.eos = EndOfSpeech()
        self.line_state = "starting"
        self._seq = 0
        self._outbox: list[dict[str, Any]] = []
        self._tasks: list[asyncio.Task[Any]] = []
        self._pump: Optional[asyncio.Task[None]] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._stopping = False
        self.ready = asyncio.Event()
        self._count = DailyCount(self.home / "placed.json")
        #: Measurement: per heard turn, (end of speech, text ready), monotonic.
        self.heard_times: list[dict[str, Any]] = []

    # ── start and stop ────────────────────────────────────────────────

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        answer = await self._hello()
        self._configure(answer.get("config") or {})
        cfg = LineConfig(home=self.home / "baresip", bind=self.bind, sip_port=self.sip_port,
                         ctrl_port=self.ctrl_port, account=self.account,
                         say_sock=self._say_sock, heard_sock=self._heard_sock)
        self.say_port = SayPort(cfg.say_sock)
        self.heard_port = HeardPort(cfg.heard_sock, self._on_frame_thread)
        self.voice = Voice(self.say_port, self.tts)
        await asyncio.to_thread(self.voice.keep, ONE_MOMENT, STILL_WITH_YOU, GIVE_UP, self._disclosure())
        self.supervisor = Supervisor(cfg, binary=self.binary, argv=self._argv, on_start=self._connect,
                                     on_exit=self._baresip_exit)
        await asyncio.to_thread(self.supervisor.prepare, aupipe=self._aupipe)
        await self.supervisor.start()
        self._tasks = [asyncio.ensure_future(self._poll()), asyncio.ensure_future(self._beat())]
        try:  # the first baresip answers on ctrl_tcp (else the supervisor keeps trying)
            await asyncio.wait_for(self.ready.wait(), 15.0)
        except asyncio.TimeoutError:
            log.warning("baresip did not answer on ctrl_tcp yet")

    async def stop(self) -> None:
        self._stopping = True
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        if self.call is not None:
            self.call.turns.close()
        if self.control is not None:
            await self.control.close()
        if self._pump is not None:
            self._pump.cancel()
        if self.supervisor is not None:
            await self.supervisor.stop()
        for port in (self.say_port, self.heard_port):
            if port is not None:
                port.close()

    def _configure(self, config: dict[str, Any]) -> None:
        self.config = dict(config or {})
        self.account = Account.of(self.config.get("account"), password=str(self.config.get("password") or ""))

    def _disclosure(self) -> str:
        return disclosure(str(self.config.get("owner") or ""))

    def _address(self) -> str:
        if self.account.kind == "telnyx":
            return f"sip:{self.account.user}@{self.account.domain or 'sip.telnyx.com'}"
        return f"sip:{self.account.user}@{self.bind}:{self.sip_port}"

    def _hello_payload(self) -> dict[str, Any]:
        call = self.call
        return {
            "version": VERSION,
            "lines": [{"id": "main", "kind": self.account.kind, "address": self._address(), "state": self.line_state}],
            "active_call": {"call_id": call.id, "direction": call.direction, "remote": call.remote,
                            "established": call.established} if call else None,
        }

    async def _hello(self) -> dict[str, Any]:
        while True:
            try:
                return await self.link.hello(self._hello_payload())
            except Exception as exc:
                if self._stopping:
                    raise
                log.info(f"the hub did not answer the hello: {exc}")
                await asyncio.sleep(2.0)

    # ── baresip ───────────────────────────────────────────────────────

    async def _connect(self) -> None:
        if self.control is not None:
            await self.control.close()
        control = ctl.Control(port=self.ctrl_port)
        await control.connect()
        self.control = control
        self.ready.set()
        if self.account.kind == "sip":
            self.line_state = "listening"  # a SIP address has no registrar
        if self._pump is not None:
            self._pump.cancel()
        self._pump = asyncio.ensure_future(self._events(control))
        await self._send_hello()

    async def _baresip_exit(self, code: int) -> None:
        self.line_state = "unregistered"
        self.ready.clear()
        self.control = None
        call, self.call = self.call, None
        if call is not None:
            call.turns.close()
            call.closed.set()
            if call.pending_cmd is not None:
                await self._post("result", cmd=call.pending_cmd, outcome="not_running", detail=f"baresip exited ({code})")
            elif call.established:
                await self._post("ended", call_id=call.id, outcome="failed", ended_by="holdspeak")

    async def _command(self, command: str, params: str = "") -> dict[str, Any]:
        if self.control is None:
            raise ctl.ControlError("baresip is not running")
        return await self.control.command(command, params)

    async def _events(self, control: ctl.Control) -> None:
        while True:
            event = await control.events.get()
            try:
                await self._on_event(event)
            except Exception as exc:
                log.warning(f"line event {event.type} not handled: {exc}")

    async def _on_event(self, event: ctl.Event) -> None:
        kind = event.type
        if kind == ctl.REGISTER_OK:
            self.line_state = "registered"
            await self._send_hello()
        elif kind in {ctl.REGISTER_FAIL}:
            self.line_state = "unregistered"
            await self._send_hello()
        elif kind == ctl.REGISTERING and self.line_state != "registered":
            self.line_state = "registering"
        elif kind == ctl.INCOMING:
            if self.call is not None and self.call.id != event.call_id:
                await self._command("hangup", f"{event.call_id} scode=486")
                return
            self.call = self._new_call(event.call_id, "in", event.peer or event.param)
            await self._command("accept", event.call_id)
        elif kind == ctl.ESTABLISHED:
            call = self.call
            if call is None or call.id != event.call_id:
                return
            call.established = True
            self.eos.reset()
            if call.direction == "in":
                await self._post("incoming", call_id=call.id, remote=call.remote, line="main")
            call.answered.set()
        elif kind == ctl.CLOSED:
            await self._closed(event)
        elif kind == ctl.DTMF_START:
            if self.call is not None:
                await self._post("dtmf", call_id=event.call_id, key=event.param)

    def _new_call(self, call_id: str, direction: str, remote: str) -> Call:
        assert self.voice is not None

        async def give_up() -> None:
            await self._hang_up(call_id)

        return Call(id=call_id, direction=direction, remote=remote,
                    turns=CallTurns(self.voice, timing=self.timing, give_up=give_up))

    async def _closed(self, event: ctl.Event) -> None:
        call = self.call
        if call is None or (event.call_id and call.id != event.call_id):
            return
        self.call = None
        call.turns.close()
        self.eos.reset()
        call.closed.set()
        if call.pending_cmd is not None and not call.established:
            cmd, call.pending_cmd = call.pending_cmd, None
            await self._post("result", cmd=cmd, outcome=close_outcome(event.param, rang_out=call.rang_out),
                             detail=event.param)
        elif call.established:
            await self._post("ended", call_id=call.id, outcome="completed",
                             ended_by="holdspeak" if call.by_us else "them", detail=event.param)
        await self._send_hello()

    async def _hang_up(self, call_id: str) -> None:
        call = self.call
        if call is None or call.id != call_id:
            return
        call.by_us = True
        call.turns.stop_clock()
        try:
            await self._command("hangup", call.id)
        except ctl.ControlError:
            return
        try:
            await asyncio.wait_for(call.closed.wait(), 5.0)
        except asyncio.TimeoutError:
            log.warning(f"call {call.id} did not close after the hang-up")

    # ── audio in ──────────────────────────────────────────────────────

    def _on_frame_thread(self, at: float, frame: np.ndarray) -> None:
        loop = self._loop
        if loop is not None and not loop.is_closed():
            loop.call_soon_threadsafe(self._on_frame, at, frame)

    def _on_frame(self, at: float, frame: np.ndarray) -> None:
        call = self.call
        if call is None or not call.established:
            return
        utterance = self.eos.feed(frame)
        if self.voice is not None and self.voice.speaking and self.eos.barge_in():
            self.voice.interrupt("interrupted")
        if utterance is not None:
            asyncio.ensure_future(self._hear(call, utterance, at))

    async def _hear(self, call: Call, utterance: np.ndarray, at: float) -> None:
        text = (await asyncio.to_thread(self.stt.transcribe, utterance)).strip()
        done = time.monotonic()
        self.heard_times.append({"end_of_speech": at, "text_at": done, "text": text})
        if not text or self.call is not call:
            return
        await self._post("heard", call_id=call.id, text=text)
        call.turns.heard()

    # ── the hub's commands ────────────────────────────────────────────

    async def _poll(self) -> None:
        after = 0
        while not self._stopping:
            try:
                commands = await self.link.next(after, 20.0)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log.info(f"the hub did not answer next: {exc}")
                await asyncio.sleep(2.0)
                continue
            for command in commands:
                after = max(after, int(command.get("id") or 0))
                asyncio.ensure_future(self._run(command))

    async def _run(self, command: dict[str, Any]) -> None:
        op, cmd = str(command.get("op") or ""), int(command.get("id") or 0)
        try:
            if op == "say":
                await self._say(cmd, str(command.get("call_id") or ""), str(command.get("text") or ""))
            elif op == "hangup":
                await self._hangup_cmd(cmd, str(command.get("call_id") or ""), str(command.get("text") or ""))
            elif op == "call":
                await self._place(cmd, str(command.get("to") or ""), float(command.get("ring_seconds") or 30.0))
        except Exception as exc:
            log.warning(f"line command {op} failed: {exc}")
            await self._post("result", cmd=cmd, result="no_call", outcome="failed", error=str(exc))

    def _call_for(self, call_id: str) -> Optional[Call]:
        call = self.call
        if call is None or not call.established or (call_id and call.id != call_id):
            return None
        return call

    async def _say(self, cmd: int, call_id: str, text: str) -> None:
        call = self._call_for(call_id)
        if call is None:
            await self._post("result", cmd=cmd, result="no_call", call_id=call_id)
            return
        result = await call.turns.say(text)
        if result == "ended" or self.call is not call:
            result = "no_call"
        elif result == "replaced":
            result = "interrupted"
        await self._post("result", cmd=cmd, result=result, call_id=call.id)

    async def _hangup_cmd(self, cmd: int, call_id: str, words: str) -> None:
        call = self._call_for(call_id)
        if call is None:
            await self._post("result", cmd=cmd, result="no_call", call_id=call_id)
            return
        call.by_us = True
        if words:
            await call.turns.say(words)
        await self._hang_up(call.id)
        await self._post("result", cmd=cmd, result="hung_up", call_id=call.id)

    def _uri(self, to: str) -> str:
        target = str(to or "").strip()
        if target.lower().startswith(("sip:", "sips:")):
            return target
        if self.account.kind == "telnyx":
            digits = re.sub(r"[^0-9+]", "", target)
            return f"sip:{digits}@{self.account.domain or 'sip.telnyx.com'}" if digits else ""
        if "@" in target:
            return "sip:" + target
        return ""

    async def _place(self, cmd: int, to: str, ring_seconds: float) -> None:
        if is_emergency(to):
            await self._post("result", cmd=cmd, outcome="emergency")
            return
        limit = int(self.config.get("daily_limit", DEFAULT_DAILY_LIMIT) or 0)
        if not self._count.allow(limit):
            await self._post("result", cmd=cmd, outcome="daily_limit")
            return
        if self.call is not None:
            await self._post("result", cmd=cmd, outcome="busy", detail="a call is in progress")
            return
        uri = self._uri(to)
        if not uri:
            await self._post("result", cmd=cmd, outcome="rejected", error="no line can call a number: add a Telnyx line")
            return
        if self.control is None:
            await self._post("result", cmd=cmd, outcome="not_running")
            return
        answer = await self._command("dial", uri)
        call_id = dial_id(str(answer.get("data") or ""))
        if not answer.get("ok") or not call_id:
            await self._post("result", cmd=cmd, outcome="rejected", detail=str(answer.get("data") or "").strip())
            return
        call = self._new_call(call_id, "out", to)
        call.pending_cmd = cmd
        self.call = call
        self._count.add()
        try:
            await asyncio.wait_for(asyncio.shield(call.answered.wait()), ring_seconds)
        except asyncio.TimeoutError:
            if call.pending_cmd is not None and not call.established:
                call.rang_out = True
                await self._hang_up(call.id)
            return
        if call.pending_cmd is None:
            return  # it closed first; the result is sent
        # The AI disclosure: the first words of every call the Line places.
        await call.turns.say(self._disclosure())
        cmd_id, call.pending_cmd = call.pending_cmd, None
        if self.call is call:
            await self._post("result", cmd=cmd_id, outcome="answered", call_id=call.id)
        else:
            await self._post("result", cmd=cmd_id, outcome="no_answer")

    # ── events out ────────────────────────────────────────────────────

    async def _post(self, kind: str, **fields: Any) -> None:
        self._seq += 1
        self._outbox.append({"seq": self._seq, "kind": kind, "at": time.time(), **fields})
        await self._flush()

    async def _flush(self) -> None:
        if not self._outbox:
            return
        batch = list(self._outbox)
        try:
            acked = await self.link.events(batch)
        except Exception as exc:
            log.info(f"events not sent yet: {exc}")
            return
        self._outbox = [event for event in self._outbox if event["seq"] > acked]

    async def _send_hello(self) -> None:
        try:
            answer = await self.link.hello(self._hello_payload())
        except Exception as exc:
            log.info(f"hello not sent: {exc}")
            return
        config = answer.get("config") or {}
        if config and config != self.config:
            account_before = self.account
            self._configure(config)
            if (self.account.kind, self.account.user, self.account.domain, self.account.password) != (
                    account_before.kind, account_before.user, account_before.domain, account_before.password):
                log.info("the line's account changed; it applies at the next start of baresip")

    async def _beat(self) -> None:
        while not self._stopping:
            await asyncio.sleep(self.heartbeat)
            await self._send_hello()
            await self._flush()


# ── the CLI ───────────────────────────────────────────────────────────


def _hub_token() -> str:
    token = os.environ.get("HOLDSPEAK_HUB_TOKEN", "").strip()
    if token:
        return token
    try:
        from ..config import Config

        return str(Config.load().meeting.web_auth_token or "")
    except Exception:
        return ""


def check() -> dict[str, Any]:
    """What the Line needs on this machine, and what is there."""
    from .speech import MODELS

    binary = find_baresip()
    out: dict[str, Any] = {"baresip": binary or "", "version": "", "aupipe": "", "speech": {}, "models": []}
    if binary:
        from .supervisor import baresip_version

        out["version"] = baresip_version(binary)
        built = state_dir() / "build" / "aupipe.so"
        out["aupipe"] = str(built) if built.exists() else ""
    for module in ("onnx_asr", "onnxruntime", "pocket_tts", "scipy"):
        try:
            __import__(module)
            out["speech"][module] = True
        except ImportError:
            out["speech"][module] = False
    out["models"] = [dict(m) for m in MODELS]
    return out


def fetch_models() -> list[str]:
    """Fetch the two speech models from huggingface.co (the one host the
    Engines window's downloads reach); each is named with its licence."""
    from huggingface_hub import snapshot_download

    from .speech import MODELS

    done = []
    for model in MODELS:
        print(f"{model['name']}: {model['repo']} (~{model['size_mb']} MB). Code {model['code']}; weights {model['weights']}.")
        snapshot_download(model["repo"])
        done.append(model["repo"])
    return done


async def _run_node(args: argparse.Namespace) -> int:
    from .speech import Parakeet, Pocket

    binary = find_baresip()
    if not binary:
        print("baresip is not installed. On macOS: brew install baresip")
        return 2
    token = _hub_token()
    if not token:
        print("No hub token: set HOLDSPEAK_HUB_TOKEN.")
        return 2
    print("Loading the speech models…", flush=True)
    stt, tts = await asyncio.to_thread(Parakeet), await asyncio.to_thread(Pocket)
    node = LineNode(args.node, HubClient(args.hub, token, args.node), stt=stt, tts=tts, binary=binary,
                    bind=args.bind, sip_port=args.sip_port, ctrl_port=args.ctrl_port)
    await node.start()
    print(f"The Line is ready: {node._address()}", flush=True)
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await node.stop()


def main(argv: Optional[list[str]] = None) -> int:
    from . import line_on

    parser = argparse.ArgumentParser(prog="holdspeak line", description="Run this machine's phone line.")
    parser.add_argument("action", nargs="?", default="run", choices=("run", "check", "build", "models"))
    parser.add_argument("--node", default="this-mac")
    parser.add_argument("--hub", default="http://127.0.0.1:8765")
    parser.add_argument("--bind", default="127.0.0.1", help="the one address SIP listens on (never 0.0.0.0)")
    parser.add_argument("--sip-port", type=int, default=5060)
    parser.add_argument("--ctrl-port", type=int, default=4444)
    args = parser.parse_args(list(argv if argv is not None else sys.argv[1:]))
    if args.action == "check":
        print(json.dumps(check(), indent=1))
        return 0
    if args.action == "build":
        from .supervisor import build_aupipe

        binary = find_baresip()
        if not binary:
            print("baresip is not installed. On macOS: brew install baresip")
            return 2
        print(build_aupipe(state_dir() / "build", binary=binary, force=True))
        return 0
    if args.action == "models":
        fetch_models()
        return 0
    if not line_on():
        print("The Line is off on this machine (HOLDSPEAK_LINE=off).")
        return 0
    try:
        return asyncio.run(_run_node(args))
    except KeyboardInterrupt:
        return 0


__all__ = ["Call", "HubClient", "HubLink", "LineNode", "LocalLink", "VERSION", "check", "close_outcome", "dial_id", "main"]
