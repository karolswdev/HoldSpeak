"""A new launch binds only a live session that began after it.

The fix proof of 2026-11-02 (launch_446adeb136b2416e): the step was handed
again in its worktree, and the rider claim of the item's earlier session
(pane %46, ended hours before; the same worktree and story) bound the new
launch. The builder read "ended" for good and its review never started.
"""
from __future__ import annotations

import pytest

from tests.unit.test_agent_hand import OWNER, PROJECT, _rig, _wait_for, db  # noqa: F401


def _row(worktree, key: str, *, lifecycle: str, claimed_at: str | None) -> dict:
    return {
        "session_key": key, "agent": "claude", "lifecycle": lifecycle,
        "repo_root": str(worktree), "cwd": str(worktree),
        "story_claim": {"project": PROJECT, "story_id": "action-ai_1", "claimed_by": "rider:claude",
                        **({"claimed_at": claimed_at} if claimed_at else {})},
    }


@pytest.mark.parametrize("stale", [
    {"lifecycle": "ended", "claimed_at": None},                     # its session ended
    {"lifecycle": "idle", "claimed_at": "2026-07-16T07:26:00Z"},   # it began before the launch (T0 12:00)
])
def test_a_stale_claim_for_the_same_worktree_never_binds_the_new_launch(tmp_path, db, monkeypatch, stale) -> None:  # noqa: F811
    rig = _rig(tmp_path, db, monkeypatch)

    def claims(**_kw):
        if not rig.worktree.exists():
            return []
        # The earlier session first: on main it took the new launch.
        return [_row(rig.worktree, "claude:old-session", **stale),
                _row(rig.worktree, "claude:live-session", lifecycle="working", claimed_at="2026-07-16T12:00:05Z")]

    monkeypatch.setattr("holdspeak.agent_context.sessions.list_agent_story_claims", claims)
    launch_id = rig.hand.hand(OWNER, "action", "ai_1")["launch_id"]
    rig.service.bind_rider_claims()
    record = _wait_for(lambda: rig.launches.get(launch_id), "state", "registered")
    rig.tmux.ended = True
    assert record["session_key"] == "claude:live-session"
