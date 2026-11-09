"""scripts/test_lock.py as one CPU budget (owner ruling 2026-11-09: a load of
30 to 70 on 12 cores is "unacceptable"): runs share the machine while their
CPUs fit $HOLDSPEAK_TEST_CPUS, a run that does not fit waits, a run larger
than the budget runs alone, waiters go in arrival order, a stale holder is
removed, and the CPUs a command takes are read from it."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "scripts" / "test_lock.py"
sys.path.insert(0, str(ROOT / "scripts"))
import test_lock  # noqa: E402


def _env(tmp: Path, **extra: str) -> dict[str, str]:
    return {**os.environ, "HOLDSPEAK_TEST_LOCK": str(tmp / "t.lock"), "HOLDSPEAK_TEST_LOCK_POLL": "0.05",
            "HOLDSPEAK_TEST_CPUS": "8", **extra}


def _run(tmp: Path, name: str, cpus: int, hold: float, log: Path, **extra: str) -> subprocess.Popen:
    body = (f"import time; f=open({str(log)!r},'a'); f.write('start {name} %f\\n' % time.time()); f.flush(); "
            f"time.sleep({hold}); f.write('end {name} %f\\n' % time.time()); f.close()")
    return subprocess.Popen([sys.executable, str(LOCK), "--cpus", str(cpus), "--", sys.executable, "-c", body],
                            env=_env(tmp, **extra), stderr=subprocess.DEVNULL)


def _times(log: Path) -> dict[tuple[str, str], float]:
    return {(kind, name): float(at) for kind, name, at in (line.split() for line in log.read_text().splitlines())}


def _wait_started(log: Path, name: str, timeout: float = 10) -> None:
    end = time.time() + timeout
    while time.time() < end:
        if log.exists() and f"start {name} " in log.read_text():
            return
        time.sleep(0.02)
    raise AssertionError(f"{name} never started")


def _wait_marker(tmp: Path, cpus: int, timeout: float = 10) -> None:
    waiters = tmp / "t.lock.waiters"
    end = time.time() + timeout
    while time.time() < end:
        if waiters.exists() and any(m.name.endswith(f".{cpus}") for m in waiters.iterdir()):
            return
        time.sleep(0.02)
    raise AssertionError(f"no waiter for {cpus} CPUs appeared")


def test_runs_that_fit_the_budget_proceed_together(tmp_path: Path) -> None:
    log = tmp_path / "log"
    a = _run(tmp_path, "a", 4, 0.8, log)
    b = _run(tmp_path, "b", 4, 0.8, log)
    assert a.wait(30) == 0 and b.wait(30) == 0
    t = _times(log)
    assert t[("start", "b")] < t[("end", "a")] and t[("start", "a")] < t[("end", "b")], t


def test_a_run_that_does_not_fit_waits(tmp_path: Path) -> None:
    log = tmp_path / "log"
    a = _run(tmp_path, "a", 6, 0.8, log)
    _wait_started(log, "a")
    b = _run(tmp_path, "b", 4, 0.1, log)
    assert a.wait(30) == 0 and b.wait(30) == 0
    t = _times(log)
    assert t[("start", "b")] >= t[("end", "a")], t
    assert not list((tmp_path / "t.lock.holders").iterdir()), "a holder was left behind"
    assert not list((tmp_path / "t.lock.waiters").iterdir()), "a marker was left behind"


def test_a_run_larger_than_the_budget_runs_alone(tmp_path: Path) -> None:
    log = tmp_path / "log"
    a = _run(tmp_path, "a", 1, 0.6, log)
    _wait_started(log, "a")
    big = _run(tmp_path, "big", 20, 0.3, log)
    assert a.wait(30) == 0 and big.wait(30) == 0
    t = _times(log)
    assert t[("start", "big")] >= t[("end", "a")], t


def test_a_small_run_does_not_pass_an_earlier_large_waiter(tmp_path: Path) -> None:
    log = tmp_path / "log"
    a = _run(tmp_path, "a", 4, 1.0, log)
    _wait_started(log, "a")
    large = _run(tmp_path, "large", 8, 0.3, log)
    _wait_marker(tmp_path, 8)
    small = _run(tmp_path, "small", 1, 0.1, log)  # it fits now, but the large run came first
    for p in (a, large, small):
        assert p.wait(30) == 0
    t = _times(log)
    assert t[("start", "large")] >= t[("end", "a")], t
    assert t[("start", "small")] >= t[("start", "large")], t


def test_a_stale_holder_is_removed(tmp_path: Path) -> None:
    holders = tmp_path / "t.lock.holders"
    holders.mkdir()
    stale = holders / "99999.8"  # nobody holds its flock
    stale.write_text("gone\n")
    log = tmp_path / "log"
    run = _run(tmp_path, "a", 4, 0.05, log)
    assert run.wait(15) == 0
    assert "start a" in log.read_text()
    assert not stale.exists()


def test_the_real_home_is_not_refused(tmp_path: Path) -> None:
    env = _env(tmp_path, HOME=os.path.expanduser("~"))
    run = subprocess.run([sys.executable, str(LOCK), "--class", "unit", "--", "true"], env=env,
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stderr


def test_the_exit_code_is_the_commands(tmp_path: Path) -> None:
    run = subprocess.run([sys.executable, str(LOCK), "--", sys.executable, "-c", "raise SystemExit(3)"],
                         env=_env(tmp_path), capture_output=True, text=True)
    assert run.returncode == 3, run.stderr


def test_the_cpus_are_read_from_the_command(monkeypatch) -> None:
    monkeypatch.setattr(test_lock, "cores", lambda: 12)
    cases = {
        ("uv", "run", "pytest", "-q", "-n", "4", "tests/unit/test_x.py"): 4,
        ("uv", "run", "pytest", "-q", "-n8", "tests/unit/test_x.py"): 8,
        ("uv", "run", "pytest", "-q", "-n", "auto", "tests/unit"): 12,
        ("uv", "run", "pytest", "-q", "tests/unit/test_x.py"): 1,
        ("uv", "run", "pytest", "-q", "-n", "4", "tests/e2e/test_desk_sweep.py"): 8,
        ("uv", "run", "python", "scripts/glass_for.py"): 2,
        ("./node_modules/.bin/vitest", "run", "--maxWorkers=8", "src/x.test.ts"): 4,
        ("npm", "--prefix", "web", "run", "build"): 1,
    }
    assert {c: test_lock.cpus_of(list(c)) for c in cases} == cases


def test_the_budget_defaults_to_the_core_count(monkeypatch) -> None:
    monkeypatch.delenv("HOLDSPEAK_TEST_CPUS", raising=False)
    assert test_lock.budget() == (os.cpu_count() or 1)
    monkeypatch.setenv("HOLDSPEAK_TEST_CPUS", "6")
    assert test_lock.budget() == 6
