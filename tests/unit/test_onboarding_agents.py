"""The Conductor K1: agent readiness (detect, one-press hooks, doctor).

Real producers: the real hook installer writes the real settings file under a
temp home; detect reads it back with the installer's own marker.  The install
runs through the real hub over authenticated HTTP as the admitted kernel
operation ``agent_hooks.install``, and its receipts are read from the kernel
tables.  The seams are PATH (``which``), the home directory and the
environment.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

import pytest

from holdspeak.agent_context.hooks import (
    AGENT_HOOK_COMMAND_MARKER,
    claude_hook_template,
    install_agent_hooks,
)
from holdspeak.agent_context.native_binding import NativeBindingError, binding_state, install_binding
from holdspeak.commands.doctor import _check_coding_agents
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition
from holdspeak.services.onboarding_service import agent_hook_template, detect_agents

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402

OWNER = Principal(PrincipalKind.OWNER, "onboarding-owner")
FOREIGN = {"matcher": "", "hooks": [{"type": "command", "command": "/usr/local/bin/my-own-hook"}]}


def _which(*present: str):
    def which(name: str) -> Optional[str]:
        return f"/opt/bin/{name}" if name in present else None

    return which


def _mcp_stub(home: Path) -> str:
    """A harmless executable entrypoint for the isolated native CLI double."""
    path = home / "bin" / "holdspeak-mcp"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("#!/bin/sh\nexit 0\n")
        path.chmod(0o755)
    return str(path)


def _rows(detected: dict) -> dict[str, dict]:
    return {row["id"]: row for row in detected["agents"]}


def _detect(home: Path, *present: str, env: Optional[dict[str, str]] = None, platform: str = "darwin") -> dict:
    base = _which(*present)
    mcp = _mcp_stub(home)
    return detect_agents(
        which=lambda name: mcp if name == "holdspeak-mcp" else base(name),
        home=home, environ=env or {}, platform=platform,
    )


# ── detect ───────────────────────────────────────────────────────────────


def test_detect_on_a_bare_home_finds_nothing_and_says_unknown_not_no(tmp_path) -> None:
    detected = _detect(tmp_path)
    rows = _rows(detected)
    assert set(rows) == {"claude", "codex", "pi"}
    for agent in ("claude", "codex"):
        row = rows[agent]
        assert row["installed"] is False and row["hooks"] == "missing" and row["verb"] is None
        assert row["signed_in"] == "unknown"  # a Keychain / keyring token is not a file
        assert row["ready"] is False
    # pi (pi spike #1020): its hooks ship with HoldSpeak (the extension); it
    # signs in to nothing of its own (the hub's engine for coding work).
    assert rows["pi"]["installed"] is False and rows["pi"]["hooks"] == "installed"
    assert rows["pi"]["ready"] is False and rows["pi"]["verb"] is None
    assert rows["claude"]["hooks_path"] == str(tmp_path / ".claude" / "settings.json")
    assert rows["codex"]["hooks_path"] == str(tmp_path / ".codex" / "hooks.json")
    assert detected["tmux"] == {"installed": False, "path": None, "version": None, "install_hint": "brew install tmux"}
    assert detected["holdspeak"]["hook_executable"]


def test_detect_reads_our_hook_entries_with_the_installer_marker(tmp_path) -> None:
    claude = tmp_path / ".claude" / "settings.json"
    claude.parent.mkdir()
    ours = claude_hook_template()
    claude.write_text(json.dumps({"model": "opus", "hooks": {**ours["hooks"], "PreCompact": [FOREIGN]}}))
    codex = tmp_path / ".codex" / "hooks.json"
    codex.parent.mkdir()
    codex.write_text(json.dumps({"hooks": {"Stop": [FOREIGN]}}))  # foreign only
    rows = _rows(_detect(tmp_path, "claude", "codex", "tmux"))
    assert rows["claude"]["hooks"] == "installed" and rows["claude"]["mcp"] == "missing"
    assert rows["claude"]["ready"] is False
    assert rows["codex"]["hooks"] == "missing" and rows["codex"]["ready"] is False
    assert rows["claude"]["verb"] == rows["codex"]["verb"] == "Use it"

    claude.write_text(json.dumps({"hooks": {"Stop": ours["hooks"]["Stop"]}}))
    assert _rows(_detect(tmp_path, "claude"))["claude"]["hooks"] == "partial"
    claude.write_text("{not json")
    assert _rows(_detect(tmp_path, "claude"))["claude"]["hooks"] == "unreadable"


def _broken_template() -> dict[str, Any]:
    """Our hooks, pointing at a holdspeak that does not exist (a moved venv)."""
    text = json.dumps(claude_hook_template())
    command = claude_hook_template()["hooks"]["Stop"][0]["hooks"][0]["command"]
    executable = command.split(" ", 1)[0]
    return json.loads(text.replace(json.dumps(executable)[1:-1], "/nonexistent/venv/bin/holdspeak"))


def test_a_hook_whose_command_cannot_run_is_not_ready(tmp_path) -> None:
    """Astra r1 finding 3: a hook that would exit 127 never reads ready."""
    claude = tmp_path / ".claude" / "settings.json"
    claude.parent.mkdir()
    claude.write_text(json.dumps(_broken_template()))
    row = _rows(_detect(tmp_path, "claude", "tmux"))["claude"]
    assert row["hooks"] == "broken" and row["ready"] is False
    bare = json.loads(json.dumps(claude_hook_template()))
    for entries in bare["hooks"].values():
        for hook in entries[0]["hooks"]:
            hook["command"] = f"holdspeak {AGENT_HOOK_COMMAND_MARKER} --agent claude"
    claude.write_text(json.dumps(bare))
    assert _rows(_detect(tmp_path, "claude"))["claude"]["hooks"] == "broken"  # bare holdspeak, not on PATH
    assert _rows(_detect(tmp_path, "claude", "holdspeak"))["claude"]["hooks"] == "installed"


def test_detect_follows_the_agent_config_dir_variables(tmp_path) -> None:
    """Astra r1 finding 2: CODEX_HOME and CLAUDE_CONFIG_DIR move the file the agent reads."""
    env = {"CODEX_HOME": str(tmp_path / "codex-home"), "CLAUDE_CONFIG_DIR": str(tmp_path / "claude-dir")}
    rows = _rows(_detect(tmp_path, "claude", "codex", env=env))
    assert rows["codex"]["hooks_path"] == str(tmp_path / "codex-home" / "hooks.json")
    assert rows["claude"]["hooks_path"] == str(tmp_path / "claude-dir" / "settings.json")
    install_agent_hooks(tmp_path / ".codex" / "hooks.json", agent_hook_template("codex"))  # the default dir
    assert _rows(_detect(tmp_path, "codex", env=env))["codex"]["hooks"] == "missing"


@pytest.mark.parametrize("text", ["{}\n", "not json", "null", json.dumps({"claudeAiOauth": {"accessToken": ""}})])
def test_claude_sign_in_is_unknown_on_inconclusive_files(tmp_path, text) -> None:
    """Astra r1 finding 4: a file's size proves nothing."""
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / ".credentials.json").write_text(text)
    (tmp_path / ".claude.json").write_text(json.dumps({"oauthAccount": {"accountUuid": "u-1"}}))  # metadata only
    assert _rows(_detect(tmp_path, "claude"))["claude"]["signed_in"] == "unknown"


