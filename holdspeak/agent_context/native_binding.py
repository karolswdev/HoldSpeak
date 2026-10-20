"""Native MCP bindings for the owner's Claude Code and Codex installs.

The agent CLIs own their configuration files.  HoldSpeak asks each CLI to add
or remove its user-scope entry and only reads the resulting file when it
reports readiness.  This keeps foreign servers and settings in the format the
agent owns, while the exact entry written by HoldSpeak is identifiable for a
safe Stop action.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, Callable, Mapping

SERVER_NAME = "holdspeak"
SERVER_COMMAND = "holdspeak-mcp"


class NativeBindingError(Exception):
    """A named failure from a native agent configuration command."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(detail)


def _usable_executable(value: str | os.PathLike[str] | None) -> str | None:
    """Return an executable file path, or ``None`` when the entrypoint is unusable."""

    if not value:
        return None
    try:
        path = Path(value).expanduser()
    except (OSError, ValueError, TypeError):
        return None
    try:
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    except OSError:
        pass
    return None


def resolve_server_command(
    *,
    which: Callable[[str], str | None] = shutil.which,
    python_executable: str | None = None,
) -> str | None:
    """Find the actual HoldSpeak MCP entrypoint used by a native agent.

    A bare ``holdspeak-mcp`` in an agent config only works when the agent
    inherits a PATH containing that command.  The desk can run with a
    different PATH, so prefer a validated PATH result and then the entrypoint
    beside the interpreter that runs this hub.  If neither exists, the caller
    must leave the native config untouched and report the binding as not ready.
    """

    try:
        on_path = _usable_executable(which(SERVER_COMMAND))
    except (OSError, ValueError, TypeError):
        on_path = None
    if on_path:
        return on_path
    interpreter = Path(python_executable or sys.executable).expanduser()
    return _usable_executable(interpreter.parent / SERVER_COMMAND)


def config_path(agent: str, *, home: Path, env: Mapping[str, str]) -> Path:
    """Return the user config file written by the native CLI."""

    if agent == "claude":
        # Claude Code stores user MCP servers in .claude.json.  When the
        # config-dir override is set, the same file lives inside that dir.
        root = Path(str(env.get("CLAUDE_CONFIG_DIR") or home)).expanduser()
        return root / ".claude.json"
    if agent == "codex":
        root = Path(str(env.get("CODEX_HOME") or (home / ".codex"))).expanduser()
        return root / "config.toml"
    raise ValueError(f"unsupported agent: {agent}")


def _claude_entry(path: Path, *, expected_command: str | None) -> tuple[str, dict[str, Any] | None]:
    if not path.is_file():
        return "missing", None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "unreadable", None
    if not isinstance(raw, dict):
        return "unreadable", None
    servers = raw.get("mcpServers")
    if not isinstance(servers, dict) or SERVER_NAME not in servers:
        return "missing", None
    entry = servers.get(SERVER_NAME)
    if not isinstance(entry, dict):
        return "foreign", None
    command = entry.get("command")
    ours = (
        entry.get("type") == "stdio"
        and (command == SERVER_COMMAND or command == expected_command)
        and entry.get("args", []) == []
        and entry.get("env", {}) == {}
        and set(entry) == {"type", "command", "args", "env"}
    )
    return ("installed" if ours else "foreign"), entry


def _codex_entry(path: Path, *, expected_command: str | None) -> tuple[str, dict[str, Any] | None]:
    if not path.is_file():
        return "missing", None
    try:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return "unreadable", None
    servers = raw.get("mcp_servers")
    if not isinstance(servers, dict) or SERVER_NAME not in servers:
        return "missing", None
    entry = servers.get(SERVER_NAME)
    if not isinstance(entry, dict):
        return "foreign", None
    # Codex's own writer emits only the command for this stdio entry.  A
    # same-name server with custom args, env, headers or any other override is
    # another owner's binding and Stop must preserve it.
    command = entry.get("command")
    ours = set(entry) == {"command"} and (command == SERVER_COMMAND or command == expected_command)
    return ("installed" if ours else "foreign"), entry


def _entry_command(entry: Mapping[str, Any] | None) -> str | None:
    value = entry.get("command") if isinstance(entry, Mapping) else None
    return value if isinstance(value, str) and value else None


