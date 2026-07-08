"""The agent hook seam (WLA-14-02).

`dw hook install|uninstall|status|emit` — the rails' own push
channel. Agent CLIs (claude, codex) get a hook command installed
into their user-level settings; on SessionStart / Notification /
Stop / SessionEnd the hook appends one line to an append-only
JSONL stream that mission-control clients drain by byte offset.
Contract: docs/absorption-ccgram.md §1 (the installer discipline
and file shapes follow ccgram v4.3.5, MIT, alexei-led — verified
against real agents there so we don't rediscover them here).

Consent stance, enforced in code exactly like the rail event log
(§3 precedent): `emit` writes ONLY whitelisted keys — timestamps,
agent, event name, session id, cwd. Never the notification
message, never prompt or transcript content. And the hook never
breaks the agent: emit swallows everything and exits 0.

The hook command deliberately reads no interface configuration —
it resolves its output path from `DW_AGENT_EVENTS` or the default,
and nothing else. `DW_HOOK_QUIET=1` in the environment suppresses
emission entirely (the nested-session guard: harness-spawned
observer agents set it so they never double-fire).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

HOOK_EVENTS = ("SessionStart", "Notification", "Stop", "SessionEnd")
# SessionEnd must never delay an exiting agent; the rest are fast
# appends under a 5 s timeout (the ccgram-proven table).
ASYNC_EVENTS = frozenset({"SessionEnd"})
HOOK_TIMEOUT_SECONDS = 5

QUIET_ENV = "DW_HOOK_QUIET"
EVENTS_PATH_ENV = "DW_AGENT_EVENTS"

# The only payload keys emit may copy from the agent's hook input.
ALLOWED_PAYLOAD_KEYS = ("session_id", "cwd")
_MAX_VALUE_CHARS = 300

_CODEX_FLAG_RE = re.compile(r"^\s*codex_hooks\s*=\s*(\S+)", re.MULTILINE)


def default_events_path(env: dict | None = None) -> Path:
    env = os.environ if env is None else env
    override = str(env.get(EVENTS_PATH_ENV) or "").strip()
    if override:
        return Path(override)
    return (
        Path.home() / ".config" / "delivery-workbench" / "agent-events.jsonl"
    )


def claude_settings_path() -> Path:
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if config_dir:
        return Path(config_dir).expanduser() / "settings.json"
    return Path.home() / ".claude" / "settings.json"


def codex_hooks_path() -> Path:
    return Path.home() / ".codex" / "hooks.json"


def codex_config_path() -> Path:
    return Path.home() / ".codex" / "config.toml"


def hook_command(agent: str) -> str:
    """The command line installed into the agent's settings.

    The RUNNING dw first — the vendored rails that executed
    `hook install` are guaranteed to know the verb; an installed
    global `dw` may predate it. `shutil.which` is the fallback for
    a packaged install run outside any checkout."""
    running = Path(sys.argv[0]).resolve()
    if running.name == "dw" and running.is_file():
        dw = str(running)
    else:
        dw = shutil.which("dw") or str(running)
    return f'"{dw}" hook emit --agent {agent}'


def _is_dw_hook_command(command: str, agent: str) -> bool:
    return "hook emit" in command and f"--agent {agent}" in f"{command} "


# ---------------------------------------------------------------- emit


def _clean(value: object) -> str:
    return str(value or "")[:_MAX_VALUE_CHARS]


def emit(
    agent: str,
    event: str,
    stdin_text: str = "",
    events_path: Path | None = None,
    env: dict | None = None,
) -> int:
    """Append one whitelisted line. Never raises, always exits 0 —
    a hook must not be able to break the agent it observes."""
    try:
        env = os.environ if env is None else env
        if str(env.get(QUIET_ENV) or "").strip():
            return 0
        if event not in HOOK_EVENTS:
            return 0
        try:
            payload = json.loads(stdin_text) if stdin_text.strip() else {}
        except (json.JSONDecodeError, ValueError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        line = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "agent": _clean(agent),
            "event": event,
        }
        for key in ALLOWED_PAYLOAD_KEYS:
            if key in payload:
                line[key] = _clean(payload[key])
        path = events_path or default_events_path(env)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            try:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            except (ImportError, OSError):
                pass  # locking is best-effort; the append is one write
            handle.write(json.dumps(line, sort_keys=True) + "\n")
        return 0
    except Exception:
        return 0


# ------------------------------------------------------------- install


def _load_settings(path: Path) -> dict | None:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"dw hook: cannot read {path}: {exc}", file=sys.stderr)
        return None
    return parsed if isinstance(parsed, dict) else None


def _write_settings(path: Path, settings: dict) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".dw-tmp")
        tmp.write_text(
            json.dumps(settings, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, path)
        return True
    except OSError as exc:
        print(f"dw hook: cannot write {path}: {exc}", file=sys.stderr)
        return False


def _event_has_ours(settings: dict, event: str, agent: str) -> bool:
    for group in settings.get("hooks", {}).get(event, []) or []:
        if not isinstance(group, dict):
            continue
        for entry in group.get("hooks", []) or []:
            if isinstance(entry, dict) and _is_dw_hook_command(
                str(entry.get("command") or ""), agent
            ):
                return True
    return False


def _hook_entry(agent: str) -> dict:
    entry: dict = {
        "type": "command",
        "command": hook_command(agent),
        "timeout": HOOK_TIMEOUT_SECONDS,
    }
    return entry


def install_agent(
    agent: str,
    settings_path: Path | None = None,
    codex_config: Path | None = None,
) -> int:
    """Idempotent install into the agent's user settings file."""
    if agent == "claude":
        path = settings_path or claude_settings_path()
    elif agent == "codex":
        if _ensure_codex_flag(codex_config) != 0:
            return 1
        path = settings_path or codex_hooks_path()
    else:
        print(f"dw hook: unsupported agent {agent!r}", file=sys.stderr)
        return 1
    settings = _load_settings(path)
    if settings is None:
        return 1
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        print(f"dw hook: {path} hooks must be an object", file=sys.stderr)
        return 1
    installed = already = 0
    for event in HOOK_EVENTS:
        if _event_has_ours(settings, event, agent):
            already += 1
            continue
        entry = _hook_entry(agent)
        if event in ASYNC_EVENTS:
            entry["async"] = True
        hooks.setdefault(event, []).append({"hooks": [entry]})
        installed += 1
    if installed and not _write_settings(path, settings):
        return 1
    print(
        f"dw hook: {agent} — {installed} installed, {already} already "
        f"present in {path}"
    )
    return 0


