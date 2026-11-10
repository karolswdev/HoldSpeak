"""Own processes at the test edge; report and reap anything a run leaves."""
from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import time
import uuid
import re


class ProcessGuard:
    def __init__(self) -> None:
        self.started: list[tuple[subprocess.Popen, str, str]] = []
        self.paths: dict[str, str] = {}
        self.original = subprocess.Popen.__init__
        self.run_id = uuid.uuid4().hex
        self.last_tmux_test = "session setup"
        self.previous_run_id = os.environ.get("HOLDSPEAK_TEST_PROCESS_RUN")

    def install(self) -> None:
        guard = self
        os.environ["HOLDSPEAK_TEST_PROCESS_RUN"] = self.run_id

        def start(process, *args, **kwargs):
            guard.original(process, *args, **kwargs)
            test = os.environ.get("PYTEST_CURRENT_TEST", "session setup").rsplit(" (", 1)[0]
            argv = process.args
            command = str(argv[0] if isinstance(argv, (list, tuple)) else argv).split()[0]
            guard.started = [(p, origin, cmd) for p, origin, cmd in guard.started if p.poll() is None]
            guard.started.append((process, test, Path(command).name))
            if Path(command).name == "tmux":
                guard.last_tmux_test = test

        subprocess.Popen.__init__ = start

    def finish(self, tmux_dir: str) -> list[str]:
        subprocess.Popen.__init__ = self.original
        rows = subprocess.run(["ps", "-axo", "pid=,ppid=,stat=,comm="],
                              capture_output=True, text=True, check=True).stdout
        table = {}
        for row in rows.splitlines():
            parts = row.split(None, 3)
            if len(parts) == 4:
                table[int(parts[0])] = (int(parts[1]), parts[2], Path(parts[3]).name)
        roots = {p.pid: (test, command) for p, test, command in self.started if p.poll() is None}
        # tmux daemonizes: read ONLY this worker's private sockets.
        if Path(tmux_dir).is_dir():
            for socket in Path(tmux_dir).rglob("*"):
                if not socket.is_socket():
                    continue
                result = subprocess.run(["tmux", "-S", str(socket), "display-message", "-p", "#{pid}"],
                                        capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip().isdigit():
                    roots[int(result.stdout.strip())] = (self.last_tmux_test, "tmux")
        # A child may daemonize or lose its parent before teardown. Its
        # inherited run id still names this run; never match agent names on
        # the owner's machine. Do not print ps's environment (it has secrets).
        environments = subprocess.run(
            ["ps", "eww", "-U", str(os.getuid()), "-o", "pid=,command="],
            capture_output=True, text=True, check=True,
        ).stdout
        for row in environments.splitlines():
            pid_text, _, command = row.strip().partition(" ")
            if pid_text.isdigit() and f"HOLDSPEAK_TEST_PROCESS_RUN={self.run_id}" in command:
                pid = int(pid_text)
                if pid in table and pid != os.getpid():
                    test = re.search(r"PYTEST_CURRENT_TEST=(.*?) \((?:setup|call|teardown)\)", command)
                    roots[pid] = (test[1] if test else "session setup", table[pid][2])
        owned = dict(roots)
        changed = True
        while changed:
            changed = False
            for pid, (parent, _state, command) in table.items():
                if parent in owned and pid not in owned:
                    owned[pid] = (owned[parent][0], command)
                    changed = True
        leaks = {pid: source for pid, source in owned.items()
                 if pid in table and not table[pid][1].startswith("Z")}
        for sig in (signal.SIGTERM, signal.SIGKILL):
            for pid in reversed(list(leaks)):
                try:
                    os.kill(pid, sig)
                except ProcessLookupError:
                    pass
            if leaks and sig == signal.SIGTERM:
                time.sleep(0.1)
        if self.previous_run_id is None:
            os.environ.pop("HOLDSPEAK_TEST_PROCESS_RUN", None)
        else:
            os.environ["HOLDSPEAK_TEST_PROCESS_RUN"] = self.previous_run_id
        return [f"pid={pid} {command}: {test}; tmp={self.paths.get(test, tmux_dir)}"
                for pid, (test, command) in sorted(leaks.items())]
