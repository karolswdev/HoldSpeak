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


# --- HS-39-02: target correction nudge -------------------------------------

from holdspeak.plugins.dictation.corrections import Correction  # noqa: E402
from holdspeak.target_profile import apply_target_correction  # noqa: E402


def _target_correction(text: str, value: str, seq: int = 1) -> Correction:
    return Correction(kind="target", key=text, value=value, sequence=seq)


def test_target_correction_noop_without_corrections() -> None:
    detected = detect_target_profile({"app_name": "Safari"})
    assert detected.id == "browser"
    nudged = apply_target_correction(detected, text="open the pr", corrections=None)
    assert nudged is detected  # byte-identical (same object)


def test_target_correction_redirects_for_similar_context() -> None:
    detected = detect_target_profile({"app_name": "Safari"})  # browser, 0.78
    corrections = [_target_correction("open the pr in claude", "claude_code")]
    nudged = apply_target_correction(
        detected, text="open the pr in claude please", corrections=corrections
    )
    assert nudged.id == "claude_code"
    assert nudged.source == "correction"


def test_target_correction_never_overrides_manual_override() -> None:
    overridden = detect_target_profile_with_override(
        {"app_name": "Safari"}, override="codex_cli"
    )
    assert overridden.source == "override"
    corrections = [_target_correction("open the pr in claude", "claude_code")]
    nudged = apply_target_correction(
        overridden, text="open the pr in claude", corrections=corrections
    )
    assert nudged.id == "codex_cli"  # manual override wins
    assert nudged is overridden


def test_target_correction_ignores_dissimilar_and_unknown() -> None:
    detected = detect_target_profile({"app_name": "Safari"})
    # Dissimilar context → no nudge.
    far = apply_target_correction(
        detected,
        text="completely different sentence entirely",
        corrections=[_target_correction("open the pr in claude", "claude_code")],
    )
    assert far.id == "browser"
    # Unknown/non-selectable value → no nudge.
    unknown = apply_target_correction(
        detected,
        text="open the pr in claude",
        corrections=[_target_correction("open the pr in claude", "not_a_profile")],
    )
    assert unknown.id == "browser"
