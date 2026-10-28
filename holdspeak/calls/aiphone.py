"""The ai-phone adapter: run the owner's ai-phone CLI and read its answers.

ai-phone (read at commit 436f9f1b, its ``docs/usage.md#agent-commands``)
prints exactly ONE JSON object on stdout for ``call``, ``listen``, ``say``
and ``hangup`` with ``--json``; ``call`` also writes progress events to
stderr, one JSON object per line. Its exit codes:

====  ==========================================================
0     answered / ended / heard / said / hung up
2     bad usage
5     busy (the other end, or a call is already in progress)
6     no answer
7     rejected
8     redirected
9     ai-phone is not running (or a hangup did not end the call)
10    ``listen`` timed out (the call, if any, goes on)
11    no such call, no call in progress, or the wrong mode
12    another ``listen`` is already waiting for calls
13    emergency number
14    daily outbound call limit reached
130   interrupted
====  ==========================================================

``ai-phone status`` and ``ai-phone lines list`` print text only, so the state
(lines, the active call, the brain) is read from ``~/.ai-phone/state.json``
(the file ``status`` prints) and liveness from ``control.sock``, the same
way ``status`` does. ``secrets.env`` (the carrier keys) is never read.
"""
from __future__ import annotations

import asyncio
import json
import os
import shlex
import shutil
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ..logging_config import get_logger

log = get_logger("calls.aiphone")

#: ai-phone's exit codes (``control/protocol.py`` EXIT), by meaning.
OK = 0
USAGE = 2
BUSY = 5
NO_ANSWER = 6
REJECTED = 7
REDIRECTED = 8
NOT_RUNNING = 9
LISTEN_TIMEOUT = 10
NO_CALL = 11
LISTENER_BUSY = 12
EMERGENCY = 13
DAILY_LIMIT = 14
INTERRUPTED = 130

#: An exit code as the word our API answers (``POST /api/calls/place`` 409).
REASONS = {
    USAGE: "usage", BUSY: "busy", NO_ANSWER: "no_answer", REJECTED: "rejected",
    REDIRECTED: "redirected", NOT_RUNNING: "not_running", LISTEN_TIMEOUT: "timeout",
    NO_CALL: "no_call", LISTENER_BUSY: "listener_busy", EMERGENCY: "emergency",
    DAILY_LIMIT: "daily_limit", INTERRUPTED: "interrupted",
}

#: The command a rig (or the owner) names whole: it wins over the settings.
COMMAND_ENV = "HOLDSPEAK_AI_PHONE"
#: ai-phone's own home override (its ``paths.py``).
HOME_ENV = "AI_PHONE_HOME"

#: How long a command may run beyond its own wait before it is stopped.
_GRACE_SECONDS = 20.0


@dataclass
class Reply:
    """One ai-phone command's answer: its exit code, its JSON object, and
    (``call`` only) its progress events."""

    code: int
    data: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.code == OK and self.data.get("ok", True) is not False

    @property
    def kind(self) -> str:
        return str(self.data.get("kind") or "")

    @property
    def reason(self) -> str:
        return REASONS.get(self.code, "failed" if self.code else "")

    @property
    def error(self) -> str:
        return str(self.data.get("error") or "")


def resolve_command(aiphone_dir: str = "") -> Optional[list[str]]:
    """The argv that runs ai-phone, or None when it is not found.

    ``HOLDSPEAK_AI_PHONE`` (a whole command) wins. Then the checkout in
    ``calls.aiphone_dir``: its venv's ``ai-phone`` when it is there (no ``uv``
    start-up on every turn), else ``uv run --project <dir> ai-phone``. Then
    ``ai-phone`` on ``PATH``."""
    named = os.environ.get(COMMAND_ENV, "").strip()
    if named:
        return shlex.split(named)
    folder = str(aiphone_dir or "").strip()
    if folder:
        root = Path(folder).expanduser()
        venv_bin = root / ".venv" / "bin" / "ai-phone"
        if venv_bin.is_file() and os.access(venv_bin, os.X_OK):
            return [str(venv_bin)]
        if (root / "pyproject.toml").is_file():
            uv = shutil.which("uv")
            if uv:
                return [uv, "run", "--project", str(root), "ai-phone"]
        return None
    found = shutil.which("ai-phone")
    return [found] if found else None


