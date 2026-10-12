"""The walk rig (scripts/graph_walk and its fixtures): isolation, faithful requests, import boundary.

Grouped by service (the fast diet, 2026-10-12). Moved verbatim from:
- test_philo13_fixture_rig.py
- test_philo16_rig_gaps.py
- test_philo16_rig_isolation.py
- test_philo7_rig_faithful.py
- test_philo5_rig_import_boundary.py
"""
from __future__ import annotations

# ── moved from tests/unit/test_philo13_fixture_rig.py ──
# Focused proof for the PHILO-13 real-input fixture boundaries.

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO = Path(__file__).resolve().parents[2]
RIG_PATH = REPO / "scripts/graph_walk.py"


def _rig():
    spec = importlib.util.spec_from_file_location("_graph_walk_for_philo13_fixture_rig", RIG_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class _Hub:
    def __init__(self, home: Path) -> None:
        self.home = home
        self.repo_root: Path | None = None
        self.proc = None
        self.wiring = {"has": ["fixture test"], "lacks": []}
        self.db_path = str(home / "holdspeak.db")
        self.restarts = 0

    def restart(self) -> dict[str, object]:
        self.restarts += 1
        self.proc = SimpleNamespace(pid=200 + self.restarts)
        return {
            "stopped_pid": 100 + self.restarts,
            "started_pid": 200 + self.restarts,
            "same_db_path": True,
            "db_path": self.db_path,
            "port": 9876,
            "downtime_s": 0.01,
        }


class _Locator:
    def __init__(self) -> None:
        self.first = self
        self.files: list[tuple[str, float]] = []
        self.options: list[tuple[str, float]] = []
        self.clicks: list[str] = []

    def set_input_files(self, value: str, *, timeout: float) -> None:
        self.files.append((value, timeout))

    def select_option(self, value: str, *, timeout: float) -> None:
        self.options.append((value, timeout))

    def click(self, *, timeout: float, button: str) -> None:
        self.clicks.append(f"click:{button}:{timeout}")

    def tap(self, *, timeout: float) -> None:
        self.clicks.append(f"tap:{timeout}")


class _Chooser:
    def __init__(self) -> None:
        self.files: list[str] = []

    def set_files(self, path: str) -> None:
        self.files.append(path)


class _ChooserEvent:
    def __init__(self, chooser: _Chooser) -> None:
        self.value = chooser

    def __enter__(self) -> "_ChooserEvent":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class _Page:
    viewport_size = {"width": 1440, "height": 900}

    def __init__(self, width: int = 1440) -> None:
        self.target = _Locator()
        self.viewport_size = {"width": width, "height": 900}
        self.chooser = _Chooser()

    def locator(self, _selector: str) -> _Locator:
        return self.target

    def expect_file_chooser(self, *, timeout: float) -> _ChooserEvent:
        assert timeout == 10000.0
        return _ChooserEvent(self.chooser)


def test_repository_fixture_binds_scalars_and_restarts_the_owned_hub(tmp_path: Path) -> None:
    rig = _rig()
    hub = _Hub(tmp_path)
    provenance: dict[str, object] = {"fixture_hashes": {}, "hub": {"pid": 11}}
    variables: dict[str, object] = {}

    record = rig._create_repository_fixture_step(
        {
            "kind": "cli",
            "action": "create_repository_fixture",
            "capture_as": "repo",
        },
        None,
        hub,
        provenance,
        variables,
    )

    fixture = provenance["repository_fixture"]
    assert isinstance(fixture, dict)
    assert set(fixture) >= {"path", "label", "project_slug", "story_id", "git_head"}
    path = Path(fixture["path"])
    assert path.is_dir() and path.parent == tmp_path
    assert len(fixture["git_head"]) == 40
    assert variables == {
        "repo_path": fixture["path"],
        "repo_label": fixture["label"],
        "repo_project_slug": fixture["project_slug"],
        "repo_story_id": fixture["story_id"],
        "repo_git_head": fixture["git_head"],
    }
    assert hub.repo_root == path
    assert hub.restarts == 1
    assert record["action"] == "create_repository_fixture"
    assert provenance["restarts"][0]["started_pid"] == 201
    assert provenance["hub"]["pid"] == 201
    assert provenance["db_path"] == hub.db_path


def test_ingest_coder_fixture_uses_real_cli_and_records_question(tmp_path: Path) -> None:
    rig = _rig()
    hub = _Hub(tmp_path)
    fixture = rig._create_repository_fixture_step(
        {"kind": "cli", "action": "create_repository_fixture"},
        None,
        hub,
        {"fixture_hashes": {}},
        {},
    )
    provenance: dict[str, object] = {"fixture_hashes": {}}
    variables: dict[str, object] = {}

    record = rig._ingest_coder_fixture_step(
        {"kind": "cli", "action": "ingest_coder_fixture", "capture_as": "coder"},
        hub,
        provenance,
        variables,
    )

    session = record["session"]
    assert session["agent"] == "codex"
    assert session["session_id"] == "phase13-coder-input"
    assert session["hook_event_name"] == "Stop"
    assert session["awaiting_response"] is True
    assert "Should I run" in session["last_assistant_text"]
    assert session["tmux_pane"] is None
    assert variables == {
        "coder_session_id": "phase13-coder-input",
        "coder_agent": "codex",
    }
    coder_fixture = provenance["coder_fixture"]
    assert Path(coder_fixture["transcript_path"]).parent == tmp_path
    assert coder_fixture["source_sha256"] == coder_fixture["sha256"]
    assert coder_fixture["session"] == session
    assert fixture["action"] == "create_repository_fixture"


def test_set_input_files_dispatches_native_path_and_records_hash(tmp_path: Path) -> None:
    rig = _rig()
    page = _Page()
    hub = _Hub(tmp_path)
    provenance: dict[str, object] = {"fixture_hashes": {}}
    value = "tests/fixtures/agent_transcripts/codex_question.jsonl"

    record = rig.run_step(
        {"kind": "ui", "action": "set_input_files", "selector": "input[type=file]", "value": value},
        page,
        hub,
        provenance,
    )

    expected_hash = hashlib.sha256((REPO / value).read_bytes()).hexdigest()
    assert page.target.files == [(str(REPO / value), 10000.0)]
    assert record["input_file"] == {
        "path": value,
        "resolved_path": str(REPO / value),
        "sha256": expected_hash,
        "scope": "repository_fixture",
    }
    assert provenance["fixture_hashes"][value] == expected_hash


@pytest.mark.parametrize("width,expected_adapter", [(1440, "ui-pointer"), (393, "ui-touch")])
def test_file_chooser_dispatch_uses_native_click_at_both_widths(
    tmp_path: Path, width: int, expected_adapter: str,
) -> None:
    rig = _rig()
    page = _Page(width)
    hub = _Hub(tmp_path)
    value = "tests/fixtures/agent_transcripts/codex_question.jsonl"

    record = rig.run_step(
        {
            "kind": "ui",
            "action": "set_input_files",
            "selector": "[data-testid=calendar-snapshot-button]",
            "value": value,
            "adapter": "ui-by-viewport",
            "file_chooser": True,
        },
        page,
        hub,
        {"fixture_hashes": {}},
    )

    assert record["adapter"] == expected_adapter
    assert page.chooser.files == [str(REPO / value)]
    if width == 1440:
        assert page.target.clicks == ["click:left:10000.0"]
    else:
        assert page.target.clicks == ["tap:10000.0"]


@pytest.mark.parametrize("width", [1440, 393])
def test_real_browser_file_chooser_accepts_detached_input_at_both_widths(
    tmp_path: Path, width: int,
) -> None:
    from playwright.sync_api import sync_playwright

    value = "tests/fixtures/philo13/calendar-input.png"
    with sync_playwright() as play:
        browser = play.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": width, "height": 900 if width == 1440 else 852},
            has_touch=width == 393,
        )
        page = context.new_page()
        page.set_content(
            """
            <button data-testid="calendar-snapshot-button">Snapshot</button>
            <script>
              window.received = null;
              document.querySelector('button').addEventListener('click', () => {
                const input = document.createElement('input');
                input.type = 'file';
                input.addEventListener('change', () => {
                  window.received = input.files[0] && input.files[0].name;
                });
                input.click();
              });
            </script>
            """
        )
        record = _rig()._ui_step(page, {
            "kind": "ui",
            "action": "set_input_files",
            "selector": "[data-testid=calendar-snapshot-button]",
            "value": value,
            "adapter": "ui-by-viewport",
            "file_chooser": True,
        }, SimpleNamespace(home=tmp_path))
        assert page.evaluate("window.received") == "calendar-input.png"
        assert record["adapter"] == ("ui-pointer" if width == 1440 else "ui-touch")
        context.close()
        browser.close()


