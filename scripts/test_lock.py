"""Run one command while holding the machine-wide test lock.

Owner catch 2026-10-07: "A ton of your workers are just running tests at the
same time and keep breaking each other." Every test run on this machine
(pytest, vitest, graph walks, glass_for) goes through this lock. The
orchestrator's FAST takes the same lock.

Usage:
    uv run python scripts/test_lock.py -- <command> [args...]
    uv run python scripts/test_lock.py --class unit -- uv run pytest -q tests/unit/test_x.py
    uv run python scripts/test_lock.py --wait 1800 -- uv run pytest -q tests/unit

Classes (2026-11-08, owner: "I still see a ton of sequentiality"):

* ``unit``: up to 3 unit runs share the machine (a semaphore of 3 slots,
  $HOLDSPEAK_TEST_LOCK_SLOTS). The default for a direct pytest run that names
  no browser file and for a direct vitest run. A unit run must set an isolated
  HOME: the lock refuses the real HOME. When the 1-minute load is above 24
  ($HOLDSPEAK_TEST_LOCK_MAX_LOAD), a unit run waits until no other unit run
  holds a slot, as before.
* ``browser``: exclusive against every other run. The default for every other
  command, and for any command that names tests/e2e, the desk sweep, glass,
  Playwright, a graph walk or tests/uat. A waiting browser run goes before
  unit runs of the same or lower priority, so it is never starved.

The lock is fcntl flocks on $HOLDSPEAK_TEST_LOCK (default
/tmp/holdspeak-tests.lock): a browser run holds it exclusive; a unit run holds
it shared plus one slot file <lock>.slot<N> exclusive. Every flock is released
when the command exits, whether it passed, failed or was killed. The exit code
is the command's.

Priority (the fast cycle, 2026-10-12): a run is HIGH by default (a quick
check, a lane's scoped run). A run started with
HOLDSPEAK_TEST_LOCK_PRIORITY=low (the main watcher's shards) does not take the
lock while any HIGH run is waiting. Each waiter registers a marker file
<lock>.waiters/<pid>.<prio>.<class>; it is removed when the waiter takes the
lock or exits, and a marker whose process is gone is ignored and removed.

Reentrant (2026-11-07): a command that already runs under this lock runs at
once, whatever its class.
"""
from __future__ import annotations

import fcntl
import os
import pwd
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import IO, Optional

PRIORITIES = ("high", "low")
CLASSES = ("unit", "browser")
#: A command that names one of these is a browser run (exclusive).
BROWSER_MARKS = ("tests/e2e", "test_desk_sweep", "playwright", "glass", "graph_walk", "tests/uat")
#: pytest options that take a value (so the value is not read as a path).
_PYTEST_VALUE_OPTS = {"-n", "-m", "-k", "-p", "-c", "-o", "--dist", "--durations", "--timeout", "--rootdir",
                      "--maxfail", "--junitxml", "--basetemp", "-W", "--deselect", "--ignore"}


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _marker(name: str) -> Optional[tuple[int, str, str]]:
    """(pid, priority, class) of a marker name; an old ``<pid>.<prio>`` marker is a browser run."""
    parts = name.split(".")
    try:
        pid = int(parts[0])
    except ValueError:
        return None
    prio = parts[1] if len(parts) > 1 else "high"
    cls = parts[2] if len(parts) > 2 else "browser"
    return pid, prio, cls


def live_waiters(waiters: Path, me: int) -> list[tuple[int, str, str]]:
    """The live waiters other than `me`; stale markers are removed."""
    found: list[tuple[int, str, str]] = []
    try:
        entries = list(waiters.iterdir())
    except FileNotFoundError:
        return found
    for entry in entries:
        row = _marker(entry.name)
        if row is None:
            continue
        if not _alive(row[0]):
            entry.unlink(missing_ok=True)
            continue
        if row[0] != me:
            found.append(row)
    return found


def high_waiters(waiters: Path, me: int) -> list[int]:
    """The live HIGH waiters other than `me` (kept for callers of the old name)."""
    return [pid for pid, prio, _ in live_waiters(waiters, me) if prio == "high"]


