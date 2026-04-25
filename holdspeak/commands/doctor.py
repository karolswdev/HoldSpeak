"""Doctor subcommand for HoldSpeak.

Performs lightweight environment checks and prints actionable remediation.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import platform
import socket
import shutil
import ssl
import sys
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import urlparse

from ..audio_devices import check_blackhole_setup, get_default_input_device
from ..config import CONFIG_FILE, Config
from ..hotkey import HotkeyListener
from ..intel import get_intel_runtime_status
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


def _check_web_runtime() -> DoctorCheck:
    """Verify deps for the default `holdspeak` web runtime are importable."""
    from importlib.util import find_spec

    missing = [m for m in ("fastapi", "uvicorn", "websockets") if find_spec(m) is None]
    if not missing:
        return DoctorCheck(
            name="Web runtime",
            status="PASS",
            detail="fastapi, uvicorn, and websockets are importable",
        )
    return DoctorCheck(
        name="Web runtime",
        status="FAIL",
        detail=f"Missing modules: {', '.join(missing)}",
        fix="Reinstall HoldSpeak (these are core deps): `uv pip install -e .` or `pip install -e .`.",
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


def _check_meeting_intel_runtime(config: Config) -> DoctorCheck:
    meeting = config.meeting
    if not meeting.intel_enabled:
        return DoctorCheck(
            name="Meeting intelligence runtime",
            status="PASS",
            detail="Disabled in config",
        )

    ok, reason = get_intel_runtime_status(
        meeting.intel_realtime_model,
        provider=meeting.intel_provider,
        cloud_model=meeting.intel_cloud_model,
        cloud_api_key_env=meeting.intel_cloud_api_key_env,
        cloud_base_url=meeting.intel_cloud_base_url,
    )
    if ok:
        return DoctorCheck(
            name="Meeting intelligence runtime",
            status="PASS",
            detail=f"Provider mode `{meeting.intel_provider}` is ready",
        )

    fix = None
    if meeting.intel_provider == "cloud":
        fix = f"Set {meeting.intel_cloud_api_key_env} and verify cloud model '{meeting.intel_cloud_model}'."
    elif meeting.intel_provider == "auto":
        fix = (
            f"Provide a local model at '{meeting.intel_realtime_model}' "
            f"or set {meeting.intel_cloud_api_key_env} for cloud fallback."
        )
    else:
        fix = f"Set a valid local model path (currently '{meeting.intel_realtime_model}')."

    return DoctorCheck(
        name="Meeting intelligence runtime",
        status="WARN",
        detail=reason or "Meeting intelligence runtime is unavailable",
        fix=fix,
    )


def _normalize_cloud_base_url(base_url: str | None) -> str:
    value = (base_url or "").strip()
    if value:
        return value.rstrip("/")
    return "https://api.openai.com/v1"


def _describe_preflight_network_error(host: str, reason: object) -> tuple[str, str]:
    if isinstance(reason, socket.gaierror):
        return (
            f"DNS lookup failed for `{host}`.",
            "Verify hostname/IP and local DNS routing (VPN/LAN).",
        )
    if isinstance(reason, (socket.timeout, TimeoutError)):
        return (
            f"Connection to `{host}` timed out.",
            "Check host reachability, firewall rules, and network latency.",
        )
    if isinstance(reason, ConnectionRefusedError):
        return (
            f"Connection refused by `{host}`.",
            "Ensure the intel API service is running and listening on the configured port.",
        )
    if isinstance(reason, ssl.SSLError):
        return (
            f"TLS handshake failed for `{host}`: {reason}",
            "Fix certificate chain/hostname, or use a trusted LAN cert.",
        )
    return (
        f"Unable to reach `{host}`: {reason}",
        "Verify endpoint address, network routing, and service availability.",
    )


def _check_meeting_intel_cloud_preflight(config: Config, *, timeout_seconds: float = 4.0) -> DoctorCheck:
    meeting = config.meeting
    if not meeting.intel_enabled:
        return DoctorCheck(
            name="Cloud intel preflight",
            status="PASS",
            detail="Skipped (meeting intelligence disabled)",
        )
    if meeting.intel_provider == "local":
        return DoctorCheck(
            name="Cloud intel preflight",
            status="PASS",
            detail="Skipped (provider mode `local`)",
        )

    api_key_env = (meeting.intel_cloud_api_key_env or "OPENAI_API_KEY").strip() or "OPENAI_API_KEY"
    api_key = (os.environ.get(api_key_env) or "").strip()
    if not api_key:
        return DoctorCheck(
            name="Cloud intel preflight",
            status="WARN",
            detail=f"Missing API key in ${api_key_env}",
            fix=f"Set {api_key_env} in your shell or service environment before running cloud intel.",
        )

    base_url = _normalize_cloud_base_url(meeting.intel_cloud_base_url)
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return DoctorCheck(
            name="Cloud intel preflight",
            status="WARN",
            detail=f"Invalid cloud base URL: {base_url}",
            fix="Set `intel_cloud_base_url` to a valid http(s) URL, e.g. http://homelab.local:8000/v1.",
        )

    models_url = f"{base_url}/models"
    request = urlrequest.Request(
        models_url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="GET",
    )

    try:
        with urlrequest.urlopen(request, timeout=timeout_seconds) as response:
            payload_bytes = response.read()
    except urlerror.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace").strip()
        if exc.code in {401, 403}:
            return DoctorCheck(
                name="Cloud intel preflight",
                status="WARN",
                detail=f"Auth rejected by `{models_url}` (HTTP {exc.code}).",
                fix=f"Check token in ${api_key_env} and endpoint auth configuration.",
            )
        if exc.code == 404:
            return DoctorCheck(
                name="Cloud intel preflight",
                status="WARN",
                detail=f"`{models_url}` returned HTTP 404.",
                fix="Verify `intel_cloud_base_url` includes the correct API prefix (commonly `/v1`).",
            )
        return DoctorCheck(
            name="Cloud intel preflight",
            status="WARN",
            detail=f"`{models_url}` returned HTTP {exc.code}: {body[:140] or 'no response body'}",
            fix="Confirm endpoint compatibility and API access policy.",
        )
    except urlerror.URLError as exc:
        host = parsed.hostname or parsed.netloc or base_url
        detail, fix = _describe_preflight_network_error(host, exc.reason)
        return DoctorCheck(
            name="Cloud intel preflight",
            status="WARN",
            detail=detail,
            fix=fix,
        )
    except TimeoutError:
        host = parsed.hostname or parsed.netloc or base_url
        return DoctorCheck(
            name="Cloud intel preflight",
            status="WARN",
            detail=f"Connection to `{host}` timed out.",
            fix="Check host reachability, firewall rules, and endpoint load.",
        )
    except Exception as exc:
        return DoctorCheck(
            name="Cloud intel preflight",
            status="WARN",
            detail=f"Unexpected preflight failure: {exc}",
            fix="Verify endpoint compatibility with the OpenAI `/models` API.",
        )

    try:
        payload = json.loads(payload_bytes.decode("utf-8", errors="replace"))
    except Exception:
        payload = None

    configured_model = (meeting.intel_cloud_model or "").strip()
    model_ids: list[str] = []
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    model_id = row.get("id")
                    if isinstance(model_id, str) and model_id.strip():
                        model_ids.append(model_id.strip())

    if model_ids and configured_model and configured_model not in model_ids:
        sample = ", ".join(model_ids[:5])
        return DoctorCheck(
            name="Cloud intel preflight",
            status="WARN",
            detail=f"Endpoint reachable, but model `{configured_model}` is unavailable.",
            fix=f"Set `intel_cloud_model` to a served model id (examples: {sample}).",
        )

    if not model_ids:
        return DoctorCheck(
            name="Cloud intel preflight",
            status="PASS",
            detail=f"Endpoint reachable at `{base_url}` (model list unavailable; model check skipped).",
        )

    return DoctorCheck(
        name="Cloud intel preflight",
        status="PASS",
        detail=f"Endpoint reachable at `{base_url}` and model `{configured_model}` is available.",
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
        _check_web_runtime(),
        _check_meeting_intel_runtime(config),
        _check_meeting_intel_cloud_preflight(config),
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
