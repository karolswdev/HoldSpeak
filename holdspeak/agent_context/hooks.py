"""Claude/Codex hook templates + tmux detection for `agent_context` (HS-34-03)."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from typing import Any, Mapping

from ._common import _optional_str


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
            "Stop": [
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
            "Stop": [
                {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
            ],
        }
    }


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
