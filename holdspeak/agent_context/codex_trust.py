"""Codex hook trust (Conductor R3): Codex runs a hook only after the owner trusts it.

Codex CLI 0.159 (observed under an isolated ``CODEX_HOME``):

* A hook from ``hooks.json`` or from ``-c hooks.<Event>=[...]`` runs only when
  the USER config layer (``$CODEX_HOME/config.toml``) holds
  ``hooks.state."<key>".trusted_hash`` equal to the hook's current hash. The
  key is ``<source>:<event_snake>:<group>:<handler>``; a session flag's source
  is ``/<session-flags>/config.toml``. A trust given by ``-c`` is ignored.
* An untrusted hook does not run. ``codex exec`` skips it with no word; the
  TUI opens "Hooks need review" at start. A changed hook (other command or
  timeout) is ``modified`` and does not run either.
* ``codex app-server`` (JSON-RPC on stdio) lists every hook with its
  ``currentHash`` and ``trustStatus`` (``hooks/list``) and writes the user
  config with Codex's own writer (``config/batchWrite``); this module uses
  only those two calls, so HoldSpeak never computes a Codex hash itself.

Only HoldSpeak's own hooks are trusted here (the rider and the gate, matched
by command); a foreign hook is never touched. The trust write happens only in
the owner-only ``agent_hooks.install`` operation.
"""
from __future__ import annotations

import hashlib
import json
import os
import select
import subprocess
import time
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

APP_SERVER_TIMEOUT_SECONDS = 20.0
SESSION_FLAGS_SOURCE = "sessionFlags"
TRUSTED = "trusted"

class CodexTrustError(RuntimeError):
    """Codex could not list or trust the hooks; ``reason`` is machine-readable."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(detail or reason)
        self.reason = reason


def is_holdspeak_hook(hook: Mapping[str, Any]) -> bool:
    """True for HoldSpeak's own Codex hooks: the rider and the gate."""
    from ..coder_gate import GATE_HOOK_MARKER
    from .hooks import AGENT_HOOK_COMMAND_MARKER

    command = str(hook.get("command") or "")
    if "--agent codex" not in command or "holdspeak" not in command:
        return False
    return AGENT_HOOK_COMMAND_MARKER in command or GATE_HOOK_MARKER in command


class _AppServer:
    """One short ``codex app-server`` process: initialize, a few calls, exit."""

    def __init__(
        self, flags: Sequence[str], *, cwd: str, executable: str = "codex",
        env: Optional[Mapping[str, str]] = None, timeout: float = APP_SERVER_TIMEOUT_SECONDS,
    ) -> None:
        self._timeout = float(timeout)
        self._next = 0
        try:
            self._proc = subprocess.Popen(
                [executable, "app-server", *flags],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                cwd=cwd, env=dict(env) if env is not None else None, text=True,
            )
        except OSError as exc:
            raise CodexTrustError("codex_unavailable", str(exc)) from exc
        self.call("initialize", {"clientInfo": {"name": "holdspeak", "version": "1"}})
        self._send({"jsonrpc": "2.0", "method": "initialized"})

    def __enter__(self) -> "_AppServer":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    def close(self) -> None:
        proc = self._proc
        try:
            if proc.stdin:
                proc.stdin.close()
        except OSError:
            pass
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)

    def _send(self, message: Mapping[str, Any]) -> None:
        assert self._proc.stdin is not None
        try:
            self._proc.stdin.write(json.dumps(message) + "\n")
            self._proc.stdin.flush()
        except OSError as exc:
            raise CodexTrustError("codex_app_server_closed", str(exc)) from exc

    def call(self, method: str, params: Mapping[str, Any]) -> Any:
        self._next += 1
        request_id = self._next
        self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": dict(params)})
        stdout = self._proc.stdout
        assert stdout is not None
        deadline = time.monotonic() + self._timeout
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                raise CodexTrustError("codex_app_server_timeout", f"{method} did not answer")
            ready, _, _ = select.select([stdout], [], [], left)
            if not ready:
                continue
            line = stdout.readline()
            if not line:
                raise CodexTrustError("codex_app_server_closed", f"{method}: the process ended")
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(message, dict) or message.get("id") != request_id:
                continue  # a notification, or another call's answer
            if "error" in message:
                raise CodexTrustError("codex_app_server_error", f"{method}: {message['error']}")
            return message.get("result")


