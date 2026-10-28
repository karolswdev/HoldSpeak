"""Programs §11, the hand kind: ``AgentHandService.hand(kind="program_step")``
through the REAL hand (real git worktree, real kernel spawn receipt; tmux
and the agent faked: the Conductor K2 rig of ``test_agent_hand.py``)."""
from __future__ import annotations

import shlex
import subprocess

from holdspeak.db.programs import ProgramStore
from holdspeak.services.program_service import ProgramService
from tests.unit.test_agent_hand import OWNER, _rig, _wait_for, db  # noqa: F401 - db is the rig's fixture
from tests.unit.test_factory_launch import _make_repo


def _git(repo, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout.strip()


def test_the_hand_launches_a_program_step_in_its_own_worktree(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    repo = _make_repo(tmp_path)
    base = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    service = ProgramService(db, kernel=lambda **_kw: None, runner=lambda: None)
    program = service.create(OWNER, title="The hub stops stalling", repository=str(repo), control="normal",
                             base_branch=base, check_command="true")
    service.plan(OWNER, program["id"], steps=[{"title": "Indexes", "brief": "Add the indexes.",
                                               "owns": ["holdspeak/db/schema.py"]}])
    step = ProgramStore(db).list_steps(program["id"])[0]
    monkeypatch.setattr("tests.unit.test_agent_hand._make_repo", lambda _path: repo)
    rig = _rig(tmp_path, db, monkeypatch, item=("program", step["id"]))
    worktree = repo.parent / f"hs-program-{step['id']}"

    def claims(**_kw):
        # The rider's SessionStart from the step's worktree (the story ref
        # the hand derived: desk/program_step-<id>).
        if not worktree.exists():
            return []
        return [{"session_key": "claude:smoke-session", "agent": "claude", "lifecycle": "working",
                 "repo_root": str(worktree.resolve()), "cwd": str(worktree.resolve()),
                 "story_claim": {"project": "desk", "story_id": f"program_step-{step['id']}",
                                 "claimed_by": "rider:claude"}}]

    monkeypatch.setattr("holdspeak.agent_context.sessions.list_agent_story_claims", claims)

    result = rig.hand.hand(OWNER, "program_step", step["id"], profile="claude-default")
    assert result["status"] == "launched", result
    assert result["worktree"] == {"name": f"hs-program-{step['id']}",
                                  "branch": "program/the-hub-stops-stalling/1-indexes"}
    assert result["origin_ref"] == {"kind": "program_step", "id": step["id"]}
    assert result["brief"]["refs"] == [f"program_step:{step['id']}"]
    assert (worktree / ".git").exists()
    assert _git(worktree, "rev-parse", "HEAD") == _git(repo, "rev-parse", base)  # from the base branch
    assert _git(worktree, "rev-parse", "--abbrev-ref", "HEAD") == "program/the-hub-stops-stalling/1-indexes"

    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    assert record["origin_ref"] == {"kind": "program_step", "id": step["id"]}
    typed = "\n".join(text for _pane, text in rig.typed)
    assert "HoldSpeak on step 1 of 1 of the program “The hub stops stalling”." in typed
    assert f"Worktree: hs-program-{step['id']}" in typed
    assert "Never report green without the log path." in typed
    from tests.unit._spawn_env import command_of

    spawn = next(c for c in rig.tmux.calls if c[1] == "new-session")
    assert command_of(spawn).startswith(f"cd {shlex.quote(str(worktree.resolve()))} && ")
    rig.tmux.ended = True


def test_a_pi_step_names_its_engine_on_the_launch_request(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    """The step's Runs on engine rides the launch request (``engine_id``);
    the launch service resolves it for pi's models.json (``pi_engine``)."""
    from holdspeak.delivery.factory_launch import LaunchService

    seen: list = []

    def pi_engine(self, engine_id: str = ""):
        seen.append(engine_id)
        raise __import__("holdspeak.delivery.factory_launch", fromlist=["LaunchRefused"]).LaunchRefused(
            "engine_unknown", "probe")

    monkeypatch.setattr(LaunchService, "pi_engine", pi_engine)
    repo = _make_repo(tmp_path)
    service = ProgramService(db, kernel=lambda **_kw: None, runner=lambda: None)
    program = service.create(OWNER, title="Pi", repository=str(repo), control="normal", check_command="true")
    service.plan(OWNER, program["id"], steps=[{"title": "On qwen"}])
    step = ProgramStore(db).list_steps(program["id"])[0]
    monkeypatch.setattr("tests.unit.test_agent_hand._make_repo", lambda _path: repo)
    rig = _rig(tmp_path, db, monkeypatch, item=("program", step["id"]))
    try:
        rig.hand.hand(OWNER, "program_step", step["id"], profile="pi-default", engine="engine-tailscale-karol-8080")
    except Exception as exc:
        assert getattr(exc, "reason", "") == "engine_unknown"
    assert seen == ["engine-tailscale-karol-8080"]