def test_set_input_files_refuses_a_path_outside_owned_roots(tmp_path: Path) -> None:
    rig = _rig()
    page = _Page()
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"input")

    with pytest.raises(rig.Blocked, match="outside tests/fixtures and the isolated hub HOME"):
        rig._ui_step(
            page,
            {"kind": "ui", "action": "set_input_files", "selector": "input", "value": str(outside)},
            _Hub(tmp_path / "home"),
        )
    assert page.target.files == []


def test_hub_environment_and_teardown_never_use_inherited_tmux_socket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    rig = _rig()
    inherited = {"HOME": "/owner", "TMUX": "/owner/default", "TMUX_PANE": "%9",
                 "HOLDSPEAK_MACOS_CALENDAR": "1"}
    env = rig._isolated_hub_env(tmp_path, inherited=inherited)
    # PHILO-16 R2: EventKit is per macOS user; a rig hub never reads the
    # owner's calendars, whatever the parent environment says.
    assert env["HOLDSPEAK_MACOS_CALENDAR"] == "0"
    assert env["HOME"] == str(tmp_path)
    assert env["TMUX_TMPDIR"] == str(tmp_path)
    assert env["HOLDSPEAK_PEOPLE_KEYSTORE_FILE"] == str(tmp_path / "people.key")
    # PHILO-16 (C): the loopback engine scan reads no port in a rig hub.
    assert env["HOLDSPEAK_LOOPBACK_ENGINE_PORTS"] == ""
    assert "TMUX" not in env and "TMUX_PANE" not in env

    calls: list[dict[str, object]] = []

    def fake_run(command, **kwargs):
        calls.append({"command": command, **kwargs})
        return subprocess.CompletedProcess(
            command, 1, stdout="", stderr="no server running on /tmp/tmux-501/default",
        )

    monkeypatch.setattr(rig.subprocess, "run", fake_run)
    teardown = rig._teardown_hub_tmux(tmp_path)
    assert teardown["no_server"] is True
    assert calls[0]["command"] == ["tmux", "kill-server"]
    kill_env = calls[0]["env"]
    assert kill_env["TMUX_TMPDIR"] == str(tmp_path)
    assert kill_env["HOLDSPEAK_PEOPLE_KEYSTORE_FILE"] == str(tmp_path / "people.key")
    assert "TMUX" not in kill_env and "TMUX_PANE" not in kill_env


def test_seed_people_prep_runs_the_real_fixture_in_the_owned_key_world(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    rig = _rig()
    hub = _Hub(tmp_path)
    provenance: dict[str, object] = {"fixture_hashes": {}, "hub": {"pid": 11}}
    variables: dict[str, object] = {}
    ids = {
        "relationship_id": "relationship",
        "event_id": "event",
        "event_uid": "uid",
        "event_source_id": "source",
        "event_title": "1:1 Priya / Karol",
        "project_id": "project",
        "meeting_id": "meeting",
        "session_id": "session",
        "action_id": "action",
    }

    def fake_run(command, **kwargs):
        assert command[2] == "seed"
        assert kwargs["env"]["HOLDSPEAK_PEOPLE_KEYSTORE_FILE"] == str(tmp_path / "people.key")
        return subprocess.CompletedProcess(
            command, 0, stdout=json.dumps({
                "schema": "philo13-b4-people-prep@1", "ids": ids,
            }), stderr="",
        )

    monkeypatch.setattr(rig.subprocess, "run", fake_run)
    record = rig._seed_people_prep_step(
        {"kind": "cli", "action": "seed_people_prep", "capture_as": "people"},
        None, hub, provenance, variables,
    )

    assert record["action"] == "seed_people_prep"
    assert variables["people_relationship_id"] == "relationship"
    assert variables["people_event_uid"] == "uid"
    assert hub.restarts == 1


def test_hub_tmux_teardown_does_not_mislabel_permission_error_as_no_server(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    rig = _rig()

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command, 1, stdout="", stderr="error connecting to /run/tmux: Permission denied",
        )

    monkeypatch.setattr(rig.subprocess, "run", fake_run)

    teardown = rig._teardown_hub_tmux(tmp_path)

    assert teardown["returncode"] == 1
    assert teardown["no_server"] is False
    assert teardown["server_stopped"] is False
    assert teardown["stderr"] == "error connecting to /run/tmux: Permission denied"


def test_hub_tmux_teardown_records_success_and_bounded_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    rig = _rig()

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="clean\n")

    monkeypatch.setattr(rig.subprocess, "run", fake_run)

    teardown = rig._teardown_hub_tmux(tmp_path)

    assert teardown["returncode"] == 0
    assert teardown["no_server"] is False
    assert teardown["server_stopped"] is True
    assert teardown["stderr"] == "clean"


def test_repository_router_passes_fixture_to_real_builder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rig = _rig()
    hub = _Hub(tmp_path)
    fixture_provenance: dict[str, object] = {"fixture_hashes": {}}
    fixture_variables: dict[str, object] = {}
    rig._create_repository_fixture_step(
        {"kind": "cli", "action": "create_repository_fixture"},
        None,
        hub,
        fixture_provenance,
        fixture_variables,
    )
    import holdspeak.web.routes as web_routes

    calls: list[dict[str, object]] = []

    def builder(ctx, *args, **kwargs):
        calls.append({"ctx": ctx, "args": args, "kwargs": kwargs})
        return "real-roadmap-router"

    monkeypatch.setattr(web_routes, "build_roadmaps_router", builder)
    monkeypatch.setenv("HOME", str(tmp_path))
    rig._install_repository_router(hub.repo_root)
    assert web_routes.build_roadmaps_router("ctx") == "real-roadmap-router"
    assert calls == [{"ctx": "ctx", "args": (), "kwargs": {"repo_root": hub.repo_root}}]


