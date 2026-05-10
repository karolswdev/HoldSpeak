from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from holdspeak.agent_context import AgentSession
from holdspeak.agent_summarizer import (
    build_agent_summary_prompt,
    build_summarizer_command,
    resolve_summarizer_command_profile,
    summarize_agent_session,
    summarizer_provider_status,
    SummarizerCommandProfile,
    validate_summarizer_command,
)


def _session(tmp_path: Path) -> AgentSession:
    return AgentSession(
        agent="codex",
        session_id="sess-1",
        cwd=str(tmp_path),
        updated_at="2026-05-10T00:00:00Z",
        hook_event_name="Stop",
        repo_root=str(tmp_path),
        project_name="HoldSpeak",
        last_prompt="Please continue the current phase.",
        last_assistant_text="I added the agent hook scaffolding. Should I add the summarizer next?",
        awaiting_response=True,
    )


def test_default_codex_command_is_read_only() -> None:
    command = build_summarizer_command("codex")

    assert command[:2] == ["codex", "exec"]
    assert "--sandbox" in command
    assert "read-only" in command
    assert "--ephemeral" in command


def test_default_claude_command_disables_tools() -> None:
    command = build_summarizer_command("claude")

    assert command[:2] == ["claude", "-p"]
    assert "--tools" in command
    assert "" in command
    assert "--no-session-persistence" in command


def test_provider_status_reports_safe_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("holdspeak.agent_summarizer.shutil.which", lambda name: f"/usr/bin/{name}")

    status = summarizer_provider_status("codex")

    assert status["provider"] == "codex"
    assert status["available"] is True
    assert status["safe_default"] is True
    assert status["unsafe_override_enabled"] is False
    assert status["executable"] == "/usr/bin/codex"
    assert "codex exec" in status["command_display"]


def test_command_profile_supports_disabled_default_and_custom() -> None:
    disabled = SummarizerCommandProfile(provider="codex", enabled=False)
    default = SummarizerCommandProfile(provider="codex")
    custom = SummarizerCommandProfile(
        provider="codex",
        command=("codex", "exec", "--sandbox", "read-only", "--ephemeral", "-"),
    )

    assert resolve_summarizer_command_profile(disabled) is None
    assert resolve_summarizer_command_profile(default) == build_summarizer_command("codex")
    assert resolve_summarizer_command_profile(custom) == list(custom.command or ())


def test_command_profile_rejects_custom_dangerous_command_without_override() -> None:
    profile = SummarizerCommandProfile(
        provider="claude",
        command=("claude", "-p", "--dangerously-skip-permissions", "summarize"),
    )

    with pytest.raises(ValueError):
        resolve_summarizer_command_profile(profile)


def test_command_profile_can_parse_mapping() -> None:
    profile = SummarizerCommandProfile.from_mapping(
        {
            "provider": "codex",
            "enabled": True,
            "command": "codex exec --sandbox read-only --ephemeral -",
        }
    )

    assert profile.provider == "codex"
    assert profile.command == ("codex", "exec", "--sandbox", "read-only", "--ephemeral", "-")


@pytest.mark.parametrize(
    "command",
    [
        ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", "summarize"],
        ["codex", "exec", "--sandbox", "danger-full-access", "summarize"],
        ["claude", "-p", "--dangerously-skip-permissions", "summarize"],
        ["claude", "-p", "--permission-mode", "bypassPermissions", "summarize"],
    ],
)
def test_validate_rejects_dangerous_modes_by_default(command: list[str]) -> None:
    with pytest.raises(ValueError):
        validate_summarizer_command(command)


def test_validate_allows_dangerous_modes_only_with_override() -> None:
    command = ["claude", "-p", "--dangerously-skip-permissions", "summarize"]

    assert validate_summarizer_command(command, unsafe_override=True) == command


def test_prompt_is_bounded(tmp_path: Path) -> None:
    session = _session(tmp_path)
    prompt, truncated = build_agent_summary_prompt(session, max_bytes=120)

    assert truncated is True
    assert len(prompt.encode("utf-8")) <= 120


def test_summarize_agent_session_with_fake_codex(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = tmp_path / "codex"
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "prompt = sys.stdin.read()\n"
        "assert 'Latest assistant message:' in prompt\n"
        "print('Project HoldSpeak; agent is asking whether to add the summarizer.')\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}")

    summary = summarize_agent_session(
        _session(tmp_path),
        provider="codex",
        timeout_seconds=5,
        now=datetime(2026, 5, 10, tzinfo=timezone.utc),
    )

    assert summary.summary == "Project HoldSpeak; agent is asking whether to add the summarizer."
    assert summary.provider == "codex"
    assert summary.source_session_id == "sess-1"
    assert summary.cwd == str(tmp_path)
    assert summary.generated_at == "2026-05-10T00:00:00Z"


def test_summarize_agent_session_parses_fake_claude_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = tmp_path / "claude"
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "sys.stdin.read()\n"
        "print(json.dumps({'result': 'Agent context compressed.'}))\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}")

    summary = summarize_agent_session(
        _session(tmp_path),
        provider="claude",
        timeout_seconds=5,
    )

    assert summary.summary == "Agent context compressed."