def list_hooks(
    flags: Sequence[str] = (), *, cwd: Optional[str] = None, executable: str = "codex",
    env: Optional[Mapping[str, str]] = None,
) -> list[dict[str, Any]]:
    """Every hook Codex sees for ``cwd`` with ``flags`` (``hooks/list``)."""
    folder = str(cwd or Path.home())
    with _AppServer(flags, cwd=folder, executable=executable, env=env) as server:
        result = server.call("hooks/list", {"cwds": [folder]}) or {}
    rows = result.get("data") if isinstance(result, Mapping) else None
    hooks: list[dict[str, Any]] = []
    for row in rows if isinstance(rows, list) else []:
        for hook in (row.get("hooks") if isinstance(row, Mapping) else None) or []:
            if isinstance(hook, Mapping):
                hooks.append(dict(hook))
    return hooks


def untrusted_launch_hooks(
    flags: Sequence[str], *, cwd: Optional[str] = None, executable: str = "codex",
    env: Optional[Mapping[str, str]] = None,
) -> list[str]:
    """The HoldSpeak session-flag hooks of a launch that Codex will NOT run.

    Empty when every one is trusted. A launch whose hooks Codex does not list
    at all (a parse refusal) returns ``["session-flags:missing"]``."""
    ours = [
        hook for hook in list_hooks(flags, cwd=cwd, executable=executable, env=env)
        if hook.get("source") == SESSION_FLAGS_SOURCE and is_holdspeak_hook(hook)
    ]
    if not ours:
        return ["session-flags:missing"]
    return [str(hook.get("key") or "") for hook in ours if hook.get("trustStatus") != TRUSTED]


def _key_path(key: str) -> str:
    escaped = str(key).replace("\\", "\\\\").replace('"', '\\"')
    return f'hooks.state."{escaped}".trusted_hash'


def trust_holdspeak_hooks(
    flags: Sequence[str], *, cwd: Optional[str] = None, executable: str = "codex",
    env: Optional[Mapping[str, str]] = None,
) -> dict[str, Any]:
    """Trust HoldSpeak's Codex hooks: the installed ``hooks.json`` entries and
    the launch's session-flag hooks (``flags``). Foreign hooks are left alone.

    Writes ``hooks.state.<key>.trusted_hash`` through Codex's own
    ``config/batchWrite`` and lists again to prove it. Returns
    ``{"trusted": [keys written], "already": n, "untrusted": [keys still not trusted]}``."""
    folder = str(cwd or Path.home())
    with _AppServer(flags, cwd=folder, executable=executable, env=env) as server:
        listed = server.call("hooks/list", {"cwds": [folder]}) or {}
        hooks = [
            dict(hook)
            for row in (listed.get("data") or [] if isinstance(listed, Mapping) else [])
            for hook in (row.get("hooks") or [] if isinstance(row, Mapping) else [])
            if isinstance(hook, Mapping) and is_holdspeak_hook(hook)
        ]
        todo = [hook for hook in hooks if hook.get("trustStatus") != TRUSTED]
        edits = [
            {"keyPath": _key_path(str(hook["key"])), "value": str(hook["currentHash"]), "mergeStrategy": "upsert"}
            for hook in todo
            if hook.get("key") and str(hook.get("currentHash") or "").startswith("sha256:")
        ]
        if edits:
            server.call("config/batchWrite", {"edits": edits, "reloadUserConfig": False})
        relisted = server.call("hooks/list", {"cwds": [folder]}) or {}
    after = [
        str(hook.get("key") or "")
        for row in (relisted.get("data") or [] if isinstance(relisted, Mapping) else [])
        for hook in (row.get("hooks") or [] if isinstance(row, Mapping) else [])
        if isinstance(hook, Mapping) and is_holdspeak_hook(hook) and hook.get("trustStatus") != TRUSTED
    ]
    return {
        "trusted": [str(hook["key"]) for hook in todo if str(hook.get("key") or "") not in after],
        "already": len(hooks) - len(todo),
        "untrusted": after,
    }


# ── the stamp (a read with no process, for the Agents card) ──────────


def flags_fingerprint(flags: Sequence[str]) -> str:
    return hashlib.sha256(json.dumps(list(flags)).encode("utf-8")).hexdigest()


def write_trust_stamp(flags: Sequence[str], path: Path) -> None:
    """Record the launch hooks the install operation trusted, so the Agents
    card reads trust without running Codex."""
    target = path
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps({"launch_hooks": flags_fingerprint(flags)}) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def trust_stamp_matches(flags: Sequence[str], path: Path) -> bool:
    """True when the install operation trusted exactly these launch hooks."""
    try:
        stamp = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(stamp, dict) and stamp.get("launch_hooks") == flags_fingerprint(flags)


__all__ = [
    "CodexTrustError",
    "is_holdspeak_hook",
    "list_hooks",
    "trust_holdspeak_hooks",
    "trust_stamp_matches",
    "untrusted_launch_hooks",
    "write_trust_stamp",
]