def ahead_of(waiters: Path, me: int, prio: str, cls: str) -> list[int]:
    """The waiters that go before this one: every HIGH waiter for a LOW run;
    for a unit run also every browser waiter of the same or higher priority."""
    ahead = []
    for pid, wprio, wcls in live_waiters(waiters, me):
        if prio == "low" and wprio == "high":
            ahead.append(pid)
        elif cls == "unit" and wcls == "browser" and (wprio == "high" or prio == "low"):
            ahead.append(pid)
    return ahead


def _pytest_paths(args: list[str]) -> list[str]:
    paths, skip = [], False
    for arg in args:
        if skip:
            skip = False
            continue
        if arg in _PYTEST_VALUE_OPTS:
            skip = True
            continue
        if not arg.startswith("-"):
            paths.append(arg)
    return paths


def guess_class(cmd: list[str]) -> str:
    """unit for a direct pytest run on named files with no browser file, or a
    direct vitest run; browser for everything else."""
    text = " ".join(cmd)
    if any(mark in text for mark in BROWSER_MARKS):
        return "browser"
    words = list(cmd)
    if words[:1] == ["uv"] and len(words) > 1 and words[1] == "run":
        words = words[2:]
        while words and words[0].startswith("--"):
            words = words[2:] if words[0] in ("--project", "--with", "--python") else words[1:]
    if words and Path(words[0]).name.startswith("python") and words[1:3] == ["-m", "pytest"]:
        words = ["pytest", *words[3:]]
    if words[:1] == ["npx"]:
        words = words[1:]
    if not words:
        return "browser"
    tool = Path(words[0]).name
    if tool == "vitest":
        return "unit"
    if tool == "pytest":
        paths = _pytest_paths(words[1:])
        # No path, or the whole tests/ tree: the suite, browser files included.
        if not paths or any(p.rstrip("/") in ("tests", ".") for p in paths):
            return "browser"
        return "unit"
    return "browser"


def real_home() -> str:
    try:
        return pwd.getpwuid(os.getuid()).pw_dir
    except KeyError:
        return ""


def _isolated_home() -> tuple[bool, str]:
    home = os.environ.get("HOME", "")
    real = real_home()
    if not home:
        return False, "HOME is not set"
    if real and os.path.realpath(home) == os.path.realpath(real):
        return False, f"HOME={home} is the real home"
    return True, ""


