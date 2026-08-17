"""UI, hotkey, and voice-macro configuration (HS-117-12).

Extracted from the monolithic ``holdspeak/config.py``.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..errors import ConfigError


@dataclass
class HotkeyConfig:
    """Hotkey configuration."""
    key: str = "alt_r"  # pynput key name
    display: str = "⌥R"  # Display string for UI


@dataclass
class UIConfig:
    """UI configuration."""
    show_audio_meter: bool = True
    history_lines: int = 10
    theme: str = "dark"  # dark, light, dracula, monokai
    desk_sounds: bool = True  # HS-135-12: mechanical sound palette, ON by default


# HS-52-02: voice command macros. A user maps a spoken keyword to a deterministic
# action; speaking the keyword fires the action instead of typing. The kinds map to
# the user's request: open a website, open/launch an app, run a shell command, type a
# snippet. OFF by default.
_KNOWN_MACRO_ACTION_KINDS = ("open_url", "launch_app", "shell", "type_text")


class VoiceMacroError(ConfigError):
    """Raised when a voice command macro fails validation (HS-52-02)."""

    code: str = "VOICE_MACRO_ERROR"


@dataclass
class VoiceMacroAction:
    """What a macro does: one deterministic action ``kind`` + its single ``payload``.

    ``kind`` is one of ``open_url`` / ``launch_app`` / ``shell`` / ``type_text``;
    ``payload`` is that kind's single value (a URL, an app name or path, a shell
    command, or the snippet text). The transcriber never composes this -- the user
    configures it, which is the consent the dispatcher acts on.
    """

    kind: str
    payload: str = ""

    def __post_init__(self) -> None:
        kind = str(self.kind or "").strip().lower()
        if kind not in _KNOWN_MACRO_ACTION_KINDS:
            raise VoiceMacroError(
                f"unknown voice macro action kind {self.kind!r}; "
                f"known kinds are {list(_KNOWN_MACRO_ACTION_KINDS)}"
            )
        self.kind = kind
        self.payload = str(self.payload or "")
        if not self.payload.strip():
            raise VoiceMacroError(f"voice macro action {kind!r} needs a non-empty payload")

    def preview(self) -> str:
        """The one plain-language line of exactly what this fires.

        Single source of truth so the card, the editor, and any audit read identically
        (design $10). Keep these strings in lockstep with the UI.
        """
        if self.kind == "open_url":
            return f"opens {self.payload}"
        if self.kind == "launch_app":
            return f"launches {self.payload}"
        if self.kind == "shell":
            return f"runs: {self.payload}"
        if self.kind == "type_text":
            return f"types: {self.payload}"
        return self.payload


@dataclass
class VoiceMacro:
    """A spoken keyword mapped to a deterministic action (HS-52-02)."""

    keyword: str
    action: VoiceMacroAction

    def __post_init__(self) -> None:
        if isinstance(self.action, dict):
            self.action = VoiceMacroAction(
                **{k: v for k, v in self.action.items() if k in {"kind", "payload"}}
            )
        elif not isinstance(self.action, VoiceMacroAction):
            raise VoiceMacroError("voice macro action must be an object")
        keyword = str(self.keyword or "").strip()
        if not keyword:
            raise VoiceMacroError("voice macro keyword must not be empty")
        self.keyword = keyword

    def matches(self, transcript: str) -> bool:
        """Deterministic whole-utterance match: the normalized transcript equals the
        normalized keyword (case-folded, trimmed). Selecting which macro, never
        composing one. The dispatcher (HS-52-04) uses this."""
        return _normalize_macro_keyword(transcript) == _normalize_macro_keyword(self.keyword)


def _normalize_macro_keyword(text: str) -> str:
    return str(text or "").strip().casefold().rstrip(".!?,")


@dataclass
class MacrosConfig:
    """Voice command macros (HS-52-02). OFF by default, byte-identical when off."""

    enabled: bool = False
    items: list[VoiceMacro] = field(default_factory=list)

    def __post_init__(self) -> None:
        coerced: list[VoiceMacro] = []
        for raw in self.items:
            if isinstance(raw, VoiceMacro):
                coerced.append(raw)
            elif isinstance(raw, dict):
                coerced.append(
                    VoiceMacro(**{k: v for k, v in raw.items() if k in {"keyword", "action"}})
                )
            else:
                raise VoiceMacroError("each voice macro must be an object")
        self.items = coerced
        self.enabled = bool(self.enabled)


# Key mapping from config names to pynput keys
KEY_MAP = {
    "alt_r": "Key.alt_r",
    "alt_l": "Key.alt_l",
    "ctrl_r": "Key.ctrl_r",
    "ctrl_l": "Key.ctrl_l",
    "cmd_r": "Key.cmd_r",
    "cmd_l": "Key.cmd_l",
    "shift_r": "Key.shift_r",
    "shift_l": "Key.shift_l",
    "caps_lock": "Key.caps_lock",
    "fn": "Key.fn",
    "f1": "Key.f1",
    "f2": "Key.f2",
    "f3": "Key.f3",
    "f4": "Key.f4",
    "f5": "Key.f5",
    "f6": "Key.f6",
    "f7": "Key.f7",
    "f8": "Key.f8",
    "f9": "Key.f9",
    "f10": "Key.f10",
    "f11": "Key.f11",
    "f12": "Key.f12",
}

# Display names for keys
KEY_DISPLAY = {
    "alt_r": "⌥R",
    "alt_l": "⌥L",
    "ctrl_r": "⌃R",
    "ctrl_l": "⌃L",
    "cmd_r": "⌘R",
    "cmd_l": "⌘L",
    "shift_r": "⇧R",
    "shift_l": "⇧L",
    "caps_lock": "⇪",
    "fn": "fn",
    "f1": "F1",
    "f2": "F2",
    "f3": "F3",
    "f4": "F4",
    "f5": "F5",
    "f6": "F6",
    "f7": "F7",
    "f8": "F8",
    "f9": "F9",
    "f10": "F10",
    "f11": "F11",
    "f12": "F12",
}


def get_available_keys() -> list[tuple[str, str]]:
    """Get list of available hotkeys as (key_name, display_name) tuples."""
    return [(k, KEY_DISPLAY.get(k, k)) for k in KEY_MAP.keys()]