def test_real_hub_reads_repository_and_coder_producers(tmp_path: Path) -> None:
    rig = _rig()
    hub = rig.Hub(tmp_path).start(timeout=60)
    provenance: dict[str, object] = {"fixture_hashes": {}}
    variables: dict[str, object] = {}
    try:
        repository_record = rig._create_repository_fixture_step(
            {"kind": "cli", "action": "create_repository_fixture", "capture_as": "repo"},
            None,
            hub,
            provenance,
            variables,
        )
        status, body = hub.api("GET", "/api/roadmaps")
        assert status == 200, body
        roadmaps = body["roadmaps"]
        assert any(item["slug"] == "atlas-desk" for item in roadmaps)
        assert repository_record["restart"]["same_db_path"] is True
        assert hub.repo_root is not None and hub.proc is not None and hub.proc.poll() is None

        coder_record = rig._ingest_coder_fixture_step(
            {"kind": "cli", "action": "ingest_coder_fixture", "capture_as": "coder"},
            hub,
            provenance,
            variables,
        )
        status, body = hub.api("GET", "/api/coders/status")
        assert status == 200, body
        session = body["agent"]["session"]
        assert session["session_id"] == coder_record["session"]["session_id"]
        assert session["awaiting_response"] is True
        assert any(
            item["session"]["session_id"] == "phase13-coder-input"
            and item["session"]["awaiting_response"]
            for item in body["agent"]["sessions"]["items"]
        )
    finally:
        hub.stop()
        rig._teardown_hub_tmux(tmp_path)


# ── moved from tests/unit/test_philo16_rig_gaps.py ──
# PHILO-16 lane 16-RIG (rig gaps G1, G2): two rig isolation gaps closed at their cause.
#
# G1. The Agents detector on a fresh isolated HOME read the owner's machine: the
#     hub inherits the owner's environment (``CLAUDE_CONFIG_DIR``, ``CODEX_HOME``,
#     ``ANTHROPIC_API_KEY`` point at his real sign-in and hook files) and pi's row
#     claimed SIGNED IN and HOOKS on every machine. ``HOLDSPEAK_AGENT_STATE=off``
#     makes those reads answer ``not_read`` (never ``no``); both rig envs set it;
#     the default (the owner's desk, ``holdspeak doctor``) stays on.
#
# G2. An ``engine_reply`` or ``cli_runner`` boundary without ``reply`` booted the
#     hub without its double; only the boundary step refused, after a work step
#     ordered before it could reach the real seam. The rig now refuses the case
#     before the build and the hub (R2's import_transcriber guard, extended), and
#     the schema requires ``reply`` on both.

import json
import os
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from holdspeak.services import onboarding_service
from holdspeak.services.onboarding_service import (
    AGENT_STATE_ENV,
    NOT_READ,
    OnboardingService,
    agent_state_read,
    detect_agents,
)
from scripts import graph_walk

REPO = Path(__file__).resolve().parents[2]
GRAPH = REPO / "docs/internal/philo/graph"
SCHEMA = GRAPH / "atlas.schema.json"


# ── G1: the agent state switch ──────────────────────────────────────────


def _which(name: str) -> str | None:
    return f"/opt/bin/{name}" if name in {"claude", "codex", "pi", "tmux", "holdspeak"} else None


def _owner_state(root: Path) -> dict[str, str]:
    """A stand-in for the owner's real agent state OUTSIDE the rig's HOME."""
    claude = root / "owner-claude"
    codex = root / "owner-codex"
    claude.mkdir(parents=True)
    codex.mkdir(parents=True)
    (claude / ".credentials.json").write_text(json.dumps({"claudeAiOauth": {"accessToken": "t"}}))
    (codex / "auth.json").write_text(json.dumps({"tokens": {"access_token": "t"}}))
    hooks = {"hooks": {"SessionStart": [{"hooks": [{"command": "holdspeak agent-hook ingest"}]}]}}
    (claude / "settings.json").write_text(json.dumps(hooks))
    (codex / "hooks.json").write_text(json.dumps(hooks))
    return {"CLAUDE_CONFIG_DIR": str(claude), "CODEX_HOME": str(codex), "ANTHROPIC_API_KEY": "sk-owner"}


@pytest.mark.parametrize("value,expected", [
    (None, True), ("", True), ("on", True), ("1", True),
    ("off", False), ("OFF", False), ("0", False), ("false", False), ("no", False),
])
def test_the_switch_is_on_by_default_and_off_only_when_named(value: str | None, expected: bool) -> None:
    env = {} if value is None else {AGENT_STATE_ENV: value}
    assert agent_state_read(env) is expected


