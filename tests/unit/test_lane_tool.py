"""scripts/lane.sh on a scratch repository: ls, new and done (no network, no uv sync)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

LANE = Path(__file__).resolve().parents[2] / "scripts" / "lane.sh"


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def _lane(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "HOLDSPEAK_LANE_NO_SYNC": "1", "GIT_TERMINAL_PROMPT": "0"}
    return subprocess.run(
        ["/bin/bash", str(LANE), *args], cwd=cwd, env=env, capture_output=True, text=True
    )


def _repo(tmp_path: Path) -> Path:
    origin = tmp_path / "origin.git"
    main = tmp_path / "Main"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    _git(tmp_path, "init", "-q", "-b", "main", str(main))
    for key, value in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")):
        _git(main, "config", key, value)
    (main / "web").mkdir()
    (main / "web" / "package-lock.json").write_text("{}\n")
    (main / "web" / "node_modules").mkdir()
    (main / ".gitignore").write_text("web/node_modules\n.venv/\n")
    _git(main, "add", ".")
    _git(main, "commit", "-q", "-m", "one")
    _git(main, "remote", "add", "origin", str(origin))
    _git(main, "push", "-q", "origin", "main")
    _git(main, "fetch", "-q", "origin")
    return main


def _rows(out: str) -> dict[str, list[str]]:
    return {line.split()[0]: line.split() for line in out.splitlines()[1:] if line.strip()}


def test_ls_names_merged_and_unmerged_lanes(tmp_path: Path) -> None:
    main = _repo(tmp_path)
    _git(main, "worktree", "add", "-q", str(tmp_path / "wt-merged"), "-b", "merged", "origin/main")
    work = tmp_path / "wt-work"
    _git(main, "worktree", "add", "-q", str(work), "-b", "work", "origin/main")
    (work / "a.txt").write_text("a\n")
    _git(work, "add", "a.txt")
    _git(work, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "two")
    (work / "b.txt").write_text("dirty\n")
    (work / ".venv").mkdir()

    result = _lane(main, "ls")
    assert result.returncode == 0, result.stderr
    rows = _rows(result.stdout)
    assert result.stdout.splitlines()[0].split() == ["NAME", "BRANCH", "MERGED", "CLEAN", "VENV", "STATE", "SIZE"]
    assert rows["wt-merged"][1:6] == ["merged", "yes", "yes", "no", "done"]
    assert rows["wt-work"][1:6] == ["work", "no", "no", "yes", "active"]
    assert rows["Main"][1] == "main"


def test_new_links_the_shared_install_and_done_removes_it(tmp_path: Path) -> None:
    main = _repo(tmp_path)
    made = _lane(main, "new", "pipe/x")
    assert made.returncode == 0, made.stderr
    lane = Path(made.stdout.strip().splitlines()[-1])
    assert lane == tmp_path / "wt-pipe-x"
    link = lane / "web" / "node_modules"
    assert link.is_symlink() and link.resolve() == (main / "web" / "node_modules").resolve()
    assert _git(lane, "branch", "--show-current").strip() == "pipe/x"

    gone = _lane(main, "done", "pipe/x")
    assert gone.returncode == 0, gone.stderr
    assert not lane.exists()
    assert "deleted branch pipe/x" in gone.stdout
    assert (main / "web" / "node_modules").is_dir()


def test_new_refuses_a_lock_file_the_shared_install_does_not_match(tmp_path: Path) -> None:
    main = _repo(tmp_path)
    (main / "web" / "package-lock.json").write_text('{"changed": true}\n')
    result = _lane(main, "new", "y")
    assert result.returncode == 1
    assert "package-lock.json differs" in result.stderr
    assert not (tmp_path / "wt-y").exists()


def test_purge_removes_merged_clean_lanes_and_leaves_active_ones_whole(tmp_path: Path) -> None:
    main = _repo(tmp_path)
    merged = tmp_path / "wt-merged"
    _git(main, "worktree", "add", "-q", str(merged), "-b", "merged", "origin/main")
    work = tmp_path / "wt-work"
    _git(main, "worktree", "add", "-q", str(work), "-b", "work", "origin/main")
    (work / "a.txt").write_text("a\n")
    _git(work, "add", "a.txt")
    _git(work, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "two")
    (work / ".venv").mkdir()

    fresh = _lane(main, "purge")  # both lanes moved seconds ago: nothing is touched
    assert fresh.returncode == 0, fresh.stderr
    assert merged.exists() and (work / ".venv").exists()
    assert "active: moved in the last 2 h" in fresh.stdout

    env_old = {"HOLDSPEAK_LANE_MIN_AGE_H": "0"}
    old = subprocess.run(
        ["/bin/bash", str(LANE), "purge"], cwd=main, capture_output=True, text=True,
        env={**os.environ, **env_old},
    )
    assert old.returncode == 0, old.stderr
    assert not merged.exists()
    assert work.exists() and (work / ".venv").exists()  # an unmerged lane keeps its installs
    assert "active: not merged" in old.stdout
    assert "removed 1 worktrees" in old.stdout
