"""Run one command while holding the machine-wide test lock.

Owner catch 2026-10-07: "A ton of your workers are just running tests at the
same time and keep breaking each other." Every test run on this machine
(pytest, vitest, graph walks, glass_for) goes through this lock, so at most
ONE run executes at a time; the rest wait their turn. The orchestrator's FAST
takes the same lock.

Usage:
    uv run python scripts/test_lock.py -- <command> [args...]
    uv run python scripts/test_lock.py --wait 1800 -- uv run pytest -q tests/unit

The lock is an fcntl flock on $HOLDSPEAK_TEST_LOCK (default
/tmp/holdspeak-tests.lock). It is released when the command exits, whether it
passed, failed or was killed. The exit code is the command's.

Priority (the fast cycle, 2026-10-12): a run is HIGH by default (a quick
check, a lane's scoped run). A run started with
HOLDSPEAK_TEST_LOCK_PRIORITY=low (the main watcher's shards) does not take the
lock while any HIGH run is waiting, so a quick check waits at most for the
run that holds the lock now. Each waiter registers a marker file
<lock>.waiters/<pid>.<prio>; it is removed when the waiter takes the lock or
exits, and a marker whose process is gone is ignored and removed. The flock
stays the mutual exclusion.
"""
from __future__ import annotations

import fcntl
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

PRIORITIES = ("high", "low")


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def high_waiters(waiters: Path, me: int) -> list[int]:
    """The live HIGH waiters other than `me`; stale markers are removed."""
    found: list[int] = []
    try:
        entries = list(waiters.iterdir())
    except FileNotFoundError:
        return found
    for marker in entries:
        pid_text, _, prio = marker.name.partition(".")
        try:
            pid = int(pid_text)
        except ValueError:
            continue
        if not _alive(pid):
            marker.unlink(missing_ok=True)
            continue
        if prio == "high" and pid != me:
            found.append(pid)
    return found


def main(argv: list[str]) -> int:
    wait = 7200.0
    if "--" not in argv:
        sys.stderr.write(__doc__)
        return 2
    split = argv.index("--")
    opts, cmd = argv[:split], argv[split + 1 :]
    i = 0
    while i < len(opts):
        if opts[i] == "--wait" and i + 1 < len(opts):
            wait = float(opts[i + 1])
            i += 2
        else:
            sys.stderr.write(f"unknown option {opts[i]}\n")
            return 2
    if not cmd:
        sys.stderr.write("no command given after --\n")
        return 2
    path = os.environ.get("HOLDSPEAK_TEST_LOCK", "/tmp/holdspeak-tests.lock")
    prio = os.environ.get("HOLDSPEAK_TEST_LOCK_PRIORITY", "high").strip().lower() or "high"
    if prio not in PRIORITIES:
        sys.stderr.write(f"test_lock: HOLDSPEAK_TEST_LOCK_PRIORITY must be one of {PRIORITIES}\n")
        return 2
    poll = float(os.environ.get("HOLDSPEAK_TEST_LOCK_POLL", "1"))
    waiters = Path(f"{path}.waiters")
    waiters.mkdir(parents=True, exist_ok=True)
    marker = waiters / f"{os.getpid()}.{prio}"
    # A TERM or INT while waiting still removes the marker (finally).
    def _stop(signum: int, _frame: object) -> None:
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, _stop)
    started = time.monotonic()
    with open(path, "a+") as handle:
        announced = False
        marker.touch()
        try:
            while True:
                ahead = high_waiters(waiters, os.getpid()) if prio == "low" else []
                if not ahead:
                    try:
                        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        pass
                if not announced:
                    why = f"{len(ahead)} high-priority run(s) go first" if ahead else "another test run holds it"
                    sys.stderr.write(f"test_lock: waiting for {path} ({why})\n")
                    announced = True
                if time.monotonic() - started > wait:
                    sys.stderr.write(f"test_lock: gave up after {wait:.0f} s\n")
                    return 75
                time.sleep(poll)
        finally:
            marker.unlink(missing_ok=True)
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
        handle.seek(0)
        handle.truncate()
        handle.write(f"{os.getpid()} {time.strftime('%H:%M:%S')} {' '.join(cmd)[:200]}\n")
        handle.flush()
        waited = time.monotonic() - started
        if waited > 1:
            sys.stderr.write(f"test_lock: acquired after {waited:.0f} s\n")
        try:
            return subprocess.call(cmd)
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
