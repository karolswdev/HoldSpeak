"""A hand again continues the builder, never its reviewer.

The fix proof of 2026-11-02 (program-4da1d4517fbb step 2, launch
launch_aeff60584b0e40ba): the step's reviewer had the same origin as its
builder and was the newest launch of the step, so the engine's hand again
for the review continued the reviewer: the new builder ran in the
``-helper`` worktree, on the ``-helper`` branch.
"""
from __future__ import annotations

from holdspeak.services import agent_helpers as helpers
from holdspeak.services.agent_hand_service import _launch_for_origin
from tests.unit.test_agent_hand import OWNER, _rig, _wait_for, db  # noqa: F401


def test_a_hand_again_continues_the_builder_in_its_worktree_not_the_reviewers(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    rig = _rig(tmp_path, db, monkeypatch)
    first = rig.hand.hand(OWNER, "action", "ai_1")
    builder = _wait_for(lambda: rig.launches.get(first["launch_id"]), "state", "registered")
    reviewer = helpers.start_helper(builder["launch_id"], instruction="Review the diff", profile=None,
                                    hand_service=rig.hand, control_mode=lambda: "yolo", ledger=rig.launches)
    helper = rig.launches.get(reviewer["launch_id"])
    assert helper["worktree_id"] != builder["worktree_id"]
    # Both ended: the builder after its turn, the reviewer after its review.
    rig.launches.update(builder["launch_id"], state="complete")
    rig.launches.update(helper["launch_id"], state="complete")

    again = rig.hand.hand(OWNER, "action", "ai_1")
    record = rig.launches.get(again["launch_id"])
    assert record["worktree_id"] == builder["worktree_id"]
    assert record["branch"] == builder["branch"] and not record["branch"].endswith("-helper")
    assert not record.get("helper_of")


def test_a_launch_that_ran_in_a_helpers_worktree_is_not_the_items_launch() -> None:
    class _Ledger:
        def __init__(self, *rows):
            self.rows = list(rows)

        def list(self):
            return self.rows

    origin = {"kind": "program_step", "id": "step-1"}
    builder = {"launch_id": "B", "origin_ref": origin, "worktree_id": "wt_builder", "state": "complete"}
    reviewer = {"launch_id": "R", "origin_ref": origin, "worktree_id": "wt_helper", "helper_of": "B",
                "state": "complete"}
    marked = {"launch_id": "M", "origin_ref": origin, "worktree_id": "wt_marked", "role": "reviewer"}
    stray = {"launch_id": "S", "origin_ref": origin, "worktree_id": "wt_helper", "state": "complete"}
    launcher = type("L", (), {"_ledger": _Ledger(builder, reviewer, marked, stray)})()
    assert _launch_for_origin(launcher, "program_step", "step-1")["launch_id"] == "B"
