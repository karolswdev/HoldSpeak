"""baresip's ``ctrl_tcp``: netstring JSON commands, responses and events.

The wire (baresip 4.12.0 ``modules/ctrl_tcp/ctrl_tcp.c``): each message is a
netstring ``<length>:<json>,``. We send ``{"command", "params", "token"}``;
baresip answers ``{"response": true, "ok", "data", "token"}`` and sends
``{"event": true, "class", "type", "id", "peeruri", "param", ...}`` for
registration, calls and DTMF. The event shapes the tests replay are recorded
from a real baresip (``tests/fixtures/baresip_events.json``,
``scripts/line/record_baresip_events.py``).
"""
from __future__ import annotations

import asyncio
import itertools
import json
from dataclasses import dataclass, field
from typing import Any, Optional

from ..logging_config import get_logger

log = get_logger("line.control")

#: The event types the Line acts on (baresip's ``ua_event`` names).
REGISTERING = "REGISTERING"
REGISTER_OK = "REGISTER_OK"
REGISTER_FAIL = "REGISTER_FAIL"
INCOMING = "CALL_INCOMING"
OUTGOING = "CALL_OUTGOING"
RINGING = "CALL_RINGING"
PROGRESS = "CALL_PROGRESS"
ESTABLISHED = "CALL_ESTABLISHED"
CLOSED = "CALL_CLOSED"
DTMF_START = "CALL_DTMF_START"
DTMF_END = "CALL_DTMF_END"

#: The longest message we take (a netstring head says how long it is).
MAX_MESSAGE = 1 << 20


def encode(message: dict[str, Any]) -> bytes:
    """One netstring of JSON."""
    raw = json.dumps(message, separators=(",", ":")).encode("utf-8")
    return str(len(raw)).encode("ascii") + b":" + raw + b","


class NetstringError(ValueError):
    pass


class Decoder:
    """Bytes in, whole messages out (a partial message waits for the rest)."""

    def __init__(self) -> None:
        self._buf = b""

    def feed(self, data: bytes) -> list[dict[str, Any]]:
        self._buf += data
        out: list[dict[str, Any]] = []
        while True:
            colon = self._buf.find(b":")
            if colon < 0:
                if len(self._buf) > 12:
                    raise NetstringError("no length head")
                return out
            head = self._buf[:colon]
            if not head.isdigit():
                raise NetstringError(f"bad length head {head[:12]!r}")
            size = int(head)
            if size > MAX_MESSAGE:
                raise NetstringError("message too long")
            end = colon + 1 + size
            if len(self._buf) < end + 1:
                return out
            if self._buf[end:end + 1] != b",":
                raise NetstringError("no closing comma")
            body, self._buf = self._buf[colon + 1:end], self._buf[end + 1:]
            try:
                value = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, ValueError) as exc:
                raise NetstringError(f"not JSON: {exc}") from None
            if isinstance(value, dict):
                out.append(value)


@dataclass
class Event:
    """One baresip event, the fields the Line reads."""

    type: str
    call_id: str = ""
    peer: str = ""
    param: str = ""
    account: str = ""
    direction: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def of(cls, message: dict[str, Any]) -> "Event":
        return cls(
            type=str(message.get("type") or ""), call_id=str(message.get("id") or ""),
            peer=str(message.get("peeruri") or ""), param=str(message.get("param") or ""),
            account=str(message.get("accountaor") or message.get("accountaref") or ""), direction=str(message.get("direction") or ""),
            raw=dict(message),
        )


class ControlError(RuntimeError):
    pass


class Control:
    """An asyncio client of one baresip's ``ctrl_tcp``."""

    def __init__(self, host: str = "127.0.0.1", port: int = 4444) -> None:
        self.host, self.port = host, int(port)
        self.events: "asyncio.Queue[Event]" = asyncio.Queue()
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._pending: dict[str, "asyncio.Future[dict[str, Any]]"] = {}
        self._tokens = itertools.count(1)
        self._task: Optional[asyncio.Task[None]] = None
        self.closed = asyncio.Event()

    async def connect(self, *, wait: float = 10.0) -> None:
        """Connect; baresip may still be starting, so try for ``wait`` s."""
        loop = asyncio.get_running_loop()
        deadline = loop.time() + wait
        while True:
            try:
                self._reader, self._writer = await asyncio.open_connection(self.host, self.port)
                break
            except OSError:
                if loop.time() > deadline:
                    raise ControlError(f"ctrl_tcp did not answer on {self.host}:{self.port}") from None
                await asyncio.sleep(0.05)
        self.closed.clear()
        self._task = asyncio.ensure_future(self._read())

    async def _read(self) -> None:
        decoder = Decoder()
        assert self._reader is not None
        try:
            while True:
                chunk = await self._reader.read(65536)
                if not chunk:
                    break
                for message in decoder.feed(chunk):
                    if message.get("event"):
                        self.events.put_nowait(Event.of(message))
                    elif message.get("response"):
                        fut = self._pending.pop(str(message.get("token") or ""), None)
                        if fut is not None and not fut.done():
                            fut.set_result(message)
        except (OSError, NetstringError) as exc:
            log.info(f"ctrl_tcp closed: {exc}")
        finally:
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(ControlError("ctrl_tcp closed"))
            self._pending.clear()
            self.closed.set()

    async def command(self, command: str, params: str = "", *, timeout: float = 5.0) -> dict[str, Any]:
        """One command and its response (``ok``, ``data``)."""
        if self._writer is None or self.closed.is_set():
            raise ControlError("ctrl_tcp is not connected")
        token = f"hs{next(self._tokens)}"
        fut: "asyncio.Future[dict[str, Any]]" = asyncio.get_running_loop().create_future()
        self._pending[token] = fut
        self._writer.write(encode({"command": command, "params": params, "token": token}))
        await self._writer.drain()
        try:
            return await asyncio.wait_for(fut, timeout)
        finally:
            self._pending.pop(token, None)

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except OSError:
                pass
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        self.closed.set()


__all__ = [
    "CLOSED", "Control", "ControlError", "DTMF_END", "DTMF_START", "Decoder", "ESTABLISHED", "Event", "INCOMING",
    "NetstringError", "OUTGOING", "PROGRESS", "REGISTER_FAIL", "REGISTER_OK", "REGISTERING", "RINGING", "encode",
]
