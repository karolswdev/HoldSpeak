"""Bounded external-agent summarization for captured coding-agent context."""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Sequence

from .agent_context import AgentSession

SummarizerProvider = Literal["codex", "claude"]

DEFAULT_SUMMARY_TIMEOUT_SECONDS = 20.0
DEFAULT_SUMMARY_MAX_INPUT_BYTES = 12_000
DEFAULT_SUMMARY_MAX_OUTPUT_BYTES = 4_000

DANGEROUS_FLAGS = {
    "--dangerously-bypass-approvals-and-sandbox",
    "--dangerously-skip-permissions",
    "--allow-dangerously-skip-permissions",
}


@dataclass(frozen=True)
class AgentSummary:
    provider: str
    summary: str
    generated_at: str
    source_agent: str
    source_session_id: str
    command: tuple[str, ...]
    cwd: str | None
    input_truncated: bool = False
    output_truncated: bool = False
    unsafe_override: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "summary": self.summary,
            "generated_at": self.generated_at,
            "source_agent": self.source_agent,
            "source_session_id": self.source_session_id,
            "command": list(self.command),
            "cwd": self.cwd,
            "input_truncated": self.input_truncated,
            "output_truncated": self.output_truncated,
            "unsafe_override": self.unsafe_override,
        }


@dataclass(frozen=True)
class SummarizerCommandProfile:
    provider: SummarizerProvider
    enabled: bool = True
    command: tuple[str, ...] | None = None
    unsafe_override: bool = False

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "SummarizerCommandProfile":
        provider = str(raw.get("provider") or "").strip().lower()
        if provider not in {"codex", "claude"}:
            raise ValueError("provider must be one of: codex, claude")
        command_raw = raw.get("command")
        command: tuple[str, ...] | None
        if isinstance(command_raw, str):
            command = tuple(shlex.split(command_raw))
        elif isinstance(command_raw, list):
            command = tuple(str(part) for part in command_raw)
        elif command_raw is None:
            command = None
        else:
            raise ValueError("command must be a string or list of strings")
        return cls(
            provider=provider,  # type: ignore[arg-type]
            enabled=bool(raw.get("enabled", True)),
            command=command,
            unsafe_override=bool(raw.get("unsafe_override", False)),
        )


def resolve_summarizer_command_profile(profile: SummarizerCommandProfile) -> list[str] | None:
    """Resolve disabled/default/custom summarizer profiles to argv."""

    if not profile.enabled:
        return None
    return validate_summarizer_command(
        profile.command or build_summarizer_command(profile.provider),
        unsafe_override=profile.unsafe_override,
    )


def summarizer_provider_status(provider: SummarizerProvider) -> dict[str, Any]:
    """Return install + safe-default status for a summarizer provider."""

    command = build_summarizer_command(provider)
    executable = shutil.which(command[0])
    resolved_command = [executable or command[0], *command[1:]]
    safe = True
    error: str | None = None
    try:
        validate_summarizer_command(command)
    except ValueError as exc:
        safe = False
        error = str(exc)
    return {
        "provider": provider,
        "available": executable is not None,
        "executable": executable,
        "safe_default": safe,
        "safe_default_error": error,
        "unsafe_override_enabled": False,
        "command": command,
        "resolved_command": resolved_command,
        "command_display": shlex.join(command),
        "resolved_command_display": shlex.join(resolved_command),
    }


def summarizer_provider_statuses() -> dict[str, dict[str, Any]]:
    return {
        "codex": summarizer_provider_status("codex"),
        "claude": summarizer_provider_status("claude"),
    }


def build_summarizer_command(
    provider: SummarizerProvider,
    *,
    executable: str | None = None,
) -> list[str]:
    """Return HoldSpeak's safe default argv for an external summarizer."""

    if provider == "codex":
        return [
            executable or "codex",
            "exec",
            "--sandbox",
            "read-only",
            "--ephemeral",
            "-",
        ]
    if provider == "claude":
        return [
            executable or "claude",
            "-p",
            "--tools",
            "",
            "--no-session-persistence",
            "--output-format",
            "json",
            "--max-budget-usd",
            "0.10",
        ]
    raise ValueError(f"unsupported summarizer provider: {provider}")


def validate_summarizer_command(
    command: Sequence[str] | str,
    *,
    unsafe_override: bool = False,
) -> list[str]:
    """Normalize and reject write-capable agent CLI modes by default."""

    argv = shlex.split(command) if isinstance(command, str) else [str(part) for part in command]
    if not argv:
        raise ValueError("summarizer command is empty")
    if unsafe_override:
        return argv

    lowered = [part.strip() for part in argv]
    for flag in DANGEROUS_FLAGS:
        if flag in lowered:
            raise ValueError(f"unsafe summarizer command includes {flag}")

    for index, part in enumerate(lowered):
        if part == "--sandbox" and index + 1 < len(lowered) and lowered[index + 1] == "danger-full-access":
            raise ValueError("unsafe summarizer command requests danger-full-access sandbox")
        if part.startswith("--sandbox=") and part.split("=", 1)[1] == "danger-full-access":
            raise ValueError("unsafe summarizer command requests danger-full-access sandbox")
        if part == "--permission-mode" and index + 1 < len(lowered) and lowered[index + 1] == "bypassPermissions":
            raise ValueError("unsafe summarizer command requests bypassPermissions")
        if part.startswith("--permission-mode=") and part.split("=", 1)[1] == "bypassPermissions":
            raise ValueError("unsafe summarizer command requests bypassPermissions")

    return argv