@pytest.mark.parametrize("text", ["{}", "null", "not json", json.dumps({"OPENAI_API_KEY": None, "tokens": None})])
def test_codex_sign_in_is_unknown_on_inconclusive_files(tmp_path, text) -> None:
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".codex" / "auth.json").write_text(text)
    assert _rows(_detect(tmp_path, "codex"))["codex"]["signed_in"] == "unknown"


def test_sign_in_is_yes_only_from_a_credential_and_never_reads_it_out(tmp_path) -> None:
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / ".credentials.json").write_text(
        json.dumps({"claudeAiOauth": {"accessToken": "SECRET-A", "refreshToken": "SECRET-R"}}))
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".codex" / "auth.json").write_text(json.dumps({"tokens": {"access_token": "SECRET-C"}}))
    detected = _detect(tmp_path, "claude", "codex")
    rows = _rows(detected)
    assert rows["claude"]["signed_in"] == "yes" and rows["codex"]["signed_in"] == "yes"
    assert "SECRET" not in repr(detected)
    env_key = _detect(tmp_path / "empty", env={"ANTHROPIC_API_KEY": "k"})
    assert _rows(env_key)["claude"]["signed_in"] == "yes"


# ── the one press, through the hub, as an admitted kernel operation ──────


NAME = "agent_hooks.install"


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _native_runner(argv, *, cwd, env, **kwargs):
    """Native CLI double: mutate only the isolated HOME/config files."""
    agent = Path(argv[0]).name
    action = argv[2]
    if agent == "claude":
        config = Path(env.get("CLAUDE_CONFIG_DIR") or env["HOME"]) / ".claude.json"
        data = json.loads(config.read_text()) if config.is_file() else {}
        servers = data.setdefault("mcpServers", {})
        if action == "add":
            servers["holdspeak"] = {"type": "stdio", "command": argv[-1], "args": [], "env": {}}
        else:
            servers.pop("holdspeak", None)
        if not servers:
            data.pop("mcpServers", None)
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(json.dumps(data))
    else:
        config = Path(env.get("CODEX_HOME") or Path(env["HOME"]) / ".codex") / "config.toml"
        current = config.read_text() if config.is_file() else ""
        block = f"[mcp_servers.holdspeak]\ncommand = \"{argv[-1]}\"\n"
        if action == "add":
            current = current + ("\n" if current and not current.endswith("\n") else "") + block
        else:
            current = current.replace(block, "")
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(current)
    return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")