def uninstall_agent(agent: str, settings_path: Path | None = None) -> int:
    """Remove exactly our entries; everything else untouched."""
    path = settings_path or (
        claude_settings_path() if agent == "claude" else codex_hooks_path()
    )
    settings = _load_settings(path)
    if not settings:
        print(f"dw hook: nothing installed for {agent}")
        return 0
    removed = 0
    hooks = settings.get("hooks", {})
    for event in list(hooks.keys() if isinstance(hooks, dict) else []):
        groups = hooks.get(event) or []
        kept_groups = []
        for group in groups:
            if not isinstance(group, dict):
                kept_groups.append(group)
                continue
            kept = [
                entry
                for entry in group.get("hooks", []) or []
                if not (
                    isinstance(entry, dict)
                    and _is_dw_hook_command(
                        str(entry.get("command") or ""), agent
                    )
                )
            ]
            removed += len(group.get("hooks", []) or []) - len(kept)
            if kept or not group.get("hooks"):
                kept_groups.append({**group, "hooks": kept})
        hooks[event] = [g for g in kept_groups if g.get("hooks")]
        if not hooks[event]:
            del hooks[event]
    if removed and not _write_settings(path, settings):
        return 1
    print(f"dw hook: {agent} — {removed} removed from {path}")
    return 0


def status_agent(agent: str, settings_path: Path | None = None) -> dict:
    path = settings_path or (
        claude_settings_path() if agent == "claude" else codex_hooks_path()
    )
    settings = _load_settings(path) or {}
    return {
        "agent": agent,
        "settings": str(path),
        "events": {
            event: _event_has_ours(settings, event, agent)
            for event in HOOK_EVENTS
        },
    }


def _ensure_codex_flag(config_path: Path | None = None) -> int:
    """`codex_hooks = true` under [features]; an explicit false is
    the owner's opt-out and is respected, not overwritten."""
    path = config_path or codex_config_path()
    text = ""
    if path.exists():
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"dw hook: cannot read {path}: {exc}", file=sys.stderr)
            return 1
    match = _CODEX_FLAG_RE.search(text)
    if match:
        if match.group(1).strip().lower() in ("false", '"false"'):
            print(
                f"dw hook: codex_hooks is explicitly false in {path}; "
                "respecting the opt-out",
                file=sys.stderr,
            )
            return 1
        return 0
    if "[features]" in text:
        text = text.replace("[features]", "[features]\ncodex_hooks = true", 1)
    else:
        text = text.rstrip() + ("\n\n" if text.strip() else "") + "[features]\ncodex_hooks = true\n"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        print(f"dw hook: cannot write {path}: {exc}", file=sys.stderr)
        return 1
    return 0