def test_with_the_switch_off_a_fresh_home_reports_no_sign_in_and_no_hooks(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    env = {**_owner_state(tmp_path), AGENT_STATE_ENV: "off"}

    rows = {row["id"]: row for row in detect_agents(which=_which, home=home, environ=env)["agents"]}

    assert set(rows) == {"claude", "codex", "pi"}
    for row in rows.values():
        # Installed is lawful to detect (the binary on PATH).
        assert row["installed"] is True
        # Never "yes", and never a "no" a face could act on.
        assert row["signed_in"] == NOT_READ, row
        assert row["signed_in_from"] is None
        assert row["hooks"] != "installed", row
        assert row["ready"] is False
    assert rows["pi"]["hooks"] == NOT_READ
    # The owner's config dirs are not where the rig looked.
    for agent in ("claude", "codex"):
        assert Path(rows[agent]["hooks_path"]).is_relative_to(home), rows[agent]["hooks_path"]


def test_the_default_still_reads_the_real_state_for_the_owner_and_doctor(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    env = _owner_state(tmp_path)  # no switch: the owner's desk

    rows = {row["id"]: row for row in detect_agents(which=_which, home=home, environ=env)["agents"]}

    assert rows["claude"]["signed_in"] == "yes"
    assert rows["claude"]["signed_in_from"] == "ANTHROPIC_API_KEY"
    assert rows["codex"]["signed_in"] == "yes"
    assert rows["claude"]["hooks_path"].startswith(env["CLAUDE_CONFIG_DIR"])
    assert rows["pi"]["signed_in"] == "yes"
    assert rows["pi"]["hooks"] in {"installed", "missing"}


def test_doctor_reads_with_the_process_environment_default_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``holdspeak doctor`` calls ``detect_agents()`` with no env: the process's, switch unset."""
    from holdspeak.commands import doctor

    monkeypatch.delenv(AGENT_STATE_ENV, raising=False)
    for key, value in _owner_state(tmp_path).items():
        monkeypatch.setenv(key, value)
    seen: dict[str, Any] = {}
    real = onboarding_service.detect_agents

    def spy(**kwargs: Any) -> dict[str, Any]:
        result = real(which=_which, home=tmp_path / "home", **kwargs)
        seen.update({row["id"]: row for row in result["agents"]})
        return result

    monkeypatch.setattr(onboarding_service, "detect_agents", spy)
    check = doctor._check_coding_agents()
    assert check.name == "Coding agents"
    assert seen["claude"]["signed_in"] == "yes" and seen["pi"]["signed_in"] == "yes"


def test_a_credential_in_the_rigs_own_home_is_still_read(tmp_path: Path) -> None:
    """Files under the isolated HOME are the rig's own state (the lane 18 glass writes them)."""
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    (home / ".codex" / "auth.json").write_text(json.dumps({"OPENAI_API_KEY": "sk-placeholder"}))
    env = {**_owner_state(tmp_path), AGENT_STATE_ENV: "off"}

    rows = {row["id"]: row for row in detect_agents(which=_which, home=home, environ=env)["agents"]}

    assert rows["codex"]["signed_in"] == "yes"
    assert rows["codex"]["signed_in_from"] == str(home / ".codex" / "auth.json")
    assert rows["claude"]["signed_in"] == NOT_READ


def test_the_install_target_stays_in_the_rigs_home_with_the_switch_off(tmp_path: Path) -> None:
    """Install hooks in a rig writes the rig's HOME, never the owner's CLAUDE_CONFIG_DIR."""
    home = tmp_path / "home"
    home.mkdir()
    owner = _owner_state(tmp_path)

    def service(env: dict[str, str]) -> OnboardingService:
        svc = OnboardingService.__new__(OnboardingService)
        svc._home = lambda: home
        svc._environ = env
        return svc

    off = service({**owner, AGENT_STATE_ENV: "off"})
    assert Path(off.agent_settings_target("claude")).is_relative_to(home)
    assert Path(off.agent_settings_target("codex")).is_relative_to(home)
    on = service(owner)
    assert off.agent_settings_target("claude") != on.agent_settings_target("claude")
    assert on.agent_settings_target("claude").startswith(owner["CLAUDE_CONFIG_DIR"])


def test_the_graph_walk_hub_env_turns_agent_state_off_without_touching_this_process(tmp_path: Path) -> None:
    before = os.environ.get(AGENT_STATE_ENV)
    env = graph_walk._isolated_hub_env(tmp_path, inherited={"PATH": "/usr/bin"})
    assert env[AGENT_STATE_ENV] == "off"
    assert agent_state_read(env) is False
    # The rig env is the child's: the parent (and `holdspeak web`) keep theirs.
    assert os.environ.get(AGENT_STATE_ENV) == before


def test_the_glass_boot_turns_agent_state_off(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import holdspeak.web_server as web_server

    from tests.e2e import glass_infra

    seen: dict[str, Any] = {}

    class _Server:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def start(self) -> str:
            seen["env"] = os.environ.get(AGENT_STATE_ENV)
            seen["home"] = os.environ.get("HOME")
            return "http://127.0.0.1:0"

    monkeypatch.setattr(web_server, "MeetingWebServer", _Server)
    glass_infra._boot(tmp_path, monkeypatch)
    assert seen["env"] == "off"
    assert seen["home"] == str(tmp_path / "home")


# ── G2: replyless boot boundaries refuse before the build and the hub ───

WORK = {
    "engine_reply": {"kind": "api", "method": "POST", "path": "/api/meetings/m1/intel/run", "body": {}},
    "cli_runner": {"kind": "api", "method": "POST", "path": "/api/channels/send", "body": {"id": "x"}},
}


def _atlas(tmp_path: Path, substitution: str, boundary: dict) -> Path:
    case = {
        "id": f"case.rig.{substitution}_after_work",
        "job": "j6",
        "edge_ids": [],
        "state_id": "state.rig",
        "applicability": "applicable",
        "preconditions": [],
        "setup": [WORK[substitution], boundary],
        "trigger": {"kind": "api", "method": "GET", "path": "/api/meetings", "body": None},
        "expected": {"predicate": {"kind": "protocol_field", "path": "/meetings", "value": []},
                     "observe_at": "protocol: GET /api/meetings"},
        "completion_bound_s": 5,
        "viewports": [1440],
    }
    path = tmp_path / "atlas.json"
    path.write_text(json.dumps({"schema_version": 1, "cases": [case], "states": []}))
    return path


@pytest.mark.parametrize("substitution", ["engine_reply", "cli_runner"])
@pytest.mark.parametrize("reply", [None, "", "  "])
@pytest.mark.parametrize("engine", ["none", "replayed"])
def test_a_work_step_before_a_replyless_boot_boundary_is_refused_with_no_hub_and_no_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, substitution: str, reply: str | None, engine: str,
) -> None:
    boundary = {"kind": "boundary", "substitute": substitution, "label": "a double that names no file",
                "adapter": "labelled-substitution"}
    if reply is not None:
        boundary["reply"] = reply
    hubs: list[Any] = []
    builds: list[Any] = []
    requests: list[Any] = []

    class _NoHub:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            hubs.append(kwargs)
            raise AssertionError("a hub was started for a refused case")

    monkeypatch.setattr(graph_walk, "Hub", _NoHub)
    monkeypatch.setattr(graph_walk, "_ensure_build", lambda: builds.append(1))
    monkeypatch.setattr(graph_walk.urllib.request, "urlopen", lambda *a, **k: requests.append(a))

    record = graph_walk.run_case(
        _atlas(tmp_path, substitution, boundary), f"case.rig.{substitution}_after_work",
        brain="muaddib", viewport=1440, out=tmp_path / "out",
        engine=engine, build=True, headless=False,
    )

    assert record["verdict"] == "blocked"
    assert any(f"a {substitution} boundary declares no `reply`" in n for n in record["notes"]), record["notes"]
    assert hubs == [] and builds == [] and requests == []


@pytest.mark.parametrize("substitution", ["engine_reply", "cli_runner"])
def test_the_schema_requires_a_reply_on_a_boot_boundary(substitution: str) -> None:
    schema = json.loads(SCHEMA.read_text())
    step = Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/step"})
    replyless = {"kind": "boundary", "substitute": substitution, "label": "a double",
                 "adapter": "labelled-substitution"}
    assert list(step.iter_errors(replyless))
    assert list(step.iter_errors({**replyless, "reply": ""}))
    assert not list(step.iter_errors({**replyless, "reply": "tests/fixtures/philo5_summary_reply.json"}))


def test_every_declared_boot_boundary_in_the_active_atlases_names_its_file() -> None:
    def boundaries(node: Any):
        if isinstance(node, dict):
            if node.get("kind") == "boundary":
                yield node
            for value in node.values():
                yield from boundaries(value)
        elif isinstance(node, list):
            for value in node:
                yield from boundaries(value)

    for path in sorted(GRAPH.glob("atlas*.json")):
        if path.name == "atlas.schema.json":
            continue
        for case in json.loads(path.read_text()).get("cases", []):
            assert graph_walk.boot_boundary_problem(case) is None, (path.name, case["id"])
            for boundary in boundaries(case):
                if boundary.get("substitute") in {"engine_reply", "cli_runner", "import_transcriber"}:
                    assert str(boundary.get("reply") or "").strip(), (path.name, case["id"])


# ── G3 closes: one rig env, both rigs ────────────────────────────────────

RIG_VARS = ("GIT_CONFIG_NOSYSTEM", "HOLDSPEAK_TEST_NO_REAL_CLI", "GH_CONFIG_DIR", "XDG_CONFIG_HOME",
            "HOLDSPEAK_DESKTOP_NOTIFY", "HOLDSPEAK_CHANNEL_KEYSTORE_FILE", "HOLDSPEAK_PEOPLE_KEYSTORE_FILE",
            AGENT_STATE_ENV, "HOLDSPEAK_MACOS_CALENDAR", "TMUX_TMPDIR")
OWNER_ENV = {"GH_CONFIG_DIR": "/Users/owner/.config/gh", "XDG_CONFIG_HOME": "/Users/owner/.config",
             "PATH": "/usr/bin"}


def _assert_rig_env(env: dict[str, Any], home: Path) -> None:
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert env["HOLDSPEAK_TEST_NO_REAL_CLI"] == "1"
    assert env["HOLDSPEAK_DESKTOP_NOTIFY"] == "0"
    assert env[AGENT_STATE_ENV] == "off"
    for name in ("GH_CONFIG_DIR", "XDG_CONFIG_HOME", "HOLDSPEAK_CHANNEL_KEYSTORE_FILE",
                 "HOLDSPEAK_PEOPLE_KEYSTORE_FILE"):
        assert Path(env[name]).is_relative_to(home), (name, env[name])


def test_the_graph_walk_hub_env_closes_every_g3_read(tmp_path: Path) -> None:
    env = graph_walk._isolated_hub_env(tmp_path, inherited=dict(OWNER_ENV))
    _assert_rig_env(env, graph_walk.guard_home(tmp_path))


def test_the_glass_boot_closes_every_g3_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import holdspeak.web_server as web_server

    from tests.e2e import glass_infra

    for key, value in OWNER_ENV.items():
        monkeypatch.setenv(key, value)
    seen: dict[str, Any] = {}

    class _Server:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def start(self) -> str:
            seen.update({name: os.environ.get(name) for name in RIG_VARS})
            return "http://127.0.0.1:0"

    monkeypatch.setattr(web_server, "MeetingWebServer", _Server)
    glass_infra._boot(tmp_path, monkeypatch)
    _assert_rig_env(seen, tmp_path / "home")


# ── desktop notifications: HOLDSPEAK_DESKTOP_NOTIFY ──────────────────────


def test_notify_posts_by_default_and_not_with_the_switch_off(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak import desktop_notify

    posted: list[str] = []
    fake = lambda title, body, *, click_url=None: posted.append(body) or True  # noqa: E731
    monkeypatch.setattr(desktop_notify, "_notify_macos", fake)
    monkeypatch.setattr(desktop_notify, "_notify_linux", fake)
    monkeypatch.setattr(desktop_notify, "_PLATFORM", "Darwin")

    monkeypatch.delenv(desktop_notify.DESKTOP_NOTIFY_ENV, raising=False)
    assert desktop_notify.desktop_notify_enabled()
    assert desktop_notify.notify("HoldSpeak", "default on") is True
    monkeypatch.setenv(desktop_notify.DESKTOP_NOTIFY_ENV, "0")
    assert not desktop_notify.desktop_notify_enabled()
    assert desktop_notify.notify("HoldSpeak", "rig") is False
    assert posted == ["default on"]


def test_the_cocoa_paths_post_nothing_with_the_switch_off(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    from holdspeak import desktop_notify, desktop_presence_cocoa

    monkeypatch.setenv(desktop_notify.DESKTOP_NOTIFY_ENV, "0")
    runs: list[Any] = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: runs.append(a))
    desktop_presence_cocoa._cocoa_notify({"title": "HoldSpeak", "body": "rig"})

    class _Renderer:
        class _commands:  # noqa: N801
            put = staticmethod(lambda item: runs.append(item))

    assert desktop_notify._notify_cocoa_child(_Renderer(), "HoldSpeak", "rig") is False
    assert runs == []


def test_the_mcp_notify_test_answers_not_posted_in_this_rig(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak import desktop_notify
    from holdspeak.mcp.families import heartbeat

    monkeypatch.setenv(desktop_notify.DESKTOP_NOTIFY_ENV, "0")
    monkeypatch.setattr(heartbeat, "db_or", lambda _: None)
    monkeypatch.setattr(heartbeat, "observer_or", lambda _: None)
    monkeypatch.setattr(heartbeat, "HeartbeatService", lambda *a, **k: None)
    monkeypatch.setattr(desktop_notify, "_notify_macos", lambda *a, **k: pytest.fail("posted"))
    assert heartbeat.dispatch("heartbeat.notify_test", {}, None) == {
        "fired": False, "reason": "not posted in this rig"}


# ── channel keys: HOLDSPEAK_CHANNEL_KEYSTORE_FILE ────────────────────────


def _production_key_stores(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin both channels to their production KEY_STORE: another test in the same
    xdist worker may have left a memory store on the module (FAST 6fae68101)."""
    from holdspeak.services import channel_email, channel_slack

    monkeypatch.setattr(channel_email, "KEY_STORE", channel_email.default_key_store)
    monkeypatch.setattr(channel_slack, "KEY_STORE", channel_slack.default_key_store)


def test_with_the_file_named_the_channel_keys_never_reach_the_keychain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import keyring

    from holdspeak.services import channel_email, channel_slack
    from holdspeak.services.channel_key_file import CHANNEL_KEYSTORE_ENV

    path = tmp_path / "home" / "channel-keys.json"
    monkeypatch.setenv(CHANNEL_KEYSTORE_ENV, str(path))
    _production_key_stores(monkeypatch)
    monkeypatch.setattr(keyring, "get_keyring", lambda: pytest.fail("the Keychain was reached"))

    channel_email.save_key("resend", "main", "re_key")
    assert channel_email.read_key("resend", "main") == "re_key"
    store = channel_slack.KEY_STORE()
    store.put("slot", "https://hooks.slack.com/services/x")
    assert store.get("slot") == "https://hooks.slack.com/services/x"
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    with pytest.raises(channel_email.EmailKeyError) as missing:
        channel_email.read_key("resend", "other")
    assert missing.value.code == "email_key_missing"
    with pytest.raises(channel_slack.SlackKeyError) as slack_missing:
        store.get("other")
    assert slack_missing.value.code == "slack_webhook_missing"


def test_unset_the_channels_use_the_keychain(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services import channel_email, channel_slack
    from holdspeak.services.channel_key_file import CHANNEL_KEYSTORE_ENV

    monkeypatch.delenv(CHANNEL_KEYSTORE_ENV, raising=False)
    monkeypatch.setattr(channel_email, "NativeEmailKeyStore", lambda: "email-keychain")
    monkeypatch.setattr(channel_slack, "NativeSlackKeyStore", lambda: "slack-keychain")
    assert channel_email.default_key_store() == "email-keychain"
    assert channel_slack.default_key_store() == "slack-keychain"


# ── nested `then` boundaries install their double before boot ────────────


def test_a_boundary_inside_a_then_installs_its_double_at_boot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    reply = "tests/fixtures/philo5_summary_reply.json"
    runner = "tests/fixtures/philo10_atlas/gh-posted.json"
    transcript = "tests/fixtures/philo16_import_transcript.json"
    trigger = {"kind": "api", "method": "GET", "path": "/api/meetings", "body": None, "then": [
        {"kind": "boundary", "substitute": "engine_reply", "label": "nested", "reply": reply},
        {"kind": "boundary", "substitute": "cli_runner", "label": "nested", "reply": runner},
        {"kind": "boundary", "substitute": "import_transcriber", "label": "nested", "reply": transcript},
    ]}
    case = {"id": "case.rig.nested", "job": "j6", "edge_ids": [], "state_id": "s", "applicability": "applicable",
            "preconditions": [], "setup": [], "trigger": trigger,
            "expected": {"predicate": {"kind": "protocol_field", "path": "/meetings", "value": []},
                         "observe_at": "protocol: GET /api/meetings"},
            "completion_bound_s": 5, "viewports": []}
    assert graph_walk.case_engine_replay(case) == reply
    assert graph_walk.case_cli_runner(case) == runner
    assert graph_walk.case_import_transcriber(case) == transcript

    booted: list[dict[str, Any]] = []

    class _Hub:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            booted.append(kwargs)
            raise RuntimeError("stop after the boot arguments")

    monkeypatch.setattr(graph_walk, "Hub", _Hub)
    atlas = tmp_path / "atlas.json"
    atlas.write_text(json.dumps({"schema_version": 1, "cases": [case], "states": []}))
    with pytest.raises(RuntimeError, match="stop after the boot arguments"):
        graph_walk.run_case(atlas, "case.rig.nested", brain="muaddib", viewport=1440,
                            out=tmp_path / "out", engine="replayed", build=False, headless=True)
    assert booted and booted[0]["engine_replay"] == REPO / reply
    assert booted[0]["cli_runner"] == REPO / runner
    assert booted[0]["import_transcriber"] == REPO / transcript


# ── Astra M1 on b7a29e8c6: the agents' folders at the env boundary ───────

AGENT_DIR_OWNER = {"CLAUDE_CONFIG_DIR": "/Users/owner/.claude", "CODEX_HOME": "/Users/owner/.codex",
                   "PI_CODING_AGENT_DIR": "/Users/owner/.pi/agent", "ANTHROPIC_API_KEY": "sk-owner",
                   "PATH": "/usr/bin"}


def _assert_agent_dirs(env: dict[str, Any], home: Path) -> None:
    for name in ("CLAUDE_CONFIG_DIR", "CODEX_HOME", "PI_CODING_AGENT_DIR"):
        assert env.get(name) and Path(env[name]).is_relative_to(home), (name, env.get(name))
    assert not env.get("ANTHROPIC_API_KEY")
    assert env.get("HOLDSPEAK_ACTIVE_TARGET") == "off"


def test_the_graph_walk_hub_env_scopes_every_agent_folder(tmp_path: Path) -> None:
    env = graph_walk._isolated_hub_env(tmp_path, inherited=dict(AGENT_DIR_OWNER))
    _assert_agent_dirs(env, graph_walk.guard_home(tmp_path))


def test_the_glass_boot_scopes_every_agent_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import holdspeak.web_server as web_server

    from tests.e2e import glass_infra

    for key, value in AGENT_DIR_OWNER.items():
        monkeypatch.setenv(key, value)
    seen: dict[str, Any] = {}

    class _Server:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def start(self) -> str:
            seen.update(os.environ)
            return "http://127.0.0.1:0"

    monkeypatch.setattr(web_server, "MeetingWebServer", _Server)
    glass_infra._boot(tmp_path, monkeypatch)
    _assert_agent_dirs(seen, tmp_path / "home")


def test_the_codex_trust_reader_in_the_rig_env_reads_under_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """factory_launch's reader (untrusted_launch_hooks, env=None) starts `codex app-server`
    with the hub's own environment: in a rig hub that is the rig env."""
    from holdspeak import coder_gate
    from holdspeak.agent_context import codex_trust

    seen = tmp_path / "seen.json"
    fake = tmp_path / "bin" / "codex"
    fake.parent.mkdir()
    fake.write_text(
        "#!/bin/sh\n"
        f"printf '{{\"CODEX_HOME\": \"%s\", \"HOME\": \"%s\"}}' \"$CODEX_HOME\" \"$HOME\" > {seen}\n"
        "exit 1\n")
    fake.chmod(0o755)
    home = tmp_path / "rig-home"
    home.mkdir()  # the reader's cwd is HOME
    rig = graph_walk._isolated_hub_env(home, inherited=dict(AGENT_DIR_OWNER))
    for key in list(os.environ):
        monkeypatch.delenv(key, raising=False)
    for key, value in rig.items():
        monkeypatch.setenv(key, value)

    with pytest.raises(codex_trust.CodexTrustError):
        codex_trust.untrusted_launch_hooks(
            coder_gate.codex_hook_flags(coder_gate.spawn_prefix()), executable=str(fake))
    read = json.loads(seen.read_text())
    rig_home = graph_walk.guard_home(home)
    assert Path(read["CODEX_HOME"]).is_relative_to(rig_home), read
    assert Path(read["HOME"]) == rig_home


# ── Astra M2: HOLDSPEAK_ACTIVE_TARGET ────────────────────────────────────


def test_active_target_detection_is_on_by_default_and_reads_nothing_when_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak import target_profile

    scripts: list[Any] = []
    monkeypatch.setattr(target_profile.subprocess, "run", lambda *a, **k: scripts.append(a) or (_ for _ in ()).throw(
        AssertionError("AppleScript ran")))
    monkeypatch.setattr(target_profile.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(target_profile.shutil, "which", lambda name: f"/usr/bin/{name}")

    monkeypatch.delenv(target_profile.ACTIVE_TARGET_ENV, raising=False)
    assert target_profile.active_target_read()
    monkeypatch.setenv(target_profile.ACTIVE_TARGET_ENV, "off")
    assert not target_profile.active_target_read()
    assert target_profile.collect_active_target_hints() == {}
    profile = target_profile.detect_active_target_profile("auto").to_dict()
    assert profile["id"] == "unknown" and profile["source"] == "not_read"
    assert profile["app_name"] is None and profile["window_title"] is None
    assert profile["details"] == {"matched": "not_read_in_rig"}
    # The owner's manual override is config, not the screen: it still applies.
    assert target_profile.detect_active_target_profile("browser").to_dict()["id"] == "browser"
    assert scripts == []


def test_the_readiness_route_answers_without_applescript_in_a_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    from fastapi.testclient import TestClient

    from holdspeak import target_profile
    from tests.e2e import glass_infra

    real_run = subprocess.run

    def guarded(argv: Any, *a: Any, **k: Any) -> Any:
        if isinstance(argv, (list, tuple)) and argv and str(argv[0]).endswith("osascript"):
            raise AssertionError("AppleScript ran in a rig")
        return real_run(argv, *a, **k)

    monkeypatch.setattr(target_profile.subprocess, "run", guarded)
    import holdspeak.web_server as web_server

    captured: dict[str, Any] = {}

    class _Server(web_server.MeetingWebServer):
        def start(self) -> str:
            captured["app"] = self.app
            return "http://127.0.0.1:0"

    monkeypatch.setattr(web_server, "MeetingWebServer", _Server)
    glass_infra._boot(tmp_path, monkeypatch, token="rig")
    client = TestClient(captured["app"])
    response = client.get("/api/dictation/readiness", headers={"Authorization": "Bearer rig"})
    assert response.status_code == 200, response.text
    target = response.json()["target"] if "target" in response.json() else response.json()["target_profile"]
    assert target["source"] == "not_read" and target["app_name"] is None


# ── Astra MAYs ───────────────────────────────────────────────────────────


def test_a_suppressed_heartbeat_notification_is_not_an_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak import desktop_notify

    monkeypatch.setenv(desktop_notify.DESKTOP_NOTIFY_ENV, "0")
    result = desktop_notify.heartbeat_notify(2, 1, edge=desktop_notify.EdgeDetector(),
                                             quiet_hours_start=0, quiet_hours_end=0)
    assert result["fired"] is False
    assert result["reason"] == "not_posted_in_rig"


def test_the_libnotify_notifier_posts_nothing_when_off(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak import desktop_notify
    from holdspeak.desktop_presence_freedesktop import _LibnotifyNotifier

    monkeypatch.setenv(desktop_notify.DESKTOP_NOTIFY_ENV, "0")
    notifier = _LibnotifyNotifier.__new__(_LibnotifyNotifier)
    notifier._notif = None
    notifier._Notify = None  # any use would raise
    notifier.notify({"summary": "s", "body": "b", "icon": "i", "urgency": 1, "transient": True})
    assert notifier._notif is None


def test_the_channel_key_file_names_its_failures_in_the_channels_codes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.services import channel_email, channel_slack
    from holdspeak.services.channel_key_file import CHANNEL_KEYSTORE_ENV

    path = tmp_path / "keys.json"
    monkeypatch.setenv(CHANNEL_KEYSTORE_ENV, str(path))
    _production_key_stores(monkeypatch)
    path.write_text(json.dumps({"HoldSpeak Email": ["not", "a", "bucket"]}))
    path.chmod(0o644)
    with pytest.raises(channel_email.EmailKeyError) as bucket:
        channel_email.read_key("resend", "main")
    assert bucket.value.code == "email_key_store_locked"
    path.write_text("{not json")
    with pytest.raises(channel_slack.SlackKeyError) as malformed:
        channel_slack.KEY_STORE().get("slot")
    assert malformed.value.code == "slack_key_store_locked"
    path.write_text("{}")
    path.chmod(0o644)
    channel_email.save_key("resend", "main", "re_key")
    assert oct(path.stat().st_mode & 0o777) == "0o600"  # an existing file is tightened too
    blocked = tmp_path / "ro"
    blocked.mkdir()
    monkeypatch.setenv(CHANNEL_KEYSTORE_ENV, str(blocked / "sub" / "keys.json"))
    blocked.chmod(0o500)
    try:
        with pytest.raises(channel_email.EmailKeyError) as write:
            channel_email.save_key("resend", "main", "re_key")
        assert write.value.code == "email_key_store_locked"
    finally:
        blocked.chmod(0o700)


# ── moved from tests/unit/test_philo16_rig_isolation.py ──
# PHILO-16 (C), Astra r1 M1/M2: the switches that keep a walk off real engines
# and off the default writer. Both default to the product's own behaviour.

from typing import Any

import pytest

from holdspeak.services import inference_default_service as ids


def test_loopback_ports_default_to_the_four_engines(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ids.LOOPBACK_PORTS_ENV, raising=False)
    assert ids.loopback_engine_ports() == ids.LOOPBACK_ENGINE_PORTS


def test_loopback_ports_read_the_env_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ids.LOOPBACK_PORTS_ENV, "1234, 9999,bad,70000")
    assert ids.loopback_engine_ports() == ((1234, "LM Studio"), (9999, "local engine"))


def test_an_empty_port_list_opens_no_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ids.LOOPBACK_PORTS_ENV, "")
    asked: list[str] = []

    def getter(url: str, **_: Any) -> tuple[int, bytes]:
        asked.append(url)
        return 200, b'{"data": [{"id": "qwen3:8b"}]}'

    assert ids.scan_loopback_engines(http_get=getter) == []
    assert asked == []


def test_the_scan_reads_only_the_named_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ids.LOOPBACK_PORTS_ENV, "1234")
    asked: list[str] = []

    def getter(url: str, **_: Any) -> tuple[int, bytes]:
        asked.append(url)
        return 200, b'{"data": [{"id": "qwen3-8b"}]}'

    found = ids.scan_loopback_engines(http_get=getter)
    assert [row["port"] for row in found] == [1234]
    assert asked and all(":1234/" in url for url in asked)


class _NoTouch:
    """Any read of the database or the assignments fails the test."""

    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"the default writer touched {name!r} while off")


def _service() -> ids.InferenceDefaultService:
    return ids.InferenceDefaultService(
        _NoTouch(), assignment_service=_NoTouch(),
        scan=lambda: (_ for _ in ()).throw(AssertionError("scanned while off")),
        find_embed_model=lambda *a, **k: None,
    )


def test_the_default_writer_is_on_unless_named_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ids.DEFAULT_WRITER_ENV, raising=False)
    assert ids.default_writer_on()
    monkeypatch.setenv(ids.DEFAULT_WRITER_ENV, "on")
    assert ids.default_writer_on()
    monkeypatch.setenv(ids.DEFAULT_WRITER_ENV, " OFF ")
    assert not ids.default_writer_on()


def test_off_the_writer_writes_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ids.DEFAULT_WRITER_ENV, "off")
    service = _service()
    service.kick("detect")
    assert service._thread is None
    assert service.ensure(reason="boot")["status"] == "off"
    assert service.rescan()["status"] == "off"


# ── moved from tests/unit/test_philo7_rig_faithful.py ──
# PHILO-7-01 round two (Astra's check on built, finding 1): the rig sends the SAME request.
#
# The rig's ``op`` step projects a canonical operation onto the existing MCP
# envelope (``scripts/graph_walk.py`` ``_op_request``). ``desk.get`` and
# ``desk.delete`` carry only ``kind`` and ``id``. Before this round, the read and
# delete projections kept the id and DROPPED every other argument, so:
#
# * a refused call became an execution — ``note.delete {note_id, owner:
#   "forged"}`` is refused by the registry (``authority_in_arguments``), but the
#   projected call deleted the note;
# * valid Thought revisions disappeared — ``note.delete`` with the right cursors
#   succeeds through ``invoke`` directly, but the projected call lost them and
#   was refused ``thought_expected_revision_required``.
#
# The rule now fenced, through the REAL hub (``MeetingWebServer`` over
# ``/api/mcp``): a projection either carries every argument of the case, or the
# rig refuses the step by name (``Blocked``) before any request is sent. Never a
# silent drop.

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition
from scripts import graph_walk as gw

TOKEN = "philo7-01-rig"
OWNER = Principal(PrincipalKind.OWNER, "owner")


class _RealHub:
    """The rig's ``hub.mcp`` seam over the real hub app's ``POST /api/mcp``."""

    def __init__(self, client: Any) -> None:
        self.client = client

    def mcp(self, request: dict[str, Any]) -> dict[str, Any]:
        resp = self.client.post("/api/mcp", json=request)
        return resp.json()


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from starlette.testclient import TestClient

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "rig.db")
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        auth_token=TOKEN,
    )
    client = TestClient(server.app, client=("127.0.0.1", 50000))
    client.headers.update({"Authorization": f"Bearer {TOKEN}"})
    yield composition.installed(), client
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _sent_arguments(request: dict[str, Any]) -> dict[str, Any]:
    arguments = request["params"]["arguments"]
    return {**arguments, **(arguments.get("data") or {})}


