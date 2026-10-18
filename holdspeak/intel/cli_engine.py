"""An agent CLI on this Mac as an engine (Betterment engines, slice E1).

A CLI engine is a destination whose transport is a process on this Mac.
HoldSpeak gives it one prompt on stdin and reads one answer from stdout. It is
a peer of an OpenAI-compatible endpoint, not a coding agent: built-in tools
are off (``--tools ""`` for Claude Code, a read-only sandbox for Codex), it
runs in an empty temporary folder, and each run is a new process.

The profile row needs no schema change: the preset goes in ``base_url`` as
``cli:<preset>`` (with ``?spend_limit_usd=<n>`` when the owner set a limit)
and the model goes in ``model`` (``default`` = the CLI's own default).

The CLI uses its own sign-in. HoldSpeak never reads, copies or passes it: the
process runs as the owner, with the hub's environment.

``HOLDSPEAK_CLI_ENGINES=off`` turns the kind off (rigs set it): nothing reads
PATH for a CLI and no CLI process starts.

The desk's tools (Betterment MCP slice M1). Each run gets HoldSpeak's own MCP
server and nothing else. Before the process starts, the hub issues a run
credential: identity ``agent:run:<run_id>``, the CONDUCTOR set (reads, People
included, and desk writes; no send, config, authority or nested model tool;
decisions #11 and #13), bound to the run, with a time to live a little past
the run's timeout. The hub URL and the token reach the child in its
environment only; a 0600 ``--mcp-config`` file (Claude Code) names the two
variables, never their values. After the process exits, fails or is killed,
the credential is revoked and the file is removed. Only HoldSpeak's server
loads (decision #12): Claude Code always gets ``--strict-mcp-config`` (without
it the login's claude.ai connectors load); Codex gets ``features.apps=false``
and the other feature switches of ``mcp/MODEL.md`` section 4, and every MCP
server in the owner's Codex config is turned off by name.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import tempfile
import threading
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs

from ..agent_summarizer import (
    _extract_summary_text,
    build_summarizer_command,
    validate_summarizer_command,
)
from ..kernel.provider_signals import (
    ProviderKnownNoGenerationTransient,
    ProviderPermanentNoGeneration,
)
from ..logging_config import get_logger
from ..redaction import redact_error
from . import cli_engine_runs
from .engine import MeetingIntel

log = get_logger("intel.cli_engine")

#: The rig switch. ``off`` = no CLI engine is read or run on this hub.
CLI_ENGINES_ENV = "HOLDSPEAK_CLI_ENGINES"
#: The profile kind (``ProfileRecord.kind``), target kind, engine and families.
PROFILE_KIND = "cliCommand"
TARGET_KIND = "cli_engine"
TRANSPORT = "subprocess"
RUNTIME_FAMILY = "cli_v1"
PROVIDER_FAMILY = "cli_agent"
BOUNDARY = "cloud"
ENDPOINT_PREFIX = "cli:"
#: The model value that means "the CLI's own default model".
DEFAULT_MODEL = "default"
#: The largest spend limit a profile can store for one run (USD).
MAX_SPEND_LIMIT_USD = 1000.0


def cli_engines_on() -> bool:
    return os.environ.get(CLI_ENGINES_ENV, "").strip().lower() != "off"


@dataclass(frozen=True)
class CliPreset:
    """One closed CLI preset. There is no free shell string."""

    id: str
    label: str
    executable: str
    vendor_host: str
    #: The longest one run may take, in seconds (kept inside the runner deadline).
    timeout_seconds: float
    #: The flag that names the model, placed before the stdin marker.
    model_flag: str
    #: True when the CLI enforces a spend limit for one run itself.
    enforces_spend_limit: bool
    #: True when the CLI reports what one run cost.
    reports_cost: bool
    #: Betterment E7: the argv for a preset the summarizer does not know (the
    #: prompt still goes on stdin). Empty for claude and codex.
    base_argv: tuple[str, ...] = ()
    #: How stdout is read: ``claude`` (``--output-format json``), ``codex``
    #: (``--json`` events), ``text`` (the answer as is) or ``gemini``
    #: (``--output-format json``: ``response``, ``stats``, ``error``).
    output: str = "claude"
    #: Betterment E7: True when the CLI's own config decides the provider, so
    #: the owner (or that config, read at Add) names the egress host.
    host_from_owner: bool = False


PRESETS: dict[str, CliPreset] = {
    "claude": CliPreset(
        id="claude", label="Claude Code", executable="claude",
        vendor_host="api.anthropic.com", timeout_seconds=240.0, model_flag="--model",
        enforces_spend_limit=True, reports_cost=True,
    ),
    "codex": CliPreset(
        id="codex", label="Codex", executable="codex",
        # The host can come from his Codex config; this is the preset's vendor.
        vendor_host="api.openai.com", timeout_seconds=240.0, model_flag="-m",
        enforces_spend_limit=False, reports_cost=False, output="codex",
    ),
    # Betterment E7. Flags from `pi --help` (pi 1.1.0) and pi's docs/cli.md,
    # never from a run: --print answers once and exits (piped stdin is the
    # prompt; stdin must close), --no-tools turns every tool off, and the
    # --no-* switches keep extensions, skills, templates, AGENTS.md/CLAUDE.md,
    # MCP servers and the session file out. --offline skips pi's start-up
    # network calls. pi's own config decides the provider, so the egress
    # host comes from the owner (or that config, read when he adds it).
    "pi": CliPreset(
        id="pi", label="pi", executable="pi",
        vendor_host="", timeout_seconds=240.0, model_flag="--model",
        enforces_spend_limit=False, reports_cost=False, output="text", host_from_owner=True,
        base_argv=(
            "--print", "--no-tools", "--no-session", "--no-extensions", "--no-skills",
            "--no-prompt-templates", "--no-context-files", "--no-mcp", "--no-approve", "--offline",
        ),
    ),
    # Betterment E7. Flags from `gemini --help` (Gemini CLI 0.18.4) and its
    # source, never from a run: with piped stdin and no query it answers once
    # (non-interactive); --approval-mode default then leaves out every tool
    # that needs approval (shell, edit, write); -e none loads no extension;
    # an allow-list that names no server loads no MCP server. Read-only tools
    # (read a file in the empty run folder, web search) stay: Gemini CLI has
    # no switch that turns every tool off.
    "gemini": CliPreset(
        id="gemini", label="Gemini CLI", executable="gemini",
        vendor_host="generativelanguage.googleapis.com", timeout_seconds=240.0, model_flag="-m",
        enforces_spend_limit=False, reports_cost=False, output="gemini",
        base_argv=(
            "--output-format", "json", "--approval-mode", "default", "-e", "none",
            "--allowed-mcp-server-names", "holdspeak-no-server",
        ),
    ),
}


def cli_endpoint(
    preset_id: str, spend_limit_usd: Optional[float] = None, host: str = "",
) -> str:
    """The ``base_url`` value that stores a preset (its spend limit, and for a
    preset whose config decides the provider, the egress host)."""
    preset = PRESETS[preset_id]
    query: list[str] = []
    if spend_limit_usd is not None:
        query.append(f"spend_limit_usd={_money(spend_limit_usd)}")
    if host and preset.host_from_owner:
        query.append(f"host={clean_host(host)}")
    return f"{ENDPOINT_PREFIX}{preset.id}" + (f"?{'&'.join(query)}" if query else "")


def clean_host(value: Any) -> str:
    """One host name or address (no scheme, path or port); '' if it is not one."""
    import re

    raw = str(value or "").strip().lower()
    if "://" in raw:
        from urllib.parse import urlparse

        raw = (urlparse(raw).hostname or "").lower()
    raw = raw.split("/")[0]
    if raw.count(":") == 1:
        raw = raw.split(":")[0]
    return raw if re.fullmatch(r"[a-z0-9][a-z0-9.\-]{0,252}", raw) else ""


def is_cli_endpoint(endpoint: Any) -> bool:
    return str(endpoint or "").strip().startswith(ENDPOINT_PREFIX)


def parse_cli_endpoint(endpoint: Any) -> tuple[CliPreset, Optional[float]] | None:
    """``(preset, spend_limit_usd)`` for a stored ``cli:`` value; None if unknown."""
    raw = str(endpoint or "").strip()
    if not raw.startswith(ENDPOINT_PREFIX):
        return None
    body = raw[len(ENDPOINT_PREFIX):]
    name, _, query = body.partition("?")
    preset = PRESETS.get(name)
    if preset is None:
        return None
    limit: Optional[float] = None
    fields = parse_qs(query) if query else {}
    if set(fields) - {"spend_limit_usd", "host"}:
        return None
    if "host" in fields and (not preset.host_from_owner or clean_host(fields["host"][0]) != fields["host"][0]):
        return None
    values = fields.get("spend_limit_usd")
    if values:
        try:
            limit = float(values[0])
        except ValueError:
            return None
        if not (0 < limit <= MAX_SPEND_LIMIT_USD):
            return None
    return preset, limit


#: The egress word for a ``host_from_owner`` preset whose host nobody named:
#: its own config decides, so the least private lamp (cloud) is shown.
UNKNOWN_HOST = "provider-in-cli-config"


def cli_vendor_host(endpoint: Any) -> str:
    """The host a ``cli:`` endpoint egresses to; '' for any other value.

    The preset's vendor; for pi, the host the owner named (or pi's config
    named when he added it), else ``UNKNOWN_HOST``."""
    parsed = parse_cli_endpoint(endpoint)
    if not parsed:
        return ""
    preset = parsed[0]
    if preset.host_from_owner:
        query = str(endpoint).partition("?")[2]
        return (parse_qs(query).get("host") or [""])[0] or UNKNOWN_HOST
    return preset.vendor_host


def pi_config_host(model: str = DEFAULT_MODEL, *, home: Optional[Path] = None) -> str:
    """The host pi's own config sends *model* to; '' when it does not say.

    Betterment E7: read when he adds pi, so the egress chip names his LAN
    box for ``lan-qwen/qwen3.8-27b``. Only ``baseUrl`` is read out of
    ``models.json`` (never a key). A built-in provider (no ``baseUrl``) gives
    '': the chip then says the provider is in pi's config, as cloud. The rig
    switch ``HOLDSPEAK_AGENT_STATE=off`` reads nothing outside HOME.
    """
    from ..services.onboarding_service import agent_state_read

    env_dir = os.environ.get("PI_CODING_AGENT_DIR", "").strip() if agent_state_read() else ""
    directory = Path(env_dir) if env_dir else (home or Path.home()) / ".pi" / "agent"
    try:
        providers = json.loads((directory / "models.json").read_text(encoding="utf-8")).get("providers")
    except (OSError, ValueError, AttributeError):
        return ""
    if not isinstance(providers, dict):
        return ""
    provider = ""
    if model and model != DEFAULT_MODEL and "/" in model:
        provider = model.split("/", 1)[0]
    else:
        try:
            settings = json.loads((directory / "settings.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            settings = {}
        provider = str(settings.get("defaultProvider") or "") if isinstance(settings, dict) else ""
    entry = providers.get(provider)
    if not isinstance(entry, dict):
        return ""
    return clean_host(entry.get("baseUrl"))


def cli_boundary(endpoint: Any) -> str:
    """The boundary of a ``cli:`` endpoint: ``cloud``, or ``private_network``
    when its host is on his network (pi on his LAN model; Betterment E7).

    A loopback host is ``private_network`` too: HoldSpeak does not pin the
    CLI's own connection, so it never says THIS DEVICE."""
    host = cli_vendor_host(endpoint)
    if not host or host == UNKNOWN_HOST:
        return BOUNDARY
    from .providers import egress_boundary

    verdict = egress_boundary(cloud=True, base_url=f"http://{host}/")
    return "private_network" if verdict in {"local", "private_network"} else BOUNDARY


