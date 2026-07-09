"""Local mesh nodes — a real ``holdspeak mesh serve`` worker, spawned and killed.

A recipe can spawn a named worker that polls the run's product as its hub
(``mesh serve --hub http://127.0.0.1:<product_port> --node <name>``) in its
own process group, watch the product report it live, then SIGINT the group
and watch it go offline. The worker is a subprocess — no ``holdspeak``
import into the conductor.

Only *local* processes here; a node on another machine is a Phase-2 question.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MeshNode:
    name: str
    hub_url: str
    home: Path
    log_dir: Path
    token: str | None = None
    proc: subprocess.Popen | None = None
    _stdout_f: object = None
    _stderr_f: object = None

    @property
    def stdout_path(self) -> Path:
        return self.log_dir / f"node-{self.name}.stdout.log"

    @property
    def stderr_path(self) -> Path:
        return self.log_dir / f"node-{self.name}.stderr.log"

    def _command(self) -> list[str]:
        return [
            sys.executable, "-m", "holdspeak.main", "mesh", "serve",
            "--hub", self.hub_url,
            "--node", self.name,
            "--token-env", "HOLDSPEAK_HUB_TOKEN",
        ]

    def _env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        if self.token:
            env["HOLDSPEAK_HUB_TOKEN"] = self.token
        return env

    def start(self) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._stdout_f = open(self.stdout_path, "ab", buffering=0)
        self._stderr_f = open(self.stderr_path, "ab", buffering=0)
        self.proc = subprocess.Popen(
            self._command(),
            cwd=str(Path(__file__).resolve().parents[3]),
            env=self._env(),
            stdout=self._stdout_f,
            stderr=self._stderr_f,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )

    @property
    def pid(self) -> int | None:
        return self.proc.pid if self.proc else None

    def is_alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def stop(self, grace: float = 5.0) -> None:
        if self.proc is not None and self.proc.poll() is None:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGINT)
            except (ProcessLookupError, OSError):
                try:
                    self.proc.send_signal(signal.SIGINT)
                except (ProcessLookupError, OSError):
                    pass
            try:
                self.proc.wait(timeout=grace)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
                except (ProcessLookupError, OSError):
                    pass
        for f in (self._stdout_f, self._stderr_f):
            try:
                if f:
                    f.close()
            except OSError:
                pass

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "hub_url": self.hub_url,
            "pid": self.pid,
            "alive": self.is_alive(),
        }


class NodeManager:
    """Owns the mesh nodes a single run has spawned."""

    def __init__(self):
        self._nodes: dict[str, MeshNode] = {}

    def spawn(self, *, name: str, hub_url: str, home: Path, log_dir: Path, token: str | None) -> MeshNode:
        if name in self._nodes and self._nodes[name].is_alive():
            return self._nodes[name]  # idempotent: a live node of this name already serves
        node = MeshNode(name=name, hub_url=hub_url, home=home, log_dir=log_dir, token=token)
        node.start()
        self._nodes[name] = node
        return node

    def kill(self, name: str) -> bool:
        node = self._nodes.get(name)
        if node is None:
            return False
        node.stop()
        return True

    def get(self, name: str) -> MeshNode | None:
        return self._nodes.get(name)

    def list(self) -> list[MeshNode]:
        return list(self._nodes.values())

    def kill_all(self) -> None:
        for node in list(self._nodes.values()):
            try:
                node.stop()
            except Exception:
                pass