def binding_state(
    agent: str,
    *,
    home: Path,
    env: Mapping[str, str],
    which: Callable[[str], str | None] = shutil.which,
    python_executable: str | None = None,
) -> dict[str, Any]:
    """Read one native MCP binding without starting an agent process."""

    path = config_path(agent, home=home, env=env)
    expected_command = resolve_server_command(which=which, python_executable=python_executable)
    state, entry = (
        _claude_entry(path, expected_command=expected_command)
        if agent == "claude"
        else _codex_entry(path, expected_command=expected_command)
    )
    command = _entry_command(entry)
    if command == SERVER_COMMAND:
        runnable = resolve_server_command(which=which, python_executable=python_executable) is not None
    elif command == expected_command:
        runnable = _usable_executable(command) is not None
    else:
        runnable = False
    return {
        "state": state,
        "path": str(path),
        "entry": entry,
        "command": command,
        "runnable": runnable,
    }


def _argv(agent: str, action: str, *, server_command: str | None = None) -> list[str]:
    if action == "install":
        command = server_command or SERVER_COMMAND
        if agent == "claude":
            return ["claude", "mcp", "add", "--scope", "user", SERVER_NAME, command]
        if agent == "codex":
            return ["codex", "mcp", "add", SERVER_NAME, "--", command]
    elif action == "remove":
        if agent == "claude":
            return ["claude", "mcp", "remove", "--scope", "user", SERVER_NAME]
        if agent == "codex":
            return ["codex", "mcp", "remove", SERVER_NAME]
    raise ValueError(f"unsupported native binding: {agent}/{action}")


def _run_native(
    agent: str,
    action: str,
    *,
    home: Path,
    env: Mapping[str, str],
    which: Callable[[str], str | None],
    server_command: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    executable = which(agent)
    if not executable:
        raise NativeBindingError(f"{agent}_not_installed", f"{agent.title()} is not installed.")
    command = [executable, *_argv(agent, action, server_command=server_command)[1:]]
    run_env = dict(env)
    run_env["HOME"] = str(home)
    try:
        completed = runner(
            command,
            cwd=str(home),
            env=run_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise NativeBindingError(f"mcp_{action}_failed", f"Could not update {agent} MCP settings: {exc}.") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "the native command failed").strip().splitlines()[-1]
        raise NativeBindingError(f"mcp_{action}_failed", f"Could not update {agent} MCP settings: {detail}.")
    return {"argv": command, "stdout": (completed.stdout or "").strip()}


def install_binding(
    agent: str,
    *,
    home: Path,
    env: Mapping[str, str],
    which: Callable[[str], str | None],
    python_executable: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    """Install the exact HoldSpeak entry, refusing a foreign same-name entry."""

    current = binding_state(agent, home=home, env=env, which=which, python_executable=python_executable)
    if current["state"] == "installed" and current["runnable"]:
        return {**current, "changed": False}
    if current["state"] == "foreign":
        raise NativeBindingError("mcp_name_taken", f"The {agent} MCP entry named holdspeak belongs to another setup.")
    if current["state"] == "unreadable":
        raise NativeBindingError("mcp_config_unreadable", f"HoldSpeak cannot read {current['path']}. Fix it and try again.")
    server_command = resolve_server_command(which=which, python_executable=python_executable)
    if server_command is None:
        raise NativeBindingError(
            "mcp_executable_missing",
            "HoldSpeak cannot find a runnable holdspeak-mcp command. Install it and try again.",
        )
    _run_native(
        agent, "install", home=home, env=env, which=which,
        server_command=server_command, runner=runner,
    )
    after = binding_state(agent, home=home, env=env, which=which, python_executable=python_executable)
    if after["state"] != "installed" or not after["runnable"] or after["command"] != server_command:
        raise NativeBindingError("mcp_binding_missing", f"{agent.title()} did not save the HoldSpeak MCP entry.")
    return {**after, "changed": True}


def remove_binding(
    agent: str,
    *,
    home: Path,
    env: Mapping[str, str],
    which: Callable[[str], str | None],
    python_executable: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    """Remove only the exact HoldSpeak entry; leave a foreign entry in place."""

    current = binding_state(agent, home=home, env=env, which=which, python_executable=python_executable)
    if current["state"] in {"missing", "foreign"}:
        return {**current, "changed": False}
    if current["state"] == "unreadable":
        raise NativeBindingError("mcp_config_unreadable", f"HoldSpeak cannot read {current['path']}. Fix it and try again.")
    _run_native(agent, "remove", home=home, env=env, which=which, runner=runner)
    after = binding_state(agent, home=home, env=env, which=which, python_executable=python_executable)
    if after["state"] != "missing":
        raise NativeBindingError("mcp_remove_incomplete", f"The {agent} HoldSpeak MCP entry is still present.")
    return {**after, "changed": True}


__all__ = [
    "NativeBindingError", "SERVER_COMMAND", "SERVER_NAME", "binding_state", "config_path",
    "install_binding", "remove_binding", "resolve_server_command",
]
