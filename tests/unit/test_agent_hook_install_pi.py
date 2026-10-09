"""`holdspeak agent-hook install|uninstall --agent pi` (owner catch 2026-10-08):
pi has no hook settings file, its hooks ride every launch as the extension,
so the CLI accepts the name and says so instead of refusing it."""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

import pytest

from holdspeak.commands.agent_hook import build_argparse_subparsers, run_agent_hook_command
from holdspeak.delivery.pi_launch import EXTENSION_PATH


def _run(argv: list[str], *, home: Path, monkeypatch) -> tuple[int, str]:
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home / "claude"))
    monkeypatch.setenv("CODEX_HOME", str(home / "codex"))
    parser = argparse.ArgumentParser()
    build_argparse_subparsers(parser)
    args = parser.parse_args(argv)
    out = io.StringIO()
    code = run_agent_hook_command(args, stream=out)
    return code, out.getvalue()


def test_install_pi_says_every_launch_loads_its_hooks(tmp_path, monkeypatch) -> None:
    code, text = _run(["install", "--agent", "pi"], home=tmp_path, monkeypatch=monkeypatch)
    assert code == 0
    assert "pi: nothing to write" in text
    assert str(EXTENSION_PATH) in text
    assert "EXTENSION IN" in text
    assert "Remove them any time" not in text
    assert not (tmp_path / "claude").exists() and not (tmp_path / "codex").exists()


def test_install_all_writes_claude_and_codex_and_names_pi(tmp_path, monkeypatch) -> None:
    code, text = _run(["install", "--agent", "all"], home=tmp_path, monkeypatch=monkeypatch)
    assert code == 0
    assert "pi: nothing to write" in text
    assert "claude:" in text and "codex:" in text
    claude = json.loads((tmp_path / "claude" / "settings.json").read_text(encoding="utf-8"))
    codex = json.loads((tmp_path / "codex" / "hooks.json").read_text(encoding="utf-8"))
    assert "SessionStart" in claude["hooks"] and "PermissionRequest" in codex["hooks"]


def test_uninstall_pi_says_nothing_to_remove_and_touches_no_file(tmp_path, monkeypatch) -> None:
    (tmp_path / "claude").mkdir()
    (tmp_path / "codex").mkdir()
    before = {
        "claude": '{"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "theirs"}]}]}}',
        "codex": '{"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "theirs"}]}]}}',
    }
    (tmp_path / "claude" / "settings.json").write_text(before["claude"], encoding="utf-8")
    (tmp_path / "codex" / "hooks.json").write_text(before["codex"], encoding="utf-8")
    code, text = _run(["uninstall", "--agent", "pi"], home=tmp_path, monkeypatch=monkeypatch)
    assert code == 0
    assert "pi: nothing to remove" in text
    assert (tmp_path / "claude" / "settings.json").read_text(encoding="utf-8") == before["claude"]
    assert (tmp_path / "codex" / "hooks.json").read_text(encoding="utf-8") == before["codex"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["claude", "codex"]


def test_settings_path_with_pi_is_a_usage_error(tmp_path, monkeypatch) -> None:
    code, _ = _run(
        ["install", "--agent", "pi", "--settings-path", str(tmp_path / "x.json")],
        home=tmp_path, monkeypatch=monkeypatch,
    )
    assert code == 2
    assert not (tmp_path / "x.json").exists()
