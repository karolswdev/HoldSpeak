"""Claude/Codex hook templates + tmux detection for `agent_context` (HS-34-03)."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Optional

from ._common import _optional_str


#: Default hook-config destinations per agent (HSM-17-02 install ergonomics).
AGENT_HOOK_SETTINGS_PATHS: dict[str, str] = {
    "claude": "~/.claude/settings.json",
    "codex": "~/.codex/hooks.json",
}
#: The variable that moves each agent's config directory (the agent reads its
#: hooks from there, so install and detect both follow it).
AGENT_CONFIG_DIR_ENV: dict[str, str] = {
    "claude": "CLAUDE_CONFIG_DIR",
    "codex": "CODEX_HOME",
}


def agent_settings_path(
    agent: str,
    *,
    home: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    """The hook settings file the agent reads: its config-dir variable, else the default under *home*.

    The one resolver for ``holdspeak agent-hook install``, the onboarding
    install and the onboarding detect.
    """
    source_env = os.environ if env is None else env
    default = AGENT_HOOK_SETTINGS_PATHS[agent]
    override = str(source_env.get(AGENT_CONFIG_DIR_ENV[agent]) or "").strip()
    if override:
        return Path(override).expanduser() / Path(default).name
    return (home or Path.home()) / default.removeprefix("~/")


def holdspeak_executable() -> str | None:
    """The ``holdspeak`` the hook command runs: on PATH, else beside this interpreter (a venv)."""
    found = shutil.which("holdspeak")
    if found:
        return found
    beside = Path(sys.executable).parent / "holdspeak"
    if beside.is_file() and os.access(beside, os.X_OK):
        return str(beside)
    return None


def hook_command_runs(command: str, *, which: Any = shutil.which) -> bool:
    """True when the executable of a hook command exists and can run."""
    try:
        parts = shlex.split(str(command or ""))
    except ValueError:
        return False
    if not parts:
        return False
    executable = parts[0]
    if os.sep in executable:
        path = Path(executable).expanduser()
        return path.is_file() and os.access(path, os.X_OK)
    return which(executable) is not None


def our_hook_commands(settings: Mapping[str, Any]) -> list[str]:
    """The commands of OUR hook entries in a settings object (marker match)."""
    hooks = settings.get("hooks")
    commands: list[str] = []
    if not isinstance(hooks, Mapping):
        return commands
    for entries in hooks.values():
        for entry in entries if isinstance(entries, list) else []:
            if not _is_our_hook_entry(entry):
                continue
            for hook in entry.get("hooks") or []:
                if isinstance(hook, Mapping) and is_our_hook_command(hook.get("command")):
                    commands.append(str(hook.get("command")))
    return commands


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


#: Environment variables a Story-scoped launcher can set so every hook
#: event from that agent process carries an explicit Story claim
#: (HS-94-04 rider claim). The combined form wins over the pair.
STORY_CLAIM_ENV_REF = "HOLDSPEAK_STORY_REF"
STORY_CLAIM_ENV_PROJECT = "HOLDSPEAK_STORY_PROJECT"
STORY_CLAIM_ENV_STORY = "HOLDSPEAK_STORY_ID"

_STORY_CLAIM_MAX_CHARS = 128


def _claim_part(value: Any) -> str | None:
    text = _optional_str(value)
    if text is None or len(text) > _STORY_CLAIM_MAX_CHARS:
        return None
    return text


def detect_story_claim(
    payload: Mapping[str, Any] | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """The Story identity a rider/hook process explicitly carries
    (HS-94-04). Returns ``{"project", "story_id"}`` or ``{}``.

    Sources, most explicit first:

    1. ``payload["story_ref"]`` — a typed launch payload
       (``{"project": ..., "story_id": ...}``);
    2. ``payload["story_project"]`` + ``payload["story_id"]``;
    3. env ``HOLDSPEAK_STORY_REF`` (``<project>/<story-id>`` or
       ``<project>:<story-id>``) — what a Story-scoped launcher exports;
    4. env ``HOLDSPEAK_STORY_PROJECT`` + ``HOLDSPEAK_STORY_ID``.

    Both parts are treated as opaque labels (§3): bounded, stripped,
    never parsed further. Anything incomplete detects as no claim —
    a guessed half-identity is worse than none.
    """
    raw = dict(payload or {})
    source_env = env if env is not None else os.environ

    story_ref = raw.get("story_ref")
    if isinstance(story_ref, Mapping):
        project = _claim_part(story_ref.get("project"))
        story_id = _claim_part(story_ref.get("story_id") or story_ref.get("story"))
        if project and story_id:
            return {"project": project, "story_id": story_id}

    project = _claim_part(raw.get("story_project"))
    story_id = _claim_part(raw.get("story_id"))
    if project and story_id:
        return {"project": project, "story_id": story_id}

    combined = _claim_part(source_env.get(STORY_CLAIM_ENV_REF))
    if combined:
        for separator in ("/", ":"):
            if separator in combined:
                head, _, tail = combined.partition(separator)
                project = _claim_part(head)
                story_id = _claim_part(tail)
                if project and story_id:
                    return {"project": project, "story_id": story_id}
                break

    project = _claim_part(source_env.get(STORY_CLAIM_ENV_PROJECT))
    story_id = _claim_part(source_env.get(STORY_CLAIM_ENV_STORY))
    if project and story_id:
        return {"project": project, "story_id": story_id}
    return {}


#: The rider hook's timeout (Conductor R3). A rider event that passes its
#: timeout is lost; ``holdspeak agent-hook ingest`` starts in about 0.1 s
#: (``cli_entry``), but under load or on a cold ``uv run`` it took over 5 s.
RIDER_HOOK_TIMEOUT_SECONDS = 30


def claude_hook_template(*, capture_messages: bool = False) -> dict[str, Any]:
    command = _agent_hook_command("claude", capture_messages=capture_messages)
    return {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|resume|clear|compact",
                    "hooks": [{"type": "command", "command": command, "timeout": RIDER_HOOK_TIMEOUT_SECONDS}],
                }
            ],
            "CwdChanged": [
                {"hooks": [{"type": "command", "command": command, "timeout": RIDER_HOOK_TIMEOUT_SECONDS}]}
            ],
            "UserPromptSubmit": [
                {"hooks": [{"type": "command", "command": command, "timeout": RIDER_HOOK_TIMEOUT_SECONDS}]}
            ],
            # HSM-17-02: the live lifecycle. Notification carries the blocking
            # ask (permission prompts, "waiting for your input") -> waiting;
            # PostToolUse is the working heartbeat (bounded matcher so a spawn
            # happens per meaningful tool, not per read); SessionEnd tombstones.
            "Notification": [
                {"hooks": [{"type": "command", "command": command, "timeout": RIDER_HOOK_TIMEOUT_SECONDS}]}
            ],
            "PostToolUse": [
                {
                    "matcher": "Bash|Edit|Write|Task",
                    "hooks": [{"type": "command", "command": command, "timeout": RIDER_HOOK_TIMEOUT_SECONDS}],
                }
            ],
            "Stop": [
                {"hooks": [{"type": "command", "command": command, "timeout": RIDER_HOOK_TIMEOUT_SECONDS}]}
            ],
            "SessionEnd": [
                {"hooks": [{"type": "command", "command": command, "timeout": RIDER_HOOK_TIMEOUT_SECONDS}]}
            ],
        }
    }


#: Codex CLI's hook events (0.159, observed): Codex has no ``Notification``
#: event. Its approval prompt fires ``PermissionRequest``; the end of a turn
#: (the agent waits for input) fires ``Stop`` with ``last_assistant_message``.
#: SessionEnd timeouts are clamped to 3 s by Codex.
CODEX_SESSION_END_TIMEOUT_SECONDS = 3


def codex_hook_template(
    *, capture_messages: bool = False, gate_command: Optional[str] = None,
) -> dict[str, Any]:
    """Codex's hooks: the rider events, and the tool gate when ``gate_command`` is given.

    ``gate_command`` (``holdspeak gate hook --agent codex``) puts the gate on
    ``PreToolUse`` for ``Bash`` with Claude Code's hold timeout (300 s), so a
    call can wait for the owner; the same command reports the receipt
    (``PostToolUse``) and revokes the session credential (``SessionEnd``).
    A Codex launch passes this template per session (``-c hooks.*``,
    ``coder_gate.codex_spawn_args``); ``agent-hook install`` writes the rider
    template without the gate."""
    from ..coder_gate import HOOK_TIMEOUT_SECONDS

    command = _agent_hook_command("codex", capture_messages=capture_messages)

    def rider(timeout: int = RIDER_HOOK_TIMEOUT_SECONDS) -> dict[str, Any]:
        return {"type": "command", "command": command, "timeout": timeout}

    hooks: dict[str, list[dict[str, Any]]] = {
        "SessionStart": [{"matcher": "startup|resume|clear", "hooks": [rider()]}],
        "UserPromptSubmit": [{"hooks": [rider()]}],
        "PreToolUse": [{"matcher": "Bash|apply_patch|Edit|Write", "hooks": [rider()]}],
        "PermissionRequest": [{"hooks": [rider()]}],
        "PostToolUse": [{"matcher": "Bash|apply_patch|Edit|Write", "hooks": [rider()]}],
        "Stop": [{"hooks": [rider()]}],
        "SessionEnd": [{"hooks": [rider(CODEX_SESSION_END_TIMEOUT_SECONDS)]}],
    }
    if gate_command:
        def gate(timeout: int) -> dict[str, Any]:
            return {"type": "command", "command": gate_command, "timeout": timeout}

        hooks["PreToolUse"].insert(0, {"matcher": "^Bash$", "hooks": [gate(HOOK_TIMEOUT_SECONDS)]})
        hooks["PostToolUse"].insert(0, {"matcher": "^Bash$", "hooks": [gate(15)]})
        hooks["SessionEnd"].insert(0, {"hooks": [gate(CODEX_SESSION_END_TIMEOUT_SECONDS)]})
    return {"hooks": hooks}


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


def is_our_hook_command(command: Any) -> bool:
    """True only for a command ``_agent_hook_command`` writes, exactly:
    ``<holdspeak> agent-hook ingest --agent <claude|codex> [--capture-messages]``.
    A wrapper, an appended command or a comment that carries the words is
    someone else's hook (Astra round 1 on #914)."""
    try:
        parts = shlex.split(str(command or ""))
    except ValueError:
        return False
    if len(parts) not in (5, 6) or os.path.basename(parts[0]) != "holdspeak":
        return False
    if parts[1:4] != ["agent-hook", "ingest", "--agent"] or parts[4] not in AGENT_HOOK_SETTINGS_PATHS:
        return False
    return parts[5:] in ([], ["--capture-messages"]) and shlex.join(parts) == str(command)


def _is_our_hook_entry(entry: Any) -> bool:
    if not isinstance(entry, Mapping):
        return False
    inner = entry.get("hooks")
    if not isinstance(inner, list):
        return False
    return any(isinstance(hook, Mapping) and is_our_hook_command(hook.get("command")) for hook in inner)


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
    executable = holdspeak_executable() or "holdspeak"
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
