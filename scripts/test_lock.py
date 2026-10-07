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
"""
from __future__ import annotations

import fcntl
import os
import subprocess
import sys
import time


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
    started = time.monotonic()
    with open(path, "a+") as handle:
        announced = False
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if not announced:
                    sys.stderr.write(f"test_lock: waiting for {path} (another test run holds it)\n")
                    announced = True
                if time.monotonic() - started > wait:
                    sys.stderr.write(f"test_lock: gave up after {wait:.0f} s\n")
                    return 75
                time.sleep(5)
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
