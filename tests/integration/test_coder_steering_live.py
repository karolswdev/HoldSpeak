"""Live peek proof (HS-87-01) — a real tmux server, a real pane.

Creates a throwaway tmux session whose pane prints a ticking clock,
then proves the attach seam against it: real content comes back, the
content-hash gate answers `not_modified` while the pane is unchanged
and reopens when it moves, and a dead pane is a typed `pane_gone`,
never an exception. Skips honestly when tmux is not on this machine.
"""

from __future__ import annotations

import shutil
import subprocess
import time
import uuid

import pytest

from holdspeak.coder_steering import peek_pane

pytestmark = pytest.mark.skipif(
    shutil.which("tmux") is None, reason="tmux is required for the live peek proof"
)


@pytest.fixture
def live_pane():
    session = f"hs87-peek-{uuid.uuid4().hex[:8]}"
    subprocess.run(
        [
            "tmux",
            "new-session",
            "-d",
            "-s",
            session,
            "printf 'line-one\\nline-two\\n'; sleep 120",
        ],
        check=True,
        timeout=10,
    )
    try:
        pane = (
            subprocess.run(
                ["tmux", "list-panes", "-t", session, "-F", "#{pane_id}"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
        )
        time.sleep(0.5)
        yield session, pane
    finally:
        subprocess.run(["tmux", "kill-session", "-t", session], timeout=10)


def test_live_peek_hash_gate_and_dead_pane(live_pane) -> None:
    session, pane = live_pane

    first = peek_pane(pane, lines=50)
    assert first["status"] == "live", first
    body = "\n".join(first["lines"])
    assert "line-one" in body and "line-two" in body

    unchanged = peek_pane(pane, lines=50, last_hash=first["hash"])
    assert unchanged == {"status": "not_modified", "hash": first["hash"]}

    subprocess.run(
        ["tmux", "send-keys", "-t", pane, "-l", "moved"],
        check=True,
        timeout=10,
    )
    time.sleep(0.3)
    moved = peek_pane(pane, lines=50, last_hash=first["hash"])
    assert moved["status"] == "live"
    assert "moved" in "\n".join(moved["lines"])

    gone = peek_pane("%999999", lines=50)
    assert gone["status"] == "pane_gone"
