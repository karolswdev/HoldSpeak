"""Focused proof for the PHILO-13 real-input fixture boundaries."""
from __future__ import annotations

import hashlib
import importlib.util
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
    inherited = {"HOME": "/owner", "TMUX": "/owner/default", "TMUX_PANE": "%9"}
    env = rig._isolated_hub_env(tmp_path, inherited=inherited)
    assert env["HOME"] == str(tmp_path)
    assert env["TMUX_TMPDIR"] == str(tmp_path)
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
    assert "TMUX" not in kill_env and "TMUX_PANE" not in kill_env


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