def test_a_refused_call_never_becomes_an_execution_through_the_rig(hub) -> None:
    root, client = hub
    note = client.post("/api/notes", json={"id": "n", "title": "Keep me"})
    assert note.status_code == 201
    args = {"note_id": "n", "owner": "forged"}
    # Direct: the registry refuses it by name.
    from holdspeak import operations

    with pytest.raises(operations.OperationRefused) as refused:
        root.operations.invoke(OWNER, "note.delete", args)
    assert refused.value.code == "authority_in_arguments"
    # Through the rig: the same request, or a named refusal of the step.
    try:
        record = gw._op_call(_RealHub(client), "note.delete", args)
    except gw.Blocked as exc:
        assert "owner" in str(exc), exc
    else:
        assert record["refusal"] is not None, f"the rig executed a refused call: {record['request']}"
    assert client.get("/api/notes/n").status_code == 200, "the note was deleted by a call the registry refuses"


def test_valid_thought_revisions_never_disappear_through_the_rig(hub) -> None:
    root, client = hub
    assert client.post("/api/directories", json={"id": "hs-seed-inbox", "name": "Inbox"}).status_code == 201
    thought = client.post("/api/thoughts", json={"request_id": "rig-1", "raw_text": "raw", "source": {"kind": "typed"}}).json()["thought"]
    args = {"note_id": thought["working_note"]["id"],
            "expected_aggregate_revision": thought["aggregate_revision"],
            "expected_lifecycle_revision": thought["lifecycle_revision"]}
    try:
        record = gw._op_call(_RealHub(client), "note.delete", args)
    except gw.Blocked as exc:
        assert "expected_aggregate_revision" in str(exc), exc
        # Blocked before any request: the note is untouched.
        assert client.get(f"/api/notes/{args['note_id']}").status_code == 200
        return
    sent = _sent_arguments(record["request"])
    missing = sorted(set(args) - {"note_id"} - set(sent))
    assert not missing, (f"the rig dropped {missing}; the hub answered "
                         f"{record['refusal'] or record['response']}")