def _seat(hub: Hub, home: Path, *present: str, env: Optional[dict[str, str]] = None) -> Any:
    """The hub's own OnboardingService, the one the operation is bound to, on a temp home and PATH."""
    service = hub.root.operations.target(NAME)
    service._home = lambda: home
    base = _which(*present)
    mcp = _mcp_stub(home)
    service._which = lambda name: mcp if name == "holdspeak-mcp" else base(name)
    service._environ = env or {}
    service._agent_runner = _native_runner
    return service


def _receipts(hub: Hub) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT o.operation_id, o.state, r.outcome FROM kernel_operations o JOIN kernel_receipts r"
            " ON r.operation_id=o.operation_id WHERE o.name=? ORDER BY o.created_at, o.rowid", (NAME,))]


def test_use_it_is_admitted_with_a_receipt_and_is_idempotent(hub, tmp_path) -> None:
    home = tmp_path / "home"
    claude = home / ".claude" / "settings.json"
    claude.parent.mkdir(parents=True)
    claude.write_text(json.dumps({"model": "opus", "hooks": {"Stop": [FOREIGN]}}))
    _seat(hub, home, "claude", "tmux")
    answer = hub.client.post("/api/onboarding/agents/use", json={"agent": "claude"})
    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert body["used"]["agent"] == "claude" and body["used"]["path"] == str(claude)
    assert body["used"]["skill"] == str(home / ".claude" / "skills" / "holdspeak" / "SKILL.md")
    assert (home / ".claude" / "skills" / "holdspeak" / "SKILL.md").is_file()
    assert _rows(body)["claude"]["hooks"] == "installed"
    assert _rows(body)["claude"]["mcp"] == "installed"
    assert body["used"]["mcp"]["command"] == _mcp_stub(home)
    assert _rows(body)["claude"]["skill"] == "installed" and _rows(body)["claude"]["ready"] is True
    assert body["operation_id"] and body["receipt"]["outcome"] == "succeeded"
    written = json.loads(claude.read_text())
    assert written["model"] == "opus" and written["hooks"]["Stop"][0] == FOREIGN  # foreign hooks kept
    once = claude.read_text()
    again = hub.client.post("/api/onboarding/agents/use", json={"agent": "claude"})
    assert again.status_code == 200 and claude.read_text() == once  # never stacked
    rows = _receipts(hub)
    assert [(r["state"], r["outcome"]) for r in rows] == [("succeeded", "succeeded")] * 2
    assert rows[0]["operation_id"] == body["operation_id"]


