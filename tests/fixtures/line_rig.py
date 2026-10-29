"""The Line's test rig: a LineNode on the fake baresip (a real subprocess),
linked in process to a LineHub, with the tone speech of ``fake_baresip``."""
from __future__ import annotations

import json
import os
import shutil
import socket
import sys
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Optional

from holdspeak.line.hub import LineHub
from holdspeak.line.node import LineNode, LocalLink
from holdspeak.line.turns import Timing
from tests.fixtures.fake_baresip import ToneSTT, ToneTTS

FAKE = Path(__file__).resolve().parent / "fake_baresip.py"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def short_dir() -> Path:
    """A unix socket path is at most 104 bytes on macOS: a short folder."""
    return Path(tempfile.mkdtemp(prefix="hsl", dir="/tmp"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


class Rig:
    def __init__(self, node: LineNode, hub: LineHub, root: Path) -> None:
        self.node, self.hub, self.root = node, hub, root
        self.out = root / "out"

    def commands(self) -> list[dict[str, Any]]:
        return read_jsonl(self.out / "commands.jsonl")

    def voice(self) -> list[dict[str, Any]]:
        return read_jsonl(self.out / "voice.jsonl")


@asynccontextmanager
async def running_node(scenario: dict[str, Any], *, hub: Optional[LineHub] = None, name: str = "this-mac",
                       timing: Optional[Timing] = None, config: Optional[dict[str, Any]] = None,
                       heartbeat: float = 1.0) -> AsyncIterator[Rig]:
    root = short_dir()
    (root / "scenario.json").write_text(json.dumps(scenario))
    saved = {key: os.environ.get(key) for key in ("FAKE_BARESIP_SCRIPT", "FAKE_BARESIP_OUT")}
    os.environ["FAKE_BARESIP_SCRIPT"] = str(root / "scenario.json")
    os.environ["FAKE_BARESIP_OUT"] = str(root / "out")
    hub = hub or LineHub()
    if config is not None:
        hub.config_fn = lambda _node: dict(config)
    node = LineNode(name, LocalLink(hub, name), stt=ToneSTT(), tts=ToneTTS(), argv=[sys.executable, str(FAKE)],
                    home=root, ctrl_port=free_port(), timing=timing, heartbeat=heartbeat)
    try:
        await node.start()
        yield Rig(node, hub, root)
    finally:
        await node.stop()
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        shutil.rmtree(root, ignore_errors=True)


__all__ = ["FAKE", "Rig", "free_port", "read_jsonl", "running_node", "short_dir"]


# ── a real caller: a second baresip with its own aupipe sockets ─────────


class Caller:
    """A real baresip that calls the Line (the spike's far end, kept)."""

    def __init__(self, binary: str, aupipe: Path, root: Path, *, sip_port: int, ctrl_port: int) -> None:
        from holdspeak.line.audio import HeardPort, SayPort
        from holdspeak.line.supervisor import Account, LineConfig, Supervisor

        self.cfg = LineConfig(home=root / "caller", sip_port=sip_port, ctrl_port=ctrl_port,
                              say_sock=root / "c.say", heard_sock=root / "c.heard",
                              account=Account(kind="sip", user="caller", codecs=("PCMU", "PCMA")))
        self.frames: list[tuple[float, Any]] = []
        self.say = SayPort(self.cfg.say_sock)
        self.heard = HeardPort(self.cfg.heard_sock, lambda at, frame: self.frames.append((at, frame)))
        self.supervisor = Supervisor(self.cfg, binary=binary)
        self.supervisor.prepare(aupipe=aupipe)
        self.control: Any = None

    async def start(self) -> None:
        from holdspeak.line.control import Control

        await self.supervisor.start()
        self.control = Control(port=self.cfg.ctrl_port)
        await self.control.connect(wait=10)

    async def wait_event(self, kind: str, timeout: float = 10.0) -> Any:
        import asyncio

        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while True:
            event = await asyncio.wait_for(self.control.events.get(), max(0.01, deadline - loop.time()))
            if event.type == kind:
                return event

    def onset_after(self, since: float, *, threshold: int = 1500) -> Optional[float]:
        import numpy as np

        for at, frame in list(self.frames):
            if at < since:
                continue
            loud = np.nonzero(np.abs(frame.astype(np.int32)) > threshold)[0]
            if len(loud):
                return at + int(loud[0]) / 16000
        return None

    async def stop(self) -> None:
        if self.control is not None:
            await self.control.close()
        await self.supervisor.stop()
        self.say.close()
        self.heard.close()
