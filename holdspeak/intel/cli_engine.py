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
from collections.abc import Iterator
from dataclasses import dataclass
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
        enforces_spend_limit=False, reports_cost=False,
    ),
}


def cli_endpoint(preset_id: str, spend_limit_usd: Optional[float] = None) -> str:
    """The ``base_url`` value that stores a preset (and its spend limit)."""
    preset = PRESETS[preset_id]
    if spend_limit_usd is None:
        return f"{ENDPOINT_PREFIX}{preset.id}"
    return f"{ENDPOINT_PREFIX}{preset.id}?spend_limit_usd={_money(spend_limit_usd)}"


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
    values = parse_qs(query).get("spend_limit_usd") if query else None
    if values:
        try:
            limit = float(values[0])
        except ValueError:
            return None
        if not (0 < limit <= MAX_SPEND_LIMIT_USD):
            return None
    return preset, limit


def cli_vendor_host(endpoint: Any) -> str:
    """The vendor host a ``cli:`` endpoint egresses to; '' for any other value."""
    parsed = parse_cli_endpoint(endpoint)
    return parsed[0].vendor_host if parsed else ""


def _money(value: float) -> str:
    return f"{float(value):.2f}"


def build_cli_argv(
    preset: CliPreset,
    *,
    executable: str,
    model: str = DEFAULT_MODEL,
    spend_limit_usd: Optional[float] = None,
) -> list[str]:
    """THE one place that builds a CLI engine's argv (the M1 seam).

    The base argv is the summarizer's safe default (``agent_summarizer``):
    tools off for Claude Code, a read-only, ephemeral sandbox for Codex. The
    summarizer's fixed ``--max-budget-usd 0.10`` is removed: the owner's
    spend limit replaces it, and with no limit there is no cap (decision #10).
    The prompt always goes on stdin. MCP slice M1 adds its flags here.
    """
    argv = build_summarizer_command(preset.id, executable=executable)  # type: ignore[arg-type]
    if "--max-budget-usd" in argv:
        index = argv.index("--max-budget-usd")
        del argv[index:index + 2]
    extra: list[str] = []
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
        if parsed.get("is_error") is True:
            raise ProviderPermanentNoGeneration()
        for key in ("total_cost_usd", "cost_usd"):
            value = parsed.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
                cost = float(value)
                break
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
        return cls(preset, model=model or DEFAULT_MODEL, spend_limit_usd=limit, profile_id=profile_id)

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
        argv = build_cli_argv(
            self.preset, executable=self._executable, model=self.cli_model,
            spend_limit_usd=self.spend_limit_usd,
        )
        prompt = messages_to_prompt(messages, response_format)
        self._record_usage(None)
        self._cost_local.cost = None
        self._cost_local.outcome = cli_engine_runs.FAILED
        try:
            raw = self._egress(argv, prompt)
            answer = parse_cli_output(raw)
            if not answer.text:
                raise ProviderPermanentNoGeneration()
        except (ProviderPermanentNoGeneration, ProviderKnownNoGenerationTransient):
            cli_engine_runs.record_run(self.profile_id, self._cost_local.outcome)
            raise
        cli_engine_runs.record_run(self.profile_id, cli_engine_runs.ANSWERED, answer.cost_usd)
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

    def _egress(self, argv: list[str], prompt: str) -> str:
        """Run the process under its egress record: the prompt goes to the vendor."""
        from ..kernel.external_egress import run_external_egress

        host = self.preset.vendor_host
        return run_external_egress(
            connector_id="meeting-intel-cli-agent",
            destination=host,
            data_classes=("model_input",),
            payload_material={"preset": self.preset.id, "model": self.cli_model, "prompt": prompt},
            sender=self._run_process,
            kwargs={"argv": argv, "prompt": prompt, "timeout": self._timeout()},
            allowed_destinations=(host,),
        )

    def _run_process(self, *, argv: list[str], prompt: str, timeout: float) -> str:
        from ..cli_guard import refuse_real_cli_in_tests

        refuse_real_cli_in_tests(argv)
        with tempfile.TemporaryDirectory(prefix="holdspeak-cli-engine-") as cwd:
            process = subprocess.Popen(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
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
                raise ProviderKnownNoGenerationTransient() from None
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
    "CliAnswer",
    "CliEngine",
    "CliPreset",
    "DEFAULT_MODEL",
    "PRESETS",
    "PROFILE_KIND",
    "PROVIDER_FAMILY",
    "RUNTIME_FAMILY",
    "TARGET_KIND",
    "TRANSPORT",
    "build_cli_argv",
    "cli_endpoint",
    "cli_engines_on",
    "cli_vendor_host",
    "is_cli_endpoint",
    "messages_to_prompt",
    "parse_cli_endpoint",
    "parse_cli_output",
]
