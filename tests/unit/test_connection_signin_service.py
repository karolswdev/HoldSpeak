"""ST8: native provider sign-in uses the shared terminal target seam."""
from __future__ import annotations

import subprocess
import re
from typing import Any

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.connection_signin_service import ConnectionSigninService, SignInRefused


OWNER = Principal(PrincipalKind.OWNER, "st8-owner")
AGENT = Principal(PrincipalKind.AGENT, "st8-agent")


def _help_runner(output: str, calls: list[list[str]]):
    def run(argv: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout=output, stderr="")

    return run


def test_native_help_selects_browser_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda binary: f"/bin/{binary}")
    gh_calls: list[list[str]] = []
    gh = ConnectionSigninService._command(
        "github", "github.example", "", runner=_help_runner("--web --hostname", gh_calls)
    )
    assert gh == ["/bin/gh", "auth", "login", "--web", "--hostname", "github.example"]
    assert gh_calls == [["/bin/gh", "auth", "login", "--help"]]

    acli_calls: list[list[str]] = []
    acli = ConnectionSigninService._command(
        "jira", "team.atlassian.net", "owner@example.com",
        runner=_help_runner("--site --email --token --web", acli_calls),
    )
    assert acli == [
        "/bin/acli", "jira", "auth", "login", "--site", "team.atlassian.net",
        "--email", "owner@example.com", "--web",
    ]
    assert acli_calls == [["/bin/acli", "jira", "auth", "login", "--help"]]


def test_start_and_status_use_the_spawned_pane(monkeypatch: pytest.MonkeyPatch) -> None:
    import holdspeak.coder_factory as coder_factory
    import shutil

    monkeypatch.setattr(shutil, "which", lambda _binary: "/bin/gh")
    spawned: dict[str, str] = {}

    def spawn(name: str, *, command: str) -> dict[str, str]:
        spawned.update(name=name, command=command)
        return {"status": "spawned", "pane_id": "%77"}

    monkeypatch.setattr(coder_factory, "spawn", spawn)

    def capture(argv: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        marker = re.search(r"HOLDSPEAK_SIGNIN_DONE:signin_[A-Za-z0-9_-]+", spawned["command"])
        assert marker
        return subprocess.CompletedProcess(argv, 0, stdout=f"{marker.group(0)}:0", stderr="")

    class Targets:
        def issue(self, ref: str) -> dict[str, str]:
            assert ref == "pane:%77"
            return {
                "status": "issued",
                "target_id": "term_st8",
                "target_generation": "gen_st8",
            }

    service = ConnectionSigninService(
        target_provider=Targets,
        runner=_help_runner("--web --hostname", []),
        tmux_runner=capture,
    )
    result = service.start_sign_in(OWNER, "github", "github.com")
    assert result["status"] == "started"
    assert result["target"]["presentation"] == "embedded"
    assert "gh" in spawned["command"]
    assert service.status(OWNER, result["run_id"])["status"] == "finished"


def test_non_owner_and_missing_browser_flow_are_named(monkeypatch: pytest.MonkeyPatch) -> None:
    service = ConnectionSigninService(target_provider=lambda: object())
    with pytest.raises(SignInRefused) as refused:
        service.start_sign_in(AGENT, "github", "github.com")
    assert refused.value.reason == "owner_required"

    import shutil

    monkeypatch.setattr(shutil, "which", lambda _binary: "/bin/gh")
    browserless = ConnectionSigninService(
        target_provider=lambda: object(),
        runner=_help_runner("--hostname --token", []),
    )
    with pytest.raises(SignInRefused) as refused:
        browserless.start_sign_in(OWNER, "github", "github.com")
    assert refused.value.reason == "browser_flow_unsupported"


def test_target_failure_cleans_only_the_new_signin_session(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil
    import holdspeak.coder_factory as coder_factory

    monkeypatch.setattr(shutil, "which", lambda _binary: "/bin/gh")
    spawned: dict[str, str] = {}

    def spawn(name: str, *, command: str) -> dict[str, str]:
        spawned["name"] = name
        return {"status": "spawned", "pane_id": "%88"}

    monkeypatch.setattr(coder_factory, "spawn", spawn)
    cleanup: list[list[str]] = []

    def tmux(argv: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        cleanup.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    class Targets:
        def issue(self, _ref: str) -> dict[str, str]:
            return {"status": "pane_gone", "detail": "private pane gone"}

    service = ConnectionSigninService(
        target_provider=Targets,
        runner=_help_runner("--web --hostname", []),
        tmux_runner=tmux,
    )
    with pytest.raises(SignInRefused) as refused:
        service.start_sign_in(OWNER, "github", "github.com")
    assert refused.value.reason == "terminal_target_failed"
    assert cleanup == [["tmux", "kill-session", "-t", spawned["name"]]]


def test_status_names_terminal_capture_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil
    import holdspeak.coder_factory as coder_factory

    monkeypatch.setattr(shutil, "which", lambda _binary: "/bin/gh")
    monkeypatch.setattr(
        coder_factory,
        "spawn",
        lambda name, *, command: {"status": "spawned", "pane_id": "%89"},
    )

    def tmux(argv: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="no server")

    class Targets:
        def issue(self, _ref: str) -> dict[str, str]:
            return {"status": "issued", "target_id": "term", "target_generation": "gen"}

    service = ConnectionSigninService(
        target_provider=Targets,
        runner=_help_runner("--web --hostname", []),
        tmux_runner=tmux,
    )
    result = service.start_sign_in(OWNER, "github", "github.com")
    status = service.status(OWNER, result["run_id"])
    assert status["status"] == "failed"
    assert status["error"] == "Sign-in terminal is unavailable."


def test_nonzero_native_exit_marker_is_a_named_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil
    import holdspeak.coder_factory as coder_factory

    monkeypatch.setattr(shutil, "which", lambda _binary: "/bin/gh")
    monkeypatch.setattr(
        coder_factory,
        "spawn",
        lambda name, *, command: {"status": "spawned", "pane_id": "%90"},
    )
    run_id = ""

    def tmux(argv: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            argv, 0, stdout=f"HOLDSPEAK_SIGNIN_DONE:{run_id}:7\n", stderr=""
        )

    class Targets:
        def issue(self, _ref: str) -> dict[str, str]:
            return {"status": "issued", "target_id": "term", "target_generation": "gen"}

    service = ConnectionSigninService(
        target_provider=Targets,
        runner=_help_runner("--web --hostname", []),
        tmux_runner=tmux,
    )
    result = service.start_sign_in(OWNER, "github", "github.com")
    run_id = result["run_id"]

    status = service.status(OWNER, run_id)

    assert status["status"] == "failed"
    assert status["exit_code"] == 7
    assert status["error"] == "CLI exited with 7"