def _money(value: float) -> str:
    return f"{float(value):.2f}"


#: Codex switches that keep everything but HoldSpeak's server away from the
#: agent (M0 live check, Codex 0.163; ``mcp/MODEL.md`` section 4). Without
#: ``features.apps=false`` the ChatGPT login's apps (GitHub writes, Sites
#: deploys) reach the agent. ``features.code_mode_host`` stays on: MCP calls go
#: through code mode, and with it off the MCP tools cannot be called.
CODEX_SWITCHES: tuple[str, ...] = (
    "features.apps=false",
    'web_search="disabled"',
    "features.plugins=false",
    "features.multi_agent=false",
    "features.image_generation=false",
    "features.browser_use=false",
    "features.computer_use=false",
    "features.in_app_browser=false",
    "features.tool_suggest=false",
    "features.skill_search=false",
    "features.goals=false",
    "features.sleep_tool=false",
    "features.view_image=false",
    "features.shell_tool=false",
    "features.unified_exec=false",
)


@dataclass(frozen=True)
class DeskTools:
    """What one run needs to reach HoldSpeak's MCP server (M1).

    ``env`` holds the run token: it goes into the child's environment only,
    and it is never in argv, a file or a repr."""

    run_id: str
    identity: str
    hub_url: str
    #: The Claude Code ``--mcp-config`` file (0600; the variable names only).
    config_path: Optional[Path]
    #: The MCP servers in the owner's Codex config, turned off by name.
    codex_servers_off: tuple[str, ...] = ()
    env: dict[str, str] = field(default_factory=dict, repr=False)


