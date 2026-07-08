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


def test_live_arm_then_killed_pane_refuses_and_revokes(live_pane) -> None:
    """HS-87-02 crown case against a real tmux server: arm pins the
    real `%N`, the grant verifies while the pane lives, and killing
    the pane makes the next check refuse AND revoke."""
    from holdspeak.coder_steering import (
        active_grants,
        arm,
        clear_grants,
        require_grant,
    )

    session, pane = live_pane
    clear_grants()
    try:
        armed = arm("claude:live-proof", f"{session}:0.0")
        assert armed["status"] == "armed"
        assert armed["pane_id"] == pane  # the real unique id, pinned

        ok = require_grant("claude:live-proof", f"{session}:0.0")
        assert ok["status"] == "ok"

        subprocess.run(["tmux", "kill-session", "-t", session], timeout=10)
        time.sleep(0.2)
        refused = require_grant("claude:live-proof", f"{session}:0.0")
        assert refused["status"] == "pane_gone"
        assert refused["revoked"] is True
        assert active_grants() == {}
    finally:
        clear_grants()


def test_live_steer_lands_in_the_real_pane(live_pane) -> None:
    """HS-87-03 against a real tmux server: an armed steer delivered
    through THE chokepoint lands in the pane exactly as composed
    (literal text, no-submit mode so the shell holds it), and the
    audit sink records the delivery against the verified %N."""
    from holdspeak.coder_steering import arm, clear_grants, deliver, peek_pane

    session, pane = live_pane
    clear_grants()
    rows: list[dict] = []
    try:
        # The fixture pane's foreground `sleep` leaves tty echo on, so
        # delivered keystrokes are visible in the capture.
        armed = arm("claude:live-steer", f"{session}:0.0")
        assert armed["status"] == "armed"
        marker = f"steered-{uuid.uuid4().hex[:8]}"
        result = deliver(
            "claude:live-steer",
            marker,
            current_target=f"{session}:0.0",
            agent="claude",
            submit=False,  # leave it visible in the composer line
            audit=lambda **kw: rows.append(kw) or 1,
        )
        assert result["status"] == "delivered"
        assert result["pane_id"] == pane
        time.sleep(0.4)
        seen = peek_pane(pane, lines=50)
        assert marker in "\n".join(seen["lines"])  # the keystrokes are IN the pane
        assert rows[0]["outcome"] == "delivered"
        assert rows[0]["pane_id"] == pane
    finally:
        clear_grants()


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
