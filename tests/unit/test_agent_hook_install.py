"""HSM-17-02: the one-command hook install — idempotent, reversible,
foreign-hook-preserving."""

from __future__ import annotations

import io
import json
from pathlib import Path
from types import SimpleNamespace

from holdspeak.agent_context import claude_hook_template
from holdspeak.agent_context.hooks import install_agent_hooks, uninstall_agent_hooks
from holdspeak.commands.agent_hook import run_agent_hook_command


def _settings(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_install_creates_the_settings_file_with_our_events(tmp_path: Path) -> None:
    target = tmp_path / ".claude" / "settings.json"

    result = install_agent_hooks(target, claude_hook_template())

    assert result["created_file"] is True
    hooks = _settings(target)["hooks"]
    for event in ("SessionStart", "UserPromptSubmit", "Notification", "PostToolUse", "Stop", "SessionEnd"):
        assert event in hooks, event
        commands = [h["command"] for entry in hooks[event] for h in entry["hooks"]]
        assert any("agent-hook ingest --agent claude" in c for c in commands)


def test_install_is_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    install_agent_hooks(target, claude_hook_template())
    first = target.read_text(encoding="utf-8")

    install_agent_hooks(target, claude_hook_template())

    assert target.read_text(encoding="utf-8") == first


def test_install_converges_when_capture_flag_changes(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    install_agent_hooks(target, claude_hook_template())

    install_agent_hooks(target, claude_hook_template(capture_messages=True))

    stop_entries = _settings(target)["hooks"]["Stop"]
    assert len(stop_entries) == 1  # replaced, not stacked
    assert "--capture-messages" in stop_entries[0]["hooks"][0]["command"]


def test_install_preserves_foreign_hooks_and_settings(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    target.write_text(
        json.dumps(
            {
                "model": "opus",
                "hooks": {
                    "Stop": [
                        {"hooks": [{"type": "command", "command": "/usr/local/bin/my-logger"}]}
                    ]
                },
            }
        ),
        encoding="utf-8",
    )

    install_agent_hooks(target, claude_hook_template())

    settings = _settings(target)
    assert settings["model"] == "opus"
    stop_commands = [
        h["command"] for entry in settings["hooks"]["Stop"] for h in entry["hooks"]
    ]
    assert "/usr/local/bin/my-logger" in stop_commands
    assert any("agent-hook ingest" in c for c in stop_commands)


def test_uninstall_reverses_install_exactly(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    original = {
        "model": "opus",
        "hooks": {
            "Stop": [{"hooks": [{"type": "command", "command": "/usr/local/bin/my-logger"}]}]
        },
    }
    target.write_text(json.dumps(original), encoding="utf-8")
    install_agent_hooks(target, claude_hook_template())

    result = uninstall_agent_hooks(target)

    assert set(result["removed_events"]) == {
        "SessionStart", "CwdChanged", "UserPromptSubmit", "Notification",
        "PostToolUse", "Stop", "SessionEnd",
    }
    assert _settings(target) == original


def test_uninstall_drops_empty_hooks_object(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    install_agent_hooks(target, claude_hook_template())

    uninstall_agent_hooks(target)

    assert "hooks" not in _settings(target)


def test_uninstall_missing_file_is_a_noop(tmp_path: Path) -> None:
    result = uninstall_agent_hooks(tmp_path / "absent.json")
    assert result["file_missing"] is True


def test_install_refuses_to_rewrite_unreadable_json(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    target.write_text("{not json", encoding="utf-8")

    import pytest

    with pytest.raises(ValueError, match="refusing to rewrite"):
        install_agent_hooks(target, claude_hook_template())
    assert target.read_text(encoding="utf-8") == "{not json"


def test_cli_install_and_uninstall_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    out = io.StringIO()
    args = SimpleNamespace(
        agent_hook_action="install", agent="claude",
        capture_messages=False, settings_path=str(target),
    )

    rc = run_agent_hook_command(args, stream=out)

    assert rc == 0
    assert "claude: created" in out.getvalue()
    assert "NEW coder sessions" in out.getvalue()

    out = io.StringIO()
    args = SimpleNamespace(
        agent_hook_action="uninstall", agent="claude", settings_path=str(target),
    )
    rc = run_agent_hook_command(args, stream=out)

    assert rc == 0
    assert "removed our hooks" in out.getvalue()
    assert _settings(target) == {}


def test_cli_install_all_requires_agent_for_settings_override(tmp_path: Path) -> None:
    out = io.StringIO()
    args = SimpleNamespace(
        agent_hook_action="install", agent="all",
        capture_messages=False, settings_path=str(tmp_path / "x.json"),
    )

    rc = run_agent_hook_command(args, stream=out)

    assert rc == 2
