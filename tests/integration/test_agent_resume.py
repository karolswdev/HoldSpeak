"""Betterment AG6: Resume after a restart.

A launched agent registers (its session id and resume command land on the
launch), a restart takes its tmux session (``record_restart_stops``), and
one press on Resume opens a new tmux session in the same worktree, through
the launch's own start-up (``factory.spawn``: a fresh credential), running
the agent's own resume. The hand rig fakes tmux only (tests/unit/
test_agent_hand.py); the composed command is then run by a real shell with
a FAKE ``claude`` first on PATH (never the owner's): a known id resumes, an
old id leaves a shell in the worktree, and the flight reads
``resume_failed`` once the agent has not reported in the window.
"""
from __future__ import annotations

import os
import stat
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import pytest

import holdspeak.agent_context as agent_context
from holdspeak.agent_context import ingest_agent_hook_event
from holdspeak.delivery.factory_launch import LaunchRefused, resume_argv
from holdspeak.services.agent_flights import (
    RESUME_WINDOW_SECONDS,
    STOPPED_BY_RESTART,
    agent_flights,
    flight_of_launch,
)
from holdspeak.services.agent_hand_service import AgentHandRefused
from holdspeak.services.launch_lane import record_restart_stops
from tests.unit._spawn_env import command_of
from tests.unit.test_agent_hand import OWNER, _rig, _wait_for, db  # noqa: F401  (db is a fixture)

SID = "3f1c2a9e-7b44-4d0e-9a61-0c2f5e8d1b7a"


def test_the_resume_argv_per_agent():
    """The agents' own resume (each CLI's --help, 2026-10-18)."""
    assert resume_argv("claude", ["claude", "--settings", "s.json"], SID) == [
        "claude", "--settings", "s.json", "--resume", SID]
    assert resume_argv("codex", ["codex", "-c", "hooks=1", "--ask-for-approval", "never"], SID) == [
        "codex", "resume", "-c", "hooks=1", "--ask-for-approval", "never", SID]
    assert resume_argv("pi", ["pi", "--session-dir", "/x/sessions"], SID) == [
        "pi", "--session-dir", "/x/sessions", "--session", SID]
    with pytest.raises(LaunchRefused) as exc:
        resume_argv("claude", ["claude"], "id; rm -rf /")
    assert exc.value.reason == "no_session_to_resume"


@pytest.fixture
def sessions(tmp_path, monkeypatch):
    path = tmp_path / "agent_sessions.json"
    monkeypatch.setattr(agent_context, "AGENT_CONTEXT_FILE", path)

    def hook(event: str, *, sid: str = "smoke-session", now=None, **payload) -> None:
        ingest_agent_hook_event(agent="claude", state_path=path, now=now, payload={
            "session_id": sid, "cwd": "/tmp/x", "hook_event_name": event, **payload})

    return hook


def _stopped(tmp_path, db, monkeypatch, sessions):  # noqa: F811
    """A launch that registered and worked, then a restart took tmux."""
    rig = _rig(tmp_path, db, monkeypatch)
    launch_id = rig.hand.hand(OWNER, "action", "ai_1")["launch_id"]
    # The launch's own first-message watcher may bind the rider first (a
    # thread): bind here too, then wait for the ledger to say registered.
    rig.service.bind_rider_claims()
    record = _wait_for(lambda: rig.launches.get(launch_id), "state", "registered")
    assert record["session_key"] == "claude:smoke-session"
    # Registration stores what Resume runs.
    assert record["resume_command"] == "claude --resume smoke-session"
    sessions("SessionStart", source="startup")
    sessions("UserPromptSubmit", prompt="the brief")
    sessions("PostToolUse", tool_name="Bash")
    # The Mac restarts: tmux and every session in it are gone.
    rig.tmux.sessions.clear()
    rig.tmux.meta.clear()
    assert record_restart_stops(db=db, ledger=rig.launches, alive=lambda _name: False) == [launch_id]
    assert flight_of_launch(db, launch_id, ledger=rig.launches)["state"] == STOPPED_BY_RESTART
    return rig, launch_id


def test_resume_runs_the_agents_own_resume_in_the_same_worktree(tmp_path, db, monkeypatch, sessions):  # noqa: F811
    rig, launch_id = _stopped(tmp_path, db, monkeypatch, sessions)
    spawns_before = len([c for c in rig.tmux.calls if c[:2] == ["tmux", "new-session"]])

    answer = rig.hand.resume_after_restart(OWNER, launch_id)
    assert answer["state"] == "registered" and answer["resume"]["state"] == "resuming"
    assert answer["resume"]["command"] == "claude --resume smoke-session"
    [spawn] = [c for c in rig.tmux.calls if c[:2] == ["tmux", "new-session"]][spawns_before:]
    record = rig.launches.get(launch_id)
    # The launch's own tmux name, the launch's worktree, the agent's resume
    # with the launch's start-up (spawn settings, MCP config), a shell after a failure.
    assert spawn[spawn.index("-s") + 1] == record["session"]
    command = command_of(spawn)
    assert command.startswith(f"cd {rig.worktree} && ")
    assert "--settings" in command and "--mcp-config" in command
    assert "--resume smoke-session" in command
    assert command.endswith('|| exec "${SHELL:-/bin/sh}" -l')
    assert record["target"]["pane_id"] and record["stopped"] is None
    # Resuming until the resumed session reports, then its own state (the
    # rig's launch clock is fixed: read the flight a second after the press).
    pressed = datetime.fromisoformat(record["resume"]["at"].replace("Z", "+00:00"))

    def state_now() -> str:
        [flight] = [f for f in agent_flights(db, ledger=rig.launches, now=pressed + timedelta(seconds=1))
                    if f["launch_id"] == launch_id]
        return flight["state"]

    assert state_now() == "resuming"
    sessions("SessionStart", source="resume", now=pressed + timedelta(milliseconds=500))
    assert state_now() == "working"


