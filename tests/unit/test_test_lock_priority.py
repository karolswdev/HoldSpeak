"""scripts/test_lock.py priority (the fast cycle, 2026-10-12): a LOW run (the
main watcher's shards) never takes the lock while a HIGH run (a quick check,
a lane's scoped run) waits; a stale marker is ignored; HIGH runs still
serialize on the flock."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "scripts" / "test_lock.py"


def _run(tmp: Path, name: str, prio: str, hold: float, log: Path) -> subprocess.Popen:
    """A locked run that logs its start and end (monotonic times) to `log`."""
    env = {**os.environ, "HOLDSPEAK_TEST_LOCK": str(tmp / "t.lock"),
           "HOLDSPEAK_TEST_LOCK_PRIORITY": prio, "HOLDSPEAK_TEST_LOCK_POLL": "0.05"}
    body = (f"import time; f=open({str(log)!r},'a'); f.write('start {name} %f\\n' % time.time()); f.flush(); "
            f"time.sleep({hold}); f.write('end {name} %f\\n' % time.time()); f.close()")
    return subprocess.Popen([sys.executable, str(LOCK), "--", sys.executable, "-c", body], env=env,
                            stderr=subprocess.DEVNULL)


def _order(log: Path) -> list[tuple[str, str, float]]:
    rows = [line.split() for line in log.read_text().splitlines()]
    return sorted(((kind, name, float(at)) for kind, name, at in rows), key=lambda r: r[2])


def _wait_for_marker(tmp: Path, prio: str, timeout: float = 10) -> None:
    waiters = tmp / "t.lock.waiters"
    end = time.time() + timeout
    while time.time() < end:
        if waiters.exists() and any(m.name.endswith(f".{prio}") for m in waiters.iterdir()):
            return
        time.sleep(0.02)
    raise AssertionError(f"no {prio} marker appeared")


def _wait_started(log: Path, name: str, timeout: float = 10) -> None:
    end = time.time() + timeout
    while time.time() < end:
        if log.exists() and f"start {name} " in log.read_text():
            return
        time.sleep(0.02)
    raise AssertionError(f"{name} never started")


def test_a_low_waiter_yields_to_a_high_waiter_that_arrives_later(tmp_path: Path) -> None:
    log = tmp_path / "log"
    holder = _run(tmp_path, "holder", "high", 1.0, log)
    _wait_started(log, "holder")
    low = _run(tmp_path, "low", "low", 0.1, log)
    _wait_for_marker(tmp_path, "low")
    time.sleep(0.2)
    high = _run(tmp_path, "high", "high", 0.1, log)  # arrives AFTER the low one
    for p in (holder, low, high):
        assert p.wait(30) == 0
    starts = [name for kind, name, _ in _order(log) if kind == "start"]
    assert starts == ["holder", "high", "low"], starts
    assert not list((tmp_path / "t.lock.waiters").iterdir()), "a marker was left behind"


def test_a_stale_high_marker_is_ignored_and_removed(tmp_path: Path) -> None:
    waiters = tmp_path / "t.lock.waiters"
    waiters.mkdir()
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    stale = waiters / f"{dead.pid}.high"
    stale.touch()
    log = tmp_path / "log"
    low = _run(tmp_path, "low", "low", 0.05, log)
    assert low.wait(15) == 0
    assert "start low" in log.read_text()
    assert not stale.exists()


def test_two_high_waiters_still_serialize(tmp_path: Path) -> None:
    log = tmp_path / "log"
    a = _run(tmp_path, "a", "high", 0.4, log)
    _wait_started(log, "a")
    b = _run(tmp_path, "b", "high", 0.4, log)
    assert a.wait(30) == 0 and b.wait(30) == 0
    rows = _order(log)
    assert [(k, n) for k, n, _ in rows] == [("start", "a"), ("end", "a"), ("start", "b"), ("end", "b")], rows


def test_a_bad_priority_is_refused(tmp_path: Path) -> None:
    env = {**os.environ, "HOLDSPEAK_TEST_LOCK": str(tmp_path / "t.lock"), "HOLDSPEAK_TEST_LOCK_PRIORITY": "urgent"}
    run = subprocess.run([sys.executable, str(LOCK), "--", "true"], env=env, capture_output=True, text=True)
    assert run.returncode == 2 and "PRIORITY" in run.stderr