def test_readiness_requires_hooks_mcp_and_skill(tmp_path) -> None:
    home = tmp_path / "home"
    claude = home / ".claude" / "settings.json"
    claude.parent.mkdir(parents=True)
    install_agent_hooks(claude, agent_hook_template("claude"))
    row = _rows(_detect(home, "claude"))["claude"]
    assert row["hooks"] == "installed" and row["mcp"] == "missing" and row["skill"] == "missing"
    assert row["ready"] is False


def test_mcp_entrypoint_missing_is_not_ready_and_install_preserves_config(tmp_path) -> None:
    """A bare native entry must not become Works when its command cannot run."""
    home = tmp_path / "home"
    config = home / ".claude.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"mcpServers": {
        "holdspeak": {"type": "stdio", "command": "holdspeak-mcp", "args": [], "env": {}},
    }}))
    before = config.read_bytes()
    current = binding_state(
        "claude", home=home, env={}, which=lambda _name: None,
        python_executable=str(tmp_path / "missing-python"),
    )
    assert current["state"] == "installed" and current["runnable"] is False
    with pytest.raises(NativeBindingError) as refused:
        install_binding(
            "claude", home=home, env={}, which=lambda _name: None,
            python_executable=str(tmp_path / "missing-python"),
            runner=lambda *_args, **_kwargs: pytest.fail("native CLI must not run"),
        )
    assert refused.value.code == "mcp_executable_missing"
    assert config.read_bytes() == before


def test_foreign_mcp_entry_is_never_overwritten(hub, tmp_path) -> None:
    home = tmp_path / "home"
    config = home / ".claude.json"
    config.parent.mkdir(parents=True)
    foreign = {"type": "stdio", "command": "some-other-server", "args": [], "env": {"TOKEN": "x"}}
    config.write_text(json.dumps({"mcpServers": {"holdspeak": foreign, "other": {"command": "other"}}}))
    _seat(hub, home, "claude")
    refused = hub.client.post("/api/onboarding/agents/use", json={"agent": "claude"})
    assert refused.status_code == 409 and refused.json()["code"] == "mcp_name_taken"
    written = json.loads(config.read_text())
    assert written["mcpServers"]["holdspeak"] == foreign
    assert "other" in written["mcpServers"]


def test_foreign_skill_is_never_overwritten_or_partially_bound(hub, tmp_path) -> None:
    home = tmp_path / "home"
    skill = home / ".claude" / "skills" / "holdspeak" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("owner's custom skill\n", encoding="utf-8")
    _seat(hub, home, "claude")
    refused = hub.client.post("/api/onboarding/agents/use", json={"agent": "claude"})
    assert refused.status_code == 409 and refused.json()["code"] == "skill_name_taken"
    assert skill.read_text(encoding="utf-8") == "owner's custom skill\n"
    assert not (home / ".claude" / "settings.json").exists()
    assert not (home / ".claude.json").exists()