READ_DELETE = ["note.read", "note.delete", "zone.read", "zone.delete", "kb.read", "kb.delete", "decision.read"]


@pytest.mark.parametrize("name", READ_DELETE)
def test_no_read_or_delete_projection_drops_an_argument(name) -> None:
    id_field = {"note": "note_id", "zone": "directory_id", "kb": "kb_id", "decision": "decision_id"}[name.split(".")[0]]
    args = {id_field: "x", "extra_field": 1}
    try:
        request = gw._op_request(name, args, 1)
    except gw.Blocked as exc:
        assert "extra_field" in str(exc)
        return
    assert "extra_field" in json.dumps(request), f"{name} dropped extra_field: {request}"


def test_an_id_only_read_and_delete_still_project() -> None:
    request = gw._op_request("zone.delete", {"directory_id": "z"}, 1)
    assert request["params"] == {"name": "desk.delete", "arguments": {"kind": "directories", "id": "z"}}
    request = gw._op_request("note.read", {"note_id": "n"}, 2)
    assert request["params"] == {"name": "desk.get", "arguments": {"kind": "notes", "id": "n"}}


# ── moved from tests/unit/test_philo5_rig_import_boundary.py ──
# PHILO-5-04: the rig stays outside the operation registry process.

import ast
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
RIG_SCRIPTS = (
    REPO / "scripts/graph_walk.py",
    REPO / "scripts/philo5_pairs.py",
)
FORBIDDEN_MODULE = "holdspeak.operations"


