"""AG13: the installed HoldSpeak skill reaches CLI and launch directories."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest

from holdspeak import cli_entry
from holdspeak.agent_skill import (
    PREVIOUS_SKILL_SHA256,
    SkillOwnershipError,
    install_codex_repo_skill,
    install_skill,
    skill_state,
    skill_text,
    uninstall_skill,
)
from holdspeak.coder_gate import write_spawn_settings


def test_skill_cli_prints_the_installed_resource(monkeypatch, capsys) -> None:
    monkeypatch.setattr("sys.argv", ["holdspeak", "--skill"])
    with pytest.raises(SystemExit) as exited:
        cli_entry.main()
    assert exited.value.code == 0
    assert capsys.readouterr().out == skill_text()


def test_owner_started_skill_uses_native_mcp_but_launched_tasks_keep_credential_refusal() -> None:
    text = skill_text()
    assert "For a HoldSpeak-launched task" in text
    assert "HOLDSPEAK_AGENT_CREDENTIAL" in text
    assert "If it is absent or empty, stop and report that this launch has no desk credential." in text
    assert "For an owner-started Claude or Codex session, use the Setup-installed HoldSpeak MCP connection." in text
    assert "If `HOLDSPEAK_AGENT_CREDENTIAL` is absent or empty, stop" not in text


def test_previous_packaged_skill_upgrades_and_stop_removes_only_owned_versions(tmp_path: Path) -> None:
    legacy = skill_text().replace(
        "1. Identify how this session started.\n"
        "   - For a HoldSpeak-launched task, check `HOLDSPEAK_AGENT_CREDENTIAL` first. If it is absent or empty, stop and report that this launch has no desk credential. Do not use an owner-started path for that task.\n"
        "   - For an owner-started Claude or Codex session, use the Setup-installed HoldSpeak MCP connection. If it is unavailable, report that HoldSpeak desk access is unavailable and stop before desk calls.",
        "1. Check the launch credential first. If `HOLDSPEAK_AGENT_CREDENTIAL` is absent or empty, stop and report that this launch has no desk credential.",
    )
    assert hashlib.sha256(legacy.encode("utf-8")).hexdigest() == PREVIOUS_SKILL_SHA256
    config_dir = tmp_path / "claude"
    path = config_dir / "skills" / "holdspeak" / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(legacy, encoding="utf-8")
    assert skill_state(path) == "outdated"
    assert install_skill(config_dir, "claude") == path
    assert skill_state(path) == "installed"
    assert uninstall_skill(config_dir, "claude") is True
    assert not path.exists()

    path.parent.mkdir(parents=True)
    path.write_text("owner's custom skill\n", encoding="utf-8")
    assert skill_state(path) == "foreign"
    with pytest.raises(SkillOwnershipError):
        install_skill(config_dir, "claude")
    assert path.read_text(encoding="utf-8") == "owner's custom skill\n"
    assert uninstall_skill(config_dir, "claude") is False


def test_spawn_settings_directory_carries_both_agent_skill_layouts(tmp_path: Path) -> None:
    settings = write_spawn_settings(tmp_path / "settings.json", project_root=tmp_path / "project")
    assert settings.is_file()
    claude = settings.parent / ".claude" / "skills" / "holdspeak" / "SKILL.md"
    codex = settings.parent / "skills" / "holdspeak" / "SKILL.md"
    assert claude.read_text(encoding="utf-8") == skill_text()
    assert codex.read_text(encoding="utf-8") == skill_text()


def test_codex_repo_skill_uses_the_native_repository_layout(tmp_path: Path) -> None:
    path = install_codex_repo_skill(tmp_path)
    assert path == tmp_path / ".agents" / "skills" / "holdspeak" / "SKILL.md"
    assert path.read_text(encoding="utf-8") == skill_text()


@pytest.mark.parametrize("agent,relative", [
    ("claude", Path("skills") / "holdspeak" / "SKILL.md"),
    ("codex", Path("skills") / "holdspeak" / "SKILL.md"),
])
def test_connect_skill_install_preserves_config_and_is_idempotent(
    tmp_path: Path, agent: str, relative: Path
) -> None:
    config_dir = tmp_path / agent
    config_dir.mkdir()
    settings = config_dir / ("settings.json" if agent == "claude" else "hooks.json")
    original = {"model": "opus", "hooks": {"Stop": [{"hooks": []}]}}
    settings.write_text(json.dumps(original) + "\n", encoding="utf-8")
    foreign = config_dir / "skills" / "foreign" / "SKILL.md"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("foreign\n", encoding="utf-8")

    path = install_skill(config_dir, agent)
    once = path.read_bytes()
    again = install_skill(config_dir, agent)
    assert again == path and path.read_bytes() == once
    assert json.loads(settings.read_text(encoding="utf-8")) == original
    assert foreign.read_text(encoding="utf-8") == "foreign\n"
    expected = config_dir / relative
    assert path == expected
    assert path.read_text(encoding="utf-8") == skill_text()
