"""Audio device discovery and BlackHole detection for HoldSpeak meeting mode.

This module provides utilities to discover audio devices, detect virtual audio
devices like BlackHole, and help users set up system audio capture.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import subprocess
import sys

try:
    import sounddevice as sd
except Exception as exc:  # pragma: no cover
    sd = None  # type: ignore[assignment]
    _SD_IMPORT_ERROR: Optional[BaseException] = exc
else:  # pragma: no cover
    _SD_IMPORT_ERROR = None

from .logging_config import get_logger

log = get_logger("audio_devices")

# Known virtual audio device names for system audio capture
VIRTUAL_AUDIO_DEVICES = [
    "BlackHole 2ch",
    "BlackHole 16ch",
    "BlackHole 64ch",
    "Soundflower (2ch)",
    "Soundflower (64ch)",
    "Loopback Audio",
]

PULSE_MONITOR_SUFFIX = ".monitor"


@dataclass
class AudioDevice:
    """Represents an audio device."""

    index: int
    name: str
    max_input_channels: int
    max_output_channels: int
    default_samplerate: float
    is_input: bool
    is_output: bool
    is_virtual: bool = False

    @property
    def is_blackhole(self) -> bool:
        """Check if this is a BlackHole device."""
        return "blackhole" in self.name.lower()

    def __str__(self) -> str:
        return f"{self.name} (idx={self.index}, in={self.max_input_channels}, out={self.max_output_channels})"


@dataclass
class PulseMonitorSource:
    """A PulseAudio/pipewire-pulse monitor source (for ffmpeg capture)."""

    name: str
    index: int = -1

    def __str__(self) -> str:
        return self.name


def _require_sounddevice():
    if sd is None:
        raise RuntimeError(
            "sounddevice/PortAudio is not available. "
            "Install system PortAudio and reinstall sounddevice."
        ) from _SD_IMPORT_ERROR
    return sd


def query_devices() -> list[AudioDevice]:
    """Query all available audio devices.

    Returns:
        List of AudioDevice objects.
    """
    devices = []
    sd_mod = _require_sounddevice()
    raw_devices = sd_mod.query_devices()

    for idx, dev in enumerate(raw_devices):
        name = dev["name"]
        is_virtual = any(v.lower() in name.lower() for v in VIRTUAL_AUDIO_DEVICES)

        device = AudioDevice(
            index=idx,
            name=name,
            max_input_channels=dev["max_input_channels"],
            max_output_channels=dev["max_output_channels"],
            default_samplerate=dev["default_samplerate"],
            is_input=dev["max_input_channels"] > 0,
            is_output=dev["max_output_channels"] > 0,
            is_virtual=is_virtual,
        )
        devices.append(device)

    return devices


def _pactl_stdout(args: list[str]) -> Optional[str]:
    try:
        proc = subprocess.run(
            ["pactl", *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError as exc:
        log.debug(f"pactl failed: {exc}")
        return None
    return proc.stdout


def list_pulse_monitor_sources() -> list[str]:
    """List PulseAudio/pipewire-pulse monitor sources (Linux)."""
    if not sys.platform.startswith("linux"):
        return []

    out = _pactl_stdout(["list", "short", "sources"])
    if not out:
        return []

    monitors: list[str] = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        name = parts[1].strip()
        if name.endswith(PULSE_MONITOR_SUFFIX):
            monitors.append(name)
    return monitors


def find_pulse_monitor_source(name: Optional[str] = None) -> Optional[str]:
    """Find a PulseAudio/pipewire-pulse monitor source name (Linux)."""
    monitors = list_pulse_monitor_sources()
    if not monitors:
        return None

    if name:
        candidate = name.strip()
        if candidate and not candidate.endswith(PULSE_MONITOR_SUFFIX):
            candidate = f"{candidate}{PULSE_MONITOR_SUFFIX}"
        if candidate in monitors:
            return candidate
        lower = name.lower()
        for m in monitors:
            if lower in m.lower():
                return m

    default_sink = _pactl_stdout(["get-default-sink"])
    if default_sink:
        candidate = f"{default_sink.strip()}{PULSE_MONITOR_SUFFIX}"
        if candidate in monitors:
            return candidate

    return monitors[0]


def get_input_devices() -> list[AudioDevice]:
    """Get all input-capable devices."""
    return [d for d in query_devices() if d.is_input]


def get_output_devices() -> list[AudioDevice]:
    """Get all output-capable devices."""
    return [d for d in query_devices() if d.is_output]


def find_blackhole() -> Optional[AudioDevice]:
    """Find BlackHole virtual audio device.

    Returns:
        AudioDevice if BlackHole is found and has input channels, None otherwise.
    """
    for device in query_devices():
        if device.is_blackhole and device.is_input:
            log.info(f"Found BlackHole device: {device}")
            return device

    log.warning("BlackHole not found among input devices")
    return None


def find_virtual_audio_device() -> Optional[AudioDevice]:
    """Find any virtual audio device suitable for system audio capture.

    Prefers BlackHole, falls back to other virtual devices.

    Returns:
        AudioDevice if found, None otherwise.
    """
    # First try BlackHole
    blackhole = find_blackhole()
    if blackhole:
        return blackhole

    # Try other virtual devices
    for device in query_devices():
        if device.is_virtual and device.is_input:
            log.info(f"Found virtual audio device: {device}")
            return device

    return None


def get_default_input_device() -> Optional[AudioDevice]:
    """Get the default input device (microphone).

    Returns:
        AudioDevice for the default input, or None if not found.
    """
    try:
        sd_mod = _require_sounddevice()
        default_idx = sd_mod.default.device[0]  # Input device index
        if default_idx is None or default_idx < 0:
            # Query for first available input
            devices = get_input_devices()
            if devices:
                return devices[0]
            return None

        devices = query_devices()
        if 0 <= default_idx < len(devices):
            return devices[default_idx]
        return None
    except Exception as e:
        log.error(f"Failed to get default input device: {e}")
        return None


def find_device_by_name(name: str) -> Optional[AudioDevice]:
    """Find a device by name (case-insensitive substring match).

    Args:
        name: Device name to search for.

    Returns:
        AudioDevice if found, None otherwise.
    """
    name_lower = name.lower()
    for device in query_devices():
        if name_lower in device.name.lower():
            return device
    return None


def check_blackhole_setup() -> dict:
    """Check BlackHole setup status and provide guidance.

    Returns:
        Dictionary with:
        - installed: bool - Whether BlackHole is detected
        - device: Optional[AudioDevice] - The BlackHole device if found
        - setup_instructions: str - Instructions for setup if needed
    """
    if sys.platform.startswith("linux"):
        monitor = find_pulse_monitor_source()
        if monitor:
            return {
                "installed": True,
                "device": PulseMonitorSource(name=monitor),
                "setup_instructions": "",
            }

        instructions = """
