"""Programs §11, the hand kind: ``AgentHandService.hand(kind="program_step")``
through the REAL hand (real git worktree, real kernel spawn receipt; tmux
and the agent faked: the Conductor K2 rig of ``test_agent_hand.py``)."""
from __future__ import annotations

import json
import shlex
import subprocess

from holdspeak.db.programs import ProgramStore
from holdspeak.services.program_service import ProgramService
from tests.unit.test_agent_hand import OWNER, _give_origin, _rig, _wait_for, db  # noqa: F401 - db is the rig's fixture
from tests.unit.test_factory_launch import _make_repo


def _git(repo, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout.strip()


def test_the_hand_launches_a_program_step_in_its_own_worktree(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    repo = _make_repo(tmp_path)
    _give_origin(repo)  # HS-S22: a step starts from the base as origin has it
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


# ── HS-S22 (D25/G22 A): the commit a new step starts at ─────────────────


def _checked(repo, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    assert proc.returncode == 0, (args, proc.stderr)
    out = proc.stdout.strip()
    assert out or args[0] in ("init", "status", "push", "remote", "commit", "add", "update-ref", "config", "fetch")
    return out


def _owner_behind_origin(tmp_path, repo):
    """``origin`` beside the repository, and an earlier step's work pushed to
    origin's main by another clone (what the local merge path does: it
    pushes ``HEAD:refs/heads/main`` and never moves the owner's main)."""
    bare = tmp_path / "origin.git"
    _checked(tmp_path, "init", "-q", "--bare", "-b", "main", str(bare))
    _checked(repo, "remote", "add", "origin", str(bare))
    _checked(repo, "push", "-q", "origin", "HEAD:refs/heads/main")
    other = tmp_path / "earlier-step"
    subprocess.run(["git", "clone", "-q", str(bare), str(other)], check=True, capture_output=True)
    _checked(other, "config", "user.email", "agent@example.test")
    _checked(other, "config", "user.name", "Agent")
    (other / "dep.py").write_text("def api():\n    return 1\n", encoding="utf-8")
    _checked(other, "add", "dep.py")
    _checked(other, "commit", "-q", "-m", "step A: the api")
    _checked(other, "push", "-q", "origin", "HEAD:refs/heads/main")
    return _checked(other, "rev-parse", "HEAD")


def _program_rig(tmp_path, db, monkeypatch, repo, steps, *, facts=None):  # noqa: F811
    service = ProgramService(db, kernel=lambda **_kw: None, runner=lambda: None)
    program = service.create(OWNER, title="Two steps", repository=str(repo), control="normal",
                             base_branch="main", check_command="true")
    service.plan(OWNER, program["id"], steps=[{"title": title, "brief": f"{title}."} for title in steps])
    store = ProgramStore(db)
    rows = store.list_steps(program["id"])
    for row, extra in zip(rows, facts or []):
        if extra:
            row["facts"] = {**(row.get("facts") or {}), **extra}
            store.save_step(row)
    monkeypatch.setattr("tests.unit.test_agent_hand._make_repo", lambda _path: repo)
    rig = _rig(tmp_path, db, monkeypatch, item=("program", rows[0]["id"]))
    trees = {row["id"]: repo.parent / f"hs-program-{row['id']}" for row in rows}

    def claims(**_kw):
        return [{"session_key": f"claude:{step_id}", "agent": "claude", "lifecycle": "working",
                 "repo_root": str(tree.resolve()), "cwd": str(tree.resolve()),
                 "story_claim": {"project": "desk", "story_id": f"program_step-{step_id}",
                                 "claimed_by": "rider:claude"}}
                for step_id, tree in trees.items() if tree.exists()]

    monkeypatch.setattr("holdspeak.agent_context.sessions.list_agent_story_claims", claims)
    git_calls: list = []
    real_git = rig.service._git

    def recording_git(argv, *args, **kwargs):
        git_calls.append(list(argv))
        return real_git(argv, *args, **kwargs)

    rig.service._git = recording_git
    return service, program, store.list_steps(program["id"]), rig, trees, git_calls


def test_a_new_step_starts_at_the_base_as_origin_has_it_not_the_owners_older_main(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    """C22-01/02/06/10: the owner's main is behind origin (step A merged on
    the remote). Step B's new worktree starts at origin's main, proved before
    the agent starts; the first message names that commit; the owner's
    checkout, index and branch do not change. Fails on main: B started at the
    owner's older local main (no dep.py)."""
    repo = _make_repo(tmp_path)
    remote = _owner_behind_origin(tmp_path, repo)
    local = _checked(repo, "rev-parse", "main")
    assert remote != local
    (repo / "notes.txt").write_text("owner's own work\n", encoding="utf-8")  # untracked: stays as it is
    service, program, [step], rig, trees, git_calls = _program_rig(tmp_path, db, monkeypatch, repo, ["Use the api"])

    result = rig.hand.hand(OWNER, "program_step", step["id"], profile="claude-default")
    assert result["status"] == "launched", result
    tree = trees[step["id"]]
    assert (tree / "dep.py").read_text(encoding="utf-8") == "def api():\n    return 1\n"
    assert _checked(tree, "rev-parse", "HEAD") == remote

    record = rig.launches.get(result["launch_id"])
    proof = record["start_input"]
    assert proof["policy"] == "remote_base" and proof["base"] == "main" and proof["remote"] == "origin"
    assert proof["selected_commit"] == proof["verified_commit"] == remote
    assert proof["step_id"] == step["id"] and proof["program_id"] == program["id"]
    assert str(tmp_path) not in json.dumps(proof)  # no remote URL, no path
    assert result["start_input"]["verified_commit"] == remote
    # One advertised commit, fetched by its id; never FETCH_HEAD.
    fetches = [argv for argv in git_calls if "fetch" in argv]
    assert fetches == [["git", "-C", str(rig.source.primary_path), "fetch", "--quiet", "--no-tags",
                        "--no-write-fetch-head", "origin", remote]]

    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    typed = "\n".join(text for _pane, text in rig.typed)
    assert f"- Starts at: commit {remote} (main as origin had it at " in typed
    assert record["start_input"]["first_text_bytes"] == result["brief"]["bytes"]

    # The owner's checkout: same branch, same commit, nothing staged, his file kept.
    assert _checked(repo, "branch", "--show-current") == "main"
    assert _checked(repo, "rev-parse", "main") == local
    assert _checked(repo, "status", "--porcelain") == "?? notes.txt"
    rig.tmux.ended = True


def test_a_repository_with_no_origin_is_refused_by_name_before_any_agent(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    """C22-04: no origin, no fallback to the local branch: the launch fails
    at start_input, no worktree is made and nothing is spawned."""
    repo = _make_repo(tmp_path)
    _service, _program, [step], rig, trees, git_calls = _program_rig(tmp_path, db, monkeypatch, repo, ["One"])

    result = rig.hand.hand(OWNER, "program_step", step["id"], profile="claude-default")
    assert result["status"] == "failed"
    assert result["failure"] == {"stage": "start_input", "outcome": "no_remote",
                                 "detail": "the repository has no origin remote"}
    assert not trees[step["id"]].exists()
    assert [c for c in rig.tmux.calls if c[1] == "new-session"] == []
    assert not any("fetch" in argv or "ls-remote" in argv for argv in git_calls)


def test_a_checkpoint_step_starts_at_its_saved_commit_and_a_moved_ref_is_refused(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    """C22-08: a checkpoint start uses the saved commit (no fetch, even when
    origin is ahead); a ref that moved from its saved commit is refused."""
    repo = _make_repo(tmp_path)
    _owner_behind_origin(tmp_path, repo)
    seed = _checked(repo, "rev-parse", "HEAD")
    _checked(repo, "update-ref", "refs/holdspeak/pin/one", seed)
    _checked(repo, "update-ref", "refs/holdspeak/pin/two", seed)
    pins = [{"start_from": {"ref": "refs/holdspeak/pin/one", "commit": seed}},
            {"start_from": {"ref": "refs/holdspeak/pin/two", "commit": seed}}]
    _service, _program, steps, rig, trees, git_calls = _program_rig(
        tmp_path, db, monkeypatch, repo, ["Exact", "Moved"], facts=pins)

    exact = rig.hand.hand(OWNER, "program_step", steps[0]["id"], profile="claude-default")
    assert exact["status"] == "launched", exact
    assert _checked(trees[steps[0]["id"]], "rev-parse", "HEAD") == seed
    proof = rig.launches.get(exact["launch_id"])["start_input"]
    assert proof["policy"] == "checkpoint" and proof["verified_commit"] == seed
    assert not any("fetch" in argv or "ls-remote" in argv for argv in git_calls)

    (repo / "later.txt").write_text("later\n", encoding="utf-8")
    _checked(repo, "add", "later.txt")
    _checked(repo, "commit", "-q", "-m", "later")
    _checked(repo, "update-ref", "refs/holdspeak/pin/two", _checked(repo, "rev-parse", "HEAD"))
    moved = rig.hand.hand(OWNER, "program_step", steps[1]["id"], profile="claude-default")
    assert moved["status"] == "failed"
    assert moved["failure"]["stage"] == "start_input" and moved["failure"]["outcome"] == "checkpoint_moved"
    assert not trees[steps[1]["id"]].exists()
    rig.tmux.ended = True


def test_the_runner_keeps_the_proved_start_as_the_diff_base_when_head_moves_at_once(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    """C22-07: the agent commits right after the spawn. The step's diff base
    is the commit proved before the spawn, not HEAD as the runner reads it."""
    from types import SimpleNamespace

    from holdspeak.services.program_runner import ProgramRunner

    repo = _make_repo(tmp_path)
    remote = _owner_behind_origin(tmp_path, repo)
    service, program, [step], rig, trees, _calls = _program_rig(tmp_path, db, monkeypatch, repo, ["Use the api"])
    tree = trees[step["id"]]

    def hand(*args, **kwargs):
        answer = rig.hand.hand(*args, **kwargs)
        _checked(tree, "config", "user.email", "agent@example.test")
        _checked(tree, "config", "user.name", "Agent")
        (tree / "b.py").write_text("from dep import api\n", encoding="utf-8")
        _checked(tree, "add", "b.py")
        _checked(tree, "commit", "-q", "-m", "step B at once")
        return answer

    ready = service.store.get_step(step["id"])
    ready["state"] = "ready"  # the runner hands a ready step
    service.store.save_step(ready)
    runner = ProgramRunner(service, hand=lambda: SimpleNamespace(hand=hand), ledger=lambda: rig.launches)
    assert runner._hand_step(service.store.get_program(program["id"]), service.store.get_step(step["id"]),
                             "claude-default", None)
    after = service.store.get_step(step["id"])
    moved = _checked(tree, "rev-parse", "HEAD")
    assert moved != remote
    assert after["facts"]["base_commit"] == remote
    assert after["facts"]["start_input"]["verified_commit"] == remote
    assert after["head_commit"] == moved
    rig.tmux.ended = True
