"""The Conductor K1: agent readiness (detect, one-press hooks, doctor).

Real producers: the real hook installer writes the real settings file under a
temp home; detect reads it back with the installer's own marker.  The seams
are PATH (``which``) and the home directory.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import pytest
from fastapi.testclient import TestClient

from holdspeak.agent_context.hooks import AGENT_HOOK_COMMAND_MARKER, claude_hook_template
from holdspeak.commands.doctor import _check_coding_agents
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, ValidationError
from holdspeak.services.onboarding_service import OnboardingService, detect_agents

OWNER = Principal(PrincipalKind.OWNER, "onboarding-owner")
FOREIGN = {"matcher": "", "hooks": [{"type": "command", "command": "/usr/local/bin/my-own-hook"}]}


def _which(*present: str):
    def which(name: str) -> Optional[str]:
        return f"/opt/bin/{name}" if name in present else None

    return which


def _service(home: Path, *present: str) -> OnboardingService:
    return OnboardingService(
        home_provider=lambda: home, environ={}, macos=SimpleNamespace(), config_loader=lambda: None,
        which=_which(*present),
    )


def _rows(detected: dict) -> dict[str, dict]:
    return {row["id"]: row for row in detected["agents"]}


def test_detect_on_a_bare_home_finds_nothing_and_says_unknown_not_no(tmp_path) -> None:
    detected = detect_agents(which=_which(), home=tmp_path, environ={}, platform="darwin")
    rows = _rows(detected)
    assert set(rows) == {"claude", "codex"}
    for row in rows.values():
        assert row["installed"] is False and row["hooks"] == "missing" and row["verb"] is None
        assert row["signed_in"] == "unknown"  # a Keychain / keyring token is not a file
        assert row["ready"] is False
    assert rows["claude"]["hooks_path"] == str(tmp_path / ".claude" / "settings.json")
    assert rows["codex"]["hooks_path"] == str(tmp_path / ".codex" / "hooks.json")
    assert detected["tmux"] == {"installed": False, "path": None, "install_hint": "brew install tmux"}
    assert detected["holdspeak"]["on_path"] is False
    assert detected["holdspeak"]["hook_executable"]


def test_detect_reads_our_hook_entries_with_the_installer_marker(tmp_path) -> None:
    claude = tmp_path / ".claude" / "settings.json"
    claude.parent.mkdir()
    ours = claude_hook_template()
    claude.write_text(json.dumps({"model": "opus", "hooks": {**ours["hooks"], "PreCompact": [FOREIGN]}}))
    codex = tmp_path / ".codex" / "hooks.json"
    codex.parent.mkdir()
    codex.write_text(json.dumps({"hooks": {"Stop": [FOREIGN]}}))  # foreign only
    rows = _rows(detect_agents(which=_which("claude", "codex", "tmux"), home=tmp_path, environ={}))
    assert rows["claude"]["hooks"] == "installed" and rows["claude"]["ready"] is True
    assert rows["codex"]["hooks"] == "missing" and rows["codex"]["ready"] is False
    assert rows["claude"]["verb"] == rows["codex"]["verb"] == "Use it"

    partial = {"hooks": {"Stop": ours["hooks"]["Stop"]}}
    claude.write_text(json.dumps(partial))
    assert _rows(detect_agents(which=_which("claude"), home=tmp_path, environ={}))["claude"]["hooks"] == "partial"
    claude.write_text("{not json")
    assert _rows(detect_agents(which=_which("claude"), home=tmp_path, environ={}))["claude"]["hooks"] == "unreadable"


def test_detect_reads_sign_in_from_files_without_reading_a_secret(tmp_path) -> None:
    (tmp_path / ".claude.json").write_text(json.dumps({"oauthAccount": {"accountUuid": "u-1"}}))
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".codex" / "auth.json").write_text(json.dumps({"tokens": {"access_token": "SECRET"}}))
    detected = detect_agents(which=_which("claude", "codex"), home=tmp_path, environ={})
    rows = _rows(detected)
    assert rows["claude"]["signed_in"] == "yes" and rows["codex"]["signed_in"] == "yes"
    assert "SECRET" not in repr(detected)
    (tmp_path / ".codex" / "auth.json").write_text(json.dumps({"OPENAI_API_KEY": None, "tokens": None}))
    assert _rows(detect_agents(which=_which("codex"), home=tmp_path, environ={}))["codex"]["signed_in"] == "no"
    env_key = detect_agents(which=_which(), home=tmp_path / "empty", environ={"ANTHROPIC_API_KEY": "k"})
    assert _rows(env_key)["claude"]["signed_in"] == "yes"


def test_use_it_installs_the_merged_file_and_is_idempotent(tmp_path) -> None:
    claude = tmp_path / ".claude" / "settings.json"
    claude.parent.mkdir()
    claude.write_text(json.dumps({"model": "opus", "hooks": {"Stop": [FOREIGN]}}))
    service = _service(tmp_path, "claude", "tmux")
    first = service.agents_use(OWNER, {"agent": "claude"})
    assert first["used"]["agent"] == "claude" and first["used"]["created_file"] is False
    assert _rows(first)["claude"]["hooks"] == "installed" and _rows(first)["claude"]["ready"] is True
    written = json.loads(claude.read_text())
    assert written["model"] == "opus"
    assert written["hooks"]["Stop"][0] == FOREIGN  # foreign hooks kept
    once = claude.read_text()
    service.agents_use(OWNER, {"agent": "claude"})
    assert claude.read_text() == once  # idempotent: our entries replaced, never stacked
    ours = [e for e in written["hooks"]["Stop"] if AGENT_HOOK_COMMAND_MARKER in json.dumps(e)]
    assert len(ours) == 1


def test_use_it_creates_the_codex_file_and_refuses_by_name(tmp_path) -> None:
    service = _service(tmp_path, "codex")
    result = service.agents_use(OWNER, {"agent": "codex"})
    assert result["used"]["created_file"] is True
    assert (tmp_path / ".codex" / "hooks.json").is_file()
    with pytest.raises(ConflictError) as caught:
        service.agents_use(OWNER, {"agent": "claude"})
    assert caught.value.code == "claude_not_installed"
    assert not (tmp_path / ".claude").exists()  # a refusal writes nothing
    with pytest.raises(ValidationError) as unknown:
        service.agents_use(OWNER, {"agent": "aider"})
    assert unknown.value.code == "agent_unknown"


def test_use_it_never_rewrites_an_unreadable_settings_file(tmp_path) -> None:
    claude = tmp_path / ".claude" / "settings.json"
    claude.parent.mkdir()
    claude.write_text("{broken")
    with pytest.raises(ConflictError) as caught:
        _service(tmp_path, "claude").agents_use(OWNER, {"agent": "claude"})
    assert caught.value.code == "agent_settings_unreadable"
    assert claude.read_text() == "{broken"


# ── the routes ───────────────────────────────────────────────────────────


def _client(service: OnboardingService) -> TestClient:
    from fastapi import FastAPI, Request

    from holdspeak.web.routes.onboarding import build_onboarding_router

    app = FastAPI()

    @app.middleware("http")
    async def owner(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_onboarding_router(SimpleNamespace(onboarding_service=service)))
    return TestClient(app)


def test_the_agent_routes_detect_install_and_refuse(tmp_path) -> None:
    client = _client(_service(tmp_path, "claude", "tmux"))
    detect = client.get("/api/onboarding/agents")
    assert detect.status_code == 200
    assert set(detect.json()) == {"agents", "tmux", "holdspeak"}
    use = client.post("/api/onboarding/agents/use", json={"agent": "claude"})
    assert use.status_code == 200, use.text
    assert _rows(use.json())["claude"]["hooks"] == "installed"
    once = (tmp_path / ".claude" / "settings.json").read_text()
    again = client.post("/api/onboarding/agents/use", json={"agent": "claude"})
    assert again.status_code == 200 and (tmp_path / ".claude" / "settings.json").read_text() == once
    refused = client.post("/api/onboarding/agents/use", json={"agent": "codex"})
    assert refused.status_code == 409 and refused.json()["code"] == "codex_not_installed"
    assert client.post("/api/onboarding/agents/use", json={"agent": ""}).status_code == 400
    assert client.post("/api/onboarding/agents/use", content=b"[]").status_code == 400


def test_the_agent_routes_are_owner_only() -> None:
    from holdspeak.principals import PrincipalRight, required_right

    for method, path in (("GET", "/api/onboarding/agents"), ("POST", "/api/onboarding/agents/use")):
        assert required_right(method, path) is PrincipalRight.OWNER


# ── doctor ───────────────────────────────────────────────────────────────


def _detected(tmp_path: Path, *present: str) -> dict:
    return detect_agents(which=_which(*present), home=tmp_path, environ={}, platform="linux")


def test_doctor_info_when_no_agent_is_installed(tmp_path) -> None:
    check = _check_coding_agents(_detected(tmp_path, "tmux"))
    assert check.name == "Coding agents" and check.status == "INFO" and check.fix is None


def test_doctor_warns_with_the_install_fix_when_hooks_are_missing(tmp_path) -> None:
    check = _check_coding_agents(_detected(tmp_path, "claude", "tmux"))
    assert check.status == "WARN"
    assert "`holdspeak agent-hook install --agent claude`" in check.fix


def test_doctor_passes_once_one_agent_has_hooks(tmp_path) -> None:
    _service(tmp_path, "claude").agents_use(OWNER, {"agent": "claude"})
    check = _check_coding_agents(_detected(tmp_path, "claude", "tmux"))
    assert check.status == "PASS" and "Claude Code hooks installed" in check.detail


def test_doctor_warns_when_tmux_is_missing_with_the_platform_hint(tmp_path) -> None:
    _service(tmp_path, "claude").agents_use(OWNER, {"agent": "claude"})
    check = _check_coding_agents(_detected(tmp_path, "claude"))
    assert check.status == "WARN" and "`sudo apt-get install tmux`" in check.fix
    mac = _check_coding_agents(detect_agents(which=_which("claude"), home=tmp_path, environ={}, platform="darwin"))
    assert "`brew install tmux`" in mac.fix