def test_codex_native_empty_args_shape_is_owned_but_args_are_foreign(tmp_path) -> None:
    home = tmp_path / "home"
    config = home / ".codex" / "config.toml"
    config.parent.mkdir(parents=True)
    command = _mcp_stub(home)
    which = lambda name: command if name == "holdspeak-mcp" else None
    config.write_text(f'[mcp_servers.holdspeak]\ncommand = "{command}"\n')
    current = binding_state("codex", home=home, env={}, which=which)
    assert current["state"] == "installed" and current["runnable"] is True
    config.write_text(f'[mcp_servers.holdspeak]\ncommand = "{command}"\nargs = []\n')
    foreign = binding_state("codex", home=home, env={}, which=which)
    assert foreign["state"] == "foreign" and foreign["command"] == command


def test_foreign_codex_mcp_overrides_are_never_removed_or_overwritten(hub, tmp_path) -> None:
    home = tmp_path / "home"
    config = home / ".codex" / "config.toml"
    config.parent.mkdir(parents=True)
    original = '[mcp_servers.holdspeak]\ncommand = "holdspeak-mcp"\nargs = ["--private"]\n'
    config.write_text(original)
    _seat(hub, home, "codex")
    refused = hub.client.post("/api/onboarding/agents/use", json={"agent": "codex"})
    assert refused.status_code == 409 and refused.json()["code"] == "mcp_name_taken"
    assert config.read_text() == original
    row = _rows(hub.client.get("/api/onboarding/agents").json())["codex"]
    assert row["mcp"] == "foreign" and row["ready"] is False


def test_stop_removes_our_bindings_and_keeps_foreign_entries(hub, tmp_path) -> None:
    home = tmp_path / "home"
    _seat(hub, home, "claude")
    used = hub.client.post("/api/onboarding/agents/use", json={"agent": "claude"})
    assert used.status_code == 200, used.text
    config = home / ".claude.json"
    data = json.loads(config.read_text())
    data["mcpServers"]["foreign"] = {"command": "foreign"}
    config.write_text(json.dumps(data))
    foreign_skill = home / ".claude" / "skills" / "foreign" / "SKILL.md"
    foreign_skill.parent.mkdir(parents=True)
    foreign_skill.write_text("foreign skill")
    stopped = hub.client.post("/api/onboarding/agents/stop", json={"agent": "claude"})
    assert stopped.status_code == 200, stopped.text
    after = json.loads(config.read_text())
    assert "holdspeak" not in after.get("mcpServers", {}) and "foreign" in after["mcpServers"]
    assert not (home / ".claude" / "skills" / "holdspeak" / "SKILL.md").exists()
    assert foreign_skill.read_text() == "foreign skill"
    row = _rows(stopped.json())["claude"]
    assert row["hooks"] == "missing" and row["mcp"] == "missing" and row["skill"] == "missing"


def test_aggregate_use_keeps_an_earlier_failure_when_a_later_agent_works(hub, tmp_path, monkeypatch) -> None:
    """The agents row must not become Works from only its last response."""
    import holdspeak.services.onboarding_service as onboarding_service

    home = tmp_path / "home"
    config = home / ".claude.json"
    config.parent.mkdir(parents=True)
    foreign = {"type": "stdio", "command": "another-mcp", "args": [], "env": {}}
    config.write_text(json.dumps({"mcpServers": {"holdspeak": foreign}}))
    monkeypatch.setattr(onboarding_service, "trust_codex_hooks", lambda **_: {"state": "trusted"})
    monkeypatch.setattr(onboarding_service, "_codex_launch_hooks_stamped", lambda _home: True)
    _seat(hub, home, "claude", "codex")

    answer = hub.client.post("/api/onboarding/agents/use", json={"agents": ["claude", "codex"]})
    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert body["ok"] is False and body["success"] is False and body["state"] == "degraded"
    assert [(item["agent"], item["ok"]) for item in body["results"]] == [("claude", False), ("codex", True)]
    assert body["results"][0]["code"] == "mcp_name_taken"
    assert body["results"][1]["used"]["agent"] == "codex"
    rows = _rows(body)
    assert rows["claude"]["ready"] is False and rows["codex"]["ready"] is True
    assert json.loads(config.read_text())["mcpServers"]["holdspeak"] == foreign