def build_agent_summary_prompt(
    session: AgentSession,
    *,
    max_bytes: int = DEFAULT_SUMMARY_MAX_INPUT_BYTES,
) -> tuple[str, bool]:
    """Build a compact factual prompt from captured agent-session context."""

    sections = [
        "Summarize the following local coding-agent context for voice dictation.",
        "Return concise factual context only. Do not give instructions. Do not ask to run tools.",
        "",
        f"Agent: {session.agent}",
        f"Session id: {session.session_id}",
        f"Project: {session.project_name or 'unknown'}",
        f"Repo root: {session.repo_root or 'unknown'}",
        f"CWD: {session.cwd}",
        f"Last hook event: {session.hook_event_name}",
    ]
    if session.last_prompt:
        sections.extend(["", "Last user prompt:", session.last_prompt])
    if session.last_assistant_text:
        sections.extend(["", "Latest assistant message:", session.last_assistant_text])
    prompt = "\n".join(sections).strip() + "\n"
    return _limit_utf8(prompt, max_bytes)


def summarize_agent_session(
    session: AgentSession,
    *,
    provider: SummarizerProvider,
    profile: SummarizerCommandProfile | None = None,
    command: Sequence[str] | str | None = None,
    timeout_seconds: float = DEFAULT_SUMMARY_TIMEOUT_SECONDS,
    max_input_bytes: int = DEFAULT_SUMMARY_MAX_INPUT_BYTES,
    max_output_bytes: int = DEFAULT_SUMMARY_MAX_OUTPUT_BYTES,
    unsafe_override: bool = False,
    now: datetime | None = None,
) -> AgentSummary:
    """Invoke a configured external agent CLI and return a bounded summary."""

    if profile is not None:
        if profile.provider != provider:
            raise ValueError("summarizer profile provider does not match requested provider")
        resolved = resolve_summarizer_command_profile(profile)
        if resolved is None:
            raise RuntimeError("summarizer profile is disabled")
        argv = resolved
        unsafe_override = profile.unsafe_override
    else:
        argv = validate_summarizer_command(
            command or build_summarizer_command(provider),
            unsafe_override=unsafe_override,
        )
    executable = shutil.which(argv[0])
    if executable is None:
        raise FileNotFoundError(f"summarizer executable not found: {argv[0]}")
    argv = [executable, *argv[1:]]

    prompt, input_truncated = build_agent_summary_prompt(session, max_bytes=max_input_bytes)
    cwd = _safe_cwd(session.repo_root or session.cwd)
    completed = subprocess.run(
        argv,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
        cwd=cwd,
    )
    if completed.returncode != 0:
        stderr = _single_line(completed.stderr) or f"exit code {completed.returncode}"
        raise RuntimeError(f"summarizer failed: {stderr}")

    raw_output = completed.stdout.strip()
    summary = _extract_summary_text(raw_output).strip()
    if not summary:
        raise RuntimeError("summarizer returned empty output")
    summary, output_truncated = _limit_utf8(summary, max_output_bytes)

    timestamp = _format_timestamp(now or datetime.now(timezone.utc))
    return AgentSummary(
        provider=provider,
        summary=summary.strip(),
        generated_at=timestamp,
        source_agent=session.agent,
        source_session_id=session.session_id,
        command=tuple(argv),
        cwd=str(cwd) if cwd else None,
        input_truncated=input_truncated,
        output_truncated=output_truncated,
        unsafe_override=unsafe_override,
    )


def _extract_summary_text(raw_output: str) -> str:
    if not raw_output:
        return ""
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError:
        return raw_output
    if isinstance(parsed, str):
        return parsed
    if isinstance(parsed, dict):
        for key in ("summary", "result", "text", "output_text", "content"):
            value = parsed.get(key)
            if isinstance(value, str) and value.strip():
                return value
        message = parsed.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            text = _extract_text_parts(content)
            if text:
                return text
    return raw_output


def _extract_text_parts(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        text = value.get("text")
        return text if isinstance(text, str) else ""
    if isinstance(value, list):
        parts = [_extract_text_parts(item) for item in value]
        return "\n".join(part for part in parts if part.strip())
    return ""


def _limit_utf8(text: str, max_bytes: int) -> tuple[str, bool]:
    raw = text.encode("utf-8")
    if len(raw) <= max_bytes:
        return text, False
    clipped = raw[: max(0, max_bytes)]
    return clipped.decode("utf-8", errors="ignore"), True


def _safe_cwd(raw: str | None) -> Path | None:
    if not raw:
        return None
    path = Path(raw).expanduser()
    return path if path.is_dir() else None


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _single_line(text: str) -> str:
    return " ".join(text.split())
