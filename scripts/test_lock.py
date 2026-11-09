"""Run one command inside the machine's test CPU budget.

Owner catch 2026-10-07: "A ton of your workers are just running tests at the
same time and keep breaking each other." Owner ruling 2026-11-09: a load of
30 to 70 on 12 cores is "unacceptable". Every test run on this machine
(pytest, vitest, graph walks, glass_for, the checks) goes through this lock.

Usage:
    uv run python scripts/test_lock.py -- <command> [args...]
    uv run python scripts/test_lock.py --cpus 8 -- uv run pytest -q -n 4 tests/e2e/test_desk_sweep.py
    uv run python scripts/test_lock.py --wait 1800 -- uv run pytest -q -n 4 tests/unit/test_x.py

One CPU budget (2026-11-09), no classes:

* A run takes CPUs: ``--cpus N``, else what the command says (``cpus_of``):
  the pytest ``-n N`` (``auto`` is every core), else 1; a command that drives
  a browser (tests/e2e, the desk sweep, glass, Playwright, a graph walk,
  tests/uat) counts double, because each worker also drives a Chromium; a
  vitest run counts 4.
* The budget is $HOLDSPEAK_TEST_CPUS (default: the core count). A run starts
  when the CPUs of the runs that hold the lock plus its own fit the budget. A
  run larger than the budget starts when no other run holds the lock.
* Waiters go in arrival order, so a large run is never starved by small ones.
  A run started with HOLDSPEAK_TEST_LOCK_PRIORITY=low (the main watcher's
  shards) also waits for every HIGH waiter, whenever it arrived.
* HOME is not checked here. The rigs isolate HOME themselves.

The lock is files next to $HOLDSPEAK_TEST_LOCK (default
/tmp/holdspeak-tests.lock): the lock file is a short mutex for each admission;
<lock>.holders/<pid>.<cpus> is one running run, flocked for its whole life (a
holder whose flock is free is stale and removed); <lock>.waiters/<pid>.<prio>.
<cpus> is one waiter (a marker whose process is gone is removed). Every flock
is released when the command exits, whether it passed, failed or was killed.
The exit code is the command's. ``--class`` is accepted and ignored (old
callers).

Reentrant (2026-11-07): a command that already runs under this lock runs at
once.
"""
from __future__ import annotations

import fcntl
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import IO, Optional

PRIORITIES = ("high", "low")
#: A command that names one of these drives a browser: its CPUs count double.
BROWSER_MARKS = ("tests/e2e", "test_desk_sweep", "playwright", "glass", "graph_walk", "tests/uat")
VITEST_CPUS = 4


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def cores() -> int:
    return os.cpu_count() or 1


def budget() -> int:
    raw = os.environ.get("HOLDSPEAK_TEST_CPUS", "").strip()
    return max(1, int(raw)) if raw.isdigit() else cores()


def _workers(value: str) -> Optional[int]:
    if value in ("auto", "logical"):
        return cores()
    return int(value) if value.isdigit() else None


def cpus_of(cmd: list[str]) -> int:
    """The CPUs a command takes: its pytest -n (doubled for a browser run),
    4 for vitest, else 1."""
    if any(Path(word).name == "vitest" for word in cmd):
        return VITEST_CPUS
    n: Optional[int] = None
    for i, word in enumerate(cmd):
        if word in ("-n", "--numprocesses") and i + 1 < len(cmd):
            n = _workers(cmd[i + 1])
        elif word.startswith("--numprocesses="):
            n = _workers(word.split("=", 1)[1])
        elif word.startswith("-n") and len(word) > 2:
            n = _workers(word[2:])
    n = max(1, n or 1)
    text = " ".join(cmd)
    return n * 2 if any(mark in text for mark in BROWSER_MARKS) else n


def _marker(name: str) -> Optional[tuple[int, str]]:
    """(pid, priority) of a waiter marker name."""
    parts = name.split(".")
    if not parts[0].isdigit():
        return None
    return int(parts[0]), parts[1] if len(parts) > 1 else "high"


def ahead_of(waiters: Path, me: int, prio: str) -> list[int]:
    """The live waiters that go before this one; stale markers are removed.
    A HIGH run waits for older HIGH waiters; a LOW run for every HIGH waiter
    and older LOW waiters."""
    rows = []
    try:
        entries = list(waiters.iterdir())
    except FileNotFoundError:
        return []
    for entry in entries:
        row = _marker(entry.name)
        if row is None:
            continue
        if not _alive(row[0]):
            entry.unlink(missing_ok=True)
            continue
        try:
            rows.append((entry.stat().st_mtime_ns, row[0], row[1]))
        except FileNotFoundError:
            continue
    mine = next(((at, pid) for at, pid, _ in rows if pid == me), (time.time_ns(), me))
    ahead = []
    for at, pid, wprio in rows:
        if pid == me:
            continue
        older = (at, pid) < mine
        if (prio == "low" and wprio == "high") or (wprio == prio and older):
            ahead.append(pid)
    return ahead