def _try(handle: IO[str], mode: int) -> bool:
    try:
        fcntl.flock(handle, mode | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


def _take_slot(slots: list[IO[str]], alone: bool) -> Optional[IO[str]]:
    """One free slot; with ``alone``, only when every slot is free."""
    if not alone:
        for handle in slots:
            if _try(handle, fcntl.LOCK_EX):
                return handle
        return None
    got = [h for h in slots if _try(h, fcntl.LOCK_EX)]
    if len(got) == len(slots):
        for handle in got[1:]:
            fcntl.flock(handle, fcntl.LOCK_UN)
        return got[0]
    for handle in got:
        fcntl.flock(handle, fcntl.LOCK_UN)
    return None


def main(argv: list[str]) -> int:
    wait = 7200.0
    cls: Optional[str] = None
    if "--" not in argv:
        sys.stderr.write(__doc__ or "")
        return 2
    split = argv.index("--")
    opts, cmd = argv[:split], argv[split + 1 :]
    i = 0
    while i < len(opts):
        if opts[i] == "--wait" and i + 1 < len(opts):
            wait = float(opts[i + 1])
            i += 2
        elif opts[i] == "--class" and i + 1 < len(opts):
            cls = opts[i + 1]
            i += 2
        else:
            sys.stderr.write(f"unknown option {opts[i]}\n")
            return 2
    if not cmd:
        sys.stderr.write("no command given after --\n")
        return 2
    if cls is not None and cls not in CLASSES:
        sys.stderr.write(f"test_lock: --class must be one of {CLASSES}\n")
        return 2
    path = os.environ.get("HOLDSPEAK_TEST_LOCK", "/tmp/holdspeak-tests.lock")
    prio = os.environ.get("HOLDSPEAK_TEST_LOCK_PRIORITY", "high").strip().lower() or "high"
    if prio not in PRIORITIES:
        sys.stderr.write(f"test_lock: HOLDSPEAK_TEST_LOCK_PRIORITY must be one of {PRIORITIES}\n")
        return 2
    poll = float(os.environ.get("HOLDSPEAK_TEST_LOCK_POLL", "1"))
    # Reentrant (2026-11-07): a command that already runs under this lock
    # (quick_check.sh, whose every step takes the lock) was wrapped in the lock
    # again by a caller that followed CLAUDE.md to the letter; the inner call
    # waited on the outer for the whole 7200 s. A nested call sees the holder's
    # pid in the environment and runs at once.
    held = os.environ.get("HOLDSPEAK_TEST_LOCK_HELD", "")
    if held.isdigit() and _alive(int(held)) and os.environ.get("HOLDSPEAK_TEST_LOCK_HELD_PATH", path) == path:
        return subprocess.call(cmd)
    cls = cls or guess_class(cmd)
    if cls == "unit":
        ok, why = _isolated_home()
        if not ok:
            sys.stderr.write(
                f"test_lock: refused: a unit run shares the machine with other runs, so it must use an "
                f"isolated HOME ({why}). Run it as: HOME=$(mktemp -d) uv run python scripts/test_lock.py "
                f"-- <command>\n")
            return 2
    slots_n = max(1, int(os.environ.get("HOLDSPEAK_TEST_LOCK_SLOTS", "3")))
    max_load = float(os.environ.get("HOLDSPEAK_TEST_LOCK_MAX_LOAD", "24"))
    waiters = Path(f"{path}.waiters")
    waiters.mkdir(parents=True, exist_ok=True)
    marker = waiters / f"{os.getpid()}.{prio}.{cls}"
    # A TERM or INT while waiting still removes the marker (finally).
    def _stop(signum: int, _frame: object) -> None:
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, _stop)
    started = time.monotonic()
    slots = [open(f"{path}.slot{n}", "a+") for n in range(slots_n)] if cls == "unit" else []
    slot: Optional[IO[str]] = None
    with open(path, "a+") as handle:
        announced = False
        marker.touch()
        try:
            while True:
                ahead = ahead_of(waiters, os.getpid(), prio, cls)
                if not ahead:
                    if cls == "browser":
                        if _try(handle, fcntl.LOCK_EX):
                            break
                    elif _try(handle, fcntl.LOCK_SH):
                        busy = os.getloadavg()[0] > max_load
                        slot = _take_slot(slots, alone=busy)
                        if slot is not None:
                            break
                        fcntl.flock(handle, fcntl.LOCK_UN)
                if not announced:
                    if ahead:
                        why = f"{len(ahead)} run(s) go first"
                    elif cls == "unit":
                        why = "a browser run holds it, or every unit slot is taken, or the load is above " \
                              f"{max_load:.0f}"
                    else:
                        why = "another test run holds it"
                    sys.stderr.write(f"test_lock: waiting for {path} ({cls} run; {why})\n")
                    announced = True
                if time.monotonic() - started > wait:
                    sys.stderr.write(f"test_lock: gave up after {wait:.0f} s\n")
                    return 75
                time.sleep(poll)
        finally:
            marker.unlink(missing_ok=True)
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
        note = slot if slot is not None else handle
        note.seek(0)
        note.truncate()
        note.write(f"{os.getpid()} {cls} {time.strftime('%H:%M:%S')} {' '.join(cmd)[:200]}\n")
        note.flush()
        waited = time.monotonic() - started
        if waited > 1:
            sys.stderr.write(f"test_lock: acquired after {waited:.0f} s\n")
        env = dict(os.environ, HOLDSPEAK_TEST_LOCK_HELD=str(os.getpid()), HOLDSPEAK_TEST_LOCK_HELD_PATH=path,
                   HOLDSPEAK_TEST_LOCK_HELD_CLASS=cls)
        try:
            return subprocess.call(cmd, env=env)
        finally:
            for h in slots:
                h.close()
            fcntl.flock(handle, fcntl.LOCK_UN)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
