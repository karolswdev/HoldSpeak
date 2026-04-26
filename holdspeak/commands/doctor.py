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

    from ..plugins.dictation.runtime import RuntimeUnavailableError, resolve_backend

    requested = cfg.runtime.backend
    try:
        resolved, reason = resolve_backend(requested)
    except RuntimeUnavailableError as exc:
        fix_hint = (
            "Install holdspeak[dictation-mlx] (Apple Silicon) or "
            "holdspeak[dictation-llama] (cross-platform), or set "
            "dictation.runtime.backend = 'auto'."
        )
        return DoctorCheck(
            name="LLM runtime",
            status="WARN",
            detail=f"requested={requested!r}; resolution failed: {exc}",
            fix=fix_hint,
        )

    target = (
        Path(cfg.runtime.mlx_model).expanduser()
        if resolved == "mlx"
        else Path(cfg.runtime.llama_cpp_model_path).expanduser()
    )
    if not target.exists():
        if resolved == "mlx":
            fix_hint = (
                f"Download Qwen3-8B-MLX-4bit to {target} "
                "(see docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md §7.2)."
            )
        else:
            fix_hint = (
                f"Download Qwen2.5-3B-Instruct-Q4_K_M.gguf to {target} "
                "(see docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md §7.2)."
            )
        return DoctorCheck(
            name="LLM runtime",
            status="WARN",
            detail=f"resolved={resolved} ({reason}); model missing at {target}",
            fix=fix_hint,
        )

    return DoctorCheck(
        name="LLM runtime",
        status="PASS",
        detail=f"resolved={resolved} ({reason}); model available at {target}",
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
        if resolved == "mlx":
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