def test_resume_refuses_a_launch_that_is_not_stopped(tmp_path, db, monkeypatch, sessions):  # noqa: F811
    rig, launch_id = _stopped(tmp_path, db, monkeypatch, sessions)
    rig.hand.resume_after_restart(OWNER, launch_id)
    with pytest.raises(AgentHandRefused) as exc:
        rig.hand.resume_after_restart(OWNER, launch_id)   # the second press
    assert exc.value.code == "launch_not_stopped"


def test_an_old_id_leaves_a_shell_in_the_worktree_and_reads_resume_failed(tmp_path, db, monkeypatch, sessions):  # noqa: F811
    rig, launch_id = _stopped(tmp_path, db, monkeypatch, sessions)
    rig.hand.resume_after_restart(OWNER, launch_id)
    spawn = [c for c in rig.tmux.calls if c[:2] == ["tmux", "new-session"]][-1]
    command = command_of(spawn)

    # The composed command, run by a real shell, with a FAKE claude first on
    # PATH: it knows no conversation "smoke-session" and exits 1, as the
    # real CLI does for an old id. The fallback is the login shell.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "fake.log"
    fake = bin_dir / "claude"
    fake.write_text(
        "#!/bin/sh\n"
        f'echo "claude $*" >> {log}\n'
        'echo "No conversation found with session ID: smoke-session" >&2\n'
        "exit 1\n"
    )
    shell = bin_dir / "login-shell"
    shell.write_text(f'#!/bin/sh\necho "shell in $(pwd)" >> {log}\n')
    for path in (fake, shell):
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin", "SHELL": str(shell), "HOME": str(tmp_path)}
    done = subprocess.run(["/bin/sh", "-c", command], env=env, capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stderr
    lines = log.read_text().splitlines()
    assert lines[0].startswith("claude ") and lines[0].endswith("--resume smoke-session")
    assert lines[1] == f"shell in {os.path.realpath(rig.worktree)}"

    # The agent never reported: past the window the flight reads resume_failed.
    pressed = datetime.fromisoformat(rig.launches.get(launch_id)["resume"]["at"].replace("Z", "+00:00"))
    later = pressed + timedelta(seconds=RESUME_WINDOW_SECONDS + 1)
    from holdspeak.services.agent_flights import launch_history

    [failed] = [f for f in launch_history(db, ledger=rig.launches, now=later) if f["launch_id"] == launch_id]
    assert failed["state"] == "resume_failed"


def test_only_the_owner_resumes(tmp_path, db, monkeypatch, sessions):  # noqa: F811
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.errors import ServiceError

    rig, launch_id = _stopped(tmp_path, db, monkeypatch, sessions)
    with pytest.raises(ServiceError) as exc:
        rig.hand.resume_after_restart(Principal(PrincipalKind.AGENT, "agent:x"), launch_id)
    assert exc.value.code == "owner_required"
    assert rig.launches.get(launch_id)["state"] == STOPPED_BY_RESTART


def test_the_route_answers_202_while_it_resumes(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from holdspeak.web.routes.agent_hand import build_agent_hand_router

    class _Service:
        def resume_after_restart(self, _principal, launch_id):
            if launch_id == "gone":
                raise AgentHandRefused("launch_not_stopped", "only an agent a restart stopped resumes")
            return {"launch_id": launch_id, "state": "registered",
                    "resume": {"state": "resuming", "at": "2026-10-18T10:00:00Z",
                               "command": "claude --resume s1", "outcome": None}}

    app = FastAPI()
    app.include_router(build_agent_hand_router(SimpleNamespace(agent_hand_service=_Service())))
    client = TestClient(app)
    answer = client.post("/api/agent/launches/l1/resume")
    assert answer.status_code == 202 and answer.json()["resume"]["state"] == "resuming"
    refused = client.post("/api/agent/launches/gone/resume")
    assert refused.status_code == 409 and refused.json()["code"] == "launch_not_stopped"


def test_a_resuming_agent_holds_a_slot_and_a_failed_resume_does_not(tmp_path, db, monkeypatch, sessions):  # noqa: F811
    """AG5 x AG6: an agent resuming after a restart counts as starting; past
    the window, a failed Resume holds no "working at once" slot."""
    from holdspeak.services.agent_flights import slot_holders

    rig, launch_id = _stopped(tmp_path, db, monkeypatch, sessions)
    rig.hand.resume_after_restart(OWNER, launch_id)
    record = rig.launches.get(launch_id)
    pressed = datetime.fromisoformat(record["resume"]["at"].replace("Z", "+00:00"))
    soon = slot_holders(db, [record], now=pressed + timedelta(seconds=1))
    assert [r["launch_id"] for r in soon] == [launch_id]
    late = slot_holders(db, [record], now=pressed + timedelta(seconds=RESUME_WINDOW_SECONDS + 1))
    assert late == []