def test_use_it_refuses_an_agent_not_installed_with_a_receipt(hub, tmp_path) -> None:
    home = tmp_path / "home"
    _seat(hub, home, "claude")
    refused = hub.client.post("/api/onboarding/agents/use", json={"agent": "codex"})
    assert refused.status_code == 409 and refused.json()["code"] == "codex_not_installed"
    assert refused.json()["receipt"]["outcome"] == "codex_not_installed"
    assert not (home / ".codex").exists()  # a refusal writes nothing
    assert [(r["state"], r["outcome"]) for r in _receipts(hub)] == [("refused", "codex_not_installed")]
    unknown = hub.client.post("/api/onboarding/agents/use", json={"agent": "aider"})
    assert unknown.status_code == 400 and unknown.json()["code"] == "invalid_arguments"
    assert unknown.json()["receipt"]["outcome"] == "invalid_arguments"


def test_a_client_can_never_name_the_file(hub, tmp_path) -> None:
    home = tmp_path / "home"
    _seat(hub, home, "claude")
    bad = hub.client.post("/api/onboarding/agents/use",
                          json={"agent": "claude", "settings_path": str(tmp_path / "elsewhere.json")})
    assert bad.status_code == 400 and bad.json()["code"] == "invalid_arguments"
    assert bad.json()["receipt"]["outcome"] == "invalid_arguments"
    assert not (tmp_path / "elsewhere.json").exists() and not (home / ".claude").exists()


def test_use_it_never_rewrites_an_unreadable_file(hub, tmp_path) -> None:
    home = tmp_path / "home"
    claude = home / ".claude" / "settings.json"
    claude.parent.mkdir(parents=True)
    claude.write_text("{broken")
    _seat(hub, home, "claude")
    refused = hub.client.post("/api/onboarding/agents/use", json={"agent": "claude"})
    assert refused.status_code == 409 and refused.json()["code"] == "agent_settings_unreadable"
    assert refused.json()["receipt"]["outcome"] == "agent_settings_unreadable"
    assert claude.read_text() == "{broken"


def test_a_failed_write_ends_failed_with_its_receipt(hub, tmp_path, monkeypatch) -> None:
    import holdspeak.agent_context.hooks as hooks

    def boom(path: Path, template: Any) -> Any:
        raise OSError("disk full")

    monkeypatch.setattr(hooks, "install_agent_hooks", boom)
    _seat(hub, tmp_path / "home", "claude")
    failed = hub.client.post("/api/onboarding/agents/use", json={"agent": "claude"})
    assert failed.status_code == 500 and failed.json()["receipt"]["outcome"] == "failed"
    assert [(r["state"], r["outcome"]) for r in _receipts(hub)] == [("failed", "failed")]


def test_use_it_refuses_when_holdspeak_cannot_be_found(hub, tmp_path, monkeypatch) -> None:
    import holdspeak.agent_context.hooks as hooks

    monkeypatch.setattr(hooks, "holdspeak_executable", lambda: None)
    _seat(hub, tmp_path / "home", "claude")
    refused = hub.client.post("/api/onboarding/agents/use", json={"agent": "claude"})
    assert refused.status_code == 409 and refused.json()["code"] == "holdspeak_not_found"
    assert not (tmp_path / "home" / ".claude").exists()


