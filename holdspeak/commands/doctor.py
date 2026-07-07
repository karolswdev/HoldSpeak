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

from pathlib import Path

from ..audio_devices import check_blackhole_setup, get_default_input_device
from ..config import CONFIG_FILE, Config
from ..hotkey import HotkeyListener
from ..intel import get_intel_runtime_status, intel_egress_posture
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
    from .. import __version__

    return DoctorCheck(
        name="Runtime",
        status="PASS",
        detail=(
            f"HoldSpeak {__version__} on {platform.system()} {platform.release()} "
            f"({platform.machine()}), Python {sys.version.split()[0]}"
        ),
    )


def _check_database() -> DoctorCheck:
    """Report the database's schema version against this build.

    Read-only: it probes the stored version without opening the database for
    use, so a newer-than-known database is reported plainly rather than refused.
    A missing database is normal before first run, not a problem.
    """
    from ..db import DEFAULT_DB_PATH, SCHEMA_VERSION, read_schema_version

    db_path = DEFAULT_DB_PATH.expanduser()

    if not db_path.exists():
        return DoctorCheck(
            name="Database",
            status="PASS",
            detail=f"No database yet at {db_path}; it is created on first use.",
        )

    stored = read_schema_version(db_path)

    if stored is None:
        return DoctorCheck(
            name="Database",
            status="WARN",
            detail=f"A file is present at {db_path} but its schema version cannot be read.",
            fix="If this is not a HoldSpeak database, move it aside and let HoldSpeak create a fresh one.",
        )

    if stored == SCHEMA_VERSION:
        return DoctorCheck(
            name="Database",
            status="PASS",
            detail=f"Schema version {stored} (current) at {db_path}.",
        )

    if stored < SCHEMA_VERSION:
        return DoctorCheck(
            name="Database",
            status="WARN",
            detail=(
                f"Schema version {stored} is older than this build ({SCHEMA_VERSION}). "
                f"HoldSpeak backs the database up and upgrades it on the next start."
            ),
            fix="Run `holdspeak backup` first if you want your own copy before the upgrade.",
        )

    return DoctorCheck(
        name="Database",
        status="FAIL",
        detail=(
            f"Schema version {stored} is newer than this build ({SCHEMA_VERSION}). "
            f"The database was written by a newer HoldSpeak; this build refuses to open it."
        ),
        fix="Upgrade HoldSpeak, or `holdspeak restore` a backup taken with this version.",
    )