def build_cli_argv(
    preset: CliPreset,
    *,
    executable: str,
    model: str = DEFAULT_MODEL,
    spend_limit_usd: Optional[float] = None,
    tools: Optional[DeskTools] = None,
    cwd: Optional[str] = None,
    codex_servers_off: tuple[str, ...] = (),
) -> list[str]:
    """THE one place that builds a CLI engine's argv (the M1 seam).

    The base argv is the summarizer's safe default (``agent_summarizer``):
    built-in tools off for Claude Code, a read-only, ephemeral sandbox for
    Codex. The summarizer's fixed ``--max-budget-usd 0.10`` is removed: the
    owner's spend limit replaces it, and with no limit there is no cap
    (decision #10). The prompt always goes on stdin.

    M1: only HoldSpeak's server, in every run (with or without ``tools``).
    With ``tools``, the run's server is added: Claude Code reads the 0600
    config; Codex reads the URL from ``-c`` and the token from the
    environment variable the config names. Without ``tools`` (a run with no
    desk tools), Codex still turns off ``codex_servers_off`` (the servers of
    the owner's own Codex config): such a run gets no MCP server at all.
    """
    from ..delivery import agent_mcp

    if preset.base_argv:
        # Betterment E7 (pi, gemini): tools off, no desk tools yet (M1 has
        # only Claude Code and Codex), the prompt on stdin.
        argv = [executable, *preset.base_argv]
        if model and model != DEFAULT_MODEL:
            argv += [preset.model_flag, model]
        return validate_summarizer_command(argv)
    argv = build_summarizer_command(preset.id, executable=executable)  # type: ignore[arg-type]
    if "--max-budget-usd" in argv:
        index = argv.index("--max-budget-usd")
        del argv[index:index + 2]
    extra: list[str] = []
    if preset.id == "claude":
        # Never without --strict-mcp-config: the claude.ai connectors (Gmail,
        # Drive, Calendar, Docs) load otherwise (M0).
        extra += ["--strict-mcp-config", "--permission-prompts", "none"]
        if tools is not None and tools.config_path is not None:
            extra += ["--mcp-config", str(tools.config_path), "--allowedTools", agent_mcp.CLAUDE_ALLOW_RULE]
    elif preset.id == "codex":
        extra += ["--skip-git-repo-check", "--json"]
        if cwd:
            extra += ["-C", cwd]
        for switch in CODEX_SWITCHES:
            extra += ["-c", switch]
        for name in (tools.codex_servers_off if tools is not None else codex_servers_off):
            extra += ["-c", f"mcp_servers.{name}.enabled=false"]
        if tools is not None:
            extra += agent_mcp.codex_args(tools.hub_url, "yolo")
    if model and model != DEFAULT_MODEL:
        extra += [preset.model_flag, model]
    if spend_limit_usd is not None and preset.enforces_spend_limit:
        extra += ["--max-budget-usd", _money(spend_limit_usd)]
    if argv and argv[-1] == "-":
        # Codex: the flags go before the stdin marker.
        argv = [*argv[:-1], *extra, "-"]
    else:
        argv = [*argv, *extra]
    return validate_summarizer_command(argv)


