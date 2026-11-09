"""scripts/quick_check_memo.py (2026-11-08): a step's key is the content of
its input set (and its test selection); a recorded green with the same key is
found again; a change to an input or to the selection is a new key."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

MEMO = Path(__file__).resolve().parents[2] / "scripts" / "quick_check_memo.py"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _memo(repo: Path, *args: str) -> str:
    env = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null"}
    return subprocess.run([sys.executable, str(MEMO), *args], cwd=repo, env=env, check=True,
                          capture_output=True, text=True).stdout


def _plan(repo: Path, *steps: str) -> dict[str, tuple[str, str]]:
    return {row.split()[0]: (row.split()[1], row.split()[2]) for row in _memo(repo, "plan", *steps).splitlines()}


def test_a_green_is_found_again_until_an_input_or_the_selection_changes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "web").mkdir(parents=True)
    (repo / "holdspeak").mkdir()
    (repo / "web" / "a.ts").write_text("a\n")
    (repo / "holdspeak" / "m.py").write_text("x = 1\n")
    _git(repo, "init", "-q")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "add", ".")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "one")
    sel = tmp_path / "sel"
    sel.write_text("tests/unit/test_a.py\n")

    first = _plan(repo, "build", f"pytest={sel}")
    assert first["build"][1] == "-" and first["pytest"][1] == "-"
    _memo(repo, "record", f"build={first['build'][0]}", f"pytest={first['pytest'][0]}")
    again = _plan(repo, "build", f"pytest={sel}")
    assert again["build"][1] != "-" and again["pytest"] == (first["pytest"][0], again["pytest"][1])
    assert again["pytest"][1] != "-"

    # A hub change is not a web input: the build stays green, pytest does not.
    (repo / "holdspeak" / "m.py").write_text("x = 2\n")
    hub = _plan(repo, "build", f"pytest={sel}")
    assert hub["build"][1] != "-" and hub["pytest"][1] == "-"

    # An untracked web file and a new selection are new keys.
    (repo / "holdspeak" / "m.py").write_text("x = 1\n")
    sel.write_text("tests/unit/test_a.py\ntests/unit/test_b.py\n")
    assert _plan(repo, f"pytest={sel}")["pytest"][1] == "-"
    (repo / "web" / "b.ts").write_text("b\n")
    assert _plan(repo, "build")["build"][1] == "-"


def test_the_install_key_moves_only_with_the_lock_file(tmp_path: Path) -> None:
    """2026-11-08: `npm ci` runs only when web/package-lock.json changed since
    its last green; a source edit under web/ is not a reason to reinstall."""
    repo = tmp_path / "repo"
    (repo / "web").mkdir(parents=True)
    (repo / "web" / "package-lock.json").write_text('{"v": 1}\n')
    (repo / "web" / "a.ts").write_text("a\n")
    _git(repo, "init", "-q")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "add", ".")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "one")
    key = _plan(repo, "npm")["npm"][0]
    _memo(repo, "record", f"npm={key}")
    (repo / "web" / "a.ts").write_text("b\n")
    assert _plan(repo, "npm")["npm"][1] != "-"
    (repo / "web" / "package-lock.json").write_text('{"v": 2}\n')
    assert _plan(repo, "npm")["npm"][1] == "-"


def test_an_unknown_step_is_refused(tmp_path: Path) -> None:
    run = subprocess.run([sys.executable, str(MEMO), "plan", "nope"], cwd=tmp_path, capture_output=True, text=True)
    assert run.returncode == 2


def test_a_retry_records_only_at_the_head_it_retries_and_only_on_the_inputs_that_run_saw(tmp_path: Path) -> None:
    """2026-11-08: a --retry recorded vitest, pytest and the repo guards green
    at a head two merges after the run it retried; the next full check skipped
    them on inputs they never ran on. A retry records a step only at the head
    of the retried run and only when the step's key is the one that run saw."""
    repo = tmp_path / "repo"
    (repo / "web").mkdir(parents=True)
    (repo / "holdspeak").mkdir()
    (repo / "web" / "a.ts").write_text("a\n")
    (repo / "holdspeak" / "m.py").write_text("x = 1\n")
    _git(repo, "init", "-q")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "add", ".")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "one")
    red_head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    seen = _plan(repo, "build", "pytest")
    retry = repo / ".tmp" / "quick-check" / "retry.txt"
    retry.parent.mkdir(parents=True)
    retry.write_text(f"base origin/main\nhead {red_head}\nkey build {seen['build'][0]}\nkey pytest {seen['pytest'][0]}\n"
                     "ids pytest tests/unit/test_a.py::test_x\nstep build\n")

    # Main moves on: a hub merge lands; the web inputs did not change.
    (repo / "holdspeak" / "m.py").write_text("x = 2\n")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "two")
    now = _plan(repo, "build", "pytest")
    out = _memo(repo, "promote", str(retry), f"build={now['build'][0]}", f"pytest={now['pytest'][0]}")
    assert f"build: green at {red_head[:9]}" in out
    assert "pytest: inputs changed since the run being retried: the next check runs this step in full" in out

    memo = __import__("json").loads((repo / ".tmp" / "quick-check" / "green.json").read_text())
    assert memo["build"]["head"] == red_head, "a retry records at the head of the run it retries"
    assert "pytest" not in memo, "a step whose inputs changed is left alone"
    after = _plan(repo, "build", "pytest")
    assert after["build"][1] == red_head[:9] and after["pytest"][1] == "-"