def _check_config() -> tuple[DoctorCheck, Config]:
    from ..config import CONFIG_VERSION

    config = Config.load()
    config_path = CONFIG_FILE.expanduser()
    if not config_path.exists():
        return DoctorCheck(
            name="Config",
            status="WARN",
            detail=f"Config file not found at {config_path}",
            fix="Run `holdspeak` once to create a default config file.",
        ), config

    if config.config_version > CONFIG_VERSION:
        return DoctorCheck(
            name="Config",
            status="WARN",
            detail=(
                f"Config version {config.config_version} is newer than this build "
                f"({CONFIG_VERSION}); some settings may be ignored. Loaded {config_path}."
            ),
            fix="Upgrade HoldSpeak so it understands this config.",
        ), config

    return DoctorCheck(
        name="Config",
        status="PASS",
        detail=f"Loaded {config_path} (config version {config.config_version})",
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


def _check_meeting_intel_egress(config: Config) -> DoctorCheck:
    """Surface, plainly, whether the active config can send transcripts off-machine."""
    meeting = config.meeting
    if not meeting.intel_enabled:
        return DoctorCheck(
            name="Meeting intelligence egress",
            status="PASS",
            detail="Disabled — no transcript leaves this machine.",
        )

    can_transmit, description = intel_egress_posture(meeting.intel_provider)
    if not can_transmit:
        return DoctorCheck(
            name="Meeting intelligence egress",
            status="PASS",
            detail=description,
        )

    # HS-84-04: name where the cloud leg ACTUALLY goes — an assigned
    # RuntimeProfile (HS-84-01) is the endpoint, not the raw legacy fields.
    from ..intel.providers import effective_intel_cloud, endpoint_host

    effective = effective_intel_cloud(meeting)
    if effective.profile_id:
        destination = (
            f" Runs on profile '{effective.profile_name}'"
            f" ({endpoint_host(effective.base_url) or effective.base_url})."
        )
    elif effective.reason:
        destination = f" NOTE: {effective.reason}."
    else:
        destination = ""

    # Cloud is a legitimate, user-chosen option; we surface it loudly so it is
    # never a surprise, but it is not a failure.
    return DoctorCheck(
        name="Meeting intelligence egress",
        status="WARN",
        detail=f"provider=`{meeting.intel_provider}`: {description}{destination}",
        fix=(
            "This is expected if you chose cloud intentionally. To keep all "
            "transcripts local, set meeting.intel_provider to 'local'."
        ),
    )


def _check_web_auth(config: Config) -> DoctorCheck:
    """Report how the web runtime is bound and whether an auth token is set."""
    token_set = bool(getattr(config.meeting, "web_auth_token", "") or "")
    # The runtime binds 127.0.0.1 today; the token activates the moment a
    # non-loopback bind is introduced (Phase 15). Surface both facts plainly.
    detail = (
        "Web runtime binds loopback (open to this machine). "
        f"Auth token is {'set' if token_set else 'not set'} — "
        "required automatically if a non-loopback bind is ever configured."
    )
    return DoctorCheck(
        name="Web runtime auth",
        status="PASS",
        detail=detail,
        fix=(
            None
            if token_set
            else "A token is generated on first web launch; no action needed."
        ),
    )


def _check_meeting_intel_cloud_preflight(
    config: Config, *, timeout_seconds: float = 4.0, skip_network: bool = False
) -> DoctorCheck:
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
    if skip_network:
        return DoctorCheck(
            name="Cloud intel preflight",
            status="PASS",
            detail="Not run (network preflight skipped at setup load)",
            fix="Run `holdspeak doctor` for a live cloud-endpoint preflight.",
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


def _check_dictation_project_context(config: Config) -> DoctorCheck:
    """Report cwd-based project detection (HS-3-02).

    Always opt-in via dictation.pipeline.enabled — when disabled,
    skips with PASS to keep `holdspeak doctor` quiet on the default
    path. Never returns FAIL: a missing project just means the
    `kb-enricher` stage has no context to inject (DIR-F-007 covers
    that path).
    """
    if not config.dictation.pipeline.enabled:
        return DoctorCheck(
            name="Project context",
            status="PASS",
            detail="dictation pipeline disabled (opt-in)",
        )

    from ..plugins.dictation.project_root import detect_project_for_cwd

    try:
        project = detect_project_for_cwd()
    except Exception as exc:  # pragma: no cover — defensive
        return DoctorCheck(
            name="Project context",
            status="WARN",
            detail=f"detection raised {type(exc).__name__}: {exc}",
            fix="File a bug — `detect_project_for_cwd` should never raise on a normal cwd.",
        )

    if project is None:
        return DoctorCheck(
            name="Project context",
            status="WARN",
            detail=f"no project root detected from cwd={Path.cwd()}",
            fix=(
                "Launch holdspeak from inside a project directory, "
                "or `mkdir <project>/.holdspeak` to mark a project root."
            ),
        )

    return DoctorCheck(
        name="Project context",
        status="PASS",
        detail=(
            f"detected {project['name']} (anchor={project['anchor']}) "
            f"at {project['root']}"
            + (" + KB" if "kb" in project else "")
        ),
    )


def _check_runtime_profiles(config: Config) -> DoctorCheck:
    """HS-84-04: name the RuntimeProfile each hub pipeline resolves to.

    One honest line per enabled pipeline (meeting intel, dictation). A
    dangling assignment is a WARN with the resolver's own reason; an adopted
    profile that `requires_key` with no key in the hub's env is a WARN naming
    the exact env var. Never FAIL — every fallback keeps the pipeline running.
    """
    from ..intel.providers import (
        _lookup_profile_record,
        effective_dictation_llm,
        effective_intel_cloud,
        endpoint_host,
        profile_key_env,
    )

    pipelines: list[tuple[str, object]] = []
    if config.meeting.intel_enabled:
        pipelines.append(("meeting intel", effective_intel_cloud(config.meeting)))
    if config.dictation.pipeline.enabled:
        pipelines.append(("dictation", effective_dictation_llm(config.dictation.runtime)))
    if not pipelines:
        return DoctorCheck(
            name="Runtime profiles",
            status="PASS",
            detail="no pipeline enabled — nothing resolves through a profile",
        )

    lines: list[str] = []
    warns: list[str] = []
    fixes: list[str] = []
    for label, effective in pipelines:
        if effective.profile_id:
            lines.append(
                f"{label}: profile '{effective.profile_name}'"
                f" ({endpoint_host(effective.base_url) or effective.base_url})"
            )
            try:
                record = _lookup_profile_record(effective.profile_id)
            except Exception:
                record = None
            if (
                record is not None
                and bool(getattr(record, "requires_key", False))
                and not os.environ.get(effective.api_key_env)
            ):
                warns.append(
                    f"{label}: profile '{effective.profile_name}' requires a key"
                    f" but ${effective.api_key_env} is unset"
                )
                fixes.append(
                    f"export {profile_key_env(effective.profile_id)}=<key> on this hub"
                    " (keys never sync; each device holds its own)"
                )
        elif effective.reason:
            warns.append(f"{label}: {effective.reason}")
            fixes.append(
                f"Re-pick the {label} profile in Settings, or clear its profile id"
            )
        else:
            lines.append(f"{label}: hub default (no profile assigned)")

    if warns:
        return DoctorCheck(
            name="Runtime profiles",
            status="WARN",
            detail="; ".join(warns + lines),
            fix=" · ".join(dict.fromkeys(fixes)),
        )
    return DoctorCheck(
        name="Runtime profiles",
        status="PASS",
        detail="; ".join(lines),
    )


def _check_dictation_runtime(config: Config) -> DoctorCheck:
    """DIR-DOC-001: report the resolved dictation LLM runtime + model availability.

    Never returns `FAIL` — DIR-01 is opt-in (DIR-DOC-003), so a
    misconfiguration is at most a `WARN`. The check does not load
    the model; it inspects the configured path with `Path.exists()`
    to keep `holdspeak doctor` cheap.
    """
    cfg = config.dictation
    if not cfg.pipeline.enabled:
        return DoctorCheck(
            name="LLM runtime",
            status="PASS",
            detail="dictation pipeline disabled (opt-in)",
        )

    from ..intel.providers import effective_dictation_llm
    from ..plugins.dictation.guidance import doctor_model_fix, doctor_runtime_install_fix
    from ..plugins.dictation.runtime import RuntimeUnavailableError, resolve_backend

    # HS-84-04: name the RuntimeProfile the pipeline resolves to. An adopted
    # profile selects the endpoint backend (HS-84-02); a dangling assignment
    # falls back to the configured backend and must say so loudly.
    effective = effective_dictation_llm(cfg.runtime)
    if effective.profile_id:
        where = (
            f"mesh node '{effective.node}'"
            if effective.node
            else f"endpoint={effective.base_url}"
        )
        return DoctorCheck(
            name="LLM runtime",
            status="PASS",
            detail=(
                f"runs on profile '{effective.profile_name}'; {where}; "
                f"model={effective.model}"
            ),
        )
    profile_note = f" NOTE: {effective.reason}." if effective.reason else ""
    profile_fix = (
        "Re-pick a profile in Dictation → Runtime (or clear "
        "dictation.runtime.profile_id). "
        if effective.reason
        else ""
    )

    requested = cfg.runtime.backend
    try:
        resolved, reason = resolve_backend(requested)
    except RuntimeUnavailableError as exc:
        return DoctorCheck(
            name="LLM runtime",
            status="WARN",
            detail=f"requested={requested!r}; resolution failed: {exc}{profile_note}",
            fix=f"{profile_fix}{doctor_runtime_install_fix(requested)}",
        )

    if resolved == "openai_compatible":
        return DoctorCheck(
            name="LLM runtime",
            status="WARN" if effective.reason else "PASS",
            detail=(
                f"resolved={resolved} ({reason}); endpoint="
                f"{cfg.runtime.openai_compatible_base_url}; "
                f"model={cfg.runtime.openai_compatible_model}{profile_note}"
            ),
            fix=profile_fix or None,
        )

    target = (
        Path(cfg.runtime.mlx_model).expanduser()
        if resolved == "mlx"
        else Path(cfg.runtime.llama_cpp_model_path).expanduser()
    )
    if not target.exists():
        return DoctorCheck(
            name="LLM runtime",
            status="WARN",
            detail=f"resolved={resolved} ({reason}); model missing at {target}{profile_note}",
            fix=f"{profile_fix}{doctor_model_fix(resolved, target)}",
        )

    return DoctorCheck(
        name="LLM runtime",
        status="WARN" if effective.reason else "PASS",
        detail=f"resolved={resolved} ({reason}); model available at {target}{profile_note}",
        fix=profile_fix or None,
    )


def _check_dictation_constraint_compile(config: Config) -> DoctorCheck:
    """DIR-DOC-002: compile the loaded `blocks.yaml` against the active backend.

    Pure-Python compile (cheap), so the doctor runs it eagerly. Never
    returns `FAIL` per DIR-DOC-003.
    """
    cfg = config.dictation
    if not cfg.pipeline.enabled:
        return DoctorCheck(
            name="Structured-output compilation",
            status="PASS",
            detail="dictation pipeline disabled (opt-in)",
        )

    from ..plugins.dictation.assembly import DEFAULT_GLOBAL_BLOCKS_PATH
    from ..plugins.dictation.blocks import BlockConfigError, resolve_blocks
    from ..plugins.dictation.grammars import (
        GrammarCompileError,
        StructuredOutputSchema,
        to_gbnf,
        to_outlines,
    )
    from ..plugins.dictation.runtime import RuntimeUnavailableError, resolve_backend

    try:
        loaded = resolve_blocks(DEFAULT_GLOBAL_BLOCKS_PATH, None)
    except BlockConfigError as exc:
        return DoctorCheck(
            name="Structured-output compilation",
            status="WARN",
            detail=f"blocks.yaml failed to load: {exc}",
            fix="Run `holdspeak dictation blocks validate` for the full error.",
        )

    if not loaded.blocks:
        return DoctorCheck(
            name="Structured-output compilation",
            status="PASS",
            detail="no blocks loaded; nothing to compile",
        )

    try:
        resolved, _reason = resolve_backend(cfg.runtime.backend)
    except RuntimeUnavailableError:
        # The runtime check already reported this; reporting again
        # would be noise. Compile against both shapes so block
        # authors still get a "your YAML is structurally valid"
        # signal.
        resolved = "llama_cpp"

    try:
        block_set = loaded.to_block_set()
        schema = StructuredOutputSchema.from_block_set(block_set)
        if resolved in {"mlx", "openai_compatible"}:
            to_outlines(schema)
        else:
            to_gbnf(schema)
    except (GrammarCompileError, Exception) as exc:
        return DoctorCheck(
            name="Structured-output compilation",
            status="WARN",
            detail=f"{resolved} compile failed: {type(exc).__name__}: {exc}",
            fix="Run `holdspeak dictation blocks validate` to see the offending block.",
        )

    return DoctorCheck(
        name="Structured-output compilation",
        status="PASS",
        detail=f"{resolved}: {len(loaded.blocks)} block(s) compiled cleanly",
    )


def _check_dictation_runtime_counters(config: Config) -> DoctorCheck:
    """DIR-O-002: surface the four LLM-runtime counters (HS-3-04).

    Always PASS — counters are advisory observability, not a health
    signal. Skipped with PASS when the dictation pipeline is disabled
    so the default doctor output stays quiet.
    """
    if not config.dictation.pipeline.enabled:
        return DoctorCheck(
            name="LLM runtime counters",
            status="PASS",
            detail="dictation pipeline disabled (opt-in)",
        )

    from ..plugins.dictation.runtime_counters import (
        get_counters,
        get_session_status,
    )

    counters = get_counters()
    session = get_session_status()
    detail = (
        f"model_loads={counters['model_loads']} "
        f"classify_calls={counters['classify_calls']} "
        f"classify_failures={counters['classify_failures']} "
        f"constrained_retries={counters['constrained_retries']} "
        f"llm_disabled_for_session={session['llm_disabled_for_session']}"
    )
    if session["llm_disabled_for_session"]:
        return DoctorCheck(
            name="LLM runtime counters",
            status="WARN",
            detail=detail + f" — {session['disabled_reason']}",
            fix="Restart `holdspeak` to retry. If it keeps tripping, raise `dictation.pipeline.max_total_latency_ms` or `warm_on_start: true`.",
        )
    return DoctorCheck(
        name="LLM runtime counters",
        status="PASS",
        detail=detail,
    )


def _check_mir_routing(config: Config) -> DoctorCheck:
    """MIR-O-001 / spec §9.10: report MIR-01 routing-pipeline config posture.

    Never returns `FAIL` — the pipeline is opt-in (mirrors DIR-DOC-003).
    Validates the configured `plugin_profile` against the pre-defined
    profile set so a typo surfaces here rather than at meeting stop.
    """
    cfg = config.meeting
    if not cfg.intent_router_enabled:
        return DoctorCheck(
            name="MIR routing",
            status="PASS",
            detail="MIR-01 routing pipeline disabled (opt-in)",
        )

    try:
        from ..plugins.router import available_profiles
    except Exception as exc:
        return DoctorCheck(
            name="MIR routing",
            status="WARN",
            detail=f"router import failed: {type(exc).__name__}: {exc}",
            fix="Inspect holdspeak/plugins/router.py for import errors.",
        )

    profiles = list(available_profiles())
    if cfg.plugin_profile not in profiles:
        return DoctorCheck(
            name="MIR routing",
            status="WARN",
            detail=(
                f"plugin_profile={cfg.plugin_profile!r} not in available profiles "
                f"({', '.join(profiles)})"
            ),
            fix=(
                "Set meeting.plugin_profile to one of the available profiles "
                "in your config.json."
            ),
        )

    return DoctorCheck(
        name="MIR routing",
        status="PASS",
        detail=(
            f"enabled; profile={cfg.plugin_profile}, "
            f"window={cfg.intent_window_seconds}s/step={cfg.intent_step_seconds}s, "
            f"threshold={cfg.intent_score_threshold}, "
            f"hysteresis_windows={cfg.intent_hysteresis_windows}"
        ),
    )


def _check_mir_telemetry() -> DoctorCheck:
    """MIR-O-002 / MIR-O-003 / spec §9.10: smoke-check that the
    router + plugin-host counter APIs are callable and return the
    expected shape. Always PASS — the APIs are pure-Python and
    exercising them costs microseconds."""
    try:
        from ..plugins.host import PluginHost
        from ..plugins.router import get_router_counters

        router_counters = get_router_counters()
        # Throwaway host purely to read the metrics-schema shape — it never
        # executes a plugin, so it needs no capability wiring (HS-16-02).
        host_metrics = PluginHost().get_metrics()
    except Exception as exc:
        return DoctorCheck(
            name="MIR telemetry",
            status="WARN",
            detail=f"telemetry API failed: {type(exc).__name__}: {exc}",
            fix="Inspect holdspeak/plugins/router.py + host.py for regressions.",
        )

    router_keys = sorted(router_counters.keys())
    host_keys = sorted(host_metrics.keys())
    return DoctorCheck(
        name="MIR telemetry",
        status="PASS",
        detail=(
            f"router_counters=[{', '.join(router_keys)}]; "
            f"host_metrics=[{', '.join(host_keys)}]"
        ),
    )


def _check_connector_packs() -> DoctorCheck:
    """HS-13-04: list every discovered connector pack and flag
    user-pack discovery errors. The first-party packs are
    statically enumerated; user packs come from
    `~/.holdspeak/connector_packs/` (or whatever
    `HOLDSPEAK_USER_PACKS_DIR` points at)."""
    from ..activity_connectors import KNOWN_CONNECTORS, discovery_errors

    by_source: dict[str, list[str]] = {}
    for descriptor in KNOWN_CONNECTORS:
        by_source.setdefault(descriptor.source, []).append(descriptor.id)
    errors = discovery_errors()

    parts = []
    for source in ("first-party", "user"):
        ids = sorted(by_source.get(source, []))
        if ids:
            parts.append(f"{source}: {', '.join(ids)}")
    detail = "; ".join(parts) if parts else "no connectors"
    if errors:
        detail += f" (rejected: {len(errors)})"

    if errors:
        return DoctorCheck(
            name="Connector packs",
            status="WARN",
            detail=detail,
            fix=(
                "Inspect rejected user packs:\n  "
                + "\n  ".join(str(e) for e in errors)
            ),
        )
    return DoctorCheck(
        name="Connector packs",
        status="PASS",
        detail=detail,
    )


def collect_doctor_checks(*, skip_network: bool = False) -> list[DoctorCheck]:
    """Collect all doctor checks in display order.

    `skip_network=True` makes every check cheap (no outbound call) — the cloud
    preflight returns a neutral "not run" check instead of probing the endpoint.
    The setup-status surface (HS-42-01) uses this so a page load never blocks on a
    4-second HTTP timeout; the CLI `holdspeak doctor` keeps the full live preflight.
    """
    is_wayland = _is_wayland_session()
    config_check, config = _check_config()

    return [
        _check_runtime(),
        config_check,
        _check_database(),
        _check_microphone(),
        _check_transcription_backend(),
        _check_web_runtime(),
        _check_web_auth(config),
        _check_meeting_intel_runtime(config),
        _check_meeting_intel_egress(config),
        _check_runtime_profiles(config),
        _check_meeting_intel_cloud_preflight(config, skip_network=skip_network),
        _check_dictation_project_context(config),
        _check_dictation_runtime(config),
        _check_dictation_constraint_compile(config),
        _check_dictation_runtime_counters(config),
        _check_mir_routing(config),
        _check_mir_telemetry(),
        _check_hotkey(config.hotkey.key, is_wayland=is_wayland),
        _check_text_injection(is_wayland=is_wayland),
        _check_clipboard_tools(is_wayland=is_wayland),
        _check_ffmpeg(),
        _check_pactl(),
        _check_system_audio_capture(),
        _check_connector_packs(),
    ]


def _summarize(checks: list[DoctorCheck]) -> tuple[int, int, int]:
    passed = sum(1 for c in checks if c.status == "PASS")
    warned = sum(1 for c in checks if c.status == "WARN")
    failed = sum(1 for c in checks if c.status == "FAIL")
    return passed, warned, failed


def run_connector_packs_listing() -> int:
    """HS-13-04: focused connector-pack listing (`doctor --connectors`).

    Prints every discovered pack with its id, source, kind, and
    file path (for user packs) plus any discovery errors. Exit
    code is 0 when all discovered files validated, 1 otherwise.
    """
    from ..activity_connectors import KNOWN_CONNECTORS, discovery_errors

    print("HoldSpeak connector packs")
    print("=" * 25)
    from .. import activity_connectors as _ac
    pack_files = {
        p.manifest.id: p.file_path
        for p in _ac._DISCOVERY.packs
        if p.file_path is not None
    }
    for descriptor in KNOWN_CONNECTORS:
        manifest = descriptor.manifest
        path = pack_files.get(descriptor.id)
        suffix = f" — {path}" if path else ""
        print(
            f"- {manifest.id} [{descriptor.source}] "
            f"kind={manifest.kind}{suffix}"
        )

    errors = discovery_errors()
    if errors:
        print()
        print(f"Rejected ({len(errors)}):")
        for entry in errors:
            print(f"  - {entry}")
        return 1
    return 0


def run_doctor_command(args) -> int:
    """Handle the `doctor` subcommand.

    Returns:
        Exit code (0 for healthy enough; non-zero for failures).
    """
    if getattr(args, "connectors", False):
        return run_connector_packs_listing()

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
