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

Only HoldSpeak's own hooks are trusted and enabled here: each matched EXACTLY
(source, definition position, event, matcher, command, timeout) against the
hooks HoldSpeak generates. A foreign hook, a wrapper, an appended command or a
comment is never touched (Astra round 1 on #914). A launch needs every one of
its hooks listed, enabled and trusted. The trust write happens only in
the owner-only ``agent_hooks.install`` operation.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import select
import subprocess
import time
import tomllib
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


SESSION_FLAGS_PATH = "/<session-flags>/config.toml"


def _snake(event: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", event).lower()


def _camel(event: str) -> str:
    return event[:1].lower() + event[1:]


def _specs_of(hooks: Mapping[str, Any], *, source: str, path: str) -> list[dict[str, Any]]:
    """One exact spec per handler of a hooks document (event -> groups)."""
    specs: list[dict[str, Any]] = []
    for event, groups in hooks.items():
        for g, group in enumerate(groups):
            if group is None:
                continue  # a foreign group position (hooks.json): not ours
            for h, handler in enumerate(group.get("hooks") or []):
                specs.append({
                    "source": source, "path": path,
                    "suffix": f":{_snake(event)}:{g}:{h}", "eventName": _camel(event),
                    "matcher": group.get("matcher"), "command": handler["command"],
                    "timeoutSec": handler.get("timeout"),
                })
    return specs


def launch_specs(flags: Sequence[str]) -> list[dict[str, Any]]:
    """The exact hooks a launch's ``-c hooks.<Event>=[...]`` flags define."""
    hooks: dict[str, Any] = {}
    pairs = zip(flags[0::2], flags[1::2])
    for flag, value in pairs:
        key, _, raw = str(value).partition("=")
        if flag == "-c" and key.startswith("hooks."):
            hooks[key[len("hooks."):]] = tomllib.loads(f"v = {raw}")["v"]
    return _specs_of(hooks, source=SESSION_FLAGS_SOURCE, path=SESSION_FLAGS_PATH)


def installed_specs(hooks_json: Path, template: Mapping[str, Any]) -> list[dict[str, Any]]:
    """HoldSpeak's rider entries in an installed ``hooks.json``: only entries
    EQUAL to the template's, at the position the file holds them."""
    try:
        document = json.loads(Path(hooks_json).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    installed = document.get("hooks") if isinstance(document, Mapping) else None
    ours = (template.get("hooks") or {})
    positions: dict[str, list[Any]] = {}
    for event, groups in (installed or {}).items():
        wanted = ours.get(event) or []
        positions[event] = [g if g in wanted else None for g in (groups if isinstance(groups, list) else [])]
    return _specs_of(positions, source="user", path=os.path.realpath(str(hooks_json)))


def _matches(hook: Mapping[str, Any], spec: Mapping[str, Any]) -> bool:
    """An exact match: source, definition position, event, matcher, command,
    timeout. A wrapper, an appended command or a comment never matches."""
    if hook.get("source") != spec["source"] or hook.get("handlerType") != "command":
        return False
    if bool(hook.get("async")) or hook.get("command") != spec["command"]:
        return False
    if hook.get("eventName") != spec["eventName"] or hook.get("matcher") != spec["matcher"]:
        return False
    if hook.get("timeoutSec") != spec["timeoutSec"]:
        return False
    key = str(hook.get("key") or "")
    if spec["source"] == SESSION_FLAGS_SOURCE:
        return key == spec["path"] + spec["suffix"]
    source_path = str(hook.get("sourcePath") or "")
    return bool(source_path) and os.path.realpath(source_path) == spec["path"] and key == source_path + spec["suffix"]


def _problems(hooks: list[dict[str, Any]], specs: list[dict[str, Any]]) -> tuple[list[tuple[dict, dict]], list[str]]:
    """Each spec's listed hook, and what keeps the set from running: a hook
    missing, disabled or not trusted."""
    found: list[tuple[dict, dict]] = []
    problems: list[str] = []
    for spec in specs:
        hook = next((h for h in hooks if _matches(h, spec)), None)
        if hook is None:
            problems.append(f"missing:{spec['path']}{spec['suffix']}")
            continue
        found.append((spec, hook))
        if hook.get("enabled") is False:
            problems.append(f"disabled:{hook['key']}")
        if hook.get("trustStatus") != TRUSTED:
            problems.append(f"untrusted:{hook['key']}")
    return found, problems


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
    """What keeps a launch's hooks from running: each expected hook that Codex
    does not list exactly, has disabled, or does not trust. Empty: all run."""
    specs = launch_specs(flags)
    if not specs:
        return ["missing:launch-hooks"]
    _found, problems = _problems(list_hooks(flags, cwd=cwd, executable=executable, env=env), specs)
    return problems


def _key_path(key: str, leaf: str = "trusted_hash") -> str:
    escaped = str(key).replace("\\", "\\\\").replace('"', '\\"')
    return f'hooks.state."{escaped}".{leaf}'


def _listed(server: "_AppServer", folder: str) -> list[dict[str, Any]]:
    listed = server.call("hooks/list", {"cwds": [folder]}) or {}
    return [
        dict(hook)
        for row in (listed.get("data") or [] if isinstance(listed, Mapping) else [])
        for hook in (row.get("hooks") or [] if isinstance(row, Mapping) else [])
        if isinstance(hook, Mapping)
    ]


def trust_holdspeak_hooks(
    flags: Sequence[str], *, cwd: Optional[str] = None, executable: str = "codex",
    env: Optional[Mapping[str, str]] = None, hooks_json: Optional[Path] = None,
    template: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Trust and enable EXACTLY HoldSpeak's Codex hooks: the launch's
    session-flag hooks (``flags``) and the rider entries of ``hooks_json``
    that equal ``template``. Anything else, a look-alike included, is left
    alone. Writes through Codex's ``config/batchWrite`` and lists again to
    prove it. Returns ``{"trusted", "enabled", "already", "untrusted"}``;
    ``untrusted`` names what still keeps a hook from running."""
    from .hooks import codex_hook_template

    specs = launch_specs(flags)
    if hooks_json is not None:
        specs += installed_specs(Path(hooks_json), template or codex_hook_template())
    folder = str(cwd or Path.home())
    with _AppServer(flags, cwd=folder, executable=executable, env=env) as server:
        found, _problems_before = _problems(_listed(server, folder), specs)
        edits: list[dict[str, Any]] = []
        trusted: list[str] = []
        enabled: list[str] = []
        for _spec, hook in found:
            key = str(hook["key"])
            if hook.get("trustStatus") != TRUSTED and str(hook.get("currentHash") or "").startswith("sha256:"):
                edits.append({"keyPath": _key_path(key), "value": str(hook["currentHash"]), "mergeStrategy": "upsert"})
                trusted.append(key)
            if hook.get("enabled") is False:
                edits.append({"keyPath": _key_path(key, "enabled"), "value": True, "mergeStrategy": "upsert"})
                enabled.append(key)
        if edits:
            server.call("config/batchWrite", {"edits": edits, "reloadUserConfig": False})
        _found_after, after = _problems(_listed(server, folder), specs)
    return {
        "trusted": trusted, "enabled": enabled,
        "already": len(found) - len(set(trusted) | set(enabled)),
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
    "installed_specs",
    "launch_specs",
    "list_hooks",
    "trust_holdspeak_hooks",
    "trust_stamp_matches",
    "untrusted_launch_hooks",
    "write_trust_stamp",
]
