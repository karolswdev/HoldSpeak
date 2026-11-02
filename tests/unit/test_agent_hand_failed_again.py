"""The live fix-Program proof (2026-11-01): on a loaded machine one spawn
timed out (`tmux list-panes` after 5 s, "the session is gone") and another
failed at its target; both launch records stayed `failed`, and every later
hand of those steps was refused `worktree_duplicate`. A launch that failed at
spawn or at its target never typed its brief (no agent took the item): its
worktree takes Hand again."""
from __future__ import annotations

from holdspeak.services.agent_hand_service import _hand_again_of


def _record(state: str, stage: str | None = None) -> dict:
    return {"launch_id": "launch_1", "worktree_id": "wt_1", "state": state,
            **({"failure": {"stage": stage, "outcome": "error"}} if stage else {})}


def test_a_launch_that_failed_at_spawn_or_target_takes_hand_again() -> None:
    assert _hand_again_of(_record("failed", "spawn")) == ("launch_1", "wt_1")
    assert _hand_again_of(_record("failed", "target")) == ("launch_1", "wt_1")


def test_a_launch_that_runs_or_failed_after_its_brief_does_not() -> None:
    assert _hand_again_of(_record("launched")) is None
    assert _hand_again_of(_record("failed", "registration")) is None
    assert _hand_again_of(_record("failed")) is None
    assert _hand_again_of(_record("complete")) == ("launch_1", "wt_1")  # unchanged
