"""Target-profile detection for dictation delivery context.

Project context answers "what repo am I working in?". Target context answers
"where is this text about to be inserted?". The first pass is deliberately
deterministic: classify app/process/window hints into stable profile IDs and
fall back to `unknown` when the OS will not expose active-window details.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any, Mapping

KNOWN_TARGET_PROFILES = {
    "claude_code",
    "codex_cli",
    "terminal_shell",
    "browser",
    "editor",
    "chat",
    "unknown",
}


@dataclass(frozen=True)
class TargetProfile:
    id: str
    label: str
    confidence: float
    source: str
    app_name: str | None = None
    process_name: str | None = None
    window_title: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "confidence": self.confidence,
            "source": self.source,
            "app_name": self.app_name,
            "process_name": self.process_name,
            "window_title": self.window_title,
            "details": dict(self.details),
        }


def detect_target_profile(hints: Mapping[str, Any] | None = None) -> TargetProfile:
    """Classify active-app hints into a stable target profile."""

    raw = dict(hints or {})
    explicit = _clean(raw.get("profile") or raw.get("target_profile"))
    if explicit in KNOWN_TARGET_PROFILES:
        return _profile(
            explicit,
            1.0,
            "explicit",
            raw,
            details={"matched": "explicit"},
        )

    app = _clean(raw.get("app") or raw.get("app_name") or raw.get("application"))
    process = _clean(raw.get("process") or raw.get("process_name") or raw.get("command"))
    title = _clean(raw.get("title") or raw.get("window_title"))
    haystack = " ".join(part for part in (app, process, title) if part)

    if "codex" in haystack:
        return _profile("codex_cli", 0.92, "hints", raw, details={"matched": "codex"})
    if "claude" in haystack and ("code" in haystack or _is_terminalish(app, process)):
        return _profile("claude_code", 0.92, "hints", raw, details={"matched": "claude"})
    if _is_chat(app, process, title):
        return _profile("chat", 0.85, "hints", raw, details={"matched": "chat_app"})
    if _is_editor(app, process):
        return _profile("editor", 0.82, "hints", raw, details={"matched": "editor_app"})
    if _is_browser(app, process):
        return _profile("browser", 0.78, "hints", raw, details={"matched": "browser_app"})
    if _is_terminalish(app, process):
        return _profile("terminal_shell", 0.74, "hints", raw, details={"matched": "terminal_app"})

    return _profile("unknown", 0.0, "hints" if raw else "none", raw, details={})


def collect_active_target_hints() -> dict[str, Any]:
    """Best-effort active-window hints; returns `{}` when unavailable."""

    system = platform.system().lower()
    try:
        if system == "darwin":
            return _collect_macos_hints()
        if system == "linux":
            return _collect_linux_x11_hints()
    except Exception:
        return {}
    return {}


def detect_active_target_profile() -> TargetProfile:
    return detect_target_profile(collect_active_target_hints())


def _profile(
    profile_id: str,
    confidence: float,
    source: str,
    raw: Mapping[str, Any],
    *,
    details: dict[str, Any],
) -> TargetProfile:
    labels = {
        "claude_code": "Claude Code",
        "codex_cli": "Codex CLI",
        "terminal_shell": "Terminal shell",
        "browser": "Browser",
        "editor": "Editor",
        "chat": "Chat",
        "unknown": "Unknown",
    }
    return TargetProfile(
        id=profile_id,
        label=labels[profile_id],
        confidence=confidence,
        source=source,
        app_name=_optional_raw(raw, "app", "app_name", "application"),
        process_name=_optional_raw(raw, "process", "process_name", "command"),
        window_title=_optional_raw(raw, "title", "window_title"),
        details=details,
    )


def _collect_macos_hints() -> dict[str, Any]:
    if shutil.which("osascript") is None:
        return {}
    script = (
        'tell application "System Events"\n'
        '  set frontApp to first application process whose frontmost is true\n'
        '  set appName to name of frontApp\n'
        '  set windowTitle to ""\n'
        '  try\n'
        '    set windowTitle to name of front window of frontApp\n'
        '  end try\n'
        '  return appName & "\n" & windowTitle\n'
        'end tell'
    )
    completed = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=0.5,
        check=False,
    )
    if completed.returncode != 0:
        return {}
    parts = completed.stdout.splitlines()
    return {
        "app_name": parts[0].strip() if parts else "",
        "window_title": parts[1].strip() if len(parts) > 1 else "",
        "platform": "darwin",
    }


def _collect_linux_x11_hints() -> dict[str, Any]:
    if shutil.which("xdotool") is None:
        return {}
    window_id = _run_text(["xdotool", "getactivewindow"])
    if not window_id:
        return {}
    title = _run_text(["xdotool", "getwindowname", window_id])
    pid = _run_text(["xdotool", "getwindowpid", window_id])
    process = _run_text(["ps", "-p", pid, "-o", "comm="]) if pid else ""
    return {
        "window_title": title,
        "process_name": process,
        "pid": pid,
        "platform": "linux-x11",
    }


def _run_text(cmd: list[str]) -> str:
    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=0.5,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _clean(value: Any) -> str:
    return str(value or "").strip().lower()


def _optional_raw(raw: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _is_terminalish(app: str, process: str) -> bool:
    terms = (
        "terminal",
        "iterm",
        "wezterm",
        "kitty",
        "alacritty",
        "gnome-terminal",
        "konsole",
        "xterm",
        "warp",
        "tabby",
    )
    return any(term in app or term in process for term in terms)


def _is_browser(app: str, process: str) -> bool:
    browsers = ("chrome", "chromium", "firefox", "safari", "edge", "brave", "arc")
    return any(browser in app or browser in process for browser in browsers)


def _is_editor(app: str, process: str) -> bool:
    editors = (
        "cursor",
        "visual studio code",
        "vscode",
        "code",
        "zed",
        "sublime",
        "nvim",
        "vim",
        "emacs",
        "pycharm",
        "webstorm",
    )
    return any(editor in app or editor in process for editor in editors)


def _is_chat(app: str, process: str, title: str) -> bool:
    chat_apps = ("slack", "discord", "teams", "telegram", "signal", "whatsapp")
    return any(chat in app or chat in process or chat in title for chat in chat_apps)
