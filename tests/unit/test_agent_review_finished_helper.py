"""A finished reviewer is done, not the builder's live helper.

The fix proof of 2026-11-02 (program-4da1d4517fbb step 2): the builder,
handed again to wait for its review, started a reviewer itself. The
reviewer finished ("Nothing to fix" in its pane, its launch complete),
the builder's reads of it timed out, and the engine's own review then
refused with "this agent already has its one helper" because the finished
reviewer's worktree was still there. The next review must start, and the
engine takes its result itself; the builder never reads it.
"""
from __future__ import annotations

import subprocess

import pytest

from holdspeak.services import agent_helpers as helpers
from holdspeak.services.agent_review import AgentReviewLoop, initial_review
from tests.unit.test_agent_hand import OWNER, _rig, _wait_for, db  # noqa: F401

CLEAR = "Check 4: PASS\nREVIEW RESULT\nMUST: none\nREQ R2: MET · the guide exists\nEND REVIEW RESULT"


def _builder_with_commit(rig):
    parent = rig.hand.hand(OWNER, "action", "ai_1")
    record = _wait_for(lambda: rig.launches.get(parent["launch_id"]), "state", "registered")
    (rig.worktree / "GUIDE.md").write_text("the guide\n")
    subprocess.run(["git", "add", "."], cwd=rig.worktree, check=True)
    subprocess.run(["git", "-c", "user.name=b", "-c", "user.email=b@x.invalid", "commit", "-q", "-m", "guide"],
                   cwd=rig.worktree, check=True)
    return parent["launch_id"], record


@pytest.mark.parametrize("pane_reads", ["done", "waiting"])   # "done": the night's case; "waiting": an idle pane
def test_a_finished_reviewer_does_not_block_the_next_review_and_its_result_is_taken_in(
        tmp_path, db, monkeypatch, pane_reads) -> None:  # noqa: F811
    rig = _rig(tmp_path, db, monkeypatch)
    builder_id, record = _builder_with_commit(rig)
    # The builder started a reviewer itself; it finished, its pane idle.
    first = helpers.start_helper(builder_id, instruction="Review the diff", profile=None,
                                 hand_service=rig.hand, control_mode=lambda: "yolo", ledger=rig.launches)
    first_id = first["launch_id"]
    rig.launches.update(first_id, state="complete")
    assert (rig.worktree.parent / f"{rig.worktree.name}-helper").exists()   # its worktree stays
    rig.launches.update(builder_id, review=initial_review("claude"))

    states = {builder_id: "done", first_id: pane_reads}
    results: dict[str, str] = {}
    loop = AgentReviewLoop(db, rig.hand, ledger=rig.launches,
                           state_reader=lambda launch_id: states.get(launch_id, ""),
                           commit_reader=lambda rec: "c73ab96",
                           result_reader=lambda launch_id: results.get(launch_id, ""))
    started = loop.tick()
    pair = rig.launches.get(builder_id)["review"]
    assert pair["status"] == "reviewing", pair.get("result")   # not "Reviewer could not start: … its one helper"
    reviewer_id = pair["reviewer_launch_id"]
    assert reviewer_id and reviewer_id != first_id
    reviewer = rig.launches.get(reviewer_id)
    assert reviewer["helper_of"] == builder_id
    assert reviewer["branch"] == f"{record['branch']}-2-helper"   # the next free round name

    # The reviewer ends its turn; the engine reads its words, not the builder.
    states[reviewer_id] = "done"
    results[reviewer_id] = CLEAR
    loop.tick()
    pair = rig.launches.get(builder_id)["review"]
    assert pair["status"] == "done" and pair["findings_left"] == []
    assert pair["rounds"][-1]["result"] == CLEAR


def test_a_reviewer_that_still_runs_is_still_the_one_helper(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    rig = _rig(tmp_path, db, monkeypatch)
    builder_id, _ = _builder_with_commit(rig)
    first = helpers.start_helper(builder_id, instruction="Review the diff", profile=None,
                                 hand_service=rig.hand, control_mode=lambda: "yolo", ledger=rig.launches)
    with pytest.raises(helpers.HelperRefused) as again:
        helpers.start_helper(builder_id, instruction="again", profile=None, hand_service=rig.hand,
                             control_mode=lambda: "yolo", ledger=rig.launches,
                             state_reader=lambda launch_id: "working" if launch_id == first["launch_id"] else "")
    assert again.value.code == "helper_exists"
