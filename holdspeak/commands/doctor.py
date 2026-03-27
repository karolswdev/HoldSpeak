"""Doctor subcommand for HoldSpeak.

Performs lightweight environment checks and prints actionable remediation.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import platform
import shutil
import sys

from ..audio_devices import check_blackhole_setup, get_default_input_device
from ..config import CONFIG_FILE, Config
from ..hotkey import HotkeyListener
from ..transcribe import TranscriberError, _resolve_backend
from ..typer import TextTyper


@dataclass(frozen=True)
class DoctorCheck:
    """A single doctor check result."""

    name: str
    status: str  # PASS | WARN | FAIL
    detail: str
    fix: str | None = None


def _is_wayland_session() -> bool:
    xdg = os.environ.get("XDG_SESSION_TYPE", "").strip().lower()
    return xdg == "wayland" or bool(os.environ.get("WAYLAND_DISPLAY"))


def _command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def _check_runtime() -> DoctorCheck:
    return DoctorCheck(
        name="Runtime",
        status="PASS",
        detail=f"{platform.system()} {platform.release()} ({platform.machine()}), Python {sys.version.split()[0]}",
    )


def _check_config() -> tuple[DoctorCheck, Config]:
    config = Config.load()
    config_path = CONFIG_FILE.expanduser()
    if config_path.exists():
        return DoctorCheck(
            name="Config",
            status="PASS",
            detail=f"Loaded {config_path}",
        ), config
    return DoctorCheck(
        name="Config",
        status="WARN",
        detail=f"Config file not found at {config_path}",
        fix="Run `holdspeak` once to create a default config file.",
    ), config


def _check_microphone() -> DoctorCheck:
    try:
        device = get_default_input_device()
    except Exception as exc:
        return DoctorCheck(
            name="Microphone",
            status="FAIL",
            detail=f"Unable to query input device: {exc}",
            fix="Install PortAudio and verify your mic is available to the OS.",
        )

    if device is None:
        return DoctorCheck(
            name="Microphone",
            status="FAIL",
            detail="No input-capable audio device found.",
            fix="Connect/enable a microphone and retry.",
        )

    return DoctorCheck(
        name="Microphone",
        status="PASS",
        detail=f"Default input: {device.name} (index {device.index})",
    )


def _check_transcription_backend() -> DoctorCheck:
    try:
        backend = _resolve_backend("auto")
    except TranscriberError as exc:
        if sys.platform.startswith("linux"):
            fix = "Install Linux backend with `pip install 'holdspeak[linux]'`."
        elif sys.platform == "darwin":
            fix = "Install supported backend dependencies, then rerun doctor."
        else:
            fix = "Install `faster-whisper` and rerun doctor."
        return DoctorCheck(
            name="Transcription backend",
            status="FAIL",
            detail=str(exc),
            fix=fix,
        )

    return DoctorCheck(
        name="Transcription backend",
        status="PASS",
        detail=f"`auto` resolves to `{backend}`",
    )


def _check_hotkey(hotkey_name: str, *, is_wayland: bool) -> DoctorCheck:
    try:
        _ = HotkeyListener(hotkey=hotkey_name)
    except Exception as exc:
        if is_wayland:
            return DoctorCheck(
                name="Global hotkey",
                status="WARN",
                detail=f"Unavailable: {exc}",
                fix="On Wayland this is often expected; keep HoldSpeak focused and hold `v` to record.",
            )
        return DoctorCheck(
            name="Global hotkey",
            status="FAIL",
            detail=f"Unavailable: {exc}",
            fix="Run inside a GUI desktop session with input permissions enabled.",
        )

    return DoctorCheck(
        name="Global hotkey",
        status="PASS",
        detail=f"Hotkey listener initialized for `{hotkey_name}`",
    )


def _check_text_injection(*, is_wayland: bool) -> DoctorCheck:
    try:
        _ = TextTyper()
    except Exception as exc:
        if is_wayland:
            return DoctorCheck(
                name="Text injection",
                status="WARN",
                detail=f"Unavailable: {exc}",
                fix="On Wayland this can be restricted. Use clipboard/manual paste when needed.",
            )
        return DoctorCheck(
            name="Text injection",
            status="FAIL",
            detail=f"Unavailable: {exc}",
            fix="Ensure GUI automation/input permissions are available in your desktop session.",
        )

    return DoctorCheck(
        name="Text injection",
        status="PASS",
        detail="Keyboard injection backend initialized",
    )


def _check_clipboard_tools(*, is_wayland: bool) -> DoctorCheck:
    if not sys.platform.startswith("linux"):
        return DoctorCheck(
            name="Clipboard backend",
            status="PASS",
            detail="Platform default clipboard backend",
        )

    if is_wayland:
        missing = [cmd for cmd in ("wl-copy", "wl-paste") if not _command_exists(cmd)]
        if missing:
            return DoctorCheck(
                name="Clipboard backend",
                status="WARN",
                detail=f"Missing tools: {', '.join(missing)}",
                fix="Install wl-clipboard (e.g., `sudo apt-get install wl-clipboard`).",
            )
        return DoctorCheck(
            name="Clipboard backend",
            status="PASS",
            detail="Wayland clipboard tools detected (wl-copy/wl-paste)",
        )

    if _command_exists("xclip") or _command_exists("xsel"):
        return DoctorCheck(
            name="Clipboard backend",
            status="PASS",
            detail="X11 clipboard tool detected",
        )
    return DoctorCheck(
        name="Clipboard backend",
        status="WARN",
        detail="No X11 clipboard tool detected",
        fix="Install xclip (e.g., `sudo apt-get install xclip`).",
    )


def _check_ffmpeg() -> DoctorCheck:
    if _command_exists("ffmpeg"):
        return DoctorCheck(
            name="ffmpeg",
            status="PASS",
            detail="Detected in PATH",
        )
    return DoctorCheck(
        name="ffmpeg",
        status="WARN",
        detail="Not found in PATH",
        fix="Install ffmpeg (e.g., `sudo apt-get install ffmpeg` or `brew install ffmpeg`).",
    )


def _check_pactl() -> DoctorCheck:
    if not sys.platform.startswith("linux"):
        return DoctorCheck(
            name="pactl",
            status="PASS",
            detail="Not required on this platform",
        )

    if _command_exists("pactl"):
        return DoctorCheck(
            name="pactl",
            status="PASS",
            detail="Detected in PATH",
        )
    return DoctorCheck(
        name="pactl",
        status="WARN",
        detail="Not found in PATH",
        fix="Install pulseaudio-utils (e.g., `sudo apt-get install pulseaudio-utils`).",
    )


def _check_system_audio_capture() -> DoctorCheck:
    try:
        status = check_blackhole_setup()
    except Exception as exc:
        return DoctorCheck(
            name="System audio capture",
            status="WARN",
            detail=f"Unable to verify setup: {exc}",
            fix="Run `holdspeak meeting --setup` for detailed setup guidance.",
        )

    if status.get("installed"):
        device = status.get("device")
        device_name = getattr(device, "name", str(device) if device is not None else "unknown")
        return DoctorCheck(
            name="System audio capture",
            status="PASS",
            detail=f"Detected: {device_name}",
        )

    return DoctorCheck(
        name="System audio capture",
        status="WARN",
        detail="System-audio capture source not configured",
        fix="Run `holdspeak meeting --setup` and follow the printed instructions.",
    )


def collect_doctor_checks() -> list[DoctorCheck]:
    """Collect all doctor checks in display order."""
    is_wayland = _is_wayland_session()
    config_check, config = _check_config()

    return [
        _check_runtime(),
        config_check,
        _check_microphone(),
        _check_transcription_backend(),
        _check_hotkey(config.hotkey.key, is_wayland=is_wayland),
        _check_text_injection(is_wayland=is_wayland),
        _check_clipboard_tools(is_wayland=is_wayland),
        _check_ffmpeg(),
        _check_pactl(),
        _check_system_audio_capture(),
    ]


def _summarize(checks: list[DoctorCheck]) -> tuple[int, int, int]:
    passed = sum(1 for c in checks if c.status == "PASS")
    warned = sum(1 for c in checks if c.status == "WARN")
    failed = sum(1 for c in checks if c.status == "FAIL")
    return passed, warned, failed


def run_doctor_command(args) -> int:
    """Handle the `doctor` subcommand.

    Returns:
        Exit code (0 for healthy enough; non-zero for failures).
    """
    checks = collect_doctor_checks()

    print("HoldSpeak Doctor")
    print("=" * 15)
    for check in checks:
        print(f"[{check.status}] {check.name}: {check.detail}")

    passed, warned, failed = _summarize(checks)
    print()
    print(f"Summary: {passed} passed, {warned} warnings, {failed} failed")

    issues = [c for c in checks if c.status in {"WARN", "FAIL"} and c.fix]
    if issues:
        print("\nSuggested fixes:")
        for check in issues:
            print(f"- {check.name}: {check.fix}")

    strict = bool(getattr(args, "strict", False))
    if failed > 0:
        return 1
    if strict and warned > 0:
        return 1
    return 0
