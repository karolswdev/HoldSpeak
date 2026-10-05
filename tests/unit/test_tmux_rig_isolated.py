"""The test rig's tmux is its own: no test sees or touches the machine's tmux server.

tmux finds its server by ``TMUX_TMPDIR`` and ``$TMUX``, not by HOME, so an
isolated HOME alone still showed the owner's real sessions on the Delivery
board. The run gets its own socket dir (``tests/conftest.py`` ``pytest_configure``).
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


def test_tmux_socket_dir_is_the_runs_own() -> None:
    assert "TMUX" not in os.environ
    tmux_dir = Path(os.environ["TMUX_TMPDIR"])
    assert tmux_dir.name.startswith("hs-tmux-") and tmux_dir.is_dir()


@pytest.mark.skipif(shutil.which("tmux") is None, reason="tmux is not installed")
def test_a_tmux_session_a_test_makes_lands_on_the_rigs_server() -> None:
    name = f"hs-rig-probe-{os.getpid()}"
    subprocess.run(["tmux", "new-session", "-d", "-s", name], check=True, timeout=10)
    try:
        socket = subprocess.run(
            ["tmux", "display-message", "-p", "-t", name, "#{socket_path}"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout.strip()
    finally:
        subprocess.run(["tmux", "kill-session", "-t", name], timeout=10, check=False)
    assert Path(socket).resolve().is_relative_to(Path(os.environ["TMUX_TMPDIR"]).resolve()), socket