def _literal_module(value: ast.AST | None) -> str | None:
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    return None


def _operation_import_violations(source: str, *, filename: str) -> list[str]:
    """Return source locations that would load the operation registry."""
    tree = ast.parse(source, filename=filename)
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == FORBIDDEN_MODULE or alias.name.startswith(
                    f"{FORBIDDEN_MODULE}."
                ):
                    violations.append(
                        f"{filename}:{node.lineno}: import {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == FORBIDDEN_MODULE or module.startswith(
                f"{FORBIDDEN_MODULE}."
            ):
                violations.append(
                    f"{filename}:{node.lineno}: from {module} import ..."
                )
            elif module == "holdspeak" and any(
                alias.name == "operations" for alias in node.names
            ):
                violations.append(
                    f"{filename}:{node.lineno}: from holdspeak import operations"
                )
        elif isinstance(node, ast.Call):
            function = node.func
            dynamic = (
                isinstance(function, ast.Name)
                and function.id in {"__import__", "import_module"}
            ) or (
                isinstance(function, ast.Attribute)
                and function.attr == "import_module"
                and isinstance(function.value, ast.Name)
                and function.value.id == "importlib"
            )
            if dynamic and node.args:
                imported = _literal_module(node.args[0])
                if imported == FORBIDDEN_MODULE or (
                    imported and imported.startswith(f"{FORBIDDEN_MODULE}.")
                ):
                    violations.append(
                        f"{filename}:{node.lineno}: dynamic import {imported}"
                    )
    return violations


def test_rig_scripts_do_not_import_operation_registry() -> None:
    violations = [
        violation
        for path in RIG_SCRIPTS
        for violation in _operation_import_violations(
            path.read_text(encoding="utf-8"), filename=str(path.relative_to(REPO))
        )
    ]
    assert not violations, "rig import boundary crossed:\n" + "\n".join(violations)


def test_same_fence_rejects_forbidden_source_mutations() -> None:
    mutations = (
        "import holdspeak.operations",
        "from holdspeak.operations import OperationRegistry",
        "from holdspeak import operations",
        "import importlib\nimportlib.import_module('holdspeak.operations')",
        "__import__('holdspeak.operations')",
    )
    for path in RIG_SCRIPTS:
        source = path.read_text(encoding="utf-8")
        for mutation in mutations:
            violations = _operation_import_violations(
                source + "\n" + mutation + "\n", filename=str(path.relative_to(REPO))
            )
            assert violations, f"mutation was accepted for {path}: {mutation}"
