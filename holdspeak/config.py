"""Configuration management for HoldSpeak."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# Default config location
CONFIG_DIR = Path.home() / ".config" / "holdspeak"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class HotkeyConfig:
    """Hotkey configuration."""
    key: str = "alt_r"  # pynput key name
    display: str = "⌥R"  # Display string for UI


@dataclass
class ModelConfig:
    """Whisper model configuration."""
    name: str = "base"
    # Available: tiny, base, small, medium, large


@dataclass
class UIConfig:
    """UI configuration."""
    show_audio_meter: bool = True
    history_lines: int = 10
    theme: str = "dark"  # dark, light, dracula, monokai


@dataclass
class MeetingConfig:
    """Meeting mode configuration."""
    # Audio devices (None = use system default)
    mic_device: Optional[str] = None  # e.g., "MacBook Pro Microphone"
    system_audio_device: Optional[str] = None  # e.g., "BlackHole 2ch"
    mic_label: str = "Me"
    remote_label: str = "Remote"

    # Export
    auto_export: bool = False
    export_format: str = "markdown"  # txt, markdown, json, srt

    # Intel (LLM-powered analysis)
    intel_enabled: bool = True
    intel_realtime_model: str = "~/Models/gguf/Mistral-7B-Instruct-v0.3-Q6_K.gguf"
    intel_summary_model: Optional[str] = None  # Falls back to realtime if None

    # Web dashboard
    web_enabled: bool = True
    web_auto_open: bool = False  # Auto-open browser on meeting start

    # Speaker diarization
    diarization_enabled: bool = False  # Identify multiple speakers in system audio
    diarize_mic: bool = False  # Also diarize mic input (for on-site meetings)
    cross_meeting_recognition: bool = True  # Recognize speakers across meetings
    similarity_threshold: float = 0.75  # Cosine similarity for speaker matching


@dataclass
class Config:
    """Main configuration container."""
    hotkey: HotkeyConfig = field(default_factory=HotkeyConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    meeting: MeetingConfig = field(default_factory=MeetingConfig)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Config":
        """Load configuration from file, or create default."""
        config_path = path or CONFIG_FILE

        if not config_path.exists():
            config = cls()
            config.save(config_path)
            return config

        try:
            with open(config_path) as f:
                data = json.load(f)

            return cls(
                hotkey=HotkeyConfig(**data.get("hotkey", {})),
                model=ModelConfig(**data.get("model", {})),
                ui=UIConfig(**data.get("ui", {})),
                meeting=MeetingConfig(**data.get("meeting", {})),
            )
        except Exception:
            # Fall back to defaults on any error
            return cls()

    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        config_path = path or CONFIG_FILE
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


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