def test_install_follows_codex_home_and_reads_back_ready(hub, tmp_path, monkeypatch) -> None:
    """Astra r1 finding 2: with CODEX_HOME set, the install writes there, never ~/.codex.
    Conductor R3: the press also trusts the hooks in Codex (a fake ``codex``
    app-server at the process boundary); only then is Codex ready."""
    from tests.unit.test_conductor_codex import make_fake_codex

    fake = make_fake_codex(tmp_path, monkeypatch)
    home = tmp_path / "home"
    # This service reads only the fake's temporary agent state. Preserve its
    # CODEX_HOME when the enclosing rig disables reads of real agent state.
    env = {"CODEX_HOME": str(fake.home), "HOLDSPEAK_AGENT_STATE": "on"}
    service = _seat(hub, home, "codex", env=env)
    service._which = lambda name: fake.exe if name == "codex" else None
    answer = hub.client.post("/api/onboarding/agents/use", json={"agent": "codex"})
    assert answer.status_code == 200, answer.text
    assert answer.json()["used"]["path"] == str(tmp_path / "codex-home" / "hooks.json")
    assert answer.json()["used"]["skill"] == str(home / ".agents" / "skills" / "holdspeak" / "SKILL.md")
    assert (home / ".agents" / "skills" / "holdspeak" / "SKILL.md").is_file()
    assert answer.json()["used"]["trust"]["state"] == "trusted"
    assert (tmp_path / "codex-home" / "hooks.json").is_file()
    assert not (home / ".codex").exists()
    assert _rows(answer.json())["codex"]["ready"] is True
    readback = hub.client.get("/api/onboarding/agents").json()
    assert _rows(readback)["codex"]["hooks"] == "installed"
    # The fake read and trusted the installed hooks in the service's CODEX_HOME.
    state = fake.read()
    assert state["runs"]
    assert any(key.startswith(f"{fake.home}/hooks.json:") for key in state["state"])


def test_codex_hooks_codex_does_not_trust_are_not_ready(hub, tmp_path) -> None:
    """Conductor R3: Codex runs no hook its config does not trust; a failed
    trust step leaves the file written and Codex not ready."""
    home = tmp_path / "home"
    env = {"CODEX_HOME": str(tmp_path / "codex-home")}
    _seat(hub, home, "codex", env=env)  # /opt/bin/codex does not exist: no trust
    answer = hub.client.post("/api/onboarding/agents/use", json={"agent": "codex"})
    assert answer.status_code == 200, answer.text
    assert answer.json()["used"]["trust"] == {"state": "failed", "reason": "codex_unavailable"}
    row = _rows(answer.json())["codex"]
    assert row["hooks"] == "untrusted" and row["ready"] is False


def test_the_service_never_writes_off_the_kernel_path(tmp_path) -> None:
    from holdspeak.services.onboarding_service import OnboardingService

    service = OnboardingService(home_provider=lambda: tmp_path, environ={}, macos=SimpleNamespace(),
                                config_loader=lambda: None, which=_which("claude"))
    with pytest.raises(RuntimeError):
        service.agents_use(OWNER, "claude", str(tmp_path / ".claude" / "settings.json"))
    assert not (tmp_path / ".claude").exists()


def test_the_agent_routes_are_owner_only() -> None:
    from holdspeak.principals import PrincipalRight, required_right

    for method, path in (("GET", "/api/onboarding/agents"), ("POST", "/api/onboarding/agents/use"),
                         ("POST", "/api/onboarding/agents/use-all")):
        assert required_right(method, path) is PrincipalRight.OWNER


def test_the_operation_is_owner_only_and_admitted() -> None:
    from holdspeak.kernel.project import OWNER_ONLY_OPERATIONS
    from holdspeak.operations import DESCRIPTORS

    row = next(d for d in DESCRIPTORS if d.name == NAME)
    assert row.owner_only and row.owner_press and row.admission.rule == "admitted"
    assert NAME in OWNER_ONLY_OPERATIONS
    stop = next(d for d in DESCRIPTORS if d.name == "agent_hooks.remove")
    assert stop.owner_only and stop.owner_press and stop.admission.rule == "admitted"
    assert "agent_hooks.remove" in OWNER_ONLY_OPERATIONS
    assert "http:POST /api/onboarding/agents/use-all" in row.exposure


# ── doctor ───────────────────────────────────────────────────────────────


