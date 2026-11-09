"""scripts/test_lock.py classes (2026-11-08, owner: "I still see a ton of
sequentiality… come on"): unit runs share the machine (3 slots), a browser run
is exclusive against every run, a waiting browser run goes before later unit
runs, a unit run needs an isolated HOME, and a high load makes a unit run wait
until it can run alone (the owner's catch 2026-10-07: runs broke each other)."""
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
    home = tmp / "home"
    home.mkdir(exist_ok=True)
    return {**os.environ, "HOME": str(home), "HOLDSPEAK_TEST_LOCK": str(tmp / "t.lock"),
            "HOLDSPEAK_TEST_LOCK_POLL": "0.05", "HOLDSPEAK_TEST_LOCK_MAX_LOAD": "100000", **extra}


def _run(tmp: Path, name: str, cls: str, hold: float, log: Path, **extra: str) -> subprocess.Popen:
    body = (f"import time; f=open({str(log)!r},'a'); f.write('start {name} %f\\n' % time.time()); f.flush(); "
            f"time.sleep({hold}); f.write('end {name} %f\\n' % time.time()); f.close()")
    return subprocess.Popen([sys.executable, str(LOCK), "--class", cls, "--", sys.executable, "-c", body],
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


def _wait_marker(tmp: Path, suffix: str, timeout: float = 10) -> None:
    waiters = tmp / "t.lock.waiters"
    end = time.time() + timeout
    while time.time() < end:
        if waiters.exists() and any(m.name.endswith(suffix) for m in waiters.iterdir()):
            return
        time.sleep(0.02)
    raise AssertionError(f"no {suffix} marker appeared")


def test_two_unit_runs_proceed_together(tmp_path: Path) -> None:
    log = tmp_path / "log"
    a = _run(tmp_path, "a", "unit", 0.8, log)
    b = _run(tmp_path, "b", "unit", 0.8, log)
    assert a.wait(30) == 0 and b.wait(30) == 0
    t = _times(log)
    assert t[("start", "b")] < t[("end", "a")] and t[("start", "a")] < t[("end", "b")], t


def test_a_browser_run_waits_for_both_unit_runs_and_a_third_unit_run_waits_for_it(tmp_path: Path) -> None:
    log = tmp_path / "log"
    a = _run(tmp_path, "a", "unit", 1.0, log)
    b = _run(tmp_path, "b", "unit", 1.0, log)
    _wait_started(log, "a")
    _wait_started(log, "b")
    browser = _run(tmp_path, "browser", "browser", 0.3, log)
    _wait_marker(tmp_path, ".high.browser")
    third = _run(tmp_path, "c", "unit", 0.1, log)  # a free slot, but a browser run waits first
    for p in (a, b, browser, third):
        assert p.wait(30) == 0
    t = _times(log)
    assert t[("start", "browser")] >= max(t[("end", "a")], t[("end", "b")]), t
    assert t[("start", "c")] >= t[("end", "browser")], t
    assert not list((tmp_path / "t.lock.waiters").iterdir()), "a marker was left behind"


def test_a_unit_run_waits_when_every_slot_is_taken(tmp_path: Path) -> None:
    log = tmp_path / "log"
    a = _run(tmp_path, "a", "unit", 0.8, log, HOLDSPEAK_TEST_LOCK_SLOTS="2")
    b = _run(tmp_path, "b", "unit", 0.8, log, HOLDSPEAK_TEST_LOCK_SLOTS="2")
    _wait_started(log, "a")
    _wait_started(log, "b")
    c = _run(tmp_path, "c", "unit", 0.1, log, HOLDSPEAK_TEST_LOCK_SLOTS="2")
    for p in (a, b, c):
        assert p.wait(30) == 0
    t = _times(log)
    assert t[("start", "c")] >= min(t[("end", "a")], t[("end", "b")]), t


def test_a_unit_run_waits_to_run_alone_when_the_load_is_high(tmp_path: Path) -> None:
    log = tmp_path / "log"
    a = _run(tmp_path, "a", "unit", 0.6, log)
    _wait_started(log, "a")
    b = _run(tmp_path, "b", "unit", 0.1, log, HOLDSPEAK_TEST_LOCK_MAX_LOAD="-1")
    assert a.wait(30) == 0 and b.wait(30) == 0
    t = _times(log)
    assert t[("start", "b")] >= t[("end", "a")], t


def test_a_unit_run_with_the_real_home_is_refused(tmp_path: Path) -> None:
    env = _env(tmp_path, HOME=test_lock.real_home())
    run = subprocess.run([sys.executable, str(LOCK), "--class", "unit", "--", "true"], env=env,
                         capture_output=True, text=True)
    assert run.returncode == 2
    assert "isolated HOME" in run.stderr and "real home" in run.stderr


def test_a_browser_run_with_the_real_home_is_not_refused(tmp_path: Path) -> None:
    env = _env(tmp_path, HOME=test_lock.real_home())
    run = subprocess.run([sys.executable, str(LOCK), "--class", "browser", "--", "true"], env=env,
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stderr


def test_the_default_class_reads_the_command() -> None:
    unit = [["uv", "run", "pytest", "-q", "-n", "8", "tests/unit/test_x.py"],
            ["./node_modules/.bin/vitest", "run", "src/x.test.ts"],
            ["uv", "run", "pytest", "-q", "-m", "not slow", "tests/unit", "tests/integration"]]
    browser = [["uv", "run", "pytest", "-q", "tests/e2e/test_desk_sweep.py"],
               ["uv", "run", "pytest", "-q", "tests/"], ["uv", "run", "pytest", "-q"],
               ["uv", "run", "pytest", "tests/unit", "tests/uat"], ["npm", "--prefix", "web", "run", "build"],
               ["sh", "-c", "uv run pytest tests/unit/x.py"], ["uv", "run", "python", "scripts/glass_for.py"]]
    assert [test_lock.guess_class(c) for c in unit] == ["unit"] * len(unit)
    assert [test_lock.guess_class(c) for c in browser] == ["browser"] * len(browser)


def test_a_bad_class_is_refused(tmp_path: Path) -> None:
    run = subprocess.run([sys.executable, str(LOCK), "--class", "gpu", "--", "true"], env=_env(tmp_path),
                         capture_output=True, text=True)
    assert run.returncode == 2 and "--class" in run.stderr
