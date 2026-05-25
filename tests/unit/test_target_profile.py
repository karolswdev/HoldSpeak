"""Tests for dictation target-profile detection."""

from __future__ import annotations

import pytest

from holdspeak.target_profile import (
    detect_target_profile,
    detect_target_profile_with_override,
    normalize_target_profile_override,
)


def test_detects_codex_cli_from_terminal_title() -> None:
    profile = detect_target_profile(
        {"app_name": "WezTerm", "window_title": "karol@host: ~/dev/HoldSpeak - codex"}
    )

    assert profile.id == "codex_cli"
    assert profile.label == "Codex CLI"
    assert profile.confidence > 0.9


def test_detects_claude_code_from_terminal_title() -> None:
    profile = detect_target_profile(
        {"process_name": "kitty", "window_title": "Claude Code - HoldSpeak"}
    )

    assert profile.id == "claude_code"


def test_detects_terminal_shell_without_agent_signal() -> None:
    profile = detect_target_profile({"app_name": "Terminal", "window_title": "zsh"})

    assert profile.id == "terminal_shell"


def test_detects_generic_browser_text_target() -> None:
    profile = detect_target_profile({"app_name": "Firefox", "window_title": "Issue comment"})

    assert profile.id == "browser"
    assert profile.label == "Browser"


def test_detects_generic_editor_text_target() -> None:
    profile = detect_target_profile({"app_name": "Visual Studio Code", "window_title": "notes.md"})

    assert profile.id == "editor"


def test_detects_generic_chat_target() -> None:
    profile = detect_target_profile({"app_name": "Slack", "window_title": "HoldSpeak"})

    assert profile.id == "chat"


def test_explicit_profile_wins() -> None:
    profile = detect_target_profile({"profile": "chat", "app_name": "Terminal"})

    assert profile.id == "chat"
    assert profile.source == "explicit"


def test_unknown_when_no_hints() -> None:
    profile = detect_target_profile({})

    assert profile.id == "unknown"
    assert profile.confidence == 0.0


def test_manual_override_wins_over_hints() -> None:
    profile = detect_target_profile_with_override(
        {"app_name": "Firefox", "window_title": "Issue comment"},
        "codex_cli",
    )

    assert profile.id == "codex_cli"
    assert profile.source == "override"
    assert profile.confidence == 1.0


def test_auto_override_uses_detection() -> None:
    profile = detect_target_profile_with_override(
        {"app_name": "Firefox", "window_title": "Issue comment"},
        "auto",
    )

    assert profile.id == "browser"
    assert profile.source == "hints"


def test_rejects_unknown_manual_override() -> None:
    with pytest.raises(ValueError, match="target_profile_override"):
        normalize_target_profile_override("spreadsheet")