def _installed(home: Path) -> None:
    install_agent_hooks(home / ".claude" / "settings.json", agent_hook_template("claude"))
    (home / ".claude.json").write_text(json.dumps({"mcpServers": {
        "holdspeak": {"type": "stdio", "command": "holdspeak-mcp", "args": [], "env": {}}
    }}))
    from holdspeak.agent_skill import install_skill

    install_skill(home / ".claude", "claude")


def test_doctor_info_when_no_agent_is_installed(tmp_path) -> None:
    check = _check_coding_agents(_detect(tmp_path, "tmux"))
    assert check.name == "Coding agents" and check.status == "INFO" and check.fix is None


def test_doctor_info_with_no_agent_and_no_tmux(tmp_path) -> None:
    """Astra r1 finding 5: tmux does not matter until an agent is installed."""
    check = _check_coding_agents(_detect(tmp_path))
    assert check.status == "INFO" and check.fix is None


def test_doctor_warns_with_the_install_fix_when_hooks_are_missing(tmp_path) -> None:
    check = _check_coding_agents(_detect(tmp_path, "claude", "tmux"))
    assert check.status == "WARN"
    assert "`holdspeak agent-hook install --agent claude`" in check.fix


def test_doctor_passes_once_one_agent_has_working_hooks(tmp_path) -> None:
    _installed(tmp_path)
    check = _check_coding_agents(_detect(tmp_path, "claude", "tmux"))
    assert check.status == "PASS" and "Claude Code hooks installed" in check.detail


def test_doctor_warns_on_hooks_that_cannot_run(tmp_path) -> None:
    claude = tmp_path / ".claude" / "settings.json"
    claude.parent.mkdir()
    claude.write_text(json.dumps(_broken_template()))
    check = _check_coding_agents(_detect(tmp_path, "claude", "tmux"))
    assert check.status == "WARN" and "cannot run" in check.detail
    assert "`holdspeak agent-hook install --agent claude`" in check.fix
    # The hook repair is truthful, but complete readiness still needs MCP and
    # the skill; the setup press supplies those two bindings.
    install_agent_hooks(claude, agent_hook_template("claude"))
    assert _check_coding_agents(_detect(tmp_path, "claude", "tmux")).status == "WARN"


def test_doctor_warns_when_tmux_is_missing_with_the_platform_hint(tmp_path) -> None:
    _installed(tmp_path)
    check = _check_coding_agents(_detect(tmp_path, "claude", platform="linux"))
    assert check.status == "WARN" and "`sudo apt-get install tmux`" in check.fix
    mac = _check_coding_agents(_detect(tmp_path, "claude", platform="darwin"))
    assert "`brew install tmux`" in mac.fix


def test_doctor_strict_exits_zero_on_info(tmp_path, monkeypatch, capsys) -> None:
    from holdspeak.commands import doctor

    monkeypatch.setattr(doctor, "collect_doctor_checks", lambda: [_check_coding_agents(_detect(tmp_path))])
    assert doctor.run_doctor_command(SimpleNamespace(strict=True, connectors=False)) == 0
    assert "[INFO] Coding agents" in capsys.readouterr().out


def test_setup_status_keeps_info_and_stays_ready(tmp_path, monkeypatch) -> None:
    """Astra r1 finding 6: INFO reaches the Setup API as info, never unknown or a primary action."""
    import holdspeak.config as config_module
    import holdspeak.setup_status as setup_status
    from holdspeak.config import Config

    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr("holdspeak.commands.doctor.collect_doctor_checks",
                        lambda **_: [_check_coding_agents(_detect(tmp_path))])
    status = setup_status.build_setup_status(config=Config())
    section = next(s for s in status["sections"] if s["id"] == "coding-agents")
    assert section["status"] == "info"
    assert status["overall"] == "ready"
    assert (status.get("primary_action") or {}).get("id") != "coding-agents"