No PulseAudio monitor source found.

To capture system audio on Linux, you need PulseAudio/pipewire-pulse and a monitor source:

1. Ensure PipeWire/PulseAudio is running.
2. Ensure `pactl` is installed (Debian/Ubuntu: `sudo apt-get install pulseaudio-utils`).
3. Verify you have a monitor source:
   pactl list short sources | grep '\\.monitor'

Then set `meeting.system_audio_device` to a source like:
  alsa_output.<...>.monitor
""".strip()

        return {
            "installed": False,
            "device": None,
            "setup_instructions": instructions,
        }

    blackhole = find_blackhole()

    if blackhole:
        return {
            "installed": True,
            "device": blackhole,
            "setup_instructions": "",
        }

    instructions = """
BlackHole is not installed or not configured for input.

To capture system audio, you need:

1. Install BlackHole (free, open source):
   brew install blackhole-2ch

2. Create a Multi-Output Device in Audio MIDI Setup:
   - Open "Audio MIDI Setup" (search in Spotlight)
   - Click "+" at bottom left, select "Create Multi-Output Device"
   - Check both your speakers AND "BlackHole 2ch"
   - Right-click the Multi-Output Device, set as "Use this device for sound output"

3. Restart HoldSpeak in meeting mode:
   holdspeak meeting

For more details: https://github.com/ExistentialAudio/BlackHole
""".strip()

    return {
        "installed": False,
        "device": None,
        "setup_instructions": instructions,
    }


def list_devices_formatted() -> str:
    """Get a formatted string listing all audio devices.

    Returns:
        Formatted device list for display.
    """
    devices = query_devices()
    lines = ["Audio Devices:", ""]

    # Inputs
    lines.append("INPUT DEVICES:")
    inputs = [d for d in devices if d.is_input]
    if inputs:
        for d in inputs:
            marker = " [VIRTUAL]" if d.is_virtual else ""
            lines.append(f"  [{d.index}] {d.name}{marker}")
    else:
        lines.append("  (none)")

    lines.append("")

    # Outputs
    lines.append("OUTPUT DEVICES:")
    outputs = [d for d in devices if d.is_output]
    if outputs:
        for d in outputs:
            marker = " [VIRTUAL]" if d.is_virtual else ""
            lines.append(f"  [{d.index}] {d.name}{marker}")
    else:
        lines.append("  (none)")

    # Defaults
    try:
        default_in, default_out = sd.default.device
        lines.append("")
        lines.append(f"Default input: {default_in}")
        lines.append(f"Default output: {default_out}")
    except Exception:
        pass

    # Pulse monitor sources (Linux)
    monitors = list_pulse_monitor_sources()
    if monitors:
        lines.append("")
        lines.append("PULSE MONITOR SOURCES (for system audio):")
        for m in monitors:
            lines.append(f"  {m}")

    return "\n".join(lines)