# -- the run's credential and config (M1) ------------------------------------

#: How long a run credential outlives the run's timeout (the revoke after the
#: run is the rule; the time to live covers a hub that died mid-run).
RUN_TTL_MARGIN_SECONDS = 30.0
#: A run config file older than this is a leftover of a hub that died mid-run.
STALE_RUN_CONFIG_SECONDS = 3600.0


def run_identity(run_id: str) -> str:
    from ..services.conductor_launch import RUN_IDENTITY_PREFIX

    return f"{RUN_IDENTITY_PREFIX}{run_id}"


def run_config_dir() -> Path:
    """The run configs, in a folder of their own beside the launch configs."""
    from ..delivery import agent_mcp

    return agent_mcp.mcp_config_dir() / "runs"


def _sweep_stale_run_configs(directory: Path) -> None:
    try:
        entries = list(directory.iterdir())
    except OSError:
        return
    cutoff = time.time() - STALE_RUN_CONFIG_SECONDS
    for entry in entries:
        try:
            if entry.is_file() and entry.stat().st_mtime < cutoff:
                entry.unlink()
        except OSError:
            pass


def codex_user_servers() -> tuple[str, ...]:
    """The MCP server NAMES in the owner's Codex config (``$CODEX_HOME`` or
    ``~/.codex``). Only the names are read out: the values hold tokens."""
    import tomllib

    home = os.environ.get("CODEX_HOME", "").strip()
    path = Path(home) if home else Path.home() / ".codex"
    try:
        with (path / "config.toml").open("rb") as handle:
            servers = tomllib.load(handle).get("mcp_servers")
    except (OSError, ValueError):
        return ()
    if not isinstance(servers, dict):
        return ()
    return tuple(sorted(str(name) for name in servers))


def _text_of(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            str(part.get("text") or "") for part in content
            if isinstance(part, dict) and part.get("type") in {None, "text"}
        ]
        return "\n".join(part for part in parts if part)
    return str(content or "")


