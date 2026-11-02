"""The fix proof of 2026-11-02 (program-4da1d4517fbb step 2): the review
started and waited on its builder's turn; the builder launch ended with no
turn end (its brief sat unsubmitted, its pane was stopped). Nothing would
start the reviewer, and the step sat in review for good. Now the next tick
hands the step again for its review, once per ended builder, and says why."""
from __future__ import annotations

from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig
from holdspeak.services.program_runner import REVIEW_BUILDER_ENDED, REVIEW_WAIT_BRIEF


def test_a_builder_that_ended_before_its_review_is_handed_again_once_and_the_review_runs(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Fix: Audit proof", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="build-and-review", control="yolo", reviewer_profile="claude-default")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Fix the guide link", "brief": "Fix it."}])
    rig.service.start(OWNER, pid)
    rig.tick()
    first = rig.step(pid, 1)["launch_id"]
    rig.agent.finish(first, {"docs/guide.md": "# guide\n"})
    rig.ledger.update(first, state="complete")   # the builder ended after its green check
    rig.tick(3)
    step = rig.step(pid, 1)
    second = step["launch_id"]
    assert second != first and step["state"] == "review"
    assert (rig.ledger.get(second)["review"] or {}).get("status") == "awaiting_builder_commit"
    # The re-handed builder never ends a turn: its pane is stopped.
    rig.ledger.update(second, state="complete")
    rig.tick()
    step = rig.step(pid, 1)
    third = step["launch_id"]
    assert third not in (first, second), "the next tick hands the step again"
    assert rig.ledger.get(third).get("first_message") == REVIEW_WAIT_BRIEF
    assert rig.ledger.get(second)["review_rehanded"]["reason"] == REVIEW_BUILDER_ENDED
    lines = [row["line"] for row in rig.service.store.list_checkpoints(pid)]
    assert f"{REVIEW_BUILDER_ENDED} ({second})" in lines, lines
    rig.tick(2)
    assert rig.step(pid, 1)["launch_id"] == third   # once per builder: the live one is waited on
    # Its turn ends; the reviewer starts as its helper, passes, the step merges.
    rig.agent.end_turn(third)
    rig.tick()
    reviewers = [r for r in rig.ledger.list() if r.get("helper_of") == third]
    assert len(reviewers) == 1
    rig.words[reviewers[0]["launch_id"]] = "MUST: none"
    rig.states[reviewers[0]["launch_id"]] = {"state": "done", "turn_id": "r1"}
    rig.tick(8)
    assert rig.step(pid, 1)["state"] in ("pr_open", "merge_ask", "merged", "done"), rig.step(pid, 1)["state"]
