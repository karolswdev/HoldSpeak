#!/usr/bin/env python3
"""Run the existing update Send glass and keep Phase 11's own shots.

The assertions are the Phase 10 production-hub fences: inline Send and
prepared Send at 1440 and 393. Only their output directory changes.
HOLDSPEAK_EVIDENCE_WRITE=1 opts into the story's tracked evidence directory.
``--story NN`` picks the story whose shots folder receives them (default 01;
PHILO-11-04 re-runs the same fences on the species).
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CHILD = """
import sys
import pytest
from tests._evidence import evidence_dir
from tests.e2e import test_philo10_04_send_face_glass as glass

glass.SHOTS = evidence_dir(
    'pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-' + sys.argv[2] + '-shots'
)
raise SystemExit(pytest.main([
    '-q', '--basetemp=' + sys.argv[1],
    'tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_first_setup_loop_and_every_file_state',
    'tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_prepared_sends_and_the_latest_result',
    *sys.argv[3:],
]))
"""


def main() -> int:
    args = sys.argv[1:]
    story = "01"
    if args[:1] == ["--story"]:
        story, args = args[1], args[2:]
    env = dict(os.environ)
    real_home = Path.home()
    env.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(real_home / "Library/Caches/ms-playwright"))
    env.setdefault("npm_config_cache", str(real_home / ".npm"))
    with tempfile.TemporaryDirectory(prefix="philo11-glass-") as home:
        env["HOME"] = home
        return subprocess.call(
            [sys.executable, "-c", CHILD, str(Path(home) / "pytest"), story, *args],
            cwd=ROOT, env=env,
        )


if __name__ == "__main__":
    raise SystemExit(main())
