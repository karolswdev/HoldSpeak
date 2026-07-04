"""Claude/Codex hook templates + tmux detection for `agent_context` (HS-34-03)."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping

from ._common import _optional_str


#: Default hook-config destinations per agent (HSM-17-02 install ergonomics).
AGENT_HOOK_SETTINGS_PATHS: dict[str, str] = {
    "claude": "~/.claude/settings.json",
    "codex": "~/.codex/hooks.json",
}


def detect_tmux_context(
    payload: Mapping[str, Any] | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return tmux pane metadata visible to an agent hook process."""

    raw = dict(payload or {})
    source_env = env if env is not None else os.environ
    pane = _optional_str(raw.get("tmux_pane")) or _optional_str(source_env.get("TMUX_PANE"))
    if not pane:
        return {}
    context = {"tmux_pane": pane}
    display = _read_tmux_display(pane, env=source_env)
    if display:
        context.update(display)
    else:
        for key in ("tmux_session", "tmux_window", "tmux_pane_index", "tmux_pane_current_path"):
            value = _optional_str(raw.get(key))
            if value:
                context[key] = value
    return context


def claude_hook_template(*, capture_messages: bool = False) -> dict[str, Any]:
    command = _agent_hook_command("claude", capture_messages=capture_messages)
    return {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|resume|clear|compact",
                    "hooks": [{"type": "command", "command": command, "timeout": 5}],
                }
            ],
            "CwdChanged": [
                {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
            ],
            "UserPromptSubmit": [
                {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
            ],
            # HSM-17-02: the live lifecycle. Notification carries the blocking
            # ask (permission prompts, "waiting for your input") -> waiting;
            # PostToolUse is the working heartbeat (bounded matcher so a spawn
            # happens per meaningful tool, not per read); SessionEnd tombstones.
            "Notification": [
                {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
            ],
            "PostToolUse": [
                {
                    "matcher": "Bash|Edit|Write|Task",
                    "hooks": [{"type": "command", "command": command, "timeout": 5}],
                }
            ],
            "Stop": [
                {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
            ],
            "SessionEnd": [
                {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
            ],
        }
    }


def codex_hook_template(*, capture_messages: bool = False) -> dict[str, Any]:
    command = _agent_hook_command("codex", capture_messages=capture_messages)
    return {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|resume|clear",
                    "hooks": [{"type": "command", "command": command, "timeout": 5}],
                }
            ],
            "UserPromptSubmit": [
                {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
            ],
            "PreToolUse": [
                {
                    "matcher": "Bash|apply_patch|Edit|Write",
                    "hooks": [{"type": "command", "command": command, "timeout": 5}],
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "Bash|apply_patch|Edit|Write",
                    "hooks": [{"type": "command", "command": command, "timeout": 5}],
                }
            ],
            "Notification": [
                {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
            ],
            "Stop": [
                {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
            ],
            "SessionEnd": [
                {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
            ],
        }
    }


#: Substring identifying OUR hook entries inside a user's settings, so the
#: installer can be idempotent and the uninstaller surgical (HSM-17-02).
AGENT_HOOK_COMMAND_MARKER = "agent-hook ingest"


def install_agent_hooks(
    settings_path: "Path",
    template: Mapping[str, Any],
) -> dict[str, Any]:
    """Merge our hook template into a Claude/Codex settings file, idempotently.

    Foreign hooks and unrelated settings are preserved byte-for-byte at the
    JSON level. Our own prior entries (identified by `AGENT_HOOK_COMMAND_MARKER`
    in the command) are replaced, so re-running install — with or without
    `--capture-messages` — converges instead of stacking duplicates. Returns
    a summary: {"path", "installed_events", "created_file"}.
    """
    settings, created = _read_settings(settings_path)
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        settings["hooks"] = hooks

    template_hooks = template.get("hooks")
    installed_events: list[str] = []
    if isinstance(template_hooks, Mapping):
        for event, our_entries in template_hooks.items():
            existing = hooks.get(event)
            existing_list = existing if isinstance(existing, list) else []
            foreign = [e for e in existing_list if not _is_our_hook_entry(e)]
            hooks[event] = foreign + [dict(entry) for entry in our_entries]
            installed_events.append(str(event))

    _write_settings(settings_path, settings)
    return {
        "path": str(settings_path),
        "installed_events": installed_events,
        "created_file": created,
    }


def uninstall_agent_hooks(settings_path: "Path") -> dict[str, Any]:
    """Remove OUR hook entries from a settings file, preserving everything else.

    Event lists that become empty are dropped; an empty `hooks` object is
    dropped too. A missing file is a no-op. Returns
    {"path", "removed_events", "file_missing"}.
    """
    if not settings_path.is_file():
        return {"path": str(settings_path), "removed_events": [], "file_missing": True}
    settings, _ = _read_settings(settings_path)
    hooks = settings.get("hooks")
    removed_events: list[str] = []
    if isinstance(hooks, dict):
        for event in list(hooks.keys()):
            entries = hooks.get(event)
            if not isinstance(entries, list):
                continue
            kept = [e for e in entries if not _is_our_hook_entry(e)]
            if len(kept) != len(entries):
                removed_events.append(str(event))
            if kept:
                hooks[event] = kept
            else:
                del hooks[event]
        if not hooks:
            del settings["hooks"]
    _write_settings(settings_path, settings)
    return {
        "path": str(settings_path),
        "removed_events": removed_events,
        "file_missing": False,
    }


def _is_our_hook_entry(entry: Any) -> bool:
    if not isinstance(entry, Mapping):
        return False
    inner = entry.get("hooks")
    if not isinstance(inner, list):
        return False
    for hook in inner:
        if isinstance(hook, Mapping) and AGENT_HOOK_COMMAND_MARKER in str(hook.get("command") or ""):
            return True
    return False


def _read_settings(settings_path: "Path") -> tuple[dict[str, Any], bool]:
    if settings_path.is_file():
        try:
            loaded = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"{settings_path} is not readable JSON ({exc}); refusing to rewrite it"
            ) from exc
        if not isinstance(loaded, dict):
            raise ValueError(f"{settings_path} does not contain a JSON object; refusing to rewrite it")
        return loaded, False
    return {}, True


def _write_settings(settings_path: "Path", settings: Mapping[str, Any]) -> None:
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _agent_hook_command(agent: str, *, capture_messages: bool = False) -> str:
    executable = shutil.which("holdspeak") or "holdspeak"
    capture = " --capture-messages" if capture_messages else ""
    return f"{shlex.quote(executable)} agent-hook ingest --agent {agent}{capture}"


def _read_tmux_display(pane: str, *, env: Mapping[str, str]) -> dict[str, str]:
    if shutil.which("tmux") is None:
        return {}
    tmux_env = os.environ.copy()
    tmux_env.update({str(key): str(value) for key, value in env.items()})
    try:
        completed = subprocess.run(
            [
                "tmux",
                "display-message",
                "-p",
                "-t",
                pane,
                "#{session_name}\t#{window_index}\t#{pane_index}\t#{pane_current_path}",
            ],
            capture_output=True,
            text=True,
            timeout=0.5,
            check=False,
            env=tmux_env,
        )
    except Exception:
        return {}
    if completed.returncode != 0:
        return {}
    parts = completed.stdout.rstrip("\n").split("\t")
    if len(parts) < 4:
        return {}
    return {
        "tmux_session": parts[0],
        "tmux_window": parts[1],
        "tmux_pane_index": parts[2],
        "tmux_pane_current_path": parts[3],
    }