def in_use(holders: Path) -> tuple[int, int]:
    """(CPUs, runs) of the live holders; a holder whose flock is free is
    stale and removed. Call it with the mutex held."""
    used = runs = 0
    try:
        entries = list(holders.iterdir())
    except FileNotFoundError:
        return 0, 0
    for entry in entries:
        parts = entry.name.split(".")
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            continue
        try:
            with open(entry, "a") as probe:
                if _try(probe, fcntl.LOCK_EX):
                    entry.unlink(missing_ok=True)
                    continue
        except FileNotFoundError:
            continue
        used += int(parts[1])
        runs += 1
    return used, runs


def _try(handle: IO[str], mode: int) -> bool:
    try:
        fcntl.flock(handle, mode | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


def main(argv: list[str]) -> int:
    wait = 7200.0
    cpus: Optional[int] = None
    if "--" not in argv:
        sys.stderr.write(__doc__ or "")
        return 2
    split = argv.index("--")
    opts, cmd = argv[:split], argv[split + 1 :]
    i = 0
    while i < len(opts):
        if opts[i] == "--wait" and i + 1 < len(opts):
            wait = float(opts[i + 1])
        elif opts[i] == "--cpus" and i + 1 < len(opts) and opts[i + 1].isdigit():
            cpus = max(1, int(opts[i + 1]))
        elif opts[i] == "--class" and i + 1 < len(opts):
            pass  # the classes are gone (2026-11-09); old callers still pass one
        else:
            sys.stderr.write(f"unknown option {opts[i]}\n")
            return 2
        i += 2
    if not cmd:
        sys.stderr.write("no command given after --\n")
        return 2
    path = os.environ.get("HOLDSPEAK_TEST_LOCK", "/tmp/holdspeak-tests.lock")
    prio = os.environ.get("HOLDSPEAK_TEST_LOCK_PRIORITY", "high").strip().lower() or "high"
    if prio not in PRIORITIES:
        sys.stderr.write(f"test_lock: HOLDSPEAK_TEST_LOCK_PRIORITY must be one of {PRIORITIES}\n")
        return 2
    poll = float(os.environ.get("HOLDSPEAK_TEST_LOCK_POLL", "1"))
    # Reentrant (2026-11-07): a nested call sees the holder's pid in the
    # environment and runs at once (its CPUs are the holder's).
    held = os.environ.get("HOLDSPEAK_TEST_LOCK_HELD", "")
    if held.isdigit() and _alive(int(held)) and os.environ.get("HOLDSPEAK_TEST_LOCK_HELD_PATH", path) == path:
        return subprocess.call(cmd)
    cpus = cpus or cpus_of(cmd)
    total = budget()
    waiters, holders = Path(f"{path}.waiters"), Path(f"{path}.holders")
    waiters.mkdir(parents=True, exist_ok=True)
    holders.mkdir(parents=True, exist_ok=True)
    marker = waiters / f"{os.getpid()}.{prio}.{cpus}"
    mine = holders / f"{os.getpid()}.{cpus}"

    def _stop(signum: int, _frame: object) -> None:  # a TERM while waiting still removes the marker
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, _stop)
    started = time.monotonic()
    hold: Optional[IO[str]] = None
    announced = False
    marker.touch()
    try:
        with open(path, "a+") as mutex:
            while hold is None:
                ahead = ahead_of(waiters, os.getpid(), prio)
                used = runs = 0
                why = f"{len(ahead)} run(s) ahead"
                if not ahead and not _try(mutex, fcntl.LOCK_EX):
                    why = "a run of the old lock holds the lock file"
                elif not ahead:
                    try:
                        used, runs = in_use(holders)
                        if runs == 0 or used + cpus <= total:
                            hold = open(mine, "w")
                            fcntl.flock(hold, fcntl.LOCK_EX)
                            hold.write(f"{os.getpid()} {cpus} {time.strftime('%H:%M:%S')} {' '.join(cmd)[:200]}\n")
                            hold.flush()
                            break
                    finally:
                        fcntl.flock(mutex, fcntl.LOCK_UN)
                    why = f"{used} of {total} CPUs in use by {runs} run(s)"
                if not announced:
                    sys.stderr.write(f"test_lock: waiting for {cpus} CPUs ({why})\n")
                    announced = True
                if time.monotonic() - started > wait:
                    sys.stderr.write(f"test_lock: gave up after {wait:.0f} s\n")
                    return 75
                time.sleep(poll)
    finally:
        marker.unlink(missing_ok=True)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
    waited = time.monotonic() - started
    if waited > 1:
        sys.stderr.write(f"test_lock: acquired {cpus} CPUs after {waited:.0f} s\n")
    env = dict(os.environ, HOLDSPEAK_TEST_LOCK_HELD=str(os.getpid()), HOLDSPEAK_TEST_LOCK_HELD_PATH=path)
    try:
        return subprocess.call(cmd, env=env)
    finally:
        mine.unlink(missing_ok=True)
        hold.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
