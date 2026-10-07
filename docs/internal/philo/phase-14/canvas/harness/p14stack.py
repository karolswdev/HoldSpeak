"""PHILO-14 canvas stack: rig.Stack plus what a Hand to agent launch leaves behind (seed_f2.py:
the clone, worktrees, launches bound to the two hook-reported sessions, a `cat` pane per launch
on a tmux server of its own) and a fake `gh` first on the hub's PATH (PR #412 open on the freeze
flag branch). Copied from the Conductor F2 built proof (../../../../conductor-canvas/harness/
shoot_built_f2.py BuiltStack), minus the transcription double. Nothing leaves the machine; no
agent starts (each pane runs `cat`).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rig  # noqa: E402

REPO = HERE.parents[5]
FAKE_GH = """#!{py}
import os, sys
from pathlib import Path
if sys.argv[1:3] == ["pr", "list"]:
    sys.stdout.write(Path(os.environ["HOME"], ".f2-gh.json").read_text())
    sys.exit(0)
sys.stderr.write("fake gh: no answer for " + " ".join(sys.argv[1:]) + "\\n")
sys.exit(1)
"""


class P14Stack(rig.Stack):
    def _enter(self):
        self.tmux = tempfile.mkdtemp(prefix="p14tmux-", dir="/tmp")
        os.environ["TMUX_TMPDIR"] = self.tmux
        self.ghdir = tempfile.mkdtemp(prefix="p14gh-", dir="/tmp")
        gh = Path(self.ghdir) / "gh"
        gh.write_text(FAKE_GH.format(py=rig.PY))
        gh.chmod(0o755)
        self.hub_env = {"PATH": f"{self.ghdir}{os.pathsep}{os.environ.get('PATH', '')}"}
        super()._enter()
        self.seed["f2"] = self.f2("seed")
        self.f2("gh", "open")
        status, body = rig.hub_api(self.hub, "POST", "/api/settings/heartbeat/run-now", {})
        self.seed["run_now"] = status
        return self

    def f2(self, *argv: str) -> dict:
        env = {**os.environ, "HOME": self.home, "PYTHONPATH": str(REPO), "TMUX_TMPDIR": self.tmux}
        done = subprocess.run([rig.PY, str(HERE / "seed_f2.py"), *argv], cwd=REPO, env=env,
                              capture_output=True, text=True, timeout=120)
        if done.returncode:
            raise RuntimeError(f"seed_f2 {argv} failed: {done.stderr[-2000:]}")
        return json.loads(done.stdout.strip().splitlines()[-1])

    def __exit__(self, *exc):
        tm = getattr(self, "tmux", None)
        try:
            if tm:
                subprocess.run(["tmux", "kill-server"], env={**os.environ, "TMUX_TMPDIR": tm}, capture_output=True, timeout=10)
        finally:
            for d in (tm, getattr(self, "ghdir", None)):
                if d:
                    shutil.rmtree(d, ignore_errors=True)
            os.environ.pop("TMUX_TMPDIR", None)
        return super().__exit__(*exc)
