"""Ruling 2026-11-01 (the live fix-Program proof): a step resumed from its
green check long after its builder ended could not get a reviewer
("Reviewer could not start: parent_operation_not_running": the reviewer is a
helper of the builder launch, and the kernel wants that parent running).
Now, when a review is due and the builder launch no longer runs, the engine
hands the step again in its same worktree and branch with a brief that
builds nothing; the reviewer starts as the helper of that live launch."""
from __future__ import annotations

from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig, git
from holdspeak.services.program_runner import REVIEW_WAIT_BRIEF


def test_a_resume_from_a_green_check_after_the_builder_ended_hands_again_and_the_reviewer_starts(
        tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Fix: Audit proof", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="build-and-review", control="yolo", reviewer_profile="claude-default")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Fix the README", "brief": "Fix it."}])
    rig.service.start(OWNER, pid)
    rig.tick()
    first = rig.step(pid, 1)["launch_id"]
    worktree = rig.ledger.get(first)["worktree_path"]
    # As on his desk: the first reviewer could not start (a desk setting), so
    # the step parked at its green check; the builder's launch then ended.
    real = rig.review._start_reviewer

    def cannot(*_args, **_kwargs):
        raise RuntimeError("Codex will not run the HoldSpeak hooks. Press Install hooks on the Agents card.")

    monkeypatch.setattr(rig.review, "_start_reviewer", cannot)
    commit = rig.agent.finish(first, {"README.md": "# app\nfixed\n"})
    rig.tick(3)
    assert rig.step(pid, 1)["state"] == "parked"
    monkeypatch.setattr(rig.review, "_start_reviewer", real)
    rig.ledger.update(first, state="complete")
    step = rig.service.store.list_steps(pid)[0]
    rig.service.decide(OWNER, pid, step["id"], kind="parked", choice="resume")  # his Resume (from the green check)
    rig.tick()
    step = rig.step(pid, 1)
    second = step["launch_id"]
    assert second != first, "the step is handed again for its review"
    record = rig.ledger.get(second)
    assert record["worktree_path"] == worktree and record["branch"] == rig.ledger.get(first)["branch"]
    assert record.get("first_message") == REVIEW_WAIT_BRIEF
    assert git(rig.repo, "-C", worktree, "rev-parse", "HEAD") == commit  # nothing built, nothing reset
    lines = [row["line"] for row in rig.service.store.list_checkpoints(pid)]
    assert any(line.startswith("Handed the step again to Claude Code for its review") for line in lines), lines
    # Its turn ends (it builds nothing); the reviewer starts as its helper.
    rig.agent.end_turn(second)
    rig.tick()
    reviewers = [r for r in rig.ledger.list() if r.get("helper_of") == second]
    assert len(reviewers) == 1 and reviewers[0]["profile_id"] == "claude-default"
    rig.words[reviewers[0]["launch_id"]] = "MUST: none"
    rig.states[reviewers[0]["launch_id"]] = {"state": "done", "turn_id": "r1"}
    rig.tick(4)
    assert rig.step(pid, 1)["state"] in ("pr_open", "merge_ask", "merged", "done"), rig.step(pid, 1)["state"]