def _schema_of(response_format: Optional[dict[str, Any]]) -> Any:
    if not isinstance(response_format, dict):
        return None
    inner = response_format.get("json_schema")
    if isinstance(inner, dict) and inner.get("schema") is not None:
        return inner["schema"]
    if response_format.get("schema") is not None:
        return response_format["schema"]
    return {} if response_format.get("type") in {"json_object", "json_schema"} else None


def messages_to_prompt(
    messages: list[dict[str, Any]], response_format: Optional[dict[str, Any]] = None,
) -> str:
    """The chat messages as one text for stdin, plus the schema for a typed job.

    A CLI cannot take ``response_format``, so a typed job gets its JSON schema
    as an instruction. The job's own check still decides: a bad answer is
    ``invalid_typed_output`` and the chain goes to its fallback.
    """
    system = [
        _text_of(m.get("content")).strip() for m in messages
        if m.get("role") == "system" and _text_of(m.get("content")).strip()
    ]
    turns = [m for m in messages if m.get("role") != "system"]
    sections: list[str] = []
    if system:
        sections.append("\n\n".join(system))
    if len(turns) == 1 and turns[0].get("role") == "user":
        sections.append(_text_of(turns[0].get("content")).strip())
    else:
        for message in turns:
            role = str(message.get("role") or "user").capitalize()
            sections.append(f"{role}:\n{_text_of(message.get('content')).strip()}")
    schema = _schema_of(response_format)
    if schema is not None:
        rule = "Reply with JSON only. Do not add other text."
        if schema:
            rule += " The JSON must match this JSON schema:\n" + json.dumps(schema, sort_keys=True)
        sections.append(rule)
    return "\n\n".join(section for section in sections if section) + "\n"


@dataclass(frozen=True)
class CliAnswer:
    text: str
    cost_usd: Optional[float]
    usage: dict[str, int]
    model: str


class CliRunFailed(ProviderPermanentNoGeneration):
    """The CLI ran and reported an error (``is_error``); ``cost_usd`` is what
    it reported that run cost, or None (Betterment E2)."""

    def __init__(self, cost_usd: Optional[float] = None) -> None:
        super().__init__()
        self.cost_usd = cost_usd