def aiphone_home() -> Path:
    """ai-phone's home folder (``AI_PHONE_HOME`` or ``~/.ai-phone``)."""
    return Path(os.environ.get(HOME_ENV) or "~/.ai-phone").expanduser()


def _last_json(text: str) -> dict[str, Any]:
    for line in reversed([line.strip() for line in str(text or "").splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    return {}


def _json_lines(text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in str(text or "").splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            out.append(value)
    return out


class AiPhone:
    """The ai-phone CLI, one command at a time, as a separate process."""

    def __init__(self, argv: list[str], *, home: Optional[Path] = None) -> None:
        self._argv = list(argv)
        self._home = home
        self._running: set[asyncio.subprocess.Process] = set()

    @classmethod
    def from_settings(cls, aiphone_dir: str = "") -> Optional["AiPhone"]:
        argv = resolve_command(aiphone_dir)
        return cls(argv) if argv else None

    @property
    def argv(self) -> list[str]:
        return list(self._argv)

    @property
    def home(self) -> Path:
        return self._home or aiphone_home()

    async def run(self, *args: str, wait: float = 60.0) -> Reply:
        """Run ``ai-phone <args> --json``; its one JSON object and exit code."""
        try:
            proc = await asyncio.create_subprocess_exec(
                *self._argv, *args, "--json",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,
            )
        except (OSError, ValueError) as exc:
            log.info(f"ai-phone did not start: {exc}")
            return Reply(NOT_RUNNING, {"ok": False, "error": f"ai-phone did not start: {exc}"})
        self._running.add(proc)
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=wait + _GRACE_SECONDS)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return Reply(NOT_RUNNING, {"ok": False, "error": "ai-phone did not answer in time"})
        except asyncio.CancelledError:
            # A cancelled listen: closing it puts its event back (ai-phone's
            # own rule), so the next listen gets it.
            if proc.returncode is None:
                proc.kill()
                await proc.wait()
            raise
        finally:
            self._running.discard(proc)
        code = int(proc.returncode if proc.returncode is not None else NOT_RUNNING)
        return Reply(code, _last_json(out.decode("utf-8", "replace")), _json_lines(err.decode("utf-8", "replace")))

    def stop_all(self) -> None:
        """Stop every command still running (the hub stops)."""
        for proc in list(self._running):
            if proc.returncode is None:
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass

    # ── the relay commands ────────────────────────────────────────────

    async def listen(self, *, call_id: str = "", timeout: float = 60.0) -> Reply:
        args = ["listen", "--timeout-sec", f"{max(1.0, float(timeout)):g}"]
        if call_id:
            args += ["--call", call_id]
        return await self.run(*args, wait=timeout)

    async def say(self, text: str, *, call_id: str = "") -> Reply:
        args = ["say", text]
        if call_id:
            args += ["--call", call_id]
        return await self.run(*args, wait=60.0)

    async def hangup(self, *, say: str = "", call_id: str = "") -> Reply:
        args = ["hangup"]
        if call_id:
            args += ["--call", call_id]
        if say:
            args += ["--say", say]
        return await self.run(*args, wait=60.0)

    async def call(self, to: str, *, ring_seconds: float = 30.0, line: str = "") -> Reply:
        args = ["call", to, "--relay", "--timeout-sec", f"{max(1.0, float(ring_seconds)):g}"]
        if line:
            args += ["--line", line]
        return await self.run(*args, wait=ring_seconds + 30.0)

    # ── its state (``ai-phone status`` reads the same two things) ─────

    def running(self) -> bool:
        path = self.home / "control.sock"
        if not path.exists():
            return False
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        try:
            sock.connect(str(path))
            return True
        except OSError:
            return False
        finally:
            sock.close()

    def state(self) -> dict[str, Any]:
        """``state.json``: ``lines``, ``active_call``, ``brain`` (empty when
        ai-phone never started)."""
        try:
            value = json.loads((self.home / "state.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return value if isinstance(value, dict) else {}


__all__ = [
    "AiPhone", "Reply", "resolve_command", "aiphone_home", "COMMAND_ENV", "HOME_ENV",
    "OK", "BUSY", "NO_ANSWER", "REJECTED", "NOT_RUNNING", "LISTEN_TIMEOUT", "NO_CALL",
    "LISTENER_BUSY", "EMERGENCY", "DAILY_LIMIT",
]
