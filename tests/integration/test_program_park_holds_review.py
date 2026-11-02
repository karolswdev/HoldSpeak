"""The rule of #1753 for reviews (the fix proof of 2026-11-02): while
program-4da1d4517fbb was parked, its step's builder ended its turn and the
review loop started a reviewer anyway (``launch_449c6d44f30540b4``). A
parked Program now gets no reviewer and no merge; after the Resume the
review starts and the step merges."""
from __future__ import annotations

from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig


def test_a_parked_program_gets_no_reviewer_and_no_merge_until_its_resume(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Fix: Audit proof", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="build-and-review", control="yolo", reviewer_profile="claude-default")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Fix the guide link", "brief": "Fix it."}])
    rig.service.start(OWNER, pid)
    rig.tick()
    builder = rig.step(pid, 1)["launch_id"]
    rig.agent.finish(builder, {"docs/guide.md": "# guide\n"})
    rig.ledger.update(builder, state="complete")   # as on his desk: the builder ended
    rig.tick(3)
    step = rig.step(pid, 1)
    assert step["state"] == "review", step["state"]
    builder = step["launch_id"]   # handed again for its review; its turn has not ended
    rig.service.park(OWNER, pid, reason="proof")
    rig.agent.end_turn(builder)   # the builder's turn ends while the Program is parked
    rig.tick(4)
    assert [r for r in rig.ledger.list() if r.get("helper_of") == builder] == [], "no reviewer while parked"
    assert rig.step(pid, 1)["state"] == "parked"
    rig.service.resume(OWNER, pid)
    rig.tick()
    reviewers = [r for r in rig.ledger.list() if r.get("helper_of") == builder]
    assert len(reviewers) == 1, "the review starts after the Resume"
    rig.words[reviewers[0]["launch_id"]] = "MUST: none"
    rig.states[reviewers[0]["launch_id"]] = {"state": "done", "turn_id": "r1"}
    rig.tick(8)
    assert rig.step(pid, 1)["state"] in ("pr_open", "merge_ask", "merged", "done"), rig.step(pid, 1)["state"]