def parse_cli_output(raw: str) -> CliAnswer:
    """Read the answer, the reported cost and the token counts from stdout.

    Claude Code (``--output-format json``) gives ``result``, ``total_cost_usd``,
    ``usage`` and ``is_error``. Codex prints the last message as text.
    """
    text = _extract_summary_text(raw.strip()).strip()
    cost: Optional[float] = None
    usage: dict[str, int] = {}
    model = ""
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        parsed = None
    if isinstance(parsed, dict):
        for key in ("total_cost_usd", "cost_usd"):
            value = parsed.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
                cost = float(value)
                break
        if parsed.get("is_error") is True:
            # E2: a run that stopped (at its spend limit, say) still cost money.
            raise CliRunFailed(cost)
        raw_usage = parsed.get("usage")
        if isinstance(raw_usage, dict):
            def count(*keys: str) -> int:
                return sum(
                    int(raw_usage[k]) for k in keys
                    if isinstance(raw_usage.get(k), int) and not isinstance(raw_usage.get(k), bool)
                )
            prompt = count("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
            completion = count("output_tokens")
            if prompt or completion:
                usage = {
                    "prompt_tokens": prompt,
                    "completion_tokens": completion,
                    "total_tokens": prompt + completion,
                }
        model_usage = parsed.get("modelUsage")
        if isinstance(model_usage, dict) and model_usage:
            model = str(next(iter(model_usage)))
    return CliAnswer(text=text, cost_usd=cost, usage=usage, model=model)


def parse_codex_output(raw: str) -> CliAnswer:
    """Read a ``codex exec --json`` run: one JSON event per line.

    The answer is the last ``agent_message`` item; the tokens are the sum of
    ``turn.completed.usage`` (tokens only, no dollars; M0). A failed turn or
    an ``error`` event is no generation. Output with no JSON event is read as
    plain text (the last message)."""
    text = ""
    prompt = completion = 0
    events = 0
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            continue
        events += 1
        kind = event["type"]
        if kind in {"turn.failed", "error"}:
            raise ProviderPermanentNoGeneration()
        item = event.get("item")
        if kind == "item.completed" and isinstance(item, dict) and item.get("type") == "agent_message":
            text = str(item.get("text") or "").strip() or text
        usage = event.get("usage")
        if kind == "turn.completed" and isinstance(usage, dict):
            def count(key: str) -> int:
                value = usage.get(key)
                return int(value) if isinstance(value, int) and not isinstance(value, bool) else 0
            prompt += count("input_tokens")
            completion += count("output_tokens")
    if not events:
        return CliAnswer(text=raw.strip(), cost_usd=None, usage={}, model="")
    usage_out = (
        {"prompt_tokens": prompt, "completion_tokens": completion, "total_tokens": prompt + completion}
        if prompt or completion else {}
    )
    return CliAnswer(text=text, cost_usd=None, usage=usage_out, model="")


def parse_text_output(raw: str) -> CliAnswer:
    """A CLI that prints only the answer (``pi --print``): the text as is.

    It is not read as JSON: a typed job's JSON answer must reach the job's
    own check unchanged."""
    return CliAnswer(text=raw.strip(), cost_usd=None, usage={}, model="")


def parse_gemini_output(raw: str) -> CliAnswer:
    """Read ``gemini --output-format json``: ``response``, ``stats``, ``error``
    (``JsonFormatter`` in gemini-cli-core). An ``error`` is no generation.
    Tokens come from ``stats.models.<model>.tokens``; there is no cost."""
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return parse_text_output(raw)
    if not isinstance(parsed, dict):
        return parse_text_output(raw)
    if parsed.get("error"):
        raise ProviderPermanentNoGeneration()
    text = str(parsed.get("response") or "").strip()
    prompt = completion = 0
    model = ""
    models = (parsed.get("stats") or {}).get("models") if isinstance(parsed.get("stats"), dict) else None
    if isinstance(models, dict):
        for name, entry in models.items():
            tokens = entry.get("tokens") if isinstance(entry, dict) else None
            if not isinstance(tokens, dict):
                continue
            model = model or str(name)
            for key, add in (("prompt", True), ("candidates", False)):
                value = tokens.get(key)
                if isinstance(value, int) and not isinstance(value, bool):
                    if add:
                        prompt += value
                    else:
                        completion += value
    usage = (
        {"prompt_tokens": prompt, "completion_tokens": completion, "total_tokens": prompt + completion}
        if prompt or completion else {}
    )
    return CliAnswer(text=text, cost_usd=None, usage=usage, model=model)


_PARSERS = {
    "claude": parse_cli_output,
    "codex": parse_codex_output,
    "text": parse_text_output,
    "gemini": parse_gemini_output,
}


class CliEngine(MeetingIntel):
    """``MeetingIntel`` over one agent CLI process per call.

    It overrides the three seams every job reaches: ``_ensure_model_loaded``
    (the executable is on PATH), ``_chat_completion_text`` (run the process)
    and ``run_prompt_stream`` (the whole answer as one delta). ``run_prompt``,
    ``run_prompt_messages``, ``analyze`` and the title helpers then work as
    they are.
    """

    def __init__(
        self, preset: CliPreset, *, model: str = DEFAULT_MODEL,
        spend_limit_usd: Optional[float] = None, profile_id: str = "",
    ) -> None:
        super().__init__(provider="cloud", cloud_model=model or DEFAULT_MODEL)
        self.preset = preset
        #: The engine's profile row; each run adds one ``cli_engine_runs`` row (E2).
        self.profile_id = str(profile_id or "")
        self.cli_model = model or DEFAULT_MODEL
        self.spend_limit_usd = spend_limit_usd
        #: M1: each run gets the desk's tools; a caller turns them off for
        #: one call on a copy (the automation's memory call, M2 follow-up).
        self.desk_tools = True
        #: The stored ``cli:`` value (its egress host, for pi).
        self.endpoint = cli_endpoint(preset.id, spend_limit_usd)
        self._executable: str = ""
        self._live: set[subprocess.Popen] = set()
        self._live_lock = threading.Lock()
        self._cost_local = threading.local()

    @classmethod
    def from_endpoint(cls, endpoint: str, *, model: str = "", profile_id: str = "") -> "CliEngine":
        parsed = parse_cli_endpoint(endpoint)
        if parsed is None:
            raise ProviderPermanentNoGeneration()
        preset, limit = parsed
        engine = cls(preset, model=model or DEFAULT_MODEL, spend_limit_usd=limit, profile_id=profile_id)
        engine.endpoint = str(endpoint)
        return engine

    # -- what the run reported ------------------------------------------------

    @property
    def last_cost_usd(self) -> Optional[float]:
        """The cost the CLI reported for this thread's last call; None if none."""
        return getattr(self._cost_local, "cost", None)

    # -- the three seams ------------------------------------------------------

    def _ensure_runtime_loaded(self) -> None:
        if not cli_engines_on():
            raise ProviderPermanentNoGeneration()
        executable = shutil.which(self.preset.executable)
        if executable is None:
            raise ProviderPermanentNoGeneration()
        self._executable = executable
        self._active_provider = PROVIDER_FAMILY
        self._active_model = self.cli_model

    def _ensure_model_loaded(self) -> None:
        self._ensure_runtime_loaded()

    def _chat_completion_text(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float,
        max_tokens: int,
        response_format: Optional[dict[str, Any]] = None,
    ) -> str:
        self._ensure_model_loaded()
        prompt = messages_to_prompt(messages, response_format)
        self._record_usage(None)
        self._cost_local.cost = None
        timeout = self._timeout()
        # E2: every run adds one cli_engine_runs row, with the cost the CLI
        # reported (also for a run that stopped at its spend limit).
        self._cost_local.outcome = cli_engine_runs.FAILED
        run_id: Optional[str] = None
        try:
            with tempfile.TemporaryDirectory(prefix="holdspeak-cli-engine-") as cwd:
                with self._desk_tools(timeout) as tools:
                    run_id = tools.run_id if tools else None
                    argv = build_cli_argv(
                        self.preset, executable=self._executable, model=self.cli_model,
                        spend_limit_usd=self.spend_limit_usd, tools=tools, cwd=cwd,
                        codex_servers_off=(
                            codex_user_servers() if tools is None and self.preset.id == "codex" else ()
                        ),
                    )
                    raw = self._egress(
                        argv, prompt, timeout=timeout, cwd=cwd, env=tools.env if tools else {},
                    )
            answer = _PARSERS[self.preset.output](raw)
            if not answer.text:
                raise ProviderPermanentNoGeneration()
        except (ProviderPermanentNoGeneration, ProviderKnownNoGenerationTransient) as exc:
            cli_engine_runs.record_run(
                self.profile_id, self._cost_local.outcome, getattr(exc, "cost_usd", None), run_id=run_id,
            )
            raise
        cli_engine_runs.record_run(self.profile_id, cli_engine_runs.ANSWERED, answer.cost_usd, run_id=run_id)
        self._record_usage(answer.usage or None)
        self._cost_local.cost = answer.cost_usd
        if answer.model and self.cli_model == DEFAULT_MODEL:
            self._active_model = answer.model
        return answer.text

    def _chat_completion_stream(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float,
        max_tokens: int,
        response_format: Optional[dict[str, Any]] = None,
    ) -> Iterator[str]:
        yield self._chat_completion_text(
            messages, temperature=temperature, max_tokens=max_tokens,
            response_format=response_format,
        )

    def run_prompt_stream(
        self,
        *,
        messages: list[dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | None = None,
    ) -> "Iterator[Any]":
        """No streaming yet: the whole answer is one text delta, then usage."""
        from ..kernel.inference_stream import Delta

        text = self._chat_completion_text(
            messages,
            temperature=self.temperature if temperature is None else temperature,
            max_tokens=self.max_tokens if max_tokens is None else max_tokens,
        )
        yield Delta(kind="text", text=text)
        meta: dict[str, Any] = dict(self.last_usage)
        if self.last_cost_usd is not None:
            meta["cost_usd"] = self.last_cost_usd
        if meta:
            yield Delta(kind="usage", meta=meta)
        yield Delta(kind="done")

    # -- the process ----------------------------------------------------------

    def cancel(self) -> None:
        """Kill every live process of this engine (the cancel seam)."""
        with self._live_lock:
            live = list(self._live)
        for process in live:
            _kill(process)

    def _timeout(self) -> float:
        """The preset timeout, kept inside the admitted child's deadline."""
        timeout = float(self.preset.timeout_seconds)
        from ..kernel.dispatch_context import dispatch_context_of

        context = dispatch_context_of(self)
        if context is not None:
            try:
                expires = float(context.warrant.get("execution_expires_at") or 0)
            except (AttributeError, TypeError, ValueError):
                expires = 0.0
            if expires:
                timeout = min(timeout, expires - time.time() - 1.0)
        return max(1.0, timeout)

    @contextmanager
    def _desk_tools(self, timeout: float) -> Iterator[Optional[DeskTools]]:
        """Issue the run's credential and config; revoke and remove them after.

        The ``finally`` runs whether the process answered, failed, timed out
        or was killed (``cancel``). A hub that dies mid-run leaves a
        credential that expires with its time to live and a config file the
        next run sweeps."""
        from ..delivery import agent_mcp
        from ..mcp.palettes import CONDUCTOR, resolve_palette
        from ..principals import CredentialPersistError, agent_credentials

        # Betterment E7: pi and Gemini CLI get no desk tools yet.
        if not self.desk_tools or self.preset.base_argv:
            yield None
            return
        servers_off: tuple[str, ...] = ()
        if self.preset.id == "codex":
            user_servers = codex_user_servers()
            if agent_mcp.SERVER_NAME in user_servers:
                # His own "holdspeak" entry would merge with the run's server
                # (it may be the owner's stdio sidecar): no desk tools.
                log.warning("Codex config has its own holdspeak server; this run gets no desk tools")
                yield None
                return
            servers_off = user_servers
        run_id = "run_" + uuid.uuid4().hex[:16]
        identity = run_identity(run_id)
        try:
            credential = agent_credentials.issue(
                identity,
                ttl_seconds=timeout + RUN_TTL_MARGIN_SECONDS,
                palette=resolve_palette(CONDUCTOR),
                palette_name=CONDUCTOR,
                launch_id=run_id,
            )
        except CredentialPersistError as exc:
            log.warning(f"run credential not stored ({exc}); this run gets no desk tools")
            yield None
            return
        directory = run_config_dir()
        try:
            _sweep_stale_run_configs(directory)
            config_path = (
                agent_mcp.write_mcp_config(run_id, directory) if self.preset.id == "claude" else None
            )
            hub_url = agent_credentials.hub_url
            yield DeskTools(
                run_id=run_id,
                identity=identity,
                hub_url=hub_url,
                config_path=config_path,
                codex_servers_off=servers_off,
                env={agent_mcp.HUB_URL_ENV: hub_url, agent_mcp.CREDENTIAL_ENV: credential.token},
            )
        finally:
            agent_credentials.revoke(identity, "run_ended")
            agent_mcp.remove_mcp_config(run_id, directory)

    def _egress(
        self, argv: list[str], prompt: str, *, timeout: float, cwd: str, env: dict[str, str],
    ) -> str:
        """Run the process under its egress record: the prompt goes to the vendor."""
        from ..kernel.external_egress import run_external_egress

        host = cli_vendor_host(self.endpoint) or self.preset.vendor_host
        return run_external_egress(
            connector_id="meeting-intel-cli-agent",
            destination=host,
            data_classes=("model_input",),
            payload_material={"preset": self.preset.id, "model": self.cli_model, "prompt": prompt},
            sender=self._run_process,
            kwargs={"argv": argv, "prompt": prompt, "timeout": timeout, "cwd": cwd, "env": env},
            allowed_destinations=(host,),
        )

    def _run_process(
        self, *, argv: list[str], prompt: str, timeout: float, cwd: str, env: dict[str, str],
    ) -> str:
        from ..cli_guard import refuse_real_cli_in_tests

        refuse_real_cli_in_tests(argv)
        # The run's hub URL and token reach this child only; the hub's own
        # environment never holds them.
        child_env = {**os.environ, **env}
        process = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
            env=child_env,
            start_new_session=True,
        )
        with self._live_lock:
            self._live.add(process)
        try:
            # communicate() writes the prompt, then closes stdin.
            stdout, stderr = process.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill(process)
            process.communicate()
            log.warning(f"{self.preset.label} did not answer in {timeout:.0f} s; stopped it")
            # Betterment E5 (FOLLOWUPS E1): a timed-out CLI is not tried again
            # (a second wait of the same length); the chain goes to its fallback.
            raise ProviderPermanentNoGeneration() from None
        finally:
            with self._live_lock:
                self._live.discard(process)
        if process.returncode != 0:
            if cli_engine_runs.says_not_signed_in(stderr or ""):
                self._cost_local.outcome = cli_engine_runs.NOT_SIGNED_IN
            detail = " ".join(redact_error(stderr or "").split())[:300]
            log.warning(f"{self.preset.label} stopped with code {process.returncode}: {detail}")
            raise ProviderPermanentNoGeneration()
        return stdout


def _kill(process: subprocess.Popen) -> None:
    """Kill the process and its children (it runs in its own session)."""
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            process.kill()
        except OSError:
            pass


__all__ = [
    "BOUNDARY",
    "CLI_ENGINES_ENV",
    "CODEX_SWITCHES",
    "CliAnswer",
    "CliRunFailed",
    "CliEngine",
    "CliPreset",
    "DEFAULT_MODEL",
    "DeskTools",
    "PRESETS",
    "PROFILE_KIND",
    "PROVIDER_FAMILY",
    "RUNTIME_FAMILY",
    "TARGET_KIND",
    "TRANSPORT",
    "build_cli_argv",
    "cli_endpoint",
    "cli_engines_on",
    "cli_boundary",
    "cli_vendor_host",
    "clean_host",
    "codex_user_servers",
    "is_cli_endpoint",
    "messages_to_prompt",
    "parse_cli_endpoint",
    "parse_cli_output",
    "parse_codex_output",
    "pi_config_host",
    "parse_gemini_output",
    "parse_text_output",
    "run_config_dir",
    "run_identity",
]
